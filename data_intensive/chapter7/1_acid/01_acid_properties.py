"""
Exercise 1: The Meaning of ACID — Transaction Safety Guarantees

DDIA Reference: Chapter 7, "The Meaning of ACID" (pp. 223-245)

This exercise simulates the four ACID properties and demonstrates why they matter.

Key concepts:
  - Atomicity: All-or-nothing writes (no partial updates)
  - Consistency: Application invariants are maintained
  - Isolation: Concurrent transactions don't interfere
  - Durability: Committed data survives crashes

Run: python 01_acid_properties.py
"""

import sys
import time
import random
import threading
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

# Fix Windows terminal encoding for Unicode output
sys.stdout.reconfigure(encoding='utf-8')


# =============================================================================
# CORE COMPONENTS: Transaction, Database, WAL
# =============================================================================

class TransactionState(Enum):
    """States a transaction can be in."""
    PENDING = "pending"
    COMMITTED = "committed"
    ABORTED = "aborted"


@dataclass
class WriteOperation:
    """A single write operation within a transaction."""
    key: str
    value: Any
    timestamp: float = field(default_factory=time.time)

    def __repr__(self):
        return f"Write({self.key}={self.value})"


@dataclass
class Transaction:
    """
    A transaction: a group of reads and writes executed as one unit.

    DDIA: "A transaction is a way for an application to group several
    reads and writes together into a logical unit. Conceptually, all the
    reads and writes in a transaction are executed as one operation:
    either the entire transaction succeeds (commit) or it fails (abort)."
    """
    txn_id: int
    operations: List[WriteOperation] = field(default_factory=list)
    state: TransactionState = TransactionState.PENDING
    start_time: float = field(default_factory=time.time)
    commit_time: Optional[float] = None

    def add_write(self, key: str, value: Any):
        """Add a write operation to this transaction."""
        self.operations.append(WriteOperation(key, value))

    def commit(self):
        """Mark this transaction as committed."""
        self.state = TransactionState.COMMITTED
        self.commit_time = time.time()

    def abort(self):
        """Mark this transaction as aborted."""
        self.state = TransactionState.ABORTED

    def is_committed(self) -> bool:
        return self.state == TransactionState.COMMITTED

    def is_aborted(self) -> bool:
        return self.state == TransactionState.ABORTED

    def __repr__(self):
        return f"Txn({self.txn_id}, {self.state.value}, ops={len(self.operations)})"


class WriteAheadLog:
    """
    Write-Ahead Log (WAL): The mechanism for durability and atomicity.

    DDIA: "Before a transaction is committed, all its writes are first
    written to a log on disk. If the database crashes, the log can be
    replayed to recover the committed transactions."
    """

    def __init__(self):
        self.entries: List[Tuple[int, WriteOperation]] = []  # (txn_id, operation)
        self.committed_txns: set = set()

    def log_write(self, txn_id: int, operation: WriteOperation):
        """Log a write operation (before it's applied to the database)."""
        self.entries.append((txn_id, operation))

    def log_commit(self, txn_id: int):
        """Log that a transaction has committed."""
        self.committed_txns.add(txn_id)

    def get_committed_writes(self) -> List[Tuple[int, WriteOperation]]:
        """Get all writes from committed transactions."""
        return [(txn_id, op) for txn_id, op in self.entries if txn_id in self.committed_txns]

    def __repr__(self):
        return f"WAL({len(self.entries)} entries, {len(self.committed_txns)} committed)"


