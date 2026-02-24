"""
Exercise 3: Consistent Hashing with Virtual Nodes (vnodes)

DDIA Reference: Chapter 6, "Rebalancing Partitions" (pp. 209-211)

This exercise demonstrates PARTITIONING PROPORTIONAL TO NODES:
  - Make the number of partitions proportional to the number of nodes
  - Use consistent hashing to assign keys to partitions
  - Use virtual nodes (vnodes) to handle node joins/leaves
  - Cassandra uses 256 vnodes per node by default

Key concepts:
  - Consistent hashing: hash(key) maps to a point on a ring
  - Virtual nodes: each physical node owns multiple virtual partitions
  - When a node joins: it takes ownership of some vnodes
  - When a node leaves: its vnodes are redistributed
  - Partition size stays stable as cluster grows

Run: python 03_consistent_hashing.py
"""

import sys
import time
import random
import hashlib
from typing import Dict, List, Tuple, Set, Any, Optional

sys.stdout.reconfigure(encoding='utf-8')


# =============================================================================
# CORE COMPONENTS: ConsistentHashRing, VirtualNode, Node
# =============================================================================

class ConsistentHashRing:
    """
    A consistent hash ring for distributing keys to nodes.

    Keys are hashed to positions on a ring (0 to 2^32-1).
    Each position is owned by the nearest node clockwise.
    """

    RING_SIZE = 2**32

    @staticmethod
    def hash_key(key: str) -> int:
        """Hash a key to a position on the ring."""
        h = hashlib.md5(str(key).encode()).digest()
        return int.from_bytes(h[:4], byteorder='big') % ConsistentHashRing.RING_SIZE

    def __init__(self, vnodes_per_node: int = 256):
        self.vnodes_per_node = vnodes_per_node
        self.ring: Dict[int, 'VirtualNode'] = {}  # position -> vnode
        self.nodes: Dict[int, 'Node'] = {}  # node_id -> Node
        self.node_counter = 0

    def add_node(self) -> int:
        """Add a new node to the ring."""
        node_id = self.node_counter
        self.node_counter += 1
        node = Node(node_id, self.vnodes_per_node)
        self.nodes[node_id] = node

        # Create vnodes for this node
        for i in range(self.vnodes_per_node):
            # Hash the node_id + vnode index to get a position
            vnode_key = f"node_{node_id}_vnode_{i}"
            position = self.hash_key(vnode_key)

            # Handle collisions (rare but possible)
            while position in self.ring:
                position = (position + 1) % self.RING_SIZE

            vnode = VirtualNode(node_id, i, position)
            self.ring[position] = vnode
            node.vnodes.append(vnode)

        return node_id

    def remove_node(self, node_id: int):
        """Remove a node from the ring."""
        if node_id not in self.nodes:
            raise ValueError(f"Node {node_id} not found")

        node = self.nodes[node_id]
        for vnode in node.vnodes:
            del self.ring[vnode.position]

        del self.nodes[node_id]

    def get_node_for_key(self, key: str) -> int:
        """Find which node owns a key."""
        if not self.ring:
            raise ValueError("Ring is empty")

        key_hash = self.hash_key(key)

        # Find the first vnode position >= key_hash (clockwise)
        sorted_positions = sorted(self.ring.keys())
        for position in sorted_positions:
            if position >= key_hash:
                return self.ring[position].node_id

        # Wrap around to the first position
        return self.ring[sorted_positions[0]].node_id

    def get_load_distribution(self) -> Dict[int, Tuple[int, int]]:
        """Return load distribution: node_id -> (vnode_count, key_count)."""
        distribution = {}
        for node_id, node in self.nodes.items():
            distribution[node_id] = (len(node.vnodes), node.key_count)
        return distribution

    def get_imbalance_ratio(self) -> float:
        """Calculate imbalance: max_keys / min_keys."""
        key_counts = [node.key_count for node in self.nodes.values()]
        if not key_counts or min(key_counts) == 0:
            return 1.0
        return max(key_counts) / min(key_counts)


class VirtualNode:
    """A virtual node (vnode) — a partition on the consistent hash ring."""

    def __init__(self, node_id: int, vnode_index: int, position: int):
        self.node_id = node_id
        self.vnode_index = vnode_index
        self.position = position

    def __repr__(self):
        return f"VNode(node={self.node_id}, index={self.vnode_index}, pos={self.position})"


