"""
Exercise 2: Dynamic Partitioning — Automatic Split and Merge

DDIA Reference: Chapter 6, "Rebalancing Partitions" (pp. 207-209)

This exercise demonstrates DYNAMIC PARTITIONING:
  - Partitions split when they exceed a size threshold (e.g., 10GB)
  - Partitions merge when they shrink below a threshold
  - Number of partitions grows/shrinks with dataset size
  - Works well with key-range partitioning

Key concepts:
  - Partition boundaries change dynamically
  - Automatic adaptation to data growth
  - Cold-start problem: new database starts with 1 partition
  - Pre-splitting: create initial partitions to avoid bottleneck

Run: python 02_dynamic_partitioning.py
"""

import sys
import time
import random
from typing import Dict, List, Tuple, Any, Optional

sys.stdout.reconfigure(encoding='utf-8')


# =============================================================================
# CORE COMPONENTS: DynamicPartition, DynamicCluster
# =============================================================================

class DynamicPartition:
    """A partition that can split and merge dynamically."""

    _next_id = 0

    def __init__(self, key_range: Tuple[int, int], parent_id: Optional[int] = None):
        self.partition_id = DynamicPartition._next_id
        DynamicPartition._next_id += 1
        self.key_range = key_range  # (min_key, max_key)
        self.data: Dict[int, Dict[str, Any]] = {}
        self.size_bytes = 0
        self.parent_id = parent_id  # For tracking split history
        self.creation_time = time.time()

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

    def delete(self, key: int):
        """Delete a key-value pair."""
        if key in self.data:
            self.size_bytes -= len(str(self.data[key]))
            del self.data[key]

    def read(self, key: int) -> Optional[Dict[str, Any]]:
        """Read a value by key."""
        return self.data.get(key)

    def split(self) -> Tuple['DynamicPartition', 'DynamicPartition']:
        """
        Split this partition into two roughly equal parts.

        Returns: (left_partition, right_partition)
        """
        min_key, max_key = self.key_range
        mid_key = (min_key + max_key) // 2

        left = DynamicPartition((min_key, mid_key), parent_id=self.partition_id)
        right = DynamicPartition((mid_key, max_key), parent_id=self.partition_id)

        # Distribute data
        for key, value in self.data.items():
            if key < mid_key:
                left.data[key] = value
                left.size_bytes += len(str(value))
            else:
                right.data[key] = value
                right.size_bytes += len(str(value))

        return left, right

    def merge(self, other: 'DynamicPartition') -> 'DynamicPartition':
        """
        Merge this partition with another.

        Assumes they are adjacent and can be merged.
        """
        min_key = min(self.key_range[0], other.key_range[0])
        max_key = max(self.key_range[1], other.key_range[1])

        merged = DynamicPartition((min_key, max_key))
        merged.data = {**self.data, **other.data}
        merged.size_bytes = self.size_bytes + other.size_bytes

        return merged

    def __repr__(self):
        return f"Partition({self.partition_id}, range={self.key_range}, size={len(self.data)} items, {self.size_bytes} bytes)"


