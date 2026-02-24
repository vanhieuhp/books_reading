# Chapter 6, Section 2: Partitioning and Secondary Indexes

This directory contains learning materials and practical exercises for **Section 2** of Chapter 6 from "Designing Data-Intensive Applications" by Martin Kleppmann.

## 📚 Contents

- **[01_local_indexes.py](./01_local_indexes.py)** - Document-partitioned (local) secondary indexes
- **[02_global_indexes.py](./02_global_indexes.py)** - Term-partitioned (global) secondary indexes
- **[03_index_consistency.py](./03_index_consistency.py)** - Consistency trade-offs between local and global indexes
- **[README.md](./README.md)** - This file
- **[QUICKSTART.md](./QUICKSTART.md)** - Get started in 3 steps

## 🎯 What You'll Learn

### The Problem
When you partition data across multiple nodes, secondary indexes become tricky. A "red car" could be stored in any partition. How do you efficiently search for it?

### Two Fundamental Approaches

**1. Local (Document-Partitioned) Indexes**
- Each partition maintains its own index
- Writing is FAST (single partition)
- Reading is SLOW (scatter/gather all partitions)
- Immediately consistent
- Best for: write-heavy workloads

**2. Global (Term-Partitioned) Indexes**
- One index covers all data, partitioned by term
- Writing is SLOW (cross-partition update)
- Reading is FAST (single index partition)
- Eventually consistent (async updates)
- Best for: read-heavy workloads

### The Trade-off
```
LOCAL INDEX:
  Write: ✅ Fast (one partition)
  Read:  ❌ Slow (all partitions)
  Consistency: ✅ Immediate

GLOBAL INDEX:
  Write: ❌ Slow (different node)
  Read:  ✅ Fast (one partition)
  Consistency: ⏳ Eventual
```

## 🚀 Quick Start

1. **Read the textbook section** (Chapter 6, pp. 208-217 in DDIA)
2. **Run the exercises in order:**
   ```bash
   python 01_local_indexes.py
   python 02_global_indexes.py
   python 03_index_consistency.py
   ```
3. **Modify and experiment** — change parameters to see how behavior changes

## 📁 Project Structure

```
2_secondary_indexes/
├── README.md                      # This file
├── QUICKSTART.md                  # Get started in 3 steps
├── 01_local_indexes.py            # Local index demo
├── 02_global_indexes.py           # Global index demo
└── 03_index_consistency.py        # Consistency trade-offs
```

## 🔑 Key Concepts

### Local Indexes (Document-Partitioned)

Each partition maintains its own secondary index covering only its documents.

```
Partition 0                    Partition 1
┌──────────────────┐          ┌──────────────────┐
│ Data:            │          │ Data:            │
│  doc_191 (red)   │          │  doc_768 (blue)  │
│  doc_214 (black) │          │  doc_893 (red)   │
│                  │          │                  │
│ Local Index:     │          │ Local Index:     │
│  red → [191]     │          │  red → [893]     │
│  black → [214]   │          │  blue → [768]    │
└──────────────────┘          └──────────────────┘

Query: "Find all red cars"
  → Send to Partition 0: returns [191]
  → Send to Partition 1: returns [893]
  → Merge: [191, 893]
```

**Pros:**
- Writes are fast (single partition)
- No distributed transactions needed

**Cons:**
- Reads require scatter/gather (all partitions)
- Tail latency: slowest partition determines query time
- Not suitable for search-heavy workloads

**Used by:** MongoDB, Cassandra, Elasticsearch

### Global Indexes (Term-Partitioned)

One global index covers all data, but the index itself is partitioned by term.

```
Data Partitions:
  Partition 0: doc_191 (red), doc_214 (black)
  Partition 1: doc_768 (blue), doc_893 (red)

Global Index Partitions (by term):
  Index Partition A (a-r):
    black → [doc_214 on Partition 0]
    blue  → [doc_768 on Partition 1]

  Index Partition B (s-z):
    red   → [doc_191 on Partition 0, doc_893 on Partition 1]

Query: "Find all red cars"
  → Query Index Partition B only
  → Returns: [doc_191 on Partition 0, doc_893 on Partition 1]
  → Fetch from data partitions
```

**Pros:**
- Reads are fast (single index partition)
- No scatter/gather needed
- Efficient for complex queries

**Cons:**
- Writes are slow (cross-partition update)
- Usually eventually consistent (async updates)
- Distributed transactions are complex

