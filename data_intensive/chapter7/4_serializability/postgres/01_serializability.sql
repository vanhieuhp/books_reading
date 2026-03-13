================================================================================
  PostgreSQL Serializability - DDIA Chapter 7.4
  Learn by doing: True Serial Execution and 2PL
================================================================================

WHAT YOU'LL LEARN:
  ✅ Actual serial execution
  ✅ Two-Phase Locking (2PL)
  ✅ Serializable Snapshot Isolation (SSI)
  ✅ Serializable isolation level in PostgreSQL

PREREQUISITES:
  - PostgreSQL 10+
  - psql or any PostgreSQL client
  - Understanding of isolation levels (Chapter 7.3)

================================================================================
CONCEPT: SERIALIZABILITY
================================================================================

From DDIA (pp. 280-300):

Serializability: The guarantee that the result of concurrent transactions
is the same as if they had run one after another (in some order).

This is the STRONGEST isolation level - prevents ALL anomalies!

================================================================================
STEP 1: CONNECT TO POSTGRESQL
================================================================================

  psql -U postgres -d postgres

================================================================================
STEP 2: SETUP TEST DATABASE
================================================================================

  CREATE DATABASE serializability_demo;
  \c serializability_demo

================================================================================
STEP 3: UNDERSTAND SERIALIZABLE ISOLATION
================================================================================

-- Set to SERIALIZABLE
SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;

-- Check current level
SHOW transaction_isolation;

-- In SERIALIZABLE, PostgreSQL uses Serializable Snapshot Isolation (SSI)
-- This detects potential serialization conflicts and may require retry

================================================================================
STEP 4: DEMONSTRATE SERIALIZABLE PREVENTING ANOMALIES
================================================================================

DROP TABLE IF EXISTS accounts CASCADE;

CREATE TABLE accounts (
    account_id SERIAL PRIMARY KEY,
    name VARCHAR(50),
    balance DECIMAL(10,2) DEFAULT 1000
);

INSERT INTO accounts (name, balance) VALUES
    ('Alice', 1000),
    ('Bob', 1000);

-- Demonstrate: Two transactions trying to transfer money

-- Session 1: SERIALIZABLE
BEGIN;
    SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;

    -- Read initial state
    SELECT * FROM accounts;

-- Session 2: Also SERIALIZABLE
-- BEGIN;
--     SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
--     SELECT * FROM accounts;

-- Session 1: Transfer
    UPDATE accounts SET balance = balance - 100 WHERE name = 'Alice';
    UPDATE accounts SET balance = balance + 100 WHERE name = 'Bob';
COMMIT;

-- Session 2: Transfer
--     UPDATE accounts SET balance = balance - 100 WHERE name = 'Bob';
--     UPDATE accounts SET balance = balance + 100 WHERE name = 'Alice';
-- COMMIT;

-- With SERIALIZABLE, one will FAIL with serialization failure!
-- Must retry

-- Check final state
SELECT * FROM accounts;

-- KEY INSIGHT: SERIALIZABLE ensures correct result!
-- But may require retry

================================================================================
STEP 5: DEMONSTRATE SSI (SERIALIZABLE SNAPSHOT ISOLATION)
================================================================================

-- PostgreSQL uses SSI (Serializable Snapshot Isolation)
-- It detects serialization conflicts and forces retry

-- Let's demonstrate with a conflict

DROP TABLE IF EXISTS inventory CASCADE;

CREATE TABLE inventory (
    item_id SERIAL PRIMARY KEY,
    item_name VARCHAR(50),
    quantity INTEGER DEFAULT 10,
    price DECIMAL(10,2)
);

INSERT INTO inventory (item_name, quantity, price) VALUES
    ('Widget', 10, 9.99),
    ('Gadget', 5, 19.99);

-- Transaction 1: Read and update based on read
BEGIN;
    SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;

    -- Read quantity
    SELECT quantity FROM inventory WHERE item_name = 'Widget';  -- 10

-- Transaction 2: Also read and update
-- BEGIN;
--     SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
--     SELECT quantity FROM inventory WHERE item_name = 'Widget';  -- 10

-- Transaction 1: Update based on its read
    UPDATE inventory SET quantity = quantity - 1 WHERE item_name = 'Widget';
