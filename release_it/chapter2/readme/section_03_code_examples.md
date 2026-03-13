# Section 3: Annotated Code Examples

## Example 1: The Cascade in Java — Thread Pool + Connection Pool Death Spiral

### ❌ Naive Approach — What Caused the Outage

```java
import java.sql.*;
import java.util.concurrent.*;

/**
 * ❌ NAIVE REQUEST HANDLER — reproduces the exact failure from Chapter 2.
 *
 * Problems:
 * 1. No timeout on database query → thread blocks forever
 * 2. No try-with-resources → connection leak on exception
 * 3. No null check → NullPointerException cascades
 * 4. Thread pool has no rejection policy → queue grows unbounded
 * 5. No circuit breaker → keeps hammering a dead dependency
 */
public class NaiveRequestHandler {

    // staff-level: Fixed-size pool with unbounded queue is a ticking time bomb.
    // LinkedBlockingQueue has Integer.MAX_VALUE capacity by default.
    // Once threads block, the queue absorbs unlimited requests → OOM eventually.
    private final ExecutorService threadPool =
        Executors.newFixedThreadPool(50);

    // staff-level: DataSource with no connection timeout means getConnection()
    // blocks indefinitely when the pool is full. This is the exact mechanism
    // that turns a thread pool problem into a system-wide deadlock.
    private final DataSource dataSource = createDataSource();

    public void handleRequest(String userId) {
        threadPool.submit(() -> {
            // ❌ NO TIMEOUT: if DB becomes slow, this thread blocks forever
            Connection conn = dataSource.getConnection();

            // ❌ NO TRY-WITH-RESOURCES: if anything below throws,
            // this connection is NEVER returned to the pool
            Statement stmt = conn.createStatement();

            // ❌ NO QUERY TIMEOUT: a slow query holds the thread + connection
            ResultSet rs = stmt.executeQuery(
                "SELECT name FROM users WHERE id = '" + userId + "'"
            );

            rs.next();

            // ❌ THE TRIGGER: rs.getString() returns null for a NULL column.
            // name.toUpperCase() throws NullPointerException.
            // The exception propagates up. The connection is never closed.
            // The thread dies. One thread gone. Repeat 50 times → system dead.
            String name = rs.getString("name");
            String upperName = name.toUpperCase();  // 💥 NPE if name is null

            return processUser(upperName);
        });
    }
}
```

**What happens step by step:**
1. `rs.getString("name")` returns `null` (unexpected `NULL` in database)
2. `name.toUpperCase()` throws `NullPointerException`
3. Exception propagates out of the lambda → thread dies
4. `Connection conn` is **never closed** → leaked from pool
5. Next request calls `dataSource.getConnection()` → one fewer connection available
6. After 20 NullPointerExceptions → **connection pool exhausted** (0 available)
7. All 50 threads now block on `getConnection()` → **thread pool exhausted**
8. New requests queue in `LinkedBlockingQueue` → **unbounded queue grows**
9. Health checks pass (process is alive) → **load balancer keeps sending traffic**
10. System is dead but looks alive → **silent death**

---

### ✅ Production Approach — What Chapter 2 Teaches

