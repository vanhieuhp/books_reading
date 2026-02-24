"""
Exercise 2: Two-Phase Locking (2PL)

DDIA Reference: Chapter 7, "Serializability - Technique 2: Two-Phase Locking" (pp. 333-340)

This exercise demonstrates TWO-PHASE LOCKING:
  - Writers block readers, readers block writers
  - Shared locks for reads, exclusive locks for writes
  - Locks held until transaction commits (two phases)
  - Prevents all concurrency anomalies but causes deadlocks
  - Used by: MySQL InnoDB, PostgreSQL (with SERIALIZABLE), Oracle

Key concepts:
  - Shared lock: multiple readers can hold simultaneously
  - Exclusive lock: only one writer, no readers
  - Lock upgrade: shared → exclusive
  - Deadlock detection and resolution
  - Predicate locks and index-range locks for phantoms

Run: python 02_two_phase_locking.py
"""

import sys
import time
from typing import Dict, List, Set, Tuple, Any
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')


# =============================================================================
# CORE COMPONENTS: Lock, LockManager, TwoPhaseLockedStore
# =============================================================================

class LockType(Enum):
    SHARED = "shared"      # Read lock
    EXCLUSIVE = "exclusive"  # Write lock


@dataclass
class Lock:
    """A lock on a data item."""
    lock_type: LockType
    tx_id: int
    acquired_at: float = 0.0

    def __repr__(self):
        return f"Lock({self.lock_type.value}, tx={self.tx_id})"


class LockManager:
    """
    Manages locks for 2PL.

    DDIA insight: "If Transaction A has read an object and Transaction B
    wants to write to that object, B must wait until A commits or aborts."
    """

    def __init__(self):
        self.locks: Dict[str, List[Lock]] = defaultdict(list)
        self.tx_locks: Dict[int, Set[str]] = defaultdict(set)  # Track locks per transaction
        self.deadlocks: List[Tuple[int, int]] = []

    def can_acquire_lock(self, key: str, lock_type: LockType, tx_id: int) -> bool:
        """Check if a transaction can acquire a lock."""
        current_locks = self.locks[key]

        if not current_locks:
            return True

        # If we already hold a lock on this key
        if any(lock.tx_id == tx_id for lock in current_locks):
            # Can upgrade shared to exclusive
            if lock_type == LockType.EXCLUSIVE:
                return all(lock.tx_id == tx_id for lock in current_locks)
            return True

        # If trying to acquire shared lock
        if lock_type == LockType.SHARED:
            # Can acquire if all existing locks are shared
            return all(lock.lock_type == LockType.SHARED for lock in current_locks)

        # If trying to acquire exclusive lock
        if lock_type == LockType.EXCLUSIVE:
            # Cannot acquire if any locks exist
            return False

        return False

    def acquire_lock(self, key: str, lock_type: LockType, tx_id: int) -> bool:
        """Acquire a lock. Returns True if successful, False if would deadlock."""
        if not self.can_acquire_lock(key, lock_type, tx_id):
            # Potential deadlock
            self.deadlocks.append((tx_id, self.locks[key][0].tx_id))
            return False

        # Remove old lock if upgrading
        self.locks[key] = [lock for lock in self.locks[key] if lock.tx_id != tx_id]

        # Add new lock
        lock = Lock(lock_type, tx_id, time.time())
        self.locks[key].append(lock)
        self.tx_locks[tx_id].add(key)

        return True

    def release_locks(self, tx_id: int):
        """Release all locks held by a transaction."""
        for key in self.tx_locks[tx_id]:
            self.locks[key] = [lock for lock in self.locks[key] if lock.tx_id != tx_id]

        self.tx_locks[tx_id].clear()

    def get_lock_info(self, key: str) -> List[Lock]:
        """Get all locks on a key."""
        return self.locks[key]


