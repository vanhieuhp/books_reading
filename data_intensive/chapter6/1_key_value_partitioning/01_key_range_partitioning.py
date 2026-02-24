"""
Exercise 1: Key Range Partitioning

DDIA Reference: Chapter 6, "Partitioning of Key-Value Data" (pp. 200-203)

This exercise demonstrates KEY RANGE PARTITIONING:
  - Assign a continuous range of keys to each partition
  - Like volumes of an encyclopedia: A-Ce, Ce-G, G-K, etc.
  - Keys within a partition are sorted (enables efficient range queries)
  - Trade-off: Hot spots when writes cluster in one range

Key concepts:
  - Range boundaries can be manually configured or auto-split
  - Efficient range queries (only touch relevant partitions)
  - Risk of hot spots (e.g., all writes for "now" go to one partition)
  - Real users: HBase, Bigtable, RethinkDB, MongoDB (before v2.4)

Run: python 01_key_range_partitioning.py
"""

import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')


# =============================================================================
# CORE COMPONENTS: Partition, PartitionedStore
# =============================================================================

class Partition:
    """A single partition holding a range of keys."""

    def __init__(self, partition_id: int, key_range: Tuple[str, str]):
        self.partition_id = partition_id
        self.key_range = key_range  # (min_key, max_key)
        self.data: Dict[str, Any] = {}
        self.write_count = 0
        self.read_count = 0

    def contains_key(self, key: str) -> bool:
        """Check if this partition owns the key."""
        min_key, max_key = self.key_range
        return min_key <= key < max_key

    def write(self, key: str, value: Any) -> bool:
        """Write a key-value pair. Returns True if successful."""
        if not self.contains_key(key):
            return False
        self.data[key] = value
        self.write_count += 1
        return True

    def read(self, key: str) -> Tuple[bool, Any]:
        """Read a key-value pair. Returns (found, value)."""
        if not self.contains_key(key):
            return False, None
        self.read_count += 1
        return True, self.data.get(key)

    def range_query(self, start_key: str, end_key: str) -> List[Tuple[str, Any]]:
        """Efficient range query within this partition."""
        results = []
        for key in sorted(self.data.keys()):
            if start_key <= key < end_key:
                results.append((key, self.data[key]))
        self.read_count += len(results)
        return results

    def get_load(self) -> int:
        """Return the load (write + read count) on this partition."""
        return self.write_count + self.read_count

    def __repr__(self):
        return f"Partition({self.partition_id}, range={self.key_range}, size={len(self.data)})"


class KeyRangePartitionedStore:
    """A key-value store using key range partitioning."""

    def __init__(self, partitions: List[Tuple[str, str]]):
        """
        Initialize with partition boundaries.

        Example: [("A", "H"), ("H", "P"), ("P", "Z")]
        """
        self.partitions = [
            Partition(i, range_tuple)
            for i, range_tuple in enumerate(partitions)
        ]

    def _find_partition(self, key: str) -> Partition:
        """Find which partition owns this key."""
        for partition in self.partitions:
            if partition.contains_key(key):
                return partition
        raise ValueError(f"No partition for key: {key}")

    def write(self, key: str, value: Any) -> str:
        """Write a key-value pair. Returns partition info."""
        partition = self._find_partition(key)
        partition.write(key, value)
        return f"Partition {partition.partition_id}"

    def read(self, key: str) -> Tuple[bool, Any, str]:
        """Read a key-value pair. Returns (found, value, partition_info)."""
        partition = self._find_partition(key)
        found, value = partition.read(key)
        return found, value, f"Partition {partition.partition_id}"

    def range_query(self, start_key: str, end_key: str) -> List[Tuple[str, Any]]:
        """
        Range query across partitions.

        Returns all keys in [start_key, end_key) from all relevant partitions.
        """
        results = []
        for partition in self.partitions:
            # Check if this partition overlaps with the query range
            p_min, p_max = partition.key_range
            if start_key < p_max and end_key > p_min:
                # Partition overlaps, query it
                partition_results = partition.range_query(start_key, end_key)
                results.extend(partition_results)
        return sorted(results)

    def get_partition_stats(self) -> List[Dict]:
        """Get statistics for each partition."""
        stats = []
        for p in self.partitions:
            stats.append({
                "id": p.partition_id,
                "range": p.key_range,
                "size": len(p.data),
                "writes": p.write_count,
                "reads": p.read_count,
                "load": p.get_load(),
            })
        return stats


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


