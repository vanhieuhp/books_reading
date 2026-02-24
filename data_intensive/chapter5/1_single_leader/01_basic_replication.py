"""
Exercise 1: Single-Leader Replication — Basic Architecture

DDIA Reference: Chapter 5, "Leaders and Followers" (pp. 152-153)

This exercise simulates the fundamental single-leader replication pattern:
  - One LEADER node accepts all writes
  - Multiple FOLLOWER nodes replicate changes
  - Clients can read from any node (but followers may be stale)

Key concepts:
  - Write path: Client → Leader → Replication Log → Followers
  - Read path: Client → Leader (consistent) or Follower (may be stale)
  - Replication is asynchronous by default
  - Followers are read-only

Run: python 01_basic_replication.py
"""

import sys
import time
import random
import threading
from collections import OrderedDict
from typing import Dict, List, Optional, Any

# Fix Windows terminal encoding for Unicode output
sys.stdout.reconfigure(encoding='utf-8')


# =============================================================================
# CORE COMPONENTS: Node, ReplicationLog, Leader, Follower
# =============================================================================

class ReplicationLogEntry:
    """A single entry in the replication log (like a WAL entry or binlog event)."""

    def __init__(self, lsn: int, operation: str, table: str, data: Dict[str, Any], timestamp: float):
        self.lsn = lsn              # Log Sequence Number (ordering)
        self.operation = operation    # INSERT, UPDATE, DELETE
        self.table = table
        self.data = data
        self.timestamp = timestamp

    def __repr__(self):
        return f"[LSN={self.lsn}] {self.operation} {self.table} {self.data}"


class ReplicationLog:
    """
    The replication log — the central mechanism for data flow.

    DDIA insight: "The leader writes the data to its local storage AND sends
    the data change to all of its followers as part of a replication log
    or change stream."
    """

    def __init__(self):
        self.entries: List[ReplicationLogEntry] = []
        self._next_lsn = 1

    def append(self, operation: str, table: str, data: Dict[str, Any]) -> ReplicationLogEntry:
        entry = ReplicationLogEntry(
            lsn=self._next_lsn,
            operation=operation,
            table=table,
            data=data,
            timestamp=time.time()
        )
        self.entries.append(entry)
        self._next_lsn += 1
        return entry

    def get_entries_after(self, lsn: int) -> List[ReplicationLogEntry]:
        """Get all entries after a given LSN (for follower catch-up)."""
        return [e for e in self.entries if e.lsn > lsn]

    @property
    def latest_lsn(self) -> int:
        return self.entries[-1].lsn if self.entries else 0


class Node:
    """Base class for a database node (leader or follower)."""

    def __init__(self, name: str):
        self.name = name
        self.storage: Dict[str, Dict[int, Dict]] = {}  # table -> {id: row}
        self.replication_position = 0  # Last applied LSN

    def _apply_to_storage(self, entry: ReplicationLogEntry):
        """Apply a replication log entry to local storage."""
        table = entry.table
        if table not in self.storage:
            self.storage[table] = {}

        if entry.operation == "INSERT":
            row_id = entry.data.get("id")
            self.storage[table][row_id] = entry.data.copy()
        elif entry.operation == "UPDATE":
            row_id = entry.data.get("id")
            if row_id in self.storage[table]:
                self.storage[table][row_id].update(entry.data)
        elif entry.operation == "DELETE":
            row_id = entry.data.get("id")
            self.storage[table].pop(row_id, None)

        self.replication_position = entry.lsn

    def read(self, table: str, row_id: int) -> Optional[Dict]:
        """Read a row from local storage."""
        return self.storage.get(table, {}).get(row_id)

    def read_all(self, table: str) -> Dict[int, Dict]:
        """Read all rows from a table."""
        return self.storage.get(table, {}).copy()

    def row_count(self, table: str) -> int:
        return len(self.storage.get(table, {}))


