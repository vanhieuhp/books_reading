"""
Exercise 1: Clock Skew — The Silent Killer

DDIA Reference: Chapter 8, "Unreliable Clocks" (pp. 106-145)

This exercise demonstrates how clock skew (disagreement between machines' clocks)
breaks Last-Write-Wins (LWW) conflict resolution, leading to silent data loss.

Key concepts:
  - Different machines' clocks can differ by milliseconds or more
  - NTP synchronization is imperfect
  - Last-Write-Wins with physical timestamps is fundamentally broken
  - An increment of 1ms in clock skew can cause data loss

Run: python 01_clock_skew.py
"""

import sys
import time
from typing import Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum

# Fix Windows terminal encoding for Unicode output
sys.stdout.reconfigure(encoding='utf-8')


# =============================================================================
# CORE COMPONENTS: Clock, Node, Storage
# =============================================================================

class ClockType(Enum):
    """Types of clocks in distributed systems."""
    ACCURATE = "accurate"      # Correct time
    FAST = "fast"              # Ahead of real time
    SLOW = "slow"              # Behind real time


@dataclass
class Write:
    """A write operation with timestamp."""
    key: str
    value: str
    timestamp: float  # Physical timestamp from the writing node's clock
    node_id: str

    def __repr__(self):
        return f"Write(key={self.key}, value={self.value}, ts={self.timestamp:.3f}, node={self.node_id})"


class Node:
    """
    A database node with its own clock.

    DDIA insight: "Every machine has its own clock, and no two clocks agree
    perfectly. Even with NTP synchronization, clocks drift by milliseconds."
    """

    def __init__(self, node_id: str, clock_type: ClockType = ClockType.ACCURATE, skew_ms: float = 0):
        self.node_id = node_id
        self.clock_type = clock_type
        self.skew_ms = skew_ms  # Milliseconds ahead/behind real time
        self.storage: Dict[str, Tuple[str, float]] = {}  # key -> (value, timestamp)
        self.write_history: List[Write] = []

    def get_time(self) -> float:
        """Get current time from this node's clock (with skew)."""
        real_time = time.time()
        skew_seconds = self.skew_ms / 1000.0
        return real_time + skew_seconds

    def write(self, key: str, value: str) -> Write:
        """
        Write a key-value pair with this node's timestamp.

        DDIA: "The leader writes the data to its local storage and sends
        the data change to all of its followers."
        """
        timestamp = self.get_time()
        write = Write(key=key, value=value, timestamp=timestamp, node_id=self.node_id)
        self.write_history.append(write)
        return write

    def apply_write(self, write: Write) -> bool:
        """
        Apply a write using Last-Write-Wins (LWW) conflict resolution.

        DDIA: "Last-Write-Wins: The write with the highest timestamp wins."

        Returns True if this write was applied, False if it was rejected.
        """
        if write.key not in self.storage:
            # First write for this key
            self.storage[write.key] = (write.value, write.timestamp)
            return True

        current_value, current_timestamp = self.storage[write.key]

        if write.timestamp > current_timestamp:
            # New write has higher timestamp — it wins
            self.storage[write.key] = (write.value, write.timestamp)
            return True
        else:
            # Current write has higher timestamp — reject new write
            return False

    def read(self, key: str) -> str:
        """Read a value from storage."""
        if key in self.storage:
            value, _ = self.storage[key]
            return value
        return None


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


def demo_1_basic_lww():
    """
    Demo 1: Last-Write-Wins works fine when clocks are synchronized.

    DDIA concept: "Last-Write-Wins is simple and works when clocks are accurate."
    """
    print_header("DEMO 1: Last-Write-Wins (With Accurate Clocks)")
    print("""
    When all nodes have synchronized clocks, LWW works correctly.
    The write with the highest timestamp wins.
    """)

    # Create two nodes with accurate clocks
    node_a = Node("Node-A", clock_type=ClockType.ACCURATE, skew_ms=0)
    node_b = Node("Node-B", clock_type=ClockType.ACCURATE, skew_ms=0)

    print("  📍 Setup: Two nodes with ACCURATE clocks (0ms skew)")
    print(f"     Node A clock: {node_a.get_time():.3f}")
    print(f"     Node B clock: {node_b.get_time():.3f}")

    # Simulate writes
    print("\n  📝 Scenario: Two clients write to the same key")

    # Write 1: Client writes to Node B
    time.sleep(0.01)  # Small delay
    write1 = node_b.write("user:1:name", "Alice")
    print(f"\n    Write 1: {write1}")

    # Write 2: Client writes to Node A (slightly later)
    time.sleep(0.01)
    write2 = node_a.write("user:1:name", "Bob")
    print(f"    Write 2: {write2}")

    # Both nodes apply both writes using LWW
    print("\n  🔄 Applying writes to both nodes using LWW:")

    node_a.apply_write(write1)
    node_a.apply_write(write2)
    print(f"    Node A: Applied Write 1 ✅, Applied Write 2 ✅ (higher timestamp)")

    node_b.apply_write(write1)
    node_b.apply_write(write2)
    print(f"    Node B: Applied Write 1 ✅, Applied Write 2 ✅ (higher timestamp)")

    # Verify consistency
    print("\n  ✅ Final state:")
    print(f"    Node A: user:1:name = {node_a.read('user:1:name')}")
    print(f"    Node B: user:1:name = {node_b.read('user:1:name')}")
    print(f"    Consistent: YES ✅")

    print("""
  💡 KEY INSIGHT:
     When clocks are synchronized, LWW works correctly.
     The write with the highest timestamp wins, and both nodes agree.
    """)


