# Section 3: Rebalancing Partitions — Hands-On Exercises

## 🎯 Learning Objectives

By completing these 4 exercises, you will:

1. ✅ **Understand fixed partition count strategy** — partition boundaries fixed, assignments change
2. ✅ **See dynamic partitioning in action** — automatic split/merge as data grows
3. ✅ **Learn consistent hashing with vnodes** — how Cassandra handles cluster membership
4. ✅ **Experience real-world challenges** — cascading failures, hot spots, data movement

## 📁 Exercise Files

| # | File | DDIA Concept | Time |
|---|------|-------------|------|
| 1 | `01_fixed_partitions.py` | Fixed partition count strategy | 30 min |
| 2 | `02_dynamic_partitioning.py` | Dynamic split/merge rebalancing | 30 min |
| 3 | `03_consistent_hashing.py` | Consistent hashing with vnodes | 30 min |
| 4 | `04_rebalancing_challenges.py` | Cascading failures, hot spots, manual vs auto | 45 min |

**Total time**: ~2.5 hours

## 🚀 How to Run

```bash
# No dependencies needed! Just run with Python 3.8+

# Exercise 1: Fixed partition count strategy
python 01_fixed_partitions.py

# Exercise 2: Dynamic partitioning (split/merge)
python 02_dynamic_partitioning.py

# Exercise 3: Consistent hashing with vnodes
python 03_consistent_hashing.py

# Exercise 4: Rebalancing challenges
python 04_rebalancing_challenges.py
```

## 🗺️ Mapping to DDIA Chapter 6

```
Exercise 1  →  "Strategy 1: Fixed Number of Partitions" (pp. 203-207)
Exercise 2  →  "Strategy 2: Dynamic Partitioning" (pp. 207-209)
Exercise 3  →  "Strategy 3: Partitioning Proportionally to Nodes" (pp. 209-211)
Exercise 4  →  "Automatic vs Manual Rebalancing" (pp. 211-215)
```

## 📊 What You'll See

Each exercise produces **rich, visual output** that tells a story:

### Exercise 1 Output Preview:
```
================================================================================
DEMO 1: Initial Cluster Setup with Fixed Partitions
================================================================================

  ✅ Created 1000 partitions
     Key range: (0, 100000)
  ✅ Added 10 nodes
  ✅ Initial partition assignment (round-robin)

────────────────────────────────────────────────────────
  📊 Initial Load Distribution
────────────────────────────────────────────────────────
  Node  0: 100 partitions,     1234 bytes
  Node  1: 100 partitions,     1289 bytes
  ...
  Imbalance ratio: 1.05x
```

### Exercise 2 Output Preview:
```
================================================================================
DEMO 1: The Cold-Start Problem
================================================================================

  After   0 inserts: 1 partitions, 0 bytes
  After  20 inserts: 1 partitions, 2345 bytes
  After  40 inserts: 2 partitions, 4567 bytes  ← SPLIT!
  After  60 inserts: 4 partitions, 6789 bytes  ← SPLIT!
  After  80 inserts: 8 partitions, 8901 bytes  ← SPLIT!

  ✅ After splits: 8 partitions
     Load is now distributed! ✅
```

### Exercise 3 Output Preview:
```
================================================================================
DEMO 2: Adding Nodes with Consistent Hashing
================================================================================

  Initial state: 3 nodes
     Node 0: 1000 keys
     Node 1: 1001 keys
     Node 2: 999 keys

  ✅ Node 3 joined
  ✅ Node 4 joined

  New distribution:
     Node 0: 800 keys
     Node 1: 801 keys
     Node 2: 799 keys
     Node 3: 800 keys
     Node 4: 800 keys

  Imbalance ratio: 1.00x
```

### Exercise 4 Output Preview:
```
================================================================================
DEMO 1: Cascading Failures from Automatic Rebalancing
================================================================================

  ⚠️  Network Blip: Node 2 Marked as Dead
  Node 2 is now UNHEALTHY

  🔄 Automatic Rebalancing Triggered
  System detects node 2 is down
  Starting automatic rebalancing...

  ✅ Rebalancing complete
     Partitions moved: 45
     Data moved: 123,456 bytes
     Network bandwidth used: 123,456 bytes
```

## 🎓 Key Concepts per Exercise

### Exercise 1: Fixed Partition Count
- Partition boundaries are **fixed forever**
- Only partition-to-node assignments change
- Rebalancing = bulk file moves (simple!)
- Must choose partition count upfront (100MB-few GB each)
- Used by: Riak, Elasticsearch, Couchbase

### Exercise 2: Dynamic Partitioning
- Partition boundaries change dynamically (split/merge)
- Number of partitions adapts to dataset size
- Cold-start problem: new DB starts with 1 partition
- Pre-splitting: create initial partitions to avoid bottleneck
- Used by: HBase, MongoDB, RethinkDB

### Exercise 3: Consistent Hashing with vnodes
- Consistent hashing avoids hash(key) % N problem
- Virtual nodes (vnodes) enable fine-grained load balancing
- Adding a node: only ~1/N of keys need to move
- Partition size grows with dataset (not node count)
- Used by: Cassandra (256 vnodes/node), Riak, Voldemort

### Exercise 4: Rebalancing Challenges
- Automatic rebalancing can cause cascading failures
- Hot spots can't be fixed by rebalancing alone
- Application-level key splitting fixes hot spots
- Manual approval prevents cascading failures
- Trade-off: manual is slower but safer

## 💡 Exercises to Try After Running

1. **Modify partition count** — what happens with 10 vs 10,000 partitions?
2. **Change split/merge thresholds** — how does this affect rebalancing?
3. **Increase vnodes per node** — does load balance better?
4. **Simulate node failures** — what happens during cascading failures?
5. **Create skewed workloads** — see how hot spots develop

## ✅ Completion Checklist

- [ ] Exercise 1: Understand fixed partition strategy and rebalancing
- [ ] Exercise 2: Can explain cold-start problem and pre-splitting
- [ ] Exercise 3: Understand consistent hashing and vnodes
- [ ] Exercise 4: Can identify cascading failures and hot spot solutions

## 📚 Next Steps

After completing Section 3:
1. ✅ You understand all three rebalancing strategies
2. ✅ You know the trade-offs between them
3. ✅ You understand real-world challenges
4. ✅ Ready for Section 4: Request Routing

---

**Start with `01_fixed_partitions.py`!** 🚀
