"""
Exercise 1: Single-Object Atomicity and Isolation

DDIA Reference: Chapter 7, "Transactions" (pp. 226-230)

This exercise demonstrates SINGLE-OBJECT ATOMICITY and ISOLATION.
Even a single write operation needs safety guarantees.

Key concepts:
  - Atomicity: Either the entire write succeeds, or none of it does
  - Isolation: No other transaction can see a half-written object
  - Implementation: Write-Ahead Log (WAL) + locks
  - Most databases provide these by default (not full ACID transactions)

Scenarios covered:
  1. Partial write with crash (atomicity problem)
  2. Reading half-written data (isolation problem)
  3. How WAL prevents corruption
  4. How locks prevent dirty reads

Run: python 01_single_object_atomicity.py
"""

import sys
import time
import random
from typing import Dict, Optional, Any
from enum import Enum
from dataclasses import dataclass

sys.stdout.reconfigure(encoding='utf-8')


# =============================================================================
# CORE COMPONENTS: WriteAheadLog, Lock, Object, Database
# =============================================================================

class TransactionState(Enum):
    """State of a transaction."""
    ACTIVE = "active"
    COMMITTED = "committed"
    ABORTED = "aborted"


@dataclass
class LogEntry:
    """An entry in the Write-Ahead Log."""
    txn_id: int
    object_id: str
    old_value: Any
    new_value: Any
    timestamp: float
    state: TransactionState

    def __repr__(self):
        return f"LogEntry(txn={self.txn_id}, obj={self.object_id}, {self.old_value}→{self.new_value}, {self.state.value})"


class WriteAheadLog:
    """
    Write-Ahead Log (WAL) — the mechanism for durability and atomicity.

    DDIA insight: "Before writing to the main database, the database
    writes the change to a log on disk. If the database crashes, it can
    replay the log to recover."

    For atomicity: the log entry is marked as COMMITTED only after
    the write succeeds. If the database crashes before this mark,
    the write is rolled back.
    """

    def __init__(self):
        self.entries: Dict[int, LogEntry] = {}  # txn_id -> LogEntry
        self._next_txn_id = 1

    def begin_transaction(self) -> int:
        """Begin a new transaction."""
        txn_id = self._next_txn_id
        self._next_txn_id += 1
        return txn_id

    def log_write(self, txn_id: int, object_id: str, old_value: Any, new_value: Any) -> LogEntry:
        """
        Log a write operation BEFORE applying it to the database.

        DDIA: "The database writes the change to the log FIRST,
        then applies it to the main storage."
        """
        entry = LogEntry(
            txn_id=txn_id,
            object_id=object_id,
            old_value=old_value,
            new_value=new_value,
            timestamp=time.time(),
            state=TransactionState.ACTIVE
        )
        self.entries[txn_id] = entry
        return entry

    def commit_transaction(self, txn_id: int):
        """Mark a transaction as committed in the log."""
        if txn_id in self.entries:
            self.entries[txn_id].state = TransactionState.COMMITTED

    def abort_transaction(self, txn_id: int):
        """Mark a transaction as aborted in the log."""
        if txn_id in self.entries:
            self.entries[txn_id].state = TransactionState.ABORTED

    def get_committed_entries(self) -> list:
        """Get all committed entries (for recovery)."""
        return [e for e in self.entries.values() if e.state == TransactionState.COMMITTED]

    def get_active_entries(self) -> list:
        """Get all active (uncommitted) entries (for rollback on crash)."""
        return [e for e in self.entries.values() if e.state == TransactionState.ACTIVE]


