# Section 7: Step-by-Step Code Lab

## Lab: Building Infrastructure-Aware Retry Logic

### 🎯 Goal
Build a production-grade retry mechanism that handles infrastructure variability - the core pattern from Chapter 5. You'll implement exponential backoff, circuit breakers, and jitter to handle the "un-virtualized ground."

### ⏱ Time
~25 minutes

### 🛠 Requirements
- Go 1.18+ OR Python 3.9+
- Basic understanding of concurrency (Goroutines/async)
- Terminal to run the code

---

## Step 1: Setup

Create a new directory for the lab:

```bash
mkdir infrastructure-lab
cd infrastructure-lab
```

Choose your language:

**Go:**
```bash
go mod init infrastructure-lab
```

**Python:**
```bash
# No setup needed - we'll use standard library
```

---

## Step 2: Implement the Naive Version

The naive approach: retry immediately, no backoff, no circuit breaking.

### Go Implementation

```go
// naive_retry.go
package main

import (
	"fmt"
	"math/rand"
	"time"
)

// SimulatedService simulates a flaky infrastructure service
type SimulatedService struct {
	failureRate float64
	callCount   int
}

func NewSimulatedService(failureRate float64) *SimulatedService {
	return &SimulatedService{failureRate: failureRate}
}

func (s *SimulatedService) Call() (string, error) {
	s.callCount++
	// Simulate variable latency (infrastructure variability)
	latency := time.Duration(50+rand.Intn(100)) * time.Millisecond
	time.Sleep(latency)

	// Simulate random failures
	if rand.Float64() < s.failureRate {
		return "", fmt.Errorf("infrastructure error")
	}
	return "success", nil
}

// ❌ NAIVE: Retry immediately without any strategy
func naiveRetry(service *SimulatedService, maxRetries int) (string, error) {
	for attempt := 0; attempt <= maxRetries; attempt++ {
		result, err := service.Call()
		if err == nil {
			return result, nil
		}
		fmt.Printf("Attempt %d failed: %v (retrying immediately...)\n", attempt+1, err)
	}
	return "", fmt.Errorf("all retries failed")
}

func main() {
	service := NewSimulatedService(0.5) // 50% failure rate

	fmt.Println("=== NAIVE RETRY (no backoff) ===")
	start := time.Now()
	result, err := naiveRetry(service, 5)
	elapsed := time.Since(start)

	if err != nil {
		fmt.Printf("FAILED: %v\n", err)
	} else {
		fmt.Printf("SUCCESS: %s\n", result)
	}
	fmt.Printf("Total calls: %d, Time: %v\n", service.callCount, elapsed)
}
```

### Python Implementation

```python
# naive_retry.py
import random
import time
from typing import Optional


class SimulatedService:
    """Simulates a flaky infrastructure service"""

    def __init__(self, failure_rate: float):
        self.failure_rate = failure_rate
        self.call_count = 0

    def call(self) -> str:
        self.call_count += 1

        # Simulate variable latency (infrastructure variability)
        latency_ms = random.randint(50, 150)
        time.sleep(latency_ms / 1000)

        # Simulate random failures
        if random.random() < self.failure_rate:
            raise ConnectionError("infrastructure error")

        return "success"


def naive_retry(service: SimulatedService, max_retries: int) -> tuple[Optional[str], Optional[Exception]]:
    """NAIVE: Retry immediately without any strategy"""

    for attempt in range(max_retries + 1):
        try:
            return service.call(), None
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e} (retrying immediately...)")

    return None, Exception("all retries failed")


if __name__ == "__main__":
    service = SimulatedService(0.5)  # 50% failure rate

    print("=== NAIVE RETRY (no backoff) ===")
    start = time.time()
    result, err = naive_retry(service, 5)
    elapsed = time.time() - start

    if err:
        print(f"FAILED: {err}")
    else:
        print(f"SUCCESS: {result}")
    print(f"Total calls: {service.call_count}, Time: {elapsed:.2f}s")
```

### Run and Observe

```bash
# Go
go run naive_retry.go

# Python
python naive_retry.py
```

