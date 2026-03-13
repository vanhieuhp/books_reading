// Circuit Breaker Demo
// Chapter 14: The Trampled Product Launch
// Demonstrates circuit breaker patterns that prevent cascade failures from third-party outages

package circuit

import (
	"context"
	"errors"
	"fmt"
	"net/http"
	"strings"
	"sync"
	"time"
)

// CircuitState represents the state of a circuit breaker
type CircuitState int

const (
	// StateClosed: Normal operation, requests pass through
	StateClosed CircuitState = iota
	// StateOpen: Failing, reject requests immediately
	StateOpen
	// StateHalfOpen: Testing if service recovered
	StateHalfOpen
)

// CircuitBreakerConfig configures circuit breaker behavior
type CircuitBreakerConfig struct {
	FailureThreshold int           // Number of failures before opening circuit
	SuccessThreshold int          // Number of successes in half-open before closing
	Timeout         time.Duration // Time in open state before trying half-open
	MaxRequests     int           // Max concurrent requests in half-open state
}

// CircuitBreaker implements the circuit breaker pattern
// Why: Prevents cascade failures from propagating to your service
// Staff-level: This pattern is essential for third-party integrations
// It transforms a synchronous failure into a fast failure
type CircuitBreaker struct {
	config      CircuitBreakerConfig
	state       CircuitState
	failures    int
	successes   int
	lastFailure time.Time
	lastSuccess time.Time
	mu          sync.RWMutex

	// Metrics
	totalRequests  int64
	totalFailures int64
	totalSuccesses int64
	stateChanges   int64
}

// NewCircuitBreaker creates a new circuit breaker with the given configuration
func NewCircuitBreaker(config CircuitBreakerConfig) *CircuitBreaker {
	return &CircuitBreaker{
		config:      config,
		state:       StateClosed,
		failures:    0,
		successes:   0,
		lastFailure: time.Now(),
	}
}

// ErrCircuitOpen is returned when the circuit is open
var ErrCircuitOpen = errors.New("circuit breaker is open")

// Execute runs a function with circuit breaker protection
// Returns ErrCircuitOpen if circuit is open
func (cb *CircuitBreaker) Execute(fn func() error) error {
	cb.mu.Lock()
	defer cb.mu.Unlock()

	// Increment total requests
	cb.totalRequests++

	// Check if circuit should transition
	cb.evaluateState()

	// Reject fast if circuit is open
	if cb.state == StateOpen {
		cb.totalFailures++
		return ErrCircuitOpen
	}

	// Execute the protected function
	err := fn()

	// Record result
	if err != nil {
		cb.recordFailure()
	} else {
		cb.recordSuccess()
	}

	return err
}

// ExecuteWithContext runs a function with circuit breaker protection and context
func (cb *CircuitBreaker) ExecuteWithContext(ctx context.Context, fn func() error) error {
	// Quick check before acquiring lock
	cb.mu.RLock()
	currentState := cb.state
	cb.mu.RUnlock()

	if currentState == StateOpen {
		// Check if we should try half-open
		cb.mu.Lock()
		cb.evaluateState()
		if cb.state == StateOpen {
			cb.mu.Unlock()
			return ErrCircuitOpen
		}
		cb.mu.Unlock()
	}

	err := cb.Execute(fn)
	if err != nil {
		return err
	}

	select {
	case <-ctx.Done():
		return ctx.Err()
	default:
		return nil
	}
}

func (cb *CircuitBreaker) evaluateState() {
	switch cb.state {
	case StateOpen:
		// Check if timeout has elapsed to try half-open
		if time.Since(cb.lastFailure) > cb.config.Timeout {
			cb.transitionTo(StateHalfOpen)
		}
	case StateHalfOpen:
		// Stay half-open until we get enough successes
		if cb.successes >= cb.config.SuccessThreshold {
			cb.transitionTo(StateClosed)
		}
	}
}

func (cb *CircuitBreaker) transitionTo(newState CircuitState) {
	if cb.state != newState {
		cb.state = newState
		cb.stateChanges++
		fmt.Printf("[CircuitBreaker] State transition: %s -> %s\n",
			cb.state.String(), newState.String())
	}
}

func (cb *CircuitBreaker) recordFailure() {
	cb.failures++
	cb.lastFailure = time.Now()
	cb.totalFailures++

	if cb.state == StateHalfOpen {
		// Any failure in half-open immediately opens circuit
		cb.transitionTo(StateOpen)
		cb.successes = 0
	} else if cb.failures >= cb.config.FailureThreshold {
		cb.transitionTo(StateOpen)
	}
}

