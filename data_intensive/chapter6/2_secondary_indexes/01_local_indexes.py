"""
Exercise 1: Document-Partitioned (Local) Secondary Indexes

DDIA Reference: Chapter 6, "Partitioning and Secondary Indexes" (pp. 208-214)

This exercise demonstrates LOCAL SECONDARY INDEXES — each partition maintains
its own index covering only the documents stored in that partition.

Key concepts:
  - Each partition has its own secondary index (local to that partition)
  - Writing is FAST: only update the local index on one partition
  - Reading is SLOW: must scatter/gather across ALL partitions
  - This is the trade-off: write-fast, read-slow

Real-world users:
  - MongoDB (local indexes on each shard)
  - Cassandra (each partition has its own secondary index)
  - Elasticsearch (each shard is a complete Lucene index)

Run: python 01_local_indexes.py
"""

import sys
import time
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')


# =============================================================================
# CORE COMPONENTS: Partition, LocalIndex, PartitionedDatabase
# =============================================================================

class Document:
    """A document with an ID and attributes."""

    def __init__(self, doc_id: str, **attributes):
        self.doc_id = doc_id
        self.attributes = attributes

    def __repr__(self):
        return f"Doc({self.doc_id}: {self.attributes})"

    def __eq__(self, other):
        return isinstance(other, Document) and self.doc_id == other.doc_id and self.attributes == other.attributes


class LocalIndex:
    """
    A LOCAL SECONDARY INDEX for a single partition.

    DDIA insight: "Each partition maintains its own secondary index,
    covering only the documents within that partition."

    The index maps: attribute_value → [doc_ids]
    Example: color:red → [doc_191, doc_893]
    """

    def __init__(self, partition_id: int):
        self.partition_id = partition_id
        # Structure: {attribute_name: {value: set(doc_ids)}}
        self.indexes: Dict[str, Dict] = defaultdict(lambda: defaultdict(set))

    def add_document(self, doc: Document):
        """Add a document to the index."""
        for attr_name, attr_value in doc.attributes.items():
            self.indexes[attr_name][attr_value].add(doc.doc_id)

    def remove_document(self, doc: Document):
        """Remove a document from the index."""
        for attr_name, attr_value in doc.attributes.items():
            self.indexes[attr_name][attr_value].discard(doc.doc_id)

    def search(self, attribute: str, value) -> Set[str]:
        """
        Search for documents with a specific attribute value.
        Returns a set of document IDs.
        """
        return self.indexes[attribute].get(value, set()).copy()

    def range_search(self, attribute: str, min_val, max_val) -> Set[str]:
        """
        Range search on an attribute.
        Returns all doc IDs where min_val <= value <= max_val.
        """
        result = set()
        for val, doc_ids in self.indexes[attribute].items():
            if min_val <= val <= max_val:
                result.update(doc_ids)
        return result


class Partition:
    """
    A single partition storing documents and maintaining a local index.

    DDIA: "Each partition maintains its own secondary index,
    covering only the documents within that partition."
    """

    def __init__(self, partition_id: int):
        self.partition_id = partition_id
        self.documents: Dict[str, Document] = {}  # doc_id → Document
        self.local_index = LocalIndex(partition_id)

    def insert(self, doc: Document):
        """Insert a document into this partition."""
        self.documents[doc.doc_id] = doc
        self.local_index.add_document(doc)

    def delete(self, doc_id: str):
        """Delete a document from this partition."""
        if doc_id in self.documents:
            doc = self.documents.pop(doc_id)
            self.local_index.remove_document(doc)

    def update(self, doc_id: str, **new_attributes):
        """Update a document in this partition."""
        if doc_id in self.documents:
            old_doc = self.documents[doc_id]
            self.local_index.remove_document(old_doc)

            updated_attrs = old_doc.attributes.copy()
            updated_attrs.update(new_attributes)
            new_doc = Document(doc_id, **updated_attrs)

            self.documents[doc_id] = new_doc
            self.local_index.add_document(new_doc)

    def search_local(self, attribute: str, value) -> List[Document]:
        """Search within this partition only."""
        doc_ids = self.local_index.search(attribute, value)
        return [self.documents[doc_id] for doc_id in doc_ids]

    def range_search_local(self, attribute: str, min_val, max_val) -> List[Document]:
        """Range search within this partition only."""
        doc_ids = self.local_index.range_search(attribute, min_val, max_val)
        return [self.documents[doc_id] for doc_id in doc_ids]

    def __repr__(self):
        return f"Partition({self.partition_id}, {len(self.documents)} docs)"


