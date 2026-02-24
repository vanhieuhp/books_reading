# QUICKSTART: Secondary Indexes

Get up and running with secondary indexes in 3 steps.

## Step 1: Understand the Problem (5 minutes)

When you partition data across multiple nodes, secondary indexes become tricky.

**Example:** You have a database of cars partitioned by car ID:
- Partition 0: cars with IDs 1-100
- Partition 1: cars with IDs 101-200
- Partition 2: cars with IDs 201-300

Now you want to search for "all red cars". The problem: red cars could be in ANY partition!

**Two solutions:**

1. **Local Indexes** (each partition indexes its own data)
   - Write: ✅ Fast (update one partition's index)
   - Read: ❌ Slow (query all partitions, merge results)

2. **Global Indexes** (one index covers all data)
   - Write: ❌ Slow (update index on different node)
   - Read: ✅ Fast (query one index partition)

## Step 2: Run the Exercises (15 minutes)

Run each exercise in order. Read the output carefully — it tells a story.

### Exercise 1: Local Indexes (5 minutes)

```bash
python 01_local_indexes.py
```

**What you'll see:**
- How local indexes are structured
- Why writes are fast (single partition)
- Why reads are slow (scatter/gather all partitions)
- The tail latency problem

**Key insight:** With 100 partitions, even if 99 are fast, the query waits for the 1 slow one.

### Exercise 2: Global Indexes (5 minutes)

```bash
python 02_global_indexes.py
```

**What you'll see:**
- How global indexes are structured
- Why reads are fast (single index partition)
- Why writes are slow (cross-partition update)
- The eventual consistency window

**Key insight:** After a write, there's a delay before the index is updated.

### Exercise 3: Consistency Trade-offs (5 minutes)

```bash
python 03_index_consistency.py
```

**What you'll see:**
- Immediate consistency (local indexes)
- Eventual consistency (global indexes)
- The consistency window problem
- Real-world implications

**Key insight:** There's no perfect choice — it's always a trade-off.

## Step 3: Experiment (10 minutes)

Modify the code to see how behavior changes.

### Experiment 1: Increase Partition Count

In `01_local_indexes.py`, change:
```python
db = LocalIndexDatabase(num_partitions=5)
```
to:
```python
db = LocalIndexDatabase(num_partitions=100)
```

**What happens:** Tail latency increases dramatically (slowest partition determines query time).

### Experiment 2: Async Index Updates

In `02_global_indexes.py`, change:
```python
db.insert(doc, async_index=False)  # Synchronous
```
to:
```python
db.insert(doc, async_index=True)   # Asynchronous
```

**What happens:** Writes are faster, but searches don't see recent writes.

### Experiment 3: Consistency Window

In `03_index_consistency.py`, modify `demo_3_consistency_window_duration()`:
```python
for i in range(100):  # Change to 1000
    db.insert(f"doc_{i}", color="red", brand="Ferrari")
```

**What happens:** Larger consistency window (more pending updates).

## 🎯 Key Takeaways

### Local Indexes
```
Write: ✅ Fast (one partition)
Read:  ❌ Slow (all partitions)
Consistency: ✅ Immediate

Best for: write-heavy workloads (logs, events, sensors)
Used by: MongoDB, Cassandra, Elasticsearch
```

### Global Indexes
```
Write: ❌ Slow (different node)
Read:  ✅ Fast (one partition)
Consistency: ⏳ Eventual

Best for: read-heavy workloads (search, analytics)
Used by: DynamoDB, Oracle, Riak
```

### The Trade-off
```
Choose LOCAL if:
  ✅ You need immediate consistency
  ✅ Writes are more common than reads
  ✅ You can tolerate slow searches

Choose GLOBAL if:
  ✅ You can tolerate eventual consistency
  ✅ Reads are more common than writes
  ✅ You need fast searches
```

## 💡 Real-World Examples

### DynamoDB Global Secondary Indexes
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

Application pattern:
  1. Write document (immediately consistent)
  2. Query local index (may scatter/gather)
  3. Or use aggregation pipeline for complex queries
```

## 🤔 Think About Your Workload

**Question 1: What's your read/write ratio?**
- Mostly reads? → Use global indexes (fast searches)
- Mostly writes? → Use local indexes (fast writes)
- Balanced? → Depends on your consistency needs

**Question 2: How important is consistency?**
- Critical? → Use local indexes (immediately consistent)
- Can tolerate delay? → Use global indexes (eventually consistent)

**Question 3: How many partitions do you have?**
- Few (< 10)? → Local indexes are acceptable (tail latency is low)
- Many (> 100)? → Global indexes are better (avoid tail latency)

## 📚 Next Steps

1. **Read DDIA Chapter 6, Section 2** (pp. 208-217)
2. **Explore the code** — modify parameters and see what happens
3. **Think about your system** — would you use local or global indexes?
4. **Move to Section 3** — Rebalancing Partitions

## 🎓 Interview Prep

**Q: What's the difference between local and global indexes?**

A: Local indexes are maintained by each partition (fast writes, slow reads). Global indexes cover all data but are partitioned by term (slow writes, fast reads).

**Q: Why is scatter/gather expensive?**

A: You must query all partitions and merge results. Tail latency: the slowest partition determines query time. With thousands of partitions, this becomes severe.

**Q: Why are global indexes usually eventually consistent?**

A: Distributed transactions are complex and slow. Most systems update the index asynchronously, creating a consistency window.

**Q: How does DynamoDB handle this?**

A: Primary index is hash-based (fast point lookups). GSI is term-partitioned (fast searches). Consistency is eventual. Applications must handle the consistency window.

---

**Ready to dive deeper?** Read the full README.md for more details and real-world examples.