class TwoPhaseLockedStore:
    """
    A key-value store using Two-Phase Locking.

    DDIA concept: "If Transaction A has read an object and Transaction B
    wants to write to that object, B must wait until A commits or aborts."
    """

    def __init__(self):
        self.data: Dict[str, Any] = {}
        self.lock_manager = LockManager()
        self.transaction_log: List[Dict] = []

    def read(self, key: str, tx_id: int) -> Tuple[bool, Any]:
        """
        Read a value with a shared lock.

        Returns (success, value)
        """
        # Acquire shared lock
        if not self.lock_manager.acquire_lock(key, LockType.SHARED, tx_id):
            return False, None

        value = self.data.get(key)
        return True, value

    def write(self, key: str, value: Any, tx_id: int) -> bool:
        """
        Write a value with an exclusive lock.

        Returns True if successful, False if deadlock.
        """
        # Acquire exclusive lock
        if not self.lock_manager.acquire_lock(key, LockType.EXCLUSIVE, tx_id):
            return False

        self.data[key] = value
        return True

    def commit(self, tx_id: int):
        """Commit a transaction and release all locks."""
        self.lock_manager.release_locks(tx_id)

    def get_lock_info(self, key: str) -> List[Lock]:
        """Get lock information for a key."""
        return self.lock_manager.get_lock_info(key)


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


def demo_1_shared_and_exclusive_locks():
    """
    Demo 1: Show shared and exclusive locks.

    DDIA concept: "To read an object, a transaction must acquire a shared lock.
    To write an object, a transaction must acquire an exclusive lock."
    """
    print_header("DEMO 1: Shared and Exclusive Locks")
    print("""
    2PL uses two types of locks:
    • SHARED lock: Multiple readers can hold simultaneously
    • EXCLUSIVE lock: Only one writer, no readers allowed
    """)

    store = TwoPhaseLockedStore()
    store.data['balance'] = 1000

    print("📝 Initial state: balance = $1000")

    print("\n📋 Scenario 1: Multiple readers (shared locks)")
    print("   TX1 reads balance")
    print("   TX2 reads balance")
    print("   TX3 reads balance")
    print("   → All can hold shared locks simultaneously ✅")

    # Simulate multiple readers
    success1, val1 = store.read('balance', tx_id=1)
    success2, val2 = store.read('balance', tx_id=2)
    success3, val3 = store.read('balance', tx_id=3)

    print(f"\n   TX1 reads: ${val1}")
    print(f"   TX2 reads: ${val2}")
    print(f"   TX3 reads: ${val3}")

    locks = store.get_lock_info('balance')
    print(f"\n   Locks on 'balance': {len(locks)} shared locks")
    for lock in locks:
        print(f"     {lock}")

    # Release locks
    store.commit(1)
    store.commit(2)
    store.commit(3)

    print("\n📋 Scenario 2: Writer blocks readers")
    print("   TX4 wants to write balance")
    print("   TX5 wants to read balance")
    print("   → TX5 must wait for TX4 to release exclusive lock ⏳")

    # TX4 acquires exclusive lock
    success4 = store.write('balance', 900, tx_id=4)
    print(f"\n   TX4 acquires exclusive lock: {success4}")

    # TX5 tries to read (would block)
    success5, val5 = store.read('balance', tx_id=5)
    print(f"   TX5 tries to read: {success5} (blocked by exclusive lock)")

    store.commit(4)

    # Now TX5 can read
    success5, val5 = store.read('balance', tx_id=5)
    print(f"   TX5 reads after TX4 commits: {success5}, value=${val5}")

    store.commit(5)

    print("""
  💡 KEY INSIGHT (DDIA):
     This is the fundamental rule of 2PL:
     • Readers block writers
     • Writers block readers
     • Writers block writers

     This prevents all concurrency anomalies but causes blocking.
    """)


