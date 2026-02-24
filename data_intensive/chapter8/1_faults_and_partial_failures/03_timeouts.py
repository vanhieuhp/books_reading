"""
Exercise 3: Timeouts and the Timeout Dilemma

DDIA Reference: Chapter 8, "Timeouts and Unbounded Delays" (pp. 283-285)

This exercise demonstrates the timeout dilemma:
  - Timeout too short: false positives (healthy nodes declared dead)
  - Timeout too long: users wait forever, system appears frozen

Key insights:
  1. Network delays are unbounded (no upper limit)
  2. There is no "correct" timeout value
  3. Fixed timeouts are fragile
  4. Adaptive timeouts are better

Sources of delay:
  - Queueing in network switches
  - CPU scheduling delays
  - TCP flow control
  - TCP retransmits
  - VM pauses in cloud environments

Run: python 03_timeouts.py
"""

import sys
import time
import random
import statistics
from typing import List, Tuple

sys.stdout.reconfigure(encoding='utf-8')


# =============================================================================
# NETWORK SIMULATION
# =============================================================================

class NetworkCondition:
    """Simulates network conditions with variable latency."""

    def __init__(self, base_latency: float, jitter: float, packet_loss: float = 0.0):
        """
        base_latency: average latency in seconds
        jitter: random variation in latency
        packet_loss: probability of packet loss (0.0 to 1.0)
        """
        self.base_latency = base_latency
        self.jitter = jitter
        self.packet_loss = packet_loss
        self.latencies = []  # Track observed latencies

    def send_request(self) -> Tuple[bool, float]:
        """
        Simulate sending a request.

        Returns:
          (success: bool, latency: float)
          - (True, latency) if request succeeded
          - (False, 0) if request was lost
        """
        # Check for packet loss
        if random.random() < self.packet_loss:
            return False, 0

        # Calculate latency with jitter
        latency = self.base_latency + random.gauss(0, self.jitter)
        latency = max(0.001, latency)  # Ensure positive

        self.latencies.append(latency)
        return True, latency

    def get_stats(self) -> dict:
        """Get statistics about observed latencies."""
        if not self.latencies:
            return {}

        return {
            "min": min(self.latencies),
            "max": max(self.latencies),
            "mean": statistics.mean(self.latencies),
            "median": statistics.median(self.latencies),
            "stdev": statistics.stdev(self.latencies) if len(self.latencies) > 1 else 0,
            "p99": sorted(self.latencies)[int(len(self.latencies) * 0.99)],
        }


# =============================================================================
# CLIENT SIMULATION
# =============================================================================

class Client:
    """A client that sends requests with a fixed timeout."""

    def __init__(self, network: NetworkCondition, timeout: float):
        self.network = network
        self.timeout = timeout
        self.successful_requests = 0
        self.failed_requests = 0
        self.false_positives = 0  # Declared dead but actually alive

    def send_request(self) -> Tuple[bool, str]:
        """
        Send a request with timeout.

        Returns:
          (success: bool, reason: str)
        """
        success, latency = self.network.send_request()

        if not success:
            # Packet was lost
            self.failed_requests += 1
            return False, "Packet lost"

        if latency > self.timeout:
            # Timeout: we didn't get response in time
            self.false_positives += 1
            self.failed_requests += 1
            return False, f"Timeout (latency was {latency:.3f}s, timeout is {self.timeout:.3f}s)"

        # Success
        self.successful_requests += 1
        return True, f"Success (latency: {latency:.3f}s)"

    def send_requests(self, count: int) -> List[Tuple[bool, str]]:
        """Send multiple requests."""
        results = []
        for _ in range(count):
            results.append(self.send_request())
        return results


# =============================================================================
# DEMONSTRATIONS
# =============================================================================

def demonstrate_timeout_dilemma():
    """Show the timeout dilemma: too short vs too long."""

    print("=" * 80)
    print("THE TIMEOUT DILEMMA")
    print("=" * 80)
    print()

    # Scenario: Normal network conditions
    print("Scenario: Normal network with average latency 100ms, jitter 50ms")
    print()

    network = NetworkCondition(base_latency=0.1, jitter=0.05)

    # Send some requests to establish baseline
    print("Sending 100 requests to establish baseline...")
    for _ in range(100):
        network.send_request()

    stats = network.get_stats()
    print(f"Observed latencies:")
    print(f"  Min: {stats['min']*1000:.1f}ms")
    print(f"  Max: {stats['max']*1000:.1f}ms")
    print(f"  Mean: {stats['mean']*1000:.1f}ms")
    print(f"  Median: {stats['median']*1000:.1f}ms")
    print(f"  P99: {stats['p99']*1000:.1f}ms")
    print()

    # Try different timeout values
    timeout_values = [0.05, 0.1, 0.15, 0.2, 0.3]

    print("Testing different timeout values:")
    print()

    for timeout in timeout_values:
        client = Client(network, timeout)
        results = client.send_requests(100)

        success_rate = (client.successful_requests / 100) * 100
        false_positive_rate = (client.false_positives / 100) * 100

        print(f"Timeout: {timeout*1000:.0f}ms")
        print(f"  Success rate: {success_rate:.1f}%")
        print(f"  False positives: {false_positive_rate:.1f}%")

        if timeout < stats['p99']:
            print(f"  ⚠️  TOO SHORT: Many false positives!")
        elif timeout > stats['p99'] * 2:
            print(f"  ⚠️  TOO LONG: Users wait too long for errors")
        else:
            print(f"  ✅ Reasonable trade-off")

        print()