class LocalIndexedDatabase:
    """
    A distributed database with LOCAL SECONDARY INDEXES.

    DDIA: "Each partition maintains its own secondary index.
    When you search for a value, the database must send the query
    to EVERY partition and merge the results."
    """

    def __init__(self, num_partitions: int):
        self.num_partitions = num_partitions
        self.partitions = [Partition(i) for i in range(num_partitions)]

    def _get_partition_for_doc(self, doc_id: str) -> int:
        """
        Determine which partition a document belongs to.
        Using simple hash-based partitioning.
        """
        return hash(doc_id) % self.num_partitions

    def insert(self, doc: Document):
        """Insert a document into the appropriate partition."""
        partition_id = self._get_partition_for_doc(doc.doc_id)
        self.partitions[partition_id].insert(doc)

    def delete(self, doc_id: str):
        """Delete a document."""
        partition_id = self._get_partition_for_doc(doc_id)
        self.partitions[partition_id].delete(doc_id)

    def update(self, doc_id: str, **new_attributes):
        """Update a document."""
        partition_id = self._get_partition_for_doc(doc_id)
        self.partitions[partition_id].update(doc_id, **new_attributes)

    def search_global(self, attribute: str, value) -> List[Document]:
        """
        Search across ALL partitions for documents with a specific attribute value.

        DDIA: "The database doesn't know which partitions contain matching documents.
        It must send the query to EVERY partition, collect the results, and merge them."

        This is the SCATTER/GATHER pattern — expensive!
        """
        results = []
        for partition in self.partitions:
            results.extend(partition.search_local(attribute, value))
        return results

    def range_search_global(self, attribute: str, min_val, max_val) -> List[Document]:
        """
        Range search across ALL partitions.
        Same scatter/gather pattern.
        """
        results = []
        for partition in self.partitions:
            results.extend(partition.range_search_local(attribute, min_val, max_val))
        return results

    def get_partition_stats(self) -> List[Tuple[int, int]]:
        """Get stats for each partition: (partition_id, doc_count)."""
        return [(p.partition_id, len(p.documents)) for p in self.partitions]


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


def demo_1_local_index_structure():
    """
    Demo 1: Show how local indexes are structured.

    DDIA concept: "Each partition maintains its own secondary index,
    covering only the documents within that partition."
    """
    print_header("DEMO 1: Local Index Structure")
    print("""
    In a LOCAL INDEX system, each partition has its own index.
    The index only covers documents stored in that partition.
    """)

    db = LocalIndexedDatabase(num_partitions=3)

    # Insert some documents
    documents = [
        Document("doc_191", color="red", brand="Toyota", price=25000),
        Document("doc_214", color="black", brand="Honda", price=22000),
        Document("doc_768", color="blue", brand="Ford", price=28000),
        Document("doc_893", color="red", brand="BMW", price=45000),
        Document("doc_512", color="silver", brand="Toyota", price=30000),
        Document("doc_445", color="black", brand="Tesla", price=50000),
    ]

    print("  📦 Inserting 6 documents into 3 partitions:\n")
    for doc in documents:
        db.insert(doc)
        partition_id = db._get_partition_for_doc(doc.doc_id)
        print(f"    {doc} → Partition {partition_id}")

    # Show partition distribution
    print_section("📊 Partition Distribution")
    for partition in db.partitions:
        print(f"\n  Partition {partition.partition_id}:")
        print(f"    Documents: {len(partition.documents)}")
        for doc_id, doc in partition.documents.items():
            print(f"      {doc}")

        print(f"\n    Local Index (color):")
        for color, doc_ids in partition.local_index.indexes["color"].items():
            print(f"      {color:8} → {doc_ids}")

    print("""
  💡 KEY INSIGHT (DDIA):
     Each partition maintains its OWN index.
     The index only covers documents in that partition.

     Example: Partition 0's "color:red" index only knows about
     red cars stored in Partition 0, not red cars in other partitions!
    """)


