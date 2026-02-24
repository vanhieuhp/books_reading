"""
Exercise 2: Monotonic vs Wall-Clock Time

DDIA Reference: Chapter 8, "Two Types of Clocks" (pp. 112-124)

This exercise demonstrates the difference between two types of clocks:
  - Time-of-day clocks: Return current date/time (can jump backward)
  - Monotonic clocks: Always move forward (good for measuring durations)

Key concepts:
  - Wall-clock time is synchronized to NTP but can jump
  - Monotonic time always increases but is not comparable across machines
  - Use wall-clock for "what time is it?" questions
  - Use monotonic for "how long did this take?" questions

Run: python 02_monotonic_vs_wall_clock.py
"""

import sys
import time
from typing import List, Tuple
from dataclasses import dataclass
from enum import Enum

# Fix Windows terminal encoding for Unicode output
sys.stdout.reconfigure(encoding='utf-8')


# =============================================================================
# CORE COMPONENTS: Clock Types
# =============================================================================

class ClockType(Enum):
    """Types of clocks in distributed systems."""
    WALL_CLOCK = "wall_clock"      # Time-of-day clock
    MONOTONIC = "monotonic"        # Monotonic clock


@dataclass
class TimeReading:
    """A reading from a clock."""
    clock_type: ClockType
    value: float
    description: str

    def __repr__(self):
        return f"{self.description}: {self.value:.3f}"


class SystemClock:
    """
    Simulates a system clock with both wall-clock and monotonic time.

    DDIA insight: "Every computer has at least two different clocks:
    a time-of-day clock and a monotonic clock."
    """

    def __init__(self, node_id: str):
        self.node_id = node_id
        self.wall_clock_offset = 0.0  # Simulates NTP adjustments
        self.monotonic_base = time.time()  # Base for monotonic time
        self.monotonic_offset = 0.0  # Simulates monotonic adjustments

    def get_wall_clock(self) -> float:
        """
        Get time-of-day clock (wall-clock time).

        DDIA: "Time-of-day clocks are synchronized to NTP. They may jump
        forward or backward if an NTP adjustment is made."
        """
        return time.time() + self.wall_clock_offset

    def get_monotonic_clock(self) -> float:
        """
        Get monotonic clock (elapsed time since arbitrary point).

        DDIA: "Monotonic clocks are not affected by NTP adjustments.
        They always move forward."
        """
        return time.time() - self.monotonic_base + self.monotonic_offset

    def simulate_ntp_adjustment(self, delta_seconds: float):
        """Simulate an NTP adjustment (clock jump)."""
        self.wall_clock_offset += delta_seconds

    def simulate_monotonic_adjustment(self, delta_seconds: float):
        """Simulate a monotonic clock adjustment (rare, but possible)."""
        self.monotonic_offset += delta_seconds


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


def demo_1_wall_clock_basics():
    """
    Demo 1: Wall-clock time basics.

    DDIA concept: "Time-of-day clocks return the current date and time."
    """
    print_header("DEMO 1: Wall-Clock Time (Time-of-Day)")
    print("""
    Wall-clock time is what you see on your watch.
    It's synchronized to NTP but can jump forward or backward.
    """)

    clock = SystemClock("Node-A")

    print("  📍 Reading wall-clock time multiple times:")
    print()

    readings = []
    for i in range(5):
        wall_time = clock.get_wall_clock()
        readings.append(wall_time)
        print(f"    Reading {i+1}: {wall_time:.3f}")
        time.sleep(0.01)

    # Verify monotonic increase
    is_monotonic = all(readings[i] <= readings[i+1] for i in range(len(readings)-1))
    print(f"\n  ✅ Wall-clock time is monotonically increasing: {is_monotonic}")

    print("""
  💡 KEY INSIGHT:
     Wall-clock time usually increases, but it can jump backward
     if NTP makes an adjustment.
    """)