class Database:
    """
    A simple in-memory database with ACID transaction support.

    DDIA: "The database takes care of safety guarantees so the
    application is free to ignore certain error scenarios."
    """

    def __init__(self):
        self.data: Dict[str, Any] = {}
        self.wal = WriteAheadLog()
        self.active_transactions: Dict[int, Transaction] = {}
        self.next_txn_id = 1
        self.lock = threading.Lock()

        # For crash simulation
        self.crashed = False
        self.crash_after_writes = None  # Crash after N writes

    def begin_transaction(self) -> Transaction:
        """Start a new transaction."""
        txn_id = self.next_txn_id
        self.next_txn_id += 1
        txn = Transaction(txn_id)
        self.active_transactions[txn_id] = txn
        return txn

    def write(self, txn: Transaction, key: str, value: Any):
        """
        Write a value within a transaction.

        DDIA Atomicity: "The write is first logged to the WAL,
        then applied to the database. If the database crashes,
        the WAL can be replayed."
        """
        if txn.is_aborted():
            raise RuntimeError(f"Cannot write to aborted transaction {txn.txn_id}")

        operation = WriteOperation(key, value)
        txn.add_write(key, value)

        # Log the write (for durability)
        self.wal.log_write(txn.txn_id, operation)

        # Simulate crash during writes
        if self.crash_after_writes is not None:
            self.crash_after_writes -= 1
            if self.crash_after_writes == 0:
                self.crashed = True
                raise RuntimeError("DATABASE CRASHED!")

    def read(self, key: str) -> Optional[Any]:
        """Read a value from the database."""
        return self.data.get(key)

    def commit(self, txn: Transaction):
        """
        Commit a transaction.

        DDIA Atomicity: "Either ALL writes are applied, or NONE are.
        The database guarantees this by using the WAL."
        """
        if txn.is_aborted():
            raise RuntimeError(f"Cannot commit aborted transaction {txn.txn_id}")

        with self.lock:
            # Apply all writes atomically
            for operation in txn.operations:
                self.data[operation.key] = operation.value

            # Log the commit (for durability)
            self.wal.log_commit(txn.txn_id)

            # Mark transaction as committed
            txn.commit()

            # Remove from active transactions
            del self.active_transactions[txn.txn_id]

    def abort(self, txn: Transaction):
        """
        Abort a transaction.

        DDIA Atomicity: "If a transaction is aborted, none of its
        writes are applied. The database rolls back any partial state."
        """
        txn.abort()
        del self.active_transactions[txn.txn_id]

    def recover_from_crash(self):
        """
        Recover from a crash using the WAL.

        DDIA Durability: "If the database crashes, the WAL can be
        replayed to recover all committed transactions."
        """
        self.crashed = False
        self.data.clear()

        # Replay all committed writes from the WAL
        for txn_id, operation in self.wal.get_committed_writes():
            self.data[operation.key] = operation.value

    def __repr__(self):
        return f"Database({len(self.data)} keys, {len(self.active_transactions)} active txns)"


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


def demo_1_atomicity_without_crash():
    """
    Demo 1: Show atomicity in the happy path (no crash).

    DDIA concept: "Atomicity means either ALL writes are applied,
    or NONE are."
    """
    print_header("DEMO 1: Atomicity — Happy Path (No Crash)")
    print("""
    Scenario: Transfer $100 from Account A to Account B.

    Without atomicity, a crash could leave the system in an
    inconsistent state (money lost or duplicated).
    """)

    db = Database()

    # Initial state
    db.data["account_a"] = 500
    db.data["account_b"] = 500

    print(f"  Initial state:")
    print(f"    Account A: ${db.data['account_a']}")
    print(f"    Account B: ${db.data['account_b']}")
    print(f"    Total: ${db.data['account_a'] + db.data['account_b']}")

    # Start transaction
    print(f"\n  💳 Starting transfer transaction...")
    txn = db.begin_transaction()

    # Perform writes
    print(f"    Step 1: Debit $100 from Account A")
    db.write(txn, "account_a", 400)

    print(f"    Step 2: Credit $100 to Account B")
    db.write(txn, "account_b", 600)

    # Commit
    print(f"\n  ✅ Committing transaction...")
    db.commit(txn)

    print(f"\n  Final state:")
    print(f"    Account A: ${db.data['account_a']}")
    print(f"    Account B: ${db.data['account_b']}")
    print(f"    Total: ${db.data['account_a'] + db.data['account_b']}")

    print(f"""
  💡 KEY INSIGHT (DDIA):
     The total is still $1000. Money was neither lost nor created.
     This is because the transaction was ATOMIC — either both writes
     succeeded, or neither would have.
    """)


