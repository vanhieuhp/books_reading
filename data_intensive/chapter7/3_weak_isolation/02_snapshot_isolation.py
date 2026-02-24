"""
Exercise 2: Snapshot Isolation and MVCC

DDIA Reference: Chapter 7, "Weak Isolation Levels" (pp. 237-243)

This exercise demonstrates SNAPSHOT ISOLATION:
  - Each transaction reads from a consistent snapshot
  - Prevents read skew (the limitation of Read Committed)
  - Implementation: Multi-Version Concurrency Control (MVCC)
  - Used by PostgreSQL (Repeatable Read), MySQL InnoDB, Oracle

Key concepts:
  - Read skew: reading from different points in time
  - Snapshot isolation: all reads from same point in time
  - MVCC: multiple versions with visibility rules
  - Visibility rule: created_by committed before txn started
  - Garbage collection: remove old versions when no longer needed

Run: python 02_snapshot_isolation.py
"""

import sys
import time
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass
from enum import Enum

sys.stdout.reconfigure(encoding='utf-8')


# =============================================================================
# CORE COMPONENTS: Transaction, DataVersion, SnapshotDatabase
# =============================================================================

class TransactionState(Enum):
    """State of a transaction."""
    ACTIVE = "ACTIVE"
    COMMITTED = "COMMITTED"
    ABORTED = "ABORTED"


@dataclass
class DataVersion:
    """A version of a data item with visibility metadata."""
    value: Any
    created_by_txn: int
    deleted_by_txn: Optional[int] = None
    timestamp: float = 0.0

    def __repr__(self):
        status = "DELETED" if self.deleted_by_txn else "ACTIVE"
        return f"v(txn={self.created_by_txn}, {status}, val={self.value})"


class Transaction:
    """A transaction under Snapshot Isolation."""

    _next_id = 1

    def __init__(self, snapshot_time: int):
        self.txn_id = Transaction._next_id
        Transaction._next_id += 1
        self.state = TransactionState.ACTIVE
        self.snapshot_time = snapshot_time  # When this transaction started
        self.start_time = time.time()
        self.read_set: Dict[str, Any] = {}
        self.write_set: Dict[str, Any] = {}
        self.committed_txns_at_start: Set[int] = set()  # Txns committed before this started

    def is_active(self) -> bool:
        return self.state == TransactionState.ACTIVE

    def is_committed(self) -> bool:
        return self.state == TransactionState.COMMITTED

    def commit(self):
        self.state = TransactionState.COMMITTED

    def abort(self):
        self.state = TransactionState.ABORTED

    def __repr__(self):
        return f"Txn({self.txn_id}, snapshot_time={self.snapshot_time}, {self.state.value})"


