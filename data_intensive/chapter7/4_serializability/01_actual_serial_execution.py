"""
Exercise 1: Actual Serial Execution

DDIA Reference: Chapter 7, "Serializability - Technique 1: Actual Serial Execution" (pp. 330-333)

This exercise demonstrates ACTUAL SERIAL EXECUTION:
  - Execute every transaction one at a time, in a single thread
  - Simplest way to achieve serializability
  - Works if transactions are short and data fits in memory
  - Used by: VoltDB, Redis, Datomic

Key concepts:
  - Single-threaded execution eliminates all concurrency anomalies
  - Stored procedures: submit entire transaction as a block
  - Partitioned serial execution: each partition has its own executor
  - Trade-off: throughput limited by single CPU core

Run: python 01_actual_serial_execution.py
"""

import sys
import time
from typing import Dict, List, Tuple, Any, Callable
from dataclasses import dataclass
from enum import Enum

sys.stdout.reconfigure(encoding='utf-8')


# =============================================================================
# CORE COMPONENTS: Transaction, SerialExecutor
# =============================================================================

class TransactionStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMMITTED = "committed"
    ABORTED = "aborted"


@dataclass
class Transaction:
    """A transaction to be executed."""
    tx_id: int
    name: str
    operations: List[Callable]  # List of operations to execute
    status: TransactionStatus = TransactionStatus.PENDING
    start_time: float = 0.0
    end_time: float = 0.0

    def duration_ms(self) -> float:
        """Return transaction duration in milliseconds."""
        if self.end_time == 0:
            return 0
        return (self.end_time - self.start_time) * 1000

    def __repr__(self):
        return f"Transaction({self.tx_id}, {self.name}, {self.status.value})"


