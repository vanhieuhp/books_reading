# Annotated Code Examples — Chapter 4: Stability Patterns

This section provides production-grade Go implementations of the key stability patterns. Each example shows the naive approach first, then the production-grade solution.

---

## Code Example 1: Circuit Breaker (State Machine)

### The Naive Approach — No Circuit Breaker

```go
package main

import (
	"context"
	"fmt"
	"time"
)

// ❌ NAIVE: No circuit breaker — calls will hang indefinitely
// Problem: If the downstream service is down, this will timeout
// only after the entire HTTP client timeout (often 30s+)
func naiveCallService(ctx context.Context, url string) (string, error) {
	// No circuit breaker means we keep hitting a failing service
	// Resources: connections, threads, memory all accumulate while waiting
	req, _ := http.NewRequestWithContext(ctx, "GET", url, nil)
	resp, err := http.DefaultClient.Do(req) // This can hang for 30+ seconds!
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()

	// Process response...
	return "success", nil
}
```

### Production Approach — Circuit Breaker Implementation

```go
package circuitbreaker

import (
	"context"
	"errors"
	"sync"
	"time"
)

// State represents the three states of a circuit breaker
type State int

const (
	StateClosed State = iota // Normal operation - requests pass through
	StateOpen                // Circuit has tripped - fail fast
	StateHalfOpen            // Testing if service recovered
)

// Configuration holds circuit breaker settings
// Staff-level note: These values should be tuned based on:
// - Service SLA (if 99.9% availability, failure threshold should be lower)
// - Request volume (high volume = lower threshold for faster detection)
// - Downstream criticality (critical services warrant more aggressive breaking)
type Config struct {
	FailureThreshold  int           // Failures before tripping (typically 5-20)
	SuccessThreshold  int           // Successes in half-open to close (typically 1-3)
	TimeoutDuration   time.Duration // Time before attempting recovery (typically 30s-5min)
	HalfOpenMaxCalls  int           // Max calls allowed in half-open state
}

var DefaultConfig = Config{
	FailureThreshold: 5,
	SuccessThreshold: 1,
	TimeoutDuration:  30 * time.Second,
	HalfOpenMaxCalls: 3,
}

// CircuitBreaker implements the circuit breaker pattern
// Thread-safe by design - can be called from multiple goroutines
type CircuitBreaker struct {
	mu           sync.RWMutex
	state        State
	failures     int
	successes    int
	lastFailure  time.Time
	config       Config

	// Metrics for observability - staff-level: always track these!
	failuresCount   int64 // Total failures since last reset
	successesCount  int64 // Total successes
	requestsRejected int64 // Requests rejected due to open circuit
}

// NewCircuitBreaker creates a new circuit breaker with given config
func NewCircuitBreaker(config Config) *CircuitBreaker {
	if config.FailureThreshold == 0 {
		config = DefaultConfig
	}
	return &CircuitBreaker{
		state:  StateClosed,
		config: config,
	}
}

// Execute runs the provided function with circuit breaker protection
// Returns error if circuit is open or if the function fails
func (cb *CircuitBreaker) Execute(ctx context.Context, fn func() error) error {
	// Check circuit state before executing
	if !cb.allowRequest() {
		atomic.AddInt64(&cb.requestsRejected, 1)
		return ErrCircuitOpen
	}

	// Execute the protected function
	err := fn()

	// Record the result
	cb.recordResult(err)

	return err
}

// allowRequest determines if a request should be allowed through
// Must be called with read lock held
func (cb *CircuitBreaker) allowRequest() bool {
	cb.mu.RLock()
	defer cb.mu.RUnlock()

	switch cb.state {
	case StateClosed:
		return true
	case StateOpen:
		// Check if timeout has elapsed - transition to half-open
		if time.Since(cb.lastFailure) > cb.config.TimeoutDuration {
			cb.transitionToHalfOpen()
			return true
		}
		return false
	case StateHalfOpen:
		// In half-open, limit concurrent test requests
		return cb.successes < cb.config.HalfOpenMaxCalls
	}
	return false
}

// recordResult updates circuit state based on function result
func (cb *CircuitBreaker) recordResult(err error) {
	cb.mu.Lock()
	defer cb.mu.Unlock()

	if err != nil {
		// Failure recorded
		atomic.AddInt64(&cb.failuresCount, 1)
		cb.failures++
		cb.lastFailure = time.Now()
		cb.successes = 0 // Reset success counter

		// Trip the circuit if threshold exceeded
		if cb.state == StateClosed && cb.failures >= cb.config.FailureThreshold {
			cb.transitionToOpen()
		} else if cb.state == StateHalfOpen {
			// Failed test in half-open - go back to open
			cb.transitionToOpen()
		}
	} else {
		// Success recorded
		atomic.AddInt64(&cb.successesCount, 1)
		cb.successes++
		cb.failures = 0 // Reset failure counter

		// Close the circuit if success threshold met
		if cb.state == StateHalfOpen && cb.successes >= cb.config.SuccessThreshold {
			cb.transitionToClosed()
		}
	}
}

// State transitions with logging
// Staff-level note: These transitions should emit metrics/events
func (cb *CircuitBreaker) transitionToOpen() {
	cb.state = StateOpen
	// In production: log.Warn("Circuit breaker opened", "failures", cb.failures)
	fmt.Printf("[ALERT] Circuit breaker OPENED after %d failures\n", cb.failures)
}

func (cb *CircuitBreaker) transitionToHalfOpen() {
	previousState := cb.state
	cb.state = StateHalfOpen
	cb.successes = 0
	// In production: log.Info("Circuit breaker half-open", "previous", previousState)
	fmt.Printf("[INFO] Circuit breaker HALF-OPEN (testing recovery)\n")
}

func (cb *CircuitBreaker) transitionToClosed() {
	cb.state = StateClosed
	cb.failures = 0
	cb.successes = 0
	// In production: log.Info("Circuit breaker closed", "totalFailures", cb.failuresCount)
	fmt.Printf("[INFO] Circuit breaker CLOSED - service recovered\n")
}

// GetState returns current circuit state (for monitoring)
func (cb *CircuitBreaker) GetState() State {
	cb.mu.RLock()
	defer cb.mu.RUnlock()
	return cb.state
}

// Metrics returns current metrics (for monitoring/dashboards)
func (cb *CircuitBreaker) Metrics() (failures, successes, rejected int64) {
	return atomic.LoadInt64(&cb.failuresCount),
		atomic.LoadInt64(&cb.successesCount),
		atomic.LoadInt64(&cb.requestsRejected)
}

// Common errors
var ErrCircuitOpen = errors.New("circuit breaker is open")

// ============================================================
// USAGE EXAMPLE
// ============================================================

func ExampleUsage() {
	cb := NewCircuitBreaker(Config{
		FailureThreshold: 3,
		TimeoutDuration:  10 * time.Second,
	})

	ctx := context.Background()

	for i := 0; i < 10; i++ {
		err := cb.Execute(ctx, func() error {
			// Simulate a failing service
			if i < 5 {
				return errors.New("service unavailable")
			}
			return nil // Success after 5th attempt
		})

		state := cb.GetState()
		fmt.Printf("Attempt %d: state=%v, error=%v\n", i+1, state, err)

		time.Sleep(500 * time.Millisecond)
	}
}
```

