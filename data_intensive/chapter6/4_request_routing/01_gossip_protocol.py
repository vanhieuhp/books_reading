"""
Exercise 4: Request Routing (Service Discovery) — Gossip Protocol

DDIA Reference: Chapter 6, "Request Routing" (pp. 471-568)

This exercise simulates how distributed databases route client requests to the
correct partition when data is spread across multiple nodes.

Key concepts:
  - The routing problem: "Which node owns partition for key X?"
  - Three approaches: Any-node proxy, Routing tier, Cluster-aware client
  - Gossip protocol: Decentralized routing via node-to-node communication
  - Partition assignment: Which node owns which partitions
  - Rebalancing: How routing tables update when partitions move

Run: python 01_gossip_protocol.py
"""

import sys
import time
import random
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from collections import defaultdict

# Fix Windows terminal encoding for Unicode output
sys.stdout.reconfigure(encoding='utf-8')


# =============================================================================
# CORE COMPONENTS: Partition, PartitionMap, Node, GossipProtocol
# =============================================================================

@dataclass
class PartitionAssignment:
    """Represents which node owns a partition."""
    partition_id: int
    node_id: str
    timestamp: float = field(default_factory=time.time)

    def __repr__(self):
        return f"Partition {self.partition_id} → Node {self.node_id}"


class PartitionMap:
    """
    A routing table: maps partition IDs to node IDs.

    DDIA insight: "The routing tier must know the current assignment of
    partitions to nodes. This assignment changes over time as partitions
    are rebalanced."
    """

    def __init__(self):
        self.assignments: Dict[int, str] = {}  # partition_id -> node_id
        self.version = 0  # Incremented on each change (for consistency)

    def assign(self, partition_id: int, node_id: str):
        """Assign a partition to a node."""
        self.assignments[partition_id] = node_id
        self.version += 1

    def get_node_for_partition(self, partition_id: int) -> Optional[str]:
        """Look up which node owns a partition."""
        return self.assignments.get(partition_id)

    def get_partitions_for_node(self, node_id: str) -> List[int]:
        """Get all partitions owned by a node."""
        return [p for p, n in self.assignments.items() if n == node_id]

    def copy(self) -> 'PartitionMap':
        """Create a copy of this routing table."""
        new_map = PartitionMap()
        new_map.assignments = self.assignments.copy()
        new_map.version = self.version
        return new_map

    def __repr__(self):
        lines = [f"PartitionMap (v{self.version}):"]
        for partition_id in sorted(self.assignments.keys()):
            node_id = self.assignments[partition_id]
            lines.append(f"  Partition {partition_id:3d} → {node_id}")
        return "\n".join(lines)


class Node:
    """
    A database node in the cluster.

    Each node:
    1. Stores some partitions (owns data)
    2. Maintains a routing table (knows where all partitions are)
    3. Participates in gossip (shares routing info with other nodes)
    """

    def __init__(self, node_id: str, num_partitions: int):
        self.node_id = node_id
        self.num_partitions = num_partitions

        # Local routing table (may be stale)
        self.routing_table = PartitionMap()

        # Partitions this node owns
        self.owned_partitions: Set[int] = set()

        # For tracking gossip messages
        self.gossip_history: List[Tuple[str, float]] = []

    def owns_partition(self, partition_id: int) -> bool:
        """Check if this node owns a partition."""
        return partition_id in self.owned_partitions

    def route_request(self, partition_id: int) -> Optional[str]:
        """
        Route a request to the correct node.

        Returns the node_id that should handle this partition,
        or None if we don't know (routing table is incomplete).
        """
        return self.routing_table.get_node_for_partition(partition_id)

    def update_routing_table(self, new_map: PartitionMap):
        """Update this node's routing table (from gossip or coordinator)."""
        if new_map.version > self.routing_table.version:
            self.routing_table = new_map.copy()

    def receive_gossip(self, sender_id: str, sender_map: PartitionMap):
        """
        Receive a gossip message from another node.

        DDIA concept: "Nodes periodically exchange messages with each other,
        sharing their knowledge of partition assignments."
        """
        if sender_map.version > self.routing_table.version:
            self.update_routing_table(sender_map)
            self.gossip_history.append((sender_id, time.time()))

    def __repr__(self):
        return f"Node({self.node_id}, owns={sorted(self.owned_partitions)})"


