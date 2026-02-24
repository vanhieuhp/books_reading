"""
Exercise 2: Multi-Object Transactions

DDIA Reference: Chapter 7, "Transactions" (pp. 230-235)

This exercise demonstrates MULTI-OBJECT TRANSACTIONS — coordinating
writes across multiple objects to maintain application invariants.

Key concepts:
  - Single-object atomicity is NOT enough
  - Multi-object transactions keep related data in sync
  - Use cases: foreign keys, denormalized documents, secondary indexes
  - Challenges: coordinating across multiple objects

Real-world scenarios:
  1. Bank transfer: debit one account, credit another
  2. Foreign key: insert row in table A, insert row in table B
  3. Denormalized document: update document and its secondary index
  4. Inventory: decrement stock, increment order count

Run: python 02_multi_object_transactions.py
"""

import sys
import time
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass

sys.stdout.reconfigure(encoding='utf-8')


# =============================================================================
# CORE COMPONENTS: Transaction, MultiObjectDatabase
# =============================================================================

class TransactionState(Enum):
    """State of a transaction."""
    ACTIVE = "active"
    COMMITTED = "committed"
    ABORTED = "aborted"


@dataclass
class WriteOperation:
    """A single write operation in a transaction."""
    object_id: str
    old_value: Any
    new_value: Any

    def __repr__(self):
        return f"Write({self.object_id}: {self.old_value}→{self.new_value})"


class Transaction:
    """
    A multi-object transaction.

    DDIA: "A transaction is a way for an application to group several
    reads and writes together into a logical unit. Conceptually, all the
    reads and writes in a transaction are executed as one operation:
    either the entire transaction succeeds (commit) or it fails (abort)."
    """

    def __init__(self, txn_id: int):
        self.txn_id = txn_id
        self.state = TransactionState.ACTIVE
        self.writes: List[WriteOperation] = []
        self.reads: Dict[str, Any] = {}

    def add_write(self, object_id: str, old_value: Any, new_value: Any):
        """Record a write operation."""
        self.writes.append(WriteOperation(object_id, old_value, new_value))

    def add_read(self, object_id: str, value: Any):
        """Record a read operation."""
        self.reads[object_id] = value

    def commit(self):
        """Commit the transaction."""
        self.state = TransactionState.COMMITTED

    def abort(self):
        """Abort the transaction."""
        self.state = TransactionState.ABORTED

    def __repr__(self):
        return f"Transaction({self.txn_id}, {len(self.writes)} writes, {self.state.value})"


class StoredObject:
    """A single object in the database."""

    def __init__(self, object_id: str, value: Any):
        self.object_id = object_id
        self.value = value
        self.version = 0  # For detecting conflicts

    def __repr__(self):
        return f"Object({self.object_id}={self.value})"


class MultiObjectDatabase:
    """
    A database supporting MULTI-OBJECT TRANSACTIONS.

    DDIA: "Multi-object transactions are needed when several objects
    need to be kept in sync."

    Key challenge: Atomicity across multiple objects.
    Solution: All-or-nothing semantics.
    """

    def __init__(self):
        self.objects: Dict[str, StoredObject] = {}
        self.transactions: Dict[int, Transaction] = {}
        self._next_txn_id = 1

    def begin_transaction(self) -> int:
        """Begin a new transaction."""
        txn_id = self._next_txn_id
        self._next_txn_id += 1
        self.transactions[txn_id] = Transaction(txn_id)
        return txn_id

    def read(self, txn_id: int, object_id: str) -> Optional[Any]:
        """Read an object within a transaction."""
        if object_id not in self.objects:
            return None

        value = self.objects[object_id].value
        self.transactions[txn_id].add_read(object_id, value)
        return value

    def write(self, txn_id: int, object_id: str, new_value: Any) -> bool:
        """
        Write an object within a transaction.

        DDIA: "The write is recorded in the transaction's write set.
        The actual write to storage happens only on commit."
        """
        if object_id not in self.objects:
            self.objects[object_id] = StoredObject(object_id, None)

        old_value = self.objects[object_id].value
        self.transactions[txn_id].add_write(object_id, old_value, new_value)
        return True

    def commit(self, txn_id: int) -> bool:
        """
        Commit a transaction.

        DDIA: "Either ALL writes succeed or NONE of them do.
        This is the all-or-nothing semantics of transactions."

        Steps:
          1. Validate all writes (check for conflicts)
          2. Apply all writes atomically
          3. Mark transaction as committed
        """
        if txn_id not in self.transactions:
            return False

        txn = self.transactions[txn_id]

        # Step 1: Validate all writes
        for write in txn.writes:
            if write.object_id not in self.objects:
                # Object doesn't exist, create it
                self.objects[write.object_id] = StoredObject(write.object_id, None)

        # Step 2: Apply all writes atomically
        try:
            for write in txn.writes:
                self.objects[write.object_id].value = write.new_value
                self.objects[write.object_id].version += 1

            # Step 3: Mark as committed
            txn.commit()
            return True

        except Exception as e:
            # If any write fails, abort the entire transaction
            txn.abort()
            return False

    def abort(self, txn_id: int):
        """Abort a transaction (discard all writes)."""
        if txn_id in self.transactions:
            self.transactions[txn_id].abort()

    def get_transaction_info(self, txn_id: int) -> Optional[Transaction]:
        """Get information about a transaction."""
        return self.transactions.get(txn_id)


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


