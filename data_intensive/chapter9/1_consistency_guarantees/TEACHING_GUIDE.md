# Teaching Guide: Chapter 9, Section 1 — Consistency Guarantees

## Overview

This teaching guide provides deep explanations for Chapter 9, Section 1 of *Designing Data-Intensive Applications*. The section covers the different consistency guarantees that distributed systems can provide, from the weakest (eventual consistency) to the strongest (linearizability).

---

## 1. The Consistency Spectrum

### Why This Matters

In Chapter 8, we learned that distributed systems are unreliable. Chapter 9 asks: **How do we build reliable systems despite these faults?**

The answer starts with understanding **consistency guarantees** — the promises a system makes about what values you'll read after a write.

Different systems make different promises:
- **Weak promises** = High availability, low latency, but you might read stale data
- **Strong promises** = Guaranteed correctness, but lower availability and higher latency

There is no "best" consistency model. The right choice depends on your application's needs.

---

## 2. Eventual Consistency (Weakest)

### What It Is

**Eventual Consistency** means: If you stop writing, and wait long enough, all replicas will eventually converge to the same value.

**Key phrase:** "Eventually" — but there's no guarantee about WHEN.

### The Promise

```
Write: x = 1 on Node A
  ↓
Node A: x = 1 ✓
Node B: x = 0 (stale)
Node C: x = 0 (stale)
  ↓ (after some time)
Node A: x = 1 ✓
Node B: x = 1 ✓
Node C: x = 1 ✓
```

### The Problem: Stale Reads

```
Timeline:
  T=0ms: Alice writes x = 1 to Node A
  T=1ms: Bob reads x from Node B (gets x = 0, the old value!)
  T=100ms: Bob reads x from Node A (gets x = 1)
  T=200ms: Bob reads x from Node B (finally gets x = 1)

Bob sees: 0 → 1 → 0 → 1

This is confusing and error-prone!
```

### When to Use

- **Social media feeds:** If you see an old version of a post for a few seconds, it's okay.
- **Caches:** Stale data is acceptable; freshness is not critical.
- **Analytics:** Approximate counts are fine; exact counts can wait.
- **NoSQL databases:** Cassandra, DynamoDB, Riak default to eventual consistency.

### When NOT to Use

- **Financial transactions:** You cannot accept stale account balances.
- **Inventory systems:** You cannot oversell items.
- **User authentication:** You cannot accept stale permission data.

### Real-World Example: Cassandra

Cassandra uses eventual consistency by default. When you write to Cassandra:

```
1. Write goes to one replica (the "coordinator")
2. Coordinator returns success immediately
3. Coordinator sends the write to other replicas in the background
4. If a replica is down, it gets the write later (via "hinted handoff")

Result: Write is acknowledged before all replicas have it!
```

---

## 3. Causal Consistency (Middle Ground)

### What It Is

**Causal Consistency** means: If event A causally caused event B, then every node must see A before B.

**Causality** = "happened before" relationship. If A is a question and B is the answer, A causally caused B.

### The Promise

```
Timeline:
  T=0ms: Alice posts question: "What is 2+2?"
  T=10ms: Bob posts answer: "4"

Causally consistent: Every node that sees Bob's answer must also see Alice's question.

Non-causally consistent: A node might see Bob's answer without seeing Alice's question!
```

### Concurrent Events

Events that are NOT causally related (concurrent) can be seen in any order:

```
Timeline:
  T=0ms: Alice posts "Hello" on Node A
  T=0ms: Bob posts "Hi" on Node B (at the same time, different nodes)

These are concurrent (neither caused the other).

Causal consistency allows:
  - Node 1 sees: "Hello", then "Hi"
  - Node 2 sees: "Hi", then "Hello"

Both are valid because the events are concurrent.
```

### How It Works: Vector Clocks

Causal consistency is implemented using **vector clocks** — a way to track causality without relying on wall-clock time.

```
Vector Clock Example:

Node A: [1, 0, 0]  (Node A has seen 1 event from itself)
  ↓ (sends message to Node B)
Node B: [1, 1, 0]  (Node B has seen 1 event from A, 1 from itself)
  ↓ (sends message to Node C)
Node C: [1, 1, 1]  (Node C has seen 1 from A, 1 from B, 1 from itself)

If Node C receives a message with vector clock [1, 0, 0]:
  - It knows this message is from Node A
  - It knows Node B hasn't seen this message yet
  - It can order events correctly
```

