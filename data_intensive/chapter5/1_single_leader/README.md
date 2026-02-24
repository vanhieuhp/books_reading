# Section 1: Single-Leader Replication — Hands-On Exercises

## 🎯 Learning Objectives

By completing these 5 exercises, you will:

1. ✅ **Understand the write/read path** in leader-follower replication
2. ✅ **See how replication logs work** (statement-based, WAL, logical)
3. ✅ **Experience the sync vs async trade-off** with real timing data
4. ✅ **Witness failover in action** — leader death, promotion, split-brain
5. ✅ **Reproduce consistency anomalies** — read-your-writes, monotonic reads, causality

## 📁 Exercise Files

| # | File | DDIA Concept | Time |
|---|------|-------------|------|
| 1 | `01_basic_replication.py` | Leader/Follower architecture | 30 min |
| 2 | `02_replication_logs.py` | Statement, WAL, Logical replication | 30 min |
| 3 | `03_sync_vs_async.py` | Synchronous vs Asynchronous replication | 30 min |
| 4 | `04_failover.py` | Failure detection, promotion, split-brain | 45 min |
| 5 | `05_replication_lag.py` | Consistency anomalies and solutions | 45 min |

**Total time**: ~3 hours

## 🚀 How to Run

```bash
# No dependencies needed! Just run with Python 3.8+

# Exercise 1: Basic leader-follower replication
python 01_basic_replication.py

# Exercise 2: Replication log mechanisms
python 02_replication_logs.py

# Exercise 3: Sync vs async trade-offs
python 03_sync_vs_async.py

# Exercise 4: Failover simulation
python 04_failover.py

# Exercise 5: Replication lag anomalies
python 05_replication_lag.py
```

## 🗺️ Mapping to DDIA Chapter 5

```
Exercise 1  →  "Leaders and Followers" (pp. 152-153)
Exercise 2  →  "Implementation of Replication Logs" (pp. 158-161)
Exercise 3  →  "Synchronous vs Asynchronous Replication" (pp. 153-155)
Exercise 4  →  "Handling Node Outages" (pp. 156-158)
Exercise 5  →  "Problems with Replication Lag" (pp. 161-167)
```

## 📊 What You'll See

Each exercise produces **rich, visual output** that tells a story:

### Exercise 1 Output Preview:
```
================================================================================
SINGLE-LEADER REPLICATION: Basic Architecture
================================================================================

[LEADER ] ← Write: INSERT user (id=1, name='Alice')
[LEADER ] Applied to local storage ✅
[LEADER ] Appending to replication log...
[FOLLOW1] Received log entry #1 → Applied ✅
[FOLLOW2] Received log entry #1 → Applied ✅ (lagging 12ms)
[FOLLOW3] Received log entry #1 → Applied ✅ (lagging 25ms)

📊 All nodes consistent: YES
```

### Exercise 4 Output Preview:
```
================================================================================
FAILOVER SIMULATION
================================================================================

💀 LEADER CRASHED at time T=5.0s!
⏱️  Followers detecting via heartbeat timeout...
🔍 Follower2 detected: no heartbeat for 3s
🗳️  Election started: Follower2 (LSN=42) vs Follower1 (LSN=38)
👑 NEW LEADER: Follower2 promoted (most up-to-date)
⚠️  DATA LOSS: 3 writes were on old leader but not replicated!
```

## 🎓 Key Concepts per Exercise

### Exercise 1: Basic Replication
- Leader accepts all writes
- Followers are read-only copies
- Writes flow: Client → Leader → Replication Log → Followers
- Reads can go to any node (but may be stale)

### Exercise 2: Replication Logs
- **Statement-based**: replay SQL (breaks with NOW(), RAND())
- **WAL shipping**: replay raw bytes (coupled to storage engine)
- **Logical/row-based**: replay row changes (best: decoupled, deterministic)

### Exercise 3: Sync vs Async
- **Synchronous**: Slow but safe (data on multiple nodes before ACK)
- **Asynchronous**: Fast but risky (data loss if leader crashes)
- **Semi-synchronous**: Sweet spot (1 sync follower + N async)

### Exercise 4: Failover
- Detecting dead leaders (heartbeat timeout)
- Choosing the best follower (most recent replication position)
- Split-brain disaster (two leaders → data corruption)
- Solutions: STONITH, fencing tokens, consensus

### Exercise 5: Replication Lag
- **Read-your-writes**: User updates profile, sees old data
- **Monotonic reads**: Data appears, disappears, reappears
- **Consistent prefix**: Answer appears before question

## 💡 Exercises to Try After Running

1. **Modify network delay** — increase `REPLICATION_DELAY` to see how lag grows
2. **Change number of followers** — what happens with 10 followers? 100?
3. **Trigger failures at different times** — see how data loss changes
4. **Break the system** — cause split-brain intentionally and observe corruption

## ✅ Completion Checklist

- [ ] Exercise 1: Understand write/read flow in leader-follower
- [ ] Exercise 2: Can explain 3 replication log types and their trade-offs
- [ ] Exercise 3: Understand sync/async/semi-sync trade-offs
- [ ] Exercise 4: Can explain failover steps and split-brain danger
- [ ] Exercise 5: Can identify and fix 3 consistency anomalies

## 📚 Next Steps

After completing Section 1:
1. ✅ You understand the most common replication pattern
2. ✅ You know why failover is the hardest part
3. ✅ Ready for Section 2: Multi-Leader Replication

---

**Start with `01_basic_replication.py`!** 🚀