def demo_2_atomicity_with_crash():
    """
    Demo 2: Show how atomicity protects against crashes.

    DDIA concept: "If the database crashes after completing only
    some writes, those partial changes are rolled back."
    """
    print_header("DEMO 2: Atomicity — With Crash")
    print("""
    Scenario: Transfer $100 from Account A to Account B.
    The database crashes AFTER the first write but BEFORE the commit.

    Without atomicity: Money is lost (Account A debited, Account B not credited).
    With atomicity: The crash is detected, and the partial write is rolled back.
    """)

    db = Database()

    # Initial state
    db.data["account_a"] = 500
    db.data["account_b"] = 500

    print(f"  Initial state:")
    print(f"    Account A: ${db.data['account_a']}")
    print(f"    Account B: ${db.data['account_b']}")
    print(f"    Total: ${db.data['account_a'] + db.data['account_b']}")

    # Start transaction
    print(f"\n  💳 Starting transfer transaction...")
    txn = db.begin_transaction()

    # Perform writes
    print(f"    Step 1: Debit $100 from Account A")
    db.write(txn, "account_a", 400)

    print(f"    Step 2: Credit $100 to Account B")
    db.write(txn, "account_b", 600)

    # Simulate crash before commit
    print(f"\n  💥 DATABASE CRASHES before commit!")
    print(f"    (Writes are in WAL but NOT yet applied to database)")

    # Recover from crash
    print(f"\n  🔧 Recovering from crash...")
    db.recover_from_crash()

    print(f"\n  State after recovery:")
    print(f"    Account A: ${db.data.get('account_a', 'NOT FOUND')}")
    print(f"    Account B: ${db.data.get('account_b', 'NOT FOUND')}")

    print(f"""
  💡 KEY INSIGHT (DDIA):
     Because the transaction was never committed, the writes were
     never applied to the database. The crash left no partial state.

     The database recovered to a consistent state:
     - Either the transaction is fully applied (if it was committed)
     - Or it's fully rolled back (if it wasn't committed)

     This is ATOMICITY: all-or-nothing.
    """)


def demo_3_consistency_invariants():
    """
    Demo 3: Show how consistency maintains application invariants.

    DDIA concept: "Consistency means that if invariants were true
    before the transaction, they will be true after."
    """
    print_header("DEMO 3: Consistency — Maintaining Invariants")
    print("""
    Scenario: Bank transfer with an invariant.

    Invariant: "The sum of all account balances must always equal $1000."

    A transaction must maintain this invariant.
    """)

    db = Database()

    # Initial state (invariant satisfied)
    db.data["account_a"] = 500
    db.data["account_b"] = 500

    print(f"  Initial state (invariant satisfied):")
    print(f"    Account A: ${db.data['account_a']}")
    print(f"    Account B: ${db.data['account_b']}")
    print(f"    Total: ${db.data['account_a'] + db.data['account_b']} ✅ (invariant: sum = $1000)")

    # Transaction 1: Valid transfer (maintains invariant)
    print(f"\n  💳 Transaction 1: Transfer $100 from A to B")
    txn1 = db.begin_transaction()
    db.write(txn1, "account_a", 400)
    db.write(txn1, "account_b", 600)
    db.commit(txn1)

    print(f"    After commit:")
    print(f"      Account A: ${db.data['account_a']}")
    print(f"      Account B: ${db.data['account_b']}")
    print(f"      Total: ${db.data['account_a'] + db.data['account_b']} ✅ (invariant maintained)")

    # Transaction 2: Invalid transfer (would violate invariant)
    print(f"\n  💳 Transaction 2: Try to transfer $200 from A to B")
    print(f"    (This would violate the invariant!)")
    txn2 = db.begin_transaction()
    db.write(txn2, "account_a", 200)  # Would be 200
    db.write(txn2, "account_b", 800)  # Would be 800
    # In a real database, this would be rejected by a constraint
    # For this demo, we'll just show the invariant violation
    print(f"    If committed:")
    print(f"      Account A: $200")
    print(f"      Account B: $800")
    print(f"      Total: $1000 ✅ (invariant still satisfied)")

    print(f"""
  💡 KEY INSIGHT (DDIA):
     Consistency is about maintaining APPLICATION INVARIANTS.

     The database can enforce some invariants (foreign keys, unique constraints),
     but it cannot know the business logic of your application.

     It's the APPLICATION's responsibility to ensure that transactions
     maintain invariants. The database just ensures that if the invariants
     were true before the transaction, they will be true after.
    """)


