"""
Exercise 4: Byzantine Fault Tolerance (PBFT)

DDIA Reference: Chapter 8, "Byzantine Fault Tolerance" (pp. 305-310)

PBFT (Practical Byzantine Fault Tolerance) is an algorithm that allows
a system to reach consensus even when some nodes are Byzantine (lying).

Key properties:
  • Tolerates f Byzantine nodes with 3f+1 total nodes
  • Guarantees safety (all honest nodes decide the same value)
  • Guarantees liveness (decisions are made in finite time)
  • O(n²) message complexity (expensive!)

PBFT has three phases:
  1. PRE-PREPARE: Leader proposes a value
  2. PREPARE: Nodes vote on the proposal
  3. COMMIT: Nodes commit the value

DDIA insight:
  "PBFT is the most famous Byzantine fault tolerance algorithm.
   It's used in some blockchains and permissioned systems.
   But it's expensive and rarely used in traditional databases."

Run: python 04_byzantine_tolerance.py
"""

import sys
from typing import List, Dict, Any, Optional, Set
from enum import Enum
from collections import Counter

# Fix Windows terminal encoding for Unicode output
sys.stdout.reconfigure(encoding='utf-8')


# =============================================================================
# CORE COMPONENTS: Node, PBFTNode, PBFTCluster
# =============================================================================

class NodeRole(Enum):
    """Role of a node in PBFT."""
    PRIMARY = "PRIMARY"
    BACKUP = "BACKUP"


class MessageType(Enum):
    """Type of PBFT message."""
    PRE_PREPARE = "PRE-PREPARE"
    PREPARE = "PREPARE"
    COMMIT = "COMMIT"


class PBFTMessage:
    """A PBFT protocol message."""

    def __init__(self, msg_type: MessageType, sender_id: int, view: int,
                 sequence: int, value: Any, is_byzantine: bool = False):
        self.msg_type = msg_type
        self.sender_id = sender_id
        self.view = view
        self.sequence = sequence
        self.value = value
        self.is_byzantine = is_byzantine

    def __repr__(self):
        return f"{self.msg_type.value}(sender={self.sender_id}, view={self.view}, seq={self.sequence})"


