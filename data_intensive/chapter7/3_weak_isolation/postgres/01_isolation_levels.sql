================================================================================
  PostgreSQL Weak Isolation Levels - DDIA Chapter 7.3
  Learn by doing: Understanding Isolation Levels and Anomalies
================================================================================

WHAT YOU'LL LEARN:
  ✅ Read Committed isolation level
  ✅ Snapshot Isolation (Repeatable Read)
  ✅ Lost Update problem
  ✅ Write Skew problem

PREREQUISITES:
  - PostgreSQL 10+
  - psql or any PostgreSQL client
  - Understanding of ACID (Chapter 7.1)

================================================================================
CONCEPT: ISOLATION LEVELS
================================================================================

From DDIA (pp. 252-280):

Isolation levels define how concurrent transactions see each other's changes.

| Level | Dirty Read | Non-Repeatable Read | Phantom Read |
|-------|-----------|-------------------|--------------|
| Read Uncommitted | ❌ | ❌ | ❌ |
| Read Committed | ✅ | ❌ | ❌ |
| Repeatable Read | ✅ | ✅ | ❌ |
| Serializable | ✅ | ✅ | ✅ |

PostgreSQL supports: Read Committed (default), Repeatable Read, Serializable

================================================================================
STEP 1: CONNECT TO POSTGRESQL
================================================================================

  psql -U postgres -d postgres

================================================================================
STEP 2: SETUP TEST DATABASE
================================================================================

  CREATE DATABASE isolation_demo;
  \c isolation_demo

================================================================================
STEP 3: UNDERSTAND CURRENT ISOLATION LEVEL
================================================================================

-- Check current isolation level
SHOW transaction_isolation;

-- Set isolation level for session
SET TRANSACTION ISOLATION LEVEL READ COMMITTED;
SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;
SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;

-- PostgreSQL default: READ COMMITTED

================================================================================
STEP 4: DEMONSTRATE READ COMMITTED
================================================================================

-- Read Committed: Each query sees committed data from other transactions

DROP TABLE IF EXISTS accounts CASCADE;

CREATE TABLE accounts (
    account_id SERIAL PRIMARY KEY,
    name VARCHAR(50),
    balance DECIMAL(10,2) DEFAULT 1000
);

INSERT INTO accounts (name, balance) VALUES
    ('Alice', 1000),
    ('Bob', 1000);

-- Session 1: Start transaction, update Alice
BEGIN;
    UPDATE accounts SET balance = balance - 100 WHERE name = 'Alice';

-- Session 2: Read Alice's balance (in another terminal)
-- Would see OLD value (1000) because Session 1 hasn't committed

-- Commit Session 1
COMMIT;

-- Now Session 2 would see NEW value (900)

-- Check final state
SELECT * FROM accounts;

-- KEY INSIGHT: Read Committed prevents DIRTY READS
-- You only see committed data

================================================================================
STEP 5: DEMONSTRATE NON-REPEATABLE READ
================================================================================

-- Problem: Same query returns different results within one transaction

-- Session 1: Start transaction
BEGIN;
    SELECT balance FROM accounts WHERE name = 'Alice';  -- Returns 900

-- Session 2: In another session, update Alice
-- UPDATE accounts SET balance = 800 WHERE name = 'Alice';
-- COMMIT;

-- Session 1: Read again
    SELECT balance FROM accounts WHERE name = 'Alice';  -- Returns 800!

-- Different result! This is "Non-Repeatable Read"
COMMIT;

-- With REPEATABLE READ, you would see the SAME value both times

================================================================================
STEP 6: DEMONSTRATE REPEATABLE READ
================================================================================

-- Set session to REPEATABLE READ
SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;

DROP TABLE IF EXISTS inventory CASCADE;

CREATE TABLE inventory (
    item_id SERIAL PRIMARY KEY,
    item_name VARCHAR(50),
    quantity INTEGER DEFAULT 10
);

INSERT INTO inventory (item_name, quantity) VALUES
    ('Widget', 10),
    ('Gadget', 5);