class SnapshotIsolationDatabase:
    """
    A database implementing SNAPSHOT ISOLATION via MVCC.

    Key features:
    - Each transaction reads from a consistent snapshot
    - Prevents read skew
    - Implementation: Multi-Version Concurrency Control (MVCC)
    - Visibility rule: created_by committed before txn started
    """

    def __init__(self):
        self.data: Dict[str, List[DataVersion]] = {}  # item_id -> [versions]
        self.transactions: Dict[int, Transaction] = {}  # txn_id -> Transaction
        self.committed_txns: Set[int] = set()  # Set of committed transaction IDs
        self.operation_log: List[Tuple[float, str]] = []
        self.logical_clock = 0  # Logical timestamp for snapshots

    def begin_transaction(self) -> Transaction:
        """Start a new transaction with a snapshot."""
        # Record which transactions are committed at this point
        snapshot_time = self.logical_clock
        txn = Transaction(snapshot_time)
        txn.committed_txns_at_start = self.committed_txns.copy()

        self.transactions[txn.txn_id] = txn
        self._log(f"BEGIN Txn{txn.txn_id} (snapshot_time={snapshot_time}, sees committed: {sorted(txn.committed_txns_at_start)})")
        return txn

    def read(self, txn: Transaction, item_id: str) -> Optional[Any]:
        """
        Read an item under Snapshot Isolation.

        Visibility rule: A version is visible if:
          1. created_by was committed BEFORE this transaction started, AND
          2. deleted_by is either NULL or was set by a txn that had NOT committed when this txn started
        """
        if not txn.is_active():
            raise ValueError(f"Transaction {txn.txn_id} is not active")

        if item_id not in self.data:
            self._log(f"  Txn{txn.txn_id} READ {item_id} = None (no versions)")
            return None

        # Find the latest visible version
        versions = self.data[item_id]
        for version in reversed(versions):
            # Check if created_by was committed before this txn started
            if version.created_by_txn not in txn.committed_txns_at_start:
                continue

            # Check if deleted_by is visible
            if version.deleted_by_txn is None:
                # Not deleted, this version is visible
                txn.read_set[item_id] = version.value
                self._log(f"  Txn{txn.txn_id} READ {item_id} = {version.value} (from Txn{version.created_by_txn})")
                return version.value
            elif version.deleted_by_txn not in txn.committed_txns_at_start:
                # Deleted by a txn that wasn't committed when this txn started
                # So the deletion is not visible, this version is still visible
                txn.read_set[item_id] = version.value
                self._log(f"  Txn{txn.txn_id} READ {item_id} = {version.value} (from Txn{version.created_by_txn}, deletion not visible)")
                return version.value

        self._log(f"  Txn{txn.txn_id} READ {item_id} = None (no visible version)")
        return None

    def write(self, txn: Transaction, item_id: str, value: Any):
        """
        Write an item under Snapshot Isolation.

        Create a new version tagged with this transaction's ID.
        """
        if not txn.is_active():
            raise ValueError(f"Transaction {txn.txn_id} is not active")

        if item_id not in self.data:
            self.data[item_id] = []

        new_version = DataVersion(
            value=value,
            created_by_txn=txn.txn_id,
            timestamp=time.time()
        )
        self.data[item_id].append(new_version)
        txn.write_set[item_id] = value

        self._log(f"  Txn{txn.txn_id} WRITE {item_id} = {value}")

    def commit_transaction(self, txn: Transaction):
        """Commit a transaction."""
        if not txn.is_active():
            raise ValueError(f"Transaction {txn.txn_id} is not active")

        txn.commit()
        self.committed_txns.add(txn.txn_id)
        self.logical_clock += 1

        self._log(f"COMMIT Txn{txn.txn_id}")

    def abort_transaction(self, txn: Transaction):
        """Abort a transaction."""
        if not txn.is_active():
            raise ValueError(f"Transaction {txn.txn_id} is not active")

        txn.abort()
        self._log(f"ABORT Txn{txn.txn_id}")

        # Remove uncommitted versions
        for item_id in txn.write_set:
            if item_id in self.data:
                self.data[item_id] = [v for v in self.data[item_id] if v.created_by_txn != txn.txn_id]

    def _log(self, message: str):
        """Log an operation."""
        self.operation_log.append((time.time(), message))
        print(message)

    def print_state(self):
        """Print current database state."""
        print("\n  📊 Database State:")
        for item_id, versions in self.data.items():
            print(f"    {item_id}:")
            for v in versions:
                status = "ACTIVE" if v.deleted_by_txn is None else f"DELETED by Txn{v.deleted_by_txn}"
                print(f"      v(Txn{v.created_by_txn}, {status}): {v.value}")

    def print_visibility(self, txn: Transaction):
        """Print what this transaction can see."""
        print(f"\n  👁️  Txn{txn.txn_id} Visibility (snapshot_time={txn.snapshot_time}):")
        print(f"     Can see committed txns: {sorted(txn.committed_txns_at_start)}")


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


def demo_1_snapshot_isolation_basics():
    """
    Demo 1: Show how Snapshot Isolation works.

    DDIA concept: "Each transaction reads from a consistent snapshot
    of the database. The transaction sees all the data that was
    committed at the start of the transaction."
    """
    print_header("DEMO 1: Snapshot Isolation Basics")
    print("""
    Each transaction gets a snapshot of the database at the moment
    it starts. All reads see this snapshot, not the current state.
    """)

    db = SnapshotIsolationDatabase()

    # Initialize data
    txn_init = db.begin_transaction()
    db.write(txn_init, "x", 1)
    db.write(txn_init, "y", 1)
    db.commit_transaction(txn_init)

    print_section("Initial State")
    print(f"  x = 1, y = 1")

    # Transaction A: Update x and y
    print_section("Transaction A: Update x=2, y=2")
    txn_a = db.begin_transaction()
    db.write(txn_a, "x", 2)
    db.write(txn_a, "y", 2)
    print(f"  (Txn{txn_a.txn_id} has NOT committed yet)")

    # Transaction B: Read x and y
    print_section("Transaction B: Read x and y")
    txn_b = db.begin_transaction()
    db.print_visibility(txn_b)
    x = db.read(txn_b, "x")
    y = db.read(txn_b, "y")
    print(f"  ✅ Txn{txn_b.txn_id} sees: x={x}, y={y}")
    print(f"     Both from the same snapshot (before Txn{txn_a.txn_id}'s changes)")

    # Commit A
    print_section("Transaction A: Commit")
    db.commit_transaction(txn_a)

    # B reads again
    print_section("Transaction B: Read x and y again")
    x = db.read(txn_b, "x")
    y = db.read(txn_b, "y")
    print(f"  ✅ Txn{txn_b.txn_id} STILL sees: x={x}, y={y}")
    print(f"     Same snapshot! Txn{txn_a.txn_id}'s changes are NOT visible")

    db.commit_transaction(txn_b)

    print("""
  💡 KEY INSIGHT (DDIA):
     Snapshot Isolation provides a consistent view:
       • All reads see the same point in time
       • Committed changes are invisible until next transaction
       • No read skew!
    """)


