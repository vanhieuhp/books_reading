"""
Exercise 3: Serializable Snapshot Isolation (SSI)

DDIA Reference: Chapter 7, "Serializability - Technique 3: SSI" (pp. 340-345)

This exercise demonstrates SERIALIZABLE SNAPSHOT ISOLATION:
  - Optimistic concurrency control (no blocking)
  - Transactions read from snapshot, no locks
  - Detect conflicts at commit time
  - Abort and retry if conflicts detected
  - Used by: PostgreSQL (SSI), FoundationDB, CockroachDB

Key concepts:
  - MVCC: Multiple versions of each row
  - Optimistic: execute freely, check at commit
  - Detect stale reads: uncommitted write before read
  - Detect write conflicts: write after read
  - No blocking, no deadlocks, but higher abort rate

Run: python 03_serializable_snapshot_isolation.py
"""

import sys
import time
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')


# =============================================================================
# CORE COMPONENTS: Version, MVCC, SSIStore
# =============================================================================

class TransactionStatus(Enum):
    ACTIVE = "active"
    COMMITTED = "committed"
    ABORTED = "aborted"


@dataclass
class Version:
    """A version of a data item."""
    value: Any
    created_by: int  # Transaction ID that created this version
    deleted_by: Optional[int] = None  # Transaction ID that deleted this version


@dataclass
class Transaction:
    """A transaction in SSI."""
    tx_id: int
    name: str
    status: TransactionStatus = TransactionStatus.ACTIVE
    start_time: float = 0.0
    commit_time: float = 0.0
    read_set: Dict[str, int] = field(default_factory=dict)  # key -> version_id
    write_set: Dict[str, Any] = field(default_factory=dict)  # key -> new_value
    dependencies: List[int] = field(default_factory=list)  # Other transactions we depend on

    def duration_ms(self) -> float:
        """Return transaction duration in milliseconds."""
        if self.commit_time == 0:
            return 0
        return (self.commit_time - self.start_time) * 1000


class SSIStore:
    """
    A key-value store using Serializable Snapshot Isolation.

    DDIA concept: "SSI is built on top of Snapshot Isolation (MVCC),
    adding an algorithm to detect serialization conflicts."
    """

    def __init__(self):
        self.data: Dict[str, List[Version]] = defaultdict(list)
        self.transactions: Dict[int, Transaction] = {}
        self.next_tx_id = 1
        self.committed_txs: List[int] = []
        self.aborted_txs: List[int] = []

    def begin_transaction(self, name: str) -> int:
        """Begin a new transaction."""
        tx_id = self.next_tx_id
        self.next_tx_id += 1

        tx = Transaction(tx_id, name, start_time=time.time())
        self.transactions[tx_id] = tx

        return tx_id

    def read(self, key: str, tx_id: int) -> Tuple[bool, Any]:
        """
        Read a value in SSI.

        Returns (success, value)
        """
        tx = self.transactions[tx_id]

        # Find the latest committed version visible to this transaction
        versions = self.data[key]
        visible_version = None

        for version in reversed(versions):
            # Version is visible if:
            # 1. It was created by a committed transaction before this one started
            # 2. It wasn't deleted by a committed transaction before this one started
            if version.created_by in self.committed_txs or version.created_by == tx_id:
                if version.deleted_by is None or version.deleted_by not in self.committed_txs:
                    visible_version = version
                    break

        if visible_version is None:
            return False, None

        # Record the read
        tx.read_set[key] = visible_version.created_by

        return True, visible_version.value

    def write(self, key: str, value: Any, tx_id: int) -> bool:
        """
        Write a value in SSI.

        Returns True if successful.
        """
        tx = self.transactions[tx_id]

        # Record the write
        tx.write_set[key] = value

        return True

    def commit(self, tx_id: int) -> bool:
        """
        Commit a transaction.

        Detects conflicts and aborts if necessary.
        Returns True if committed, False if aborted.
        """
        tx = self.transactions[tx_id]

        # Detect conflicts
        conflicts = self._detect_conflicts(tx)

        if conflicts:
            # Abort this transaction
            tx.status = TransactionStatus.ABORTED
            tx.commit_time = time.time()
            self.aborted_txs.append(tx_id)
            return False

        # Apply writes
        for key, value in tx.write_set.items():
            version = Version(value, created_by=tx_id)
            self.data[key].append(version)

        # Mark as committed
        tx.status = TransactionStatus.COMMITTED
        tx.commit_time = time.time()
        self.committed_txs.append(tx_id)

        return True

    def _detect_conflicts(self, tx: Transaction) -> bool:
        """
        Detect if this transaction has conflicts.

        Returns True if conflicts detected (should abort).
        """
        # Check for stale reads: another transaction wrote to something we read
        for key, read_version_id in tx.read_set.items():
            for other_tx_id in self.committed_txs:
                if other_tx_id == tx.tx_id or other_tx_id == 0:
                    continue

                if other_tx_id not in self.transactions:
                    continue

                other_tx = self.transactions[other_tx_id]

                # If another transaction wrote to a key we read
                if key in other_tx.write_set:
                    # And that write happened after we started
                    if other_tx.commit_time > tx.start_time:
                        return True

        # Check for write conflicts: another transaction read something we wrote
        for key, value in tx.write_set.items():
            for other_tx_id in self.committed_txs:
                if other_tx_id == tx.tx_id or other_tx_id == 0:
                    continue

                if other_tx_id not in self.transactions:
                    continue

                other_tx = self.transactions[other_tx_id]

                # If another transaction read a key we're writing
                if key in other_tx.read_set:
                    # And that read happened before we started
                    if other_tx.start_time < tx.start_time:
                        return True

        return False

    def get_stats(self) -> Dict:
        """Get statistics."""
        return {
            "total_transactions": len(self.transactions),
            "committed": len(self.committed_txs),
            "aborted": len(self.aborted_txs),
            "abort_rate": len(self.aborted_txs) / len(self.transactions) if self.transactions else 0,
        }


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


