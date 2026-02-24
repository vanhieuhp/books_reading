"""
Exercise 1: Fixed Number of Partitions — Rebalancing Strategy

DDIA Reference: Chapter 6, "Rebalancing Partitions" (pp. 203-207)

This exercise demonstrates the FIXED PARTITION COUNT strategy:
  - Create many more partitions than nodes (e.g., 1000 partitions for 10 nodes)
  - Keep partition count constant forever
  - When nodes join/leave, reassign partitions to nodes (not partition boundaries)
  - Rebalancing = bulk file moves between nodes

Key concepts:
  - Partition boundaries NEVER change
  - Only partition-to-node assignments change
  - Rebalancing is simple: copy entire partition files
  - Trade-off: must guess partition count upfront

Run: python 01_fixed_partitions.py
"""

import sys
import time
import random
from collections import defaultdict
from typing import Dict, List, Set, Tuple, Any

sys.stdout.reconfigure(encoding='utf-8')


# =============================================================================
# CORE COMPONENTS: Partition, Node, Cluster
# =============================================================================

class Partition:
    """A single partition — a range of keys with data."""

    def __init__(self, partition_id: int, key_range: Tuple[int, int]):
        self.partition_id = partition_id
        self.key_range = key_range  # (min_key, max_key)
        self.data: Dict[int, Dict[str, Any]] = {}
        self.size_bytes = 0

    def contains_key(self, key: int) -> bool:
        """Check if this partition owns the key."""
        min_key, max_key = self.key_range
        return min_key <= key < max_key

    def insert(self, key: int, value: Dict[str, Any]):
        """Insert a key-value pair."""
        if not self.contains_key(key):
            raise ValueError(f"Key {key} not in partition range {self.key_range}")
        self.data[key] = value.copy()
        self.size_bytes += len(str(value))

    def read(self, key: int) -> Dict[str, Any]:
        """Read a value by key."""
        return self.data.get(key)

    def read_range(self, min_key: int, max_key: int) -> List[Tuple[int, Dict]]:
        """Range query within this partition."""
        return [(k, v) for k, v in self.data.items() if min_key <= k < max_key]

    def __repr__(self):
        return f"Partition({self.partition_id}, range={self.key_range}, size={len(self.data)} items, {self.size_bytes} bytes)"


class Node:
    """A database node that holds multiple partitions."""

    def __init__(self, node_id: int):
        self.node_id = node_id
        self.partitions: Dict[int, Partition] = {}  # partition_id -> Partition
        self.total_size_bytes = 0

    def assign_partition(self, partition: Partition):
        """Assign a partition to this node."""
        self.partitions[partition.partition_id] = partition
        self.total_size_bytes += partition.size_bytes

    def remove_partition(self, partition_id: int) -> Partition:
        """Remove and return a partition from this node."""
        partition = self.partitions.pop(partition_id)
        self.total_size_bytes -= partition.size_bytes
        return partition

    def get_partition_for_key(self, key: int) -> Partition:
        """Find the partition that owns this key."""
        for partition in self.partitions.values():
            if partition.contains_key(key):
                return partition
        raise ValueError(f"No partition on node {self.node_id} owns key {key}")

    def write(self, key: int, value: Dict[str, Any]):
        """Write a key-value pair to the appropriate partition."""
        partition = self.get_partition_for_key(key)
        partition.insert(key, value)
        self.total_size_bytes += len(str(value))

    def read(self, key: int) -> Dict[str, Any]:
        """Read a key-value pair."""
        partition = self.get_partition_for_key(key)
        return partition.read(key)

    def partition_count(self) -> int:
        return len(self.partitions)

    def __repr__(self):
        return f"Node({self.node_id}, {self.partition_count()} partitions, {self.total_size_bytes} bytes)"