def demo_1_single_object_insufficient():
    """
    Demo 1: Show why single-object atomicity is insufficient.

    DDIA concept: "Single-object atomicity is NOT enough.
    You need multi-object transactions to keep related data in sync."
    """
    print_header("DEMO 1: Why Single-Object Atomicity is Insufficient")
    print("""
    Scenario: Bank transfer ($100 from Account A to Account B).

    With only single-object atomicity:
      • Debit Account A: ✅ Atomic
      • Credit Account B: ✅ Atomic
      • But if crash between them: money vanishes!

    With multi-object transactions:
      • Both operations succeed together
      • Or both are rolled back together
      • Money is never lost
    """)

    db = MultiObjectDatabase()

    # Create accounts
    db.objects["account_a"] = StoredObject("account_a", 100)
    db.objects["account_b"] = StoredObject("account_b", 50)

    print(f"  Initial state:")
    print(f"    Account A: ${db.objects['account_a'].value}")
    print(f"    Account B: ${db.objects['account_b'].value}")
    print(f"    Total: ${db.objects['account_a'].value + db.objects['account_b'].value}\n")

    print(f"  ❌ WITHOUT multi-object transactions:")
    print(f"    1. Debit Account A: $100 → $0")
    print(f"    2. 💥 CRASH!")
    print(f"    3. Credit Account B: NEVER HAPPENS")
    print(f"    Result: Account A lost $100, Account B never received it!")
    print(f"    Money vanished! 💸\n")

    print(f"  ✅ WITH multi-object transactions:")
    print(f"    1. Begin transaction")
    txn_id = db.begin_transaction()
    print(f"       Transaction {txn_id} started")

    print(f"\n    2. Debit Account A")
    db.write(txn_id, "account_a", 0)
    print(f"       Recorded: Account A: $100 → $0")

    print(f"\n    3. Credit Account B")
    db.write(txn_id, "account_b", 150)
    print(f"       Recorded: Account B: $50 → $150")

    print(f"\n    4. Commit transaction")
    if db.commit(txn_id):
        print(f"       ✅ Both writes applied atomically")
    else:
        print(f"       ❌ Transaction failed, both writes rolled back")

    print(f"\n  Final state:")
    print(f"    Account A: ${db.objects['account_a'].value}")
    print(f"    Account B: ${db.objects['account_b'].value}")
    print(f"    Total: ${db.objects['account_a'].value + db.objects['account_b'].value}")
    print(f"    ✅ Money is conserved!")

    print("""
  💡 KEY INSIGHT (DDIA):
     Multi-object transactions guarantee:
       • All writes succeed together
       • Or all are rolled back together
       • Application invariants are maintained

     This is why financial systems use transactions!
    """)


