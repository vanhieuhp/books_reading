"""
Exercise 1: Quorum Basics — Majority Consensus

DDIA Reference: Chapter 8, "The Truth is Defined by the Majority" (pp. 300-302)

In a distributed system, a node cannot trust its own judgment. A node might think
it's the leader, but the network has partitioned and the other nodes have elected
a new leader. The old node is now a "zombie leader" — it thinks it's in charge,
but nobody else agrees.

The solution: QUORUMS. A node cannot unilaterally declare something as true.
It can only believe something if a MAJORITY of nodes (a quorum) agrees.

Key insight from DDIA:
  "In a distributed system, we can't rely on any single node's judgment.
   We need a quorum — a majority of nodes — to agree on a decision."

Run: python 01_quorum_basics.py
"""

import sys
from typing import List, Dict, Any
from collections import Counter

# Fix Windows terminal encoding for Unicode output
sys.stdout.reconfigure(encoding='utf-8')


# =============================================================================
# CORE COMPONENTS: Node, Quorum, VotingSystem
# =============================================================================

class Node:
    """A single node in the distributed system."""

    def __init__(self, node_id: int, name: str = None):
        self.node_id = node_id
        self.name = name or f"Node-{node_id}"
        self.vote = None  # What this node votes for
        self.is_alive = True

    def cast_vote(self, value: Any) -> Any:
        """This node votes for a value."""
        self.vote = value
        return value

    def __repr__(self):
        return f"{self.name}"