---

## Code Example 2: Bulkhead (Thread Pool Isolation)

### The Naive Approach — Shared Thread Pool

```go
package main

import (
	"fmt"
	"sync"
	"time"
)

// ❌ NAIVE: Single shared thread pool for all operations
// Problem: One slow operation exhausts the pool, affecting all others
type SharedPool struct {
	workChan chan func()
	wg      sync.WaitGroup
}

func NewSharedPool(size int) *SharedPool {
	pool := &SharedPool{
		workChan: make(chan func(), 100), // Small buffer!
	}

	// Start worker goroutines
	for i := 0; i < size; i++ {
		pool.wg.Add(1)
		go func() {
			defer pool.wg.Done()
			for work := range pool.workChan {
				work() // No timeout - can hang indefinitely!
			}
		}()
	}

	return pool
}

func (p *SharedPool) Submit(task func()) {
	// If pool is full, this blocks or drops the task
	// Either way: bad experience for user
	p.workChan <- task
}
```

### Production Approach — Bulkhead with Multiple Isolated Pools

```go
package bulkhead

import (
	"context"
	"errors"
	"fmt"
	"sync"
	"time"
)

// BulkheadConfig defines isolation boundaries
// Staff-level note: Pool sizing requires understanding:
// - Expected concurrent requests per service
// - SLA requirements (how much queuing is acceptable)
// - Resource constraints (memory per goroutine ~2KB)
type BulkheadConfig struct {
	MaxConcurrentCalls int           // Max parallel calls per bulkhead
	MaxQueueSize       int           // Max queued calls (0 = no queuing = fail fast)
	Timeout           time.Duration // Max time to wait for available slot
}

var DefaultBulkheadConfig = BulkheadConfig{
	MaxConcurrentCalls: 10,
	MaxQueueSize:      0,  // 0 = fail immediately if no slot
	Timeout:           3 * time.Second,
}

// Bulkhead implements isolation pattern for a specific operation type
// Each bulkhead is independent - failure in one doesn't affect others
type Bulkhead struct {
	name   string
	config BulkheadConfig

	// Semaphore for limiting concurrent calls
	semaphore chan struct{}

	// Metrics
	activeCalls    int64
	queuedCalls    int64
	rejectedCalls  int64
	timeoutCalls   int64
	completedCalls int64

	mu sync.RWMutex
}

// NewBulkhead creates a new bulkhead for a specific operation type
// Staff-level note: Name should identify the resource/operation
// e.g., "payment-service", "database-users-table", "external-api-fraud-check"
func NewBulkhead(name string, config BulkheadConfig) *Bulkhead {
	if config.MaxConcurrentCalls == 0 {
		config = DefaultBulkheadConfig
	}

	return &Bulkhead{
		name:      name,
		config:    config,
		semaphore: make(chan struct{}, config.MaxConcurrentCalls),
	}
}

// Execute runs the function within the bulkhead's isolation bounds
// Returns error if:
// - Context cancelled
// - Bulkhead is full (MaxQueueSize exceeded)
// - Timeout exceeded waiting for slot
func (b *Bulkhead) Execute(ctx context.Context, fn func() error) error {
	// Track attempt
	atomic.AddInt64(&b.queuedCalls, 1)

	// Try to acquire a slot with timeout
	select {
	case b.semaphore <- struct{}{}: // Got a slot
		atomic.AddInt64(&b.activeCalls, 1)
		atomic.AddInt64(&b.queuedCalls, -1)

		// Execute the protected function
		err := fn()

		// Release slot
		<-b.semaphore
		atomic.AddInt64(&b.activeCalls, -1)

		if err == nil {
			atomic.AddInt64(&b.completedCalls, 1)
		}
		return err

	case <-ctx.Done():
		// Context cancelled
		atomic.AddInt64(&b.rejectedCalls, 1)
		atomic.AddInt64(&b.queuedCalls, -1)
		return ctx.Err()

	case <-time.After(b.config.Timeout):
		// Timeout waiting for slot
		atomic.AddInt64(&b.timeoutCalls, 1)
		atomic.AddInt64(&b.queuedCalls, -1)
		return ErrBulkheadTimeout
	}
}

// AvailableSlots returns how many concurrent slots are available
// Staff-level note: Useful for load shedding decisions
func (b *Bulkhead) AvailableSlots() int {
	return cap(b.semaphore) - len(b.semaphore)
}

// Metrics returns current bulkhead metrics
func (b *Bulkhead) Metrics() BulkheadMetrics {
	return BulkheadMetrics{
		Name:            b.name,
		ActiveCalls:     atomic.LoadInt64(&b.activeCalls),
		QueuedCalls:     atomic.LoadInt64(&b.queuedCalls),
		RejectedCalls:   atomic.LoadInt64(&b.rejectedCalls),
		TimeoutCalls:    atomic.LoadInt64(&b.timeoutCalls),
		CompletedCalls:  atomic.LoadInt64(&b.completedCalls),
		MaxConcurrent:   b.config.MaxConcurrentCalls,
		AvailableSlots:  b.AvailableSlots(),
	}
}

type BulkheadMetrics struct {
	Name           string
	ActiveCalls    int64
	QueuedCalls    int64
	RejectedCalls  int64
	TimeoutCalls   int64
	CompletedCalls int64
	MaxConcurrent  int
	AvailableSlots int
}

var ErrBulkheadTimeout = errors.New("bulkhead: timeout waiting for available slot")

// ============================================================
// MULTI-BULKHEAD ORCHESTRATOR
// ============================================================

// BulkheadRegistry manages multiple bulkheads for different operations
// Staff-level note: This is the pattern used in practice -
// each downstream service/operation gets its own bulkhead
type BulkheadRegistry struct {
	bulkheads map[string]*Bulkhead
	mu        sync.RWMutex
}

func NewBulkheadRegistry() *BulkheadRegistry {
	return &BulkheadRegistry{
		bulkheads: make(map[string]*Bulkhead),
	}
}

// GetOrCreate returns an existing bulkhead or creates a new one
func (r *BulkheadRegistry) GetOrCreate(name string, config BulkheadConfig) *Bulkhead {
	r.mu.RLock()
	if b, exists := r.bulkheads[name]; exists {
		r.mu.RUnlock()
		return b
	}
	r.mu.RUnlock()

	r.mu.Lock()
	defer r.mu.Unlock()

	// Double-check after acquiring write lock
	if b, exists := r.bulkheads[name]; exists {
		return b
	}

	b := NewBulkhead(name, config)
	r.bulkheads[name] = b
	return b
}

// Execute calls the named bulkhead's Execute method
func (r *BulkheadRegistry) Execute(name string, ctx context.Context, fn func() error) error {
	b := r.GetOrCreate(name, DefaultBulkheadConfig)
	return b.Execute(ctx, fn)
}

// ============================================================
// USAGE EXAMPLE
// ============================================================

func ExampleUsage() {
	// Create registry with different bulkheads for different services
	registry := NewBulkheadRegistry()

	// High-priority: smaller pool, fail fast
	_ = registry.GetOrCreate("auth-service", BulkheadConfig{
		MaxConcurrentCalls: 50,
		MaxQueueSize:      0,
		Timeout:           1 * time.Second,
	})

	// Lower-priority: larger pool, can queue
	_ = registry.GetOrCreate("email-service", BulkheadConfig{
		MaxConcurrentCalls: 10,
		MaxQueueSize:      100,
		Timeout:           30 * time.Second,
	})

	ctx := context.Background()

	// Each operates independently
	err := registry.Execute("auth-service", ctx, func() error {
		// This has its own limited pool
		fmt.Println("Auth service called")
		return nil
	})

	err = registry.Execute("email-service", ctx, func() error {
		// This has a different pool - can queue while auth runs hot
		fmt.Println("Email service called")
		return nil
	})

	// Print metrics
	authBulkhead := registry.GetOrCreate("auth-service", DefaultBulkheadConfig)
	fmt.Printf("Auth metrics: %+v\n", authBulkhead.Metrics())
}
```

