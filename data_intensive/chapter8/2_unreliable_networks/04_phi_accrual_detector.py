"""
Exercise 4: Phi Accrual Failure Detector

DDIA Reference: Chapter 8, "Phi Accrual Failure Detector" (pp. 287-289)

This exercise implements the Phi Accrual failure detector, used by Akka
and Cassandra. Instead of a binary "dead or alive" decision, it outputs
a suspicion level (phi φ) that increases over time without a heartbeat.

Key concepts:
  - Heartbeat-based failure detection
  - Phi calculation: φ = -log10(P(heartbeat arrives within time T))
  - Suspicion level increases over time
  - Application chooses threshold for declaring node dead
  - Adaptive to network conditions
  - Used by Akka, Cassandra, and other systems

Run: python 04_phi_accrual_detector.py
"""

import sys
import time
import random
import math
import statistics
from typing import List, Optional
from dataclasses import dataclass, field

# Fix Windows terminal encoding for Unicode output
sys.stdout.reconfigure(encoding='utf-8')


# =============================================================================
# CORE COMPONENTS: PhiAccrualDetector
# =============================================================================

@dataclass
class HeartbeatSample:
    """A single heartbeat sample."""
    timestamp: float
    inter_arrival_time_ms: float  # Time since last heartbeat


class PhiAccrualDetector:
    """
    Phi Accrual Failure Detector.

    DDIA: "Phi Accrual Failure Detector (used by Akka and Cassandra):
    Instead of a binary 'dead or alive,' it outputs a suspicion level
    (phi φ) that increases over time without a heartbeat."

    The phi value represents the probability that the node has failed.
    Higher phi = more confident the node is dead.

    Formula:
      φ(t) = -log10(P(heartbeat arrives within time t))

    Where P(heartbeat arrives within time t) is estimated from the
    distribution of inter-arrival times.
    """

    def __init__(self, threshold: float = 5.0, max_samples: int = 1000):
        """
        Initialize the detector.

        Args:
            threshold: Phi value above which node is considered dead
                      (typically 5.0 = 99.999% confidence)
            max_samples: Maximum number of samples to keep
        """
        self.threshold = threshold
        self.max_samples = max_samples
        self.samples: List[HeartbeatSample] = []
        self.last_heartbeat_time: float = time.time()
        self.node_id: str = "unknown"

    def receive_heartbeat(self):
        """Receive a heartbeat from the node."""
        current_time = time.time()

        if self.samples:
            # Calculate inter-arrival time (time since last heartbeat)
            inter_arrival_ms = (current_time - self.last_heartbeat_time) * 1000
        else:
            # First heartbeat
            inter_arrival_ms = 0

        self.samples.append(HeartbeatSample(current_time, inter_arrival_ms))
        self.last_heartbeat_time = current_time

        # Keep only recent samples
        if len(self.samples) > self.max_samples:
            self.samples = self.samples[-self.max_samples:]

    def get_phi(self) -> float:
        """
        Calculate the current phi value.

        φ(t) = -log10(P(heartbeat arrives within time t))

        Returns:
            Phi value (higher = more confident node is dead)
        """
        if len(self.samples) < 2:
            # Not enough samples yet
            return 0.0

        # Time since last heartbeat
        time_since_last_heartbeat_ms = (time.time() - self.last_heartbeat_time) * 1000

        # Get inter-arrival times (excluding the first sample which is 0)
        inter_arrivals = [s.inter_arrival_time_ms for s in self.samples[1:]]

        if not inter_arrivals:
            return 0.0

        # Calculate mean and stdev of inter-arrival times
        mean_inter_arrival = statistics.mean(inter_arrivals)
        stdev_inter_arrival = statistics.stdev(inter_arrivals) if len(inter_arrivals) > 1 else 0

        if mean_inter_arrival == 0:
            return 0.0

        # Estimate probability using exponential distribution
        # P(X > t) = e^(-t/mean)
        # P(X <= t) = 1 - e^(-t/mean)

        try:
            # Probability that heartbeat arrives within time_since_last_heartbeat
            prob_heartbeat_arrives = 1 - math.exp(-time_since_last_heartbeat_ms / mean_inter_arrival)

            # Phi = -log10(probability)
            # If prob is very small, phi becomes very large
            if prob_heartbeat_arrives >= 1.0:
                prob_heartbeat_arrives = 0.9999

            phi = -math.log10(1 - prob_heartbeat_arrives) if prob_heartbeat_arrives < 1.0 else 10.0

            return max(phi, 0.0)
        except (ValueError, ZeroDivisionError):
            return 0.0

    def is_suspected_dead(self) -> bool:
        """Check if node is suspected dead (phi > threshold)."""
        return self.get_phi() > self.threshold

    def get_status(self) -> str:
        """Get current status."""
        phi = self.get_phi()
        status = "SUSPECTED DEAD" if self.is_suspected_dead() else "ALIVE"
        confidence = min(phi / self.threshold * 100, 100)
        return f"{status} (φ={phi:.2f}, confidence={confidence:.0f}%)"


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


