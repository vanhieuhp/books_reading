#!/usr/bin/env python3
"""
Exercise 1: The Consensus Problem

This exercise demonstrates the consensus problem and why it's hard.

Key concepts:
- Uniform Agreement: No two nodes decide differently
- Integrity: No node decides twice
- Validity: If a node decides value v, then v was proposed by some node
- Termination: Every non-crashed node eventually decides

The FLP Impossibility Result:
- In a purely asynchronous system, there is no algorithm that always reaches
  consensus if even one node can crash.
- Practical algorithms use timeouts (partial synchrony) to work around this.
"""

import random
from typing import List, Dict, Optional


class ConsensusNode:
    """A node participating in consensus."""

    def __init__(self, node_id: int, proposed_value: int):
        self.node_id = node_id
        self.proposed_value = proposed_value
        self.decided_value: Optional[int] = None
        self.decided = False

    def __repr__(self):
        return f"Node({self.node_id})"


def simple_majority_consensus(nodes: List[ConsensusNode]) -> bool:
    """
    Simple majority voting consensus.

    Returns True if consensus was reached, False otherwise.
    """
    print("\n" + "=" * 80)
    print("SIMPLE MAJORITY VOTING CONSENSUS")
    print("=" * 80)

    # Count votes
    vote_counts: Dict[int, int] = {}
    for node in nodes:
        value = node.proposed_value
        vote_counts[value] = vote_counts.get(value, 0) + 1

    print(f"\nProposed values:")
    for node in nodes:
        print(f"  {node}: proposes {node.proposed_value}")

    print(f"\nVote counts: {vote_counts}")

    # Check if any value has a majority
    majority_threshold = len(nodes) // 2 + 1
    for value, count in vote_counts.items():
        if count >= majority_threshold:
            print(f"\n✅ CONSENSUS REACHED: Value {value} has {count} votes (majority)")
            for node in nodes:
                node.decided_value = value
                node.decided = True
            return True

    print(f"\n❌ NO CONSENSUS: No value has {majority_threshold} votes")
    return False


def flp_impossibility_demo():
    """
    Demonstrate the FLP impossibility result.

    In an asynchronous system, if even one node can crash, there is no
    algorithm that always reaches consensus.
    """
    print("\n" + "=" * 80)
    print("FLP IMPOSSIBILITY RESULT")
    print("=" * 80)

    print("""
The FLP Impossibility Result (Fischer, Lynch, Paterson, 1985):

In a purely asynchronous system (where you cannot guarantee message delivery
times), there is NO algorithm that always reaches consensus if even one node
can crash.

Why this matters:
- You send a message to Node B
- You don't know if Node B crashed or if the message is just delayed
- You cannot distinguish between the two cases
- Therefore, you cannot safely decide

The trick: Real systems use TIMEOUTS as a heuristic for failure detection.
- Assume a node is dead if it doesn't respond within a timeout
- This is called PARTIAL SYNCHRONY
- Practical algorithms (Paxos, Raft) ensure SAFETY even if timeouts are wrong
- They just lose LIVENESS (progress) temporarily

Example:
  Timeout = 1 second
  Node B is slow (takes 2 seconds to respond)
  You assume Node B crashed
  You decide without Node B
  But Node B is actually alive!
  This can cause SPLIT-BRAIN (two leaders)

Solution: Use QUORUMS and FENCING TOKENS to prevent split-brain
    """)


def quorum_consensus_demo():
    """
    Demonstrate why quorums prevent split-brain.

    Quorum: A majority of nodes.
    Key insight: Any two quorums overlap.
    """)
    print("\n" + "=" * 80)
    print("QUORUM-BASED CONSENSUS")
    print("=" * 80)

    num_nodes = 5
    quorum_size = num_nodes // 2 + 1

    print(f"\nTotal nodes: {num_nodes}")
    print(f"Quorum size: {quorum_size}")

    print(f"\nExample quorums:")
    print(f"  Quorum 1: {{Node 0, Node 1, Node 2}}")
    print(f"  Quorum 2: {{Node 2, Node 3, Node 4}}")
    print(f"  Overlap: {{Node 2}}")

    print(f"""
Why quorums prevent split-brain:

If Quorum 1 decides value v, then Quorum 2 must know about it
(because they overlap at Node 2).

This ensures that:
1. Any two quorums overlap
2. If one quorum decides v, any other quorum must know about it
3. Therefore, all quorums will decide the same value
4. Split-brain is impossible!

Network partition scenario:
  Partition A: {quorum_size} nodes (can form quorum) → decides value v
  Partition B: {num_nodes - quorum_size} nodes (cannot form quorum) → waits

Result: Only Partition A can decide. No split-brain! ✅
    """)


def consensus_with_crashes_demo():
    """
    Demonstrate consensus with node crashes.
    """
    print("\n" + "=" * 80)
    print("CONSENSUS WITH NODE CRASHES")
    print("=" * 80)

    num_nodes = 5
    quorum_size = num_nodes // 2 + 1

    print(f"\nScenario: {num_nodes} nodes, {quorum_size} needed for quorum")

    # Simulate crashes
    alive_nodes = num_nodes - 1  # One node crashes
    print(f"\nOne node crashes. Alive nodes: {alive_nodes}")

    if alive_nodes >= quorum_size:
        print(f"✅ Quorum can still be formed ({alive_nodes} >= {quorum_size})")
        print(f"   Consensus can proceed")
    else:
        print(f"❌ Quorum cannot be formed ({alive_nodes} < {quorum_size})")
        print(f"   Consensus is blocked (waiting for partition to heal)")

    # Simulate more crashes
    alive_nodes = num_nodes - 2
    print(f"\nTwo nodes crash. Alive nodes: {alive_nodes}")

    if alive_nodes >= quorum_size:
        print(f"✅ Quorum can still be formed ({alive_nodes} >= {quorum_size})")
        print(f"   Consensus can proceed")
    else:
        print(f"❌ Quorum cannot be formed ({alive_nodes} < {quorum_size})")
        print(f"   Consensus is blocked (waiting for partition to heal)")


def main():
    print("\n" + "=" * 80)
    print("EXERCISE 1: THE CONSENSUS PROBLEM")
    print("=" * 80)

    # Demo 1: Simple majority voting
    print("\n--- Demo 1: Simple Majority Voting ---")
    nodes = [
        ConsensusNode(0, 0),
        ConsensusNode(1, 0),
        ConsensusNode(2, 0),
        ConsensusNode(3, 1),
        ConsensusNode(4, 1),
    ]
    simple_majority_consensus(nodes)

    # Demo 2: No consensus
    print("\n--- Demo 2: No Consensus (Split Votes) ---")
    nodes = [
        ConsensusNode(0, 0),
        ConsensusNode(1, 1),
        ConsensusNode(2, 2),
        ConsensusNode(3, 0),
        ConsensusNode(4, 1),
    ]
    simple_majority_consensus(nodes)

    # Demo 3: FLP Impossibility
    flp_impossibility_demo()

    # Demo 4: Quorum-based consensus
    quorum_consensus_demo()

    # Demo 5: Consensus with crashes
    consensus_with_crashes_demo()

    print("\n" + "=" * 80)
    print("KEY TAKEAWAYS")
    print("=" * 80)
    print("""
1. Consensus requires all nodes to agree on a value
2. FLP proves consensus is impossible in a purely asynchronous system
3. Practical algorithms use timeouts (partial synchrony)
4. Quorums prevent split-brain (any two quorums overlap)
5. Consensus can tolerate up to (n-1)/2 node crashes
6. Real systems use Paxos or Raft for consensus
    """)


if __name__ == "__main__":
    main()
