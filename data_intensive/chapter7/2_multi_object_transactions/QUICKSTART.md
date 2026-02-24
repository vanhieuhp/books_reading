# QUICKSTART: Single-Object vs. Multi-Object Operations

Get up and running with transactions in 3 steps.

## Step 1: Understand the Problem (5 minutes)

Databases need to handle multiple types of failures. Transactions are the solution.

**Example 1: Single-Object Problem**
```
Writing a 20 KB JSON document.
Database crashes after writing 10 KB.
Result: corrupted half-document
```

**Example 2: Multi-Object Problem**
```
Bank transfer: debit Account A, credit Account B.
Database crashes between the two writes.
Result: money vanishes!
```

**Example 3: Retry Problem**
```
Network fails after transaction succeeds.
Client thinks transaction failed.
Client retries.
Result: duplicate transaction!
```

## Step 2: Run the Exercises (15 minutes)

Run each exercise in order. Read the output carefully — it tells a story.

### Exercise 1: Single-Object Atomicity (5 minutes)

```bash
python3 01_single_object_atomicity.py
```

**What you'll see:**
- How atomicity prevents corruption
- How Write-Ahead Log (WAL) works
- How locks prevent dirty reads
- How crash recovery works

**Key insight:** WAL ensures that either the entire write succeeds or none of it does.

### Exercise 2: Multi-Object Transactions (5 minutes)

```bash
python3 02_multi_object_transactions.py
```

**What you'll see:**
- Why single-object atomicity is insufficient
- How multi-object transactions coordinate writes
- Real-world scenarios (bank transfers, foreign keys, indexes)
- All-or-nothing semantics

**Key insight:** Multi-object transactions keep related data in sync.

### Exercise 3: Error Handling and Retries (5 minutes)

```bash
python3 03_error_handling_retries.py
```

**What you'll see:**
- Why retries are needed
- How idempotency keys prevent duplicates
- Exponential backoff strategy
- Error classification (transient vs permanent)

**Key insight:** Retries are safe because of atomicity, but need idempotency keys.

## Step 3: Experiment (10 minutes)

Modify the code to see how behavior changes.

### Experiment 1: Crash Timing

In `01_single_object_atomicity.py`, modify `demo_5_crash_recovery()`:
```python
# Before crash, change the number of transactions
txn_1 = db.begin_transaction()
db.write(txn_1, "counter", 1)
db.commit_transaction(txn_1)

txn_2 = db.begin_transaction()
db.write(txn_2, "counter", 2)
# Crash here (txn_2 is active, not committed)
```

**What happens:** Active transactions are rolled back, committed transactions are replayed.

### Experiment 2: Multi-Object Failure

In `02_multi_object_transactions.py`, modify `demo_5_transaction_atomicity()`:
```python
# Simulate failure in the middle
txn_id = db.begin_transaction()
db.write(txn_id, "account_a", 70)
db.write(txn_id, "account_b", 80)
# Simulate failure here
db.abort(txn_id)  # All writes are rolled back
```

**What happens:** All writes are rolled back together (all-or-nothing).

### Experiment 3: Retry Strategy

In `03_error_handling_retries.py`, modify the retry policy:
```python
# Change max retries and backoff
policy = RetryPolicy(max_retries=10, initial_backoff_ms=5)
```

**What happens:** More retries with shorter backoff times.

## 🎯 Key Takeaways

### Single-Object Atomicity
```
Problem: Crash during write leaves corrupted data
Solution: Write-Ahead Log (WAL)
  1. Write to log FIRST
  2. Then apply to storage
  3. If crash, replay log to recover
```

### Multi-Object Transactions
```
Problem: Crash between writes loses data
Solution: All-or-nothing semantics
  1. Buffer all writes
  2. On commit: apply all atomically
  3. On abort: discard all
```

### Error Handling and Retries
```
Problem: Network fails after success, client retries
Solution: Idempotency keys
  1. Assign unique key to each request
  2. Server records result with key
  3. On retry: return cached result
```

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

## 🤔 Think About Your System

**Question 1: What guarantees do you need?**
- Atomicity: all-or-nothing writes
- Isolation: no dirty reads
- Durability: survive crashes
- Consistency: maintain invariants

**Question 2: What errors can occur?**
- Hardware crashes
- Network failures
- Application crashes
- Concurrent writes
- Partial reads

**Question 3: How should you handle retries?**
- Transient errors: retry with backoff
- Permanent errors: fail immediately
- Duplicate requests: return cached result

## 📚 Next Steps

1. **Read DDIA Chapter 7, Section 2** (pp. 226-240)
2. **Explore the code** — modify parameters and see what happens
3. **Think about your system** — what guarantees do you need?
4. **Move to Section 3** — Weak Isolation Levels

## 🎓 Interview Prep

**Q: What is atomicity in ACID?**

A: Either ALL writes succeed or NONE of them do. Implemented using Write-Ahead Log (WAL). Enables safe retries.

**Q: Why is single-object atomicity insufficient?**

A: Bank transfer needs to debit one account and credit another. If crash between them, money vanishes. Need multi-object transactions.

**Q: How does Write-Ahead Log (WAL) work?**

A: Write change to log FIRST, then apply to main storage. If crash, replay log to recover.

**Q: Why do we need idempotency keys?**

A: Network fails after transaction succeeds. Client retries. Without idempotency: duplicate effect. With idempotency: server detects duplicate, returns cached result.

**Q: When should we retry a failed transaction?**

A: Transient errors (network timeout, overload): retry with backoff. Permanent errors (constraint violation): fail immediately. Duplicate requests: return cached result.

---

**Ready to dive deeper?** Read the full README.md for more details and real-world examples.
