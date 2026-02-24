"""
Exercise 1: Read Committed Isolation Level

DDIA Reference: Chapter 7, "Weak Isolation Levels" (pp. 233-237)

This exercise demonstrates READ COMMITTED isolation:
  - The most basic level of transaction isolation
  - Prevents dirty reads: never see uncommitted data
  - Prevents dirty writes: never overwrite uncommitted data
  - Implementation: row-level locks + multi-version storage

Key concepts:
  - Dirty read: reading uncommitted data from another transaction
  - Dirty write: overwriting uncommitted data from another transaction
  - Read Committed prevents both
  - Default in PostgreSQL, Oracle, SQL Server

Run: python 01_read_committed.py
"""

import sys
import time
import threading
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

sys.stdout.reconfigure(encoding='utf-8')


# =============================================================================
# CORE COMPONENTS: Transaction, Lock, Database
# =============================================================================

class TransactionState(Enum):
    """State of a transaction."""
    ACTIVE = "ACTIVE"
    COMMITTED = "COMMITTED"
    ABORTED = "ABORTED"


@dataclass
class DataVersion:
    """A version of a data item."""
    value: Any
    created_by_txn: int
    deleted_by_txn: Optional[int] = None
    timestamp: float = 0.0

    def __repr__(self):
        status = "DELETED" if self.deleted_by_txn else "ACTIVE"
        return f"v(txn={self.created_by_txn}, {status}, val={self.value})"


class Lock:
    """A lock on a data item."""

    def __init__(self, item_id: str):
        self.item_id = item_id
        self.held_by_txn: Optional[int] = None
        self.lock_type = None  # 'read' or 'write'

    def is_locked(self) -> bool:
        return self.held_by_txn is not None

    def __repr__(self):
        return f"Lock({self.item_id}, held_by={self.held_by_txn}, type={self.lock_type})"


class Transaction:
    """A database transaction."""

    _next_id = 1

    def __init__(self):
        self.txn_id = Transaction._next_id
        Transaction._next_id += 1
        self.state = TransactionState.ACTIVE
        self.start_time = time.time()
        self.read_set: Dict[str, Any] = {}  # item_id -> value read
        self.write_set: Dict[str, Any] = {}  # item_id -> value to write
        self.locks_held: List[Lock] = []

    def is_active(self) -> bool:
        return self.state == TransactionState.ACTIVE

    def is_committed(self) -> bool:
        return self.state == TransactionState.COMMITTED

    def commit(self):
        self.state = TransactionState.COMMITTED

    def abort(self):
        self.state = TransactionState.ABORTED

    def __repr__(self):
        return f"Txn({self.txn_id}, {self.state.value})"


