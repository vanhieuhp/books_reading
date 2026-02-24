"""
Causal Consistency Example

This module demonstrates causal consistency using vector clocks.
Causal consistency means: if event A causally caused event B,
then every node must see A before B.

Key characteristics:
- Preserves "happened before" relationships
- Concurrent events can be seen in any order
- Implemented using vector clocks
- Stronger than eventual, weaker than linearizability
"""

from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class VectorClock:
    """
    A vector clock tracks causality across nodes.
    Each node has a counter that increments when it processes an event.
    """
    clock: Dict[str, int] = field(default_factory=dict)

    def increment(self, node_id: str) -> None:
        """Increment the clock for a node."""
        self.clock[node_id] = self.clock.get(node_id, 0) + 1

    def merge(self, other: 'VectorClock') -> None:
        """Merge with another vector clock (take max for each node)."""
        for node_id, value in other.clock.items():
            self.clock[node_id] = max(self.clock.get(node_id, 0), value)

    def happens_before(self, other: 'VectorClock') -> bool:
        """Check if this clock happens before another."""
        if self.clock == other.clock:
            return False

        for node_id in set(self.clock.keys()) | set(other.clock.keys()):
            self_val = self.clock.get(node_id, 0)
            other_val = other.clock.get(node_id, 0)
            if self_val > other_val:
                return False

        return True

    def concurrent_with(self, other: 'VectorClock') -> bool:
        """Check if this clock is concurrent with another."""
        return not self.happens_before(other) and not other.happens_before(self)

    def __str__(self) -> str:
        items = [f"{k}:{v}" for k, v in sorted(self.clock.items())]
        return "{" + ", ".join(items) + "}"

    def copy(self) -> 'VectorClock':
        """Create a copy of this vector clock."""
        return VectorClock(dict(self.clock))


@dataclass
class Event:
    """Represents an event in the system."""
    event_id: str
    node_id: str
    data: Any
    vector_clock: VectorClock


class CausallyConsistentStore:
    """
    A causally consistent key-value store using vector clocks.

    Behavior:
    - Each node maintains a vector clock
    - Events are tagged with vector clocks
    - Events are delivered in causal order
    - Concurrent events can be in any order
    """

    def __init__(self, node_id: str, all_nodes: List[str]):
        self.node_id = node_id
        self.all_nodes = all_nodes
        self.vector_clock = VectorClock({node: 0 for node in all_nodes})
        self.data: Dict[str, Any] = {}
        self.event_log: List[Event] = []
        self.peers: Dict[str, 'CausallyConsistentStore'] = {}

    def add_peer(self, node_id: str, node: 'CausallyConsistentStore') -> None:
        """Register a peer node."""
        self.peers[node_id] = node

    def write(self, key: str, value: Any) -> Event:
        """
        Write a value and create an event with the current vector clock.
        """
        # Increment our own clock
        self.vector_clock.increment(self.node_id)

        # Create event
        event = Event(
            event_id=f"{self.node_id}-{len(self.event_log)}",
            node_id=self.node_id,
            data={"key": key, "value": value},
            vector_clock=self.vector_clock.copy()
        )

        # Store locally
        self.data[key] = value
        self.event_log.append(event)

        print(f"[{self.node_id}] Write: {key} = {value}")
        print(f"  Vector Clock: {event.vector_clock}")

        return event

    def receive_event(self, event: Event) -> None:
        """
        Receive an event from another node.
        Update vector clock to maintain causality.
        """
        # Merge the received vector clock
        self.vector_clock.merge(event.vector_clock)

        # Increment our own clock
        self.vector_clock.increment(self.node_id)

        # Store the event
        self.event_log.append(event)
        self.data[event.data["key"]] = event.data["value"]

        print(f"[{self.node_id}] Received event from {event.node_id}: {event.data['key']} = {event.data['value']}")
        print(f"  Vector Clock: {self.vector_clock}")

    def send_event_to_peer(self, peer_id: str, event: Event) -> None:
        """Send an event to a peer node."""
        if peer_id in self.peers:
            self.peers[peer_id].receive_event(event)

    def get_state(self) -> Dict[str, Any]:
        """Get the current state of this node."""
        return dict(self.data)

    def get_event_log(self) -> List[str]:
        """Get the event log for debugging."""
        return [f"{e.event_id}: {e.data}" for e in self.event_log]


