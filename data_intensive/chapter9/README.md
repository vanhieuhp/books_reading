# Chapter 9: Consistency and Consensus

This directory contains learning materials and practical exercises for **Chapter 9** of "Designing Data-Intensive Applications" by Martin Kleppmann.

## 📚 Contents

- **[textbook.md](./textbook.md)** - Comprehensive textbook-style explanation of Chapter 9 concepts
- **[3_ordering_guarantees/](./3_ordering_guarantees/)** - Section 3: Ordering Guarantees (code examples and teaching guide)

## 🎯 What You'll Learn

1. **Consistency Guarantees**: Eventual, causal, and linearizable consistency
2. **Linearizability**: The strongest single-object consistency model
3. **Ordering Guarantees**: Causal order, total order, and total order broadcast
4. **Consensus Algorithms**: Raft, Paxos, and how they work
5. **Distributed Transactions**: Two-phase commit and its limitations
6. **Coordination Services**: ZooKeeper and how to use it

## 🚀 Quick Start

### Section 3: Ordering Guarantees

1. Read `textbook.md` for conceptual understanding (focus on section 3)
2. Go to `3_ordering_guarantees/` and run the code examples:
   ```bash
   python 01_causal_ordering.py
   python 02_total_order_broadcast.py
   python 03_ordering_comparison.py
   ```
3. Run the teaching guide:
   ```bash
   python teaching_guide.py
   ```

## 📁 Project Structure

```
chapter9/
├── textbook.md                           # Concepts and theory
├── README.md                             # This file
└── 3_ordering_guarantees/                # Section 3: Ordering Guarantees
    ├── 01_causal_ordering.py             # Causal ordering and vector clocks
    ├── 02_total_order_broadcast.py       # Total order broadcast concepts
    ├── 03_ordering_comparison.py         # Comparing different ordering guarantees
    └── teaching_guide.py                 # 8 interview questions with answers
```

## 🔑 Key Concepts

### Consistency Guarantees (Weakest to Strongest)

```
Eventual Consistency
    ↓
Causal Consistency
    ↓
Linearizability
    ↓
Strict Serializability
```

### Ordering Guarantees

**Causal Ordering (Partial Order):**
- Preserves cause-and-effect relationships
- If A caused B, all nodes see A before B
- Concurrent events can be in any order
- Example: Question → Answer → Comment

**Total Order:**
- All nodes see events in the same order
- No concurrent events (or defined order)
- Stronger than causal, weaker than linearizability
- Example: Single-leader replication log

**Total Order Broadcast:**
- Reliable delivery: All nodes get all messages
- Total ordering: All nodes deliver in the same order
- Equivalent to consensus in power
- Example: Replication log in PostgreSQL, MySQL

**Linearizability:**
- Total order consistent with real-time
- Once a write completes, all subsequent reads see the new value
- Strongest single-object consistency model
- Example: ZooKeeper, etcd, Spanner

### Vector Clocks

Track causal relationships in distributed systems:
- Each node maintains a vector of logical timestamps
- Increment own entry on local event
- Merge vectors on message receipt
- Can detect concurrent events

### Consensus Algorithms

**Raft:**
- Understandable alternative to Paxos
- Three sub-problems: Leader Election, Log Replication, Safety
- Used by: etcd, CockroachDB, TiKV, Consul

**Paxos:**
- Original consensus algorithm
- Notoriously difficult to understand
- Used by: Google Chubby

**ZooKeeper Atomic Broadcast (ZAB):**
- Used by: ZooKeeper
- Provides: Linearizable writes, serializable reads

## 💡 Learning Tips

1. **Run the code** - Each example demonstrates a concept in action
2. **Modify parameters** - Change timeouts, partition sizes, etc. to see effects
3. **Answer interview questions** - Try without looking at answers first
4. **Think about trade-offs** - Consistency vs Availability, Latency vs Ordering
5. **Design exercises** - Try to design a distributed counter using total order broadcast

## 🛠️ Prerequisites

- Python 3.8+
- No external packages needed (uses only standard library!)

## 📖 Key Terminology

| Term | Definition |
|------|-----------|
| **Causal Consistency** | Preserves cause-and-effect ordering; concurrent events can be in any order |
| **Total Order** | Every pair of events is ordered; all nodes see events in the same order |
| **Total Order Broadcast** | Protocol ensuring reliable delivery and total ordering of messages |
| **Linearizability** | Behaves as if one copy of data; operations are atomic and globally ordered |
| **Vector Clock** | Mechanism for tracking causal relationships using logical timestamps |
| **Consensus** | Getting all non-faulty nodes to agree on a single value |
| **Raft** | Understandable consensus algorithm with leader election and log replication |
| **Paxos** | Original consensus algorithm; harder to understand than Raft |
| **Epoch/Term** | Monotonically increasing number identifying a leadership period |
| **CAP Theorem** | During a network partition, choose Consistency or Availability |
| **FLP Impossibility** | No deterministic consensus in a purely asynchronous system |
| **ZooKeeper** | Coordination service providing consensus, leader election, and distributed locks |

## 🎓 Interview Preparation

The `3_ordering_guarantees/teaching_guide.py` contains 8 interview-level questions:

1. **What is the difference between causal ordering and total ordering?** (Medium)
2. **What is total order broadcast and why is it equivalent to consensus?** (Hard)
3. **How does total order broadcast relate to linearizability?** (Hard)
4. **Explain the concept of vector clocks and how they track causality.** (Hard)
5. **In a single-leader replication system, what ordering guarantee does the replication log provide?** (Medium)
6. **Why is total order broadcast equivalent to consensus?** (Hard)
7. **What are the trade-offs between causal consistency and total order?** (Medium)
8. **How would you implement a distributed counter using total order broadcast?** (Hard)

Each question includes:
- Detailed answer with examples
- Key points to remember
- Follow-up questions for deeper understanding

## 🔗 Related Concepts

- **Raft Consensus Algorithm** - Uses total order broadcast for log replication
- **Paxos Algorithm** - Classic consensus algorithm
- **Google Spanner** - Uses TrueTime for clock synchronization
- **Byzantine Generals Problem** - Classic problem in distributed systems
- **CAP Theorem** - Consistency, Availability, Partition tolerance trade-offs
- **Replication** - How databases replicate data across nodes
- **Distributed Locks** - Using consensus for leader election

## 📚 Further Reading

- Chapter 9 of "Designing Data-Intensive Applications" by Martin Kleppmann
- Raft consensus algorithm: https://raft.github.io/
- Google Spanner paper: https://research.google/pubs/spanner-googles-globally-distributed-database/
- Byzantine Generals Problem: Leslie Lamport's papers
- ZooKeeper documentation: https://zookeeper.apache.org/

## 🎯 Learning Path

1. **Start here**: Read `textbook.md` section 3 for conceptual understanding
2. **Run examples**: Execute the code examples to see concepts in action
3. **Study code**: Read through the code to understand implementation details
4. **Answer questions**: Try the interview questions without looking at answers
5. **Modify code**: Change parameters and see how behavior changes
6. **Design exercises**: Try to implement your own ordering guarantees

---

**Start with `3_ordering_guarantees/01_causal_ordering.py` to begin your hands-on practice!**
