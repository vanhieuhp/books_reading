# Chapter 9: Consistency and Consensus

This is a comprehensive summary of **Chapter 9: Consistency and Consensus** from *Designing Data-Intensive Applications* by Martin Kleppmann.

---

## Introduction: The Crown Jewel

Chapter 8 showed us everything that can go wrong in a distributed system. Chapter 9 shows us **how to build correct systems despite all those faults.**

The central question: **How do you get multiple nodes to agree on something?** (e.g., "Who is the leader?", "Was this transaction committed?", "Is this value 5 or 6?"). This is the **consensus problem**, and its solution is the foundation of all reliable distributed systems.

---

# 1. Consistency Guarantees

Different systems offer different consistency guarantees. From weakest to strongest:

### Eventual Consistency
* After all writes stop, and you wait long enough, all replicas will eventually converge to the same value.
* **No guarantee about when.** You might read stale data for an unbounded amount of time.
* Very weak, but very available. Most NoSQL databases (Cassandra, DynamoDB) default to this.

### Causal Consistency
* Preserves the cause-and-effect ordering of events.
* If event A causally caused event B (e.g., A is a question and B is the answer), every node must see A before B.
* Events that are not causally related (concurrent) can be seen in any order.
* Stronger than eventual, weaker than linearizability.

### Linearizability (Strongest)
* The system behaves **as if there is only one copy of the data**, and every operation takes effect atomically at some point between its start and end.
* Once a write completes, ALL subsequent reads (from any client, on any node) must see the new value.
* Equivalent to having a single-threaded, single-machine database from the perspective of any observer.

---

# 2. Linearizability

Linearizability is the strongest single-object consistency model. Informally, it means: **"behave as if there is only one copy of the data, and all operations on it are atomic."**

## What Linearizability Looks Like

```
Timeline:
         0ms          50ms         100ms         150ms
Client A: ──write(x=1)────────────────|
Client B:          ──read(x)────|
Client C:                   ──read(x)──────|

Linearizable: Client B must read x=1 (because the write started before B's read).
              Client C must also read x=1.

Non-Linearizable: If Client B reads x=0 (old value), but Client C reads x=1 (new value),
                  that would be okay under eventual consistency.
                  But if Client B reads x=1 and then Client C reads x=0, that violates
                  even basic monotonicity, which linearizability prevents.
```

**The Key Rule:** Once ANY client has seen a new value, ALL subsequent reads by ALL clients must also see that new value (or a newer one). There is a single, global "point in time" where the write becomes visible, and you cannot go back.

## Where Linearizability Is Required

1. **Leader Election:** When a new leader is elected (e.g., using a lock in ZooKeeper), all nodes must agree on who the leader is. Linearizability ensures that once a node acquires the lock, all other nodes see it as acquired.

2. **Unique Constraints:** If two users try to register the same username concurrently, exactly one must succeed. This requires a linearizable compare-and-set operation: "Set this username to 'alice' only if it is currently unset."

3. **Cross-Channel Timing Dependencies:** If you write data to a database and then send a notification via a message queue, the consumer might read from the database before the write is visible (under non-linearizable systems). Linearizability closes this gap.

## The Cost of Linearizability (The CAP Theorem)

The **CAP Theorem** (more precisely, the **CAP conjecture**, proven by Gilbert and Lynch) states:

> In the presence of a **Network Partition**, a distributed system must choose between **Consistency** (linearizability) and **Availability** (every request receives a response).

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

You cannot have all three. Since network partitions WILL happen (they're
unavoidable), you must choose between C and A during a partition:

  CP System (Consistent + Partition-tolerant):
    During a partition, some requests return errors (sacrifices availability).
    Examples: ZooKeeper, etcd, HBase, Spanner.

  AP System (Available + Partition-tolerant):
    During a partition, all requests get a response, but some may be stale 
    (sacrifices linearizability).
    Examples: Cassandra, DynamoDB, CouchDB.