### When to Use

- **Collaborative editing:** If Alice edits a document and then Bob edits it, Bob's editor should see Alice's changes first.
- **Social media comments:** If Alice posts a comment and Bob replies to it, everyone should see the comment before the reply.
- **Message boards:** Threads should maintain causality (question before answer).

### When NOT to Use

- **Inventory systems:** Causality doesn't help with concurrent writes to the same item.
- **Financial transactions:** You need stronger guarantees than causality.

### Real-World Example: Git

Git uses causality (DAG — Directed Acyclic Graph) to track commits:

```
Commit A: "Add feature X"
  ↓
Commit B: "Fix bug in feature X"

Git ensures that if you see Commit B, you also see Commit A.
This is causal consistency!
```

---

## 4. Linearizability (Strongest)

### What It Is

**Linearizability** means: The system behaves **as if there is only one copy of the data**, and every operation takes effect atomically at some point between its start and end.

**Key insight:** Once ANY client has seen a new value, ALL subsequent reads by ALL clients must also see that new value (or a newer one).

### The Promise

```
Timeline:
         0ms          50ms         100ms         150ms
Client A: ──write(x=1)────────────────|
Client B:          ──read(x)────|
Client C:                   ──read(x)──────|

Linearizable behavior:
  - Client A's write completes at some point (let's say 75ms)
  - Client B's read starts at 50ms, ends at 100ms
  - Since B's read overlaps with A's write, B might read 0 or 1
  - But once B reads 1, Client C (reading after B) MUST also read 1
  - There is a single "point in time" where the write becomes visible

Non-linearizable behavior:
  - Client B reads 1
  - Client C reads 0 (the old value!)
  - This violates linearizability
```

### The Key Rule

**Once any client has seen a new value, all subsequent reads must see that new value or a newer one.**

There is a global "point in time" where each write becomes visible. You cannot go backward in time.

### Why Linearizability Is Hard

Linearizability requires **coordination** between replicas. To guarantee that all clients see the same value:

1. Every write must be replicated to a quorum (majority) of nodes
2. Every read must check the quorum to get the latest value
3. This adds latency (network round-trips)

```
Write with linearizability:
  Client → Node A (primary)
    ↓
  Node A → Node B (replica)
    ↓
  Node A → Node C (replica)
    ↓
  Wait for majority (A + B or A + C) to confirm
    ↓
  Return success to client

This is slow! Every write requires multiple network round-trips.
```

### When to Use

1. **Leader Election:** When a new leader is elected, all nodes must agree on who the leader is.

```
Scenario: Two nodes both think they're the leader!
  - Node A: "I'm the leader" (writes to shared storage)
  - Node B: "I'm the leader" (writes to shared storage)

With linearizability:
  - Only one write succeeds (atomic compare-and-set)
  - All nodes see the same leader

Without linearizability:
  - Both writes might succeed
  - Different nodes see different leaders
  - Disaster! (split-brain)
```

2. **Unique Constraints:** If two users try to register the same username concurrently, exactly one must succeed.

```
Scenario: Alice and Bob both try to register "alice"
  - Alice: "Set username to 'alice' if unset"
  - Bob: "Set username to 'alice' if unset"

With linearizability:
  - Only one succeeds (atomic compare-and-set)
  - The other gets an error

Without linearizability:
  - Both might succeed!
  - Two users with the same username
  - Constraint violated!
```

3. **Cross-Channel Timing Dependencies:** If you write to a database and then send a notification, the consumer must see the write.

```
Scenario:
  1. Alice writes to database: "Transfer $100"
  2. Alice sends message to Bob: "Check your balance"
  3. Bob reads from database

Without linearizability:
  - Bob might read the old balance (before the transfer)
  - Bob doesn't see the $100
  - Confusion!

With linearizability:
  - Bob is guaranteed to see the transfer
```

### The Cost: CAP Theorem

The **CAP Theorem** states: In the presence of a network partition, you must choose between **Consistency** (linearizability) and **Availability**.

