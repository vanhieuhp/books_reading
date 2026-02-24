"""
Exercise 3: Byzantine Faults

DDIA Reference: Chapter 8, "Byzantine Faults" (pp. 302-305)

So far, we've assumed nodes are HONEST but potentially FAULTY.
They might crash, be slow, or lose messages, but they don't intentionally lie.

A BYZANTINE FAULT is when a node sends incorrect or malicious messages.
A Byzantine node might:
  • Send contradictory messages to different peers
  • Claim to have data it doesn't have
  • Pretend to be a different node
  • Send garbage data

DDIA insight:
  "Byzantine fault tolerance (BFT) means the system operates correctly
   even if some nodes are lying, compromised, or sending contradictory
   messages to different peers."

Key question: When do you need Byzantine tolerance?
  • Most databases: NO (all nodes in same datacenter, trusted)
  • Blockchains: YES (participants may be adversarial)
  • Aerospace: YES (cosmic rays can flip bits)
  • Distributed systems with untrusted participants: YES

Cost: Byzantine tolerance is EXPENSIVE. PBFT requires O(n²) messages
and can tolerate only f faults with 3f+1 nodes.

Run: python 03_byzantine_faults.py
"""

import sys
from typing import List, Dict, Any, Optional
from enum import Enum

# Fix Windows terminal encoding for Unicode output
sys.stdout.reconfigure(encoding='utf-8')


# =============================================================================
# CORE COMPONENTS: Node, ByzantineNode, Cluster
# =============================================================================

class NodeType(Enum):
    """Type of node."""
    HONEST = "HONEST"
    BYZANTINE = "BYZANTINE"


class Node:
    """An honest node in the distributed system."""

    def __init__(self, node_id: int, name: str = None):
        self.node_id = node_id
        self.name = name or f"Node-{node_id}"
        self.node_type = NodeType.HONEST
        self.value = None  # The value this node holds
        self.received_messages: Dict[int, Any] = {}  # Messages from other nodes

    def send_message(self, value: Any) -> Dict[str, Any]:
        """Send a message with the node's value."""
        return {
            "from": self.node_id,
            "value": value,
            "type": "HONEST"
        }

    def receive_message(self, message: Dict[str, Any]):
        """Receive a message from another node."""
        sender_id = message["from"]
        value = message["value"]
        self.received_messages[sender_id] = value

    def decide_value(self) -> Any:
        """
        Decide on a value based on received messages.

        DDIA insight: "In a Byzantine system, a node must use a voting
        mechanism to decide on a value, ignoring messages from Byzantine nodes."
        """
        if not self.received_messages:
            return self.value

        # Count votes for each value
        vote_counts = {}
        for sender_id, value in self.received_messages.items():
            vote_counts[value] = vote_counts.get(value, 0) + 1

        # Return the value with the most votes
        if vote_counts:
            return max(vote_counts, key=vote_counts.get)
        return self.value

    def __repr__(self):
        return f"{self.name}({self.node_type.value})"


class ByzantineNode(Node):
    """A Byzantine node that sends incorrect messages."""

    def __init__(self, node_id: int, name: str = None, attack_type: str = "random"):
        super().__init__(node_id, name)
        self.node_type = NodeType.BYZANTINE
        self.attack_type = attack_type  # "random", "always_lie", "split_vote"

    def send_message(self, value: Any) -> Dict[str, Any]:
        """
        Send a message, but lie about the value.

        DDIA insight: "A Byzantine node can send different messages
        to different peers, or send garbage data."
        """
        if self.attack_type == "random":
            # Send random value
            return {
                "from": self.node_id,
                "value": "GARBAGE",
                "type": "BYZANTINE"
            }
        elif self.attack_type == "always_lie":
            # Send opposite of the truth
            return {
                "from": self.node_id,
                "value": not value if isinstance(value, bool) else "LIE",
                "type": "BYZANTINE"
            }
        elif self.attack_type == "split_vote":
            # Send different values to different nodes (handled by caller)
            return {
                "from": self.node_id,
                "value": "SPLIT",
                "type": "BYZANTINE"
            }
        else:
            return super().send_message(value)

    def send_message_to(self, recipient_id: int, value: Any) -> Dict[str, Any]:
        """
        Send a different message to each recipient (split-brain attack).

        DDIA insight: "A Byzantine node can send contradictory messages
        to different peers."
        """
        if self.attack_type == "split_vote":
            # Send different values to different nodes
            if recipient_id % 2 == 0:
                return {"from": self.node_id, "value": True, "type": "BYZANTINE"}
            else:
                return {"from": self.node_id, "value": False, "type": "BYZANTINE"}
        return self.send_message(value)