class Leader(Node):
    """
    The LEADER node — accepts all writes.

    DDIA: "One of the replicas is designated the leader. When clients want
    to write to the database, they must send their requests to the leader,
    which first writes the new data to its local storage."
    """

    def __init__(self, name: str = "LEADER"):
        super().__init__(name)
        self.replication_log = ReplicationLog()
        self.followers: List['Follower'] = []

    def register_follower(self, follower: 'Follower'):
        self.followers.append(follower)

    def write(self, operation: str, table: str, data: Dict[str, Any]) -> ReplicationLogEntry:
        """
        Process a write request.

        Write path:
          1. Validate the query
          2. Apply to local storage (durability)
          3. Append to replication log
          4. Send to followers (async)
          5. Return success to client
        """
        # Step 1: Append to replication log
        entry = self.replication_log.append(operation, table, data)

        # Step 2: Apply to local storage
        self._apply_to_storage(entry)

        # Step 3: Send to followers (asynchronously — simulated with delay)
        self._replicate_to_followers(entry)

        return entry

    def _replicate_to_followers(self, entry: ReplicationLogEntry):
        """Send log entry to all followers (simulating async replication)."""
        for follower in self.followers:
            # Simulate network delay (async replication)
            delay = random.uniform(0.01, 0.05)  # 10-50ms
            follower.receive_log_entry(entry, delay)


class Follower(Node):
    """
    A FOLLOWER node — read-only replica.

    DDIA: "The other replicas are known as followers. Whenever the leader
    writes new data to its local storage, it also sends the data change
    to each of its followers."
    """

    def __init__(self, name: str):
        super().__init__(name)
        self._replication_lag_ms = 0

    def receive_log_entry(self, entry: ReplicationLogEntry, network_delay: float):
        """
        Receive and apply a log entry from the leader.

        In real systems, this happens asynchronously over the network.
        """
        # Simulate network delay
        time.sleep(network_delay)
        self._replication_lag_ms = network_delay * 1000

        # Apply to local storage
        self._apply_to_storage(entry)

    @property
    def lag_ms(self) -> float:
        return self._replication_lag_ms


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


def demo_1_basic_write_flow():
    """
    Demo 1: Show the basic write flow through the system.

    DDIA concept: "The leader writes data to its local storage and sends
    the data change to all of its followers."
    """
    print_header("DEMO 1: Basic Write Flow")
    print("""
    This demonstrates how a single write flows through the system:
    Client → Leader → Replication Log → Followers
    """)

    # Set up the cluster
    leader = Leader("LEADER")
    followers = [Follower(f"FOLLOWER-{i+1}") for i in range(3)]
    for f in followers:
        leader.register_follower(f)

    print("📦 Cluster setup:")
    print(f"   Leader: {leader.name}")
    print(f"   Followers: {', '.join(f.name for f in followers)}")

    # Perform writes
    writes = [
        ("INSERT", "users", {"id": 1, "name": "Alice", "email": "alice@example.com"}),
        ("INSERT", "users", {"id": 2, "name": "Bob", "email": "bob@example.com"}),
        ("UPDATE", "users", {"id": 1, "name": "Alice", "email": "alice@newdomain.com"}),
        ("INSERT", "users", {"id": 3, "name": "Charlie", "email": "charlie@example.com"}),
        ("DELETE", "users", {"id": 2}),
    ]

    for op, table, data in writes:
        print(f"\n{'─' * 60}")
        print(f"  📝 Client sends: {op} {table} {data}")
        print(f"{'─' * 60}")

        entry = leader.write(op, table, data)

        print(f"  [{leader.name:>10}] Applied to local storage ✅ (LSN={entry.lsn})")

        for f in followers:
            lag = f.lag_ms
            lag_indicator = f"(lag: {lag:.0f}ms)" if lag > 0 else ""
            print(f"  [{f.name:>10}] Received & applied LSN={entry.lsn} ✅ {lag_indicator}")

    # Verify consistency
    print_section("📊 Final State — Consistency Check")

    print(f"\n  {'Node':<15} {'Row Count':<12} {'Repl. Position':<18} {'Data'}")
    print(f"  {'─'*70}")

    all_nodes = [leader] + followers
    leader_data = leader.read_all("users")

    for node in all_nodes:
        node_data = node.read_all("users")
        consistent = "✅" if node_data == leader_data else "❌"
        data_summary = {k: v.get("name", "?") for k, v in node_data.items()}
        print(f"  {node.name:<15} {node.row_count('users'):<12} LSN={node.replication_position:<14} {data_summary} {consistent}")

    all_consistent = all(n.read_all("users") == leader_data for n in followers)
    print(f"\n  🔍 All nodes consistent: {'YES ✅' if all_consistent else 'NO ❌'}")