func (cb *CircuitBreaker) recordSuccess() {
	cb.successes++
	cb.lastSuccess = time.Now()
	cb.totalSuccesses++
}

// State returns the current state of the circuit breaker
func (cb *CircuitBreaker) State() CircuitState {
	cb.mu.RLock()
	defer cb.mu.RUnlock()
	return cb.state
}

// String returns a string representation of the circuit state
func (cs CircuitState) String() string {
	switch cs {
	case StateClosed:
		return "CLOSED"
	case StateOpen:
		return "OPEN"
	case StateHalfOpen:
		return "HALF_OPEN"
	default:
		return "UNKNOWN"
	}
}

// Metrics returns current circuit breaker metrics
func (cb *CircuitBreaker) Metrics() CircuitBreakerMetrics {
	cb.mu.RLock()
	defer cb.mu.RUnlock()

	var successRate float64
	if cb.totalRequests > 0 {
		successRate = float64(cb.totalSuccesses) / float64(cb.totalRequests) * 100
	}

	return CircuitBreakerMetrics{
		State:                 cb.state,
		TotalRequests:        cb.totalRequests,
		TotalFailures:        cb.totalFailures,
		TotalSuccesses:       cb.totalSuccesses,
		SuccessRate:          successRate,
		StateChanges:         cb.stateChanges,
		ConsecutiveFailures:  cb.failures,
		ConsecutiveSuccesses: cb.successes,
	}
}

// CircuitBreakerMetrics holds circuit breaker statistics
type CircuitBreakerMetrics struct {
	State                 CircuitState
	TotalRequests        int64
	TotalFailures        int64
	TotalSuccesses       int64
	SuccessRate          float64
	StateChanges         int64
	ConsecutiveFailures  int
	ConsecutiveSuccesses int
}

// PrintMetrics prints the circuit breaker metrics
func (cb *CircuitBreaker) PrintMetrics() {
	metrics := cb.Metrics()
	fmt.Println("\n" + strings.Repeat("=", 50))
	fmt.Println("CIRCUIT BREAKER METRICS")
	fmt.Println(strings.Repeat("=", 50))
	fmt.Printf("State:                  %s\n", metrics.State)
	fmt.Printf("Total Requests:        %d\n", metrics.TotalRequests)
	fmt.Printf("Total Successes:       %d\n", metrics.TotalSuccesses)
	fmt.Printf("Total Failures:        %d\n", metrics.TotalFailures)
	fmt.Printf("Success Rate:          %.2f%%\n", metrics.SuccessRate)
	fmt.Printf("State Changes:         %d\n", metrics.StateChanges)
	fmt.Printf("Consecutive Failures:  %d\n", metrics.ConsecutiveFailures)
	fmt.Printf("Consecutive Successes: %d\n", metrics.ConsecutiveSuccesses)
	fmt.Println(strings.Repeat("=", 50) + "\n")
}

// ============================================================
// Payment Service with Circuit Breaker - Example Usage
// ============================================================

// PaymentProcessor defines the interface for payment processing
type PaymentProcessor interface {
	ProcessPayment(amount float64) error
}

// PrimaryPaymentProcessor simulates a primary payment provider
type PrimaryPaymentProcessor struct {
	shouldFail bool
	failUntil  time.Time
}

func NewPrimaryPaymentProcessor() *PrimaryPaymentProcessor {
	return &PrimaryPaymentProcessor{
		shouldFail: false,
	}
}

func (p *PrimaryPaymentProcessor) ProcessPayment(amount float64) error {
	// Simulate occasional failures
	if p.shouldFail && time.Now().Before(p.failUntil) {
		return errors.New("payment provider unavailable")
	}
	// Simulate network latency
	time.Sleep(50 * time.Millisecond)
	return nil
}

// FallbackPaymentProcessor simulates an offline payment processor
type FallbackPaymentProcessor struct{}

func (p *FallbackPaymentProcessor) ProcessPayment(amount float64) error {
	// Simulate offline processing (slower but available)
	time.Sleep(200 * time.Millisecond)
	fmt.Printf("[Fallback] Processed payment: $%.2f\n", amount)
	return nil
}

// PaymentServiceWithCircuit demonstrates proper third-party integration
type PaymentServiceWithCircuit struct {
	primary  *PrimaryPaymentProcessor
	fallback PaymentProcessor
	cb       *CircuitBreaker
}

