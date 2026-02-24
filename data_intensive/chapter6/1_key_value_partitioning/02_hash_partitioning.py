"""
Exercise 2: Hash Partitioning

DDIA Reference: Chapter 6, "Partitioning by Hash of Key" (pp. 203-206)

This exercise demonstrates HASH PARTITIONING:
  - Use a hash function to scramble keys before assigning to partitions
  - Good hash function distributes skewed data uniformly
  - Eliminates hot spots for typical workloads
  - Trade-off: Range queries become inefficient (must query all partitions)

Key concepts:
  - Hash function must be deterministic (MD5, MurmurHash, xxHash)
  - NOT Python's hash() or Java's hashCode() (non-deterministic)
  - Excellent for load balancing
  - Terrible for range queries
  - Real users: Cassandra, Riak, Voldemort, Redis Cluster, DynamoDB

Run: python 02_hash_partitioning.py
"""

import sys
import hashlib
from typing import Dict, List, Tuple, Any

sys.stdout.reconfigure(encoding='utf-8')


# =============================================================================
# HASH FUNCTIONS
# =============================================================================

def md5_hash(key: str) -> int:
    """
    MD5-based hash function (deterministic).

    DDIA note: "You should NOT use Java's Object.hashCode() or Python's hash()
    because they may give different results in different processes."
    """
    hash_bytes = hashlib.md5(key.encode()).digest()
    return int.from_bytes(hash_bytes[:4], byteorder='big')


def simple_hash(key: str) -> int:
    """Simple hash for demonstration (not production-grade)."""
    return sum(ord(c) for c in key) * 31


# =============================================================================
# CORE COMPONENTS: Partition, HashPartitionedStore
# =============================================================================

class Partition:
    """A single partition in a hash-partitioned store."""

    def __init__(self, partition_id: int, hash_range: Tuple[int, int]):
        self.partition_id = partition_id
        self.hash_range = hash_range  # (min_hash, max_hash)
        self.data: Dict[str, Any] = {}
        self.write_count = 0
        self.read_count = 0

    def contains_hash(self, hash_value: int) -> bool:
        """Check if this partition owns the hash value."""
        min_hash, max_hash = self.hash_range
        return min_hash <= hash_value < max_hash

    def write(self, key: str, value: Any) -> bool:
        """Write a key-value pair."""
        self.data[key] = value
        self.write_count += 1
        return True

    def read(self, key: str) -> Tuple[bool, Any]:
        """Read a key-value pair."""
        self.read_count += 1
        return True, self.data.get(key)

    def get_load(self) -> int:
        """Return the load on this partition."""
        return self.write_count + self.read_count

    def __repr__(self):
        return f"Partition({self.partition_id}, hash_range={self.hash_range}, size={len(self.data)})"


