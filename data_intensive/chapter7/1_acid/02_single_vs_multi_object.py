"""
Exercise 1b: Single-Object vs. Multi-Object Transactions

DDIA Reference: Chapter 7, "Single-Object vs. Multi-Object Operations" (pp. 245-250)

This exercise demonstrates the difference between single-object and multi-object
transactions, and why multi-object transactions are needed.

Key concepts:
  - Single-object writes: Basic atomicity and isolation
  - Multi-object transactions: Keeping multiple objects in sync
  - Foreign key constraints: Maintaining referential integrity
  - Secondary indexes: Keeping indexes in sync with data
  - Error handling and retries: Idempotency and exponential backoff

Run: python 02_single_vs_multi_object.py
"""

import sys
import time
import random
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

# Fix Windows terminal encoding for Unicode output
sys.stdout.reconfigure(encoding='utf-8')


# =============================================================================
# CORE COMPONENTS: Transaction, Database with Multi-Object Support
# =============================================================================

class TransactionState(Enum):
    """States a transaction can be in."""
    PENDING = "pending"
    COMMITTED = "committed"
    ABORTED = "aborted"


class ErrorType(Enum):
    """Types of errors that can occur."""
    TRANSIENT = "transient"  # Retry-able (e.g., deadlock, network timeout)
    PERMANENT = "permanent"  # Not retry-able (e.g., constraint violation)


@dataclass
class WriteOperation:
    """A single write operation within a transaction."""
    table: str
    key: str
    value: Any
    timestamp: float = field(default_factory=time.time)

    def __repr__(self):
        return f"Write({self.table}.{self.key}={self.value})"


@dataclass
class Transaction:
    """A multi-object transaction."""
    txn_id: int
    operations: List[WriteOperation] = field(default_factory=list)
    state: TransactionState = TransactionState.PENDING
    start_time: float = field(default_factory=time.time)
    commit_time: Optional[float] = None

    def add_write(self, table: str, key: str, value: Any):
        """Add a write operation to this transaction."""
        self.operations.append(WriteOperation(table, key, value))

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


class MultiObjectDatabase:
    """
    A database with support for multi-object transactions.

    DDIA: "Multi-object transactions are needed when several objects
    need to be kept in sync."
    """

    def __init__(self):
        # Multiple tables
        self.tables: Dict[str, Dict[str, Any]] = {}

        # Secondary indexes: table -> {index_name -> {value -> [keys]}}
        self.indexes: Dict[str, Dict[str, Dict[Any, List[str]]]] = {}

        # Foreign key constraints: (table, column) -> (ref_table, ref_column)
        self.foreign_keys: Dict[Tuple[str, str], Tuple[str, str]] = {}

        # Active transactions
        self.active_transactions: Dict[int, Transaction] = {}
        self.next_txn_id = 1

    def create_table(self, table_name: str):
        """Create a new table."""
        self.tables[table_name] = {}
        self.indexes[table_name] = {}

    def create_index(self, table_name: str, index_name: str, column: str):
        """Create a secondary index on a table."""
        if table_name not in self.indexes:
            self.indexes[table_name] = {}
        self.indexes[table_name][index_name] = {}

    def add_foreign_key(self, table: str, column: str, ref_table: str, ref_column: str):
        """Add a foreign key constraint."""
        self.foreign_keys[(table, column)] = (ref_table, ref_column)

    def begin_transaction(self) -> Transaction:
        """Start a new transaction."""
        txn_id = self.next_txn_id
        self.next_txn_id += 1
        txn = Transaction(txn_id)
        self.active_transactions[txn_id] = txn
        return txn

    def write(self, txn: Transaction, table: str, key: str, value: Any):
        """Write a value within a transaction."""
        if txn.is_aborted():
            raise RuntimeError(f"Cannot write to aborted transaction {txn.txn_id}")

        txn.add_write(table, key, value)

    def commit(self, txn: Transaction):
        """
        Commit a multi-object transaction.

        DDIA: "Either ALL writes are applied, or NONE are."
        """
        if txn.is_aborted():
            raise RuntimeError(f"Cannot commit aborted transaction {txn.txn_id}")

        # Apply all writes atomically
        for operation in txn.operations:
            table = operation.table
            key = operation.key
            value = operation.value

            if table not in self.tables:
                self.tables[table] = {}

            self.tables[table][key] = value

        # Mark transaction as committed
        txn.commit()
        del self.active_transactions[txn.txn_id]

    def read(self, table: str, key: str) -> Optional[Any]:
        """Read a value from a table."""
        if table not in self.tables:
            return None
        return self.tables[table].get(key)

    def read_all(self, table: str) -> Dict[str, Any]:
        """Read all rows from a table."""
        return self.tables.get(table, {}).copy()

    def abort(self, txn: Transaction):
        """Abort a transaction."""
        txn.abort()
        del self.active_transactions[txn.txn_id]

    def __repr__(self):
        return f"Database({len(self.tables)} tables, {len(self.active_transactions)} active txns)"


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


