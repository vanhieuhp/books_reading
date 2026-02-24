"""
Exercise 4: Handling Skewed Workloads and Hot Spots

DDIA Reference: Chapter 6, "Handling Skewed Workloads and Hot Spots" (pp. 207-209)

This exercise demonstrates how to handle the "celebrity problem":
  - Millions of requests target the same key (e.g., viral post)
  - Even with hash partitioning, that key maps to ONE partition
  - That partition becomes a hot spot
  - Solution: Application-level key splitting

Key concepts:
  - Hot spots are unavoidable in some cases
  - Databases can't automatically fix this
  - Application must detect hot keys and split them
  - Trade-off: Reads must query multiple split keys and merge

Run: python 04_hot_spot_solutions.py
"""

import sys
import hashlib
import random
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
# CORE COMPONENTS: Partition, HotSpotStore
# =============================================================================

class Partition:
    """A single partition."""

    def __init__(self, partition_id: int):
        self.partition_id = partition_id
        self.data: Dict[str, Any] = {}
        self.write_count = 0
        self.read_count = 0

    def write(self, key: str, value: Any):
        """Write a key-value pair."""
        self.data[key] = value
        self.write_count += 1

    def read(self, key: str) -> Tuple[bool, Any]:
        """Read a key-value pair."""
        self.read_count += 1
        return True, self.data.get(key)

    def get_load(self) -> int:
        """Return the load on this partition."""
        return self.write_count + self.read_count

    def __repr__(self):
        return f"Partition({self.partition_id}, size={len(self.data)})"


