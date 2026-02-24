"""
Exercise 2: Term-Partitioned (Global) Secondary Indexes

DDIA Reference: Chapter 6, "Partitioning and Secondary Indexes" (pp. 214-217)

This exercise demonstrates GLOBAL SECONDARY INDEXES — a single index covers
ALL data, but the index itself is partitioned by TERM (the indexed value).

Key concepts:
  - One global index covers all data across all partitions
  - The index is partitioned by TERM (e.g., color:red, color:blue)
  - Reading is FAST: query goes to one index partition
  - Writing is SLOW: must update index on a different node (async)
  - Index is usually EVENTUALLY CONSISTENT (async updates)

Real-world users:
  - DynamoDB (Global Secondary Indexes — GSI)
  - Oracle (global partitioned indexes)
  - Riak (search feature uses term-partitioned index)

Run: python 02_global_indexes.py
"""

import sys
import time
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict
from enum import Enum

sys.stdout.reconfigure(encoding='utf-8')


# =============================================================================
# CORE COMPONENTS: GlobalIndex, TermPartition, GlobalIndexedDatabase
# =============================================================================

class Document:
    """A document with an ID and attributes."""

    def __init__(self, doc_id: str, partition_id: int, **attributes):
        self.doc_id = doc_id
        self.partition_id = partition_id  # Which data partition stores this doc
        self.attributes = attributes

    def __repr__(self):
        return f"Doc({self.doc_id}: {self.attributes})"

    def __eq__(self, other):
        return isinstance(other, Document) and self.doc_id == other.doc_id


class IndexEntry:
    """An entry in the global index."""

    def __init__(self, term_value, doc_id: str, data_partition_id: int):
        self.term_value = term_value
        self.doc_id = doc_id
        self.data_partition_id = data_partition_id  # Where the actual doc is stored

    def __repr__(self):
        return f"IndexEntry({self.term_value} → {self.doc_id} on Partition {self.data_partition_id})"


class TermPartition:
    """
    A partition of the GLOBAL INDEX, covering a range of terms.

    DDIA: "The global index is itself partitioned — but partitioned
    differently from the data. It's partitioned by TERM."

    Example: Index Partition A handles terms a-r, Index Partition B handles s-z.
    """

    def __init__(self, partition_id: int, term_range: Tuple[str, str]):
        self.partition_id = partition_id
        self.term_range = term_range  # (min_term, max_term)
        # Structure: {attribute_name: {term_value: [(doc_id, data_partition_id), ...]}}
        self.index: Dict[str, Dict] = defaultdict(lambda: defaultdict(list))

    def add_entry(self, attribute: str, term_value, doc_id: str, data_partition_id: int):
        """Add an entry to this index partition."""
        self.index[attribute][term_value].append((doc_id, data_partition_id))

    def remove_entry(self, attribute: str, term_value, doc_id: str):
        """Remove an entry from this index partition."""
        entries = self.index[attribute][term_value]
        self.index[attribute][term_value] = [(d, p) for d, p in entries if d != doc_id]

    def search(self, attribute: str, term_value) -> List[Tuple[str, int]]:
        """
        Search for a specific term.
        Returns list of (doc_id, data_partition_id) tuples.
        """
        return self.index[attribute].get(term_value, []).copy()

    def range_search(self, attribute: str, min_term, max_term) -> List[Tuple[str, int]]:
        """Range search on terms."""
        result = []
        for term_val, entries in self.index[attribute].items():
            if min_term <= term_val <= max_term:
                result.extend(entries)
        return result

    def __repr__(self):
        total_entries = sum(len(terms) for attr in self.index.values() for terms in attr.values())
        return f"TermPartition({self.partition_id}, {total_entries} entries)"


class DataPartition:
    """A partition storing actual documents."""

    def __init__(self, partition_id: int):
        self.partition_id = partition_id
        self.documents: Dict[str, Document] = {}

    def insert(self, doc: Document):
        """Insert a document."""
        self.documents[doc.doc_id] = doc

    def delete(self, doc_id: str):
        """Delete a document."""
        self.documents.pop(doc_id, None)

    def get(self, doc_id: str) -> Optional[Document]:
        """Retrieve a document."""
        return self.documents.get(doc_id)

    def __repr__(self):
        return f"DataPartition({self.partition_id}, {len(self.documents)} docs)"