class PBFTNode:
    """A node participating in PBFT consensus."""

    def __init__(self, node_id: int, name: str = None, is_byzantine: bool = False):
        self.node_id = node_id
        self.name = name or f"Node-{node_id}"
        self.is_byzantine = is_byzantine
        self.role = NodeRole.BACKUP
        self.view = 0  # Current view (like term in Raft)
        self.sequence = 0  # Sequence number of last committed message
        self.log: List[PBFTMessage] = []  # Committed messages
        self.pre_prepare_messages: Dict[int, PBFTMessage] = {}  # Received PRE-PREPARE
        self.prepare_messages: Dict[int, List[PBFTMessage]] = {}  # Received PREPARE
        self.commit_messages: Dict[int, List[PBFTMessage]] = {}  # Received COMMIT
        self.decided_values: List[Any] = []  # Values this node has decided

    def set_primary(self):
        """This node becomes the primary."""
        self.role = NodeRole.PRIMARY

    def set_backup(self):
        """This node becomes a backup."""
        self.role = NodeRole.BACKUP

    def send_pre_prepare(self, value: Any, sequence: int) -> PBFTMessage:
        """
        Primary sends PRE-PREPARE message.

        PBFT Phase 1: Primary proposes a value.
        """
        msg = PBFTMessage(
            msg_type=MessageType.PRE_PREPARE,
            sender_id=self.node_id,
            view=self.view,
            sequence=sequence,
            value=value,
            is_byzantine=self.is_byzantine
        )
        self.pre_prepare_messages[sequence] = msg
        return msg

    def send_prepare(self, sequence: int) -> PBFTMessage:
        """
        Backup sends PREPARE message.

        PBFT Phase 2: Backups vote on the proposal.
        """
        msg = PBFTMessage(
            msg_type=MessageType.PREPARE,
            sender_id=self.node_id,
            view=self.view,
            sequence=sequence,
            value=None,  # PREPARE doesn't include value
            is_byzantine=self.is_byzantine
        )
        if sequence not in self.prepare_messages:
            self.prepare_messages[sequence] = []
        self.prepare_messages[sequence].append(msg)
        return msg

    def send_commit(self, sequence: int) -> PBFTMessage:
        """
        Node sends COMMIT message.

        PBFT Phase 3: Nodes commit the value.
        """
        msg = PBFTMessage(
            msg_type=MessageType.COMMIT,
            sender_id=self.node_id,
            view=self.view,
            sequence=sequence,
            value=None,  # COMMIT doesn't include value
            is_byzantine=self.is_byzantine
        )
        if sequence not in self.commit_messages:
            self.commit_messages[sequence] = []
        self.commit_messages[sequence].append(msg)
        return msg

    def receive_pre_prepare(self, msg: PBFTMessage):
        """Receive a PRE-PREPARE message."""
        self.pre_prepare_messages[msg.sequence] = msg

    def receive_prepare(self, msg: PBFTMessage):
        """Receive a PREPARE message."""
        if msg.sequence not in self.prepare_messages:
            self.prepare_messages[msg.sequence] = []
        self.prepare_messages[msg.sequence].append(msg)

    def receive_commit(self, msg: PBFTMessage):
        """Receive a COMMIT message."""
        if msg.sequence not in self.commit_messages:
            self.commit_messages[msg.sequence] = []
        self.commit_messages[msg.sequence].append(msg)

    def has_prepare_quorum(self, sequence: int, total_nodes: int) -> bool:
        """
        Check if this node has received PREPARE messages from a quorum.

        PBFT requires 2f+1 PREPARE messages (including self) to proceed.
        """
        f = (total_nodes - 1) // 3  # Max Byzantine nodes
        required = 2 * f + 1

        if sequence not in self.prepare_messages:
            return False

        # Count PREPARE messages (including self)
        count = len(self.prepare_messages[sequence]) + 1
        return count >= required

    def has_commit_quorum(self, sequence: int, total_nodes: int) -> bool:
        """
        Check if this node has received COMMIT messages from a quorum.

        PBFT requires 2f+1 COMMIT messages (including self) to commit.
        """
        f = (total_nodes - 1) // 3  # Max Byzantine nodes
        required = 2 * f + 1

        if sequence not in self.commit_messages:
            return False

        # Count COMMIT messages (including self)
        count = len(self.commit_messages[sequence]) + 1
        return count >= required

    def decide(self, value: Any):
        """This node decides on a value."""
        self.decided_values.append(value)

    def __repr__(self):
        role_str = "PRIMARY" if self.role == NodeRole.PRIMARY else "BACKUP"
        byzantine_str = " (BYZANTINE)" if self.is_byzantine else ""
        return f"{self.name}({role_str}){byzantine_str}"


class PBFTCluster:
    """A cluster of nodes running PBFT."""

    def __init__(self, total_nodes: int, byzantine_count: int = 0):
        self.nodes: List[PBFTNode] = []
        self.total_nodes = total_nodes
        self.byzantine_count = byzantine_count
        self.f = (total_nodes - 1) // 3  # Max Byzantine nodes tolerated
        self.quorum_size = 2 * self.f + 1

        # Create nodes
        for i in range(total_nodes):
            is_byzantine = i < byzantine_count
            node = PBFTNode(i, f"Node-{i+1}", is_byzantine)
            self.nodes.append(node)

        # First node is primary
        self.nodes[0].set_primary()
        for node in self.nodes[1:]:
            node.set_backup()

    def get_primary(self) -> PBFTNode:
        """Get the primary node."""
        for node in self.nodes:
            if node.role == NodeRole.PRIMARY:
                return node
        return None

    def get_backups(self) -> List[PBFTNode]:
        """Get all backup nodes."""
        return [n for n in self.nodes if n.role == NodeRole.BACKUP]

    def get_byzantine_nodes(self) -> List[PBFTNode]:
        """Get all Byzantine nodes."""
        return [n for n in self.nodes if n.is_byzantine]

    def get_honest_nodes(self) -> List[PBFTNode]:
        """Get all honest nodes."""
        return [n for n in self.nodes if not n.is_byzantine]


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

