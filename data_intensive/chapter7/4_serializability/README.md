# Section 4: Serializability — Hands-On Exercises

## 🎯 Learning Objectives

By completing these 4 exercises, you will:

1. ✅ **Understand Actual Serial Execution** — simplest way to achieve serializability
2. ✅ **Understand Two-Phase Locking (2PL)** — traditional approach with locks
3. ✅ **Understand Serializable Snapshot Isolation (SSI)** — modern optimistic approach
4. ✅ **Compare all isolation levels** — understand trade-offs and when to use each

## 📁 Exercise Files

| # | File | DDIA Concept | Time |
|---|------|-------------|------|
| 1 | `01_actual_serial_execution.py` | Serial execution, stored procedures, partitioning | 30 min |
| 2 | `02_two_phase_locking.py` | Shared/exclusive locks, deadlocks, predicate locks | 30 min |
| 3 | `03_serializable_snapshot_isolation.py` | MVCC, optimistic execution, conflict detection | 30 min |
| 4 | `04_isolation_levels_comparison.py` | All isolation levels, choosing the right one | 30 min |

**Total time**: ~2 hours

## 🚀 How to Run

```bash
# No dependencies needed! Just run with Python 3.8+

# Exercise 1: Actual Serial Execution
python3 01_actual_serial_execution.py

# Exercise 2: Two-Phase Locking
python3 02_two_phase_locking.py

# Exercise 3: Serializable Snapshot Isolation
python3 03_serializable_snapshot_isolation.py

# Exercise 4: Isolation Levels Comparison
python3 04_isolation_levels_comparison.py
```

## 🗺️ Mapping to DDIA Chapter 7, Section 4

```
Exercise 1  →  "Technique 1: Actual Serial Execution" (pp. 330-333)
Exercise 2  →  "Technique 2: Two-Phase Locking" (pp. 333-340)
Exercise 3  →  "Technique 3: Serializable Snapshot Isolation" (pp. 340-345)
Exercise 4  →  "Summary: Isolation Levels Comparison" (pp. 345-350)
```

## 📊 What You'll Learn

### Exercise 1: Actual Serial Execution

**Concept:** Execute every transaction one at a time, in a single thread.

**Key Points:**
- Simplest way to achieve serializability
- No concurrency anomalies (no dirty reads, lost updates, etc.)
- Works if transactions are short and data fits in memory
- Stored procedures eliminate network round-trips
- Partitioned serial execution enables parallelism

**Real Users:** VoltDB, Redis, Datomic

**Trade-offs:**
- ✅ Simple, no deadlocks, predictable latency
- ❌ Limited throughput (single CPU core)

---

### Exercise 2: Two-Phase Locking (2PL)

**Concept:** Lock before accessing data, release at commit.

**Key Points:**
- Shared locks for reads, exclusive locks for writes
- Readers block writers, writers block readers
- Prevents all concurrency anomalies
- Deadlocks possible
- Predicate locks prevent phantoms

**Real Users:** MySQL InnoDB, PostgreSQL (SERIALIZABLE), Oracle

**Trade-offs:**
- ✅ Guaranteed throughput, works with long transactions
- ❌ High latency due to blocking, deadlocks possible

---

### Exercise 3: Serializable Snapshot Isolation (SSI)

**Concept:** Execute freely, detect conflicts at commit time.

**Key Points:**
- MVCC: Multiple versions of each row
- Optimistic: no locks, no blocking
- Detect stale reads and write conflicts
- Abort and retry if conflicts detected
- No deadlocks

**Real Users:** PostgreSQL (SSI), CockroachDB, FoundationDB

**Trade-offs:**
- ✅ Low latency, no blocking, no deadlocks
- ❌ Higher abort rate under contention

---

### Exercise 4: Isolation Levels Comparison

**Concept:** Compare all isolation levels and techniques.

**Key Points:**
- Read Uncommitted: No protection
- Read Committed: No dirty reads/writes
- Snapshot Isolation: No read skew
- Serializable: No anomalies
- Three techniques: Serial, 2PL, SSI

**Real Users:** All major databases

---

## 💡 Core Concepts

### Serializability

> "The strongest isolation level. It guarantees that even though transactions may execute in parallel, the result is the same as if they had executed one at a time, in some serial order."

### The Three Techniques

1. **Actual Serial Execution**
   - Execute transactions one at a time
   - Simplest, but limited throughput

2. **Two-Phase Locking (2PL)**
   - Lock before accessing, release at commit
   - Traditional approach, but causes blocking

3. **Serializable Snapshot Isolation (SSI)**
   - Execute freely, detect conflicts at commit
   - Modern approach, better latency

### Concurrency Anomalies

