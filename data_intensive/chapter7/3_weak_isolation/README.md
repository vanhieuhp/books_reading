# Section 3: Weak Isolation Levels — Hands-On Exercises

## 🎯 Learning Objectives

By completing these 4 exercises, you will:

1. ✅ **Understand Read Committed** — prevents dirty reads/writes but allows read skew
2. ✅ **Learn Snapshot Isolation** — MVCC fixes read skew but allows lost updates
3. ✅ **See Lost Updates** — concurrent read-modify-write and four solutions
4. ✅ **Experience Write Skew** — phantom problem and why serializability is needed

## 📁 Exercise Files

| # | File | DDIA Concept | Time |
|---|------|-------------|------|
| 1 | `01_read_committed.py` | Dirty reads/writes, read skew limitation | 30 min |
| 2 | `02_snapshot_isolation.py` | MVCC, snapshot consistency, garbage collection | 30 min |
| 3 | `03_lost_updates.py` | Read-modify-write, 4 solutions | 30 min |
| 4 | `04_write_skew.py` | Phantom problem, materializing conflicts | 30 min |

**Total time**: ~2 hours

## 🚀 How to Run

```bash
# No dependencies needed! Just run with Python 3.8+

# Exercise 1: Read Committed isolation
python3 01_read_committed.py

# Exercise 2: Snapshot Isolation and MVCC
python3 02_snapshot_isolation.py

# Exercise 3: Lost Updates and solutions
python3 03_lost_updates.py

# Exercise 4: Write Skew and Phantoms
python3 04_write_skew.py
```

## 🗺️ Mapping to DDIA Chapter 7

```
Exercise 1  →  "Read Committed" (pp. 233-237)
Exercise 2  →  "Snapshot Isolation and Repeatable Read" (pp. 237-243)
Exercise 3  →  "Preventing Lost Updates" (pp. 243-250)
Exercise 4  →  "Write Skew and Phantoms" (pp. 250-258)
```

## 📊 What You'll See

### Exercise 1 Output Preview:
```
================================================================================
DEMO 1: No Dirty Reads
================================================================================

  Transaction A: Update balance to 50
  (Txn1 has NOT committed yet)

  Transaction B: Read balance
    ✅ Txn2 sees: balance = 100
       This is the OLD committed value, NOT Txn1's uncommitted change!

  Transaction A: Commit
  (Lock on 'balance' is now released)

  Transaction B: Read balance again
    ✅ Txn2 now sees: balance = 50
       Now it sees Txn1's committed change!
```

### Exercise 2 Output Preview:
```
================================================================================
DEMO 2: Snapshot Isolation Fixes Read Skew
================================================================================

  Alice's View
  Account 1: $500
  Account 2: $600
  Total: $1100
  ✅ CONSISTENT! Alice sees $1000 (from the same snapshot)
```

### Exercise 3 Output Preview:
```
================================================================================
DEMO 1: The Lost Update Problem
================================================================================

  Final State
  counter = 1
  ❌ WRONG! Should be 2, but is 1
     One increment was LOST!
```

### Exercise 4 Output Preview:
```
================================================================================
DEMO 1: The Write Skew Problem
================================================================================

  Final State
  📊 Doctor Status:
    Alice: OFF CALL
    Bob: OFF CALL
    Total on call: 0
  ❌ INVARIANT VIOLATED! Nobody is on call!
```

## 🎓 Key Concepts per Exercise

### Exercise 1: Read Committed
- **Prevents:** Dirty reads, dirty writes
- **Allows:** Read skew, lost updates, write skew
- **Implementation:** Row-level locks + multi-version storage
- **Default in:** PostgreSQL, Oracle, SQL Server
- **Problem:** Read skew (reading from different points in time)

### Exercise 2: Snapshot Isolation
- **Prevents:** Dirty reads, dirty writes, read skew
- **Allows:** Lost updates, write skew
- **Implementation:** MVCC with visibility rules
- **Visibility rule:** created_by committed before txn started
- **Used by:** PostgreSQL (Repeatable Read), MySQL InnoDB, Oracle
- **Garbage collection:** Remove old versions when no longer needed

### Exercise 3: Lost Updates
- **Problem:** Concurrent read-modify-write overwrites changes
- **Solution 1:** Atomic operations (best when applicable)
- **Solution 2:** Explicit locking (SELECT ... FOR UPDATE)
- **Solution 3:** Compare-and-set (for systems without transactions)
- **Solution 4:** Automatic conflict detection (PostgreSQL, Oracle)

### Exercise 4: Write Skew and Phantoms
- **Write skew:** Two txns read overlapping data, write to different objects
- **Phantom:** A write changes the result of an earlier SELECT
- **Problem:** Can't lock rows that don't exist yet
- **Workaround:** Materializing conflicts (ugly, not recommended)
- **Solution:** Serializability (next chapter)

## 💡 Isolation Levels Comparison

| Anomaly | Read Committed | Snapshot Isolation | Two-Phase Locking | Serializable |
|---------|---|---|---|---|
| Dirty reads | ✅ | ✅ | ✅ | ✅ |
| Dirty writes | ✅ | ✅ | ✅ | ✅ |
| Read skew | ❌ | ✅ | ✅ | ✅ |
| Lost updates | ❌ | ❌ | ✅ | ✅ |
| Write skew | ❌ | ❌ | ❌ | ✅ |
| Phantoms | ❌ | ❌ | ❌ | ✅ |

## 💡 Exercises to Try After Running

1. **Modify transaction timing** — see how timing affects anomalies
2. **Add more transactions** — what happens with 3+ concurrent txns?
3. **Change isolation levels** — compare behavior
4. **Create custom scenarios** — test your understanding

## ✅ Completion Checklist

- [ ] Exercise 1: Understand Read Committed and read skew
- [ ] Exercise 2: Understand MVCC and snapshot consistency
- [ ] Exercise 3: Know 4 solutions to lost updates
- [ ] Exercise 4: Understand write skew and phantom problem

## 📚 Next Steps

After completing Section 3:
1. ✅ You understand weak isolation levels
2. ✅ You know the trade-offs between them
3. ✅ You understand real-world concurrency bugs
4. ✅ Ready for Chapter 8: Serializability

---

**Start with `01_read_committed.py`!** 🚀
