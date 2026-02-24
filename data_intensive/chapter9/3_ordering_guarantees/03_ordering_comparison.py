"""
Comparing Ordering Guarantees: Causal vs Total vs Linearizable

Different consistency models provide different ordering guarantees:

1. Causal Consistency: Preserves cause-and-effect (partial order)
2. Total Order: Every pair of events is ordered (total order)
3. Linearizability: Total order consistent with real-time

This example shows the differences and trade-offs.
"""

from dataclasses import dataclass
from typing import List, Dict, Set, Tuple
from enum import Enum


@dataclass
class Event:
    event_id: str
    content: str
    timestamp: float
    depends_on: List[str] = None

    def __post_init__(self):
        if self.depends_on is None:
            self.depends_on = []


class OrderingComparison:
    """Compare different ordering guarantees"""

    def __init__(self):
        self.events: Dict[str, Event] = {}

    def add_event(self, event: Event) -> None:
        self.events[event.event_id] = event

    def is_causally_ordered(self, order: List[str]) -> bool:
        """Check if an order respects causal dependencies"""
        seen = set()
        for event_id in order:
            event = self.events[event_id]
            # All dependencies must be seen before this event
            for dep in event.depends_on:
                if dep not in seen:
                    return False
            seen.add(event_id)
        return True

    def is_total_order(self, order: List[str]) -> bool:
        """Check if an order is a total order (all events present)"""
        return set(order) == set(self.events.keys())

    def is_linearizable(self, order: List[str]) -> bool:
        """
        Check if an order is linearizable.
        Simplified: order must respect both causality and real-time.
        """
        if not self.is_causally_ordered(order):
            return False

        # Check real-time ordering: if A.timestamp < B.timestamp,
        # and A is not dependent on B, then A should come before B
        for i, event_id_a in enumerate(order):
            event_a = self.events[event_id_a]
            for j, event_id_b in enumerate(order):
                if i >= j:
                    continue
                event_b = self.events[event_id_b]

                # If B happened before A in real-time, and A doesn't depend on B,
                # this violates linearizability
                if event_b.timestamp < event_a.timestamp:
                    if event_id_a not in event_b.depends_on:
                        # B happened first, so B should come first
                        return False

        return True


def demo_causal_vs_total_order():
    """Show the difference between causal and total order"""
    print("=" * 70)
    print("DEMO 1: Causal Order vs Total Order")
    print("=" * 70)

    comp = OrderingComparison()

    # Create events: Q1 and Q2 are concurrent (no causal relationship)
    q1 = Event("Q1", "How to use Python?", timestamp=100.0)
    q2 = Event("Q2", "How to use JavaScript?", timestamp=101.0)
    a1 = Event("A1", "Use 'python script.py'", timestamp=105.0, depends_on=["Q1"])
    a2 = Event("A2", "Use 'node script.js'", timestamp=106.0, depends_on=["Q2"])

    comp.add_event(q1)
    comp.add_event(q2)
    comp.add_event(a1)
    comp.add_event(a2)

    print("\nEvents:")
    print("  Q1 (t=100): Question about Python")
    print("  Q2 (t=101): Question about JavaScript (concurrent with Q1)")
    print("  A1 (t=105): Answer to Q1 (depends on Q1)")
    print("  A2 (t=106): Answer to Q2 (depends on Q2)")

    # Order 1: Q1, Q2, A1, A2
    order1 = ["Q1", "Q2", "A1", "A2"]
    print(f"\nOrder 1: {order1}")
    print(f"  Causal? {comp.is_causally_ordered(order1)}")
    print(f"  Total? {comp.is_total_order(order1)}")
    print(f"  Linearizable? {comp.is_linearizable(order1)}")

    # Order 2: Q2, Q1, A2, A1 (different order for concurrent events)
    order2 = ["Q2", "Q1", "A2", "A1"]
    print(f"\nOrder 2: {order2}")
    print(f"  Causal? {comp.is_causally_ordered(order2)}")
    print(f"  Total? {comp.is_total_order(order2)}")
    print(f"  Linearizable? {comp.is_linearizable(order2)}")

    # Order 3: Q1, A1, Q2, A2 (respects causality and real-time)
    order3 = ["Q1", "A1", "Q2", "A2"]
    print(f"\nOrder 3: {order3}")
    print(f"  Causal? {comp.is_causally_ordered(order3)}")
    print(f"  Total? {comp.is_total_order(order3)}")
    print(f"  Linearizable? {comp.is_linearizable(order3)}")

    print("\n[OK] Key insight: Causal order allows concurrent events in any order")
    print("  Total order requires a single order for all events")


