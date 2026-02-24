"""
Exercise 3: Synchronous vs Asynchronous Replication

DDIA Reference: Chapter 5, "Synchronous Versus Asynchronous Replication" (pp. 153-155)

This exercise demonstrates the fundamental trade-off:
  - SYNCHRONOUS: Slow but safe (data on multiple nodes before ACK)
  - ASYNCHRONOUS: Fast but risky (data loss if leader crashes)
  - SEMI-SYNCHRONOUS: Sweet spot (1 sync + N async)

You'll see REAL timing differences and understand why most systems
choose async or semi-sync in production.

Run: python 03_sync_vs_async.py
"""

import sys
import time
import random
import threading
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum

# Fix Windows terminal encoding for Unicode output
sys.stdout.reconfigure(encoding='utf-8')


# =============================================================================
# REPLICATION MODES
# =============================================================================

class ReplicationMode(Enum):
    SYNCHRONOUS = "synchronous"
    ASYNCHRONOUS = "asynchronous"
    SEMI_SYNCHRONOUS = "semi-synchronous"


class FollowerNode:
    """A follower node with configurable network delay and failure simulation."""

    def __init__(self, name: str, network_delay_ms: float = 10.0, failure_rate: float = 0.0):
        self.name = name
        self.network_delay_ms = network_delay_ms
        self.failure_rate = failure_rate  # 0.0 = never fail, 1.0 = always fail
        self.storage: Dict[int, Dict] = {}
        self.acknowledged = False
        self._is_down = False

    def receive_and_ack(self, write_id: int, data: Dict) -> Tuple[bool, float]:
        """
        Receive a write and acknowledge it.
        Returns (success, time_taken_ms).

        Simulates:
        - Network delay
        - Possible node failure
        """
        start = time.time()

        # Simulate network delay
        actual_delay = self.network_delay_ms / 1000.0
        actual_delay *= random.uniform(0.8, 1.2)  # Add jitter
        time.sleep(actual_delay)

        # Check for failure
        if random.random() < self.failure_rate or self._is_down:
            elapsed_ms = (time.time() - start) * 1000
            return False, elapsed_ms

        # Apply write
        self.storage[write_id] = data.copy()
        self.acknowledged = True
        elapsed_ms = (time.time() - start) * 1000
        return True, elapsed_ms

    def go_down(self):
        self._is_down = True

    def come_back(self):
        self._is_down = False


class ReplicationCluster:
    """
    A single-leader cluster with configurable replication mode.

    DDIA: "The advantage of synchronous replication is that the follower
    is guaranteed to have an up-to-date copy. The disadvantage is that
    if the synchronous follower doesn't respond, the write cannot be
    processed."
    """

    def __init__(self, mode: ReplicationMode, followers: List[FollowerNode],
                 sync_follower_count: int = 1):
        self.mode = mode
        self.followers = followers
        self.sync_follower_count = sync_follower_count
        self.leader_storage: Dict[int, Dict] = {}
        self._write_counter = 0
        self.write_stats: List[Dict] = []

    def write(self, data: Dict, timeout_ms: float = 5000) -> Dict[str, Any]:
        """
        Process a write through the leader.

        SYNCHRONOUS: Wait for ALL followers to ACK
        ASYNCHRONOUS: Don't wait for any follower
        SEMI-SYNC: Wait for sync_follower_count followers to ACK
        """
        self._write_counter += 1
        write_id = self._write_counter
        start = time.time()

        # Step 1: Write to leader's local storage
        self.leader_storage[write_id] = data.copy()

        result = {
            "write_id": write_id,
            "mode": self.mode.value,
            "data": data,
            "start_time": start,
        }

        if self.mode == ReplicationMode.SYNCHRONOUS:
            # Wait for ALL followers to acknowledge
            acks = []
            all_success = True
            for f in self.followers:
                success, delay_ms = f.receive_and_ack(write_id, data)
                acks.append({"follower": f.name, "success": success, "delay_ms": delay_ms})
                if not success:
                    all_success = False

            result["acks"] = acks
            result["success"] = all_success
            result["nodes_with_data"] = 1 + sum(1 for a in acks if a["success"])

        elif self.mode == ReplicationMode.ASYNCHRONOUS:
            # Return immediately — replicate in background
            result["success"] = True  # Always returns success quickly
            result["nodes_with_data"] = 1  # Only leader has data for now

            # Background replication (simulated)
            for f in self.followers:
                # Fire and forget — don't wait
                threading.Thread(
                    target=f.receive_and_ack,
                    args=(write_id, data),
                    daemon=True
                ).start()

            result["acks"] = [{"follower": f.name, "success": "pending", "delay_ms": 0}
                              for f in self.followers]

        elif self.mode == ReplicationMode.SEMI_SYNCHRONOUS:
            # Wait for at least sync_follower_count followers
            acks = []
            sync_count = 0
            for i, f in enumerate(self.followers):
                if sync_count < self.sync_follower_count:
                    # Sync follower — wait for ACK
                    success, delay_ms = f.receive_and_ack(write_id, data)
                    acks.append({"follower": f.name, "success": success,
                                 "delay_ms": delay_ms, "type": "SYNC"})
                    if success:
                        sync_count += 1
                else:
                    # Async followers — fire and forget
                    threading.Thread(
                        target=f.receive_and_ack,
                        args=(write_id, data),
                        daemon=True
                    ).start()
                    acks.append({"follower": f.name, "success": "pending",
                                 "delay_ms": 0, "type": "ASYNC"})

            result["acks"] = acks
            result["success"] = sync_count >= self.sync_follower_count
            result["nodes_with_data"] = 1 + sync_count

        elapsed_ms = (time.time() - start) * 1000
        result["total_ms"] = elapsed_ms

        self.write_stats.append(result)
        return result