def demo_2_monotonic_clock_basics():
    """
    Demo 2: Monotonic clock basics.

    DDIA concept: "Monotonic clocks always move forward."
    """
    print_header("DEMO 2: Monotonic Clock (Elapsed Time)")
    print("""
    Monotonic clocks measure elapsed time since an arbitrary point.
    They NEVER jump backward, even if NTP adjusts the system time.
    """)

    clock = SystemClock("Node-A")

    print("  📍 Reading monotonic clock multiple times:")
    print()

    readings = []
    for i in range(5):
        mono_time = clock.get_monotonic_clock()
        readings.append(mono_time)
        print(f"    Reading {i+1}: {mono_time:.3f}")
        time.sleep(0.01)

    # Verify monotonic increase
    is_monotonic = all(readings[i] <= readings[i+1] for i in range(len(readings)-1))
    print(f"\n  ✅ Monotonic clock is always increasing: {is_monotonic}")

    print("""
  💡 KEY INSIGHT:
     Monotonic clocks are guaranteed to never jump backward.
     This makes them perfect for measuring durations.
    """)


def demo_3_measuring_duration():
    """
    Demo 3: Using monotonic clocks to measure duration.

    DDIA concept: "Use monotonic clocks for measuring elapsed time."
    """
    print_header("DEMO 3: Measuring Duration (Correct Way)")
    print("""
    To measure how long an operation takes, use monotonic clocks.
    Wall-clock time can jump, making duration measurements unreliable.
    """)

    clock = SystemClock("Node-A")

    print("  📍 Measuring operation duration using monotonic clock:")
    print()

    # Start operation
    start_mono = clock.get_monotonic_clock()
    print(f"    Operation started at monotonic time: {start_mono:.3f}")

    # Simulate operation
    time.sleep(0.05)

    # End operation
    end_mono = clock.get_monotonic_clock()
    print(f"    Operation ended at monotonic time:   {end_mono:.3f}")

    duration = end_mono - start_mono
    print(f"\n    Duration: {duration:.3f} seconds ✅")

    print("""
  💡 KEY INSIGHT:
     Monotonic clocks are perfect for measuring durations.
     The difference between two monotonic readings is always accurate.
    """)


def demo_4_wall_clock_jump():
    """
    Demo 4: Wall-clock can jump backward (NTP adjustment).

    DDIA concept: "NTP can occasionally jump backward."
    """
    print_header("DEMO 4: Wall-Clock Jump (NTP Adjustment)")
    print("""
    When NTP adjusts the system time, wall-clock can jump backward.
    This breaks duration measurements if you use wall-clock time.
    """)

    clock = SystemClock("Node-A")

    print("  📍 Scenario: NTP adjustment causes clock to jump backward")
    print()

    # Read wall-clock before adjustment
    wall_before = clock.get_wall_clock()
    print(f"    Wall-clock before NTP adjustment: {wall_before:.3f}")

    # Simulate NTP adjustment: clock jumps backward by 100ms
    print(f"\n    ⏰ NTP adjustment: Clock jumps backward by 100ms!")
    clock.simulate_ntp_adjustment(-0.1)

    # Read wall-clock after adjustment
    wall_after = clock.get_wall_clock()
    print(f"    Wall-clock after NTP adjustment:  {wall_after:.3f}")

    print(f"\n    ⚠️  Wall-clock went BACKWARD: {wall_before:.3f} → {wall_after:.3f}")

    print("""
  💥 CONSEQUENCES:
     If you measure duration using wall-clock:
       start_time = wall_clock()  # 1000.500
       ... do work ...
       end_time = wall_clock()    # 1000.400 (jumped backward!)
       duration = end_time - start_time  # -0.100 (NEGATIVE!)

     This breaks timeouts, leases, and any time-based logic.
    """)


def demo_5_comparing_across_machines():
    """
    Demo 5: Monotonic clocks are not comparable across machines.

    DDIA concept: "Monotonic clocks are not meaningful across machines."
    """
    print_header("DEMO 5: Monotonic Clocks Are Not Comparable Across Machines")
    print("""
    Monotonic clocks measure elapsed time since an arbitrary point.
    Different machines have different arbitrary points, so you can't
    compare monotonic clock values across machines.
    """)

    node_a = SystemClock("Node-A")
    node_b = SystemClock("Node-B")

    print("  📍 Reading monotonic clocks from two different nodes:")
    print()

    mono_a = node_a.get_monotonic_clock()
    mono_b = node_b.get_monotonic_clock()

    print(f"    Node A monotonic clock: {mono_a:.3f}")
    print(f"    Node B monotonic clock: {mono_b:.3f}")

    print(f"\n    ⚠️  These values are NOT comparable!")
    print(f"    Node A's 0 point is different from Node B's 0 point.")

    print("""
  💡 KEY INSIGHT:
     Monotonic clocks are perfect for measuring durations on a single machine.
     But you CANNOT use them to order events across machines.

     DDIA: "Monotonic clocks are not meaningful across machines."
    """)