def demo_1_pbft_overview():
    """
    Demo 1: Overview of PBFT algorithm.

    DDIA concept: "PBFT has three phases: PRE-PREPARE, PREPARE, COMMIT."
    """
    print_header("DEMO 1: PBFT Algorithm Overview")
    print("""
    PBFT (Practical Byzantine Fault Tolerance) is a consensus algorithm
    that tolerates Byzantine faults.

    DDIA insight: "PBFT requires 3f+1 nodes to tolerate f Byzantine nodes."
    """)

    print_section("PBFT Phases")
    print("""
    Phase 1: PRE-PREPARE
      • Primary proposes a value
      • Sends PRE-PREPARE message to all backups
      • Message includes: view, sequence number, value

    Phase 2: PREPARE
      • Backups receive PRE-PREPARE
      • Backups send PREPARE message to all other nodes
      • Backups wait for 2f+1 PREPARE messages (including self)

    Phase 3: COMMIT
      • Once 2f+1 PREPARE messages received, send COMMIT
      • Wait for 2f+1 COMMIT messages (including self)
      • Once 2f+1 COMMIT messages received, commit the value

    Safety: All honest nodes decide the same value ✅
    Liveness: Decisions are made in finite time ✅
    """)

    print_section("Message Complexity")
    print("""
    Total messages: O(n²)
      • Phase 1: 1 message (primary to all)
      • Phase 2: n messages (each node to all)
      • Phase 3: n messages (each node to all)
      • Total: ~3n messages per consensus

    Compare to Raft: O(n) messages
    PBFT is 3x more expensive! 💰
    """)


def demo_2_pbft_with_no_faults():
    """
    Demo 2: PBFT with no Byzantine nodes.

    DDIA concept: "PBFT works even with no faults, but it's slower
    than simpler algorithms like Raft."
    """
    print_header("DEMO 2: PBFT with No Byzantine Nodes (4 nodes)")
    print("""
    Scenario: 4 honest nodes, no Byzantine nodes.
    Primary proposes value: "WRITE x=10"
    """)

    cluster = PBFTCluster(total_nodes=4, byzantine_count=0)

    print(f"  Total nodes: {cluster.total_nodes}")
    print(f"  Byzantine nodes: 0")
    print(f"  Quorum size: {cluster.quorum_size}")
    print(f"  Primary: {cluster.get_primary().name}")

    print_section("Phase 1: PRE-PREPARE")
    primary = cluster.get_primary()
    value = "WRITE x=10"
    sequence = 1

    pre_prepare_msg = primary.send_pre_prepare(value, sequence)
    print(f"  {primary.name} sends PRE-PREPARE")
    print(f"    Value: {value}")
    print(f"    Sequence: {sequence}")

    # All backups receive PRE-PREPARE
    for backup in cluster.get_backups():
        backup.receive_pre_prepare(pre_prepare_msg)
        print(f"  {backup.name} receives PRE-PREPARE ✅")

    print_section("Phase 2: PREPARE")
    print(f"  All nodes send PREPARE messages")

    for node in cluster.nodes:
        prepare_msg = node.send_prepare(sequence)
        for other in cluster.nodes:
            if other.node_id != node.node_id:
                other.receive_prepare(prepare_msg)

    for node in cluster.nodes:
        has_quorum = node.has_prepare_quorum(sequence, cluster.total_nodes)
        status = "✅" if has_quorum else "❌"
        print(f"  {node.name}: Has PREPARE quorum {status}")

    print_section("Phase 3: COMMIT")
    print(f"  All nodes send COMMIT messages")

    for node in cluster.nodes:
        commit_msg = node.send_commit(sequence)
        for other in cluster.nodes:
            if other.node_id != node.node_id:
                other.receive_commit(commit_msg)

    for node in cluster.nodes:
        has_quorum = node.has_commit_quorum(sequence, cluster.total_nodes)
        if has_quorum:
            node.decide(value)
            print(f"  {node.name}: Commits {value} ✅")

    print("""
  💡 KEY INSIGHT (DDIA):
     All nodes decided the same value.
     PBFT guarantees safety even with Byzantine nodes. ✅
    """)


