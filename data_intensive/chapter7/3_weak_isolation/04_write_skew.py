"""
Exercise 4: Write Skew and Phantoms

DDIA Reference: Chapter 7, "Weak Isolation Levels" (pp. 250-258)

This exercise demonstrates WRITE SKEW and PHANTOM problems:
  - Write skew: two txns read overlapping data, write to different objects
  - Result violates application-level invariant
  - Phantom: a write changes the result of a search query
  - Neither Read Committed nor Snapshot Isolation prevents this
  - Solution: Serializability (next chapter)

Key concepts:
  - Write skew: generalized version of lost update
  - Phantom: write changes result of earlier SELECT
  - Can't lock rows that don't exist yet
  - Materializing conflicts: artificial objects to lock
  - True serializability needed for correctness

Run: python 04_write_skew.py
"""

import sys
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass

sys.stdout.reconfigure(encoding='utf-8')


# =============================================================================
# CORE COMPONENTS: Transaction, Database
# =============================================================================

@dataclass
class Doctor:
    name: str
    on_call: bool


class WriteSkewDatabase:
    """Database demonstrating write skew and phantom problems."""

    def __init__(self):
        self.doctors: Dict[str, Doctor] = {}
        self.operation_log: List[str] = []

    def add_doctor(self, name: str, on_call: bool = True):
        self.doctors[name] = Doctor(name, on_call)

    def count_on_call(self) -> int:
        return sum(1 for d in self.doctors.values() if d.on_call)

    def set_on_call(self, name: str, on_call: bool):
        if name in self.doctors:
            self.doctors[name].on_call = on_call

    def _log(self, message: str):
        self.operation_log.append(message)
        print(message)

    def print_state(self):
        print("\n  📊 Doctor Status:")
        for name, doctor in self.doctors.items():
            status = "ON CALL" if doctor.on_call else "OFF CALL"
            print(f"    {name}: {status}")
        print(f"    Total on call: {self.count_on_call()}")


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


def demo_1_write_skew_problem():
    """
    Demo 1: Show the write skew problem.

    DDIA concept: "Write Skew is a more subtle and generalized version
    of the Lost Update. It occurs when two transactions read overlapping
    data, make decisions based on what they read, and then write to
    DIFFERENT objects."
    """
    print_header("DEMO 1: The Write Skew Problem")
    print("""
    Scenario: A hospital requires at least one doctor on call at all times.
    Two doctors (Alice and Bob) are both on call.
    Both click "take myself off call" at the same time.

    Under Snapshot Isolation: BOTH go off call! Invariant is BROKEN!
    """)

    db = WriteSkewDatabase()
    db.add_doctor("Alice", on_call=True)
    db.add_doctor("Bob", on_call=True)

    print_section("Initial State")
    db.print_state()
    print(f"  Invariant: At least 1 doctor must be on call")

    # Transaction A: Alice takes herself off call
    print_section("Transaction A: Alice checks if she can go off call")
    print(f"  SELECT COUNT(*) FROM doctors WHERE on_call = TRUE")
    currently_on_call_a = db.count_on_call()
    print(f"  Result: {currently_on_call_a} doctors on call")

    if currently_on_call_a >= 2:
        print(f"  ✅ At least 2 on call, Alice can go off call")
        print(f"  (Txn A has NOT committed yet)")
    else:
        print(f"  ❌ Only 1 on call, Alice cannot go off call")

    # Transaction B: Bob takes himself off call
    print_section("Transaction B: Bob checks if he can go off call")
    print(f"  SELECT COUNT(*) FROM doctors WHERE on_call = TRUE")
    currently_on_call_b = db.count_on_call()
    print(f"  Result: {currently_on_call_b} doctors on call")

    if currently_on_call_b >= 2:
        print(f"  ✅ At least 2 on call, Bob can go off call")
        print(f"  (Txn B has NOT committed yet)")
    else:
        print(f"  ❌ Only 1 on call, Bob cannot go off call")

    # Both commit
    print_section("Both transactions commit")
    db.set_on_call("Alice", False)
    print(f"  Txn A: UPDATE doctors SET on_call = FALSE WHERE name = 'Alice'")
    db.set_on_call("Bob", False)
    print(f"  Txn B: UPDATE doctors SET on_call = FALSE WHERE name = 'Bob'")

    print_section("Final State")
    db.print_state()
    print(f"  ❌ INVARIANT VIOLATED! Nobody is on call!")

    print("""
  💡 KEY INSIGHT (DDIA):
     Write skew occurs because:
       1. Both txns read: count = 2
       2. Both txns decide: OK to go off call
       3. Txn A writes: Alice off call
       4. Txn B writes: Bob off call
       5. Result: count = 0 (invariant broken!)

     Why this is hard:
       • Neither Read Committed nor Snapshot Isolation prevents this
       • Each txn reads a VALID snapshot
       • Each txn makes a VALID decision
       • But the COMBINATION violates the invariant
    """)


