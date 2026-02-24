# Chapter 9, Section 5: Key Terminology and Interview-Level Questions — Teaching Guide

## Overview

Chapter 9 is about **Consistency and Consensus** — the crown jewel of distributed systems. While Chapter 8 showed us everything that can go wrong, Chapter 9 shows us how to build correct systems despite those faults.

The central question: **How do you get multiple nodes to agree on something?**

This teaching guide breaks down the key terminology and prepares you for interview questions about consistency models, consensus algorithms, and distributed transactions.

---

## Key Terminology Explained

### 1. Consistency Models (Weakest to Strongest)

#### Eventual Consistency
**Definition:** After all writes stop and you wait long enough, all replicas will eventually converge to the same value.

**Key characteristics:**
- No guarantee about *when* convergence happens
- You might read stale data for an unbounded amount of time
- Very weak, but very available
- Used by: Cassandra, DynamoDB, most NoSQL databases

**Example:**
```
Write "x = 5" to Node A
Node A replicates to Node B (eventually)
Node B replicates to Node C (eventually)

If you read from Node C immediately: might get old value
If you wait long enough: will get "x = 5"
```

**Interview insight:** "Eventual consistency is the weakest guarantee. It's available but offers no ordering guarantees."

---

#### Causal Consistency
**Definition:** Preserves the cause-and-effect ordering of events. If event A causally caused event B, every node must see A before B.

**Key characteristics:**
- Stronger than eventual consistency
- Weaker than linearizability
- Respects "happens-before" relationships
- Concurrent events can be in any order

**Example:**
```
Event A: Alice posts a question
Event B: Bob answers the question

Causal relationship: A → B (A caused B)

With causal consistency:
- Every node must see A before B
- If you read B, you must also see A

But if Event C (unrelated) happens concurrently:
- C can be seen before or after A and B
```

**Interview insight:** "Causal consistency is a middle ground. It respects cause-and-effect but allows concurrent events to be reordered."

---

#### Linearizability (Strict Consistency)
**Definition:** The system behaves as if there is only one copy of the data, and every operation takes effect atomically at some point between its start and end.

**Key characteristics:**
- Strongest single-object consistency model
- Once a write completes, ALL subsequent reads must see the new value
- Real-time ordering: if operation A finishes before B starts, A's effects are visible to B
- Equivalent to a single-threaded, single-machine database

**Example:**
```
Timeline:
         0ms          50ms         100ms         150ms
Client A: ──write(x=1)────────────────|
Client B:          ──read(x)────|
Client C:                   ──read(x)──────|

Linearizable:
- Client B reads x=1 (write started before B's read)
- Client C reads x=1 (write started before C's read)

Non-linearizable:
- If Client B reads x=0 but Client C reads x=1, that violates linearizability
```

**Interview insight:** "Linearizability is the strongest guarantee. It's what most people intuitively expect from a database."

---

### 2. Ordering Concepts

#### Partial Order
**Definition:** Some events are ordered (comparable), and some are not (concurrent).

**Example:**
```
Event A: Question posted
Event B: Answer posted
Event C: Another answer posted (concurrent with B)

Partial order:
- A < B (A happened before B)
- A < C (A happened before C)
- B and C are incomparable (concurrent)
```

**Interview insight:** "Partial orders capture causality. They're used in vector clocks and DAGs."

---

#### Total Order
**Definition:** Every pair of events can be compared. There are no concurrent events.

**Example:**
```
Total order: A < B < C < D < E

Every pair is comparable:
- A < B ✓
- A < C ✓
- B < D ✓
- etc.
```

**Interview insight:** "Total orders are what single-leader replication provides. The leader assigns a total order to all writes."

---

#### Total Order Broadcast (Atomic Broadcast)
**Definition:** A protocol that guarantees:
1. **Reliable delivery:** If a message is delivered to one node, it's delivered to ALL nodes
2. **Total ordering:** All nodes deliver messages in the SAME order

**Example:**
```
Replication log in a single-leader database:

Leader's log:
  [write(x=1), write(y=2), write(z=3)]

Follower 1 receives:
  [write(x=1), write(y=2), write(z=3)]

Follower 2 receives:
  [write(x=1), write(y=2), write(z=3)]

All nodes process in the same order!
```

