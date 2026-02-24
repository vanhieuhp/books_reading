# Section 1: Faults and Partial Failures — Hands-On Exercises

## 🎯 Learning Objectives

By completing these 3 exercises, you will:

1. ✅ **Understand the ambiguity problem** — why you can't tell why you didn't get a response
2. ✅ **See why retries are dangerous** — and how idempotency solves it
3. ✅ **Experience network partitions** — and how they cause split-brain
4. ✅ **Learn about quorums** — how they prevent split-brain
5. ✅ **Understand the timeout dilemma** — why there's no "correct" timeout
6. ✅ **See cascading failures** — how timeouts can cause system collapse
7. ✅ **Learn adaptive timeouts** — a better approach than fixed timeouts

## 📁 Exercise Files

| # | File | DDIA Concept | Time |
|---|------|-------------|------|
| 1 | `01_ambiguity_problem.py` | Ambiguity, retries, idempotency | 30 min |
| 2 | `02_network_partition.py` | Network partitions, split-brain, quorums | 30 min |
| 3 | `03_timeouts.py` | Timeouts, cascading failures, adaptive timeouts | 30 min |

**Total time**: ~1.5 hours

## 🚀 How to Run

```bash
# No dependencies needed! Just run with Python 3.8+

# Exercise 1: The ambiguity problem
python 01_ambiguity_problem.py

# Exercise 2: Network partitions
python 02_network_partition.py

# Exercise 3: Timeouts
python 03_timeouts.py
```

## 🗺️ Mapping to DDIA Chapter 8

```
Exercise 1  →  "Faults and Partial Failures" (pp. 280-283)
              "Unreliable Networks" (pp. 282-283)

Exercise 2  →  "Network Partitions" (pp. 282-283)
              "Knowledge, Truth, and Lies" (pp. 300-302)

Exercise 3  →  "Timeouts and Unbounded Delays" (pp. 283-285)
              "Detecting Faults" (pp. 285-286)
```

## 📊 What You'll See

Each exercise produces **rich, visual output** that tells a story:

### Exercise 1 Output Preview:
```
================================================================================
EXERCISE 1: THE AMBIGUITY PROBLEM
================================================================================

🔴 FAILURE MODE: Request lost in network
────────────────────────────────────────────────────────────────────────────────
💳 Client sends: Payment request #1 for $100.0
   (Client will wait up to 1 second for response)

⏱️  Result: Timeout

🖥️  Server state:
   - Crashed: False
   - Processed requests: []

❓ CLIENT'S PERSPECTIVE:
   'I didn't get a response. Why?'

   Possible reasons:
   1. Request was lost in the network
   2. Server is processing (slow)
   3. Server processed it, but response was lost
   4. Server crashed mid-processing

   ⚠️  I CANNOT TELL WHICH ONE!

✅ ACTUAL REASON: Request lost in network
```

### Exercise 2 Output Preview:
```
================================================================================
SCENARIO 2: NETWORK PARTITION (Split-Brain)
================================================================================

🔴 NETWORK PARTITION OCCURS!
   Node 0 ◄──► Node 1     Node 2 (isolated)

💥 SPLIT-BRAIN DISASTER!
   Multiple leaders: [Node0(LEADER), Node2(LEADER)]

Writing conflicting data to different leaders:
  Node0(LEADER): {'user:1': 'Alice-v1'}
  Node2(LEADER): {'user:1': 'Alice-v2'}

⚠️  Data is now inconsistent across the cluster!
```

### Exercise 3 Output Preview:
```
================================================================================
THE TIMEOUT DILEMMA
================================================================================

Scenario: Normal network with average latency 100ms, jitter 50ms

Observed latencies:
  Min: 45.2ms
  Max: 198.3ms
  Mean: 102.1ms
  Median: 99.8ms
  P99: 185.4ms

Testing different timeout values:

Timeout: 50ms
  Success rate: 32.0%
  False positives: 68.0%
  ⚠️  TOO SHORT: Many false positives!

Timeout: 100ms
  Success rate: 68.5%
  False positives: 31.5%
  ✅ Reasonable trade-off
```

## 🎓 Key Concepts per Exercise

### Exercise 1: The Ambiguity Problem

**The Problem:**
When you send a request and don't get a response, you cannot tell why:
- Request lost in network?
- Server is processing (slow)?
- Server processed it, response lost?
- Server crashed mid-processing?

All four look identical from the client's perspective.

**The Danger:**
Naive retries are dangerous. If the first request actually succeeded, retrying executes it twice.

**The Solution:**
Idempotent operations with unique request IDs. The server deduplicates based on request ID, so retries are safe.

---

### Exercise 2: Network Partitions

**The Problem:**
A network partition splits the cluster into isolated groups. Both sides think the other is dead. Both sides might try to become the leader (split-brain). Data becomes inconsistent.

**The Danger:**
Split-brain causes data corruption. Both leaders accept writes. When the partition heals, you have conflicting data.

**The Solution:**
Quorums. A node can only become leader if it has support from a MAJORITY of nodes. In a partition, at most one side has a quorum.

---

### Exercise 3: Timeouts

**The Problem:**
Network delays are unbounded. There is no "correct" timeout value.
- Too short: false positives (healthy nodes declared dead)
- Too long: users wait forever, system appears frozen

**The Danger:**
Cascading failures. One timeout triggers a failover. Failover causes more load. More load causes more timeouts. System collapses.

**The Solution:**
Adaptive timeouts. Measure observed latencies and adjust timeout based on distribution. Phi Accrual: suspicion level instead of binary decision.

---

## 💡 Exercises to Try After Running

### Exercise 1
1. **Modify failure modes** — change which scenario occurs
2. **Try different retry strategies** — see why they fail
3. **Implement idempotency** — see why it works

### Exercise 2
1. **Change cluster size** — what happens with 5 nodes? 7 nodes?
2. **Introduce multiple partitions** — what if the cluster splits into 3 groups?
3. **Heal partitions at different times** — see how data reconciliation works

### Exercise 3
1. **Increase network jitter** — see how it affects timeouts
2. **Introduce packet loss** — see how it affects success rate
3. **Simulate cascading failures** — increase load and watch timeouts cascade

---

## ✅ Completion Checklist

- [ ] Exercise 1: Understand the ambiguity problem
- [ ] Exercise 1: Understand why retries are dangerous
- [ ] Exercise 1: Understand how idempotency solves it
- [ ] Exercise 2: Understand network partitions
- [ ] Exercise 2: Understand split-brain
- [ ] Exercise 2: Understand how quorums prevent split-brain
- [ ] Exercise 3: Understand the timeout dilemma
- [ ] Exercise 3: Understand cascading failures
- [ ] Exercise 3: Understand adaptive timeouts
- [ ] Can reason about failure scenarios in your own systems

---

## 📚 Next Steps

After completing Section 1:
1. ✅ You understand the fundamental challenges of distributed systems
2. ✅ You know why partial failures are the core problem
3. ✅ Ready for Section 2: Unreliable Networks (deeper dive into network problems)
4. ✅ Ready for Section 3: Unreliable Clocks (time-based problems)

---

## 🎓 Teaching Guide

For a comprehensive explanation of concepts, see [teaching_guide.md](./teaching_guide.md).

---

**Start with `01_ambiguity_problem.py`!** 🚀
