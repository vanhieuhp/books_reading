# Chapter 7, Section 2: Single-Object vs. Multi-Object Operations

This directory contains learning materials and practical exercises for **Section 2** of Chapter 7 from "Designing Data-Intensive Applications" by Martin Kleppmann.

## 📚 Contents

- **[01_single_object_atomicity.py](./01_single_object_atomicity.py)** - Single-object atomicity and isolation
- **[02_multi_object_transactions.py](./02_multi_object_transactions.py)** - Multi-object transaction coordination
- **[03_error_handling_retries.py](./03_error_handling_retries.py)** - Error handling and retry strategies
- **[README.md](./README.md)** - This file
- **[QUICKSTART.md](./QUICKSTART.md)** - Get started in 3 steps

## 🎯 What You'll Learn

### The Problem
Databases need to handle multiple types of failures:
1. Hardware crashes (partial writes)
2. Application crashes (incomplete operations)
3. Network failures (lost acknowledgments)
4. Concurrent writes (conflicting updates)
5. Partial reads (seeing half-written data)

### The Solution: Transactions
A transaction groups multiple reads and writes into a logical unit with safety guarantees.

### Two Levels of Transactions

**1. Single-Object Transactions**
- Atomicity: Either the entire write succeeds or none of it does
- Isolation: No other transaction can see a half-written object
- Implementation: Write-Ahead Log (WAL) + locks
- Most databases provide these by default

**2. Multi-Object Transactions**
- Coordinate writes across multiple objects
- Maintain application invariants
- Use cases: bank transfers, foreign keys, indexes
- More complex to implement

## 🚀 Quick Start

1. **Read the textbook section** (Chapter 7, pp. 226-240 in DDIA)
2. **Run the exercises in order:**
   ```bash
   python3 01_single_object_atomicity.py
   python3 02_multi_object_transactions.py
   python3 03_error_handling_retries.py
   ```
3. **Modify and experiment** — change parameters to see how behavior changes

## 📁 Project Structure

```
2_multi_object_transactions/
├── README.md                           # This file
├── QUICKSTART.md                       # Get started in 3 steps
├── 01_single_object_atomicity.py       # Single-object safety
├── 02_multi_object_transactions.py     # Multi-object coordination
└── 03_error_handling_retries.py        # Error handling and retries
```

## 🔑 Key Concepts

### Single-Object Atomicity

**The Problem:**
```
Writing a 20 KB JSON document.
Database crashes after writing 10 KB.
Result: corrupted half-document
```

**The Solution: Write-Ahead Log (WAL)**
```
1. Write change to log FIRST (small, sequential write)
2. Then apply to main storage
3. If crash, replay log to recover
```

**Mechanisms:**
- **Atomicity**: Either all writes succeed or none
- **Isolation**: Locks prevent dirty reads
- **Durability**: WAL ensures recovery

### Multi-Object Transactions

**The Problem:**
```
Bank transfer: debit Account A, credit Account B.
If crash between them: money vanishes!
```

**The Solution: All-or-Nothing Semantics**
```
1. Buffer all writes in transaction's write set
2. On commit: apply all writes atomically
3. On abort: discard all writes
```

**Use Cases:**
- Bank transfers (debit one account, credit another)
- Foreign keys (insert in two tables)
- Denormalized documents (update document and index)
- Secondary indexes (update data and index)

### Error Handling and Retries

**The Problem:**
```
Network fails after transaction succeeds.
Client thinks transaction failed.
Client retries.
Result: duplicate transaction!
```

**The Solution: Idempotency Keys**
```
1. Assign unique key to each request
2. Server records result with key
3. On retry: server detects duplicate
4. Server returns cached result
```

**Retry Strategy:**
- **Transient errors** (network timeout, overload): retry with exponential backoff
- **Permanent errors** (constraint violation, invalid input): fail immediately
- **Duplicate requests**: return cached result

## 💡 Real-World Examples

### Bank Transfer (Multi-Object Transaction)
```python
BEGIN TRANSACTION
  UPDATE accounts SET balance = balance - 100 WHERE id = 1
  UPDATE accounts SET balance = balance + 100 WHERE id = 2
COMMIT

# Either both succeed or both fail
# Money is never lost
```

