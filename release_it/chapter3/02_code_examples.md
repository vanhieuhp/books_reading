# Annotated Code Examples — Stability Anti-Patterns

This section provides **production-grade code examples** in both **Go** (preferred for systems/concurrency topics) demonstrating how the anti-patterns manifest and how to fix them.

---

## Example 1: Integration Points — Missing Timeouts

### The Naive Approach (What Most Developers Do)

```go
// ❌ NAIVE: No timeout on database call
// Why this is dangerous:
// - If the database hangs, the thread blocks forever
// - Connection pool fills up
// - Cascading failure begins

func GetUserNaive(userID string) (*User, error) {
    // staff-level: This looks innocent but is a silent killer
    // There is NO timeout here - the call can block indefinitely
    row := db.QueryRow("SELECT id, name, email FROM users WHERE id = ?", userID)

    var user User
    err := row.Scan(&user.ID, &user.Name, &user.Email)
    if err != nil {
        return nil, err
    }
    return &user, nil
}
```

### Production-Grade Approach

```go
// ✅ PRODUCTION: Timeout on every external call
// Why this is correct:
// - Context with timeout ensures call fails fast
// - Resources are released quickly on failure
// - Prevents cascading failures from slow integration points

import (
    "context"
    "time"
)

func GetUserProduction(ctx context.Context, userID string) (*User, error) {
    // staff-level: Always wrap external calls with timeout context
    // Even if caller passes context, enforce a maximum wait time
    ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
    defer cancel()

    // staff-level: Pass context to driver - this is CRITICAL
    // The driver will respect context timeout and cancel the query
    row := db.QueryRowContext(ctx,
        "SELECT id, name, email FROM users WHERE id = ?", userID)

    var user User
    err := row.Scan(&user.ID, &user.Name, &user.Email)
    if err != nil {
        // staff-level: Distinguish between timeout and other errors
        if ctx.Err() == context.DeadlineExceeded {
            return nil, fmt.Errorf("database timeout for user %s: %w", userID, err)
        }
        return nil, err
    }
    return &user, nil
}
```

---

## Example 2: Resource Exhaustion — Connection Pool Misconfiguration

### The Naive Approach

```python
# ❌ NAIVE: No pool limits, unbounded connections
# Why this is dangerous:
# - Connections can grow indefinitely
# - Database gets overwhelmed
# - No backpressure mechanism

import psycopg2

def get_connection_naive():
    # staff-level: Every call creates a new connection
    # Under load, this explodes - you'll have thousands of connections
    conn = psycopg2.connect(
        host="db.example.com",
        database="users",
        user="app",
        password="password"
    )
    return conn

def fetch_users_naive(user_ids):
    conn = get_connection_naive()  # New connection every time
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ANY(%s)", (user_ids,))
    results = cursor.fetchall()
    cursor.close()
    conn.close()  # Hope this executes before the next call...
    return results
```

### Production-Grade Approach

```python
# ✅ PRODUCTION: Connection pool with proper limits
# Why this is correct:
# - Bounded pool prevents resource exhaustion
# - Connection reuse reduces overhead
# - Backpressure when pool is exhausted

import psycopg2
from psycopg2 import pool
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

class DatabasePool:
    """Staff-level: Production-grade connection pool management"""

    def __init__(self, min_conn=5, max_conn=20):
        # staff-level: Set explicit limits
        # - min_conn: Always maintain these for latency-sensitive ops
        # - max_conn: Hard limit prevents overwhelming the database
        self.pool = pool.ThreadedConnectionPool(
            minconn=min_conn,
            maxconn=max_conn,
            host="db.example.com",
            database="users",
            user="app",
            password="password",
            # staff-level: Additional safety settings
            connect_timeout=5,
            options="-c statement_timeout=5000"  # 5 second query timeout
        )
        logger.info(f"Connection pool initialized: {min_conn}-{max_conn} connections")

    @contextmanager
    def get_connection(self):
        """Context manager ensures connections return to pool"""
        conn = None
        try:
            conn = self.pool.getconn()
            # staff-level: Verify connection is alive before use
            # A connection might have timed out while idle
            if conn.closed:
                logger.warning("Reconnecting - pool connection was closed")
                conn = self.pool.getconn()
            yield conn
        except pool.pool_exhausted:
            # staff-level: Handle pool exhaustion gracefully
            # This is backpressure - the caller should retry later
            logger.error("Connection pool exhausted - applying backpressure")
            raise
        finally:
            if conn:
                self.pool.putconn(conn)  # Always return to pool

# Usage
db_pool = DatabasePool(min_conn=5, max_conn=20)

def fetch_users_production(user_ids):
    with db_pool.get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE id = ANY(%s)", (user_ids,))
            return cursor.fetchall()
```

