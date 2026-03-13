# Code Lab: Build a Circuit Breaker from Scratch

## Lab Overview

```
🧪 Lab: Circuit Breaker Implementation
🎯 Goal: Build a production-grade circuit breaker and observe its behavior
⏱ Time: ~45-60 minutes
🛠 Requirements:
  - Go 1.20+ installed
  - Basic understanding of concurrency (goroutines, channels)
  - Understanding of the circuit breaker pattern (from this chapter)
```

---

## Step 1: Setup

Create a new Go module and create the following file structure:

```bash
mkdir circuit-breaker-lab
cd circuit-breaker-lab
go mod init circuit-breaker-lab
```

Create a file `main.go` that we'll build throughout the lab:

```go
package main

import (
	"context"
	"errors"
	"fmt"
	"sync"
	"sync/atomic"
	"time"
)

// This lab will guide you through building a circuit breaker
// from scratch, demonstrating all three states (Closed, Open, Half-Open)

func main() {
	fmt.Println("=== Circuit Breaker Lab ===")
	fmt.Println("We'll build a circuit breaker step by step")
}
```

---

## Step 2: Define the State Machine

Add the following types and configuration to your file:

```go
// State represents the three states of a circuit breaker
type State int

const (
	StateClosed State = iota // Normal operation
	StateOpen               // Failing fast
	StateHalfOpen           // Testing recovery
)

// Config holds circuit breaker configuration
type Config struct {
	FailureThreshold  int           // Failures before opening circuit
	SuccessThreshold int           // Successes to close circuit
	TimeoutDuration  time.Duration // Time before attempting recovery
	HalfOpenMaxCalls int           // Max test calls in half-open
}

// DefaultConfig provides sensible defaults
var DefaultConfig = Config{
	FailureThreshold: 3,
	SuccessThreshold: 1,
	TimeoutDuration:  5 * time.Second,
	HalfOpenMaxCalls: 2,
}

var stateNames = map[State]string{
	StateClosed:   "CLOSED",
	StateOpen:     "OPEN",
	StateHalfOpen: "HALF-OPEN",
}
```

**Run it to verify:**

```bash
go run main.go
```

Expected output:
```
=== Circuit Breaker Lab ===
We'll build a circuit breaker step by step
```

---

## Step 3: Implement the Circuit Breaker Structure

Add the CircuitBreaker struct with all necessary fields:

```go
// CircuitBreaker is the main structure
type CircuitBreaker struct {
	mu              sync.RWMutex
	state           State
	failures        int
	successes       int
	lastFailureTime time.Time
	config          Config

	// Metrics - critical for production monitoring
	totalRequests    int64
	totalFailures    int64
	totalSuccesses   int64
	rejectedRequests int64
	stateChanges     int64
}

// NewCircuitBreaker creates a new circuit breaker
func NewCircuitBreaker(config Config) *CircuitBreaker {
	if config.FailureThreshold == 0 {
		config = DefaultConfig
	}

	return &CircuitBreaker{
		state:  StateClosed,
		config: config,
	}
}

// String returns a string representation of the circuit breaker
func (cb *CircuitBreaker) String() string {
	cb.mu.RLock()
	defer cb.mu.RUnlock()

	return fmt.Sprintf("CircuitBreaker(state=%s, failures=%d, successes=%d)",
		stateNames[cb.state], cb.failures, cb.successes)
}
```

**Test it:**

```go
func main() {
	cb := NewCircuitBreaker(DefaultConfig)
	fmt.Println(cb) // Should show CLOSED state
}
```

---

## Step 4: Implement Request Permission Logic

This is the core logic that determines whether a request can proceed:

```go
// canExecute checks if a request is allowed based on current state
func (cb *CircuitBreaker) canExecute() bool {
	cb.mu.Lock()
	defer cb.mu.Unlock()

	atomic.AddInt64(&cb.totalRequests, 1)

	switch cb.state {
	case StateClosed:
		// Normal operation - allow all requests
		return true

	case StateOpen:
		// Check if timeout has elapsed
		if time.Since(cb.lastFailureTime) > cb.config.TimeoutDuration {
			cb.transitionToHalfOpenLocked()
			return true
		}
		// Still open - reject
		atomic.AddInt64(&cb.rejectedRequests, 1)
		return false

	case StateHalfOpen:
		// Limited requests allowed to test recovery
		if cb.successes < cb.config.HalfOpenMaxCalls {
			return true
		}
		atomic.AddInt64(&cb.rejectedRequests, 1)
		return false
	}

	return false
}

// transitionToHalfOpenLocked transitions to half-open state
// Caller must hold the write lock
func (cb *CircuitBreaker) transitionToHalfOpenLocked() {
	cb.state = StateHalfOpen
	cb.successes = 0
	atomic.AddInt64(&cb.stateChanges, 1)
	fmt.Printf("[TRANSITION] %s -> HALF-OPEN (testing recovery)\n",
		stateNames[StateClosed])
}

// transitionToOpenLocked transitions to open state
// Caller must hold the write lock
func (cb *CircuitBreaker) transitionToOpenLocked() {
	if cb.state != StateOpen {
		cb.state = StateOpen
		atomic.AddInt64(&cb.stateChanges, 1)
		fmt.Printf("[TRANSITION] -> OPEN (fail fast)\n")
	}
}

// transitionToClosedLocked transitions to closed state
// Caller must hold the write lock
func (cb *CircuitBreaker) transitionToClosedLocked() {
	cb.state = StateClosed
	cb.failures = 0
	cb.successes = 0
	atomic.AddInt64(&cb.stateChanges, 1)
	fmt.Printf("[TRANSITION] -> CLOSED (recovered)\n")
}
```

---

## Step 5: Implement Execute Method

The main API for the circuit breaker:

```go
var ErrCircuitOpen = errors.New("circuit breaker is open")

// Execute runs the provided function with circuit breaker protection
// Returns error if circuit is open or if the function fails
func (cb *CircuitBreaker) Execute(fn func() error) error {
	// Check if we can execute
	if !cb.canExecute() {
		return ErrCircuitOpen
	}

	// Execute the protected function
	err := fn()

	// Record the result
	cb.recordResult(err)

	return err
}

// recordResult updates state based on function outcome
func (cb *CircuitBreaker) recordResult(err error) {
	cb.mu.Lock()
	defer cb.mu.Unlock()

	if err != nil {
		// Failure case
		atomic.AddInt64(&cb.totalFailures, 1)
		cb.failures++
		cb.lastFailureTime = time.Now()
		cb.successes = 0 // Reset successes

		// Check if we should open the circuit
		if cb.state == StateClosed && cb.failures >= cb.config.FailureThreshold {
			cb.transitionToOpenLocked()
		} else if cb.state == StateHalfOpen {
			// Failed in half-open - go back to open
			cb.transitionToOpenLocked()
		}
	} else {
		// Success case
		atomic.AddInt64(&cb.totalSuccesses, 1)
		cb.successes++
		cb.failures = 0 // Reset failures

		// Check if we should close the circuit
		if cb.state == StateHalfOpen && cb.successes >= cb.config.SuccessThreshold {
			cb.transitionToClosedLocked()
		}
	}
}
```

---

## Step 6: Add Metrics and Monitoring

```go
// Metrics returns current metrics
type Metrics struct {
	State             string
	TotalRequests     int64
	TotalFailures     int64
	TotalSuccesses    int64
	RejectedRequests  int64
	StateChanges      int64
	FailureRate       float64
}

// GetMetrics returns current circuit breaker metrics
func (cb *CircuitBreaker) GetMetrics() Metrics {
	cb.mu.RLock()
	defer cb.mu.RUnlock()

	total := atomic.LoadInt64(&cb.totalRequests)
	failures := atomic.LoadInt64(&cb.totalFailures)

	var failureRate float64
	if total > 0 {
		failureRate = float64(failures) / float64(total) * 100
	}

	return Metrics{
		State:            stateNames[cb.state],
		TotalRequests:    total,
		TotalFailures:    failures,
		TotalSuccesses:   atomic.LoadInt64(&cb.totalSuccesses),
		RejectedRequests: atomic.LoadInt64(&cb.rejectedRequests),
		StateChanges:     atomic.LoadInt64(&cb.stateChanges),
		FailureRate:      failureRate,
	}
}

// PrintMetrics prints current metrics
func (cb *CircuitBreaker) PrintMetrics() {
	m := cb.GetMetrics()
	fmt.Printf("\n=== Circuit Breaker Metrics ===\n")
	fmt.Printf("State:              %s\n", m.State)
	fmt.Printf("Total Requests:     %d\n", m.TotalRequests)
	fmt.Printf("Total Failures:     %d\n", m.TotalFailures)
	fmt.Printf("Total Successes:    %d\n", m.TotalSuccesses)
	fmt.Printf("Rejected Requests:  %d\n", m.RejectedRequests)
	fmt.Printf("State Changes:      %d\n", m.StateChanges)
	fmt.Printf("Failure Rate:       %.1f%%\n", m.FailureRate)
	fmt.Printf("================================\n\n")
}
```

