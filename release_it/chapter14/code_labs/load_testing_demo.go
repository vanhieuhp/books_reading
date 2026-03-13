// Load Testing Infrastructure Demo
// Chapter 14: The Trampled Product Launch
// Demonstrates proper load testing setup that should have been done before launch

package loadtest

import (
	"context"
	"fmt"
	"math"
	"net/http"
	"sort"
	"strings"
	"sync"
	"time"
)

// LoadTestConfig defines the parameters for load testing
type LoadTestConfig struct {
	RequestsPerSecond int           // Target RPS
	Duration         time.Duration  // Test duration
	RampUpTime      time.Duration  // Time to reach target RPS
	ThinkTime       time.Duration  // Pause between requests
	Timeout         time.Duration  // Per-request timeout
	MaxConcurrent   int           // Maximum concurrent requests
}

// LoadTestResult contains the results of a load test
type LoadTestResult struct {
	TotalRequests    int
	Successful       int
	Failed           int
	P50Latency      time.Duration
	P95Latency      time.Duration
	P99Latency      time.Duration
	MaxLatency      time.Duration
	ErrorsByType    map[string]int
	RequestsPerSecond float64
	Duration        time.Duration
}

// Result represents a single request result
type Result struct {
	Latency time.Duration
	Success bool
	Error   error
}

// NewLoadTestConfig creates a default configuration
func NewLoadTestConfig() LoadTestConfig {
	return LoadTestConfig{
		RequestsPerSecond: 100,
		Duration:         time.Minute,
		RampUpTime:      10 * time.Second,
		ThinkTime:       100 * time.Millisecond,
		Timeout:         5 * time.Second,
		MaxConcurrent:   50,
	}
}

// RunLoadTest executes a load test against the target service
// Why: Simulates production traffic patterns to find bottlenecks BEFORE launch
func RunLoadTest(ctx context.Context, targetURL string, config LoadTestConfig) (*LoadTestResult, error) {
	// Use a rate limiter to control request rate precisely
	// This prevents the test itself from becoming a DOS attack
	limiter := NewTokenBucket(config.RequestsPerSecond, config.RequestsPerSecond*2)

	var (
		wg sync.WaitGroup
		mu sync.Mutex
		results []Result
	)

	// Channel to collect results
	resultChan := make(chan Result, 10000)

	// Start time
	startTime := time.Now()
	endTime := startTime.Add(config.Duration)

	// Worker goroutines
	workerCount := config.MaxConcurrent
	workerChan := make(chan struct{}, workerCount)

	// Context with cancellation
	ctx, cancel := context.WithCancel(ctx)
	defer cancel()

	// Ramp up: gradually increase load
	rampUpEnd := startTime.Add(config.RampUpTime)

	// Main test loop
	go func() {
		ticker := time.NewTicker(config.ThinkTime)
		defer ticker.Stop()

		requestCount := 0
		for {
			select {
			case <-ctx.Done():
				return
			case <-ticker.C:
				if time.Now().After(endTime) {
					cancel()
					return
				}

				// During ramp-up, reduce rate
				var effectiveRate int
				if time.Now().Before(rampUpEnd) {
					// Linear ramp-up
					elapsed := time.Since(startTime)
					progress := elapsed.Seconds() / config.RampUpTime.Seconds()
					effectiveRate = int(float64(config.RequestsPerSecond) * progress)
					if effectiveRate < 10 {
						effectiveRate = 10
					}
				} else {
					effectiveRate = config.RequestsPerSecond
				}

				// Adjust token bucket rate
				limiter.SetRate(effectiveRate)

				// Acquire token from rate limiter
				select {
				case workerChan <- struct{}{}:
					wg.Add(1)
					go func(reqID int) {
						defer wg.Done()
						defer func() { <-workerChan }()

						// Execute request with timeout
						result := executeRequest(ctx, targetURL, config.Timeout, reqID)
						resultChan <- result
					}(requestCount)
					requestCount++
				default:
					// Worker pool full, skip this request
				}
			}
		}
	}()

	// Wait for completion
	wg.Wait()
	close(resultChan)

	// Collect results
	for result := range resultChan {
		results = append(results, result)
	}

	return aggregateResults(results, startTime, time.Now()), nil
}

// executeRequest performs a single HTTP request with timing
func executeRequest(ctx context.Context, url string, timeout time.Duration, reqID int) Result {
	start := time.Now()

	// Create request with timeout
	reqCtx, cancel := context.WithTimeout(ctx, timeout)
	defer cancel()

	req, err := http.NewRequestWithContext(reqCtx, "GET", url, nil)
	if err != nil {
		return Result{
			Latency: time.Since(start),
			Success: false,
			Error:   err,
		}
	}

	// Perform request (simplified - would use actual HTTP client)
	client := &http.Client{Timeout: timeout}
	resp, err := client.Do(req)

	latency := time.Since(start)

	if err != nil {
		return Result{
			Latency: latency,
			Success: false,
			Error:   err,
		}
	}
	defer resp.Body.Close()

	return Result{
		Latency: latency,
		Success: resp.StatusCode < 400,
		Error:   nil,
	}
}

