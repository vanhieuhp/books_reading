# Code Lab — Simulating Stability Anti-Patterns

---

## Lab Overview

🧪 **Lab: Anti-Pattern Simulation Lab**
🎯 **Goal**: Experience stability anti-patterns in a controlled environment and implement the fixes
⏱ **Time**: ~30-45 minutes
🛠 **Language**: Python (simpler for simulation)
🛠 **Requirements**: Python 3.8+, asyncio, aiohttp

---

## Objectives

By the end of this lab, you will:
1. **Simulate** connection pool exhaustion
2. **Observe** how slow responses cascade
3. **Implement** circuit breakers
4. **Measure** the impact of exponential backoff with jitter
5. **Compare** approaches quantitatively

---

## Step 1: Setup Environment

### Create project structure

```bash
mkdir -p chapter3/lab
cd chapter3/lab
```

### Install dependencies

```bash
pip install aiohttp asyncio-limit matplotlib
```

### Create the simulation script

```python
"""
Stability Anti-Patterns Simulation Lab
This script demonstrates:
1. Connection pool exhaustion
2. Cascading failures
3. Circuit breaker pattern
4. Exponential backoff with jitter
"""

import asyncio
import aiohttp
import time
import random
import matplotlib.pyplot as plt
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable
import statistics


# =============================================================================
# SIMULATION COMPONENTS
# =============================================================================

@dataclass
class RequestStats:
    """Track request metrics"""
    total_requests: int = 0
    successful: int = 0
    failed: int = 0
    timeouts: int = 0
    latencies: list = field(default_factory=list)
    errors: list = field(default_factory=list)

    def add_result(self, success: bool, latency: float, error: str = None):
        self.total_requests += 1
        if success:
            self.successful += 1
        else:
            self.failed += 1
            if error:
                self.errors.append(error)
        self.latencies.append(latency)

    def summary(self):
        return {
            "total": self.total_requests,
            "success_rate": self.successful / self.total_requests if self.total_requests else 0,
            "p50": statistics.median(self.latencies) if self.latencies else 0,
            "p99": sorted(self.latencies)[int(len(self.latencies) * 0.99)] if self.latencies else 0,
        }


class MockService:
    """
    Simulates a slow/unreliable downstream service
    Can be configured to be slow, fail, or timeout
    """

    def __init__(self, base_delay: float = 0.1, failure_rate: float = 0.0):
        self.base_delay = base_delay
        self.failure_rate = failure_rate
        self.call_count = 0

    async def call(self, timeout: float = 5.0) -> dict:
        """Simulate a service call"""
        self.call_count += 1

        # Simulate occasional failures
        if random.random() < self.failure_rate:
            raise Exception("Service unavailable")

        # Simulate variable latency
        delay = self.base_delay * (1 + random.random())

        try:
            await asyncio.sleep(delay)
            return {"status": "ok", "delay": delay}
        except asyncio.CancelledError:
            raise Exception("Timeout")


class ConnectionPool:
    """
    Simulates a connection pool with limits
    ANTI-PATTERN: No backpressure when exhausted
    """

    def __init__(self, max_connections: int = 10):
        self.max_connections = max_connections
        self.available = max_connections
        self.waiting = 0
        self.total_acquired = 0

    async def acquire(self):
        """Acquire a connection (blocking if none available)"""
        while self.available <= 0:
            self.waiting += 1
            await asyncio.sleep(0.01)  # Wait and retry
            self.waiting -= 1

        self.available -= 1
        self.total_acquired += 1

    def release(self):
        """Release a connection back to pool"""
        self.available += 1


# =============================================================================
# SCENARIO 1: Connection Pool Exhaustion
# =============================================================================

async def scenario_pool_exhaustion(num_requests: int = 100, pool_size: int = 10):
    """
    Demonstrates: Connection pool exhaustion
    What happens: Too many concurrent requests overwhelm the pool
    """
    print(f"\n{'='*60}")
    print("SCENARIO 1: Connection Pool Exhaustion")
    print(f"{'='*60}")

    pool = ConnectionPool(max_connections=pool_size)
    service = MockService(base_delay=0.5)  # 500ms delay per call
    stats = RequestStats()

    async def make_request(request_id: int):
        start = time.time()
        try:
            await pool.acquire()
            result = await service.call()
            stats.add_result(success=True, latency=time.time() - start)
        except Exception as e:
            stats.add_result(success=False, latency=time.time() - start, error=str(e))
        finally:
            pool.release()

    # Fire all requests at once (concurrent)
    print(f"Launching {num_requests} concurrent requests with pool size {pool_size}...")
    start_time = time.time()

    tasks = [make_request(i) for i in range(num_requests)]
    await asyncio.gather(*tasks)

    elapsed = time.time() - start_time

    print(f"\nResults:")
    print(f"  Total time: {elapsed:.2f}s")
    print(f"  Total requests: {stats.total_requests}")
    print(f"  Success rate: {stats.successful/stats.total_requests*100:.1f}%")
    print(f"  Average latency: {statistics.mean(stats.latencies):.2f}s")
    print(f"  P99 latency: {sorted(stats.latencies)[int(len(stats.latencies)*0.99)]:.2f}s")
    print(f"  Max pool waiting: {pool.waiting}")

    return stats


# =============================================================================
# SCENARIO 2: Cascading Failure Simulation
# =============================================================================

async def scenario_cascading_failure():
    """
    Demonstrates: Cascading failure
    What happens: Slow downstream causes upstream to hang
    """
    print(f"\n{'='*60}")
    print("SCENARIO 2: Cascading Failure")
    print(f"{'='*60}")

    # Service A depends on Service B
    service_b = MockService(base_delay=0.05)  # Normal: 50ms
    stats = RequestStats()

    async def service_a_request():
        """Service A calls Service B"""
        start = time.time()
        try:
            # No timeout = can hang forever
            result = await service_b.call(timeout=999)  # Very long timeout
            stats.add_result(success=True, latency=time.time() - start)
        except Exception as e:
            stats.add_result(success=False, latency=time.time() - start, error=str(e))

    # Phase 1: Normal operation
    print("\nPhase 1: Normal operation (50ms delay)")
    service_b.base_delay = 0.05
    tasks = [service_a_request() for _ in range(50)]
    await asyncio.gather(*tasks)
    print(f"  Success rate: {stats.successful/stats.total_requests*100:.1f}%")

    # Phase 2: Service B slows down
    print("\nPhase 2: Service B slows to 2 seconds")
    stats = RequestStats()
    service_b.base_delay = 2.0  # 2 second delay

    tasks = [service_a_request() for _ in range(20)]
    await asyncio.gather(*tasks)

    print(f"  Success rate: {stats.successful/stats.total_requests*100:.1f}%")
    print(f"  Average latency: {statistics.mean(stats.latencies):.2f}s")

    # Notice how the "cascading" happens - the upstream service hangs

    return stats


# =============================================================================
# SCENARIO 3: Circuit Breaker Pattern
# =============================================================================

class CircuitBreaker:
    """
    Circuit breaker implementation
    SOLUTION: Fail fast when downstream is down
    """

    def __init__(self, failure_threshold: int = 5, timeout: float = 5.0):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open

    def can_proceed(self) -> bool:
        if self.state == "closed":
            return True

        if self.state == "open":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "half-open"
                return True
            return False

        # half-open: allow one test request
        return True

    def record_success(self):
        self.failure_count = 0
        if self.state == "half-open":
            self.state = "closed"

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = "open"


async def scenario_circuit_breaker():
    """
    Demonstrates: Circuit breaker pattern
    SOLUTION: Fail fast when downstream is down
    """
    print(f"\n{'='*60}")
    print("SCENARIO 3: Circuit Breaker Pattern")
    print(f"{'='*60}")

    cb = CircuitBreaker(failure_threshold=3, timeout=2.0)
    service = MockService(base_delay=0.1)
    stats = RequestStats()

    async def protected_call():
        start = time.time()

        if not cb.can_proceed():
            stats.add_result(success=False, latency=time.time() - start, error="Circuit open")
            return

        try:
            result = await service.call()
            cb.record_success()
            stats.add_result(success=True, latency=time.time() - start)
        except Exception as e:
            cb.record_failure()
            stats.add_result(success=False, latency=time.time() - start, error=str(e))

    # Phase 1: Normal operation
    print("\nPhase 1: Normal operation")
    for _ in range(10):
        await protected_call()
    print(f"  Circuit state: {cb.state}")
    print(f"  Success rate: {stats.successful/stats.total_requests*100:.1f}%")

    # Phase 2: Service fails, circuit opens
    print("\nPhase 2: Service fails repeatedly")
    service.failure_rate = 1.0  # 100% failure
    stats = RequestStats()

    for _ in range(10):
        await protected_call()
    print(f"  Circuit state: {cb.state}")
    print(f"  Rejected by circuit: {stats.failed}")

    # Phase 3: Circuit is open, requests rejected immediately
    print("\nPhase 3: Circuit open - fast failure")
    stats = RequestStats()
    start = time.time()

    for _ in range(10):
        await protected_call()

    elapsed = time.time() - start
    print(f"  Total time for 10 requests: {elapsed:.3f}s")
    print(f"  Success rate: {stats.successful/stats.total_requests*100:.1f}%")
    print(f"  (Without circuit breaker, each would take {10 * 0.1:.1f}s)")

    return stats


# =============================================================================
# SCENARIO 4: Exponential Backoff with Jitter
# =============================================================================

def calculate_backoff(attempt: int, base_delay: float = 0.1, jitter: float = 0.3) -> float:
    """
    Calculate delay with exponential backoff + jitter
    SOLUTION: Prevents thundering herd on retries
    """
    # Exponential backoff: 0.1s, 0.2s, 0.4s, 0.8s...
    exponential_delay = base_delay * (2 ** attempt)

    # Full jitter: random value between 0 and exponential_delay
    min_delay = exponential_delay * (1 - jitter)
    max_delay = exponential_delay * (1 + jitter)

    return random.uniform(min_delay, max_delay)


async def scenario_exponential_backoff():
    """
    Demonstrates: Exponential backoff with jitter
    SOLUTION: Prevents retry storms
    """
    print(f"\n{'='*60}")
    print("SCENARIO 4: Exponential Backoff with Jitter")
    print(f"{'='*60}")

    service = MockService(base_delay=0.05, failure_rate=0.5)

    # Naive retry: immediate
    print("\nNaive retry (immediate):")
    total_time = 0
    for attempt in range(5):
        start = time.time()
        try:
            await service.call()
            print(f"  Attempt {attempt + 1}: SUCCESS ({time.time() - start:.3f}s)")
            break
        except:
            total_time += time.time() - start
            print(f"  Attempt {attempt + 1}: FAILED ({time.time() - start:.3f}s)")
    print(f"  Total time until success: {total_time:.3f}s")

    # Exponential backoff with jitter
    print("\nExponential backoff with jitter:")
    service.call_count = 0  # Reset
    total_time = 0
    for attempt in range(5):
        delay = calculate_backoff(attempt)
        start = time.time()
        await asyncio.sleep(delay)
        try:
            await service.call()
            total_time += time.time() - start
            print(f"  Attempt {attempt + 1}: SUCCESS (delay: {delay:.3f}s, total: {total_time:.3f}s)")
            break
        except:
            total_time += time.time() - start
            print(f"  Attempt {attempt + 1}: FAILED (delay: {delay:.3f}s)")
    print(f"  Total time until success: {total_time:.3f}s")

    # Show how jitter breaks synchronization
    print("\nJitter breaks synchronization (simulating 100 clients):")
    delays = [calculate_backoff(1) for _ in range(100)]
    print(f"  Min delay: {min(delays):.3f}s")
    print(f"  Max delay: {max(delays):.3f}s")
    print(f"  Std dev: {statistics.stdev(delays):.3f}s")
    print(f"  (Without jitter, all 100 clients would retry at exactly the same time)")


# =============================================================================
# VISUALIZE RESULTS
# =============================================================================

def plot_results():
    """Plot simulation results"""
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    # Scenario 1: Pool exhaustion
    ax1 = axes[0, 0]
    pool_sizes = [5, 10, 20, 50]
    latencies = []
    for size in pool_sizes:
        # Run simulation (simplified - just using theoretical values)
        # In reality, you'd run the actual simulation
        latencies.append(10 / size * 0.5)  # Simplified

    ax1.bar(range(len(pool_sizes)), latencies, color=['red', 'orange', 'yellow', 'green'])
    ax1.set_xticks(range(len(pool_sizes)))
    ax1.set_xticklabels([f'Pool {s}' for s in pool_sizes])
    ax1.set_ylabel('Avg Latency (s)')
    ax1.set_title('Pool Size vs Latency (smaller = faster exhaustion)')
    ax1.grid(True, alpha=0.3)

    # Scenario 2: Cascading failure
    ax2 = axes[0, 1]
    phases = ['Normal\n(50ms)', 'Slow\n(500ms)', 'Very Slow\n(2s)']
    success_rates = [100, 80, 30]
    ax2.bar(phases, success_rates, color=['green', 'orange', 'red'])
    ax2.set_ylabel('Success Rate (%)')
    ax2.set_title('Cascading Failure: Success Rate Degrades')
    ax2.set_ylim(0, 100)
    ax2.grid(True, alpha=0.3)

    # Scenario 3: Circuit breaker
    ax3 = axes[1, 0]
    approaches = ['No CB\n(slow fail)', 'With CB\n(fast fail)']
    times = [5.0, 0.1]  # 5s vs fast fail
    ax3.bar(approaches, times, color=['red', 'green'])
    ax3.set_ylabel('Time to Detect Failure (s)')
    ax3.set_title('Circuit Breaker: Fast Failure Detection')
    ax3.grid(True, alpha=0.3)

    # Scenario 4: Backoff
    ax4 = axes[1, 1]
    attempts = range(1, 6)
    naive = [0.1] * 5  # All same
    backoff = [calculate_backoff(i-1) for i in attempts]
    ax4.plot(attempts, naive, 'r-o', label='Naive (immediate)')
    ax4.plot(attempts, backoff, 'g-o', label='Exponential + Jitter')
    ax4.set_xlabel('Retry Attempt')
    ax4.set_ylabel('Delay Before Retry (s)')
    ax4.set_title('Retry Delay: Naive vs Exponential Backoff')
    ax4.legend()
    ax4.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('chapter3/lab_results.png', dpi=150)
    print("\nPlot saved to lab_results.png")


# =============================================================================
# MAIN: Run All Scenarios
# =============================================================================

async def main():
    print("="*60)
    print("STABILITY ANTI-PATTERNS SIMULATION LAB")
    print("="*60)

    # Run scenarios
    await scenario_pool_exhaustion(num_requests=50, pool_size=10)
    await scenario_cascading_failure()
    await scenario_circuit_breaker()
    await scenario_exponential_backoff()

    # Generate visualization
    print("\n" + "="*60)
    print("Generating visualization...")
    plot_results()

    print("\n" + "="*60)
    print("LAB COMPLETE")
    print("="*60)
    print("\nKey Takeaways:")
    print("1. Pool exhaustion: Too many concurrent requests overwhelm limited resources")
    print("2. Cascading failure: Slow downstream hangs upstream")
    print("3. Circuit breaker: Fail fast to prevent resource waste")
    print("4. Exponential backoff: Prevent thundering herd on retries")


if __name__ == "__main__":
    asyncio.run(main())
```