def demo_total_order_vs_linearizable():
    """Show the difference between total order and linearizability"""
    print("\n" + "=" * 70)
    print("DEMO 2: Total Order vs Linearizability")
    print("=" * 70)

    comp = OrderingComparison()

    # Create events with real-time constraints
    w1 = Event("W1", "Write X=1", timestamp=100.0)
    r1 = Event("R1", "Read X", timestamp=105.0, depends_on=["W1"])
    w2 = Event("W2", "Write X=2", timestamp=110.0)
    r2 = Event("R2", "Read X", timestamp=115.0, depends_on=["W2"])

    comp.add_event(w1)
    comp.add_event(r1)
    comp.add_event(w2)
    comp.add_event(r2)

    print("\nEvents (with real-time ordering):")
    print("  W1 (t=100): Write X=1")
    print("  R1 (t=105): Read X (depends on W1)")
    print("  W2 (t=110): Write X=2")
    print("  R2 (t=115): Read X (depends on W2)")

    # Order 1: W1, R1, W2, R2 (respects real-time)
    order1 = ["W1", "R1", "W2", "R2"]
    print(f"\nOrder 1: {order1}")
    print(f"  Causal? {comp.is_causally_ordered(order1)}")
    print(f"  Total? {comp.is_total_order(order1)}")
    print(f"  Linearizable? {comp.is_linearizable(order1)}")

    # Order 2: W2, W1, R1, R2 (violates real-time)
    order2 = ["W2", "W1", "R1", "R2"]
    print(f"\nOrder 2: {order2}")
    print(f"  Causal? {comp.is_causally_ordered(order2)}")
    print(f"  Total? {comp.is_total_order(order2)}")
    print(f"  Linearizable? {comp.is_linearizable(order2)}")

    print("\n[OK] Key insight: Linearizability requires total order consistent with real-time")
    print("  Total order alone doesn't guarantee real-time consistency")


def demo_ordering_hierarchy():
    """Show the hierarchy of ordering guarantees"""
    print("\n" + "=" * 70)
    print("DEMO 3: Hierarchy of Ordering Guarantees")
    print("=" * 70)

    print("""
Ordering Guarantees (from weakest to strongest):

1. EVENTUAL CONSISTENCY (No ordering guarantee)
   - Nodes may see events in different orders
   - Eventually converge (but no ordering guarantee)
   - Example: Cassandra, DynamoDB

2. CAUSAL CONSISTENCY (Partial order)
   - Preserves cause-and-effect relationships
   - Concurrent events can be in any order
   - Example: Git (DAG of commits), Riak

3. TOTAL ORDER (Total order, but not real-time)
   - All nodes see events in the same order
   - But order may not match real-time
   - Example: Single-leader replication log

4. LINEARIZABILITY (Total order + real-time)
   - All nodes see events in the same order
   - Order matches real-time
   - Example: ZooKeeper, etcd, Spanner

5. STRICT SERIALIZABILITY (Linearizability + transactions)
   - Linearizability + multi-object transactions
   - Strongest guarantee
   - Example: CockroachDB, Spanner

Trade-offs:
- Stronger guarantees → Higher latency, lower availability
- Weaker guarantees → Lower latency, higher availability
    """)