**Interview insight:** "Total order broadcast is equivalent to consensus. You can build linearizable storage on top of it."

---

### 3. Consensus and Algorithms

#### Consensus Problem
**Definition:** Getting several nodes to agree on something. Once a decision is made, it is final, and all nodes agree.

**Formal requirements:**
1. **Uniform Agreement:** No two nodes decide differently
2. **Integrity:** No node decides twice
3. **Validity:** If a node decides value `v`, then `v` was proposed by some node
4. **Termination:** Every non-crashed node eventually decides

**Interview insight:** "Consensus is the foundation of all reliable distributed systems. It's hard because of partial failures."

---

#### FLP Impossibility Result
**Definition:** Fischer, Lynch, and Paterson (1985) proved that in an asynchronous system, there is NO algorithm that always reaches consensus if even one node can crash.

**Key insight:**
- In a purely asynchronous system (no timing guarantees), consensus is impossible
- Real systems use **partial synchrony** — they rely on timeouts but ensure safety even if timeouts are wrong
- Practical algorithms (Paxos, Raft) sacrifice liveness (progress) to maintain safety

**Interview insight:** "FLP proves consensus is impossible in theory, but practical systems work around it using timeouts."

---

#### Two-Phase Commit (2PC)
**Definition:** A protocol for distributed transactions that span multiple database nodes.

**How it works:**
```
Phase 1 — Prepare:
  Coordinator: "Can you commit this transaction?"
  Node A: "Yes, I'm ready." (writes to WAL, doesn't commit)
  Node B: "Yes, I'm ready." (writes to WAL, doesn't commit)

Phase 2 — Commit:
  Coordinator: "OK, commit!"
  Node A: Commits
  Node B: Commits
```

**The fatal flaw:**
If the coordinator crashes after Phase 1 but before Phase 2:
- Participants have voted "Yes" but don't know the final decision
- They cannot abort (coordinator might say "Commit")
- They cannot commit (coordinator might say "Abort")
- They are **stuck**, holding locks, blocking all other transactions

**Interview insight:** "2PC is NOT a consensus algorithm. It can get stuck if the coordinator crashes. This is why it's rarely used."

---

#### Raft Consensus Algorithm
**Definition:** An understandable alternative to Paxos that breaks consensus into three sub-problems.

**Three sub-problems:**
1. **Leader Election:** Nodes elect a leader using majority votes
2. **Log Replication:** Leader replicates log entries to followers
3. **Safety:** Ensures committed entries are never lost

**How leader election works:**
```
1. Nodes start as followers
2. If a follower doesn't hear from leader for timeout period:
   - Becomes a candidate
   - Increments term number
   - Votes for itself
   - Requests votes from other nodes
3. If candidate gets majority votes: becomes leader
4. Leader sends periodic heartbeats to maintain authority
```

**Key concept: Terms (Epoch Numbers)**
- Each leadership period has a unique term number
- Term numbers are monotonically increasing
- If a node receives a message from a stale term, it ignores it
- This prevents old leaders from overriding new ones

**Interview insight:** "Raft is designed to be understandable. It's used by etcd, CockroachDB, and many other systems."

---

#### Paxos Consensus Algorithm
**Definition:** The original consensus algorithm, invented by Leslie Lamport (1989).

**Key characteristics:**
- Foundational and theoretically sound
- Notoriously difficult to understand and implement
- Used by Google's Chubby lock service
- Underlies many Google systems

**Interview insight:** "Paxos is the gold standard for consensus, but Raft is more practical for most systems."

---

### 4. Distributed Transactions and Coordination

#### CAP Theorem
**Definition:** In the presence of a network partition, a distributed system must choose between **Consistency** (linearizability) and **Availability** (every request gets a response).

**The three properties:**
- **Consistency:** Linearizable consistency
- **Availability:** Every request gets a non-error response
- **Partition Tolerance:** System works despite network partitions

**Key insight:** You cannot have all three. Since network partitions WILL happen, you must choose between C and A.

