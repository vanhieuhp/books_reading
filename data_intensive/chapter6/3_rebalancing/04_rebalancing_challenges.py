"""
Exercise 4: Rebalancing Challenges — Hot Spots and Data Movement

DDIA Reference: Chapter 6, "Rebalancing Partitions" (pp. 211-215)

This exercise demonstrates real-world challenges during rebalancing:
  - Cascading failures: rebalancing floods network, triggers more failures
  - Hot spots: some partitions get disproportionate load
  - Data movement overhead: network and disk I/O during rebalancing
  - Automatic vs manual rebalancing trade-offs

Key concepts:
  - Automatic rebalancing can cause cascading failures
  - Manual approval prevents catastrophic cascades
  - Hot spots require application-level fixes
  - Rebalancing must not block reads/writes

Run: python 04_rebalancing_challenges.py
"""

import sys
import time
import random
from typing import Dict, List, Tuple, Any, Optional
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')


# =============================================================================
# CORE COMPONENTS: Partition, Node, Cluster with Rebalancing
# =============================================================================

class Partition:
    """A partition with data and metadata."""

    def __init__(self, partition_id: int, key_range: Tuple[int, int]):
        self.partition_id = partition_id
        self.key_range = key_range
        self.data: Dict[int, Dict[str, Any]] = {}
        self.size_bytes = 0
        self.read_count = 0
        self.write_count = 0

    def contains_key(self, key: int) -> bool:
        min_key, max_key = self.key_range
        return min_key <= key < max_key

    def insert(self, key: int, value: Dict[str, Any]):
        if not self.contains_key(key):
            raise ValueError(f"Key {key} not in partition range {self.key_range}")
        self.data[key] = value.copy()
        self.size_bytes += len(str(value))
        self.write_count += 1

    def read(self, key: int) -> Optional[Dict[str, Any]]:
        self.read_count += 1
        return self.data.get(key)

    def get_load_score(self) -> float:
        """Calculate load score: combination of reads, writes, and size."""
        return self.read_count + self.write_count * 2 + self.size_bytes / 1000

    def __repr__(self):
        return f"Partition({self.partition_id}, range={self.key_range}, size={self.size_bytes}, reads={self.read_count}, writes={self.write_count})"


class Node:
    """A database node with partitions."""

    def __init__(self, node_id: int):
        self.node_id = node_id
        self.partitions: Dict[int, Partition] = {}
        self.total_size_bytes = 0
        self.is_healthy = True
        self.rebalancing = False

    def assign_partition(self, partition: Partition):
        self.partitions[partition.partition_id] = partition
        self.total_size_bytes += partition.size_bytes

    def remove_partition(self, partition_id: int) -> Partition:
        partition = self.partitions.pop(partition_id)
        self.total_size_bytes -= partition.size_bytes
        return partition

    def get_partition_for_key(self, key: int) -> Partition:
        for partition in self.partitions.values():
            if partition.contains_key(key):
                return partition
        raise ValueError(f"No partition on node {self.node_id} owns key {key}")

    def write(self, key: int, value: Dict[str, Any]):
        partition = self.get_partition_for_key(key)
        partition.insert(key, value)
        self.total_size_bytes += len(str(value))

    def read(self, key: int) -> Optional[Dict[str, Any]]:
        partition = self.get_partition_for_key(key)
        return partition.read(key)

    def get_load_score(self) -> float:
        """Calculate total load on this node."""
        return sum(p.get_load_score() for p in self.partitions.values())

    def get_hottest_partition(self) -> Optional[Partition]:
        """Find the partition with highest load."""
        if not self.partitions:
            return None
        return max(self.partitions.values(), key=lambda p: p.get_load_score())

    def __repr__(self):
        return f"Node({self.node_id}, {len(self.partitions)} partitions, {self.total_size_bytes} bytes, healthy={self.is_healthy})"


