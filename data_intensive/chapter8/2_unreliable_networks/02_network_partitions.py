"""
Exercise 2: Network Partitions — Split-Brain Disaster

DDIA Reference: Chapter 8, "Network Partitions" (pp. 282-284)

This exercise demonstrates network partitions (netsplits) where the network
link between some nodes is broken, isolating them into separate groups.

Key concepts:
  - Network partition isolates nodes into separate groups
  - Each group can communicate internally but not across groups
  - Both groups might think they're the "real" cluster
  - Split-brain: two leaders in different partitions
  - Quorum: only the partition with majority can continue
  - Data corruption when partition heals

Run: python 02_network_partitions.py
"""

import sys
import time
import random
from enum import Enum
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, field

# Fix Windows terminal encoding for Unicode output
sys.stdout.reconfigure(encoding='utf-8')


# =============================================================================
# CORE COMPONENTS: Node, Cluster, NetworkPartition
# =============================================================================

class NodeRole(Enum):
    """Role of a node in the cluster."""
    LEADER = "leader"
    FOLLOWER = "follower"
    CANDIDATE = "candidate"


@dataclass
class HeartbeatMessage:
    """A heartbeat message from leader to followers."""
    leader_id: str
    term: int
    timestamp: float


@dataclass
class Node:
    """
    A node in a distributed cluster.

    DDIA: "A network partition is when the network link between some nodes
    is broken, isolating them into separate groups that can communicate
    within a group but not across groups."
    """

    node_id: str
    role: NodeRole = NodeRole.FOLLOWER
    term: int = 0  # Election term (like Raft)
    leader_id: Optional[str] = None
    storage: Dict[str, str] = field(default_factory=dict)
    last_heartbeat: float = field(default_factory=time.time)
    is_alive: bool = True

    def __repr__(self):
        role_str = self.role.value.upper()
        leader_str = f" (leader={self.leader_id})" if self.leader_id else ""
        return f"[{self.node_id}:{role_str}{leader_str}]"


class Cluster:
    """
    A distributed cluster of nodes.

    Simulates a cluster where nodes can communicate and elect leaders.
    """

    def __init__(self, node_ids: List[str]):
        self.nodes: Dict[str, Node] = {node_id: Node(node_id) for node_id in node_ids}
        self.partitions: List[Set[str]] = [set(node_ids)]  # Initially one partition
        self.write_log: List[Dict] = []

    def get_node(self, node_id: str) -> Node:
        return self.nodes[node_id]

    def get_partition_for_node(self, node_id: str) -> Set[str]:
        """Get the partition (group of nodes) that a node belongs to."""
        for partition in self.partitions:
            if node_id in partition:
                return partition
        return set()

    def can_communicate(self, node_a: str, node_b: str) -> bool:
        """Check if two nodes can communicate (are in same partition)."""
        return self.get_partition_for_node(node_a) == self.get_partition_for_node(node_b)

    def create_partition(self, group1: Set[str], group2: Set[str]):
        """
        Create a network partition splitting the cluster into two groups.

        DDIA: "A network partition is when the network link between some nodes
        is broken, isolating them into separate groups."
        """
        self.partitions = [group1, group2]

    def heal_partition(self):
        """Heal the network partition, reuniting all nodes."""
        all_nodes = set(self.nodes.keys())
        self.partitions = [all_nodes]

    def elect_leader_in_partition(self, partition: Set[str]):
        """
        Elect a leader in a partition using simple majority voting.

        DDIA: "The solution is to use a quorum: a majority of nodes must
        agree for a decision to be considered valid."
        """
        if len(partition) == 0:
            return

        # Check if partition has a majority
        total_nodes = len(self.nodes)
        has_majority = len(partition) > total_nodes / 2

        if not has_majority:
            # Minority partition cannot elect a leader
            for node_id in partition:
                node = self.get_node(node_id)
                node.role = NodeRole.FOLLOWER
                node.leader_id = None
            return

        # Majority partition elects a leader
        # Choose the node with highest term (or random if tied)
        candidates = [self.get_node(nid) for nid in partition]
        leader = max(candidates, key=lambda n: (n.term, n.node_id))

        for node_id in partition:
            node = self.get_node(node_id)
            if node_id == leader.node_id:
                node.role = NodeRole.LEADER
                node.term += 1
                node.leader_id = node_id
            else:
                node.role = NodeRole.FOLLOWER
                node.leader_id = leader.node_id

    def write_to_leader(self, partition: Set[str], key: str, value: str) -> bool:
        """
        Write data to the leader in a partition.

        Returns True if write succeeded, False if no leader in partition.
        """
        # Find leader in partition
        leader = None
        for node_id in partition:
            node = self.get_node(node_id)
            if node.role == NodeRole.LEADER:
                leader = node
                break

        if leader is None:
            return False

        # Write to leader
        leader.storage[key] = value
        self.write_log.append({
            "partition": partition,
            "leader": leader.node_id,
            "key": key,
            "value": value,
            "timestamp": time.time()
        })
        return True

    def get_state_summary(self) -> str:
        """Get a summary of cluster state."""
        lines = []
        for i, partition in enumerate(self.partitions):
            lines.append(f"\n  Partition {i+1}: {sorted(partition)}")
            for node_id in sorted(partition):
                node = self.get_node(node_id)
                role_str = node.role.value.upper()
                lines.append(f"    {node_id}: {role_str} (term={node.term})")
        return "\n".join(lines)


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


