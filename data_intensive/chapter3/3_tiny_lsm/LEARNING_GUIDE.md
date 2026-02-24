# LSM Tree Learning Guide

## 🎯 Learning Path

This guide will help you deeply understand LSM trees by exploring the implementation step by step.

---

## 📚 Resources Created

1. **`LSM_DEEP_DIVE.md`** - Comprehensive explanation of all concepts
2. **`QUICK_REFERENCE.md`** - Quick lookup for key concepts
3. **`lsm_visual_demo.py`** - Interactive visualization
4. **Code files** - Separated by class for clarity

---

## 🚀 Step-by-Step Learning Plan

### Phase 1: Understanding the Basics (30 min)

**Goal**: Understand why LSM trees exist and their core idea

1. **Read**: `LSM_DEEP_DIVE.md` → "Why LSM Trees?" section
2. **Think**: 
   - Why are sequential writes faster than random writes?
   - What's the trade-off between read and write performance?
3. **Compare**: Think about how a B-tree would handle the same operations

**Checkpoint**: Can you explain why LSM trees favor writes over reads?

---

### Phase 2: Write Path Deep Dive (45 min)

**Goal**: Understand how writes flow through the system

1. **Read**: `LSM_DEEP_DIVE.md` → "Data Flow: Write Path" section
2. **Trace**: Follow a single `put()` call through the code:
   ```python
   db.put("user:1", {"name": "Alice"})
   ```
   - Where does it go first? (WAL)
   - Where does it go second? (Memtable)
   - When does it flush?
3. **Run**: Execute `lsm_visual_demo.py` and watch the write path
4. **Inspect**: Look at the actual files created:
   ```bash
   cat lsm_demo_data/wal.log
   ```

**Checkpoint**: Can you trace a write from `put()` to disk?

---

### Phase 3: Read Path Deep Dive (45 min)

**Goal**: Understand how reads find data

1. **Read**: `LSM_DEEP_DIVE.md` → "Data Flow: Read Path" section
2. **Trace**: Follow a single `get()` call:
   ```python
   db.get("user:1")
   ```
   - Why check memtable first?
   - Why check newest SSTable first?
   - How does sparse index help?
3. **Run**: Execute `lsm_visual_demo.py` and watch the read path
4. **Experiment**: Try reading keys that are:
   - In memtable
   - In newest SSTable
   - In oldest SSTable
   - Deleted (tombstone)
   - Don't exist

**Checkpoint**: Can you explain why reads may be slower than writes?

---

### Phase 4: Sparse Index Understanding (30 min)

**Goal**: Understand how sparse indexing speeds up lookups

1. **Read**: `LSM_DEEP_DIVE.md` → "Sparse Index" section
2. **Read**: `sparse_index.py` code
3. **Trace**: Follow `find_start_offset()`:
   ```python
   index.find_start_offset("user:75")
   ```
   - How does binary search work?
   - Why return the previous entry?
4. **Run**: Execute sparse index demo in `lsm_visual_demo.py`
5. **Experiment**: Change `sparse_step` and see the effect:
   ```python
   db = LSMKV(sparse_step=10)  # More index entries
   db = LSMKV(sparse_step=100) # Fewer index entries
   ```

**Checkpoint**: Can you explain the trade-off between index size and lookup speed?

---

### Phase 5: Compaction Deep Dive (45 min)

**Goal**: Understand why and how compaction works

1. **Read**: `LSM_DEEP_DIVE.md` → "Compaction: The Heart of LSM" section
2. **Trace**: Follow `compact_two_oldest()`:
   - Why merge two oldest?
   - How does the merge work?
   - What happens to duplicate keys?
3. **Run**: Execute compaction demo in `lsm_visual_demo.py`
4. **Visualize**: Draw the merge process on paper
5. **Experiment**: Create multiple SSTables and watch them merge

**Checkpoint**: Can you explain why compaction is necessary?

---

### Phase 6: Advanced Features (30 min)

**Goal**: Understand tombstones and optional features

1. **Read**: `LSM_DEEP_DIVE.md` → "Advanced Features Explained" section
2. **Trace**: Follow a delete operation:
   ```python
   db.delete("user:1")
   ```
   - What is a tombstone?
   - Why do we need it?
   - When can we remove it?
3. **Think**: How would you implement bloom filters?
4. **Read**: Research bloom filters (optional but recommended)

**Checkpoint**: Can you explain why tombstones are needed?

---

### Phase 7: Trade-offs and Design Decisions (30 min)

**Goal**: Understand the engineering trade-offs

1. **Read**: `LSM_DEEP_DIVE.md` → "Trade-offs and Design Decisions" section
2. **Think**: For each trade-off:
   - When would you choose LSM over B-tree?
   - When would you choose B-tree over LSM?
3. **Compare**: Make a table comparing:
   - Write performance
   - Read performance
   - Space usage
   - Complexity

**Checkpoint**: Can you explain when to use LSM trees?

---

### Phase 8: Hands-On Experimentation (60 min)

**Goal**: Solidify understanding through experimentation

