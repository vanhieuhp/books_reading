"""
Exercise 2: Leader Election with Quorums

DDIA Reference: Chapter 8, "The Truth is Defined by the Majority" (pp. 300-302)

One of the most important applications of quorums is LEADER ELECTION.

The problem: When the leader crashes, how do we elect a new one?
The naive approach: Any follower can declare itself the new leader.
The disaster: If there's a network partition, both sides might elect leaders!
This is SPLIT-BRAIN — two leaders writing to the same data = corruption.

The solution: Use quorums for leader election.
A node can only become leader if it gets votes from a MAJORITY of nodes.
In a network partition, only the majority partition can elect a leader.

DDIA insight:
  "A node cannot unilaterally declare itself the leader. It must get
   votes from a quorum of nodes. This prevents split-brain."

Run: python 02_leader_election.py
"""

import sys
import time
from typing import List, Optional, Dict, Set
from enum import Enum

# Fix Windows terminal encoding for Unicode output
sys.stdout.reconfigure(encoding='utf-8')


# =============================================================================
# CORE COMPONENTS: NodeState, Node, Cluster, LeaderElection
# =============================================================================

class NodeState(Enum):
    """State of a node in the cluster."""
    FOLLOWER = "FOLLOWER"
    CANDIDATE = "CANDIDATE"
    LEADER = "LEADER"
    DEAD = "DEAD"


class Node:
    """A node in the distributed system."""

    def __init__(self, node_id: int, name: str = None):
        self.node_id = node_id
        self.name = name or f"Node-{node_id}"
        self.state = NodeState.FOLLOWER
        self.current_term = 0  # Election term (like Raft)
        self.voted_for = None  # Who this node voted for in current term
        self.is_alive = True
        self.heartbeat_time = time.time()

    def vote_for(self, candidate_id: int, term: int) -> bool:
        """
        Vote for a candidate in a given term.

        DDIA insight: "A node can only vote once per term."
        This prevents a node from voting for multiple candidates.
        """
        if term > self.current_term:
            self.current_term = term
            self.voted_for = candidate_id
            return True
        elif term == self.current_term and self.voted_for == candidate_id:
            # Already voted for this candidate
            return True
        else:
            # Already voted for someone else in this term
            return False

    def become_leader(self, term: int):
        """This node becomes the leader."""
        self.state = NodeState.LEADER
        self.current_term = term
        self.heartbeat_time = time.time()

    def become_follower(self, term: int):
        """This node becomes a follower."""
        self.state = NodeState.FOLLOWER
        self.current_term = term
        self.voted_for = None

    def become_candidate(self, term: int):
        """This node becomes a candidate."""
        self.state = NodeState.CANDIDATE
        self.current_term = term
        self.voted_for = self.node_id  # Vote for itself

    def __repr__(self):
        return f"{self.name}({self.state.value})"


class Cluster:
    """A cluster of nodes."""

    def __init__(self, node_count: int):
        self.nodes = [Node(i, f"Node-{i+1}") for i in range(node_count)]
        self.total_nodes = node_count
        self.quorum_size = (node_count // 2) + 1
        self.current_leader = None
        self.current_term = 0

    def get_alive_nodes(self) -> List[Node]:
        """Get all alive nodes."""
        return [n for n in self.nodes if n.is_alive]

    def partition_cluster(self, partition_a_size: int) -> tuple:
        """
        Simulate a network partition.

        Returns: (partition_a_nodes, partition_b_nodes)
        """
        partition_a = self.nodes[:partition_a_size]
        partition_b = self.nodes[partition_a_size:]
        return partition_a, partition_b

    def can_partition_have_leader(self, partition: List[Node]) -> bool:
        """Check if a partition has enough nodes for a quorum."""
        return len(partition) >= self.quorum_size


class LeaderElection:
    """Simulates leader election with quorums."""

    def __init__(self, cluster: Cluster):
        self.cluster = cluster

    def request_votes(self, candidate: Node, partition: List[Node]) -> int:
        """
        Candidate requests votes from nodes in a partition.

        Returns: Number of votes received
        """
        votes = 0

        for node in partition:
            if node.node_id == candidate.node_id:
                # Candidate votes for itself
                votes += 1
            else:
                # Request vote from other node
                if node.vote_for(candidate.node_id, candidate.current_term):
                    votes += 1

        return votes

    def elect_leader(self, partition: List[Node]) -> Optional[Node]:
        """
        Attempt to elect a leader in a partition.

        Returns: The elected leader, or None if no quorum
        """
        if len(partition) < self.cluster.quorum_size:
            return None

        # Find the node with the highest term
        candidate = max(partition, key=lambda n: n.current_term)

        # Candidate increments term and requests votes
        candidate.become_candidate(candidate.current_term + 1)

        # Request votes from all nodes in partition
        votes = self.request_votes(candidate, partition)

        # Check if quorum is reached
        if votes >= self.cluster.quorum_size:
            candidate.become_leader(candidate.current_term)
            return candidate
        else:
            candidate.become_follower(candidate.current_term)
            return None


def print_header(title: str):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_section(title: str):
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}")