def demo_1_normal_cluster():
    """
    Demo 1: Normal cluster operation (no partition).

    All nodes can communicate, one leader is elected.
    """
    print_header("DEMO 1: Normal Cluster Operation")
    print("""
    In a healthy cluster, all nodes can communicate.
    A leader is elected and accepts writes.
    """)

    cluster = Cluster(["A", "B", "C"])

    print("  Initial state:")
    print(cluster.get_state_summary())

    print("\n  Electing leader in partition {A, B, C}...")
    cluster.elect_leader_in_partition(cluster.partitions[0])

    print(cluster.get_state_summary())

    print("\n  Writing data to leader:")
    success = cluster.write_to_leader(cluster.partitions[0], "user:1", "Alice")
    print(f"    Write 'user:1' = 'Alice': {'✅ SUCCESS' if success else '❌ FAILED'}")

    success = cluster.write_to_leader(cluster.partitions[0], "user:2", "Bob")
    print(f"    Write 'user:2' = 'Bob': {'✅ SUCCESS' if success else '❌ FAILED'}")

    print("""
  💡 KEY INSIGHT:
     In a healthy cluster, there's one leader and all writes go through it.
     All nodes can communicate, so they agree on who the leader is.
    """)


def demo_2_network_partition_occurs():
    """
    Demo 2: Network partition occurs.

    The cluster splits into two groups that cannot communicate.
    """
    print_header("DEMO 2: Network Partition Occurs")
    print("""
    A network link fails, splitting the cluster into two isolated groups.
    Each group can communicate internally but not across groups.

    Before:  A ◄──► B ◄──► C
    After:   A ◄──► B     C (isolated)
    """)

    cluster = Cluster(["A", "B", "C"])

    print("  Before partition:")
    print(cluster.get_state_summary())

    # Elect leader in healthy cluster
    cluster.elect_leader_in_partition(cluster.partitions[0])
    print("\n  Leader elected: A")

    # Create partition: {A, B} vs {C}
    print("\n  💥 NETWORK PARTITION OCCURS!")
    print("     Link between B and C is broken")

    cluster.create_partition({"A", "B"}, {"C"})

    print("\n  After partition:")
    print(cluster.get_state_summary())

    print("""
  💡 KEY INSIGHT:
     The cluster is now split into two groups:
       • Partition 1: {A, B} - has 2 nodes (majority of 3)
       • Partition 2: {C}   - has 1 node (minority of 3)

     The majority partition can continue operating.
     The minority partition should stop accepting writes.
    """)


