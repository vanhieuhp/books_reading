# QUICKSTART: Chapter 8, Section 2 — Unreliable Networks

## 🚀 Quick Start (5 minutes)

Run all exercises in order:

```bash
python 01_network_failures.py
python 02_network_partitions.py
python 03_timeouts_and_delays.py
python 04_phi_accrual_detector.py
```

## 📚 What Each Exercise Teaches

### Exercise 1: Network Failures
**Problem**: When you don't get a response, you can't tell why.

```
Scenario 1: Request lost          → No response
Scenario 2: Server slow           → No response
Scenario 3: Response lost         → No response
Scenario 4: Server crashed        → No response

All four look identical from the client's perspective!
```

**Solution**: Make operations idempotent with request IDs.

---

### Exercise 2: Network Partitions
**Problem**: Network splits cluster into isolated groups. Both groups might elect leaders (split-brain).

```
Before:  A ◄──► B ◄──► C
After:   A ◄──► B     C (isolated)

Partition 1 {A, B}: Elects leader A
Partition 2 {C}:    Elects leader C (WRONG!)

Result: Two leaders → data corruption
```

**Solution**: Use quorum voting. Only majority partition can elect leader.

```
Partition 1 {A, B}: 2 nodes = MAJORITY → can elect leader ✅
Partition 2 {C}:    1 node  = MINORITY → cannot elect leader ❌
```

---

### Exercise 3: Timeouts and Delays
**Problem**: Network delays are unbounded. Fixed timeout is either too short or too long.

```
Too short (30ms):
  ✅ Normal network (50ms): Works
  ❌ Congestion (100ms): False positive!
  ❌ GC pause (500ms): False positive!

Too long (5000ms):
  ✅ All scenarios work
  ❌ Dead node takes 5 seconds to detect
```

**Solution**: Adaptive timeout. Measure observed latencies and adjust.

```
timeout = mean + (multiplier × stdev)
```

---

### Exercise 4: Phi Accrual Detector
**Problem**: Fixed timeout is binary (dead or alive). Doesn't adapt to network patterns.

**Solution**: Phi Accrual outputs suspicion level (0 to infinity).

```
φ(t) = -log10(P(heartbeat arrives within time t))

Healthy node:     φ = 0.5 (low suspicion)
Slow node:        φ = 2.0 (medium suspicion)
Dead node:        φ = 8.0 (high suspicion)

Application chooses threshold (e.g., 5.0) for declaring dead.
```

---

## 🎯 Key Concepts Cheat Sheet

| Concept | Problem | Solution |
|---------|---------|----------|
| **Network Failures** | Can't distinguish 4 failure scenarios | Idempotent operations + request IDs |
| **Network Partitions** | Split-brain (two leaders) | Quorum voting (majority only) |
| **Timeouts** | Fixed timeout too short or too long | Adaptive timeout (based on observed latency) |
| **Failure Detection** | Binary decision (dead/alive) | Phi Accrual (suspicion level) |

---

## 💡 Real-World Applications

### Cassandra
- Uses Phi Accrual detector for failure detection
- Threshold = 5.0 (99.999% confidence)
- Adapts to network conditions automatically

### Akka
- Uses Phi Accrual detector
- Configurable threshold
- Heartbeat interval: 1 second (default)

### Raft Consensus
- Uses fixed timeout for leader election
- Timeout range: 150-300ms (randomized)
- Prevents split-brain with quorum voting

---

## 🔍 Common Mistakes

### ❌ Mistake 1: Fixed Timeout
```python
# BAD: Fixed timeout causes false positives
if time_since_heartbeat > 1000:  # 1 second
    declare_node_dead()
```

### ✅ Solution: Adaptive Timeout
```python
# GOOD: Adaptive timeout based on observed latency
timeout = mean_latency + (2.0 * stdev_latency)
if time_since_heartbeat > timeout:
    declare_node_dead()
```

---

### ❌ Mistake 2: No Quorum
```python
# BAD: Both partitions elect leaders
if no_heartbeat_from_leader:
    elect_new_leader()  # Both partitions do this!
```

### ✅ Solution: Quorum Voting
```python
# GOOD: Only majority partition can elect leader
if len(partition) > total_nodes / 2:
    elect_new_leader()  # Only majority partition
else:
    stop_accepting_writes()  # Minority partition
```

---

### ❌ Mistake 3: Non-Idempotent Operations
```python
# BAD: Retrying causes duplicate execution
def transfer_money(from_account, to_account, amount):
    debit(from_account, amount)
    credit(to_account, amount)

# If response is lost, client retries → double transfer!
```

### ✅ Solution: Idempotent Operations
```python
# GOOD: Include request ID, check if already processed
def transfer_money(request_id, from_account, to_account, amount):
    if already_processed(request_id):
        return cached_response(request_id)

    debit(from_account, amount)
    credit(to_account, amount)
    cache_response(request_id, result)
    return result

# Retrying is safe: server returns cached response
```

---

## 📊 Comparison Table

| Aspect | Fixed Timeout | Adaptive Timeout | Phi Accrual |
|--------|---------------|------------------|------------|
| **Decision** | Binary (dead/alive) | Binary (dead/alive) | Continuous (suspicion level) |
| **Adapts to network** | ❌ No | ✅ Yes | ✅ Yes |
| **False positives** | ❌ Many | ✅ Few | ✅ Very few |
| **Detection speed** | ⚠️ Depends on timeout | ✅ Fast | ✅ Fast |
| **Complexity** | ✅ Simple | ⚠️ Medium | ⚠️ Medium |
| **Used by** | Many systems | Cassandra, Akka | Cassandra, Akka |

---

## 🧪 Try These Experiments

### Experiment 1: Increase Network Delay
Edit `03_timeouts_and_delays.py`:
```python
network = NetworkSimulator(base_latency_ms=100, jitter_ms=50)  # Increase delay
```
See how adaptive timeout adjusts while fixed timeout fails.

### Experiment 2: Change Quorum Size
Edit `02_network_partitions.py`:
```python
cluster = Cluster(["A", "B", "C", "D", "E"])  # 5 nodes instead of 3
```
See how quorum requirement changes (3 out of 5 instead of 2 out of 3).

### Experiment 3: Adjust Phi Threshold
Edit `04_phi_accrual_detector.py`:
```python
detector = PhiAccrualDetector(threshold=3.0)  # More aggressive
```
See how lower threshold detects failures faster but with more false positives.

---

## 📖 Further Reading

- **DDIA Chapter 8**: "The Trouble with Distributed Systems"
- **Cassandra Documentation**: Phi Accrual Failure Detector
- **Akka Documentation**: Failure Detection
- **Raft Consensus**: https://raft.github.io/

---

## ✅ Learning Checklist

- [ ] Understand the 4 network failure scenarios
- [ ] Know why you can't distinguish between them
- [ ] Understand split-brain and quorum voting
- [ ] Know why fixed timeouts don't work
- [ ] Understand adaptive timeouts
- [ ] Know how Phi Accrual works
- [ ] Can explain why Cassandra uses Phi Accrual
- [ ] Can implement idempotent operations

---

**Ready to learn about Unreliable Clocks? Move to Section 3!** ⏰
