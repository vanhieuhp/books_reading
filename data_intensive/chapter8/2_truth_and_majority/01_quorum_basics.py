"""
Chapter 8: The Truth is Defined by the Majority - Quorum Basics

This module demonstrates the fundamental principle that in distributed systems,
a node cannot trust its own judgment. Truth is determined by consensus of a majority.

Key Concepts:
- A single node's view is unreliable (network partition, clock skew, etc.)
- A quorum (majority) provides consensus
- Quorum size = floor(n/2) + 1 for n nodes
- Quorum-based decisions are safe even with network partitions
"""

from typing import List, Set, Dict, Optional
from dataclasses import dataclass
from enum import Enum


class NodeState(Enum):
    """Possible states of a node in the system."""
    LEADER = "leader"
    FOLLOWER = "follower"
    CANDIDATE = "candidate"
    UNKNOWN = "unknown"


@dataclass
class Node:
    """Represents a node in a distributed system."""
    node_id: int
    state: NodeState = NodeState.UNKNOWN
    term: int = 0  # Logical clock for leader election
    voted_for: Optional[int] = None  # Which node this node voted for in current term

    def __repr__(self) -> str:
        return f"Node({self.node_id}, state={self.state.value}, term={self.term})"


class QuorumVoter:
    """
    Demonstrates quorum-based voting for leader election.

    The key insight: A node cannot declare itself the leader unilaterally.
    It must get votes from a MAJORITY of nodes.
    """

    def __init__(self, nodes: List[Node]):
        self.nodes = {node.node_id: node for node in nodes}
        self.total_nodes = len(nodes)
        self.quorum_size = (self.total_nodes // 2) + 1

    def get_quorum_size(self) -> int:
        """Calculate the minimum quorum size needed for consensus."""
        return self.quorum_size

    def can_tolerate_failures(self) -> int:
        """How many node failures can the system tolerate?"""
        return self.total_nodes - self.quorum_size

    def request_vote(self, candidate_id: int, term: int) -> Dict[int, bool]:
        """
        Candidate requests votes from all nodes.

        Returns: dict mapping node_id -> voted_for_candidate (bool)
        """
        votes = {}

        for node_id, node in self.nodes.items():
            # A node votes for a candidate if:
            # 1. The candidate's term is >= node's current term
            # 2. The node hasn't voted yet in this term (or voted for this candidate)

            if term > node.term:
                # Candidate has a higher term, so it's more up-to-date
                node.term = term
                node.voted_for = candidate_id
                votes[node_id] = True
            elif term == node.term and (node.voted_for is None or node.voted_for == candidate_id):
                # Same term, and node hasn't voted or already voted for this candidate
                node.voted_for = candidate_id
                votes[node_id] = True
            else:
                # Node won't vote (either lower term or already voted for someone else)
                votes[node_id] = False

        return votes

    def can_become_leader(self, votes: Dict[int, bool]) -> bool:
        """Check if a candidate has enough votes to become leader."""
        vote_count = sum(1 for voted in votes.values() if voted)
        return vote_count >= self.quorum_size

    def simulate_election(self, candidate_id: int, term: int) -> bool:
        """
        Simulate a leader election.

        Returns: True if candidate becomes leader, False otherwise.
        """
        print(f"\n--- Leader Election ---")
        print(f"Candidate {candidate_id} requesting votes for term {term}")
        print(f"Quorum size needed: {self.quorum_size} out of {self.total_nodes} nodes")

        votes = self.request_vote(candidate_id, term)

        print(f"Votes received: {votes}")
        vote_count = sum(1 for v in votes.values() if v)
        print(f"Vote count: {vote_count}/{self.total_nodes}")

        if self.can_become_leader(votes):
            print(f"[OK] Candidate {candidate_id} becomes LEADER")
            self.nodes[candidate_id].state = NodeState.LEADER
            return True
        else:
            print(f"[FAIL] Candidate {candidate_id} fails to become leader (needs {self.quorum_size}, got {vote_count})")
            return False


class NetworkPartitionSimulation:
    """
    Demonstrates why quorums prevent split-brain scenarios.

    Split-brain: Two nodes both think they're the leader.
    Quorums prevent this because only one partition can have a majority.
    """

    def __init__(self, total_nodes: int):
        self.total_nodes = total_nodes
        self.quorum_size = (total_nodes // 2) + 1

    def simulate_partition(self, partition_a_size: int) -> tuple[bool, bool]:
        """
        Simulate a network partition.

        partition_a_size: number of nodes in partition A
        Returns: (can_partition_a_elect_leader, can_partition_b_elect_leader)
        """
        partition_b_size = self.total_nodes - partition_a_size

        print(f"\n--- Network Partition Simulation ---")
        print(f"Total nodes: {self.total_nodes}")
        print(f"Partition A: {partition_a_size} nodes")
        print(f"Partition B: {partition_b_size} nodes")
        print(f"Quorum size needed: {self.quorum_size}")

        can_a_elect = partition_a_size >= self.quorum_size
        can_b_elect = partition_b_size >= self.quorum_size

        print(f"\nPartition A can elect leader: {can_a_elect}")
        print(f"Partition B can elect leader: {can_b_elect}")

        if can_a_elect and can_b_elect:
            print("[WARN] DANGER: Both partitions can elect leaders (split-brain possible!)")
        elif can_a_elect or can_b_elect:
            print("[OK] SAFE: Only one partition can elect a leader")
        else:
            print("[OK] SAFE: Neither partition can elect a leader (system unavailable but consistent)")

        return can_a_elect, can_b_elect


def main():
    """Demonstrate quorum-based consensus."""

    print("=" * 60)
    print("QUORUM BASICS: The Truth is Defined by the Majority")
    print("=" * 60)

    # Example 1: Basic quorum calculation
    print("\n### Example 1: Quorum Sizes ###")
    for n in [3, 5, 7, 9]:
        quorum = (n // 2) + 1
        tolerance = n - quorum
        print(f"  {n} nodes: quorum={quorum}, can tolerate {tolerance} failures")

    # Example 2: Leader election with quorum
    print("\n### Example 2: Leader Election ###")
    nodes = [Node(i) for i in range(5)]
    voter = QuorumVoter(nodes)

    # Candidate 0 requests votes for term 1
    voter.simulate_election(candidate_id=0, term=1)

    # Candidate 1 requests votes for term 2 (higher term)
    voter.simulate_election(candidate_id=1, term=2)

    # Example 3: Network partition scenarios
    print("\n### Example 3: Network Partitions ###")
    sim = NetworkPartitionSimulation(total_nodes=5)

    # Scenario 1: 3-2 split (one partition has quorum)
    sim.simulate_partition(partition_a_size=3)

    # Scenario 2: 4-1 split (one partition has quorum)
    sim.simulate_partition(partition_a_size=4)

    # Scenario 3: 2-3 split (one partition has quorum)
    sim.simulate_partition(partition_a_size=2)

    # Example 4: Why single-node decisions are dangerous
    print("\n### Example 4: Single-Node Decisions Are Dangerous ###")
    print("Scenario: Node 0 thinks it's the leader (no quorum check)")
    print("  - Network partition occurs")
    print("  - Node 0 is isolated (partition of 1)")
    print("  - Node 0 still thinks it's the leader")
    print("  - Nodes 1-4 elect a new leader (partition of 4)")
    print("  - Result: TWO leaders, data corruption!")
    print("\nWith quorum: Node 0 cannot become leader (needs 3 votes, gets 1)")
    print("  - Only the partition with 4 nodes can elect a leader")
    print("  - No split-brain, system remains consistent")


if __name__ == "__main__":
    main()