class RebalancingCluster:
    """A cluster that can rebalance partitions."""

    def __init__(self, num_partitions: int, key_range: Tuple[int, int]):
        self.num_partitions = num_partitions
        self.key_range = key_range
        self.nodes: Dict[int, Node] = {}
        self.partitions: Dict[int, Partition] = {}
        self.partition_to_node: Dict[int, int] = {}
        self.rebalancing_history: List[Tuple[float, str]] = []
        self.network_bandwidth_used = 0

        # Create partitions
        min_key, max_key = key_range
        keys_per_partition = (max_key - min_key) // num_partitions

        for p_id in range(num_partitions):
            p_min = min_key + (p_id * keys_per_partition)
            p_max = p_min + keys_per_partition if p_id < num_partitions - 1 else max_key
            self.partitions[p_id] = Partition(p_id, (p_min, p_max))

    def add_node(self) -> int:
        node_id = len(self.nodes)
        self.nodes[node_id] = Node(node_id)
        return node_id

    def initial_assignment(self):
        for p_id, partition in self.partitions.items():
            node_id = p_id % len(self.nodes)
            self.nodes[node_id].assign_partition(partition)
            self.partition_to_node[p_id] = node_id

    def write(self, key: int, value: Dict[str, Any]):
        for partition in self.partitions.values():
            if partition.contains_key(key):
                node_id = self.partition_to_node[partition.partition_id]
                if self.nodes[node_id].is_healthy:
                    self.nodes[node_id].write(key, value)
                return
        raise ValueError(f"No partition owns key {key}")

    def read(self, key: int) -> Optional[Dict[str, Any]]:
        for partition in self.partitions.values():
            if partition.contains_key(key):
                node_id = self.partition_to_node[partition.partition_id]
                if self.nodes[node_id].is_healthy:
                    return self.nodes[node_id].read(key)
        return None

    def get_load_distribution(self) -> Dict[int, float]:
        """Return load per node."""
        return {node_id: node.get_load_score() for node_id, node in self.nodes.items()}

    def get_imbalance_ratio(self) -> float:
        """Calculate imbalance: max_load / min_load."""
        loads = [node.get_load_score() for node in self.nodes.values() if node.is_healthy]
        if not loads or min(loads) == 0:
            return 1.0
        return max(loads) / min(loads)

    def rebalance_automatic(self) -> Tuple[int, int]:
        """
        Automatic rebalancing: move partitions to balance load.

        Returns: (partitions_moved, bytes_moved)
        """
        partitions_moved = 0
        bytes_moved = 0

        # Find most and least loaded nodes
        loads = {nid: node.get_load_score() for nid, node in self.nodes.items() if node.is_healthy}
        if not loads:
            return 0, 0

        most_loaded_node_id = max(loads, key=loads.get)
        least_loaded_node_id = min(loads, key=loads.get)

        most_loaded = self.nodes[most_loaded_node_id]
        least_loaded = self.nodes[least_loaded_node_id]

        # Move partitions from most to least loaded
        while most_loaded.get_load_score() > least_loaded.get_load_score() * 1.1:
            hottest = most_loaded.get_hottest_partition()
            if not hottest:
                break

            # Move partition
            partition = most_loaded.remove_partition(hottest.partition_id)
            least_loaded.assign_partition(partition)
            self.partition_to_node[hottest.partition_id] = least_loaded_node_id

            bytes_moved += partition.size_bytes
            partitions_moved += 1
            self.network_bandwidth_used += partition.size_bytes

        return partitions_moved, bytes_moved

    def rebalance_manual(self, plan: List[Tuple[int, int]]) -> Tuple[int, int]:
        """
        Manual rebalancing: execute a pre-approved plan.

        Args:
            plan: List of (partition_id, target_node_id) tuples

        Returns: (partitions_moved, bytes_moved)
        """
        partitions_moved = 0
        bytes_moved = 0

        for partition_id, target_node_id in plan:
            # Find current node
            current_node_id = self.partition_to_node[partition_id]
            if current_node_id == target_node_id:
                continue

            # Move partition
            partition = self.nodes[current_node_id].remove_partition(partition_id)
            self.nodes[target_node_id].assign_partition(partition)
            self.partition_to_node[partition_id] = target_node_id

            bytes_moved += partition.size_bytes
            partitions_moved += 1
            self.network_bandwidth_used += partition.size_bytes

        return partitions_moved, bytes_moved


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