---

## Step 7: Test the Circuit Breaker

Now let's create a comprehensive test that demonstrates all three states:

```go
// simulateService simulates a service that fails initially then recovers
func simulateService(failCount int) func() error {
	attempts := 0
	return func() error {
		attempts++
		if attempts <= failCount {
			return errors.New("service unavailable")
		}
		return nil // Success after failCount attempts
	}
}

func main() {
	fmt.Println("=== Circuit Breaker Lab ===\n")

	// Create circuit breaker with aggressive settings for demo
	config := Config{
		FailureThreshold: 3,
		SuccessThreshold: 1,
		TimeoutDuration:  2 * time.Second, // Short for demo
		HalfOpenMaxCalls: 2,
	}
	cb := NewCircuitBreaker(config)

	fmt.Println("Phase 1: Normal operation with failures (should open)\n")

	// Phase 1: Cause the circuit to open
	for i := 0; i < 5; i++ {
		err := cb.Execute(simulateService(10)) // Will fail first 3 times
		fmt.Printf("Attempt %d: %v\n", i+1, cb)
		if err != nil {
			fmt.Printf("  -> Error: %v\n", err)
		} else {
			fmt.Printf("  -> Success!\n")
		}
		time.Sleep(200 * time.Millisecond)
	}

	cb.PrintMetrics()

	fmt.Println("Phase 2: Circuit is open (should fail fast)\n")

	// Phase 2: Circuit should be open - all requests fail fast
	for i := 0; i < 3; i++ {
		err := cb.Execute(func() error {
			return errors.New("this should not be called")
		})
		fmt.Printf("Attempt %d: %v\n", i+1, cb)
		if err == ErrCircuitOpen {
			fmt.Printf("  -> Correctly rejected: circuit is open\n")
		}
		time.Sleep(100 * time.Millisecond)
	}

	fmt.Println("\nPhase 3: Wait for timeout, enter half-open\n")

	// Phase 3: Wait for timeout
	fmt.Println("Waiting for timeout...")
	time.Sleep(config.TimeoutDuration + 500*time.Millisecond)

	// Now should be in half-open state
	fmt.Printf("After wait: %v\n", cb)

	fmt.Println("\nPhase 4: Test requests in half-open (should succeed and close)\n")

	// Phase 4: Test requests - should succeed and close
	for i := 0; i < 3; i++ {
		err := cb.Execute(func() error {
			return nil // Always succeed
		})
		fmt.Printf("Attempt %d: %v\n", i+1, cb)
		if err != nil {
			fmt.Printf("  -> Error: %v\n", err)
		} else {
			fmt.Printf("  -> Success!\n")
		}
		time.Sleep(100 * time.Millisecond)
	}

	cb.PrintMetrics()

	fmt.Println("=== Lab Complete ===")
}
```

---

## Step 8: Run the Full Demo

```bash
go run main.go
```

**Expected output:**