class GossipProtocol:
    """
    Implements the gossip protocol for decentralized routing.

    DDIA: "Cassandra and Riak take a different approach: They use a gossip
    protocol instead of a centralized coordinator. Nodes periodically exchange
    messages with each other, sharing their knowledge of partition assignments."
    """

    def __init__(self, nodes: List[Node], gossip_interval: float = 0.1):
        self.nodes = {n.node_id: n for n in nodes}
        self.gossip_interval = gossip_interval
        self.round = 0

    def run_gossip_round(self):
        """
        Execute one round of gossip.

        Each node picks a random peer and exchanges routing tables.
        """
        self.round += 1

        for node in self.nodes.values():
            # Pick a random peer
            peers = [n for n in self.nodes.values() if n.node_id != node.node_id]
            if not peers:
                continue

            peer = random.choice(peers)

            # Exchange routing tables
            node.receive_gossip(peer.node_id, peer.routing_table)
            peer.receive_gossip(node.node_id, node.routing_table)

    def run_gossip_rounds(self, num_rounds: int):
        """Run multiple rounds of gossip."""
        for _ in range(num_rounds):
            self.run_gossip_round()
            time.sleep(self.gossip_interval)

    def all_nodes_converged(self) -> bool:
        """Check if all nodes have the same routing table version."""
        if not self.nodes:
            return True

        versions = [n.routing_table.version for n in self.nodes.values()]
        return len(set(versions)) == 1

    def convergence_time(self, target_version: int) -> Optional[float]:
        """Measure how long it takes for all nodes to reach a target version."""
        start = time.time()
        while not all(n.routing_table.version >= target_version for n in self.nodes.values()):
            self.run_gossip_round()
            if time.time() - start > 10:  # Timeout
                return None
        return time.time() - start


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


def demo_1_initial_cluster_setup():
    """
    Demo 1: Set up a cluster with initial partition assignment.

    DDIA concept: "When a database cluster starts, each node must know
    which partitions it owns and where all other partitions are."
    """
    print_header("DEMO 1: Initial Cluster Setup")
    print("""
    We have a cluster with 3 nodes and 12 partitions.
    Each node owns 4 partitions.
    """)

    # Create nodes
    nodes = [Node(f"Node-{i}", num_partitions=12) for i in range(1, 4)]

    # Assign partitions to nodes
    partition_assignments = [
        (0, "Node-1"), (1, "Node-1"), (2, "Node-1"), (3, "Node-1"),
        (4, "Node-2"), (5, "Node-2"), (6, "Node-2"), (7, "Node-2"),
        (8, "Node-3"), (9, "Node-3"), (10, "Node-3"), (11, "Node-3"),
    ]

    print("  📋 Initial Partition Assignment:")
    for partition_id, node_id in partition_assignments:
        node = next(n for n in nodes if n.node_id == node_id)
        node.owned_partitions.add(partition_id)
        node.routing_table.assign(partition_id, node_id)
        print(f"    Partition {partition_id:2d} → {node_id}")

    # Verify each node knows the full routing table
    print("\n  ✅ Each node's routing table:")
    for node in nodes:
        print(f"\n    {node.node_id}:")
        for p in sorted(node.routing_table.assignments.keys()):
            owner = node.routing_table.get_node_for_partition(p)
            print(f"      Partition {p:2d} → {owner}")

    return nodes


def demo_2_gossip_convergence():
    """
    Demo 2: Show how gossip protocol spreads routing information.

    DDIA concept: "Over time, all nodes converge on a consistent routing table."
    """
    print_header("DEMO 2: Gossip Protocol Convergence")
    print("""
    Scenario: Node-1 learns about a partition reassignment.
    It doesn't have a central coordinator, so it spreads the news via gossip.

    We'll measure how long it takes for all nodes to learn about the change.
    """)

    # Create nodes
    nodes = [Node(f"Node-{i}", num_partitions=12) for i in range(1, 4)]

    # Initial assignment
    for partition_id in range(12):
        node_id = f"Node-{(partition_id % 3) + 1}"
        for node in nodes:
            node.routing_table.assign(partition_id, node_id)
            if node.node_id == node_id:
                node.owned_partitions.add(partition_id)

    print(f"  Initial state: All nodes at routing table version {nodes[0].routing_table.version}")

    # Simulate a rebalancing: Partition 0 moves from Node-1 to Node-2
    print(f"\n  🔄 Rebalancing: Partition 0 moves from Node-1 to Node-2")
    nodes[0].routing_table.assign(0, "Node-2")  # Node-1 learns first
    nodes[0].owned_partitions.discard(0)
    nodes[1].owned_partitions.add(0)

    print(f"  After rebalancing:")
    print(f"    Node-1 routing table version: {nodes[0].routing_table.version}")
    print(f"    Node-2 routing table version: {nodes[1].routing_table.version}")
    print(f"    Node-3 routing table version: {nodes[2].routing_table.version}")

    # Run gossip protocol
    print(f"\n  📡 Running gossip protocol...")
    gossip = GossipProtocol(nodes, gossip_interval=0.01)

    convergence_time = gossip.convergence_time(target_version=nodes[0].routing_table.version)

    print(f"\n  ✅ Convergence achieved in {gossip.round} gossip rounds ({convergence_time:.3f}s)")
    print(f"  Final state: All nodes at routing table version {nodes[0].routing_table.version}")

    print(f"\n  📊 Gossip history:")
    for node in nodes:
        print(f"    {node.node_id}: received {len(node.gossip_history)} gossip messages")


