# Section 7: Step-by-Step Code Lab

```
🧪 Lab: Reproducing & Fixing the Chapter 2 Cascade
🎯 Goal: Build a system that cascades from a single exception, observe it,
         then apply Chapter 2 fixes and verify they work
⏱ Time: ~25 mins
🛠 Requirements: Go 1.21+, Docker (for PostgreSQL), curl or hey (HTTP load tool)
```

---

## Step 1: Setup — Start PostgreSQL and Create Schema

```bash
# Start PostgreSQL in Docker
docker run --name cascade-lab -d \
  -e POSTGRES_DB=cascade_lab \
  -e POSTGRES_USER=lab \
  -e POSTGRES_PASSWORD=lab \
  -p 5432:5432 \
  postgres:16

# Wait for postgres to be ready
sleep 3

# Create the table and insert test data — including the NULL trigger
docker exec -i cascade-lab psql -U lab -d cascade_lab <<'SQL'
CREATE TABLE users (
    id    TEXT PRIMARY KEY,
    name  TEXT  -- NOTE: nullable! This is the Chapter 2 trigger.
);

-- Normal users
INSERT INTO users (id, name) VALUES ('user-1', 'Alice');
INSERT INTO users (id, name) VALUES ('user-2', 'Bob');
INSERT INTO users (id, name) VALUES ('user-3', 'Charlie');

-- 💥 THE TRIGGER: user with NULL name — exactly like Chapter 2
INSERT INTO users (id, name) VALUES ('user-null', NULL);

-- Verify
SELECT * FROM users;
SQL
```

**Expected output:**
```
    id     |  name
-----------+---------
 user-1    | Alice
 user-2    | Bob
 user-3   | Charlie
 user-null |          ← NULL name
(4 rows)
```

---

## Step 2: Implement the Naive Server (Vulnerable to Cascade)

Create `naive_server.go`:

```go
package main

import (
	"database/sql"
	"fmt"
	"log"
	"net/http"
	"strings"
	"sync/atomic"

	_ "github.com/lib/pq"
)

var (
	db             *sql.DB
	requestCount   int64
	errorCount     int64
	activeRequests int64
)

func main() {
	var err error
	db, err = sql.Open("postgres",
		"postgres://lab:lab@localhost:5432/cascade_lab?sslmode=disable")
	if err != nil {
		log.Fatal(err)
	}

	// ❌ DELIBERATE VULNERABILITY: Small pool to make cascade visible quickly.
	// In production, this might be 20-50, but the mechanic is identical.
	db.SetMaxOpenConns(5)
	db.SetMaxIdleConns(2)
	// ❌ NO connection timeout set — getConnection() blocks forever

	http.HandleFunc("/user", handleUser)
	http.HandleFunc("/stats", handleStats)

	log.Println("🚀 Naive server starting on :8080")
	log.Println("Try: curl http://localhost:8080/user?id=user-1")
	log.Println("Trigger cascade: curl http://localhost:8080/user?id=user-null")
	log.Fatal(http.ListenAndServe(":8080", nil))
}

func handleUser(w http.ResponseWriter, r *http.Request) {
	atomic.AddInt64(&requestCount, 1)
	atomic.AddInt64(&activeRequests, 1)
	defer atomic.AddInt64(&activeRequests, -1)

	userID := r.URL.Query().Get("id")

	// ❌ NO CONTEXT/TIMEOUT: blocks forever if DB is slow
	row := db.QueryRow("SELECT name FROM users WHERE id = $1", userID)

	var name string
	if err := row.Scan(&name); err != nil {
		atomic.AddInt64(&errorCount, 1)
		http.Error(w, fmt.Sprintf("error: %v", err), 500)
		return
	}

	// ❌ THE TRIGGER: if name is NULL, Scan puts empty string.
	// strings.ToUpper("") works, but what if we had a method that
	// does name[0:1]? → panic! Let's simulate with explicit nil check.
	if name == "" {
		// Simulate the NullPointerException equivalent:
		// In real code, this might be name.SomeMethod() on a nil pointer.
		panic("unexpected empty name — simulating NullPointerException")
	}

	fmt.Fprintf(w, `{"name": "%s"}`, strings.ToUpper(name))
}

func handleStats(w http.ResponseWriter, r *http.Request) {
	stats := db.Stats()
	fmt.Fprintf(w, `{
  "requests_total": %d,
  "errors_total": %d,
  "active_requests": %d,
  "db_open_connections": %d,
  "db_in_use": %d,
  "db_idle": %d,
  "db_wait_count": %d,
  "db_wait_duration_ms": %d
}`,
		atomic.LoadInt64(&requestCount),
		atomic.LoadInt64(&errorCount),
		atomic.LoadInt64(&activeRequests),
		stats.OpenConnections,
		stats.InUse,
		stats.Idle,
		stats.WaitCount,
		stats.WaitDuration.Milliseconds(),
	)
}
```

