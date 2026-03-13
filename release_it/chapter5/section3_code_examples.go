package main

import (
	"context"
	"errors"
	"fmt"
	"math"
	"math/rand"
	"sync"
	"time"
)

// =============================================================================
// SECTION 3: ANNOTATED CODE EXAMPLES
// =============================================================================
// These examples demonstrate patterns for handling infrastructure variability
// as discussed in Chapter 5 of "Release It!"
// =============================================================================

// =============================================================================
// EXAMPLE 1: Handling Variable Latency with Timeout and Backoff
// =============================================================================

// ErrTimeout represents a timeout error
var ErrTimeout = errors.New("operation timed out")

// ErrCircuitOpen represents an open circuit breaker
var ErrCircuitOpen = errors.New("circuit breaker is open")

// InfrastructureClient simulates a client making requests to infrastructure
// that has variable latency due to virtualization/ hardware issues
type InfrastructureClient struct {
	name          string
	baseLatency   time.Duration
	variance      time.Duration // This represents the variability from virtualization
	failureRate   float64
	circuitOpen   bool
	failureCount  int
	successCount  int
	mu            sync.Mutex
}

// NewInfrastructureClient creates a client with specified characteristics
// Why: In production, you need to model infrastructure variability to test resilience
func NewInfrastructureClient(name string, baseLatency, variance time.Duration, failureRate float64) *InfrastructureClient {
	return &InfrastructureClient{
		name:        name,
		baseLatency: baseLatency,
		variance:    variance,
		failureRate: failureRate,
	}
}

// SimulateRequest makes a request with variable latency
// The variance simulates: CPU steal, I/O wait, network virtualization overhead
func (c *InfrastructureClient) SimulateRequest(ctx context.Context) (string, error) {
	c.mu.Lock()
	defer c.mu.Unlock()

	if c.circuitOpen {
		return "", ErrCircuitOpen
	}

	// Simulate variable latency (the "un-virtualized ground" problem)
	// Staff-level insight: This is what happens when noisy neighbors consume resources
	actualLatency := c.baseLatency + time.Duration(rand.Float64()*float64(c.variance))

	// Check for timeout
	select {
	case <-ctx.Done():
		c.failureCount++
		return "", ctx.Err()
	default:
	}

	// Simulate the request
	time.Sleep(actualLatency)

	// Simulate random failures (hardware issues, network problems)
	// Staff-level insight: Random failures often come from hardware, not code
	if rand.Float64() < c.failureRate {
		c.failureCount++
		return "", errors.New("infrastructure failure")
	}

	c.successCount++
	return fmt.Sprintf("response from %s (latency: %v)", c.name, actualLatency), nil
}

// =============================================================================
// NAIVE APPROACH: No timeouts, no resilience
// =============================================================================

// NaiveRequestWithoutTimeout demonstrates what most developers do
// ❌ This will hang indefinitely when infrastructure has issues
func NaiveRequestWithoutTimeout(client *InfrastructureClient) (string, error) {
	// BAD: No context, no timeout
	// When the hypervisor throttles CPU or I/O waits spike, this hangs forever
	result, err := client.SimulateRequest(context.Background())
	if err != nil {
		return "", fmt.Errorf("request failed: %w", err)
	}
	return result, nil
}

// =============================================================================
// PRODUCTION APPROACH: Timeout with context
// =============================================================================

// RequestWithTimeout demonstrates proper timeout handling
// Why: Infrastructure variability means operations can take arbitrarily long
// Staff-level insight: Timeout is your circuit breaker at the request level
func RequestWithTimeout(client *InfrastructureClient, timeout time.Duration) (string, error) {
	// GOOD: Create context with timeout
	// This prevents hanging when VM migration or noisy neighbors cause delays
	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	defer cancel()

	result, err := client.SimulateRequest(ctx)
	if err != nil {
		if errors.Is(err, context.DeadlineExceeded) {
			return "", fmt.Errorf("%w: infrastructure latency exceeded %v", ErrTimeout, timeout)
		}
		return "", fmt.Errorf("request failed: %w", err)
	}
	return result, nil
}