def demo_2_read_from_different_nodes():
    """
    Demo 2: Show that reads from different nodes may return different data.

    DDIA concept: Reading from a follower may return stale data
    because of replication lag.
    """
    print_header("DEMO 2: Reading from Different Nodes")
    print("""
    This shows that reading from the leader is always consistent,
    but reading from followers may return stale data.
    """)

    leader = Leader("LEADER")
    followers = [Follower(f"FOLLOWER-{i+1}") for i in range(3)]
    for f in followers:
        leader.register_follower(f)

    # Insert some data
    leader.write("INSERT", "users", {"id": 1, "name": "Alice", "age": 25})
    leader.write("INSERT", "users", {"id": 2, "name": "Bob", "age": 30})

    print("  ✅ Data inserted: Alice (age=25), Bob (age=30)")

    # UPDATE on leader — followers will get it with delay
    print(f"\n  📝 Client updates: Alice age → 26")
    leader.write("UPDATE", "users", {"id": 1, "name": "Alice", "age": 26})

    # Read from different nodes
    print(f"\n  📖 Reading Alice's data from different nodes:\n")

    alice_from_leader = leader.read("users", 1)
    print(f"  [{leader.name:>10}] Alice = {alice_from_leader}  ← Always consistent ✅")

    for f in followers:
        alice_from_follower = f.read("users", 1)
        is_stale = alice_from_follower != alice_from_leader
        status = "⚠️  STALE!" if is_stale else "✅ Up-to-date"
        print(f"  [{f.name:>10}] Alice = {alice_from_follower}  ← {status}")

    print("""
  💡 KEY INSIGHT (DDIA):
     Reading from the LEADER is always consistent.
     Reading from a FOLLOWER may return stale data.

     This is the trade-off:
       • Read from leader  → consistent, but leader is bottleneck
       • Read from follower → scales reads, but may be stale
    """)


def demo_3_write_scaling_limitation():
    """
    Demo 3: Show that single-leader has a write bottleneck.

    DDIA concept: "All writes must go through the leader, which means
    the leader is a bottleneck for write throughput."
    """
    print_header("DEMO 3: Write Bottleneck")
    print("""
    Single-leader replication scales READS (add more followers)
    but NOT WRITES (all writes go through one leader).
    """)

    leader = Leader("LEADER")
    follower_counts = [1, 3, 5, 10]

    for count in follower_counts:
        # Reset
        leader = Leader("LEADER")
        followers = [Follower(f"FOLLOWER-{i+1}") for i in range(count)]
        for f in followers:
            leader.register_follower(f)

        # Measure write throughput
        num_writes = 100
        start = time.time()
        for i in range(num_writes):
            leader.write("INSERT", "users", {"id": i, "name": f"User_{i}"})
        elapsed = time.time() - start

        writes_per_sec = num_writes / elapsed if elapsed > 0 else float('inf')
        print(f"  {count:2d} followers → {num_writes} writes in {elapsed:.3f}s "
              f"({writes_per_sec:.0f} writes/sec)")

    print("""
  💡 KEY INSIGHT (DDIA):
     Notice how write throughput DECREASES as you add more followers!
     Each write must be replicated to every follower.

     ✅ Adding followers scales READS (more nodes to read from)
     ❌ Adding followers does NOT scale WRITES (still one leader)

     → This is why DDIA introduces multi-leader and leaderless patterns
       for write-heavy workloads.
    """)