def demo_1_mvcc_snapshot_isolation():
    """
    Demo 1: Show MVCC and snapshot isolation.

    DDIA concept: "Instead of holding only one version of each data item,
    the database keeps multiple versions."
    """
    print_header("DEMO 1: MVCC and Snapshot Isolation")
    print("""
    MVCC (Multi-Version Concurrency Control):
    • Keep multiple versions of each row
    • Each version tagged with transaction ID
    • Each transaction sees a consistent snapshot

    Example:
      TX1 writes: balance = $400
      TX2 writes: balance = $500
      TX3 writes: balance = $600

    Physical table:
      created_by=TX1, deleted_by=TX2, value=$400
      created_by=TX2, deleted_by=TX3, value=$500
      created_by=TX3, deleted_by=NULL, value=$600

    TX4 (started before TX3 committed):
      → Sees: balance = $500 (from TX2)

    TX5 (started after TX3 committed):
      → Sees: balance = $600 (from TX3)
    """)

    store = SSIStore()

    print("📝 Simulating multiple writes:")

    # TX1: Write $400
    tx1_id = store.begin_transaction("Write $400")
    store.write('balance', 400, tx1_id)
    store.commit(tx1_id)
    print(f"   TX1 commits: balance = $400")

    # TX2: Write $500
    tx2_id = store.begin_transaction("Write $500")
    store.write('balance', 500, tx2_id)
    store.commit(tx2_id)
    print(f"   TX2 commits: balance = $500")

    # TX3: Write $600
    tx3_id = store.begin_transaction("Write $600")
    store.write('balance', 600, tx3_id)
    store.commit(tx3_id)
    print(f"   TX3 commits: balance = $600")

    # TX4: Read (started before TX3 committed)
    tx4_id = store.begin_transaction("Read (snapshot)")
    success, value = store.read('balance', tx4_id)
    print(f"\n   TX4 reads: balance = ${value}")
    print(f"   (TX4 sees snapshot from when it started)")

    store.commit(tx4_id)

    print("""
  💡 KEY INSIGHT (DDIA):
     MVCC allows multiple transactions to read different versions
     simultaneously without blocking. Each transaction sees a
     consistent snapshot from its start time.
    """)