def demo_1_cascading_failures():
    """
    Demo 1: Show how automatic rebalancing can cause cascading failures.

    DDIA concept: "If the system incorrectly detects a node as dead,
    it might start a massive rebalancing operation. This floods the
    network with data transfers, which makes the already-overloaded
    network even slower, which triggers more incorrect failure
    detections — a cascading failure."
    """
    print_header("DEMO 1: Cascading Failures from Automatic Rebalancing")
    print("""
    Scenario: A temporary network blip causes a node to be marked
    as dead. Automatic rebalancing starts, flooding the network.
    This makes the network even slower, triggering more failures.
    """)

    cluster = RebalancingCluster(num_partitions=100, key_range=(0, 100000))
    for i in range(5):
        cluster.add_node()
    cluster.initial_assignment()

    # Insert data
    for i in range(5000):
        key = random.randint(0, 99999)
        value = {"id": i, "data": f"value_{i}"}
        cluster.write(key, value)

    print(f"  📊 Initial state: {len(cluster.nodes)} nodes, {len(cluster.partitions)} partitions")
    print(f"     Total data: {sum(n.total_size_bytes for n in cluster.nodes.values()):,} bytes")

    # Simulate network blip: mark node 2 as dead
    print_section("⚠️  Network Blip: Node 2 Marked as Dead")
    cluster.nodes[2].is_healthy = False
    print(f"  Node 2 is now UNHEALTHY")

    # Automatic rebalancing starts
    print_section("🔄 Automatic Rebalancing Triggered")
    print(f"  System detects node 2 is down")
    print(f"  Starting automatic rebalancing...")

    start_time = time.time()
    partitions_moved, bytes_moved = cluster.rebalance_automatic()
    elapsed = time.time() - start_time

    print(f"  ✅ Rebalancing complete")
    print(f"     Partitions moved: {partitions_moved}")
    print(f"     Data moved: {bytes_moved:,} bytes")
    print(f"     Time: {elapsed:.3f}s")
    print(f"     Network bandwidth used: {cluster.network_bandwidth_used:,} bytes")

    # Network recovers, but damage is done
    print_section("🔧 Network Recovers")
    cluster.nodes[2].is_healthy = True
    print(f"  Node 2 is back online!")
    print(f"  But the network was flooded during rebalancing.")
    print(f"  This could have triggered more failures...")

    print("""
  💡 DDIA INSIGHT:
     Automatic rebalancing is risky because:
       ❌ Temporary network blips trigger massive data movement
       ❌ Data movement floods the network
       ❌ Flooded network triggers more failure detections
       ❌ Cascading failure: system spirals out of control

     Solution: MANUAL APPROVAL
       ✅ System suggests rebalancing plan
       ✅ Human administrator reviews and approves
       ✅ Prevents catastrophic cascades
       ✅ Trade-off: adds delay but prevents disasters
    """)


def demo_2_hot_spots():
    """
    Demo 2: Show how hot spots develop and cause imbalance.

    DDIA concept: "If millions of requests all target the exact same
    key, that partition becomes an extreme hot spot. The database
    cannot automatically fix this."
    """
    print_header("DEMO 2: Hot Spots and Load Imbalance")
    print("""
    Scenario: A celebrity post goes viral. Millions of reads target
    the same key, causing a hot spot on one partition.
    """)

    cluster = RebalancingCluster(num_partitions=100, key_range=(0, 100000))
    for i in range(5):
        cluster.add_node()
    cluster.initial_assignment()

    # Insert data
    print_section("📝 Inserting Initial Data")
    for i in range(5000):
        key = random.randint(0, 99999)
        value = {"id": i, "data": f"value_{i}"}
        cluster.write(key, value)

    print(f"  ✅ Inserted 5000 keys")

    # Show initial load distribution
    print_section("📊 Initial Load Distribution")
    loads = cluster.get_load_distribution()
    for node_id in sorted(loads.keys()):
        print(f"  Node {node_id}: load score = {loads[node_id]:.0f}")

    imbalance = cluster.get_imbalance_ratio()
    print(f"\n  Imbalance ratio: {imbalance:.2f}x")

    # Viral post: millions of reads on one key
    print_section("🔥 Viral Post: Millions of Reads on Key 50000")
    viral_key = 50000
    for i in range(10000):
        cluster.read(viral_key)

    print(f"  ✅ 10,000 reads on key {viral_key}")

    # Show new load distribution
    print_section("📊 Load Distribution After Viral Post")
    loads = cluster.get_load_distribution()
    for node_id in sorted(loads.keys()):
        print(f"  Node {node_id}: load score = {loads[node_id]:.0f}")

    imbalance = cluster.get_imbalance_ratio()
    print(f"\n  Imbalance ratio: {imbalance:.2f}x ⚠️  VERY IMBALANCED!")

    # Try automatic rebalancing
    print_section("🔄 Automatic Rebalancing (Won't Help!)")
    partitions_moved, bytes_moved = cluster.rebalance_automatic()
    print(f"  Partitions moved: {partitions_moved}")
    print(f"  Data moved: {bytes_moved:,} bytes")

    loads = cluster.get_load_distribution()
    imbalance = cluster.get_imbalance_ratio()
    print(f"\n  Imbalance ratio after rebalancing: {imbalance:.2f}x")
    print(f"  ⚠️  Still imbalanced! Rebalancing didn't help.")

    print("""
  💡 DDIA INSIGHT:
     Automatic rebalancing can't fix hot spots because:
       ❌ The hot partition is still hot after moving
       ❌ Moving it just moves the problem to another node
       ❌ The fundamental issue is the skewed workload

     Solution: APPLICATION-LEVEL KEY SPLITTING
       ✅ Append random suffix to hot key: "post_8932_00" to "post_8932_99"
       ✅ Splits load across 100 partitions
       ✅ Trade-off: reads must query all 100 keys and merge

     Real-world example:
       • Twitter: trending topics cause hot spots
       • Solution: split hot keys across multiple partitions
       • Only applied to keys known to be hot
    """)