class Cluster:
    """A cluster of nodes (some may be Byzantine)."""

    def __init__(self, honest_count: int, byzantine_count: int = 0):
        self.nodes: List[Node] = []
        self.honest_count = honest_count
        self.byzantine_count = byzantine_count
        self.total_nodes = honest_count + byzantine_count

        # Create honest nodes
        for i in range(honest_count):
            self.nodes.append(Node(i, f"Node-{i+1}"))

        # Create Byzantine nodes
        for i in range(byzantine_count):
            node_id = honest_count + i
            self.nodes.append(ByzantineNode(node_id, f"Node-{node_id+1}", "random"))

    def get_byzantine_nodes(self) -> List[ByzantineNode]:
        """Get all Byzantine nodes."""
        return [n for n in self.nodes if isinstance(n, ByzantineNode)]

    def get_honest_nodes(self) -> List[Node]:
        """Get all honest nodes."""
        return [n for n in self.nodes if not isinstance(n, ByzantineNode)]


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

def demo_1_honest_system():
    """
    Demo 1: System with only honest nodes.

    DDIA concept: "In a system with only honest nodes, consensus is easy."
    """
    print_header("DEMO 1: Honest System (No Byzantine Nodes)")
    print("""
    Scenario: 5 honest nodes, all trying to agree on a value.
    """)

    cluster = Cluster(honest_count=5, byzantine_count=0)

    print(f"  Cluster: {', '.join(n.name for n in cluster.nodes)}")
    print(f"  Byzantine nodes: 0")

    print_section("Broadcast phase")
    print(f"  All nodes broadcast their value: TRUE")

    # All nodes send TRUE
    for node in cluster.nodes:
        node.value = True

    # Collect messages
    for node in cluster.nodes:
        for other in cluster.nodes:
            if node.node_id != other.node_id:
                msg = other.send_message(other.value)
                node.receive_message(msg)

    print_section("Decision phase")
    for node in cluster.nodes:
        decided_value = node.decide_value()
        print(f"  {node.name}: Decides {decided_value} ✅")

    print("""
  💡 KEY INSIGHT (DDIA):
     All nodes agree on TRUE.
     No Byzantine nodes to cause confusion. ✅
    """)


def demo_2_one_byzantine_node():
    """
    Demo 2: System with one Byzantine node.

    DDIA concept: "One Byzantine node can disrupt consensus."
    """
    print_header("DEMO 2: One Byzantine Node (5 nodes total)")
    print("""
    Scenario: 4 honest nodes + 1 Byzantine node.
    Honest nodes want to agree on TRUE.
    Byzantine node sends garbage.
    """)

    cluster = Cluster(honest_count=4, byzantine_count=1)

    print(f"  Cluster: {', '.join(n.name for n in cluster.nodes)}")
    print(f"  Honest nodes: 4")
    print(f"  Byzantine nodes: 1")

    print_section("Broadcast phase")
    print(f"  Honest nodes broadcast: TRUE")
    print(f"  Byzantine node broadcasts: GARBAGE")

    # Set values
    for node in cluster.get_honest_nodes():
        node.value = True

    for node in cluster.get_byzantine_nodes():
        node.value = "GARBAGE"

    # Collect messages
    for node in cluster.nodes:
        for other in cluster.nodes:
            if node.node_id != other.node_id:
                msg = other.send_message(other.value)
                node.receive_message(msg)

    print_section("Decision phase")
    for node in cluster.nodes:
        decided_value = node.decide_value()
        status = "✅" if decided_value == True else "❌"
        print(f"  {node.name}: Decides {decided_value} {status}")

    print("""
  💡 KEY INSIGHT (DDIA):
     Honest nodes still decide TRUE (majority vote).
     Byzantine node's garbage is outvoted. ✅

     But this only works if Byzantine nodes are a minority!
    """)