**Used by:** DynamoDB (GSI), Oracle, Riak, Elasticsearch

### Consistency Trade-off

**Local Indexes: Immediately Consistent**
- Write and index update happen on same partition
- No delay between write and visibility in searches
- But searches are slow (scatter/gather)

**Global Indexes: Eventually Consistent**
- Write to data partition is immediate
- Index update happens asynchronously
- There's a window where data exists but isn't indexed
- But searches are fast (single partition)

## 💡 Real-World Examples

### DynamoDB Global Secondary Indexes (GSI)
```
Primary Index: hash-based (fast point lookups)
GSI: term-partitioned (fast searches)
Consistency: eventually consistent
  "GSI updates are typically complete within a few seconds,
   but can take longer under heavy load."

Application pattern:
  1. Write item (returns immediately)
  2. Query GSI (may not see recent writes)
  3. If you need immediate consistency, query data partition directly
```

### Elasticsearch
```
Index: inverted index (term-partitioned)
Consistency: eventually consistent
Refresh interval: 1 second (configurable)

Application pattern:
  1. Index document (queued)
  2. Wait for refresh interval
  3. Query index (sees document)
```

### MongoDB
```
Local indexes: immediately consistent
Sharded cluster: scatter/gather for cross-shard queries
Can add global indexes for specific use cases

Application pattern:
  1. Write document (immediately consistent)
  2. Query local index (may scatter/gather)
  3. Or use aggregation pipeline for complex queries
```

## 🛠️ Prerequisites

- Python 3.8+
- No external packages needed (uses only standard library!)

## 📖 How to Use These Exercises

1. **Run each exercise** and read the output carefully — it tells a story
2. **Understand the trade-offs** — why is one approach fast and the other slow?
3. **Modify parameters** — change partition counts, document counts, etc.
4. **Think about your workload** — would you use local or global indexes?

## 🎓 Learning Path

1. **Start with 01_local_indexes.py**
   - Understand how local indexes work
   - See why writes are fast but reads are slow
   - Experience the scatter/gather problem

2. **Then 02_global_indexes.py**
   - Understand how global indexes work
   - See why reads are fast but writes are slow
   - Experience the eventual consistency window

3. **Finally 03_index_consistency.py**
   - Compare the two approaches
   - Understand the consistency trade-off
   - See real-world implications

## 🤔 Interview Questions

1. **What is the difference between local and global indexes?**
   - Local: each partition has its own index (fast writes, slow reads)
   - Global: one index covers all data, partitioned by term (slow writes, fast reads)

2. **Why is scatter/gather expensive?**
   - Must query all partitions
   - Tail latency: slowest partition determines query time
   - With thousands of partitions, tail latency becomes severe

3. **Why are global indexes usually eventually consistent?**
   - Distributed transactions are complex and slow
   - Most systems update the index asynchronously
   - This creates a consistency window where data exists but isn't indexed

4. **When would you choose local indexes over global indexes?**
   - Write-heavy workloads (logs, events, sensors)
   - When you can tolerate slow searches
   - When immediate consistency is critical

5. **When would you choose global indexes over local indexes?**
   - Read-heavy workloads (search, analytics)
   - When you can tolerate eventual consistency
   - When search performance is critical

6. **How does DynamoDB handle this trade-off?**
   - Primary index: hash-based (fast point lookups)
   - GSI: term-partitioned (fast searches)
   - Consistency: eventually consistent
   - Application must handle the consistency window

7. **What is the "consistency window"?**
   - Time between write to data partition and index update
   - During this window, data exists but isn't indexed
   - Duration depends on how often async process runs

8. **How can you implement read-after-write consistency with global indexes?**
   - After a write, read from the data partition directly (not the index)
   - This ensures you see your own write immediately
   - Trade-off: slower read, but consistent

## 📚 References

- **DDIA Chapter 6**: "Partitioning" (pp. 200-227)
- **Section 2**: "Partitioning and Secondary Indexes" (pp. 208-217)
- **Key papers**:
  - DynamoDB paper (2012) — describes GSI design
  - Bigtable paper (2006) — describes local index design

## 🎯 Next Steps

After mastering this section, explore:
- **Section 3**: Rebalancing Partitions (how to add/remove nodes)
- **Section 4**: Request Routing (how clients find the right partition)
- **Chapter 5**: Replication (how to replicate partitions for fault tolerance)

---

**Start with `QUICKSTART.md` to begin your hands-on practice!**