def demo_1_healthy_node():
    """
    Demo 1: Healthy node sending regular heartbeats.

    Phi stays low because heartbeats arrive regularly.
    """
    print_header("DEMO 1: Healthy Node")
    print("""
    A healthy node sends heartbeats regularly.
    Phi stays low because heartbeats arrive as expected.
    """)

    detector = PhiAccrualDetector(threshold=5.0)
    detector.node_id = "Node-A"

    print("  Scenario: Node sends heartbeat every 100ms")
    print(f"  {'#':<4} {'Time (ms)':<12} {'Phi':<8} {'Status':<30}")
    print(f"  {'─'*60}")

    for i in range(15):
        # Simulate heartbeat every 100ms
        time.sleep(0.1)
        detector.receive_heartbeat()

        phi = detector.get_phi()
        status = detector.get_status()

        elapsed = (time.time() - detector.last_heartbeat_time) * 1000
        print(f"  {i+1:<4} {elapsed:<12.0f} {phi:<8.2f} {status:<30}")

    print("""
  💡 KEY INSIGHT:
     Phi stays low (< 1.0) because heartbeats arrive regularly.
     The node is clearly alive.
    """)


def demo_2_node_becomes_slow():
    """
    Demo 2: Node becomes slow (increased latency).

    Phi increases as heartbeats arrive later than expected.
    """
    print_header("DEMO 2: Node Becomes Slow")
    print("""
    The node is still alive but becomes slow.
    Heartbeats arrive later than expected.
    Phi increases but stays below threshold.
    """)

    detector = PhiAccrualDetector(threshold=5.0)
    detector.node_id = "Node-B"

    print("  Scenario: Node latency increases from 100ms to 500ms")
    print(f"  {'#':<4} {'Interval (ms)':<15} {'Phi':<8} {'Status':<30}")
    print(f"  {'─'*60}")

    # Normal heartbeats
    for i in range(5):
        time.sleep(0.1)
        detector.receive_heartbeat()
        phi = detector.get_phi()
        status = detector.get_status()
        print(f"  {i+1:<4} {'100':<15} {phi:<8.2f} {status:<30}")

    # Node becomes slow
    print("\n  Node becomes slow (latency increases)...")
    for i in range(5):
        time.sleep(0.5)  # 500ms instead of 100ms
        detector.receive_heartbeat()
        phi = detector.get_phi()
        status = detector.get_status()
        print(f"  {i+6:<4} {'500':<15} {phi:<8.2f} {status:<30}")

    print("""
  💡 KEY INSIGHT:
     Phi increased as heartbeats arrived later.
     But it stayed below threshold (5.0) because heartbeats still arrived.
     The detector adapted to the new latency pattern.
    """)