def demo_2_clock_skew_disaster():
    """
    Demo 2: Clock skew breaks LWW — silent data loss!

    DDIA concept: "Clock Skew: The Silent Killer"
    "An increment of 1ms in clock skew can cause data loss."
    """
    print_header("DEMO 2: Clock Skew Breaks LWW (Silent Data Loss)")
    print("""
    When clocks are skewed, LWW chooses the WRONG winner.
    The write with the highest timestamp wins, but that timestamp
    may not reflect the actual order of events!
    """)

    # Create two nodes with clock skew
    node_a = Node("Node-A", clock_type=ClockType.FAST, skew_ms=5)  # 5ms FAST
    node_b = Node("Node-B", clock_type=ClockType.ACCURATE, skew_ms=0)  # Accurate

    print("  📍 Setup: Two nodes with CLOCK SKEW")
    print(f"     Node A clock: {node_a.get_time():.3f}  (5ms FAST)")
    print(f"     Node B clock: {node_b.get_time():.3f}  (accurate)")

    # Simulate writes in real time order
    print("\n  📝 Scenario: Two writes in REAL TIME order")
    print("     (But Node A's clock is ahead!)")

    # Write 1: Client writes to Node B FIRST (in real time)
    write1 = node_b.write("user:1:name", "Alice")
    print(f"\n    Write 1 (FIRST in real time):  {write1}")

    # Write 2: Client writes to Node A SECOND (in real time)
    # But Node A's clock is ahead, so it gets a higher timestamp!
    time.sleep(0.001)  # Tiny delay
    write2 = node_a.write("user:1:name", "Bob")
    print(f"    Write 2 (SECOND in real time): {write2}")

    print(f"\n  ⚠️  PROBLEM: Write 2's timestamp ({write2.timestamp:.3f}) > Write 1's timestamp ({write1.timestamp:.3f})")
    print(f"     But Write 1 actually happened FIRST in real time!")

    # Both nodes apply both writes using LWW
    print("\n  🔄 Applying writes to both nodes using LWW:")

    node_a.apply_write(write1)
    result_a1 = node_a.apply_write(write2)
    print(f"    Node A: Applied Write 1 ✅, Applied Write 2 ✅ (higher timestamp)")

    node_b.apply_write(write1)
    result_b1 = node_b.apply_write(write2)
    print(f"    Node B: Applied Write 1 ✅, Applied Write 2 ✅ (higher timestamp)")

    # Verify consistency
    print("\n  ❌ Final state:")
    print(f"    Node A: user:1:name = {node_a.read('user:1:name')}")
    print(f"    Node B: user:1:name = {node_b.read('user:1:name')}")
    print(f"    Consistent: YES (but WRONG value!)")

    print("""
  💥 DATA LOSS OCCURRED:
     Write 1 (Alice) was SILENTLY DELETED!
     Write 2 (Bob) won because it had a higher timestamp.
     But Write 1 actually happened FIRST in real time!

     The user's name was changed from Alice to Bob,
     but the system thinks Bob was written first.
     Alice's write is lost forever.
    """)