---

## Example 3: Cascading Failures — Retry Without Backoff

### The Naive Approach

```go
// ❌ NAIVE: Aggressive retries without backoff
// Why this is dangerous:
// - Thundering herd: all clients retry at once
// - Overwhelms recovering service
// - Can turn a brief blip into a full outage

func CallServiceNaive(ctx context.Context, url string) ([]byte, error) {
    // staff-level: This is the DEFAULT behavior in many HTTP clients
    // and it's catastrophic under load
    client := &http.Client{}

    // staff-level: No timeout means this can hang forever
    // (We won't even demonstrate this antipattern fully)

    // No retry logic? Let's add "simple" retries:
    for i := 0; i < 3; i++ {
        resp, err := client.Get(url)
        if err == nil {
            defer resp.Body.Close()
            if resp.StatusCode == http.StatusOK {
                return io.ReadAll(resp.Body)
            }
        }
        // staff-level: IMMEDIATE RETRY - the worst possible choice
        // If service is recovering, this pushes it back down
    }

    return nil, fmt.Errorf("service unavailable after 3 attempts")
}
```

### Production-Grade Approach

```go
// ✅ PRODUCTION: Exponential backoff with jitter
// Why this is correct:
// - Exponential backoff: each retry waits longer
// - Jitter: randomizes timing to break synchronization
// - Circuit breaker: stops calling when service is down

import (
    "math"
    "math/rand"
    "time"
)

type RetryConfig struct {
    MaxRetries     int
    InitialDelay   time.Duration
    MaxDelay       time.Duration
    JitterFactor   float64 // 0.0 - 1.0
}

func withRetry(ctx context.Context, config RetryConfig, fn func() error) error {
    var lastErr error

    for attempt := 0; attempt <= config.MaxRetries; attempt++ {
        err := fn()
        if err == nil {
            return nil // Success
        }

        lastErr = err

        // Don't retry on final attempt
        if attempt == config.MaxRetries {
            break
        }

        // Calculate delay with exponential backoff + jitter
        delay := config.InitialDelay * time.Duration(math.Pow(2, float64(attempt)))
        delay = min(delay, config.MaxDelay)

        // staff-level: JITTER is critical
        // Without jitter, all clients retry at the same time (thundering herd)
        // Full jitter: random value between 0 and delay
        jitter := time.Duration(rand.Float64() * float64(delay*config.JitterFactor))
        delay = delay - jitter + time.Duration(rand.Float64()*float64(jitter))

        // Wait with context cancellation support
        select {
        case <-time.After(delay):
            // Continue to next attempt
        case <-ctx.Done():
            return ctx.Err()
        }
    }

    return lastErr
}

// Usage with circuit breaker
func CallServiceProduction(ctx context.Context, url string) ([]byte, error) {
    // staff-level: Use circuit breaker to fail fast when service is down
    // This prevents calling a failing service repeatedly
    if !circuitBreaker.CanProceed() {
        return nil, fmt.Errorf("circuit breaker open - service unavailable")
    }

    return nil, withRetry(ctx, RetryConfig{
        MaxRetries:   3,
        InitialDelay: 100 * time.Millisecond,
        MaxDelay:     5 * time.Second,
        JitterFactor: 0.5,
    }, func() error {
        resp, err := http.Get(url)
        if err != nil {
            return err
        }
        defer resp.Body.Close()

        if resp.StatusCode >= 500 {
            // staff-level: Only retry on server errors, not client errors
            return fmt.Errorf("server error: %d", resp.StatusCode)
        }
        return nil
    })
}
```

