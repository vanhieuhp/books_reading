# Section 4: Knowledge, Truth, and Lies — Hands-On Exercises

## 🎯 Learning Objectives

By completing these 4 exercises, you will:

1. ✅ **Understand quorum-based decision making** — why majority consensus matters
2. ✅ **Implement leader election with quorums** — preventing zombie leaders
3. ✅ **Explore Byzantine faults** — what happens when nodes lie
4. ✅ **See why Byzantine tolerance is expensive** — and when you actually need it

## 📁 Exercise Files

| # | File | DDIA Concept | Time |
|---|------|-------------|------|
| 1 | `01_quorum_basics.py` | Quorum voting, majority consensus | 30 min |
| 2 | `02_leader_election.py` | Preventing zombie leaders with quorums | 40 min |
| 3 | `03_byzantine_faults.py` | Byzantine failures and detection | 35 min |
| 4 | `04_byzantine_tolerance.py` | PBFT-style Byzantine fault tolerance | 45 min |

**Total time**: ~2.5 hours

## 🚀 How to Run

```bash
# No dependencies needed! Just run with Python 3.8+

# Exercise 1: Quorum basics
python 01_quorum_basics.py

# Exercise 2: Leader election with quorums
python 02_leader_election.py

# Exercise 3: Byzantine faults
python 03_byzantine_faults.py

# Exercise 4: Byzantine tolerance
python 04_byzantine_tolerance.py
```

## 🗺️ Mapping to DDIA Chapter 8

```
Exercise 1  →  "The Truth is Defined by the Majority" (pp. 300-302)
Exercise 2  →  "The Truth is Defined by the Majority" + Leader Election
Exercise 3  →  "Byzantine Faults" (pp. 302-305)
Exercise 4  →  "Byzantine Fault Tolerance" (pp. 305-310)
```

## 📊 What You'll See

### Exercise 1 Output Preview:
```
================================================================================
QUORUM BASICS: Majority Consensus
================================================================================

Scenario: 5 nodes voting on a value
─────────────────────────────────────────────────────────────────

Node 1: VOTE YES ✅
Node 2: VOTE YES ✅
Node 3: VOTE NO ❌
Node 4: VOTE YES ✅
Node 5: VOTE NO ❌

Quorum size needed: 3 (majority of 5)
Votes for YES: 3
Votes for NO: 2

✅ DECISION: YES (quorum reached)
```

### Exercise 2 Output Preview:
```
================================================================================
LEADER ELECTION WITH QUORUMS
================================================================================

Scenario: Network partition splits cluster
─────────────────────────────────────────────────────────────────

PARTITION A (3 nodes):
  Node 1: Votes for Node 1 as leader ✅
  Node 2: Votes for Node 1 as leader ✅
  Node 3: Votes for Node 1 as leader ✅
  → Quorum reached! Node 1 is VALID leader

PARTITION B (2 nodes):
  Node 4: Votes for Node 4 as leader ✅
  Node 5: Votes for Node 4 as leader ✅
  → NO quorum (need 3 of 5). Node 4 is ZOMBIE leader ❌
```

## 🎓 Key Concepts per Exercise

### Exercise 1: Quorum Basics
- **Quorum**: A majority of nodes (> N/2)
- **Why majority**: Ensures at most one quorum can exist at a time
- **Voting**: Nodes vote on decisions (leader, lock holder, value)
- **Consensus**: A decision is valid only if a quorum agrees

### Exercise 2: Leader Election
- **Heartbeat failure detection**: Followers detect dead leader
- **Election process**: Candidates request votes from all nodes
- **Quorum requirement**: Candidate needs majority to become leader
- **Zombie prevention**: Minority partition cannot elect a leader
- **Split-brain prevention**: Only one partition can have a valid leader

### Exercise 3: Byzantine Faults
- **Byzantine node**: A node that sends arbitrary/contradictory messages
- **Detection**: Comparing messages from different nodes
- **Impact**: Can cause data corruption if not handled
- **Cost**: Byzantine tolerance requires 3f+1 nodes to tolerate f faults
- **When needed**: Blockchains, adversarial environments (rarely in databases)

### Exercise 4: Byzantine Tolerance
- **PBFT (Practical Byzantine Fault Tolerance)**: Algorithm for BFT
- **Phases**: Pre-prepare, prepare, commit
- **Quorum requirement**: 2f+1 nodes needed to tolerate f Byzantine nodes
- **Message complexity**: O(n²) — expensive!
- **Trade-off**: Safety vs. performance

## 💡 Exercises to Try After Running

1. **Modify quorum size** — what happens with 7 nodes? 10 nodes?
2. **Simulate network delays** — how does latency affect election?
3. **Introduce Byzantine nodes** — how many can the system tolerate?
4. **Trigger cascading failures** — what happens with multiple failures?

## ✅ Completion Checklist

- [ ] Exercise 1: Understand quorum voting and majority consensus
- [ ] Exercise 2: Can explain why quorums prevent zombie leaders
- [ ] Exercise 3: Can identify Byzantine faults and their impact
- [ ] Exercise 4: Understand why Byzantine tolerance is expensive

## 📚 Next Steps

After completing Section 4:
1. ✅ You understand how distributed systems make decisions
2. ✅ You know why quorums are the foundation of consensus
3. ✅ You understand the cost of Byzantine tolerance
4. ✅ Ready for real consensus algorithms (Raft, Paxos)

---

**Start with `01_quorum_basics.py`!** 🚀
