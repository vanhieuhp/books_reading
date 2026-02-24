"""
Eventual Consistency Example

This module demonstrates eventual consistency using a simple distributed key-value store.
Eventual consistency means: if you stop writing, replicas will eventually converge to the same value.
But there's no guarantee about WHEN.

Key characteristics:
- Writes return immediately (don't wait for replication)
- Reads might return stale data
- Replicas eventually sync (via background replication)
- High availability, low latency, but weak consistency
"""

import time
from typing import Dict, Any, Optional
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class WriteOperation:
    """Represents a write operation with a timestamp."""
    key: str
    value: Any
    timestamp: float
    node_id: str


class EventuallyConsistentStore:
    """
    A simple eventually consistent key-value store.

    Behavior:
    - Writes go to the primary node and return immediately
    - Writes are replicated to other nodes in the background
    - Reads return the local value (might be stale)
    - Replicas eventually converge
    """

    def __init__(self, node_id: str, replica_nodes: list = None):
        self.node_id = node_id
        self.data: Dict[str, Any] = {}
        self.timestamps: Dict[str, float] = {}
        self.replica_nodes = replica_nodes or []
        self.pending_replications: list = []

    def write(self, key: str, value: Any) -> bool:
        """
        Write a value to this node.
        Returns immediately without waiting for replication.
        """
        current_time = time.time()
        self.data[key] = value
        self.timestamps[key] = current_time

        # Queue replication to other nodes (happens in background)
        operation = WriteOperation(key, value, current_time, self.node_id)
        self.pending_replications.append(operation)

        print(f"[{self.node_id}] Write: {key} = {value} (timestamp: {current_time:.3f})")
        return True

    def read(self, key: str) -> Optional[Any]:
        """
        Read a value from this node.
        Might return stale data if replication hasn't happened yet.
        """
        value = self.data.get(key)
        timestamp = self.timestamps.get(key, "never")
        print(f"[{self.node_id}] Read: {key} = {value} (timestamp: {timestamp})")
        return value

    def replicate_to_peer(self, peer_node: 'EventuallyConsistentStore') -> None:
        """
        Replicate pending writes to a peer node.
        This happens asynchronously in a real system.
        """
        while self.pending_replications:
            operation = self.pending_replications.pop(0)

            # Only replicate if peer doesn't have a newer version
            peer_timestamp = peer_node.timestamps.get(operation.key, 0)
            if operation.timestamp > peer_timestamp:
                peer_node.data[operation.key] = operation.value
                peer_node.timestamps[operation.key] = operation.timestamp
                print(f"  → Replicated {operation.key} to [{peer_node.node_id}]")

    def get_state(self) -> Dict[str, Any]:
        """Get the current state of this node."""
        return dict(self.data)


def demo_eventual_consistency():
    """
    Demonstrate eventual consistency with stale reads.
    """
    print("=" * 60)
    print("EVENTUAL CONSISTENCY DEMO")
    print("=" * 60)

    # Create three nodes
    node_a = EventuallyConsistentStore("Node-A")
    node_b = EventuallyConsistentStore("Node-B")
    node_c = EventuallyConsistentStore("Node-C")

    # Set up replication
    node_a.replica_nodes = [node_b, node_c]
    node_b.replica_nodes = [node_a, node_c]
    node_c.replica_nodes = [node_a, node_b]

    print("\n1. Alice writes x=1 to Node-A")
    node_a.write("x", 1)

    print("\n2. Bob reads x from Node-B (STALE READ!)")
    value_b = node_b.read("x")
    print(f"   Bob got: {value_b} (expected 1, but got None because replication hasn't happened)")

    print("\n3. Replication happens (background sync)")
    node_a.replicate_to_peer(node_b)
    node_a.replicate_to_peer(node_c)

    print("\n4. Bob reads x from Node-B again (NOW IT'S CONSISTENT)")
    value_b = node_b.read("x")
    print(f"   Bob got: {value_b} (now consistent!)")

    print("\n5. Charlie reads x from Node-C")
    value_c = node_c.read("x")
    print(f"   Charlie got: {value_c}")

    print("\n" + "=" * 60)
    print("FINAL STATE (All nodes eventually converged)")
    print("=" * 60)
    print(f"Node-A: {node_a.get_state()}")
    print(f"Node-B: {node_b.get_state()}")
    print(f"Node-C: {node_c.get_state()}")


def demo_stale_read_problem():
    """
    Demonstrate the problem with stale reads in eventual consistency.
    """
    print("\n\n" + "=" * 60)
    print("STALE READ PROBLEM")
    print("=" * 60)

    node_a = EventuallyConsistentStore("Node-A")
    node_b = EventuallyConsistentStore("Node-B")
    node_a.replica_nodes = [node_b]
    node_b.replica_nodes = [node_a]

    print("\nScenario: Alice updates her account balance")
    print("1. Alice writes balance=1000 to Node-A")
    node_a.write("balance", 1000)

    print("\n2. Alice checks her balance on Node-B (STALE!)")
    balance = node_b.read("balance")
    print(f"   Alice sees: {balance} (None, because replication hasn't happened)")

    print("\n3. Replication happens")
    node_a.replicate_to_peer(node_b)

    print("\n4. Alice checks again on Node-B")
    balance = node_b.read("balance")
    print(f"   Alice sees: {balance} (now correct!)")

    print("\nProblem: Alice might think her write failed!")
    print("Solution: Use read-your-writes consistency or read from the primary node")


def demo_concurrent_writes():
    """
    Demonstrate how eventual consistency handles concurrent writes.
    """
    print("\n\n" + "=" * 60)
    print("CONCURRENT WRITES IN EVENTUAL CONSISTENCY")
    print("=" * 60)

    node_a = EventuallyConsistentStore("Node-A")
    node_b = EventuallyConsistentStore("Node-B")
    node_a.replica_nodes = [node_b]
    node_b.replica_nodes = [node_a]

    print("\nScenario: Alice and Bob write to different nodes concurrently")
    print("1. Alice writes x=1 to Node-A")
    node_a.write("x", 1)

    print("\n2. Bob writes x=2 to Node-B (at the same time)")
    node_b.write("x", 2)

    print("\n3. Replication happens")
    node_a.replicate_to_peer(node_b)
    node_b.replicate_to_peer(node_a)

    print("\n4. Final state (Last-Write-Wins)")
    print(f"   Node-A: x = {node_a.read('x')}")
    print(f"   Node-B: x = {node_b.read('x')}")

    print("\nNote: The node with the later timestamp wins (Last-Write-Wins)")
    print("This can cause data loss if not handled carefully!")


if __name__ == "__main__":
    demo_eventual_consistency()
    demo_stale_read_problem()
    demo_concurrent_writes()
