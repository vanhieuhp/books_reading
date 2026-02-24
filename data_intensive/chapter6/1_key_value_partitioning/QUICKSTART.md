# Quick Start Guide — Chapter 6, Section 1

## 🚀 Get Started in 5 Minutes

### Step 1: Run Exercise 1 (Key Range Partitioning)

```bash
python 01_key_range_partitioning.py
```

**What you'll learn:**
- How keys are assigned to partitions based on ranges
- Why range queries are efficient
- The hot spot problem with time-series data
- How to fix hot spots by prefixing keys

**Time:** ~5 minutes

---

### Step 2: Run Exercise 2 (Hash Partitioning)

```bash
python 02_hash_partitioning.py
```

**What you'll learn:**
- How hash functions distribute keys uniformly
- Why hash partitioning eliminates hot spots
- Why range queries become slow
- Why the hash function must be deterministic

**Time:** ~5 minutes

---

### Step 3: Run Exercise 3 (Compound Keys)

```bash
python 03_compound_keys.py
```

**What you'll learn:**
- How compound keys combine hashing and sorting
- Efficient range queries within a partition
- Inefficient range queries across partitions
- Real-world use cases (social media, IoT, time-series)

**Time:** ~5 minutes

---

### Step 4: Run Exercise 4 (Hot Spot Solutions)

```bash
python 04_hot_spot_solutions.py
```

**What you'll learn:**
- The "celebrity problem" (viral posts)
- How to detect hot keys
- Key splitting as a solution
- The read/write trade-off

**Time:** ~5 minutes

---

## 📊 The Big Picture

After running all 4 exercises, you'll understand:

```
┌─────────────────────────────────────────────────────────────┐
│ PARTITIONING STRATEGIES                                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ 1. RANGE PARTITIONING                                       │
│    Keys: A-H, H-P, P-Z                                      │
│    ✅ Fast range queries                                    │
│    ❌ Hot spots (all writes for "now" go to 1 partition)    │
│                                                             │
│ 2. HASH PARTITIONING                                        │
│    Keys: hash(key) % num_partitions                         │
│    ✅ No hot spots (even distribution)                      │
│    ❌ Slow range queries (must query all partitions)        │
│                                                             │
│ 3. COMPOUND KEYS (BEST OF BOTH)                             │
│    PRIMARY KEY (user_id, timestamp)                         │
│    • user_id: HASHED (determines partition)                 │
│    • timestamp: SORTED (enables range queries)              │
│    ✅ No hot spots + fast range queries (within partition)  │
│    ❌ Slow cross-partition range queries                    │
│                                                             │
│ 4. HOT SPOT SOLUTIONS                                       │
│    Key splitting: post_8932 → post_8932_00, _01, ..., _99   │
│    ✅ Spreads load across partitions                        │
│    ❌ Reads must query all split keys                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Key Insights from DDIA

### Exercise 1: Range Partitioning
> "Assign a continuous range of keys to each partition, similar to how volumes of a printed encyclopedia cover letters A–Ce, Ce–G, G–K, and so on."

**The Hot Spot Problem:**
> "If your key is a timestamp, ALL writes for 'right now' go to one partition (the one whose range covers the current time), while all historical partitions sit idle."

**The Fix:**
> "The traditional fix is to prefix the timestamp with another dimension: Key = sensor_name + '_' + timestamp"

---

### Exercise 2: Hash Partitioning
> "A good hash function takes skewed, clustered data and distributes it uniformly across an output range."

**Important Warning:**
> "You should NOT use Java's Object.hashCode() or Python's hash() because they may give different results in different processes. Databases use well-defined, deterministic hash functions like MD5, MurmurHash, xxHash, FNV."

**The Trade-off:**
> "Range queries are impossible on the main key. Since hash('user_001') and hash('user_002') land on completely different partitions, a query like WHERE user_id BETWEEN 'user_001' AND 'user_100' must be sent to ALL partitions."

---

### Exercise 3: Compound Keys
> "Cassandra uses a brilliant compromise between key range and hash partitioning. The first column (user_id) is hashed to determine the partition. The remaining columns (timestamp) are used as a sorted index within that partition."

**Perfect For:**
> "This pattern is extremely powerful for social media feeds, IoT sensor data, and time-series workloads."

---

### Exercise 4: Hot Spots
> "Hashing evenly distributes keys, but what if millions of requests all target the exact same key? Even with hash partitioning, that key maps to exactly one partition, and that partition becomes an extreme hot spot."

**The Reality:**
> "Today, most data systems are not able to automatically compensate for such a highly skewed workload, so it's the responsibility of the application to reduce the skew."

**The Solution:**
> "Append a random number (e.g., 00-99) to the hot key. This splits the single hot partition's load across up to 100 partitions. You should only apply this for keys you know are hot."

---

## 💡 Discussion Questions

After running the exercises, think about:

1. **When would you use range partitioning?**
   - Answer: When you have frequent range queries and can tolerate some hot spots

2. **When would you use hash partitioning?**
   - Answer: When you need even load distribution and don't need range queries

3. **Why is compound key partitioning so popular?**
   - Answer: It combines the benefits of both approaches for common workloads

4. **How would you detect hot keys in production?**
   - Answer: Monitor partition load, track request rates per key, set thresholds

5. **What's the cost of key splitting?**
   - Answer: Reads become slower (must query all split keys), but writes become faster

---

## 🔗 Real-World Systems

### HBase (Range Partitioning)
- Row keys are byte-strings sorted lexicographically
- Partitions (regions) have configurable split points
- Automatic region splitting when size exceeds threshold

### Cassandra (Compound Keys)
- `PRIMARY KEY (partition_key, clustering_key)`
- partition_key is hashed (determines node)
- clustering_key is sorted (enables range queries)
- 256 vnodes per node by default

### DynamoDB (Hash + Global Secondary Indexes)
- Primary key: hash-based partitioning
- Global Secondary Indexes: term-partitioned (we'll see this in Section 2)
- Handles hot spots with auto-scaling

### MongoDB (Flexible)
- Before v2.4: range-based sharding only
- After v2.4: hash-based sharding available
- Compound shard keys supported

---

## 📚 Next Steps

1. ✅ Complete all 4 exercises
2. ✅ Understand the trade-offs of each strategy
3. ✅ Read DDIA Chapter 6, Section 1 (pp. 200-209)
4. ✅ Move to Section 2: Partitioning and Secondary Indexes

---

## ❓ Troubleshooting

**Q: The output is too fast to read**
- A: Add `input()` calls in the code to pause between demos

**Q: I want to modify the code**
- A: Great! Try changing:
  - Number of partitions
  - Data distribution (more skewed)
  - Key splitting count
  - Partition boundaries

**Q: How do I run just one demo?**
- A: Edit the `main()` function and comment out the demos you don't want

---

**Ready? Start with `python 01_key_range_partitioning.py`!** 🚀