def demonstrate_cascading_failures():
    """Show how timeouts can cause cascading failures."""

    print("=" * 80)
    print("CASCADING FAILURES")
    print("=" * 80)
    print()

    print("Scenario: System under load")
    print("  - Normal latency: 50ms")
    print("  - Under load: latency increases")
    print("  - Timeout: 100ms")
    print()

    # Simulate increasing load
    loads = [
        ("Light load", 0.05, 0.01),
        ("Medium load", 0.1, 0.02),
        ("Heavy load", 0.2, 0.05),
        ("Overload", 0.5, 0.1),
    ]

    for load_name, base_latency, jitter in loads:
        network = NetworkCondition(base_latency=base_latency, jitter=jitter)
        client = Client(network, timeout=0.1)

        # Send requests
        for _ in range(50):
            network.send_request()

        results = client.send_requests(100)

        success_rate = (client.successful_requests / 100) * 100
        false_positive_rate = (client.false_positives / 100) * 100

        print(f"{load_name}:")
        print(f"  Avg latency: {base_latency*1000:.0f}ms")
        print(f"  Success rate: {success_rate:.1f}%")
        print(f"  False positives: {false_positive_rate:.1f}%")

        if false_positive_rate > 10:
            print(f"  💥 CASCADING FAILURE RISK!")
            print(f"     - Timeouts trigger failovers")
            print(f"     - Failovers cause more load")
            print(f"     - More load causes more timeouts")
            print(f"     - System collapses")

        print()


def demonstrate_adaptive_timeout():
    """Show how adaptive timeouts work better."""

    print("=" * 80)
    print("ADAPTIVE TIMEOUTS")
    print("=" * 80)
    print()

    print("Strategy: Adjust timeout based on observed latencies")
    print()

    # Simulate changing network conditions
    conditions = [
        ("Normal", 0.05, 0.01),
        ("Degraded", 0.15, 0.05),
        ("Recovery", 0.08, 0.02),
    ]

    for condition_name, base_latency, jitter in conditions:
        print(f"Network condition: {condition_name}")
        print()

        network = NetworkCondition(base_latency=base_latency, jitter=jitter)

        # Collect baseline latencies
        print("  Collecting baseline latencies...")
        for _ in range(50):
            network.send_request()

        stats = network.get_stats()

        # Calculate adaptive timeout: mean + 2*stdev (covers ~95% of requests)
        adaptive_timeout = stats['mean'] + (2 * stats['stdev'])

        print(f"  Mean latency: {stats['mean']*1000:.1f}ms")
        print(f"  Stdev: {stats['stdev']*1000:.1f}ms")
        print(f"  Adaptive timeout: {adaptive_timeout*1000:.1f}ms")
        print()

        # Test with adaptive timeout
        client = Client(network, adaptive_timeout)
        results = client.send_requests(100)

        success_rate = (client.successful_requests / 100) * 100
        false_positive_rate = (client.false_positives / 100) * 100

        print(f"  Results:")
        print(f"    Success rate: {success_rate:.1f}%")
        print(f"    False positives: {false_positive_rate:.1f}%")
        print()


def demonstrate_phi_accrual():
    """Show the Phi Accrual Failure Detector concept."""

    print("=" * 80)
    print("PHI ACCRUAL FAILURE DETECTOR")
    print("=" * 80)
    print()

    print("Instead of binary 'dead or alive', use a suspicion level (phi)")
    print()

    print("Concept:")
    print("  - Track heartbeat arrival times")
    print("  - Calculate probability that node is dead")
    print("  - Phi = -log10(probability)")
    print("  - Higher phi = more likely to be dead")
    print()

    print("Example:")
    print()

    # Simulate heartbeats
    heartbeat_intervals = [0.1, 0.11, 0.09, 0.12, 0.1, 0.5, 1.0, 1.5]

    print("Heartbeat intervals (seconds):")
    for i, interval in enumerate(heartbeat_intervals):
        # Calculate phi (simplified)
        # In real implementation, this uses exponential distribution
        if interval < 0.2:
            phi = 0.5
            status = "✅ Healthy"
        elif interval < 0.5:
            phi = 2.0
            status = "⚠️  Suspicious"
        else:
            phi = 5.0
            status = "💀 Likely dead"

        print(f"  {i+1}. Interval: {interval:.2f}s → Phi: {phi:.1f} {status}")

    print()
    print("Advantages over fixed timeout:")
    print("  - Adapts to changing network conditions")
    print("  - Gradual suspicion instead of binary decision")
    print("  - Application chooses threshold for declaring dead")
    print("  - Reduces false positives")
    print()


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    demonstrate_timeout_dilemma()
    print()
    print()
    demonstrate_cascading_failures()
    print()
    print()
    demonstrate_adaptive_timeout()
    print()
    print()
    demonstrate_phi_accrual()

    print()
    print("=" * 80)
    print("KEY TAKEAWAYS")
    print("=" * 80)
    print()
    print("1. Network delays are unbounded")
    print("   - No upper limit on how long a request can take")
    print("   - Caused by queueing, scheduling, retransmits, VM pauses, etc.")
    print()
    print("2. The timeout dilemma")
    print("   - Too short: false positives (healthy nodes declared dead)")
    print("   - Too long: users wait forever, system appears frozen")
    print("   - No 'correct' value")
    print()
    print("3. Fixed timeouts are fragile")
    print("   - Work fine under normal conditions")
    print("   - Fail under load (cascading failures)")
    print()
    print("4. Adaptive timeouts are better")
    print("   - Measure observed latencies")
    print("   - Adjust timeout based on distribution")
    print("   - Phi Accrual: suspicion level instead of binary")
    print()
