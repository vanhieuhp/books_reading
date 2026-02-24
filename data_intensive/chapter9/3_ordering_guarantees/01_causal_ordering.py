"""
Causal Ordering: Understanding Partial Orders

In a distributed system, events can be causally related (one caused the other)
or concurrent (neither caused the other).

Causal ordering preserves the "happened-before" relationship:
- If event A causally caused event B, all nodes must see A before B
- If events are concurrent, they can be seen in any order

This is a PARTIAL ORDER: some pairs are ordered, some are not.
"""

from dataclasses import dataclass
from typing import List, Dict, Set
from enum import Enum


class EventType(Enum):
    QUESTION_POSTED = "question_posted"
    ANSWER_POSTED = "answer_posted"
    COMMENT_ADDED = "comment_added"


@dataclass
class Event:
    """Represents an event in the system"""
    event_id: str
    event_type: EventType
    content: str
    timestamp: int
    node_id: str
    depends_on: List[str] = None  # IDs of events this depends on

    def __post_init__(self):
        if self.depends_on is None:
            self.depends_on = []


class CausalOrderingDemo:
    """
    Demonstrates causal ordering in a distributed system.

    Scenario: A Q&A forum where:
    - User A posts a question
    - User B posts an answer (depends on the question)
    - User C posts a comment (depends on the answer)

    Causal ordering ensures all nodes see: Question -> Answer -> Comment
    """

    def __init__(self):
        self.events: Dict[str, Event] = {}
        self.node_logs: Dict[str, List[str]] = {}  # node_id -> list of event_ids

    def add_event(self, event: Event) -> None:
        """Add an event to the system"""
        self.events[event.event_id] = event
        print(f"Event created: {event.event_id} ({event.event_type.value})")
        print(f"  Content: {event.content}")
        if event.depends_on:
            print(f"  Depends on: {event.depends_on}")

    def replicate_to_node(self, node_id: str, event_id: str) -> bool:
        """
        Replicate an event to a node, respecting causal ordering.

        Returns True if replication succeeded, False if dependencies not met.
        """
        if node_id not in self.node_logs:
            self.node_logs[node_id] = []

        event = self.events[event_id]

        # Check if all dependencies are already on this node
        for dep_id in event.depends_on:
            if dep_id not in self.node_logs[node_id]:
                print(f"  [FAIL] Cannot replicate {event_id} to {node_id}: "
                      f"dependency {dep_id} not yet present")
                return False

        # All dependencies satisfied, replicate the event
        self.node_logs[node_id].append(event_id)
        print(f"  [OK] Replicated {event_id} to {node_id}")
        return True

    def get_node_view(self, node_id: str) -> List[Event]:
        """Get the ordered view of events on a node"""
        if node_id not in self.node_logs:
            return []
        return [self.events[eid] for eid in self.node_logs[node_id]]

    def print_node_view(self, node_id: str) -> None:
        """Print the causal order of events on a node"""
        events = self.get_node_view(node_id)
        print(f"\nNode {node_id} view:")
        for i, event in enumerate(events, 1):
            print(f"  {i}. {event.event_id}: {event.content}")


def demo_basic_causal_ordering():
    """Demonstrate basic causal ordering"""
    print("=" * 70)
    print("DEMO 1: Basic Causal Ordering")
    print("=" * 70)

    demo = CausalOrderingDemo()

    # Create events with causal dependencies
    q1 = Event(
        event_id="Q1",
        event_type=EventType.QUESTION_POSTED,
        content="How do I use Python?",
        timestamp=100,
        node_id="user_a"
    )

    a1 = Event(
        event_id="A1",
        event_type=EventType.ANSWER_POSTED,
        content="Use 'python script.py'",
        timestamp=105,
        node_id="user_b",
        depends_on=["Q1"]  # Answer depends on question
    )

    c1 = Event(
        event_id="C1",
        event_type=EventType.COMMENT_ADDED,
        content="Great answer!",
        timestamp=110,
        node_id="user_c",
        depends_on=["A1"]  # Comment depends on answer
    )

    demo.add_event(q1)
    demo.add_event(a1)
    demo.add_event(c1)

    # Replicate to Node1 in correct order
    print("\n--- Replicating to Node1 (correct order) ---")
    demo.replicate_to_node("node1", "Q1")
    demo.replicate_to_node("node1", "A1")
    demo.replicate_to_node("node1", "C1")
    demo.print_node_view("node1")

    # Try to replicate to Node2 in wrong order
    print("\n--- Attempting to replicate to Node2 (wrong order) ---")
    demo.replicate_to_node("node2", "C1")  # Try comment first
    demo.replicate_to_node("node2", "Q1")  # Then question
    demo.replicate_to_node("node2", "A1")  # Then answer
    demo.print_node_view("node2")