// =============================================================================
// EXAMPLE 2: Circuit Breaker Pattern
// =============================================================================

// CircuitBreakerState represents the state of a circuit breaker
type CircuitBreakerState int

const (
	CircuitClosed CircuitBreakerState = iota
	CircuitOpen
	CircuitHalfOpen
)

// CircuitBreaker prevents cascading failures from infrastructure issues
// Why: When infrastructure is failing, don't keep hammering it
// Staff-level insight: This is the application-level defense against bad hardware
type CircuitBreaker struct {
	mu               sync.Mutex
	state            CircuitBreakerState
	failureThreshold int
	successThreshold int
	failureCount     int
	successCount     int
	lastFailureTime  time.Time
	openDuration    time.Duration
}

// NewCircuitBreaker creates a circuit breaker with specified thresholds
func NewCircuitBreaker(failureThreshold int, openDuration time.Duration) *CircuitBreaker {
	return &CircuitBreaker{
		state:            CircuitClosed,
		failureThreshold: failureThreshold,
		openDuration:     openDuration,
	}
}

// Execute runs a function through the circuit breaker
// Staff-level insight: This pattern comes from electrical engineering - fail fast
// to prevent damage (in this case, cascading failures)
func (cb *CircuitBreaker) Execute(fn func() error) error {
	cb.mu.Lock()
	defer cb.mu.Unlock()

	switch cb.state {
	case CircuitOpen:
		// Check if we should try half-open
		if time.Since(cb.lastFailureTime) > cb.openDuration {
			cb.state = CircuitHalfOpen
			cb.successCount = 0
		} else {
			return ErrCircuitOpen
		}
	case CircuitHalfOpen:
		// Allow limited requests to test recovery
	}

	err := fn()

	if err != nil {
		cb.recordFailure()
		return err
	}

	cb.recordSuccess()
	return nil
}

func (cb *CircuitBreaker) recordFailure() {
	cb.failureCount++
	cb.lastFailureTime = time.Now()

	if cb.state == CircuitHalfOpen {
		cb.state = CircuitOpen // Failed during test, go back to open
	} else if cb.failureCount >= cb.failureThreshold {
		cb.state = CircuitOpen // Too many failures, open the circuit
	}
}

func (cb *CircuitBreaker) recordSuccess() {
	cb.successCount++

	if cb.state == CircuitHalfOpen {
		if cb.successCount >= cb.successThreshold {
			cb.state = CircuitClosed
			cb.failureCount = 0
		}
	} else {
		// Reset failure count on success in closed state
		cb.failureCount = 0
	}
}

// GetState returns the current state of the circuit breaker
func (cb *CircuitBreaker) GetState() CircuitBreakerState {
	cb.mu.Lock()
	defer cb.mu.Unlock()
	return cb.state
}

// =============================================================================
// EXAMPLE 3: Retry with Exponential Backoff
// =============================================================================

// RetryConfig holds configuration for retry behavior
type RetryConfig struct {
	MaxRetries     int
	InitialDelay   time.Duration
	MaxDelay       time.Duration
	Multiplier     float64
	ShouldRetry    func(error) bool
}

// DefaultRetryConfig returns sensible defaults for infrastructure retries
// Why: Infrastructure failures are often transient (temp CPU spike, brief I/O wait)
func DefaultRetryConfig() *RetryConfig {
	return &RetryConfig{
		MaxRetries:   3,
		InitialDelay: 100 * time.Millisecond,
		MaxDelay:     5 * time.Second,
		Multiplier:   2.0,
		ShouldRetry: func(err error) bool {
			// Don't retry on circuit open or explicit non-retryable errors
			if errors.Is(err, ErrCircuitOpen) {
				return false
			}
			return true
		},
	}
}