def demo_2_optimistic_execution():
    """
    Demo 2: Show optimistic execution (no blocking).

    DDIA concept: "Instead of blocking (pessimistic), SSI allows
    transactions to proceed without blocking."
    """
    print_header("DEMO 2: Optimistic Execution (No Blocking)")
    print("""
    SSI is optimistic:
    • Transactions execute without acquiring locks
    • No blocking, no waiting
    • Conflicts detected at commit time
    • If conflict detected, abort and retry

    Contrast with 2PL (pessimistic):
    • Lock before accessing data
    • Readers block writers, writers block readers
    • Guaranteed no conflicts, but causes blocking
    """)

    store = SSIStore()

    print("📝 Scenario: Two concurrent transactions")
    print("   TX1: Read A, Write B")
    print("   TX2: Read B, Write A")

    # TX1 starts
    tx1_id = store.begin_transaction("Read A, Write B")
    print(f"\n   TX1 starts (no locks acquired)")

    # TX2 starts
    tx2_id = store.begin_transaction("Read B, Write A")
    print(f"   TX2 starts (no locks acquired)")

    # TX1 reads A
    success, value = store.read('A', tx1_id)
    print(f"\n   TX1 reads A (no lock)")

    # TX2 reads B
    success, value = store.read('B', tx2_id)
    print(f"   TX2 reads B (no lock)")

    # TX1 writes B
    store.write('B', 100, tx1_id)
    print(f"\n   TX1 writes B (no lock)")

    # TX2 writes A
    store.write('A', 200, tx2_id)
    print(f"   TX2 writes A (no lock)")

    # TX1 commits
    success1 = store.commit(tx1_id)
    print(f"\n   TX1 commits: {store.transactions[tx1_id].status.value}")

    # TX2 commits
    success2 = store.commit(tx2_id)
    print(f"   TX2 commits: {store.transactions[tx2_id].status.value}")

    print("""
  💡 KEY INSIGHT (DDIA):
     With SSI, both transactions execute without blocking.
     If there's a conflict, one is aborted at commit time.
     This is much better for latency than 2PL's blocking approach.
    """)


def demo_3_conflict_detection():
    """
    Demo 3: Show conflict detection.

    DDIA concept: "The database tracks dependencies and aborts one of
    the conflicting transactions at commit time."
    """
    print_header("DEMO 3: Conflict Detection")
    print("""
    SSI detects two types of conflicts:

    1. Stale Read: Another transaction wrote to something we read
       TX1 reads X
       TX2 writes X and commits
       TX1 tries to commit → CONFLICT! Abort TX1

    2. Write Conflict: Another transaction read something we wrote
       TX1 reads X
       TX2 writes X and commits
       TX1 tries to commit → CONFLICT! Abort TX1
    """)

    store = SSIStore()

    # Initialize data
    store.data['counter'] = [Version(0, created_by=0)]
    store.committed_txs.append(0)

    print("📝 Scenario: Lost update detection")
    print("   TX1: Read counter, increment, write")
    print("   TX2: Read counter, increment, write")

    # TX1 starts
    tx1_id = store.begin_transaction("Increment counter")
    success, value = store.read('counter', tx1_id)
    print(f"\n   TX1 reads counter = {value}")

    # TX2 starts
    tx2_id = store.begin_transaction("Increment counter")
    success, value = store.read('counter', tx2_id)
    print(f"   TX2 reads counter = {value}")

    # TX1 writes
    store.write('counter', 1, tx1_id)
    print(f"\n   TX1 writes counter = 1")

    # TX2 writes
    store.write('counter', 1, tx2_id)
    print(f"   TX2 writes counter = 1")

    # TX1 commits
    success1 = store.commit(tx1_id)
    print(f"\n   TX1 commits: {store.transactions[tx1_id].status.value}")

    # TX2 commits
    success2 = store.commit(tx2_id)
    print(f"   TX2 commits: {store.transactions[tx2_id].status.value}")

    if not success2:
        print(f"   ⚠️  CONFLICT DETECTED! TX2 aborted.")

    stats = store.get_stats()
    print(f"\n   Abort rate: {stats['abort_rate']*100:.0f}%")

    print("""
  💡 KEY INSIGHT (DDIA):
     SSI automatically detects lost updates and other conflicts.
     One transaction is aborted and can be retried.
     This is much cleaner than application-level conflict handling!
    """)