**Trade-offs:**
```
CP System (Consistent + Partition-tolerant):
- During partition: some requests return errors
- Examples: ZooKeeper, etcd, HBase, Spanner
- Sacrifices availability

AP System (Available + Partition-tolerant):
- During partition: all requests get responses (might be stale)
- Examples: Cassandra, DynamoDB, CouchDB
- Sacrifices linearizability
```

**Interview insight:** "CAP is often misunderstood. It specifically refers to linearizability, not generic 'consistency'."

---

#### Coordination Services
**Definition:** Small, highly reliable key-value stores optimized for configuration data, leader election, and distributed locks.

**Examples:**
- **ZooKeeper:** Uses ZAB (Zookeeper Atomic Broadcast)
- **etcd:** Uses Raft
- **Consul:** Uses Raft
- **Google Chubby:** Uses Paxos

**Key features:**
- Linearizable writes (all writes go through leader)
- Serializable reads (can be stale by default)
- Ephemeral nodes (auto-deleted when creator disconnects)
- Watches (push notifications on changes)

**Interview insight:** "Coordination services are not general-purpose databases. They're specialized for distributed coordination."

---

#### Ephemeral Nodes
**Definition:** A ZooKeeper node that is automatically deleted when its creator disconnects.

**Use case: Leader Election**
```
1. Leader creates ephemeral node /leader
2. If leader crashes: node is auto-deleted
3. Other nodes watch /leader
4. When node disappears: new election triggered
5. New leader creates /leader
```

**Interview insight:** "Ephemeral nodes are elegant. They solve the zombie leader problem automatically."

---

### 5. Consistency vs Performance Trade-offs

#### Linearizability Cost
**Definition:** Linearizability has a performance cost because every write must wait for a round-trip to a quorum of replicas.

**Example:**
```
Write latency with linearizability:
- Write to local node: 1ms
- Wait for quorum confirmation: 10ms (network round-trip)
- Total: 11ms

Write latency without linearizability:
- Write to local node: 1ms
- Return immediately: 1ms
```

**Interview insight:** "Many systems sacrifice linearizability for performance, not just for availability during partitions."

---

## Learning Progression

### Level 1: Understanding Consistency Models
**Goal:** Understand the spectrum from eventual to linearizable consistency

**Key questions:**
1. What is eventual consistency? When is it acceptable?
2. What is linearizability? Why is it hard to achieve?
3. What is causal consistency? How is it different from linearizability?

**Exercises:**
- Draw a timeline showing linearizable vs non-linearizable reads
- Explain why eventual consistency is available but weak
- Compare consistency models in real databases

---

### Level 2: Understanding Ordering and Consensus
**Goal:** Understand how ordering relates to consistency and consensus

**Key questions:**
1. What is a total order? Why is it important?
2. What is total order broadcast? How does it relate to consensus?
3. Why is consensus hard? (FLP impossibility)

**Exercises:**
- Implement a simple total order broadcast
- Explain why 2PC is not a consensus algorithm
- Compare Raft and Paxos

---

### Level 3: Understanding Algorithms and Trade-offs
**Goal:** Understand practical consensus algorithms and their trade-offs

**Key questions:**
1. How does Raft work? What are its three sub-problems?
2. What is the CAP theorem? What does it really mean?
3. When should you use CP vs AP systems?

**Exercises:**
- Simulate Raft leader election
- Explain CAP theorem to a non-technical person
- Design a system that handles network partitions

---

### Level 4: Interview Preparation
**Goal:** Be able to answer complex questions about consistency and consensus

**Key questions:**
1. Explain the difference between linearizability and serializability
2. Why is 2PC problematic? What are the alternatives?
3. How would you design a distributed lock service?
4. What is the relationship between total order broadcast and consensus?

**Exercises:**
- Answer all interview questions without looking at answers
- Explain concepts to someone else
- Design systems that use consensus

---

## Common Misconceptions

### Misconception 1: "Linearizability and Serializability are the same"
**Reality:** They're different!

- **Linearizability:** Single-object, real-time ordering guarantee
- **Serializability:** Multi-object, transaction isolation (no real-time guarantee)
- **Strict Serializability:** Both (linearizable + serializable)

**Example:**
```
Linearizable but not serializable:
- Transaction A: read(x), write(y)
- Transaction B: read(y), write(x)
- These can interleave in a way that's linearizable but not serializable

Serializable but not linearizable:
- Transaction A: write(x=1)
- Transaction B: read(x)
- If B reads x=0 (old value), it's serializable but not linearizable
```

