# QUICKSTART: Section 3 — Rebalancing Partitions

## 🎯 5-Minute Overview

**Rebalancing** is how distributed databases handle cluster changes (adding/removing nodes). There are three main strategies:

### Strategy 1: Fixed Partition Count
```
Create 1000 partitions upfront for a 10-node cluster.
Each node gets 100 partitions.

When you add a new node:
  • New node "steals" partitions from existing nodes
  • Partition boundaries NEVER change
  • Rebalancing = bulk file moves (simple!)

Trade-off:
  ✅ Simple to understand
  ❌ Must guess partition count upfront
```

### Strategy 2: Dynamic Partitioning
```
Start with 1 partition. As data grows, split it.

When partition exceeds 10GB:
  • Split into two 5GB partitions
  • Number of partitions grows with dataset

Trade-off:
  ✅ Automatic adaptation
  ❌ Cold-start problem: new DB starts with 1 partition (bottleneck!)
  ❌ More complex to implement
```

### Strategy 3: Consistent Hashing with vnodes
```
Each physical node owns multiple virtual nodes (vnodes).
Cassandra uses 256 vnodes per node by default.

When you add a node:
  • It takes ownership of some vnodes
  • Only ~1/N of keys need to move
  • Partition size grows with dataset

Trade-off:
  ✅ Minimal data movement on node join/leave
  ✅ Decentralized (no coordinator needed)
  ❌ More complex to understand
```

## 🚀 Quick Start (10 minutes)

### Step 1: Run Exercise 1 (Fixed Partitions)
```bash
python 01_fixed_partitions.py
```

**What you'll see:**
- How 1000 partitions are distributed across 10 nodes
- What happens when you add 5 new nodes
- Why partition count matters
- How much data moves during rebalancing

**Key insight:** With fixed partitions, only ~10% of data moves when adding a node (vs ~90% with hash(key) % N).

### Step 2: Run Exercise 2 (Dynamic Partitioning)
```bash
python 02_dynamic_partitioning.py
```

**What you'll see:**
- The cold-start problem: new DB starts with 1 partition
- How pre-splitting avoids the bottleneck
- Automatic split and merge in action
- How partition boundaries change

**Key insight:** Dynamic partitioning adapts to data growth, but requires pre-splitting to avoid cold-start bottleneck.

### Step 3: Run Exercise 3 (Consistent Hashing)
```bash
python 03_consistent_hashing.py
```

**What you'll see:**
- How consistent hashing distributes keys
- What happens when nodes join/leave
- Impact of vnodes per node
- Why Cassandra uses 256 vnodes

**Key insight:** Consistent hashing avoids the hash(key) % N problem. Only ~1/N of keys move when adding a node.

### Step 4: Run Exercise 4 (Challenges)
```bash
python 04_rebalancing_challenges.py
```

**What you'll see:**
- How automatic rebalancing can cause cascading failures
- How hot spots develop and can't be fixed by rebalancing
- Data movement overhead
- Why manual approval is safer than automatic rebalancing

**Key insight:** Automatic rebalancing is risky. Manual approval prevents cascading failures.

## 📊 Comparison Table

| Aspect | Fixed | Dynamic | Consistent Hash |
|--------|-------|---------|-----------------|
| **Partition boundaries** | Fixed forever | Change (split/merge) | Change (vnodes) |
| **Partition count** | Fixed upfront | Grows with data | Grows with nodes |
| **Rebalancing** | Manual reassign | Auto split/merge | Auto redistribute |
| **Upfront planning** | Guess size | None | None |
| **Complexity** | Low | Medium | Medium |
| **Cold-start problem** | No | Yes | No |
| **Data movement** | ~1/N of data | Varies | ~1/N of data |
| **Used by** | Riak, ES | HBase, MongoDB | Cassandra, Riak |

## 💡 Key Insights from DDIA

### 1. The hash(key) % N Problem
```
WRONG: partition = hash(key) % number_of_nodes

Why it fails:
  • Adding 1 node to 10 nodes changes modulo for ~90% of keys
  • ~90% of data must move across network
  • Wildly impractical!

SOLUTION: Use fixed partitions or consistent hashing
  • Only ~10% of data moves
  • Much more practical
```