class GlobalIndexedDatabase:
    """
    A distributed database with GLOBAL SECONDARY INDEXES.

    DDIA: "Instead of each partition keeping a local index, a global index
    is constructed that covers data from ALL partitions. However, the global
    index is itself partitioned — but partitioned differently from the data."

    Trade-off:
      ✅ Reads are FAST (query goes to one index partition)
      ❌ Writes are SLOW (must update index on different node)
      ⚠️  Index is usually EVENTUALLY CONSISTENT (async updates)
    """

    def __init__(self, num_data_partitions: int, num_index_partitions: int):
        self.num_data_partitions = num_data_partitions
        self.num_index_partitions = num_index_partitions

        # Data partitions store actual documents
        self.data_partitions = [DataPartition(i) for i in range(num_data_partitions)]

        # Index partitions store the global index (partitioned by term)
        self.index_partitions = [
            TermPartition(i, (chr(ord('a') + i), chr(ord('a') + i + 1)))
            for i in range(num_index_partitions)
        ]

        # Track pending index updates (for eventual consistency demo)
        self.pending_updates: List[Tuple[str, str, str, int, str]] = []  # (op, attr, term, doc_id, data_part)

    def _get_data_partition_for_doc(self, doc_id: str) -> int:
        """Determine which data partition a document belongs to."""
        return hash(doc_id) % self.num_data_partitions

    def _get_index_partition_for_term(self, attribute: str, term_value) -> int:
        """
        Determine which index partition handles a term.
        Simple approach: partition by first letter of term.
        """
        if isinstance(term_value, str) and term_value:
            first_char = term_value[0].lower()
            return ord(first_char) % self.num_index_partitions
        return 0

    def insert(self, doc: Document, async_index: bool = True):
        """
        Insert a document.

        DDIA: "When you insert a new document, you must update the global index.
        However, the index is on a different node. This requires a distributed
        transaction, which is complex and slow. So most systems update the index
        ASYNCHRONOUSLY — the index is eventually consistent."
        """
        # Step 1: Insert into data partition
        data_partition_id = self._get_data_partition_for_doc(doc.doc_id)
        doc.partition_id = data_partition_id
        self.data_partitions[data_partition_id].insert(doc)

        # Step 2: Update global index (sync or async)
        for attr_name, attr_value in doc.attributes.items():
            if async_index:
                # Queue for async update
                self.pending_updates.append(("INSERT", attr_name, str(attr_value), doc.doc_id, data_partition_id))
            else:
                # Synchronous update
                self._update_index("INSERT", attr_name, str(attr_value), doc.doc_id, data_partition_id)

    def delete(self, doc_id: str, async_index: bool = True):
        """Delete a document."""
        data_partition_id = self._get_data_partition_for_doc(doc_id)
        doc = self.data_partitions[data_partition_id].get(doc_id)

        if doc:
            self.data_partitions[data_partition_id].delete(doc_id)

            # Update index
            for attr_name, attr_value in doc.attributes.items():
                if async_index:
                    self.pending_updates.append(("DELETE", attr_name, str(attr_value), doc_id, data_partition_id))
                else:
                    self._update_index("DELETE", attr_name, str(attr_value), doc_id, data_partition_id)

    def _update_index(self, operation: str, attribute: str, term_value: str, doc_id: str, data_partition_id: int):
        """Update the global index."""
        index_partition_id = self._get_index_partition_for_term(attribute, term_value)
        index_partition = self.index_partitions[index_partition_id]

        if operation == "INSERT":
            index_partition.add_entry(attribute, term_value, doc_id, data_partition_id)
        elif operation == "DELETE":
            index_partition.remove_entry(attribute, term_value, doc_id)

    def flush_pending_updates(self):
        """
        Flush all pending index updates.
        This simulates the async index update process.
        """
        for op, attr, term, doc_id, data_part in self.pending_updates:
            self._update_index(op, attr, term, doc_id, data_part)
        self.pending_updates.clear()

    def search_global(self, attribute: str, term_value: str) -> List[Document]:
        """
        Search for documents with a specific attribute value.

        DDIA: "A query for color='red' only needs to go to the one index
        partition that holds the 'red' term. No scatter/gather needed!"
        """
        index_partition_id = self._get_index_partition_for_term(attribute, term_value)
        index_partition = self.index_partitions[index_partition_id]

        # Get (doc_id, data_partition_id) pairs from index
        index_entries = index_partition.search(attribute, term_value)

        # Fetch actual documents from data partitions
        results = []
        for doc_id, data_partition_id in index_entries:
            doc = self.data_partitions[data_partition_id].get(doc_id)
            if doc:
                results.append(doc)

        return results

    def range_search_global(self, attribute: str, min_term: str, max_term: str) -> List[Document]:
        """Range search on terms."""
        results = []

        # May need to query multiple index partitions
        for index_partition in self.index_partitions:
            index_entries = index_partition.range_search(attribute, min_term, max_term)
            for doc_id, data_partition_id in index_entries:
                doc = self.data_partitions[data_partition_id].get(doc_id)
                if doc:
                    results.append(doc)

        return results

    def get_index_stats(self) -> List[Tuple[int, int]]:
        """Get stats for each index partition: (partition_id, entry_count)."""
        stats = []
        for idx_part in self.index_partitions:
            total_entries = sum(len(terms) for attr in idx_part.index.values() for terms in attr.values())
            stats.append((idx_part.partition_id, total_entries))
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