def demo_3_data_movement_overhead():
    """
    Demo 3: Measure data movement overhead during rebalancing.

    DDIA concept: "Rebalancing must move only the minimum necessary
    data to minimize network and disk I/O."
    """
    print_header("DEMO 3: Data Movement Overhead")
    print("""
    We'll measure how much data moves during rebalancing
    and the impact on the network.
    """)

    cluster = RebalancingCluster(num_partitions=1000, key_range=(0, 100000))
    for i in range(10):
        cluster.add_node()
    cluster.initial_assignment()

    # Insert data
    for i in range(10000):
        key = random.randint(0, 99999)
        value = {"id": i, "data": f"value_{i}" * 2}
        cluster.write(key, value)

    total_data = sum(n.total_size_bytes for n in cluster.nodes.values())
    print(f"  📊 Total data in cluster: {total_data:,} bytes")

    # Simulate adding nodes and rebalancing
    print_section("Adding Nodes and Rebalancing")

    for num_new_nodes in [1, 2, 5]:
        # Reset cluster
        cluster = RebalancingCluster(num_partitions=1000, key_range=(0, 100000))
        for i in range(10):
            cluster.add_node()
        cluster.initial_assignment()

        # Insert data
        for i in range(10000):
            key = random.randint(0, 99999)
            value = {"id": i, "data": f"value_{i}" * 2}
            cluster.write(key, value)

        total_data = sum(n.total_size_bytes for n in cluster.nodes.values())

        # Add new nodes
        for i in range(num_new_nodes):
            cluster.add_node()

        # Rebalance
        cluster.network_bandwidth_used = 0
        partitions_moved, bytes_moved = cluster.rebalance_automatic()

        total_nodes = len(cluster.nodes)
        percent_of_total = (bytes_moved / total_data * 100) if total_data > 0 else 0

        print(f"  Adding {num_new_nodes} nodes (total: {total_nodes})")
        print(f"    Data moved: {bytes_moved:,} bytes ({percent_of_total:.1f}% of total)")
        print(f"    Partitions moved: {partitions_moved}")

    print("""
  💡 KEY INSIGHT (DDIA):
     With fixed partitions, data movement is proportional to
     the number of new nodes, not the total dataset size.

     This is why fixed partitions are better than hash(key) % N:
       • hash(key) % N: ~90% of data moves when adding 1 node to 10
       • Fixed partitions: ~10% of data moves
    """)