def demo_1_basic_range_partitioning():
    """
    Demo 1: Show how key range partitioning works.

    DDIA concept: "Assign a continuous range of keys to each partition,
    similar to how volumes of a printed encyclopedia cover letters A–Ce, Ce–G, etc."
    """
    print_header("DEMO 1: Basic Key Range Partitioning")
    print("""
    This demonstrates how keys are assigned to partitions based on ranges.
    Think of it like encyclopedia volumes:
      Volume 1: A-H
      Volume 2: I-P
      Volume 3: Q-Z
    """)

    # Create a partitioned store with 3 partitions
    partitions = [("A", "H"), ("H", "P"), ("P", "Z")]
    store = KeyRangePartitionedStore(partitions)

    print("📚 Partition setup:")
    for p in store.partitions:
        print(f"   {p}")

    # Insert some data
    test_data = [
        ("Alice", {"age": 30, "city": "NYC"}),
        ("Bob", {"age": 25, "city": "LA"}),
        ("Charlie", {"age": 35, "city": "Chicago"}),
        ("Diana", {"age": 28, "city": "Boston"}),
        ("Eve", {"age": 32, "city": "Seattle"}),
        ("Frank", {"age": 29, "city": "Denver"}),
        ("Grace", {"age": 31, "city": "Austin"}),
        ("Henry", {"age": 26, "city": "Portland"}),
        ("Iris", {"age": 33, "city": "Miami"}),
        ("Jack", {"age": 27, "city": "Phoenix"}),
    ]

    print("\n📝 Inserting data:")
    for key, value in test_data:
        partition_info = store.write(key, value)
        print(f"   {key:10} → {partition_info}")

    # Show partition distribution
    print_section("📊 Partition Distribution")
    stats = store.get_partition_stats()
    for stat in stats:
        keys_in_partition = [k for k, _ in test_data if stat["range"][0] <= k < stat["range"][1]]
        print(f"   Partition {stat['id']} ({stat['range'][0]}-{stat['range'][1]}): "
              f"{stat['size']} keys → {keys_in_partition}")

    print("""
  💡 KEY INSIGHT (DDIA):
     Keys are sorted within each partition. This enables efficient
     range queries — you only need to touch the partitions that
     overlap with your query range.
    """)


def demo_2_efficient_range_queries():
    """
    Demo 2: Show how range queries are efficient with key range partitioning.

    DDIA concept: "A query like SELECT * FROM readings WHERE timestamp
    BETWEEN '2024-01-01' AND '2024-01-05' only needs to contact the one
    partition whose range covers that interval."
    """
    print_header("DEMO 2: Efficient Range Queries")
    print("""
    With key range partitioning, range queries are FAST because they
    only touch the partitions that overlap with the query range.
    """)

    # Create partitions for timestamps
    partitions = [
        ("2024-01-01", "2024-01-11"),
        ("2024-01-11", "2024-01-21"),
        ("2024-01-21", "2024-02-01"),
    ]
    store = KeyRangePartitionedStore(partitions)

    print("📅 Partition setup (by date):")
    for p in store.partitions:
        print(f"   {p}")

    # Insert sensor readings
    print("\n📝 Inserting sensor readings:")
    readings = [
        ("2024-01-05", {"sensor": "temp_1", "value": 72.5}),
        ("2024-01-08", {"sensor": "temp_2", "value": 71.2}),
        ("2024-01-15", {"sensor": "temp_1", "value": 73.1}),
        ("2024-01-18", {"sensor": "temp_2", "value": 70.8}),
        ("2024-01-25", {"sensor": "temp_1", "value": 74.3}),
        ("2024-01-28", {"sensor": "temp_2", "value": 72.0}),
    ]

    for key, value in readings:
        store.write(key, value)
        print(f"   {key}: {value}")

    # Perform range queries
    print_section("🔍 Range Queries")

    queries = [
        ("2024-01-01", "2024-01-10", "Early January"),
        ("2024-01-15", "2024-01-20", "Mid January"),
        ("2024-01-01", "2024-02-01", "All of January"),
    ]

    for start, end, description in queries:
        print(f"\n  Query: {description}")
        print(f"  Range: [{start}, {end})")

        # Count which partitions are touched
        touched_partitions = set()
        for partition in store.partitions:
            p_min, p_max = partition.key_range
            if start < p_max and end > p_min:
                touched_partitions.add(partition.partition_id)

        results = store.range_query(start, end)
        print(f"  Touched partitions: {sorted(touched_partitions)}")
        print(f"  Results ({len(results)} rows):")
        for key, value in results:
            print(f"    {key}: {value}")

    print("""
  💡 KEY INSIGHT (DDIA):
     Notice how range queries only touch the partitions that overlap
     with the query range. This is MUCH faster than hash partitioning,
     where you'd need to query ALL partitions.
    """)


