// naive_load_shedding.go
// ============================================================
// ❌ NAIVE APPROACH — What most developers do
// ============================================================
// This is what happens when you DON'T implement proper load shedding.
// This code is FOR LEARNING PURPOSES ONLY - it demonstrates failure modes.
//
// Key problems demonstrated:
// 1. No load shedding - tries to serve all requests
// 2. No connection pool management
// 3. No circuit breaker
// 4. Synchronous blocking calls
// 5. Immediate retry on failure (retry storm)
//
// Run: go run naive_load_shedding.go
// Expected: System crashes under load

package main

import (
	"fmt"
	"log"
	"net/http"
	"sync"
	"time"
)

// Simulating downstream dependencies
var (
	downstreamCallCount    int
	downstreamFailureCount int
	mu                     sync.Mutex
)

// ============================================================
// PROBLEM 1: No load shedding - accepts ALL requests
// ============================================================
// Staff-level insight: Every request consumes resources even before
// we know if we can handle it. By the time we realize we can't,
// we're already overwhelmed.

func naiveHandler(w http.ResponseWriter, r *http.Request) {
	// Problem: No queue limit, no early rejection
	// This will accept requests until the system dies

	start := time.Now()

	// Make synchronous call to downstream service
	// Problem: This blocks the thread, limiting concurrency
	err := callDownstreamService(r.Context())

	if err != nil {
		// Problem: Immediate retry with no backoff!
		// This creates retry storms
		log.Printf("First attempt failed: %v, retrying immediately...", err)

		// Second attempt - also synchronous
		err = callDownstreamService(r.Context())
		if err != nil {
			// Problem: No circuit breaker - keeps calling failing service
			log.Printf("Second attempt failed: %v", err)

			// Problem: No graceful degradation - just fail
			http.Error(w, "Service unavailable", http.StatusInternalServerError)
			return
		}
	}

	// Success
	duration := time.Since(start)
	w.WriteHeader(http.StatusOK)
	fmt.Fprintf(w, `{"status": "ok", "duration": "%v"}`, duration)
}

// ============================================================
// PROBLEM 2: No connection pool management
// ============================================================
// Staff-level insight: Under load, this will exhaust OS connections,
// causing hangs and cascade failures.

func callDownstreamService(ctx interface{ Context() interface{} }) error {
	// Problem: No connection pool limit
	// Problem: No timeout
	// Problem: No circuit breaker

	mu.Lock()
	downstreamCallCount++
	callNum := downstreamCallCount
	mu.Unlock()

	// Simulate downstream service call
	// In real code: http.Get() or database call
	time.Sleep(100 * time.Millisecond) // Simulated latency

	// Simulate occasional failures
	if callNum%10 == 0 {
		mu.Lock()
		downstreamFailureCount++
		mu.Unlock()
		return fmt.Errorf("downstream service error")
	}

	return nil
}

// ============================================================
// PROBLEM 3: No resource monitoring or metrics
// ============================================================
// Staff-level insight: We have no idea what's happening until crash

func main() {
	fmt.Println("Starting NAIVE server on :8080")
	fmt.Println("⚠️  This will fail under load - FOR DEMONSTRATION ONLY")
	fmt.Println()

	// No health check that reflects actual system state
	// No load shedding middleware
	// No circuit breaker

	http.HandleFunc("/api/naive", naiveHandler)

	// Basic health check - but doesn't show if we're overloaded
	http.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		fmt.Fprintf(w, "OK")
	})

	// Problem: No metrics endpoint for observability
	// http.HandleFunc("/metrics", ...)

	log.Fatal(http.ListenAndServe(":8080", nil))
}

// ============================================================
// OBSERVATIONS WHEN RUN UNDER LOAD:
// ============================================================
//
// 1. Response time increases linearly with load
// 2. Memory grows unbounded (no limits)
// 3. Connection pool exhausts (file descriptors)
// 4. Thread pool exhausts (goroutines blocked on I/O)
// 5. Downstream service receives 2x-3x traffic due to retries
// 6. Complete failure within minutes
//
// TO TEST: Run this, then use hey or wrk:
//   hey -n 10000 -c 100 http://localhost:8080/api/naive
//
// EXPECTED OUTPUT:
//   - Initial success: ~100ms response
//   - After 30 seconds: timeouts
//   - After 60 seconds: connection refused
// ============================================================