class Lock:
    """A lock on an object (for isolation)."""

    def __init__(self, object_id: str):
        self.object_id = object_id
        self.held_by: Optional[int] = None  # txn_id holding the lock
        self.lock_type: Optional[str] = None  # "read" or "write"

    def acquire_write_lock(self, txn_id: int) -> bool:
        """Acquire an exclusive write lock."""
        if self.held_by is None:
            self.held_by = txn_id
            self.lock_type = "write"
            return True
        return False

    def acquire_read_lock(self, txn_id: int) -> bool:
        """Acquire a shared read lock."""
        if self.held_by is None or (self.held_by == txn_id and self.lock_type == "read"):
            self.held_by = txn_id
            self.lock_type = "read"
            return True
        return False

    def release_lock(self, txn_id: int):
        """Release the lock."""
        if self.held_by == txn_id:
            self.held_by = None
            self.lock_type = None

    def is_locked_by(self, txn_id: int) -> bool:
        """Check if locked by a specific transaction."""
        return self.held_by == txn_id


class StoredObject:
    """A single object in the database."""

    def __init__(self, object_id: str, value: Any):
        self.object_id = object_id
        self.value = value
        self.lock = Lock(object_id)
        self.write_lock_holder: Optional[int] = None  # txn_id holding write lock

    def __repr__(self):
        return f"Object({self.object_id}={self.value})"


class AtomicDatabase:
    """
    A simple database with SINGLE-OBJECT ATOMICITY and ISOLATION.

    DDIA: "Most databases provide single-object guarantees by default.
    These are NOT transactions in the ACID sense, though. They are just
    basic safety features."

    Mechanisms:
      1. Write-Ahead Log (WAL) for atomicity
      2. Locks for isolation
      3. Crash recovery
    """

    def __init__(self):
        self.objects: Dict[str, StoredObject] = {}
        self.wal = WriteAheadLog()
        self.active_transactions: Dict[int, Dict] = {}  # txn_id -> {object_id: old_value}

    def begin_transaction(self) -> int:
        """Begin a new transaction."""
        txn_id = self.wal.begin_transaction()
        self.active_transactions[txn_id] = {}
        return txn_id

    def read(self, txn_id: int, object_id: str) -> Optional[Any]:
        """
        Read an object.

        DDIA: "To prevent dirty reads, the database uses locks.
        If another transaction is writing to this object, we must wait."
        """
        if object_id not in self.objects:
            return None

        obj = self.objects[object_id]

        # Try to acquire read lock
        if not obj.lock.acquire_read_lock(txn_id):
            # Lock is held by another transaction
            return None  # In real DB, would block and wait

        return obj.value

    def write(self, txn_id: int, object_id: str, new_value: Any) -> bool:
        """
        Write an object with atomicity and isolation.

        DDIA: "The database writes the change to the log FIRST,
        then applies it to the main storage."

        Steps:
          1. Acquire exclusive lock (isolation)
          2. Log the write (atomicity)
          3. Apply to storage
          4. Mark as committed in log
        """
        # Ensure object exists
        if object_id not in self.objects:
            self.objects[object_id] = StoredObject(object_id, None)

        obj = self.objects[object_id]

        # Step 1: Acquire exclusive write lock
        if not obj.lock.acquire_write_lock(txn_id):
            # Lock is held by another transaction
            return False  # In real DB, would block and wait

        # Step 2: Log the write BEFORE applying it
        old_value = obj.value
        self.wal.log_write(txn_id, object_id, old_value, new_value)

        # Step 3: Apply to storage
        obj.value = new_value

        # Step 4: Mark as committed in log
        self.wal.commit_transaction(txn_id)

        # Release lock
        obj.lock.release_lock(txn_id)

        return True

    def commit_transaction(self, txn_id: int):
        """Commit a transaction."""
        if txn_id in self.active_transactions:
            del self.active_transactions[txn_id]

    def abort_transaction(self, txn_id: int):
        """Abort a transaction and rollback changes."""
        if txn_id in self.active_transactions:
            # Rollback: restore old values
            for object_id, old_value in self.active_transactions[txn_id].items():
                if object_id in self.objects:
                    self.objects[object_id].value = old_value

            self.wal.abort_transaction(txn_id)
            del self.active_transactions[txn_id]

    def crash_and_recover(self):
        """
        Simulate a crash and recovery.

        DDIA: "If the database crashes, it can replay the log to recover.
        Any transaction marked as ACTIVE is rolled back."
        """
        # Rollback active transactions
        for entry in self.wal.get_active_entries():
            if entry.object_id in self.objects:
                self.objects[entry.object_id].value = entry.old_value

        # Replay committed transactions
        for entry in self.wal.get_committed_entries():
            if entry.object_id in self.objects:
                self.objects[entry.object_id].value = entry.new_value


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


