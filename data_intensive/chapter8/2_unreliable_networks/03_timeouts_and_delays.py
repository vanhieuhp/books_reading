"""
Exercise 3: Timeouts and Unbounded Delays

DDIA Reference: Chapter 8, "Timeouts and Unbounded Delays" (pp. 284-287)

This exercise demonstrates the timeout problem: how long should you wait
before assuming a node is dead? Too short = false positives (healthy nodes
declared dead). Too long = slow failure detection.

Key concepts:
  - Network delays are unbounded (no guaranteed upper limit)
  - Fixed timeouts are brittle
  - Adaptive timeouts adjust based on observed latency
  - Cascading failures from false positives
  - Phi Accrual detector (covered in next exercise)

Run: python 03_timeouts_and_delays.py
"""

import sys
import time
import random
import statistics
from typing import List, Tuple
from dataclasses import dataclass, field

# Fix Windows terminal encoding for Unicode output
sys.stdout.reconfigure(encoding='utf-8')


# =============================================================================
# CORE COMPONENTS: Heartbeat, Node, FailureDetector
# =============================================================================

@dataclass
class HeartbeatSample:
    """A single heartbeat sample with latency."""
    timestamp: float
    latency_ms: float


class FixedTimeoutDetector:
    """
    Failure detector using a fixed timeout.

    DDIA: "The practical approach is to use a timeout: if no response
    within X seconds, assume the node is dead."
    """

    def __init__(self, timeout_ms: float):
        self.timeout_ms = timeout_ms
        self.last_heartbeat: float = time.time()
        self.is_alive = True
        self.false_positives = 0
        self.missed_failures = 0

    def receive_heartbeat(self):
        """Receive a heartbeat from the node."""
        self.last_heartbeat = time.time()
        self.is_alive = True

    def check_alive(self) -> bool:
        """Check if node is still alive based on timeout."""
        elapsed_ms = (time.time() - self.last_heartbeat) * 1000
        if elapsed_ms > self.timeout_ms:
            self.is_alive = False
        return self.is_alive

    def get_status(self) -> str:
        """Get current status."""
        elapsed_ms = (time.time() - self.last_heartbeat) * 1000
        return f"{'ALIVE' if self.is_alive else 'DEAD'} (elapsed: {elapsed_ms:.0f}ms)"


class AdaptiveTimeoutDetector:
    """
    Failure detector using adaptive timeout.

    Measures observed response times and adjusts timeout based on
    the distribution (mean + multiple standard deviations).

    DDIA: "Systems like Akka and Cassandra use an adaptive approach:
    measure observed response times and their variability (jitter),
    and automatically adjust the timeout based on the distribution."
    """

    def __init__(self, initial_timeout_ms: float = 100, multiplier: float = 2.0):
        self.initial_timeout_ms = initial_timeout_ms
        self.multiplier = multiplier
        self.samples: List[HeartbeatSample] = []
        self.last_heartbeat: float = time.time()
        self.is_alive = True
        self.false_positives = 0
        self.missed_failures = 0

    def receive_heartbeat(self, latency_ms: float):
        """Receive a heartbeat with measured latency."""
        self.samples.append(HeartbeatSample(time.time(), latency_ms))
        self.last_heartbeat = time.time()
        self.is_alive = True

        # Keep only recent samples (last 100)
        if len(self.samples) > 100:
            self.samples = self.samples[-100:]

    def get_adaptive_timeout_ms(self) -> float:
        """Calculate adaptive timeout based on observed latencies."""
        if len(self.samples) < 2:
            return self.initial_timeout_ms

        latencies = [s.latency_ms for s in self.samples]
        mean = statistics.mean(latencies)
        stdev = statistics.stdev(latencies) if len(latencies) > 1 else 0

        # Timeout = mean + (multiplier * stdev)
        # This adapts to the observed variability
        adaptive_timeout = mean + (self.multiplier * stdev)
        return max(adaptive_timeout, self.initial_timeout_ms)

    def check_alive(self) -> bool:
        """Check if node is still alive based on adaptive timeout."""
        timeout_ms = self.get_adaptive_timeout_ms()
        elapsed_ms = (time.time() - self.last_heartbeat) * 1000

        if elapsed_ms > timeout_ms:
            self.is_alive = False
        return self.is_alive

    def get_status(self) -> str:
        """Get current status."""
        timeout_ms = self.get_adaptive_timeout_ms()
        elapsed_ms = (time.time() - self.last_heartbeat) * 1000
        return f"{'ALIVE' if self.is_alive else 'DEAD'} (timeout: {timeout_ms:.0f}ms, elapsed: {elapsed_ms:.0f}ms)"