def demo_3_hot_spot_problem():
    """
    Demo 3: Show the hot spot problem with time-series data.

    DDIA concept: "If your key is a timestamp, ALL writes for 'right now'
    go to one partition (the one whose range covers the current time),
    while all historical partitions sit idle. One node does all the work."
    """
    print_header("DEMO 3: The Hot Spot Problem")
    print("""
    With time-series data, all writes for "right now" go to the same
    partition, creating a HOT SPOT. Historical partitions sit idle.
    """)

    # Create partitions for months
    partitions = [
        ("2024-01", "2024-02"),
        ("2024-02", "2024-03"),
        ("2024-03", "2024-04"),
    ]
    store = KeyRangePartitionedStore(partitions)

    print("📅 Partition setup (by month):")
    for p in store.partitions:
        print(f"   {p}")

    # Simulate writes over time
    print("\n📝 Simulating writes (all for 'now' = 2024-03):")

    # All writes go to March partition
    for i in range(10):
        key = f"2024-03-15T{i:02d}:00:00"
        store.write(key, {"event": f"event_{i}"})

    # A few writes to other months
    store.write("2024-01-15T10:00:00", {"event": "old_event_1"})
    store.write("2024-02-15T10:00:00", {"event": "old_event_2"})

    # Show the imbalance
    print_section("📊 Partition Load (Hot Spot!)")
    stats = store.get_partition_stats()
    for stat in stats:
        bar = "█" * stat["writes"]
        print(f"   Partition {stat['id']} ({stat['range'][0]}-{stat['range'][1]}): "
              f"{stat['writes']:2d} writes {bar}")

    total_writes = sum(s["writes"] for s in stats)
    march_writes = stats[2]["writes"]
    print(f"\n   March partition: {march_writes}/{total_writes} writes ({100*march_writes/total_writes:.0f}%)")
    print(f"   ⚠️  HOT SPOT: One partition handles most of the load!")

    print("""
  💡 KEY INSIGHT (DDIA):
     This is the fundamental problem with time-series data and key range
     partitioning. All writes for "now" go to one partition, while
     historical partitions sit idle.

     Solution: Prefix the timestamp with another dimension (e.g., sensor_id)
     so writes are spread across multiple partitions.
    """)


def demo_4_fixing_hot_spot_with_prefix():
    """
    Demo 4: Show how to fix the hot spot by prefixing the key.

    DDIA concept: "The traditional fix is to prefix the timestamp with
    another dimension: Key = sensor_name + '_' + timestamp"
    """
    print_header("DEMO 4: Fixing Hot Spots with Key Prefixing")
    print("""
    Instead of using just timestamp as the key, prefix it with sensor_id.
    This spreads writes across multiple partitions.
    """)

    # Create partitions
    partitions = [
        ("sensor_1_2024-03", "sensor_2_2024-03"),
        ("sensor_2_2024-03", "sensor_3_2024-03"),
        ("sensor_3_2024-03", "sensor_4_2024-03"),
    ]
    store = KeyRangePartitionedStore(partitions)

    print("📅 Partition setup (by sensor + month):")
    for p in store.partitions:
        print(f"   {p}")

    # Simulate writes from multiple sensors at the same time
    print("\n📝 Simulating writes from multiple sensors (all at 2024-03-15):")

    sensors = ["sensor_1", "sensor_2", "sensor_3"]
    for sensor in sensors:
        for i in range(5):
            key = f"{sensor}_2024-03-15T{i:02d}:00:00"
            store.write(key, {"value": 72.5 + i})
            print(f"   {key}")

    # Show the balanced load
    print_section("📊 Partition Load (Balanced!)")
    stats = store.get_partition_stats()
    for stat in stats:
        bar = "█" * stat["writes"]
        print(f"   Partition {stat['id']}: {stat['writes']:2d} writes {bar}")

    print(f"\n   ✅ Load is now balanced across partitions!")

    print("""
  💡 KEY INSIGHT (DDIA):
     By prefixing the timestamp with sensor_id, writes are spread across
     multiple partitions. The trade-off is that range queries become more
     complex:

     ❌ OLD: "Get all sensors' readings from Jan 1-5" → one partition
     ✅ NEW: "Get all sensors' readings from Jan 1-5" → query all partitions

     But this is usually worth it to avoid the hot spot!
    """)


