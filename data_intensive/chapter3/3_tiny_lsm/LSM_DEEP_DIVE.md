# LSM Tree Deep Dive: Understanding Your Tiny KV-Store

## Table of Contents
1. [Why LSM Trees?](#why-lsm-trees)
2. [Architecture Overview](#architecture-overview)
3. [Component Deep Dive](#component-deep-dive)
4. [Data Flow: Write Path](#data-flow-write-path)
5. [Data Flow: Read Path](#data-flow-read-path)
6. [Compaction: The Heart of LSM](#compaction-the-heart-of-lsm)
7. [Advanced Features Explained](#advanced-features-explained)
8. [Trade-offs and Design Decisions](#trade-offs-and-design-decisions)

---

## Why LSM Trees?

### The Problem with Traditional B-Trees
- **Random writes**: B-trees require random disk I/O for updates
- **Write amplification**: Updating a single key may require writing multiple pages
- **Slow on SSDs**: Random writes are slower than sequential writes on modern storage

### The LSM Solution
- **Append-only writes**: All writes are sequential (fast!)
- **Batch writes**: Accumulate writes in memory, flush in batches
- **Read optimization**: Use indexes and bloom filters to minimize disk reads

**Key Insight**: Trade read performance for write performance. Reads may need to check multiple files, but writes are always fast sequential operations.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    LSMKV Store                           │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐         ┌──────────────┐             │
│  │   Memtable   │         │     WAL      │             │
│  │ (in-memory)  │◄────────│ (disk log)   │             │
│  │  sorted map  │         │              │             │
│  └──────┬───────┘         └──────────────┘             │
│         │                                                │
│         │ flush (when threshold reached)                │
│         ▼                                                │
│  ┌──────────────┐                                        │
│  │   SSTable    │                                        │
│  │  (on disk)   │                                        │
│  │  + Sparse    │                                        │
│  │    Index     │                                        │
│  └──────┬───────┘                                        │
│         │                                                │
│         │ compaction (merge old SSTables)               │
│         ▼                                                │
│  ┌──────────────┐                                        │
│  │  Merged      │                                        │
│  │  SSTable     │                                        │
│  └──────────────┘                                        │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Key Components

1. **WAL (Write-Ahead Log)**: Crash recovery guarantee
2. **Memtable**: Fast in-memory writes
3. **SSTables**: Immutable sorted files on disk
4. **Sparse Index**: Fast key lookup in SSTables
5. **Manifest**: Metadata about SSTables

---

## Component Deep Dive

### 1. WAL (Write-Ahead Log)

**Location**: `lsm_kv.py` → `_append_wal()`, `recover()`

**Purpose**: 
- **Durability**: Ensure writes survive crashes
- **Recovery**: Rebuild memtable after restart

**How it works**:
```python
# Every write goes to WAL first
def put(self, key, value):
    # 1. Write to WAL (disk) - CRITICAL for durability
    self._append_wal({"op": "PUT", "k": key, "v": value})
    
    # 2. Then update memtable (memory) - fast
    self._mem_put(key, value)
```

**Why WAL first?**
- If crash happens after WAL write but before memtable update → recover from WAL
- If crash happens before WAL write → data loss (but that's acceptable for this design)
- **Write-ahead** = write to log BEFORE updating data structure

**Recovery Process** (`recover()` method):
```python
# On startup, replay WAL to rebuild memtable
for line in wal_file:
    record = json.loads(line)
    if record["op"] == "PUT":
        memtable[record["k"]] = record["v"]
    elif record["op"] == "DEL":
        memtable[record["k"]] = TOMBSTONE
```

**Key Design Decision**: 
- After flush, WAL is truncated (cleared)
- Why? Because flushed data is now safely in SSTable
- Alternative: Keep WAL and mark which parts are flushed (more complex)

---

### 2. Memtable

**Location**: `lsm_kv.py` → `mem`, `mem_keys_sorted`, `_mem_put()`

**Purpose**:
- Fast in-memory writes (O(log n) insertion)
- Accumulate writes before flushing to disk

**Data Structure**:
```python
mem: Dict[str, dict]              # Fast O(1) lookup
mem_keys_sorted: List[str]        # Sorted keys for flush
```

**Why two structures?**
- `mem`: Fast key-value lookup (hash map)
- `mem_keys_sorted`: Maintains sorted order for efficient flush

**Insertion** (`_mem_put()`):
```python
def _mem_put(self, key, entry):
    if key not in self.mem:
        insort(self.mem_keys_sorted, key)  # Insert in sorted order
    self.mem[key] = entry
```

**Key Insight**: 
- `insort()` uses binary search → O(log n) per insertion
- But we need sorted order for efficient flush to SSTable
- Trade-off: Slightly slower writes for much faster flushes

**When does it flush?**
- When `len(mem) >= flush_threshold` (default: 5000 keys)
- Or manually via `flush()`

---

### 3. SSTable (Sorted String Table)

**Location**: `sstable.py`

**Purpose**:
- Immutable sorted file on disk
- Efficient for sequential reads
- Can be merged efficiently (both inputs are sorted)

**Structure**:
```
sst_1234567890_abc123.dat    # Data file (sorted key-value pairs)
sst_1234567890_abc123.idx    # Sparse index file
```

**Data File Format** (one JSON record per line):
```json
{"k":"user:1","t":0,"v":{"name":"Hieu"}}
{"k":"user:2","t":0,"v":{"name":"An"}}
{"k":"user:3","t":1,"v":null}  // t=1 means tombstone (deleted)
```

**Why JSON per line?**
- Simple to parse (one `readline()` per record)
- Human-readable for debugging
- Trade-off: Not the most space-efficient (could use binary format)

**Key Properties**:
1. **Immutable**: Once written, never modified
2. **Sorted**: Keys are in sorted order
3. **Append-only**: New SSTables are created, old ones are merged

---

### 4. Sparse Index

**Location**: `sparse_index.py`

**Purpose**: 
- Fast key lookup without scanning entire SSTable
- Index every Nth key (configurable via `sparse_step`)

**How it works**:
```python
# Example: sparse_step = 50
# Index entries: [("user:0", offset_0), ("user:50", offset_50), ...]

# To find "user:75":
# 1. Binary search finds "user:50" is the largest <= "user:75"
# 2. Seek to offset_50
# 3. Scan forward until we find "user:75" or pass it
```

**Algorithm** (`find_start_offset()`):
```python
def find_start_offset(self, key: str) -> int:
    # Binary search for largest indexed key <= target key
    keys = [k for k, _ in self.entries]
    i = bisect_left(keys, key)  # Find insertion point
    
    if i == 0:
        return 0  # Key is before first index entry
    
    # Return offset of previous entry (largest <= key)
    return self.entries[i - 1][1]
```

**Example**:
```
SSTable data:
  offset 0:  {"k":"user:0",...}
  offset 100: {"k":"user:10",...}
  offset 200: {"k":"user:20",...}
  offset 300: {"k":"user:30",...}
  ...

Sparse index (sparse_step=10):
  [("user:0", 0), ("user:10", 100), ("user:20", 200), ...]

Lookup "user:25":
  1. Binary search finds "user:20" (index entry)
  2. Seek to offset 200
  3. Scan forward: user:20, user:21, ..., user:25 ✓
```

**Trade-off**:
- **Smaller sparse_step** → More index entries → Faster lookups but larger index
- **Larger sparse_step** → Fewer index entries → Slower lookups but smaller index
- Default: 50 (good balance)

---

### 5. Manifest

**Location**: `lsm_kv.py` → `_load_manifest()`, `_save_manifest()`

**Purpose**:
- Track which SSTables exist
- Maintain order (newest → oldest)
- Persist across restarts

**Format**:
```json
{
  "sst_ids": [
    "1234567890_abc123",  // newest
    "1234567880_def456",  // older
    "1234567870_ghi789"   // oldest
  ]
}
```

**Why atomic write?**
```python
def _save_manifest(self):
    tmp = self.manifest_path + ".tmp"
    # Write to temp file
    json.dump({"sst_ids": self.sst_ids}, tmp)
    fsync_file(tmp)
    # Atomic rename (prevents corruption)
    os.replace(tmp, self.manifest_path)
```

**Key Insight**: 
- If crash during write, old manifest is preserved
- `os.replace()` is atomic on most filesystems

---

## Data Flow: Write Path

### Step-by-Step: `put("user:1", {"name": "Hieu"})`

```
1. User calls: db.put("user:1", {"name": "Hieu"})
   │
   ├─► 2. _append_wal() writes to WAL:
   │      wal.log: {"op":"PUT","ts":1234567890,"k":"user:1","v":{"name":"Hieu"}}\n
   │      [fsync if durable=True]
   │
   ├─► 3. _mem_put() updates memtable:
   │      mem["user:1"] = {"t": 0, "v": {"name": "Hieu"}}
   │      insort(mem_keys_sorted, "user:1")
   │
   └─► 4. Check if flush needed:
        if len(mem) >= flush_threshold:
            flush()
```

### Flush Process: `flush()`

```
1. Check: if memtable is empty, return
   │
   ├─► 2. Generate SSTable ID: "1234567890_abc123"
   │
   ├─► 3. Create files:
   │      sst_1234567890_abc123.dat
   │      sst_1234567890_abc123.idx
   │
   ├─► 4. Write data file (sorted):
   │      for key in mem_keys_sorted:  # Already sorted!
   │          record = {"k": key, "t": entry["t"], "v": entry["v"]}
   │          offset = file.tell()
   │          file.write(json.dumps(record) + "\n")
   │          
   │          if count % sparse_step == 0:
   │              sparse_index.append((key, offset))
   │      fsync_file()
   │
   ├─► 5. Write index file:
   │      json.dump(sparse_index.to_json(), idx_file)
   │      fsync_file()
   │
   ├─► 6. Update manifest:
   │      sst_ids.insert(0, "1234567890_abc123")  # Newest first
   │      _save_manifest()
   │
   └─► 7. Clear memtable and truncate WAL:
        mem.clear()
        mem_keys_sorted.clear()
        _truncate_wal()  # Safe because data is now in SSTable
```

**Key Observations**:
- Flush is **sequential write** (very fast!)
- Data is **already sorted** (no sorting needed during flush)
- **Atomic operation**: Either entire flush succeeds or fails
- After flush, WAL can be cleared (data is safely on disk)

---

## Data Flow: Read Path

### Step-by-Step: `get("user:1")`

```
1. User calls: db.get("user:1")
   │
   ├─► 2. Check memtable first (fastest):
   │      if "user:1" in mem:
   │          entry = mem["user:1"]
   │          if entry["t"] == 1:  # tombstone?
   │              return None
   │          else:
   │              return entry["v"]
   │
   └─► 3. If not in memtable, check SSTables (newest → oldest):
        for sst_id in sst_ids:  # [newest, ..., oldest]
            sst = _load_sstable(sst_id)
            record = sst.get("user:1")
            
            if record is not None:
                if record["t"] == 1:  # tombstone?
                    return None
                else:
                    return record["v"]  # Found it!
        
        return None  # Not found anywhere
```

### SSTable Lookup: `sst.get("user:1")`

```
1. Use sparse index to find approximate location:
   │
   ├─► start_offset = sparse_index.find_start_offset("user:1")
   │    # Binary search in index, returns offset of largest indexed key <= "user:1"
   │
   ├─► 2. Seek to that offset in data file:
   │      file.seek(start_offset)
   │
   └─► 3. Scan forward (linear search):
        while True:
            line = file.readline()
            if not line:
                return None  # End of file
            
            record = json.loads(line)
            
            if record["k"] == "user:1":
                return record  # Found!
            
            if record["k"] > "user:1":
                return None  # Passed it (keys are sorted)
```

**Why newest → oldest?**
- Newer data overwrites older data
- If we find key in newer SSTable, we can stop (it's the latest value)

**Performance**:
- **Best case**: Key in memtable → O(1) hash lookup
- **Average case**: Key in newest SSTable → O(log n) binary search in index + small linear scan
- **Worst case**: Key in oldest SSTable → Check all SSTables

---

## Compaction: The Heart of LSM

### Why Compaction?

**Problem**: Without compaction, you'd have many small SSTables:
- Slow reads (must check many files)
- Wasted space (overwritten keys in multiple files)
- Tombstones never removed

**Solution**: Merge SSTables to:
- Reduce number of files
- Remove overwritten keys
- Remove tombstones (eventually)

### Compaction Strategy: `compact_two_oldest()`

**Algorithm**: Merge two oldest SSTables into one

```
Input: Two sorted SSTables
  older.dat: [user:1, user:3, user:5, user:7]
  newer.dat: [user:2, user:4, user:5, user:8]

Process: Merge like merge sort
  Step 1: Compare user:1 (old) vs user:2 (new)
          → user:1 < user:2 → write user:1
  Step 2: Compare user:3 (old) vs user:2 (new)
          → user:2 < user:3 → write user:2
  Step 3: Compare user:3 (old) vs user:4 (new)
          → user:3 < user:4 → write user:3
  Step 4: Compare user:5 (old) vs user:4 (new)
          → user:4 < user:5 → write user:4
  Step 5: Compare user:5 (old) vs user:5 (new)
          → Same key! → write user:5 (newer wins)
  ...

Output: Merged SSTable
  merged.dat: [user:1, user:2, user:3, user:4, user:5, user:7, user:8]
```

**Code Walkthrough**:

```python
def compact_two_oldest(self):
    # 1. Get two oldest SSTables
    older = load_sstable(sst_ids[-1])  # Oldest
    newer = load_sstable(sst_ids[-2])  # Second oldest
    
    # 2. Create iterators (both are sorted!)
    it_old = iter_sstable_records(older.dat_path)
    it_new = iter_sstable_records(newer.dat_path)
    
    rec_old = next(it_old, None)
    rec_new = next(it_new, None)
    
    # 3. Merge loop (like merge sort)
    while rec_old is not None or rec_new is not None:
        if rec_old is None:
            # Only new records left
            chosen = rec_new
            rec_new = next(it_new, None)
        elif rec_new is None:
            # Only old records left
            chosen = rec_old
            rec_old = next(it_old, None)
        else:
            # Both have records - compare keys
            if rec_new["k"] < rec_old["k"]:
                chosen = rec_new
                rec_new = next(it_new, None)
            elif rec_new["k"] > rec_old["k"]:
                chosen = rec_old
                rec_old = next(it_old, None)
            else:
                # Same key: NEWER wins (overwrites older)
                chosen = rec_new
                rec_new = next(it_new, None)
                rec_old = next(it_old, None)  # Skip old one
        
        # Write chosen record to merged SSTable
        write(chosen)
    
    # 4. Replace old SSTables with merged one
    delete(older)
    delete(newer)
    sst_ids = sst_ids[:-2] + [merged_id]
```

**Key Insights**:
1. **Both inputs are sorted** → Merge is O(n + m) linear time
2. **Newer wins** → When keys match, newer value overwrites older
3. **Tombstones preserved** → Can be removed in later compaction if needed
4. **Sequential I/O** → Very fast on modern storage

**Alternative Strategies** (not implemented, but common):
- **Leveled compaction**: Organize SSTables into levels, merge level by level
- **Size-tiered compaction**: Merge SSTables of similar size
- **Tiered compaction**: Merge all SSTables in a tier

---

## Advanced Features Explained

### 1. Tombstones

**Purpose**: Mark deleted keys without immediately removing them

**How it works**:
```python
def delete(self, key):
    # Write tombstone to WAL
    _append_wal({"op": "DEL", "k": key})
    
    # Mark as deleted in memtable
    _mem_put(key, {"t": 1, "v": None})  # t=1 means tombstone
```

**Why needed?**
- If key exists in older SSTable, we need to mark it deleted
- Can't modify SSTable (it's immutable)
- Tombstone tells us: "this key was deleted, don't return it"

**Example**:
```
SSTable 1 (old): {"k":"user:1","v":"Alice"}
SSTable 2 (new): {"k":"user:1","t":1}  // tombstone

get("user:1"):
  1. Check memtable → not found
  2. Check SSTable 2 → found tombstone → return None
  3. Don't check SSTable 1 (already found in newer file)
```

**Cleanup**:
- Tombstones can be removed during compaction
- If we know all older SSTables are compacted, we can drop tombstones
- Current implementation: Keeps tombstones (simpler, but wastes space)

### 2. Sparse Index (Already Covered)

See [Sparse Index](#4-sparse-index) section above.

### 3. Bloom Filters (Not Implemented, But Explained)

**What is it?**
- Probabilistic data structure
- Answers: "Is key **definitely not** in this SSTable?"
- Can have false positives (says key might be there when it's not)
- Never has false negatives (if it says "not there", it's definitely not)

**Why useful?**
- Avoid reading SSTable if key definitely isn't there
- Small memory footprint (few bits per key)

**How it would work**:
```python
# On flush, create bloom filter
bloom = BloomFilter()
for key in mem_keys_sorted:
    bloom.add(key)

# On get, check bloom filter first
def get(self, key):
    # Check memtable...
    
    for sst_id in sst_ids:
        sst = load_sstable(sst_id)
        
        # Check bloom filter first
        if not sst.bloom_filter.might_contain(key):
            continue  # Definitely not in this SSTable, skip it
        
        # Bloom says "might be there", so check SSTable
        record = sst.get(key)
        if record:
            return record
```

**Trade-off**:
- **Memory**: Small overhead per SSTable
- **Speed**: Avoids many unnecessary SSTable reads
- **Complexity**: Need to implement bloom filter

---

## Trade-offs and Design Decisions

### 1. Write Performance vs Read Performance

**LSM Trees favor writes**:
- ✅ Writes: Always sequential (fast)
- ❌ Reads: May need to check multiple files (slower)

**Mitigations**:
- Sparse index: Reduces scan time in SSTable
- Bloom filter: Avoids unnecessary SSTable reads
- Memtable: Fastest reads (in memory)

### 2. Space Amplification

**Problem**: 
- Same key may exist in multiple SSTables
- Tombstones take space
- Overwritten values take space

**Solution**: 
- Compaction removes duplicates
- But compaction itself uses temporary space

**Trade-off**: 
- More frequent compaction → Less space, more CPU
- Less frequent compaction → More space, less CPU

### 3. Write Amplification

**Problem**: 
- One logical write may cause multiple physical writes:
  1. WAL write
  2. Memtable update
  3. Flush to SSTable
  4. Compaction rewrites

**Mitigation**: 
- Batch writes (flush threshold)
- Efficient compaction (merge sorted files)

### 4. Durability Guarantees

**Current implementation**:
- `durable=True` (default): `fsync()` after WAL write
- `durable=False`: Write to OS buffer (faster, but may lose data on crash)

**Trade-off**:
- `durable=True`: Slower, but guaranteed durability
- `durable=False`: Faster, but risk of data loss

### 5. Recovery Strategy

**Current**: Truncate WAL after flush

**Alternative**: Keep WAL, mark which parts are flushed
- More complex
- Allows point-in-time recovery
- Better for large WALs

---

## Key Takeaways

1. **LSM Trees trade read performance for write performance**
   - Writes are always fast (sequential)
   - Reads may be slower (check multiple files)

2. **Immutable SSTables enable efficient merging**
   - Can't modify files → must merge to update
   - But merging sorted files is very fast

3. **Sparse indexes balance lookup speed vs index size**
   - Index every Nth key
   - Binary search + small linear scan

4. **Compaction is critical**
   - Prevents unbounded growth
   - Removes duplicates and tombstones
   - But uses CPU and I/O

5. **WAL ensures durability**
   - Write to log before updating data
   - Replay on recovery

---

## Exercises to Deepen Understanding

1. **Add bloom filter**: Implement bloom filter per SSTable
2. **Leveled compaction**: Organize SSTables into levels
3. **Range queries**: Implement `scan(start_key, end_key)`
4. **Metrics**: Track read/write amplification
5. **Benchmark**: Compare with hash index implementation

---

## Further Reading

- **Designing Data-Intensive Applications** (Chapter 3): Storage and Retrieval
- **LSM-Tree Paper**: "The Log-Structured Merge-Tree" by O'Neil et al.
- **RocksDB**: Production LSM implementation (Facebook/Meta)
- **LevelDB**: Original LSM implementation (Google)

---

## Questions to Test Understanding

1. Why do we check memtable before SSTables in `get()`?
2. Why are SSTables immutable?
3. What happens if we don't compact?
4. Why does newer SSTable win when keys overlap?
5. What's the purpose of the sparse index?
6. Why do we truncate WAL after flush?
7. How would you implement range queries?
8. What are the trade-offs of smaller vs larger `sparse_step`?

---

*Happy learning! 🚀*
