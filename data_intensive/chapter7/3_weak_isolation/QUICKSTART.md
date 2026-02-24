# QUICKSTART: Section 3 — Weak Isolation Levels

## 🎯 5-Minute Overview

**Isolation levels** define how much concurrency anomalies a database prevents. There are four main levels:

### Level 1: Read Committed (Most Common)
```
Prevents:
  ✅ Dirty reads (never see uncommitted data)
  ✅ Dirty writes (never overwrite uncommitted data)

Allows:
  ❌ Read skew (reading from different points in time)
  ❌ Lost updates (concurrent read-modify-write)
  ❌ Write skew (phantom problem)

Implementation:
  • Row-level locks for writes
  • Multi-version storage for reads
  • Readers see only committed data

Default in: PostgreSQL, Oracle, SQL Server
```

### Level 2: Snapshot Isolation (MVCC)
```
Prevents:
  ✅ Dirty reads and writes
  ✅ Read skew (all reads from same snapshot)

Allows:
  ❌ Lost updates
  ❌ Write skew

Implementation:
  • Multi-Version Concurrency Control (MVCC)
  • Each txn reads from a consistent snapshot
  • Visibility rule: created_by committed before txn started

Used by: PostgreSQL (Repeatable Read), MySQL InnoDB, Oracle
```

### Level 3: Two-Phase Locking (2PL)
```
Prevents:
  ✅ All anomalies except phantoms

Allows:
  ❌ Phantoms (write changes result of SELECT)

Trade-off:
  • Readers block writers (performance impact)
  • Risk of deadlocks
```

### Level 4: Serializability (Strongest)
```
Prevents:
  ✅ ALL anomalies (dirty reads, read skew, lost updates, write skew, phantoms)

Trade-off:
  • Highest performance cost
  • Used by VoltDB, Redis, Datomic
```

## 🚀 Quick Start (10 minutes)

### Step 1: Run Exercise 1 (Read Committed)
```bash
python3 01_read_committed.py
```

**What you'll see:**
- How Read Committed prevents dirty reads
- How it prevents dirty writes
- The read skew problem (Alice sees inconsistent totals)

**Key insight:** Read Committed is the default, but it allows read skew.

### Step 2: Run Exercise 2 (Snapshot Isolation)
```bash
python3 02_snapshot_isolation.py
```

**What you'll see:**
- How MVCC provides consistent snapshots
- How it fixes read skew
- Visibility rules for multi-version storage
- Garbage collection of old versions

**Key insight:** Snapshot Isolation fixes read skew but allows lost updates.

### Step 3: Run Exercise 3 (Lost Updates)
```bash
python3 03_lost_updates.py
```

**What you'll see:**
- The lost update problem (concurrent read-modify-write)
- Solution 1: Atomic operations (best)
- Solution 2: Explicit locking (SELECT ... FOR UPDATE)
- Solution 3: Compare-and-set (for NoSQL)
- Solution 4: Automatic conflict detection

**Key insight:** Both Read Committed and Snapshot Isolation allow lost updates.

### Step 4: Run Exercise 4 (Write Skew)
```bash
python3 04_write_skew.py
```

**What you'll see:**
- The write skew problem (on-call doctors example)
- The phantom problem (can't lock rows that don't exist)
- Materializing conflicts (ugly workaround)
- Real-world examples (booking, inventory, games)

**Key insight:** Write skew requires serializability to prevent.

## 📊 Anomalies Explained

### Dirty Read
```
Transaction A:                    Transaction B:
  UPDATE balance SET value = 50
  (not committed yet)
                                  SELECT balance
                                  (sees 50 - DIRTY!)
  ROLLBACK;
  (balance is back to 100)
                                  (but B already saw 50!)
```

### Read Skew
```
Alice has $500 in each account ($1000 total).
Transfer moves $100 from Account 1 to Account 2.

Alice reads Account 1: $500 (before transfer)
Transfer commits
Alice reads Account 2: $600 (after transfer)
Alice sees: $500 + $600 = $1100 (WRONG!)
```

### Lost Update
```
Transaction A:                    Transaction B:
  counter = read(key);  → 42      counter = read(key);  → 42
  counter = counter + 1;          counter = counter + 1;
  write(key, 43);                 write(key, 43);

Result: counter = 43 (should be 44!)
```

### Write Skew
```
Invariant: At least 1 doctor on call

Transaction A:                    Transaction B:
  count = SELECT COUNT(*)
  WHERE on_call = TRUE;  → 2      count = SELECT COUNT(*)
                                  WHERE on_call = TRUE;  → 2
  if count >= 2:
    UPDATE doctors SET on_call=FALSE
    WHERE name='Alice';
                                  if count >= 2:
                                    UPDATE doctors SET on_call=FALSE
                                    WHERE name='Bob';

Result: 0 doctors on call (INVARIANT BROKEN!)
```