| Anomaly | Description | Prevented By |
|---------|-------------|--------------|
| Dirty Read | Reading uncommitted data | Read Committed+ |
| Dirty Write | Overwriting uncommitted data | Read Committed+ |
| Read Skew | Seeing data from two different times | Snapshot Isolation+ |
| Lost Update | Two read-modify-write cycles | Serializable |
| Write Skew | Two transactions violate invariant | Serializable |
| Phantom | Write changes result of query | Serializable |

---

## 🔑 Key Quotes from DDIA

### On Serial Execution
> "The simplest solution: literally execute every transaction one at a time, in a single thread, on a single CPU core. This sounds crazy-slow, but it works if every transaction is very short and fast, the active dataset fits in memory, and write throughput is low enough for a single CPU core."

### On 2PL
> "For ~30 years, Two-Phase Locking was the only widely used algorithm for serializability. If Transaction A has read an object and Transaction B wants to write to that object, B must wait until A commits or aborts."

### On SSI
> "SSI is the cutting-edge approach. It provides full serializability without the performance cost of 2PL. Instead of blocking (pessimistic), SSI allows transactions to proceed without blocking. When a transaction wants to commit, the database checks whether anything bad happened."

### On Choosing Isolation Level
> "Full serializability is expensive. Most databases therefore offer 'weaker' isolation levels that protect against some concurrency bugs but not all. These weak isolation levels are notoriously hard to understand, with subtle bugs that can cause real financial loss."

---

## 🎓 Real-World Systems

### PostgreSQL
- Default: Read Committed
- Serializable: SSI (since v9.1)
- Excellent for OLTP

### MySQL InnoDB
- Default: Repeatable Read (Snapshot Isolation)
- Serializable: 2PL
- Uses Next-Key Locking for phantom prevention

### Oracle
- Default: Read Committed
- Serializable: Snapshot Isolation (confusingly named)
- Excellent for data warehousing

### CockroachDB
- Default: Serializable (SSI)
- Distributed, always serializable
- Great for consistency-critical applications

### DynamoDB
- Default: Read Uncommitted (single-item)
- Multi-item transactions: eventual consistency
- Limited transaction support

---

## 📈 Performance Comparison

### Low Contention (Different Keys)

| Technique | Throughput | Latency | Deadlocks |
|-----------|-----------|---------|-----------|
| Serial | ✗ Low | ✓ Predictable | ✓ None |
| 2PL | ✓ Good | ✗ High | ✗ Possible |
| SSI | ✓✓ Best | ✓✓ Low | ✓ None |

### High Contention (Same Key)

| Technique | Throughput | Latency | Deadlocks |
|-----------|-----------|---------|-----------|
| Serial | ✗ Low | ✓ Predictable | ✓ None |
| 2PL | ✓✓ Best | ✗ High | ✗ Possible |
| SSI | ✗ Low | ✗ High | ✓ None |

---

## 🎯 Choosing an Isolation Level

### Decision Tree

1. **Do you need to prevent dirty reads?**
   - Yes → Use at least Read Committed
   - No → Read Uncommitted (rare)

2. **Do you need to prevent read skew?**
   - Yes → Use at least Snapshot Isolation
   - No → Read Committed is fine

3. **Do you need to prevent lost updates and write skew?**
   - Yes → Use Serializable
   - No → Snapshot Isolation is fine

4. **Can you tolerate occasional aborts?**
   - Yes → Use SSI (better latency)
   - No → Use 2PL (guaranteed throughput)

### Common Scenarios

**OLTP (Online Transaction Processing)**
- Recommendation: Snapshot Isolation or SSI
- Why: Good throughput, low latency

**OLAP (Online Analytical Processing)**
- Recommendation: Read Committed or Snapshot Isolation
- Why: Queries don't need to block each other

**Financial Systems**
- Recommendation: Serializable (2PL or SSI)
- Why: Prevent all anomalies

**Social Media**
- Recommendation: Snapshot Isolation
- Why: Good balance of consistency and performance

---

## ✅ Completion Checklist

- [ ] Exercise 1: Understand serial execution and stored procedures
- [ ] Exercise 2: Understand 2PL, locks, and deadlocks
- [ ] Exercise 3: Understand MVCC, SSI, and conflict detection
- [ ] Exercise 4: Understand all isolation levels and trade-offs

---

## 📚 Next Steps

After completing Section 4:
1. ✅ You understand how to achieve serializability
2. ✅ You know the trade-offs of each technique
3. ✅ You can choose the right isolation level for your workload
4. ✅ Ready for Chapter 8: Distributed Systems

---

**Start with `01_actual_serial_execution.py`!** 🚀