def demo_1_atomicity_problem():
    """
    Demo 1: Show the atomicity problem without WAL.

    DDIA concept: "If the database crashes after writing only part of
    the data, we get a corrupted half-written object."
    """
    print_header("DEMO 1: Atomicity Problem (Without WAL)")
    print("""
    Scenario: Writing a 20 KB JSON document.
    The database crashes after writing only 10 KB.

    Without atomicity:
      • 10 KB is written to disk
      • 10 KB is lost
      • Result: corrupted half-document
    """)

    print("  📝 Writing a large document:\n")

    # Simulate writing a large document
    document = {"id": 1, "name": "Alice", "email": "alice@example.com", "data": "x" * 1000}
    print(f"  Document size: {len(str(document))} bytes")

    print(f"\n  Writing to disk...")
    print(f"    [████████░░░░░░░░░░] 50% written")
    print(f"    💥 DATABASE CRASHES!")

    print(f"\n  ❌ Without atomicity:")
    print(f"    • 50% of document is on disk")
    print(f"    • 50% is lost")
    print(f"    • Result: corrupted data")
    print(f"    • Next read: garbage or crash")

    print("""
  💡 KEY INSIGHT (DDIA):
     Without atomicity, a crash leaves the database in an inconsistent state.
     The application can't trust the data.

     Solution: Write-Ahead Log (WAL)
       1. Write change to log FIRST (small, sequential write)
       2. Then apply to main storage
       3. If crash occurs, replay log to recover
    """)


def demo_2_wal_prevents_corruption():
    """
    Demo 2: Show how WAL prevents corruption.

    DDIA concept: "The database writes the change to the log FIRST,
    then applies it to the main storage."
    """
    print_header("DEMO 2: WAL Prevents Corruption")
    print("""
    With Write-Ahead Log (WAL):
      1. Write change to log FIRST
      2. Then apply to main storage
      3. If crash, replay log to recover
    """)

    db = AtomicDatabase()

    print("  📝 Writing a document with WAL:\n")

    # Create initial object
    db.objects["doc_1"] = StoredObject("doc_1", {"name": "Alice", "age": 25})
    print(f"  Initial: {db.objects['doc_1']}")

    # Begin transaction
    txn_id = db.begin_transaction()
    print(f"\n  Transaction {txn_id} begins")

    # Write with WAL
    print(f"\n  Step 1: Log the write to WAL")
    db.wal.log_write(txn_id, "doc_1", {"name": "Alice", "age": 25}, {"name": "Alice", "age": 26})
    print(f"    ✅ Logged: {db.wal.entries[txn_id]}")

    print(f"\n  Step 2: Apply to main storage")
    db.objects["doc_1"].value = {"name": "Alice", "age": 26}
    print(f"    ✅ Applied: {db.objects['doc_1']}")

    print(f"\n  Step 3: Mark as committed in log")
    db.wal.commit_transaction(txn_id)
    print(f"    ✅ Committed: {db.wal.entries[txn_id]}")

    print(f"\n  💥 DATABASE CRASHES!")

    print(f"\n  Recovery process:")
    print(f"    1. Replay committed entries from log")
    print(f"    2. Rollback active entries")

    db.crash_and_recover()

    print(f"\n  ✅ After recovery:")
    print(f"    Document: {db.objects['doc_1']}")
    print(f"    Data is consistent! ✅")

    print("""
  💡 KEY INSIGHT (DDIA):
     WAL ensures atomicity:
       • If crash before commit: rollback (old value restored)
       • If crash after commit: replay (new value restored)
       • Result: always consistent, never corrupted

     This is why databases are reliable!
    """)


