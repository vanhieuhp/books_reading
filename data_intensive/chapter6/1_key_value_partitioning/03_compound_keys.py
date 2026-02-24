"""
Exercise 3: Compound Primary Keys (Cassandra-Style)

DDIA Reference: Chapter 6, "Hybrid Approach: Compound Primary Keys" (pp. 206-207)

This exercise demonstrates COMPOUND PRIMARY KEYS:
  - First column is HASHED (determines partition)
  - Remaining columns are SORTED within the partition (enables range queries)
  - Best of both worlds: load balancing + efficient range queries
  - Used by Cassandra, DynamoDB, and others

Key concepts:
  - PRIMARY KEY (user_id, timestamp)
  - user_id is hashed → determines which partition
  - timestamp is sorted within partition → efficient range queries
  - Can query "all events for user_42 from Jan 1-5" efficiently
  - Cannot query "all users' events from Jan 1-5" efficiently

Run: python 03_compound_keys.py
"""

import sys
import hashlib
from typing import Dict, List, Tuple, Any
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')


# =============================================================================
# HASH FUNCTION
# =============================================================================

def md5_hash(key: str) -> int:
    """Deterministic hash function."""
    hash_bytes = hashlib.md5(key.encode()).digest()
    return int.from_bytes(hash_bytes[:4], byteorder='big')


# =============================================================================
# CORE COMPONENTS: Partition, CompoundKeyStore
# =============================================================================

class SortedIndex:
    """A sorted index within a partition (like a B-tree or SSTable)."""

    def __init__(self):
        self.data: Dict[str, Any] = {}

    def insert(self, sort_key: str, value: Any):
        """Insert a value with a sort key."""
        self.data[sort_key] = value

    def range_query(self, start_key: str, end_key: str) -> List[Tuple[str, Any]]:
        """Efficient range query on sorted keys."""
        results = []
        for key in sorted(self.data.keys()):
            if start_key <= key < end_key:
                results.append((key, self.data[key]))
        return results

    def get_all(self) -> List[Tuple[str, Any]]:
        """Get all entries sorted by key."""
        return [(k, self.data[k]) for k in sorted(self.data.keys())]


class Partition:
    """A partition with a sorted index for the clustering key."""

    def __init__(self, partition_id: int, partition_key: str):
        self.partition_id = partition_id
        self.partition_key = partition_key  # The hashed key (e.g., user_id)
        self.sorted_index = SortedIndex()  # Sorted by clustering key (e.g., timestamp)
        self.write_count = 0
        self.read_count = 0

    def write(self, sort_key: str, value: Any):
        """Write a value with a sort key."""
        self.sorted_index.insert(sort_key, value)
        self.write_count += 1

    def range_query(self, start_key: str, end_key: str) -> List[Tuple[str, Any]]:
        """Efficient range query on the clustering key."""
        self.read_count += len(self.sorted_index.data)
        return self.sorted_index.range_query(start_key, end_key)

    def get_all(self) -> List[Tuple[str, Any]]:
        """Get all entries in sorted order."""
        return self.sorted_index.get_all()

    def __repr__(self):
        return f"Partition({self.partition_id}, key={self.partition_key}, size={len(self.sorted_index.data)})"