COMMIT;

-- Transaction 2: Try to update - will fail!
--     UPDATE inventory SET quantity = quantity - 1 WHERE item_name = 'Widget';
-- COMMIT;

-- ERROR: could not serialize access due to read/write dependencies

-- Let's check what happened
SELECT * FROM inventory;

-- KEY INSIGHT: SSI detects the conflict and prevents incorrect result!

================================================================================
STEP 6: DEMONSTRATE TWO-PHASE LOCKING (2PL)
================================================================================

-- 2PL: Growing phase + Shrinking phase
-- Growing: Acquire locks
-- Shrinking: Release locks (cannot acquire new locks)

-- PostgreSQL doesn't use classic 2PL, but we can simulate it

DROP TABLE IF EXISTS resources CASCADE;

CREATE TABLE resources (
    resource_id SERIAL PRIMARY KEY,
    name VARCHAR(50),
    value INTEGER DEFAULT 0
);

INSERT INTO resources (name, value) VALUES
    ('Resource A', 0),
    ('Resource B', 0);

-- Simulate 2PL

-- Session 1: Acquire locks (growing phase)
BEGIN;
    SELECT * FROM resources WHERE name = 'Resource A' FOR UPDATE;
    -- Lock acquired on Resource A

-- Session 2: Try to acquire lock on Resource A
-- SELECT * FROM resources WHERE name = 'Resource A' FOR UPDATE;
-- Will wait!

-- Session 1: Acquire more locks
    SELECT * FROM resources WHERE name = 'Resource B' FOR UPDATE;
    -- Now holds locks on both A and B

-- Session 1: Release locks (shrinking phase)
COMMIT;
-- All locks released

-- Session 2: Now can acquire lock
-- SELECT * FROM resources WHERE name = 'Resource A' FOR UPDATE;

-- KEY INSIGHT: 2PL ensures serializability!
-- But can cause deadlocks

================================================================================
STEP 7: DEMONSTRATE DEADLOCKS
================================================================================

-- Deadlock: Two transactions each hold a lock the other needs

DROP TABLE IF EXISTS deadlock_demo CASCADE;

CREATE TABLE deadlock_demo (
    id SERIAL PRIMARY KEY,
    value INTEGER
);

INSERT INTO deadlock_demo (value) VALUES (1), (2);

-- Transaction A: Lock row 1, then row 2
BEGIN;
    SELECT * FROM deadlock_demo WHERE id = 1 FOR UPDATE;
    -- Holds lock on row 1

    -- Transaction B: Lock row 2, then row 1
    -- BEGIN;
    --     SELECT * FROM deadlock_demo WHERE id = 2 FOR UPDATE;
    --     -- Holds lock on row 2

    -- Transaction A: Try to lock row 2
        SELECT * FROM deadlock_demo WHERE id = 2 FOR UPDATE;
        -- WAITS - row 2 is locked by Transaction B

    -- Transaction B: Try to lock row 1
    --     SELECT * FROM deadlock_demo WHERE id = 1 FOR UPDATE;
    --     -- DEADLOCK! Both waiting for each other

COMMIT;
-- COMMIT;
-- PostgreSQL detects deadlock and rolls back one

-- Let's check
SELECT * FROM deadlock_demo;

-- KEY INSIGHT: Deadlocks can occur with locking!
-- PostgreSQL automatically detects and resolves

================================================================================
STEP 8: PREVENTING DEADLOCKS
================================================================================

-- Best practices to prevent deadlocks:

-- 1. Always acquire locks in same order
-- 2. Keep transactions short
-- 3. Use lower isolation levels when possible

-- Let's demonstrate proper locking order

-- Transaction A: Lock in order A, then B
BEGIN;
    SELECT * FROM deadlock_demo WHERE id = 1 FOR UPDATE;
    SELECT * FROM deadlock_demo WHERE id = 2 FOR UPDATE;
COMMIT;

-- Transaction B: Lock in SAME order A, then B
-- BEGIN;
--     SELECT * FROM deadlock_demo WHERE id = 1 FOR UPDATE;
--     SELECT * FROM deadlock_demo WHERE id = 2 FOR UPDATE;
-- COMMIT;

-- No deadlock! Transaction B waits, then proceeds