**Run it:**
```bash
go run naive_server.go
```

---

## Step 3: Observe Normal Behavior

```bash
# Test with valid users — should work fine
curl http://localhost:8080/user?id=user-1
# {"name": "ALICE"}

curl http://localhost:8080/user?id=user-2
# {"name": "BOB"}

# Check stats — everything healthy
curl -s http://localhost:8080/stats | jq .
# {
#   "requests_total": 2,
#   "errors_total": 0,
#   "active_requests": 0,
#   "db_open_connections": 2,
#   "db_in_use": 0,
#   "db_idle": 2,
#   "db_wait_count": 0,
#   "db_wait_duration_ms": 0
# }
```

---

## Step 4: Trigger the Cascade

```bash
# 💥 Hit the NULL user — this triggers the panic
curl http://localhost:8080/user?id=user-null
# Connection will be reset (server panics on that goroutine)

# The panic is recovered by net/http, but the pattern is clear.
# Now simulate load — 50 concurrent requests, mix of good and bad:

# Install hey (HTTP load tester): go install github.com/rakyll/hey@latest
# Or use: apt install hey / brew install hey

# Send 200 requests, 50 concurrent, mix of user-1 and user-null
hey -n 200 -c 50 "http://localhost:8080/user?id=user-1" &
hey -n 50 -c 10 "http://localhost:8080/user?id=user-null" &
wait

# Check stats after the load:
curl -s http://localhost:8080/stats | jq .
```

**Expected observation:**
- Success rate drops for ALL requests (even `user-1`) when `user-null` panics are occurring
- `db_wait_count` increases — requests are waiting for connections
- `active_requests` spikes — requests are stuck
- Even though the "bad" requests are only 20% of traffic, they degrade the entire system

---

## Step 5: Implement the Production Server (With Chapter 2 Fixes)

Create `production_server.go`:

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
	"sync/atomic"
	"time"

	_ "github.com/lib/pq"
)

var (
	db             *sql.DB
	logger         *slog.Logger
	requestCount   int64
	errorCount     int64
	successCount   int64
	timeoutCount   int64
	activeRequests int64
)

