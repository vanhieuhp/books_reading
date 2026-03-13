# Section 7: Step-by-Step Code Lab

## Lab: Building a Resilient Load Shedding Proxy

---

## 🧪 Lab: Load Shedding Proxy

### 🎯 Goal
Build a Go-based load shedding proxy that:
1. Accepts HTTP requests
2. Limits concurrent requests (semaphore)
3. Queues excess requests with timeout
4. Rejects when queue is full (load shedding)
5. Implements circuit breaker for downstream calls
6. Handles retries with exponential backoff + jitter

### ⏱ Time: ~25 minutes

### 🛠 Requirements
- Go 1.18+ installed
- Terminal/command line
- `hey` or `wrk` for load testing (optional)

---

## Step 1: Project Setup

Create a new Go project:

```bash
mkdir load_shedder
cd load_shedder
go mod init github.com/yourname/load_shedder
```

### Expected Output
```
go: creating new go.mod: module github.com/yourname/load_shedder
```

---

## Step 2: Implement Core Types

Create `types.go`:

```go
package main

import (
	"context"
	"math"
	"math/rand"
	"sync"
	"sync/atomic"
	"time"
)

// Config holds all tunable parameters
type Config struct {
	MaxConcurrentRequests int           // Semaphore limit
	QueueSize           int           // Request queue size
	QueueTimeout        time.Duration // Max wait in queue
	MaxRetries         int           // Retry attempts
	InitialBackoff     time.Duration // Starting backoff
	MaxBackoff         time.Duration // Max backoff
	JitterFactor       float64       // Randomization (0-1)
}

// Default configuration
var defaultConfig = Config{
	MaxConcurrentRequests: 50,
	QueueSize:             20,
	QueueTimeout:          500 * time.Millisecond,
	MaxRetries:            3,
	InitialBackoff:        100 * time.Millisecond,
	MaxBackoff:            5 * time.Second,
	JitterFactor:          0.3,
}

// Request represents an incoming HTTP request
type Request struct {
	ID        string
	Context   context.Context
	StartTime time.Time
	Result    chan Result
}

// Result holds the outcome of request processing
type Result struct {
	Accepted bool
	Err      error
}

// Metrics tracks system health
type Metrics struct {
	Received   int64
	Accepted   int64
	Rejected   int64
	Succeeded  int64
	Failed     int64
	QueueWait  int64
	ProcessDur int64
}

var metrics Metrics
```

### Expected Behavior
- Config struct allows tuning without code changes
- Metrics use atomic operations for lock-free updates

---

## Step 3: Implement Load Shedder

Create `shedder.go`:

```go
package main

import (
	"context"
	"log"
	"sync"
	"sync/atomic"
	"time"
)

// LoadShedder manages request admission
type LoadShedder struct {
	config   Config
	sem      chan struct{}     // Concurrency limit
	queue    chan Request     // Request queue
	mu       sync.RWMutex
	shutdown bool
}

func NewLoadShedder(cfg Config) *LoadShedder {
	return &LoadShedder{
		config: cfg,
		sem:    make(chan struct{}, cfg.MaxConcurrentRequests),
		queue:  make(chan Request, cfg.QueueSize),
	}
}

// TryAccept attempts to admit a request
// Returns true if accepted, false if rejected (load shed)
func (ls *LoadShedder) TryAccept(req Request) bool {
	atomic.AddInt64(&metrics.Received, 1)

	select {
	case ls.sem <- struct{}{}:
		// Got semaphore - process immediately
		atomic.AddInt64(&metrics.Accepted, 1)
		return true
	default:
		// At capacity, try queue
	}

	select {
	case ls.queue <- req:
		atomic.AddInt64(&metrics.Accepted, 1)
		return true
	case <-time.After(ls.config.QueueTimeout):
		// Queue timeout - reject
		atomic.AddInt64(&metrics.Rejected, 1)
		return false
	case <-ls.shuttingDown():
		atomic.AddInt64(&metrics.Rejected, 1)
		return false
	}
}

// Release returns a concurrency slot
func (ls *LoadShedder) Release() {
	select {
	case <-ls.sem:
		// Successfully released
	default:
		// Wasn't holding a slot
	}
}

// ProcessQueue handles queued requests
// Call this in a goroutine
func (ls *LoadShedder) ProcessQueue(handler func(Request)) {
	for req := range ls.queue {
		waitTime := time.Since(req.StartTime)
		atomic.AddInt64(&metrics.QueueWait, waitTime.Nanoseconds())
		handler(req)
	}
}

func (ls *LoadShedder) shuttingDown() <-chan struct{} {
	// Simple shutdown signal
	ch := make(chan struct{})
	go func() {
		// This would be connected to context
		<-time.After(1 * time.Hour) // Placeholder
		close(ch)
	}()
	return ch
}
```

