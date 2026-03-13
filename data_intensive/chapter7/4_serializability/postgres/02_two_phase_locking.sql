================================================================================
  PostgreSQL Two-Phase Locking - DDIA Chapter 7.4
  Learn by doing: Understanding 2PL
================================================================================

COVERS:
  - Two-Phase Locking (2PL) concept
  - Growing phase vs shrinking phase
  - Deadlock detection
  - Strict 2PL

================================================================================
STEP 1: CONNECT
================================================================================

  psql -U postgres -d postgres
  CREATE DATABASE two_phase_locking_demo;
  \c two_phase_locking_demo

================================================================================
STEP 2: SETUP
================================================================================

DROP TABLE IF EXISTS resources CASCADE;
DROP TABLE IF EXISTS accounts CASCADE;

CREATE TABLE resources (
    resource_id SERIAL PRIMARY KEY,
    name VARCHAR(50),
    value INTEGER DEFAULT 0
);

CREATE TABLE accounts (
    account_id SERIAL PRIMARY KEY,
    name VARCHAR(50),
    balance DECIMAL(10,2) DEFAULT 1000
);

INSERT INTO resources (name, value) VALUES
    ('Resource A', 0),
    ('Resource B', 0),
    ('Resource C', 0);

INSERT INTO accounts (name, balance) VALUES
    ('Alice', 1000),
    ('Bob', 1000);

================================================================================
STEP 3: TWO-PHASE LOCKING EXPLAINED
================================================================================

-- Two-Phase Locking (2PL):
-- Phase 1: Growing - Acquire locks, no locks released
-- Phase 2: Shrinking - Release locks, no new locks acquired

-- Classic 2PL:
-- Growing: Acquire all needed locks
-- Shrinking: Release all locks

-- PostgreSQL uses strict 2PL:
-- Locks held until transaction end

-- FOR UPDATE acquires exclusive lock
-- FOR SHARE acquires shared lock

================================================================================
STEP 4: DEMONSTRATE 2PL
================================================================================

-- Session 1: Acquire lock on Resource A
BEGIN;
    SELECT * FROM resources WHERE name = 'Resource A' FOR UPDATE;
    -- Lock acquired on Resource A (growing phase)

-- Session 2: Try to acquire lock on Resource A
-- BEGIN;
--     SELECT * FROM resources WHERE name = 'Resource A' FOR UPDATE;
--     -- WAITS! Session 1 holds the lock

-- Session 1: Acquire lock on Resource B
    SELECT * FROM resources WHERE name = 'Resource B' FOR UPDATE;
    -- Now holds locks on A and B (growing phase)

-- Session 1: Commit (releases all locks - shrinking phase)
COMMIT;

-- Session 2: Now can acquire lock
--     SELECT * FROM resources WHERE name = 'Resource A' FOR UPDATE;
-- COMMIT;

-- KEY: 2PL ensures serializable execution!

================================================================================
STEP 5: DEADLOCKS
================================================================================

-- Deadlock: Two transactions each hold a lock the other needs

-- Scenario:
-- T1: Lock A, wants B
-- T2: Lock B, wants A

-- Reset resources
UPDATE resources SET value = 0;

-- Transaction 1: Lock Resource A, then try Resource B
BEGIN;
    SELECT * FROM resources WHERE resource_id = 1 FOR UPDATE;
    -- Holds lock on Resource A

-- Transaction 2: Lock Resource B, then try Resource A
-- BEGIN;
--     SELECT * FROM resources WHERE resource_id = 2 FOR UPDATE;
--     -- Holds lock on Resource B

-- Transaction 1: Try Resource B
--     SELECT * FROM resources WHERE resource_id = 2 FOR UPDATE;
--     -- WAITS - locked by Transaction 2

-- Transaction 2: Try Resource A
--     SELECT * FROM resources WHERE resource_id = 1 FOR UPDATE;
--     -- DEADLOCK! Both waiting for each other

-- COMMIT;
-- COMMIT;
-- PostgreSQL detects and rolls back one!

-- KEY: PostgreSQL automatically detects deadlocks!

================================================================================
STEP 6: PREVENTING DEADLOCKS
================================================================================

-- Best practice: Always acquire locks in same order

-- Transaction 1: Lock A then B
BEGIN;
    SELECT * FROM resources WHERE resource_id = 1 FOR UPDATE;
    SELECT * FROM resources WHERE resource_id = 2 FOR UPDATE;
COMMIT;

-- Transaction 2: Lock A then B (same order!)
-- BEGIN;
--     SELECT * FROM resources WHERE resource_id = 1 FOR UPDATE;
--     SELECT * FROM resources WHERE resource_id = 2 FOR UPDATE;
-- COMMIT;

-- No deadlock! Transaction 2 waits for T1 to release A

-- KEY: Consistent lock ordering prevents deadlocks!

================================================================================
STEP 7: LOCK TYPES
================================================================================

-- Exclusive lock (FOR UPDATE):
-- - Only one transaction can hold
-- - Prevents reads and writes

-- Shared lock (FOR SHARE):
-- - Multiple transactions can hold
-- - Prevents writes, allows reads

-- Example: Read-only transaction with shared lock
BEGIN;
    SELECT * FROM accounts FOR SHARE;
    -- Others can read, but can't update
COMMIT;

-- UPDATE needs exclusive lock
BEGIN;
    SELECT * FROM accounts WHERE account_id = 1 FOR UPDATE;
    -- Others can't read or write this row
COMMIT;

-- View current locks
-- SELECT * FROM pg_locks;

================================================================================
STEP 8: SUMMARY
================================================================================

✅ TWO-PHASE LOCKING:
  - Phase 1: Growing (acquire locks)
  - Phase 2: Shrinking (release locks)
  - Ensures serializability

✅ STRICT 2PL:
  - PostgreSQL uses strict 2PL
  - Locks released at commit/rollback

✅ DEADLOCKS:
  - Can occur with 2PL
  - PostgreSQL detects and resolves
  - Prevention: consistent lock ordering

✅ LOCK TYPES:
  - FOR UPDATE (exclusive)
  - FOR SHARE (shared)

EOF
