# Chapter 7: Transactions

This is a comprehensive summary of **Chapter 7: Transactions** from *Designing Data-Intensive Applications* by Martin Kleppmann.

---

## Why Do We Need Transactions?

Many things can go wrong in a data system:
1. The database software or hardware may fail at any time (including in the middle of a write).
2. The application may crash at any time (including halfway through a series of operations).
3. Network interruptions can cut off the application from the database, or one database node from another.
4. Several clients may write to the database at the same time, overwriting each other's changes.
5. A client may read data that doesn't make sense because it has only been partially updated.
6. Race conditions between clients can cause surprising bugs.

**Transactions** have been the mechanism of choice for simplifying these problems. A transaction is a way for an application to group several reads and writes together into a logical unit. Conceptually, all the reads and writes in a transaction are executed as one operation: either the entire transaction succeeds (**commit**) or it fails (**abort/rollback**). If it fails, the application can safely retry.

With transactions, the application is free to ignore certain potential error scenarios and concurrency issues because the database takes care of them instead. We call these safety guarantees.

---

# 1. The Meaning of ACID

The safety guarantees provided by transactions are often described by the well-known acronym **ACID**: Atomicity, Consistency, Isolation, and Durability.

However, in practice, one database's implementation of ACID does not equal another's. The devil is in the details, especially for "Isolation."

## Atomicity
**Atomicity is NOT about concurrency.** (The word "atomic" is confusing because in multi-threaded programming, "atomic" means "thread-safe." ACID Atomicity has nothing to do with threads.)

Atomicity means: if a transaction makes several changes, and the database crashes after completing only some of those changes, those partial changes must be **rolled back**. The database guarantees: either ALL the writes of a transaction are applied, or NONE of them are.

* **The Key Benefit:** If a transaction is aborted (for any reason — a crash, a network failure, a constraint violation), the application can be sure that nothing was half-written. It can safely retry the entire transaction.
* **Think of it as:** "Abortability." The ability to undo incomplete work on error.

```
Example: Transferring $100 from Account A to Account B.
  Step 1: Debit $100 from Account A.
  --- DATABASE CRASHES HERE ---
  Step 2: Credit $100 to Account B.  (NEVER EXECUTED!)

Without Atomicity: Account A lost $100. Account B never received it. Money vanished.
With Atomicity: The database detects the crash and rolls back Step 1.
                Account A gets its $100 back. The user can retry.
```

## Consistency
Consistency in ACID means that you have certain *invariants* (statements about your data that must always be true), and the transaction guarantees that if the invariants were true before the transaction, they will be true after the transaction has committed.

* **Example Invariant:** "In an accounting system, credits and debits across all accounts must always balance to zero."
* **IMPORTANT:** Consistency is actually the *application's* responsibility, not the database's. The database can enforce constraints (foreign keys, unique constraints), but it cannot know the correctness rules of your specific business logic. Kleppmann argues that the "C" in ACID is a stretch — it's there to make the acronym work.

## Isolation
Isolation means that concurrently executing transactions are isolated from each other: they cannot step on each other's toes.

The classic formal guarantee is **Serializability**: the database guarantees that even though transactions may run concurrently, the result is the same as if they had run one after another, in some serial order.

* **Why this matters:** If Transaction A reads data while Transaction B is modifying it, Transaction A could see halfway-written results, leading to bugs. Isolation prevents this.
* **In practice:** Full serializability has a performance cost, so most databases use weaker isolation levels. This is where the real complexity lies (and where most real-world bugs happen).

## Durability
Durability is the promise that once a transaction has committed successfully, any data it has written will not be forgotten, even if there is a hardware fault or the database crashes.

In practice, this means writing to non-volatile storage (a hard drive or SSD) and/or replicating the data to other nodes.

* **Perfect durability does not exist.** If every disk in every datacenter is destroyed simultaneously, no database can save you. Durability is about reducing risk, not eliminating it.

---

# 2. Single-Object vs. Multi-Object Operations