```java
import java.sql.*;
import java.util.Optional;
import java.util.concurrent.*;
import com.zaxxer.hikari.HikariConfig;
import com.zaxxer.hikari.HikariDataSource;
import io.github.resilience4j.circuitbreaker.CircuitBreaker;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * ✅ PRODUCTION REQUEST HANDLER — applies every lesson from Chapter 2.
 *
 * Defenses:
 * 1. Connection pool with timeouts (HikariCP)
 * 2. Query timeouts at statement level
 * 3. try-with-resources for guaranteed resource cleanup
 * 4. Null-safe data handling
 * 5. Bounded thread pool with rejection policy
 * 6. Circuit breaker to fail fast when DB is unhealthy
 * 7. Structured logging for observability
 */
public class ProductionRequestHandler {

    private static final Logger log = LoggerFactory.getLogger(ProductionRequestHandler.class);

    // staff-level: Bounded queue + CallerRunsPolicy creates natural backpressure.
    // When all threads are busy AND queue is full, the calling thread handles
    // the request itself. This slows down the caller (load balancer thread)
    // and naturally reduces incoming traffic rate.
    private final ExecutorService threadPool = new ThreadPoolExecutor(
        20,                              // core threads
        50,                              // max threads
        60, TimeUnit.SECONDS,            // idle timeout for non-core threads
        new ArrayBlockingQueue<>(100),   // BOUNDED queue — max 100 waiting
        new ThreadPoolExecutor.CallerRunsPolicy()  // backpressure: caller handles it
    );

    // staff-level: HikariCP is the gold standard for JDBC connection pooling.
    // Every timeout here is deliberate and tested against expected latencies.
    private final HikariDataSource dataSource;

    // staff-level: Circuit breaker prevents cascading into a known-dead dependency.
    // After 5 failures in 10 seconds → open circuit → fail fast for 30 seconds
    // → then allow one probe request to test recovery.
    private final CircuitBreaker circuitBreaker;

    public ProductionRequestHandler() {
        // ✅ TIMEOUT AT EVERY LAYER
        HikariConfig config = new HikariConfig();
        config.setJdbcUrl("jdbc:postgresql://localhost:5432/mydb");
        config.setMaximumPoolSize(20);          // staff-level: size = Tn × (Cm - 1) + 1
                                                  // where Tn = threads, Cm = simultaneous connections per thread
        config.setConnectionTimeout(3_000);     // 3s to get connection, then give up
        config.setIdleTimeout(600_000);         // 10 min idle before eviction
        config.setMaxLifetime(1_800_000);       // 30 min max lifetime — prevent stale connections
        config.setLeakDetectionThreshold(5_000); // alert if connection held > 5s — catches leaks in dev
        this.dataSource = new HikariDataSource(config);

        // ✅ CIRCUIT BREAKER configuration
        this.circuitBreaker = CircuitBreaker.ofDefaults("userService");
    }

    /**
     * ✅ Handle request with full defensive stack.
     *
     * Returns Optional.empty() on failure — never throws across boundary.
     * This is the key architectural insight: exceptions should not cross
     * service/module boundaries. Return result types instead.
     */
    public CompletableFuture<Optional<String>> handleRequest(String userId) {
        return CompletableFuture.supplyAsync(() ->
            // ✅ Circuit breaker wraps the entire operation
            circuitBreaker.executeSupplier(() -> fetchAndProcessUser(userId)),
            threadPool
        ).exceptionally(ex -> {
            // staff-level: exceptionally() catches EVERYTHING — including
            // circuit breaker rejections, thread pool rejections, and
            // unexpected exceptions. The caller always gets a result.
            log.error("Request failed for user {}: {}", userId, ex.getMessage());
            return Optional.empty();
        });
    }

    private Optional<String> fetchAndProcessUser(String userId) {
        // ✅ try-with-resources guarantees connection is ALWAYS returned to pool.
        // Even if NullPointerException or any other exception is thrown,
        // the connection is closed in the implicit finally block.
        try (Connection conn = dataSource.getConnection();
             PreparedStatement stmt = conn.prepareStatement(
                 "SELECT name FROM users WHERE id = ?")) {

            // ✅ QUERY TIMEOUT: prevents a slow query from holding thread + connection
            stmt.setQueryTimeout(5);  // 5 seconds max query execution

            // ✅ PARAMETERIZED QUERY: prevents SQL injection (not chapter 2 topic,
            // but a staff engineer would never use string concatenation)
            stmt.setString(1, userId);

            try (ResultSet rs = stmt.executeQuery()) {
                if (!rs.next()) {
                    log.warn("User not found: {}", userId);
                    return Optional.empty();
                }

                // ✅ NULL-SAFE: the exact fix for the chapter 2 trigger.
                // Optional.ofNullable handles NULL columns gracefully.
                String name = rs.getString("name");
                return Optional.ofNullable(name)
                    .map(String::toUpperCase)
                    .or(() -> {
                        log.warn("User {} has NULL name", userId);
                        return Optional.of("UNKNOWN");
                    });
            }
        } catch (SQLTimeoutException e) {
            // staff-level: Distinguish timeout from other SQL errors.
            // Timeouts suggest the dependency is overwhelmed — circuit breaker
            // should count this as a failure.
            log.error("Query timeout for user {}", userId, e);
            throw new RuntimeException("Database timeout", e);
        } catch (SQLException e) {
            log.error("Database error for user {}", userId, e);
            throw new RuntimeException("Database error", e);
        }
    }
}
```