def demo_practical_implications():
    """Show practical implications of different ordering guarantees"""
    print("\n" + "=" * 70)
    print("DEMO 4: Practical Implications")
    print("=" * 70)

    print("""
Scenario: Bank transfer from Account A to Account B

EVENTUAL CONSISTENCY:
  - Debit A: -$100 (visible on some nodes)
  - Credit B: +$100 (visible on other nodes)
  - Problem: Money might disappear if you read from wrong nodes
  - Risk: High

CAUSAL CONSISTENCY:
  - Debit A: -$100 (happens first)
  - Credit B: +$100 (depends on debit)
  - Guarantee: If you see credit, you'll see debit
  - Risk: Medium (but concurrent transfers might be reordered)

TOTAL ORDER:
  - All nodes see: Debit A, then Credit B
  - Guarantee: Consistent order across all nodes
  - Risk: Low (but order might not match real-time)

LINEARIZABILITY:
  - All nodes see: Debit A, then Credit B
  - In the same order as real-time
  - Guarantee: Highest consistency
  - Risk: Very Low
  - Cost: Higher latency (need quorum writes)

STRICT SERIALIZABILITY:
  - Linearizability + multi-object transactions
  - Guarantee: Highest consistency for complex transactions
  - Risk: Minimal
  - Cost: Highest latency
    """)


def demo_ordering_in_practice():
    """Show how different systems implement ordering"""
    print("\n" + "=" * 70)
    print("DEMO 5: Ordering in Real Systems")
    print("=" * 70)

    print("""
PostgreSQL (Single-Leader Replication):
  - Writes go to primary
  - Primary writes to WAL (Write-Ahead Log)
  - Followers replicate WAL entries in order
  - Provides: Total order (all followers see same order)
  - Guarantee: Causal consistency (with synchronous replication)

Cassandra (Multi-Leader):
  - Writes can go to any node
  - Nodes use timestamps to order writes
  - Problem: Clock skew can cause wrong ordering
  - Provides: Eventual consistency
  - Guarantee: Weak (no ordering guarantee)

Kafka (Partitioned Log):
  - Each partition has a leader
  - Leader assigns sequence numbers
  - Consumers read in order
  - Provides: Total order (per partition)
  - Guarantee: Causal consistency (within partition)

ZooKeeper (Consensus):
  - Uses Zookeeper Atomic Broadcast (ZAB)
  - All writes go through leader
  - Provides: Linearizability
  - Guarantee: Strong (but higher latency)

Google Spanner (Distributed):
  - Uses TrueTime (atomic clocks)
  - Provides: Linearizability
  - Guarantee: Strong (across datacenters)
  - Cost: Very high latency
    """)


if __name__ == "__main__":
    demo_causal_vs_total_order()
    demo_total_order_vs_linearizable()
    demo_ordering_hierarchy()
    demo_practical_implications()
    demo_ordering_in_practice()

    print("\n" + "=" * 70)
    print("KEY TAKEAWAYS")
    print("=" * 70)
    print("""
1. Causal consistency: Preserves cause-and-effect (partial order)
   - Weaker than total order
   - Allows concurrent events in any order
   - Good for: Q&A forums, social media

2. Total order: All nodes see events in the same order
   - Stronger than causal
   - But order may not match real-time
   - Good for: Single-leader replication

3. Linearizability: Total order + real-time consistency
   - Strongest single-object guarantee
   - Order matches real-time
   - Good for: Distributed locks, leader election

4. Trade-off: Stronger ordering → Higher latency, lower availability
   - Choose based on your application needs
   - Most applications don't need linearizability

5. Real systems use different approaches:
   - PostgreSQL: Total order (single-leader)
   - Cassandra: Eventual consistency (multi-leader)
   - Kafka: Total order per partition
   - ZooKeeper: Linearizability (consensus)
    """)