def demo_causal_consistency():
    """
    Demonstrate causal consistency with vector clocks.
    """
    print("=" * 70)
    print("CAUSAL CONSISTENCY DEMO (Vector Clocks)")
    print("=" * 70)

    # Create 3 nodes
    node_a = CausallyConsistentStore("Node-A", ["Node-A", "Node-B", "Node-C"])
    node_b = CausallyConsistentStore("Node-B", ["Node-A", "Node-B", "Node-C"])
    node_c = CausallyConsistentStore("Node-C", ["Node-A", "Node-B", "Node-C"])

    # Set up peer relationships
    node_a.add_peer("Node-B", node_b)
    node_a.add_peer("Node-C", node_c)
    node_b.add_peer("Node-A", node_a)
    node_b.add_peer("Node-C", node_c)
    node_c.add_peer("Node-A", node_a)
    node_c.add_peer("Node-B", node_b)

    print("\n1. Alice writes x=1 on Node-A")
    event1 = node_a.write("x", 1)

    print("\n2. Alice sends the event to Node-B")
    node_a.send_event_to_peer("Node-B", event1)

    print("\n3. Bob reads x on Node-B (sees Alice's write)")
    print(f"   Bob sees: x = {node_b.data.get('x')}")

    print("\n4. Bob writes y=2 on Node-B (depends on Alice's write)")
    event2 = node_b.write("y", 2)

    print("\n5. Bob sends the event to Node-C")
    node_b.send_event_to_peer("Node-C", event2)

    print("\n6. Charlie reads on Node-C")
    print(f"   Charlie sees: x = {node_c.data.get('x')}, y = {node_c.data.get('y')}")

    print("\n" + "=" * 70)
    print("CAUSAL ORDER PRESERVED")
    print("=" * 70)
    print("Alice's write (x=1) happened before Bob's write (y=2)")
    print("Every node that sees Bob's write also sees Alice's write")
    print("This is causal consistency!")


def demo_concurrent_events():
    """
    Demonstrate how concurrent events can be in any order.
    """
    print("\n\n" + "=" * 70)
    print("CONCURRENT EVENTS (Can be in any order)")
    print("=" * 70)

    # Create 2 nodes
    node_a = CausallyConsistentStore("Node-A", ["Node-A", "Node-B"])
    node_b = CausallyConsistentStore("Node-B", ["Node-A", "Node-B"])

    node_a.add_peer("Node-B", node_b)
    node_b.add_peer("Node-A", node_a)

    print("\n1. Alice writes x=1 on Node-A")
    event1 = node_a.write("x", 1)

    print("\n2. Bob writes y=2 on Node-B (at the same time, different node)")
    event2 = node_b.write("y", 2)

    print("\n3. These events are CONCURRENT (neither caused the other)")
    print(f"   Event1 clock: {event1.vector_clock}")
    print(f"   Event2 clock: {event2.vector_clock}")
    print(f"   Concurrent: {event1.vector_clock.concurrent_with(event2.vector_clock)}")

    print("\n4. Node-A receives Event2 from Node-B")
    node_a.receive_event(event2)

    print("\n5. Node-B receives Event1 from Node-A")
    node_b.receive_event(event1)

    print("\n6. Final state")
    print(f"   Node-A: {node_a.get_state()}")
    print(f"   Node-B: {node_b.get_state()}")

    print("\n" + "-" * 70)
    print("Key Point:")
    print("- Node-A sees: x=1, then y=2")
    print("- Node-B sees: y=2, then x=1")
    print("- Both orders are valid because x and y are concurrent")
    print("- This is allowed in causal consistency")