def demo_1_global_index_structure():
    """
    Demo 1: Show how global indexes are structured.

    DDIA concept: "A global index covers all data, but is itself partitioned
    by TERM (the indexed value)."
    """
    print_header("DEMO 1: Global Index Structure")
    print("""
    In a GLOBAL INDEX system:
      - One index covers ALL documents across ALL data partitions
      - The index is partitioned by TERM (e.g., color:red, color:blue)
      - Each index partition handles a range of terms
    """)

    db = GlobalIndexedDatabase(num_data_partitions=3, num_index_partitions=3)

    # Insert documents
    documents = [
        Document("doc_191", 0, color="red", brand="Toyota", price=25000),
        Document("doc_214", 0, color="black", brand="Honda", price=22000),
        Document("doc_768", 0, color="blue", brand="Ford", price=28000),
        Document("doc_893", 0, color="red", brand="BMW", price=45000),
        Document("doc_512", 0, color="silver", brand="Toyota", price=30000),
        Document("doc_445", 0, color="black", brand="Tesla", price=50000),
    ]

    print("  📦 Inserting 6 documents:\n")
    for doc in documents:
        db.insert(doc, async_index=False)
        print(f"    {doc} → Data Partition {doc.partition_id}")

    # Flush async updates
    db.flush_pending_updates()

    # Show index structure
    print_section("📊 Global Index Structure (by term)")

    for idx_part in db.index_partitions:
        print(f"\n  Index Partition {idx_part.partition_id}:")
        if not idx_part.index:
            print(f"    (empty)")
            continue

        for attr_name, terms in idx_part.index.items():
            print(f"    Attribute: {attr_name}")
            for term_val, entries in terms.items():
                doc_refs = [f"{doc_id}@P{part_id}" for doc_id, part_id in entries]
                print(f"      {term_val:8} → {doc_refs}")

    print("""
  💡 KEY INSIGHT (DDIA):
     The global index is partitioned by TERM, not by document ID.

     Example: Index Partition 0 handles terms starting with 'a-g'
              Index Partition 1 handles terms starting with 'h-o'
              Index Partition 2 handles terms starting with 'p-z'

     When you search for "color=red", you only query the index partition
     that handles the term "red". No scatter/gather needed!
    """)


