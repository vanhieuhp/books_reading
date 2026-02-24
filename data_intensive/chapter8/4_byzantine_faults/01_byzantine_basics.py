"""
Chapter 8: Byzantine Faults

This module demonstrates Byzantine fault tolerance concepts.

Byzantine Fault: A node that behaves arbitrarily - it may:
- Send contradictory messages to different peers
- Lie about its state
- Refuse to respond
- Send corrupted data
- Collude with other faulty nodes

Key Concepts:
- Most databases DON'T need Byzantine fault tolerance (all nodes trusted)
- Byzantine tolerance is needed for: blockchains, aerospace, adversarial systems
- BFT algorithms are dramatically more complex and expensive than crash-fault tolerant ones
- With f faulty nodes, you need at least 3f+1 total nodes to tolerate Byzantine faults
"""

from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict


class NodeBehavior(Enum):
    """Types of node behavior in Byzantine scenarios."""
    HONEST = "honest"
    CRASH = "crash"
    BYZANTINE = "byzantine"


@dataclass
class Message:
    """A message sent by a node."""
    sender_id: int
    value: str
    timestamp: int
    signature: Optional[str] = None  # In real systems, cryptographic signature

    def __repr__(self) -> str:
        return f"Message(from={self.sender_id}, value={self.value}, ts={self.timestamp})"


@dataclass
class ByzantineNode:
    """A node that may behave Byzantine."""
    node_id: int
    behavior: NodeBehavior
    current_value: Optional[str] = None
    message_log: List[Message] = field(default_factory=list)

    def send_message(self, value: str, timestamp: int) -> Message:
        """Send a message (honest nodes send truthfully)."""
        if self.behavior == NodeBehavior.HONEST:
            msg = Message(self.node_id, value, timestamp)
        elif self.behavior == NodeBehavior.CRASH:
            # Crashed nodes don't send anything
            return None
        elif self.behavior == NodeBehavior.BYZANTINE:
            # Byzantine nodes can send anything (we'll simulate different strategies)
            msg = Message(self.node_id, value, timestamp)
        else:
            msg = Message(self.node_id, value, timestamp)

        self.message_log.append(msg)
        return msg

    def __repr__(self) -> str:
        return f"Node({self.node_id}, {self.behavior.value})"