---

## Code Example 3: Timeout (The Foundation Pattern)

### The Naive Approach — No Explicit Timeout

```go
package main

import (
	"context"
	"fmt"
	"net/http"
	"time"
)

// ❌ NAIVE: Using default HTTP client timeouts (often infinite!)
// Problem: Go's http.DefaultClient has no timeout by default
// This means one hanging request can consume resources indefinitely
func naiveHTTPClient() {
	// DefaultClient has zero timeout!
	// A slow server = hung goroutine = memory leak
	resp, err := http.Get("http://slow-service/api/data")
	// This can hang FOREVER
}
```

### Production Approach — Layered Timeouts

```go
package timeout

import (
	"context"
	"errors"
	"fmt"
	"net/http"
	"time"
)

// TimeoutConfig defines timeout hierarchy
// Staff-level note: Timeouts should be:
// - Proportional to operation complexity
// - Shorter for user-facing requests
// - Longer for internal/batch operations
// - Tested under load (timeouts behave differently under pressure)
type TimeoutConfig struct {
	ConnectTimeout   time.Duration // TCP connection timeout
	ReadHeaderTimeout time.Duration // Time to read response headers
	ReadTimeout      time.Duration // Time to read response body
	WriteTimeout     time.Duration // Time to write request
	IdleTimeout      time.Duration // Time for idle connections
}

var DefaultTimeoutConfig = TimeoutConfig{
	ConnectTimeout:    2 * time.Second,
	ReadHeaderTimeout: 2 * time.Second,
	ReadTimeout:       5 * time.Second,
	WriteTimeout:      3 * time.Second,
	IdleTimeout:       30 * time.Second,
}

// NewTimeoutClient creates an HTTP client with proper timeouts
// Staff-level note: ALWAYS create your own client, never use DefaultClient
func NewTimeoutClient(config TimeoutConfig) *http.Client {
	return &http.Client{
		Transport: &http.Transport{
			DialContext: (&net.Dialer{
				Timeout: config.ConnectTimeout,
			}).DialContext,
			TLSHandshakeTimeout:   config.ConnectTimeout,
			ResponseHeaderTimeout: config.ReadHeaderTimeout,
			IdleConnTimeout:       config.IdleTimeout,
		},
		// Note: We don't set ReadTimeout/WriteTimeout here
		// because they're handled by the Transport
		Timeout: config.ReadTimeout + config.WriteTimeout,
	}
}

// Operation-level timeouts using context
// Staff-level note: Context timeout is your safety net
// Even if HTTP client timeout fails, context will eventually cancel
func CallWithTimeout(ctx context.Context, client *http.Client, url string) error {
	// Create a timeout context - this is your deadline
	// Staff-level: Make this proportional to user expectations
	// - API calls: 1-5 seconds
	// - User-facing: 10-30 seconds
	// - Background jobs: minutes
	ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
	defer cancel()

	req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
	if err != nil {
		return err
	}

	resp, err := client.Do(req)
	if err != nil {
		// Check if it was a timeout
		if errors.Is(err, context.DeadlineExceeded) {
			return ErrOperationTimeout
		}
		if errors.Is(err, context.Canceled) {
			return ErrOperationCanceled
		}
		return err
	}
	defer resp.Body.Close()

	return nil
}

// RetryWithTimeout demonstrates timeout + retry pattern
// Staff-level note: Timeouts and retries are complementary
// - Timeout limits wait time per attempt
// - Retry provides resilience against transient failures
func RetryWithTimeout(
	ctx context.Context,
	fn func() error,
	maxRetries int,
	timeoutPerAttempt time.Duration,
) error {
	var lastErr error

	for attempt := 0; attempt < maxRetries; attempt++ {
		// Each attempt gets its own timeout
		attemptCtx, cancel := context.WithTimeout(ctx, timeoutPerAttempt)
		defer cancel()

		if err := fn(); err != nil {
			lastErr = err
			// Check if we should retry
			if isTransient(err) {
				// Wait with exponential backoff
				waitTime := time.Duration(attempt+1) * 500 * time.Millisecond
				select {
				case <-attemptCtx.Done():
					return attemptCtx.Err()
				case <-time.After(waitTime):
					continue // Retry
				}
			}
			return err // Non-transient error, don't retry
		}
		return nil // Success
	}

	return fmt.Errorf("max retries (%d) exceeded: %w", maxRetries, lastErr)
}

// isTransient determines if an error is likely temporary
func isTransient(err error) bool {
	// Add your logic here - network errors, timeouts, 5xx codes
	// This is a simplified example
	return true
}

var (
	ErrOperationTimeout  = errors.New("operation timed out")
	ErrOperationCanceled = errors.New("operation was canceled")
)

// ============================================================
// TIMEOUT STRATEGY GUIDE
// ============================================================

/*
Timeout Strategy by Operation Type:

| Operation Type        | Suggested Timeout | Rationale                                    |
|----------------------|-------------------|---------------------------------------------|
| Cache lookup         | 50-200ms          | Sub-millisecond in practice, padding for    |
|                      |                   | network variance                            |
| Internal service     | 1-3 seconds       | Same datacenter, low latency expected      |
| Database query       | 1-5 seconds       | Depends on query complexity                |
| External API         | 5-30 seconds     | Varies widely, consider SLA                |
| User-facing request  | 10-30 seconds    | User tolerance threshold                   |
| Background job       | Minutes           | Longer running, less time-critical         |

Common Mistakes:
1. Setting timeout = 0 (infinite) - NEVER DO THIS
2. Setting same timeout for all operations
3. Not testing timeouts under load
4. No visibility into timeout causes
5. Not handling timeout errors distinctly from other errors

Staff-level insight:
- Timeouts are your "emergency brake"
- They prevent resource accumulation during slow degradation
- Always have visibility into timeout frequency
- Tune based on p99 latency, not average
*/
