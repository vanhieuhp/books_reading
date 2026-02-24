# Teaching Guide: Linearizability

## Overview

Linearizability is the strongest single-object consistency model. It means: **"The system behaves as if there is only one copy of the data, and every operation takes effect atomically at some point between its start and end."**

This guide walks you through the key concepts and helps you understand when and why linearizability matters.

---

## Core Concept: The Single-Copy Illusion

### What Linearizability Means

Imagine a distributed system with multiple replicas of the same data. Linearizability creates the illusion that there is **only one copy** of the data, and all operations happen in a single, global order.

**Key Rule:** Once ANY client has seen a new value, ALL subsequent reads by ALL clients must also see that new value (or a newer one).

### Visual Example

```
Timeline:
         0ms          50ms         100ms         150ms
Client A: ──write(x=1)────────────────|
Client B:          ──read(x)────|
Client C:                   ──read(x)──────|

Linearizable:
  - Client B reads x=1 (because write started before B's read)
  - Client C reads x=1 (because write completed before C's read)

Non-Linearizable (Eventual Consistency):
  - Client B reads x=0 (stale, write hasn't replicated yet)
  - Client C reads x=1 (write has replicated now)
  - This is allowed in eventual consistency, but violates linearizability
```

---

## Why Linearizability Matters

### 1. Leader Election

When a new leader is elected (e.g., using a lock in ZooKeeper), all nodes must agree on who the leader is.

**Without linearizability:**
- Node A thinks it's the leader
- Node B thinks it's the leader
- **Split-brain**: Two leaders making conflicting decisions

**With linearizability:**
- Only one node can acquire the lock
- All other nodes see it as acquired
- No split-brain

### 2. Unique Constraints

If two users try to register the same username concurrently, exactly one must succeed.

**Without linearizability:**
- Both writes succeed (no check)
- Replicas eventually converge to one value
- But which one? Undefined!

**With linearizability:**
- Use compare-and-set: "Set username to 'alice' only if it's currently empty"
- Exactly one client succeeds
- No race condition

### 3. Cross-Channel Timing Dependencies

If you write data to a database and then send a notification via a message queue, the consumer might read from the database before the write is visible (in non-linearizable systems).

**Example:**
1. Client writes: "User registered: alice"
2. Client sends notification: "alice registered"
3. Consumer reads database: "alice not found" ← **Problem!**

**With linearizability:**
- Once the write completes, the notification is sent
- Consumer is guaranteed to see the write

---

## Linearizability vs Other Consistency Models

### Hierarchy of Consistency

```
Strongest ────────────────────────────────────────────── Weakest
  │                                                        │
  ▼                                                        ▼

Strict             Linearizability     Causal        Eventual
Serializability    (+ Serializable     Consistency   Consistency
                    transactions)

"Everything       "One copy,          "Respect     "Eventually
 is sequential     atomic ops"         cause &      converge,
 and ordered"                          effect"      no ordering"
```

### Key Differences

| Model | Guarantee | Example |
|-------|-----------|---------|
| **Linearizability** | Single-object, real-time ordering | "Once write completes, all reads see new value" |
| **Causal Consistency** | Preserves cause-and-effect | "If A caused B, all nodes see A before B" |
| **Eventual Consistency** | Eventually converge | "Replicas will eventually agree (no timeline)" |

---

## The CAP Theorem: The Cost of Linearizability

### The Trade-off

**CAP Theorem:** In the presence of a network partition, a distributed system must choose between:
- **C**onsistency (linearizability)
- **A**vailability (every request gets a response)
- **P**artition tolerance (must handle network splits)

You cannot have all three. Since network partitions WILL happen, you must choose between C and A.

### CP System (Consistent + Partition-tolerant)

During a network partition, some requests return errors.

**Examples:** ZooKeeper, etcd, HBase, Spanner

```
Network Partition: 3 nodes vs 2 nodes
Quorum size: 3 (need majority of 5)

Partition A (3 nodes): Has quorum → can make decisions
Partition B (2 nodes): No quorum → REJECTS requests

Result: Consistent but unavailable on minority side
```