# =============================================================================
# DEMONSTRATIONS
# =============================================================================

def demo_1_normal_leader_election():
    """
    Demo 1: Normal leader election with no partition.

    DDIA concept: "When the leader crashes, followers detect it
    and elect a new leader."
    """
    print_header("DEMO 1: Normal Leader Election (No Partition)")
    print("""
    Scenario: 5-node cluster, leader crashes, followers elect new leader.
    """)

    cluster = Cluster(5)
    election = LeaderElection(cluster)

    print(f"  Cluster: {', '.join(n.name for n in cluster.nodes)}")
    print(f"  Quorum size: {cluster.quorum_size}")

    print_section("Step 1: Initial state")
    print(f"  All nodes are followers")
    for node in cluster.nodes:
        print(f"    {node.name}: {node.state.value}")

    print_section("Step 2: Leader crashes")
    print(f"  Followers detect no heartbeat for 3 seconds")
    print(f"  Followers start election")

    print_section("Step 3: Election process")
    print(f"  Node-1 becomes candidate and requests votes")

    # Simulate election
    partition = cluster.nodes  # All nodes can communicate
    leader = election.elect_leader(partition)

    if leader:
        print(f"\n  ✅ NEW LEADER ELECTED: {leader.name}")
        print(f"     Term: {leader.current_term}")
        print(f"     Votes received: {cluster.quorum_size}")
    else:
        print(f"\n  ❌ NO LEADER ELECTED (no quorum)")

    print_section("Step 4: Final state")
    for node in cluster.nodes:
        status = "👑" if node.state == NodeState.LEADER else "  "
        print(f"  {status} {node.name}: {node.state.value} (term={node.current_term})")


def demo_2_network_partition_split_brain_prevention():
    """
    Demo 2: Network partition — quorums prevent split-brain.

    DDIA concept: "In a network partition, only the majority partition
    can elect a leader. The minority partition cannot."
    """
    print_header("DEMO 2: Network Partition — Split-Brain Prevention")
    print("""
    Scenario: 5-node cluster splits into two partitions.
    Quorum size = 3

    PARTITION A: Nodes 1, 2, 3 (majority)
    PARTITION B: Nodes 4, 5 (minority)

    DDIA insight: "Only the majority partition can elect a leader."
    """)

    cluster = Cluster(5)
    election = LeaderElection(cluster)

    print(f"  Total nodes: {cluster.total_nodes}")
    print(f"  Quorum size: {cluster.quorum_size}")

    # Simulate partition
    partition_a, partition_b = cluster.partition_cluster(3)

    print_section("Partition A (Majority: 3 nodes)")
    print(f"  Nodes: {', '.join(n.name for n in partition_a)}")
    print(f"  Nodes available: {len(partition_a)}")
    print(f"  Quorum needed: {cluster.quorum_size}")

    leader_a = election.elect_leader(partition_a)
    if leader_a:
        print(f"  ✅ LEADER ELECTED: {leader_a.name}")
        print(f"     Votes: {cluster.quorum_size}/{len(partition_a)}")
    else:
        print(f"  ❌ NO LEADER (no quorum)")

    print_section("Partition B (Minority: 2 nodes)")
    print(f"  Nodes: {', '.join(n.name for n in partition_b)}")
    print(f"  Nodes available: {len(partition_b)}")
    print(f"  Quorum needed: {cluster.quorum_size}")

    leader_b = election.elect_leader(partition_b)
    if leader_b:
        print(f"  ✅ LEADER ELECTED: {leader_b.name}")
        print(f"     Votes: {cluster.quorum_size}/{len(partition_b)}")
    else:
        print(f"  ❌ NO LEADER (no quorum)")

    print_section("Result")
    print(f"""
  Partition A: {'✅ HAS LEADER' if leader_a else '❌ NO LEADER'}
  Partition B: {'✅ HAS LEADER' if leader_b else '❌ NO LEADER'}

  💡 KEY INSIGHT (DDIA):
     Only ONE partition has a leader!
     This prevents split-brain and data corruption. ✅

     • Partition A can accept writes
     • Partition B cannot (no quorum)
     • When partition heals, B catches up from A
    """)