## Single-Object Writes
Atomicity and isolation should also apply when a single object is being written. Imagine writing a 20 KB JSON document to a database. If the power goes out after only 10 KB have been written:
* **Atomicity** ensures we don't get a corrupted half-document. The database uses a WAL (Write-Ahead Log) to detect and roll back partial writes.
* **Isolation** ensures that no other transaction can read the half-written document. This is typically done using a lock on the object.

Most databases provide single-object guarantees by default. These are NOT transactions in the ACID sense, though. They are just basic safety features.

## Multi-Object Transactions (The Real Deal)
Multi-object transactions are needed when several objects need to be kept in sync:
1. A foreign key reference: inserting a row that references another table means both tables need to be updated together.
2. A document database: Updating a denormalized document might require updating several documents that embed or reference each other.
3. Databases with secondary indexes: When you update a value, the secondary index needs to be updated too. Without transactions, the index might be updated but the value might not (or vice versa), leading to inconsistencies.

### Handling Errors and Retries
A key safety feature of transactions is the ability to **retry** on failure (because Atomicity means the failed transaction left no partial state). However, retrying is not as simple as it looks:
1. If the transaction actually succeeded, but the network failed while sending the acknowledgment back to the client, the client may retry and execute it *twice* (e.g., sending an email twice or charging a credit card twice). You need **idempotency**.
2. If the error is due to overload, retrying makes the problem worse (more load). You need **exponential backoff**.
3. It is only worth retrying on *transient* errors (e.g., deadlock, temporary network issue). Retrying on a *permanent* error (e.g., constraint violation) is pointless.

---

# 3. Weak Isolation Levels

Full serializability is expensive. Most databases therefore offer "weaker" isolation levels that protect against *some* concurrency bugs but not all.

These weak isolation levels are notoriously hard to understand, with subtle bugs that can cause real financial loss. Kleppmann urges you to understand the trade-offs rather than blindly trusting the database.

## Read Committed
The most basic level of transaction isolation. It provides two guarantees:
1. **No Dirty Reads:** When reading from the database, you will only see data that has been committed. You will never see data that is still being written by an in-progress transaction.
2. **No Dirty Writes:** When writing to the database, you will only overwrite data that has been committed. Your write will not interleave with another in-progress transaction's writes.

**Implementation:**
* **Preventing dirty writes:** Use row-level locks. When a transaction wants to modify an object, it must first acquire a lock on that object. It holds the lock until the transaction is committed or aborted. If another transaction wants to write the same object, it must wait.
* **Preventing dirty reads:** For every object that is written, the database remembers both the old committed value and the new uncommitted value set by the transaction holding the write lock. Any other transaction that reads the object is simply given the old value. Only when the write transaction commits does the new value become visible.

```
Transaction A:                         Transaction B:
  BEGIN;                                 BEGIN;
  UPDATE users SET age = 30              -- No dirty read!
  WHERE id = 1;                          SELECT age FROM users WHERE id = 1;
  -- (not committed yet!)                -- Returns old value (e.g., 25), NOT 30.
  COMMIT;
                                         SELECT age FROM users WHERE id = 1;
                                         -- NOW returns 30.
```

**Read Committed is the default in PostgreSQL, Oracle, and SQL Server.**

## Snapshot Isolation and Repeatable Read
Read Committed is useful but has a problem called **Read Skew** (a type of non-repeatable read).