class HashPartitionedStore:
    """A key-value store using hash partitioning."""

    def __init__(self, num_partitions: int, hash_func=md5_hash):
        """
        Initialize with a number of partitions.

        The hash space is divided evenly among partitions.
        """
        self.num_partitions = num_partitions
        self.hash_func = hash_func
        self.max_hash = 2**31  # Hash range: 0 to 2^31

        # Create partitions with equal hash ranges
        partition_size = self.max_hash // num_partitions
        self.partitions = []
        for i in range(num_partitions):
            min_hash = i * partition_size
            max_hash = (i + 1) * partition_size if i < num_partitions - 1 else self.max_hash
            self.partitions.append(Partition(i, (min_hash, max_hash)))

    def _find_partition(self, key: str) -> Partition:
        """Find which partition owns this key."""
        hash_value = self.hash_func(key) % self.max_hash
        for partition in self.partitions:
            if partition.contains_hash(hash_value):
                return partition
        raise ValueError(f"No partition for key: {key}")

    def write(self, key: str, value: Any) -> Tuple[str, int]:
        """Write a key-value pair. Returns (partition_info, hash_value)."""
        hash_value = self.hash_func(key) % self.max_hash
        partition = self._find_partition(key)
        partition.write(key, value)
        return f"Partition {partition.partition_id}", hash_value

    def read(self, key: str) -> Tuple[bool, Any, str, int]:
        """Read a key-value pair. Returns (found, value, partition_info, hash_value)."""
        hash_value = self.hash_func(key) % self.max_hash
        partition = self._find_partition(key)
        found, value = partition.read(key)
        return found, value, f"Partition {partition.partition_id}", hash_value

    def range_query(self, start_key: str, end_key: str) -> List[Tuple[str, Any]]:
        """
        Range query across partitions.

        With hash partitioning, this requires querying ALL partitions
        because hashed keys are scattered randomly.
        """
        results = []
        for partition in self.partitions:
            for key, value in partition.data.items():
                if start_key <= key < end_key:
                    results.append((key, value))
        return sorted(results)

    def get_partition_stats(self) -> List[Dict]:
        """Get statistics for each partition."""
        stats = []
        for p in self.partitions:
            stats.append({
                "id": p.partition_id,
                "hash_range": p.hash_range,
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


def demo_1_hash_distribution():
    """
    Demo 1: Show how hash partitioning distributes keys uniformly.

    DDIA concept: "A good hash function takes skewed, clustered data
    and distributes it uniformly across an output range."
    """
    print_header("DEMO 1: Hash Distribution")
    print("""
    Hash partitioning uses a hash function to scramble keys before
    assigning them to partitions. This distributes even skewed data
    uniformly across partitions.
    """)

    store = HashPartitionedStore(num_partitions=4)

    print("🔢 Partition setup (4 partitions):")
    for p in store.partitions:
        print(f"   {p}")

    # Insert sequential user IDs (skewed data)
    print("\n📝 Inserting sequential user IDs (user_001, user_002, ...):")
    print("    (Sequential IDs are skewed, but hashing will distribute them)")

    for i in range(1, 13):
        key = f"user_{i:03d}"
        partition_info, hash_value = store.write(key, {"id": i})
        print(f"   {key} → hash={hash_value:10d} → {partition_info}")

    # Show balanced distribution
    print_section("📊 Partition Distribution (Balanced!)")
    stats = store.get_partition_stats()
    for stat in stats:
        bar = "█" * stat["size"]
        print(f"   Partition {stat['id']}: {stat['size']:2d} keys {bar}")

    print("""
  💡 KEY INSIGHT (DDIA):
     Even though user IDs are sequential (001, 002, 003, ...),
     their hash values are scattered across the partition space.
     This eliminates hot spots for typical workloads!
    """)


def demo_2_hash_vs_range_for_hot_spots():
    """
    Demo 2: Compare hash partitioning vs range partitioning for hot spots.

    DDIA concept: "Hash partitioning is excellent at eliminating hot spots
    for most workloads."
    """
    print_header("DEMO 2: Hash Partitioning Eliminates Hot Spots")
    print("""
    With time-series data, range partitioning creates hot spots.
    Hash partitioning spreads the load evenly.
    """)

    store = HashPartitionedStore(num_partitions=3)

    print("🔢 Partition setup (3 partitions):")
    for p in store.partitions:
        print(f"   {p}")

    # Simulate writes for "now" (all same timestamp)
    print("\n📝 Simulating writes for 2024-03-15 (all at same time):")

    sensors = ["sensor_1", "sensor_2", "sensor_3", "sensor_4", "sensor_5"]
    for sensor in sensors:
        key = f"{sensor}_2024-03-15T10:00:00"
        partition_info, hash_value = store.write(key, {"value": 72.5})
        print(f"   {key} → {partition_info}")

    # Show balanced load
    print_section("📊 Partition Load (Balanced!)")
    stats = store.get_partition_stats()
    for stat in stats:
        bar = "█" * stat["writes"]
        print(f"   Partition {stat['id']}: {stat['writes']:2d} writes {bar}")

    print("""
  💡 KEY INSIGHT (DDIA):
     Even though all writes are for the same timestamp, hash partitioning
     spreads them across multiple partitions. No hot spot!

     Compare this to range partitioning, where all writes for "now"
     would go to a single partition.
    """)


def demo_3_range_queries_are_slow():
    """
    Demo 3: Show that range queries are inefficient with hash partitioning.

    DDIA concept: "Range queries are impossible on the main key. Since
    hash('user_001') and hash('user_002') land on completely different
    partitions, a query like WHERE user_id BETWEEN 'user_001' AND 'user_100'
    must be sent to ALL partitions."
    """
    print_header("DEMO 3: Range Queries Are Inefficient")
    print("""
    With hash partitioning, range queries must be sent to ALL partitions
    because hashed keys are scattered randomly.
    """)

    store = HashPartitionedStore(num_partitions=4)

    print("🔢 Partition setup (4 partitions):")
    for p in store.partitions:
        print(f"   {p}")

    # Insert data
    print("\n📝 Inserting user data:")
    for i in range(1, 11):
        key = f"user_{i:02d}"
        store.write(key, {"name": f"User {i}"})
        print(f"   {key}")

    # Perform range query
    print_section("🔍 Range Query: user_01 to user_05")
    print("""
    With key range partitioning:
      → Only touch 1 partition (the one covering user_01-user_05)
      → Very fast!

    With hash partitioning:
      → Must query ALL 4 partitions
      → Slow! (scatter/gather)
    """)

    # Show which partitions are touched
    print("\n  Querying all partitions for keys in range [user_01, user_05):")
    results = store.range_query("user_01", "user_05")
    for key, value in results:
        print(f"    {key}: {value}")

    print(f"\n  ⚠️  Had to query ALL {store.num_partitions} partitions!")
    print(f"  ✅ Found {len(results)} results")

    print("""
  💡 KEY INSIGHT (DDIA):
     This is the fundamental trade-off:

     ✅ Hash partitioning: Excellent load balancing, eliminates hot spots
     ❌ Hash partitioning: Range queries are slow (must query all partitions)

     ✅ Range partitioning: Range queries are fast (touch few partitions)
     ❌ Range partitioning: Hot spots when writes cluster

     Choose based on your workload!
    """)


def demo_4_hash_function_matters():
    """
    Demo 4: Show why the hash function matters.

    DDIA concept: "You should NOT use Java's Object.hashCode() or Python's
    hash() because they may give different results in different processes."
    """
    print_header("DEMO 4: Hash Function Matters")
    print("""
    The hash function must be DETERMINISTIC and CONSISTENT across processes.
    Using Python's built-in hash() is a common mistake!
    """)

    print("\n❌ WRONG: Using Python's built-in hash()")
    print("   (Non-deterministic, different results in different processes)")

    # Show that Python's hash() is non-deterministic
    key = "user_123"
    print(f"\n   hash('{key}') in this process: {hash(key)}")
    print(f"   (If you run this again, you'll get a different value!)")

    print("\n✅ CORRECT: Using MD5 hash (deterministic)")
    print("   (Same result every time, across all processes)")

    store = HashPartitionedStore(num_partitions=4, hash_func=md5_hash)

    for i in range(1, 6):
        key = f"user_{i:03d}"
        partition_info, hash_value = store.write(key, {"id": i})
        print(f"   {key} → hash={hash_value:10d} (deterministic) → {partition_info}")

    print("""
  💡 KEY INSIGHT (DDIA):
     Real databases use deterministic hash functions:
       • MongoDB: MD5
       • Cassandra: Murmur3
       • Redis: CRC16
       • DynamoDB: MD5

     These functions don't need to be cryptographically strong—
     they just need to uniformly distribute data.
    """)


def demo_5_consistent_hashing():
    """
    Demo 5: Introduce consistent hashing (preview of rebalancing).

    DDIA concept: "The problem with hash(key) % N is that adding or
    removing a node causes massive data movement."
    """
    print_header("DEMO 5: The Problem with hash(key) % N")
    print("""
    A naive approach: hash(key) % number_of_nodes

    Problem: If you add or remove a node, almost every key moves!
    """)

    print("\n📊 Before adding a node (10 nodes):")
    print("   hash('alice') % 10 = 3  → Node 3")
    print("   hash('bob')   % 10 = 1  → Node 1")
    print("   hash('charlie') % 10 = 7  → Node 7")

    print("\n📊 After adding a node (11 nodes):")
    print("   hash('alice') % 11 = 7  → Node 7  💥 MOVED!")
    print("   hash('bob')   % 11 = 9  → Node 9  💥 MOVED!")
    print("   hash('charlie') % 11 = 4  → Node 4  💥 MOVED!")

    print("""
    ⚠️  Most keys moved! This causes massive network traffic.

    Solution: CONSISTENT HASHING (used by Cassandra, Riak, etc.)
      • Arrange nodes in a ring
      • Each key maps to the nearest node on the ring
      • Adding a node only affects keys "near" that node
      • Much less data movement!
    """)

    print("""
  💡 KEY INSIGHT (DDIA):
     This is why real distributed systems use consistent hashing
     instead of simple modulo. We'll see this in Chapter 6, Section 3
     (Rebalancing Partitions).
    """)


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 80)
    print("  EXERCISE 2: HASH PARTITIONING")
    print("  DDIA Chapter 6: 'Partitioning by Hash of Key'")
    print("=" * 80)
    print("""
  This exercise demonstrates HASH PARTITIONING:
  - Hash function scrambles keys before assigning to partitions
  - Excellent at eliminating hot spots
  - Trade-off: Range queries become inefficient
    """)

    demo_1_hash_distribution()
    demo_2_hash_vs_range_for_hot_spots()
    demo_3_range_queries_are_slow()
    demo_4_hash_function_matters()
    demo_5_consistent_hashing()

    print("\n" + "=" * 80)
    print("  EXERCISE 2 COMPLETE ✅")
    print("=" * 80)
    print("""
  Key Takeaways:

  1. 🔢 Hash function scrambles keys uniformly across partitions
  2. ⚖️  Excellent at eliminating hot spots
  3. 🔍 Range queries are slow (must query all partitions)
  4. 🔐 Hash function must be deterministic (MD5, MurmurHash, etc.)
  5. ⚠️  Simple hash(key) % N causes massive data movement on rebalancing

  Next: Run 03_compound_keys.py to learn about hybrid approaches
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