class NetworkSimulator:
    """Simulates network with variable latency."""

    def __init__(self, base_latency_ms: float = 10, jitter_ms: float = 5):
        self.base_latency_ms = base_latency_ms
        self.jitter_ms = jitter_ms
        self.is_slow = False
        self.slow_multiplier = 1.0

    def get_latency_ms(self) -> float:
        """Get current network latency."""
        jitter = random.uniform(-self.jitter_ms, self.jitter_ms)
        latency = self.base_latency_ms + jitter

        if self.is_slow:
            latency *= self.slow_multiplier

        return max(latency, 1.0)  # At least 1ms

    def make_slow(self, multiplier: float = 5.0):
        """Simulate network becoming slow (e.g., GC pause, congestion)."""
        self.is_slow = True
        self.slow_multiplier = multiplier

    def make_fast(self):
        """Network returns to normal."""
        self.is_slow = False
        self.slow_multiplier = 1.0


# =============================================================================
# DEMONSTRATION SCENARIOS
# =============================================================================

def print_header(title: str):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_section(title: str):
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}")


def demo_1_fixed_timeout_too_short():
    """
    Demo 1: Fixed timeout that's too short.

    Causes false positives: healthy nodes declared dead.
    """
    print_header("DEMO 1: Fixed Timeout Too Short")
    print("""
    If the timeout is too short, healthy nodes are falsely declared dead.
    This triggers unnecessary failovers, which cause cascading failures.

    DDIA: "Too short: You'll falsely declare healthy nodes as dead.
    This triggers unnecessary failovers, which cause even more load,
    which causes more timeouts — a cascading failure."
    """)

    network = NetworkSimulator(base_latency_ms=50, jitter_ms=30)
    detector = FixedTimeoutDetector(timeout_ms=30)  # Too short!

    print("  Network: base latency = 50ms, jitter = ±30ms")
    print("  Timeout: 30ms (TOO SHORT!)")
    print("  Expected latency range: 20-80ms")
    print("  But timeout is only 30ms!")

    print("\n  Simulating heartbeats:")
    print(f"  {'Time':<8} {'Latency':<12} {'Status':<20} {'Result'}")
    print(f"  {'─'*60}")

    false_positives = 0
    for i in range(10):
        latency = network.get_latency_ms()
        time.sleep(latency / 1000)
        detector.receive_heartbeat()

        status = detector.get_status()
        is_false_positive = not detector.is_alive and latency < detector.timeout_ms

        if is_false_positive:
            false_positives += 1
            result = "❌ FALSE POSITIVE!"
        else:
            result = "✅ Correct"

        print(f"  {i+1:<8} {latency:<12.0f} {status:<20} {result}")

    print(f"\n  ⚠️  FALSE POSITIVES: {false_positives} out of 10")
    print("""
  💡 PROBLEM:
     The timeout is too short for the actual network latency.
     Healthy nodes are falsely declared dead.

     This triggers failovers:
       1. Healthy node declared dead
       2. Failover to backup node
       3. Backup node becomes new leader
       4. Original node rejoins, causing split-brain
       5. Data corruption

     This is a cascading failure!
    """)


def demo_2_fixed_timeout_too_long():
    """
    Demo 2: Fixed timeout that's too long.

    Causes slow failure detection: dead nodes take too long to detect.
    """
    print_header("DEMO 2: Fixed Timeout Too Long")
    print("""
    If the timeout is too long, dead nodes take too long to detect.
    Users wait forever for an error message.

    DDIA: "Too long: Users wait forever for an error message.
    Dead nodes aren't detected quickly enough."
    """)

    network = NetworkSimulator(base_latency_ms=50, jitter_ms=30)
    detector = FixedTimeoutDetector(timeout_ms=5000)  # Too long!

    print("  Network: base latency = 50ms, jitter = ±30ms")
    print("  Timeout: 5000ms (TOO LONG!)")
    print("  Expected latency range: 20-80ms")

    print("\n  Scenario: Node dies after 3 heartbeats")
    print(f"  {'Time':<8} {'Event':<30} {'Status':<20}")
    print(f"  {'─'*60}")

    for i in range(6):
        if i < 3:
            # Node is alive
            latency = network.get_latency_ms()
            time.sleep(latency / 1000)
            detector.receive_heartbeat()
            event = f"Heartbeat #{i+1}"
        else:
            # Node is dead
            time.sleep(0.1)
            event = "Node dies (no heartbeat)"

        detector.check_alive()
        status = detector.get_status()
        print(f"  {i+1:<8} {event:<30} {status:<20}")

    print(f"\n  ⏱️  TIME TO DETECT FAILURE: ~5 seconds")
    print("""
  💡 PROBLEM:
     The timeout is too long for the actual network latency.
     Dead nodes take too long to detect.

     Users experience:
       1. Send request to dead node
       2. Wait 5 seconds for timeout
       3. Finally get error message
       4. Retry on different node

     This is terrible user experience!
    """)