def demo_2_read_is_fast():
    """
    Demo 2: Show that reads are FAST with global indexes.

    DDIA concept: "Reading is fast because the query goes to only ONE
    index partition, not all partitions."
    """
    print_header("DEMO 2: Reads are FAST (Global Index)")
    print("""
    When you search for a term, you only need to:
      1. Determine which index partition handles that term
      2. Query that ONE index partition
      3. Fetch documents from data partitions

    No scatter/gather across all partitions!
    """)

    db = GlobalIndexedDatabase(num_data_partitions=10, num_index_partitions=5)

    # Insert test data
    print("  📦 Inserting test data...\n")
    colors = ["red", "blue", "black", "silver", "white"]
    for i in range(1000):
        color = colors[i % len(colors)]
        doc = Document(f"car_{i}", 0, color=color, brand="Toyota", price=25000)
        db.insert(doc, async_index=False)

    db.flush_pending_updates()

    # Measure search performance
    print("  🔍 Searching for RED cars:\n")

    start = time.time()
    results = db.search_global("color", "red")
    elapsed = time.time() - start

    print(f"  Found {len(results)} red cars")
    print(f"  Query time: {elapsed:.4f}s")

    print(f"\n  📊 Index partition stats:")
    for idx_part_id, entry_count in db.get_index_stats():
        print(f"    Index Partition {idx_part_id}: {entry_count} entries")

    print("""
  💡 KEY INSIGHT (DDIA):
     The query only touches ONE index partition.
     No tail latency problem!

     Compare to local indexes:
       Local:  Must query ALL 10 data partitions → slow
       Global: Must query 1 index partition → fast

     → This is why global indexes are FAST for reads!
    """)


def demo_3_write_is_slow_and_async():
    """
    Demo 3: Show that writes are SLOW and ASYNC with global indexes.

    DDIA concept: "Writing is slow because you must update the index
    on a different node. Most systems do this asynchronously."
    """
    print_header("DEMO 3: Writes are SLOW (Async Index Updates)")
    print("""
    When you insert a document:
      1. Write to data partition (fast, local)
      2. Update global index (slow, different node)

    Most systems do step 2 ASYNCHRONOUSLY to avoid blocking.
    This means the index is EVENTUALLY CONSISTENT.
    """)

    db = GlobalIndexedDatabase(num_data_partitions=5, num_index_partitions=3)

    print("  ✍️  Inserting documents with ASYNC index updates:\n")

    # Insert with async updates
    for i in range(100):
        doc = Document(f"car_{i}", 0, color="red", brand="Toyota", price=25000)
        db.insert(doc, async_index=True)

    print(f"  Inserted 100 documents")
    print(f"  Pending index updates: {len(db.pending_updates)}")

    # Try to search before flushing
    print(f"\n  🔍 Searching BEFORE index updates are flushed:")
    results_before = db.search_global("color", "red")
    print(f"  Found {len(results_before)} red cars (should be 0 or few)")

    # Flush updates
    print(f"\n  ⏳ Flushing pending index updates...")
    db.flush_pending_updates()

    # Search after flushing
    print(f"\n  🔍 Searching AFTER index updates are flushed:")
    results_after = db.search_global("color", "red")
    print(f"  Found {len(results_after)} red cars (should be 100)")

    print("""
  💡 KEY INSIGHT (DDIA):
     With async index updates, there's a window where:
       • Data is in the data partition (visible if you know the doc_id)
       • But the index hasn't been updated yet (not visible in searches)

     This is EVENTUAL CONSISTENCY:
       • Writes are fast (don't wait for index)
       • Reads are eventually consistent (index catches up later)

     Real-world example: DynamoDB Global Secondary Indexes
       "GSIs are eventually consistent. Updates may take a few seconds."

     → This is the trade-off for fast reads!
    """)


def demo_4_consistency_window():
    """
    Demo 4: Demonstrate the consistency window.

    DDIA concept: "With async index updates, there's a window where
    data is written but not yet indexed."
    """
    print_header("DEMO 4: Consistency Window")
    print("""
    With async index updates, there's a time window where:
      • Document is in the data partition
      • But index hasn't been updated yet
      • Searches won't find it
    """)

    db = GlobalIndexedDatabase(num_data_partitions=3, num_index_partitions=2)

    print("  Timeline of a write with async index:\n")

    # Insert a document
    doc = Document("doc_1", 0, color="red", brand="Ferrari", price=200000)
    print(f"  T0: Client inserts {doc}")
    db.insert(doc, async_index=True)

    print(f"  T1: Document is in data partition ✅")
    print(f"      But index update is PENDING ⏳")
    print(f"      Pending updates: {len(db.pending_updates)}")

    # Try to search
    results = db.search_global("color", "red")
    print(f"\n  T2: Client searches for 'color=red'")
    print(f"      Found: {len(results)} documents")
    print(f"      ⚠️  Document not found yet (index not updated)")

    # Flush updates
    print(f"\n  T3: Index updates are flushed (async process completes)")
    db.flush_pending_updates()

    # Search again
    results = db.search_global("color", "red")
    print(f"\n  T4: Client searches for 'color=red' again")
    print(f"      Found: {len(results)} documents")
    print(f"      ✅ Document now found (index updated)")

    print("""
  💡 KEY INSIGHT (DDIA):
     This consistency window is the trade-off for fast writes.

     In DynamoDB:
       • Put item: returns immediately (fast)
       • GSI update: happens asynchronously (may take seconds)
       • Query GSI: may not see recently written items

     Application must handle this:
       • If you need immediate consistency, query the data partition directly
       • If you can tolerate eventual consistency, query the index
    """)