class Node:
    """A physical node that owns multiple vnodes."""

    def __init__(self, node_id: int, vnodes_per_node: int):
        self.node_id = node_id
        self.vnodes: List[VirtualNode] = []
        self.data: Dict[str, Dict[str, Any]] = {}
        self.key_count = 0

    def write(self, key: str, value: Dict[str, Any]):
        """Write a key-value pair."""
        self.data[key] = value.copy()
        self.key_count += 1

    def read(self, key: str) -> Optional[Dict[str, Any]]:
        """Read a key-value pair."""
        return self.data.get(key)

    def __repr__(self):
        return f"Node({self.node_id}, vnodes={len(self.vnodes)}, keys={self.key_count})"


class ConsistentHashCluster:
    """A cluster using consistent hashing with vnodes."""

    def __init__(self, vnodes_per_node: int = 256):
        self.ring = ConsistentHashRing(vnodes_per_node)
        self.data: Dict[str, Dict[str, Any]] = {}

    def add_node(self) -> int:
        """Add a new node to the cluster."""
        return self.ring.add_node()

    def remove_node(self, node_id: int):
        """Remove a node from the cluster."""
        self.ring.remove_node(node_id)

    def write(self, key: str, value: Dict[str, Any]):
        """Write to the cluster."""
        node_id = self.ring.get_node_for_key(key)
        node = self.ring.nodes[node_id]
        node.write(key, value)
        self.data[key] = value.copy()

    def read(self, key: str) -> Optional[Dict[str, Any]]:
        """Read from the cluster."""
        node_id = self.ring.get_node_for_key(key)
        node = self.ring.nodes[node_id]
        return node.read(key)

    def get_load_distribution(self) -> Dict[int, Tuple[int, int]]:
        """Return load distribution."""
        return self.ring.get_load_distribution()

    def get_imbalance_ratio(self) -> float:
        """Get imbalance ratio."""
        return self.ring.get_imbalance_ratio()


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


def demo_1_consistent_hashing_basics():
    """
    Demo 1: Show how consistent hashing works.

    DDIA concept: "Consistent hashing avoids the hash(key) % N problem.
    When a node is added or removed, only a fraction of keys need to move."
    """
    print_header("DEMO 1: Consistent Hashing Basics")
    print("""
    We'll create a cluster with consistent hashing and show how
    keys are distributed across nodes.
    """)

    cluster = ConsistentHashCluster(vnodes_per_node=4)

    # Add nodes
    print_section("Adding Nodes")
    for i in range(3):
        node_id = cluster.add_node()
        print(f"  ✅ Node {node_id} joined (4 vnodes)")

    # Insert data
    print_section("Inserting Data")
    num_keys = 1000
    for i in range(num_keys):
        key = f"key_{i}"
        value = {"id": i, "data": f"value_{i}"}
        cluster.write(key, value)

    print(f"  ✅ Inserted {num_keys} keys")

    # Show distribution
    print_section("📊 Load Distribution")
    distribution = cluster.get_load_distribution()
    for node_id in sorted(distribution.keys()):
        vnode_count, key_count = distribution[node_id]
        print(f"  Node {node_id}: {vnode_count} vnodes, {key_count:4d} keys")

    imbalance = cluster.get_imbalance_ratio()
    print(f"\n  Imbalance ratio: {imbalance:.2f}x")

    print("""
  💡 KEY INSIGHT (DDIA):
     With consistent hashing, keys are distributed fairly evenly.
     Each node gets roughly 1/N of the keys.
    """)


def demo_2_adding_nodes():
    """
    Demo 2: Show what happens when a node joins.

    DDIA concept: "When a new node joins, it takes ownership of
    some vnodes. Only the keys in those vnodes need to move."
    """
    print_header("DEMO 2: Adding Nodes with Consistent Hashing")
    print("""
    Starting with 3 nodes, we add 2 more nodes.
    Watch how keys are redistributed.
    """)

    cluster = ConsistentHashCluster(vnodes_per_node=4)

    # Initial cluster
    print_section("Initial Cluster (3 nodes)")
    for i in range(3):
        cluster.add_node()

    # Insert data
    for i in range(1000):
        key = f"key_{i}"
        value = {"id": i, "data": f"value_{i}"}
        cluster.write(key, value)

    distribution = cluster.get_load_distribution()
    print(f"  Total keys: {sum(k for _, k in distribution.values())}")
    for node_id in sorted(distribution.keys()):
        vnode_count, key_count = distribution[node_id]
        print(f"  Node {node_id}: {key_count:4d} keys")

    # Add new nodes
    print_section("Adding 2 New Nodes")
    for i in range(2):
        node_id = cluster.add_node()
        print(f"  ✅ Node {node_id} joined")

    # Show new distribution
    print_section("📊 New Load Distribution")
    distribution = cluster.get_load_distribution()
    for node_id in sorted(distribution.keys()):
        vnode_count, key_count = distribution[node_id]
        print(f"  Node {node_id}: {key_count:4d} keys")

    imbalance = cluster.get_imbalance_ratio()
    print(f"\n  Imbalance ratio: {imbalance:.2f}x")

    print("""
  💡 KEY INSIGHT (DDIA):
     With consistent hashing:
       • Only ~20% of keys moved (those in the new node's vnodes)
       • Other 80% stayed in place
       • Compare to hash(key) % N: ~80% would move! ❌

     This is why consistent hashing is used in Cassandra, Riak, etc.
    """)


