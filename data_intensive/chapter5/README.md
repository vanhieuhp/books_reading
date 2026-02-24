# Chapter 5: Replication

This directory contains learning materials and practical exercises for **Chapter 5** of "Designing Data-Intensive Applications" by Martin Kleppmann.

## 📚 Contents

- **[textbook.md](./textbook.md)** - Comprehensive textbook-style explanation of Chapter 5 concepts
- **[1_single_leader/](./1_single_leader/)** - Single-Leader Replication exercises (the most important pattern)

## 🎯 What You'll Learn

1. **Single-Leader Replication**: Master/Slave architecture, write/read paths, replication logs
2. **Failover**: Leader failure detection, promotion, split-brain prevention
3. **Replication Lag**: Read-after-write, monotonic reads, consistent prefix reads
4. **Sync vs Async**: Trade-offs between consistency and performance
5. **Multi-Leader Replication**: Conflict resolution, CRDTs (coming soon)
6. **Leaderless Replication**: Quorums, read repair, anti-entropy (coming soon)

## 🚀 Quick Start

1. Read `textbook.md` for conceptual understanding
2. Go to `1_single_leader/` and follow the `QUICKSTART.md`
3. Run the Python exercises — no external dependencies needed!

## 📁 Project Structure

```
chapter5/
├── textbook.md                    # Concepts and theory
├── README.md                      # This file
├── requirements.txt               # Dependencies (stdlib only!)
├── 1_single_leader/               # Section 1 exercises
│   ├── README.md                  # Detailed exercise guide
│   ├── QUICKSTART.md              # Get started in 3 steps
│   ├── 01_basic_replication.py    # Core: leader/follower data flow
│   ├── 02_replication_logs.py     # How data actually moves between nodes
│   ├── 03_sync_vs_async.py        # Sync, async, semi-sync trade-offs
│   ├── 04_failover.py             # Leader failure, promotion, split-brain
│   └── 05_replication_lag.py      # Consistency anomalies and solutions
├── 2_multi_leader/                # (coming soon)
└── 3_leaderless/                  # (coming soon)
```

## 🔑 Key Concepts

### Replication Patterns

- **Single-Leader**: One leader accepts writes, followers replicate (MySQL, PostgreSQL, MongoDB)
- **Multi-Leader**: Multiple leaders, each accepts writes (multi-datacenter, offline-first)
- **Leaderless**: No leader, clients write to multiple nodes (DynamoDB, Cassandra)

### The Hard Problems

- **Failover**: What happens when the leader dies?
- **Split-Brain**: Two nodes both think they're the leader
- **Replication Lag**: Followers are behind, users see stale data

## 🛠️ Prerequisites

- Python 3.8+
- No external packages needed (uses only standard library!)

## 💡 Tips

- Run each exercise and **read the output carefully** — it tells a story
- Modify parameters (delay, failure timing) to see how behavior changes
- Each exercise maps to a section in the textbook

---

**Start with `1_single_leader/QUICKSTART.md` to begin your hands-on practice!**
