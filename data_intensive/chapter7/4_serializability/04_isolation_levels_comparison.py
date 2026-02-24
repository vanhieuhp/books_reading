"""
Exercise 4: Isolation Levels Comparison

DDIA Reference: Chapter 7, "Summary: Isolation Levels Comparison" (pp. 345-350)

This exercise compares all isolation levels and serializability techniques.

Key concepts:
  - Read Uncommitted: No protection
  - Read Committed: No dirty reads/writes
  - Snapshot Isolation: No read skew
  - Serializable: No anomalies
  - Three techniques: Serial, 2PL, SSI

Run: python 04_isolation_levels_comparison.py
"""

import sys

sys.stdout.reconfigure(encoding='utf-8')


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


def demo_1_isolation_levels_table():
    """
    Demo 1: Show the isolation levels comparison table.

    DDIA concept: "Full serializability is expensive. Most databases
    therefore offer 'weaker' isolation levels."
    """
    print_header("DEMO 1: Isolation Levels Comparison")
    print("""
    Different isolation levels provide different guarantees:
    """)

    print("""
    ┌──────────────────────┬──────────┬──────────┬──────────┬──────────┬──────────┐
    │ Isolation Level      │ Dirty    │ Dirty    │ Read     │ Lost     │ Write    │
    │                      │ Read     │ Write    │ Skew     │ Update   │ Skew /   │
    │                      │          │          │ (Non-Rep)│          │ Phantom  │
    ├──────────────────────┼──────────┼──────────┼──────────┼──────────┼──────────┤
    │ Read Uncommitted     │ ✗        │ ✗        │ ✗        │ ✗        │ ✗        │
    │ Read Committed       │ ✓        │ ✓        │ ✗        │ ✗        │ ✗        │
    │ Snapshot Isolation   │ ✓        │ ✓        │ ✓        │ ✗*       │ ✗        │
    │ Serializable         │ ✓        │ ✓        │ ✓        │ ✓        │ ✓        │
    └──────────────────────┴──────────┴──────────┴──────────┴──────────┴──────────┘

    ✓ = Prevented
    ✗ = Possible
    * = Some databases (PostgreSQL, Oracle) auto-detect lost updates
    """)

    print("""
    Anomalies explained:

    1. Dirty Read: Reading uncommitted data from another transaction
    2. Dirty Write: Overwriting uncommitted data from another transaction
    3. Read Skew: Seeing data from two different points in time
    4. Lost Update: Two read-modify-write cycles, one overwrites the other
    5. Write Skew: Two transactions read, decide independently, write to different objects
    6. Phantom: A write changes the result of another transaction's query
    """)


def demo_2_real_world_defaults():
    """
    Demo 2: Show real-world database defaults.

    DDIA concept: "Most databases default to Read Committed or Snapshot Isolation,
    not Serializable."
    """
    print_header("DEMO 2: Real-World Database Defaults")
    print("""
    Different databases have different defaults:
    """)

    print("""
    ┌──────────────────┬──────────────────────────┬──────────────────────────┐
    │ Database         │ Default Isolation Level  │ Serializable Available?  │
    ├──────────────────┼──────────────────────────┼──────────────────────────┤
    │ PostgreSQL       │ Read Committed           │ Yes (SSI since v9.1)     │
    │ MySQL (InnoDB)   │ Repeatable Read          │ Yes (2PL)                │
    │ Oracle           │ Read Committed           │ Yes (Snapshot Isolation) │
    │ SQL Server       │ Read Committed           │ Yes (2PL or Snapshot)    │
    │ CockroachDB      │ Serializable (SSI)       │ Yes (default!)           │
    │ MongoDB          │ Read Uncommitted*        │ Multi-doc txn since 4.0  │
    └──────────────────┴──────────────────────────┴──────────────────────────┘

    * MongoDB's default for single-document reads is effectively Read Uncommitted
      from a multi-document perspective.
    """)

    print("""
    Why not default to Serializable?

    1. Performance: Serializability has a cost
       • 2PL: Blocking, deadlocks, reduced throughput
       • SSI: Higher abort rate under contention

    2. Complexity: Serializability is harder to implement correctly

    3. Workload: Most applications don't need full serializability
       • Read Committed is sufficient for many workloads
       • Snapshot Isolation is good for OLTP
    """)