```

**Kleppmann's nuanced take:** CAP is often misapplied. In practice:
* "Consistency" in CAP means specifically linearizability — not the generic word "consistency."
* "Availability" in CAP means *every* request gets a *non-error* response — a very strict definition.
* Many real systems offer points between CP and AP depending on configuration (e.g., Cassandra with `QUORUM` reads approaches CP behavior).

### Linearizability and Network Latency
Even without network partitions, linearizability has a **performance cost**. To guarantee linearizability, every write must wait for a round-trip to a quorum of replicas. This adds latency proportional to the network distance between replicas.

Many systems choose NOT to be linearizable primarily for **performance**, not just for availability during partitions. RAM-based caches, most multi-leader setups, and async replicated databases sacrifice linearizability to achieve lower latency.

---

# 3. Ordering Guarantees

If you can establish a consistent **order** of events across nodes, many consistency problems are solved.

## Causal Order (Partial Order)

Two events are causally related if one "happened before" the other (e.g., a question was posted before the answer). Two events are **concurrent** if neither caused the other.

Causal ordering is a **partial order**: some events are comparable (one happened before the other), and some are not (they happened concurrently).

## Total Order

A **total order** means every pair of events can be compared — you can always say "A happened before B" or "B happened before A." There are no concurrent events in a total order.

* **In a single-leader replication system:** The leader assigns a total order to all writes by putting them in its replication log. Every follower processes writes in the same order.
* **In a multi-leader or leaderless system:** There is no single point that defines the order. Different nodes may process writes in different orders.

**Linearizability implies a total order.** If a system is linearizable, there is a total order of all operations, consistent with real-time.

## Total Order Broadcast

**Total Order Broadcast** (also called **Atomic Broadcast**) is a protocol that guarantees:
1. **Reliable delivery:** If a message is delivered to one node, it is delivered to ALL nodes.
2. **Total ordering:** All nodes deliver messages in the **same order**.

This is exactly what a replication log in a single-leader database provides. It's also equivalent to consensus (we'll see why below).

### Relationship Between Total Order Broadcast and Linearizability
* **Total Order Broadcast → Linearizable storage:** You can build a linearizable key-value store on top of total order broadcast. To do a linearizable write, you broadcast a message "set x = v" and wait for it to come back to you in the delivery order. When it arrives, it has been ordered relative to all other writes.
* **Linearizable storage → Total Order Broadcast:** You can use a linearizable register as a counter to assign sequence numbers. Each message gets the next sequence number atomically, providing a total order.

They are equivalent in power!

---

# 4. Distributed Transactions and Consensus

## The Consensus Problem

**Consensus** means: getting several nodes to agree on something. Once a decision is made, it is final, and all nodes agree on the same decision.

Formally, a consensus algorithm must satisfy:
1. **Uniform Agreement:** No two nodes decide differently.
2. **Integrity:** No node decides twice.
3. **Validity:** If a node decides value `v`, then `v` was proposed by some node.
4. **Termination:** Every non-crashed node eventually decides.

## The FLP Impossibility Result

Fischer, Lynch, and Paterson (1985) proved that **in an asynchronous system** (one where you can't guarantee message delivery times), there is **no algorithm that always reaches consensus** if even one node can crash.

**But wait — we have working consensus algorithms!** The trick: real systems use **timeouts** as a heuristic for failure detection. FLP assumes a purely asynchronous model; practical algorithms (Paxos, Raft) use partial synchrony — they rely on timeouts but ensure safety even if timeouts are wrong (they just lose liveness/progress temporarily).

## Two-Phase Commit (2PC)

2PC is the most common protocol for **distributed transactions** (transactions that span multiple database nodes).

```
Phase 1 — Prepare:
  Coordinator: "Can you commit this transaction?"
  Node A: "Yes, I'm ready." (writes to WAL, but doesn't commit)
  Node B: "Yes, I'm ready." (writes to WAL, but doesn't commit)

Phase 2 — Commit:
  Coordinator: "OK, commit!"
  Node A: Commits.
  Node B: Commits.

  OR, if any node voted "No" in Phase 1:
  Coordinator: "Abort!"
  Node A: Rolls back.
  Node B: Rolls back.
```

### The Fatal Flaw of 2PC: Coordinator Failure
If the coordinator crashes after sending "Prepare" but before sending "Commit" or "Abort":
* The participants have voted "Yes" (promised to commit) but don't know the final decision.
* They **cannot abort** (because the coordinator might come back and say "Commit").
* They **cannot commit** (because the coordinator might come back and say "Abort").
* They are **stuck**, holding locks on the data, blocking all other transactions!

The participants must wait for the coordinator to recover. This is a **blocking** protocol. If the coordinator's disk is destroyed, the participants may be stuck forever with locked data.

**2PC is NOT a consensus algorithm** — it does not satisfy the Termination property (it can get stuck).

## Three-Phase Commit (3PC)
An attempt to fix 2PC's blocking problem by adding an extra round. In theory, 3PC is non-blocking. In practice, it doesn't work well with network partitions and is rarely used.

## Real Consensus Algorithms: Paxos and Raft

### Paxos
* Invented by Leslie Lamport (1989). The foundational consensus algorithm.
* Notoriously difficult to understand and implement.
* Used by Google's Chubby lock service, which underlies many Google systems.

### Raft
* Invented by Diego Ongaro and John Ousterhout (2014) as an "understandable" alternative to Paxos.
* Breaks consensus into three sub-problems: Leader Election, Log Replication, and Safety.
* **Used by:** etcd (Kubernetes' key-value store), CockroachDB, TiKV (TiDB's storage engine), Consul.

### How Raft Works (Simplified)
```
1. Leader Election:
   - Nodes start as followers.
   - If a follower doesn't hear from a leader for a timeout period, 
     it becomes a candidate and requests votes from other nodes.
   - A candidate that receives a majority of votes becomes the leader.
   - The leader sends periodic heartbeats to maintain authority.

2. Log Replication:
   - The leader receives all writes and appends them to its log.
   - The leader sends log entries to followers.
   - Once a majority of followers have confirmed the entry, 
     the leader considers it "committed" and applies it.

3. Safety:
   - A candidate can only be elected leader if its log is at least 
     as up-to-date as a majority of nodes.
   - This ensures that the new leader never loses committed entries.
```

### Epoch Numbers (Terms)
Consensus algorithms don't guarantee a unique leader at all times (there may be brief periods with no leader or two candidates). Instead, they use **epoch numbers** (called **terms** in Raft):
* Each time a new leader is elected, the epoch/term number increments.
* If a node receives a message from a leader with a stale epoch, it ignores it.
* This ensures that even during leader transition, old leaders can't override new ones.

## Consensus in Practice

Consensus algorithms are used by **coordination services**, not directly by application developers:

| Service | Algorithm | Used For |
|---------|-----------|----------|
| ZooKeeper | ZAB (Zookeeper Atomic Broadcast) | Leader election, config management, distributed locks |
| etcd | Raft | Kubernetes state storage, service discovery |
| Consul | Raft | Service mesh, service discovery, KV store |
| Google Chubby | Paxos | Internal: Bigtable, MapReduce coordinator |

These services provide:
* **Linearizable key-value storage**
* **Total order broadcast** (for event ordering)
* **Leader election** (who is the current leader?)
* **Distributed locks and leases** (with fencing tokens)
* **Membership and failure detection** (which nodes are alive?)

---

# 5. Membership and Coordination Services

## ZooKeeper: The Practical Example

ZooKeeper is not a general-purpose database. It's a **coordination service** — a small, highly reliable key-value store optimized for configuration data, leader election, and distributed locks.

Key features:
* **Linearizable writes:** All writes go through the leader (via ZAB consensus). Every write is totally ordered.
* **Serializable (!!!) reads:** By default, reads can be served by any replica and might be stale. To get linearizable reads, you must use the `sync` operation before reading.
* **Ephemeral nodes:** A ZooKeeper node (a key) can be marked "ephemeral." If the client that created it disconnects (crash, network failure), ZooKeeper automatically deletes it. This is perfect for leader election: a leader creates an ephemeral node, and if it dies, the node disappears, triggering a new election.
* **Watches:** A client can subscribe to changes on a ZNode. When the ZNode changes, ZooKeeper pushes a notification to the client. This avoids polling.

### Service Discovery
Databases like HBase, Kafka, and Solr use ZooKeeper to track:
* Which nodes are alive (via ephemeral nodes and heartbeats)
* Which node is the leader for each partition
* Where partitions are located (for request routing — Chapter 6)

When a node crashes, its ephemeral node disappears. ZooKeeper notifies all watchers. The remaining nodes can immediately elect a new leader and update routing tables.

---

# Summary: The Hierarchy of Consistency Models

```
Strongest ────────────────────────────────────────────── Weakest
  │                                                        │
  ▼                                                        ▼

Strict             Linearizability     Causal        Eventual
Serializability    (+ Serializable     Consistency   Consistency
(strongest ever)    transactions)

  "Everything       "One copy,          "Respect     "Eventually
   is sequential     atomic ops"         cause &      converge,
   and ordered"                          effect"      no ordering"

  Requires           Requires            Requires     Just wait
  consensus          consensus           vector       long enough
  (Raft/Paxos)       or single-leader    clocks

  Examples:          Examples:           Examples:    Examples:
  Spanner,           ZooKeeper,          Git (DAG),   Cassandra,
  CockroachDB        etcd                Riak         DynamoDB
```

---

# Key Terminology

* **Linearizability:** Behaves as if one copy of data; operations are atomic and globally ordered.
* **Causal Consistency:** Preserves happen-before ordering; concurrent events can be in any order.
* **Total Order:** Every pair of events is ordered (no concurrency).
* **Partial Order:** Some events are ordered; concurrent events are incomparable.
* **Total Order Broadcast:** Protocol ensuring all nodes deliver messages in the same order.
* **Consensus:** Getting all non-faulty nodes to agree on a single value.
* **2PC (Two-Phase Commit):** Blocking distributed transaction protocol. Not true consensus.
* **Raft:** Understandable consensus algorithm. Leader-based. Used by etcd, CockroachDB.
* **Paxos:** Original consensus algorithm. Harder to understand. Used by Google Chubby.
* **Epoch/Term:** A monotonically increasing number identifying a leadership period.
* **CAP Theorem:** During a network partition, choose Consistency or Availability.
* **FLP Impossibility:** No deterministic consensus in a purely asynchronous system.
* **ZooKeeper:** A coordination service providing consensus, leader election, and distributed locks.
* **Ephemeral Node:** A ZooKeeper node that is auto-deleted when its creator disconnects.

---

# Interview-Level Questions

1. **What is linearizability and how does it differ from serializability?**
   → Linearizability: single-object, real-time ordering guarantee. Serializability: multi-object, transaction isolation (no real-time guarantee). Strict Serializability = Serializable + Linearizable.

2. **Explain the CAP theorem. What does a CP system sacrifice?**
   → During a network partition, you choose Consistency or Availability. A CP system (e.g., ZooKeeper) rejects requests on the minority side of a partition — it sacrifices availability to maintain linearizable consistency.

3. **What is the fundamental flaw of Two-Phase Commit?**
   → If the coordinator crashes after Phase 1 but before Phase 2, participants are stuck. They cannot commit or abort. Data is locked, and they must wait for the coordinator to recover. This is a blocking protocol.

4. **How does Raft elect a leader?**
   → If a follower times out waiting for heartbeats, it increments the term number, votes for itself, and requests votes from peers. If it gets a majority, it becomes leader. It sends heartbeats to maintain authority.

5. **Why are ephemeral nodes in ZooKeeper useful for leader election?**
   → The leader creates an ephemeral node. If the leader crashes, ZooKeeper automatically deletes the node. Other nodes watch the node and immediately trigger a new election when it disappears.

6. **What is Total Order Broadcast and why is it equivalent to consensus?**
   → Total Order Broadcast guarantees all nodes deliver messages in the same order. It's equivalent to consensus because you can use it to implement a linearizable register (and vice versa). It's essentially what a single-leader replication log provides.
