# Quick Reference: Chapter 9, Section 3 - Ordering Guarantees

## 🎯 Learning Path

### Step 1: Understand the Concepts (Read textbook.md)
- Causal ordering (partial order)
- Total order
- Total order broadcast
- Relationship to linearizability

### Step 2: Run Code Examples
```bash
# Start with causal ordering
python 01_causal_ordering.py

# Then total order broadcast
python 02_total_order_broadcast.py

# Compare different guarantees
python 03_ordering_comparison.py
```

### Step 3: Study Interview Questions
```bash
python teaching_guide.py
```

---

## 📚 Key Concepts at a Glance

### Causal Ordering (Partial Order)
```
Question → Answer → Comment
(causally related, must be in this order)

Question A and Question B
(concurrent, can be in any order)
```

**Guarantee:** If A caused B, all nodes see A before B
**Concurrent events:** Can be in any order
**Strength:** Weaker than total order
**Efficiency:** More efficient, lower latency

### Total Order
```
All nodes see: Event1 → Event2 → Event3 → Event4
(same order on all nodes)
```

**Guarantee:** All nodes see events in the same order
**Concurrent events:** Have a defined order
**Strength:** Stronger than causal
**Implementation:** Single-leader replication log

### Total Order Broadcast
```
1. Reliable delivery: All nodes get all messages
2. Total ordering: All nodes deliver in same order
```

**Equivalent to:** Consensus (can implement one using the other)
**Implementation:** Replication log in PostgreSQL, MySQL, MongoDB
**Use case:** Distributed transactions, leader election

### Linearizability
```
Total order + Real-time consistency
```

**Guarantee:** Total order consistent with real-time
**Strength:** Strongest single-object guarantee
**Cost:** Higher latency (need quorum writes)
**Example:** ZooKeeper, etcd, Spanner

---

## 🔄 Ordering Hierarchy

```
Strongest ────────────────────────────────────────── Weakest
   │                                                    │
   ▼                                                    ▼

Strict Serializability
   ↑
Linearizability (+ real-time)
   ↑
Total Order (all nodes same order)
   ↑
Causal Consistency (preserve cause-effect)
   ↑
Eventual Consistency (no ordering guarantee)
```

---

## 🧮 Vector Clocks

Track causal relationships:

```
Node A: [1, 0, 0] → sends message → [2, 0, 0]
Node B: receives [2, 0, 0] → [2, 1, 0] → local event → [2, 2, 0]
Node C: receives [2, 2, 0] → [2, 2, 1]

Causality: A → B → C (can be detected from vector clocks)
```

---

## 💡 Interview Questions Summary

| # | Question | Difficulty | Key Insight |
|---|----------|-----------|------------|
| 1 | Causal vs Total Order | Medium | Causal = partial order, Total = total order |
| 2 | Total Order Broadcast & Consensus | Hard | They're equivalent in power |
| 3 | Total Order Broadcast & Linearizability | Hard | TOB can implement linearizable storage |
| 4 | Vector Clocks | Hard | Track causality with logical timestamps |
| 5 | Single-Leader Replication | Medium | Provides total order broadcast |
| 6 | Why TOB ≡ Consensus | Hard | Both require all nodes to agree |
| 7 | Causal vs Total Trade-offs | Medium | Causal: faster, Total: stronger |
| 8 | Distributed Counter | Hard | Broadcast increments, apply in order |

---

## 🏗️ Real-World Systems

| System | Ordering | Algorithm | Use Case |
|--------|----------|-----------|----------|
| PostgreSQL | Total Order | Single-leader replication | OLTP databases |
| Cassandra | Eventual | Multi-leader | High availability |
| Kafka | Total Order (per partition) | Partitioned log | Event streaming |
| ZooKeeper | Linearizability | ZAB consensus | Coordination |
| etcd | Linearizability | Raft consensus | Kubernetes state |
| CockroachDB | Strict Serializability | Raft + transactions | Distributed SQL |

---

## 🎓 Study Tips

1. **Run the code first** - See concepts in action
2. **Modify parameters** - Change timeouts, partition sizes
3. **Answer questions** - Try without looking at answers
4. **Think about trade-offs** - Consistency vs Performance
5. **Design exercises** - Implement your own ordering system

---

## 📖 File Guide

| File | Purpose | Time |
|------|---------|------|
| 01_causal_ordering.py | Understand causal ordering & vector clocks | 5 min |
| 02_total_order_broadcast.py | Learn total order broadcast & consensus | 5 min |
| 03_ordering_comparison.py | Compare all ordering guarantees | 5 min |
| teaching_guide.py | Interview preparation | 30 min |

---

## ✅ Checklist

- [ ] Read textbook.md section 3
- [ ] Run 01_causal_ordering.py
- [ ] Run 02_total_order_broadcast.py
- [ ] Run 03_ordering_comparison.py
- [ ] Answer all 8 interview questions
- [ ] Understand vector clocks
- [ ] Understand total order broadcast
- [ ] Understand relationship to consensus
- [ ] Understand trade-offs between ordering guarantees
- [ ] Can explain to someone else

---

## 🚀 Next Steps

After mastering ordering guarantees:
1. Study consensus algorithms (Raft, Paxos)
2. Learn about distributed transactions
3. Explore coordination services (ZooKeeper)
4. Study real-world systems (PostgreSQL, Kafka, etcd)

---

**Start here:** `python 01_causal_ordering.py`
