# QUICKSTART: Linearizability in 3 Steps

Get up to speed with linearizability in just 3 steps.

## Step 1: Understand the Core Concept (5 minutes)

**Linearizability = "Behave as if there is only one copy of the data"**

Once a write completes, ALL subsequent reads see the new value.

```
Timeline:
         0ms          50ms         100ms         150ms
Client A: ──write(x=1)────────────────|
Client B:          ──read(x)────|
Client C:                   ──read(x)──────|

Linearizable: B reads 1, C reads 1 ✓
Non-Linearizable: B reads 0, C reads 1 ✗
```

**Key Rule:** Once ANY client has seen a new value, ALL subsequent reads must also see that new value.

---

## Step 2: Run the Code Examples (5 minutes)

```bash
python 01_linearizability_basics.py
```

This demonstrates:
1. **Linearizability vs Non-Linearizability** - See the difference
2. **Total Order** - All operations have a single, global order
3. **CAP Theorem** - The consistency vs availability trade-off
4. **Performance Cost** - Why linearizability is slower
5. **Compare-and-Set** - Why it requires linearizability

---

## Step 3: Learn the Key Concepts (10 minutes)

### Why Linearizability Matters

#### 1. Leader Election
- Without: Two nodes both think they're the leader (split-brain)
- With: Only one node can acquire the lock

#### 2. Unique Constraints
- Without: Two users can register the same username
- With: Exactly one user succeeds (using compare-and-set)

#### 3. Cross-Channel Dependencies
- Without: Write to database, send notification, consumer reads stale data
- With: Once write completes, notification is sent, consumer sees write

### The CAP Theorem

During a network partition, choose:
- **CP (Consistent + Partition-tolerant):** Reject requests on minority side
  - Examples: ZooKeeper, etcd
- **AP (Available + Partition-tolerant):** Accept requests, but data may be stale
  - Examples: Cassandra, DynamoDB

### Performance Cost

Linearizable write requires 2 round-trips:
```
1. Client → Leader
2. Leader → Replicas
3. Wait for quorum
4. Leader → Client
```

Non-linearizable write requires 1 round-trip:
```
1. Client → Primary
2. Primary acknowledges immediately
```

**Result:** Linearizability is ~2x slower

---

## Quick Reference

### Linearizability vs Other Models

| Model | Guarantee | Example |
|-------|-----------|---------|
| **Linearizability** | Single-object, real-time | "Once write completes, all reads see new value" |
| **Causal Consistency** | Preserves cause-and-effect | "If A caused B, all nodes see A before B" |
| **Eventual Consistency** | Eventually converge | "Replicas will eventually agree" |

### Key Terminology

- **Linearizability:** Behaves as if one copy of data
- **Total Order:** Every pair of operations is ordered
- **Quorum:** Majority of nodes (more than half)
- **CAP Theorem:** Choose Consistency or Availability during partitions
- **Compare-and-Set (CAS):** "Set value only if it's currently X"

---

## Next Steps

1. **Read the Teaching Guide:** [TEACHING_GUIDE.md](./TEACHING_GUIDE.md)
   - Deep dive into each concept
   - Interview questions with answers
   - Hands-on exercises

2. **Experiment with the Code:**
   - Modify `01_linearizability_basics.py`
   - Try different scenarios
   - Measure latencies

3. **Answer Interview Questions:**
   - What is linearizability?
   - Explain the CAP theorem
   - Why is linearizability expensive?
   - How does compare-and-set work?

4. **Design Your Own System:**
   - How would you implement leader election?
   - How would you prevent split-brain?
   - How would you handle network partitions?

---

## Common Misconceptions

❌ **"Linearizability = No Concurrency"**
✓ Linearizability allows concurrent operations. It just means there's a total order.

❌ **"Linearizability = Serializability"**
✓ They're different. Linearizability is single-object, real-time. Serializability is multi-object, transaction isolation.

❌ **"CAP Means You Must Always Choose"**
✓ CAP only applies during network partitions. In normal operation, you can have all three.

---

## Key Takeaways

1. **Linearizability = "one copy of data"**
2. **Once a write completes, ALL reads see the new value**
3. **Linearizability implies a total order of operations**
4. **CAP Theorem: Choose Consistency or Availability during partitions**
5. **Linearizability has performance cost (requires quorum confirmation)**
6. **Used for: leader election, unique constraints, cross-channel dependencies**
7. **Implemented via: consensus algorithms (Raft, Paxos), single-leader replication**

---

**Ready to dive deeper? Read [TEACHING_GUIDE.md](./TEACHING_GUIDE.md) next!**