class ByzantineConsensusSimulation:
    """
    Simulates consensus with Byzantine nodes.

    The problem: Nodes need to agree on a value, but some nodes may lie.
    """

    def __init__(self, total_nodes: int, byzantine_nodes: int):
        self.total_nodes = total_nodes
        self.byzantine_count = byzantine_nodes
        self.honest_count = total_nodes - byzantine_nodes

        # Create nodes
        self.nodes: List[ByzantineNode] = []
        for i in range(total_nodes):
            if i < byzantine_nodes:
                behavior = NodeBehavior.BYZANTINE
            else:
                behavior = NodeBehavior.HONEST
            self.nodes.append(ByzantineNode(i, behavior))

    def can_tolerate_byzantine(self) -> bool:
        """
        Check if the system can tolerate the Byzantine nodes.

        Rule: Need at least 3f+1 nodes to tolerate f Byzantine nodes.
        """
        f = self.byzantine_count
        required_nodes = 3 * f + 1
        return self.total_nodes >= required_nodes

    def simulate_byzantine_general_problem(self, commander_value: str):
        """
        Simulate the Byzantine Generals Problem.

        One commander sends a value to all lieutenants.
        Some lieutenants may be Byzantine and send contradictory messages.
        """
        print(f"\n### Byzantine Generals Problem ###")
        print(f"Total nodes: {self.total_nodes}")
        print(f"Byzantine nodes: {self.byzantine_count}")
        print(f"Honest nodes: {self.honest_count}")
        print(f"Can tolerate Byzantine: {self.can_tolerate_byzantine()}")

        if not self.can_tolerate_byzantine():
            print(f"[WARN] UNSAFE: Need at least {3 * self.byzantine_count + 1} nodes, have {self.total_nodes}")
            return

        print(f"\nCommander (Node 0) sends: '{commander_value}'")

        # Commander sends message to all lieutenants
        messages_received = defaultdict(list)

        for node in self.nodes:
            if node.node_id == 0:
                # Commander
                msg = node.send_message(commander_value, timestamp=1)
                if msg:
                    print(f"  {node} sends: {msg}")
            else:
                # Lieutenants receive from commander
                if self.nodes[0].behavior == NodeBehavior.HONEST:
                    msg = Message(0, commander_value, 1)
                elif self.nodes[0].behavior == NodeBehavior.BYZANTINE:
                    # Byzantine commander sends different values to different nodes
                    if node.node_id % 2 == 0:
                        msg = Message(0, "ATTACK", 1)
                    else:
                        msg = Message(0, "RETREAT", 1)
                else:
                    msg = None

                if msg:
                    messages_received[node.node_id].append(msg)

        # Lieutenants relay messages to each other
        print("\nLieutenants relay messages to each other...")
        for node in self.nodes[1:]:  # Skip commander
            for other_node in self.nodes[1:]:
                if node.node_id != other_node.node_id:
                    if node.behavior == NodeBehavior.HONEST:
                        # Honest node relays truthfully
                        for msg in messages_received[node.node_id]:
                            relay_msg = Message(node.node_id, msg.value, 2)
                            messages_received[other_node.node_id].append(relay_msg)
                    elif node.behavior == NodeBehavior.BYZANTINE:
                        # Byzantine node sends contradictory messages
                        relay_msg = Message(node.node_id, "ATTACK", 2)
                        messages_received[other_node.node_id].append(relay_msg)

        # Each node decides based on majority
        print("\nEach node decides based on majority vote:")
        for node in self.nodes[1:]:
            votes = defaultdict(int)
            for msg in messages_received[node.node_id]:
                votes[msg.value] += 1

            if votes:
                decision = max(votes, key=votes.get)
                print(f"  {node}: votes={dict(votes)}, decision='{decision}'")
            else:
                print(f"  {node}: no messages received")


class CrashFaultVsByzantineFault:
    """
    Compares crash faults vs Byzantine faults.

    Crash Fault: Node stops responding (honest failure)
    Byzantine Fault: Node sends arbitrary/malicious messages (dishonest failure)
    """

    @staticmethod
    def compare_tolerance():
        """Compare how many faults each type can tolerate."""
        print("\n### Crash Fault vs Byzantine Fault Tolerance ###\n")

        print("Crash Fault Tolerance (CFT):")
        print("  - Nodes either work correctly or crash")
        print("  - Need f+1 nodes to tolerate f failures")
        print("  - Example: 3 nodes can tolerate 1 crash")
        print("  - Used in: Most databases (Raft, Paxos)")

        print("\nByzantine Fault Tolerance (BFT):")
        print("  - Nodes can lie, send contradictory messages")
        print("  - Need 3f+1 nodes to tolerate f Byzantine nodes")
        print("  - Example: 4 nodes can tolerate 1 Byzantine node")
        print("  - Used in: Blockchains, aerospace, adversarial systems")

        print("\nComparison for different fault counts:")
        print("  Faults | CFT Nodes | BFT Nodes | BFT Overhead")
        print("  -------|-----------|-----------|-------------")
        for f in range(1, 6):
            cft_nodes = f + 1
            bft_nodes = 3 * f + 1
            overhead = bft_nodes / cft_nodes
            print(f"    {f}    |     {cft_nodes}     |     {bft_nodes}     |    {overhead:.1f}x")

    @staticmethod
    def why_databases_dont_need_bft():
        """Explain why most databases don't need Byzantine fault tolerance."""
        print("\n### Why Most Databases Don't Need BFT ###\n")

        print("Assumptions in typical datacenters:")
        print("  [OK] All nodes run by same organization")
        print("  [OK] All nodes in same physical location (or trusted network)")
        print("  [OK] No adversarial participants")
        print("  [OK] Hardware is trusted (no cosmic ray bit flips)")
        print("  [OK] Nodes fail by crashing, not by lying")

        print("\nWhy BFT is expensive:")
        print("  • Requires cryptographic signatures on every message")
        print("  • Requires multiple rounds of communication")
        print("  • Requires 3f+1 nodes instead of f+1")
        print("  • Dramatically slower than crash-fault tolerant algorithms")

        print("\nWhere BFT is necessary:")
        print("  • Blockchains (untrusted participants)")
        print("  • Aerospace systems (cosmic rays can flip bits)")
        print("  • Systems with adversarial participants")
        print("  • Distributed systems across untrusted organizations")