def demo_3_choosing_isolation_level():
    """
    Demo 3: Guide for choosing isolation level.

    DDIA concept: "The choice depends on your workload and requirements."
    """
    print_header("DEMO 3: Choosing an Isolation Level")
    print("""
    Decision tree for choosing isolation level:
    """)

    print("""
    1. Do you need to prevent dirty reads?
       → Yes: Use at least Read Committed
       → No: Read Uncommitted (rare, only for analytics)

    2. Do you need to prevent read skew?
       → Yes: Use at least Snapshot Isolation
       → No: Read Committed is fine

    3. Do you need to prevent lost updates and write skew?
       → Yes: Use Serializable
       → No: Snapshot Isolation is fine

    4. Can you tolerate occasional aborts?
       → Yes: Use SSI (better latency)
       → No: Use 2PL (guaranteed throughput)
    """)

    print("""
    Common scenarios:

    OLTP (Online Transaction Processing):
      • Many concurrent transactions
      • Short transactions
      • Recommendation: Snapshot Isolation or SSI
      • Why: Good throughput, low latency

    OLAP (Online Analytical Processing):
      • Few concurrent transactions
      • Long-running queries
      • Recommendation: Read Committed or Snapshot Isolation
      • Why: Queries don't need to block each other

    Financial Systems:
      • Need strong consistency
      • Can tolerate lower throughput
      • Recommendation: Serializable (2PL or SSI)
      • Why: Prevent all anomalies

    Social Media:
      • High throughput needed
      • Some inconsistency acceptable
      • Recommendation: Snapshot Isolation
      • Why: Good balance of consistency and performance
    """)


def demo_4_serializability_techniques_comparison():
    """
    Demo 4: Compare the three serializability techniques.

    DDIA concept: "There are three main techniques for achieving Serializability."
    """
    print_header("DEMO 4: Serializability Techniques Comparison")
    print("""
    Three techniques to achieve Serializability:
    """)

    print("""
    1. ACTUAL SERIAL EXECUTION
    ┌─────────────────────────────────────────────────────────────┐
    │ How: Execute transactions one at a time, single thread      │
    │ Pros:                                                       │
    │   ✓ Simple to understand and implement                      │
    │   ✓ No deadlocks                                            │
    │   ✓ Predictable latency                                     │
    │ Cons:                                                       │
    │   ✗ Limited throughput (single CPU core)                    │
    │   ✗ Doesn't scale to multiple cores                         │
    │ Best for:                                                   │
    │   • Short transactions                                      │
    │   • In-memory data                                          │
    │   • Low write throughput                                    │
    │ Used by: VoltDB, Redis, Datomic                             │
    └─────────────────────────────────────────────────────────────┘

    2. TWO-PHASE LOCKING (2PL)
    ┌─────────────────────────────────────────────────────────────┐
    │ How: Lock before accessing, release at commit               │
    │ Pros:                                                       │
    │   ✓ Guaranteed throughput (no aborts)                       │
    │   ✓ Works with long transactions                            │
    │ Cons:                                                       │
    │   ✗ Readers block writers, writers block readers            │
    │   ✗ Deadlocks possible                                      │
    │   ✗ High latency due to blocking                            │
    │ Best for:                                                   │
    │   • High contention workloads                               │
    │   • Need guaranteed throughput                              │
    │ Used by: MySQL InnoDB, PostgreSQL (SERIALIZABLE)            │
    └─────────────────────────────────────────────────────────────┘

    3. SERIALIZABLE SNAPSHOT ISOLATION (SSI)
    ┌─────────────────────────────────────────────────────────────┐
    │ How: Execute freely, detect conflicts at commit             │
    │ Pros:                                                       │
    │   ✓ No blocking, no deadlocks                               │
    │   ✓ Low latency                                             │
    │   ✓ Scales well to multiple cores                           │
    │ Cons:                                                       │
    │   ✗ Higher abort rate under contention                      │
    │   ✗ Requires application retry logic                        │
    │ Best for:                                                   │
    │   • Low contention workloads                                │
    │   • Need low latency                                        │
    │ Used by: PostgreSQL (SSI), CockroachDB, FoundationDB        │
    └─────────────────────────────────────────────────────────────┘
    """)

    print("""
    Performance comparison:

    Low Contention (different keys):
      Serial Execution: ✓ Good throughput
      2PL:             ✓ Good throughput, but some blocking
      SSI:             ✓✓ Best latency, no blocking

    High Contention (same key):
      Serial Execution: ✗ Bottleneck
      2PL:             ✓ Guaranteed throughput
      SSI:             ✗ High abort rate
    """)