def demo_1_single_object_writes():
    """
    Demo 1: Single-object writes with basic atomicity.

    DDIA concept: "Most databases provide single-object guarantees
    by default. These are NOT transactions in the ACID sense, though.
    They are just basic safety features."
    """
    print_header("DEMO 1: Single-Object Writes")
    print("""
    Scenario: Writing a single JSON document to the database.

    Single-object writes have basic atomicity and isolation:
      • Atomicity: The document is either fully written or not at all
      • Isolation: Other transactions can't see half-written documents
    """)

    db = MultiObjectDatabase()
    db.create_table("documents")

    print(f"  📝 Writing a single document...")

    # Single-object write (no transaction needed)
    document = {
        "id": 1,
        "title": "Hello World",
        "content": "This is a test document",
        "author": "Alice"
    }

    db.tables["documents"][1] = document

    print(f"    Document written: {document}")

    # Read it back
    read_doc = db.read("documents", 1)
    print(f"    Document read back: {read_doc}")

    print(f"""
  💡 KEY INSIGHT (DDIA):
     Single-object writes have basic atomicity:
       • If the database crashes during the write, the document is either
         fully written or not at all (no half-written documents)
       • This is implemented using a Write-Ahead Log (WAL)

     However, this is NOT a transaction in the ACID sense.
     It's just a basic safety feature.
    """)


def demo_2_multi_object_foreign_keys():
    """
    Demo 2: Multi-object transactions for foreign key constraints.

    DDIA concept: "Multi-object transactions are needed when several
    objects need to be kept in sync."
    """
    print_header("DEMO 2: Multi-Object Transactions — Foreign Keys")
    print("""
    Scenario: Insert a new user and create a profile for them.

    Without multi-object transactions:
      • Insert user in 'users' table
      • Insert profile in 'profiles' table
      • If crash between the two, we have a user with no profile!

    With multi-object transactions:
      • Both inserts happen atomically
      • Either both succeed or both fail
    """)

    db = MultiObjectDatabase()
    db.create_table("users")
    db.create_table("profiles")

    # Add foreign key constraint
    db.add_foreign_key("profiles", "user_id", "users", "id")

    print(f"  📋 Initial state:")
    print(f"    Users: {db.read_all('users')}")
    print(f"    Profiles: {db.read_all('profiles')}")

    # Multi-object transaction
    print(f"\n  💳 Transaction: Create user and profile")
    txn = db.begin_transaction()

    # Write to users table
    db.write(txn, "users", "user_1", {
        "id": "user_1",
        "name": "Alice",
        "email": "alice@example.com"
    })

    # Write to profiles table
    db.write(txn, "profiles", "profile_1", {
        "id": "profile_1",
        "user_id": "user_1",
        "bio": "Software engineer",
        "avatar": "alice.jpg"
    })

    # Commit atomically
    print(f"  ✅ Committing transaction...")
    db.commit(txn)

    print(f"\n  📋 After transaction:")
    print(f"    Users: {db.read_all('users')}")
    print(f"    Profiles: {db.read_all('profiles')}")

    print(f"""
  💡 KEY INSIGHT (DDIA):
     The user and profile were created atomically.
     If the database crashed between the two writes, both would be rolled back.

     This maintains the foreign key constraint:
       • Every profile has a corresponding user
       • No orphaned profiles
    """)


def demo_3_multi_object_secondary_indexes():
    """
    Demo 3: Multi-object transactions for secondary indexes.

    DDIA concept: "When you update a value, the secondary index needs
    to be updated too. Without transactions, the index might be updated
    but the value might not (or vice versa)."
    """
    print_header("DEMO 3: Multi-Object Transactions — Secondary Indexes")
    print("""
    Scenario: Update a user's email address.

    The email is indexed for fast lookups. When we update the email:
      1. Update the 'users' table
      2. Update the 'email_index' (secondary index)

    Without multi-object transactions:
      • Update users table
      • Crash before updating index
      • Index is stale (points to old email)

    With multi-object transactions:
      • Both updates happen atomically
      • Index is always consistent with data
    """)

    db = MultiObjectDatabase()
    db.create_table("users")
    db.create_index("users", "email_index", "email")

    # Initial data
    db.tables["users"]["user_1"] = {
        "id": "user_1",
        "name": "Alice",
        "email": "alice@example.com"
    }

    # Manually create index entry
    db.indexes["users"]["email_index"]["alice@example.com"] = ["user_1"]

    print(f"  📋 Initial state:")
    print(f"    User: {db.read('users', 'user_1')}")
    print(f"    Email index: {db.indexes['users']['email_index']}")

    # Multi-object transaction: Update email
    print(f"\n  💳 Transaction: Update user's email")
    txn = db.begin_transaction()

    # Update users table
    db.write(txn, "users", "user_1", {
        "id": "user_1",
        "name": "Alice",
        "email": "alice.new@example.com"
    })

    # Update index (simulated as a write to a special index table)
    db.write(txn, "_index_email", "alice.new@example.com", ["user_1"])

    # Commit atomically
    print(f"  ✅ Committing transaction...")
    db.commit(txn)

    print(f"\n  📋 After transaction:")
    print(f"    User: {db.read('users', 'user_1')}")
    print(f"    Index entry: {db.read('_index_email', 'alice.new@example.com')}")

    print(f"""
  💡 KEY INSIGHT (DDIA):
     The user data and index were updated atomically.
     The index is always consistent with the data.

     Without multi-object transactions, the index could become stale:
       • Index points to old email
       • Queries using the index would fail
    """)