---

### Misconception 2: "CAP means you must choose one"
**Reality:** CAP is more nuanced.

- You must choose between C and A *during a partition*
- Most systems are CP or AP, not both
- But you can be CA when there's no partition (which is most of the time)

**Example:**
```
Normal operation (no partition): CA
- System is consistent and available

During partition: Choose C or A
- CP: Consistent but unavailable (reject requests)
- AP: Available but inconsistent (stale reads)
```

---

### Misconception 3: "Consensus is always needed"
**Reality:** Consensus is expensive. Use it only when necessary.

**When you need consensus:**
- Leader election
- Distributed locks
- Atomic transactions across multiple nodes

**When you don't need consensus:**
- Read-heavy workloads (eventual consistency is fine)
- Single-leader replication (leader provides ordering)
- Leaderless systems with quorum reads/writes

---

### Misconception 4: "2PC is a consensus algorithm"
**Reality:** 2PC is NOT a consensus algorithm.

**Why:**
- 2PC can get stuck if coordinator crashes
- Consensus requires termination (every node eventually decides)
- 2PC violates termination property

**Better alternatives:**
- Raft or Paxos for consensus
- Sagas for distributed transactions
- Event sourcing for eventual consistency

---

## Discussion Questions

### For Understanding Consistency Models
1. **Why is eventual consistency acceptable for social media but not for banking?**
   - Answer: Social media can tolerate stale data. Banking cannot tolerate inconsistency.

2. **Can you have linearizability without consensus?**
   - Answer: No. Linearizability requires a total order, which requires consensus.

3. **Why do most NoSQL databases default to eventual consistency?**
   - Answer: Eventual consistency is available and performant. Linearizability is expensive.

---

### For Understanding Consensus
1. **Why does Raft use term numbers?**
   - Answer: To prevent stale leaders from overriding new leaders.

2. **What happens if the Raft leader crashes?**
   - Answer: Followers timeout, elect a new leader. System continues.

3. **Why is 2PC problematic?**
   - Answer: Coordinator failure causes participants to get stuck.

---

### For Understanding Trade-offs
1. **When would you choose an AP system over a CP system?**
   - Answer: When availability is more important than consistency (e.g., social media).

2. **Why is consensus expensive?**
   - Answer: Every write must wait for quorum confirmation, adding latency.

3. **How would you design a system that's both consistent and available?**
   - Answer: Use single-leader replication (consistent) with read replicas (available).

---

## Real-World Examples

### Consistency Models in Practice
- **Cassandra:** Eventual consistency (configurable with quorum reads/writes)
- **DynamoDB:** Eventual consistency (with strong consistency option)
- **PostgreSQL:** Linearizable (single-leader replication)
- **Google Spanner:** Linearizable (with TrueTime)

### Consensus Algorithms in Practice
- **Raft:** etcd, CockroachDB, TiKV, Consul
- **Paxos:** Google Chubby, Apache ZooKeeper (uses ZAB, similar to Paxos)
- **PBFT:** Blockchains, Hyperledger Fabric

### Coordination Services in Practice
- **ZooKeeper:** Kafka, HBase, Solr, Hadoop
- **etcd:** Kubernetes, CoreOS, Docker Swarm
- **Consul:** HashiCorp ecosystem, service mesh

---

## Key Takeaways

1. **Consistency models form a spectrum** — from eventual to linearizable
2. **Ordering is fundamental** — total order broadcast is equivalent to consensus
3. **Consensus is hard** — FLP impossibility, but practical algorithms work around it
4. **Trade-offs are everywhere** — consistency vs availability, latency vs safety
5. **Choose the right tool** — don't use consensus when eventual consistency suffices

---

## Further Reading

From DDIA:
- Chapter 9: "Consistency and Consensus"
- Chapter 8: "The Trouble with Distributed Systems" (for context)

Related topics:
- Raft consensus algorithm (https://raft.github.io/)
- Paxos algorithm (Leslie Lamport's papers)
- Google Spanner paper (TrueTime)
- CAP theorem (Eric Brewer's papers)