def demo_2_write_is_fast():
    """
    Demo 2: Show that writes are FAST with local indexes.

    DDIA concept: "Writing is fast because you only update
    the local index on one partition."
    """
    print_header("DEMO 2: Writes are FAST (Local Index)")
    print("""
    When you insert a document, you only need to:
      1. Write to one partition
      2. Update that partition's local index

    No cross-partition coordination needed!
    """)

    db = LocalIndexedDatabase(num_partitions=5)

    print("  ⏱️  Measuring write performance:\n")

    # Measure write time
    num_writes = 1000
    start = time.time()

    for i in range(num_writes):
        doc = Document(f"car_{i}", color="red", brand="Toyota", price=25000 + i)
        db.insert(doc)

    elapsed = time.time() - start
    writes_per_sec = num_writes / elapsed if elapsed > 0 else float('inf')

    print(f"  Inserted {num_writes} documents in {elapsed:.4f}s")
    print(f"  Throughput: {writes_per_sec:.0f} writes/sec")

    print(f"\n  📊 Distribution across partitions:")
    for partition_id, doc_count in db.get_partition_stats():
        print(f"    Partition {partition_id}: {doc_count} documents")

    print("""
  💡 KEY INSIGHT (DDIA):
     Each write is LOCAL to one partition.
     No network calls to other partitions.
     No distributed transactions.

     → This is why local indexes are FAST for writes!
    """)


def demo_3_read_requires_scatter_gather():
    """
    Demo 3: Show that reads are SLOW with local indexes.

    DDIA concept: "Reading requires scatter/gather across ALL partitions.
    A single slow partition creates high tail latency."
    """
    print_header("DEMO 3: Reads are SLOW (Scatter/Gather)")
    print("""
    When you search for "color = red", the database must:
      1. Send query to EVERY partition
      2. Each partition searches its local index
      3. Merge results from all partitions

    This is the SCATTER/GATHER pattern — expensive!
    """)

    db = LocalIndexedDatabase(num_partitions=10)

    # Insert test data
    print("  📦 Inserting test data...\n")
    colors = ["red", "blue", "black", "silver", "white"]
    for i in range(500):
        color = colors[i % len(colors)]
        doc = Document(f"car_{i}", color=color, brand="Toyota", price=25000)
        db.insert(doc)

    # Perform a search
    print("  🔍 Searching for all RED cars:\n")

    start = time.time()
    results = db.search_global("color", "red")
    elapsed = time.time() - start

    print(f"  Found {len(results)} red cars")
    print(f"  Query time: {elapsed:.4f}s")

    print(f"\n  📊 Results by partition:")
    for partition in db.partitions:
        local_results = partition.search_local("color", "red")
        print(f"    Partition {partition.partition_id}: {len(local_results)} red cars")

    print("""
  💡 KEY INSIGHT (DDIA):
     The query must be sent to ALL 10 partitions.
     Each partition searches its local index independently.
     Results are merged at the client.

     If ANY partition is slow, the entire query is slow.
     This is called TAIL LATENCY — the slowest partition wins!

     → This is why local indexes are SLOW for reads!
    """)