def demo_4_error_handling_retries():
    """
    Demo 4: Error handling and retries.

    DDIA concept: "Retrying is not as simple as it looks."
    """
    print_header("DEMO 4: Error Handling and Retries")
    print("""
    Scenario: Retry a failed transaction.

    Challenges:
      1. Idempotency: If the transaction succeeded but the network failed,
         retrying would execute it twice (e.g., charge credit card twice)
      2. Exponential backoff: If the error is due to overload, retrying
         makes the problem worse
      3. Transient vs. permanent errors: Only retry transient errors
    """)

    db = MultiObjectDatabase()
    db.create_table("accounts")

    # Initial state
    db.tables["accounts"]["account_1"] = {"id": "account_1", "balance": 1000}

    print(f"  💳 Scenario: Transfer $100 from account_1 to account_2")
    print(f"    Initial balance: ${db.read('accounts', 'account_1')['balance']}")

    # Attempt 1: Transient error (deadlock)
    print(f"\n  Attempt 1: Transient error (deadlock)")
    print(f"    ❌ Transaction failed with deadlock")
    print(f"    → This is a TRANSIENT error, retry is safe")

    # Attempt 2: Retry with exponential backoff
    print(f"\n  Attempt 2: Retry after exponential backoff")
    print(f"    ⏳ Waiting 100ms before retry...")
    time.sleep(0.1)

    txn = db.begin_transaction()
    db.write(txn, "accounts", "account_1", {"id": "account_1", "balance": 900})
    db.write(txn, "accounts", "account_2", {"id": "account_2", "balance": 100})
    db.commit(txn)

    print(f"    ✅ Transaction succeeded")
    print(f"    Final balance: ${db.read('accounts', 'account_1')['balance']}")

    # Attempt 3: Permanent error (constraint violation)
    print(f"\n  Attempt 3: Permanent error (constraint violation)")
    print(f"    ❌ Transaction failed: Insufficient funds")
    print(f"    → This is a PERMANENT error, retrying won't help")

    print(f"""
  💡 KEY INSIGHT (DDIA):
     Retrying is not as simple as it looks:

     1. IDEMPOTENCY: If the transaction succeeded but the network failed,
        retrying would execute it twice. You need idempotent operations.

     2. EXPONENTIAL BACKOFF: If the error is due to overload, retrying
        immediately makes the problem worse. Use exponential backoff.

     3. TRANSIENT vs. PERMANENT:
        • Transient errors (deadlock, network timeout): Retry is safe
        • Permanent errors (constraint violation): Retrying won't help

     Best practice:
       • Retry only on transient errors
       • Use exponential backoff
       • Ensure operations are idempotent
    """)