### Expected Behavior
- Semaphore limits concurrent processing
- Queue provides temporary buffer
- Timeout prevents indefinite waiting
- Rejection is explicit (load shed)

---

## Step 4: Implement Circuit Breaker

Create `breaker.go`:

```go
package main

import (
	"sync"
	"sync/atomic"
	"time"
)

type CircuitState int

const (
	StateClosed CircuitState = iota
	StateOpen
	StateHalfOpen
)

type CircuitBreaker struct {
	state             CircuitState
	failures          int
	successes         int
	lastFailure       time.Time
	failureThreshold  int
	timeout           time.Duration
	halfOpenMaxCalls  int
	mu                sync.RWMutex
}

func NewCircuitBreaker(threshold int, timeout time.Duration) *CircuitBreaker {
	return &CircuitBreaker{
		state:            StateClosed,
		failureThreshold: threshold,
		timeout:          timeout,
		halfOpenMaxCalls: 3,
	}
}

// Execute runs fn if circuit allows
// Returns error if open or fn fails
func (cb *CircuitBreaker) Execute(fn func() error) error {
	cb.mu.RLock()
	state := cb.state
	cb.mu.RUnlock()

	if state == StateOpen {
		// Check if we should try half-open
		if time.Since(cb.lastFailure) > cb.timeout {
			cb.mu.Lock()
			if cb.state == StateOpen {
				cb.state = StateHalfOpen
				cb.successes = 0
			}
			cb.mu.Unlock()
		} else {
			return &CircuitOpenError{Message: "circuit is open"}
		}
	}

	err := fn()

	if err != nil {
		cb.recordFailure()
	} else {
		cb.recordSuccess()
	}

	return err
}

func (cb *CircuitBreaker) recordFailure() {
	cb.mu.Lock()
	defer cb.mu.Unlock()

	cb.failures++
	cb.lastFailure = time.Now()

	if cb.failures >= cb.failureThreshold && cb.state == StateClosed {
		cb.state = StateOpen
		log.Printf("⚠️ Circuit breaker OPENED after %d failures", cb.failures)
	}
}

func (cb *CircuitBreaker) recordSuccess() {
	cb.mu.Lock()
	defer cb.mu.Unlock()

	if cb.state == StateHalfOpen {
		cb.successes++
		if cb.successes >= cb.halfOpenMaxCalls {
			cb.state = StateClosed
			cb.failures = 0
			log.Printf("✅ Circuit breaker CLOSED")
		}
	} else {
		cb.failures = 0
	}
}

type CircuitOpenError struct {
	Message string
}

func (e *CircuitOpenError) Error() string
```

### Expected Output
- Fill in the Error() method
- The circuit should transition: Closed → Open → HalfOpen → Closed

---

## Step 5: Implement Retry with Backoff

Create `retry.go`:

```go
package main

import (
	"context"
	"fmt"
	"math"
	"math/rand"
	"time"
)

// RetryWithBackoff executes fn with exponential backoff + jitter
func RetryWithBackoff(ctx context.Context, cfg Config, fn func() error) error {
	var lastErr error

	for attempt := 0; attempt <= cfg.MaxRetries; attempt++ {
		err := fn()
		if err == nil {
			return nil
		}

		lastErr = err

		if attempt < cfg.MaxRetries {
			backoff := calculateBackoff(cfg, attempt)
			select {
			case <-ctx.Done():
				return ctx.Err()
			case <-time.After(backoff):
			}
		}
	}

	return lastErr
}

func calculateBackoff(cfg Config, attempt int) time.Duration {
	// Exponential: base * 2^attempt
	backoff := cfg.InitialBackoff * time.Duration(math.Pow(2, float64(attempt)))

	// Cap at max
	if backoff > cfg.MaxBackoff {
		backoff = cfg.MaxBackoff
	}

	// Add jitter: randomize by ±jitterFactor
	jitter := 1 + (rand.Float64()*2-1)*cfg.JitterFactor
	backoff = time.Duration(float64(backoff) * jitter)

	return backoff
}
```

### Key Insight
The jitter formula `(rand.Float64()*2-1)` produces values from -1 to +1, creating ±30% randomization by default.

---

## Step 6: Wire Together the HTTP Server