def demo_2_fixes_read_skew():
    """
    Demo 2: Show how Snapshot Isolation fixes read skew.

    DDIA concept: "Snapshot Isolation solves the read skew problem
    by ensuring all reads see the same snapshot."
    """
    print_header("DEMO 2: Snapshot Isolation Fixes Read Skew")
    print("""
    Same scenario as before: Alice has $500 in each account.
    A transfer moves $100 from Account 1 to Account 2.
    Alice reads both accounts.

    Under SNAPSHOT ISOLATION: Alice sees consistent state!
    """)

    db = SnapshotIsolationDatabase()

    # Initialize accounts
    txn_init = db.begin_transaction()
    db.write(txn_init, "account_1", 500)
    db.write(txn_init, "account_2", 500)
    db.commit_transaction(txn_init)

    print_section("Initial State")
    print(f"  Account 1: $500")
    print(f"  Account 2: $500")
    print(f"  Total: $1000")

    # Transaction A: Transfer $100
    print_section("Transaction A: Transfer $100 from Account 1 to Account 2")
    txn_a = db.begin_transaction()
    db.write(txn_a, "account_1", 400)
    db.write(txn_a, "account_2", 600)
    print(f"  (Txn{txn_a.txn_id} has NOT committed yet)")

    # Transaction B: Alice reads both accounts
    print_section("Transaction B: Alice reads both accounts")
    txn_b = db.begin_transaction()
    db.print_visibility(txn_b)
    acc1 = db.read(txn_b, "account_1")
    print(f"  Alice reads Account 1: ${acc1}")

    # Commit A
    print_section("Transaction A: Commit")
    db.commit_transaction(txn_a)
    print(f"  Transfer is now committed")

    # B reads second account
    print_section("Transaction B: Alice reads Account 2")
    acc2 = db.read(txn_b, "account_2")
    print(f"  Alice reads Account 2: ${acc2}")

    db.commit_transaction(txn_b)

    print_section("Alice's View")
    print(f"  Account 1: ${acc1}")
    print(f"  Account 2: ${acc2}")
    print(f"  Total: ${acc1 + acc2}")
    print(f"  ✅ CONSISTENT! Alice sees $1000 (from the same snapshot)")

    print("""
  💡 KEY INSIGHT (DDIA):
     Snapshot Isolation fixes read skew:
       • Alice's transaction has a snapshot_time
       • All reads see data committed BEFORE that time
       • Even though Txn{txn_a.txn_id} commits during Alice's transaction,
         she doesn't see its changes
       • Result: consistent view of the data
    """)


def demo_3_mvcc_visibility_rules():
    """
    Demo 3: Show MVCC visibility rules in detail.

    DDIA concept: "A transaction can see a row version only if:
    - created_by was committed BEFORE transaction started, AND
    - deleted_by is either NULL or was set by a transaction that
      had NOT YET committed when this transaction started."
    """
    print_header("DEMO 3: MVCC Visibility Rules")
    print("""
    MVCC stores multiple versions of each item.
    Each version has metadata about which transactions created/deleted it.

    Visibility rule:
      A version is visible if:
        1. created_by was committed BEFORE this txn started
        2. deleted_by is NULL or not yet committed
    """)

    db = SnapshotIsolationDatabase()

    # Create initial version
    print_section("Step 1: Create initial version")
    txn1 = db.begin_transaction()
    db.write(txn1, "value", "v1")
    db.commit_transaction(txn1)
    print(f"  Txn{txn1.txn_id} created version 'v1'")

    # Create second version (uncommitted)
    print_section("Step 2: Create second version (uncommitted)")
    txn2 = db.begin_transaction()
    db.write(txn2, "value", "v2")
    print(f"  Txn{txn2.txn_id} created version 'v2' (NOT committed)")

    # Read from another transaction
    print_section("Step 3: Read from another transaction")
    txn3 = db.begin_transaction()
    db.print_visibility(txn3)
    result = db.read(txn3, "value")
    print(f"  Txn{txn3.txn_id} reads 'value' = {result}")
    print(f"  (Sees v1 from Txn{txn1.txn_id}, ignores v2 from uncommitted Txn{txn2.txn_id})")

    # Commit txn2
    print_section("Step 4: Commit txn2")
    db.commit_transaction(txn2)
    print(f"  Txn{txn2.txn_id} is now committed")

    # Read from another transaction (started after txn2 committed)
    print_section("Step 5: Read from new transaction (started after txn2 committed)")
    txn4 = db.begin_transaction()
    db.print_visibility(txn4)
    result = db.read(txn4, "value")
    print(f"  Txn{txn4.txn_id} reads 'value' = {result}")
    print(f"  (Now sees v2 from committed Txn{txn2.txn_id})")

    db.commit_transaction(txn3)
    db.commit_transaction(txn4)

    print_section("Database State")
    db.print_state()

    print("""
  💡 KEY INSIGHT (DDIA):
     MVCC visibility rules ensure:
       • Transactions see consistent snapshots
       • Uncommitted changes are invisible
       • Old versions are kept for active transactions
       • Garbage collection removes old versions when no longer needed
    """)


