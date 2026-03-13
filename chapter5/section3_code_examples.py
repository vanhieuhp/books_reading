#!/usr/bin/env python3
"""
Section 3: Python Code Examples - Infrastructure Variability Handling

This module demonstrates patterns for handling infrastructure variability
as discussed in Chapter 5 of "Release It!"

These examples complement the Go examples - Python is often used for
observability, monitoring, and automation scripts.
"""

import asyncio
import contextlib
import random
import time
from dataclasses import dataclass, field
from typing import Callable, Optional
from functools import wraps
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# EXAMPLE 1: Infrastructure Metrics Collection
# =============================================================================

@dataclass
class InfrastructureMetrics:
    """
    Staff-level insight: Infrastructure metrics are often the first indicator
    of problems that will later manifest as application errors.
    """
    cpu_steal: float = 0.0
    io_wait: float = 0.0
    memory_usage: float = 0.0
    network_latency: float = 0.0
    disk_latency: float = 0.0

    # Historical data for trend analysis
    history: list = field(default_factory=list)

    def record(self):
        """Record current metrics to history"""
        self.history.append({
            'timestamp': time.time(),
            'cpu_steal': self.cpu_steal,
            'io_wait': self.io_wait,
            'memory_usage': self.memory_usage,
            'network_latency': self.network_latency,
            'disk_latency': self.disk_latency,
        })

        # Keep only last 1000 samples
        if len(self.history) > 1000:
            self.history.pop(0)

    def get_alert_status(self) -> list:
        """
        Determine if any metrics exceed thresholds.
        Staff-level insight: These thresholds should be tuned to your workload.
        """
        alerts = []

        if self.cpu_steal > 10:
            alerts.append(f"CRITICAL: CPU steal at {self.cpu_steal:.1f}% (threshold: 10%)")

        if self.io_wait > 20:
            alerts.append(f"WARNING: I/O wait at {self.io_wait:.1f}% (threshold: 20%)")

        if self.memory_usage > 85:
            alerts.append(f"WARNING: Memory usage at {self.memory_usage:.1f}% (threshold: 85%)")

        if self.network_latency > 100:
            alerts.append(f"WARNING: Network latency at {self.network_latency:.1f}ms (threshold: 100ms)")

        if self.disk_latency > 50:
            alerts.append(f"WARNING: Disk latency at {self.disk_latency:.1f}ms (threshold: 50ms)")

        return alerts

    def is_healthy(self) -> bool:
        """Check if infrastructure is operating normally"""
        return (
            self.cpu_stele < 5 and
            self.io_wait < 10 and
            self.memory_usage < 80 and
            self.network_latency < 50 and
            self.disk_latency < 20
        )


# =============================================================================
# EXAMPLE 2: Simulated Infrastructure Variability
# =============================================================================

class SimulatedInfrastructure:
    """
    Simulates the variable performance of virtualized infrastructure.
    Staff-level insight: Use this to test your application's resilience patterns.
    """

    def __init__(
        self,
        base_latency_ms: float = 10,
        variance_ms: float = 50,
        failure_rate: float = 0.05,
        noisy_neighbor_probability: float = 0.1
    ):
        self.base_latency_ms = base_latency_ms
        self.variance_ms = variance_ms
        self.failure_rate = failure_rate
        self.noisy_neighbor_probability = noisy_neighbor_probability
        self.is_noisy = False

    def simulate_call(self, operation_name: str) -> float:
        """
        Simulate a call with variable latency.
        Returns the actual latency in milliseconds.
        """
        # Simulate noisy neighbor effect (random "bad days")
        if random.random() < self.noisy_neighbor_probability:
            self.is_noisy = True
            # Noisy neighbor causes massive latency spikes
            latency = self.base_latency_ms + random.uniform(0, self.variance_ms * 5)
        else:
            self.is_noisy = False
            # Normal variability (context switching, etc.)
            latency = self.base_latency_ms + random.uniform(0, self.variance_ms)

        # Simulate failures (hardware issues, timeouts)
        if random.random() < self.failure_rate:
            raise ConnectionError(f"Infrastructure failure during {operation_name}")

        # Simulate VM migration (occasional huge spike)
        if random.random() < 0.01:
            latency += random.uniform(500, 2000)  # 0.5-2 second spike

        return latency