func NewPaymentServiceWithCircuit() *PaymentServiceWithCircuit {
	return &PaymentServiceWithCircuit{
		primary:  NewPrimaryPaymentProcessor(),
		fallback: &FallbackPaymentProcessor{},
		cb: NewCircuitBreaker(CircuitBreakerConfig{
			FailureThreshold: 3,
			SuccessThreshold: 2,
			Timeout:          10 * time.Second,
		}),
	}
}

func (s *PaymentServiceWithCircuit) ProcessPayment(amount float64) error {
	// Try primary with circuit breaker
	err := s.cb.Execute(func() error {
		return s.primary.ProcessPayment(amount)
	})

	// Circuit is open or call failed - use fallback
	if err != nil {
		fmt.Printf("[Circuit] Primary failed: %v, using fallback\n", err)
		return s.fallback.ProcessPayment(amount)
	}

	fmt.Printf("[Circuit] Primary succeeded for: $%.2f\n", amount)
	return nil
}

// SimulateFailures demonstrates circuit breaker behavior
func SimulateFailures() {
	fmt.Println("\n" + strings.Repeat("=", 60))
	fmt.Println("CIRCUIT BREAKER SIMULATION")
	fmt.Println(strings.Repeat("=", 60))

	service := NewPaymentServiceWithCircuit()

	// Phase 1: Normal operation
	fmt.Println("\n--- Phase 1: Normal Operation ---")
	for i := 0; i < 5; i++ {
		service.ProcessPayment(100.0)
		service.cb.PrintMetrics()
	}

	// Phase 2: Primary fails - circuit opens
	fmt.Println("\n--- Phase 2: Primary Fails ---")
	service.primary.shouldFail = true
	service.primary.failUntil = time.Now().Add(30 * time.Second)

	for i := 0; i < 5; i++ {
		service.ProcessPayment(100.0)
		service.cb.PrintMetrics()
	}

	// Phase 3: Circuit open - fallback used
	fmt.Println("\n--- Phase 3: Circuit Open - Fallback Used ---")
	time.Sleep(500 * time.Millisecond)
	for i := 0; i < 3; i++ {
		service.ProcessPayment(100.0)
		service.cb.PrintMetrics()
	}

	// Phase 4: Recovery - circuit half-open
	fmt.Println("\n--- Phase 4: Recovery ---")
	service.primary.shouldFail = false
	time.Sleep(11 * time.Second) // Wait for timeout

	for i := 0; i < 5; i++ {
		service.ProcessPayment(100.0)
		service.cb.PrintMetrics()
	}
}

// ============================================================
// HTTP Middleware Circuit Breaker
// ============================================================

// HTTPCircuitBreaker creates an HTTP middleware that wraps requests in a circuit breaker
type HTTPCircuitBreaker struct {
	circuitBreaker *CircuitBreaker
	handler        http.Handler
}

func NewHTTPCircuitBreaker(handler http.Handler, config CircuitBreakerConfig) *HTTPCircuitBreaker {
	return &HTTPCircuitBreaker{
		circuitBreaker: NewCircuitBreaker(config),
		handler:        handler,
	}
}

func (hcb *HTTPCircuitBreaker) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	err := hcb.circuitBreaker.Execute(func() error {
		// Create a context with timeout
		ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
		defer cancel()

		// Create a response recorder to capture the result
		rec := &statusRecorder{ResponseWriter: w, statusCode: 200}

		// Execute the handler
		handlerChan := make(chan error, 1)
		go func() {
			handlerChan <- nil
			hcb.handler.ServeHTTP(rec, r.WithContext(ctx))
		}()

		select {
		case err := <-handlerChan:
			return err
		case <-ctx.Done():
			return ctx.Err()
		}
	})

	if err != nil {
		if err == ErrCircuitOpen {
			w.WriteHeader(http.StatusServiceUnavailable)
			w.Write([]byte("Service temporarily unavailable"))
			return
		}
		w.WriteHeader(http.StatusInternalServerError)
		w.Write([]byte(err.Error()))
		return
	}
}

// statusRecorder wraps http.ResponseWriter to capture status code
type statusRecorder struct {
	http.ResponseWriter
	statusCode int
}

func (rec *statusRecorder) WriteHeader(code int) {
	rec.statusCode = code
	rec.ResponseWriter.WriteHeader(code)
}