def demo_2_phantom_problem():
    """
    Demo 2: Show the phantom problem.

    DDIA concept: "In many cases, Write Skew follows this pattern:
    1. A SELECT query checks whether some condition is met
    2. Based on the result, the application decides to write
    3. The write CHANGES THE RESULT of the earlier SELECT"
    """
    print_header("DEMO 2: The Phantom Problem")
    print("""
    Scenario: Booking a meeting room.
    Transaction A checks if a time slot is available.
    Transaction B books the same time slot.
    Transaction A's check is now invalid!
    """)

    print_section("Pseudocode")
    print("""
    Transaction A:                    Transaction B:
      BEGIN;
      SELECT * FROM bookings
      WHERE room = 'A' AND
            time = '2pm'
      (returns 0 rows)
                                      BEGIN;
                                      INSERT INTO bookings
                                      VALUES (room='A', time='2pm')
                                      COMMIT;
      if (no_conflicts):
        INSERT INTO bookings
        VALUES (room='A', time='2pm')
      COMMIT;
      (CONFLICT! But we didn't detect it)
    """)

    print_section("The Problem")
    print("""
    The key issue: You can't lock rows that DON'T EXIST YET!

    With SELECT ... FOR UPDATE:
      • You can lock existing rows
      • But you can't lock the ABSENCE of rows
      • So Txn B can insert a new row that conflicts with Txn A's check
    """)

    print("""
  💡 KEY INSIGHT (DDIA):
     Phantom problem:
       • A write in one txn changes the result of a SELECT in another
       • Can't use SELECT ... FOR UPDATE to prevent this
       • The conflicting row doesn't exist when we try to lock it
       • Solution: Serializability (next chapter)
    """)


def demo_3_materializing_conflicts():
    """
    Demo 3: Show materializing conflicts (ugly workaround).

    DDIA concept: "One possible solution: Artificially create objects
    that you can lock. For example, create a table of time slots for
    the next 6 months. To book a meeting room, you attempt to lock
    the specific time-slot row."
    """
    print_header("DEMO 3: Materializing Conflicts (Workaround)")
    print("""
    One way to prevent phantoms: artificially create objects to lock.
    """)

    print_section("Approach")
    print("""
    Instead of checking if a time slot is available:
      SELECT * FROM bookings WHERE room = 'A' AND time = '2pm'

    Create a table of all possible time slots:
      CREATE TABLE time_slots (
        room VARCHAR,
        time VARCHAR,
        PRIMARY KEY (room, time)
      )

    Then lock the specific time slot:
      SELECT * FROM time_slots
      WHERE room = 'A' AND time = '2pm'
      FOR UPDATE;

      -- If we get here, we have the lock
      -- Now we can safely check and insert
    """)

    print_section("Pros and Cons")
    print("""
    Pros:
      ✅ Prevents phantoms
      ✅ Works with existing databases

    Cons:
      ❌ Ugly: leaks concurrency control into data model
      ❌ Requires pre-creating all possible time slots
      ❌ Doesn't scale well (millions of time slots?)
      ❌ Hard to maintain
    """)

    print("""
  💡 KEY INSIGHT (DDIA):
     Materializing conflicts is a workaround, not a solution.
     True Serializability is much cleaner.
    """)


def demo_4_write_skew_examples():
    """
    Demo 4: Show real-world examples of write skew.

    DDIA concept: "Write skew is subtle and can cause real bugs."
    """
    print_header("DEMO 4: Real-World Write Skew Examples")
    print("""
    Write skew appears in many real-world scenarios.
    """)

    print_section("Example 1: Meeting Room Booking")
    print("""
    Invariant: No two meetings in the same room at the same time

    Txn A:                            Txn B:
      SELECT * FROM meetings
      WHERE room = 'A' AND
            time = '2pm'
      (no conflicts)
                                      SELECT * FROM meetings
                                      WHERE room = 'A' AND
                                            time = '2pm'
                                      (no conflicts)
      INSERT meeting (room='A', time='2pm')
                                      INSERT meeting (room='A', time='2pm')
      COMMIT;
                                      COMMIT;
      (CONFLICT! Two meetings at same time)
    """)

    print_section("Example 2: Multiplayer Game")
    print("""
    Invariant: Player can't move to two places at once

    Txn A:                            Txn B:
      SELECT position FROM players
      WHERE id = 1
      (position = 'A')
                                      SELECT position FROM players
                                      WHERE id = 1
                                      (position = 'A')
      UPDATE players SET position='B'
                                      UPDATE players SET position='C'
      COMMIT;
                                      COMMIT;
      (Player is now at 'C', but Txn A thought they were at 'A')
    """)

    print_section("Example 3: Inventory Management")
    print("""
    Invariant: Can't sell more items than in stock

    Txn A:                            Txn B:
      SELECT quantity FROM inventory
      WHERE item = 'X'
      (quantity = 10)
                                      SELECT quantity FROM inventory
                                      WHERE item = 'X'
                                      (quantity = 10)
      UPDATE inventory SET quantity=5
      (sold 5 items)
                                      UPDATE inventory SET quantity=8
                                      (sold 2 items)
      COMMIT;
                                      COMMIT;
      (Sold 7 items total, but only 10 in stock - OK)
      (But what if we had 5 in stock? We'd oversell!)
    """)

    print("""
  💡 KEY INSIGHT (DDIA):
     Write skew is common in:
       • Booking systems
       • Inventory management
       • Multiplayer games
       • Financial systems
       • Any system with invariants
    """)