def demo_3_client_routing():
    """
    Demo 3: Show how a client routes requests using the gossip-based routing table.

    DDIA concept: "The client connects to any node. If that node doesn't own
    the requested key, it forwards the request to the correct node."
    """
    print_header("DEMO 3: Client Request Routing")
    print("""
    A client wants to read key "user_42".

    Step 1: Hash the key to get a partition ID
    Step 2: Look up which node owns that partition
    Step 3: Route the request to that node
    """)

    # Create cluster
    nodes = [Node(f"Node-{i}", num_partitions=12) for i in range(1, 4)]

    # Assign partitions
    for partition_id in range(12):
        node_id = f"Node-{(partition_id % 3) + 1}"
        for node in nodes:
            node.routing_table.assign(partition_id, node_id)
            if node.node_id == node_id:
                node.owned_partitions.add(partition_id)

    # Simulate client requests
    keys = ["user_42", "user_100", "user_7", "post_999", "comment_5"]

    print(f"\n  🔑 Client requests:")
    for key in keys:
        # Hash the key to get partition ID
        partition_id = hash(key) % 12

        # Pick a random node to contact first
        contacted_node = random.choice(nodes)

        # Look up the correct node
        correct_node_id = contacted_node.route_request(partition_id)

        # Check if we contacted the right node
        is_correct = contacted_node.node_id == correct_node_id
        status = "✅ Direct hit" if is_correct else f"→ Forward to {correct_node_id}"

        print(f"    Key '{key}' → Partition {partition_id} → {status}")


def demo_4_rebalancing_and_routing():
    """
    Demo 4: Show how routing tables update during rebalancing.

    DDIA concept: "When partitions are rebalanced (moved between nodes),
    every routing layer must be updated immediately."
    """
    print_header("DEMO 4: Rebalancing and Routing Updates")
    print("""
    Scenario: A new node joins the cluster.
    Partitions are rebalanced to distribute load evenly.
    The gossip protocol spreads the new routing table.
    """)

    # Create initial 3-node cluster
    nodes = [Node(f"Node-{i}", num_partitions=12) for i in range(1, 4)]

    # Initial assignment: 4 partitions per node
    for partition_id in range(12):
        node_id = f"Node-{(partition_id % 3) + 1}"
        for node in nodes:
            node.routing_table.assign(partition_id, node_id)
            if node.node_id == node_id:
                node.owned_partitions.add(partition_id)

    print(f"  Initial cluster: 3 nodes, 12 partitions (4 per node)")
    print(f"  Partitions per node:")
    for node in nodes:
        print(f"    {node.node_id}: {sorted(node.owned_partitions)}")

    # New node joins
    print(f"\n  🆕 New node joins: Node-4")
    new_node = Node("Node-4", num_partitions=12)
    nodes.append(new_node)

    # Rebalance: move 3 partitions to the new node
    print(f"\n  🔄 Rebalancing: Moving partitions to Node-4")
    partitions_to_move = [0, 4, 8]  # One from each original node

    for partition_id in partitions_to_move:
        # Update all nodes' routing tables
        for node in nodes:
            node.routing_table.assign(partition_id, "Node-4")

        # Update ownership
        for node in nodes:
            if partition_id in node.owned_partitions:
                node.owned_partitions.discard(partition_id)
        new_node.owned_partitions.add(partition_id)

        print(f"    Partition {partition_id}: moved to Node-4")

    print(f"\n  ✅ After rebalancing:")
    for node in nodes:
        print(f"    {node.node_id}: {sorted(node.owned_partitions)}")

    # Simulate gossip spreading the new routing table
    print(f"\n  📡 Gossip protocol spreads the new routing table...")
    gossip = GossipProtocol(nodes, gossip_interval=0.01)
    gossip.run_gossip_rounds(5)

    print(f"  ✅ All nodes converged: {gossip.all_nodes_converged()}")
    print(f"  Routing table version: {nodes[0].routing_table.version}")