def demo_3_byzantine_tolerance_requirement():
    """
    Demo 3: How many Byzantine nodes can a system tolerate?

    DDIA concept: "To tolerate f Byzantine nodes, you need 3f+1 total nodes."
    """
    print_header("DEMO 3: Byzantine Tolerance Requirement")
    print("""
    DDIA insight: "To tolerate f Byzantine nodes, you need 3f+1 total nodes."

    Why 3f+1?
      • f Byzantine nodes (liars)
      • f nodes that might be slow/offline
      • f nodes that might be partitioned
      • 1 node to break ties

    Total: 3f + 1 nodes
    """)

    print_section("Tolerance Analysis")
    print(f"\n  {'Total Nodes':<15} {'Byzantine Tolerance':<20} {'Majority'}")
    print(f"  {'─'*50}")

    for f in range(1, 5):
        total = 3 * f + 1
        tolerance = f
        majority = (total // 2) + 1
        print(f"  {total:<15} {tolerance} Byzantine nodes    {majority} nodes")

    print("""
  Examples:
    • 4 nodes: tolerate 1 Byzantine (3*1+1=4)
    • 7 nodes: tolerate 2 Byzantine (3*2+1=7)
    • 10 nodes: tolerate 3 Byzantine (3*3+1=10)

  💡 KEY INSIGHT (DDIA):
     Byzantine tolerance is EXPENSIVE!
     You need 4x more nodes than the number of faults you want to tolerate.

     Compare to crash faults: only need 2f+1 nodes to tolerate f failures.
    """)


def demo_4_split_brain_attack():
    """
    Demo 4: Byzantine node performs split-brain attack.

    DDIA concept: "A Byzantine node can send different messages to
    different peers, causing them to disagree."
    """
    print_header("DEMO 4: Split-Brain Attack by Byzantine Node")
    print("""
    Scenario: 3 honest nodes + 1 Byzantine node.
    Byzantine node sends different values to different peers.
    """)

    cluster = Cluster(honest_count=3, byzantine_count=1)

    print(f"  Cluster: {', '.join(n.name for n in cluster.nodes)}")

    print_section("Broadcast phase")
    print(f"  Honest nodes broadcast: TRUE")
    print(f"  Byzantine node sends:")
    print(f"    → To Node-1: TRUE")
    print(f"    → To Node-2: FALSE")
    print(f"    → To Node-3: FALSE")

    # Set values
    for node in cluster.get_honest_nodes():
        node.value = True

    byzantine = cluster.get_byzantine_nodes()[0]
    byzantine.attack_type = "split_vote"
    byzantine.value = True

    # Collect messages (Byzantine node sends different values)
    for node in cluster.nodes:
        for other in cluster.nodes:
            if node.node_id != other.node_id:
                if isinstance(other, ByzantineNode):
                    msg = other.send_message_to(node.node_id, other.value)
                else:
                    msg = other.send_message(other.value)
                node.receive_message(msg)

    print_section("Decision phase")
    for node in cluster.nodes:
        decided_value = node.decide_value()
        print(f"  {node.name}: Decides {decided_value}")

    print("""
  💡 KEY INSIGHT (DDIA):
     With only 4 nodes and 1 Byzantine, we can't guarantee consensus!
     The Byzantine node can cause nodes to disagree.

     This is why you need 3f+1 nodes to tolerate f Byzantine nodes.
    """)


def demo_5_when_do_you_need_bft():
    """
    Demo 5: When do you actually need Byzantine Fault Tolerance?

    DDIA concept: "Most databases don't need BFT. It's only needed
    when participants may be adversarial."
    """
    print_header("DEMO 5: When Do You Need Byzantine Fault Tolerance?")
    print("""
    DDIA insight: "Byzantine fault tolerance is rarely needed for
    typical data systems. It's expensive and complex."
    """)

    print_section("Systems that DON'T need BFT")
    print("""
    ✅ Traditional databases (PostgreSQL, MySQL, MongoDB)
       • All nodes in same datacenter
       • Run by same organization
       • Nodes are trusted
       • Only need to handle crash faults

    ✅ Cloud databases (AWS RDS, Google Cloud SQL)
       • Managed by cloud provider
       • Nodes are trusted
       • Only need to handle crash faults

    ✅ Distributed databases in enterprise (Cassandra, HBase)
       • Nodes in same organization
       • Nodes are trusted
       • Only need to handle crash faults
    """)

    print_section("Systems that DO need BFT")
    print("""
    ❌ Blockchains (Bitcoin, Ethereum)
       • Participants may be adversarial
       • No central authority
       • Must tolerate Byzantine nodes

    ❌ Aerospace systems
       • Cosmic rays can flip bits (Byzantine fault)
       • Must tolerate arbitrary failures

    ❌ Distributed systems with untrusted participants
       • P2P networks
       • Systems where participants may be compromised
    """)

    print("""
  💡 KEY INSIGHT (DDIA):
     DDIA recommends: "For most data systems, Byzantine fault tolerance
     is not worth the cost. Focus on crash fault tolerance instead."

     Cost comparison:
       • Crash fault tolerance: 2f+1 nodes for f failures
       • Byzantine fault tolerance: 3f+1 nodes for f failures
       • Message complexity: O(n) vs O(n²)
       • Latency: Low vs High
    """)


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 80)
    print("  EXERCISE 3: BYZANTINE FAULTS")
    print("  DDIA Chapter 8: 'Byzantine Faults'")
    print("=" * 80)
    print("""
  This exercise explores Byzantine faults — nodes that send incorrect
  or malicious messages.

  Key insight: Byzantine fault tolerance is expensive and rarely needed
  for typical databases. It's mainly used in blockchains and adversarial
  environments.
    """)

    demo_1_honest_system()
    demo_2_one_byzantine_node()
    demo_3_byzantine_tolerance_requirement()
    demo_4_split_brain_attack()
    demo_5_when_do_you_need_bft()

    print("\n" + "=" * 80)
    print("  EXERCISE 3 COMPLETE ✅")
    print("=" * 80)
    print("""
  Key Takeaways:

  1. 🤥 Byzantine node = node that sends incorrect/malicious messages
  2. 🛡️  Byzantine tolerance requires 3f+1 nodes for f faults
  3. 💰 Byzantine tolerance is EXPENSIVE (O(n²) messages)
  4. 🔗 Needed for blockchains, rarely for databases
  5. 📊 Most databases only need crash fault tolerance (2f+1 nodes)

  Next: Run 04_byzantine_tolerance.py to see PBFT algorithm
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