def demo_5_isolation_levels_summary():
    """
    Demo 5: Summary of isolation levels and what they prevent.
    """
    print_header("DEMO 5: Isolation Levels Summary")
    print("""
    Comparison of all isolation levels.
    """)

    print_section("Anomalies Prevented by Each Level")
    print(f"""
  {'Anomaly':<25} {'RC':<10} {'SI':<10} {'2PL':<10} {'Serializable'}
  {'─'*70}
  {'Dirty reads':<25} {'✅':<10} {'✅':<10} {'✅':<10} {'✅'}
  {'Dirty writes':<25} {'✅':<10} {'✅':<10} {'✅':<10} {'✅'}
  {'Read skew':<25} {'❌':<10} {'✅':<10} {'✅':<10} {'✅'}
  {'Lost updates':<25} {'❌':<10} {'❌':<10} {'✅':<10} {'✅'}
  {'Write skew':<25} {'❌':<10} {'❌':<10} {'❌':<10} {'✅'}
  {'Phantoms':<25} {'❌':<10} {'❌':<10} {'❌':<10} {'✅'}

  RC = Read Committed
  SI = Snapshot Isolation
  2PL = Two-Phase Locking
    """)

    print_section("When to Use Each Level")
    print("""
    Read Committed:
      ✅ Default in PostgreSQL, Oracle, SQL Server
      ✅ Good for most applications
      ❌ Allows read skew, lost updates, write skew

    Snapshot Isolation:
      ✅ Prevents read skew
      ✅ Good for reporting queries
      ❌ Allows lost updates, write skew
      ✅ Used by PostgreSQL (Repeatable Read), MySQL InnoDB, Oracle

    Two-Phase Locking:
      ✅ Prevents lost updates and write skew
      ❌ Readers block writers (performance impact)
      ❌ Risk of deadlocks

    Serializability:
      ✅ Prevents all anomalies
      ✅ Strongest guarantee
      ❌ Highest performance cost
      ✅ Used by VoltDB, Redis, Datomic
    """)

    print("""
  💡 DDIA RECOMMENDATION:
     • Start with Read Committed (default)
     • If you see read skew, upgrade to Snapshot Isolation
     • If you see lost updates, use explicit locking or atomic ops
     • If you see write skew, you need Serializability
     • Most applications can get by with Snapshot Isolation + explicit locking
    """)


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 80)
    print("  EXERCISE 4: WRITE SKEW AND PHANTOMS")
    print("  DDIA Chapter 7: 'Weak Isolation Levels'")
    print("=" * 80)
    print("""
  This exercise demonstrates WRITE SKEW and PHANTOM problems.
  You'll see why neither Read Committed nor Snapshot Isolation
  can prevent these anomalies, and why Serializability is needed.
    """)

    demo_1_write_skew_problem()
    demo_2_phantom_problem()
    demo_3_materializing_conflicts()
    demo_4_write_skew_examples()
    demo_5_isolation_levels_summary()

    print("\n" + "=" * 80)
    print("  EXERCISE 4 COMPLETE ✅")
    print("=" * 80)
    print("""
  Key Takeaways:

  1. ✍️  WRITE SKEW: txns read overlapping data, write to different objects
  2. 👻 PHANTOM: a write changes the result of an earlier SELECT
  3. 🔒 Can't lock rows that don't exist yet
  4. 🏗️  Materializing conflicts: ugly workaround (not recommended)
  5. 📊 Neither Read Committed nor Snapshot Isolation prevents write skew
  6. 🎯 Need Serializability for correctness

  Next: Chapter 8 covers Serializability and real-world challenges
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