def demo_4_isolation_concurrent_reads():
    """
    Demo 4: Show isolation preventing dirty reads.

    DDIA concept: "Isolation means concurrent transactions don't
    interfere with each other."
    """
    print_header("DEMO 4: Isolation — Preventing Dirty Reads")
    print("""
    Scenario: Two concurrent transactions.

    Transaction A: Transfers $100 from Account A to Account B
    Transaction B: Reads both accounts

    Without isolation: Transaction B might see a halfway-written state
    (Account A debited but Account B not yet credited).

    With isolation: Transaction B sees either the old state or the new state,
    but never a halfway state.
    """)

    db = Database()

    # Initial state
    db.data["account_a"] = 500
    db.data["account_b"] = 500

    print(f"  Initial state:")
    print(f"    Account A: ${db.data['account_a']}")
    print(f"    Account B: ${db.data['account_b']}")

    # Transaction A: Transfer
    print(f"\n  💳 Transaction A: Transfer $100 from A to B")
    txn_a = db.begin_transaction()
    db.write(txn_a, "account_a", 400)
    print(f"    (After first write, before commit)")

    # Transaction B: Read (should see old values, not dirty reads)
    print(f"\n  📖 Transaction B: Read both accounts")
    print(f"    Account A: ${db.read('account_a')} (sees old value, not dirty read)")
    print(f"    Account B: ${db.read('account_b')} (sees old value, not dirty read)")

    # Complete Transaction A
    print(f"\n  ✅ Transaction A commits")
    db.write(txn_a, "account_b", 600)
    db.commit(txn_a)

    # Transaction B reads again
    print(f"\n  📖 Transaction B: Read both accounts again")
    print(f"    Account A: ${db.read('account_a')} (now sees new value)")
    print(f"    Account B: ${db.read('account_b')} (now sees new value)")

    print(f"""
  💡 KEY INSIGHT (DDIA):
     Transaction B never saw a halfway state where Account A was debited
     but Account B wasn't credited. This is ISOLATION.

     The database ensures that concurrent transactions don't see
     each other's uncommitted changes (dirty reads).
    """)


def demo_5_durability_persistence():
    """
    Demo 5: Show durability persisting committed data.

    DDIA concept: "Durability means committed data survives crashes."
    """
    print_header("DEMO 5: Durability — Persisting Committed Data")
    print("""
    Scenario: Commit a transaction, then crash.

    Without durability: The committed data is lost in the crash.
    With durability: The committed data is recovered from the WAL.
    """)

    db = Database()

    # Initial state
    db.data["account_a"] = 500
    db.data["account_b"] = 500

    print(f"  Initial state:")
    print(f"    Account A: ${db.data['account_a']}")
    print(f"    Account B: ${db.data['account_b']}")

    # Transaction: Transfer
    print(f"\n  💳 Transaction: Transfer $100 from A to B")
    txn = db.begin_transaction()
    db.write(txn, "account_a", 400)
    db.write(txn, "account_b", 600)

    # Commit (writes to WAL)
    print(f"  ✅ Committing transaction...")
    db.commit(txn)

    print(f"    After commit:")
    print(f"      Account A: ${db.data['account_a']}")
    print(f"      Account B: ${db.data['account_b']}")

    # Simulate crash
    print(f"\n  💥 DATABASE CRASHES!")
    print(f"    (In-memory data is lost, but WAL is on disk)")

    # Recover
    print(f"\n  🔧 Recovering from crash...")
    db.recover_from_crash()

    print(f"    After recovery:")
    print(f"      Account A: ${db.data['account_a']}")
    print(f"      Account B: ${db.data['account_b']}")

    print(f"""
  💡 KEY INSIGHT (DDIA):
     Even though the database crashed, the committed data was recovered
     from the Write-Ahead Log (WAL). This is DURABILITY.

     The WAL is written to disk BEFORE the transaction is committed.
     If the database crashes, the WAL can be replayed to recover
     all committed transactions.
    """)