def demo_4_setting_up_new_follower():
    """
    Demo 4: Setting up a new follower without downtime.

    DDIA concept: "Setting Up New Followers" (p. 155)
    You can't just copy data — the leader keeps writing during the copy.
    """
    print_header("DEMO 4: Setting Up a New Follower")
    print("""
    Adding a new follower to an existing cluster without downtime.
    The key challenge: the leader keeps accepting writes while the
    new follower is being set up.
    """)

    leader = Leader("LEADER")
    follower1 = Follower("FOLLOWER-1")
    leader.register_follower(follower1)

    # Write initial data
    print("  Step 0: Existing cluster with data\n")
    for i in range(5):
        leader.write("INSERT", "users", {"id": i, "name": f"User_{i}"})
    print(f"    Leader has {leader.row_count('users')} rows, LSN={leader.replication_log.latest_lsn}")

    # Step 1: Take a snapshot
    print(f"\n  Step 1: Take a consistent snapshot of the leader")
    snapshot_lsn = leader.replication_log.latest_lsn
    snapshot_data = leader.read_all("users")
    print(f"    Snapshot taken at LSN={snapshot_lsn}")
    print(f"    Snapshot contains {len(snapshot_data)} rows")

    # Step 2: While copying, leader keeps accepting writes
    print(f"\n  Step 2: Leader keeps accepting writes during copy")
    leader.write("INSERT", "users", {"id": 5, "name": "NewUser_5"})
    leader.write("INSERT", "users", {"id": 6, "name": "NewUser_6"})
    leader.write("INSERT", "users", {"id": 7, "name": "NewUser_7"})
    print(f"    Leader now has {leader.row_count('users')} rows, LSN={leader.replication_log.latest_lsn}")

    # Step 3: Copy snapshot to new follower
    print(f"\n  Step 3: Copy snapshot to new follower")
    new_follower = Follower("FOLLOWER-2")
    new_follower.storage["users"] = {k: v.copy() for k, v in snapshot_data.items()}
    new_follower.replication_position = snapshot_lsn
    print(f"    New follower has {new_follower.row_count('users')} rows, position=LSN={snapshot_lsn}")

    # Step 4: Catch up from snapshot position
    print(f"\n  Step 4: Catch up on changes since snapshot")
    missed_entries = leader.replication_log.get_entries_after(snapshot_lsn)
    print(f"    Entries to catch up: {len(missed_entries)}")
    for entry in missed_entries:
        new_follower._apply_to_storage(entry)
        print(f"    Applied: {entry}")

    # Step 5: Register and verify
    leader.register_follower(new_follower)
    print(f"\n  Step 5: New follower is ready! ✅")
    print(f"    New follower: {new_follower.row_count('users')} rows, LSN={new_follower.replication_position}")
    print(f"    Leader:       {leader.row_count('users')} rows, LSN={leader.replication_log.latest_lsn}")

    consistent = new_follower.read_all("users") == leader.read_all("users")
    print(f"\n    Consistent with leader: {'YES ✅' if consistent else 'NO ❌'}")

    print("""
  💡 KEY INSIGHT (DDIA):
     The snapshot must be associated with a known replication log position.
     Without this position, the follower wouldn't know where to start
     catching up!

     Real database tools:
       PostgreSQL: pg_basebackup (records WAL position)
       MySQL:      mysqldump --single-transaction (records binlog position)
       MongoDB:    mongodump (records oplog timestamp)
    """)


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 80)
    print("  EXERCISE 1: SINGLE-LEADER REPLICATION — BASIC ARCHITECTURE")
    print("  DDIA Chapter 5: 'Leaders and Followers'")
    print("=" * 80)
    print("""
  This exercise simulates the fundamental single-leader pattern.
  You'll see how writes flow through the system, how reads work,
  and why this architecture has inherent trade-offs.
    """)

    demo_1_basic_write_flow()
    demo_2_read_from_different_nodes()
    demo_3_write_scaling_limitation()
    demo_4_setting_up_new_follower()

    print("\n" + "=" * 80)
    print("  EXERCISE 1 COMPLETE ✅")
    print("=" * 80)
    print("""
  Key Takeaways:

  1. 📝 ALL writes go through the leader — single source of truth
  2. 📖 Reads can go to any node — but followers may be stale
  3. 📈 Adding followers scales reads but NOT writes
  4. 📸 New followers need snapshot + catch-up from known position
  5. ⏱️  Replication lag is REAL — followers always lag behind

  Next: Run 02_replication_logs.py to learn HOW data moves between nodes
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
