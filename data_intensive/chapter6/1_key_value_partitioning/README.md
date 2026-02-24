# Section 1: Partitioning of Key-Value Data — Hands-On Exercises

## 🎯 Learning Objectives

By completing these 4 exercises, you will:

1. ✅ **Understand key range partitioning** — how to assign keys to partitions based on ranges
2. ✅ **Understand hash partitioning** — how to use hash functions to distribute keys uniformly
3. ✅ **Learn compound primary keys** — the hybrid approach (hash + sort) used by Cassandra
4. ✅ **Handle hot spots** — how to detect and fix skewed workloads

## 📁 Exercise Files

| # | File | DDIA Concept | Time |
|---|------|-------------|------|
| 1 | `01_key_range_partitioning.py` | Range-based key assignment | 30 min |
| 2 | `02_hash_partitioning.py` | Hash-based key distribution | 30 min |
| 3 | `03_compound_keys.py` | Hybrid approach (Cassandra-style) | 30 min |
| 4 | `04_hot_spot_solutions.py` | Handling skewed workloads | 30 min |

**Total time**: ~2 hours

## 🚀 How to Run

```bash
# No dependencies needed! Just run with Python 3.8+

# Exercise 1: Key range partitioning
python 01_key_range_partitioning.py

# Exercise 2: Hash partitioning
python 02_hash_partitioning.py

# Exercise 3: Compound primary keys
python 03_compound_keys.py

# Exercise 4: Hot spot solutions
python 04_hot_spot_solutions.py
```

## 🗺️ Mapping to DDIA Chapter 6, Section 1

```
Exercise 1  →  "Partitioning by Key Range" (pp. 200-203)
Exercise 2  →  "Partitioning by Hash of Key" (pp. 203-206)
Exercise 3  →  "Hybrid Approach: Compound Primary Keys" (pp. 206-207)
Exercise 4  →  "Handling Skewed Workloads and Hot Spots" (pp. 207-209)
```

## 📊 What You'll See

Each exercise produces **rich, visual output** that tells a story:

### Exercise 1 Output Preview:
```
================================================================================
DEMO 1: Basic Key Range Partitioning
================================================================================

📚 Partition setup:
   Partition(0, range=('A', 'H'), size=0)
   Partition(1, range=('H', 'P'), size=0)
   Partition(2, range=('P', 'Z'), size=0)

📝 Inserting data:
   Alice      → Partition 0
   Bob        → Partition 1
   Charlie    → Partition 1
   ...

📊 Partition Distribution
   Partition 0 (A-H): 3 keys → ['Alice', 'Diana', 'Grace']
   Partition 1 (H-P): 4 keys → ['Bob', 'Charlie', 'Henry', 'Jack']
   Partition 2 (P-Z): 3 keys → ['Eve', 'Frank', 'Iris']
```

### Exercise 2 Output Preview:
```
================================================================================
DEMO 1: Hash Distribution
================================================================================

🔢 Partition setup (4 partitions):
   Partition(0, hash_range=(0, 536870912), size=0)
   Partition(1, hash_range=(536870912, 1073741824), size=0)
   ...

📝 Inserting sequential user IDs (user_001, user_002, ...):
   user_001 → hash=1234567890 → Partition 2
   user_002 → hash=9876543210 → Partition 0
   user_003 → hash=5555555555 → Partition 1
   ...

📊 Partition Distribution (Balanced!)
   Partition 0: 3 keys ███
   Partition 1: 3 keys ███
   Partition 2: 3 keys ███
   Partition 3: 3 keys ███
```

### Exercise 3 Output Preview:
```
================================================================================
DEMO 2: Efficient Range Queries Within a Partition
================================================================================

🔍 Range Query: user_42 from Jan 1-3
   Query: SELECT * FROM events WHERE user_id='user_42' AND timestamp BETWEEN '2024-01-01' AND '2024-01-03'

   ✅ Touched 1 partition (efficient!)
   Found 3 results:
     2024-01-01T10:00:00 → logged in
     2024-01-02T14:30:00 → updated profile
     2024-01-03T09:15:00 → posted comment
```

### Exercise 4 Output Preview:
```
================================================================================
DEMO 1: The Celebrity Problem
================================================================================

📊 Partition Load (Hot Spot!)
   Partition 0:  300 writes ██████
   Partition 1:  300 writes ██████
   Partition 2: 1300 writes ██████████████████████████
   Partition 3:  100 writes ██

   Viral post partition: 1300/2000 writes (65%)
   ⚠️  HOT SPOT: One partition handles most of the load!
```

## 🎓 Key Concepts per Exercise