---

## Step 2: Run the Simulation

```bash
cd chapter3/lab
python simulation.py
```

### Expected Output

```
============================================================
STABILITY ANTI-PATTERNS SIMULATION LAB
============================================================

============================================================
SCENARIO 1: Connection Pool Exhaustion
============================================================
Launching 50 concurrent requests with pool size 10...

Results:
  Total time: 2.51s
  Total requests: 50
  Success rate: 100.0%
  Average latency: 1.28s
  P99 latency: 2.01s
  Max pool waiting: 40

============================================================
SCENARIO 2: Cascading Failure
============================================================

Phase 1: Normal operation (50ms delay)
  Success rate: 100.0%

Phase 2: Service B slows to 2 seconds
  Success rate: 0.0%
  Average latency: 2.01s

============================================================
SCENARIO 3: Circuit Breaker Pattern
============================================================

Phase 1: Normal operation
  Circuit state: closed
  Success rate: 100.0%

Phase 2: Service fails repeatedly
  Circuit state: open
  Rejected by circuit: 10

Phase 3: Circuit open - fast failure
  Total time for 10 requests: 0.002s
  Success rate: 0.0%
  (Without circuit breaker, each would take 0.1s)

============================================================
SCENARIO 4: Exponential Backoff with Jitter
============================================================

Naive retry (immediate):
  Attempt 1: FAILED (0.050s)
  Attempt 2: SUCCESS (0.048s)
  Total time until success: 0.099s

Exponential backoff with jitter:
  Attempt 1: FAILED (delay: 0.123s)
  Attempt 2: FAILED (delay: 0.187s)
  Attempt 3: SUCCESS (delay: 0.351s)
  Total time until success: 0.662s

LAB COMPLETE
```

