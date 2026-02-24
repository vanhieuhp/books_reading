# Section 4: Distributed Transactions and Consensus — Hands-On Exercises

## 🎯 Learning Objectives

By completing these 5 exercises, you will:

1. ✅ **Understand the Consensus Problem** and why it's fundamental to distributed systems
2. ✅ **Experience Two-Phase Commit (2PC)** and discover its fatal flaw: blocking on coordinator failure
3. ✅ **Implement Raft consensus** — the understandable alternative to Paxos
4. ✅ **Explore Paxos (simplified)** — the original consensus algorithm
5. ✅ **Combine consensus with fencing tokens** — building truly safe distributed transactions

## 📁 Exercise Files

| # | File | DDIA Concept | Time |
|---|------|-------------|------|
| 1 | `01_consensus_problem.py` | Consensus definition, FLP impossibility | 30 min |
| 2 | `02_two_phase_commit.py` | 2PC protocol, blocking problem, coordinator failure | 40 min |
| 3 | `03_raft_consensus.py` | Raft algorithm, leader election, log replication | 50 min |
| 4 | `04_paxos_simplified.py` | Paxos algorithm, proposers, acceptors, learners | 50 min |
| 5 | `05_consensus_with_fencing.py` | Combining consensus with fencing tokens | 40 min |

**Total time**: ~3.5 hours

## 🚀 How to Run

```bash
# No dependencies needed! Just run with Python 3.8+

# Exercise 1: Understanding the consensus problem
python 01_consensus_problem.py

# Exercise 2: Two-Phase Commit and its limitations
python 02_two_phase_commit.py

# Exercise 3: Raft consensus algorithm
python 03_raft_consensus.py

# Exercise 4: Paxos simplified
python 04_paxos_simplified.py

# Exercise 5: Consensus with fencing tokens
python 05_consensus_with_fencing.py
```

## 🗺️ Mapping to DDIA Chapter 9

```
Exercise 1  →  "The Consensus Problem" (pp. 147-158)
              "Uniform Agreement, Integrity, Validity, Termination" (pp. 149-152)
              "FLP Impossibility Result" (pp. 159-163)

Exercise 2  →  "Two-Phase Commit (2PC)" (pp. 165-178)
              "Phase 1: Prepare" (pp. 167-170)
              "Phase 2: Commit" (pp. 170-172)
              "The Fatal Flaw: Coordinator Failure" (pp. 173-178)

Exercise 3  →  "Real Consensus Algorithms: Raft" (pp. 200-220)
              "Leader Election" (pp. 205-210)
              "Log Replication" (pp. 210-215)
              "Safety" (pp. 215-220)

Exercise 4  →  "Real Consensus Algorithms: Paxos" (pp. 189-199)
              "Proposers, Acceptors, Learners" (pp. 191-195)
              "The Paxos Algorithm" (pp. 195-199)

Exercise 5  →  "Consensus in Practice" (pp. 239-256)
              "Combining Consensus with Fencing" (pp. 250-256)
```

## 📊 What You'll See

### Exercise 1 Output Preview:
```
================================================================================
THE CONSENSUS PROBLEM
================================================================================

Scenario: 5 nodes trying to agree on a leader

Attempt 1: All nodes propose themselves
  Node 0 proposes: 0
  Node 1 proposes: 1
  Node 2 proposes: 2
  Node 3 proposes: 3
  Node 4 proposes: 4

Result: NO CONSENSUS ❌
  Each node has a different value!

Attempt 2: Using majority voting
  Node 0 proposes: 0
  Node 1 proposes: 0
  Node 2 proposes: 0
  Node 3 proposes: 1
  Node 4 proposes: 1

Result: CONSENSUS ✅
  Majority (3 nodes) agreed on value 0
```

### Exercise 2 Output Preview:
```
================================================================================
TWO-PHASE COMMIT: The Blocking Problem
================================================================================

Scenario: Coordinator crashes after Phase 1

Phase 1 (Prepare):
  Coordinator: "Can you commit transaction T1?"
  Node A: "Yes, I'm ready." (writes to WAL)
  Node B: "Yes, I'm ready." (writes to WAL)

Phase 2 (Commit):
  Coordinator: --- CRASHES ---

Result: BLOCKED ❌
  Node A: Waiting for decision (cannot commit or abort)
  Node B: Waiting for decision (cannot commit or abort)
  Data is LOCKED. Other transactions cannot proceed.

  If coordinator's disk is destroyed:
    Participants may be stuck FOREVER.
```