```
              ┌─────────────────────┐
              │   CAP Theorem       │
              └──────┬──────────────┘
                     │
          ┌──────────┼──────────────┐
          │          │              │
     Consistency  Availability   Partition
     (Linearizable) (Always respond) Tolerance
                                  (Must handle
                                   netsplits)

You cannot have all three. Since network partitions WILL happen,
you must choose between C and A during a partition.
```

#### CP System (Consistent + Partition-tolerant)

During a network partition, some requests return errors.

```
Network partition:
  Node A ←→ Node B
    ↓
  Node A ←X→ Node B (partition!)

CP system behavior:
  - Requests to the minority side get errors
  - Requests to the majority side succeed
  - Linearizability is maintained

Examples: ZooKeeper, etcd, HBase, Spanner
```

#### AP System (Available + Partition-tolerant)

During a network partition, all requests get a response, but some may be stale.

```
Network partition:
  Node A ←X→ Node B

AP system behavior:
  - Both sides accept writes
  - Writes are replicated when partition heals
  - Linearizability is sacrificed

Examples: Cassandra, DynamoDB, CouchDB
```

### Linearizability and Latency

Even without network partitions, linearizability has a **performance cost**. Every write must wait for a round-trip to a quorum of replicas.

```
Latency comparison:

Eventual consistency:
  Write: Client → Node A → return (1 network hop)
  Latency: ~1ms (local network)

Linearizability:
  Write: Client → Node A → Node B → Node C → wait for majority → return
  Latency: ~10ms (multiple hops, waiting for slowest replica)

10x slower! This is why many systems choose eventual consistency.
```

---

## 5. Comparison Table

| Aspect | Eventual | Causal | Linearizable |
|--------|----------|--------|--------------|
| **Stale reads?** | Yes, unbounded | No (respects causality) | No |
| **Concurrent events** | Any order | Any order | Total order |
| **Latency** | Low | Medium | High |
| **Availability** | High | High | Lower (CAP) |
| **Implementation** | Simple | Vector clocks | Quorum + consensus |
| **Use case** | Caches, feeds | Collaborative apps | Leader election, constraints |
| **Examples** | Cassandra, DynamoDB | Git, Riak | ZooKeeper, etcd, Spanner |

---

## 6. Real-World Examples

### Cassandra (Eventual Consistency)

```python
# Write
cassandra.write(key='user:123', value={'balance': 100})
# Returns immediately, even if replicas haven't received it yet

# Read
balance = cassandra.read(key='user:123')
# Might return old value if replicas haven't synced
```

### Git (Causal Consistency)

```bash
# Commit A
git commit -m "Add feature X"

# Commit B (depends on A)
git commit -m "Fix bug in feature X"

# Git ensures: if you see B, you also see A
# This is causal consistency!
```

### ZooKeeper (Linearizability)

```python
# Leader election using ZooKeeper
zk.create('/leader', 'node-1', ephemeral=True)

# All nodes see the same leader
# If node-1 crashes, the ephemeral node disappears
# A new leader is elected
# All nodes agree on the new leader (linearizable)
```

### Google Spanner (Linearizability + Causal)

```python
# Spanner uses TrueTime (GPS + atomic clocks)
# to guarantee linearizability across datacenters

transaction = spanner.transaction()
transaction.write(key='account:123', value=100)
transaction.commit()

# All subsequent reads see the new value
# Even across datacenters!
```

---

## 7. Interview Questions

### Q1: What is the difference between eventual consistency and linearizability?

**Answer:**
- **Eventual consistency:** After writes stop, replicas eventually converge. No guarantee about when. You might read stale data indefinitely.
- **Linearizability:** Once any client sees a new value, all subsequent reads see that value or a newer one. There's a global "point in time" where each write becomes visible.

### Q2: Why can't you use eventual consistency for leader election?

**Answer:**
If two nodes both think they're the leader (split-brain), the system breaks. You need linearizability to ensure that only one node can acquire the leader lock at a time. This requires atomic compare-and-set operations, which need quorum-based coordination.

### Q3: What is the CAP theorem and what does it mean for a CP system?

**Answer:**
The CAP theorem states that during a network partition, you must choose between Consistency (linearizability) and Availability. A CP system (like ZooKeeper) sacrifices availability — it rejects requests on the minority side of a partition to maintain linearizable consistency.