def demo_5_practical_advice():
    """
    Demo 5: Practical advice for using transactions.

    DDIA concept: "Understanding the trade-offs is crucial for building
    correct and performant systems."
    """
    print_header("DEMO 5: Practical Advice")
    print("""
    Best practices for using transactions:
    """)

    print("""
    1. UNDERSTAND YOUR ISOLATION LEVEL
       • Don't assume Serializable if you're using Read Committed
       • Read the documentation for your database
       • Test your application with the actual isolation level

    2. KEEP TRANSACTIONS SHORT
       • Long transactions hold locks longer
       • Increases contention and deadlock risk
       • Move non-database work outside the transaction

    3. HANDLE RETRIES PROPERLY
       • Implement exponential backoff
       • Don't retry on permanent errors (constraint violations)
       • Only retry on transient errors (deadlock, timeout)

    4. AVOID DEADLOCKS
       • Access resources in a consistent order
       • Use timeouts to detect deadlocks
       • Consider using SSI to avoid deadlocks entirely

    5. TEST CONCURRENCY
       • Test with multiple concurrent transactions
       • Use tools to simulate failures and race conditions
       • Don't rely on single-threaded testing

    6. MONITOR PERFORMANCE
       • Track transaction latency and abort rate
       • Monitor lock contention
       • Adjust isolation level if needed

    7. DOCUMENT YOUR ASSUMPTIONS
       • Document which isolation level you're using
       • Document which anomalies you're protecting against
       • Document which anomalies you're accepting
    """)

    print("""
    Common mistakes:

    ✗ Assuming Serializable when using Read Committed
    ✗ Holding locks for too long
    ✗ Not handling retries
    ✗ Accessing resources in inconsistent order
    ✗ Not testing concurrency
    ✗ Ignoring deadlock warnings
    ✗ Using Serializable when Read Committed is sufficient
    """)


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 80)
    print("  EXERCISE 4: ISOLATION LEVELS COMPARISON")
    print("  DDIA Chapter 7: 'Summary and Practical Advice'")
    print("=" * 80)
    print("""
  This exercise compares all isolation levels and serializability techniques.
    """)

    demo_1_isolation_levels_table()
    demo_2_real_world_defaults()
    demo_3_choosing_isolation_level()
    demo_4_serializability_techniques_comparison()
    demo_5_practical_advice()

    print("\n" + "=" * 80)
    print("  EXERCISE 4 COMPLETE ✅")
    print("=" * 80)
    print("""
  Key Takeaways:

  1. 📊 Different isolation levels prevent different anomalies
  2. 🗄️  Most databases default to Read Committed or Snapshot Isolation
  3. 🔒 Serializability has a performance cost
  4. ⚙️  Three techniques: Serial, 2PL, SSI
  5. 🎯 Choose based on your workload and requirements

  Next: Read README.md for complete guide and real-world examples
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