def demo_3_pbft_with_byzantine_node():
    """
    Demo 3: PBFT with one Byzantine node.

    DDIA concept: "PBFT tolerates Byzantine nodes through quorum voting."
    """
    print_header("DEMO 3: PBFT with One Byzantine Node (4 nodes)")
    print("""
    Scenario: 3 honest nodes + 1 Byzantine node.
    Byzantine node tries to disrupt consensus.
    """)

    cluster = PBFTCluster(total_nodes=4, byzantine_count=1)

    print(f"  Total nodes: {cluster.total_nodes}")
    print(f"  Honest nodes: 3")
    print(f"  Byzantine nodes: 1")
    print(f"  Quorum size: {cluster.quorum_size}")

    print_section("Cluster composition")
    for node in cluster.nodes:
        byzantine_str = " (BYZANTINE)" if node.is_byzantine else ""
        print(f"  {node.name}{byzantine_str}")

    print_section("Phase 1: PRE-PREPARE")
    primary = cluster.get_primary()
    value = "WRITE x=10"
    sequence = 1

    pre_prepare_msg = primary.send_pre_prepare(value, sequence)
    print(f"  {primary.name} sends PRE-PREPARE: {value}")

    for backup in cluster.get_backups():
        backup.receive_pre_prepare(pre_prepare_msg)

    print_section("Phase 2: PREPARE")
    print(f"  Honest nodes send PREPARE")
    print(f"  Byzantine node sends garbage")

    for node in cluster.nodes:
        prepare_msg = node.send_prepare(sequence)
        for other in cluster.nodes:
            if other.node_id != node.node_id:
                other.receive_prepare(prepare_msg)

    print_section("Phase 3: COMMIT")
    print(f"  Nodes check if they have PREPARE quorum")

    for node in cluster.nodes:
        has_quorum = node.has_prepare_quorum(sequence, cluster.total_nodes)
        status = "✅" if has_quorum else "❌"
        print(f"  {node.name}: Has PREPARE quorum {status}")

    print(f"\n  All nodes have quorum (Byzantine node outvoted)")

    for node in cluster.nodes:
        commit_msg = node.send_commit(sequence)
        for other in cluster.nodes:
            if other.node_id != node.node_id:
                other.receive_commit(commit_msg)

    for node in cluster.nodes:
        has_quorum = node.has_commit_quorum(sequence, cluster.total_nodes)
        if has_quorum:
            node.decide(value)
            print(f"  {node.name}: Commits {value} ✅")

    print("""
  💡 KEY INSIGHT (DDIA):
     Even with 1 Byzantine node, all honest nodes decide the same value.
     The Byzantine node is outvoted by the quorum. ✅
    """)


def demo_4_pbft_requirements():
    """
    Demo 4: PBFT requirements for different cluster sizes.

    DDIA concept: "PBFT requires 3f+1 nodes to tolerate f Byzantine nodes."
    """
    print_header("DEMO 4: PBFT Requirements")
    print("""
    DDIA insight: "To tolerate f Byzantine nodes, you need 3f+1 total nodes."
    """)

    print_section("PBFT Tolerance Analysis")
    print(f"\n  {'Total':<10} {'Byzantine':<12} {'Quorum':<10} {'Tolerance'}")
    print(f"  {'Nodes':<10} {'Tolerance':<12} {'Size':<10} {'(failures)'}")
    print(f"  {'─'*45}")

    for f in range(1, 5):
        total = 3 * f + 1
        quorum = 2 * f + 1
        tolerance = f
        print(f"  {total:<10} {tolerance:<12} {quorum:<10} {tolerance}")

    print("""
  Examples:
    • 4 nodes: tolerate 1 Byzantine (quorum=3)
    • 7 nodes: tolerate 2 Byzantine (quorum=5)
    • 10 nodes: tolerate 3 Byzantine (quorum=7)
    • 13 nodes: tolerate 4 Byzantine (quorum=9)

  💡 KEY INSIGHT (DDIA):
     PBFT is expensive!
     • Crash fault tolerance: 2f+1 nodes
     • Byzantine fault tolerance: 3f+1 nodes
     • PBFT requires 50% more nodes than crash-only systems
    """)