# =============================================================================
# DEMONSTRATIONS
# =============================================================================

def print_header(title: str):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_section(title: str):
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}")


def demo_1_synchronous():
    """
    Demo 1: Synchronous replication — safe but slow.

    DDIA: "The leader waits until followers have confirmed that they
    received the write before reporting success to the user."
    """
    print_header("1️⃣  SYNCHRONOUS REPLICATION")
    print("""
    Leader waits for ALL followers to acknowledge before returning success.
    Guaranteed: data exists on ALL nodes when client gets success.
    Problem: ONE slow follower blocks EVERYTHING.
    """)

    followers = [
        FollowerNode("FOLLOWER-1", network_delay_ms=10),   # Fast
        FollowerNode("FOLLOWER-2", network_delay_ms=20),   # Medium
        FollowerNode("FOLLOWER-3", network_delay_ms=100),  # Slow!
    ]

    cluster = ReplicationCluster(ReplicationMode.SYNCHRONOUS, followers)

    print("  Writing 5 records synchronously:\n")
    total_time = 0.0
    for i in range(5):
        result = cluster.write({"id": i, "name": f"User_{i}"})
        ack_details = ", ".join(
            f"{a['follower']}={a['delay_ms']:.0f}ms" for a in result["acks"]
        )
        print(f"  Write {i}: {result['total_ms']:6.1f}ms total | "
              f"Nodes with data: {result['nodes_with_data']}/4 | "
              f"ACKs: [{ack_details}]")
        total_time += result['total_ms']

    avg_time = total_time / 5
    print(f"\n  ⏱️  Average write latency: {avg_time:.1f}ms")
    print(f"  ✅ Data safety: ALL nodes have ALL data")

    # Demo: one slow follower blocks everything
    print_section("💥 What happens when a follower is slow/down?")

    followers[2].go_down()  # FOLLOWER-3 goes down
    print("  FOLLOWER-3 is DOWN!")

    result = cluster.write({"id": 99, "name": "User_99"})
    failed_acks = [a for a in result["acks"] if not a["success"]]
    print(f"\n  Write attempt: {'SUCCESS ✅' if result['success'] else 'FAILED ❌'}")
    print(f"  Time: {result['total_ms']:.1f}ms")
    if failed_acks:
        print(f"  Failed follower: {failed_acks[0]['follower']}")
    print(f"\n  ❌ ONE slow/dead follower blocks ALL writes!")
    print(f"     This is why fully synchronous is rarely used in production.")

    followers[2].come_back()