def demo_question_answer():
    """
    Demonstrate causal consistency with question-answer scenario.
    """
    print("\n\n" + "=" * 70)
    print("QUESTION-ANSWER SCENARIO (Causal Dependency)")
    print("=" * 70)

    # Create 3 nodes
    node_a = CausallyConsistentStore("Node-A", ["Node-A", "Node-B", "Node-C"])
    node_b = CausallyConsistentStore("Node-B", ["Node-A", "Node-B", "Node-C"])
    node_c = CausallyConsistentStore("Node-C", ["Node-A", "Node-B", "Node-C"])

    node_a.add_peer("Node-B", node_b)
    node_a.add_peer("Node-C", node_c)
    node_b.add_peer("Node-A", node_a)
    node_b.add_peer("Node-C", node_c)
    node_c.add_peer("Node-A", node_a)
    node_c.add_peer("Node-B", node_b)

    print("\n1. Alice posts question on Node-A")
    question = node_a.write("post:1", "What is 2+2?")

    print("\n2. Alice sends question to Node-B")
    node_a.send_event_to_peer("Node-B", question)

    print("\n3. Bob reads question on Node-B and posts answer")
    print(f"   Bob sees: {node_b.data.get('post:1')}")
    answer = node_b.write("post:2", "The answer is 4")

    print("\n4. Bob sends answer to Node-C")
    node_b.send_event_to_peer("Node-C", answer)

    print("\n5. Charlie reads on Node-C")
    print(f"   Charlie sees question: {node_c.data.get('post:1')}")
    print(f"   Charlie sees answer: {node_c.data.get('post:2')}")

    print("\n" + "-" * 70)
    print("Key Point:")
    print("- Charlie sees the question BEFORE the answer")
    print("- This is guaranteed by causal consistency")
    print("- The answer causally depends on the question")
    print("- Every node respects this dependency")


def demo_vector_clock_ordering():
    """
    Demonstrate how vector clocks determine event ordering.
    """
    print("\n\n" + "=" * 70)
    print("VECTOR CLOCK ORDERING")
    print("=" * 70)

    # Create 2 nodes
    node_a = CausallyConsistentStore("Node-A", ["Node-A", "Node-B"])
    node_b = CausallyConsistentStore("Node-B", ["Node-A", "Node-B"])

    node_a.add_peer("Node-B", node_b)
    node_b.add_peer("Node-A", node_a)

    print("\n1. Alice writes x=1 on Node-A")
    event1 = node_a.write("x", 1)
    print(f"   Vector Clock: {event1.vector_clock}")

    print("\n2. Alice sends to Node-B")
    node_a.send_event_to_peer("Node-B", event1)

    print("\n3. Bob writes y=2 on Node-B (after seeing Alice's write)")
    event2 = node_b.write("y", 2)
    print(f"   Vector Clock: {event2.vector_clock}")

    print("\n4. Check ordering")
    print(f"   Event1 happens before Event2: {event1.vector_clock.happens_before(event2.vector_clock)}")
    print(f"   Event2 happens before Event1: {event2.vector_clock.happens_before(event1.vector_clock)}")
    print(f"   Concurrent: {event1.vector_clock.concurrent_with(event2.vector_clock)}")

    print("\n" + "-" * 70)
    print("Vector Clock Interpretation:")
    print(f"   Event1: {event1.vector_clock} = Alice has done 1 thing, Bob has done 0")
    print(f"   Event2: {event2.vector_clock} = Alice has done 1 thing, Bob has done 1")
    print("   Event2's clock is >= Event1's clock in all dimensions")
    print("   This means Event1 happened before Event2")


if __name__ == "__main__":
    demo_causal_consistency()
    demo_concurrent_events()
    demo_question_answer()
    demo_vector_clock_ordering()