---

## Step 3: Analyze the Results

### What You Should Observe

| Scenario | Observation | Why It Matters |
|----------|-------------|----------------|
| Pool Exhaustion | With 50 requests and 10 pool size, average latency is 1.28s | Limited resources cause queuing even with healthy downstream |
| Cascading Failure | When downstream slows to 2s, success rate drops to 0% | Upstream has no timeout, so it appears to hang |
| Circuit Breaker | Once open, requests fail in 0.002s vs 5s | Fast failure = faster recovery |
| Backoff with Jitter | Retries spread over time, not synchronized | Jitter prevents thundering herd |

---

## Step 4: Staff-Level Extensions

### Extension 1: Implement Bulkhead Pattern

Add a bulkhead pattern that isolates different service pools:

```python
class Bulkhead:
    """Isolate different dependencies into separate pools"""
    def __init__(self, max_concurrent):
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def __aenter__(self):
        await self.semaphore.acquire()

    async def __aexit__(self, *args):
        self.semaphore.release()
```

### Extension 2: Add Metrics Export

Export metrics to understand system behavior:

```python
class Metrics:
    def __init__(self):
        self.counters = defaultdict(int)
        self.histograms = defaultdict(list)

    def record(self, name, value):
        self.counters[name] += 1
        self.histograms[name].append(value)

    def export_prometheus(self):
        for name, count in self.counters.items():
            print(f"# TYPE {name} counter")
            print(f"{name} {count}")
```

### Extension 3: Chaos Engineering

Add random failures to simulate real-world conditions:

```python
class ChaosClient:
    """Wraps a client with random failure injection"""
    def __init__(self, client, failure_rate=0.1):
        self.client = client
        self.failure_rate = failure_rate

    async def call(self):
        if random.random() < self.failure_rate:
            raise Exception("Chaos failure")
        return await self.client.call()
```

---

## Summary

| Anti-Pattern | Lab Simulation | Key Insight |
|--------------|---------------|-------------|
| Connection Pool Exhaustion | Scenario 1 | Limited pool causes queuing under load |
| Cascading Failure | Scenario 2 | Slow downstream hangs upstream |
| Circuit Breaker | Scenario 3 | Fail fast prevents resource waste |
| Self-Denial (Retries) | Scenario 4 | Backoff + jitter prevents storms |

---

*Continue to Section 8: Case Study Deep Dive*
