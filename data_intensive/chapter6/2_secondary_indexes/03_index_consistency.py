"""
Exercise 3: Index Consistency Trade-offs

DDIA Reference: Chapter 6, "Partitioning and Secondary Indexes" (pp. 214-217)

This exercise compares the consistency guarantees of LOCAL vs GLOBAL indexes.

Key concepts:
  - LOCAL indexes: immediately consistent (write to one partition)
  - GLOBAL indexes: eventually consistent (async updates)
  - Trade-off: consistency vs performance

Consistency models:
  - Strong consistency: all reads see latest writes
  - Eventual consistency: reads eventually see writes
  - Causal consistency: related operations are ordered

Real-world implications:
  - DynamoDB GSI: "eventually consistent" (may take seconds)
  - MongoDB local indexes: immediately consistent
  - Elasticsearch: eventually consistent (refresh interval)

Run: python 03_index_consistency.py
"""

import sys
import time
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
from enum import Enum

sys.stdout.reconfigure(encoding='utf-8')


# =============================================================================
# CONSISTENCY MODELS
# =============================================================================

class ConsistencyModel(Enum):
    STRONG = "strong"
    EVENTUAL = "eventual"
    CAUSAL = "causal"


# =============================================================================
# LOCAL INDEX IMPLEMENTATION (Immediately Consistent)
# =============================================================================

class LocalIndexPartition:
    """A partition with LOCAL secondary index (immediately consistent)."""

    def __init__(self, partition_id: int):
        self.partition_id = partition_id
        self.documents: Dict[str, Dict] = {}
        self.indexes: Dict[str, Dict] = defaultdict(lambda: defaultdict(set))

    def insert(self, doc_id: str, **attributes):
        """Insert a document (immediately consistent)."""
        self.documents[doc_id] = attributes.copy()
        for attr_name, attr_value in attributes.items():
            self.indexes[attr_name][attr_value].add(doc_id)

    def delete(self, doc_id: str):
        """Delete a document."""
        if doc_id in self.documents:
            attrs = self.documents.pop(doc_id)
            for attr_name, attr_value in attrs.items():
                self.indexes[attr_name][attr_value].discard(doc_id)

    def search(self, attribute: str, value) -> List[str]:
        """Search (immediately consistent)."""
        return list(self.indexes[attribute].get(value, set()))


class LocalIndexDatabase:
    """Database with LOCAL indexes (immediately consistent)."""

    def __init__(self, num_partitions: int):
        self.num_partitions = num_partitions
        self.partitions = [LocalIndexPartition(i) for i in range(num_partitions)]

    def _get_partition(self, doc_id: str) -> int:
        return hash(doc_id) % self.num_partitions

    def insert(self, doc_id: str, **attributes):
        """Insert (immediately consistent)."""
        partition_id = self._get_partition(doc_id)
        self.partitions[partition_id].insert(doc_id, **attributes)

    def delete(self, doc_id: str):
        """Delete (immediately consistent)."""
        partition_id = self._get_partition(doc_id)
        self.partitions[partition_id].delete(doc_id)

    def search_global(self, attribute: str, value) -> List[str]:
        """Search across all partitions (scatter/gather)."""
        results = []
        for partition in self.partitions:
            results.extend(partition.search(attribute, value))
        return results


# =============================================================================
# GLOBAL INDEX IMPLEMENTATION (Eventually Consistent)
# =============================================================================

class GlobalIndexPartition:
    """A partition of the GLOBAL index (eventually consistent)."""

    def __init__(self, partition_id: int):
        self.partition_id = partition_id
        self.indexes: Dict[str, Dict] = defaultdict(lambda: defaultdict(list))

    def add_entry(self, attribute: str, value, doc_id: str, data_partition_id: int):
        """Add index entry."""
        self.indexes[attribute][value].append((doc_id, data_partition_id))

    def remove_entry(self, attribute: str, value, doc_id: str):
        """Remove index entry."""
        entries = self.indexes[attribute][value]
        self.indexes[attribute][value] = [(d, p) for d, p in entries if d != doc_id]

    def search(self, attribute: str, value) -> List[Tuple[str, int]]:
        """Search (returns doc_id and data partition)."""
        return self.indexes[attribute].get(value, []).copy()