def demo_6_acid_summary():
    """
    Demo 6: Summary of ACID properties and their trade-offs.

    DDIA concept: "ACID provides safety guarantees, but at a cost."
    """
    print_header("DEMO 6: ACID Summary and Trade-Offs")
    print("""
    DDIA describes the four ACID properties and their trade-offs.
    """)

    print("""
    ┌─────────────────────────────────────────────────────────────────┐
    │ ATOMICITY: All-or-Nothing                                       │
    ├─────────────────────────────────────────────────────────────────┤
    │                                                                  │
    │ Definition:                                                      │
    │   Either ALL writes in a transaction are applied, or NONE are.  │
    │   No partial updates.                                            │
    │                                                                  │
    │ Implementation:                                                  │
    │   Write-Ahead Log (WAL): All writes are logged before applied.   │
    │   On crash, the log is replayed to recover committed txns.      │
    │                                                                  │
    │ Benefit:                                                         │
    │   Application can safely retry failed transactions.              │
    │   No need to worry about partial state.                          │
    │                                                                  │
    │ Cost:                                                            │
    │   Logging overhead (writes to disk).                             │
    │   Rollback overhead (undoing partial writes).                    │
    └─────────────────────────────────────────────────────────────────┘
    """)

    print("""
    ┌─────────────────────────────────────────────────────────────────┐
    │ CONSISTENCY: Invariants Maintained                              │
    ├─────────────────────────────────────────────────────────────────┤
    │                                                                  │
    │ Definition:                                                      │
    │   If invariants were true before the transaction, they will     │
    │   be true after. The database moves from one valid state to     │
    │   another valid state.                                           │
    │                                                                  │
    │ Implementation:                                                  │
    │   Application logic: Ensure transactions maintain invariants.    │
    │   Database constraints: Foreign keys, unique constraints, etc.   │
    │                                                                  │
    │ Benefit:                                                         │
    │   Data integrity is maintained.                                  │
    │   No invalid states are possible.                                │
    │                                                                  │
    │ Cost:                                                            │
    │   Application must understand and enforce invariants.            │
    │   Database constraint checking overhead.                         │
    │                                                                  │
    │ IMPORTANT: Consistency is the APPLICATION's responsibility!     │
    │ The database can't know your business logic.                     │
    └─────────────────────────────────────────────────────────────────┘
    """)

    print("""
    ┌─────────────────────────────────────────────────────────────────┐
    │ ISOLATION: Concurrent Transactions Don't Interfere              │
    ├─────────────────────────────────────────────────────────────────┤
    │                                                                  │
    │ Definition:                                                      │
    │   Concurrently executing transactions are isolated from each     │
    │   other. They cannot see each other's uncommitted changes.       │
    │                                                                  │
    │ Implementation:                                                  │
    │   Locking: Transactions lock data they're modifying.             │
    │   MVCC: Multiple versions of data for different transactions.    │
    │                                                                  │
    │ Benefit:                                                         │
    │   No dirty reads, lost updates, or race conditions.              │
    │   Concurrent transactions behave as if they ran serially.        │
    │                                                                  │
    │ Cost:                                                            │
    │   Locking overhead (contention, deadlocks).                      │
    │   Memory overhead (multiple versions).                           │
    │   Performance impact (serialization).                            │
    │                                                                  │
    │ TRADE-OFF: Full serializability is expensive. Most databases     │
    │ use weaker isolation levels for better performance.              │
    └─────────────────────────────────────────────────────────────────┘
    """)

    print("""
    ┌─────────────────────────────────────────────────────────────────┐
    │ DURABILITY: Committed Data Survives Crashes                     │
    ├─────────────────────────────────────────────────────────────────┤
    │                                                                  │
    │ Definition:                                                      │
    │   Once a transaction is committed, its data will not be lost,    │
    │   even if the database crashes.                                  │
    │                                                                  │
    │ Implementation:                                                  │
    │   Write-Ahead Log (WAL): Writes to disk before commit.           │
    │   Replication: Data is replicated to other nodes.                │
    │                                                                  │
    │ Benefit:                                                         │
    │   Data is safe and persistent.                                   │
    │   Can recover from hardware failures.                            │
    │                                                                  │
    │ Cost:                                                            │
    │   Disk I/O overhead (WAL writes).                                │
    │   Network overhead (replication).                                │
    │   Latency (must wait for disk/network).                          │
    │                                                                  │
    │ IMPORTANT: Perfect durability doesn't exist. If all disks        │
    │ in all datacenters are destroyed, no database can save you.      │
    │ Durability is about reducing risk, not eliminating it.           │
    └─────────────────────────────────────────────────────────────────┘
    """)

    print("""
    ┌─────────────────────────────────────────────────────────────────┐
    │ TRADE-OFFS: ACID vs. Performance                                │
    ├─────────────────────────────────────────────────────────────────┤
    │                                                                  │
    │ Full ACID compliance is expensive:                               │
    │   • Logging overhead (atomicity & durability)                    │
    │   • Locking overhead (isolation)                                 │
    │   • Constraint checking (consistency)                            │
    │                                                                  │
    │ Many systems relax ACID guarantees for performance:              │
    │   • NoSQL databases: Weaker consistency (eventual consistency)   │
    │   • Weak isolation levels: Read Committed, Snapshot Isolation    │
    │   • Asynchronous replication: Durability trade-off               │
    │                                                                  │
    │ The choice depends on your workload:                             │
    │   • Financial systems: Need full ACID                            │
    │   • Social media: Can tolerate eventual consistency              │
    │   • Analytics: Can tolerate stale data                           │
    └─────────────────────────────────────────────────────────────────┘
    """)


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 80)
    print("  EXERCISE 1: THE MEANING OF ACID")
    print("  DDIA Chapter 7: 'Transactions'")
    print("=" * 80)
    print("""
  This exercise demonstrates the four ACID properties and why they matter.

  ACID provides safety guarantees for transactions:
    • Atomicity: All-or-nothing writes
    • Consistency: Invariants are maintained
    • Isolation: Concurrent transactions don't interfere
    • Durability: Committed data survives crashes

  We'll simulate each property and show how it protects against failures.
    """)

    demo_1_atomicity_without_crash()
    demo_2_atomicity_with_crash()
    demo_3_consistency_invariants()
    demo_4_isolation_concurrent_reads()
    demo_5_durability_persistence()
    demo_6_acid_summary()

    print("\n" + "=" * 80)
    print("  EXERCISE 1 COMPLETE ✅")
    print("=" * 80)
    print("""
  Key Takeaways:

  1. 🔒 ATOMICITY: All-or-nothing writes (no partial updates)
     → Implemented via Write-Ahead Log (WAL)
     → Allows safe retry on failure

  2. ✅ CONSISTENCY: Application invariants are maintained
     → Application's responsibility, not database's
     → Database enforces constraints (FK, unique, etc.)

  3. 🚫 ISOLATION: Concurrent transactions don't interfere
     → Prevents dirty reads, lost updates, race conditions
     → Trade-off: Full serializability is expensive

  4. 💾 DURABILITY: Committed data survives crashes
     → Implemented via WAL and/or replication
     → Perfect durability doesn't exist

  5. ⚖️  TRADE-OFFS: ACID vs. Performance
     → Full ACID is expensive
     → Many systems relax guarantees for performance
     → Choose based on your workload

  Next: Run 02_isolation_levels.py to learn about weak isolation levels
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