def demo_3_vnodes_per_node():
    """
    Demo 3: Show the impact of vnodes per node.

    DDIA concept: "Cassandra uses 256 vnodes per node by default.
    More vnodes = finer-grained load balancing."
    """
    print_header("DEMO 3: Impact of Virtual Nodes Per Node")
    print("""
    We'll compare different vnode counts and see how they affect
    load distribution when nodes join/leave.
    """)

    scenarios = [
        ("Few vnodes (1)", 1),
        ("Medium vnodes (16)", 16),
        ("Many vnodes (256)", 256),
    ]

    print_section("Scenario: 10 nodes, 10,000 keys")

    for scenario_name, vnodes_per_node in scenarios:
        cluster = ConsistentHashCluster(vnodes_per_node=vnodes_per_node)

        # Add nodes
        for i in range(10):
            cluster.add_node()

        # Insert data
        for i in range(10000):
            key = f"key_{i}"
            value = {"id": i}
            cluster.write(key, value)

        imbalance = cluster.get_imbalance_ratio()
        print(f"  {scenario_name:<25} Imbalance: {imbalance:.3f}x")

    print("""
  💡 KEY INSIGHT (DDIA):
     More vnodes per node = better load balancing.
     But more vnodes = more metadata to track.

     Cassandra default: 256 vnodes per node
       • Good balance between distribution and overhead
       • Allows fine-grained rebalancing
    """)


def demo_4_removing_nodes():
    """
    Demo 4: Show what happens when a node leaves.

    DDIA concept: "When a node is removed, its vnodes are
    redistributed to other nodes."
    """
    print_header("DEMO 4: Removing Nodes")
    print("""
    Starting with 5 nodes, we remove 2 nodes.
    Watch how their keys are redistributed.
    """)

    cluster = ConsistentHashCluster(vnodes_per_node=8)

    # Initial cluster
    print_section("Initial Cluster (5 nodes)")
    for i in range(5):
        cluster.add_node()

    # Insert data
    for i in range(2000):
        key = f"key_{i}"
        value = {"id": i}
        cluster.write(key, value)

    distribution = cluster.get_load_distribution()
    print(f"  Total keys: {sum(k for _, k in distribution.values())}")
    for node_id in sorted(distribution.keys()):
        vnode_count, key_count = distribution[node_id]
        print(f"  Node {node_id}: {vnode_count} vnodes, {key_count:4d} keys")

    # Remove nodes
    print_section("Removing Nodes 3 and 4")
    cluster.remove_node(3)
    cluster.remove_node(4)
    print(f"  ✅ Nodes removed")

    # Show new distribution
    print_section("📊 New Load Distribution")
    distribution = cluster.get_load_distribution()
    for node_id in sorted(distribution.keys()):
        vnode_count, key_count = distribution[node_id]
        print(f"  Node {node_id}: {vnode_count} vnodes, {key_count:4d} keys")

    imbalance = cluster.get_imbalance_ratio()
    print(f"\n  Imbalance ratio: {imbalance:.2f}x")

    print("""
  💡 KEY INSIGHT (DDIA):
     When nodes are removed, their vnodes are redistributed.
     The remaining nodes take on the extra load.
     With many vnodes, the load is distributed fairly evenly.
    """)