class QuorumSystem:
    """
    A quorum system for distributed consensus.

    DDIA insight: "A quorum is a majority of nodes. In a system with N nodes,
    a quorum is any set of more than N/2 nodes."

    Why majority? Because at most one majority can exist at a time.
    If you split 5 nodes into two groups, one group has 3+ nodes (majority)
    and the other has 2 nodes (minority). Only the majority can make decisions.
    """

    def __init__(self, nodes: List[Node]):
        self.nodes = nodes
        self.total_nodes = len(nodes)
        self.quorum_size = (self.total_nodes // 2) + 1  # Majority

    def collect_votes(self, values: Dict[int, Any]) -> Dict[str, Any]:
        """
        Collect votes from nodes and determine if a quorum agrees.

        Args:
            values: Dict mapping node_id to the value that node votes for

        Returns:
            Dict with decision, vote counts, and quorum status
        """
        # Count votes
        vote_counts = Counter(values.values())

        # Find the value with the most votes
        most_common_value, vote_count = vote_counts.most_common(1)[0]

        # Check if quorum is reached
        quorum_reached = vote_count >= self.quorum_size

        return {
            "most_common_value": most_common_value,
            "vote_count": vote_count,
            "quorum_size": self.quorum_size,
            "quorum_reached": quorum_reached,
            "vote_distribution": dict(vote_counts),
            "total_votes": len(values),
        }

    def can_have_two_quorums(self) -> bool:
        """
        Can two different quorums exist at the same time?

        DDIA insight: NO! If you have N nodes and need > N/2 for a quorum,
        then at most one quorum can exist. If two quorums existed, they would
        need to overlap (share nodes), which is impossible.
        """
        # Two quorums would need 2 * quorum_size nodes
        # But we only have total_nodes
        return 2 * self.quorum_size <= self.total_nodes


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

def demo_1_basic_quorum_voting():
    """
    Demo 1: Basic quorum voting with 5 nodes.

    DDIA concept: "A quorum is a majority of nodes."
    """
    print_header("DEMO 1: Basic Quorum Voting (5 nodes)")
    print("""
    Scenario: 5 nodes vote on whether to accept a write.
    Quorum size = 3 (majority of 5)
    """)

    # Create 5 nodes
    nodes = [Node(i, f"Node-{i+1}") for i in range(5)]
    quorum = QuorumSystem(nodes)

    print(f"  Total nodes: {quorum.total_nodes}")
    print(f"  Quorum size: {quorum.quorum_size} (majority)")

    # Scenario 1: 3 YES, 2 NO
    print_section("Scenario 1: 3 YES, 2 NO")
    votes = {0: "YES", 1: "YES", 2: "NO", 3: "YES", 4: "NO"}

    for node_id, vote in votes.items():
        print(f"  {nodes[node_id].name}: VOTE {vote} {'✅' if vote == 'YES' else '❌'}")

    result = quorum.collect_votes(votes)
    print(f"\n  Vote distribution: {result['vote_distribution']}")
    print(f"  Quorum size needed: {result['quorum_size']}")
    print(f"  Votes for {result['most_common_value']}: {result['vote_count']}")
    print(f"\n  ✅ DECISION: {result['most_common_value']} (quorum reached)")

    # Scenario 2: 2 YES, 3 NO
    print_section("Scenario 2: 2 YES, 3 NO")
    votes = {0: "YES", 1: "NO", 2: "NO", 3: "YES", 4: "NO"}

    for node_id, vote in votes.items():
        print(f"  {nodes[node_id].name}: VOTE {vote} {'✅' if vote == 'YES' else '❌'}")

    result = quorum.collect_votes(votes)
    print(f"\n  Vote distribution: {result['vote_distribution']}")
    print(f"  Quorum size needed: {result['quorum_size']}")
    print(f"  Votes for {result['most_common_value']}: {result['vote_count']}")
    print(f"\n  ✅ DECISION: {result['most_common_value']} (quorum reached)")

    # Scenario 3: 2 YES, 2 NO, 1 ABSTAIN
    print_section("Scenario 3: 2 YES, 2 NO, 1 ABSTAIN")
    votes = {0: "YES", 1: "NO", 2: "NO", 3: "YES", 4: "ABSTAIN"}

    for node_id, vote in votes.items():
        status = "✅" if vote == "YES" else ("❌" if vote == "NO" else "⏸️")
        print(f"  {nodes[node_id].name}: VOTE {vote} {status}")

    result = quorum.collect_votes(votes)
    print(f"\n  Vote distribution: {result['vote_distribution']}")
    print(f"  Quorum size needed: {result['quorum_size']}")
    print(f"  Votes for {result['most_common_value']}: {result['vote_count']}")
    print(f"\n  ✅ DECISION: {result['most_common_value']} (quorum reached)")


def demo_2_quorum_sizes():
    """
    Demo 2: How quorum size changes with cluster size.

    DDIA concept: Quorum = > N/2 nodes
    """
    print_header("DEMO 2: Quorum Sizes for Different Cluster Sizes")
    print("""
    DDIA insight: "In a system with N nodes, a quorum is any set of
    more than N/2 nodes."

    This table shows how quorum size grows:
    """)

    print(f"\n  {'Cluster Size':<15} {'Quorum Size':<15} {'Tolerance':<15}")
    print(f"  {'─'*45}")

    for n in [3, 5, 7, 9, 11, 21, 101]:
        quorum_size = (n // 2) + 1
        tolerance = n - quorum_size  # How many nodes can fail
        print(f"  {n:<15} {quorum_size:<15} {tolerance} nodes")

    print("""
  💡 KEY INSIGHT (DDIA):
     • With 3 nodes: quorum = 2 (can tolerate 1 failure)
     • With 5 nodes: quorum = 3 (can tolerate 2 failures)
     • With 7 nodes: quorum = 4 (can tolerate 3 failures)

     Adding more nodes increases fault tolerance, but also increases
     latency (must wait for more nodes to respond).
    """)


def demo_3_two_quorums_impossible():
    """
    Demo 3: Prove that two quorums cannot exist simultaneously.

    DDIA concept: "At most one quorum can exist at a time."
    This is the fundamental property that prevents split-brain.
    """
    print_header("DEMO 3: Two Quorums Cannot Coexist")
    print("""
    DDIA insight: "If you have N nodes and need > N/2 for a quorum,
    then at most one quorum can exist at a time."

    Why? Because two quorums would need to overlap (share nodes).
    """)

    print_section("Mathematical Proof")
    print("""
    Assume we have N nodes and quorum size Q = ⌊N/2⌋ + 1

    If two quorums existed:
      Quorum A: Q nodes
      Quorum B: Q nodes
      Total needed: 2Q nodes

    But: 2Q = 2(⌊N/2⌋ + 1) = N + 2 > N

    We only have N nodes, so 2Q > N is impossible!
    Therefore, at most one quorum can exist. ✅
    """)

    print_section("Practical Example: 5 Nodes")
    nodes = [Node(i, f"Node-{i+1}") for i in range(5)]
    quorum = QuorumSystem(nodes)

    print(f"  Total nodes: 5")
    print(f"  Quorum size: 3")
    print(f"  Can two quorums exist? {quorum.can_have_two_quorums()}")

    print("""
    Possible quorums (any 3 nodes):
      {1, 2, 3}, {1, 2, 4}, {1, 2, 5}, {1, 3, 4}, {1, 3, 5},
      {1, 4, 5}, {2, 3, 4}, {2, 3, 5}, {2, 4, 5}, {3, 4, 5}

    If Quorum A = {1, 2, 3} and Quorum B = {3, 4, 5}:
      They share node 3 (overlap)
      If node 3 votes for A, it cannot vote for B
      So they cannot both be valid quorums ✅
    """)

    print("""
  💡 KEY INSIGHT (DDIA):
     This is why quorums prevent split-brain!
     In a network partition, only one partition can have a quorum.
     The other partition cannot make decisions.
    """)


def demo_4_network_partition():
    """
    Demo 4: How quorums handle network partitions.

    DDIA concept: "In a network partition, only the partition with
    a quorum can make decisions."
    """
    print_header("DEMO 4: Network Partition with Quorums")
    print("""
    Scenario: 5-node cluster splits into two partitions.
    Quorum size = 3

    PARTITION A: Nodes 1, 2, 3 (can communicate)
    PARTITION B: Nodes 4, 5 (can communicate)
    """)

    print_section("Partition A (3 nodes)")
    nodes_a = [Node(i, f"Node-{i+1}") for i in range(3)]
    quorum_a = QuorumSystem(nodes_a)

    print(f"  Nodes: {', '.join(n.name for n in nodes_a)}")
    print(f"  Quorum size needed: 3 (majority of 5)")
    print(f"  Nodes available: 3")
    print(f"  ✅ CAN MAKE DECISIONS (has quorum)")

    print_section("Partition B (2 nodes)")
    nodes_b = [Node(i+3, f"Node-{i+4}") for i in range(2)]
    quorum_b = QuorumSystem(nodes_b)

    print(f"  Nodes: {', '.join(n.name for n in nodes_b)}")
    print(f"  Quorum size needed: 3 (majority of 5)")
    print(f"  Nodes available: 2")
    print(f"  ❌ CANNOT MAKE DECISIONS (no quorum)")

    print("""
  💡 KEY INSIGHT (DDIA):
     • Partition A can elect a new leader, accept writes, etc.
     • Partition B cannot do anything (no quorum)
     • When the partition heals, Partition B catches up from A
     • This prevents split-brain and data corruption ✅
    """)


def demo_5_quorum_read_write():
    """
    Demo 5: Using quorums for read/write operations.

    DDIA concept: "Quorums can be used for both reads and writes."
    """
    print_header("DEMO 5: Quorum-Based Read/Write")
    print("""
    In a leaderless system (like Dynamo, Cassandra), quorums are used
    for both reads and writes to ensure consistency.

    DDIA concept: "If you write to a quorum and read from a quorum,
    you're guaranteed to see the latest write."
    """)

    print_section("Write Quorum")
    print("""
    Write operation:
      1. Client sends write to all N nodes
      2. Client waits for W (write quorum) nodes to acknowledge
      3. Write is considered successful once W nodes confirm

    With N=5, W=3:
      • Client writes to all 5 nodes
      • Waits for 3 nodes to confirm
      • Even if 2 nodes fail, write is durable ✅
    """)

    print_section("Read Quorum")
    print("""
    Read operation:
      1. Client sends read request to all N nodes
      2. Client waits for R (read quorum) nodes to respond
      3. Client returns the value with the highest version

    With N=5, R=3:
      • Client reads from all 5 nodes
      • Waits for 3 nodes to respond
      • Takes the value with highest version/timestamp
      • Guaranteed to see latest write if W + R > N ✅
    """)

    print_section("Quorum Overlap Guarantee")
    print("""
    Why does W + R > N guarantee consistency?

    Example: N=5, W=3, R=3
      W + R = 6 > 5 ✅

    Proof:
      • Write quorum: 3 nodes
      • Read quorum: 3 nodes
      • Total nodes: 5
      • Overlap: 3 + 3 - 5 = 1 node minimum

    The read quorum MUST overlap with the write quorum by at least 1 node.
    That node has the latest value, so the read will see it. ✅
    """)


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 80)
    print("  EXERCISE 1: QUORUM BASICS — MAJORITY CONSENSUS")
    print("  DDIA Chapter 8: 'The Truth is Defined by the Majority'")
    print("=" * 80)
    print("""
  This exercise teaches the fundamental concept of quorums:
  In a distributed system, decisions must be made by a MAJORITY of nodes.

  Why? Because at most one majority can exist at a time.
  This prevents split-brain and ensures consistency.
    """)

    demo_1_basic_quorum_voting()
    demo_2_quorum_sizes()
    demo_3_two_quorums_impossible()
    demo_4_network_partition()
    demo_5_quorum_read_write()

    print("\n" + "=" * 80)
    print("  EXERCISE 1 COMPLETE ✅")
    print("=" * 80)
    print("""
  Key Takeaways:

  1. 🗳️  QUORUM = Majority of nodes (> N/2)
  2. 🔒 At most ONE quorum can exist at a time
  3. 🛡️  Quorums prevent split-brain disasters
  4. 📊 Quorum size = (N // 2) + 1
  5. 🌐 In network partitions, only majority partition can decide

  Next: Run 02_leader_election.py to see quorums in action for leader election
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