class DataPartition:
    """A data partition storing actual documents."""

    def __init__(self, partition_id: int):
        self.partition_id = partition_id
        self.documents: Dict[str, Dict] = {}

    def insert(self, doc_id: str, **attributes):
        """Insert a document."""
        self.documents[doc_id] = attributes.copy()

    def delete(self, doc_id: str):
        """Delete a document."""
        self.documents.pop(doc_id, None)

    def get(self, doc_id: str) -> Optional[Dict]:
        """Get a document."""
        return self.documents.get(doc_id)


class GlobalIndexDatabase:
    """Database with GLOBAL indexes (eventually consistent)."""

    def __init__(self, num_data_partitions: int, num_index_partitions: int):
        self.num_data_partitions = num_data_partitions
        self.num_index_partitions = num_index_partitions

        self.data_partitions = [DataPartition(i) for i in range(num_data_partitions)]
        self.index_partitions = [GlobalIndexPartition(i) for i in range(num_index_partitions)]

        # Pending updates (for eventual consistency)
        self.pending_updates: List[Tuple[str, str, str, str, int]] = []

    def _get_data_partition(self, doc_id: str) -> int:
        return hash(doc_id) % self.num_data_partitions

    def _get_index_partition(self, attribute: str, value: str) -> int:
        return hash(f"{attribute}:{value}") % self.num_index_partitions

    def insert(self, doc_id: str, **attributes):
        """Insert (data is immediate, index is async)."""
        data_partition_id = self._get_data_partition(doc_id)
        self.data_partitions[data_partition_id].insert(doc_id, **attributes)

        # Queue index updates
        for attr_name, attr_value in attributes.items():
            self.pending_updates.append(("INSERT", attr_name, str(attr_value), doc_id, data_partition_id))

    def delete(self, doc_id: str):
        """Delete (data is immediate, index is async)."""
        data_partition_id = self._get_data_partition(doc_id)
        doc = self.data_partitions[data_partition_id].get(doc_id)

        if doc:
            self.data_partitions[data_partition_id].delete(doc_id)
            for attr_name, attr_value in doc.items():
                self.pending_updates.append(("DELETE", attr_name, str(attr_value), doc_id, data_partition_id))

    def flush_index_updates(self):
        """Flush pending index updates (simulates async process)."""
        for op, attr, value, doc_id, data_part in self.pending_updates:
            index_partition_id = self._get_index_partition(attr, value)
            index_partition = self.index_partitions[index_partition_id]

            if op == "INSERT":
                index_partition.add_entry(attr, value, doc_id, data_part)
            elif op == "DELETE":
                index_partition.remove_entry(attr, value, doc_id)

        self.pending_updates.clear()

    def search_global(self, attribute: str, value: str) -> List[str]:
        """Search (may not see recent writes)."""
        index_partition_id = self._get_index_partition(attribute, value)
        index_partition = self.index_partitions[index_partition_id]

        entries = index_partition.search(attribute, value)
        results = []
        for doc_id, data_partition_id in entries:
            doc = self.data_partitions[data_partition_id].get(doc_id)
            if doc:
                results.append(doc_id)

        return results


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