func main() {
	logger = slog.New(slog.NewJSONHandler(os.Stdout, nil))

	var err error
	db, err = sql.Open("postgres",
		"postgres://lab:lab@localhost:5432/cascade_lab?sslmode=disable")
	if err != nil {
		logger.Error("failed to open database", "error", err)
		os.Exit(1)
	}

	// ✅ FIX 1: Connection pool with proper limits
	db.SetMaxOpenConns(5)
	db.SetMaxIdleConns(2)
	db.SetConnMaxLifetime(30 * time.Minute)
	db.SetConnMaxIdleTime(5 * time.Minute)

	// ✅ FIX 2: Verify database connectivity on startup
	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	defer cancel()
	if err := db.PingContext(ctx); err != nil {
		logger.Error("database unreachable", "error", err)
		os.Exit(1)
	}

	mux := http.NewServeMux()
	mux.HandleFunc("/user", handleUser)
	mux.HandleFunc("/stats", handleStats)
	mux.HandleFunc("/health", handleHealth)

	// ✅ FIX 3: Server-level timeouts
	server := &http.Server{
		Addr:         ":8081",
		Handler:      mux,
		ReadTimeout:  5 * time.Second,
		WriteTimeout: 10 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	logger.Info("production server starting", "addr", ":8081")
	if err := server.ListenAndServe(); err != nil {
		logger.Error("server failed", "error", err)
	}
}

type Response struct {
	Name   string `json:"name,omitempty"`
	UserID string `json:"user_id,omitempty"`
	Error  string `json:"error,omitempty"`
}

func handleUser(w http.ResponseWriter, r *http.Request) {
	atomic.AddInt64(&requestCount, 1)
	atomic.AddInt64(&activeRequests, 1)
	defer atomic.AddInt64(&activeRequests, -1)

	userID := r.URL.Query().Get("id")
	if userID == "" {
		writeJSON(w, http.StatusBadRequest, Response{Error: "missing user ID"})
		atomic.AddInt64(&errorCount, 1)
		return
	}

	// ✅ FIX 4: Request-scoped timeout — the MOST important fix.
	// This ensures the goroutine + connection are released after 2 seconds,
	// no matter what happens.
	ctx, cancel := context.WithTimeout(r.Context(), 2*time.Second)
	defer cancel()

	// ✅ FIX 5: Use QueryRowContext — respects the deadline
	row := db.QueryRowContext(ctx,
		"SELECT COALESCE(name, '') FROM users WHERE id = $1", userID)

	var name sql.NullString
	if err := row.Scan(&name); err != nil {
		if err == sql.ErrNoRows {
			writeJSON(w, http.StatusNotFound, Response{Error: "user not found"})
			atomic.AddInt64(&errorCount, 1)
			return
		}
		if ctx.Err() == context.DeadlineExceeded {
			atomic.AddInt64(&timeoutCount, 1)
			logger.Warn("query timeout", "user_id", userID)
			writeJSON(w, http.StatusGatewayTimeout, Response{Error: "timeout"})
			return
		}
		atomic.AddInt64(&errorCount, 1)
		logger.Error("query failed", "user_id", userID, "error", err)
		writeJSON(w, http.StatusInternalServerError, Response{Error: "internal error"})
		return
	}

	// ✅ FIX 6: NULL-safe handling — no panic, no crash, graceful default
	displayName := "UNKNOWN"
	if name.Valid && name.String != "" {
		displayName = strings.ToUpper(name.String)
	} else {
		logger.Warn("user has null/empty name", "user_id", userID)
	}

	atomic.AddInt64(&successCount, 1)
	writeJSON(w, http.StatusOK, Response{Name: displayName, UserID: userID})
}

// ✅ FIX 7: Deep health check — verifies database connectivity
func handleHealth(w http.ResponseWriter, r *http.Request) {
	ctx, cancel := context.WithTimeout(r.Context(), 1*time.Second)
	defer cancel()

	if err := db.PingContext(ctx); err != nil {
		w.WriteHeader(http.StatusServiceUnavailable)
		fmt.Fprintf(w, `{"status": "unhealthy", "error": "%s"}`, err.Error())
		return
	}

	stats := db.Stats()
	if stats.InUse >= stats.MaxOpenConnections {
		w.WriteHeader(http.StatusServiceUnavailable)
		fmt.Fprintf(w, `{"status": "unhealthy", "reason": "connection pool exhausted"}`)
		return
	}

	fmt.Fprintf(w, `{"status": "healthy"}`)
}

func handleStats(w http.ResponseWriter, r *http.Request) {
	stats := db.Stats()
	fmt.Fprintf(w, `{
  "requests_total": %d,
  "success_total": %d,
  "errors_total": %d,
  "timeouts_total": %d,
  "active_requests": %d,
  "db_max_connections": %d,
  "db_open_connections": %d,
  "db_in_use": %d,
  "db_idle": %d,
  "db_wait_count": %d,
  "db_wait_duration_ms": %d
}`,
		atomic.LoadInt64(&requestCount),
		atomic.LoadInt64(&successCount),
		atomic.LoadInt64(&errorCount),
		atomic.LoadInt64(&timeoutCount),
		atomic.LoadInt64(&activeRequests),
		stats.MaxOpenConnections,
		stats.OpenConnections,
		stats.InUse,
		stats.Idle,
		stats.WaitCount,
		stats.WaitDuration.Milliseconds(),
	)
}

func writeJSON(w http.ResponseWriter, status int, resp Response) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(resp)
}
```

**Run it:**
```bash
go run production_server.go
```

---

## Step 5: Compare & Measure

```bash
# Test the production server with the same load
# First, verify normal behavior:
curl http://localhost:8081/user?id=user-1
# {"name":"ALICE","user_id":"user-1"}