def demo_concurrent_events():
    """Demonstrate concurrent events (no causal relationship)"""
    print("\n" + "=" * 70)
    print("DEMO 2: Concurrent Events (No Causal Relationship)")
    print("=" * 70)

    demo = CausalOrderingDemo()

    # Two independent questions posted at roughly the same time
    q1 = Event(
        event_id="Q1",
        event_type=EventType.QUESTION_POSTED,
        content="How do I use Python?",
        timestamp=100,
        node_id="user_a"
    )

    q2 = Event(
        event_id="Q2",
        event_type=EventType.QUESTION_POSTED,
        content="How do I use JavaScript?",
        timestamp=101,
        node_id="user_b"
    )

    demo.add_event(q1)
    demo.add_event(q2)

    print("\n--- Replicating to Node1 (Q1 then Q2) ---")
    demo.replicate_to_node("node1", "Q1")
    demo.replicate_to_node("node1", "Q2")
    demo.print_node_view("node1")

    print("\n--- Replicating to Node2 (Q2 then Q1) ---")
    demo.replicate_to_node("node2", "Q2")
    demo.replicate_to_node("node2", "Q1")
    demo.print_node_view("node2")

    print("\n[OK] Both orderings are valid! Q1 and Q2 are concurrent (no causal relationship)")


def demo_vector_clocks():
    """Demonstrate vector clocks for tracking causality"""
    print("\n" + "=" * 70)
    print("DEMO 3: Vector Clocks (Tracking Causality)")
    print("=" * 70)

    @dataclass
    class VectorClockEvent:
        event_id: str
        content: str
        vector_clock: Dict[str, int]
        node_id: str

    class VectorClockSystem:
        def __init__(self, nodes: List[str]):
            self.clocks: Dict[str, int] = {node: 0 for node in nodes}
            self.events: List[VectorClockEvent] = []

        def local_event(self, node_id: str, event_id: str, content: str):
            """Record a local event on a node"""
            self.clocks[node_id] += 1
            vc = self.clocks.copy()
            event = VectorClockEvent(event_id, content, vc, node_id)
            self.events.append(event)
            print(f"Event {event_id} on {node_id}: VC={vc}")

        def send_message(self, from_node: str, to_node: str, msg_id: str):
            """Send a message (increments sender's clock)"""
            self.clocks[from_node] += 1
            print(f"Send {msg_id} from {from_node}: VC={self.clocks.copy()}")

        def receive_message(self, to_node: str, msg_id: str, sender_vc: Dict[str, int]):
            """Receive a message (merge vector clocks)"""
            # Merge: take max of each component
            for node in self.clocks:
                self.clocks[node] = max(self.clocks[node], sender_vc.get(node, 0))
            self.clocks[to_node] += 1
            print(f"Receive {msg_id} on {to_node}: VC={self.clocks.copy()}")

    vc_system = VectorClockSystem(["A", "B", "C"])

    print("\nScenario: Three nodes exchanging messages")
    vc_system.local_event("A", "E1", "Post question")
    vc_system.send_message("A", "B", "M1")
    vc_system.receive_message("B", "M1", {"A": 1, "B": 0, "C": 0})
    vc_system.local_event("B", "E2", "Post answer")
    vc_system.send_message("B", "C", "M2")
    vc_system.receive_message("C", "M2", {"A": 1, "B": 2, "C": 0})
    vc_system.local_event("C", "E3", "Post comment")

    print("\n[OK] Vector clocks track causal relationships precisely")


if __name__ == "__main__":
    demo_basic_causal_ordering()
    demo_concurrent_events()
    demo_vector_clocks()

    print("\n" + "=" * 70)
    print("KEY TAKEAWAYS")
    print("=" * 70)
    print("""
1. Causal ordering is a PARTIAL ORDER:
   - Some events are ordered (causally related)
   - Some events are concurrent (no causal relationship)

2. Causal consistency guarantees:
   - If A causally caused B, all nodes see A before B
   - Concurrent events can be seen in any order

3. Vector clocks can track causality:
   - Each node maintains a vector of logical timestamps
   - Merging clocks on message receipt captures causality

4. Causal ordering is weaker than linearizability:
   - Allows concurrent events in any order
   - But preserves cause-and-effect relationships
    """)