class ByzantineAttackScenarios:
    """Demonstrates different Byzantine attack strategies."""

    @staticmethod
    def sybil_attack():
        """
        Sybil Attack: One attacker creates many fake identities.
        """
        print("\n### Sybil Attack ###")
        print("Attacker creates 10 fake nodes to influence consensus")
        print("  Real nodes: 5")
        print("  Fake nodes: 10")
        print("  Total: 15 nodes")
        print("\nAttacker controls 10/15 = 67% of nodes")
        print("Attacker can force any decision (needs only 51% majority)")
        print("\nDefense: Require proof-of-work or proof-of-stake")
        print("         (make creating fake identities expensive)")

    @staticmethod
    def eclipse_attack():
        """
        Eclipse Attack: Attacker isolates a node from honest peers.
        """
        print("\n### Eclipse Attack ###")
        print("Attacker controls all network connections to a node")
        print("  Honest node: Node A")
        print("  Attacker: Controls all peers Node A can reach")
        print("\nNode A receives only messages from attacker")
        print("Node A's view of consensus is completely controlled by attacker")
        print("\nDefense: Maintain connections to multiple peers")
        print("         Verify peer identities cryptographically")

    @staticmethod
    def double_spending():
        """
        Double Spending: Attacker sends same money to two recipients.
        """
        print("\n### Double Spending (Blockchain Example) ###")
        print("Attacker has 1 Bitcoin")
        print("  Transaction 1: Send 1 BTC to Alice")
        print("  Transaction 2: Send 1 BTC to Bob")
        print("\nWithout Byzantine tolerance:")
        print("  Attacker can convince Alice that Tx1 is confirmed")
        print("  Attacker can convince Bob that Tx2 is confirmed")
        print("  Both think they received the Bitcoin!")
        print("\nWith Byzantine tolerance (Proof-of-Work):")
        print("  Attacker needs 51% of mining power to rewrite history")
        print("  Both Alice and Bob see the same confirmed transaction")


def main():
    """Demonstrate Byzantine fault concepts."""

    print("=" * 60)
    print("BYZANTINE FAULTS")
    print("=" * 60)

    # Example 1: Byzantine Generals Problem
    print("\n### Example 1: Byzantine Generals Problem ###")
    sim = ByzantineConsensusSimulation(total_nodes=4, byzantine_nodes=1)
    sim.simulate_byzantine_general_problem("ATTACK")

    # Example 2: Insufficient nodes
    print("\n### Example 2: Insufficient Nodes (UNSAFE) ###")
    sim_unsafe = ByzantineConsensusSimulation(total_nodes=3, byzantine_nodes=1)
    sim_unsafe.simulate_byzantine_general_problem("ATTACK")

    # Example 3: Crash Fault vs Byzantine Fault
    CrashFaultVsByzantineFault.compare_tolerance()
    CrashFaultVsByzantineFault.why_databases_dont_need_bft()

    # Example 4: Byzantine attack scenarios
    print("\n" + "=" * 60)
    print("BYZANTINE ATTACK SCENARIOS")
    print("=" * 60)
    ByzantineAttackScenarios.sybil_attack()
    ByzantineAttackScenarios.eclipse_attack()
    ByzantineAttackScenarios.double_spending()


if __name__ == "__main__":
    main()