def demo_5_single_vs_multi_comparison():
    """
    Demo 5: Compare single-object and multi-object transactions.

    DDIA concept: "Single-object writes are simple but insufficient
    for maintaining consistency across multiple objects."
    """
    print_header("DEMO 5: Single-Object vs. Multi-Object Transactions")
    print("""
    DDIA describes the differences and trade-offs.
    """)

    print("""
    ┌─────────────────────────────────────────────────────────────────┐
    │ SINGLE-OBJECT WRITES                                            │
    ├─────────────────────────────────────────────────────────────────┤
    │                                                                  │
    │ Definition:                                                      │
    │   Atomicity and isolation for a single object (row, document).   │
    │                                                                  │
    │ Implementation:                                                  │
    │   Write-Ahead Log (WAL): Ensures atomicity                       │
    │   Locking: Ensures isolation                                     │
    │                                                                  │
    │ Pros:                                                            │
    │   • Simple to implement                                          │
    │   • Fast (no coordination overhead)                              │
    │   • Most databases provide this by default                       │
    │                                                                  │
    │ Cons:                                                            │
    │   • Can't maintain consistency across multiple objects           │
    │   • Foreign key constraints can be violated                      │
    │   • Secondary indexes can become stale                           │
    │                                                                  │
    │ Use case:                                                        │
    │   • Simple updates to a single row/document                      │
    │   • No dependencies on other objects                             │
    └─────────────────────────────────────────────────────────────────┘
    """)

    print("""
    ┌─────────────────────────────────────────────────────────────────┐
    │ MULTI-OBJECT TRANSACTIONS                                       │
    ├─────────────────────────────────────────────────────────────────┤
    │                                                                  │
    │ Definition:                                                      │
    │   Atomicity and isolation for multiple objects.                  │
    │   All writes succeed or all fail.                                │
    │                                                                  │
    │ Implementation:                                                  │
    │   Two-Phase Commit (2PC): Coordinates across multiple objects    │
    │   Locking: Locks all objects involved                            │
    │   MVCC: Multiple versions for isolation                          │
    │                                                                  │
    │ Pros:                                                            │
    │   • Maintains consistency across multiple objects                │
    │   • Foreign key constraints are enforced                         │
    │   • Secondary indexes stay in sync                               │
    │   • Application can safely retry on failure                      │
    │                                                                  │
    │ Cons:                                                            │
    │   • More complex to implement                                    │
    │   • Slower (coordination overhead)                               │
    │   • Risk of deadlocks                                            │
    │   • Reduced concurrency (more locking)                           │
    │                                                                  │
    │ Use case:                                                        │
    │   • Updates that span multiple tables                            │
    │   • Maintaining foreign key constraints                          │
    │   • Keeping indexes in sync                                      │
    │   • Any operation that must maintain invariants                  │
    └─────────────────────────────────────────────────────────────────┘
    """)

    print("""
    ┌─────────────────────────────────────────────────────────────────┐
    │ COMPARISON TABLE                                                │
    ├──────────────────────┬──────────────┬──────────────────────────┤
    │ Aspect               │ Single-Obj   │ Multi-Object             │
    ├──────────────────────┼──────────────┼──────────────────────────┤
    │ Scope                │ One object   │ Multiple objects         │
    │ Complexity           │ Simple       │ Complex                  │
    │ Performance          │ Fast         │ Slower                   │
    │ Consistency          │ Limited      │ Strong                   │
    │ Foreign keys         │ Not enforced │ Enforced                 │
    │ Index consistency    │ Not guaranteed│ Guaranteed              │
    │ Deadlock risk        │ None         │ Possible                 │
    │ Concurrency          │ High         │ Lower                    │
    └──────────────────────┴──────────────┴──────────────────────────┘
    """)


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 80)
    print("  EXERCISE 1b: SINGLE-OBJECT vs. MULTI-OBJECT TRANSACTIONS")
    print("  DDIA Chapter 7: 'Single-Object vs. Multi-Object Operations'")
    print("=" * 80)
    print("""
  This exercise demonstrates the difference between single-object and
  multi-object transactions, and why multi-object transactions are needed.

  Single-object writes have basic atomicity and isolation, but they can't
  maintain consistency across multiple objects. Multi-object transactions
  are needed for:
    • Foreign key constraints
    • Secondary indexes
    • Denormalized documents
    • Any operation that must maintain invariants
    """)

    demo_1_single_object_writes()
    demo_2_multi_object_foreign_keys()
    demo_3_multi_object_secondary_indexes()
    demo_4_error_handling_retries()
    demo_5_single_vs_multi_comparison()

    print("\n" + "=" * 80)
    print("  EXERCISE 1b COMPLETE ✅")
    print("=" * 80)
    print("""
  Key Takeaways:

  1. 📝 SINGLE-OBJECT WRITES: Basic atomicity and isolation
     → Implemented via WAL and locking
     → Fast but can't maintain consistency across objects

  2. 🔗 MULTI-OBJECT TRANSACTIONS: Atomicity across multiple objects
     → Needed for foreign keys, indexes, denormalized data
     → Slower but maintains consistency

  3. 🔄 ERROR HANDLING: Retrying is not simple
     → Idempotency: Avoid executing twice
     → Exponential backoff: Don't overload the system
     → Transient vs. permanent errors: Only retry transient

  4. ⚖️  TRADE-OFFS: Consistency vs. Performance
     → Single-object: Fast but limited consistency
     → Multi-object: Slower but strong consistency

  5. 🏗️  DESIGN DECISION: Choose based on your needs
     → Simple updates: Single-object writes
     → Complex operations: Multi-object transactions

  Next: Run 03_isolation_levels.py to learn about weak isolation levels
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
