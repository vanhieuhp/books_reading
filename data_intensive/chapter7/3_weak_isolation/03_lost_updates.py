"""
Exercise 3: Lost Updates — Concurrent Read-Modify-Write

DDIA Reference: Chapter 7, "Weak Isolation Levels" (pp. 243-250)

This exercise demonstrates the LOST UPDATE problem:
  - Occurs when two transactions perform read-modify-write concurrently
  - One transaction's write overwrites the other's change
  - Both Read Committed and Snapshot Isolation allow this
  - Solutions: atomic operations, explicit locking, CAS, auto-detection

Key concepts:
  - Read-modify-write cycle: read value, modify, write back
  - Lost update: one transaction's change is overwritten
  - Atomic operations: best solution when applicable
  - SELECT ... FOR UPDATE: explicit locking
  - Compare-and-set: for systems without transactions
  - Automatic conflict detection: PostgreSQL, Oracle, SQL Server

Run: python 03_lost_updates.py
"""

import sys
import time
from typing import Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum

sys.stdout.reconfigure(encoding='utf-8')


# =============================================================================
# CORE COMPONENTS: Transaction, Database
# =============================================================================

class TransactionState(Enum):
    ACTIVE = "ACTIVE"
    COMMITTED = "COMMITTED"
    ABORTED = "ABORTED"


@dataclass
class DataVersion:
    value: Any
    created_by_txn: int
    version_number: int = 0


class Transaction:
    _next_id = 1

    def __init__(self):
        self.txn_id = Transaction._next_id
        Transaction._next_id += 1
        self.state = TransactionState.ACTIVE
        self.read_set: Dict[str, Any] = {}
        self.write_set: Dict[str, Any] = {}
        self.locked_items: Dict[str, int] = {}  # item_id -> version_number

    def is_active(self) -> bool:
        return self.state == TransactionState.ACTIVE

    def commit(self):
        self.state = TransactionState.COMMITTED

    def abort(self):
        self.state = TransactionState.ABORTED

    def __repr__(self):
        return f"Txn{self.txn_id}"


class LostUpdateDatabase:
    """Database demonstrating lost update problem and solutions."""

    def __init__(self):
        self.data: Dict[str, DataVersion] = {}
        self.transactions: Dict[int, Transaction] = {}
        self.locks: Dict[str, Optional[int]] = {}  # item_id -> txn_id holding lock
        self.operation_log: List[str] = []

    def begin_transaction(self) -> Transaction:
        txn = Transaction()
        self.transactions[txn.txn_id] = txn
        self._log(f"BEGIN {txn}")
        return txn

    def read(self, txn: Transaction, item_id: str) -> Optional[Any]:
        if not txn.is_active():
            raise ValueError(f"{txn} is not active")

        if item_id not in self.data:
            self._log(f"  {txn} READ {item_id} = None")
            return None

        value = self.data[item_id].value
        version = self.data[item_id].version_number
        txn.read_set[item_id] = (value, version)
        self._log(f"  {txn} READ {item_id} = {value} (version {version})")
        return value

    def write(self, txn: Transaction, item_id: str, value: Any):
        if not txn.is_active():
            raise ValueError(f"{txn} is not active")

        if item_id not in self.data:
            self.data[item_id] = DataVersion(value, txn.txn_id, 0)
        else:
            self.data[item_id].value = value
            self.data[item_id].created_by_txn = txn.txn_id
            self.data[item_id].version_number += 1

        txn.write_set[item_id] = value
        self._log(f"  {txn} WRITE {item_id} = {value}")

    def commit_transaction(self, txn: Transaction):
        if not txn.is_active():
            raise ValueError(f"{txn} is not active")

        txn.commit()
        self._log(f"COMMIT {txn}")

    def abort_transaction(self, txn: Transaction):
        if not txn.is_active():
            raise ValueError(f"{txn} is not active")

        txn.abort()
        self._log(f"ABORT {txn}")

    def _log(self, message: str):
        self.operation_log.append(message)
        print(message)


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


def demo_1_lost_update_problem():
    """
    Demo 1: Show the lost update problem.

    DDIA concept: "A Lost Update can occur when two transactions
    perform a read-modify-write cycle concurrently, and one
    overwrites the other's change."
    """
    print_header("DEMO 1: The Lost Update Problem")
    print("""
    Scenario: Two transactions increment a counter.
    Both read the same value, increment it, and write back.
    One increment is LOST.
    """)

    db = LostUpdateDatabase()

    # Initialize counter
    txn_init = db.begin_transaction()
    db.write(txn_init, "counter", 0)
    db.commit_transaction(txn_init)

    print_section("Initial State")
    print(f"  counter = 0")

    # Transaction A: Read-modify-write
    print_section("Transaction A: Increment counter")
    txn_a = db.begin_transaction()
    value_a = db.read(txn_a, "counter")
    print(f"  {txn_a} increments: {value_a} + 1 = {value_a + 1}")
    db.write(txn_a, "counter", value_a + 1)

    # Transaction B: Read-modify-write (reads same initial value!)
    print_section("Transaction B: Increment counter")
    txn_b = db.begin_transaction()
    value_b = db.read(txn_b, "counter")
    print(f"  {txn_b} increments: {value_b} + 1 = {value_b + 1}")
    db.write(txn_b, "counter", value_b + 1)

    # Commit both
    print_section("Commit both transactions")
    db.commit_transaction(txn_a)
    db.commit_transaction(txn_b)

    print_section("Final State")
    final_value = db.data["counter"].value
    print(f"  counter = {final_value}")
    print(f"  ❌ WRONG! Should be 2, but is {final_value}")
    print(f"     One increment was LOST!")

    print("""
  💡 KEY INSIGHT (DDIA):
     Lost update occurs because:
       1. Both txns read counter = 0
       2. Txn A writes counter = 1
       3. Txn B writes counter = 1 (overwrites A's write!)
       4. Result: counter = 1 (should be 2)

     This happens under both Read Committed and Snapshot Isolation!
    """)


