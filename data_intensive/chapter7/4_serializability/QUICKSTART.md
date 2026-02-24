# Quick Start Guide — Chapter 7, Section 4

## 🚀 Get Started in 5 Minutes

### Step 1: Run Exercise 1 (Actual Serial Execution)

```bash
python3 01_actual_serial_execution.py
```

**What you'll learn:**
- How serial execution eliminates all concurrency anomalies
- Why stored procedures are important
- How partitioned serial execution enables parallelism

**Time:** ~5 minutes

---

### Step 2: Run Exercise 2 (Two-Phase Locking)

```bash
python3 02_two_phase_locking.py
```

**What you'll learn:**
- How shared and exclusive locks work
- Why readers block writers and vice versa
- How deadlocks occur and are detected
- How predicate locks prevent phantoms

**Time:** ~5 minutes

---

### Step 3: Run Exercise 3 (Serializable Snapshot Isolation)

```bash
python3 03_serializable_snapshot_isolation.py
```

**What you'll learn:**
- How MVCC (Multi-Version Concurrency Control) works
- Why SSI is optimistic (no blocking)
- How conflicts are detected at commit time
- Why abort rate increases under contention

**Time:** ~5 minutes

---

### Step 4: Run Exercise 4 (Isolation Levels Comparison)

```bash
python3 04_isolation_levels_comparison.py
```

**What you'll learn:**
- All isolation levels and what they prevent
- Real-world database defaults
- How to choose the right isolation level
- Practical advice for using transactions

**Time:** ~5 minutes

---

## 📊 The Big Picture

### Three Techniques for Serializability

```
ACTUAL SERIAL EXECUTION
  • Execute one transaction at a time
  • ✅ Simple, no deadlocks
  • ❌ Limited throughput

TWO-PHASE LOCKING (2PL)
  • Lock before accessing, release at commit
  • ✅ Guaranteed throughput
  • ❌ High latency, deadlocks possible

SERIALIZABLE SNAPSHOT ISOLATION (SSI)
  • Execute freely, detect conflicts at commit
  • ✅ Low latency, no deadlocks
  • ❌ Higher abort rate under contention
```

### Isolation Levels

```
Read Uncommitted
  • No protection
  • Rarely used

Read Committed
  • No dirty reads/writes
  • Default in PostgreSQL, Oracle, SQL Server

Snapshot Isolation
  • No read skew
  • Default in MySQL InnoDB (called Repeatable Read)

Serializable
  • No anomalies
  • Strongest guarantee, highest cost
```

---

## 🎯 Key Insights from DDIA

### On Serial Execution
> "The simplest solution: literally execute every transaction one at a time, in a single thread, on a single CPU core."

### On 2PL
> "For ~30 years, Two-Phase Locking was the only widely used algorithm for serializability. If Transaction A has read an object and Transaction B wants to write to that object, B must wait until A commits or aborts."

### On SSI
> "SSI is the cutting-edge approach. It provides full serializability without the performance cost of 2PL."

### On Choosing Isolation Level
> "Full serializability is expensive. Most databases therefore offer 'weaker' isolation levels that protect against some concurrency bugs but not all."

---

## 💡 Discussion Questions

After running the exercises, think about:

1. **When would you use serial execution?**
   - Answer: Short transactions, in-memory data, low write throughput

2. **Why is 2PL still used despite its drawbacks?**
   - Answer: Guaranteed throughput, works with long transactions, well-understood

3. **Why is SSI better for modern workloads?**
   - Answer: Low latency, no deadlocks, scales to multiple cores

4. **How do you choose between 2PL and SSI?**
   - Answer: Low contention → SSI, High contention → 2PL

5. **What's the cost of serializability?**
   - Answer: Performance (throughput or latency), complexity

---

## 🔗 Real-World Systems

### PostgreSQL
- Default: Read Committed
- Serializable: SSI (since v9.1)
- Excellent for OLTP

### MySQL InnoDB
- Default: Repeatable Read (Snapshot Isolation)
- Serializable: 2PL
- Uses Next-Key Locking

### CockroachDB
- Default: Serializable (SSI)
- Distributed, always serializable
- Great for consistency-critical applications

### DynamoDB
- Limited transaction support
- Single-item: Read Uncommitted
- Multi-item: eventual consistency

---

## 📚 Next Steps

1. ✅ Complete all 4 exercises
2. ✅ Understand the trade-offs of each technique
3. ✅ Read DDIA Chapter 7, Section 4 (pp. 330-350)
4. ✅ Move to Chapter 8: Distributed Systems

---

## ❓ Troubleshooting

**Q: The output is too fast to read**
- A: Add `input()` calls in the code to pause between demos

**Q: I want to modify the code**
- A: Great! Try changing:
  - Number of transactions
  - Contention level (same key vs different keys)
  - Transaction complexity

**Q: How do I run just one demo?**
- A: Edit the `main()` function and comment out the demos you don't want

---

**Ready? Start with `python3 01_actual_serial_execution.py`!** 🚀