// RetryWithBackoff demonstrates retry with exponential backoff
// Staff-level insight: The backoff allows infrastructure to recover
// (VM migration completes, noisy neighbor's job ends, etc.)
func RetryWithBackoff(client *InfrastructureClient, cfg *RetryConfig) (string, error) {
	var lastErr error
	delay := cfg.InitialDelay

	for attempt := 0; attempt <= cfg.MaxRetries; attempt++ {
		if attempt > 0 {
			// Add jitter to prevent thundering herd
			jitter := time.Duration(rand.Float64() * float64(delay))
			fmt.Printf("Retry %d: waiting %v before retry...\n", attempt, delay+jitter)
			time.Sleep(delay + jitter)

			// Exponential backoff
			delay = time.Duration(math.Min(
				float64(delay)*cfg.Multiplier,
				float64(cfg.MaxDelay),
			))
		}

		ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
		defer cancel()

		result, err := client.SimulateRequest(ctx)
		if err == nil {
			return result, nil
		}

		lastErr = err

		// Check if we should retry this error
		if cfg.ShouldRetry != nil && !cfg.ShouldRetry(err) {
			return "", err
		}

		fmt.Printf("Attempt %d failed: %v\n", attempt+1, err)
	}

	return "", fmt.Errorf("all retries exhausted, last error: %w", lastErr)
}

// =============================================================================
// EXAMPLE 4: Graceful Degradation
// =============================================================================

// ServiceLevel represents different levels of service capability
type ServiceLevel int

const (
	LevelFull ServiceLevel = iota
	LevelDegraded
	LevelMinimal
	LevelDown
)

// DegradedService demonstrates graceful degradation
// Why: When infrastructure is struggling, reduce load rather than crash
// Staff-level insight: This is the "safety valve" pattern from the chapter
type DegradedService struct {
	client          *InfrastructureClient
	currentLevel    ServiceLevel
	requestsFull    int
	requestsDegraded int
	requestsMinimal int
	mu              sync.Mutex
}

// NewDegradedService creates a service with graceful degradation capability
func NewDegradedService(client *InfrastructureClient) *DegradedService {
	return &DegradedService{
		client:       client,
		currentLevel: LevelFull,
	}
}

// HandleRequest handles a request with appropriate degradation
// Staff-level insight: At LevelDegraded, we skip expensive operations
// At LevelMinimal, we return cached/stale data if possible
func (s *DegradedService) HandleRequest(ctx context.Context) (string, error) {
	s.mu.Lock()
	level := s.currentLevel
	s.mu.Unlock()

	switch level {
	case LevelFull:
		return s.handleFull(ctx)
	case LevelDegraded:
		return s.handleDegraded(ctx)
	case LevelMinimal:
		return s.handleMinimal(ctx)
	default:
		return "", errors.New("service unavailable")
	}
}

func (s *DegradedService) handleFull(ctx context.Context) (string, error) {
	s.mu.Lock()
	s.requestsFull++
	s.mu.Unlock()

	// Full processing - make the infrastructure call
	result, err := s.client.SimulateRequest(ctx)
	if err != nil {
		// If we fail repeatedly, degrade
		s.mu.Lock()
		if s.requestsFull > 5 {
			s.currentLevel = LevelDegraded
			fmt.Println("⚠️ Degrading to LevelDegraded")
		}
		s.mu.Unlock()
	}
	return result, err
}

func (s *DegradedService) handleDegraded(ctx context.Context) (string, error) {
	s.mu.Lock()
	s.requestsDegraded++
	s.mu.Unlock()

	// Skip expensive operations - maybe just cache check
	// For demo, we'll use a shorter timeout
	ctx, cancel := context.WithTimeout(ctx, 500*time.Millisecond)
	defer cancel()

	result, err := s.client.SimulateRequest(ctx)
	if err != nil {
		s.mu.Lock()
		s.currentLevel = LevelMinimal
		fmt.Println("⚠️ Degrading to LevelMinimal")
		s.mu.Unlock()
	}
	return result, err
}

