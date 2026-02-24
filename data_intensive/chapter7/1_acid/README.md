# Chapter 7, Section 1: The Meaning of ACID

## Overview

This section covers **ACID transactions** — the fundamental mechanism for ensuring data safety in databases.

**The Problem:**
Many things can go wrong in a data system:
1. Database software or hardware may fail at any time
2. Application may crash halfway through a series of operations
3. Network interruptions can cut off the application from the database
4. Multiple clients may write to the database simultaneously
5. A client may read partially updated data
6. Race conditions between clients can cause bugs

**The Solution:**
**Transactions** group several reads and writes into a logical unit. Either the entire transaction succeeds (**commit**) or it fails (**abort/rollback**). If it fails, the application can safely retry.

---

## ACID: Four Safety Guarantees

### 1. Atomicity: All-or-Nothing

**Definition:**
If a transaction makes several changes, and the database crashes after completing only some of those changes, those partial changes must be **rolled back**. Either ALL writes are applied, or NONE are.

**Key Benefit:**
If a transaction is aborted (for any reason — crash, network failure, constraint violation), the application can be sure that nothing was half-written. It can safely retry the entire transaction.

**Example:**
```
Transferring $100 from Account A to Account B:
  Step 1: Debit $100 from Account A
  --- DATABASE CRASHES HERE ---
  Step 2: Credit $100 to Account B (NEVER EXECUTED!)

Without Atomicity:
  Account A lost $100. Account B never received it. Money vanished.

With Atomicity:
  The database detects the crash and rolls back Step 1.
  Account A gets its $100 back. The user can retry.
```

**Implementation:**
- **Write-Ahead Log (WAL):** All writes are logged to disk BEFORE they're applied to the database
- **On crash:** The log is replayed to recover committed transactions
- **Rollback:** If a transaction is aborted, its writes are undone

**Trade-offs:**
- ✅ Guarantees no partial updates
- ❌ Logging overhead (writes to disk)
- ❌ Rollback overhead (undoing partial writes)

---

### 2. Consistency: Invariants Maintained

**Definition:**
You have certain *invariants* (statements about your data that must always be true). A transaction guarantees that if the invariants were true before the transaction, they will be true after.

**Example Invariant:**
"In an accounting system, credits and debits across all accounts must always balance to zero."

**Important Note:**
**Consistency is the APPLICATION's responsibility, not the database's!**

The database can enforce some constraints (foreign keys, unique constraints), but it cannot know the correctness rules of your specific business logic.

**Implementation:**
- Application logic: Ensure transactions maintain invariants
- Database constraints: Foreign keys, unique constraints, check constraints
- Validation: Application validates data before committing

**Trade-offs:**
- ✅ Data integrity is maintained
- ❌ Application must understand and enforce invariants
- ❌ Database constraint checking overhead

---

### 3. Isolation: Concurrent Transactions Don't Interfere

**Definition:**
Concurrently executing transactions are isolated from each other: they cannot step on each other's toes.

**Formal Guarantee:**
**Serializability:** The database guarantees that even though transactions may run concurrently, the result is the same as if they had run one after another, in some serial order.

**Why It Matters:**
If Transaction A reads data while Transaction B is modifying it, Transaction A could see halfway-written results, leading to bugs. Isolation prevents this.

**Example Problem (Dirty Read):**
```
Transaction A:                    Transaction B:
  BEGIN;                            BEGIN;
  UPDATE users SET age = 30         -- No dirty read!
  WHERE id = 1;                     SELECT age FROM users WHERE id = 1;
  -- (not committed yet!)           -- Returns old value (e.g., 25), NOT 30.
  COMMIT;
                                    SELECT age FROM users WHERE id = 1;
                                    -- NOW returns 30.
```

**Implementation:**
- **Locking:** Transactions lock data they're modifying
- **MVCC:** Multiple versions of data for different transactions
- **Isolation levels:** Different levels of protection (Read Committed, Snapshot Isolation, Serializability)

**Trade-offs:**
- ✅ No dirty reads, lost updates, or race conditions
- ❌ Locking overhead (contention, deadlocks)
- ❌ Memory overhead (multiple versions)
- ❌ Performance impact (serialization)

**Important:**
Full serializability is expensive. Most databases use **weaker isolation levels** for better performance. This is where most real-world bugs happen!

---

### 4. Durability: Committed Data Survives Crashes

**Definition:**
Once a transaction has committed successfully, any data it has written will not be forgotten, even if there is a hardware fault or the database crashes.