def demo_4_tail_latency_problem():
    """
    Demo 4: Demonstrate the tail latency problem.

    DDIA concept: "A single slow partition can create high tail latency
    for the entire query."
    """
    print_header("DEMO 4: Tail Latency Problem")
    print("""
    With scatter/gather, the query is only as fast as the SLOWEST partition.
    If one partition is slow (e.g., due to disk I/O), the entire query stalls.
    """)

    db = LocalIndexedDatabase(num_partitions=100)

    # Insert data
    for i in range(10000):
        color = ["red", "blue", "black"][i % 3]
        doc = Document(f"car_{i}", color=color, brand="Toyota", price=25000)
        db.insert(doc)

    print("  🔍 Searching across 100 partitions:\n")

    # Simulate partition response times
    partition_times = []
    for partition in db.partitions:
        start = time.time()
        results = partition.search_local("color", "red")
        elapsed = time.time() - start
        partition_times.append(elapsed)

    print(f"  Partition response times:")
    print(f"    Min:    {min(partition_times)*1000:.2f}ms")
    print(f"    Max:    {max(partition_times)*1000:.2f}ms")
    print(f"    Median: {sorted(partition_times)[len(partition_times)//2]*1000:.2f}ms")
    print(f"    Mean:   {sum(partition_times)/len(partition_times)*1000:.2f}ms")

    print(f"\n  ⏱️  Total query time: {max(partition_times)*1000:.2f}ms")
    print(f"      (determined by the SLOWEST partition)")

    print("""
  💡 KEY INSIGHT (DDIA):
     With 100 partitions, even if 99 are fast, the query waits for the 1 slow one.

     This is the TAIL LATENCY problem:
       • Average latency: ~0.5ms per partition
       • But max latency: ~2ms (the slowest partition)
       • Query latency: 2ms (limited by the slowest)

     In production with thousands of partitions, tail latency becomes severe!

     → This is a fundamental limitation of scatter/gather!
    """)


def demo_5_write_vs_read_trade_off():
    """
    Demo 5: Compare write and read performance.

    DDIA concept: "Local indexes are fast for writes but slow for reads.
    This is a fundamental trade-off."
    """
    print_header("DEMO 5: Write vs Read Trade-off")
    print("""
    Local indexes optimize for WRITES at the cost of READS.

    Write: Fast (single partition)
    Read:  Slow (all partitions)
    """)

    db = LocalIndexedDatabase(num_partitions=10)

    # Measure writes
    print("  ✍️  Measuring WRITE performance:\n")
    num_writes = 1000
    start = time.time()
    for i in range(num_writes):
        doc = Document(f"car_{i}", color="red", brand="Toyota", price=25000)
        db.insert(doc)
    write_time = time.time() - start
    write_throughput = num_writes / write_time

    print(f"    {num_writes} writes in {write_time:.4f}s")
    print(f"    Throughput: {write_throughput:.0f} writes/sec")

    # Measure reads
    print(f"\n  📖 Measuring READ performance:\n")
    num_reads = 100
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
    print(f"    Ratio: {write_throughput/read_throughput:.1f}x faster writes")

    print("""
  💡 KEY INSIGHT (DDIA):
     Local indexes are optimized for WRITE-HEAVY workloads.

     Best for:
       ✅ Write-heavy applications (IoT sensors, logs, events)
       ✅ Applications that rarely search by secondary attributes

     Worst for:
       ❌ Read-heavy search workloads
       ❌ Applications with complex queries

     → For search-heavy workloads, use GLOBAL INDEXES (next demo)!
    """)


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 80)
    print("  EXERCISE 1: DOCUMENT-PARTITIONED (LOCAL) SECONDARY INDEXES")
    print("  DDIA Chapter 6: 'Partitioning and Secondary Indexes'")
    print("=" * 80)
    print("""
  This exercise demonstrates LOCAL SECONDARY INDEXES.
  Each partition maintains its own index covering only its documents.

  Trade-off:
    ✅ Writes are FAST (single partition)
    ❌ Reads are SLOW (scatter/gather all partitions)
    """)

    demo_1_local_index_structure()
    demo_2_write_is_fast()
    demo_3_read_requires_scatter_gather()
    demo_4_tail_latency_problem()
    demo_5_write_vs_read_trade_off()

    print("\n" + "=" * 80)
    print("  EXERCISE 1 COMPLETE ✅")
    print("=" * 80)
    print("""
  Key Takeaways:

  1. 📝 Each partition has its OWN secondary index (local)
  2. ✍️  Writes are FAST — only update one partition's index
  3. 📖 Reads are SLOW — must scatter/gather across ALL partitions
  4. ⏱️  Tail latency: slowest partition determines query time
  5. 🎯 Best for: write-heavy workloads (logs, events, sensors)

  Next: Run 02_global_indexes.py to see the opposite trade-off
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