Create `main.go`:

```go
package main

import (
	"context"
	"fmt"
	"log"
	"math/rand"
	"net/http"
	"time"
)

var (
	shedder   *LoadShedder
	breaker   *CircuitBreaker
	responded int64
)

func main() {
	rand.Seed(time.Now().UnixNano())

	shedder = NewLoadShedder(defaultConfig)
	breaker = NewCircuitBreaker(5, 30*time.Second)

	// Start queue processor
	go shedder.ProcessQueue(handleRequest)

	// Routes
	http.HandleFunc("/api", handleAPI)
	http.HandleFunc("/health", handleHealth)
	http.HandleFunc("/metrics", handleMetrics)

	log.Println("Load shedding proxy starting on :8080")
	log.Fatal(http.ListenAndServe(":8080", nil))
}

func handleAPI(w http.ResponseWriter, r *http.Request) {
	req := Request{
		ID:        fmt.Sprintf("%d", rand.Int63()),
		Context:   r.Context(),
		StartTime: time.Now(),
		Result:    make(chan Result, 1),
	}

	if !shedder.TryAccept(req) {
		// Load shed!
		w.Header().Set("Retry-After", "30")
		w.Header().Set("X-LoadShed", "true")
		http.Error(w, "Service overloaded", http.StatusServiceUnavailable)
		return
	}

	// Release semaphore when done
	defer shedder.Release()

	// Execute with circuit breaker
	start := time.Now()
	err := breaker.Execute(func() error {
		return RetryWithBackoff(r.Context(), defaultConfig, func() error {
			// Simulate downstream call
			time.Sleep(50 * time.Millisecond)
			if rand.Intn(10) == 0 {
				return fmt.Errorf("downstream error")
			}
			return nil
		})
	})

	duration := time.Since(start)
	atomic.AddInt64(&metrics.ProcessDur, duration.Nanoseconds())

	if err != nil {
		atomic.AddInt64(&metrics.Failed, 1)
		http.Error(w, "Request failed", http.StatusServiceUnavailable)
		return
	}

	atomic.AddInt64(&metrics.Succeeded, 1)
	atomic.AddInt64(&responded, 1)
	w.WriteHeader(http.StatusOK)
	fmt.Fprintf(w, `{"status": "ok", "duration": "%v"}`, duration)
}

func handleRequest(req Request) {
	// Queue processor - processes requests from queue
	// In practice, this would be similar to handleAPI
}

func handleHealth(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusOK)
	fmt.Fprintf(w, `{"status": "healthy", "responded": %d}`, responded)
}

func handleMetrics(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	fmt.Fprintf(w, `{
		"received": %d,
		"accepted": %d,
		"rejected": %d,
		"succeeded": %d,
		"failed": %d
	}`,
		metrics.Received,
		metrics.Accepted,
		metrics.Rejected,
		metrics.Succeeded,
		metrics.Failed,
	)
}
```

---

## Step 7: Test It

```bash
# Build
go build -o load_shedder main.go types.go shedder.go breaker.go retry.go

# Run
./load_shedder

# In another terminal, test normal load
curl http://localhost:8080/api

# Check metrics
curl http://localhost:8080/metrics

# Load test (if you have hey or wrk)
hey -n 1000 -c 100 http://localhost:8080/api

# Check metrics again
curl http://localhost:8080/metrics
```

### Expected Output
```
# Normal request
{"status": "ok", "duration": "52.123ms"}

# Metrics after load
{"received": 1000, "accepted": 850, "rejected": 150, "succeeded": 800, "failed": 50}
```

---

## 🔬 Stretch Challenge (Staff-Level)

### Challenge 1: Add Per-Client Rate Limiting
Modify to track requests per client IP and reject when limit exceeded.

### Challenge 2: Implement Dynamic Thresholds
Adjust load shedding thresholds based on downstream latency (if latency > 500ms, reduce acceptance rate).

### Challenge 3: Add Distributed Tracing
Integrate OpenTelemetry to trace requests through the load shedder.

---

## ✅ Success Criteria

| Criteria | How to Verify |
|----------|---------------|
| Load shedding works | Run load test, see rejected count > 0 |
| Circuit breaker works | Check logs for state transitions |
| Retry with backoff | Add logging to see retry attempts |
| Metrics accurate | Verify received = accepted + rejected |

---

## Continue To

- **Section 8**: Case Study → `case_study.md`
- **Section 9**: Trade-offs Analysis → `tradeoffs_analysis.md`
- **Section 10**: Summary → `summary.md`