def demo_2_asynchronous():
    """
    Demo 2: Asynchronous replication — fast but risky.

    DDIA: "If the leader fails and is not recoverable, any writes that
    have not yet been replicated to followers are lost."
    """
    print_header("2️⃣  ASYNCHRONOUS REPLICATION")
    print("""
    Leader returns success IMMEDIATELY — doesn't wait for followers.
    Fast writes, but data only exists on ONE node when client gets success.
    Risk: If leader crashes, unreplicated writes are LOST.
    """)

    followers = [
        FollowerNode("FOLLOWER-1", network_delay_ms=10),
        FollowerNode("FOLLOWER-2", network_delay_ms=20),
        FollowerNode("FOLLOWER-3", network_delay_ms=100),
    ]

    cluster = ReplicationCluster(ReplicationMode.ASYNCHRONOUS, followers)

    print("  Writing 5 records asynchronously:\n")
    total_time = 0.0
    for i in range(5):
        result = cluster.write({"id": i, "name": f"User_{i}"})
        print(f"  Write {i}: {result['total_ms']:6.1f}ms total | "
              f"Nodes with data: {result['nodes_with_data']}/4 (at return time) | "
              f"Followers: catching up in background...")
        total_time += result['total_ms']

    avg_time = total_time / 5
    print(f"\n  ⏱️  Average write latency: {avg_time:.1f}ms  ← MUCH FASTER!")
    print(f"  ⚠️  Data safety: Only LEADER has data at return time")

    # Wait for background replication
    time.sleep(0.2)
    print(f"\n  After 200ms: Followers have caught up (background)")

    # Demo: data loss scenario
    print_section("💀 DATA LOSS SCENARIO: Leader crashes after write")

    crash_cluster = ReplicationCluster(
        ReplicationMode.ASYNCHRONOUS,
        [FollowerNode(f"F-{i}", network_delay_ms=50) for i in range(3)]
    )

    # Write some data
    for i in range(5):
        crash_cluster.write({"id": i, "name": f"User_{i}"})

    # Simulate more writes that haven't replicated yet
    print("\n  Leader accepts 3 more writes...")
    crash_cluster.leader_storage[6] = {"id": 6, "name": "Critical_User_6"}
    crash_cluster.leader_storage[7] = {"id": 7, "name": "Critical_User_7"}
    crash_cluster.leader_storage[8] = {"id": 8, "name": "Critical_User_8"}
    print(f"  Leader has {len(crash_cluster.leader_storage)} writes")

    # Check follower state
    time.sleep(0.1)
    for f in crash_cluster.followers:
        print(f"  {f.name} has {len(f.storage)} writes")

    print(f"""
  💀 Leader CRASHES! Unreplicated writes 6, 7, 8 are LOST!
     - Client was told writes 6, 7, 8 succeeded
     - But they only existed on the leader
     - Leader is gone → data is GONE

  ⚠️  This is the fundamental risk of async replication!
     Most databases use async by default for performance.
    """)


def demo_3_semi_synchronous():
    """
    Demo 3: Semi-synchronous — the production sweet spot.

    DDIA: "Often, leader-based replication is configured to be completely
    asynchronous... However, one follower is synchronous, and the others
    are asynchronous."
    """
    print_header("3️⃣  SEMI-SYNCHRONOUS REPLICATION ⭐")
    print("""
    Leader waits for AT LEAST ONE follower to ACK.
    Other followers catch up asynchronously.

    Sweet spot: data on 2 nodes (safety) without waiting for ALL (speed).
    """)

    followers = [
        FollowerNode("SYNC-F1", network_delay_ms=10),    # Sync follower
        FollowerNode("ASYNC-F2", network_delay_ms=50),   # Async
        FollowerNode("ASYNC-F3", network_delay_ms=100),  # Async
    ]

    cluster = ReplicationCluster(
        ReplicationMode.SEMI_SYNCHRONOUS,
        followers,
        sync_follower_count=1  # Wait for 1 follower
    )

    print("  Writing 5 records (semi-synchronous, 1 sync follower):\n")
    total_time = 0.0
    for i in range(5):
        result = cluster.write({"id": i, "name": f"User_{i}"})
        sync_acks = [a for a in result["acks"] if a.get("type") == "SYNC"]
        async_acks = [a for a in result["acks"] if a.get("type") == "ASYNC"]

        sync_detail = ", ".join(
            f"{a['follower']}={a['delay_ms']:.0f}ms" for a in sync_acks
        )
        async_detail = ", ".join(f"{a['follower']}" for a in async_acks)

        print(f"  Write {i}: {result['total_ms']:6.1f}ms | "
              f"Guaranteed on {result['nodes_with_data']} nodes | "
              f"Sync:[{sync_detail}] Async:[{async_detail}]")
        total_time += result['total_ms']

    avg_time = total_time / 5
    print(f"\n  ⏱️  Average write latency: {avg_time:.1f}ms")
    print(f"  ✅ Data guaranteed on 2 nodes (leader + 1 sync follower)")
    print(f"  ✅ Fast: don't wait for slow async followers")

    # What happens if the sync follower goes down?
    print_section("🔄 Sync follower goes down → promote another")

    followers[0].go_down()  # Sync follower dies
    print("  SYNC-F1 is DOWN!")
    print("  In real systems: ASYNC-F2 is promoted to be the new sync follower")
    print("  → Data guarantee maintained on 2 nodes at all times!")

    followers[0].come_back()