### Q4: Why is linearizability expensive?

**Answer:**
Linearizability requires coordination between replicas. Every write must be replicated to a quorum (majority) and acknowledged before returning to the client. This adds latency (multiple network round-trips). Many systems choose eventual consistency for performance.

### Q5: How does causal consistency differ from linearizability?

**Answer:**
- **Causal consistency:** Preserves "happened before" relationships. Concurrent events can be in any order.
- **Linearizability:** Provides a total order of all events, consistent with real-time. No concurrency.

Causal consistency is weaker but cheaper to implement (vector clocks). Linearizability is stronger but requires quorum-based coordination.

### Q6: Can you have both causal consistency and linearizability?

**Answer:**
Yes! Linearizability implies causal consistency. If a system is linearizable, it automatically preserves causality. Google Spanner is an example — it provides both.

---

## 8. Common Mistakes

### Mistake 1: Assuming Eventual Consistency Is "Good Enough"

**Wrong:** Using eventual consistency for financial transactions.

```python
# Cassandra (eventual consistency)
cassandra.write(key='account:123', value=100)
balance = cassandra.read(key='account:123')
# Might read 0 (old value) even though we just wrote 100!
```

**Right:** Use linearizability for financial data.

```python
# ZooKeeper (linearizable)
zk.write(key='account:123', value=100)
balance = zk.read(key='account:123')
# Guaranteed to read 100
```

### Mistake 2: Confusing Causal Consistency with Linearizability

**Wrong:** Thinking causal consistency provides a total order.

```python
# Causal consistency allows:
# Node 1 sees: A, B, C
# Node 2 sees: B, A, C (different order for concurrent A and B)
```

**Right:** Understand that causal consistency only orders causally related events.

### Mistake 3: Not Considering the CAP Theorem

**Wrong:** Expecting a system to be both linearizable and available during a partition.

```python
# During a network partition:
# CP system (ZooKeeper): Rejects requests on minority side
# AP system (Cassandra): Accepts requests, but sacrifices consistency
```

**Right:** Choose CP or AP based on your application's needs.

### Mistake 4: Assuming Linearizability Is "Always Better"

**Wrong:** Using linearizability for everything.

```python
# Linearizability adds latency (quorum coordination)
# For a social media feed, this is overkill
# Eventual consistency is better (faster, more available)
```

**Right:** Choose the right consistency model for each use case.

---

## 9. Key Insights from DDIA

### Insight 1: Consistency Models Are About Visibility

> "Consistency is about what values you can read after a write. Different models make different promises about visibility."

### Insight 2: Stronger Consistency = Higher Cost

> "Linearizability is the strongest single-object consistency model, but it comes at a cost: latency and availability. You must choose what you're willing to sacrifice."

### Insight 3: CAP Is About Partitions

> "The CAP theorem is often misunderstood. It's not about choosing between consistency and availability in general. It's specifically about what happens during a network partition."

### Insight 4: Causality Is Cheaper Than Linearizability

> "Causal consistency is a sweet spot: it's stronger than eventual consistency (respects causality) but cheaper than linearizability (no quorum coordination needed)."

---

## 10. Further Reading

- DDIA Chapter 9: "Consistency and Consensus"
- Lamport's "Time, Clocks, and the Ordering of Events in a Distributed System"
- Vector Clocks: "Timestamps in Message-Passing Systems That Preserve the Partial Ordering"
- CAP Theorem: "Brewer's Conjecture and the Feasibility of Consistent, Available, Partition-Tolerant Web Services"
- Linearizability: "Linearizability: A Correctness Condition for Concurrent Objects"

---

## Summary

**Key Takeaways:**

1. 📊 **Eventual Consistency:** Weakest, fastest, most available. Replicas eventually converge.
2. 🔗 **Causal Consistency:** Middle ground. Respects "happened before" relationships.
3. 🔒 **Linearizability:** Strongest, slowest, less available. Behaves like a single copy.
4. ⚖️ **CAP Theorem:** During a partition, choose Consistency or Availability.
5. 💰 **Trade-offs:** Stronger consistency = higher latency, lower availability.
6. 🎯 **Choose wisely:** Different use cases need different consistency models.

**Remember:** There is no "best" consistency model. The right choice depends on your application's requirements and constraints.
