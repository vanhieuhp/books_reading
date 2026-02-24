# Teaching Guide: Chapter 9, Section 4 — Distributed Transactions and Consensus

## Overview

This teaching guide provides deep explanations for Chapter 9, Section 4 of *Designing Data-Intensive Applications*. The section covers how to get multiple nodes to agree on something — the consensus problem — and the algorithms that solve it.

---

## 1. The Consensus Problem

### What is Consensus?

Consensus means: **getting several nodes to agree on something, and once a decision is made, it is final.**

**Real-world examples:**
- **Leader election:** "Who is the current leader?"
- **Atomic transactions:** "Was this transaction committed or aborted?"
- **Unique constraints:** "Is this username already taken?"
- **Configuration changes:** "What is the current cluster membership?"

### The Four Properties of Consensus

A consensus algorithm must satisfy four properties:

#### 1. Uniform Agreement
**No two nodes decide differently.**

If Node A decides value `v`, then Node B cannot decide value `w` (where `w ≠ v`).

```
Node A: Decides "Leader is Node 1"
Node B: Decides "Leader is Node 1"  ✅ (same decision)

Node A: Decides "Leader is Node 1"
Node B: Decides "Leader is Node 2"  ❌ (violates uniform agreement)
```

#### 2. Integrity
**No node decides twice.**

Once a node has decided on a value, it cannot change its mind.

```
Node A: Decides "Leader is Node 1"
Node A: Later decides "Leader is Node 2"  ❌ (violates integrity)
```

#### 3. Validity
**If a node decides value v, then v was proposed by some node.**

A node cannot decide on a value that was never proposed. (Prevents the algorithm from deciding on arbitrary values.)

```
Proposed values: {1, 2, 3}
Node A: Decides 2  ✅ (2 was proposed)
Node A: Decides 5  ❌ (5 was never proposed)
```

#### 4. Termination
**Every non-crashed node eventually decides.**

The algorithm must make progress. A non-crashed node cannot wait forever.

```
Node A: Crashes (doesn't need to decide)
Node B: Eventually decides  ✅ (non-crashed node decides)
```

### Why Consensus is Hard

Consensus is hard because of **network partitions** and **node crashes**.

```
Scenario: 5 nodes, network partition splits them 3-2

Partition A (3 nodes):
  Can reach consensus (majority)
  Decides: "Leader is Node 1"

Partition B (2 nodes):
  Cannot reach consensus (minority)
  Waits for partition to heal

Problem: What if Partition B thinks it's the majority?
  Both partitions might decide differently!
```

---

## 2. The FLP Impossibility Result

### What is FLP?

**FLP** stands for **Fischer, Lynch, and Paterson** — three computer scientists who proved a fundamental impossibility result in 1985.

### The Theorem

> In an **asynchronous system** (one where you cannot guarantee message delivery times), there is **no algorithm that always reaches consensus** if even one node can crash.

### What This Means

**Asynchronous system:** You don't know how long a message will take to arrive. It could be 1ms or 1 hour.

**The problem:**
- You send a message to Node B
- You don't know if Node B crashed or if the message is just delayed
- You cannot distinguish between the two cases