### Exercise 3 Output Preview:
```
================================================================================
RAFT CONSENSUS: Leader Election and Log Replication
================================================================================

Initial State:
  Node 0: Follower (term 0)
  Node 1: Follower (term 0)
  Node 2: Follower (term 0)

Election Timeout Triggered on Node 1:
  Node 1: Becomes Candidate (term 1)
  Node 1: Requests votes from peers

Voting:
  Node 0: Votes for Node 1 (term 1)
  Node 2: Votes for Node 1 (term 1)

Result: LEADER ELECTED ✅
  Node 1: Leader (term 1)
  Node 0: Follower (term 1)
  Node 2: Follower (term 1)

Log Replication:
  Leader receives write: "set x = 5"
  Leader appends to log: [entry(term=1, value="set x = 5")]
  Leader sends to followers
  Followers append to log
  Leader commits when majority has entry

Result: ALL NODES HAVE SAME LOG ✅
```

## 🎓 Key Concepts per Exercise

### Exercise 1: The Consensus Problem
- **Uniform Agreement:** No two nodes decide differently
- **Integrity:** No node decides twice
- **Validity:** If a node decides value v, then v was proposed by some node
- **Termination:** Every non-crashed node eventually decides
- **FLP Impossibility:** No deterministic algorithm can guarantee consensus in a purely asynchronous system with even one crash

### Exercise 2: Two-Phase Commit
- **Phase 1 (Prepare):** Coordinator asks participants if they can commit
- **Phase 2 (Commit/Abort):** Coordinator tells participants the final decision
- **The Fatal Flaw:** If coordinator crashes after Phase 1, participants are stuck
- **Blocking Protocol:** Participants hold locks while waiting for coordinator
- **Not True Consensus:** Doesn't satisfy the Termination property

### Exercise 3: Raft Consensus
- **Leader Election:** Followers become candidates, request votes, winner becomes leader
- **Log Replication:** Leader receives writes, replicates to followers, commits when majority has entry
- **Safety:** New leader must have all committed entries
- **Terms (Epoch Numbers):** Monotonically increasing, prevent old leaders from overriding new ones
- **Heartbeats:** Leader sends periodic heartbeats to maintain authority

### Exercise 4: Paxos Consensus
- **Proposers:** Propose values
- **Acceptors:** Accept proposals and remember them
- **Learners:** Learn the final decision
- **Two Phases:** Prepare phase (get promises) and Accept phase (get acceptances)
- **Quorum:** Majority of acceptors must agree
- **Liveness:** Paxos can get stuck if proposers keep conflicting (need leader election)

### Exercise 5: Consensus with Fencing
- **Combine Raft with Fencing Tokens:** Use Raft to elect a leader, issue fencing tokens
- **Storage Layer Enforcement:** Storage checks tokens on every write
- **Prevent Zombie Writes:** Even if a leader thinks it's still leader, stale tokens are rejected
- **True Safety:** Combines consensus (agreement) with fencing (enforcement)

## 💡 Exercises to Try After Running

1. **Increase network partitions** — see how Raft handles split-brain scenarios
2. **Simulate node crashes** — observe how Raft recovers
3. **Add Byzantine nodes** — see why Paxos needs quorums
4. **Vary quorum sizes** — understand the trade-off between safety and availability
5. **Disable fencing tokens** — see what happens without the safeguard

## ✅ Completion Checklist

- [ ] Exercise 1: Can explain the four properties of consensus
- [ ] Exercise 1: Understand why FLP impossibility matters
- [ ] Exercise 2: Can identify the blocking problem in 2PC
- [ ] Exercise 2: Know why 2PC is not true consensus
- [ ] Exercise 3: Can explain Raft leader election
- [ ] Exercise 3: Understand how Raft ensures safety
- [ ] Exercise 4: Can explain Paxos proposers, acceptors, learners
- [ ] Exercise 4: Understand why Paxos needs quorums
- [ ] Exercise 5: Can combine consensus with fencing tokens
- [ ] Exercise 5: Understand the complete safety model

## 📚 Next Steps

After completing Section 4:
1. ✅ You understand the consensus problem and why it's hard
2. ✅ You know why 2PC fails and what true consensus looks like
3. ✅ You can explain Raft and Paxos algorithms
4. ✅ You understand how to build safe distributed systems
5. ✅ Ready for real-world systems: ZooKeeper, etcd, CockroachDB

---

**Start with `01_consensus_problem.py`!** 🚀