class ReadCommittedDatabase:
    """
    A database implementing READ COMMITTED isolation.

    Key features:
    - Prevents dirty reads: readers see only committed data
    - Prevents dirty writes: writers don't overwrite uncommitted data
    - Implementation: row-level locks + multi-version storage
    """

    def __init__(self):
        self.data: Dict[str, List[DataVersion]] = {}  # item_id -> [versions]
        self.locks: Dict[str, Lock] = {}  # item_id -> Lock
        self.transactions: Dict[int, Transaction] = {}  # txn_id -> Transaction
        self.operation_log: List[Tuple[float, str]] = []

    def begin_transaction(self) -> Transaction:
        """Start a new transaction."""
        txn = Transaction()
        self.transactions[txn.txn_id] = txn
        self._log(f"BEGIN Txn{txn.txn_id}")
        return txn

    def read(self, txn: Transaction, item_id: str) -> Optional[Any]:
        """
        Read an item under READ COMMITTED isolation.

        Rule: Only see committed data.
        Implementation: Return the latest committed version.
        """
        if not txn.is_active():
            raise ValueError(f"Transaction {txn.txn_id} is not active")

        # Ensure item exists
        if item_id not in self.data:
            self.data[item_id] = []
            return None

        # Find the latest committed version
        versions = self.data[item_id]
        for version in reversed(versions):
            # Check if this version is committed
            creator_txn = self.transactions.get(version.created_by_txn)
            if creator_txn and creator_txn.is_committed():
                # Check if it's not deleted
                if version.deleted_by_txn is None:
                    deleter_txn = None
                else:
                    deleter_txn = self.transactions.get(version.deleted_by_txn)

                if deleter_txn is None or not deleter_txn.is_committed():
                    # This version is visible
                    txn.read_set[item_id] = version.value
                    self._log(f"  Txn{txn.txn_id} READ {item_id} = {version.value} (from Txn{version.created_by_txn})")
                    return version.value

        self._log(f"  Txn{txn.txn_id} READ {item_id} = None (no committed version)")
        return None

    def write(self, txn: Transaction, item_id: str, value: Any):
        """
        Write an item under READ COMMITTED isolation.

        Rule: Don't overwrite uncommitted data (acquire write lock).
        Implementation: Acquire lock, create new version.
        """
        if not txn.is_active():
            raise ValueError(f"Transaction {txn.txn_id} is not active")

        # Acquire write lock
        if item_id not in self.locks:
            self.locks[item_id] = Lock(item_id)

        lock = self.locks[item_id]

        # Check if lock is held by another transaction
        if lock.is_locked() and lock.held_by_txn != txn.txn_id:
            self._log(f"  Txn{txn.txn_id} BLOCKED on {item_id} (held by Txn{lock.held_by_txn})")
            # In a real system, we'd wait. For simulation, we'll just note the conflict.
            return False

        # Acquire lock
        lock.held_by_txn = txn.txn_id
        lock.lock_type = 'write'
        txn.locks_held.append(lock)

        # Create new version
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
        return True

    def commit_transaction(self, txn: Transaction):
        """Commit a transaction."""
        if not txn.is_active():
            raise ValueError(f"Transaction {txn.txn_id} is not active")

        txn.commit()
        self._log(f"COMMIT Txn{txn.txn_id}")

        # Release locks
        for lock in txn.locks_held:
            lock.held_by_txn = None
            lock.lock_type = None

    def abort_transaction(self, txn: Transaction):
        """Abort a transaction."""
        if not txn.is_active():
            raise ValueError(f"Transaction {txn.txn_id} is not active")

        txn.abort()
        self._log(f"ABORT Txn{txn.txn_id}")

        # Release locks
        for lock in txn.locks_held:
            lock.held_by_txn = None
            lock.lock_type = None

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


def demo_1_no_dirty_reads():
    """
    Demo 1: Show that READ COMMITTED prevents dirty reads.

    DDIA concept: "When reading from the database, you will only see
    data that has been committed. You will never see data that is
    still being written by an in-progress transaction."
    """
    print_header("DEMO 1: No Dirty Reads")
    print("""
    Scenario: Transaction A updates a value but hasn't committed yet.
    Transaction B tries to read the same value.

    Under READ COMMITTED: B sees the OLD committed value, not A's uncommitted change.
    """)

    db = ReadCommittedDatabase()

    # Initialize data
    txn_init = db.begin_transaction()
    db.write(txn_init, "balance", 100)
    db.commit_transaction(txn_init)

    print_section("Initial State")
    db.print_state()

    # Transaction A: Update balance
    print_section("Transaction A: Update balance to 50")
    txn_a = db.begin_transaction()
    db.write(txn_a, "balance", 50)
    print(f"  (Txn{txn_a.txn_id} has NOT committed yet)")

    # Transaction B: Read balance
    print_section("Transaction B: Read balance")
    txn_b = db.begin_transaction()
    value = db.read(txn_b, "balance")
    print(f"  ✅ Txn{txn_b.txn_id} sees: balance = {value}")
    print(f"     This is the OLD committed value, NOT Txn{txn_a.txn_id}'s uncommitted change!")

    # Commit A
    print_section("Transaction A: Commit")
    db.commit_transaction(txn_a)

    # B reads again
    print_section("Transaction B: Read balance again")
    value = db.read(txn_b, "balance")
    print(f"  ✅ Txn{txn_b.txn_id} now sees: balance = {value}")
    print(f"     Now it sees Txn{txn_a.txn_id}'s committed change!")

    db.commit_transaction(txn_b)

    print("""
  💡 KEY INSIGHT (DDIA):
     READ COMMITTED prevents dirty reads by:
       1. Holding write locks until commit
       2. Readers see only committed versions
       3. Uncommitted changes are invisible to other transactions
    """)