class Cluster:
    """A distributed cluster with fixed partitions."""

    def __init__(self, num_partitions: int, key_range: Tuple[int, int]):
        """
        Initialize cluster with fixed partitions.

        Args:
            num_partitions: Total number of partitions (fixed forever)
            key_range: (min_key, max_key) — the entire key space
        """
        self.num_partitions = num_partitions
        self.key_range = key_range
        self.nodes: Dict[int, Node] = {}
        self.partition_to_node: Dict[int, int] = {}  # partition_id -> node_id
        self.partitions: Dict[int, Partition] = {}  # partition_id -> Partition

        # Create all partitions upfront with fixed boundaries
        min_key, max_key = key_range
        keys_per_partition = (max_key - min_key) // num_partitions

        for p_id in range(num_partitions):
            p_min = min_key + (p_id * keys_per_partition)
            p_max = p_min + keys_per_partition if p_id < num_partitions - 1 else max_key
            self.partitions[p_id] = Partition(p_id, (p_min, p_max))

    def add_node(self) -> int:
        """Add a new node to the cluster."""
        node_id = len(self.nodes)
        self.nodes[node_id] = Node(node_id)
        return node_id

    def initial_assignment(self):
        """Assign partitions to nodes initially (round-robin)."""
        for p_id, partition in self.partitions.items():
            node_id = p_id % len(self.nodes)
            self.nodes[node_id].assign_partition(partition)
            self.partition_to_node[p_id] = node_id

    def write(self, key: int, value: Dict[str, Any]):
        """Write to the cluster."""
        # Find which partition owns this key
        for partition in self.partitions.values():
            if partition.contains_key(key):
                node_id = self.partition_to_node[partition.partition_id]
                self.nodes[node_id].write(key, value)
                return
        raise ValueError(f"No partition owns key {key}")

    def read(self, key: int) -> Dict[str, Any]:
        """Read from the cluster."""
        for partition in self.partitions.values():
            if partition.contains_key(key):
                node_id = self.partition_to_node[partition.partition_id]
                return self.nodes[node_id].read(key)
        raise ValueError(f"No partition owns key {key}")

    def rebalance(self):
        """
        Rebalance partitions across all nodes.

        Strategy: Distribute partitions as evenly as possible.
        """
        # Clear current assignments
        for node in self.nodes.values():
            node.partitions.clear()
            node.total_size_bytes = 0

        # Redistribute partitions round-robin
        for p_id in range(self.num_partitions):
            node_id = p_id % len(self.nodes)
            self.nodes[node_id].assign_partition(self.partitions[p_id])
            self.partition_to_node[p_id] = node_id

    def get_load_distribution(self) -> Dict[int, Tuple[int, int]]:
        """Return load distribution: node_id -> (partition_count, size_bytes)."""
        return {
            node_id: (node.partition_count(), node.total_size_bytes)
            for node_id, node in self.nodes.items()
        }

    def get_imbalance_ratio(self) -> float:
        """Calculate imbalance: max_load / min_load."""
        loads = [node.total_size_bytes for node in self.nodes.values()]
        if not loads or min(loads) == 0:
            return 1.0
        return max(loads) / min(loads)


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


def demo_1_initial_setup():
    """
    Demo 1: Set up a cluster with fixed partitions.

    DDIA concept: "Create many more partitions than there are nodes,
    and keep the number of partitions fixed forever."
    """
    print_header("DEMO 1: Initial Cluster Setup with Fixed Partitions")
    print("""
    We create 1000 partitions for a 10-node cluster.
    Each node initially gets 100 partitions.
    Partition boundaries are FIXED and never change.
    """)

    # Create cluster: 1000 partitions, key range 0-100000
    cluster = Cluster(num_partitions=1000, key_range=(0, 100000))
    print(f"  ✅ Created {cluster.num_partitions} partitions")
    print(f"     Key range: {cluster.key_range}")

    # Add 10 nodes
    for i in range(10):
        cluster.add_node()
    print(f"  ✅ Added {len(cluster.nodes)} nodes")

    # Initial assignment
    cluster.initial_assignment()
    print(f"  ✅ Initial partition assignment (round-robin)")

    # Show distribution
    print_section("📊 Initial Load Distribution")
    distribution = cluster.get_load_distribution()
    for node_id in sorted(distribution.keys()):
        part_count, size = distribution[node_id]
        print(f"  Node {node_id:2d}: {part_count:3d} partitions, {size:8d} bytes")

    imbalance = cluster.get_imbalance_ratio()
    print(f"\n  Imbalance ratio: {imbalance:.2f}x")

    # Insert some data
    print_section("📝 Inserting Test Data")
    num_inserts = 5000
    for i in range(num_inserts):
        key = random.randint(0, 99999)
        value = {"id": i, "data": f"value_{i}", "timestamp": time.time()}
        cluster.write(key, value)

    print(f"  ✅ Inserted {num_inserts} key-value pairs")

    # Show distribution after data
    print_section("📊 Load Distribution After Data Insertion")
    distribution = cluster.get_load_distribution()
    for node_id in sorted(distribution.keys()):
        part_count, size = distribution[node_id]
        print(f"  Node {node_id:2d}: {part_count:3d} partitions, {size:8d} bytes")

    imbalance = cluster.get_imbalance_ratio()
    print(f"\n  Imbalance ratio: {imbalance:.2f}x")

    print("""
  💡 KEY INSIGHT (DDIA):
     With random key distribution, load is fairly balanced.
     But if keys are skewed (e.g., timestamps), some partitions
     become hot spots. This is why partition count matters!
    """)

    return cluster