---

## Example 2: The Cascade in Go — Goroutine Leak + Channel Deadlock

### ❌ Naive Approach — Goroutine Leak Cascade

```go
package main

import (
	"database/sql"
	"fmt"
	"log"
	"net/http"
	"strings"

	_ "github.com/lib/pq"
)

// ❌ NAIVE GO HANDLER — demonstrates how Go's concurrency can still cascade.
//
// Common misconception: "Go doesn't have thread pools, so we're safe."
// Reality: goroutines are cheap, but database connections, file descriptors,
// and memory are not. The cascade mechanic is identical.

var db *sql.DB

func init() {
	var err error
	// ❌ No connection pool limits set — defaults to unlimited connections.
	// In practice, the database has a connection limit (e.g., 100).
	// Go will happily open 10,000 goroutines, each trying to get a connection,
	// creating massive contention.
	db, err = sql.Open("postgres", "postgres://localhost/mydb?sslmode=disable")
	if err != nil {
		log.Fatal(err)
	}
}

func handleUser(w http.ResponseWriter, r *http.Request) {
	userID := r.URL.Query().Get("id")

	// ❌ NO CONTEXT/TIMEOUT: this query can block forever.
	// In Go, the idiomatic way to enforce timeouts is context.Context.
	// Without it, a slow query blocks the goroutine indefinitely.
	row := db.QueryRow("SELECT name FROM users WHERE id = $1", userID)

	var name string
	if err := row.Scan(&name); err != nil {
		// ❌ LEAKING GOROUTINE: if Scan fails, we still write to ResponseWriter.
		// But more importantly, if db.QueryRow blocks forever, this goroutine
		// is leaked. 10,000 leaked goroutines = 10,000 blocked connections.
		http.Error(w, "user not found", 500)
		return
	}

	// ❌ NO NULL CHECK: if name is empty string from NULL column,
	// strings.ToUpper works but returns empty — silent data corruption.
	fmt.Fprintf(w, "Hello, %s", strings.ToUpper(name))
}

func main() {
	http.HandleFunc("/user", handleUser)
	log.Fatal(http.ListenAndServe(":8080", nil))
}
```

### ✅ Production Approach — Context-Aware with Proper Pool Management