def demo_2_no_dirty_writes():
    """
    Demo 2: Show that READ COMMITTED prevents dirty writes.

    DDIA concept: "When writing to the database, you will only
    overwrite data that has been committed. Your write will not
    interleave with another in-progress transaction's writes."
    """
    print_header("DEMO 2: No Dirty Writes")
    print("""
    Scenario: Transaction A is updating a value.
    Transaction B tries to update the same value.

    Under READ COMMITTED: B must wait for A to commit/abort first.
    """)

    db = ReadCommittedDatabase()

    # Initialize data
    txn_init = db.begin_transaction()
    db.write(txn_init, "counter", 0)
    db.commit_transaction(txn_init)

    print_section("Initial State")
    db.print_state()

    # Transaction A: Update counter
    print_section("Transaction A: Update counter to 1")
    txn_a = db.begin_transaction()
    db.write(txn_a, "counter", 1)
    print(f"  (Txn{txn_a.txn_id} holds write lock on 'counter')")

    # Transaction B: Try to update counter
    print_section("Transaction B: Try to update counter to 2")
    txn_b = db.begin_transaction()
    success = db.write(txn_b, "counter", 2)
    if not success:
        print(f"  ⚠️  Txn{txn_b.txn_id} BLOCKED (Txn{txn_a.txn_id} holds the lock)")

    # Commit A
    print_section("Transaction A: Commit")
    db.commit_transaction(txn_a)
    print(f"  (Lock on 'counter' is now released)")

    # B can now write
    print_section("Transaction B: Now can update counter to 2")
    success = db.write(txn_b, "counter", 2)
    if success:
        print(f"  ✅ Txn{txn_b.txn_id} acquired lock and wrote counter = 2")

    db.commit_transaction(txn_b)

    print_section("Final State")
    db.print_state()

    print("""
  💡 KEY INSIGHT (DDIA):
     READ COMMITTED prevents dirty writes by:
       1. Acquiring write locks on modified items
       2. Holding locks until commit/abort
       3. Other writers must wait for the lock
       4. No interleaving of writes
    """)


def demo_3_read_committed_limitations():
    """
    Demo 3: Show limitations of READ COMMITTED.

    DDIA concept: "Read Committed is useful but has a problem
    called Read Skew (a type of non-repeatable read)."
    """
    print_header("DEMO 3: Limitations of Read Committed — Read Skew")
    print("""
    Scenario: Alice has $500 in Account 1 and $500 in Account 2.
    A transfer moves $100 from Account 1 to Account 2.
    Alice reads both accounts while the transfer is in progress.

    Under READ COMMITTED: Alice sees inconsistent state!
    """)

    db = ReadCommittedDatabase()

    # Initialize accounts
    txn_init = db.begin_transaction()
    db.write(txn_init, "account_1", 500)
    db.write(txn_init, "account_2", 500)
    db.commit_transaction(txn_init)

    print_section("Initial State")
    print(f"  Account 1: $500")
    print(f"  Account 2: $500")
    print(f"  Total: $1000")

    # Transaction A: Transfer $100 from Account 1 to Account 2
    print_section("Transaction A: Transfer $100 from Account 1 to Account 2")
    txn_a = db.begin_transaction()
    db.write(txn_a, "account_1", 400)
    db.write(txn_a, "account_2", 600)
    print(f"  (Txn{txn_a.txn_id} has NOT committed yet)")

    # Transaction B: Alice reads both accounts
    print_section("Transaction B: Alice reads both accounts")
    txn_b = db.begin_transaction()
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
    print(f"  ⚠️  INCONSISTENT! Should be $1000, but Alice sees ${acc1 + acc2}")

    print("""
  💡 KEY INSIGHT (DDIA):
     READ COMMITTED has a problem: READ SKEW
       • Alice reads from two different points in time
       • She sees Account 1 BEFORE the transfer
       • She sees Account 2 AFTER the transfer
       • Result: inconsistent view of the data

     Solution: SNAPSHOT ISOLATION (next exercise)
       • Each transaction reads from a consistent snapshot
       • All reads see the same point in time
    """)