def demo_5_write_vs_read_trade_off():
    """
    Demo 5: Compare write and read performance.

    DDIA concept: "Global indexes are slow for writes but fast for reads.
    This is the opposite trade-off from local indexes."
    """
    print_header("DEMO 5: Write vs Read Trade-off (Global Index)")
    print("""
    Global indexes optimize for READS at the cost of WRITES.

    Write: Slow (must update index on different node)
    Read:  Fast (query only one index partition)
    """)

    db = GlobalIndexedDatabase(num_data_partitions=10, num_index_partitions=5)

    # Measure writes
    print("  ✍️  Measuring WRITE performance:\n")
    num_writes = 1000
    start = time.time()
    for i in range(num_writes):
        doc = Document(f"car_{i}", 0, color="red", brand="Toyota", price=25000)
        db.insert(doc, async_index=False)  # Synchronous for fair comparison
    write_time = time.time() - start
    write_throughput = num_writes / write_time

    print(f"    {num_writes} writes in {write_time:.4f}s")
    print(f"    Throughput: {write_throughput:.0f} writes/sec")

    # Measure reads
    print(f"\n  📖 Measuring READ performance:\n")
    num_reads = 1000
    start = time.time()
    for _ in range(num_reads):
        results = db.search_global("color", "red")
    read_time = time.time() - start
    read_throughput = num_reads / read_time

    print(f"    {num_reads} reads in {read_time:.4f}s")
    print(f"    Throughput: {read_throughput:.0f} reads/sec")

    print(f"\n  📊 Comparison:")
    print(f"    Write throughput: {write_throughput:.0f} ops/sec")
    print(f"    Read throughput:  {read_throughput:.0f} ops/sec")
    print(f"    Ratio: {read_throughput/write_throughput:.1f}x faster reads")

    print("""
  💡 KEY INSIGHT (DDIA):
     Global indexes are optimized for READ-HEAVY workloads.

     Best for:
       ✅ Read-heavy search applications (e-commerce, search engines)
       ✅ Applications with complex queries
       ✅ Can tolerate eventual consistency

     Worst for:
       ❌ Write-heavy applications
       ❌ Applications requiring immediate consistency

     → For write-heavy workloads, use LOCAL INDEXES!
    """)


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 80)
    print("  EXERCISE 2: TERM-PARTITIONED (GLOBAL) SECONDARY INDEXES")
    print("  DDIA Chapter 6: 'Partitioning and Secondary Indexes'")
    print("=" * 80)
    print("""
  This exercise demonstrates GLOBAL SECONDARY INDEXES.
  One index covers all data, but is partitioned by TERM.

  Trade-off:
    ❌ Writes are SLOW (cross-partition update)
    ✅ Reads are FAST (single index partition)
    ⚠️  Index is usually EVENTUALLY CONSISTENT (async)
    """)

    demo_1_global_index_structure()
    demo_2_read_is_fast()
    demo_3_write_is_slow_and_async()
    demo_4_consistency_window()
    demo_5_write_vs_read_trade_off()

    print("\n" + "=" * 80)
    print("  EXERCISE 2 COMPLETE ✅")
    print("=" * 80)
    print("""
  Key Takeaways:

  1. 🌍 One global index covers ALL data
  2. 📊 Index is partitioned by TERM (not by document ID)
  3. 📖 Reads are FAST — query only one index partition
  4. ✍️  Writes are SLOW — must update index on different node
  5. ⏳ Index is usually EVENTUALLY CONSISTENT (async updates)
  6. 🎯 Best for: read-heavy workloads (search, analytics)

  Next: Run 03_index_consistency.py to see consistency trade-offs
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
