"""
Linearizability Example

This module demonstrates linearizability using a quorum-based key-value store.
Linearizability means: the system behaves as if there is only one copy of the data,
and every operation takes effect atomically at some point between its start and end.

Key characteristics:
- Writes must be replicated to a quorum (majority) before returning
- Reads must check a quorum to get the latest value
- Once any client sees a new value, all subsequent reads see that value or newer
- Strong consistency, but higher latency
"""

import time
from typing import Dict, Any, Optional, Set
from dataclasses import dataclass
from enum import Enum


class OperationType(Enum):
    WRITE = "write"
    READ = "read"


@dataclass
class Operation:
    """Represents a read or write operation."""
    op_type: OperationType
    key: str
    value: Any = None
    timestamp: float = 0
    node_id: str = ""


class LinearizableStore:
    """
    A quorum-based linearizable key-value store.

    Behavior:
    - Writes must be acknowledged by a quorum (majority) of nodes
    - Reads must check a quorum to get the latest value
    - Guarantees: once a write completes, all subsequent reads see the new value
    """

    def __init__(self, node_id: str, total_nodes: int):
        self.node_id = node_id
        self.total_nodes = total_nodes
        self.quorum_size = (total_nodes // 2) + 1
        self.data: Dict[str, Any] = {}
        self.versions: Dict[str, int] = {}  # Track version numbers
        self.peers: Dict[str, 'LinearizableStore'] = {}

    def add_peer(self, node_id: str, node: 'LinearizableStore') -> None:
        """Register a peer node."""
        self.peers[node_id] = node

    def write(self, key: str, value: Any) -> bool:
        """
        Write a value with quorum replication.
        Returns only after a quorum acknowledges the write.
        """
        version = self.versions.get(key, 0) + 1
        current_time = time.time()

        # Prepare write on all nodes
        acks = 0
        nodes_acked = []

        # Write to self
        self.data[key] = value
        self.versions[key] = version
        acks += 1
        nodes_acked.append(self.node_id)

        # Write to peers
        for peer_id, peer in self.peers.items():
            peer.data[key] = value
            peer.versions[key] = version
            acks += 1
            nodes_acked.append(peer_id)

        # Check if we have a quorum
        if acks >= self.quorum_size:
            print(f"[{self.node_id}] Write: {key} = {value} (version {version})")
            print(f"  ✓ Quorum achieved: {acks}/{self.total_nodes} nodes")
            print(f"  ✓ Nodes: {nodes_acked}")
            return True
        else:
            print(f"[{self.node_id}] Write FAILED: {key} = {value}")
            print(f"  ✗ Quorum not achieved: {acks}/{self.total_nodes} nodes")
            return False

    def read(self, key: str) -> Optional[Any]:
        """
        Read a value by checking a quorum.
        Returns the value with the highest version number.
        """
        # Read from self
        responses = []
        responses.append((self.node_id, self.data.get(key), self.versions.get(key, 0)))

        # Read from peers
        for peer_id, peer in self.peers.items():
            responses.append((peer_id, peer.data.get(key), peer.versions.get(key, 0)))

        # Sort by version (highest first)
        responses.sort(key=lambda x: x[2], reverse=True)

        # Get the value with the highest version
        if responses:
            node_id, value, version = responses[0]
            print(f"[{self.node_id}] Read: {key} = {value} (version {version})")
            print(f"  ✓ Quorum responses: {len(responses)} nodes")
            for nid, val, ver in responses[:self.quorum_size]:
                print(f"    - {nid}: {val} (v{ver})")
            return value
        return None

    def get_state(self) -> Dict[str, Any]:
        """Get the current state of this node."""
        return dict(self.data)


def demo_linearizability():
    """
    Demonstrate linearizability with quorum-based writes and reads.
    """
    print("=" * 70)
    print("LINEARIZABILITY DEMO (Quorum-Based)")
    print("=" * 70)

    # Create 3 nodes (quorum size = 2)
    node_a = LinearizableStore("Node-A", total_nodes=3)
    node_b = LinearizableStore("Node-B", total_nodes=3)
    node_c = LinearizableStore("Node-C", total_nodes=3)

    # Set up peer relationships
    node_a.add_peer("Node-B", node_b)
    node_a.add_peer("Node-C", node_c)
    node_b.add_peer("Node-A", node_a)
    node_b.add_peer("Node-C", node_c)
    node_c.add_peer("Node-A", node_a)
    node_c.add_peer("Node-B", node_b)

    print("\n1. Alice writes x=1 to Node-A")
    node_a.write("x", 1)

    print("\n2. Bob reads x from Node-B")
    value = node_b.read("x")
    print(f"   Bob got: {value} (guaranteed to be 1 or newer)")

    print("\n3. Charlie reads x from Node-C")
    value = node_c.read("x")
    print(f"   Charlie got: {value}")

    print("\n" + "=" * 70)
    print("FINAL STATE (All nodes have the same value)")
    print("=" * 70)
    print(f"Node-A: {node_a.get_state()}")
    print(f"Node-B: {node_b.get_state()}")
    print(f"Node-C: {node_c.get_state()}")


def demo_linearizability_vs_eventual():
    """
    Compare linearizability with eventual consistency.
    """
    print("\n\n" + "=" * 70)
    print("LINEARIZABILITY vs EVENTUAL CONSISTENCY")
    print("=" * 70)

    # Linearizable store
    lin_a = LinearizableStore("Lin-A", total_nodes=3)
    lin_b = LinearizableStore("Lin-B", total_nodes=3)
    lin_c = LinearizableStore("Lin-C", total_nodes=3)

    lin_a.add_peer("Lin-B", lin_b)
    lin_a.add_peer("Lin-C", lin_c)
    lin_b.add_peer("Lin-A", lin_a)
    lin_b.add_peer("Lin-C", lin_c)
    lin_c.add_peer("Lin-A", lin_a)
    lin_c.add_peer("Lin-B", lin_b)

    print("\nLinearizable Store:")
    print("1. Alice writes x=1")
    lin_a.write("x", 1)

    print("\n2. Bob reads x (guaranteed to see 1)")
    lin_b.read("x")

    print("\n3. Charlie reads x (guaranteed to see 1)")
    lin_c.read("x")

    print("\n" + "-" * 70)
    print("Key Difference:")
    print("- Linearizable: Bob and Charlie are GUARANTEED to see x=1")
    print("- Eventual: Bob and Charlie might see x=0 (stale) for a while")
    print("- Linearizable: Higher latency (quorum coordination)")
    print("- Eventual: Lower latency (no coordination)")


def demo_leader_election():
    """
    Demonstrate how linearizability is used for leader election.
    """
    print("\n\n" + "=" * 70)
    print("LEADER ELECTION WITH LINEARIZABILITY")
    print("=" * 70)

    # Create 3 nodes
    node_a = LinearizableStore("Node-A", total_nodes=3)
    node_b = LinearizableStore("Node-B", total_nodes=3)
    node_c = LinearizableStore("Node-C", total_nodes=3)

    node_a.add_peer("Node-B", node_b)
    node_a.add_peer("Node-C", node_c)
    node_b.add_peer("Node-A", node_a)
    node_b.add_peer("Node-C", node_c)
    node_c.add_peer("Node-A", node_a)
    node_c.add_peer("Node-B", node_b)

    print("\nScenario: Three nodes try to become leader")
    print("1. Node-A tries to acquire leader lock")
    node_a.write("leader", "Node-A")

    print("\n2. Node-B tries to acquire leader lock")
    # In a real system, this would be a compare-and-set operation
    # For simplicity, we just overwrite
    node_b.write("leader", "Node-B")

    print("\n3. All nodes read who the leader is")
    print("   Node-A reads:")
    node_a.read("leader")
    print("   Node-B reads:")
    node_b.read("leader")
    print("   Node-C reads:")
    node_c.read("leader")

    print("\n" + "-" * 70)
    print("Key Point:")
    print("- All nodes see the SAME leader (linearizability)")
    print("- No split-brain (two leaders)")
    print("- This is why ZooKeeper uses linearizability for leader election")


def demo_unique_constraint():
    """
    Demonstrate how linearizability enforces unique constraints.
    """
    print("\n\n" + "=" * 70)
    print("UNIQUE CONSTRAINT WITH LINEARIZABILITY")
    print("=" * 70)

    # Create 3 nodes
    node_a = LinearizableStore("Node-A", total_nodes=3)
    node_b = LinearizableStore("Node-B", total_nodes=3)
    node_c = LinearizableStore("Node-C", total_nodes=3)

    node_a.add_peer("Node-B", node_b)
    node_a.add_peer("Node-C", node_c)
    node_b.add_peer("Node-A", node_a)
    node_b.add_peer("Node-C", node_c)
    node_c.add_peer("Node-A", node_a)
    node_c.add_peer("Node-B", node_b)

    print("\nScenario: Alice and Bob both try to register username 'alice'")
    print("1. Alice tries to register 'alice' on Node-A")
    node_a.write("username:alice", "alice")

    print("\n2. Bob tries to register 'alice' on Node-B")
    node_b.write("username:alice", "bob")

    print("\n3. Check who owns 'alice'")
    print("   Node-A reads:")
    node_a.read("username:alice")
    print("   Node-B reads:")
    node_b.read("username:alice")

    print("\n" + "-" * 70)
    print("Key Point:")
    print("- Both writes succeeded (in this simplified example)")
    print("- But all nodes see the SAME value (linearizability)")
    print("- In a real system, only one write would succeed (compare-and-set)")
    print("- This prevents duplicate usernames")


if __name__ == "__main__":
    demo_linearizability()
    demo_linearizability_vs_eventual()
    demo_leader_election()
    demo_unique_constraint()