def demo_6_wall_clock_for_ordering():
    """
    Demo 6: Wall-clock time for ordering events (with caveats).

    DDIA concept: "Wall-clock time can be used for ordering, but with care."
    """
    print_header("DEMO 6: Using Wall-Clock for Ordering Events")
    print("""
    Wall-clock time can be used to order events across machines,
    but only if you account for clock skew and NTP adjustments.
    """)

    node_a = SystemClock("Node-A")
    node_b = SystemClock("Node-B")

    print("  📍 Scenario: Two events on different nodes")
    print()

    # Event 1: on Node A
    event1_time = node_a.get_wall_clock()
    print(f"    Event 1 on Node A at wall-clock time: {event1_time:.3f}")

    time.sleep(0.01)

    # Event 2: on Node B
    event2_time = node_b.get_wall_clock()
    print(f"    Event 2 on Node B at wall-clock time: {event2_time:.3f}")

    print(f"\n    Event 2 happened after Event 1: {event2_time > event1_time}")

    print("""
  ⚠️  CAVEATS:
     1. Clock skew: Node A's clock might be ahead of Node B's
     2. NTP jumps: Clocks can jump backward
     3. Precision: Clocks may not have enough precision

     DDIA: "You cannot rely on wall-clock time for ordering events
     in a distributed system."
    """)


def demo_7_best_practices():
    """
    Demo 7: Best practices for using clocks.

    DDIA concept: "Use the right clock for the right job."
    """
    print_header("DEMO 7: Best Practices for Using Clocks")
    print("""
    Summary of when to use each type of clock:
    """)

    print("""
  📊 WALL-CLOCK TIME (Time-of-Day):
     ✅ Use for:
        - Recording when an event happened (for logs, timestamps)
        - Displaying current time to users
        - Scheduling tasks at specific times

     ❌ Don't use for:
        - Measuring durations
        - Ordering events across machines
        - Timeouts and leases

  📊 MONOTONIC CLOCK (Elapsed Time):
     ✅ Use for:
        - Measuring how long an operation took
        - Implementing timeouts
        - Detecting when a deadline has passed

     ❌ Don't use for:
        - Ordering events across machines
        - Recording absolute timestamps
        - Comparing times from different machines

  📊 LOGICAL CLOCKS (Lamport, Vector Clocks):
     ✅ Use for:
        - Ordering events across machines
        - Detecting causality
        - Conflict resolution

     ❌ Don't use for:
        - Measuring real-world time
        - Scheduling tasks
        - Timeouts
    """)


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 80)
    print("  EXERCISE 2: MONOTONIC VS WALL-CLOCK TIME")
    print("  DDIA Chapter 8: 'Two Types of Clocks'")
    print("=" * 80)
    print("""
  This exercise demonstrates the difference between two types of clocks
  and when to use each one.

  Key insight: Use the right clock for the right job!
    """)

    demo_1_wall_clock_basics()
    demo_2_monotonic_clock_basics()
    demo_3_measuring_duration()
    demo_4_wall_clock_jump()
    demo_5_comparing_across_machines()
    demo_6_wall_clock_for_ordering()
    demo_7_best_practices()

    print("\n" + "=" * 80)
    print("  EXERCISE 2 COMPLETE ✅")
    print("=" * 80)
    print("""
  Key Takeaways:

  1. 🕐 Wall-clock time can jump backward (NTP adjustments)
  2. ⏱️  Monotonic clocks always move forward
  3. 📏 Use monotonic clocks for measuring durations
  4. 🌍 Monotonic clocks are not comparable across machines
  5. 🔗 Use logical clocks for ordering events across machines

  Next: Run 03_process_pauses.py to learn about GC pauses and leases
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