1. **Modify**: Change `flush_threshold` and observe behavior
2. **Modify**: Change `sparse_step` and measure lookup time
3. **Add**: Implement a simple bloom filter (optional)
4. **Benchmark**: Compare write vs read performance
5. **Debug**: Add logging to trace operations

**Checkpoint**: Can you modify the code confidently?

---

## 🧪 Experiments to Try

### Experiment 1: Write Amplification
```python
import time

db = LSMKV(flush_threshold=100)
start = time.time()
for i in range(1000):
    db.put(f"key{i}", f"value{i}")
end = time.time()
print(f"Time: {end - start}")
print(f"SSTables: {len(db.sst_ids)}")
```

**Question**: How many disk writes happened? (Check WAL + SSTables)

---

### Experiment 2: Read Performance
```python
# Write many keys
for i in range(1000):
    db.put(f"key{i}", f"value{i}")

# Time reads
import time
start = time.time()
for i in range(100):
    db.get(f"key{i}")
end = time.time()
print(f"Read time: {end - start}")
```

**Question**: How does read time change as SSTables grow?

---

### Experiment 3: Compaction Impact
```python
# Create many SSTables
for i in range(10):
    for j in range(100):
        db.put(f"key{i*100+j}", f"value{j}")
    db.flush()

print(f"Before compaction: {len(db.sst_ids)} SSTables")

# Compact
db.compact_two_oldest()

print(f"After compaction: {len(db.sst_ids)} SSTables")
```

**Question**: How does compaction affect read performance?

---

### Experiment 4: Tombstone Behavior
```python
# Write and delete
db.put("key1", "value1")
db.flush()
db.delete("key1")
db.flush()

# Try to read
print(db.get("key1"))  # Should return None

# Check SSTables - tombstone should be there
```

**Question**: Where is the tombstone? Can you see it in the SSTable?

---

## 📖 Reading Order

### For Quick Understanding (1 hour)
1. `QUICK_REFERENCE.md` - Get the big picture
2. Run `lsm_visual_demo.py` - See it in action
3. `LSM_DEEP_DIVE.md` - Read sections that interest you

### For Deep Understanding (4-6 hours)
1. `LSM_DEEP_DIVE.md` - Read entire document
2. Read source code files in order:
   - `utils.py` - Simple utilities
   - `sparse_index.py` - Indexing
   - `sstable.py` - Disk storage
   - `lsm_kv.py` - Main logic
3. Run `lsm_visual_demo.py` - Visualize each concept
4. Try experiments above
5. `QUICK_REFERENCE.md` - Review key concepts

### For Implementation (8+ hours)
1. Complete "Deep Understanding" path
2. Implement extensions:
   - Bloom filter
   - Range queries
   - Leveled compaction
   - Metrics/benchmarking
3. Compare with other implementations (RocksDB, LevelDB)

---

## 🎓 Key Questions to Answer

After completing this guide, you should be able to answer:

1. **Why LSM?**
   - Why do LSM trees exist?
   - What problem do they solve?
   - When should you use them?

2. **How writes work?**
   - What is the write path?
   - Why WAL first?
   - When does flush happen?
   - Why sequential writes?

3. **How reads work?**
   - What is the read path?
   - Why check memtable first?
   - Why newest SSTable first?
   - How does sparse index help?

4. **Why compaction?**
   - Why is compaction needed?
   - How does it work?
   - What are the trade-offs?

5. **Design decisions?**
   - Why immutable SSTables?
   - Why tombstones?
   - Why sparse index?
   - What are the trade-offs?

---

## 🔗 Further Resources

### Papers
- **The Log-Structured Merge-Tree (LSM-Tree)** - O'Neil et al.
- **WiscKey: Separating Keys from Values in SSD-conscious Storage** - Lu et al.

### Production Implementations
- **RocksDB** (Facebook/Meta) - https://rocksdb.org/
- **LevelDB** (Google) - https://github.com/google/leveldb
- **Cassandra** - Uses LSM for storage

### Books
- **Designing Data-Intensive Applications** (Chapter 3) - Martin Kleppmann
- **Database Internals** - Alex Petrov

---

## ✅ Checklist

- [ ] Understand why LSM trees exist
- [ ] Can trace a write from `put()` to disk
- [ ] Can trace a read from `get()` through all components
- [ ] Understand how sparse index works
- [ ] Understand why compaction is needed
- [ ] Understand tombstones
- [ ] Can explain trade-offs
- [ ] Can modify the code confidently
- [ ] Can answer all key questions above

---

## 🎯 Next Steps

Once you've mastered the basics:

1. **Implement bloom filter** - Speed up reads
2. **Add range queries** - `scan(start_key, end_key)`
3. **Implement leveled compaction** - More efficient compaction
4. **Add metrics** - Track performance
5. **Benchmark** - Compare with other implementations
6. **Optimize** - Improve based on benchmarks

---

*Happy learning! Remember: Understanding comes from doing, not just reading. Run the code, modify it, break it, fix it!* 🚀
