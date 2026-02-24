"""
Total Order Broadcast: Ensuring All Nodes See Events in the Same Order

Total Order Broadcast (also called Atomic Broadcast) guarantees:
1. Reliable delivery: If one node receives a message, all nodes receive it
2. Total ordering: All nodes deliver messages in the SAME order

This is exactly what a single-leader replication log provides.

Key insight: Total Order Broadcast is EQUIVALENT to consensus!
"""

from dataclasses import dataclass, field
from typing import List, Dict, Set
from enum import Enum
import time


@dataclass
class Message:
    """A message in the system"""
    msg_id: str
    content: str
    sequence_number: int = -1  # Assigned by leader


class TotalOrderBroadcastDemo:
    """
    Demonstrates total order broadcast using a single-leader approach.

    Scenario: A distributed counter where all nodes must increment in the same order.
    """

    def __init__(self, leader_id: str, node_ids: List[str]):
        self.leader_id = leader_id
        self.node_ids = node_ids
        self.next_sequence = 0
        self.message_queue: List[Message] = []  # Leader's queue
        self.node_logs: Dict[str, List[Message]] = {nid: [] for nid in node_ids}
        self.node_applied: Dict[str, int] = {nid: 0 for nid in node_ids}

    def broadcast(self, msg: Message) -> None:
        """
        Broadcast a message through the leader.
        The leader assigns a sequence number (total order).
        """
        msg.sequence_number = self.next_sequence
        self.next_sequence += 1
        self.message_queue.append(msg)
        print(f"Leader assigned sequence {msg.sequence_number} to {msg.msg_id}: {msg.content}")

    def replicate_to_node(self, node_id: str) -> int:
        """
        Replicate messages to a node in order.
        Returns the number of new messages replicated.
        """
        if node_id not in self.node_logs:
            return 0

        replicated = 0
        for msg in self.message_queue:
            if msg not in self.node_logs[node_id]:
                self.node_logs[node_id].append(msg)
                replicated += 1

        return replicated

    def apply_messages(self, node_id: str) -> None:
        """Apply messages on a node (in order)"""
        if node_id not in self.node_logs:
            return

        while self.node_applied[node_id] < len(self.node_logs[node_id]):
            msg = self.node_logs[node_id][self.node_applied[node_id]]
            print(f"  {node_id} applies: seq={msg.sequence_number}, {msg.msg_id}: {msg.content}")
            self.node_applied[node_id] += 1

    def get_node_log(self, node_id: str) -> List[Message]:
        """Get the ordered log on a node"""
        return self.node_logs.get(node_id, [])

    def print_all_logs(self) -> None:
        """Print logs on all nodes"""
        print("\n--- All Node Logs ---")
        for node_id in self.node_ids:
            log = self.get_node_log(node_id)
            print(f"{node_id}: {[f'seq={m.sequence_number}' for m in log]}")


def demo_total_order_broadcast():
    """Demonstrate total order broadcast"""
    print("=" * 70)
    print("DEMO 1: Total Order Broadcast (Single-Leader)")
    print("=" * 70)

    demo = TotalOrderBroadcastDemo(
        leader_id="leader",
        node_ids=["node1", "node2", "node3"]
    )

    # Broadcast messages
    print("\n--- Broadcasting Messages ---")
    demo.broadcast(Message("M1", "Increment counter"))
    demo.broadcast(Message("M2", "Decrement counter"))
    demo.broadcast(Message("M3", "Reset counter"))

    # Replicate to nodes
    print("\n--- Replicating to Nodes ---")
    for node_id in demo.node_ids:
        replicated = demo.replicate_to_node(node_id)
        print(f"Replicated {replicated} messages to {node_id}")

    # Apply messages on each node
    print("\n--- Applying Messages on Each Node ---")
    for node_id in demo.node_ids:
        demo.apply_messages(node_id)

    demo.print_all_logs()

    print("\n[OK] All nodes applied messages in the SAME order!")


def demo_network_partition():
    """Demonstrate total order broadcast with network partition"""
    print("\n" + "=" * 70)
    print("DEMO 2: Total Order Broadcast with Network Partition")
    print("=" * 70)

    demo = TotalOrderBroadcastDemo(
        leader_id="leader",
        node_ids=["node1", "node2", "node3"]
    )

    # Broadcast initial messages
    print("\n--- Phase 1: Broadcasting Initial Messages ---")
    demo.broadcast(Message("M1", "Write A=1"))
    demo.broadcast(Message("M2", "Write B=2"))

    # Replicate to all nodes
    print("\n--- Replicating to All Nodes ---")
    for node_id in demo.node_ids:
        demo.replicate_to_node(node_id)
        demo.apply_messages(node_id)

    # Network partition: node3 isolated
    print("\n--- Phase 2: Network Partition (node3 isolated) ---")
    print("Broadcasting M3 and M4 (only node1 and node2 receive)")

    demo.broadcast(Message("M3", "Write C=3"))
    demo.broadcast(Message("M4", "Write D=4"))

    # Replicate only to node1 and node2
    for node_id in ["node1", "node2"]:
        demo.replicate_to_node(node_id)
        demo.apply_messages(node_id)

    print("node3 does NOT receive M3 and M4 (isolated)")

    demo.print_all_logs()

    print("\n--- Phase 3: Partition Heals ---")
    print("Replicating M3 and M4 to node3")
    demo.replicate_to_node("node3")
    demo.apply_messages("node3")

    demo.print_all_logs()

    print("\n[OK] Once partition heals, node3 catches up in the SAME order!")