class DynamicCluster:
    """A cluster with dynamic partitioning."""

    def __init__(
        self,
        key_range: Tuple[int, int],
        split_threshold_bytes: int = 1000,
        merge_threshold_bytes: int = 200,
        pre_split_count: int = 1,
    ):
        """
        Initialize cluster with dynamic partitioning.

        Args:
            key_range: (min_key, max_key) — the entire key space
            split_threshold_bytes: Split when partition exceeds this size
            merge_threshold_bytes: Merge when partition falls below this size
            pre_split_count: Number of initial partitions (avoid cold-start)
        """
        self.key_range = key_range
        self.split_threshold = split_threshold_bytes
        self.merge_threshold = merge_threshold_bytes
        self.partitions: Dict[int, DynamicPartition] = {}
        self.split_history: List[Tuple[int, int, int]] = []  # (old_id, left_id, right_id)
        self.merge_history: List[Tuple[int, int, int]] = []  # (left_id, right_id, merged_id)

        # Create initial partitions
        if pre_split_count == 1:
            partition = DynamicPartition(key_range)
            self.partitions[partition.partition_id] = partition
        else:
            # Pre-split into multiple partitions
            min_key, max_key = key_range
            keys_per_partition = (max_key - min_key) // pre_split_count

            for i in range(pre_split_count):
                p_min = min_key + (i * keys_per_partition)
                p_max = p_min + keys_per_partition if i < pre_split_count - 1 else max_key
                partition = DynamicPartition((p_min, p_max))
                self.partitions[partition.partition_id] = partition

    def write(self, key: int, value: Dict[str, Any]):
        """Write to the cluster."""
        # Find partition that owns this key
        for partition in self.partitions.values():
            if partition.contains_key(key):
                partition.insert(key, value)
                # Check if split is needed
                self._check_split(partition)
                return
        raise ValueError(f"No partition owns key {key}")

    def delete(self, key: int):
        """Delete from the cluster."""
        for partition in self.partitions.values():
            if partition.contains_key(key):
                partition.delete(key)
                # Check if merge is needed
                self._check_merge(partition)
                return
        raise ValueError(f"No partition owns key {key}")

    def read(self, key: int) -> Optional[Dict[str, Any]]:
        """Read from the cluster."""
        for partition in self.partitions.values():
            if partition.contains_key(key):
                return partition.read(key)
        raise ValueError(f"No partition owns key {key}")

    def _check_split(self, partition: DynamicPartition):
        """Check if partition should split."""
        if partition.size_bytes > self.split_threshold:
            left, right = partition.split()
            del self.partitions[partition.partition_id]
            self.partitions[left.partition_id] = left
            self.partitions[right.partition_id] = right
            self.split_history.append((partition.partition_id, left.partition_id, right.partition_id))

    def _check_merge(self, partition: DynamicPartition):
        """Check if partition should merge with adjacent partition."""
        if partition.size_bytes > self.merge_threshold:
            return  # Don't merge if still above threshold

        # Find adjacent partition
        min_key, max_key = partition.key_range
        adjacent = None

        for other in self.partitions.values():
            if other.partition_id == partition.partition_id:
                continue
            other_min, other_max = other.key_range
            # Check if adjacent (touching boundaries)
            if other_max == min_key or other_min == max_key:
                if other.size_bytes <= self.merge_threshold:
                    adjacent = other
                    break

        if adjacent:
            merged = partition.merge(adjacent)
            del self.partitions[partition.partition_id]
            del self.partitions[adjacent.partition_id]
            self.partitions[merged.partition_id] = merged
            self.merge_history.append((partition.partition_id, adjacent.partition_id, merged.partition_id))

    def get_partition_count(self) -> int:
        return len(self.partitions)

    def get_total_size(self) -> int:
        return sum(p.size_bytes for p in self.partitions.values())

    def get_partition_sizes(self) -> List[Tuple[int, int, int]]:
        """Return list of (partition_id, key_range, size_bytes)."""
        return [(p.partition_id, p.key_range, p.size_bytes) for p in sorted(self.partitions.values(), key=lambda p: p.key_range[0])]


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


def demo_1_cold_start_problem():
    """
    Demo 1: Show the cold-start problem.

    DDIA concept: "When a brand-new database starts, it has only
    one partition because there is no data yet. All writes hit a
    single node until the first split threshold is reached."
    """
    print_header("DEMO 1: The Cold-Start Problem")
    print("""
    A new database starts with ONE partition.
    All writes go to one node until it grows large enough to split.
    This is a bottleneck!
    """)

    cluster = DynamicCluster(
        key_range=(0, 100000),
        split_threshold_bytes=5000,
        pre_split_count=1,
    )

    print(f"  📊 Initial state: {cluster.get_partition_count()} partition")
    print(f"     All writes go to ONE node! ❌")

    # Insert data until split
    print_section("📝 Inserting Data Until Split")
    for i in range(100):
        key = random.randint(0, 99999)
        value = {"id": i, "data": f"value_{i}" * 5}  # Make it bigger
        cluster.write(key, value)

        if i % 20 == 0:
            print(f"  After {i:3d} inserts: {cluster.get_partition_count()} partitions, "
                  f"{cluster.get_total_size():,} bytes")

    print(f"\n  ✅ After splits: {cluster.get_partition_count()} partitions")
    print(f"     Load is now distributed! ✅")

    print("""
  💡 DDIA SOLUTION: Pre-Splitting
     Instead of starting with 1 partition, create multiple
     empty partitions at database creation time.
    """)