def demo_3_isolation_dirty_reads():
    """
    Demo 3: Show the dirty read problem and how locks prevent it.

    DDIA concept: "Isolation means no other transaction can see
    a half-written object."
    """
    print_header("DEMO 3: Isolation — Preventing Dirty Reads")
    print("""
    Scenario: Transaction A is writing, Transaction B is reading.

    Without isolation (dirty read):
      • Transaction B sees half-written data
      • Result: inconsistent view

    With isolation (locks):
      • Transaction B must wait for Transaction A to finish
      • Result: consistent view
    """)

    db = AtomicDatabase()

    # Create initial object
    db.objects["account"] = StoredObject("account", {"balance": 100})
    print(f"  Initial: {db.objects['account']}\n")

    # Transaction A: write
    txn_a = db.begin_transaction()
    print(f"  Transaction A begins (txn_id={txn_a})")
    print(f"    Acquiring write lock on 'account'...")
    db.objects["account"].lock.acquire_write_lock(txn_a)
    print(f"    ✅ Lock acquired")

    print(f"\n  Transaction A: Updating balance 100 → 50")
    db.objects["account"].value = {"balance": 50}
    print(f"    (not committed yet)")

    # Transaction B: try to read
    txn_b = db.begin_transaction()
    print(f"\n  Transaction B begins (txn_id={txn_b})")
    print(f"    Trying to read 'account'...")

    # Try to acquire read lock
    if db.objects["account"].lock.acquire_read_lock(txn_b):
        print(f"    ✅ Lock acquired, reading...")
        value = db.objects["account"].value
        print(f"    Read: {value}")
    else:
        print(f"    ❌ Lock is held by Transaction A")
        print(f"    Transaction B must WAIT")
        print(f"    (In real DB, would block until Transaction A commits)")

    # Transaction A commits
    print(f"\n  Transaction A commits")
    db.wal.commit_transaction(txn_a)
    db.objects["account"].lock.release_lock(txn_a)
    print(f"    ✅ Lock released")

    # Transaction B can now read
    print(f"\n  Transaction B can now read:")
    if db.objects["account"].lock.acquire_read_lock(txn_b):
        value = db.objects["account"].value
        print(f"    ✅ Read: {value}")
        print(f"    Sees committed value (no dirty read) ✅")

    print("""
  💡 KEY INSIGHT (DDIA):
     Locks prevent dirty reads:
       • Writer acquires exclusive lock
       • Reader must wait for lock to be released
       • Reader only sees committed values

     This is why databases are consistent!
    """)


def demo_4_atomicity_in_practice():
    """
    Demo 4: Show atomicity in practice with multiple writes.

    DDIA concept: "Atomicity means either ALL writes succeed or NONE."
    """
    print_header("DEMO 4: Atomicity in Practice")
    print("""
    Scenario: Bank transfer (debit one account, credit another).

    Without atomicity:
      • Debit succeeds, credit fails
      • Money vanishes!

    With atomicity:
      • Both succeed or both fail
      • Money is never lost
    """)

    db = AtomicDatabase()

    # Create accounts
    db.objects["account_a"] = StoredObject("account_a", 100)
    db.objects["account_b"] = StoredObject("account_b", 50)

    print(f"  Initial state:")
    print(f"    Account A: {db.objects['account_a'].value}")
    print(f"    Account B: {db.objects['account_b'].value}")
    print(f"    Total: {db.objects['account_a'].value + db.objects['account_b'].value}\n")

    # Begin transaction
    txn_id = db.begin_transaction()
    print(f"  Transaction {txn_id}: Transfer $30 from A to B\n")

    # Debit account A
    print(f"  Step 1: Debit $30 from Account A")
    db.write(txn_id, "account_a", 70)
    print(f"    ✅ Account A: {db.objects['account_a'].value}")

    # Credit account B
    print(f"\n  Step 2: Credit $30 to Account B")
    db.write(txn_id, "account_b", 80)
    print(f"    ✅ Account B: {db.objects['account_b'].value}")

    # Commit
    db.commit_transaction(txn_id)
    print(f"\n  Transaction committed ✅")

    print(f"\n  Final state:")
    print(f"    Account A: {db.objects['account_a'].value}")
    print(f"    Account B: {db.objects['account_b'].value}")
    print(f"    Total: {db.objects['account_a'].value + db.objects['account_b'].value}")
    print(f"    ✅ Money is conserved!")

    print("""
  💡 KEY INSIGHT (DDIA):
     Atomicity guarantees:
       • All writes in a transaction succeed together
       • Or all are rolled back together
       • Never a partial state

     This is why financial systems use transactions!
    """)