class HotSpotStore:
    """A key-value store that can handle hot spots via key splitting."""

    def __init__(self, num_partitions: int):
        self.num_partitions = num_partitions
        self.max_hash = 2**31
        self.partitions = [Partition(i) for i in range(num_partitions)]
        self.split_keys: Dict[str, int] = {}  # key -> number of splits

    def _find_partition(self, key: str) -> Partition:
        """Find which partition owns this key."""
        hash_value = md5_hash(key) % self.max_hash
        partition_id = (hash_value * self.num_partitions) // self.max_hash
        return self.partitions[partition_id]

    def write(self, key: str, value: Any) -> Tuple[str, int]:
        """Write a key-value pair. Returns (partition_info, load)."""
        partition = self._find_partition(key)
        partition.write(key, value)
        return f"Partition {partition.partition_id}", partition.get_load()

    def read(self, key: str) -> Tuple[bool, Any]:
        """Read a key-value pair."""
        partition = self._find_partition(key)
        return partition.read(key)

    def split_hot_key(self, key: str, num_splits: int):
        """
        Split a hot key into multiple keys.

        Instead of writing to "post_8932", write to:
        "post_8932_00", "post_8932_01", ..., "post_8932_99"
        """
        self.split_keys[key] = num_splits

    def write_with_splitting(self, key: str, value: Any) -> Tuple[List[str], List[int]]:
        """
        Write a key-value pair, applying splitting if the key is hot.

        Returns (partition_infos, loads)
        """
        if key in self.split_keys:
            # Write to a random split key
            num_splits = self.split_keys[key]
            split_suffix = random.randint(0, num_splits - 1)
            split_key = f"{key}_{split_suffix:02d}"
            partition = self._find_partition(split_key)
            partition.write(split_key, value)
            return [f"Partition {partition.partition_id}"], [partition.get_load()]
        else:
            # Write normally
            partition = self._find_partition(key)
            partition.write(key, value)
            return [f"Partition {partition.partition_id}"], [partition.get_load()]

    def read_with_splitting(self, key: str) -> List[Tuple[bool, Any]]:
        """
        Read a key-value pair, handling splitting if the key is hot.

        If the key is split, query all split keys and merge results.
        """
        if key in self.split_keys:
            # Query all split keys
            num_splits = self.split_keys[key]
            results = []
            for i in range(num_splits):
                split_key = f"{key}_{i:02d}"
                partition = self._find_partition(split_key)
                found, value = partition.read(split_key)
                if found:
                    results.append((found, value))
            return results
        else:
            # Read normally
            partition = self._find_partition(key)
            return [partition.read(key)]

    def get_partition_stats(self) -> List[Dict]:
        """Get statistics for each partition."""
        stats = []
        for p in self.partitions:
            stats.append({
                "id": p.partition_id,
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


def demo_1_celebrity_problem():
    """
    Demo 1: Show the celebrity problem (hot spot).

    DDIA concept: "Hashing evenly distributes keys, but what if millions
    of requests all target the exact same key?"
    """
    print_header("DEMO 1: The Celebrity Problem")
    print("""
    A viral post gets millions of reads/writes.
    Even with hash partitioning, that post maps to ONE partition.
    That partition becomes a HOT SPOT.
    """)

    store = HotSpotStore(num_partitions=4)

    print("📊 Partition setup (4 partitions):")
    for p in store.partitions:
        print(f"   {p}")

    # Simulate normal posts
    print("\n📝 Simulating normal posts (100 writes each):")
    normal_posts = ["post_1001", "post_1002", "post_1003", "post_1004"]
    for post_id in normal_posts:
        for i in range(100):
            store.write(post_id, {"likes": i})

    # Simulate viral post (1000 writes)
    print("📝 Simulating viral post (1000 writes):")
    viral_post = "post_8932"
    for i in range(1000):
        store.write(viral_post, {"likes": i})

    # Show the hot spot
    print_section("📊 Partition Load (Hot Spot!)")
    stats = store.get_partition_stats()
    for stat in stats:
        bar = "█" * (stat["writes"] // 50)  # Scale for display
        print(f"   Partition {stat['id']}: {stat['writes']:4d} writes {bar}")

    # Find which partition has the viral post
    viral_partition = store._find_partition(viral_post)
    total_writes = sum(s["writes"] for s in stats)
    viral_writes = viral_partition.write_count
    print(f"\n   Viral post partition: {viral_writes}/{total_writes} writes ({100*viral_writes/total_writes:.0f}%)")
    print(f"   ⚠️  HOT SPOT: One partition handles most of the load!")

    print("""
  💡 KEY INSIGHT (DDIA):
     "Today, most data systems are not able to automatically compensate
     for such a highly skewed workload, so it's the responsibility of
     the application to reduce the skew."

     The database can't fix this automatically. The application must
     detect hot keys and handle them specially.
    """)


def demo_2_key_splitting_solution():
    """
    Demo 2: Show how to fix hot spots with key splitting.

    DDIA concept: "Append a random number (e.g., 00-99) to the hot key:
    Instead of writing to 'post_8932', write to one of:
    'post_8932_00', 'post_8932_01', ..., 'post_8932_99'"
    """
    print_header("DEMO 2: Key Splitting Solution")
    print("""
    Fix: Split the hot key into multiple keys.

    Instead of:  "post_8932"
    Write to:    "post_8932_00", "post_8932_01", ..., "post_8932_99"

    This spreads the load across multiple partitions!
    """)

    store = HotSpotStore(num_partitions=4)

    print("📊 Partition setup (4 partitions):")
    for p in store.partitions:
        print(f"   {p}")

    # Mark the viral post as hot
    print("\n🔥 Marking post_8932 as hot (split into 100 keys):")
    store.split_keys["post_8932"] = 100

    # Simulate normal posts
    print("\n📝 Simulating normal posts (100 writes each):")
    normal_posts = ["post_1001", "post_1002", "post_1003", "post_1004"]
    for post_id in normal_posts:
        for i in range(100):
            store.write_with_splitting(post_id, {"likes": i})

    # Simulate viral post with splitting (1000 writes)
    print("📝 Simulating viral post with splitting (1000 writes):")
    viral_post = "post_8932"
    for i in range(1000):
        store.write_with_splitting(viral_post, {"likes": i})

    # Show the balanced load
    print_section("📊 Partition Load (Balanced!)")
    stats = store.get_partition_stats()
    for stat in stats:
        bar = "█" * (stat["writes"] // 50)  # Scale for display
        print(f"   Partition {stat['id']}: {stat['writes']:4d} writes {bar}")

    total_writes = sum(s["writes"] for s in stats)
    max_writes = max(s["writes"] for s in stats)
    print(f"\n   Max partition load: {max_writes}/{total_writes} writes ({100*max_writes/total_writes:.0f}%)")
    print(f"   ✅ Load is now balanced!")

    print("""
  💡 KEY INSIGHT (DDIA):
     By splitting the hot key into 100 keys, the load is spread
     across multiple partitions. The hot spot is eliminated!

     Trade-off: Reading the viral post now requires querying all
     100 split keys and merging the results.
    """)


def demo_3_read_write_trade_off():
    """
    Demo 3: Show the read/write trade-off with key splitting.

    DDIA concept: "Reading data for post_8932 now requires querying
    all 100 split keys from their respective partitions and merging
    the results."
    """
    print_header("DEMO 3: Read/Write Trade-Off")
    print("""
    Key splitting has a trade-off:

    ✅ WRITES: Spread across multiple partitions (fast)
    ❌ READS: Must query all split keys and merge (slow)
    """)

    store = HotSpotStore(num_partitions=4)

    # Mark the viral post as hot
    store.split_keys["post_8932"] = 100

    # Write some data
    print("📝 Writing 1000 likes to post_8932 (with splitting):")
    for i in range(1000):
        store.write_with_splitting("post_8932", {"like_id": i})

    # Read the data
    print_section("📖 Reading post_8932 (with splitting)")
    print("   Query: SELECT * FROM posts WHERE post_id='post_8932'")

    results = store.read_with_splitting("post_8932")

    print(f"\n   ⚠️  Had to query 100 split keys!")
    print(f"   Found {len(results)} results")

    print("""
  💡 KEY INSIGHT (DDIA):
     This is the fundamental trade-off:

     ✅ Without splitting:
        • Writes: Fast (1 partition)
        • Reads: Fast (1 partition)
        • Problem: Hot spot!

     ❌ With splitting:
        • Writes: Fast (spread across partitions)
        • Reads: Slow (query all split keys)
        • Benefit: No hot spot!

     You should only apply splitting for keys you KNOW are hot.
     For the vast majority of keys with normal traffic, the overhead
     of splitting and merging is not worth it.
    """)


def demo_4_selective_splitting():
    """
    Demo 4: Show selective key splitting (only for hot keys).

    DDIA concept: "You should only apply this for keys you know are hot
    (e.g., you bookkeep a list of currently-trending post IDs)."
    """
    print_header("DEMO 4: Selective Key Splitting")
    print("""
    In practice, you only split keys that are KNOWN to be hot.

    Example: Track trending posts and split only those.
    """)

    store = HotSpotStore(num_partitions=4)

    print("📊 Partition setup (4 partitions):")
    for p in store.partitions:
        print(f"   {p}")

    # Simulate normal posts
    print("\n📝 Simulating normal posts (100 writes each):")
    normal_posts = ["post_1001", "post_1002", "post_1003", "post_1004"]
    for post_id in normal_posts:
        for i in range(100):
            store.write_with_splitting(post_id, {"likes": i})

    # Detect hot posts (e.g., posts with > 500 writes)
    print("\n🔍 Detecting hot posts (> 500 writes):")
    stats = store.get_partition_stats()
    hot_threshold = 500

    # Simulate detecting post_8932 as hot
    print("   Detected: post_8932 is trending!")
    store.split_keys["post_8932"] = 100

    # Now write to the hot post with splitting
    print("\n📝 Simulating viral post with splitting (1000 writes):")
    viral_post = "post_8932"
    for i in range(1000):
        store.write_with_splitting(viral_post, {"likes": i})

    # Show the result
    print_section("📊 Final Partition Load")
    stats = store.get_partition_stats()
    for stat in stats:
        bar = "█" * (stat["writes"] // 50)
        print(f"   Partition {stat['id']}: {stat['writes']:4d} writes {bar}")

    print("""
  💡 KEY INSIGHT (DDIA):
     In real systems:
     1. Monitor partition load
     2. Detect hot keys (e.g., posts with > 500 writes)
     3. Add those keys to a "hot key list"
     4. Apply splitting only to keys in the list
     5. Remove from list when they cool down

     This way, most keys have fast reads, and only hot keys
     have the read overhead.
    """)


def demo_5_real_world_example():
    """
    Demo 5: Real-world example - social media platform.
    """
    print_header("DEMO 5: Real-World Example - Social Media Platform")
    print("""
    Scenario: A social media platform with millions of users.

    Normal posts: ~100 likes/comments per day
    Viral posts: ~100,000 likes/comments per day

    Without splitting: Viral posts create hot spots
    With splitting: Load is balanced
    """)

    store = HotSpotStore(num_partitions=8)

    print("📊 Partition setup (8 partitions):")
    print("   (Simulating a real cluster)")

    # Simulate normal posts
    print("\n📝 Simulating 1000 normal posts (100 writes each):")
    for post_num in range(1000):
        post_id = f"post_{post_num}"
        for i in range(100):
            store.write_with_splitting(post_id, {"like_id": i})

    # Detect viral posts
    print("\n🔥 Detecting viral posts (trending):")
    viral_posts = ["post_42", "post_123", "post_999"]
    for post_id in viral_posts:
        store.split_keys[post_id] = 100
        print(f"   {post_id} is trending! Splitting into 100 keys.")

    # Simulate viral posts
    print("\n📝 Simulating viral posts (1000 writes each):")
    for post_id in viral_posts:
        for i in range(1000):
            store.write_with_splitting(post_id, {"like_id": i})

    # Show the result
    print_section("📊 Final Partition Load")
    stats = store.get_partition_stats()
    total_writes = sum(s["writes"] for s in stats)
    for stat in stats:
        bar = "█" * (stat["writes"] // 100)
        percentage = 100 * stat["writes"] / total_writes
        print(f"   Partition {stat['id']}: {stat['writes']:5d} writes ({percentage:5.1f}%) {bar}")

    max_load = max(s["writes"] for s in stats)
    min_load = min(s["writes"] for s in stats)
    print(f"\n   Load balance: {min_load}-{max_load} writes per partition")
    print(f"   ✅ Reasonably balanced despite viral posts!")

    print("""
  💡 KEY INSIGHT (DDIA):
     In production systems:
     • Monitor which posts are trending
     • Dynamically split hot keys
     • Remove splitting when posts cool down
     • This keeps the system balanced without manual intervention
    """)


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 80)
    print("  EXERCISE 4: HANDLING SKEWED WORKLOADS AND HOT SPOTS")
    print("  DDIA Chapter 6: 'Handling Skewed Workloads and Hot Spots'")
    print("=" * 80)
    print("""
  This exercise demonstrates how to handle the "celebrity problem":
  - Millions of requests target the same key
  - Even with hash partitioning, that key maps to ONE partition
  - Solution: Application-level key splitting
    """)

    demo_1_celebrity_problem()
    demo_2_key_splitting_solution()
    demo_3_read_write_trade_off()
    demo_4_selective_splitting()
    demo_5_real_world_example()

    print("\n" + "=" * 80)
    print("  EXERCISE 4 COMPLETE ✅")
    print("=" * 80)
    print("""
  Key Takeaways:

  1. 🎬 Hot spots occur when millions of requests target one key
  2. 🔐 Databases can't fix this automatically
  3. 🔧 Solution: Application-level key splitting
  4. ⚖️  Trade-off: Fast writes, slower reads
  5. 🎯 Only split keys you KNOW are hot

  Next: Run 05_secondary_indexes.py to learn about partitioning secondary indexes
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