### AP System (Available + Partition-tolerant)

During a network partition, all requests get a response, but some may be stale.

**Examples:** Cassandra, DynamoDB, CouchDB

```
Network Partition: 3 nodes vs 2 nodes

Partition A (3 nodes): Accepts writes → may be stale
Partition B (2 nodes): Accepts writes → may be stale

Result: Available but not linearizable
```

---

## Performance Cost of Linearizability

### Why Linearizability is Slow

To guarantee linearizability, every write must wait for a round-trip to a quorum of replicas.

```
Linearizable Write:
  1. Client sends write to leader
  2. Leader sends to all replicas
  3. Wait for majority (quorum) to acknowledge
  4. Leader confirms to client
  Latency: ~2 * network_round_trip_time

Non-Linearizable Write (async replication):
  1. Client sends write to primary
  2. Primary acknowledges immediately
  3. Primary sends to replicas asynchronously
  Latency: ~1 * network_round_trip_time
```

### Real-World Example

With 3 replicas across 3 datacenters:
- Network latency between datacenters: 50ms
- Linearizable write: ~100ms (2 round-trips)
- Non-linearizable write: ~50ms (1 round-trip)

**Result:** Linearizability has 2x latency cost!

This is why many systems choose NOT to be linearizable, primarily for **performance**, not just for availability during partitions.

---

## Linearizability and Total Order

### Key Insight

**Linearizability implies a total order of all operations.**

A total order means every pair of operations can be compared: "A happened before B" or "B happened before A." There are no concurrent operations in a total order.

### Example

```
Operations in order:
1. Client A: write(x=1)
2. Client B: write(x=2)
3. Client C: read(x) → 2
4. Client D: write(x=3)
5. Client E: read(x) → 3

All clients see operations in this same order.
No client can see operation 4 before operation 2.
```

### Why This Matters

If you can establish a consistent order of events across nodes, many consistency problems are solved:
- Leader election: "Who was elected first?"
- Unique constraints: "Who registered first?"
- Transaction ordering: "Which transaction committed first?"

---

## How to Achieve Linearizability

### Single-Leader Replication

The simplest way to achieve linearizability:

1. All writes go through a single leader
2. Leader assigns a total order to all writes
3. Followers apply writes in the same order
4. Reads can be served from any replica (if you wait for replication)

**Problem:** If the leader fails, you need to elect a new one (consensus algorithm)

### Consensus Algorithms

To handle leader failures, use a consensus algorithm:

**Raft:**
- Simpler to understand
- Used by: etcd, CockroachDB, TiKV
- Breaks consensus into: Leader Election, Log Replication, Safety

**Paxos:**
- Original consensus algorithm
- Harder to understand
- Used by: Google Chubby

### Total Order Broadcast

**Total Order Broadcast** (also called Atomic Broadcast) guarantees:
1. Reliable delivery: If a message is delivered to one node, it's delivered to ALL
2. Total ordering: All nodes deliver messages in the SAME order

This is exactly what a replication log in a single-leader database provides.

---

## Common Misconceptions

### Misconception 1: "Linearizability = Serializability"

**False.** They're different:
- **Linearizability:** Single-object, real-time ordering guarantee
- **Serializability:** Multi-object, transaction isolation (no real-time guarantee)

**Strict Serializability** = Serializable + Linearizable

### Misconception 2: "Linearizability = No Concurrency"

**False.** Linearizability allows concurrent operations. It just means there's a total order that's consistent with real-time.

### Misconception 3: "CAP Theorem Means You Must Choose"

**Partially true.** CAP only applies during network partitions. In normal operation (no partition), you can have all three. But since partitions WILL happen, you must choose C or A for those periods.

---

## Interview Questions

### Q1: What is linearizability and how does it differ from serializability?

**Answer:**
- **Linearizability:** Single-object consistency. Once a write completes, all subsequent reads see the new value. Real-time ordering guarantee.
- **Serializability:** Multi-object consistency. Transactions appear to execute sequentially, but no real-time guarantee.
- **Strict Serializability** = both