**Expected Output:**
```
=== NAIVE RETRY (no backoff) ===
Attempt 1 failed: infrastructure error (retrying immediately...)
Attempt 2 failed: infrastructure error (retrying immediately...)
Attempt 3 failed: infrastructure error (retrying immediately...)
Attempt 4 failed: infrastructure error (retrying immediately...)
Attempt 5 failed: infrastructure error (retrying immediately...)
Attempt 6 failed: infrastructure error (retrying immediately...)
FAILED: all retries failed
Total calls: 6, Time: 0.6s
```

**Problems Identified:**
- ❌ Retries happen too fast - doesn't give infrastructure time to recover
- ❌ No jitter - all clients retry at same time (thundering herd)
- ❌ No circuit breaker - keeps hammering failing service
- ❌ No distinction between transient and permanent failures

---

## Step 3: Implement Production-Grade Retry

Now implement the production approach with exponential backoff, jitter, and circuit breaker.

### Go Implementation

```go
// production_retry.go
package main

import (
	"context"
	"errors"
	"fmt"
	"math"
	"math/rand"
	"time"
)

// =============================================================================
// Circuit Breaker - Prevents hammering failing services
// =============================================================================

type CircuitState int

const (
	CircuitClosed CircuitState = iota
	CircuitOpen
	CircuitHalfOpen
)

type CircuitBreaker struct {
	failures         int
	successes        int
	state            CircuitState
	failureThreshold int
	successThreshold int
	timeout          time.Duration
	lastFailure      time.Time
}

func NewCircuitBreaker(failureThreshold int, timeout time.Duration) *CircuitBreaker {
	return &CircuitBreaker{
		failureThreshold: failureThreshold,
		timeout:          timeout,
		state:            CircuitClosed,
	}
}

func (cb *CircuitBreaker) Execute(fn func() error) error {
	switch cb.state {
	case CircuitOpen:
		if time.Since(cb.lastFailure) > cb.timeout {
			cb.state = CircuitHalfOpen
			cb.successes = 0
		} else {
			return errors.New("circuit open")
		}
	case CircuitHalfOpen:
		// Allow through to test
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
	cb.failures++
	cb.lastFailure = time.Now()

	if cb.state == CircuitHalfOpen {
		cb.state = CircuitOpen
	} else if cb.failures >= cb.failureThreshold {
		cb.state = CircuitOpen
	}
}

func (cb *CircuitBreaker) recordSuccess() {
	cb.successes++
	cb.failures = 0 // Reset failures on success

	if cb.state == CircuitHalfOpen && cb.successes >= cb.successThreshold {
		cb.state = CircuitClosed
	}
}

func (cb *CircuitBreaker) State() string {
	states := []string{"CLOSED", "OPEN", "HALF_OPEN"}
	return states[cb.state]
}

// =============================================================================
// Retry with Backoff and Jitter
// =============================================================================

type RetryConfig struct {
	MaxRetries     int
	BaseDelay      time.Duration
	MaxDelay       time.Duration
	Multiplier     float64
	Jitter         bool
}

func NewRetryConfig() *RetryConfig {
	return &RetryConfig{
		MaxRetries: 5,
		BaseDelay:  100 * time.Millisecond,
		MaxDelay:   5 * time.Second,
		Multiplier: 2.0,
		Jitter:     true,
	}
}

// ✅ PRODUCTION: Retry with exponential backoff and jitter
func RetryWithBackoff(
	ctx context.Context,
	cb *CircuitBreaker,
	service *SimulatedService,
	cfg *RetryConfig,
) (string, error) {

	var lastErr error
	delay := cfg.BaseDelay

	for attempt := 0; attempt <= cfg.MaxRetries; attempt++ {
		// Check circuit breaker first
		err := cb.Execute(func() error {
			return ctx.Err() // Check for cancellation
		})
		if err != nil {
			return "", err
		}

		// Attempt the call through circuit breaker
		result, err := cb.Execute(func() error {
			return ctx.Err()
		})
		if err != nil {
			return "", err
		}
		_ = result // unused

		// Actually call the service
		result, err = service.Call()
		if err == nil {
			return result, nil
		}

		lastErr = err

		// Don't retry if circuit opened during call
		if cb.State() == "OPEN" {
			return "", errors.New("circuit opened during retry")
		}

		// Calculate delay with exponential backoff
		if attempt < cfg.MaxRetries {
			actualDelay := delay
			if cfg.Jitter {
				// Add jitter: 0.5-1.5x to prevent thundering herd
				jitter := 0.5 + rand.Float64()
				actualDelay = time.Duration(float64(delay) * jitter)
			}

			fmt.Printf("Attempt %d failed: %v. Retrying in %v...\n",
				attempt+1, err, actualDelay)

			select {
			case <-ctx.Done():
				return "", ctx.Err()
			case <-time.After(actualDelay):
			}

			// Exponential backoff
			delay = time.Duration(math.Min(
				float64(delay)*cfg.Multiplier,
				float64(cfg.MaxDelay),
			))
		}
	}

	return "", fmt.Errorf("all retries exhausted: %w", lastErr)
}

func main() {
	rand.Seed(time.Now().UnixNano())

	service := NewSimulatedService(0.4) // 40% failure rate
	cb := NewCircuitBreaker(3, 2*time.Second)
	cfg := NewRetryConfig()

	fmt.Println("=== PRODUCTION RETRY (with backoff + circuit breaker) ===")

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	start := time.Now()
	result, err := RetryWithBackoff(ctx, cb, service, cfg)
	elapsed := time.Since(start)

	if err != nil {
		fmt.Printf("FAILED: %v\n", err)
	} else {
		fmt.Printf("SUCCESS: %s\n", result)
	}
	fmt.Printf("Total calls: %d, Time: %v, Circuit: %s\n",
		service.callCount, elapsed, cb.State())
}
```

