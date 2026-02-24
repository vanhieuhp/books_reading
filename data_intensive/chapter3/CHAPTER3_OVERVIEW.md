# Chapter 3: Storage & Retrieval - Complete Overview

> **"How databases actually work"** - This is where DDIA stops being app design and starts being database internals.

---

## 🎯 Core Theme

**Storage engines optimize a trade-off between:**
- **Write performance** (how fast can we write data?)
- **Read performance** (how fast can we read data?)
- **Space amplification** (how much extra space do we use?)

When you execute:
```sql
SELECT ... WHERE key = ?
```

Chapter 3 explains what happens behind the scenes:
- How data is laid out on disk
- How indexes find data fast
- Why writes are often "append-only"
- Why compaction exists
- Why reads can be fast even when data is huge

---

## 📚 Learning Journey (10 Days)

### Day 1: Append-Only Logs
**Location:** `1_log_append/`

**What you learned:**
- Sequential vs random I/O (why appending is fast)
- Why updates-in-place are expensive
- Append-only log structure
- Reverse scanning to find latest values

**Key files:**
- `logdb.py` - Basic append-only log database
- `buffer_explanation.md` - Understanding buffering
- `binary_vs_text_demo.py` - Text vs binary formats

**Key insight:** Sequential writes are 100-1000x faster than random writes!

---

### Day 2: Hash Indexes
**Location:** `2_hash_index/`

**What you learned:**
- Hash index: fast O(1) point lookups
- Mapping `key → byte_offset` in memory
- Why hash indexes are bad for range queries
- Trade-off: memory usage vs lookup speed

**Key files:**
- `logdb_indexed.py` - Hash-indexed log database
- `hash_index_explanation.md` - Comprehensive explanation
- `hash_index_demo.py` - Visual demonstration

**Key insight:** Indexes make lookups thousands of times faster, but use memory and don't help with ranges!

---

### Day 3-4: B-Tree Mental Model
**What you learned:**
- Data stored in pages (fixed-size blocks)
- B-tree nodes contain many keys (high fanout)
- Search is log base ~100 (very shallow tree)
- Random I/O vs caching
- Write-ahead log (WAL) for crash safety

**Key insight:** B-trees are optimized for read performance and range queries, but writes can be expensive due to page splits.

**Note:** This section focuses on understanding the concept. Practical implementation can be done with PostgreSQL/SQLite experiments.

---

### Day 5-7: LSM Tree Implementation
**Location:** `3_tiny_lsm/`

**What you learned:**
- **WAL (Write-Ahead Log)** - Crash safety, write log first
- **Memtable** - In-memory sorted map for fast writes
- **SSTables** - Sorted string tables on disk
- **Compaction** - Merge sorted files, drop overwritten keys
- **Sparse Index** - Key every N lines for fast binary search
- **Bloom Filters** - Avoid reading SSTables that definitely don't contain key
- **Tombstones** - Mark deleted keys

**Key files:**
- `lsm_kv.py` - Basic LSM implementation
- `lsm_kv_enhanced.py` - Full-featured LSM with bloom filters
- `LSM_DEEP_DIVE.md` - Comprehensive explanation
- `LEARNING_GUIDE.md` - Step-by-step learning path
- `QUICK_REFERENCE.md` - Quick lookup guide
- `BLOOM_FILTER_EXPLANATION.md` - Bloom filter deep dive

**Key insight:** LSM trees optimize for writes (append-only) at the cost of reads (may check multiple places). Compaction pays the cost later.

**Real-world usage:** RocksDB, LevelDB, Cassandra, ScyllaDB, HBase

---

### Day 8-9: Column Stores (OLAP)
**Location:** `4_column_store/`

**What you learned:**
- **Row Store (OLTP)** - Great for "get one record"
- **Column Store (OLAP)** - Great for "sum over billions"
- Why compression works better with columns
- Vectorized operations (SIMD-friendly)
- Cache locality advantages

**Key files:**
- `row_store_query.py` - Row-by-row approach (simulates OLTP)
- `column_store_query.py` - Column-by-column arrays (simulates OLAP)
- `benchmark_comparison.py` - Performance comparison
- `visual_demo.py` - Step-by-step visualization
- `COLUMN_STORE_EXPLANATION.md` - Comprehensive explanation
- `generate_dataset.py` - Generate 5M row dataset

**Key insight:** Column stores read only the columns they need (40% less data), enable better compression (10x smaller), and support vectorized operations.