def demo_2_foreign_key_consistency():
    """
    Demo 2: Show multi-object transactions for foreign key consistency.

    DDIA concept: "A foreign key reference: inserting a row that
    references another table means both tables need to be updated together."
    """
    print_header("DEMO 2: Foreign Key Consistency")
    print("""
    Scenario: Insert a new order that references a customer.

    Tables:
      customers: {id, name}
      orders: {id, customer_id, amount}

    Invariant: Every order must reference an existing customer.

    Without multi-object transactions:
      • Insert customer: ✅
      • Insert order: ✅
      • But if crash between them: orphaned order!

    With multi-object transactions:
      • Both inserts succeed together
      • Or both are rolled back together
      • Invariant is maintained
    """)

    db = MultiObjectDatabase()

    # Create initial data
    db.objects["customer_1"] = StoredObject("customer_1", {"id": 1, "name": "Alice"})
    db.objects["order_count"] = StoredObject("order_count", 0)

    print(f"  Initial state:")
    print(f"    Customer 1: {db.objects['customer_1'].value}")
    print(f"    Order count: {db.objects['order_count'].value}\n")

    print(f"  Transaction: Create new order for Customer 1\n")

    txn_id = db.begin_transaction()
    print(f"  Step 1: Verify customer exists")
    customer = db.read(txn_id, "customer_1")
    print(f"    ✅ Customer found: {customer}")

    print(f"\n  Step 2: Create order")
    db.write(txn_id, "order_1", {"id": 1, "customer_id": 1, "amount": 100})
    print(f"    Recorded: Create order_1")

    print(f"\n  Step 3: Update order count")
    db.write(txn_id, "order_count", 1)
    print(f"    Recorded: order_count: 0 → 1")

    print(f"\n  Step 4: Commit transaction")
    if db.commit(txn_id):
        print(f"    ✅ Both writes applied atomically")
        print(f"    Invariant maintained: order references existing customer")
    else:
        print(f"    ❌ Transaction failed")

    print(f"\n  Final state:")
    print(f"    Customer 1: {db.objects['customer_1'].value}")
    print(f"    Order 1: {db.objects['order_1'].value}")
    print(f"    Order count: {db.objects['order_count'].value}")

    print("""
  💡 KEY INSIGHT (DDIA):
     Multi-object transactions maintain referential integrity:
       • Foreign key constraints are enforced
       • Related data stays in sync
       • No orphaned records

     This is why relational databases use transactions!
    """)


def demo_3_denormalized_document_consistency():
    """
    Demo 3: Show multi-object transactions for denormalized documents.

    DDIA concept: "Updating a denormalized document might require
    updating several documents that embed or reference each other."
    """
    print_header("DEMO 3: Denormalized Document Consistency")
    print("""
    Scenario: Update a user's profile and their secondary index.

    Documents:
      user_profile: {id, name, email, age}
      user_index: {email, user_id}  (for fast lookup by email)

    Invariant: user_index must always point to valid user_profile.

    Without multi-object transactions:
      • Update user_profile: ✅
      • Update user_index: ✅
      • But if crash between them: index is stale!

    With multi-object transactions:
      • Both updates succeed together
      • Or both are rolled back together
      • Index stays in sync
    """)

    db = MultiObjectDatabase()

    # Create initial data
    db.objects["user_1"] = StoredObject("user_1", {"id": 1, "name": "Alice", "email": "alice@old.com"})
    db.objects["email_index"] = StoredObject("email_index", {"alice@old.com": 1})

    print(f"  Initial state:")
    print(f"    User 1: {db.objects['user_1'].value}")
    print(f"    Email index: {db.objects['email_index'].value}\n")

    print(f"  Transaction: Update user's email\n")

    txn_id = db.begin_transaction()

    print(f"  Step 1: Update user profile")
    db.write(txn_id, "user_1", {"id": 1, "name": "Alice", "email": "alice@new.com"})
    print(f"    Recorded: email: alice@old.com → alice@new.com")

    print(f"\n  Step 2: Update email index")
    new_index = {"alice@new.com": 1}
    db.write(txn_id, "email_index", new_index)
    print(f"    Recorded: index updated")

    print(f"\n  Step 3: Commit transaction")
    if db.commit(txn_id):
        print(f"    ✅ Both updates applied atomically")
        print(f"    Index stays in sync with profile")
    else:
        print(f"    ❌ Transaction failed")

    print(f"\n  Final state:")
    print(f"    User 1: {db.objects['user_1'].value}")
    print(f"    Email index: {db.objects['email_index'].value}")

    print("""
  💡 KEY INSIGHT (DDIA):
     Multi-object transactions maintain denormalized consistency:
       • Primary data and indexes stay in sync
       • No stale indexes
       • Searches always find the right data

     This is why document databases use transactions!
    """)