def demo_3_zombie_leader_detection():
    """
    Demo 3: Detecting and removing zombie leaders.

    DDIA concept: "A zombie leader is a leader that thinks it's still
    in charge, but the cluster has elected a new leader."
    """
    print_header("DEMO 3: Zombie Leader Detection")
    print("""
    Scenario: Network partition creates a zombie leader.
    The minority partition has a leader, but it's not valid.

    DDIA insight: "A leader is only valid if it has a quorum."
    """)

    cluster = Cluster(5)
    election = LeaderElection(cluster)

    print(f"  Total nodes: {cluster.total_nodes}")
    print(f"  Quorum size: {cluster.quorum_size}")

    # Simulate partition
    partition_a, partition_b = cluster.partition_cluster(3)

    print_section("Before partition")
    print(f"  All nodes can communicate")
    print(f"  Node-1 is the leader")
    cluster.nodes[0].become_leader(1)

    print_section("Network partition occurs")
    print(f"  Partition A: {', '.join(n.name for n in partition_a)}")
    print(f"  Partition B: {', '.join(n.name for n in partition_b)}")

    print_section("Partition A (Majority)")
    print(f"  Nodes: {len(partition_a)}")
    print(f"  Old leader (Node-1) is in this partition")
    print(f"  ✅ Node-1 remains valid leader (has quorum)")

    print_section("Partition B (Minority)")
    print(f"  Nodes: {len(partition_b)}")
    print(f"  No leader in this partition")
    print(f"  Cannot elect new leader (no quorum)")

    print_section("Zombie Leader Scenario")
    print(f"""
    If Node-4 (in minority partition) tries to become leader:
      • Node-4 requests votes from Node-5
      • Node-4 gets 2 votes (itself + Node-5)
      • Quorum needed: 3
      • ❌ NO QUORUM → Node-4 is a ZOMBIE leader

    Why is this safe?
      • Node-4 cannot write to the database
      • Clients won't accept writes from Node-4 (no quorum)
      • When partition heals, Node-4 discovers Node-1 is the real leader
      • Node-4 steps down and becomes a follower ✅
    """)


def demo_4_quorum_sizes_and_tolerance():
    """
    Demo 4: How quorum size affects fault tolerance.

    DDIA concept: "Larger clusters can tolerate more failures."
    """
    print_header("DEMO 4: Quorum Sizes and Fault Tolerance")
    print("""
    DDIA insight: "The quorum size determines how many nodes can fail
    while still maintaining a valid leader."
    """)

    print_section("Fault Tolerance Analysis")
    print(f"\n  {'Cluster':<12} {'Quorum':<10} {'Can Tolerate':<20} {'Example'}")
    print(f"  {'─'*60}")

    for n in [3, 5, 7, 9]:
        quorum = (n // 2) + 1
        tolerance = n - quorum
        example = f"{tolerance} node{'s' if tolerance != 1 else ''}"
        print(f"  {n} nodes    {quorum:<10} {tolerance} failures       {example}")

    print("""
  💡 KEY INSIGHT (DDIA):
     • 3 nodes: quorum=2, tolerate 1 failure
     • 5 nodes: quorum=3, tolerate 2 failures
     • 7 nodes: quorum=4, tolerate 3 failures

     More nodes = more fault tolerance, but also more latency
     (must wait for more nodes to respond).
    """)


def demo_5_term_numbers_prevent_stale_leaders():
    """
    Demo 5: How term numbers prevent stale leaders.

    DDIA concept: "Term numbers ensure that old leaders cannot
    override new leaders."
    """
    print_header("DEMO 5: Term Numbers Prevent Stale Leaders")
    print("""
    DDIA insight: "Each election increments a term number.
    A node with a higher term number is always newer."
    """)

    cluster = Cluster(5)

    print_section("Scenario: Old leader comes back online")
    print(f"""
    Timeline:
      T=0: Node-1 is leader (term=1)
      T=5: Network partition occurs
      T=10: Partition A elects Node-2 as new leader (term=2)
      T=15: Partition heals, Node-1 comes back online
    """)

    print_section("What happens when Node-1 comes back?")
    print(f"""
    Node-1 (term=1) sends heartbeat to Node-2 (term=2)
    Node-2 sees: term 1 < term 2
    Node-2 rejects Node-1's heartbeat ✅

    Node-1 receives Node-2's heartbeat with term=2
    Node-1 sees: term 1 < term 2
    Node-1 steps down and becomes follower ✅

    Result: Node-2 remains leader, no split-brain! ✅
    """)

    print("""
  💡 KEY INSIGHT (DDIA):
     Term numbers are like version numbers for leadership.
     A higher term always wins, preventing stale leaders
     from overriding new leaders.
    """)


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 80)
    print("  EXERCISE 2: LEADER ELECTION WITH QUORUMS")
    print("  DDIA Chapter 8: 'The Truth is Defined by the Majority'")
    print("=" * 80)
    print("""
  This exercise shows how quorums are used for leader election.

  Key insight: A node can only become leader if it gets votes from
  a MAJORITY of nodes. This prevents split-brain disasters.
    """)

    demo_1_normal_leader_election()
    demo_2_network_partition_split_brain_prevention()
    demo_3_zombie_leader_detection()
    demo_4_quorum_sizes_and_tolerance()
    demo_5_term_numbers_prevent_stale_leaders()

    print("\n" + "=" * 80)
    print("  EXERCISE 2 COMPLETE ✅")
    print("=" * 80)
    print("""
  Key Takeaways:

  1. 🗳️  Leader election requires QUORUM of votes
  2. 🛡️  Quorums prevent split-brain disasters
  3. 🔒 Only majority partition can elect leader
  4. 📊 Minority partition cannot make decisions
  5. 🔢 Term numbers prevent stale leaders

  Next: Run 03_byzantine_faults.py to see what happens when nodes lie
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