**Real-world usage:**
- OLTP (Row): PostgreSQL, MySQL, MongoDB
- OLAP (Column): ClickHouse, Apache Druid, Snowflake, BigQuery
- Hybrid: Amazon Redshift

---

### Day 10: Choose Engine by Workload
**Decision Guide:**

| Workload | Storage Engine | Why |
|----------|---------------|-----|
| OLTP + range queries | B-tree | Fast point lookups, efficient range scans |
| Write-heavy + log ingestion | LSM | Fast sequential writes, compaction later |
| Analytics aggregations | Column store | Only read needed columns, better compression |
| Point lookups only | Hash index | O(1) lookups, but no ranges |
| Simple append-only | Log | Fastest writes, but slow reads |

---

## 🏗️ Storage Engine Families

### 1. B-Tree Family (Classic OLTP)

**Characteristics:**
- Updates in-place (conceptually)
- Great for point lookups + range queries
- Index is a tree of disk pages
- High fanout (many keys per node)

**Trade-offs:**
- ✅ Fast reads (logarithmic search)
- ✅ Efficient range queries
- ❌ Writes can be expensive (page splits)
- ❌ Random I/O for writes

**Real-world:** PostgreSQL, MySQL, SQLite, MongoDB (WiredTiger)

---

### 2. LSM-Tree Family (Log-Structured Merge)

**Characteristics:**
- Writes are fast (append-only)
- Reads may check multiple places (memtable + SSTables)
- Compaction merges sorted files in background
- Write amplification (data written multiple times)

**Trade-offs:**
- ✅ Fast writes (sequential append)
- ✅ Good for write-heavy workloads
- ❌ Reads may be slower (check multiple levels)
- ❌ Write amplification (compaction overhead)

**Real-world:** RocksDB, LevelDB, Cassandra, ScyllaDB, HBase

---

### 3. Column Store Family (OLAP)

**Characteristics:**
- Each column stored as separate array
- Only read columns you need
- Better compression (similar values together)
- Vectorized operations (SIMD-friendly)

**Trade-offs:**
- ✅ Fast aggregations over many rows
- ✅ Excellent compression
- ✅ Vectorized operations
- ❌ Slow point lookups (must read multiple columns)
- ❌ Poor for frequent updates

**Real-world:** ClickHouse, Apache Druid, Snowflake, BigQuery, Amazon Redshift

---

## 🔑 Key Concepts Cheat Sheet

### Append-Only Logs
- **What:** Write data by appending to end of file
- **Why:** Sequential writes are 100-1000x faster than random writes
- **Trade-off:** Fast writes, but slow reads (must scan)

### Hash Index
- **What:** In-memory dictionary mapping `key → byte_offset`
- **Why:** O(1) lookups instead of O(n) scans
- **Trade-off:** Fast lookups, but uses memory and no range queries

### B-Tree
- **What:** Tree structure with pages, high fanout
- **Why:** Logarithmic search (very shallow tree)
- **Trade-off:** Fast reads and ranges, but writes can be expensive

### LSM Tree
- **What:** Memtable + SSTables + Compaction
- **Why:** Fast writes (append-only), compaction pays cost later
- **Trade-off:** Fast writes, but reads may check multiple places

### WAL (Write-Ahead Log)
- **What:** Write log first, then update data structure
- **Why:** Crash safety - can replay log to recover
- **Trade-off:** Extra write, but ensures durability

### SSTable (Sorted String Table)
- **What:** Sorted key-value pairs on disk
- **Why:** Enables binary search and efficient merging
- **Trade-off:** Must be sorted (write cost), but fast reads

### Compaction
- **What:** Merge multiple SSTables into one, drop overwritten keys
- **Why:** Prevents unbounded growth, improves read performance
- **Trade-off:** Background work (write amplification), but necessary

### Sparse Index
- **What:** Index every Nth key instead of every key
- **Why:** Smaller index, still enables binary search
- **Trade-off:** Must scan small range, but saves memory

### Bloom Filter
- **What:** Probabilistic data structure: "definitely not here" or "maybe here"
- **Why:** Avoid reading SSTables that definitely don't contain key
- **Trade-off:** Small memory overhead, but avoids many disk reads

### Column Store
- **What:** Each column stored as separate array
- **Why:** Only read columns you need, better compression
- **Trade-off:** Fast aggregations, but slow point lookups

---

## 📊 Performance Characteristics

### Write Performance