def demo_4_secondary_index_consistency():
    """
    Demo 4: Show multi-object transactions for secondary index consistency.

    DDIA concept: "When you update a value, the secondary index needs
    to be updated too. Without transactions, the index might be updated
    but the value might not (or vice versa)."
    """
    print_header("DEMO 4: Secondary Index Consistency")
    print("""
    Scenario: Update a product's color and update the color index.

    Data:
      product_1: {id, name, color}
      color_index: {red: [1, 3, 5], blue: [2, 4]}

    Invariant: color_index must always match product colors.

    Without multi-object transactions:
      • Update product color: ✅
      • Update color index: ✅
      • But if crash between them: index is inconsistent!

    With multi-object transactions:
      • Both updates succeed together
      • Or both are rolled back together
      • Index stays consistent
    """)

    db = MultiObjectDatabase()

    # Create initial data
    db.objects["product_1"] = StoredObject("product_1", {"id": 1, "name": "Car", "color": "red"})
    db.objects["color_index"] = StoredObject("color_index", {"red": [1], "blue": []})

    print(f"  Initial state:")
    print(f"    Product 1: {db.objects['product_1'].value}")
    print(f"    Color index: {db.objects['color_index'].value}\n")

    print(f"  Transaction: Change product color from red to blue\n")

    txn_id = db.begin_transaction()

    print(f"  Step 1: Update product color")
    db.write(txn_id, "product_1", {"id": 1, "name": "Car", "color": "blue"})
    print(f"    Recorded: color: red → blue")

    print(f"\n  Step 2: Update color index")
    new_index = {"red": [], "blue": [1]}
    db.write(txn_id, "color_index", new_index)
    print(f"    Recorded: index updated")

    print(f"\n  Step 3: Commit transaction")
    if db.commit(txn_id):
        print(f"    ✅ Both updates applied atomically")
        print(f"    Index stays consistent with data")
    else:
        print(f"    ❌ Transaction failed")

    print(f"\n  Final state:")
    print(f"    Product 1: {db.objects['product_1'].value}")
    print(f"    Color index: {db.objects['color_index'].value}")

    print("""
  💡 KEY INSIGHT (DDIA):
     Multi-object transactions maintain index consistency:
       • Data and indexes are always in sync
       • No stale or inconsistent indexes
       • Searches always return correct results

     This is why databases use transactions for indexes!
    """)


def demo_5_transaction_atomicity():
    """
    Demo 5: Show all-or-nothing semantics of transactions.

    DDIA concept: "Either the entire transaction succeeds (commit)
    or it fails (abort/rollback)."
    """
    print_header("DEMO 5: Transaction Atomicity (All-or-Nothing)")
    print("""
    Scenario: Multi-step transaction with potential failure.

    Steps:
      1. Debit account A
      2. Credit account B
      3. Update transaction log

    If any step fails:
      • All steps are rolled back
      • Database returns to initial state
      • No partial updates
    """)

    db = MultiObjectDatabase()

    # Create initial data
    db.objects["account_a"] = StoredObject("account_a", 100)
    db.objects["account_b"] = StoredObject("account_b", 50)
    db.objects["txn_log"] = StoredObject("txn_log", [])

    print(f"  Initial state:")
    print(f"    Account A: ${db.objects['account_a'].value}")
    print(f"    Account B: ${db.objects['account_b'].value}")
    print(f"    Transaction log: {db.objects['txn_log'].value}\n")

    print(f"  Scenario 1: Successful transaction\n")

    txn_id = db.begin_transaction()
    print(f"  Transaction {txn_id}:")
    db.write(txn_id, "account_a", 70)
    print(f"    Step 1: Debit Account A: $100 → $70")
    db.write(txn_id, "account_b", 80)
    print(f"    Step 2: Credit Account B: $50 → $80")
    db.write(txn_id, "txn_log", ["Transfer: A→B $30"])
    print(f"    Step 3: Log transaction")

    if db.commit(txn_id):
        print(f"    ✅ Committed: All 3 steps applied")
    else:
        print(f"    ❌ Aborted: All 3 steps rolled back")

    print(f"\n  State after successful transaction:")
    print(f"    Account A: ${db.objects['account_a'].value}")
    print(f"    Account B: ${db.objects['account_b'].value}")
    print(f"    Transaction log: {db.objects['txn_log'].value}\n")

    print(f"  Scenario 2: Failed transaction (simulated)\n")

    # Reset
    db.objects["account_a"].value = 100
    db.objects["account_b"].value = 50
    db.objects["txn_log"].value = []

    txn_id = db.begin_transaction()
    print(f"  Transaction {txn_id}:")
    db.write(txn_id, "account_a", 70)
    print(f"    Step 1: Debit Account A: $100 → $70")
    db.write(txn_id, "account_b", 80)
    print(f"    Step 2: Credit Account B: $50 → $80")

    # Simulate failure
    print(f"    Step 3: Constraint violation (insufficient funds)")
    db.abort(txn_id)
    print(f"    ❌ Aborted: All steps rolled back")

    print(f"\n  State after failed transaction:")
    print(f"    Account A: ${db.objects['account_a'].value}")
    print(f"    Account B: ${db.objects['account_b'].value}")
    print(f"    Transaction log: {db.objects['txn_log'].value}")
    print(f"    ✅ Database returned to initial state!")

    print("""
  💡 KEY INSIGHT (DDIA):
     All-or-nothing semantics guarantee:
       • Successful transaction: all writes applied
       • Failed transaction: all writes rolled back
       • Never a partial state
       • Application can safely retry

     This is the fundamental promise of transactions!
    """)