def demo_3_split_brain_disaster():
    """
    Demo 3: Split-brain disaster.

    Both partitions elect leaders, causing data corruption.
    """
    print_header("DEMO 3: Split-Brain Disaster")
    print("""
    ⚠️  DANGER: If both partitions elect leaders, we have split-brain!
    Two leaders in different partitions can accept conflicting writes.
    When the partition heals, data is corrupted.
    """)

    cluster = Cluster(["A", "B", "C"])

    # Initial state
    cluster.elect_leader_in_partition(cluster.partitions[0])
    print("  Initial: Leader A elected in {A, B, C}")

    # Create partition
    cluster.create_partition({"A", "B"}, {"C"})
    print("\n  Partition occurs: {A, B} vs {C}")

    # WRONG: Both partitions elect leaders
    print("\n  ⚠️  WRONG APPROACH: Both partitions elect leaders")
    print("     (This is what happens if you don't use quorum)")

    # Partition 1 elects leader
    cluster.elect_leader_in_partition({"A", "B"})
    leader1 = cluster.get_node("A")
    print(f"\n  Partition 1 {{A, B}}: Leader = {leader1.node_id}")

    # Partition 2 elects leader (WRONG!)
    cluster.elect_leader_in_partition({"C"})
    leader2 = cluster.get_node("C")
    print(f"  Partition 2 {{C}}:   Leader = {leader2.node_id}")

    print("\n  💥 SPLIT-BRAIN: Two leaders!")
    print(f"     Leader 1 (A) in partition {{A, B}}")
    print(f"     Leader 2 (C) in partition {{C}}")

    # Conflicting writes
    print("\n  Conflicting writes occur:")
    print("    Leader A writes: user:1 = 'Alice'")
    cluster.write_to_leader({"A", "B"}, "user:1", "Alice")

    print("    Leader C writes: user:1 = 'Charlie'")
    cluster.write_to_leader({"C"}, "user:1", "Charlie")

    print("\n  When partition heals:")
    print("    A has: user:1 = 'Alice'")
    print("    B has: user:1 = 'Alice'")
    print("    C has: user:1 = 'Charlie'")
    print("    ❌ DATA CORRUPTION: Which value is correct?")

    print("""
  💡 SOLUTION: Use Quorum

     Only the partition with a MAJORITY of nodes can elect a leader.
     Minority partitions cannot accept writes.

     In a 3-node cluster:
       • Majority: 2 or more nodes
       • Minority: 1 node

     Partition 1 {A, B}: 2 nodes = MAJORITY → can elect leader ✅
     Partition 2 {C}:    1 node  = MINORITY → cannot elect leader ❌
    """)


def demo_4_quorum_prevents_split_brain():
    """
    Demo 4: Using quorum to prevent split-brain.

    Only the majority partition can elect a leader.
    """
    print_header("DEMO 4: Quorum Prevents Split-Brain")
    print("""
    Using quorum voting, only the partition with a majority of nodes
    can elect a leader. The minority partition stops accepting writes.
    """)

    cluster = Cluster(["A", "B", "C"])

    # Initial state
    cluster.elect_leader_in_partition(cluster.partitions[0])
    print("  Initial: Leader A elected in {A, B, C}")

    # Create partition
    cluster.create_partition({"A", "B"}, {"C"})
    print("\n  Partition occurs: {A, B} vs {C}")

    # CORRECT: Use quorum
    print("\n  ✅ CORRECT APPROACH: Use quorum voting")

    # Partition 1 (majority) elects leader
    cluster.elect_leader_in_partition({"A", "B"})
    print(f"\n  Partition 1 {{A, B}}: 2 nodes = MAJORITY")
    print(f"    → Can elect leader: {cluster.get_node('A').node_id}")
    print(f"    → Can accept writes ✅")

    # Partition 2 (minority) cannot elect leader
    cluster.elect_leader_in_partition({"C"})
    print(f"\n  Partition 2 {{C}}: 1 node = MINORITY")
    print(f"    → Cannot elect leader (no majority)")
    print(f"    → Cannot accept writes ❌")

    # Writes
    print("\n  Write attempts:")
    success = cluster.write_to_leader({"A", "B"}, "user:1", "Alice")
    print(f"    Partition 1 write: {'✅ SUCCESS' if success else '❌ FAILED'}")

    success = cluster.write_to_leader({"C"}, "user:1", "Charlie")
    print(f"    Partition 2 write: {'✅ FAILED (no leader)' if not success else '❌ UNEXPECTED SUCCESS'}")

    print("\n  When partition heals:")
    print("    A has: user:1 = 'Alice'")
    print("    B has: user:1 = 'Alice'")
    print("    C has: user:1 = ??? (no write occurred)")
    print("    ✅ NO DATA CORRUPTION: Minority partition didn't write")

    print("""
  💡 KEY INSIGHT:
     By using quorum, we ensure:
       1. Only one partition can have a leader
       2. Only the leader can accept writes
       3. When partition heals, minority partition catches up from majority

     This is the fundamental principle behind Raft, Paxos, and other
     consensus algorithms.
    """)