| Storage Engine | Write Speed | Why |
|---------------|-------------|-----|
| Append-only log | ⚡⚡⚡ Fastest | Sequential write |
| LSM tree | ⚡⚡ Fast | Append to memtable |
| B-tree | ⚡ Moderate | May need page splits |
| Column store | ⚡ Slow | Must update multiple columns |

### Read Performance

| Storage Engine | Read Speed | Why |
|---------------|------------|-----|
| Hash index | ⚡⚡⚡ Fastest | O(1) lookup |
| B-tree | ⚡⚡ Fast | Logarithmic search |
| Column store (analytics) | ⚡⚡ Fast | Only read needed columns |
| LSM tree | ⚡ Moderate | May check multiple levels |
| Append-only log | 🐌 Slow | Must scan |

### Space Efficiency

| Storage Engine | Space Usage | Why |
|---------------|-------------|-----|
| Column store (compressed) | ⚡⚡⚡ Best | 10-100x compression |
| B-tree | ⚡⚡ Good | Efficient page usage |
| LSM tree | ⚡ Moderate | Write amplification |
| Hash index | ⚡ Moderate | Index in memory |
| Append-only log | 🐌 Poor | No deduplication |

---

## 🎓 Learning Path Summary

### Beginner → Intermediate
1. ✅ **Day 1:** Understand why sequential writes are fast (append-only logs)
2. ✅ **Day 2:** Add indexes to make reads fast (hash index)
3. ✅ **Day 3-4:** Understand B-trees (mental model)

### Intermediate → Advanced
4. ✅ **Day 5-7:** Build LSM tree (WAL, memtable, SSTables, compaction)
5. ✅ **Day 8-9:** Understand column stores (OLAP vs OLTP)

### Advanced → Mastery
6. ✅ **Day 10:** Choose the right engine for your workload

---

## 🛠️ Practical Implementations

### What You Built

1. **Append-Only Log Database** (`1_log_append/logdb.py`)
   - Basic put/get operations
   - Reverse scanning for latest values
   - Demonstrates sequential write advantage

2. **Hash-Indexed Database** (`2_hash_index/logdb_indexed.py`)
   - In-memory hash index
   - O(1) lookups
   - Demonstrates index power

3. **LSM Key-Value Store** (`3_tiny_lsm/lsm_kv.py`)
   - WAL for crash safety
   - Memtable for fast writes
   - SSTables for persistent storage
   - Compaction for maintenance
   - Optional: Bloom filters, sparse index

4. **Column Store Query Engine** (`4_column_store/`)
   - Row-by-row processing (OLTP simulation)
   - Column-by-column processing (OLAP simulation)
   - Performance benchmarking

---

## 🔍 Real-World Database Mapping

### OLTP Databases (Row Stores)
- **PostgreSQL** - B-tree indexes, WAL
- **MySQL (InnoDB)** - B-tree indexes, WAL
- **MongoDB (WiredTiger)** - B-tree indexes
- **SQLite** - B-tree indexes

### Write-Heavy Databases (LSM)
- **RocksDB** - LSM tree (used by MySQL, MongoDB, etc.)
- **LevelDB** - LSM tree (used by Chrome, etc.)
- **Cassandra** - LSM tree
- **ScyllaDB** - LSM tree (Cassandra-compatible)
- **HBase** - LSM tree

### OLAP Databases (Column Stores)
- **ClickHouse** - Column store
- **Apache Druid** - Column store
- **Snowflake** - Column store
- **Google BigQuery** - Column store
- **Amazon Redshift** - Column store (hybrid)

---

## 💡 Key Insights

### 1. Sequential > Random I/O
- Sequential writes: 100-1000x faster
- This is why append-only logs and LSM trees exist

### 2. Indexes Trade Memory for Speed
- Hash index: O(1) lookups, but uses RAM
- Sparse index: Less memory, still fast
- B-tree: Logarithmic search, efficient

### 3. Write vs Read Trade-off
- **B-tree:** Optimize reads, writes can be expensive
- **LSM:** Optimize writes, reads may check multiple places
- **Column store:** Optimize aggregations, point lookups slow

### 4. Compression Loves Similarity
- Column stores compress 10-100x better
- Similar values together = better compression
- Row stores: mixed data types = poor compression

### 5. Vectorization Matters
- Modern CPUs: SIMD (process 8-16 values at once)
- Column stores enable vectorized operations
- Row stores: process one row at a time