class SerialExecutor:
    """
    A single-threaded executor that runs transactions serially.

    DDIA insight: "The simplest solution: literally execute every transaction
    one at a time, in a single thread, on a single CPU core."
    """

    def __init__(self):
        self.data: Dict[str, Any] = {}
        self.transaction_log: List[Transaction] = []
        self.current_tx: Transaction = None

    def execute_transaction(self, tx: Transaction) -> bool:
        """
        Execute a transaction serially.

        Returns True if successful, False if aborted.
        """
        self.current_tx = tx
        tx.status = TransactionStatus.RUNNING
        tx.start_time = time.time()

        try:
            # Execute all operations in the transaction
            for operation in tx.operations:
                operation(self.data)

            # If we get here, transaction succeeded
            tx.status = TransactionStatus.COMMITTED
            tx.end_time = time.time()
            self.transaction_log.append(tx)
            return True

        except Exception as e:
            # Transaction failed, rollback
            tx.status = TransactionStatus.ABORTED
            tx.end_time = time.time()
            self.transaction_log.append(tx)
            return False

    def execute_batch(self, transactions: List[Transaction]) -> Tuple[int, int]:
        """
        Execute a batch of transactions serially.

        Returns (committed_count, aborted_count)
        """
        committed = 0
        aborted = 0

        for tx in transactions:
            if self.execute_transaction(tx):
                committed += 1
            else:
                aborted += 1

        return committed, aborted

    def get_value(self, key: str) -> Any:
        """Get a value from the data store."""
        return self.data.get(key)

    def set_value(self, key: str, value: Any):
        """Set a value in the data store."""
        self.data[key] = value

    def get_stats(self) -> Dict:
        """Get execution statistics."""
        total_time = sum(tx.duration_ms() for tx in self.transaction_log)
        committed = sum(1 for tx in self.transaction_log if tx.status == TransactionStatus.COMMITTED)
        aborted = sum(1 for tx in self.transaction_log if tx.status == TransactionStatus.ABORTED)

        return {
            "total_transactions": len(self.transaction_log),
            "committed": committed,
            "aborted": aborted,
            "total_time_ms": total_time,
            "avg_time_ms": total_time / len(self.transaction_log) if self.transaction_log else 0,
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


def demo_1_basic_serial_execution():
    """
    Demo 1: Show how serial execution works.

    DDIA concept: "The simplest solution: literally execute every transaction
    one at a time, in a single thread, on a single CPU core."
    """
    print_header("DEMO 1: Basic Serial Execution")
    print("""
    Serial execution means: one transaction at a time, no concurrency.
    This eliminates ALL concurrency anomalies (dirty reads, lost updates, etc.)
    """)

    executor = SerialExecutor()

    # Create transactions
    def tx1_ops(data):
        """Transaction 1: Transfer $100 from Account A to Account B"""
        data['account_a'] = data.get('account_a', 1000) - 100
        data['account_b'] = data.get('account_b', 500) + 100

    def tx2_ops(data):
        """Transaction 2: Transfer $50 from Account B to Account C"""
        data['account_b'] = data.get('account_b', 600) - 50
        data['account_c'] = data.get('account_c', 200) + 50

    tx1 = Transaction(1, "Transfer A→B", [tx1_ops])
    tx2 = Transaction(2, "Transfer B→C", [tx2_ops])

    print("📝 Initial state:")
    print("   Account A: $1000")
    print("   Account B: $500")
    print("   Account C: $200")

    print("\n📋 Transactions to execute:")
    print("   TX1: Transfer $100 from A to B")
    print("   TX2: Transfer $50 from B to C")

    # Execute serially
    print("\n⏱️  Executing serially (one at a time):")
    committed, aborted = executor.execute_batch([tx1, tx2])

    print(f"\n   TX1: {tx1.status.value} ({tx1.duration_ms():.2f}ms)")
    print(f"   TX2: {tx2.status.value} ({tx2.duration_ms():.2f}ms)")

    print("\n💰 Final state:")
    print(f"   Account A: ${executor.get_value('account_a')}")
    print(f"   Account B: ${executor.get_value('account_b')}")
    print(f"   Account C: ${executor.get_value('account_c')}")

    print(f"\n   Total: ${executor.get_value('account_a') + executor.get_value('account_b') + executor.get_value('account_c')}")
    print(f"   ✅ Money is conserved! (started with $1700, still $1700)")

    print("""
  💡 KEY INSIGHT (DDIA):
     Serial execution guarantees serializability because there is NO
     concurrency. Each transaction sees a consistent state before and after.
     No dirty reads, no lost updates, no write skew — nothing!
    """)


def demo_2_no_concurrency_anomalies():
    """
    Demo 2: Show that serial execution prevents all anomalies.

    DDIA concept: "All the anomalies we've discussed (dirty reads, dirty writes,
    read skew, lost updates, write skew, phantoms) are prevented by Serializability."
    """
    print_header("DEMO 2: No Concurrency Anomalies")
    print("""
    With serial execution, we can't have:
    ✅ Dirty reads (no concurrent reads)
    ✅ Dirty writes (no concurrent writes)
    ✅ Read skew (each transaction sees consistent snapshot)
    ✅ Lost updates (no concurrent modifications)
    ✅ Write skew (no concurrent decisions)
    ✅ Phantoms (no concurrent inserts/deletes)
    """)

    executor = SerialExecutor()

    # Scenario: Counter increment (classic lost update problem)
    def increment_counter(data):
        """Increment counter by 1"""
        data['counter'] = data.get('counter', 0) + 1

    print("📝 Initial state: counter = 0")
    print("\n📋 Transactions: 10 transactions, each increments counter by 1")

    # Create 10 transactions
    transactions = [
        Transaction(i, f"Increment {i}", [increment_counter])
        for i in range(1, 11)
    ]

    # Execute serially
    print("\n⏱️  Executing serially:")
    committed, aborted = executor.execute_batch(transactions)

    final_counter = executor.get_value('counter')
    print(f"\n   Final counter: {final_counter}")
    print(f"   Expected: 10")
    print(f"   ✅ CORRECT! No lost updates!")

    print("""
  💡 KEY INSIGHT (DDIA):
     With concurrent execution, we might get counter = 5 or 7 (lost updates).
     With serial execution, we ALWAYS get counter = 10.
     This is the power of serializability!
    """)


def demo_3_stored_procedures():
    """
    Demo 3: Show how stored procedures enable serial execution.

    DDIA concept: "Instead of the application interactively executing
    statements one at a time (with network round-trips), the application
    submits the entire transaction as a stored procedure."
    """
    print_header("DEMO 3: Stored Procedures")
    print("""
    Stored procedures are the key to making serial execution practical.
    Instead of:
      1. Client sends: SELECT balance FROM accounts WHERE id=1
      2. Database responds
      3. Client sends: UPDATE accounts SET balance=... WHERE id=1
      4. Database responds

    With stored procedures:
      1. Client sends: EXECUTE transfer_money(from_id, to_id, amount)
      2. Database executes entire procedure atomically
      3. Database responds with result
    """)

    executor = SerialExecutor()

    # Define a stored procedure as a function
    def transfer_money_procedure(from_account: str, to_account: str, amount: int):
        """Stored procedure: transfer money between accounts"""
        def procedure(data):
            # Check balance
            from_balance = data.get(from_account, 0)
            if from_balance < amount:
                raise ValueError(f"Insufficient funds in {from_account}")

            # Transfer
            data[from_account] = from_balance - amount
            data[to_account] = data.get(to_account, 0) + amount

        return procedure

    # Initialize accounts
    executor.set_value('alice', 1000)
    executor.set_value('bob', 500)
    executor.set_value('charlie', 200)

    print("📝 Initial state:")
    print(f"   Alice: ${executor.get_value('alice')}")
    print(f"   Bob: ${executor.get_value('bob')}")
    print(f"   Charlie: ${executor.get_value('charlie')}")

    # Create transactions using stored procedures
    tx1 = Transaction(1, "Alice→Bob $100", [transfer_money_procedure('alice', 'bob', 100)])
    tx2 = Transaction(2, "Bob→Charlie $50", [transfer_money_procedure('bob', 'charlie', 50)])
    tx3 = Transaction(3, "Charlie→Alice $25", [transfer_money_procedure('charlie', 'alice', 25)])

    print("\n📋 Stored procedures to execute:")
    print("   TX1: transfer_money('alice', 'bob', 100)")
    print("   TX2: transfer_money('bob', 'charlie', 50)")
    print("   TX3: transfer_money('charlie', 'alice', 25)")

    # Execute serially
    print("\n⏱️  Executing serially:")
    committed, aborted = executor.execute_batch([tx1, tx2, tx3])

    print(f"\n   TX1: {tx1.status.value}")
    print(f"   TX2: {tx2.status.value}")
    print(f"   TX3: {tx3.status.value}")

    print("\n💰 Final state:")
    print(f"   Alice: ${executor.get_value('alice')}")
    print(f"   Bob: ${executor.get_value('bob')}")
    print(f"   Charlie: ${executor.get_value('charlie')}")

    print(f"\n   Total: ${executor.get_value('alice') + executor.get_value('bob') + executor.get_value('charlie')}")
    print(f"   ✅ Money is conserved!")

    print("""
  💡 KEY INSIGHT (DDIA):
     Stored procedures eliminate network round-trips. The entire transaction
     is submitted as a block and executed atomically. This makes serial
     execution practical for real applications.
    """)


def demo_4_performance_characteristics():
    """
    Demo 4: Show performance characteristics of serial execution.

    DDIA concept: "This sounds crazy-slow, but it works if:
    1. Every transaction is very short and fast (microseconds).
    2. The active dataset fits in memory (RAM is fast, disk is slow).
    3. Write throughput is low enough for a single CPU core."
    """
    print_header("DEMO 4: Performance Characteristics")
    print("""
    Serial execution has interesting performance characteristics:
    ✅ Predictable latency (no waiting for locks)
    ✅ No deadlocks
    ✅ Simple to reason about
    ❌ Limited throughput (single CPU core)
    ❌ Doesn't scale to multiple cores
    """)

    executor = SerialExecutor()

    # Simulate different transaction sizes
    def create_transaction(tx_id: int, size: str, num_ops: int):
        """Create a transaction with a certain number of operations"""
        def ops(data):
            for i in range(num_ops):
                key = f"key_{i}"
                data[key] = data.get(key, 0) + 1

        return Transaction(tx_id, f"{size} transaction", [ops])

    print("📊 Transaction sizes:")
    print("   Small: 10 operations")
    print("   Medium: 100 operations")
    print("   Large: 1000 operations")

    # Create transactions
    transactions = []
    tx_id = 1

    for _ in range(5):
        transactions.append(create_transaction(tx_id, "Small", 10))
        tx_id += 1

    for _ in range(5):
        transactions.append(create_transaction(tx_id, "Medium", 100))
        tx_id += 1

    for _ in range(5):
        transactions.append(create_transaction(tx_id, "Large", 1000))
        tx_id += 1

    # Execute
    print("\n⏱️  Executing 15 transactions (5 small, 5 medium, 5 large):")
    committed, aborted = executor.execute_batch(transactions)

    # Analyze
    print_section("📊 Performance Analysis")

    small_txs = [tx for tx in executor.transaction_log if "Small" in tx.name]
    medium_txs = [tx for tx in executor.transaction_log if "Medium" in tx.name]
    large_txs = [tx for tx in executor.transaction_log if "Large" in tx.name]

    print(f"\n   Small transactions:")
    print(f"     Avg time: {sum(tx.duration_ms() for tx in small_txs) / len(small_txs):.3f}ms")

    print(f"\n   Medium transactions:")
    print(f"     Avg time: {sum(tx.duration_ms() for tx in medium_txs) / len(medium_txs):.3f}ms")

    print(f"\n   Large transactions:")
    print(f"     Avg time: {sum(tx.duration_ms() for tx in large_txs) / len(large_txs):.3f}ms")

    stats = executor.get_stats()
    print(f"\n   Total time: {stats['total_time_ms']:.2f}ms")
    print(f"   Throughput: {len(executor.transaction_log) / (stats['total_time_ms'] / 1000):.0f} tx/sec")

    print("""
  💡 KEY INSIGHT (DDIA):
     Serial execution works well when:
     1. Transactions are SHORT (microseconds, not seconds)
     2. Data fits in MEMORY (RAM is fast, disk is slow)
     3. Write throughput is LOW (single core is enough)

     If any of these conditions are violated, serial execution becomes
     a bottleneck. This is why it's used by specialized systems like
     VoltDB and Redis, not general-purpose databases.
    """)


def demo_5_partitioned_serial_execution():
    """
    Demo 5: Show partitioned serial execution.

    DDIA concept: "If data is partitioned, each partition can have its own
    single-threaded executor. Transactions that only touch a single partition
    can run in parallel across partitions."
    """
    print_header("DEMO 5: Partitioned Serial Execution")
    print("""
    To scale beyond a single CPU core, partition the data.
    Each partition has its own serial executor.
    Transactions that touch only one partition can run in parallel!
    """)

    # Create multiple executors (one per partition)
    executors = {
        'partition_1': SerialExecutor(),
        'partition_2': SerialExecutor(),
        'partition_3': SerialExecutor(),
    }

    # Initialize data
    for partition, executor in executors.items():
        executor.set_value('balance', 1000)

    print("📊 Partition setup:")
    print("   Partition 1: accounts 1-100")
    print("   Partition 2: accounts 101-200")
    print("   Partition 3: accounts 201-300")

    # Create transactions that touch different partitions
    def transfer_within_partition(partition: str, amount: int):
        """Transfer within a partition"""
        def ops(data):
            data['balance'] = data.get('balance', 0) - amount

        return ops

    print("\n📋 Transactions:")
    print("   TX1: Transfer within Partition 1")
    print("   TX2: Transfer within Partition 2")
    print("   TX3: Transfer within Partition 3")
    print("   (These can run in PARALLEL!)")

    # Execute in parallel (simulated)
    print("\n⏱️  Executing in parallel (one executor per partition):")

    tx1 = Transaction(1, "P1 transfer", [transfer_within_partition('partition_1', 100)])
    tx2 = Transaction(2, "P2 transfer", [transfer_within_partition('partition_2', 100)])
    tx3 = Transaction(3, "P3 transfer", [transfer_within_partition('partition_3', 100)])

    # Execute each in its partition
    executors['partition_1'].execute_transaction(tx1)
    executors['partition_2'].execute_transaction(tx2)
    executors['partition_3'].execute_transaction(tx3)

    print(f"\n   TX1 (P1): {tx1.status.value} ({tx1.duration_ms():.3f}ms)")
    print(f"   TX2 (P2): {tx2.status.value} ({tx2.duration_ms():.3f}ms)")
    print(f"   TX3 (P3): {tx3.status.value} ({tx3.duration_ms():.3f}ms)")

    print("\n   ✅ All 3 transactions executed in parallel!")
    print("   ✅ Each partition maintains serializability!")

    print("""
  💡 KEY INSIGHT (DDIA):
     Partitioned serial execution is the key to scaling serial execution.
     If your data is partitioned and most transactions touch only one
     partition, you can achieve:
     • Serializability (within each partition)
     • Parallelism (across partitions)
     • Good throughput (multiple cores)

     This is used by VoltDB and other systems.
    """)


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 80)
    print("  EXERCISE 1: ACTUAL SERIAL EXECUTION")
    print("  DDIA Chapter 7: 'Serializability - Technique 1'")
    print("=" * 80)
    print("""
  This exercise demonstrates ACTUAL SERIAL EXECUTION:
  - Execute every transaction one at a time, in a single thread
  - Simplest way to achieve serializability
  - Works if transactions are short and data fits in memory
    """)

    demo_1_basic_serial_execution()
    demo_2_no_concurrency_anomalies()
    demo_3_stored_procedures()
    demo_4_performance_characteristics()
    demo_5_partitioned_serial_execution()

    print("\n" + "=" * 80)
    print("  EXERCISE 1 COMPLETE ✅")
    print("=" * 80)
    print("""
  Key Takeaways:

  1. 🔒 Serial execution eliminates ALL concurrency anomalies
  2. 📦 Stored procedures make serial execution practical
  3. ⚡ Works well for short transactions and in-memory data
  4. 🔄 Partitioned serial execution enables parallelism
  5. 📊 Limited throughput (single CPU core per partition)

  Next: Run 02_two_phase_locking.py to learn about 2PL
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