### Idempotent Payment Processing
```python
# First attempt
POST /payments with idempotency_key="payment_123"
  → Charge credit card
  → Record transaction
  → Return success

# Network fails, client retries
POST /payments with idempotency_key="payment_123"
  → Server detects duplicate key
  → Returns cached result
  → Credit card is NOT charged again
```

### Exponential Backoff
```
Attempt 1: retry immediately
Attempt 2: wait 10ms
Attempt 3: wait 20ms
Attempt 4: wait 40ms
Attempt 5: wait 80ms

Benefits:
  • Reduces load on overloaded system
  • Gives system time to recover
  • Prevents cascading failures
```

## 🛠️ Prerequisites

- Python 3.8+
- No external packages needed (uses only standard library!)

## 📖 How to Use These Exercises

1. **Run each exercise** and read the output carefully — it tells a story
2. **Understand the mechanisms** — why is WAL needed? Why are locks needed?
3. **Modify parameters** — change crash timing, retry counts, etc.
4. **Think about your system** — what guarantees do you need?

## 🎓 Learning Path

1. **Start with 01_single_object_atomicity.py**
   - Understand the atomicity problem
   - See how WAL prevents corruption
   - Learn about locks and isolation
   - Experience crash recovery

2. **Then 02_multi_object_transactions.py**
   - Understand why single-object is insufficient
   - See multi-object coordination
   - Learn about all-or-nothing semantics
   - Experience transaction buffering

3. **Finally 03_error_handling_retries.py**
   - Understand retry challenges
   - Learn about idempotency keys
   - See exponential backoff
   - Experience error classification

## 🤔 Interview Questions

1. **What is atomicity in ACID?**
   - Either ALL writes succeed or NONE of them do
   - Implemented using Write-Ahead Log (WAL)
   - Enables safe retries

2. **Why is single-object atomicity insufficient?**
   - Bank transfer needs to debit one account and credit another
   - If crash between them, money vanishes
   - Need multi-object transactions

3. **How does Write-Ahead Log (WAL) work?**
   - Write change to log FIRST
   - Then apply to main storage
   - If crash, replay log to recover

4. **What is the difference between atomicity and isolation?**
   - Atomicity: all-or-nothing (either all writes or none)
   - Isolation: no dirty reads (locks prevent it)

5. **Why do we need idempotency keys?**
   - Network fails after transaction succeeds
   - Client retries
   - Without idempotency: duplicate effect
   - With idempotency: server detects duplicate, returns cached result

6. **When should we retry a failed transaction?**
   - Transient errors (network timeout, overload): retry with backoff
   - Permanent errors (constraint violation): fail immediately
   - Duplicate requests: return cached result

7. **What is exponential backoff?**
   - Wait time increases with each retry
   - Prevents overwhelming overloaded system
   - Gives system time to recover
   - Prevents cascading failures

8. **What are the three types of errors?**
   - Transient: retry is safe (network timeout, overload)
   - Permanent: retry is pointless (constraint violation, invalid input)
   - Duplicate: return cached result (idempotency key detected duplicate)

## 📚 References

- **DDIA Chapter 7**: "Transactions" (pp. 200-280)
- **Section 2**: "Single-Object vs. Multi-Object Operations" (pp. 226-240)
- **Key concepts**:
  - Atomicity (pp. 226-228)
  - Consistency (pp. 228-229)
  - Isolation (pp. 229-230)
  - Durability (pp. 230-231)
  - Single-object writes (pp. 231-232)
  - Multi-object transactions (pp. 232-235)
  - Error handling and retries (pp. 235-240)

## 🎯 Next Steps

After mastering this section, explore:
- **Section 3**: Weak Isolation Levels (Read Committed, Snapshot Isolation)
- **Section 4**: Serializability (2PL, SSI)
- **Chapter 8**: The Trouble with Distributed Systems

---

**Start with `QUICKSTART.md` to begin your hands-on practice!**