### 2. The Cold-Start Problem
```
Dynamic partitioning starts with 1 partition.
All writes go to ONE node until it grows large enough to split.
This is a bottleneck!

SOLUTION: Pre-splitting
  • Create multiple empty partitions at database creation
  • Distributes writes from the start
  • Trade-off: requires knowing initial partition boundaries
```

### 3. Hot Spots Can't Be Fixed by Rebalancing
```
Scenario: A celebrity post goes viral.
Millions of reads target the same key.
That partition becomes a hot spot.

Rebalancing doesn't help:
  • Moving the partition just moves the problem
  • The fundamental issue is the skewed workload

SOLUTION: Application-level key splitting
  • Append random suffix: "post_8932_00" to "post_8932_99"
  • Splits load across 100 partitions
  • Trade-off: reads must query all 100 keys and merge
  • Only apply to keys known to be hot
```

### 4. Automatic Rebalancing Can Cause Cascading Failures
```
Scenario: Temporary network blip marks a node as dead.
System starts automatic rebalancing.
Rebalancing floods the network with data transfers.
Flooded network triggers more failure detections.
System spirals out of control.

SOLUTION: Manual approval
  • System suggests rebalancing plan
  • Human administrator reviews and approves
  • Prevents catastrophic cascades
  • Trade-off: adds delay but prevents disasters

Used by: Couchbase, Riak, Voldemort
```

## 🎓 What Each Exercise Teaches

### Exercise 1: Fixed Partitions
- Partition boundaries are fixed
- Only assignments to nodes change
- Rebalancing is simple (bulk file moves)
- Must choose partition count upfront
- Good rule of thumb: 100MB-few GB per partition

### Exercise 2: Dynamic Partitioning
- Boundaries change dynamically
- Automatic adaptation to data growth
- Cold-start problem requires pre-splitting
- More complex than fixed partitions
- Works well with key-range partitioning

### Exercise 3: Consistent Hashing
- Avoids hash(key) % N problem
- Virtual nodes enable fine-grained balancing
- Minimal data movement on cluster changes
- Partition size grows with dataset
- Used by Cassandra (256 vnodes/node)

### Exercise 4: Real-World Challenges
- Cascading failures from automatic rebalancing
- Hot spots require application-level fixes
- Data movement overhead
- Manual approval prevents disasters

## 🔍 Deep Dive: Cassandra's Approach

Cassandra uses **consistent hashing with vnodes**:

```
1. Each node owns 256 virtual nodes (vnodes)
2. Keys are hashed to positions on a ring
3. Each position is owned by the nearest node clockwise

When a node joins:
  • It takes ownership of some vnodes
  • Only ~1/256 of keys need to move per vnode
  • Total: ~1/N of keys move (where N = number of nodes)

When a node leaves:
  • Its vnodes are redistributed to other nodes
  • Again, only ~1/N of keys move

Result:
  • Minimal data movement
  • Decentralized (no coordinator needed)
  • Scales to thousands of nodes
```

## ❓ Common Questions

**Q: Why not just use hash(key) % N?**
A: Adding 1 node to 10 nodes causes ~90% of data to move. With fixed partitions or consistent hashing, only ~10% moves.

**Q: When should I use fixed partitions?**
A: When you can estimate dataset size and want simplicity. Used by Riak, Elasticsearch, Couchbase.

**Q: When should I use dynamic partitioning?**
A: When dataset size is unpredictable and you're using key-range partitioning. Used by HBase, MongoDB.

**Q: When should I use consistent hashing?**
A: When you need to handle dynamic cluster membership and want minimal data movement. Used by Cassandra, Riak.

**Q: Why does Cassandra use 256 vnodes?**
A: It's a sweet spot between load balancing (more vnodes = better) and management overhead (fewer vnodes = simpler).

**Q: How do I fix hot spots?**
A: Application-level key splitting. Append random suffix to hot keys to split load across multiple partitions.

**Q: Is automatic rebalancing safe?**
A: No. Temporary network blips can trigger cascading failures. Use manual approval instead.

## 📚 Next Steps

1. Run all 4 exercises in order
2. Modify the code to experiment:
   - Change partition count in Exercise 1
   - Change split/merge thresholds in Exercise 2
   - Change vnodes per node in Exercise 3
   - Simulate different failure scenarios in Exercise 4
3. Read DDIA Chapter 6 for deeper understanding
4. Move on to Section 4: Request Routing

---

**Ready to start?** Run `python 01_fixed_partitions.py` 🚀