def demo_2_adding_nodes():
    """
    Demo 2: Add new nodes and rebalance.

    DDIA concept: "When a new node joins, it steals partitions
    from existing nodes. Partition boundaries don't change."
    """
    print_header("DEMO 2: Adding Nodes and Rebalancing")
    print("""
    Starting with 10 nodes, we add 5 new nodes.
    Rebalancing redistributes partitions (not boundaries).
    """)

    # Start with existing cluster
    cluster = Cluster(num_partitions=1000, key_range=(0, 100000))
    for i in range(10):
        cluster.add_node()
    cluster.initial_assignment()

    # Insert data
    for i in range(5000):
        key = random.randint(0, 99999)
        value = {"id": i, "data": f"value_{i}"}
        cluster.write(key, value)

    print(f"  📊 Starting state: {len(cluster.nodes)} nodes")
    distribution = cluster.get_load_distribution()
    for node_id in sorted(distribution.keys()):
        part_count, size = distribution[node_id]
        print(f"     Node {node_id:2d}: {part_count:3d} partitions")

    # Add new nodes
    print_section("➕ Adding 5 New Nodes")
    for i in range(5):
        new_node_id = cluster.add_node()
        print(f"  ✅ Node {new_node_id} joined the cluster")

    print(f"\n  Total nodes now: {len(cluster.nodes)}")

    # Rebalance
    print_section("🔄 Rebalancing Partitions")
    start_time = time.time()
    cluster.rebalance()
    elapsed = time.time() - start_time

    print(f"  ✅ Rebalancing complete in {elapsed:.3f}s")

    # Show new distribution
    print_section("📊 Load Distribution After Rebalancing")
    distribution = cluster.get_load_distribution()
    for node_id in sorted(distribution.keys()):
        part_count, size = distribution[node_id]
        print(f"  Node {node_id:2d}: {part_count:3d} partitions, {size:8d} bytes")

    imbalance = cluster.get_imbalance_ratio()
    print(f"\n  Imbalance ratio: {imbalance:.2f}x")

    print("""
  💡 KEY INSIGHT (DDIA):
     Notice how partitions are redistributed evenly.
     With 1000 partitions and 15 nodes:
       - Some nodes get 66-67 partitions
       - Load is balanced automatically

     If we had only 15 partitions (one per node):
       - Adding a node would require splitting partitions
       - Much more complex!
    """)