def demo_1_immediate_consistency():
    """
    Demo 1: LOCAL indexes provide IMMEDIATE CONSISTENCY.

    DDIA concept: "With local indexes, writes are immediately visible
    in searches because everything is on one partition."
    """
    print_header("DEMO 1: Immediate Consistency (Local Indexes)")
    print("""
    LOCAL indexes are IMMEDIATELY CONSISTENT.
    After a write, the next read sees the change immediately.
    """)

    db = LocalIndexDatabase(num_partitions=5)

    print("  Timeline:\n")

    # Insert a document
    print("  T0: Insert doc_1 with color=red")
    db.insert("doc_1", color="red", brand="Ferrari")

    # Search immediately
    print("  T1: Search for color=red (immediately after insert)")
    results = db.search_global("color", "red")
    print(f"      Found: {results}")
    print(f"      ✅ Document is visible immediately!")

    # Delete the document
    print("\n  T2: Delete doc_1")
    db.delete("doc_1")

    # Search immediately
    print("  T3: Search for color=red (immediately after delete)")
    results = db.search_global("color", "red")
    print(f"      Found: {results}")
    print(f"      ✅ Document is gone immediately!")

    print("""
  💡 KEY INSIGHT (DDIA):
     LOCAL indexes are immediately consistent because:
       • Write and index update happen on the SAME partition
       • No network delay between data and index
       • No async queue

     Real-world: MongoDB, Cassandra (local indexes)
    """)


def demo_2_eventual_consistency():
    """
    Demo 2: GLOBAL indexes provide EVENTUAL CONSISTENCY.

    DDIA concept: "With global indexes, writes are async, so there's
    a window where data is written but not yet indexed."
    """
    print_header("DEMO 2: Eventual Consistency (Global Indexes)")
    print("""
    GLOBAL indexes are EVENTUALLY CONSISTENT.
    After a write, there's a delay before the index is updated.
    """)

    db = GlobalIndexDatabase(num_data_partitions=5, num_index_partitions=3)

    print("  Timeline:\n")

    # Insert a document
    print("  T0: Insert doc_1 with color=red")
    db.insert("doc_1", color="red", brand="Ferrari")
    print(f"      Pending index updates: {len(db.pending_updates)}")

    # Search immediately (before index update)
    print("\n  T1: Search for color=red (immediately after insert)")
    results = db.search_global("color", "red")
    print(f"      Found: {results}")
    print(f"      ⚠️  Document NOT visible yet (index not updated)")

    # Flush index updates
    print("\n  T2: Index updates are flushed (async process completes)")
    db.flush_index_updates()

    # Search after index update
    print("\n  T3: Search for color=red (after index update)")
    results = db.search_global("color", "red")
    print(f"      Found: {results}")
    print(f"      ✅ Document is now visible!")

    print("""
  💡 KEY INSIGHT (DDIA):
     GLOBAL indexes are eventually consistent because:
       • Write to data partition is immediate
       • Index update is queued and happens asynchronously
       • There's a window where data exists but isn't indexed

     Real-world: DynamoDB GSI, Elasticsearch
       "GSIs are eventually consistent. Updates may take a few seconds."
    """)


def demo_3_consistency_window_duration():
    """
    Demo 3: Show the duration of the consistency window.

    DDIA concept: "The consistency window depends on how often
    the async index update process runs."
    """
    print_header("DEMO 3: Consistency Window Duration")
    print("""
    The consistency window is the time between:
      • Write to data partition (immediate)
      • Index update (async)

    Duration depends on:
      • How often the async process runs
      • Network latency
      • Index partition load
    """)

    db = GlobalIndexDatabase(num_data_partitions=5, num_index_partitions=3)

    print("  Scenario: Inserting 100 documents\n")

    # Insert documents
    for i in range(100):
        db.insert(f"doc_{i}", color="red", brand="Ferrari")

    print(f"  After inserts:")
    print(f"    Pending index updates: {len(db.pending_updates)}")

    # Search before flush
    results_before = db.search_global("color", "red")
    print(f"    Search results: {len(results_before)} documents")
    print(f"    ⚠️  Consistency window is OPEN")

    # Simulate async process running
    print(f"\n  Async index update process runs...")
    db.flush_index_updates()

    # Search after flush
    results_after = db.search_global("color", "red")
    print(f"\n  After index update:")
    print(f"    Pending index updates: {len(db.pending_updates)}")
    print(f"    Search results: {len(results_after)} documents")
    print(f"    ✅ Consistency window is CLOSED")

    print("""
  💡 KEY INSIGHT (DDIA):
     The consistency window can be:
       • Very short (milliseconds) if async process runs frequently
       • Long (seconds) if async process is batched
       • Very long (minutes) if system is overloaded

     In DynamoDB:
       "GSI updates are typically complete within a few seconds,
        but can take longer under heavy load."

     Application must handle this:
       • If you need immediate consistency, query data partition directly
       • If you can tolerate eventual consistency, query the index
    """)