-- KEY INSIGHT: Lock ordering prevents deadlocks!

================================================================================
STEP 9: ACTUAL SERIAL EXECUTION
================================================================================

-- True serial execution: One transaction at a time
-- Used for maximum consistency

-- PostgreSQL doesn't run truly serially by default
-- But we can simulate it with advisory locks

DROP TABLE IF EXISTS serial_execution CASCADE;

CREATE TABLE serial_execution (
    id SERIAL PRIMARY KEY,
    counter INTEGER DEFAULT 0
);

INSERT INTO serial_execution (counter) VALUES (0);

-- Function to simulate serial execution
CREATE OR REPLACE FUNCTION increment_serial()
RETURNS INTEGER AS $$
DECLARE
    current_value INTEGER;
BEGIN
    -- Acquire advisory lock
    PERFORM pg_advisory_xact_lock(1);

    -- Read current value
    SELECT counter INTO current_value FROM serial_execution WHERE id = 1;

    -- Simulate some work
    current_value := current_value + 1;

    -- Update
    UPDATE serial_execution SET counter = current_value WHERE id = 1;

    -- Lock released automatically at transaction end

    RETURN current_value;
END;
$$ LANGUAGE plpgsql;

-- Test serial execution
SELECT increment_serial();
SELECT increment_serial();
SELECT increment_serial();

SELECT * FROM serial_execution;

-- KEY INSIGHT: Advisory locks provide serial execution!
-- Useful for critical sections

================================================================================
STEP 10: COMPARE SERIALIZABILITY APPROACHES
================================================================================

-- Create comparison table

DROP TABLE IF EXISTS serializability_comparison CASCADE;

CREATE TABLE serializability_comparison (
    approach TEXT PRIMARY KEY,
    description TEXT,
    pros TEXT,
    cons TEXT
);

INSERT INTO serializability_comparison VALUES
    ('Actual Serial Execution', 'One txn at a time', 'Simple, no anomalies', 'No parallelism'),
    ('Two-Phase Locking (2PL)', 'Lock-based', 'Strong guarantee', 'Deadlocks possible'),
    ('Serializable Snapshot Isolation', 'MVCC + conflict detection', 'No locks, good performance', 'May require retry'),
    ('Optimistic Concurrency', 'Check conflicts on commit', 'High throughput', 'May abort');

SELECT * FROM serializability_comparison;

-- Check PostgreSQL's serializable implementation
SELECT name, setting
FROM pg_settings
WHERE name LIKE '%isolation%';

================================================================================
STEP 11: PRACTICAL RECOMMENDATIONS
================================================================================

-- When to use SERIALIZABLE:

-- Use when:
--   - Correctness is critical
--   - Conflicts are rare
--   - Willing to retry on conflicts

-- Don't use when:
--   - High contention
--   - Many concurrent updates
--   - Performance is critical

-- Best practices:
--   1. Keep transactions short
--   2. Design for minimal conflicts
--   3. Implement retry logic in application

-- Example retry logic (in application code):
/*
   while (true) {
       try {
           // Execute transaction
           break;
       } catch (SerializationFailure e) {
           // Retry
           sleep(random());
       }
   }
*/

================================================================================
SUMMARY: SERIALIZABILITY
================================================================================

✅ SERIALIZABLE:
  - Strongest isolation level
  - Prevents ALL anomalies
  - Uses SSI in PostgreSQL

✅ SSI (Serializable Snapshot Isolation):
  - MVCC-based
  - Detects conflicts
  - May require retry

✅ TWO-PHASE LOCKING:
  - Classic approach
  - Locks ensure serializability
  - Deadlock risk

⚠️ TRADE-OFFS:
  - Serializability = less concurrency
  - May require retries (SSI)
  - Deadlocks possible (2PL)

📌 CHOOSE WISELY:
  - Use SERIALIZABLE for correctness-critical operations
  - Use lower levels for better performance

================================================================================
NEXT STEPS:
================================================================================

1. Review all of Chapter 7:
   - ACID properties
   - Multi-object transactions
   - Isolation levels
   - Serializability

2. Compare with real systems:
   - PostgreSQL: SSI
   - MySQL: 2PL
   - Oracle: Serialized with OCI

3. Read DDIA pp. 280-310 for more theory

EOF