---

## 📁 Project Structure

```
chapter3/
├── 1_log_append/          # Day 1: Append-only logs
│   ├── logdb.py           # Basic log database
│   ├── buffer_explanation.md
│   └── ...
├── 2_hash_index/          # Day 2: Hash indexes
│   ├── logdb_indexed.py   # Hash-indexed database
│   ├── hash_index_explanation.md
│   └── ...
├── 3_tiny_lsm/            # Day 5-7: LSM tree
│   ├── lsm_kv.py          # Basic LSM implementation
│   ├── lsm_kv_enhanced.py # Full-featured LSM
│   ├── LSM_DEEP_DIVE.md
│   ├── LEARNING_GUIDE.md
│   └── ...
├── 4_column_store/         # Day 8-9: Column stores
│   ├── row_store_query.py
│   ├── column_store_query.py
│   ├── benchmark_comparison.py
│   ├── COLUMN_STORE_EXPLANATION.md
│   └── ...
├── textbook.md            # Original learning plan
└── CHAPTER3_OVERVIEW.md   # This file
```

---

## 🎯 What You Should Remember

### The Big Picture
1. **Storage engines optimize write vs read vs space**
2. **Sequential I/O is 100-1000x faster than random I/O**
3. **Indexes trade memory for speed**
4. **Different engines for different workloads**

### The Details
- **WAL:** Write log first for crash safety
- **Hash index:** O(1) lookups, but no ranges
- **B-tree:** Logarithmic search, great for ranges
- **LSM:** Fast writes, compaction later
- **SSTable:** Sorted for binary search
- **Compaction:** Merge files, drop overwritten keys
- **Bloom filter:** Avoid unnecessary disk reads
- **Column store:** Only read columns you need

### The Trade-offs
- **Row store:** Fast point lookups, slow aggregations
- **Column store:** Fast aggregations, slow point lookups
- **B-tree:** Fast reads, writes can be expensive
- **LSM:** Fast writes, reads may check multiple places

---

## 🚀 Next Steps

### Deepen Your Understanding
1. **Read DDIA Chapter 3** - Connect concepts to real databases
2. **Experiment with real databases:**
   - PostgreSQL (B-tree)
   - RocksDB (LSM)
   - ClickHouse (Column store)
3. **Benchmark your implementations** - See real performance differences
4. **Explore advanced topics:**
   - Multi-version concurrency control (MVCC)
   - Write-ahead log formats
   - Compression algorithms
   - Query optimization

### Apply Your Knowledge
1. **Choose storage engine** for your next project
2. **Optimize queries** based on storage layout
3. **Design data models** that match storage characteristics
4. **Debug performance issues** with storage engine knowledge

---

## 📚 Additional Resources

### Documentation in This Project
- `1_log_append/buffer_explanation.md` - Buffering concepts
- `2_hash_index/hash_index_explanation.md` - Hash index deep dive
- `3_tiny_lsm/LSM_DEEP_DIVE.md` - LSM tree comprehensive guide
- `3_tiny_lsm/BLOOM_FILTER_EXPLANATION.md` - Bloom filter explained
- `4_column_store/COLUMN_STORE_EXPLANATION.md` - Column store deep dive

### External Resources
- **Designing Data-Intensive Applications** (Chapter 3)
- **RocksDB Wiki** - Real-world LSM implementation
- **ClickHouse Documentation** - Column store in practice
- **PostgreSQL Internals** - B-tree implementation details

---

## ✅ Mastery Checklist

- [ ] I understand why sequential writes are faster than random writes
- [ ] I can explain how hash indexes work and their limitations
- [ ] I understand the B-tree mental model (pages, fanout, search)
- [ ] I can trace a write through an LSM tree (WAL → memtable → SSTable)
- [ ] I can trace a read through an LSM tree (memtable → SSTables)
- [ ] I understand why compaction is necessary
- [ ] I can explain how bloom filters avoid unnecessary disk reads
- [ ] I understand the difference between row stores and column stores
- [ ] I can choose the right storage engine for a workload
- [ ] I've implemented at least one storage engine from scratch

---

## 🎉 Congratulations!

You've completed Chapter 3: Storage & Retrieval! You now understand:
- How databases store data on disk
- How indexes make lookups fast
- Why different storage engines exist
- How to choose the right engine for your workload

**You're ready to build production-grade storage systems!** 🚀

---

*Last updated: After completing all 10 days of Chapter 3*