def demo_5_crash_recovery():
    """
    Demo 5: Show crash recovery with WAL.

    DDIA concept: "If the database crashes, it can replay the log to recover."
    """
    print_header("DEMO 5: Crash Recovery with WAL")
    print("""
    Scenario: Database crashes during a transaction.

    Recovery process:
      1. Replay committed entries from log
      2. Rollback active entries
      3. Database is consistent again
    """)

    db = AtomicDatabase()

    # Create initial state
    db.objects["counter"] = StoredObject("counter", 0)
    print(f"  Initial: counter = {db.objects['counter'].value}\n")

    # Transaction 1: committed
    print(f"  Transaction 1: counter = 1")
    txn_1 = db.begin_transaction()
    db.write(txn_1, "counter", 1)
    db.commit_transaction(txn_1)
    print(f"    ✅ Committed")

    # Transaction 2: active (not committed)
    print(f"\n  Transaction 2: counter = 2")
    txn_2 = db.begin_transaction()
    db.write(txn_2, "counter", 2)
    print(f"    ⏳ Active (not committed yet)")

    print(f"\n  Current state: counter = {db.objects['counter'].value}")

    print(f"\n  💥 DATABASE CRASHES!")

    print(f"\n  Recovery process:")
    print(f"    1. Rollback active transactions")
    print(f"       Transaction 2 is rolled back")
    print(f"    2. Replay committed transactions")
    print(f"       Transaction 1 is replayed")

    db.crash_and_recover()

    print(f"\n  ✅ After recovery:")
    print(f"    counter = {db.objects['counter'].value}")
    print(f"    (Transaction 1 is there, Transaction 2 is gone)")
    print(f"    Database is consistent! ✅")

    print("""
  💡 KEY INSIGHT (DDIA):
     WAL enables crash recovery:
       • Committed transactions are replayed
       • Active transactions are rolled back
       • Database always recovers to a consistent state

     This is why databases survive crashes!
    """)


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 80)
    print("  EXERCISE 1: SINGLE-OBJECT ATOMICITY AND ISOLATION")
    print("  DDIA Chapter 7: 'Transactions'")
    print("=" * 80)
    print("""
  This exercise demonstrates SINGLE-OBJECT ATOMICITY and ISOLATION.
  Even a single write operation needs safety guarantees.

  Key mechanisms:
    • Write-Ahead Log (WAL) for atomicity
    • Locks for isolation
    • Crash recovery
    """)

    demo_1_atomicity_problem()
    demo_2_wal_prevents_corruption()
    demo_3_isolation_dirty_reads()
    demo_4_atomicity_in_practice()
    demo_5_crash_recovery()

    print("\n" + "=" * 80)
    print("  EXERCISE 1 COMPLETE ✅")
    print("=" * 80)
    print("""
  Key Takeaways:

  1. 📝 Atomicity: Either ALL writes succeed or NONE
  2. 🔒 Isolation: No dirty reads (locks prevent it)
  3. 📋 WAL: Write-Ahead Log ensures durability
  4. 💥 Crash recovery: Replay log to recover
  5. 🏦 Real-world: Banks rely on these guarantees

  Next: Run 02_multi_object_transactions.py to see multi-object coordination
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