def demo_4_read_after_write_consistency():
    """
    Demo 4: Demonstrate read-after-write consistency issues.

    DDIA concept: "With eventual consistency, a user may write data
    and then not see it in their own read."
    """
    print_header("DEMO 4: Read-After-Write Consistency Issue")
    print("""
    With eventual consistency, a user may experience:
      • Write succeeds (returns immediately)
      • Read doesn't see the write (index not updated yet)
      • User sees stale data

    This is a common issue with global indexes.
    """)

    db = GlobalIndexDatabase(num_data_partitions=5, num_index_partitions=3)

    print("  User's perspective:\n")

    # User writes a document
    print("  1. User writes: 'I'm selling a red Ferrari'")
    db.insert("listing_1", color="red", brand="Ferrari", price=200000)
    print("     ✅ Write succeeds (returns immediately)")

    # User searches for their listing
    print("\n  2. User searches: 'Show me all red cars'")
    results = db.search_global("color", "red")
    print(f"     Found: {len(results)} cars")
    print(f"     ❌ User's listing is NOT visible!")
    print(f"     User thinks: 'Did my listing fail to post?'")

    # Index updates
    print("\n  3. [System] Index updates are flushed")
    db.flush_index_updates()

    # User searches again
    print("\n  4. User searches again: 'Show me all red cars'")
    results = db.search_global("color", "red")
    print(f"     Found: {len(results)} cars")
    print(f"     ✅ User's listing is now visible!")

    print("""
  💡 KEY INSIGHT (DDIA):
     This is a real problem in production systems!

     Solutions:
       1. Read-after-write consistency:
          After a write, read from the data partition directly
          (not from the index)

       2. Monotonic reads:
          Always read from the same replica
          (ensures you don't go backwards in time)

       3. Consistent prefix reads:
          Ensure causally related operations are seen in order

     Real-world: DynamoDB applications often implement
     read-after-write consistency by querying the data partition
     directly after a write.
    """)


def demo_5_comparison_table():
    """
    Demo 5: Compare LOCAL vs GLOBAL index consistency.

    DDIA concept: "The choice between local and global indexes
    is fundamentally a consistency vs performance trade-off."
    """
    print_header("DEMO 5: Consistency Comparison")
    print("""
    LOCAL vs GLOBAL indexes: consistency vs performance trade-off
    """)

    print("\n  📊 Comparison Table:\n")

    comparison = [
        ("Aspect", "Local Index", "Global Index"),
        ("─" * 20, "─" * 20, "─" * 20),
        ("Consistency", "Immediate ✅", "Eventual ⏳"),
        ("Write speed", "Fast ⚡", "Fast ⚡ (data only)"),
        ("Read speed", "Slow 🐢", "Fast ⚡"),
        ("Scatter/gather", "Yes (all partitions)", "No (one partition)"),
        ("Index update", "Synchronous", "Asynchronous"),
        ("Tail latency", "High (many partitions)", "Low (one partition)"),
        ("Best for", "Write-heavy", "Read-heavy"),
        ("Used by", "MongoDB, Cassandra", "DynamoDB, Elasticsearch"),
    ]

    for row in comparison:
        print(f"  {row[0]:<20} {row[1]:<20} {row[2]:<20}")

    print("""
  💡 KEY INSIGHT (DDIA):
     There is NO perfect choice. It's a trade-off:

     Choose LOCAL indexes if:
       ✅ You need immediate consistency
       ✅ Writes are more common than reads
       ✅ You can tolerate slow searches

     Choose GLOBAL indexes if:
       ✅ You can tolerate eventual consistency
       ✅ Reads are more common than writes
       ✅ You need fast searches

     Many systems support BOTH:
       • MongoDB: local indexes by default, but supports global
       • DynamoDB: global indexes (GSI) for search, query data directly for consistency
    """)