def demo_2_lock_upgrade():
    """
    Demo 2: Show lock upgrade (shared → exclusive).

    DDIA concept: "If a transaction first reads and then writes, it must
    upgrade its shared lock to an exclusive lock."
    """
    print_header("DEMO 2: Lock Upgrade")
    print("""
    A transaction can upgrade its lock:
    • Start with shared lock (for reading)
    • Upgrade to exclusive lock (for writing)
    """)

    store = TwoPhaseLockedStore()
    store.data['counter'] = 0

    print("📝 Initial state: counter = 0")

    print("\n📋 Transaction: Read-modify-write")
    print("   Step 1: Read counter (acquire shared lock)")
    print("   Step 2: Increment counter")
    print("   Step 3: Write counter (upgrade to exclusive lock)")

    # Step 1: Read (shared lock)
    success, value = store.read('counter', tx_id=1)
    print(f"\n   Step 1: Read counter = {value}")
    locks = store.get_lock_info('counter')
    print(f"   Locks: {[str(l) for l in locks]}")

    # Step 2: Increment
    new_value = value + 1
    print(f"\n   Step 2: Increment to {new_value}")

    # Step 3: Write (upgrade lock)
    success = store.write('counter', new_value, tx_id=1)
    print(f"\n   Step 3: Write counter = {new_value}")
    locks = store.get_lock_info('counter')
    print(f"   Locks: {[str(l) for l in locks]}")
    print(f"   ✅ Lock upgraded from shared to exclusive!")

    store.commit(1)

    print("""
  💡 KEY INSIGHT (DDIA):
     Lock upgrade is necessary for read-modify-write cycles.
     Without it, another transaction could modify the value between
     the read and write, causing a lost update.
    """)


def demo_3_deadlock_detection():
    """
    Demo 3: Show deadlock detection.

    DDIA concept: "The database must detect deadlocks and abort one of
    the transactions."
    """
    print_header("DEMO 3: Deadlock Detection")
    print("""
    Deadlock: TX1 waits for TX2's lock, TX2 waits for TX1's lock.
    Both are stuck forever!

    Solution: Detect and abort one transaction.
    """)

    store = TwoPhaseLockedStore()
    store.data['account_a'] = 1000
    store.data['account_b'] = 500

    print("📝 Initial state:")
    print("   Account A: $1000")
    print("   Account B: $500")

    print("\n📋 Scenario: Circular wait (deadlock)")
    print("   TX1: Transfer A→B")
    print("   TX2: Transfer B→A")
    print("   Both start at the same time...")

    # TX1 locks A
    success_a1 = store.write('account_a', 900, tx_id=1)
    print(f"\n   TX1 locks account_a: {success_a1}")

    # TX2 locks B
    success_b2 = store.write('account_b', 600, tx_id=2)
    print(f"   TX2 locks account_b: {success_b2}")

    # TX1 tries to lock B (held by TX2)
    success_b1 = store.write('account_b', 600, tx_id=1)
    print(f"\n   TX1 tries to lock account_b: {success_b1}")
    if not success_b1:
        print(f"   ⚠️  DEADLOCK DETECTED!")

    # TX2 tries to lock A (held by TX1)
    success_a2 = store.write('account_a', 900, tx_id=2)
    print(f"   TX2 tries to lock account_a: {success_a2}")
    if not success_a2:
        print(f"   ⚠️  DEADLOCK DETECTED!")

    print(f"\n   Deadlocks detected: {len(store.lock_manager.deadlocks)}")
    for tx1, tx2 in store.lock_manager.deadlocks:
        print(f"     TX{tx1} ↔ TX{tx2}")

    print("""
  💡 KEY INSIGHT (DDIA):
     Deadlocks are a major problem with 2PL. The database must:
     1. Detect deadlocks (cycle detection in wait graph)
     2. Abort one transaction
     3. Let the other retry

     This adds complexity and can hurt performance under contention.
    """)


