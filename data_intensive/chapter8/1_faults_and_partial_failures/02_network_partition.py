"""
Exercise 2: Network Partitions and Split-Brain

DDIA Reference: Chapter 8, "Unreliable Networks" (pp. 282-283)

This exercise demonstrates what happens when a network partition splits
a cluster into two isolated groups.

Key scenarios:
  1. Normal operation: all nodes can communicate
  2. Network partition: cluster splits into two groups
  3. Both sides think the other is dead
  4. Both sides might try to become the leader (split-brain)
  5. Data written to one side is invisible to the other
  6. When partition heals, you have conflicting data

The solution: Quorums. A node can only become leader if it has support
from a MAJORITY of nodes.

Run: python 02_network_partition.py
"""

import sys
import time
from enum import Enum
from typing import List, Dict, Set, Optional

sys.stdout.reconfigure(encoding='utf-8')


# =============================================================================
# NODE SIMULATION
# =============================================================================

class NodeRole(Enum):
    """Role of a node in the cluster."""
    LEADER = "LEADER"
    FOLLOWER = "FOLLOWER"
    CANDIDATE = "CANDIDATE"


class Node:
    """A node in a distributed cluster."""

    def __init__(self, node_id: int, total_nodes: int):
        self.node_id = node_id
        self.total_nodes = total_nodes
        self.role = NodeRole.FOLLOWER
        self.term = 0  # Election term
        self.voted_for = None
        self.data = {}  # Key-value store
        self.log = []  # Write log
        self.reachable_nodes: Set[int] = set(range(total_nodes))  # Nodes I can reach
        self.heartbeat_time = time.time()

    def can_reach(self, other_node_id: int) -> bool:
        """Check if I can reach another node."""
        return other_node_id in self.reachable_nodes

    def isolate_from(self, other_node_id: int):
        """Simulate network partition: can't reach this node."""
        self.reachable_nodes.discard(other_node_id)

    def reconnect_to(self, other_node_id: int):
        """Heal network partition: can reach this node again."""
        self.reachable_nodes.add(other_node_id)

    def write(self, key: str, value: str) -> bool:
        """
        Write data to this node.

        Only the leader can accept writes.
        """
        if self.role != NodeRole.LEADER:
            return False

        self.data[key] = value
        self.log.append({"key": key, "value": value, "term": self.term})
        return True

    def read(self, key: str) -> Optional[str]:
        """Read data from this node."""
        return self.data.get(key)

    def __repr__(self):
        return f"Node{self.node_id}({self.role.value})"


# =============================================================================
# CLUSTER SIMULATION
# =============================================================================