def demo_5_partition_healing():
    """
    Demo 5: Partition heals and cluster recovers.

    When the network link is restored, nodes rejoin and sync state.
    """
    print_header("DEMO 5: Partition Healing")
    print("""
    When the network partition is healed, the isolated nodes rejoin
    the cluster and catch up on missed writes.
    """)

    cluster = Cluster(["A", "B", "C"])

    # Initial state
    cluster.elect_leader_in_partition(cluster.partitions[0])
    print("  Initial: Leader A elected")

    # Create partition
    cluster.create_partition({"A", "B"}, {"C"})
    cluster.elect_leader_in_partition({"A", "B"})
    cluster.elect_leader_in_partition({"C"})

    print("\n  Partition occurs: {A, B} vs {C}")
    print("  Partition 1 {A, B}: Leader = A")
    print("  Partition 2 {C}:   No leader (minority)")

    # Writes in majority partition
    print("\n  Writes in majority partition:")
    cluster.write_to_leader({"A", "B"}, "user:1", "Alice")
    print("    A writes: user:1 = 'Alice'")
    cluster.write_to_leader({"A", "B"}, "user:2", "Bob")
    print("    A writes: user:2 = 'Bob'")

    print("\n  State before healing:")
    print(f"    A storage: {cluster.get_node('A').storage}")
    print(f"    B storage: {cluster.get_node('B').storage}")
    print(f"    C storage: {cluster.get_node('C').storage}")

    # Heal partition
    print("\n  🔧 Network partition is healed!")
    cluster.heal_partition()

    print("\n  Nodes rejoin and sync:")
    print("    C receives missed writes from A")
    print("    C catches up to A's state")

    # Simulate catch-up
    cluster.get_node("C").storage = cluster.get_node("A").storage.copy()

    print("\n  State after healing:")
    print(f"    A storage: {cluster.get_node('A').storage}")
    print(f"    B storage: {cluster.get_node('B').storage}")
    print(f"    C storage: {cluster.get_node('C').storage}")

    print("""
  💡 KEY INSIGHT:
     When partition heals:
       1. Minority partition nodes rejoin the cluster
       2. They catch up on missed writes from the leader
       3. Cluster returns to consistent state
       4. No data loss (because minority didn't accept writes)
    """)


def demo_6_quorum_sizes():
    """
    Demo 6: How quorum size affects partition tolerance.

    Show different cluster sizes and their quorum requirements.
    """
    print_header("DEMO 6: Quorum Sizes and Partition Tolerance")
    print("""
    The quorum size determines how many nodes can fail while the
    cluster continues operating.

    Formula: Quorum = (N / 2) + 1
    where N = total number of nodes
    """)

    cluster_sizes = [3, 5, 7]

    print(f"\n  {'Nodes':<8} {'Quorum':<8} {'Can Tolerate':<20} {'Partition Scenario'}")
    print(f"  {'─'*70}")

    for n in cluster_sizes:
        quorum = (n // 2) + 1
        can_tolerate = quorum - 1
        partition_scenario = f"{quorum} vs {n - quorum}"

        print(f"  {n:<8} {quorum:<8} {can_tolerate} node failures  {partition_scenario}")

    print("""
  💡 KEY INSIGHTS:

     3-node cluster:
       • Quorum = 2 nodes
       • Can tolerate 1 node failure
       • Partition: 2 vs 1 (majority can continue)

     5-node cluster:
       • Quorum = 3 nodes
       • Can tolerate 2 node failures
       • Partition: 3 vs 2 (majority can continue)

     7-node cluster:
       • Quorum = 4 nodes
       • Can tolerate 3 node failures
       • Partition: 4 vs 3 (majority can continue)

     Trade-off:
       • More nodes = more fault tolerance
       • More nodes = slower consensus (more nodes to wait for)
       • More nodes = more network traffic
    """)


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 80)
    print("  EXERCISE 2: NETWORK PARTITIONS — SPLIT-BRAIN DISASTER")
    print("  DDIA Chapter 8: 'Network Partitions'")
    print("=" * 80)
    print("""
  This exercise demonstrates network partitions where the cluster splits
  into isolated groups. You'll see how split-brain occurs and how quorum
  voting prevents it.
    """)

    demo_1_normal_cluster()
    demo_2_network_partition_occurs()
    demo_3_split_brain_disaster()
    demo_4_quorum_prevents_split_brain()
    demo_5_partition_healing()
    demo_6_quorum_sizes()

    print("\n" + "=" * 80)
    print("  EXERCISE 2 COMPLETE ✅")
    print("=" * 80)
    print("""
  Key Takeaways:

  1. 🔴 Network partitions split the cluster into isolated groups
  2. 🔴 Both groups might try to elect leaders (split-brain)
  3. 🔴 Split-brain causes data corruption
  4. ✅ Solution: Use quorum voting (majority partition only)
  5. ✅ Minority partition stops accepting writes
  6. ✅ When partition heals, minority catches up from majority

  Next: Run 03_timeouts_and_delays.py to learn about timeout strategies
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
