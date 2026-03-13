================================================================================
  PostgreSQL Isolation Levels Comparison - DDIA Chapter 7.4
  Learn by doing: Comparing All Isolation Levels
================================================================================

COVERS:
  - All isolation levels in PostgreSQL
  - Comparison table
  - When to use each level
  - Performance implications

================================================================================
STEP 1: CONNECT
================================================================================

  psql -U postgres -d postgres
  CREATE DATABASE isolation_comparison_demo;
  \c isolation_comparison_demo

================================================================================
STEP 2: SETUP
================================================================================

DROP TABLE IF EXISTS accounts CASCADE;
DROP TABLE IF EXISTS orders CASCADE;

CREATE TABLE accounts (
    account_id SERIAL PRIMARY KEY,
    name VARCHAR(50),
    balance DECIMAL(10,2) DEFAULT 1000
);

CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INTEGER,
    total DECIMAL(10,2),
    status VARCHAR(20) DEFAULT 'pending'
);

INSERT INTO accounts (name, balance) VALUES
    ('Alice', 1000), ('Bob', 1000), ('Charlie', 1000);

================================================================================
STEP 3: ISOLATION LEVELS IN POSTGRESQL
================================================================================

-- PostgreSQL supports 3 isolation levels:

-- 1. Read Committed (default)
-- 2. Repeatable Read
-- 3. Serializable

-- Set isolation level:
SET TRANSACTION ISOLATION LEVEL READ COMMITTED;
SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;
SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;

-- Or per-transaction:
BEGIN;
    SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
    -- operations
COMMIT;

================================================================================
STEP 4: COMPARISON TABLE
================================================================================

-- Create comparison table
DROP TABLE IF EXISTS isolation_levels CASCADE;

CREATE TABLE isolation_levels (
    level TEXT,
    dirty_reads TEXT,
    nonrepeatable_reads TEXT,
    phantom_reads TEXT,
    description TEXT
);

INSERT INTO isolation_levels VALUES
    ('Read Committed',
     'Prevented ✓',
     'Possible ✗',
     'Possible ✗',
     'Default. Each statement sees committed data'),

    ('Repeatable Read',
     'Prevented ✓',
     'Prevented ✓',
     'Possible ✗',
     'Transaction sees snapshot from start'),

    ('Serializable',
     'Prevented ✓',
     'Prevented ✓',
     'Prevented ✓',
     'Full isolation. May require retry');

-- View comparison
SELECT * FROM isolation_levels;

================================================================================
STEP 5: DEMONSTRATE DIFFERENCES
================================================================================

-- Read Committed (default):
-- - Each statement sees committed data
-- - Non-repeatable reads possible

SET TRANSACTION ISOLATION LEVEL READ COMMITTED;
BEGIN;
    SELECT balance FROM accounts WHERE name = 'Alice';  -- 1000
    -- If another transaction updates Alice, next read sees new value
COMMIT;

-- Repeatable Read:
-- - Same query returns same results
-- - Phantom reads possible

SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;
BEGIN;
    SELECT balance FROM accounts WHERE name = 'Alice';  -- 1000
    -- Even if another transaction updates, still sees 1000
COMMIT;

-- Serializable:
-- - Full isolation
-- - May fail with serialization error

SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
BEGIN;
    SELECT balance FROM accounts WHERE name = 'Alice';
    -- If conflict detected, may need to retry
COMMIT;

================================================================================
STEP 6: PERFORMANCE COMPARISON
================================================================================

-- Performance: Serializability > Isolation > Concurrency

-- More isolation = More locking = Less concurrency = Slower

-- Benchmark example:
/*
  Isolation Level | Throughput | Latency
  ----------------|------------|---------
  Read Committed  | 100% (baseline) | Lowest
  Repeatable Read | ~80% | Medium
  Serializable    | ~50% | Highest
*/

-- View current locks
-- SELECT * FROM pg_locks;

-- Check isolation level
SELECT current_setting('transaction_isolation') AS current_level;

================================================================================
STEP 7: WHEN TO USE EACH LEVEL
================================================================================

-- Read Committed (default):
-- ✓ Most applications
-- ✓ Good performance
-- ✓ Most operations
-- ✗ Not for critical calculations

-- Repeatable Read:
-- ✓ Financial reports
-- ✓ Consistent reads within transaction
-- ✓ Balance calculations
-- ✗ Higher locking overhead

-- Serializable:
-- ✓ Critical business rules
-- ✓ Financial transactions
-- ✓ When correctness > performance
-- ✗ May require retries
-- ✗ Higher failure rate

================================================================================
STEP 8: REAL-WORLD DECISION GUIDE
================================================================================

-- Decision tree:

-- 1. Can you tolerate non-repeatable reads?
--    Yes → Read Committed (default)

-- 2. Can you tolerate phantom reads?
--    No → Serializable

-- 3. Must you prevent write skew?
--    Yes → Serializable

-- 4. Do you need consistent reads?
--    Yes → Repeatable Read

-- Example applications:
-- Read Committed: Web apps, analytics, logging
-- Repeatable Read: Reports, audits, calculations
-- Serializable: Financial transactions, inventory

================================================================================
STEP 9: SUMMARY
================================================================================

✅ READ COMMITTED:
  - Default in PostgreSQL
  - Good performance
  - Most common choice

✅ REPEATABLE READ:
  - Consistent snapshot
  - Good for reports
  - May have phantoms

✅ SERIALIZABLE:
  - Full isolation
  - May require retry
  - For critical operations

📌 TRADE-OFF:
  Isolation ↑ = Concurrency ↓ = Performance ↓

📌 RECOMMENDATION:
  Start with Read Committed, upgrade only when needed

EOF