def demo_6_transaction_write_set():
    """
    Demo 6: Show how transactions buffer writes.

    DDIA concept: "The write is recorded in the transaction's write set.
    The actual write to storage happens only on commit."
    """
    print_header("DEMO 6: Transaction Write Set")
    print("""
    Scenario: Transaction buffers writes before committing.

    Process:
      1. Application issues writes
      2. Writes are buffered in transaction's write set
      3. On commit, all writes are applied atomically
      4. On abort, all writes are discarded

    This allows:
      • Atomicity: all-or-nothing
      • Isolation: other transactions don't see uncommitted writes
      • Consistency: invariants are maintained
    """)

    db = MultiObjectDatabase()

    # Create initial data
    db.objects["x"] = StoredObject("x", 10)
    db.objects["y"] = StoredObject("y", 20)
    db.objects["z"] = StoredObject("z", 30)

    print(f"  Initial state:")
    print(f"    x = {db.objects['x'].value}")
    print(f"    y = {db.objects['y'].value}")
    print(f"    z = {db.objects['z'].value}\n")

    txn_id = db.begin_transaction()
    print(f"  Transaction {txn_id} begins\n")

    print(f"  Application issues writes:")
    print(f"    1. Write x = 11")
    db.write(txn_id, "x", 11)
    print(f"       ✅ Buffered in write set")

    print(f"    2. Write y = 21")
    db.write(txn_id, "y", 21)
    print(f"       ✅ Buffered in write set")

    print(f"    3. Write z = 31")
    db.write(txn_id, "z", 31)
    print(f"       ✅ Buffered in write set")

    print(f"\n  Current state (before commit):")
    print(f"    x = {db.objects['x'].value} (unchanged)")
    print(f"    y = {db.objects['y'].value} (unchanged)")
    print(f"    z = {db.objects['z'].value} (unchanged)")
    print(f"    ✅ Other transactions don't see uncommitted writes!")

    txn = db.get_transaction_info(txn_id)
    print(f"\n  Transaction write set:")
    for write in txn.writes:
        print(f"    {write}")

    print(f"\n  Commit transaction")
    if db.commit(txn_id):
        print(f"    ✅ All writes applied atomically")

    print(f"\n  Final state (after commit):")
    print(f"    x = {db.objects['x'].value}")
    print(f"    y = {db.objects['y'].value}")
    print(f"    z = {db.objects['z'].value}")

    print("""
  💡 KEY INSIGHT (DDIA):
     Transaction write set enables:
       • Atomicity: all writes applied together
       • Isolation: uncommitted writes are invisible
       • Consistency: invariants are maintained

     This is how databases implement transactions!
    """)


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 80)
    print("  EXERCISE 2: MULTI-OBJECT TRANSACTIONS")
    print("  DDIA Chapter 7: 'Transactions'")
    print("=" * 80)
    print("""
  This exercise demonstrates MULTI-OBJECT TRANSACTIONS.
  Coordinating writes across multiple objects to maintain invariants.

  Key scenarios:
    • Bank transfers (debit one account, credit another)
    • Foreign keys (insert in two tables)
    • Denormalized documents (update document and index)
    • Secondary indexes (update data and index)
    """)

    demo_1_single_object_insufficient()
    demo_2_foreign_key_consistency()
    demo_3_denormalized_document_consistency()
    demo_4_secondary_index_consistency()
    demo_5_transaction_atomicity()
    demo_6_transaction_write_set()

    print("\n" + "=" * 80)
    print("  EXERCISE 2 COMPLETE ✅")
    print("=" * 80)
    print("""
  Key Takeaways:

  1. 📝 Single-object atomicity is NOT enough
  2. 🔗 Multi-object transactions keep related data in sync
  3. 💰 Bank transfers need atomicity across accounts
  4. 🔑 Foreign keys need atomicity across tables
  5. 📊 Indexes need atomicity with data
  6. ✅ All-or-nothing semantics: commit or abort

  Next: Run 03_error_handling_retries.py to see error handling
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