def demo_5_partition_rebalancing():
    """
    Demo 5: Show how partitions can be rebalanced when data grows unevenly.

    DDIA concept: "The range boundaries are not necessarily evenly spaced.
    If your data is not uniformly distributed, the boundaries must be
    chosen to equalize the data volume."
    """
    print_header("DEMO 5: Partition Rebalancing")
    print("""
    When data grows unevenly, partitions can become imbalanced.
    Rebalancing adjusts the boundaries to equalize data volume.
    """)

    # Start with even partitions
    partitions = [("A", "H"), ("H", "P"), ("P", "Z")]
    store = KeyRangePartitionedStore(partitions)

    print("📚 Initial partition setup:")
    for p in store.partitions:
        print(f"   {p}")

    # Insert data with skewed distribution
    print("\n📝 Inserting data (skewed toward A-H):")

    # Many writes to A-H
    for i in range(20):
        key = chr(ord('A') + (i % 7))  # A-G
        store.write(key, {"value": i})

    # Few writes to H-P
    for i in range(5):
        key = chr(ord('H') + (i % 8))  # H-O
        store.write(key, {"value": i})

    # Few writes to P-Z
    for i in range(3):
        key = chr(ord('P') + (i % 10))  # P-Y
        store.write(key, {"value": i})

    # Show imbalance
    print_section("📊 Before Rebalancing (Imbalanced)")
    stats = store.get_partition_stats()
    for stat in stats:
        bar = "█" * stat["size"]
        print(f"   Partition {stat['id']} ({stat['range'][0]}-{stat['range'][1]}): "
              f"{stat['size']:2d} keys {bar}")

    # Simulate rebalancing
    print_section("🔄 Rebalancing Partitions")
    print("""
    The system detects imbalance and adjusts boundaries:
      Old: ("A", "H"), ("H", "P"), ("P", "Z")
      New: ("A", "E"), ("E", "M"), ("M", "Z")
    """)

    # Create new partitions with adjusted boundaries
    new_partitions = [("A", "E"), ("E", "M"), ("M", "Z")]
    new_store = KeyRangePartitionedStore(new_partitions)

    # Copy data to new partitions
    for partition in store.partitions:
        for key, value in partition.data.items():
            new_store.write(key, value)

    # Show balance
    print_section("📊 After Rebalancing (Balanced)")
    new_stats = new_store.get_partition_stats()
    for stat in new_stats:
        bar = "█" * stat["size"]
        print(f"   Partition {stat['id']} ({stat['range'][0]}-{stat['range'][1]}): "
              f"{stat['size']:2d} keys {bar}")

    print("""
  💡 KEY INSIGHT (DDIA):
     Rebalancing is necessary when data distribution is skewed.
     The goal is to keep partitions roughly equal in size.

     In real systems:
       • HBase: Administrators manually configure split points
       • Bigtable: Google's system auto-splits regions
       • RethinkDB: Automatic rebalancing
    """)


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 80)
    print("  EXERCISE 1: KEY RANGE PARTITIONING")
    print("  DDIA Chapter 6: 'Partitioning of Key-Value Data'")
    print("=" * 80)
    print("""
  This exercise demonstrates KEY RANGE PARTITIONING:
  - Keys are assigned to partitions based on continuous ranges
  - Keys within a partition are sorted (enables efficient range queries)
  - Trade-off: Hot spots when writes cluster in one range
    """)

    demo_1_basic_range_partitioning()
    demo_2_efficient_range_queries()
    demo_3_hot_spot_problem()
    demo_4_fixing_hot_spot_with_prefix()
    demo_5_partition_rebalancing()

    print("\n" + "=" * 80)
    print("  EXERCISE 1 COMPLETE ✅")
    print("=" * 80)
    print("""
  Key Takeaways:

  1. 📚 Keys are assigned to partitions based on continuous ranges
  2. 🔍 Range queries are efficient (only touch relevant partitions)
  3. ⚠️  Hot spots occur when writes cluster in one range (e.g., "now")
  4. 🔧 Fix hot spots by prefixing keys with another dimension
  5. ⚖️  Rebalancing adjusts boundaries to equalize partition sizes

  Next: Run 02_hash_partitioning.py to learn about hash-based partitioning
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