### Python Implementation

```python
# production_retry.py
import asyncio
import random
import time
from dataclasses import dataclass, field
from typing import Optional, Callable
import contextlib


@dataclass
class CircuitBreaker:
    """Circuit breaker pattern implementation"""

    failure_threshold: int = 3
    success_threshold: int = 2
    timeout: float = 2.0

    _state: str = "closed"
    _failures: int = 0
    _successes: int = 0
    _last_failure: Optional[float] = None

    @property
    def state(self) -> str:
        if self._state == "open" and self._last_failure:
            if time.time() - self._last_failure > self.timeout:
                self._state = "half_open"
                self._successes = 0
        return self._state

    def record_success(self):
        if self._state == "half_open":
            self._successes += 1
            if self._successes >= self.success_threshold:
                self._state = "closed"
                self._failures = 0
        else:
            self._failures = 0

    def record_failure(self):
        self._failures += 1
        self._last_failure = time.time()

        if self._state == "half_open":
            self._state = "open"
        elif self._failures >= self.failure_threshold:
            self._state = "open"

    @contextlib.contextmanager
    def __call__(self):
        if self.state == "open":
            raise ConnectionError("Circuit is open")

        try:
            yield
            self.record_success()
        except Exception as e:
            self.record_failure()
            raise


@dataclass
class RetryConfig:
    max_retries: int = 5
    base_delay: float = 0.1  # 100ms
    max_delay: float = 5.0   # 5s
    multiplier: float = 2.0
    jitter: bool = True


async def retry_with_backoff(
    service: 'SimulatedService',
    cb: CircuitBreaker,
    cfg: RetryConfig,
    timeout: float = 30.0
) -> tuple[Optional[str], Optional[Exception]]:
    """PRODUCTION: Retry with exponential backoff and circuit breaker"""

    delay = cfg.base_delay

    for attempt in range(cfg.max_retries + 1):
        # Check circuit breaker
        if cb.state == "open":
            return None, ConnectionError("Circuit is open")

        try:
            result = service.call()
            return result, None
        except Exception as e:
            cb.record_failure()

            if cb.state == "open":
                return None, ConnectionError("Circuit opened during retry")

            # Calculate delay with exponential backoff
            if attempt < cfg.max_retries:
                actual_delay = delay
                if cfg.jitter:
                    # Add jitter: 0.5-1.5x
                    actual_delay = delay * (0.5 + random.random())

                print(f"Attempt {attempt + 1} failed: {e}. Retrying in {actual_delay:.2f}s...")
                await asyncio.sleep(actual_delay)

                # Exponential backoff
                delay = min(delay * cfg.multiplier, cfg.max_delay)

    return None, Exception("all retries exhausted")


async def main():
    service = SimulatedService(0.4)  # 40% failure rate
    cb = CircuitBreaker(failure_threshold=3, timeout=2.0)
    cfg = RetryConfig()

    print("=== PRODUCTION RETRY (with backoff + circuit breaker) ===")

    start = time.time()
    result, err = await retry_with_backoff(service, cb, cfg)
    elapsed = time.time() - start

    if err:
        print(f"FAILED: {err}")
    else:
        print(f"SUCCESS: {result}")
    print(f"Total calls: {service.call_count}, Time: {elapsed:.2f}s, Circuit: {cb.state}")


if __name__ == "__main__":
    asyncio.run(main())
```