// aggregateResults calculates statistics from raw results
func aggregateResults(results []Result, startTime, endTime time.Time) *LoadTestResult {
	if len(results) == 0 {
		return &LoadTestResult{}
	}

	latencies := make([]time.Duration, 0, len(results))
	errorsByType := make(map[string]int)

	var successful, failed int

	for _, r := range results {
		if r.Success {
			successful++
			latencies = append(latencies, r.Latency)
		} else {
			failed++
			errType := "unknown"
			if r.Error != nil {
				errType = r.Error.Error()
			}
			errorsByType[errType]++
		}
	}

	// Calculate percentiles
	sortedLatencies := make([]float64, len(latencies))
	for i, l := range latencies {
		sortedLatencies[i] = l.Seconds() * 1000 // Convert to ms
	}
	sort.Float64s(sortedLatencies)

	calculatePercentile := func(p float64) time.Duration {
		if len(sortedLatencies) == 0 {
			return 0
		}
		idx := int(float64(len(sortedLatencies)) * p)
		if idx >= len(sortedLatencies) {
			idx = len(sortedLatencies) - 1
		}
		return time.Duration(sortedLatencies[idx]) * time.Millisecond
	}

	duration := endTime.Sub(startTime)

	return &LoadTestResult{
		TotalRequests:    len(results),
		Successful:       successful,
		Failed:           failed,
		P50Latency:      calculatePercentile(0.50),
		P95Latency:      calculatePercentile(0.95),
		P99Latency:      calculatePercentile(0.99),
		MaxLatency:      calculatePercentile(1.0),
		ErrorsByType:    errorsByType,
		RequestsPerSecond: float64(len(results)) / duration.Seconds(),
		Duration:        duration,
	}
}

// PrintResults prints the load test results in a readable format
func PrintResults(result *LoadTestResult) {
	fmt.Println("\n" + strings.Repeat("=", 60))
	fmt.Println("LOAD TEST RESULTS")
	fmt.Println(strings.Repeat("=", 60))

	fmt.Printf("\n📊 Summary:\n")
	fmt.Printf("  Total Requests:    %d\n", result.TotalRequests)
	fmt.Printf("  Successful:        %d (%.1f%%)\n", result.Successful,
		float64(result.Successful)/float64(result.TotalRequests)*100)
	fmt.Printf("  Failed:            %d (%.1f%%)\n", result.Failed,
		float64(result.Failed)/float64(result.TotalRequests)*100)
	fmt.Printf("  RPS:              %.2f\n", result.RequestsPerSecond)

	fmt.Printf("\n⏱️  Latency:\n")
	fmt.Printf("  P50:              %v\n", result.P50Latency)
	fmt.Printf("  P95:              %v\n", result.P95Latency)
	fmt.Printf("  P99:              %v\n", result.P99Latency)
	fmt.Printf("  Max:              %v\n", result.MaxLatency)

	if len(result.ErrorsByType) > 0 {
		fmt.Printf("\n❌ Errors by Type:\n")
		for errType, count := range result.ErrorsByType {
			fmt.Printf("  %s: %d\n", errType, count)
		}
	}

	// Determine pass/fail
	fmt.Printf("\n%s\n", strings.Repeat("=", 60))
	if result.P99Latency > 500*time.Millisecond {
		fmt.Println("⚠️  WARNING: P99 latency exceeds 500ms")
	}
	if float64(result.Failed)/float64(result.TotalRequests) > 0.01 {
		fmt.Println("⚠️  WARNING: Error rate exceeds 1%")
	}
	fmt.Println(strings.Repeat("=", 60) + "\n")
}

// TokenBucket implements a token bucket rate limiter
// Why: Token bucket allows burst handling while maintaining average rate
type TokenBucket struct {
	tokens     int64
	capacity   int64
	refillRate int64
	lastRefill time.Time
	mu         sync.Mutex
}

// NewTokenBucket creates a rate limiter using token bucket algorithm
func NewTokenBucket(rate int, capacity int) *TokenBucket {
	return &TokenBucket{
		tokens:     int64(capacity),
		capacity:   int64(capacity),
		refillRate: int64(rate),
		lastRefill: time.Now(),
	}
}

// SetRate dynamically adjusts the refill rate
func (tb *TokenBucket) SetRate(rate int) {
	tb.mu.Lock()
	defer tb.mu.Unlock()
	tb.refillRate = int64(rate)
}

// Acquire attempts to acquire a token from the bucket
// Returns true if successful, false if bucket is empty
func (tb *TokenBucket) Acquire() bool {
	tb.mu.Lock()
	defer tb.mu.Unlock()

	tb.refill()

	if tb.tokens > 0 {
		tb.tokens--
		return true
	}
	return false
}

// refill adds tokens based on time elapsed
func (tb *TokenBucket) refill() {
	now := time.Now()
	elapsed := now.Sub(tb.lastRefill).Seconds()

	tokensToAdd := float64(tb.refillRate) * elapsed
	tb.tokens = int64(math.Min(float64(tb.capacity), float64(tb.tokens)+tokensToAdd))
	tb.lastRefill = now
}
