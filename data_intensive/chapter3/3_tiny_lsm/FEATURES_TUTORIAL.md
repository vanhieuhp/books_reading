# Advanced Features Tutorial: Deep Dive

This tutorial will teach you each advanced feature step by step, with examples and explanations.

---

## 📚 Table of Contents

1. [Bloom Filters](#1-bloom-filters)
2. [Range Queries](#2-range-queries)
3. [Leveled Compaction](#3-leveled-compaction)
4. [Metrics Tracking](#4-metrics-tracking)
5. [Benchmarking](#5-benchmarking)

---

## 1. Bloom Filters

### What is a Bloom Filter?

A **Bloom Filter** is a probabilistic data structure that can tell you:
- ✅ **Definitely NOT in set**: "This key is definitely not here"
- ❓ **Might be in set**: "This key might be here (but could be false positive)"

**Key Properties**:
- **No false negatives**: If it says "not there", it's definitely not there
- **Can have false positives**: If it says "might be there", it could be wrong
- **Very memory efficient**: ~10 bits per key
- **Very fast**: O(k) where k is number of hash functions (typically 3-7)

### Why Do We Need It?

**Problem**: When reading a key, we might check many SSTables before finding it (or not finding it).

**Example**:
```
get("user:999")
  ↓
Check SSTable 1 → Not found (read entire file)
  ↓
Check SSTable 2 → Not found (read entire file)
  ↓
Check SSTable 3 → Not found (read entire file)
  ↓
Check SSTable 4 → Found! (read entire file)

Total: 4 disk reads, but key was only in the last one!
```

**Solution**: Bloom filter tells us "definitely not there" without reading the file!

```
get("user:999")
  ↓
Check Bloom Filter 1 → "Definitely not there" → Skip SSTable 1 ✓
  ↓
Check Bloom Filter 2 → "Definitely not there" → Skip SSTable 2 ✓
  ↓
Check Bloom Filter 3 → "Definitely not there" → Skip SSTable 3 ✓
  ↓
Check Bloom Filter 4 → "Might be there" → Read SSTable 4 → Found! ✓

Total: 1 disk read instead of 4!
```

### How Does It Work?

**Conceptually**:
1. Start with a bit array (all zeros)
2. For each key, hash it multiple times (with different hash functions)
3. Set the bits at those positions to 1
4. To check a key: hash it the same way, if all bits are 1 → "might be there"

**Visual Example**:

```
Initial state (8 bits):
[0, 0, 0, 0, 0, 0, 0, 0]

Add "user:1":
  Hash 1 → position 2
  Hash 2 → position 5
  Hash 3 → position 7
[0, 0, 1, 0, 0, 1, 0, 1]

Add "user:2":
  Hash 1 → position 1
  Hash 2 → position 5 (already set)
  Hash 3 → position 3
[0, 1, 1, 1, 0, 1, 0, 1]

Check "user:1":
  Hash 1 → position 2 → 1 ✓
  Hash 2 → position 5 → 1 ✓
  Hash 3 → position 7 → 1 ✓
  All 1s → "Might be there" ✓

Check "user:999":
  Hash 1 → position 0 → 0 ✗
  Not all 1s → "Definitely not there" ✓
```

### Implementation Details

**Our Implementation** (`bloom_filter.py`):

```python
class BloomFilter:
    def __init__(self, capacity=10000, error_rate=0.01):
        # Calculate optimal size
        # Formula: m = -n * ln(p) / (ln(2)^2)
        # where n = capacity, p = error_rate
        self.size = int(-capacity * math.log(error_rate) / (math.log(2) ** 2))
        
        # Calculate optimal hash count
        # Formula: k = (m/n) * ln(2)
        self.hash_count = int((self.size / capacity) * math.log(2))
        
        # Bit array (using bytearray for efficiency)
        self.bit_array = bytearray((self.size + 7) // 8)
```

**Key Design Decisions**:
1. **Capacity**: Expected number of keys (affects size)
2. **Error Rate**: Desired false positive rate (1% = 0.01)
3. **Hash Functions**: We use MD5 with different seeds (simple but effective)

### Usage Example

```python
from lsm_kv_enhanced import LSMKV

# Create database with bloom filter
db = LSMKV(
    enable_bloom_filter=True,  # Enable bloom filters
    bloom_capacity=10000,       # Expect ~10k keys per SSTable
    bloom_error_rate=0.01      # 1% false positive rate
)

# Write some keys
for i in range(1000):
    db.put(f"user:{i}", {"id": i})

# Read operations now use bloom filter
value = db.get("user:500")  # Fast! Bloom filter helps skip SSTables
value = db.get("user:9999")  # Even faster! Bloom filter says "not there"
```

### Trade-offs

**Pros**:
- ✅ Dramatically reduces unnecessary SSTable reads
- ✅ Very memory efficient (~10 bits per key)
- ✅ Fast (O(k) where k is small, typically 3-7)
- ✅ No false negatives (if it says "not there", it's correct)

**Cons**:
- ❌ Can have false positives (says "might be there" when it's not)
- ❌ Can't remove keys (bloom filters are add-only)
- ❌ Small memory overhead per SSTable

**When to Use**:
- ✅ Many read operations
- ✅ Many keys don't exist (high miss rate)
- ✅ Memory is not extremely constrained

**When NOT to Use**:
- ❌ Very memory constrained
- ❌ All keys exist (no benefit)
- ❌ Write-only workload

---

## 2. Range Queries

### What is a Range Query?

A **range query** retrieves all keys within a specified range.

**Example**:
```python
# Get all users from "user:100" to "user:200"
for key, value in db.scan("user:100", "user:200"):
    print(f"{key}: {value}")
```

### Why Do We Need It?

**Problem**: Getting multiple keys requires multiple `get()` calls:
```python
# Inefficient: Multiple disk reads
for i in range(100, 201):
    value = db.get(f"user:{i}")  # Each call might read multiple SSTables
```

**Solution**: Single `scan()` call reads relevant portions of files:
```python
# Efficient: Single scan, reads only relevant parts
for key, value in db.scan("user:100", "user:200"):
    print(f"{key}: {value}")
```

### How Does It Work?

**Algorithm**:
1. **Check memtable**: Get all keys in range (already sorted)
2. **For each SSTable** (newest to oldest):
   - Use sparse index to find start position
   - Scan forward until end of range
   - Collect records
3. **Merge results**: Newer values overwrite older ones
4. **Return sorted iterator**

**Visual Example**:

```
Memtable: [user:50, user:150, user:250]
SSTable 1: [user:100, user:120, user:140, user:160]
SSTable 2: [user:110, user:130, user:150, user:170]

Scan("user:100", "user:200"):

Step 1: Check memtable
  Found: user:150, user:250 (but 250 > 200, skip)
  Result: {user:150: value_from_memtable}

Step 2: Check SSTable 1
  Sparse index → seek to user:100
  Scan: user:100, user:120, user:140, user:160
  Result: {user:100, user:120, user:140, user:160}

Step 3: Check SSTable 2
  Sparse index → seek to user:110
  Scan: user:110, user:130, user:150, user:170
  user:150 already in result (newer wins), skip
  Result: {user:110, user:130, user:170}

Final: [user:100, user:110, user:120, user:130, user:140, user:150, user:160, user:170]
```

### Implementation Details

**Our Implementation** (`sstable.py`):

```python
def scan(self, start_key: str, end_key: Optional[str] = None) -> Iterator[dict]:
    """Scan records from start_key to end_key (inclusive)."""
    if not os.path.exists(self.dat_path):
        return

    # Use sparse index to find start position
    start_off = self.sparse_index.find_start_offset(start_key)
    
    with open(self.dat_path, "rb") as f:
        f.seek(start_off)
        for line in f:
            rec = json.loads(line)
            k = rec["k"]
            
            # Skip until we reach start_key
            if k < start_key:
                continue
            
            # Stop if we've passed end_key
            if end_key is not None and k > end_key:
                break
            
            yield rec
```

**In LSMKV** (`lsm_kv_enhanced.py`):

```python
def scan(self, start_key: str, end_key: Optional[str] = None) -> Iterator[Tuple[str, Any]]:
    seen_keys = set()
    results = []
    
    # Check memtable (already sorted)
    for key in self.mem_keys_sorted:
        if key < start_key:
            continue
        if end_key is not None and key > end_key:
            break
        if self.mem[key]["t"] != 1:  # Not a tombstone
            results.append((key, self.mem[key]["v"]))
        seen_keys.add(key)
    
    # Check SSTables (newest to oldest)
    for level in self.levels:
        for sst_id in level:
            sst = self._load_sstable(sst_id)
            for rec in sst.scan(start_key, end_key):
                key = rec["k"]
                if key in seen_keys:
                    continue  # Newer value already found
                if rec["t"] != 1:
                    results.append((key, rec["v"]))
                seen_keys.add(key)
    
    # Sort and yield
    results.sort(key=lambda x: x[0])
    for key, value in results:
        yield key, value
```

### Usage Examples

**Basic Range Query**:
```python
# Get all keys from "a" to "z"
for key, value in db.scan("a", "z"):
    print(f"{key}: {value}")
```

**Open-Ended Range**:
```python
# Get all keys from "user:100" to end
for key, value in db.scan("user:100", None):
    print(f"{key}: {value}")
```

**Prefix Scan**:
```python
# Get all keys starting with "user:"
for key, value in db.scan("user:", "user:\xff"):  # \xff is high byte
    print(f"{key}: {value}")
```

**Count Keys in Range**:
```python
count = sum(1 for _ in db.scan("user:1", "user:1000"))
print(f"Found {count} keys")
```

### Performance Characteristics

**Time Complexity**:
- **Best case**: O(k) where k is keys in range (all in memtable)
- **Average case**: O(k + log n) where n is SSTable size (sparse index lookup)
- **Worst case**: O(k + m) where m is total keys scanned

**Space Complexity**: O(k) for results

**Optimizations**:
- ✅ Uses sparse index to skip to start position
- ✅ Stops early when past end_key
- ✅ Skips tombstones
- ✅ Newer values overwrite older ones automatically

---

## 3. Leveled Compaction

### What is Leveled Compaction?

**Leveled Compaction** organizes SSTables into levels, where:
- **Level 0**: Newest SSTables (from memtable flushes)
- **Level 1**: Older SSTables (merged from level 0)
- **Level 2**: Even older SSTables (merged from level 1)
- And so on...

Each level can be up to **10x** the size of the previous level.

### Why Do We Need It?

**Problem with Size-Tiered Compaction** (our original approach):
- All SSTables in one flat list
- Unpredictable read performance
- May need to check many SSTables
- Space amplification (duplicates across files)

**Solution: Leveled Compaction**:
- Organized into levels
- Each level has size limit
- More predictable read performance
- Better space utilization
- Industry standard (RocksDB, LevelDB)

### How Does It Work?

**Structure**:
```
Level 0: [SSTable1, SSTable2, SSTable3, SSTable4]  (4 SSTables, ~4MB each)
Level 1: [SSTable5, SSTable6, SSTable7]            (3 SSTables, ~40MB each)
Level 2: [SSTable8, SSTable9]                      (2 SSTables, ~400MB each)
Level 3: [SSTable10]                               (1 SSTable, ~4GB)
```

**Compaction Trigger**:
- When level N has more than `max_sstables_per_level` SSTables
- Merge SSTables from level N with overlapping SSTables from level N+1
- Write merged SSTable to level N+1

**Example Compaction**:

```
Before:
Level 0: [SST1, SST2, SST3, SST4, SST5]  (5 > 4, trigger compaction!)
Level 1: [SST6, SST7]

Compaction:
1. Take first 4 SSTables from Level 0: [SST1, SST2, SST3, SST4]
2. Find overlapping SSTables in Level 1: [SST6] (overlaps with SST1-SST4)
3. Merge: SST1 + SST2 + SST3 + SST4 + SST6 → SST8
4. Write SST8 to Level 1

After:
Level 0: [SST5]  (only SST5 remains)
Level 1: [SST7, SST8]  (SST8 is the merged one)
```

### Implementation Details

**Our Implementation** (`lsm_kv_enhanced.py`):

```python
def _compact_level(self, level: int) -> None:
    """Compact a level: merge SSTables with next level."""
    if level >= len(self.levels):
        return
    
    # Check if compaction needed
    if len(self.levels[level]) <= self.max_sstables_per_level:
        return
    
    # Get SSTables to compact
    sstables_to_compact = self.levels[level][:self.max_sstables_per_level]
    
    # Get overlapping SSTables from next level
    next_level = level + 1
    if next_level >= len(self.levels):
        self.levels.append([])
    
    overlapping = self.levels[next_level]  # Simplified: merge with all
    
    # Merge all SSTables
    merged_id = self._merge_multiple_sstables(
        sstables_to_compact + overlapping,
        next_level
    )
    
    # Remove old SSTables, add merged one
    # ... (cleanup code)
    
    # Recursively compact next level if needed
    if len(self.levels[next_level]) > self.max_sstables_per_level:
        self._compact_level(next_level)
```

**Key Features**:
1. **Automatic**: Compaction happens automatically when thresholds are reached
2. **Recursive**: If next level gets too large, it compacts too
3. **Size-based**: Each level can be 10x the size of previous level
4. **Overlap detection**: Merges with overlapping SSTables (simplified in our implementation)

### Usage Example

```python
from lsm_kv_enhanced import LSMKV

# Create database with leveled compaction
db = LSMKV(
    use_leveled_compaction=True,      # Enable leveled compaction
    max_sstables_per_level=4,         # Compact when 4+ SSTables in level
    level_size_multiplier=10          # Each level 10x size of previous
)

# Write many keys (triggers flushes and compactions)
for i in range(50000):
    db.put(f"key:{i}", {"value": i})
    if i % 1000 == 0:
        print(f"Written {i} keys, Levels: {[len(level) for level in db.levels]}")

# Manual compaction (optional)
db.compact_level(0)  # Compact level 0
```

### Benefits

**Read Performance**:
- ✅ More predictable: Each level has limited SSTables
- ✅ Fewer SSTables to check: Levels are organized
- ✅ Better cache locality: Related data in same level

**Space Efficiency**:
- ✅ Less duplication: Compaction removes overwritten keys
- ✅ Better utilization: Levels have size limits
- ✅ Tombstone cleanup: Can remove tombstones in deeper levels

**Write Performance**:
- ✅ Similar to size-tiered: Still sequential writes
- ✅ Slightly more overhead: More complex merging logic

### Trade-offs

**Pros**:
- ✅ Industry standard (RocksDB, LevelDB)
- ✅ Predictable performance
- ✅ Better space utilization
- ✅ Automatic tombstone cleanup

**Cons**:
- ❌ More complex implementation
- ❌ Slightly more write amplification
- ❌ Requires more tuning (level sizes, compaction triggers)

---

## 4. Metrics Tracking

### What is Metrics Tracking?

**Metrics** collect performance data about your LSM tree:
- Operation counts (writes, reads, deletes)
- Latencies (average, P95)
- Amplification (write, read)
- I/O statistics (bytes written/read)

### Why Do We Need It?

**Problem**: Without metrics, you don't know:
- How fast your database is
- Where bottlenecks are
- If optimizations help
- Resource usage

**Solution**: Comprehensive metrics tracking!

### What Metrics Do We Track?

**1. Operation Counts**:
```python
metrics.write_count      # Total writes
metrics.read_count       # Total reads
metrics.delete_count    # Total deletes
metrics.flush_count     # Total flushes
metrics.compaction_count # Total compactions
```

**2. Latencies**:
```python
metrics.get_avg_write_latency()    # Average write latency (ms)
metrics.get_p95_write_latency()    # 95th percentile write latency (ms)
metrics.get_avg_read_latency()     # Average read latency (ms)
metrics.get_p95_read_latency()     # 95th percentile read latency (ms)
```

**3. Amplification**:
```python
metrics.get_write_amplification()  # Physical writes / logical writes
metrics.get_read_amplification()   # Bytes read / bytes requested
```

**4. I/O Statistics**:
```python
metrics.bytes_written  # Total bytes written to disk
metrics.bytes_read     # Total bytes read from disk
```

### How Does It Work?

**Implementation** (`metrics.py`):

```python
class Metrics:
    def record_write(self, latency_ms: float, bytes_written: int = 0):
        """Record a write operation."""
        self.write_count += 1
        self.write_latencies.append(latency_ms)
        self.bytes_written += bytes_written
    
    def record_read(self, latency_ms: float, bytes_read: int = 0):
        """Record a read operation."""
        self.read_count += 1
        self.read_latencies.append(latency_ms)
        self.bytes_read += bytes_read
```

**In LSMKV**:

```python
def put(self, key: str, value: Any, durable: bool = True):
    start_time = time.time()
    
    # ... do the write ...
    
    latency_ms = (time.time() - start_time) * 1000
    self.metrics.record_write(latency_ms)
```

### Usage Examples

**Basic Usage**:
```python
from lsm_kv_enhanced import LSMKV

db = LSMKV()

# Do some operations
for i in range(1000):
    db.put(f"key:{i}", {"value": i})

# Get metrics
metrics = db.get_metrics()
print(f"Writes: {metrics.write_count}")
print(f"Avg write latency: {metrics.get_avg_write_latency():.2f} ms")
```

**Print All Stats**:
```python
db.print_stats()
```

**Output**:
```
============================================================
LSM Tree Metrics
============================================================

Operations:
  Writes:    1,000
  Reads:     500
  Deletes:   10
  Flushes:  5
  Compactions: 2

Latencies (ms):
  Write avg: 0.15
  Write p95: 0.45
  Read avg:  1.23
  Read p95:  3.67

Amplification:
  Write: 2.34x
  Read:  1.56x

I/O:
  Bytes written: 1,234,567
  Bytes read:    567,890
============================================================
```

**Get Specific Metrics**:
```python
stats = metrics.get_stats()
print(f"Write amplification: {stats['amplification']['write']:.2f}x")
print(f"P95 read latency: {stats['latencies_ms']['read_p95']:.2f} ms")
```

### Understanding the Metrics

**Write Amplification**:
- **Definition**: Physical writes / Logical writes
- **Example**: If you write 1MB logically but 2.5MB physically → 2.5x amplification
- **Why it matters**: Higher = more disk wear, slower writes
- **Good value**: 2-3x is typical for LSM trees

**Read Amplification**:
- **Definition**: Bytes read / Bytes requested
- **Example**: If you request 1KB but read 1.5KB → 1.5x amplification
- **Why it matters**: Higher = more disk I/O, slower reads
- **Good value**: 1-2x is typical

**P95 Latency**:
- **Definition**: 95% of operations complete within this time
- **Why it matters**: Shows worst-case performance (not just average)
- **Example**: Avg 1ms, P95 5ms → Most are fast, but 5% are slow

---

## 5. Benchmarking

### What is Benchmarking?

**Benchmarking** measures performance under controlled conditions to:
- Compare different configurations
- Identify bottlenecks
- Validate optimizations
- Understand trade-offs

### Our Benchmark Script

**Features**:
1. **Write Benchmark**: Measures write throughput and latency
2. **Read Benchmark**: Measures read throughput, latency, hit rate
3. **Range Query Benchmark**: Measures range query performance
4. **Configuration Comparison**: Side-by-side comparison

### How to Use

**Basic Benchmark**:
```bash
python benchmark.py --writes 10000 --reads 5000
```

**Compare Configurations**:
```bash
python benchmark.py --compare
```

**What It Tests**:
1. **Write Performance**:
   - Throughput (writes/second)
   - Average latency
   - Total time

2. **Read Performance**:
   - Throughput (reads/second)
   - Average latency
   - Hit rate (found vs not found)

3. **Range Queries**:
   - Average time per query
   - Average keys per query

4. **Metrics**:
   - Write amplification
   - Read amplification
   - Total flushes/compactions

### Example Output

```
============================================================
Benchmark: Full Optimized (Bloom + Leveled)
============================================================
Configuration:
  flush_threshold: 1000
  sparse_step: 50
  enable_bloom_filter: True
  use_leveled_compaction: True

1. Write Benchmark
   Throughput: 45,234 writes/sec
   Avg latency: 0.22 ms

2. Read Benchmark
   Throughput: 12,345 reads/sec
   Avg latency: 0.81 ms
   Found: 1600, Not found: 400

3. Range Query Benchmark
   Avg time per query: 2.34 ms
   Avg keys per query: 15.6

4. Metrics
   Write amplification: 2.1x
   Read amplification: 1.4x
   Total flushes: 10
   Total compactions: 3
```

### Understanding Results

**Write Throughput**:
- **High is good**: More writes per second
- **Typical**: 10,000-100,000 writes/sec (depends on hardware)
- **Factors**: Disk speed, flush threshold, durability settings

**Read Throughput**:
- **High is good**: More reads per second
- **Typical**: 5,000-50,000 reads/sec
- **Factors**: Number of SSTables, bloom filter, cache

**Amplification**:
- **Lower is better**: Less overhead
- **Write**: 2-3x is good
- **Read**: 1-2x is good

**Latency**:
- **Lower is better**: Faster operations
- **Write**: <1ms is excellent
- **Read**: <5ms is excellent

### Comparing Configurations

The `--compare` flag tests multiple configurations:

1. **Baseline**: No optimizations
2. **With Bloom Filter**: Bloom filter enabled
3. **With Leveled Compaction**: Leveled compaction enabled
4. **Full Optimized**: Both enabled

**Example Comparison**:
```
Configuration                          Write (ops/s)   Read (ops/s)   Read Latency (ms)
--------------------------------------------------------------------------------------
Baseline                               42,123          8,456           2.34
With Bloom Filter                      41,987          12,345          1.23
With Leveled Compaction                40,123          9,876           1.89
Full Optimized                         39,876          13,456          0.98
```

**Key Insights**:
- Bloom filter: +45% read throughput, -47% read latency
- Leveled compaction: +17% read throughput, -19% read latency
- Combined: +59% read throughput, -58% read latency

---

## 🎓 Practice Exercises

### Exercise 1: Bloom Filter Impact

**Goal**: Measure the impact of bloom filters on read performance.

**Steps**:
1. Create two databases (with and without bloom filter)
2. Write 10,000 keys
3. Read 5,000 keys (mix of existing and non-existing)
4. Compare read latencies

**Expected Result**: Bloom filter should reduce read latency by 20-40%.

### Exercise 2: Range Query Performance

**Goal**: Compare range queries vs multiple gets.

**Steps**:
1. Write 10,000 keys
2. Time 100 range queries (100 keys each)
3. Time 100 × 100 individual gets
4. Compare total time

**Expected Result**: Range queries should be 5-10x faster.

### Exercise 3: Leveled Compaction

**Goal**: Observe leveled compaction in action.

**Steps**:
1. Create database with leveled compaction
2. Write keys in batches (trigger flushes)
3. Monitor level structure: `[len(level) for level in db.levels]`
4. Observe automatic compactions

**Expected Result**: Levels should organize automatically, oldest levels have fewer SSTables.

### Exercise 4: Metrics Analysis

**Goal**: Understand your database's performance characteristics.

**Steps**:
1. Run a workload (mix of writes and reads)
2. Print metrics: `db.print_stats()`
3. Analyze:
   - Is write amplification reasonable? (2-3x)
   - Is read amplification reasonable? (1-2x)
   - Are latencies acceptable?

**Expected Result**: You should understand where time is spent.

---

## 🔑 Key Takeaways

1. **Bloom Filters**: Skip SSTables that definitely don't contain a key
   - Reduces read latency by 20-40%
   - Small memory overhead (~10 bits per key)

2. **Range Queries**: Efficiently scan key ranges
   - 5-10x faster than multiple gets
   - Uses sparse index for efficiency

3. **Leveled Compaction**: Organize SSTables into levels
   - More predictable performance
   - Better space utilization
   - Industry standard approach

4. **Metrics**: Understand your database's performance
   - Track operations, latencies, amplification
   - Identify bottlenecks
   - Validate optimizations

5. **Benchmarking**: Measure and compare performance
   - Test different configurations
   - Understand trade-offs
   - Validate improvements

---

## 📚 Further Reading

- **Bloom Filters**: "Space/Time Trade-offs in Hash Coding with Allowable Errors" (Bloom, 1970)
- **Leveled Compaction**: RocksDB documentation
- **LSM Trees**: "The Log-Structured Merge-Tree" (O'Neil et al., 1996)
- **Metrics**: "Designing Data-Intensive Applications" Chapter 3

---

*Happy learning! Experiment with the code, run benchmarks, and observe how each feature affects performance.* 🚀