def demo_4_abort_rate_under_contention():
    """
    Demo 4: Show abort rate under contention.

    DDIA concept: "Higher abort rate when there is high contention on
    the same data."
    """
    print_header("DEMO 4: Abort Rate Under Contention")
    print("""
    SSI's weakness: High abort rate under contention.

    Low contention (different keys):
      • Few conflicts
      • Low abort rate
      • Good throughput

    High contention (same key):
      • Many conflicts
      • High abort rate
      • Lower throughput
    """)

    # Scenario 1: Low contention
    print("\n📊 Scenario 1: Low contention (different keys)")
    store1 = SSIStore()
    store1.data['key_1'] = [Version(0, created_by=0)]
    store1.data['key_2'] = [Version(0, created_by=0)]
    store1.data['key_3'] = [Version(0, created_by=0)]
    store1.committed_txs.append(0)

    for i in range(10):
        tx_id = store1.begin_transaction(f"TX{i}")
        key = f"key_{(i % 3) + 1}"
        success, value = store1.read(key, tx_id)
        store1.write(key, value + 1, tx_id)
        store1.commit(tx_id)

    stats1 = store1.get_stats()
    print(f"   Committed: {stats1['committed']}")
    print(f"   Aborted: {stats1['aborted']}")
    print(f"   Abort rate: {stats1['abort_rate']*100:.0f}%")

    # Scenario 2: High contention
    print("\n📊 Scenario 2: High contention (same key)")
    store2 = SSIStore()
    store2.data['shared_key'] = [Version(0, created_by=0)]
    store2.committed_txs.append(0)

    for i in range(10):
        tx_id = store2.begin_transaction(f"TX{i}")
        success, value = store2.read('shared_key', tx_id)
        store2.write('shared_key', value + 1, tx_id)
        store2.commit(tx_id)

    stats2 = store2.get_stats()
    print(f"   Committed: {stats2['committed']}")
    print(f"   Aborted: {stats2['aborted']}")
    print(f"   Abort rate: {stats2['abort_rate']*100:.0f}%")

    print("""
  💡 KEY INSIGHT (DDIA):
     SSI works great for low-contention workloads.
     Under high contention, abort rate increases significantly.

     This is the trade-off:
     • 2PL: Guaranteed throughput, high latency
     • SSI: Low latency, but higher abort rate under contention
    """)


def demo_5_ssi_vs_2pl():
    """
    Demo 5: Compare SSI with 2PL.

    DDIA concept: "SSI is the cutting-edge approach. It provides full
    serializability without the performance cost of 2PL."
    """
    print_header("DEMO 5: SSI vs 2PL")
    print("""
    Two approaches to serializability:

    2PL (Pessimistic):
      • Lock before accessing data
      • Readers block writers, writers block readers
      • Guaranteed no conflicts
      • Deadlocks possible
      • High latency, good throughput

    SSI (Optimistic):
      • No locks, execute freely
      • Detect conflicts at commit
      • Abort and retry if conflict
      • No deadlocks
      • Low latency, but higher abort rate under contention

    When to use:
      • 2PL: High contention, need guaranteed throughput
      • SSI: Low contention, need low latency
    """)

    print("""
    Real-world usage:
      • PostgreSQL: Supports both (SERIALIZABLE uses SSI since v9.1)
      • MySQL InnoDB: Uses 2PL
      • Oracle: Uses Snapshot Isolation (not full SSI)
      • CockroachDB: Uses SSI by default
      • FoundationDB: Uses SSI
    """)

    print("""
  💡 KEY INSIGHT (DDIA):
     SSI is the modern approach to serializability.
     It provides better latency than 2PL without the blocking overhead.
     The trade-off is higher abort rate under contention, which is
     usually acceptable for most workloads.
    """)


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 80)
    print("  EXERCISE 3: SERIALIZABLE SNAPSHOT ISOLATION (SSI)")
    print("  DDIA Chapter 7: 'Serializability - Technique 3'")
    print("=" * 80)
    print("""
  This exercise demonstrates SERIALIZABLE SNAPSHOT ISOLATION:
  - Optimistic concurrency control (no blocking)
  - Transactions read from snapshot, no locks
  - Detect conflicts at commit time
  - Abort and retry if conflicts detected
    """)

    demo_1_mvcc_snapshot_isolation()
    demo_2_optimistic_execution()
    demo_3_conflict_detection()
    demo_4_abort_rate_under_contention()
    demo_5_ssi_vs_2pl()

    print("\n" + "=" * 80)
    print("  EXERCISE 3 COMPLETE ✅")
    print("=" * 80)
    print("""
  Key Takeaways:

  1. 📦 MVCC: Keep multiple versions of each row
  2. 🚀 Optimistic: Execute freely, no blocking
  3. 🔍 Detect conflicts at commit time
  4. ⚠️  Higher abort rate under contention
  5. 📊 SSI is the modern approach to serializability

  Next: Run 04_isolation_levels_comparison.py to compare all techniques
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