def demo_6_real_world_scenario():
    """
    Demo 6: Real-world scenario showing the trade-off.

    DDIA concept: "In practice, systems choose based on their workload."
    """
    print_header("DEMO 6: Real-World Scenario")
    print("""
    Scenario: E-commerce product search

    Two approaches:
      1. LOCAL indexes: Immediate consistency, slow search
      2. GLOBAL indexes: Fast search, eventual consistency
    """)

    print("\n  Approach 1: LOCAL Indexes (Immediate Consistency)\n")
    print("    Seller lists a product:")
    print("      1. Write to data partition")
    print("      2. Update local index")
    print("      3. Return to seller")
    print("    Buyer searches:")
    print("      1. Query all partitions (scatter/gather)")
    print("      2. Merge results")
    print("      3. Return to buyer")
    print("\n    Pro: Seller sees product immediately ✅")
    print("    Con: Search is slow (many partitions) 🐢")

    print("\n  Approach 2: GLOBAL Indexes (Fast Search)\n")
    print("    Seller lists a product:")
    print("      1. Write to data partition (immediate)")
    print("      2. Queue index update (async)")
    print("      3. Return to seller")
    print("    Buyer searches:")
    print("      1. Query one index partition")
    print("      2. Return to buyer")
    print("\n    Pro: Search is fast ⚡")
    print("    Con: Seller may not see product immediately ⏳")

    print("""
  💡 KEY INSIGHT (DDIA):
     Real-world systems often use HYBRID approaches:

     Example: DynamoDB
       • Primary index: hash-based (fast point lookups)
       • Global Secondary Index: term-partitioned (fast searches)
       • Consistency: eventually consistent (async updates)

     Example: Elasticsearch
       • Inverted index: term-partitioned (fast searches)
       • Consistency: eventually consistent (refresh interval)
       • Refresh interval: 1 second (configurable)

     Example: MongoDB
       • Local indexes: immediately consistent
       • Sharded cluster: scatter/gather for cross-shard queries
       • Can add global indexes for specific use cases

     The choice depends on:
       • Read/write ratio
       • Consistency requirements
       • Latency requirements
       • Cost constraints
    """)


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 80)
    print("  EXERCISE 3: INDEX CONSISTENCY TRADE-OFFS")
    print("  DDIA Chapter 6: 'Partitioning and Secondary Indexes'")
    print("=" * 80)
    print("""
  This exercise compares consistency guarantees of LOCAL vs GLOBAL indexes.

  Key question: What are you willing to trade for performance?
    • Immediate consistency? (LOCAL indexes)
    • Fast searches? (GLOBAL indexes)
    """)

    demo_1_immediate_consistency()
    demo_2_eventual_consistency()
    demo_3_consistency_window_duration()
    demo_4_read_after_write_consistency()
    demo_5_comparison_table()
    demo_6_real_world_scenario()

    print("\n" + "=" * 80)
    print("  EXERCISE 3 COMPLETE ✅")
    print("=" * 80)
    print("""
  Key Takeaways:

  1. 🔄 LOCAL indexes: immediately consistent, slow reads
  2. ⏳ GLOBAL indexes: eventually consistent, fast reads
  3. 📊 Consistency window: time between write and index update
  4. 👤 Read-after-write: user may not see their own write
  5. 🎯 Choice depends on: read/write ratio, consistency needs
  6. 🏢 Real systems: often use hybrid approaches

  Summary:
    • LOCAL indexes: write-heavy workloads (logs, events)
    • GLOBAL indexes: read-heavy workloads (search, analytics)
    • No perfect choice — it's always a trade-off!
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