def demo_4_garbage_collection():
    """
    Demo 4: Show garbage collection of old versions.

    DDIA concept: "Old versions are garbage collected when they
    are no longer needed by any running transaction."
    """
    print_header("DEMO 4: Garbage Collection of Old Versions")
    print("""
    As transactions commit, old versions become invisible.
    The database can garbage collect them to save space.
    """)

    db = SnapshotIsolationDatabase()

    # Create initial version
    txn1 = db.begin_transaction()
    db.write(txn1, "value", "v1")
    db.commit_transaction(txn1)

    print_section("After Txn1 commits")
    db.print_state()

    # Create second version
    txn2 = db.begin_transaction()
    db.write(txn2, "value", "v2")
    db.commit_transaction(txn2)

    print_section("After Txn2 commits")
    db.print_state()
    print(f"  v1 is now invisible (replaced by v2)")
    print(f"  But we keep it in case an old transaction needs it")

    # Create third version
    txn3 = db.begin_transaction()
    db.write(txn3, "value", "v3")
    db.commit_transaction(txn3)

    print_section("After Txn3 commits")
    db.print_state()
    print(f"  v1 and v2 are now invisible")
    print(f"  We can garbage collect them if no active txns need them")

    print("""
  💡 KEY INSIGHT (DDIA):
     Garbage collection:
       • Removes versions that are no longer visible to any transaction
       • Saves disk space
       • Must be careful not to remove versions needed by active txns
       • Typically done when all transactions that could see a version
         have committed or aborted
    """)


def demo_5_comparison_with_read_committed():
    """
    Demo 5: Compare Snapshot Isolation with Read Committed.

    DDIA concept: "Snapshot Isolation is stronger than Read Committed
    but weaker than Serializability."
    """
    print_header("DEMO 5: Snapshot Isolation vs Read Committed")
    print("""
    Comparison of isolation levels.
    """)

    print_section("Isolation Level Comparison")
    print(f"""
  {'Anomaly':<25} {'Read Committed':<20} {'Snapshot Isolation'}
  {'─'*70}
  {'Dirty reads':<25} {'Prevented':<20} {'Prevented'}
  {'Dirty writes':<25} {'Prevented':<20} {'Prevented'}
  {'Read skew':<25} {'ALLOWED':<20} {'Prevented'}
  {'Lost updates':<25} {'ALLOWED':<20} {'ALLOWED'}
  {'Write skew':<25} {'ALLOWED':<20} {'ALLOWED'}
  {'Phantoms':<25} {'ALLOWED':<20} {'ALLOWED'}
    """)

    print("""
  💡 KEY INSIGHT (DDIA):
     Snapshot Isolation:
       ✅ Prevents dirty reads and writes
       ✅ Prevents read skew
       ❌ Allows lost updates (need explicit locking)
       ❌ Allows write skew (need serializability)

     Used by:
       • PostgreSQL (Repeatable Read)
       • MySQL InnoDB (Repeatable Read)
       • Oracle
       • SQL Server (Snapshot Isolation)
    """)


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 80)
    print("  EXERCISE 2: SNAPSHOT ISOLATION AND MVCC")
    print("  DDIA Chapter 7: 'Weak Isolation Levels'")
    print("=" * 80)
    print("""
  This exercise demonstrates SNAPSHOT ISOLATION.
  You'll see how MVCC provides consistent snapshots and fixes
  the read skew problem of Read Committed.
    """)

    demo_1_snapshot_isolation_basics()
    demo_2_fixes_read_skew()
    demo_3_mvcc_visibility_rules()
    demo_4_garbage_collection()
    demo_5_comparison_with_read_committed()

    print("\n" + "=" * 80)
    print("  EXERCISE 2 COMPLETE ✅")
    print("=" * 80)
    print("""
  Key Takeaways:

  1. 📸 SNAPSHOT ISOLATION: each txn reads from a consistent snapshot
  2. 🔧 MVCC: multiple versions with visibility rules
  3. ✅ Fixes read skew (the limitation of Read Committed)
  4. 👁️  Visibility rule: created_by committed before txn started
  5. 🗑️  Garbage collection: remove old versions when no longer needed
  6. ⚠️  Still allows lost updates and write skew

  Next: Run 03_lost_updates.py to see concurrent write problems
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