class Cluster:
    """A cluster of nodes."""

    def __init__(self, num_nodes: int):
        self.nodes = [Node(i, num_nodes) for i in range(num_nodes)]
        self.num_nodes = num_nodes
        self.quorum_size = (num_nodes // 2) + 1

    def elect_leader(self):
        """
        Simulate leader election using quorum-based consensus.

        A node can only become leader if it can reach a quorum of nodes.
        """
        print()
        print("🗳️  LEADER ELECTION")
        print("-" * 60)

        for node in self.nodes:
            # Count how many nodes this node can reach
            reachable_count = len(node.reachable_nodes)

            print(f"{node}: can reach {reachable_count}/{self.num_nodes} nodes", end="")

            if reachable_count >= self.quorum_size:
                # This node has quorum support
                node.role = NodeRole.LEADER
                node.term += 1
                print(f" → ELECTED LEADER (term {node.term}) ✅")
            else:
                # This node doesn't have quorum support
                node.role = NodeRole.FOLLOWER
                print(f" → REMAINS FOLLOWER (needs {self.quorum_size})")

        print()

    def get_leader(self) -> Optional[Node]:
        """Get the current leader (if any)."""
        leaders = [n for n in self.nodes if n.role == NodeRole.LEADER]
        return leaders[0] if leaders else None

    def count_leaders(self) -> int:
        """Count how many leaders exist (should be 0 or 1)."""
        return len([n for n in self.nodes if n.role == NodeRole.LEADER])

    def print_state(self):
        """Print the current state of the cluster."""
        print("📊 CLUSTER STATE:")
        print("-" * 60)
        for node in self.nodes:
            reachable = sorted(list(node.reachable_nodes))
            print(f"{node}: reachable={reachable}, data={node.data}")
        print()


# =============================================================================
# DEMONSTRATION
# =============================================================================

def demonstrate_normal_operation():
    """Show normal operation without partitions."""

    print("=" * 80)
    print("SCENARIO 1: NORMAL OPERATION (No Partition)")
    print("=" * 80)
    print()

    cluster = Cluster(num_nodes=3)

    print("Initial state: 3 nodes, all can communicate")
    cluster.print_state()

    # Elect leader
    cluster.elect_leader()

    leader = cluster.get_leader()
    print(f"✅ Leader elected: {leader}")
    print()

    # Write data
    print("💾 Writing data to leader...")
    leader.write("user:1", "Alice")
    leader.write("user:2", "Bob")
    print(f"Leader data: {leader.data}")
    print()

    # Replicate to followers
    print("📤 Replicating to followers...")
    for node in cluster.nodes:
        if node != leader:
            node.data = leader.data.copy()
            print(f"  {node}: {node.data}")
    print()

    print("✅ All nodes have consistent data")
    print()


def demonstrate_network_partition():
    """Show what happens during a network partition."""

    print("=" * 80)
    print("SCENARIO 2: NETWORK PARTITION (Split-Brain)")
    print("=" * 80)
    print()

    cluster = Cluster(num_nodes=3)

    # Initial state
    print("Initial state: 3 nodes, all can communicate")
    cluster.elect_leader()
    leader = cluster.get_leader()
    print(f"Leader: {leader}")
    print()

    # Write initial data
    leader.write("user:1", "Alice")
    for node in cluster.nodes:
        if node != leader:
            node.data = leader.data.copy()
    print(f"Initial data on all nodes: {leader.data}")
    print()

    # Introduce partition
    print("🔴 NETWORK PARTITION OCCURS!")
    print("   Node 0 ◄──► Node 1     Node 2 (isolated)")
    print()

    # Node 2 is isolated from nodes 0 and 1
    cluster.nodes[2].isolate_from(0)
    cluster.nodes[2].isolate_from(1)
    cluster.nodes[0].isolate_from(2)
    cluster.nodes[1].isolate_from(2)

    print("After partition:")
    cluster.print_state()

    # New election
    print("⏱️  Heartbeat timeout. New election starts...")
    cluster.elect_leader()

    print(f"Leaders after partition: {cluster.count_leaders()}")
    print()

    # Show the problem
    leaders = [n for n in cluster.nodes if n.role == NodeRole.LEADER]
    if len(leaders) > 1:
        print("💥 SPLIT-BRAIN DISASTER!")
        print(f"   Multiple leaders: {leaders}")
        print()

        # Write conflicting data
        print("Writing conflicting data to different leaders:")
        leaders[0].write("user:1", "Alice-v1")
        leaders[1].write("user:1", "Alice-v2")
        print(f"  {leaders[0]}: {leaders[0].data}")
        print(f"  {leaders[1]}: {leaders[1].data}")
        print()

        print("⚠️  Data is now inconsistent across the cluster!")
        print()


def demonstrate_quorum_solution():
    """Show how quorums prevent split-brain."""

    print("=" * 80)
    print("SCENARIO 3: QUORUM-BASED SOLUTION")
    print("=" * 80)
    print()

    cluster = Cluster(num_nodes=3)
    print(f"Cluster size: {cluster.num_nodes}")
    print(f"Quorum size: {cluster.quorum_size}")
    print()

    # Initial state
    print("Initial state: 3 nodes, all can communicate")
    cluster.elect_leader()
    leader = cluster.get_leader()
    print(f"Leader: {leader}")
    print()

    # Write initial data
    leader.write("user:1", "Alice")
    for node in cluster.nodes:
        if node != leader:
            node.data = leader.data.copy()
    print()

    # Introduce partition
    print("🔴 NETWORK PARTITION OCCURS!")
    print("   Node 0 ◄──► Node 1     Node 2 (isolated)")
    print()

    cluster.nodes[2].isolate_from(0)
    cluster.nodes[2].isolate_from(1)
    cluster.nodes[0].isolate_from(2)
    cluster.nodes[1].isolate_from(2)

    # New election
    print("⏱️  Heartbeat timeout. New election starts...")
    cluster.elect_leader()

    print()
    print("✅ QUORUM PREVENTS SPLIT-BRAIN:")
    print()

    # Check each partition
    partition_a = [cluster.nodes[0], cluster.nodes[1]]
    partition_b = [cluster.nodes[2]]

    print(f"Partition A (nodes 0, 1): {len(partition_a)} nodes")
    print(f"  Can form quorum? {len(partition_a) >= cluster.quorum_size}")
    leaders_a = [n for n in partition_a if n.role == NodeRole.LEADER]
    print(f"  Leaders: {leaders_a if leaders_a else 'None'}")
    print()

    print(f"Partition B (node 2): {len(partition_b)} nodes")
    print(f"  Can form quorum? {len(partition_b) >= cluster.quorum_size}")
    leaders_b = [n for n in partition_b if n.role == NodeRole.LEADER]
    print(f"  Leaders: {leaders_b if leaders_b else 'None'}")
    print()

    print("Result:")
    print(f"  Total leaders: {cluster.count_leaders()}")
    if cluster.count_leaders() <= 1:
        print("  ✅ No split-brain! At most one leader.")
    print()


def demonstrate_partition_healing():
    """Show what happens when a partition heals."""

    print("=" * 80)
    print("SCENARIO 4: PARTITION HEALING")
    print("=" * 80)
    print()

    cluster = Cluster(num_nodes=3)

    # Initial state
    print("Initial state: 3 nodes, all can communicate")
    cluster.elect_leader()
    leader = cluster.get_leader()
    leader.write("user:1", "Alice")
    for node in cluster.nodes:
        if node != leader:
            node.data = leader.data.copy()
    print(f"Leader: {leader}, data: {leader.data}")
    print()

    # Partition
    print("🔴 Network partition occurs")
    cluster.nodes[2].isolate_from(0)
    cluster.nodes[2].isolate_from(1)
    cluster.nodes[0].isolate_from(2)
    cluster.nodes[1].isolate_from(2)
    cluster.elect_leader()
    print()

    # Write to the leader in partition A
    leader_a = [n for n in cluster.nodes[:2] if n.role == NodeRole.LEADER][0]
    print(f"Leader in partition A: {leader_a}")
    leader_a.write("user:1", "Alice-updated")
    print(f"Write to partition A: user:1 = Alice-updated")
    print()

    # Heal partition
    print("🟢 Network partition heals")
    cluster.nodes[2].reconnect_to(0)
    cluster.nodes[2].reconnect_to(1)
    cluster.nodes[0].reconnect_to(2)
    cluster.nodes[1].reconnect_to(2)
    print()

    print("State after healing:")
    for node in cluster.nodes:
        print(f"  {node}: {node.data}")
    print()

    print("⚠️  PROBLEM: Data is inconsistent!")
    print("   Partition A has: Alice-updated")
    print("   Partition B has: Alice (old value)")
    print()

    print("Solution: Reconciliation")
    print("  - Partition B (minority) must accept data from partition A (majority)")
    print("  - Or use conflict resolution (Last-Write-Wins, CRDTs, etc.)")
    print()


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    demonstrate_normal_operation()
    print()
    print()
    demonstrate_network_partition()
    print()
    print()
    demonstrate_quorum_solution()
    print()
    print()
    demonstrate_partition_healing()

    print()
    print("=" * 80)
    print("KEY TAKEAWAYS")
    print("=" * 80)
    print()
    print("1. Network partitions are common and cause split-brain")
    print("   - Both sides think the other is dead")
    print("   - Both sides might try to become leader")
    print("   - Data becomes inconsistent")
    print()
    print("2. Quorums prevent split-brain")
    print("   - A node can only become leader if it has support from a MAJORITY")
    print("   - In a partition, at most one side has a quorum")
    print("   - The minority side cannot become leader")
    print()
    print("3. When partitions heal, data must be reconciled")
    print("   - The minority side must accept data from the majority")
    print("   - Or use conflict resolution strategies")
    print()