**Read Skew Example (DDIA's Bank Transfer):**
Imagine Alice has $500 in Account 1 and $500 in Account 2 ($1000 total).
A transaction transfers $100 from Account 1 to Account 2.
Alice happens to be viewing her accounts while the transfer is in progress:
1. She reads Account 1 first: $500 (transfer hasn't deducted yet).
2. The transfer commits: Account 1 = $400, Account 2 = $600.
3. She reads Account 2: $600 (transfer has been applied).

Alice sees: $500 + $600 = **$1100**. Wait, where did $100 come from? Is the bank giving her free money? Of course not — she just read from two different points in time! This inconsistency is Read Skew, and it's allowed under Read Committed.

**Solution: Snapshot Isolation.**
Each transaction reads from a *consistent snapshot* of the database. The transaction sees all the data that was committed at the start of the transaction. Even if the data is subsequently changed by another transaction, each transaction sees only the old data from that particular point in time.

**Implementation: Multi-Version Concurrency Control (MVCC).**
Instead of holding only one version of each data item, the database keeps multiple versions:
* When a transaction writes, it creates a new version of the object and tags it with the transaction's unique ID.
* When a transaction reads, it only looks at versions created by transactions that were already committed at the time the reading transaction started.
* Old versions are garbage collected when they are no longer needed by any running transaction.

Each row has metadata:
* `created_by`: Transaction ID that created this version.
* `deleted_by`: Transaction ID that deleted/replaced this version (if any).

**Visibility Rule:**
A transaction with ID=100 can see a row version only if:
* `created_by` was committed **before** transaction 100 started, AND
* `deleted_by` is either NULL or was set by a transaction that had NOT YET committed when transaction 100 started.

```
                    Physical Table
  ┌─────────────────────────────────────────────┐
  │ created_by │ deleted_by │   id │  balance    │
  ├────────────┼────────────┼──────┼─────────────┤
  │ txn_5      │ txn_12     │  1   │  $500       │  ← old version
  │ txn_12     │ NULL       │  1   │  $400       │  ← new version
  │ txn_5      │ txn_12     │  2   │  $500       │  ← old version
  │ txn_12     │ NULL       │  2   │  $600       │  ← new version
  └─────────────────────────────────────────────┘

  Transaction 13 (started BEFORE txn_12 committed):
    → Sees: Account 1 = $500, Account 2 = $500 (old versions) ✅ Consistent!

  Transaction 14 (started AFTER txn_12 committed):
    → Sees: Account 1 = $400, Account 2 = $600 (new versions) ✅ Consistent!
```

**Snapshot Isolation is called "Repeatable Read" in PostgreSQL and MySQL InnoDB.** (Confusingly, the SQL standard's definition of "Repeatable Read" is different from what these databases actually implement, which is Snapshot Isolation.)

---

## Preventing Lost Updates

Read Committed and Snapshot Isolation deal with *reading* problems. But there is also a *write* concurrency problem: the **Lost Update**.

A Lost Update can occur when two transactions perform a **read-modify-write cycle** concurrently, and one overwrites the other's change.

**Classic Lost Update Example:**
```
Transaction A:                         Transaction B:
  counter = read(key);  → gets 42        counter = read(key);  → gets 42
  counter = counter + 1;                 counter = counter + 1;
  write(key, counter);  → writes 43      write(key, counter);  → writes 43

Result: counter = 43. WRONG! Should be 44. One increment was LOST.
```

**Solutions:**

### 1. Atomic Operations (Best)
```sql
UPDATE counters SET value = value + 1 WHERE key = 'foo';
```
This is a single atomic instruction that the database executes internally, preventing any interleaving. This is the best solution when applicable.

### 2. Explicit Locking (SELECT ... FOR UPDATE)
```sql
BEGIN;
SELECT * FROM orders WHERE id = 123 FOR UPDATE; -- Acquires a lock!
-- Application logic: calculate the new state
UPDATE orders SET status = 'shipped' WHERE id = 123;
COMMIT;
```
The `FOR UPDATE` clause tells the database to lock the selected rows. Any other transaction that tries to read those rows `FOR UPDATE` will block until the first transaction commits.

### 3. Automatically Detecting Lost Updates
Some databases (PostgreSQL, Oracle, SQL Server with Snapshot Isolation) can automatically detect when a Lost Update has occurred. If a conflict is detected, one of the transactions is aborted and retried automatically.

### 4. Compare-and-Set (CAS)
Used in databases that don't provide transactions (like many NoSQL databases).
```sql
UPDATE wiki SET content = 'new content'
WHERE id = 1234 AND content = 'old content'; -- Only update if unchanged!
```
If someone else already modified the content, the `WHERE` clause won't match, and the update has no effect. The application can detect this (0 rows updated) and retry.

---

## Write Skew and Phantoms

**Write Skew** is a more subtle and generalized version of the Lost Update. It occurs when two transactions read overlapping data, make decisions based on what they read, and then write to *different* objects. The result violates an application-level invariant.

**DDIA's Classic Example (On-Call Doctors):**
A hospital requires at least one doctor to be on call at all times. Two doctors (Alice and Bob) are both on call. Both click "take myself off call" at the same time.

```
Transaction A (Alice):                  Transaction B (Bob):
  currently_on_call = SELECT COUNT(*)     currently_on_call = SELECT COUNT(*)
  FROM doctors WHERE on_call = TRUE;      FROM doctors WHERE on_call = TRUE;
  → currently_on_call = 2                 → currently_on_call = 2

  if currently_on_call >= 2:              if currently_on_call >= 2:
    UPDATE doctors SET on_call = FALSE      UPDATE doctors SET on_call = FALSE
    WHERE name = 'Alice';                   WHERE name = 'Bob';
  COMMIT;                                 COMMIT;

Result: BOTH are now off call. Nobody is on call! The invariant is BROKEN.
```

**Why this is hard:** Neither Read Committed nor Snapshot Isolation prevents this! Each transaction reads a *valid snapshot*, makes a valid decision based on that snapshot, but the *combination* of both transactions' writes violates the invariant.

### The Phantom Problem
In many cases, Write Skew follows this pattern:
1. A `SELECT` query checks whether some condition is met (e.g., "at least 2 doctors on call").
2. Based on the result, the application decides to write.
3. The write *changes the result of the earlier SELECT* in step 1!

This is called a **Phantom**: a write in one transaction changes the result of a search query in another transaction.

**The key insight:** You can't lock rows that *don't exist yet*. If the condition in Step 1 depends on the *absence* of certain rows, or on a count, there are no specific rows to lock with `SELECT ... FOR UPDATE`.

### Materializing Conflicts
One possible solution: Artificially create objects that you can lock. For example, create a table of time slots for the next 6 months. To book a meeting room, you attempt to lock the specific time-slot row. If another transaction is trying to book the same slot, it will block.

But this approach is ugly. It leaks a concurrency control mechanism into the application data model. True Serializable Isolation is a much cleaner solution.

---

# 4. Serializability

Serializability is the strongest isolation level. It guarantees that even though transactions may execute in parallel, the result is the same as if they had executed one at a time, in some serial order.

All the anomalies we've discussed (dirty reads, dirty writes, read skew, lost updates, write skew, phantoms) are prevented by Serializability.

There are three main techniques for achieving Serializability:

## Technique 1: Actual Serial Execution
The simplest solution: literally execute every transaction one at a time, in a single thread, on a single CPU core.

This sounds crazy-slow, but it works if:
1. Every transaction is very short and fast (microseconds).
2. The active dataset fits in memory (RAM is fast, disk is slow).
3. Write throughput is low enough for a single CPU core.

**How to make it work:**
* **Stored Procedures:** Instead of the application interactively executing statements one at a time (with network round-trips), the application submits the *entire* transaction as a stored procedure (a block of code). The database executes the entire thing in one go, one after another.
* **Partitioned Serial Execution:** If data is partitioned, each partition can have its own single-threaded executor. Transactions that only touch a single partition can run in parallel across partitions. Cross-partition transactions require coordination and are much slower.

* **Used by:** VoltDB, Redis (single-threaded by design), Datomic.

## Technique 2: Two-Phase Locking (2PL)

For ~30 years, Two-Phase Locking was the only widely used algorithm for serializability. It is significantly stronger than regular locking (like `SELECT ... FOR UPDATE`).

**The Rule:**
* If Transaction A has *read* an object and Transaction B wants to *write* to that object, B must wait until A commits or aborts (and vice versa).
* Under 2PL, writers block readers, and readers block writers.

(This is different from Snapshot Isolation, where "readers never block writers, and writers never block readers.")

**Implementation: Shared and Exclusive Locks.**
* To **read** an object, a transaction must acquire a **shared lock**. Multiple transactions can hold a shared lock simultaneously.
* To **write** an object, a transaction must acquire an **exclusive lock**. No other transaction can hold any lock on that object (shared or exclusive).
* If a transaction first reads and then writes, it must **upgrade** its shared lock to an exclusive lock.
* Locks are held until the transaction commits or aborts (the "two-phase" part: acquiring locks in Phase 1, releasing them all at once in Phase 2).

**The Downside: Performance.**
2PL makes the database significantly slower because of all the blocking. Transaction throughput and response times are much worse than with weak isolation levels. Plus, it is prone to **deadlocks** (Transaction A waits for B's lock, and B waits for A's lock → both stuck forever). The database must detect deadlocks and abort one of the transactions.

### Predicate Locks (Solving Phantoms)
To prevent phantoms, 2PL databases use **Predicate Locks**. Instead of locking a specific row, a predicate lock locks all objects that *match a search condition*.

```sql
SELECT * FROM bookings
WHERE room_id = 123
AND start_time > '2024-01-01 12:00'
AND end_time < '2024-01-01 14:00';
```
A predicate lock would apply to *all rows matching that WHERE clause*, including rows that don't exist yet. If another transaction tries to insert, update, or delete a booking for room 123 in that time slot, it must wait.

**Performance Issue:** Checking whether a lock's predicate matches a new write is expensive.

### Index-Range Locks (Practical Predicate Locks)
Most databases with 2PL use a simpler, coarser approximation called **Index-Range Locks** (also called **Next-Key Locking**). Instead of locking the exact set of rows matching a precise predicate, the database locks a bigger range of the index.

For example, instead of locking "room 123 between 12:00 and 14:00," you might lock "room 123 for the entire afternoon" or "all rooms between 12:00 and 14:00." This locks more than strictly necessary, but is much cheaper to check and prevents phantoms.

* **Used by:** MySQL InnoDB's "Repeatable Read" level actually uses Next-Key Locking. This is why InnoDB's Repeatable Read is closer to Serializability than the SQL standard suggests.

## Technique 3: Serializable Snapshot Isolation (SSI)

SSI is the cutting-edge approach. It provides full serializability without the performance cost of 2PL.

**The Core Idea: Optimistic Concurrency Control.**
Instead of blocking (pessimistic), SSI allows transactions to proceed without blocking. When a transaction wants to commit, the database checks whether anything bad happened (whether the transaction's reads are still valid). If so, the transaction is aborted and retried.

SSI is built on top of Snapshot Isolation (MVCC), adding an algorithm to detect serialization conflicts.

**How it detects conflicts:**
1. **Detecting reads of a stale MVCC object version (uncommitted write before the read):** If another transaction made an uncommitted write before our transaction read the same object, and that write later commits, our read may be stale.
2. **Detecting writes that affect prior reads (write after the read):** If another transaction writes to an object that our transaction previously read, the premise on which our transaction's decision was based may no longer be true.

In either case, the database tracks these dependencies and aborts one of the conflicting transactions at commit time.

**Pros:**
* No blocking. Much better performance than 2PL.
* Much more predictable query latency.
* Handles Read-Only transactions beautifully (they never need to be aborted).

**Cons:**
* Higher abort rate when there is high contention on the same data. The database does more work to detect and resolve conflicts.
* Requires application code to be prepared for transaction retries.

* **Used by:** PostgreSQL (since 9.1, when you set `SERIALIZABLE` isolation level), FoundationDB, CockroachDB.

---

# Summary: Isolation Levels Comparison

```
┌─────────────────────────────┬────────────┬────────────┬────────────┬──────────┬──────────┐
│ Isolation Level             │ Dirty Read │ Dirty Write│ Read Skew  │ Lost Upd │ Write    │
│                             │            │            │ (Non-Rep   │          │ Skew /   │
│                             │            │            │  Read)     │          │ Phantom  │
├─────────────────────────────┼────────────┼────────────┼────────────┼──────────┼──────────┤
│ Read Uncommitted            │ Possible   │ Possible   │ Possible   │ Possible │ Possible │
│ Read Committed              │ PREVENTED  │ PREVENTED  │ Possible   │ Possible │ Possible │
│ Snapshot Isolation          │ PREVENTED  │ PREVENTED  │ PREVENTED  │ Possible*│ Possible │
│ (Repeatable Read)           │            │            │            │          │          │
│ Serializable                │ PREVENTED  │ PREVENTED  │ PREVENTED  │PREVENTED │PREVENTED │
└─────────────────────────────┴────────────┴────────────┴────────────┴──────────┴──────────┘

  * Some databases (PostgreSQL, Oracle) auto-detect lost updates under
    Snapshot Isolation. MySQL/InnoDB does NOT.
```

---

# Key Terminology Cheat Sheet

* **Transaction:** A group of reads/writes treated as a single logical unit.
* **ACID:** Atomicity, Consistency, Isolation, Durability.
* **Atomicity:** All-or-nothing. Partial failures are rolled back.
* **Isolation:** Concurrent transactions don't interfere with each other.
* **Dirty Read:** Reading uncommitted data written by another transaction.
* **Dirty Write:** Overwriting uncommitted data written by another transaction.
* **Read Skew:** Seeing data from two different points in time within one transaction.
* **Lost Update:** Two read-modify-write cycles; one overwrites the other's change.
* **Write Skew:** Two transactions read, make independent decisions, and together violate an invariant.
* **Phantom:** A write in one transaction changes the search result of another transaction's query.
* **MVCC:** Multi-Version Concurrency Control. Keep multiple versions of each row.
* **2PL:** Two-Phase Locking. Writers block readers; readers block writers. Strong but slow.
* **SSI:** Serializable Snapshot Isolation. Optimistic: run without blocking, detect conflicts at commit.

---

# Real-World Database Defaults

| Database       | Default Isolation Level | Serializable Available? |
|----------------|------------------------|------------------------|
| PostgreSQL     | Read Committed          | Yes (SSI since v9.1)   |
| MySQL (InnoDB) | Repeatable Read         | Yes (2PL via `SERIALIZABLE`) |
| Oracle         | Read Committed          | Yes (called `SERIALIZABLE`, actually Snapshot Isolation) |
| SQL Server     | Read Committed          | Yes (2PL or Snapshot)  |
| CockroachDB    | Serializable (SSI)      | Yes (default!)         |
| MongoDB        | Read Uncommitted*       | Multi-doc txn since 4.0|

_*MongoDB's default for single-document reads is effectively Read Uncommitted from a multi-document perspective._

---

# Interview-Level Questions

1. **What's the difference between Atomicity and Isolation?**
   → Atomicity = all-or-nothing on failure. Isolation = protection from concurrency.

2. **Why don't most databases default to Serializable?**
   → Performance cost. 2PL causes excessive blocking/deadlocks. SSI is newer and better but has higher abort rates under contention.

3. **Draw and explain a Write Skew scenario.**
   → Two transactions read overlapping data, make independent decisions, write to different objects, and together violate a business rule (e.g., the on-call doctor example).

4. **How does MVCC work?**
   → The database keeps multiple timestamped versions of each row. Each transaction sees a consistent snapshot from its start time. Old versions are garbage collected.

5. **What is the Phantom problem, and how do you solve it?**
   → A Phantom is when Transaction B's write changes the result of Transaction A's earlier query. Solved by predicate locks (2PL) or conflict detection (SSI).

6. **Compare 2PL vs SSI.**
   → 2PL is pessimistic (lock and block), SSI is optimistic (execute freely, check at commit). 2PL has guaranteed throughput but high latency. SSI has better latency but may abort more transactions under contention.