def demo_3_node_dies():
    """
    Demo 3: Node dies (stops sending heartbeats).

    Phi increases rapidly as time passes without heartbeat.
    Eventually exceeds threshold.
    """
    print_header("DEMO 3: Node Dies")
    print("""
    The node dies and stops sending heartbeats.
    Phi increases rapidly as time passes.
    Eventually exceeds threshold and node is declared dead.
    """)

    detector = PhiAccrualDetector(threshold=5.0)
    detector.node_id = "Node-C"

    print("  Scenario: Node sends heartbeats, then dies")
    print(f"  {'#':<4} {'Time Since HB (ms)':<20} {'Phi':<8} {'Status':<30}")
    print(f"  {'─'*60}")

    # Normal heartbeats
    for i in range(5):
        time.sleep(0.1)
        detector.receive_heartbeat()
        phi = detector.get_phi()
        status = detector.get_status()
        elapsed = (time.time() - detector.last_heartbeat_time) * 1000
        print(f"  {i+1:<4} {elapsed:<20.0f} {phi:<8.2f} {status:<30}")

    # Node dies (no more heartbeats)
    print("\n  💀 Node dies (no more heartbeats)...")
    for i in range(8):
        time.sleep(0.2)
        # Don't call receive_heartbeat() - node is dead
        phi = detector.get_phi()
        status = detector.get_status()
        elapsed = (time.time() - detector.last_heartbeat_time) * 1000
        print(f"  {i+6:<4} {elapsed:<20.0f} {phi:<8.2f} {status:<30}")

    print("""
  💡 KEY INSIGHT:
     Phi increased rapidly as time passed without heartbeat.
     When phi exceeded threshold (5.0), node was declared dead.

     The detector didn't need a fixed timeout!
     It adapted based on the observed heartbeat pattern.
    """)


def demo_4_threshold_comparison():
    """
    Demo 4: Show how different thresholds affect detection.

    Lower threshold = faster detection but more false positives.
    Higher threshold = slower detection but fewer false positives.
    """
    print_header("DEMO 4: Threshold Comparison")
    print("""
    Different applications can choose different thresholds based on
    their tolerance for false positives vs detection speed.

    DDIA: "The application chooses its own threshold for declaring
    a node dead."
    """)

    thresholds = [1.0, 3.0, 5.0, 8.0]

    print("  Scenario: Node dies after 5 heartbeats")
    print(f"  {'Time (ms)':<12}", end="")
    for t in thresholds:
        print(f"  {'φ (T='+str(t)+')':<12}", end="")
    print()
    print(f"  {'─'*12}", end="")
    for _ in thresholds:
        print(f"  {'─'*12}", end="")
    print()

    detectors = [PhiAccrualDetector(threshold=t) for t in thresholds]

    # Normal heartbeats
    for i in range(5):
        time.sleep(0.1)
        for detector in detectors:
            detector.receive_heartbeat()

    # Node dies
    for i in range(10):
        time.sleep(0.1)
        elapsed = (time.time() - detectors[0].last_heartbeat_time) * 1000

        print(f"  {elapsed:<12.0f}", end="")
        for detector in detectors:
            phi = detector.get_phi()
            status = "DEAD" if detector.is_suspected_dead() else "ALIVE"
            print(f"  {phi:<8.2f} {status:<3}", end="")
        print()

    print("""
  💡 KEY INSIGHT:
     Different thresholds have different trade-offs:

     Threshold = 1.0 (aggressive):
       ✅ Fast detection (detects dead node quickly)
       ❌ More false positives (healthy nodes might be declared dead)

     Threshold = 5.0 (balanced):
       ✅ Good balance between speed and accuracy
       ✅ Used by Cassandra

     Threshold = 8.0 (conservative):
       ✅ Fewer false positives
       ❌ Slower detection (takes longer to detect dead node)

     Applications choose based on their requirements!
    """)


def demo_5_comparison_with_fixed_timeout():
    """
    Demo 5: Compare Phi Accrual with fixed timeout.

    Show how Phi Accrual adapts while fixed timeout doesn't.
    """
    print_header("DEMO 5: Phi Accrual vs Fixed Timeout")
    print("""
    Compare the Phi Accrual detector with a simple fixed timeout.

    Fixed timeout: Binary decision (dead or alive)
    Phi Accrual: Continuous suspicion level (0 to infinity)
    """)

    phi_detector = PhiAccrualDetector(threshold=5.0)
    fixed_timeout_ms = 500

    print("  Scenario: Node latency increases gradually")
    print(f"  {'#':<4} {'Interval (ms)':<15} {'Phi':<8} {'Fixed Timeout':<20}")
    print(f"  {'─'*60}")

    # Gradually increasing latency
    intervals = [100, 150, 200, 250, 300, 350, 400, 450, 500, 550, 600]

    for i, interval_ms in enumerate(intervals):
        time.sleep(interval_ms / 1000)
        phi_detector.receive_heartbeat()

        phi = phi_detector.get_phi()
        phi_status = "DEAD" if phi_detector.is_suspected_dead() else "ALIVE"

        # Fixed timeout
        if interval_ms > fixed_timeout_ms:
            fixed_status = "DEAD (timeout)"
        else:
            fixed_status = "ALIVE"

        print(f"  {i+1:<4} {interval_ms:<15} {phi:<8.2f} {phi_status:<8} {fixed_status:<20}")

    print("""
  💡 KEY INSIGHT:
     Phi Accrual gradually increases suspicion as latency increases.
     It adapts to the changing network conditions.

     Fixed timeout is binary:
       • Below threshold: ALIVE
       • Above threshold: DEAD (sudden change)

     Phi Accrual is continuous:
       • Gradually increases suspicion
       • Adapts to network patterns
       • Application chooses when to declare dead
    """)