**Implementation:**
- **Write-Ahead Log (WAL):** Writes to disk before commit
- **Replication:** Data is replicated to other nodes
- **Fsync:** Force operating system to flush buffers to disk

**Example:**
```
1. Application sends: "Transfer $100 from A to B"
2. Database writes to WAL: "Debit A, Credit B"
3. Database applies to memory: A = 400, B = 600
4. Database commits: Writes commit marker to WAL
5. Database crashes
6. On recovery: Replay WAL, recover the committed transaction
```

**Important Note:**
**Perfect durability does not exist!**

If every disk in every datacenter is destroyed simultaneously, no database can save you. Durability is about reducing risk, not eliminating it.

**Trade-offs:**
- ✅ Data is safe and persistent
- ❌ Disk I/O overhead (WAL writes)
- ❌ Network overhead (replication)
- ❌ Latency (must wait for disk/network)

---

## Single-Object vs. Multi-Object Transactions

### Single-Object Writes

**Definition:**
Atomicity and isolation for a single object (row, document).

**Implementation:**
- Write-Ahead Log (WAL): Ensures atomicity
- Locking: Ensures isolation

**Pros:**
- Simple to implement
- Fast (no coordination overhead)
- Most databases provide this by default

**Cons:**
- Can't maintain consistency across multiple objects
- Foreign key constraints can be violated
- Secondary indexes can become stale

**Example:**
```
Writing a 20 KB JSON document:
  • Atomicity: If power goes out after 10 KB, the database uses WAL
    to detect and roll back the partial write
  • Isolation: No other transaction can read the half-written document
    (using a lock on the object)
```

---

### Multi-Object Transactions

**Definition:**
Atomicity and isolation for multiple objects. All writes succeed or all fail.

**Why Needed:**
1. **Foreign key references:** Inserting a row that references another table means both tables need to be updated together
2. **Document databases:** Updating a denormalized document might require updating several documents
3. **Secondary indexes:** When you update a value, the secondary index needs to be updated too

**Implementation:**
- Two-Phase Commit (2PC): Coordinates across multiple objects
- Locking: Locks all objects involved
- MVCC: Multiple versions for isolation

**Pros:**
- Maintains consistency across multiple objects
- Foreign key constraints are enforced
- Secondary indexes stay in sync
- Application can safely retry on failure

**Cons:**
- More complex to implement
- Slower (coordination overhead)
- Risk of deadlocks
- Reduced concurrency (more locking)

**Example:**
```
Creating a user and profile:
  Transaction:
    1. Insert user in 'users' table
    2. Insert profile in 'profiles' table
    3. Commit

  If crash between steps 1 and 2:
    • Without multi-object txn: User exists but no profile (inconsistent)
    • With multi-object txn: Both rolled back (consistent)
```

---

## Error Handling and Retries

**Challenge:**
Retrying is not as simple as it looks. Three issues:

### 1. Idempotency

**Problem:**
If the transaction actually succeeded, but the network failed while sending the acknowledgment back to the client, the client may retry and execute it twice.

**Example:**
```
Transaction: Send email to user
  1. Database processes: Email sent
  2. Network fails: Client doesn't receive confirmation
  3. Client retries: Email sent AGAIN (duplicate!)
```

**Solution:**
Make operations idempotent. Retrying should have the same effect as executing once.

### 2. Exponential Backoff

**Problem:**
If the error is due to overload, retrying immediately makes the problem worse (more load).

**Solution:**
Use exponential backoff:
```
Attempt 1: Fail immediately
Attempt 2: Wait 100ms, retry
Attempt 3: Wait 200ms, retry
Attempt 4: Wait 400ms, retry
...
```

### 3. Transient vs. Permanent Errors

**Problem:**
Only some errors are worth retrying. Retrying on a permanent error is pointless.

**Transient Errors (Retry-able):**
- Deadlock
- Temporary network timeout
- Temporary overload