### Exercise 1: Key Range Partitioning

**How it works:**
- Assign continuous ranges of keys to partitions
- Like encyclopedia volumes: A-H, H-P, P-Z
- Keys within a partition are sorted

**Pros:**
- ✅ Efficient range queries (only touch relevant partitions)
- ✅ Data locality (related keys live together)

**Cons:**
- ❌ Hot spots when writes cluster (e.g., all writes for "now")
- ❌ Uneven distribution if data is skewed

**Real users:** HBase, Bigtable, RethinkDB, MongoDB (before v2.4)

---

### Exercise 2: Hash Partitioning

**How it works:**
- Hash function scrambles keys uniformly
- Distribute even skewed data evenly across partitions
- Use deterministic hash (MD5, MurmurHash, not Python's hash())

**Pros:**
- ✅ Excellent at eliminating hot spots
- ✅ Even load distribution

**Cons:**
- ❌ Range queries are slow (must query all partitions)
- ❌ Simple `hash(key) % N` causes massive data movement on rebalancing

**Real users:** Cassandra, Riak, Voldemort, Redis Cluster, DynamoDB

---

### Exercise 3: Compound Primary Keys

**How it works:**
- First column is HASHED (determines partition)
- Remaining columns are SORTED (enables range queries within partition)
- Best of both worlds!

**Example:** `PRIMARY KEY (user_id, timestamp)`
- `user_id` is hashed → determines which partition
- `timestamp` is sorted within partition → efficient range queries

**Pros:**
- ✅ No hot spots (hashing spreads load)
- ✅ Efficient range queries within partition (e.g., "my events from Jan 1-5")

**Cons:**
- ❌ Cross-partition range queries are slow (e.g., "all events from Jan 1-5")

**Real users:** Cassandra, DynamoDB, HBase

**Perfect for:** Social media feeds, IoT sensor data, time-series workloads

---

### Exercise 4: Handling Hot Spots

**The Problem:**
- Millions of requests target the same key (e.g., viral post)
- Even with hash partitioning, that key maps to ONE partition
- That partition becomes a hot spot
- Databases can't fix this automatically

**The Solution: Key Splitting**
- Instead of writing to `post_8932`, write to:
  - `post_8932_00`, `post_8932_01`, ..., `post_8932_99`
- Spreads load across multiple partitions

**Trade-off:**
- ✅ Writes are fast (spread across partitions)
- ❌ Reads are slow (must query all split keys and merge)

**When to use:**
- Only split keys you KNOW are hot
- Monitor partition load and detect hot keys
- Remove splitting when keys cool down

---

## 💡 Exercises to Try After Running

1. **Modify partition count** — what happens with 2 partitions? 10? 100?
2. **Change data distribution** — make it more skewed and see the effect
3. **Experiment with key splitting** — try different split counts (10, 50, 100)
4. **Combine approaches** — use compound keys with hot spot detection

## 🔄 Comparison Table: All Strategies

| Strategy | Range Queries | Hot Spots | Load Balance | Real Users |
|----------|---------------|-----------|--------------|-----------|
| **Range Partitioning** | ✅ Fast (1 partition) | ❌ Yes | ❌ Uneven | HBase, Bigtable |
| **Hash Partitioning** | ❌ Slow (all partitions) | ✅ No | ✅ Even | Cassandra, Riak |
| **Compound Keys** | ✅ Fast (within partition) | ✅ No | ✅ Even | Cassandra, DynamoDB |
| **+ Hot Spot Splitting** | ⚠️ Slow (split keys) | ✅ No | ✅ Even | All systems |

## ✅ Completion Checklist

- [ ] Exercise 1: Understand range partitioning and hot spots
- [ ] Exercise 2: Understand hash partitioning and why it eliminates hot spots
- [ ] Exercise 3: Understand compound keys and their trade-offs
- [ ] Exercise 4: Understand hot spot detection and key splitting

## 📚 Next Steps

After completing Section 1:
1. ✅ You understand how keys are assigned to partitions
2. ✅ You know the trade-offs between range and hash partitioning
3. ✅ You understand why compound keys are powerful
4. ✅ Ready for Section 2: Partitioning and Secondary Indexes

---

## 🎯 Key Takeaways

1. **Range Partitioning:** Fast range queries, but hot spots
2. **Hash Partitioning:** No hot spots, but slow range queries
3. **Compound Keys:** Best of both (hash + sort)
4. **Hot Spots:** Unavoidable in some cases, fix with application-level key splitting
5. **Trade-offs:** Every partitioning strategy has trade-offs — choose based on your workload

---

**Start with `01_key_range_partitioning.py`!** 🚀
