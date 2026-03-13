// Chapter 16: The Systemic View - Code Examples
// Language: Go (production-grade systems programming)
//
// This package demonstrates:
// 1. System observability - tracking components and their interactions
// 2. Feedback loop implementation - negative feedback for self-healing
// 3. Human-centered design - structured logging for operators

package main

import (
	"context"
	"fmt"
	"log"
	"math/rand"
	"sync"
	"time"
)

// ============================================================
// SECTION 1: System Observability - Naive vs Production
// ============================================================

// ❌ Naive approach - just logs, no structure, no correlation
// Problem: Can't trace requests across components, no context
func naiveServiceCall(serviceName string) error {
	log.Printf("Calling service %s", serviceName)
	// Simulate work
	time.Sleep(time.Millisecond * 100)
	if rand.Float32() < 0.1 {
		return fmt.Errorf("service %s failed", serviceName)
	}
	return nil
}

// ✅ Production approach - structured logging with correlation IDs
// Why: Enables tracing requests across service boundaries,
// helps operators diagnose issues, supports incident investigation

type SystemContext struct {
	TraceID    string
	SpanID     string
	Component  string
	StartedAt  time.Time
	Metadata   map[string]interface{}
}

func NewSystemContext(traceID, component string) *SystemContext {
	return &SystemContext{
		TraceID:   traceID,
		SpanID:    generateSpanID(),
		Component: component,
		StartedAt: time.Now(),
		Metadata:  make(map[string]string),
	}
}

// Structured log format for operators and tooling
func (sc *SystemContext) Log(level, message string) {
	elapsed := time.Since(sc.StartedAt).Milliseconds()
	log.Printf("[%s] trace_id=%s span_id=%s component=%s elapsed_ms=%d message=%s",
		level,
		sc.TraceID,
		sc.SpanID,
		sc.Component,
		elapsed,
		message,
	)
}

func (sc *SystemContext) LogError(err error) {
	sc.Log("ERROR", err.Error())
	sc.Metadata["error"] = err.Error()
}

func (sc *SystemContext) WithMetadata(key, value string) *SystemContext {
	sc.Metadata[key] = value
	return sc
}

func generateSpanID() string {
	return fmt.Sprintf("%016x", rand.Uint64())
}

// Production service call with full observability
func productionServiceCall(ctx context.Context, serviceName string) error {
	sysCtx := NewSystemContext(getTraceID(ctx), serviceName)
	sysCtx.Log("INFO", fmt.Sprintf("Calling downstream service: %s", serviceName))

	// Create child context for downstream
	childCtx := context.WithValue(ctx, "span_id", sysCtx.SpanID)

	// Simulate work with timeout
	select {
	case <-time.After(100 * time.Millisecond):
		sysCtx.Log("INFO", "Service call completed successfully")
		return nil
	case <-childCtx.Done():
		sysCtx.LogError(childCtx.Err())
		return childCtx.Err()
	}
}

func getTraceID(ctx context.Context) string {
	if traceID, ok := ctx.Value("trace_id").(string); ok {
		return traceID
	}
	return generateSpanID()
}

// ============================================================
// SECTION 2: Feedback Loop - Negative Feedback for Self-Healing
// ============================================================

// ❌ Naive approach - no circuit breaker, no backpressure
// Problem: Cascading failures when downstream service is down
type NaiveClient struct{}

func (nc *NaiveClient) Call(url string) error {
	// Blindly retry forever - this is what most people do
	for {
		resp, err := http.Get(url)
		if err == nil {
			resp.Body.Close()
			return nil
		}
		log.Printf("Retry after error: %v", err)
		time.Sleep(time.Second)
	}
}

// ✅ Production approach - Circuit Breaker with negative feedback
// Why: Circuit Breaker is a negative feedback loop that:
// 1. Detects failures (the "sense" phase)
// 2. Stops requests to failing service (the "act" phase)
// 3. Allows service to recover (the "recover" phase)
// This prevents cascading failures and enables self-healing

type CircuitState int

const (
	CircuitClosed CircuitState = iota // Normal operation
	CircuitOpen                        // Failing, rejecting requests
	CircuitHalfOpen                    // Testing if service recovered
)

type CircuitBreaker struct {
	mu             sync.Mutex
	state          CircuitState
	failures       int
	successes      int
	failureThreshold int
	successThreshold int
	timeout        time.Duration
	lastFailure    time.Time
	name           string
}

func NewCircuitBreaker(name string, failureThreshold, successThreshold int, timeout time.Duration) *CircuitBreaker {
	return &CircuitBreaker{
		name:              name,
		state:              CircuitClosed,
		failureThreshold:  failureThreshold,
		successThreshold:  successThreshold,
		timeout:           timeout,
	}
}