def demo_3_partition_count_matters():
    """
    Demo 3: Show why partition count matters.

    DDIA concept: "Too few partitions → large partition moves.
    Too many partitions → management overhead."
    """
    print_header("DEMO 3: Why Partition Count Matters")
    print("""
    We'll compare different partition counts and see the impact
    on rebalancing efficiency and management overhead.
    """)

    scenarios = [
        ("Few partitions (15)", 15),
        ("Medium partitions (100)", 100),
        ("Many partitions (1000)", 1000),
        ("Very many partitions (10000)", 10000),
    ]

    print_section("📊 Partition Count Impact")
    print(f"  {'Scenario':<30} {'Partitions':<12} {'Per Node':<12} {'Mgmt Overhead'}")
    print(f"  {'─'*70}")

    for scenario_name, num_partitions in scenarios:
        cluster = Cluster(num_partitions=num_partitions, key_range=(0, 100000))
        for i in range(10):
            cluster.add_node()
        cluster.initial_assignment()

        partitions_per_node = num_partitions // 10
        mgmt_overhead = "Low" if num_partitions <= 100 else "Medium" if num_partitions <= 1000 else "High"

        print(f"  {scenario_name:<30} {num_partitions:<12} {partitions_per_node:<12} {mgmt_overhead}")

    print("""
  💡 DDIA RECOMMENDATION:
     Each partition should be between 100MB and a few GB.

     Example calculation:
       - Total dataset: 1TB
       - Target partition size: 1GB
       - Number of partitions needed: 1000
       - With 10 nodes: 100 partitions per node
       - With 100 nodes: 10 partitions per node
    """)


def demo_4_data_movement_cost():
    """
    Demo 4: Measure data movement during rebalancing.

    DDIA concept: "Only the minimum necessary data is moved
    between nodes to minimize network and disk I/O."
    """
    print_header("DEMO 4: Data Movement Cost During Rebalancing")
    print("""
    We'll measure how much data needs to move when adding nodes.
    """)

    cluster = Cluster(num_partitions=1000, key_range=(0, 100000))
    for i in range(10):
        cluster.add_node()
    cluster.initial_assignment()

    # Insert data
    for i in range(10000):
        key = random.randint(0, 99999)
        value = {"id": i, "data": f"value_{i}"}
        cluster.write(key, value)

    # Measure total data
    total_data = sum(node.total_size_bytes for node in cluster.nodes.values())
    print(f"  📊 Total data in cluster: {total_data:,} bytes")

    # Calculate data to move when adding nodes
    print_section("📈 Data Movement When Adding Nodes")

    for num_new_nodes in [1, 5, 10]:
        # Create new nodes
        for i in range(num_new_nodes):
            cluster.add_node()

        # Calculate data that needs to move
        # With fixed partitions, we move: (new_nodes / total_nodes) * total_data
        total_nodes = len(cluster.nodes)
        data_to_move = total_data * (num_new_nodes / total_nodes)

        print(f"  Adding {num_new_nodes} nodes (total: {total_nodes})")
        print(f"    Data to move: {data_to_move:,.0f} bytes ({data_to_move/total_data*100:.1f}% of total)")

    print("""
  💡 KEY INSIGHT (DDIA):
     With FIXED partitions, data movement is proportional to
     the number of new nodes, not the total dataset size.

     Compare to hash(key) % N:
       - Adding 1 node to 10 nodes: ~90% of data moves! ❌
       - With fixed partitions: ~10% of data moves ✅
    """)


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 80)
    print("  EXERCISE 1: FIXED NUMBER OF PARTITIONS — REBALANCING STRATEGY")
    print("  DDIA Chapter 6: 'Rebalancing Partitions'")
    print("=" * 80)
    print("""
  This exercise demonstrates the FIXED PARTITION COUNT strategy.
  You'll see how partition boundaries stay constant while partition
  assignments to nodes change during rebalancing.
    """)

    demo_1_initial_setup()
    demo_2_adding_nodes()
    demo_3_partition_count_matters()
    demo_4_data_movement_cost()

    print("\n" + "=" * 80)
    print("  EXERCISE 1 COMPLETE ✅")
    print("=" * 80)
    print("""
  Key Takeaways:

  1. 🔒 Partition boundaries are FIXED forever
  2. 📍 Only partition-to-node assignments change during rebalancing
  3. 📦 Rebalancing = bulk file moves (simple!)
  4. 🎯 Partition count must be chosen upfront (100MB-few GB each)
  5. 📊 With many partitions, load balances automatically
  6. 🚀 Data movement is proportional to new nodes, not total data

  Next: Run 02_dynamic_partitioning.py to see automatic split/merge
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