-- Session 1: Start REPEATABLE READ transaction
BEGIN;
    SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;

    SELECT quantity FROM inventory WHERE item_name = 'Widget';  -- Returns 10

-- Session 2: Update the quantity
-- UPDATE inventory SET quantity = 8 WHERE item_name = 'Widget';
-- COMMIT;

-- Session 1: Read again
    SELECT quantity FROM inventory WHERE item_name = 'Widget';
    -- Still returns 10! (snapshot from transaction start)

COMMIT;

-- KEY INSIGHT: REPEATABLE READ provides consistent snapshot
-- But it can still have PHANTOM READS

================================================================================
STEP 7: DEMONSTRATE PHANTOM READ
================================================================================

-- Phantom Read: Query returns different number of rows

DROP TABLE IF EXISTS orders CASCADE;

CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INTEGER,
    status VARCHAR(20) DEFAULT 'pending'
);

INSERT INTO orders (customer_id, status) VALUES
    (1, 'pending'),
    (2, 'pending');

-- Session 1: REPEATABLE READ
BEGIN;
    SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;

    SELECT COUNT(*) FROM orders WHERE status = 'pending';  -- Returns 2

-- Session 2: Insert new order
-- INSERT INTO orders (customer_id, status) VALUES (3, 'pending');
-- COMMIT;

-- Session 1: Count again
    SELECT COUNT(*) FROM orders WHERE status = 'pending';  -- Returns 3!
    -- Different number of rows! (Phantom read)

COMMIT;

-- With SERIALIZABLE, you would get an error!

================================================================================
STEP 8: DEMONSTRATE LOST UPDATE
================================================================================

-- Lost Update: Two transactions read same value, both update, one overwrites other

DROP TABLE IF EXISTS counters CASCADE;

CREATE TABLE counters (
    counter_id SERIAL PRIMARY KEY,
    name VARCHAR(50),
    value INTEGER DEFAULT 0
);

INSERT INTO counters (name, value) VALUES ('page_views', 0);

-- Session 1: Read counter
BEGIN;
    SELECT value FROM counters WHERE name = 'page_views';  -- Returns 0

-- Session 2: Read counter
-- BEGIN;
    SELECT value FROM counters WHERE name = 'page_views';  -- Returns 0

-- Session 1: Increment and write
    UPDATE counters SET value = value + 1 WHERE name = 'page_views';
COMMIT;

-- Session 2: Increment and write
    UPDATE counters SET value = value + 1 WHERE name = 'page_views';
-- COMMIT;

-- Expected: 2, Actual: 1 (Lost update!)

SELECT * FROM counters;

-- SOLUTION: Use SELECT FOR UPDATE to lock the row

================================================================================
STEP 9: SOLVING LOST UPDATE WITH FOR UPDATE
================================================================================

-- Reset counter
UPDATE counters SET value = 0 WHERE name = 'page_views';

-- Session 1: Lock the row
BEGIN;
    SELECT value FROM counters WHERE name = 'page_views' FOR UPDATE;
    -- Row is now locked

-- Session 2: Try to read same row
-- SELECT value FROM counters WHERE name = 'page_views' FOR UPDATE;
-- Will WAIT until Session 1 commits

-- Session 1: Update
    UPDATE counters SET value = value + 1 WHERE name = 'page_views';
COMMIT;

-- Session 2: Now can proceed
    SELECT value FROM counters WHERE name = 'page_views' FOR UPDATE;
    UPDATE counters SET value = value + 1 WHERE name = 'page_views';
COMMIT;

-- Now value is 2!
SELECT * FROM counters;

-- KEY INSIGHT: SELECT FOR UPDATE prevents lost updates!

================================================================================
STEP 10: DEMONSTRATE WRITE SKEW
================================================================================

-- Write Skew: Two transactions read overlapping data, both write different things

DROP TABLE IF EXISTS doctors CASCADE;

CREATE TABLE doctors (
    doctor_id SERIAL PRIMARY KEY,
    name VARCHAR(50),
    on_call BOOLEAN DEFAULT TRUE
);