def demo_2_presplitting():
    """
    Demo 2: Show how pre-splitting avoids the cold-start problem.

    DDIA concept: "HBase and MongoDB allow you to configure an
    initial set of partition boundaries at database creation time."
    """
    print_header("DEMO 2: Pre-Splitting to Avoid Cold-Start")
    print("""
    We create 10 initial partitions instead of 1.
    This distributes writes from the start.
    """)

    cluster = DynamicCluster(
        key_range=(0, 100000),
        split_threshold_bytes=5000,
        pre_split_count=10,
    )

    print(f"  📊 Initial state: {cluster.get_partition_count()} partitions (pre-split)")
    print(f"     Writes are distributed from the start! ✅")

    # Insert data
    print_section("📝 Inserting Data")
    for i in range(100):
        key = random.randint(0, 99999)
        value = {"id": i, "data": f"value_{i}" * 5}
        cluster.write(key, value)

        if i % 20 == 0:
            print(f"  After {i:3d} inserts: {cluster.get_partition_count()} partitions, "
                  f"{cluster.get_total_size():,} bytes")

    print(f"\n  ✅ Final: {cluster.get_partition_count()} partitions")

    print("""
  💡 KEY INSIGHT (DDIA):
     Pre-splitting trades off:
       ✅ Avoids cold-start bottleneck
       ❌ Requires knowing initial partition boundaries
       ❌ More complex setup
    """)


def demo_3_split_and_merge():
    """
    Demo 3: Show automatic split and merge in action.

    DDIA concept: "Partitions split when they exceed a threshold,
    and merge when they shrink below a threshold."
    """
    print_header("DEMO 3: Automatic Split and Merge")
    print("""
    We'll insert data (causing splits) and then delete data
    (causing merges). Watch the partition count change.
    """)

    cluster = DynamicCluster(
        key_range=(0, 100000),
        split_threshold_bytes=2000,
        merge_threshold_bytes=400,
        pre_split_count=4,
    )

    print(f"  📊 Initial: {cluster.get_partition_count()} partitions")

    # Phase 1: Insert data (cause splits)
    print_section("📈 Phase 1: Inserting Data (Splits)")
    keys_inserted = []
    for i in range(150):
        key = random.randint(0, 99999)
        keys_inserted.append(key)
        value = {"id": i, "data": f"value_{i}" * 3}
        cluster.write(key, value)

        if i % 30 == 0 and i > 0:
            print(f"  After {i:3d} inserts: {cluster.get_partition_count()} partitions, "
                  f"{cluster.get_total_size():,} bytes")

    print(f"\n  ✅ After inserts: {cluster.get_partition_count()} partitions")
    print(f"     Split history: {len(cluster.split_history)} splits")

    # Phase 2: Delete data (cause merges)
    print_section("📉 Phase 2: Deleting Data (Merges)")
    for i, key in enumerate(keys_inserted[:100]):
        cluster.delete(key)

        if i % 20 == 0 and i > 0:
            print(f"  After {i:3d} deletes: {cluster.get_partition_count()} partitions, "
                  f"{cluster.get_total_size():,} bytes")

    print(f"\n  ✅ After deletes: {cluster.get_partition_count()} partitions")
    print(f"     Merge history: {len(cluster.merge_history)} merges")

    print("""
  💡 KEY INSIGHT (DDIA):
     Dynamic partitioning automatically adapts to data growth.
     The number of partitions is proportional to dataset size.
    """)