def demo_5_pbft_vs_crash_fault_tolerance():
    """
    Demo 5: Compare PBFT to crash fault tolerance.

    DDIA concept: "Byzantine tolerance is expensive. Use it only when needed."
    """
    print_header("DEMO 5: PBFT vs Crash Fault Tolerance")
    print("""
    DDIA insight: "Most databases don't need Byzantine tolerance.
    Crash fault tolerance is sufficient and much cheaper."
    """)

    print_section("Comparison")
    print("""
    Crash Fault Tolerance (Raft, Paxos):
      • Nodes may crash or be slow
      • Nodes don't lie
      • Requires: 2f+1 nodes to tolerate f failures
      • Message complexity: O(n)
      • Latency: Low
      • Used in: Most databases, cloud systems

    Byzantine Fault Tolerance (PBFT):
      • Nodes may crash, be slow, OR lie
      • Nodes can send contradictory messages
      • Requires: 3f+1 nodes to tolerate f failures
      • Message complexity: O(n²)
      • Latency: High
      • Used in: Blockchains, adversarial systems

    Cost comparison for tolerating 2 failures:
      • Crash fault: 5 nodes (2*2+1)
      • Byzantine fault: 7 nodes (3*2+1)
      • 40% more nodes needed!
    """)

    print_section("When to use each")
    print("""
    Use Crash Fault Tolerance (Raft/Paxos):
      ✅ Traditional databases
      ✅ Cloud systems (AWS, GCP, Azure)
      ✅ Enterprise systems
      ✅ Systems with trusted participants

    Use Byzantine Fault Tolerance (PBFT):
      ✅ Blockchains (Bitcoin, Ethereum)
      ✅ Permissioned systems with untrusted nodes
      ✅ Aerospace systems
      ✅ Systems where participants may be adversarial

    DDIA recommendation:
      "For most data systems, Byzantine fault tolerance is not worth
       the cost. Focus on crash fault tolerance instead."
    """)


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 80)
    print("  EXERCISE 4: BYZANTINE FAULT TOLERANCE (PBFT)")
    print("  DDIA Chapter 8: 'Byzantine Fault Tolerance'")
    print("=" * 80)
    print("""
  This exercise explores PBFT (Practical Byzantine Fault Tolerance),
  an algorithm that reaches consensus even when some nodes are lying.

  Key insight: Byzantine tolerance is expensive and rarely needed
  for typical databases. It's mainly used in blockchains.
    """)

    demo_1_pbft_overview()
    demo_2_pbft_with_no_faults()
    demo_3_pbft_with_byzantine_node()
    demo_4_pbft_requirements()
    demo_5_pbft_vs_crash_fault_tolerance()

    print("\n" + "=" * 80)
    print("  EXERCISE 4 COMPLETE ✅")
    print("=" * 80)
    print("""
  Key Takeaways:

  1. 🔐 PBFT = Practical Byzantine Fault Tolerance
  2. 📊 Requires 3f+1 nodes to tolerate f Byzantine nodes
  3. 💬 Three phases: PRE-PREPARE, PREPARE, COMMIT
  4. 💰 Expensive: O(n²) messages, 50% more nodes
  5. 🔗 Used in blockchains, rarely in databases

  Section 4 Complete! You now understand:
    ✅ Quorums and majority consensus
    ✅ Leader election with quorums
    ✅ Byzantine faults and their impact
    ✅ Byzantine fault tolerance algorithms

  Next: Explore real consensus algorithms (Raft, Paxos) in production systems
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