def demo_4_comparison():
    """Side-by-side timing comparison of all three modes."""
    print_header("📊 SPEED vs SAFETY COMPARISON")

    modes = [
        ("SYNCHRONOUS", ReplicationMode.SYNCHRONOUS),
        ("SEMI-SYNC", ReplicationMode.SEMI_SYNCHRONOUS),
        ("ASYNCHRONOUS", ReplicationMode.ASYNCHRONOUS),
    ]

    num_writes = 20

    print(f"\n  Running {num_writes} writes in each mode...\n")
    print(f"  {'Mode':<20} {'Avg Latency':<15} {'Data Safety':<30} {'Availability'}")
    print(f"  {'─'*85}")

    for mode_name, mode in modes:
        followers = [
            FollowerNode(f"F-{i}", network_delay_ms=random.uniform(5, 30))
            for i in range(3)
        ]
        cluster = ReplicationCluster(mode, followers, sync_follower_count=1)

        total_ms = 0.0
        for i in range(num_writes):
            result = cluster.write({"id": i, "name": f"User_{i}"})
            total_ms += result['total_ms']

        avg_ms = total_ms / num_writes

        if mode == ReplicationMode.SYNCHRONOUS:
            safety = "ALL nodes ✅✅✅"
            availability = "❌ Blocked by slowest"
        elif mode == ReplicationMode.ASYNCHRONOUS:
            safety = "Leader ONLY ⚠️"
            availability = "✅ Always available"
        else:
            safety = "Leader + 1 follower ✅✅"
            availability = "✅ Mostly available"

        print(f"  {mode_name:<20} {avg_ms:>8.1f}ms      {safety:<30} {availability}")

    print("""
  ┌────────────────────────────────────────────────────────────────────┐
  │                    THE REPLICATION TRADE-OFF                       │
  │                                                                    │
  │   Synchronous ◄──────────────────────────────► Asynchronous       │
  │   (Safer)                                       (Faster)           │
  │                                                                    │
  │   • All nodes have data         • Only leader has data             │
  │   • Slow (wait for all)         • Fast (return immediately)        │
  │   • One failure blocks writes   • Failures don't block             │
  │                                                                    │
  │              Semi-synchronous: sweet spot ⭐                       │
  │              • 2 nodes have data (safe enough)                     │
  │              • Fast (only wait for 1 follower)                     │
  │              • Available (only blocked by 1 follower)              │
  └────────────────────────────────────────────────────────────────────┘
    """)


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 80)
    print("  EXERCISE 3: SYNCHRONOUS vs ASYNCHRONOUS REPLICATION")
    print("  DDIA Chapter 5: 'Synchronous Versus Asynchronous Replication'")
    print("=" * 80)
    print("""
  This exercise shows you the REAL performance difference between
  sync, async, and semi-sync replication — and what you gain/lose.
    """)

    demo_1_synchronous()
    demo_2_asynchronous()
    demo_3_semi_synchronous()
    demo_4_comparison()

    print("\n" + "=" * 80)
    print("  EXERCISE 3 COMPLETE ✅")
    print("=" * 80)
    print("""
  Key Takeaways:

  1. ⏱️  SYNCHRONOUS: Safe but slow — one dead follower blocks all writes
  2. 🚀 ASYNCHRONOUS: Fast but risky — data loss if leader crashes
  3. ⭐ SEMI-SYNC: Sweet spot — data on 2 nodes, only wait for 1 follower

  Production configurations:
    • PostgreSQL: synchronous_commit = on + synchronous_standby_names
    • MySQL: Semi-synchronous replication plugin (rpl_semi_sync)
    • MongoDB: write concern {"w": "majority"} (similar to semi-sync)

  Next: Run 04_failover.py to see what happens when the leader DIES
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