def demo_5_three_routing_approaches():
    """
    Demo 5: Compare the three routing approaches.

    DDIA concept: "There are three fundamental approaches to routing:
    1. Contact any node (gossip-based)
    2. Routing tier (proxy)
    3. Cluster-aware client"
    """
    print_header("DEMO 5: Three Routing Approaches")
    print("""
    DDIA describes three ways to route requests in a partitioned system.
    Let's compare them:
    """)

    print("""
    ┌─────────────────────────────────────────────────────────────────┐
    │ APPROACH 1: Contact Any Node (Gossip-Based)                     │
    ├─────────────────────────────────────────────────────────────────┤
    │ Client → Random Node → (if needed) Forward to correct node      │
    │                                                                  │
    │ Pros:                                                            │
    │   • Simple client (no routing knowledge needed)                  │
    │   • Decentralized (no single point of failure)                   │
    │   • Gossip protocol eventually converges                         │
    │                                                                  │
    │ Cons:                                                            │
    │   • Extra hop if you contact the wrong node                      │
    │   • Routing table may be stale (eventual consistency)            │
    │                                                                  │
    │ Used by: Cassandra, Riak                                         │
    └─────────────────────────────────────────────────────────────────┘
    """)

    print("""
    ┌─────────────────────────────────────────────────────────────────┐
    │ APPROACH 2: Routing Tier (Proxy)                                │
    ├─────────────────────────────────────────────────────────────────┤
    │ Client → Routing Tier → Correct Node                            │
    │                                                                  │
    │ Pros:                                                            │
    │   • Client is simple (just talks to router)                      │
    │   • Router has authoritative routing table (from config servers) │
    │   • Always routes to correct node (no extra hops)                │
    │                                                                  │
    │ Cons:                                                            │
    │   • Routing tier is a bottleneck                                 │
    │   • Routing tier is a single point of failure (needs replication)│
    │   • Extra network hop through router                             │
    │                                                                  │
    │ Used by: MongoDB (mongos), HBase (via ZooKeeper)                │
    └─────────────────────────────────────────────────────────────────┘
    """)

    print("""
    ┌─────────────────────────────────────────────────────────────────┐
    │ APPROACH 3: Cluster-Aware Client                                │
    ├─────────────────────────────────────────────────────────────────┤
    │ Client (knows routing) → Correct Node (direct)                  │
    │                                                                  │
    │ Pros:                                                            │
    │   • No extra hops (direct to correct node)                       │
    │   • No routing tier bottleneck                                   │
    │   • Highest performance                                          │
    │                                                                  │
    │ Cons:                                                            │
    │   • Client must stay up-to-date with routing changes             │
    │   • Client library is more complex                               │
    │   • Requires smart driver (e.g., Datastax Cassandra driver)      │
    │                                                                  │
    │ Used by: Cassandra (with smart driver), Kafka clients            │
    └─────────────────────────────────────────────────────────────────┘
    """)

    print("""
    ┌─────────────────────────────────────────────────────────────────┐
    │ COMPARISON TABLE                                                │
    ├──────────────────────┬──────────┬──────────┬──────────────────┤
    │ Aspect               │ Any Node │ Routing  │ Cluster-Aware    │
    │                      │ (Gossip) │ Tier     │ Client           │
    ├──────────────────────┼──────────┼──────────┼──────────────────┤
    │ Client Complexity    │ Low      │ Low      │ High             │
    │ Network Hops         │ 1-2      │ 2        │ 1                │
    │ Routing Consistency  │ Eventual │ Strong   │ Eventual         │
    │ Bottleneck Risk      │ None     │ Router   │ None             │
    │ Decentralized        │ Yes      │ No       │ Yes              │
    └──────────────────────┴──────────┴──────────┴──────────────────┘
    """)


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 80)
    print("  EXERCISE 4: REQUEST ROUTING (SERVICE DISCOVERY)")
    print("  DDIA Chapter 6: 'Request Routing'")
    print("=" * 80)
    print("""
  This exercise simulates how distributed databases route client requests
  to the correct partition when data is spread across multiple nodes.

  We'll explore three routing approaches and the gossip protocol.
    """)

    demo_1_initial_cluster_setup()
    demo_2_gossip_convergence()
    demo_3_client_routing()
    demo_4_rebalancing_and_routing()
    demo_5_three_routing_approaches()

    print("\n" + "=" * 80)
    print("  EXERCISE 4 COMPLETE ✅")
    print("=" * 80)
    print("""
  Key Takeaways:

  1. 🗺️  Routing Problem: "Which node owns partition for key X?"
  2. 📡 Gossip Protocol: Decentralized routing via node-to-node communication
  3. 🔄 Convergence: All nodes eventually learn about partition changes
  4. 🎯 Three Approaches:
     • Any-node proxy (Cassandra, Riak) — simple but may need forwarding
     • Routing tier (MongoDB) — centralized but can be bottleneck
     • Cluster-aware client (Cassandra driver) — fastest but complex
  5. 🔗 ZooKeeper: Centralized coordination for routing updates
  6. ⚡ Trade-offs: Consistency vs. performance vs. complexity

  Next: Run 02_zookeeper_coordination.py to learn centralized routing
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