def demo_3_unbounded_delays():
    """
    Demo 3: Why network delays are unbounded.

    Show various sources of delay that make it impossible to set a
    "correct" fixed timeout.
    """
    print_header("DEMO 3: Why Network Delays Are Unbounded")
    print("""
    Network delays have NO upper bound. Unlike telephone circuits
    (which guarantee constant bandwidth), the Internet uses packet
    switching with no guaranteed delivery time.

    DDIA: "Network delays are unbounded. Reasons for delay:
    1. Queueing: Network switches buffer packets
    2. CPU scheduling: OS may not run your process for milliseconds
    3. TCP flow control: Receiver slow, TCP throttles sender
    4. TCP retransmits: Lost packet, TCP retransmits (adds RTT)
    5. Virtualization: VM can be paused for live migration"
    """)

    sources_of_delay = [
        ("Normal network latency", 10, 50),
        ("Network congestion (queueing)", 50, 200),
        ("TCP retransmit (lost packet)", 100, 500),
        ("GC pause (Java/Go)", 100, 1000),
        ("VM live migration", 500, 5000),
        ("Disk I/O (network-attached storage)", 1000, 10000),
    ]

    print(f"\n  {'Source':<35} {'Min (ms)':<12} {'Max (ms)':<12} {'Range'}")
    print(f"  {'─'*70}")

    for source, min_ms, max_ms in sources_of_delay:
        range_str = f"{min_ms}-{max_ms}ms"
        print(f"  {source:<35} {min_ms:<12} {max_ms:<12} {range_str}")

    print("""
  💡 KEY INSIGHT:
     There is NO "correct" fixed timeout!

     If you set timeout = 50ms:
       • Normal network: ✅ Works
       • Congestion: ❌ False positives
       • GC pause: ❌ False positives
       • VM migration: ❌ False positives

     If you set timeout = 5000ms:
       • Normal network: ✅ Works (but slow)
       • Congestion: ✅ Works
       • GC pause: ✅ Works
       • VM migration: ✅ Works (but very slow)
       • Dead node: ❌ Takes 5 seconds to detect

     This is why adaptive timeouts are necessary!
    """)


def demo_4_adaptive_timeout():
    """
    Demo 4: Adaptive timeout that adjusts based on observed latency.

    Learns from the network and adjusts timeout dynamically.
    """
    print_header("DEMO 4: Adaptive Timeout")
    print("""
    Instead of a fixed timeout, measure observed response times
    and adjust the timeout based on the distribution.

    DDIA: "Systems like Akka and Cassandra use an adaptive approach:
    measure observed response times and their variability (jitter),
    and automatically adjust the timeout based on the distribution."

    Formula: timeout = mean + (multiplier × stdev)
    """)

    network = NetworkSimulator(base_latency_ms=50, jitter_ms=30)
    detector = AdaptiveTimeoutDetector(initial_timeout_ms=100, multiplier=2.0)

    print("  Network: base latency = 50ms, jitter = ±30ms")
    print("  Adaptive timeout: mean + (2.0 × stdev)")

    print("\n  Phase 1: Learning (collecting samples)")
    print(f"  {'#':<4} {'Latency':<12} {'Timeout':<12} {'Status':<20}")
    print(f"  {'─'*60}")

    for i in range(10):
        latency = network.get_latency_ms()
        time.sleep(latency / 1000)
        detector.receive_heartbeat(latency)
        detector.check_alive()

        timeout = detector.get_adaptive_timeout_ms()
        status = detector.get_status()
        print(f"  {i+1:<4} {latency:<12.0f} {timeout:<12.0f} {status:<20}")

    print("\n  Phase 2: Network becomes slow (GC pause, congestion)")
    print(f"  {'#':<4} {'Latency':<12} {'Timeout':<12} {'Status':<20}")
    print(f"  {'─'*60}")

    network.make_slow(multiplier=3.0)

    for i in range(5):
        latency = network.get_latency_ms()
        time.sleep(latency / 1000)
        detector.receive_heartbeat(latency)
        detector.check_alive()

        timeout = detector.get_adaptive_timeout_ms()
        status = detector.get_status()
        print(f"  {i+11:<4} {latency:<12.0f} {timeout:<12.0f} {status:<20}")

    print("""
  💡 KEY INSIGHT:
     The adaptive timeout automatically increased when the network
     became slow. It learned from the observed latencies and adjusted.

     Benefits:
       ✅ No false positives (timeout adapts to network conditions)
       ✅ Fast failure detection (timeout is based on actual latency)
       ✅ Handles variable network conditions
       ✅ Learns over time

     This is how Akka and Cassandra work!
    """)