// Negative feedback loop: sense → act → recover
func (cb *CircuitBreaker) Execute(fn func() error) error {
	cb.mu.Lock()
	defer cb.mu.Unlock()

	// ACT PHASE: If circuit is open, reject immediately
	// This is the "negative feedback" - we stop sending requests
	// to let the downstream service recover
	if cb.state == CircuitOpen {
		// Check if timeout has elapsed - try half-open
		if time.Since(cb.lastFailure) > cb.timeout {
			cb.state = CircuitHalfOpen
			cb.successes = 0
			log.Printf("[CIRCUIT] %s: transitioning to HALF_OPEN", cb.name)
		} else {
			return fmt.Errorf("circuit breaker open: %s", cb.name)
		}
	}

	// Execute the protected call
	err := fn()

	// SENSE PHASE: Detect failures
	if err != nil {
		cb.failures++
		cb.lastFailure = time.Now()
		log.Printf("[CIRCUIT] %s: failure %d/%d", cb.name, cb.failures, cb.failureThreshold)

		// ACT PHASE: Open circuit after threshold failures
		if cb.failures >= cb.failureThreshold {
			cb.state = CircuitOpen
			log.Printf("[CIRCUIT] %s: OPEN - preventing cascade", cb.name)
		}
		return err
	}

	// RECOVERY PHASE: Track successes
	cb.successes++
	if cb.state == CircuitHalfOpen && cb.successes >= cb.successThreshold {
		cb.state = CircuitClosed
		cb.failures = 0
		log.Printf("[CIRCUIT] %s: CLOSED - recovered", cb.name)
	}

	return nil
}

// ============================================================
// SECTION 3: Human-Centered Design - Operator-Friendly
// ============================================================

// ❌ Naive approach - cryptic error messages
// Problem: Operators waste time deciphering error logs
func naiveErrorHandler(err error) {
	log.Printf("Error: %v", err)
}

// ✅ Production approach - structured errors with context
// Why: Errors should be actionable by humans:
// - Clear description of what happened
// - What the system did about it
// - What the operator should do

type OperatorError struct {
	What       string   // What happened
	Impact     string   // What the system did (self-healing)
	Action     string   // What the operator should do
	Runbook    string   // Link to runbook
	TraceID    string   // For correlation
	Timestamp  time.Time
	Components []string // Which components were involved
}

func (oe *OperatorError) Error() string {
	return fmt.Sprintf("[%s] %s | Impact: %s | Action: %s | See: %s",
		oe.Timestamp.Format(time.RFC3339),
		oe.What,
		oe.Impact,
		oe.Action,
		oe.Runbook,
	)
}

// Human-readable log format for on-call engineers
func (oe *OperatorError) Log() {
	log.Printf("""
╔══════════════════════════════════════════════════════════════╗
║ INCIDENT ALERT                                                ║
╠══════════════════════════════════════════════════════════════╣
║ WHAT: %s
║ IMPACT: %s
║ ACTION REQUIRED: %s
║ RUNBOOK: %s
║ TRACE: %s
║ COMPONENTS: %v
╚══════════════════════════════════════════════════════════════╝
	`, oe.What, oe.Impact, oe.Action, oe.Runbook, oe.TraceID, oe.Components)
}

// Production error handler that creates actionable errors
func productionErrorHandler(err error, traceID string) *OperatorError {
	return &OperatorError{
		What:       "Database connection pool exhausted",
		Impact:     "Circuit breaker opened, requests rejected with 503",
		Action:     "Check database CPU/memory; consider scaling up",
		Runbook:    "https://wiki/runbooks/db-pool-exhaustion",
		TraceID:    traceID,
		Timestamp:  time.Now(),
		Components: []string{"postgres-primary", "connection-pooler"},
	}
}

// ============================================================
// DEMO: Running the Production Patterns
// ============================================================

func main() {
	fmt.Println("=== Chapter 16: Production Code Examples ===\n")

	// Demo 1: System Observability
	fmt.Println("1. System Observability Demo")
	traceID := generateSpanID()
	ctx := context.WithValue(context.Background(), "trace_id", traceID)

	sysCtx := NewSystemContext(traceID, "demo-service")
	sysCtx.Log("INFO", "Starting service")
	sysCtx.WithMetadata("version", "1.0.0")

	if err := productionServiceCall(ctx, "downstream-api"); err != nil {
		sysCtx.LogError(err)
	}

	// Demo 2: Circuit Breaker (Negative Feedback Loop)
	fmt.Println("\n2. Circuit Breaker (Negative Feedback) Demo")
	cb := NewCircuitBreaker("downstream-api", 3, 2, 5*time.Second)

	for i := 0; i < 10; i++ {
		err := cb.Execute(func() error {
			// Simulate random failures
			if rand.Float32() < 0.7 {
				return fmt.Errorf("downstream service unavailable")
			}
			return nil
		})

		stateNames := []string{"CLOSED", "OPEN", "HALF_OPEN"}
		status := "SUCCESS"
		if err != nil {
			status = "REJECTED"
		}
		fmt.Printf("  Attempt %d: %s (circuit: %s)\n", i+1, status, stateNames[cb.state])

		time.Sleep(200 * time.Millisecond)
	}

	// Demo 3: Human-Centered Error Handling
	fmt.Println("\n3. Human-Centered Error Handling Demo")
	err := productionErrorHandler(fmt.Errorf("connection refused"), traceID)
	err.Log()
}