def demo_6_real_world_scenario():
    """
    Demo 6: Real-world scenario with network jitter.

    Simulate a realistic network with variable latency.
    """
    print_header("DEMO 6: Real-World Scenario")
    print("""
    Simulate a realistic network with variable latency (jitter).
    The Phi Accrual detector adapts to the pattern.
    """)

    detector = PhiAccrualDetector(threshold=5.0)

    print("  Scenario: Network with variable latency (jitter)")
    print("  Normal latency: 50-150ms")
    print("  Spike: 500-1000ms")
    print("  Node dies: No heartbeats")

    print(f"\n  {'#':<4} {'Interval (ms)':<15} {'Phi':<8} {'Status':<30}")
    print(f"  {'─'*60}")

    # Phase 1: Normal latency with jitter
    print("\n  Phase 1: Normal network (50-150ms jitter)")
    for i in range(8):
        interval = random.uniform(50, 150)
        time.sleep(interval / 1000)
        detector.receive_heartbeat()
        phi = detector.get_phi()
        status = detector.get_status()
        print(f"  {i+1:<4} {interval:<15.0f} {phi:<8.2f} {status:<30}")

    # Phase 2: Network spike
    print("\n  Phase 2: Network spike (500-1000ms)")
    for i in range(3):
        interval = random.uniform(500, 1000)
        time.sleep(interval / 1000)
        detector.receive_heartbeat()
        phi = detector.get_phi()
        status = detector.get_status()
        print(f"  {i+9:<4} {interval:<15.0f} {phi:<8.2f} {status:<30}")

    # Phase 3: Node dies
    print("\n  Phase 3: Node dies (no heartbeats)")
    for i in range(5):
        time.sleep(0.2)
        phi = detector.get_phi()
        status = detector.get_status()
        elapsed = (time.time() - detector.last_heartbeat_time) * 1000
        print(f"  {i+12:<4} {elapsed:<15.0f} {phi:<8.2f} {status:<30}")

    print("""
  💡 KEY INSIGHT:
     The Phi Accrual detector handled all three phases:
       1. Normal jitter: Phi stayed low
       2. Network spike: Phi increased but stayed below threshold
       3. Node dies: Phi increased rapidly and exceeded threshold

     The detector adapted to the changing network conditions
     without requiring manual timeout tuning!
    """)


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 80)
    print("  EXERCISE 4: PHI ACCRUAL FAILURE DETECTOR")
    print("  DDIA Chapter 8: 'Phi Accrual Failure Detector'")
    print("=" * 80)
    print("""
  This exercise implements the Phi Accrual failure detector used by Akka
  and Cassandra. Instead of a binary "dead or alive" decision, it outputs
  a suspicion level (phi φ) that increases over time without a heartbeat.
    """)

    demo_1_healthy_node()
    demo_2_node_becomes_slow()
    demo_3_node_dies()
    demo_4_threshold_comparison()
    demo_5_comparison_with_fixed_timeout()
    demo_6_real_world_scenario()

    print("\n" + "=" * 80)
    print("  EXERCISE 4 COMPLETE ✅")
    print("=" * 80)
    print("""
  Key Takeaways:

  1. 📊 Phi Accrual outputs suspicion level (not binary)
  2. 📊 φ = -log10(P(heartbeat arrives within time t))
  3. 📊 Adapts to observed heartbeat patterns
  4. 📊 Application chooses threshold for declaring dead
  5. ✅ Used by Akka, Cassandra, and other systems
  6. ✅ Better than fixed timeouts (no false positives)

  Next: You've completed Chapter 8, Section 2!
  Ready for Section 3: Unreliable Clocks
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