def demo_4_predicate_locks():
    """
    Demo 4: Show predicate locks for preventing phantoms.

    DDIA concept: "To prevent phantoms, 2PL databases use Predicate Locks.
    Instead of locking a specific row, a predicate lock locks all objects
    that match a search condition."
    """
    print_header("DEMO 4: Predicate Locks (Preventing Phantoms)")
    print("""
    Phantom problem: A write in one transaction changes the result of
    a search query in another transaction.

    Solution: Predicate locks lock all rows matching a condition,
    including rows that don't exist yet!
    """)

    print("""
    Example: Booking a meeting room

    TX1: SELECT * FROM bookings WHERE room_id=123 AND time='14:00'
         → Returns: no bookings
         → Acquires predicate lock on (room_id=123 AND time='14:00')

    TX2: INSERT INTO bookings (room_id, time) VALUES (123, '14:00')
         → Tries to insert, but predicate lock blocks it!
         → TX2 must wait for TX1 to commit

    Result: No phantom! TX1's query result remains valid.
    """)

    print("""
    ✅ Predicate locks prevent phantoms
    ❌ But they're expensive to check (must evaluate predicate for every write)

    Real databases use Index-Range Locks instead:
    • Lock a range of the index (e.g., "room 123 for the entire afternoon")
    • Cheaper to check, but locks more than strictly necessary
    • Still prevents phantoms
    """)

    print("""
  💡 KEY INSIGHT (DDIA):
     Predicate locks are the "right" solution to phantoms, but they're
     expensive. Most databases use Index-Range Locks (Next-Key Locking)
     as a practical compromise.

     MySQL InnoDB's "Repeatable Read" uses Next-Key Locking, which is
     why it's closer to Serializability than the SQL standard suggests.
    """)


def demo_5_2pl_vs_snapshot_isolation():
    """
    Demo 5: Compare 2PL with Snapshot Isolation.

    DDIA concept: "Under 2PL, writers block readers, and readers block writers.
    This is different from Snapshot Isolation, where readers never block
    writers, and writers never block readers."
    """
    print_header("DEMO 5: 2PL vs Snapshot Isolation")
    print("""
    Two different approaches to serializability:

    2PL (Pessimistic):
      • Lock before accessing data
      • Readers block writers, writers block readers
      • Guaranteed no conflicts, but causes blocking
      • Used by: MySQL InnoDB, PostgreSQL (SERIALIZABLE)

    Snapshot Isolation (Optimistic):
      • Read from snapshot, no locks
      • Readers never block writers
      • Detect conflicts at commit time
      • Used by: PostgreSQL (SSI), Oracle, CockroachDB
    """)

    print("""
    Performance comparison:

    2PL:
      ✅ Guaranteed throughput (no aborts)
      ❌ High latency (blocking)
      ❌ Deadlocks
      ❌ Doesn't scale well

    Snapshot Isolation:
      ✅ Low latency (no blocking)
      ✅ No deadlocks
      ✅ Scales better
      ❌ Higher abort rate under contention
      ❌ Requires application retry logic
    """)

    print("""
  💡 KEY INSIGHT (DDIA):
     2PL is the traditional approach (used for ~30 years).
     Snapshot Isolation is newer and often better for modern workloads.

     The choice depends on your workload:
     • Low contention? Use Snapshot Isolation (better latency)
     • High contention? Use 2PL (fewer aborts)
    """)


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 80)
    print("  EXERCISE 2: TWO-PHASE LOCKING (2PL)")
    print("  DDIA Chapter 7: 'Serializability - Technique 2'")
    print("=" * 80)
    print("""
  This exercise demonstrates TWO-PHASE LOCKING:
  - Writers block readers, readers block writers
  - Shared locks for reads, exclusive locks for writes
  - Prevents all concurrency anomalies but causes deadlocks
    """)

    demo_1_shared_and_exclusive_locks()
    demo_2_lock_upgrade()
    demo_3_deadlock_detection()
    demo_4_predicate_locks()
    demo_5_2pl_vs_snapshot_isolation()

    print("\n" + "=" * 80)
    print("  EXERCISE 2 COMPLETE ✅")
    print("=" * 80)
    print("""
  Key Takeaways:

  1. 🔒 Shared locks for reads, exclusive locks for writes
  2. 🔄 Readers block writers, writers block readers
  3. ⚠️  Deadlocks are a major problem
  4. 🎯 Predicate locks prevent phantoms (but expensive)
  5. 📊 2PL is pessimistic: lock before accessing

  Next: Run 03_serializable_snapshot_isolation.py to learn about SSI
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