### Run and Compare

```bash
# Go
go run production_retry.go

# Python
python production_retry.py
```

**Expected Output:**
```
=== PRODUCTION RETRY (with backoff + circuit breaker) ===
Attempt 1 failed: infrastructure error. Retrying in 0.15s...
Attempt 2 failed: infrastructure error. Retrying in 0.32s...
Attempt 3 failed: infrastructure error. Retrying in 0.78s...
Circuit opened!
FAILED: circuit opened during retry
Total calls: 3, Time: 1.25s, Circuit: OPEN
```

Or success:
```
=== PRODUCTION RETRY (with backoff + circuit breaker) ===
Attempt 1 failed: infrastructure error. Retrying in 0.12s...
SUCCESS: success
Total calls: 2, Time: 0.22s, Circuit: CLOSED
```

---

## Step 4: Compare Results

| Metric | Naive | Production |
|--------|-------|------------|
| Total calls (success) | 2-6 | 2-4 |
| Total calls (fail) | 6 | 3 (circuit opens) |
| Time (success) | ~0.6s | ~0.2s |
| Time (fail) | ~0.6s | ~1.2s |
| Thundering herd risk | HIGH | LOW (jitter) |
| Service protection | NONE | Circuit breaker |

---

## Step 5: Stretch Challenge

### Challenge 1: Add Deadline Awareness
Modify the retry logic to respect context deadlines - stop retrying if there's less time remaining than one retry would take.

### Challenge 2: Add Metrics
Add counters for:
- Total attempts
- Total successes
- Total failures
- Circuit state transitions

### Challenge 3: Add Different Retry Strategies
Implement:
- `RetryAlways` - Always retry (for idempotent operations)
- `RetryOnSpecificErrors` - Only retry on certain errors
- `RetryWithFallback` - Call fallback service on failure

### Challenge 4: Test with Real Variability
Modify `SimulatedService` to simulate:
- VM migration (random 5-second pause)
- Noisy neighbor (random latency spikes)
- Gradual degradation (increasing failure rate over time)

---

## Solution Keys

### Go (for Challenge 4 - Simulated Variability)

```go
type VariabilityType int

const (
	VariabilityNormal VariabilityType = iota
	VariabilityNoisyNeighbor
	VariabilityMigration
	VariabilityDegradation
)

func (s *SimulatedService) SetVariability(v VariabilityType) {
	s.variabilityType = v
}

func (s *SimulatedService) Call() (string, error) {
	s.callCount++

	// Apply variability
	var latency time.Duration
	switch s.variabilityType {
	case VariabilityNoisyNeighbor:
		// Random massive spikes
		latency = time.Duration(50+rand.Intn(500)) * time.Millisecond
	case VariabilityMigration:
		// Occasional huge pause
		if rand.Float10.01 {
			latency = 5 * time.Second
		} else {
			latency = time.Duration(50+rand.Intn(100)) * time.Millisecond
		}
	case VariabilityDegradation:
		// Gets worse over time
		latency = time.Duration(50+int(float64(s.callCount)*10)) * time.Millisecond
	default:
		latency = time.Duration(50+rand.Intn(100)) * time.Millisecond
	}

	time.Sleep(latency)

	if rand.Float64() < s.failureRate {
		return "", fmt.Errorf("infrastructure error")
	}
	return "success", nil
}
```

---

## Reflection Questions

1. **Why is jitter important?** What happens without it?
2. **When should you use circuit breakers vs. timeouts?**
3. **How does this pattern apply to database connections?**
4. **What's the relationship between retry logic and idempotency?**

---

## 📚 Further Reading

- [Microsoft Azure Circuit Breaker Pattern](https://docs.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker)
- [Netflix Hystrix Wiki](https://github.com/Netflix/Hystrix/wiki)
- [Google SRE Book - Handling Overload](https://sre.google/sre-book/handling-overload/)

---

*Next: [Section 8 - Case Study Deep Dive](section8_case_study.md)*

*Lab complete! You've built production-grade retry logic that handles infrastructure variability.*