# Test the NULL user — should return gracefully, NOT crash
curl http://localhost:8081/user?id=user-null
# {"name":"UNKNOWN","user_id":"user-null"}  ← Graceful degradation!

# Load test — same mix as before
hey -n 200 -c 50 "http://localhost:8081/user?id=user-1" &
hey -n 50 -c 10 "http://localhost:8081/user?id=user-null" &
wait

# Compare stats
curl -s http://localhost:8081/stats | jq .

# Health check — actually verifies database connectivity
curl http://localhost:8081/health
# {"status": "healthy"}
```

**Expected results:**
| Metric | Naive Server | Production Server |
|---|---|---|
| Success rate (user-1) | ~80% (degraded by user-null panics) | 100% |
| user-null response | Connection reset (panic) | `{"name":"UNKNOWN"}` (200 OK) |
| db_wait_count | High (requests queuing) | Low (timeouts release connections) |
| Recovery after load | May need restart | Self-recovers immediately |

---

## Step 6: Stretch Challenge (Staff-Level Extension)

### Challenge: Add a Simulated Slow Database

Modify the PostgreSQL configuration to add artificial latency, simulating the "slow dependency" cascade:

```sql
-- Connect to the database
docker exec -it cascade-lab psql -U lab -d cascade_lab

-- Create a function that simulates slow queries
CREATE OR REPLACE FUNCTION slow_lookup(uid TEXT)
RETURNS TEXT AS $$
BEGIN
    -- Simulate a slow database by sleeping 10 seconds
    PERFORM pg_sleep(10);
    RETURN (SELECT name FROM users WHERE id = uid);
END;
$$ LANGUAGE plpgsql;
```

Now test:
- **Naive server**: All requests will block for 10s → thread pool exhausts → cascade
- **Production server**: Requests timeout after 2s → fast failure → other requests succeed

```bash
# Create a view that simulates slow queries
docker exec -i cascade-lab psql -U lab -d cascade_lab <<'SQL'
CREATE OR REPLACE VIEW slow_users AS
SELECT id, name, pg_sleep(10) FROM users;
SQL

# Now benchmark both servers and compare how they handle slow queries.
# The production server should timeout and return errors within 2 seconds.
# The naive server may block goroutines for the full 10 seconds.
```

### Challenge Questions:
1. What happens if you increase the connection pool to 50 on the naive server? Does it fix the cascade, or just delay it?
2. What timeout value would you set if your SLA requires p99 < 500ms?
3. How would you add a circuit breaker that opens after 5 timeouts in 10 seconds?

---

## Cleanup

```bash
docker stop cascade-lab && docker rm cascade-lab
```

---

[← Previous: Section 6](./section_06_leverage_multipliers.md) | [Next: Section 8 — Case Study →](./section_08_case_study.md)