**Permanent Errors (Don't Retry):**
- Constraint violation (e.g., duplicate key)
- Invalid data
- Permission denied

---

## ACID Trade-Offs

### Full ACID is Expensive

Implementing full ACID compliance has significant costs:
- **Logging overhead:** Atomicity & durability require disk writes
- **Locking overhead:** Isolation requires locks (contention, deadlocks)
- **Constraint checking:** Consistency requires validation
- **Coordination overhead:** Multi-object transactions need coordination

### Many Systems Relax ACID for Performance

**NoSQL Databases:**
- Weaker consistency (eventual consistency)
- No multi-object transactions
- Better performance and scalability

**Weak Isolation Levels:**
- Read Committed: Faster than Serializability
- Snapshot Isolation: Good balance of consistency and performance
- Serializability: Strongest but slowest

**Asynchronous Replication:**
- Durability trade-off: Data may be lost if all replicas fail
- Better performance: Don't wait for replication

### Choose Based on Your Workload

**Need Full ACID:**
- Financial systems (banking, payments)
- Accounting systems
- Any system where data loss is unacceptable

**Can Tolerate Eventual Consistency:**
- Social media (likes, comments)
- Analytics
- Caching layers

**Can Tolerate Stale Data:**
- Recommendations
- Analytics
- Reporting

---

## Real-World Examples

### PostgreSQL (Full ACID)
- Default isolation level: Read Committed
- Supports Serializable isolation
- Write-Ahead Log for durability
- Multi-object transactions with 2PC

### MongoDB (Relaxed ACID)
- Single-document ACID transactions (always)
- Multi-document transactions (since 4.0)
- Default: Eventual consistency
- Can enable stronger consistency

### Cassandra (Eventual Consistency)
- No multi-object transactions
- Single-row atomicity only
- Eventual consistency
- High availability and performance

### DynamoDB (Eventual Consistency)
- Single-item ACID transactions
- Multi-item transactions (limited)
- Eventual consistency by default
- Strong consistency available (slower)

---

## Key Insights from DDIA

1. **ACID is not all-or-nothing:** Different databases implement ACID differently
2. **Consistency is the application's job:** The database can't know your business logic
3. **Isolation is expensive:** Full serializability has a performance cost
4. **Durability is probabilistic:** Perfect durability doesn't exist
5. **Trade-offs matter:** Choose based on your workload, not blindly trusting ACID

---

## Exercises

### Exercise 1: ACID Properties (`01_acid_properties.py`)
- Demonstrate atomicity with and without crashes
- Show consistency maintaining invariants
- Demonstrate isolation preventing dirty reads
- Show durability recovering from crashes
- Compare ACID properties and trade-offs

### Exercise 2: Single vs. Multi-Object (`02_single_vs_multi_object.py`)
- Single-object writes with basic atomicity
- Multi-object transactions for foreign keys
- Multi-object transactions for secondary indexes
- Error handling and retries
- Compare single-object and multi-object transactions

---

## Interview Questions

1. **What is atomicity in ACID?**
   - All-or-nothing: Either ALL writes are applied, or NONE are
   - Implemented via Write-Ahead Log (WAL)
   - Allows safe retry on failure

2. **Why is consistency the application's responsibility?**
   - Database can't know your business logic
   - Database can enforce constraints (FK, unique, etc.)
   - Application must ensure invariants are maintained

3. **What is the difference between isolation and consistency?**
   - Isolation: Concurrent transactions don't interfere
   - Consistency: Invariants are maintained
   - Both are needed for data integrity

4. **Why is full serializability expensive?**
   - Requires locking all data involved
   - Reduces concurrency (transactions must wait)
   - Increases risk of deadlocks

5. **What is the difference between single-object and multi-object transactions?**
   - Single-object: Fast but limited consistency
   - Multi-object: Slower but maintains consistency across objects

6. **When should you retry a failed transaction?**
   - Transient errors: Yes (deadlock, network timeout)
   - Permanent errors: No (constraint violation, invalid data)
   - Use exponential backoff to avoid overload

7. **What is the Write-Ahead Log (WAL)?**
   - Logs all writes to disk BEFORE applying to database
   - Enables recovery from crashes
   - Ensures atomicity and durability

8. **Can you have perfect durability?**
   - No: If all disks in all datacenters are destroyed, data is lost
   - Durability is about reducing risk, not eliminating it
   - Trade-off: More replication = more durability but more cost

---

## Summary

**ACID transactions** provide four safety guarantees:

1. **Atomicity:** All-or-nothing writes (no partial updates)
2. **Consistency:** Application invariants are maintained
3. **Isolation:** Concurrent transactions don't interfere
4. **Durability:** Committed data survives crashes

**Key Trade-offs:**
- Full ACID is expensive (logging, locking, coordination)
- Many systems relax ACID for performance
- Choose based on your workload, not blindly trusting ACID

**Single vs. Multi-Object:**
- Single-object: Fast but limited consistency
- Multi-object: Slower but maintains consistency across objects

**Error Handling:**
- Idempotency: Avoid executing twice
- Exponential backoff: Don't overload the system
- Transient vs. permanent: Only retry transient errors

**Key Insight:** ACID is not all-or-nothing. Different databases implement ACID differently. Understand the trade-offs and choose what's right for your workload.