### Phantom
```
Transaction A:                    Transaction B:
  SELECT * FROM bookings
  WHERE room='A' AND time='2pm'
  (returns 0 rows)
                                  INSERT INTO bookings
                                  VALUES (room='A', time='2pm')
                                  COMMIT;
  if (no_conflicts):
    INSERT INTO bookings
    VALUES (room='A', time='2pm')
  (CONFLICT! But we didn't detect it)
```

## 💡 Key Insights from DDIA

### 1. Read Committed is Default but Weak
```
Most databases default to Read Committed because:
  ✅ Good performance (minimal locking)
  ✅ Prevents dirty reads/writes
  ❌ But allows read skew, lost updates, write skew

If you see anomalies, upgrade to Snapshot Isolation.
```

### 2. MVCC is Elegant
```
Multi-Version Concurrency Control:
  • Store multiple versions of each item
  • Each version has metadata: created_by, deleted_by
  • Visibility rule: created_by committed before txn started
  • Readers never block writers (great for read-heavy workloads)
  • Garbage collect old versions when no longer needed
```

### 3. Lost Updates Need Explicit Handling
```
Both Read Committed and Snapshot Isolation allow lost updates.
You must choose a solution:

  1. Atomic operations (best when applicable)
     UPDATE counter SET value = value + 1;

  2. Explicit locking (general purpose)
     SELECT * FROM counter FOR UPDATE;

  3. Compare-and-set (for NoSQL)
     UPDATE counter SET value = new WHERE value = old;

  4. Automatic detection (PostgreSQL, Oracle)
     Database detects conflict and aborts one txn
```

### 4. Write Skew is Subtle
```
Write skew is a generalized version of lost update:
  • Two txns read overlapping data
  • Make decisions based on what they read
  • Write to DIFFERENT objects
  • Result violates application invariant

Examples:
  • On-call doctors (must have at least 1)
  • Meeting room booking (no double-booking)
  • Inventory management (can't oversell)
  • Multiplayer games (player can't be in two places)

Solution: Serializability (next chapter)
```

### 5. Phantoms Can't Be Locked
```
Phantom problem:
  • A write changes the result of an earlier SELECT
  • Can't use SELECT ... FOR UPDATE to prevent this
  • The conflicting row doesn't exist when we try to lock it

Workaround: Materializing conflicts
  • Create a table of all possible time slots
  • Lock the specific time slot row
  • Ugly and doesn't scale well

Better solution: Serializability
```

## 🎓 When to Use Each Level

### Read Committed
```
Use when:
  ✅ You don't have concurrent writes to the same data
  ✅ You can tolerate read skew
  ✅ You need good performance

Avoid when:
  ❌ You have concurrent read-modify-write cycles
  ❌ You have application invariants that must be maintained
```

### Snapshot Isolation
```
Use when:
  ✅ You need to prevent read skew
  ✅ You have mostly reads with occasional writes
  ✅ You can handle lost updates with explicit locking

Avoid when:
  ❌ You have many concurrent writes to the same data
  ❌ You have complex application invariants
```

### Two-Phase Locking
```
Use when:
  ✅ You need to prevent lost updates
  ✅ You can tolerate blocking

Avoid when:
  ❌ You have high read concurrency (readers block writers)
  ❌ You want to avoid deadlocks
```

### Serializability
```
Use when:
  ✅ You have complex application invariants
  ✅ You need the strongest guarantees
  ✅ You can tolerate performance cost

Avoid when:
  ❌ You need high throughput
  ❌ You have long-running transactions
```

## ❓ Common Questions

**Q: What's the difference between Read Committed and Snapshot Isolation?**
A: Read Committed allows read skew (reading from different points in time). Snapshot Isolation fixes this by having each transaction read from a consistent snapshot.

**Q: Why does Snapshot Isolation allow lost updates?**
A: Because both transactions read the same value, modify it independently, and write back. Neither transaction sees the other's change.

**Q: Can I use explicit locking to prevent write skew?**
A: Not easily. Write skew involves writing to different objects, so you'd need to lock both objects. And with phantoms, you can't lock rows that don't exist yet.

**Q: What's the performance impact of Snapshot Isolation?**
A: Minimal. MVCC is very efficient. The main cost is garbage collection of old versions.

**Q: Should I always use Serializability?**
A: No. Serializability has a performance cost. Start with Snapshot Isolation and use explicit locking for lost updates. Only upgrade to Serializability if you have write skew.

**Q: How do I know if I have a concurrency bug?**
A: Look for:
  • Inconsistent data (read skew)
  • Lost updates (counter doesn't match expected value)
  • Violated invariants (on-call doctor example)
  • Phantom reads (data appears/disappears)

## 📚 Next Steps

1. Run all 4 exercises in order
2. Modify the code to experiment:
   - Add more transactions
   - Change timing
   - Create custom scenarios
3. Read DDIA Chapter 7 for deeper understanding
4. Move on to Chapter 8: Serializability

---

**Ready to start?** Run `python3 01_read_committed.py` 🚀