def demo_equivalence_to_consensus():
    """
    Demonstrate why Total Order Broadcast is equivalent to consensus.

    Key insight:
    - Total Order Broadcast → Linearizable storage: Use a linearizable register
      as a counter to assign sequence numbers
    - Linearizable storage → Total Order Broadcast: Broadcast messages and use
      the linearizable register to order them
    """
    print("\n" + "=" * 70)
    print("DEMO 3: Total Order Broadcast ↔ Consensus Equivalence")
    print("=" * 70)

    print("""
Consensus Problem: Get all nodes to agree on a value.

Total Order Broadcast Solution:
1. Each node proposes a value
2. Use total order broadcast to order all proposals
3. All nodes apply proposals in the same order
4. The first proposal in the order is the consensus value

Example: Leader Election
- Multiple nodes propose themselves as leader
- Use total order broadcast to order proposals
- All nodes see the same first proposal
- That node becomes the leader (consensus!)

Why they're equivalent:
- Total Order Broadcast requires consensus on the order
- Consensus can be implemented using total order broadcast
- They're two sides of the same coin
    """)

    # Simulate leader election using total order broadcast
    print("\n--- Simulating Leader Election via Total Order Broadcast ---")

    demo = TotalOrderBroadcastDemo(
        leader_id="coordinator",
        node_ids=["node1", "node2", "node3"]
    )

    # Each node proposes itself as leader
    print("\nPhase 1: Nodes propose themselves as leader")
    demo.broadcast(Message("PROPOSE_LEADER_1", "node1 proposes itself"))
    demo.broadcast(Message("PROPOSE_LEADER_2", "node2 proposes itself"))
    demo.broadcast(Message("PROPOSE_LEADER_3", "node3 proposes itself"))

    # Replicate to all nodes
    print("\nPhase 2: Replicate proposals to all nodes")
    for node_id in demo.node_ids:
        demo.replicate_to_node(node_id)

    # All nodes apply in the same order
    print("\nPhase 3: All nodes apply proposals in the same order")
    for node_id in demo.node_ids:
        demo.apply_messages(node_id)

    # Determine leader
    first_proposal = demo.get_node_log("node1")[0]
    print(f"\n[OK] Consensus reached: {first_proposal.content}")
    print("  All nodes agree on the same leader!")


def demo_single_leader_replication():
    """
    Demonstrate how single-leader replication implements total order broadcast.

    This is what databases like PostgreSQL, MySQL, and MongoDB do.
    """
    print("\n" + "=" * 70)
    print("DEMO 4: Single-Leader Replication = Total Order Broadcast")
    print("=" * 70)

    print("""
Single-Leader Replication:
1. All writes go to the leader
2. Leader writes to its WAL (Write-Ahead Log)
3. Leader sends log entries to followers
4. Followers apply entries in the same order

This is exactly total order broadcast!

The replication log provides:
- Reliable delivery: Followers eventually get all entries
- Total ordering: All followers apply entries in the same order

Example: PostgreSQL Streaming Replication
    """)

    demo = TotalOrderBroadcastDemo(
        leader_id="primary",
        node_ids=["primary", "replica1", "replica2"]
    )

    print("\n--- Simulating PostgreSQL Replication ---")

    # Client writes to primary
    print("\nClient writes to primary:")
    demo.broadcast(Message("TXN1", "INSERT user (id=1, name='Alice')"))
    demo.broadcast(Message("TXN2", "INSERT user (id=2, name='Bob')"))
    demo.broadcast(Message("TXN3", "UPDATE user SET name='Alice Smith' WHERE id=1"))

    # Primary applies immediately
    print("\nPrimary applies transactions:")
    demo.apply_messages("primary")

    # Replicate to replicas
    print("\nReplicating to replicas:")
    for node_id in ["replica1", "replica2"]:
        demo.replicate_to_node(node_id)
        demo.apply_messages(node_id)

    demo.print_all_logs()

    print("\n[OK] All replicas have the same data in the same order!")


if __name__ == "__main__":
    demo_total_order_broadcast()
    demo_network_partition()
    demo_equivalence_to_consensus()
    demo_single_leader_replication()

    print("\n" + "=" * 70)
    print("KEY TAKEAWAYS")
    print("=" * 70)
    print("""
1. Total Order Broadcast guarantees:
   - Reliable delivery: All nodes get all messages
   - Total ordering: All nodes apply messages in the same order

2. Single-leader replication implements total order broadcast:
   - Leader assigns sequence numbers
   - Followers apply in order

3. Total Order Broadcast is equivalent to consensus:
   - Can implement consensus using total order broadcast
   - Can implement total order broadcast using consensus

4. Real systems use this:
   - PostgreSQL: Streaming replication
   - MySQL: Binlog replication
   - MongoDB: Oplog replication
   - Kafka: Partition logs
   - Raft: Log replication
    """)