# =============================================================================
# EXAMPLE 3: Timeout with Asyncio
# =============================================================================

async def async_operation_with_timeout(coro, timeout_seconds: float):
    """
    Staff-level insight: In async Python, you must explicitly handle timeouts.
    This is even more critical when infrastructure is unreliable.
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout_seconds)
    except asyncio.TimeoutError:
        raise TimeoutError(f"Operation exceeded {timeout_seconds}s timeout")


async def unreliable_service_call(infrastructure: SimulatedInfrastructure):
    """
    Simulates calling an unreliable service.
    Staff-level insight: This is what happens when you call a service
    running on a poorly-provisioned VM.
    """
    latency = infrastructure.simulate_call("service_call")
    await asyncio.sleep(latency / 1000)  # Convert ms to seconds
    return f"completed in {latency:.1f}ms"


# =============================================================================
# EXAMPLE 4: Retry with Exponential Backoff
# =============================================================================

class RetryConfig:
    """Configuration for retry behavior"""

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 0.1,  # 100ms
        max_delay: float = 5.0,   # 5 seconds
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter


def with_retry(config: RetryConfig):
    """
    Decorator that adds retry with exponential backoff to async functions.
    Staff-level insight: Jitter prevents thundering herd when many clients retry.
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(config.max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    if attempt < config.max_retries:
                        # Calculate delay with exponential backoff
                        delay = min(
                            config.base_delay * (config.exponential_base ** attempt),
                            config.max_delay
                        )

                        # Add jitter to prevent thundering herd
                        if config.jitter:
                            delay = delay * (0.5 + random.random())

                        logger.warning(
                            f"Attempt {attempt + 1} failed: {e}. "
                            f"Retrying in {delay:.2f}s..."
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(f"All {config.max_retries + 1} attempts failed")

            raise last_exception

        return wrapper
    return decorator


# =============================================================================
# EXAMPLE 5: Circuit Breaker
# =============================================================================

class CircuitBreaker:
    """
    Circuit breaker pattern for handling infrastructure failures.
    Staff-level insight: When infrastructure is failing, fail fast to preserve
    resources and allow recovery.
    """

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

    def __init__(
        self,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout: float = 30.0
    ):
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout = timeout
        self.state = self.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None

    async def call(self, func: Callable, *args, **kwargs):
        """Execute function through circuit breaker"""

        # Check if we should transition from OPEN to HALF_OPEN
        if self.state == self.OPEN:
            if time.time() - self.last_failure_time > self.timeout:
                logger.info("Circuit breaker transitioning to HALF_OPEN")
                self.state = self.HALF_OPEN
                self.success_count = 0
            else:
                raise ConnectionError("Circuit breaker is OPEN")

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e

    def _on_success(self):
        """Handle successful call"""
        if self.state == self.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                logger.info("Circuit breaker closing after successful recovery")
                self.state = self.CLOSED
                self.failure_count = 0
        elif self.state == self.CLOSED:
            self.failure_count = 0  # Reset on success

    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.state == self.HALF_OPEN:
            logger.warning("Circuit breaker reopening after failed half-open attempt")
            self.state = self.OPEN
        elif self.failure_count >= self.failure_threshold:
            logger.warning(f"Circuit breaker opening after {self.failure_count} failures")
            self.state = self.OPEN


# =============================================================================
# EXAMPLE 6: Health Check with Infrastructure Metrics
# =============================================================================

class InfrastructureHealthChecker:
    """
    Performs health checks that include infrastructure metrics.
    Staff-level insight: Traditional health checks often don't catch
    infrastructure problems until they cause failures.
    """

    def __init__(self, infrastructure: SimulatedInfrastructure):
        self.infrastructure = infrastructure
        self.metrics_history = []

    async def perform_health_check(self) -> dict:
        """
        Perform a comprehensive health check including infrastructure metrics.
        Returns detailed status for monitoring and alerting.
        """
        check_result = {
            "healthy": True,
            "infrastructure_issues": [],
            "recommendations": [],
            "timestamp": time.time()
        }

        # Simulate collecting infrastructure metrics
        metrics = InfrastructureMetrics()
        metrics.cpu_steal = random.uniform(0, 15)  # Simulated
        metrics.io_wait = random.uniform(0, 25)
        metrics.memory_usage = random.uniform(30, 90)
        metrics.network_latency = random.uniform(5, 150)
        metrics.disk_latency = random.uniform(2, 60)

        # Check for issues
        alerts = metrics.get_alert_status()

        if alerts:
            check_result["healthy"] = False
            check_result["infrastructure_issues"] = alerts

            # Generate recommendations based on specific issues
            if metrics.cpu_steal > 10:
                check_result["recommendations"].append(
                    "Consider moving to dedicated hosts or reducing VM density"
                )

            if metrics.io_wait > 20:
                check_result["recommendations"].append(
                    "Review I/O intensive operations; consider SSD storage"
                )

            if metrics.network_latency > 100:
                check_result["recommendations"].append(
                    "Check for network contention; consider VPC peering"
                )

        # Store for trend analysis
        self.metrics_history.append(check_result)
        if len(self.metrics_history) > 100:
            self.metrics_history.pop(0)

        return check_result


# =============================================================================
# DEMO: Running the Examples
# =============================================================================

async def run_demo():
    """Demonstrate all patterns"""

    print("=" * 60)
    print("Chapter 5: Infrastructure Variability - Python Demo")
    print("=" * 60)
    print()

    # Create simulated infrastructure with high variability
    infra = SimulatedInfrastructure(
        base_latency_ms=10,
        variance_ms=100,  # High variance!
        failure_rate=0.2,  # 20% failure rate
        noisy_neighbor_probability=0.2  # 20% chance of "bad day"
    )

    # Demo 1: Metrics Collection
    print("--- Demo 1: Infrastructure Metrics ---")
    metrics = InfrastructureMetrics(
        cpu_steal=12.5,
        io_wait=22.3,
        memory_usage=87.0,
        network_latency=150.0,
        disk_latency=45.0
    )

    alerts = metrics.get_alert_status()
    for alert in alerts:
        print(f"  ⚠️  {alert}")
    print()

    # Demo 2: Retry with Backoff
    print("--- Demo 2: Retry with Exponential Backoff ---")

    @with_retry(RetryConfig(max_retries=3, base_delay=0.1))
    async def unreliable_call():
        latency = infra.simulate_call("retry_test")
        await asyncio.sleep(latency / 1000)
        return f"success after {latency:.1f}ms"

    try:
        result = await unreliable_call()
        print(f"  ✓ {result}")
    except Exception as e:
        print(f"  ✗ Failed: {e}")
    print()

    # Demo 3: Circuit Breaker
    print("--- Demo 3: Circuit Breaker ---")
    cb = CircuitBreaker(failure_threshold=3, timeout=2.0)

    # Simulate some failures
    for i in range(10):
        try:
            await cb.call(unreliable_call)
            print(f"  Request {i+1}: SUCCESS (state: {cb.state})")
        except ConnectionError as e:
            print(f"  Request {i+1}: BLOCKED - {e} (state: {cb.state})")
            if cb.state == CircuitBreaker.OPEN:
                print("  → Circuit is open, waiting for timeout...")
                break

    print()

    # Demo 4: Health Check
    print("--- Demo 4: Infrastructure Health Check ---")
    health_checker = InfrastructureHealthChecker(infra)

    for _ in range(3):
        result = await health_checker.perform_health_check()
        status = "✓ HEALTHY" if result["healthy"] else "✗ UNHEALTHY"
        print(f"  {status}")

        if result["infrastructure_issues"]:
            for issue in result["infrastructure_issues"]:
                print(f"    - {issue}")
        if result["recommendations"]:
            for rec in result["recommendations"]:
                print(f"    → {rec}")

        await asyncio.sleep(0.5)

    print()
    print("=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_demo())