### Q2: Explain the CAP theorem. What does a CP system sacrifice?

**Answer:**
- CAP: During a network partition, choose Consistency or Availability
- CP system (e.g., ZooKeeper): Sacrifices availability. Rejects requests on the minority side of a partition to maintain linearizable consistency.
- AP system (e.g., Cassandra): Sacrifices consistency. Accepts requests on both sides, but data may be stale.

### Q3: Why is linearizability expensive?

**Answer:**
- Every write must wait for a round-trip to a quorum of replicas
- This adds latency proportional to network distance
- Many systems choose NOT to be linearizable primarily for performance

### Q4: How does compare-and-set (CAS) require linearizability?

**Answer:**
- CAS: "Set this value only if it's currently X"
- Used for unique constraints (e.g., username registration)
- Without linearizability: Both writes succeed, replicas converge to undefined value
- With linearizability: Exactly one succeeds

### Q5: What is the relationship between linearizability and total order?

**Answer:**
- Linearizability implies a total order of all operations
- Total order is consistent with real-time
- All clients see operations in the same order
- This is why consensus algorithms (Raft, Paxos) are used to implement linearizability

---

## Hands-On Exercises

### Exercise 1: Understand Quorum Size

For a system with n nodes, what's the quorum size and fault tolerance?

```python
def calculate_quorum(n):
    quorum = (n // 2) + 1
    fault_tolerance = n - quorum
    return quorum, fault_tolerance

# Try different sizes
for n in [3, 5, 7, 9]:
    q, f = calculate_quorum(n)
    print(f"{n} nodes: quorum={q}, can tolerate {f} failures")
```

### Exercise 2: Simulate Network Partition

With 5 nodes, what happens if the network splits 3-2?

```
Quorum size: 3
Partition A (3 nodes): Has quorum → can make decisions
Partition B (2 nodes): No quorum → cannot make decisions

Result: Only partition A can elect a leader
```

### Exercise 3: Compare Latencies

Calculate the latency difference between linearizable and non-linearizable writes:

```
Linearizable: 2 * network_latency
Non-linearizable: 1 * network_latency

If network_latency = 50ms:
  Linearizable: 100ms
  Non-linearizable: 50ms
  Difference: 2x slower
```

### Exercise 4: Design a Leader Election

How would you use linearizability to implement leader election?

```
1. All candidates try to write to a shared register: "I am the leader"
2. Only one write succeeds (linearizable compare-and-set)
3. That candidate becomes the leader
4. All other nodes see the same leader (linearizability)
```

---

## Key Terminology

| Term | Definition |
|------|-----------|
| **Linearizability** | Behaves as if one copy of data; operations are atomic and globally ordered |
| **Total Order** | Every pair of events is ordered (no concurrency) |
| **Partial Order** | Some events are ordered; concurrent events are incomparable |
| **Quorum** | Majority of nodes (more than half) |
| **Split-Brain** | Two nodes both think they're the leader |
| **CAP Theorem** | During a network partition, choose Consistency or Availability |
| **Compare-and-Set (CAS)** | Atomic operation: "Set value only if it's currently X" |
| **Consensus Algorithm** | Algorithm to get all nodes to agree on a value (Raft, Paxos) |
| **Total Order Broadcast** | Protocol ensuring all nodes deliver messages in the same order |

---

## Further Reading

- Chapter 9 of "Designing Data-Intensive Applications" by Martin Kleppmann
- Raft consensus algorithm: https://raft.github.io/
- Google Spanner paper: https://research.google/pubs/spanner-googles-globally-distributed-database/
- Paxos algorithm: Leslie Lamport's papers
- CAP Theorem: Gilbert and Lynch's proof

---

## Next Steps

1. Run `01_linearizability_basics.py` to see demonstrations
2. Modify the code to experiment with different scenarios
3. Answer the interview questions without looking at answers
4. Design your own linearizable system using consensus algorithms
