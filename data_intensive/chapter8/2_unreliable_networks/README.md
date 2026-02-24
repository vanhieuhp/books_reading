# Section 2: Unreliable Networks — Hands-On Exercises

## 🎯 Learning Objectives

By completing these 4 exercises, you will:

1. ✅ **Understand the ambiguity of network failures** — Request lost? Server slow? Response lost? You can't tell!
2. ✅ **Experience network partitions** — Nodes isolated into separate groups, causing split-brain
3. ✅ **Master timeout strategies** — Fixed vs adaptive timeouts and their trade-offs
4. ✅ **Implement failure detection** — Phi Accrual detector for robust node health monitoring

## 📁 Exercise Files

| # | File | DDIA Concept | Time |
|---|------|-------------|------|
| 1 | `01_network_failures.py` | Request/response ambiguity | 30 min |
| 2 | `02_network_partitions.py` | Network partitions & split-brain | 40 min |
| 3 | `03_timeouts_and_delays.py` | Fixed vs adaptive timeouts | 35 min |
| 4 | `04_phi_accrual_detector.py` | Phi Accrual failure detection | 45 min |

**Total time**: ~2.5 hours

## 🚀 How to Run

```bash
# No dependencies needed! Just run with Python 3.8+

# Exercise 1: Network failure scenarios
python 01_network_failures.py

# Exercise 2: Network partitions
python 02_network_partitions.py

# Exercise 3: Timeout strategies
python 03_timeouts_and_delays.py

# Exercise 4: Phi Accrual detector
python 04_phi_accrual_detector.py
```

## 🗺️ Mapping to DDIA Chapter 8

```
Exercise 1  →  "What Can Go Wrong with a Network Request" (pp. 280-282)
Exercise 2  →  "Network Partitions" (pp. 282-284)
Exercise 3  →  "Timeouts and Unbounded Delays" (pp. 284-287)
Exercise 4  →  "Phi Accrual Failure Detector" (pp. 287-289)
```

## 📊 What You'll See

### Exercise 1 Output Preview:
```
================================================================================
NETWORK FAILURES: The Ambiguity Problem
================================================================================

Scenario 1: Request Lost in Network
  Client ──── X ────► Server
  Result: No response (timeout after 5s)

Scenario 2: Server Processing (Slow)
  Client ────────────► Server (processing for 30 seconds...)
  Result: No response (timeout after 5s)

Scenario 3: Response Lost in Network
  Client ◄──── X ──── Server
  Result: No response (timeout after 5s)

Scenario 4: Server Crashed Mid-Processing
  Client ────────────► Server 💥
  Result: No response (timeout after 5s)

🔍 From client's perspective: ALL FOUR LOOK IDENTICAL!
```

### Exercise 2 Output Preview:
```
================================================================================
NETWORK PARTITIONS: Split-Brain Disaster
================================================================================

Normal Cluster:
  [Node A] ◄──► [Node B] ◄──► [Node C]
  All nodes can communicate

After Network Partition:
  [Node A] ◄──► [Node B]     [Node C] (isolated)

  Partition 1 (A, B): Can elect leader, continue operations
  Partition 2 (C):    Thinks it's dead, stops accepting writes

⚠️  DANGER: If C was the leader, A/B might elect a new leader
    → Two leaders in different partitions!
    → Data corruption when partition heals
```

## 🎓 Key Concepts per Exercise

### Exercise 1: Network Failures
- **The fundamental problem**: You can't distinguish between 4 different failure modes
- **Request lost**: Network drops your message before server sees it
- **Server slow**: Server received it but is processing slowly
- **Response lost**: Server processed it but network drops the response
- **Server crashed**: Server crashed while processing (may or may not have completed)
- **Implication**: You must assume the worst and retry, but retries can cause duplicates

### Exercise 2: Network Partitions
- **Definition**: Network link failure isolating groups of nodes
- **Partition tolerance**: System must handle being split into isolated groups
- **Split-brain**: Two groups both think they're the "real" cluster
- **Quorum**: Only the partition with a majority can continue
- **Healing**: When partition heals, conflicts must be resolved

### Exercise 3: Timeouts
- **Fixed timeout**: Simple but brittle (too short = false positives, too long = slow detection)
- **Unbounded delays**: Network delays have no upper bound (packet switching, queueing, GC)
- **Adaptive timeout**: Measure response times, adjust based on distribution
- **Phi Accrual**: Instead of binary "dead/alive", output suspicion level (phi φ)

### Exercise 4: Phi Accrual Detector
- **Heartbeat-based**: Nodes send periodic heartbeats
- **Phi calculation**: φ = -log10(P(heartbeat arrives within time T))
- **Suspicion level**: Higher φ = more confident node is dead
- **Adaptive**: Learns from observed heartbeat patterns
- **Used by**: Akka, Cassandra, other distributed systems

## 💡 Exercises to Try After Running

1. **Modify network delay** — increase `NETWORK_DELAY` to see cascading failures
2. **Change partition duration** — see how long it takes to detect
3. **Trigger failures at different times** — observe different outcomes
4. **Adjust timeout values** — see false positives vs slow detection
5. **Simulate GC pauses** — add random delays to heartbeat processing

## ✅ Completion Checklist

- [ ] Exercise 1: Understand the 4 network failure scenarios
- [ ] Exercise 2: Can explain split-brain and quorum solutions
- [ ] Exercise 3: Understand fixed vs adaptive timeout trade-offs
- [ ] Exercise 4: Can explain phi accrual and implement it

## 📚 Next Steps

After completing Section 2:
1. ✅ You understand why networks are fundamentally unreliable
2. ✅ You know the limits of timeouts and failure detection
3. ✅ Ready for Section 3: Unreliable Clocks

---

**Start with `01_network_failures.py`!** 🚀