```go
package main

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"log/slog"
	"net/http"
	"os"
	"strings"
	"time"

	_ "github.com/lib/pq"
)

// ✅ PRODUCTION GO HANDLER — applies Chapter 2 lessons idiomatically.

var (
	db     *sql.DB
	logger *slog.Logger
)

func init() {
	logger = slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{
		Level: slog.LevelInfo,
	}))

	var err error
	db, err = sql.Open("postgres", "postgres://localhost/mydb?sslmode=disable")
	if err != nil {
		logger.Error("failed to open database", "error", err)
		os.Exit(1)
	}

	// ✅ CONNECTION POOL CONFIGURATION — the Go equivalent of HikariCP settings.
	// These prevent the cascade at the resource level.
	db.SetMaxOpenConns(25)              // staff-level: match to expected concurrency, not max
	db.SetMaxIdleConns(10)              // keep warm connections ready
	db.SetConnMaxLifetime(30 * time.Minute)  // prevent stale connections (TLS cert rotation, etc.)
	db.SetConnMaxIdleTime(5 * time.Minute)   // release idle connections back to system

	// ✅ VERIFY CONNECTION ON STARTUP — fail fast, don't discover in production
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	if err := db.PingContext(ctx); err != nil {
		logger.Error("database unreachable at startup", "error", err)
		os.Exit(1)
	}
}

// UserResponse is the typed response — never return raw strings in production APIs.
type UserResponse struct {
	Name   string `json:"name"`
	UserID string `json:"user_id"`
}

// ErrorResponse provides structured error information.
type ErrorResponse struct {
	Error   string `json:"error"`
	Code    string `json:"code"`
}

func handleUser(w http.ResponseWriter, r *http.Request) {
	// ✅ REQUEST-SCOPED TIMEOUT — the single most important defense.
	// Every request gets a hard deadline. If the DB is slow, the goroutine
	// cancels after 3 seconds and returns an error — never blocks forever.
	ctx, cancel := context.WithTimeout(r.Context(), 3*time.Second)
	defer cancel()

	userID := r.URL.Query().Get("id")
	if userID == "" {
		writeError(w, http.StatusBadRequest, "missing_id", "user ID required")
		return
	}

	// ✅ CONTEXT-AWARE QUERY — db.QueryRowContext respects the deadline.
	// When ctx expires, the query is cancelled at the database level too.
	// This frees both the goroutine AND the database connection.
	row := db.QueryRowContext(ctx, "SELECT name FROM users WHERE id = $1", userID)

	// ✅ sql.NullString handles NULL columns safely — the exact fix for Ch2 trigger.
	var name sql.NullString
	if err := row.Scan(&name); err != nil {
		if err == sql.ErrNoRows {
			writeError(w, http.StatusNotFound, "not_found",
				fmt.Sprintf("user %s not found", userID))
			return
		}

		// staff-level: Check if the error is a context timeout vs actual DB error.
		// This distinction matters for circuit breaker decisions.
		if ctx.Err() == context.DeadlineExceeded {
			logger.Warn("database query timeout",
				"user_id", userID,
				"timeout", "3s",
			)
			writeError(w, http.StatusGatewayTimeout, "timeout", "database query timed out")
			return
		}

		logger.Error("database query failed",
			"user_id", userID,
			"error", err,
		)
		writeError(w, http.StatusInternalServerError, "db_error", "internal error")
		return
	}

	// ✅ NULL-SAFE PROCESSING with explicit handling
	displayName := "UNKNOWN"
	if name.Valid && name.String != "" {
		displayName = strings.ToUpper(name.String)
	} else {
		logger.Warn("user has NULL or empty name",
			"user_id", userID,
		)
	}

	// ✅ STRUCTURED RESPONSE — typed, not ad-hoc strings
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(UserResponse{
		Name:   displayName,
		UserID: userID,
	})
}

func writeError(w http.ResponseWriter, status int, code, msg string) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(ErrorResponse{
		Error: msg,
		Code:  code,
	})
}

func main() {
	mux := http.NewServeMux()
	mux.HandleFunc("/user", handleUser)

	// ✅ SERVER-LEVEL TIMEOUTS — defense in depth
	server := &http.Server{
		Addr:         ":8080",
		Handler:      mux,
		ReadTimeout:  5 * time.Second,   // max time to read request
		WriteTimeout: 10 * time.Second,  // max time to write response
		IdleTimeout:  120 * time.Second, // keep-alive timeout
	}

	logger.Info("server starting", "addr", server.Addr)
	if err := server.ListenAndServe(); err != nil {
		logger.Error("server failed", "error", err)
		os.Exit(1)
	}
}
```

---

## Side-by-Side Comparison

| Aspect | ❌ Naive | ✅ Production |
|---|---|---|
| **Connection timeout** | None (blocks forever) | 3s (context deadline) |
| **Query timeout** | None | 5s (statement-level) |
| **Connection pool** | Unbounded / no limit | Sized to concurrency, with max lifetime |
| **Null handling** | `NullPointerException` / empty string | `Optional` / `sql.NullString` |
| **Resource cleanup** | Relies on GC / happy path | `try-with-resources` / `defer cancel()` |
| **Thread/goroutine control** | Unbounded queue | Bounded queue + backpressure |
| **Error propagation** | Exception crosses boundaries | Result types (`Optional`, typed errors) |
| **Observability** | `System.out.println` | Structured logging with context |
| **Circuit breaking** | Keeps hitting dead dependency | Fails fast after threshold |

---

[← Previous: Section 2](./section_02_visual_architecture.md) | [Next: Section 4 — Database Angle →](./section_04_database_angle.md)