def demo_4_manual_vs_automatic():
    """
    Demo 4: Compare manual vs automatic rebalancing.

    DDIA concept: "Manual approval prevents cascading failures but
    adds delay. Automatic rebalancing is convenient but risky."
    """
    print_header("DEMO 4: Manual vs Automatic Rebalancing")
    print("""
    Comparison of manual and automatic rebalancing strategies.
    """)

    print_section("Scenario: Adding 3 Nodes to 10-Node Cluster")

    # Setup
    cluster = RebalancingCluster(num_partitions=1000, key_range=(0, 100000))
    for i in range(10):
        cluster.add_node()
    cluster.initial_assignment()

    for i in range(10000):
        key = random.randint(0, 99999)
        value = {"id": i, "data": f"value_{i}"}
        cluster.write(key, value)

    initial_imbalance = cluster.get_imbalance_ratio()
    print(f"  Initial imbalance: {initial_imbalance:.2f}x")

    # Add nodes
    for i in range(3):
        cluster.add_node()

    print(f"  Added 3 nodes (total: {len(cluster.nodes)})")

    # Automatic rebalancing
    print_section("Automatic Rebalancing")
    cluster_auto = RebalancingCluster(num_partitions=1000, key_range=(0, 100000))
    for i in range(10):
        cluster_auto.add_node()
    cluster_auto.initial_assignment()

    for i in range(10000):
        key = random.randint(0, 99999)
        value = {"id": i, "data": f"value_{i}"}
        cluster_auto.write(key, value)

    for i in range(3):
        cluster_auto.add_node()

    start = time.time()
    partitions_moved, bytes_moved = cluster_auto.rebalance_automatic()
    auto_time = time.time() - start

    auto_imbalance = cluster_auto.get_imbalance_ratio()
    print(f"  Time: {auto_time:.3f}s")
    print(f"  Partitions moved: {partitions_moved}")
    print(f"  Final imbalance: {auto_imbalance:.2f}x")
    print(f"  Risk: ⚠️  Cascading failures possible")

    # Manual rebalancing
    print_section("Manual Rebalancing")
    print(f"  1. System generates rebalancing plan")
    print(f"  2. Administrator reviews plan")
    print(f"  3. Administrator approves")
    print(f"  4. System executes plan")

    # Create a simple plan: distribute partitions evenly
    plan = []
    partition_id = 0
    for node_id in range(len(cluster.nodes)):
        for i in range(1000 // len(cluster.nodes)):
            plan.append((partition_id, node_id))
            partition_id += 1

    start = time.time()
    partitions_moved, bytes_moved = cluster.rebalance_manual(plan)
    manual_time = time.time() - start

    manual_imbalance = cluster.get_imbalance_ratio()
    print(f"\n  Time: {manual_time:.3f}s")
    print(f"  Partitions moved: {partitions_moved}")
    print(f"  Final imbalance: {manual_imbalance:.2f}x")
    print(f"  Risk: ✅ Cascading failures prevented")

    print("""
  💡 DDIA RECOMMENDATION:
     Use MANUAL APPROVAL for rebalancing:
       ✅ Prevents cascading failures
       ✅ Administrator can verify plan is correct
       ✅ Adds delay but prevents disasters

     Used by: Couchbase, Riak, Voldemort

     Trade-off:
       ❌ Requires human intervention
       ❌ Slower response to cluster changes
       ✅ Much safer than automatic rebalancing
    """)


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 80)
    print("  EXERCISE 4: REBALANCING CHALLENGES")
    print("  DDIA Chapter 6: 'Rebalancing Partitions'")
    print("=" * 80)
    print("""
  This exercise demonstrates real-world challenges during rebalancing:
  cascading failures, hot spots, data movement overhead, and the
  trade-offs between automatic and manual rebalancing.
    """)

    demo_1_cascading_failures()
    demo_2_hot_spots()
    demo_3_data_movement_overhead()
    demo_4_manual_vs_automatic()

    print("\n" + "=" * 80)
    print("  EXERCISE 4 COMPLETE ✅")
    print("=" * 80)
    print("""
  Key Takeaways:

  1. ⚠️  Automatic rebalancing can cause cascading failures
  2. 🔥 Hot spots can't be fixed by rebalancing alone
  3. 🔑 Application-level key splitting fixes hot spots
  4. 📊 Data movement is proportional to new nodes (with fixed partitions)
  5. 👤 Manual approval prevents cascading failures
  6. ⚙️  Trade-off: manual is slower but safer

  Next: You've completed Section 3! Review all exercises and concepts.
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