**The consequence:**
- You cannot safely decide (because you don't know if Node B is dead or just slow)
- But you also cannot wait forever (because then you never make progress)

### Why This Matters

FLP proves that **no deterministic algorithm can guarantee consensus in a purely asynchronous system.**

But wait — **we have working consensus algorithms!** How?

### The Trick: Partial Synchrony

Real systems use **timeouts** as a heuristic for failure detection.

```
Timeout-based failure detection:
  1. Send message to Node B
  2. Wait for response (with timeout)
  3. If no response within timeout, assume Node B crashed
  4. Proceed without Node B

Problem: What if Node B is just slow?
  You might decide Node B is dead, but it's actually alive!
  This can cause split-brain (two leaders).

Solution: Use quorums and fencing tokens to prevent split-brain.
```

### Key Insight from DDIA

> "FLP proves that consensus is impossible in a purely asynchronous system. But practical algorithms (Paxos, Raft) use timeouts and assume partial synchrony. They ensure safety (no split-brain) even if timeouts are wrong. They just lose liveness (progress) temporarily."

---

## 3. Two-Phase Commit (2PC)

### What is 2PC?

**Two-Phase Commit** is the most common protocol for **distributed transactions** — transactions that span multiple database nodes.

### How 2PC Works

```
Scenario: Transaction T1 writes to Node A and Node B

Phase 1 — Prepare:
  Coordinator: "Can you commit transaction T1?"
  Node A: "Yes, I'm ready." (writes to WAL, but doesn't commit)
  Node B: "Yes, I'm ready." (writes to WAL, but doesn't commit)

Phase 2 — Commit:
  Coordinator: "OK, commit!"
  Node A: Commits (writes are now permanent)
  Node B: Commits (writes are now permanent)

  OR, if any node voted "No" in Phase 1:
  Coordinator: "Abort!"
  Node A: Rolls back (undoes the write)
  Node B: Rolls back (undoes the write)
```

### The Fatal Flaw: Coordinator Failure

**Scenario:** Coordinator crashes after Phase 1 but before Phase 2.

```
Phase 1:
  Coordinator: "Can you commit T1?"
  Node A: "Yes, I'm ready." (writes to WAL)
  Node B: "Yes, I'm ready." (writes to WAL)

Phase 2:
  Coordinator: --- CRASHES ---

Result:
  Node A: Waiting for decision (cannot commit or abort)
  Node B: Waiting for decision (cannot commit or abort)
  Data is LOCKED. Other transactions cannot proceed.

  If coordinator's disk is destroyed:
    Participants may be stuck FOREVER with locked data.
```

### Why This is Dangerous

1. **Blocking protocol:** Participants hold locks while waiting for coordinator
2. **Coordinator failure:** If coordinator crashes, participants are stuck
3. **Data locked:** Other transactions cannot access the locked data
4. **Indefinite wait:** If coordinator's disk is destroyed, participants may wait forever

### Why 2PC is NOT True Consensus

2PC does **not** satisfy the **Termination** property of consensus.

- **Termination:** Every non-crashed node eventually decides
- **2PC:** Participants can wait indefinitely for coordinator

Therefore, 2PC is **not a consensus algorithm**.

### Key Insight from DDIA

> "2PC is a blocking protocol. If the coordinator crashes, participants are stuck. This is why 2PC is rarely used in practice for critical systems. Real consensus algorithms (Paxos, Raft) are non-blocking."

---

## 4. Three-Phase Commit (3PC)

### What is 3PC?

**Three-Phase Commit** is an attempt to fix 2PC's blocking problem by adding an extra round.

### How 3PC Works

```
Phase 1 — Prepare:
  Coordinator: "Can you commit?"
  Participants: "Yes, I'm ready."

Phase 2 — Pre-Commit:
  Coordinator: "I'm about to commit."
  Participants: "OK, I'm ready to commit."

Phase 3 — Commit:
  Coordinator: "Commit!"
  Participants: "Committed."
```

### Why 3PC Doesn't Work Well

In theory, 3PC is non-blocking. In practice:
- **Network partitions:** 3PC doesn't handle partitions well
- **Complexity:** Much harder to implement correctly
- **Rarely used:** Most systems use Paxos or Raft instead

---

## 5. Real Consensus Algorithms: Paxos and Raft

### Paxos

**Invented by Leslie Lamport (1989).**

**Characteristics:**
- The foundational consensus algorithm
- Notoriously difficult to understand and implement
- Used by Google's Chubby lock service
- Guarantees safety and liveness (with partial synchrony)

**Key insight:** Paxos uses quorums to ensure that any two quorums overlap. This prevents split-brain.

### Raft

**Invented by Diego Ongaro and John Ousterhout (2014).**

**Characteristics:**
- Designed to be more understandable than Paxos
- Breaks consensus into three sub-problems: Leader Election, Log Replication, Safety
- Used by etcd (Kubernetes), CockroachDB, TiKV, Consul
- Easier to implement and reason about

---

## 6. How Raft Works

### Overview

Raft breaks consensus into three sub-problems:

1. **Leader Election:** Elect a leader
2. **Log Replication:** Replicate log entries to followers
3. **Safety:** Ensure the new leader has all committed entries

### State Machine

Each node has three possible states:

```
Follower:
  - Receives messages from leader
  - Votes in elections
  - Default state

Candidate:
  - Becomes candidate if election timeout expires
  - Requests votes from other nodes
  - Becomes leader if gets majority of votes

Leader:
  - Sends heartbeats to followers
  - Receives writes from clients
  - Replicates log entries to followers
```

### Leader Election

```
Initial state:
  All nodes are followers

Election timeout expires on Node 1:
  Node 1: Becomes candidate (increments term)
  Node 1: Requests votes from peers

Voting:
  Node 0: Votes for Node 1 (if Node 1's log is up-to-date)
  Node 2: Votes for Node 1 (if Node 1's log is up-to-date)

Result:
  Node 1: Becomes leader (got majority of votes)
  Node 0: Remains follower
  Node 2: Remains follower

Leader sends heartbeats:
  Node 1: Sends heartbeats to Node 0 and Node 2
  Node 0: Resets election timeout
  Node 2: Resets election timeout
```

### Log Replication

```
Client writes "set x = 5" to leader:
  Leader: Appends entry to log: [entry(term=1, value="set x = 5")]
  Leader: Sends entry to followers

Followers receive entry:
  Follower 0: Appends entry to log
  Follower 2: Appends entry to log
  Followers: Send acknowledgment to leader

Leader receives acknowledgments:
  Leader: Entry is now replicated on majority (leader + 2 followers)
  Leader: Commits entry (applies to state machine)
  Leader: Sends commit notification to followers

Followers receive commit notification:
  Follower 0: Commits entry (applies to state machine)
  Follower 2: Commits entry (applies to state machine)

Result: ALL NODES HAVE SAME STATE ✅
```

### Safety: Ensuring No Data Loss

**Problem:** What if the leader crashes and a new leader is elected?

**Solution:** The new leader must have all committed entries.

**How Raft ensures this:**

1. **Candidate restriction:** A candidate can only be elected leader if its log is at least as up-to-date as a majority of nodes.
2. **Up-to-date check:** A log is more up-to-date if:
   - It has a higher term number, OR
   - It has the same term but is longer

```
Example:
  Node A: log = [entry(term=1), entry(term=2)]
  Node B: log = [entry(term=1)]

  Node A's log is more up-to-date (higher term)
  Node A can be elected leader
  Node B cannot be elected leader (would lose entry(term=2))
```

### Terms (Epoch Numbers)

**Terms** are monotonically increasing numbers that identify leadership periods.

```
Term 0: No leader elected yet
Term 1: Node 1 is leader
Term 2: Node 2 is leader (after Node 1 crashes)
Term 3: Node 0 is leader (after Node 2 crashes)
```

**Why terms matter:**

1. **Prevent old leaders:** If a node receives a message from a leader with a stale term, it ignores it
2. **Detect new leaders:** If a node receives a message with a higher term, it updates its term
3. **Ensure safety:** Even during leader transitions, old leaders can't override new ones

---

## 7. How Paxos Works (Simplified)

### Roles

**Proposers:** Propose values

**Acceptors:** Accept proposals and remember them

**Learners:** Learn the final decision

### Two Phases

#### Phase 1: Prepare

```
Proposer: "I'm proposing value v with proposal number n"
Acceptors: "OK, I promise not to accept any proposal with number < n"
```

#### Phase 2: Accept

```
Proposer: "Please accept value v with proposal number n"
Acceptors: "OK, I accept value v with proposal number n"
```

### Quorum

**Quorum:** A majority of acceptors.

**Why quorums matter:**

Any two quorums overlap. This prevents split-brain.

```
Example: 5 acceptors

Quorum 1: {A, B, C}
Quorum 2: {C, D, E}

Overlap: {C}

If Quorum 1 accepts value v, then Quorum 2 must know about it
(because C is in both quorums).
```

### Key Insight from DDIA

> "Paxos is correct but hard to understand. Raft is easier to understand and equally correct. Both use quorums to prevent split-brain."

---

## 8. Consensus in Practice

### Coordination Services

Consensus algorithms are used by **coordination services**, not directly by application developers.

| Service | Algorithm | Used For |
|---------|-----------|----------|
| ZooKeeper | ZAB (Zookeeper Atomic Broadcast) | Leader election, config management, distributed locks |
| etcd | Raft | Kubernetes state storage, service discovery |
| Consul | Raft | Service mesh, service discovery, KV store |
| Google Chubby | Paxos | Internal: Bigtable, MapReduce coordinator |

### What These Services Provide

1. **Linearizable key-value storage:** All writes go through the leader
2. **Total order broadcast:** All nodes deliver messages in the same order
3. **Leader election:** Who is the current leader?
4. **Distributed locks and leases:** With fencing tokens
5. **Membership and failure detection:** Which nodes are alive?

---

## 9. Combining Consensus with Fencing Tokens

### The Problem

Consensus ensures that all nodes **agree** on a decision. But what if a node thinks it's the leader but actually isn't?

```
Scenario: Leader crashes and a new leader is elected

Old leader: Thinks it's still the leader
Old leader: Tries to write data
New leader: Also writes data

Result: Two leaders writing! Data corruption! ❌
```

### The Solution: Fencing Tokens

Combine consensus (for agreement) with fencing tokens (for enforcement).

```
Step 1: Use Raft to elect a leader
  Raft ensures all nodes agree on who the leader is

Step 2: Leader issues fencing tokens
  Leader: "You are the leader. Here's your fencing token = 33"

Step 3: Storage layer checks tokens
  Old leader: Tries to write with token = 33
  Storage: "I've already seen token 34. Token 33 is stale. REJECTED."
  New leader: Writes with token = 34
  Storage: "Token 34 is valid. ACCEPTED."

Result: Only the new leader can write! ✅
```

### Why This Works

1. **Consensus ensures agreement:** All nodes agree on who the leader is
2. **Fencing tokens ensure enforcement:** Only the current leader can write
3. **Combined safety:** Even if a node thinks it's the leader, it can't write with a stale token

---

## 10. Best Practices

### For Consensus

1. **Use a coordination service (ZooKeeper, etcd, Consul)**
   - Don't implement consensus yourself
   - These services are battle-tested

2. **Use Raft if you need to understand the algorithm**
   - Easier to understand than Paxos
   - Used by etcd, CockroachDB, TiKV

3. **Use Paxos if you need the original algorithm**
   - More complex but equally correct
   - Used by Google Chubby

4. **Always use quorums**
   - Prevents split-brain
   - Ensures safety during network partitions

### For Distributed Transactions

1. **Avoid 2PC if possible**
   - Blocking protocol
   - Coordinator failure causes indefinite waits

2. **Use consensus-based transactions**
   - Raft or Paxos for agreement
   - Fencing tokens for enforcement

3. **Use single-leader replication**
   - Simpler than multi-leader
   - Easier to reason about

4. **Combine consensus with fencing tokens**
   - Ensures both agreement and enforcement
   - Prevents zombie writes

---

## 11. Real-World Examples

### ZooKeeper

ZooKeeper uses **ZAB (Zookeeper Atomic Broadcast)** — a consensus algorithm similar to Paxos.

**Used by:**
- HBase (leader election, region assignment)
- Kafka (broker coordination, partition leadership)
- Solr (cluster state management)

### etcd

etcd uses **Raft** for consensus.

**Used by:**
- Kubernetes (cluster state storage)
- CoreOS (service discovery)
- Consul (service mesh)

### CockroachDB

CockroachDB uses **Raft** for consensus and **fencing tokens** for safety.

**Key features:**
- Distributed SQL database
- Automatic replication
- Strong consistency

### Google Spanner

Google Spanner uses **Paxos** for consensus and **TrueTime** for ordering.

**Key features:**
- Globally distributed database
- Strong consistency across datacenters
- Uses GPS and atomic clocks for TrueTime

---

## 12. Interview Questions

### Q1: What are the four properties of consensus?

**Answer:**
1. **Uniform Agreement:** No two nodes decide differently
2. **Integrity:** No node decides twice
3. **Validity:** If a node decides value v, then v was proposed by some node
4. **Termination:** Every non-crashed node eventually decides

### Q2: What is the FLP impossibility result?

**Answer:** FLP proves that in a purely asynchronous system, there is no algorithm that always reaches consensus if even one node can crash. But practical algorithms use timeouts (partial synchrony) to work around this. They ensure safety even if timeouts are wrong, but may lose liveness temporarily.

### Q3: What is the fatal flaw of Two-Phase Commit?

**Answer:** If the coordinator crashes after Phase 1 but before Phase 2, participants are stuck. They cannot commit or abort. Data is locked, and they must wait for the coordinator to recover. This is a blocking protocol and violates the Termination property of consensus.

### Q4: How does Raft elect a leader?

**Answer:** If a follower times out waiting for heartbeats, it increments the term number, votes for itself, and requests votes from peers. If it gets a majority of votes and its log is at least as up-to-date as a majority, it becomes leader. It sends heartbeats to maintain authority.

### Q5: Why are quorums important in consensus algorithms?

**Answer:** Quorums ensure that any two quorums overlap. This prevents split-brain. If one quorum decides value v, any other quorum must know about it (because they overlap). This ensures uniform agreement even during network partitions.

### Q6: How do fencing tokens prevent zombie writes?

**Answer:** Fencing tokens are monotonically increasing numbers issued with each leadership period. The storage service checks the token on every write and rejects writes with stale tokens. This prevents a node that thinks it's the leader from writing data if a new leader has already been elected.

### Q7: Why is Raft easier to understand than Paxos?

**Answer:** Raft breaks consensus into three sub-problems (Leader Election, Log Replication, Safety) and makes explicit design choices (e.g., strong leader). Paxos is more abstract and doesn't make these choices explicit, making it harder to understand and implement.

---

## 13. Common Mistakes

### Mistake 1: Implementing Consensus Yourself

**Wrong:** Building your own consensus algorithm.

**Right:** Use a battle-tested coordination service (ZooKeeper, etcd, Consul).

### Mistake 2: Using 2PC for Critical Systems

**Wrong:** Using Two-Phase Commit for transactions that must not fail.

**Right:** Use consensus-based transactions (Raft + fencing tokens).

### Mistake 3: Assuming a Single Leader

**Wrong:** Assuming there's always exactly one leader.

**Right:** Use consensus to elect a leader and handle leader transitions.

### Mistake 4: Not Using Fencing Tokens

**Wrong:** Relying only on consensus for safety.

**Right:** Combine consensus with fencing tokens to prevent zombie writes.

### Mistake 5: Ignoring Network Partitions

**Wrong:** Assuming the network is always connected.

**Right:** Use quorums and handle split-brain scenarios.

---

## 14. Further Reading

- DDIA Chapter 9: "Consistency and Consensus"
- Raft paper: "In Search of an Understandable Consensus Algorithm"
- Paxos paper: "The Part-Time Parliament" by Leslie Lamport
- ZooKeeper paper: "ZooKeeper: Wait-free Coordination for Internet-scale Systems"
- Google Spanner paper: "Spanner: Google's Globally-Distributed Database"

---

## Summary

**Key Takeaways:**

1. 🤝 **Consensus** means getting all nodes to agree on something
2. 🚫 **FLP Impossibility** proves consensus is impossible in a purely asynchronous system
3. 🔒 **2PC is blocking** — coordinator failure causes indefinite waits
4. 🎯 **Raft is understandable** — breaks consensus into three sub-problems
5. 🔐 **Fencing tokens prevent zombie writes** — combine consensus with enforcement
6. ⚖️ **Quorums prevent split-brain** — any two quorums overlap
7. 🛠️ **Use coordination services** — don't implement consensus yourself

**Remember:** Consensus is hard. Use battle-tested coordination services (ZooKeeper, etcd, Consul) instead of implementing it yourself.