def demo_5_cascading_failure():
    """
    Demo 5: Show how false positives cause cascading failures.

    When a healthy node is falsely declared dead, it triggers a
    failover, which causes more load, which causes more timeouts.
    """
    print_header("DEMO 5: Cascading Failure from False Positives")
    print("""
    When a healthy node is falsely declared dead:
      1. Failover is triggered
      2. Load shifts to remaining nodes
      3. Remaining nodes become overloaded
      4. More timeouts occur
      5. More false positives
      6. More failovers
      7. Cascading failure!

    DDIA: "This triggers unnecessary failovers, which cause even more
    load, which causes more timeouts — a cascading failure."
    """)

    print("\n  Scenario: 3-node cluster with fixed timeout (too short)")
    print("  ─" * 60)

    print("\n  Initial state:")
    print("    Node A: LEADER (handling 100 requests/sec)")
    print("    Node B: FOLLOWER (handling 50 requests/sec)")
    print("    Node C: FOLLOWER (handling 50 requests/sec)")
    print("    Total: 200 requests/sec")

    print("\n  Step 1: Network congestion causes latency spike")
    print("    Latency: 10ms → 100ms")
    print("    Fixed timeout: 30ms (too short!)")

    print("\n  Step 2: Node A falsely declared dead")
    print("    ❌ FALSE POSITIVE: Node A is healthy but timeout triggered")

    print("\n  Step 3: Failover to Node B")
    print("    Node B: NEW LEADER (now handling 200 requests/sec)")
    print("    Node C: FOLLOWER (handling 50 requests/sec)")
    print("    Total: 250 requests/sec (overloaded!)")

    print("\n  Step 4: Node B becomes overloaded")
    print("    More latency: 100ms → 500ms")
    print("    More timeouts!")

    print("\n  Step 5: Node B falsely declared dead")
    print("    ❌ FALSE POSITIVE: Node B is healthy but timeout triggered")

    print("\n  Step 6: Failover to Node C")
    print("    Node C: NEW LEADER (now handling 300 requests/sec)")
    print("    Total: 300 requests/sec (severely overloaded!)")

    print("\n  Step 7: Cascading failure")
    print("    Node C becomes overloaded")
    print("    Latency: 500ms → 5000ms")
    print("    All nodes timeout")
    print("    Cluster becomes unavailable")

    print("""
  💡 KEY INSIGHT:
     False positives cause a cascading failure:
       1. One false positive triggers failover
       2. Failover causes overload
       3. Overload causes more timeouts
       4. More timeouts cause more false positives
       5. Cluster collapses

     This is why adaptive timeouts are critical!
     They prevent false positives by adapting to network conditions.
    """)


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 80)
    print("  EXERCISE 3: TIMEOUTS AND UNBOUNDED DELAYS")
    print("  DDIA Chapter 8: 'Timeouts and Unbounded Delays'")
    print("=" * 80)
    print("""
  This exercise demonstrates the timeout problem: how long should you wait
  before assuming a node is dead? Too short = false positives. Too long =
  slow detection. Network delays are unbounded, so fixed timeouts don't work.
    """)

    demo_1_fixed_timeout_too_short()
    demo_2_fixed_timeout_too_long()
    demo_3_unbounded_delays()
    demo_4_adaptive_timeout()
    demo_5_cascading_failure()

    print("\n" + "=" * 80)
    print("  EXERCISE 3 COMPLETE ✅")
    print("=" * 80)
    print("""
  Key Takeaways:

  1. 🔴 Fixed timeouts are brittle (too short or too long)
  2. 🔴 Network delays are unbounded (no "correct" timeout)
  3. 🔴 False positives cause cascading failures
  4. ✅ Solution: Adaptive timeouts (adjust based on observed latency)
  5. ✅ Solution: Phi Accrual detector (suspicion level instead of binary)

  Next: Run 04_phi_accrual_detector.py to learn about adaptive failure detection
    """)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting...")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
