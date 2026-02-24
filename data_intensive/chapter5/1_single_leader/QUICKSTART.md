# Section 1: Quick Start Guide

## 🚀 Get Started in 3 Steps

### Step 1: Verify Python Version

```bash
python --version
# Requires Python 3.8+
```

### Step 2: Run Your First Exercise

```bash
python 01_basic_replication.py
```

### Step 3: Read the Output Carefully

The output tells a **story** — it simulates real distributed system behavior.
Watch for timestamps, lag measurements, and consistency checks.

## 📋 Exercise Order

Run them in order — each builds on the previous:

```
1. 01_basic_replication.py   ← Start here! Core architecture
2. 02_replication_logs.py    ← How data moves between nodes
3. 03_sync_vs_async.py       ← The fundamental trade-off
4. 04_failover.py            ← What happens when leader dies
5. 05_replication_lag.py     ← Consistency problems users face
```

## 💡 Key Questions to Answer

As you run each exercise, think about:

### Exercise 1: Basic Replication
- Why must ALL writes go through the leader?
- What happens if a follower receives a write directly?
- How does adding more followers affect read performance?

### Exercise 2: Replication Logs
- Why does `NOW()` break statement-based replication?
- Why can't you do a rolling upgrade with WAL shipping?
- Why is logical replication the best approach?

### Exercise 3: Sync vs Async
- What happens if a sync follower is slow?
- How much data can you lose with async replication?
- Why is semi-sync the production sweet spot?

### Exercise 4: Failover
- How do you tell if a leader is dead vs. just slow?
- Why is split-brain so dangerous?
- What data is lost during failover?

### Exercise 5: Replication Lag
- Why does a user see their old profile after updating?
- Why does a comment appear, disappear, then reappear?
- Why does an answer appear before a question?

## ✅ Completion Checklist

- [ ] Ran all 5 exercises successfully
- [ ] Can explain single-leader architecture
- [ ] Understand 3 types of replication logs
- [ ] Know the sync/async/semi-sync trade-offs
- [ ] Understand failover steps and split-brain
- [ ] Can identify 3 consistency anomalies

## 📚 Next Steps

After completing all exercises:
1. ✅ Re-read DDIA Chapter 5, pages 152-167
2. ✅ Move to multi-leader replication (Section 2)

---

**Ready? Run `python 01_basic_replication.py` now!** 🚀