def demo_4_implementation_details():
    """
    Demo 4: Show how READ COMMITTED is implemented.

    DDIA concept: "Implementation: row-level locks + multi-version storage"
    """
    print_header("DEMO 4: Implementation Details")
    print("""
    READ COMMITTED uses:
    1. Row-level locks to prevent dirty writes
    2. Multi-version storage to prevent dirty reads
    """)

    print_section("Multi-Version Storage")
    print("""
    Instead of storing one version of each item, the database
    stores multiple versions with metadata:

      created_by: Transaction ID that created this version
      deleted_by: Transaction ID that deleted this version (if any)

    When a transaction reads:
      • Find the latest committed version
      • Ignore uncommitted versions
      • Ignore deleted versions (unless deletion is uncommitted)
    """)

    db = ReadCommittedDatabase()

    # Create initial version
    txn1 = db.begin_transaction()
    db.write(txn1, "value", "v1")
    db.commit_transaction(txn1)

    # Create second version (uncommitted)
    txn2 = db.begin_transaction()
    db.write(txn2, "value", "v2")

    # Read from another transaction
    txn3 = db.begin_transaction()
    result = db.read(txn3, "value")
    print(f"\n  Txn{txn3.txn_id} reads 'value' = {result}")
    print(f"  (Sees v1 from Txn{txn1.txn_id}, ignores v2 from uncommitted Txn{txn2.txn_id})")

    db.commit_transaction(txn2)
    db.commit_transaction(txn3)

    print_section("Database State After All Commits")
    db.print_state()

    print("""
  💡 KEY INSIGHT (DDIA):
     Multi-version storage allows:
       • Readers to see committed data
       • Writers to create new versions without blocking readers
       • Uncommitted versions to be invisible
    """)


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 80)
    print("  EXERCISE 1: READ COMMITTED ISOLATION LEVEL")
    print("  DDIA Chapter 7: 'Weak Isolation Levels'")
    print("=" * 80)
    print("""
  This exercise demonstrates READ COMMITTED isolation.
  You'll see how it prevents dirty reads and dirty writes,
  and understand its limitations (read skew).
    """)

    demo_1_no_dirty_reads()
    demo_2_no_dirty_writes()
    demo_3_read_committed_limitations()
    demo_4_implementation_details()

    print("\n" + "=" * 80)
    print("  EXERCISE 1 COMPLETE ✅")
    print("=" * 80)
    print("""
  Key Takeaways:

  1. 🔒 READ COMMITTED prevents dirty reads and dirty writes
  2. 📖 Readers see only committed data (multi-version storage)
  3. ✍️  Writers hold locks until commit (no dirty writes)
  4. ⚠️  READ COMMITTED has a limitation: READ SKEW
  5. 📊 Alice can see inconsistent totals (different points in time)
  6. 🔧 Solution: SNAPSHOT ISOLATION (next exercise)

  Next: Run 02_snapshot_isolation.py to see how MVCC fixes read skew
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