def demo_2_atomic_operations():
    """
    Demo 2: Show how atomic operations prevent lost updates.

    DDIA concept: "Atomic Operations (Best): UPDATE counters SET
    value = value + 1 WHERE key = 'foo'; This is a single atomic
    instruction that the database executes internally."
    """
    print_header("DEMO 2: Solution 1 — Atomic Operations")
    print("""
    Instead of read-modify-write in the application,
    use a single atomic database operation.
    """)

    db = LostUpdateDatabase()

    # Initialize counter
    txn_init = db.begin_transaction()
    db.write(txn_init, "counter", 0)
    db.commit_transaction(txn_init)

    print_section("Initial State")
    print(f"  counter = 0")

    # Atomic increment (simulated)
    print_section("Atomic Increment (simulated)")
    print(f"  UPDATE counter SET value = value + 1")
    print(f"  (Database executes this atomically, no interleaving)")

    # Simulate two concurrent atomic increments
    current = db.data["counter"].value
    db.data["counter"].value = current + 1
    db.data["counter"].version_number += 1
    print(f"  After increment 1: counter = {db.data['counter'].value}")

    current = db.data["counter"].value
    db.data["counter"].value = current + 1
    db.data["counter"].version_number += 1
    print(f"  After increment 2: counter = {db.data['counter'].value}")

    print_section("Final State")
    print(f"  counter = {db.data['counter'].value}")
    print(f"  ✅ CORRECT! Both increments were applied")

    print("""
  💡 KEY INSIGHT (DDIA):
     Atomic operations:
       ✅ Best solution when applicable
       ✅ No application-level coordination needed
       ✅ Database handles concurrency internally
       ❌ Only works for specific operations (increment, append, etc.)
       ❌ Not applicable for complex business logic
    """)


def demo_3_explicit_locking():
    """
    Demo 3: Show how explicit locking prevents lost updates.

    DDIA concept: "Explicit Locking (SELECT ... FOR UPDATE):
    The FOR UPDATE clause tells the database to lock the selected rows."
    """
    print_header("DEMO 3: Solution 2 — Explicit Locking (SELECT ... FOR UPDATE)")
    print("""
    Use SELECT ... FOR UPDATE to acquire a lock before reading.
    This prevents other transactions from modifying the value.
    """)

    print_section("Pseudocode")
    print("""
    BEGIN;
    SELECT * FROM counter WHERE id = 1 FOR UPDATE;  -- Acquire lock!
    -- Application logic: read value, increment
    UPDATE counter SET value = value + 1 WHERE id = 1;
    COMMIT;
    """)

    print_section("Execution Timeline")
    print("""
    Transaction A:                    Transaction B:
      BEGIN;
      SELECT ... FOR UPDATE;            BEGIN;
      (acquires lock)                   SELECT ... FOR UPDATE;
                                        (BLOCKED, waiting for lock)
      UPDATE counter SET value = 1;
      COMMIT;
      (releases lock)
                                        (now acquires lock)
                                        UPDATE counter SET value = 2;
                                        COMMIT;
    """)

    print_section("Result")
    print(f"  counter = 2")
    print(f"  ✅ CORRECT! Both increments were applied in order")

    print("""
  💡 KEY INSIGHT (DDIA):
     Explicit locking:
       ✅ Prevents lost updates
       ✅ Works for any business logic
       ❌ Requires application code changes
       ❌ Can cause deadlocks if not careful
       ❌ Performance impact (blocking)
    """)