class CompoundKeyStore:
    """
    A key-value store using compound primary keys.

    PRIMARY KEY (partition_key, clustering_key)
      • partition_key: hashed to determine partition
      • clustering_key: sorted within partition
    """

    def __init__(self, num_partitions: int):
        self.num_partitions = num_partitions
        self.max_hash = 2**31
        self.partitions: Dict[int, Partition] = {}

    def _get_partition_id(self, partition_key: str) -> int:
        """Determine which partition owns this partition key."""
        hash_value = md5_hash(partition_key) % self.max_hash
        return (hash_value * self.num_partitions) // self.max_hash

    def _get_or_create_partition(self, partition_key: str) -> Partition:
        """Get or create a partition for this partition key."""
        partition_id = self._get_partition_id(partition_key)
        if partition_id not in self.partitions:
            self.partitions[partition_id] = Partition(partition_id, partition_key)
        return self.partitions[partition_id]

    def write(self, partition_key: str, clustering_key: str, value: Any) -> str:
        """
        Write a value with compound key.

        partition_key: determines which partition (hashed)
        clustering_key: determines position within partition (sorted)
        """
        partition = self._get_or_create_partition(partition_key)
        partition.write(clustering_key, value)
        return f"Partition {partition.partition_id}"

    def range_query_within_partition(self, partition_key: str, start_clustering: str, end_clustering: str) -> List[Tuple[str, Any]]:
        """
        Efficient range query WITHIN a single partition key.

        Example: "Get all events for user_42 from Jan 1-5"
        → Hash user_42 → go to one partition → do efficient range scan
        """
        partition = self._get_or_create_partition(partition_key)
        return partition.range_query(start_clustering, end_clustering)

    def range_query_across_partitions(self, start_clustering: str, end_clustering: str) -> List[Tuple[str, Tuple[str, Any]]]:
        """
        Range query across ALL partitions (scatter/gather).

        Example: "Get all events from Jan 1-5 (any user)"
        → Must query ALL partitions
        → Slow!
        """
        results = []
        for partition in self.partitions.values():
            partition_results = partition.range_query(start_clustering, end_clustering)
            for clustering_key, value in partition_results:
                results.append((partition.partition_key, (clustering_key, value)))
        return sorted(results)

    def get_partition_stats(self) -> List[Dict]:
        """Get statistics for each partition."""
        stats = []
        for partition in sorted(self.partitions.values(), key=lambda p: p.partition_id):
            stats.append({
                "id": partition.partition_id,
                "key": partition.partition_key,
                "size": len(partition.sorted_index.data),
                "writes": partition.write_count,
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


def demo_1_compound_key_structure():
    """
    Demo 1: Show how compound keys work.

    DDIA concept: "A table can declare a compound primary key of several
    columns, e.g., PRIMARY KEY (user_id, timestamp)."
    """
    print_header("DEMO 1: Compound Primary Key Structure")
    print("""
    Cassandra uses compound primary keys:
      PRIMARY KEY (user_id, timestamp)

    • user_id is HASHED → determines partition
    • timestamp is SORTED within partition → enables range queries
    """)

    store = CompoundKeyStore(num_partitions=3)

    print("📊 Partition setup (3 partitions):")
    print("   Each partition stores data for one user_id")
    print("   Within each partition, data is sorted by timestamp")

    # Insert user activity data
    print("\n📝 Inserting user activity data:")

    activities = [
        ("user_42", "2024-01-01T10:00:00", "logged in"),
        ("user_42", "2024-01-02T14:30:00", "updated profile"),
        ("user_42", "2024-01-03T09:15:00", "posted comment"),
        ("user_42", "2024-01-04T16:45:00", "logged out"),
        ("user_99", "2024-01-01T11:00:00", "logged in"),
        ("user_99", "2024-01-02T15:30:00", "liked post"),
        ("user_99", "2024-01-03T10:15:00", "shared article"),
    ]

    for user_id, timestamp, action in activities:
        partition_info = store.write(user_id, timestamp, action)
        print(f"   {user_id} | {timestamp} | {action:20} → {partition_info}")

    # Show partition structure
    print_section("📊 Partition Structure")
    stats = store.get_partition_stats()
    for stat in stats:
        print(f"\n   Partition {stat['id']} (user_id={stat['key']}):")
        partition = store.partitions[stat['id']]
        for clustering_key, value in partition.get_all():
            print(f"     {clustering_key} → {value}")

    print("""
  💡 KEY INSIGHT (DDIA):
     Notice how data for each user is stored in ONE partition,
     and within that partition, data is sorted by timestamp.
     This enables efficient range queries!
    """)


def demo_2_efficient_within_partition_range_query():
    """
    Demo 2: Show efficient range queries within a partition.

    DDIA concept: "Query: 'Give me user_42's activity from Jan 1 to Jan 3'
    → Hash user_42 → go to one partition → do an efficient range scan. ✅ FAST!"
    """
    print_header("DEMO 2: Efficient Range Queries Within a Partition")
    print("""
    With compound keys, range queries WITHIN a partition are FAST.

    Query: "Get all events for user_42 from Jan 1-3"
    → Hash user_42 → go to ONE partition → efficient range scan
    """)

    store = CompoundKeyStore(num_partitions=3)

    # Insert data
    print("📝 Inserting user activity data:")
    activities = [
        ("user_42", "2024-01-01T10:00:00", "logged in"),
        ("user_42", "2024-01-02T14:30:00", "updated profile"),
        ("user_42", "2024-01-03T09:15:00", "posted comment"),
        ("user_42", "2024-01-04T16:45:00", "logged out"),
        ("user_42", "2024-01-05T11:20:00", "liked post"),
    ]

    for user_id, timestamp, action in activities:
        store.write(user_id, timestamp, action)
        print(f"   {timestamp} → {action}")

    # Perform range query
    print_section("🔍 Range Query: user_42 from Jan 1-3")
    print("   Query: SELECT * FROM events WHERE user_id='user_42' AND timestamp BETWEEN '2024-01-01' AND '2024-01-03'")

    results = store.range_query_within_partition(
        "user_42",
        "2024-01-01T00:00:00",
        "2024-01-03T23:59:59"
    )

    print(f"\n   ✅ Touched 1 partition (efficient!)")
    print(f"   Found {len(results)} results:")
    for timestamp, action in results:
        print(f"     {timestamp} → {action}")

    print("""
  💡 KEY INSIGHT (DDIA):
     This is FAST because:
     1. We hash user_42 → know exactly which partition
     2. Within that partition, data is sorted by timestamp
     3. We can do a binary search / range scan
     4. No need to touch other partitions!
    """)


def demo_3_inefficient_cross_partition_range_query():
    """
    Demo 3: Show inefficient range queries across partitions.

    DDIA concept: "Query: 'Give me ALL users' activity from Jan 1 to Jan 3'
    → You need to scatter/gather across ALL partitions. ❌ SLOW."
    """
    print_header("DEMO 3: Inefficient Range Queries Across Partitions")
    print("""
    Range queries that DON'T specify the partition key are SLOW.

    Query: "Get all events from Jan 1-3 (any user)"
    → Must query ALL partitions (scatter/gather)
    """)

    store = CompoundKeyStore(num_partitions=3)

    # Insert data from multiple users
    print("📝 Inserting user activity data:")
    activities = [
        ("user_42", "2024-01-01T10:00:00", "logged in"),
        ("user_42", "2024-01-02T14:30:00", "updated profile"),
        ("user_99", "2024-01-01T11:00:00", "logged in"),
        ("user_99", "2024-01-02T15:30:00", "liked post"),
        ("user_77", "2024-01-01T09:00:00", "posted comment"),
        ("user_77", "2024-01-03T10:15:00", "shared article"),
    ]

    for user_id, timestamp, action in activities:
        store.write(user_id, timestamp, action)

    # Perform cross-partition range query
    print_section("🔍 Range Query: All events from Jan 1-3 (any user)")
    print("   Query: SELECT * FROM events WHERE timestamp BETWEEN '2024-01-01' AND '2024-01-03'")

    results = store.range_query_across_partitions(
        "2024-01-01T00:00:00",
        "2024-01-03T23:59:59"
    )

    print(f"\n   ⚠️  Touched {len(store.partitions)} partitions (inefficient!)")
    print(f"   Found {len(results)} results:")
    for user_id, (timestamp, action) in results:
        print(f"     {user_id} | {timestamp} → {action}")

    print("""
  💡 KEY INSIGHT (DDIA):
     This is SLOW because:
     1. We don't know which partitions contain the data
     2. We must query ALL partitions
     3. We wait for the slowest partition (tail latency)
     4. Network overhead increases with more partitions

     This is why compound keys are designed for queries that
     specify the partition key!
    """)


def demo_4_real_world_example_social_media():
    """
    Demo 4: Real-world example - social media feed.

    DDIA concept: "This pattern is extremely powerful for social media
    feeds, IoT sensor data, and time-series workloads."
    """
    print_header("DEMO 4: Real-World Example - Social Media Feed")
    print("""
    Cassandra uses compound keys for social media feeds:
      PRIMARY KEY (user_id, timestamp)

    This enables:
    ✅ Fast: "Get my feed from the last 24 hours"
    ✅ Fast: "Get my feed from Jan 1-5"
    ❌ Slow: "Get all posts from Jan 1-5 (any user)"
    """)

    store = CompoundKeyStore(num_partitions=4)

    print("📝 Inserting social media feed data:")

    feed_data = [
        ("alice", "2024-01-05T10:00:00", "Posted: 'Beautiful sunset!'"),
        ("alice", "2024-01-05T14:30:00", "Liked: Bob's photo"),
        ("alice", "2024-01-05T18:45:00", "Commented: 'Great article!'"),
        ("bob", "2024-01-05T09:00:00", "Posted: 'Coffee time ☕'"),
        ("bob", "2024-01-05T15:30:00", "Shared: News article"),
        ("charlie", "2024-01-05T11:00:00", "Posted: 'Gym day 💪'"),
        ("charlie", "2024-01-05T19:15:00", "Liked: Alice's post"),
    ]

    for user_id, timestamp, action in feed_data:
        store.write(user_id, timestamp, action)

    # Query: Get Alice's feed for today
    print_section("🔍 Query 1: Get Alice's feed for today")
    print("   SELECT * FROM feed WHERE user_id='alice' AND timestamp >= '2024-01-05T00:00:00'")

    alice_feed = store.range_query_within_partition(
        "alice",
        "2024-01-05T00:00:00",
        "2024-01-05T23:59:59"
    )

    print(f"\n   ✅ Fast! (1 partition touched)")
    print(f"   Alice's feed ({len(alice_feed)} items):")
    for timestamp, action in alice_feed:
        print(f"     {timestamp} → {action}")

    # Query: Get all posts from today (any user)
    print_section("🔍 Query 2: Get all posts from today (any user)")
    print("   SELECT * FROM feed WHERE timestamp >= '2024-01-05T00:00:00'")

    all_posts = store.range_query_across_partitions(
        "2024-01-05T00:00:00",
        "2024-01-05T23:59:59"
    )

    print(f"\n   ⚠️  Slow! ({len(store.partitions)} partitions touched)")
    print(f"   All posts ({len(all_posts)} items):")
    for user_id, (timestamp, action) in all_posts:
        print(f"     {user_id} | {timestamp} → {action}")

    print("""
  💡 KEY INSIGHT (DDIA):
     Compound keys are designed for the common case:
     "Get my data from a time range"

     They're NOT designed for:
     "Get all data from a time range (any user)"

     This is a fundamental trade-off in distributed systems!
    """)


def demo_5_comparison_with_other_approaches():
    """
    Demo 5: Compare compound keys with other partitioning strategies.
    """
    print_header("DEMO 5: Comparison - Compound Keys vs Other Approaches")
    print("""
    Let's compare three partitioning strategies for time-series data:
    """)

    print("""
    ┌─────────────────────────────────────────────────────────────────┐
    │ Strategy 1: Range Partitioning (by timestamp)                   │
    ├─────────────────────────────────────────────────────────────────┤
    │ PRIMARY KEY: timestamp                                          │
    │                                                                 │
    │ ✅ Range queries by time: FAST (1 partition)                    │
    │ ❌ Hot spot: All writes for "now" go to 1 partition             │
    │ ❌ User-specific queries: SLOW (all partitions)                 │
    └─────────────────────────────────────────────────────────────────┘

    ┌─────────────────────────────────────────────────────────────────┐
    │ Strategy 2: Hash Partitioning (by user_id)                      │
    ├─────────────────────────────────────────────────────────────────┤
    │ PRIMARY KEY: user_id                                            │
    │                                                                 │
    │ ✅ No hot spots: Writes spread evenly                           │
    │ ✅ User-specific queries: FAST (1 partition)                    │
    │ ❌ Range queries by time: SLOW (all partitions)                 │
    └─────────────────────────────────────────────────────────────────┘

    ┌─────────────────────────────────────────────────────────────────┐
    │ Strategy 3: Compound Keys (user_id HASHED, timestamp SORTED)    │
    ├─────────────────────────────────────────────────────────────────┤
    │ PRIMARY KEY (user_id, timestamp)                                │
    │                                                                 │
    │ ✅ No hot spots: Writes spread evenly (hashed user_id)          │
    │ ✅ User-specific range queries: FAST (1 partition)              │
    │ ❌ Global range queries: SLOW (all partitions)                  │
    │                                                                 │
    │ BEST FOR: Social media, IoT sensors, time-series data           │
    └─────────────────────────────────────────────────────────────────┘
    """)

    print("""
  💡 KEY INSIGHT (DDIA):
     Compound keys are a brilliant compromise:
     • Get load balancing from hashing (no hot spots)
     • Get efficient range queries from sorting (within partition)
     • Perfect for the common case: "my data from a time range"
    """)


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 80)
    print("  EXERCISE 3: COMPOUND PRIMARY KEYS")
    print("  DDIA Chapter 6: 'Hybrid Approach: Compound Primary Keys'")
    print("=" * 80)
    print("""
  This exercise demonstrates COMPOUND PRIMARY KEYS:
  - First column is HASHED (determines partition)
  - Remaining columns are SORTED (enables range queries)
  - Best of both worlds: load balancing + efficient range queries
    """)

    demo_1_compound_key_structure()
    demo_2_efficient_within_partition_range_query()
    demo_3_inefficient_cross_partition_range_query()
    demo_4_real_world_example_social_media()
    demo_5_comparison_with_other_approaches()

    print("\n" + "=" * 80)
    print("  EXERCISE 3 COMPLETE ✅")
    print("=" * 80)
    print("""
  Key Takeaways:

  1. 🔑 Compound keys: first part hashed, remaining parts sorted
  2. ⚖️  Get load balancing from hashing (no hot spots)
  3. 🔍 Get efficient range queries from sorting (within partition)
  4. 📱 Perfect for social media feeds, IoT sensors, time-series data
  5. ⚠️  Trade-off: cross-partition range queries are still slow

  Next: Run 04_hot_spot_solutions.py to learn about handling skewed workloads
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