INSERT INTO doctors (name, on_call) VALUES
    ('Dr. Alice', TRUE),
    ('Dr. Bob', TRUE);

-- Rule: At least one doctor must be on call

-- Session 1: Alice checks if Bob is on call
BEGIN;
    SELECT COUNT(*) FROM doctors WHERE on_call = TRUE;  -- Returns 2
    SELECT on_call FROM doctors WHERE name = 'Dr. Alice';  -- TRUE

-- Session 2: Bob checks if Alice is on call
-- BEGIN;
    SELECT COUNT(*) FROM doctors WHERE on_call = TRUE;  -- Returns 2
    SELECT on_call FROM doctors WHERE name = 'Dr. Bob';  -- TRUE

-- Session 1: Alice goes off call
    UPDATE doctors SET on_call = FALSE WHERE name = 'Dr. Alice';
COMMIT;

-- Session 2: Bob goes off call
    UPDATE doctors SET on_call = FALSE WHERE name = 'Dr. Bob';
-- COMMIT;

-- Result: No doctor on call! (Violation of business rule)

SELECT * FROM doctors;

-- KEY INSIGHT: Write skew is harder to prevent!
-- Need SERIALIZABLE or explicit locking

================================================================================
STEP 11: COMPARE ISOLATION LEVELS
================================================================================

-- Create comparison table

DROP TABLE IF EXISTS isolation_comparison CASCADE;

CREATE TABLE isolation_comparison (
    level VARCHAR(20),
    dirty_reads BOOLEAN,
    non_repeatable_reads BOOLEAN,
    phantom_reads BOOLEAN,
    description TEXT
);

INSERT INTO isolation_comparison VALUES
    ('Read Uncommitted', '❌ Possible', '❌ Possible', '❌ Possible', 'Can see uncommitted data'),
    ('Read Committed', '✅ Prevented', '❌ Possible', '❌ Possible', 'Only see committed data'),
    ('Repeatable Read', '✅ Prevented', '✅ Prevented', '❌ Possible', 'Consistent snapshot'),
    ('Serializable', '✅ Prevented', '✅ Prevented', '✅ Prevented', 'Full isolation');

SELECT * FROM isolation_comparison;

-- Check PostgreSQL's actual implementation
SELECT name, setting
FROM pg_settings
WHERE name = 'default_transaction_isolation';

================================================================================
STEP 12: PRACTICAL RECOMMENDATIONS
================================================================================

-- When to use each level:

-- READ COMMITTED (Default):
--   - Most applications
--   - Good balance of performance and safety
--   - PostgreSQL default

-- REPEATABLE READ:
--   - When you need consistent reads within transaction
--   - Financial calculations
--   - Reports that must be consistent

-- SERIALIZABLE:
--   - When correctness is critical
--   - Willing to accept lower performance
--   - Use carefully (may cause serialization failures)

-- Show current setting
SELECT current_setting('transaction_isolation');

-- Set for a transaction
BEGIN;
    SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
    -- Your operations here
COMMIT;

================================================================================
SUMMARY: ISOLATION LEVELS
================================================================================

✅ READ COMMITTED:
  - Default in PostgreSQL
  - Prevents dirty reads
  - Non-repeatable reads possible

✅ REPEATABLE READ:
  - Consistent snapshot within transaction
  - Prevents non-repeatable reads
  - Phantom reads possible

✅ SERIALIZABLE:
  - Full isolation
  - Prevents all anomalies
  - May cause serialization failures

⚠️ ANOMALIES:
  - Lost Update: Use SELECT FOR UPDATE
  - Write Skew: Use SERIALIZABLE or explicit locks

📌 TRADE-OFF:
  - Higher isolation = more locking = less concurrency
  - Choose based on correctness requirements

================================================================================
NEXT STEPS:
================================================================================

1. Try Chapter 7.4: Serializability
   - See true serial execution
   - Learn about 2PL and SSI

2. Read DDIA pp. 252-290 for more theory

EOF