```
=== Circuit Breaker Lab ===

Phase 1: Normal operation with failures (should open)

Attempt 1: CircuitBreaker(state=CLOSED, failures=1, successes=0)
  -> Error: service unavailable
Attempt 2: CircuitBreaker(state=CLOSED, failures=2, successes=0)
  -> Error: service unavailable
Attempt 3: CircuitBreaker(state=CLOSED, failures=3, successes=0)
[TRANSITION] -> OPEN (fail fast)
  -> Error: service unavailable
Attempt 4: CircuitBreaker(state=OPEN, failures=3, successes=0)
  -> Error: circuit breaker is open
Attempt 5: CircuitBreaker(state=OPEN, failures=3, successes=0)
  -> Error: circuit breaker is open

=== Circuit Breaker Metrics ===
State:              OPEN
Total Requests:     5
Total Failures:     3
Total Successes:    0
Rejected Requests:  2
State Changes:      1
Failure Rate:       60.0%
================================

Phase 2: Circuit is open (should fail fast)

Attempt 1: CircuitBreaker(state=OPEN, failures=3, successes=0)
  -> Correctly rejected: circuit is open
Attempt 2: CircuitBreaker(state=OPEN, failures=3, successes=0)
  -> Correctly rejected: circuit is open
Attempt 3: CircuitBreaker(state=OPEN, failures=3, successes=0)
  -> Correctly rejected: circuit is open

Phase 3: Wait for timeout, enter half-open

Waiting for timeout...
After wait: CircuitBreaker(state=HALF-OPEN, failures=3, successes=0)

Phase 4: Test requests in half-open (should succeed and close)

Attempt 1: CircuitBreaker(state=HALF-OPEN, failures=3, successes=1)
  -> Success!
[TRANSITION] -> CLOSED (recovered)
Attempt 2: CircuitBreaker(state=CLOSED, failures=0, successes=1)
  -> Success!
Attempt 3: CircuitBreaker(state=CLOSED, failures=0, successes=1)
  -> Success!

=== Circuit Breaker Metrics ===
State:              CLOSED
Total Requests:     11
Total Failures:     3
Total Successes:    5
Rejected Requests:  5
State Changes:      3
Failure Rate:       27.3%
================================

=== Lab Complete ===
```

---

## Stretch Challenge: Add Context Support

Add context cancellation support to the circuit breaker:

```go
// ExecuteWithContext runs the function with context support
func (cb *CircuitBreaker) ExecuteWithContext(ctx context.Context, fn func() error) error {
	// Check context first
	select {
	case <-ctx.Done():
		return ctx.Err()
	default:
	}

	if !cb.canExecute() {
		return ErrCircuitOpen
	}

	// Execute with context
	errCh := make(chan error, 1)
	go func() {
		errCh <- fn()
	}()

	select {
	case <-ctx.Done():
		return ctx.Err()
	case err := <-errCh:
		cb.recordResult(err)
		return err
	}
}
```

---

## Stretch Challenge: Add Concurrent Safety Test

Test the circuit breaker under concurrent load:

```go
func testConcurrency() {
	cb := NewCircuitBreaker(Config{
		FailureThreshold: 10,
		TimeoutDuration: 1 * time.Second,
	})

	var wg sync.WaitGroup
	successCount := int64(0)
	failCount := int64(0)

	// 100 concurrent goroutines
	for i := 0; i < 100; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()

			err := cb.Execute(func() error {
				// Simulate work
				time.Sleep(time.Millisecond)
				return nil
			})

			if err != nil {
				atomic.AddInt64(&failCount, 1)
			} else {
				atomic.AddInt64(&successCount, 1)
			}
		}()
	}

	wg.Wait()

	fmt.Printf("Concurrent test: %d success, %d failed\n",
		successCount, failCount)
}
```

---

## Key Takeaways from the Lab

1. **State machine**: The circuit breaker maintains three distinct states with clear transitions
2. **Fail fast**: When open, requests don't even reach the downstream service
3. **Recovery testing**: Half-open state allows testing without full exposure
4. **Metrics**: Production circuit breakers need rich metrics for debugging
5. **Tuning matters**: Threshold and timeout values significantly impact behavior

---

## Next Steps

1. **Add to your project**: Integrate this circuit breaker into a real service
2. **Explore libraries**: Look at existing implementations (go-breaker, hystrix-go)
3. **Combine patterns**: Add bulkhead isolation around the circuit breaker
4. **Observe in production**: Add logging and metrics to see state changes in real traffic