func (s *DegradedService) handleMinimal(ctx context.Context) (string, error) {
	s.mu.Lock()
	s.requestsMinimal++
	s.mu.Unlock()

	// Return cached or fallback data
	// For demo, this would be cached response
	return "cached_response", nil
}

// GetStats returns current service statistics
func (s *DegradedService) GetStats() (full, degraded, minimal int) {
	s.mu.Lock()
	defer s.mu.Unlock()
	return s.requestsFull, s.requestsDegraded, s.requestsMinimal
}

// =============================================================================
// MAIN: Demonstration
// =============================================================================

func main() {
	fmt.Println("╔════════════════════════════════════════════════════════════════╗")
	fmt.Println("║  Chapter 5: Handling Infrastructure Variability Demo         ║")
	fmt.Println("║  (The Un-virtualized Ground)                                  ║")
	fmt.Println("╚════════════════════════════════════════════════════════════════╝")
	fmt.Println()

	// Create a client with high variance (simulating problematic infrastructure)
	// base: 100ms, variance: 500ms, failure rate: 10%
	client := NewInfrastructureClient("problematic-db", 100*time.Millisecond, 500*time.Millisecond, 0.1)

	// Demo 1: Naive approach - will hang
	fmt.Println("--- Demo 1: Naive Request (no timeout) ---")
	fmt.Println("⚠️  This would hang indefinitely in production")
	// result, _ := NaiveRequestWithoutTimeout(client) // Don't run this!

	// Demo 2: With timeout
	fmt.Println("\n--- Demo 2: Request with Timeout ---")
	result, err := RequestWithTimeout(client, 200*time.Millisecond)
	if err != nil {
		fmt.Printf("✓ Correctly handled: %v\n", err)
	} else {
		fmt.Printf("✓ Success: %s\n", result)
	}

	// Demo 3: Circuit Breaker
	fmt.Println("\n--- Demo 3: Circuit Breaker ---")
	cb := NewCircuitBreaker(3, 5*time.Second) // Open after 3 failures

	for i := 0; i < 10; i++ {
		err := cb.Execute(func() error {
			// 50% failure rate to trip circuit
			if rand.Float64() > 0.5 {
				return errors.New("simulated failure")
			}
			return nil
		})

		state := []string{"CLOSED", "OPEN", "HALF-OPEN"}[cb.GetState()]
		if err != nil {
			fmt.Printf("Request %d: FAILED - %v [Circuit: %s]\n", i+1, err, state)
		} else {
			fmt.Printf("Request %d: SUCCESS [Circuit: %s]\n", i+1, state)
		}

		if cb.GetState() == CircuitOpen {
			fmt.Println("→ Circuit opened! Further requests will fail fast.")
			break
		}
	}

	// Demo 4: Retry with Backoff
	fmt.Println("\n--- Demo 4: Retry with Exponential Backoff ---")
	client2 := NewInfrastructureClient("unreliable-service", 50*time.Millisecond, 100*time.Millisecond, 0.3)
	result, err = RetryWithBackoff(client2, DefaultRetryConfig())
	if err != nil {
		fmt.Printf("✓ All retries failed: %v\n", err)
	} else {
		fmt.Printf("✓ Success after retries: %s\n", result)
	}

	// Demo 5: Graceful Degradation
	fmt.Println("\n--- Demo 5: Graceful Degradation ---")
	client3 := NewInfrastructureClient("degrading-service", 100*time.Millisecond, 50*time.Millisecond, 0.4)
	service := NewDegradedService(client3)

	for i := 0; i < 10; i++ {
		result, err := service.HandleRequest(context.Background())
		if err != nil {
			fmt.Printf("Request %d: %v\n", i+1, err)
		} else {
			fmt.Printf("Request %d: %s\n", i+1, result)
		}
		time.Sleep(100 * time.Millisecond)
	}

	full, degraded, minimal := service.GetStats()
	fmt.Printf("\nStats - Full: %d, Degraded: %d, Minimal: %d\n", full, degraded, minimal)

	fmt.Println("\n✅ Demo complete!")
}