def demo_5_partition_size_stability():
    """
    Demo 5: Show how partition size stays stable as cluster grows.

    DDIA concept: "With per-node partitioning, partition size stays
    relatively stable as the cluster grows."
    """
    print_header("DEMO 5: Partition Size Stability")
    print("""
    We'll grow the cluster from 1 to 10 nodes and track partition sizes.
    """)

    print_section("Growing Cluster with Fixed Dataset (10,000 keys)")

    for num_nodes in [1, 2, 5, 10]:
        cluster = ConsistentHashCluster(vnodes_per_node=256)

        # Add nodes
        for i in range(num_nodes):
            cluster.add_node()

        # Insert data
        for i in range(10000):
            key = f"key_{i}"
            value = {"id": i}
            cluster.write(key, value)

        distribution = cluster.get_load_distribution()
        total_keys = sum(k for _, k in distribution.values())
        avg_keys_per_node = total_keys / num_nodes
        imbalance = cluster.get_imbalance_ratio()

        print(f"  {num_nodes:2d} nodes: {avg_keys_per_node:7.0f} keys/node, imbalance: {imbalance:.3f}x")

    print("""
  💡 KEY INSIGHT (DDIA):
     With per-node partitioning (vnodes):
       • Partition size stays roughly constant
       • As you add nodes, each gets ~same amount of data
       • This is different from fixed partitioning
         (where partition size grows with dataset)
    """)


def demo_6_comparison_with_other_strategies():
    """
    Demo 6: Compare consistent hashing with other strategies.

    DDIA concept: "Different rebalancing strategies have different
    trade-offs."
    """
    print_header("DEMO 6: Rebalancing Strategies Comparison")
    print("""
    Comparison of fixed partitions, dynamic partitioning, and
    consistent hashing with vnodes.
    """)

    print_section("Strategy Comparison")
    print(f"""
  {'Aspect':<30} {'Fixed':<20} {'Dynamic':<20} {'Consistent Hash'}
  {'─'*80}
  {'Partition count':<30} {'Fixed upfront':<20} {'Grows with data':<20} {'Grows with nodes'}
  {'Partition boundaries':<30} {'Fixed forever':<20} {'Change (split)':<20} {'Change (vnodes)'}
  {'Rebalancing':<30} {'Manual reassign':<20} {'Auto split/merge':<20} {'Auto redistribute'}
  {'Upfront planning':<30} {'Guess size':<20} {'None':<20} {'None'}
  {'Complexity':<30} {'Low':<20} {'Medium':<20} {'Medium'}
  {'Used by':<30} {'Riak, ES':<20} {'HBase, MongoDB':<20} {'Cassandra, Riak'}
    """)

    print("""
  💡 DDIA GUIDANCE:
     Choose based on your needs:

     FIXED PARTITIONS:
       ✅ Simple to understand and implement
       ✅ Predictable partition sizes
       ❌ Must guess partition count upfront
       ❌ Rebalancing is manual

     DYNAMIC PARTITIONING:
       ✅ Automatic adaptation to data growth
       ✅ No upfront planning needed
       ❌ More complex to implement
       ❌ Partition boundaries change

     CONSISTENT HASHING (vnodes):
       ✅ Automatic adaptation to node count
       ✅ Minimal data movement on node join/leave
       ✅ Decentralized (no coordinator needed)
       ❌ More complex to understand
       ❌ Partition size grows with dataset
    """)


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 80)
    print("  EXERCISE 3: CONSISTENT HASHING WITH VIRTUAL NODES")
    print("  DDIA Chapter 6: 'Rebalancing Partitions'")
    print("=" * 80)
    print("""
  This exercise demonstrates CONSISTENT HASHING with virtual nodes.
  This is the strategy used by Cassandra, Riak, and other systems
  that need to handle dynamic cluster membership.
    """)

    demo_1_consistent_hashing_basics()
    demo_2_adding_nodes()
    demo_3_vnodes_per_node()
    demo_4_removing_nodes()
    demo_5_partition_size_stability()
    demo_6_comparison_with_other_strategies()

    print("\n" + "=" * 80)
    print("  EXERCISE 3 COMPLETE ✅")
    print("=" * 80)
    print("""
  Key Takeaways:

  1. 🔄 Consistent hashing avoids the hash(key) % N problem
  2. 📍 Virtual nodes (vnodes) enable fine-grained load balancing
  3. ➕ Adding a node: only ~1/N of keys need to move
  4. ➖ Removing a node: its vnodes are redistributed
  5. 📊 Partition size grows with dataset (not node count)
  6. 🎯 Used by Cassandra (256 vnodes/node), Riak, Voldemort

  Next: Run 04_rebalancing_challenges.py to see real-world issues
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