---

## Example 4: Bulkhead Pattern — Isolating Resources

### The Naive Approach

```python
# ❌ NAIVE: Single shared thread pool for all operations
# Why this is dangerous:
# - Slow operation A blocks fast operation B
# - One bad dependency takes down everything

from concurrent.futures import ThreadPoolExecutor

# staff-level: ONE pool for everything - the classic mistake
shared_executor = ThreadPoolExecutor(max_workers=100)

def process_order(order_id):
    # Calls slow service
    user = shared_executor.submit(get_user, order_id.user_id).result()
    # Calls slow service
    inventory = shared_executor.submit(check_inventory, order_id.items).result()
    # Calls slow service
    shipping = shared_executor.submit(get_shipping, order_id.address).result()

    return combine_results(user, inventory, shipping)

def get_user(user_id):
    # This might hang for 30 seconds
    return external_user_service.get(user_id)  # No timeout!

# staff-level: If get_user hangs, all 100 threads are blocked
# Now get_inventory and get_shipping can't run either
# Entire service is frozen
```

### Production-Grade Approach

```python
# ✅ PRODUCTION: Bulkhead pattern - separate pools for different operations
# Why this is correct:
// - Slow user service doesn't block inventory service
// - Each operation has guaranteed minimum resources
// - Failure is contained to one bulkhead

from concurrent.futures import ThreadPoolExecutor
import threading

class BulkheadPool:
    """Staff-level: Bulkhead pattern implementation"""

    def __init__(self, max_workers, pool_name):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.pool_name = pool_name
        self.active_count = 0
        self._lock = threading.Lock()

    def submit(self, fn, *args, **kwargs):
        with self._lock:
            if self.active_count >= self.executor._max_workers:
                # staff-level: Bulkhead is full - fail fast
                # This is backpressure, not waiting in queue
                raise BulkheadFullException(
                    f"Bulkhead '{self.pool_name}' exhausted"
                )
            self.active_count += 1

        # Submit with callback to track completion
        future = self.executor.submit(fn, *args, **kwargs)
        future.add_done_callback(self._release)

        return future

    def _release(self, _):
        with self._lock:
            self.active_count -= 1


class BulkheadFullException(Exception):
    """Raised when bulkhead cannot accept more work"""
    pass


# staff-level: Separate pools for different dependencies
# Each has different size based on criticality and expected load
user_bulkhead = BulkheadPool(max_workers=10, pool_name="user-service")
inventory_bulkhead = BulkheadPool(max_workers=20, pool_name="inventory-service")
shipping_bulkhead = BulkheadPool(max_workers=5, pool_name="shipping-service")


def process_order_bulkhead(order_id):
    # staff-level: Each operation uses its own bulkhead
    # If user service is slow, it doesn't affect inventory or shipping

    user_future = user_bulkhead.submit(get_user_with_timeout, order_id.user_id)
    inventory_future = inventory_bulkhead.submit(check_inventory_with_timeout, order_id.items)
    shipping_future = shipping_bulkhead.submit(get_shipping_with_timeout, order_id.address)

    # Wait for all with overall timeout
    # This prevents one slow dependency from blocking forever
    try:
        user = user_future.result(timeout=2.0)
        inventory = inventory_future.result(timeout=1.0)
        shipping = shipping_future.result(timeout=1.0)
    except TimeoutError as e:
        # staff-level: Fail fast - we know which dependency failed
        logger.error(f"Order processing timeout: {e}")
        raise
    except BulkheadFullException as e:
        # staff-level: Backpressure - don't accept more work
        logger.error(f"Backpressure applied: {e}")
        raise

    return combine_results(user, inventory, shipping)


def get_user_with_timeout(user_id):
    # Use context with timeout
    return user_service.get_user(user_id)  # Should have its own timeout
```