def demo_4_partition_boundaries():
    """
    Demo 4: Show how partition boundaries change.

    DDIA concept: "Unlike fixed partitions, boundaries change
    dynamically as partitions split and merge."
    """
    print_header("DEMO 4: Partition Boundaries Change Dynamically")
    print("""
    We'll track how partition boundaries evolve as we insert data.
    """)

    cluster = DynamicCluster(
        key_range=(0, 1000),
        split_threshold_bytes=1500,
        pre_split_count=2,
    )

    print_section("Initial Partition Boundaries")
    for p_id, key_range, size in cluster.get_partition_sizes():
        print(f"  Partition {p_id}: keys {key_range[0]:4d}-{key_range[1]:4d}, {size:5d} bytes")

    # Insert data
    print_section("Inserting Data...")
    for i in range(80):
        key = random.randint(0, 999)
        value = {"id": i, "data": f"value_{i}" * 2}
        cluster.write(key, value)

    print_section("Partition Boundaries After Splits")
    for p_id, key_range, size in cluster.get_partition_sizes():
        print(f"  Partition {p_id}: keys {key_range[0]:4d}-{key_range[1]:4d}, {size:5d} bytes")

    print(f"\n  Total partitions: {cluster.get_partition_count()}")
    print(f"  Total splits: {len(cluster.split_history)}")

    print("""
  💡 KEY INSIGHT (DDIA):
     Partition boundaries are NOT fixed. They change as data
     is inserted and deleted. This is the key difference from
     fixed partitioning.

     Trade-offs:
       ✅ Automatic adaptation to data growth
       ✅ No need to guess partition count upfront
       ❌ More complex to implement
       ❌ Partition boundaries change (harder to reason about)
    """)


def demo_5_comparison_with_fixed():
    """
    Demo 5: Compare dynamic vs fixed partitioning.

    DDIA concept: "Dynamic partitioning works well with key-range
    partitioning. Fixed partitioning is simpler but requires upfront
    planning."
    """
    print_header("DEMO 5: Dynamic vs Fixed Partitioning")
    print("""
    Comparison of the two strategies.
    """)

    print_section("Scenario: Growing Dataset")
    print("""
    Starting with 1GB of data, growing to 10GB over time.
    """)

    print(f"\n  {'Aspect':<30} {'Dynamic':<25} {'Fixed'}")
    print(f"  {'─'*80}")
    print(f"  {'Initial partitions':<30} {'1 (cold-start)':<25} {'100 (pre-planned)'}")
    print(f"  {'Partition boundaries':<30} {'Change dynamically':<25} {'Fixed forever'}")
    print(f"  {'Rebalancing':<30} {'Automatic (split/merge)':<25} {'Manual (reassign)'}")
    print(f"  {'Upfront planning':<30} {'None':<25} {'Guess partition count'}")
    print(f"  {'Complexity':<30} {'Higher':<25} {'Lower'}")
    print(f"  {'Best for':<30} {'Unknown growth':<25} {'Predictable growth'}")

    print("""
  💡 DDIA GUIDANCE:
     Use DYNAMIC partitioning when:
       • Dataset size is unpredictable
       • Using key-range partitioning
       • You can tolerate split/merge overhead

     Use FIXED partitioning when:
       • You can estimate dataset size
       • You want simplicity
       • You're using hash partitioning
    """)


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 80)
    print("  EXERCISE 2: DYNAMIC PARTITIONING — AUTOMATIC SPLIT AND MERGE")
    print("  DDIA Chapter 6: 'Rebalancing Partitions'")
    print("=" * 80)
    print("""
  This exercise demonstrates DYNAMIC PARTITIONING.
  Partitions automatically split when they grow and merge when
  they shrink. The number of partitions adapts to dataset size.
    """)

    demo_1_cold_start_problem()
    demo_2_presplitting()
    demo_3_split_and_merge()
    demo_4_partition_boundaries()
    demo_5_comparison_with_fixed()

    print("\n" + "=" * 80)
    print("  EXERCISE 2 COMPLETE ✅")
    print("=" * 80)
    print("""
  Key Takeaways:

  1. 🔄 Partition boundaries change dynamically (split/merge)
  2. 📊 Number of partitions adapts to dataset size
  3. ❄️  Cold-start problem: new DB starts with 1 partition
  4. 🔨 Pre-splitting: create initial partitions to avoid bottleneck
  5. 🎯 Works well with key-range partitioning
  6. ⚙️  More complex than fixed partitioning

  Next: Run 03_consistent_hashing.py to see per-node partitioning
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