def demo_3_varying_clock_skew():
    """
    Demo 3: Show how different amounts of clock skew affect data loss.

    DDIA concept: "Even small clock skew can cause data loss."
    """
    print_header("DEMO 3: Impact of Clock Skew on Data Loss")
    print("""
    How much clock skew is needed to cause data loss?
    Answer: Even 1 millisecond can cause problems!
    """)

    skew_values = [0, 1, 5, 10, 50, 100]  # milliseconds

    print("  📊 Testing different clock skew values:\n")
    print(f"  {'Skew (ms)':<12} {'Write 1 TS':<15} {'Write 2 TS':<15} {'Winner':<12} {'Data Loss?'}")
    print(f"  {'─'*70}")

    for skew_ms in skew_values:
        node_a = Node("Node-A", clock_type=ClockType.FAST, skew_ms=skew_ms)
        node_b = Node("Node-B", clock_type=ClockType.ACCURATE, skew_ms=0)

        # Write 1: to Node B (first in real time)
        write1 = node_b.write("key", "value1")

        # Write 2: to Node A (second in real time)
        time.sleep(0.001)
        write2 = node_a.write("key", "value2")

        winner = "Write 2" if write2.timestamp > write1.timestamp else "Write 1"
        data_loss = "❌ YES" if write2.timestamp > write1.timestamp else "✅ NO"

        print(f"  {skew_ms:<12} {write1.timestamp:<15.3f} {write2.timestamp:<15.3f} {winner:<12} {data_loss}")

    print("""
  💡 KEY INSIGHT:
     Even 1ms of clock skew can cause data loss!
     This is why relying on physical timestamps for ordering is dangerous.

     DDIA: "An increment of 1ms in clock skew can cause data loss."
    """)


def demo_4_ntp_jump():
    """
    Demo 4: NTP can jump backward, breaking LWW even more.

    DDIA concept: "NTP can occasionally jump backward"
    """
    print_header("DEMO 4: NTP Clock Jump (Backward)")
    print("""
    NTP synchronization can cause clocks to jump backward.
    This is even worse than gradual skew!
    """)

    print("  📍 Scenario: NTP adjustment causes clock to jump backward")

    # Simulate a node with a clock that jumps backward
    node = Node("Node-A", clock_type=ClockType.ACCURATE, skew_ms=0)

    # Write 1
    write1 = node.write("key", "value1")
    print(f"\n    Write 1 at time {write1.timestamp:.3f}: {write1}")

    # Simulate NTP adjustment: clock jumps backward by 100ms
    print(f"\n    ⏰ NTP adjustment: Clock jumps backward by 100ms!")

    # Write 2 (with clock jumped backward)
    node.skew_ms = -100  # Simulate clock jump
    write2 = node.write("key", "value2")
    print(f"    Write 2 at time {write2.timestamp:.3f}: {write2}")

    print(f"\n  ⚠️  PROBLEM: Write 2's timestamp ({write2.timestamp:.3f}) < Write 1's timestamp ({write1.timestamp:.3f})")
    print(f"     Write 1 will be considered the \"latest\" write!")
    print(f"     Write 2 will be silently rejected!")

    print("""
  💥 CONSEQUENCES:
     - Write 2 is lost
     - Timeouts may expire prematurely
     - Leases may be considered expired when they're not
     - Cascading failures can occur
    """)


def demo_5_google_spanner_solution():
    """
    Demo 5: Google Spanner's TrueTime solution.

    DDIA concept: "Google Spanner's approach (TrueTime)"
    """
    print_header("DEMO 5: Google Spanner's TrueTime Solution")
    print("""
    Google Spanner solves clock skew using GPS receivers and atomic clocks.
    The TrueTime API returns an uncertainty interval instead of a point in time.
    """)

    print("""
  🛰️  Google Spanner's approach:
     1. GPS receivers in every datacenter
     2. Atomic clocks for backup
     3. Clocks synchronized to within ~7ms
     4. TrueTime API returns [earliest, latest] interval
     5. Transactions wait for intervals to pass before committing

  💰 Cost: VERY EXPENSIVE
     - GPS receivers: $100,000+
     - Atomic clocks: $50,000+
     - Specialized infrastructure
     - Only Google can afford this

  📊 Result:
     - Guaranteed ordering of transactions
     - No silent data loss from clock skew
     - But: No open-source database replicates this approach
    """)


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 80)
    print("  EXERCISE 1: CLOCK SKEW — THE SILENT KILLER")
    print("  DDIA Chapter 8: 'Unreliable Clocks'")
    print("=" * 80)
    print("""
  This exercise demonstrates how clock skew breaks Last-Write-Wins (LWW)
  conflict resolution, leading to silent data loss.

  Key insight: You cannot use physical timestamps to order events
  in a distributed system. Clocks are unreliable.
    """)

    demo_1_basic_lww()
    demo_2_clock_skew_disaster()
    demo_3_varying_clock_skew()
    demo_4_ntp_jump()
    demo_5_google_spanner_solution()

    print("\n" + "=" * 80)
    print("  EXERCISE 1 COMPLETE ✅")
    print("=" * 80)
    print("""
  Key Takeaways:

  1. 🕐 Different machines' clocks can differ by milliseconds or more
  2. 📉 NTP synchronization is imperfect and can jump backward
  3. 💥 Last-Write-Wins with physical timestamps is fundamentally broken
  4. 🔇 Clock skew causes SILENT data loss (no error message!)
  5. 🛰️  Google Spanner's TrueTime is the only reliable solution (and very expensive)

  Next: Run 02_monotonic_vs_wall_clock.py to learn about clock types
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