---

## Example 5: Circuit Breaker — Preventing Cascading Failures

### Go Implementation

```go
// ✅ PRODUCTION: Circuit breaker pattern
// Why this is correct:
// - Fails fast when downstream is down
// - Gives downstream time to recover
// - Prevents resource exhaustion from repeated calls

import (
    "errors"
    "sync"
    "time"
)

type CircuitState int

const (
    StateClosed CircuitState = iota  // Normal operation
    StateOpen                         // Failing - reject calls
    StateHalfOpen                     // Testing if recovery possible
)

type CircuitBreaker struct {
    mu             sync.Mutex
    state          CircuitState
    failureCount   int
    successCount   int
    lastFailure    time.Time

    // Configuration
    failureThreshold int           // Failures before opening
    successThreshold int           // Successes to close from half-open
    timeout          time.Duration // Time in open state before trying half-open

    // Metrics
    totalRequests  int64
    rejectedCalls  int64
}

func NewCircuitBreaker(failureThreshold int, timeout time.Duration) *CircuitBreaker {
    return &CircuitBreaker{
        state:            StateClosed,
        failureThreshold: failureThreshold,
        timeout:          timeout,
        successThreshold: 3, // Need 3 successes to close
    }
}

// staff-level: Thread-safe state check
func (cb *CircuitBreaker) CanProceed() bool {
    cb.mu.Lock()
    defer cb.mu.Unlock()

    switch cb.state {
    case StateClosed:
        return true

    case StateOpen:
        // staff-level: Check if we've waited long enough to try again
        // This is "half-open" - allow some requests through to test
        if time.Since(cb.lastFailure) > cb.timeout {
            cb.state = StateHalfOpen
            cb.successCount = 0
            return true
        }
        return false

    case StateHalfOpen:
        // staff-level: Allow limited requests to test recovery
        return true
    }

    return false
}

func (cb *CircuitBreaker) Execute(fn func() error) error {
    if !cb.CanProceed() {
        cb.mu.Lock()
        cb.rejectedCalls++
        cb.mu.Unlock()
        return errors.New("circuit breaker open - call rejected")
    }

    cb.mu.Lock()
    cb.totalRequests++
    cb.mu.Unlock()

    // Execute the protected call
    err := fn()

    cb.mu.Lock()
    defer cb.mu.Unlock()

    if err != nil {
        // Call failed
        cb.failureCount++
        cb.lastFailure = time.Now()

        // staff-level: Open the circuit after threshold failures
        if cb.failureCount >= cb.failureThreshold {
            cb.state = StateOpen
        }
        return err
    }

    // Call succeeded
    if cb.state == StateHalfOpen {
        cb.successCount++
        // staff-level: Close circuit after enough successes
        if cb.successCount >= cb.successThreshold {
            cb.state = StateClosed
            cb.failureCount = 0
        }
    } else {
        // In closed state, reset failure count on success
        cb.failureCount = 0
    }

    return nil
}
```

---

## Summary: Key Code Patterns

| Anti-Pattern | Naive Code | Production Code |
|--------------|-----------|-----------------|
| Integration Points | No timeout | `context.WithTimeout()` |
| Resource Exhaustion | Unlimited connections | Bounded pool + backpressure |
| Cascading Failures | Aggressive retries | Exponential backoff + jitter + circuit breaker |
| Bulkheads | Shared thread pool | Separate pools per dependency |
| Slow Responses | Infinite wait | Timeout on every call |

---

*Continue to Section 5: Real-World Use Cases*