def demo_4_compare_and_set():
    """
    Demo 4: Show Compare-and-Set for systems without transactions.

    DDIA concept: "Compare-and-Set (CAS): Used in databases that
    don't provide transactions (like many NoSQL databases)."
    """
    print_header("DEMO 4: Solution 3 — Compare-and-Set (CAS)")
    print("""
    For systems without transactions, use CAS:
    UPDATE table SET value = new_value
    WHERE id = 1 AND value = old_value;  -- Only update if unchanged!
    """)

    print_section("Pseudocode")
    print("""
    old_value = read(key);
    new_value = old_value + 1;
    success = update(key, new_value, expected=old_value);
    if not success:
        retry();  -- Another txn modified the value, retry
    """)

    print_section("Execution Timeline")
    print("""
    Transaction A:                    Transaction B:
      old_value = 0
      new_value = 1
      UPDATE WHERE value = 0
      (succeeds, writes 1)
                                      old_value = 0
                                      new_value = 1
                                      UPDATE WHERE value = 0
                                      (FAILS! value is now 1)
                                      retry();
                                      old_value = 1
                                      new_value = 2
                                      UPDATE WHERE value = 1
                                      (succeeds, writes 2)
    """)

    print_section("Result")
    print(f"  counter = 2")
    print(f"  ✅ CORRECT! Both increments were applied")

    print("""
  💡 KEY INSIGHT (DDIA):
     Compare-and-Set:
       ✅ Works for systems without transactions
       ✅ Detects conflicts automatically
       ❌ Requires retry logic in application
       ❌ Can cause livelock under high contention
       ✅ Used by many NoSQL databases (Cassandra, DynamoDB, etc.)
    """)


def demo_5_automatic_detection():
    """
    Demo 5: Show automatic conflict detection.

    DDIA concept: "Some databases (PostgreSQL, Oracle, SQL Server
    with Snapshot Isolation) can automatically detect when a Lost
    Update has occurred."
    """
    print_header("DEMO 5: Solution 4 — Automatic Conflict Detection")
    print("""
    Some databases automatically detect lost updates and abort
    one of the conflicting transactions.
    """)

    print_section("How It Works")
    print("""
    Under Snapshot Isolation with automatic detection:

    Transaction A:                    Transaction B:
      BEGIN;
      READ counter = 0
      WRITE counter = 1
      COMMIT;
      (succeeds)
                                      BEGIN;
                                      READ counter = 0
                                      WRITE counter = 1
                                      COMMIT;
                                      (CONFLICT DETECTED!)
                                      (Txn B is aborted)
    """)

    print_section("Result")
    print(f"  counter = 1")
    print(f"  ✅ CORRECT! Txn B is aborted and can retry")

    print("""
  💡 KEY INSIGHT (DDIA):
     Automatic conflict detection:
       ✅ Transparent to application
       ✅ Prevents lost updates automatically
       ❌ Requires retry logic in application
       ✅ Used by PostgreSQL, Oracle, SQL Server
    """)


def demo_6_comparison():
    """
    Demo 6: Compare all solutions.
    """
    print_header("DEMO 6: Comparison of Lost Update Solutions")
    print("""
    Comparison of different approaches.
    """)

    print_section("Solution Comparison")
    print(f"""
  {'Solution':<25} {'Pros':<30} {'Cons'}
  {'─'*80}
  {'Atomic operations':<25} {'Simple, fast':<30} {'Limited to specific ops'}
  {'Explicit locking':<25} {'General purpose':<30} {'Blocking, deadlocks'}
  {'Compare-and-set':<25} {'Works without txns':<30} {'Retry logic needed'}
  {'Auto-detection':<25} {'Transparent':<30} {'Retry logic needed'}
    """)

    print("""
  💡 DDIA RECOMMENDATION:
     Choose based on your database:

     PostgreSQL/Oracle/SQL Server:
       → Use automatic conflict detection (Snapshot Isolation)
       → Or use explicit locking (SELECT ... FOR UPDATE)

     MySQL InnoDB:
       → Use explicit locking (SELECT ... FOR UPDATE)

     NoSQL (Cassandra, DynamoDB):
       → Use Compare-and-Set
       → Or use atomic operations if available

     Redis:
       → Use Lua scripts (atomic)
       → Or use WATCH/MULTI/EXEC (optimistic locking)
    """)


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 80)
    print("  EXERCISE 3: LOST UPDATES — CONCURRENT READ-MODIFY-WRITE")
    print("  DDIA Chapter 7: 'Weak Isolation Levels'")
    print("=" * 80)
    print("""
  This exercise demonstrates the LOST UPDATE problem.
  You'll see how concurrent read-modify-write cycles can lose updates,
  and learn four solutions to prevent this.
    """)

    demo_1_lost_update_problem()
    demo_2_atomic_operations()
    demo_3_explicit_locking()
    demo_4_compare_and_set()
    demo_5_automatic_detection()
    demo_6_comparison()

    print("\n" + "=" * 80)
    print("  EXERCISE 3 COMPLETE ✅")
    print("=" * 80)
    print("""
  Key Takeaways:

  1. 🔄 LOST UPDATE: concurrent read-modify-write overwrites changes
  2. ⚛️  ATOMIC OPERATIONS: best solution when applicable
  3. 🔒 EXPLICIT LOCKING: SELECT ... FOR UPDATE
  4. 🔀 COMPARE-AND-SET: for systems without transactions
  5. 🤖 AUTOMATIC DETECTION: PostgreSQL, Oracle, SQL Server
  6. ⚠️  Both Read Committed and Snapshot Isolation allow lost updates

  Next: Run 04_write_skew.py to see the phantom problem
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
