# LSM Tree Quick Reference

## Core Concepts

### LSM Tree = Log-Structured Merge Tree
- **Write-optimized** storage engine
- Trades read performance for write performance
- Used in: RocksDB, LevelDB, Cassandra, HBase

---

## Components

| Component | Purpose | Location |
|-----------|---------|----------|
| **WAL** | Crash recovery, durability | `wal.log` |
| **Memtable** | Fast in-memory writes | `mem`, `mem_keys_sorted` |
| **SSTable** | Immutable sorted file | `sst_*.dat` |
| **Sparse Index** | Fast key lookup | `sst_*.idx` |
| **Manifest** | SSTable metadata | `manifest.json` |

---

## Write Path

```
put(key, value)
  ↓
1. Write to WAL (disk) ← Durability guarantee
  ↓
2. Update memtable (memory) ← Fast
  ↓
3. If memtable.size >= threshold:
     flush() → Create SSTable
```

**Key Points**:
- WAL first (durability)
- Memtable second (speed)
- Flush when threshold reached
- Sequential writes (fast!)

---

## Read Path

```
get(key)
  ↓
1. Check memtable ← O(1) hash lookup
  ↓ (if not found)
2. Check SSTables (newest → oldest)
   ↓
   For each SSTable:
     a. Use sparse index to find offset
     b. Seek to offset
     c. Scan forward until found or passed
  ↓
3. Return value (or None)
```

**Key Points**:
- Check memtable first (fastest)
- Newest SSTable wins (overwrites older)
- Sparse index reduces scan time
- May need to check multiple SSTables

---

## Compaction

**Purpose**: Merge SSTables to reduce files and remove duplicates

**Algorithm**: Merge sort
```
Input: Two sorted SSTables
  older: [a, c, e]
  newer: [b, d, e]

Process: Merge like merge sort
  Compare keys, write smaller
  If same key: newer wins

Output: [a, b, c, d, e]
```

**Key Points**:
- Both inputs sorted → O(n+m) merge
- Newer values overwrite older
- Sequential I/O (fast)
- Reduces number of files

---

## Data Structures

### Memtable
```python
mem: Dict[str, dict]           # O(1) lookup
mem_keys_sorted: List[str]    # Sorted for flush
```

### SSTable Record
```json
{"k": "key", "t": 0, "v": value}  // t=0: normal
{"k": "key", "t": 1, "v": null}  // t=1: tombstone
```

### Sparse Index
```python
entries: List[Tuple[str, int]]  # [(key, offset), ...]
# Index every Nth key (sparse_step)
```

---

## Key Methods

### `put(key, value)`
1. Append to WAL
2. Update memtable
3. Flush if threshold reached

### `get(key)`
1. Check memtable
2. Check SSTables (newest → oldest)
3. Return value or None

### `delete(key)`
1. Write tombstone to WAL
2. Mark as deleted in memtable
3. Flush if threshold reached

### `flush()`
1. Create new SSTable from memtable
2. Write sorted data + sparse index
3. Update manifest
4. Clear memtable + truncate WAL

### `compact_two_oldest()`
1. Load two oldest SSTables
2. Merge (newer wins on conflicts)
3. Write merged SSTable
4. Delete old SSTables
5. Update manifest

---

## Configuration

| Parameter | Default | Purpose |
|-----------|---------|---------|
| `flush_threshold` | 5000 | Keys before flush |
| `sparse_step` | 50 | Index every N keys |

**Trade-offs**:
- Smaller `flush_threshold` → More frequent flushes, smaller SSTables
- Larger `flush_threshold` → Less frequent flushes, larger SSTables
- Smaller `sparse_step` → Faster lookups, larger index
- Larger `sparse_step` → Slower lookups, smaller index

---

## File Structure

```
lsm_data/
├── wal.log              # Write-ahead log
├── manifest.json        # SSTable metadata
├── sst_TIMESTAMP_ID.dat # SSTable data (sorted)
└── sst_TIMESTAMP_ID.idx # Sparse index
```

---

## Performance Characteristics

### Writes
- **Best case**: O(1) memtable insert
- **Average case**: O(1) + occasional flush
- **Worst case**: O(n) flush (n = memtable size)
- **Amplification**: 1 write → 1 WAL + 1 memtable + flush + compaction

### Reads
- **Best case**: O(1) memtable lookup
- **Average case**: O(log n) index + small scan
- **Worst case**: Check all SSTables
- **Amplification**: May read multiple SSTables

---

## Trade-offs

| Aspect | LSM Tree | B-Tree |
|--------|----------|--------|
| **Writes** | Fast (sequential) | Slower (random) |
| **Reads** | Slower (multiple files) | Fast (single file) |
| **Space** | More (duplicates) | Less (in-place) |
| **Compaction** | Required | Not needed |

---

## Common Patterns

### Write Pattern
```python
db.put("key", "value")  # Fast, always sequential
```

### Read Pattern
```python
value = db.get("key")   # May check multiple files
```

### Batch Pattern
```python
# Write many keys
for key, value in items:
    db.put(key, value)
# Flush happens automatically when threshold reached
```

### Compaction Pattern
```python
# After many writes, compact to reduce files
db.compact_two_oldest()
```

---

## Recovery

**On startup**:
1. Load manifest → Get SSTable list
2. Replay WAL → Rebuild memtable
3. Ready to serve requests

**Why it works**:
- WAL has all writes since last flush
- SSTables are immutable (safe)
- Manifest tracks all SSTables

---

## Tombstones

**Purpose**: Mark deleted keys

**How**:
```python
delete("key") → {"k": "key", "t": 1, "v": null}
```

**Why needed**:
- SSTables are immutable
- Can't remove key from old SSTable
- Tombstone tells us: "this was deleted"

**Cleanup**:
- Can be removed during compaction
- If all older SSTables compacted, safe to drop

---

## Sparse Index Details

**How it works**:
1. Index every Nth key (e.g., every 50th)
2. Binary search to find largest indexed key ≤ target
3. Seek to that offset
4. Scan forward until found or passed

**Example**:
```
Index: [("user:0", 0), ("user:50", 1000), ("user:100", 2000)]
Lookup "user:75":
  1. Binary search → "user:50" (largest ≤ "user:75")
  2. Seek to offset 1000
  3. Scan: user:50, user:51, ..., user:75 ✓
```

**Trade-off**:
- More index entries → Faster lookup, larger index
- Fewer index entries → Slower lookup, smaller index

---

## Debugging Tips

1. **Check memtable**: `db.mem`
2. **Check SSTables**: `db.sst_ids`
3. **View WAL**: `cat lsm_data/wal.log`
4. **View manifest**: `cat lsm_data/manifest.json`
5. **View SSTable**: `cat lsm_data/sst_*.dat`
6. **View index**: `cat lsm_data/sst_*.idx`

---

## Common Issues

### Too many SSTables
- **Symptom**: Slow reads
- **Solution**: Run compaction more frequently

### Large WAL
- **Symptom**: Slow recovery
- **Solution**: Flush more frequently (lower threshold)

### High write amplification
- **Symptom**: Many disk writes per logical write
- **Solution**: Increase flush threshold, compact less frequently

### Slow reads
- **Symptom**: Checking many SSTables
- **Solution**: Add bloom filter, compact more frequently

---

## Next Steps

1. ✅ Understand write path
2. ✅ Understand read path
3. ✅ Understand compaction
4. 🔲 Add bloom filter
5. 🔲 Implement range queries
6. 🔲 Add metrics/benchmarking
7. 🔲 Implement leveled compaction

---

*For detailed explanations, see `LSM_DEEP_DIVE.md`*
