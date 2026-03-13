================================================================================
  PostgreSQL ACID Properties - DDIA Chapter 7.1
  Learn by doing: Understanding ACID Transactions

  COVERS:
  - Atomicity: All-or-nothing transactions
  - Consistency: Invariants maintained
  - Isolation: Concurrent transactions don't interfere
  - Durability: Committed data survives crashes
  - Write-Ahead Log (WAL) implementation
  - Single-object vs multi-object operations
================================================================================

WHAT YOU'LL LEARN:
  ✅ Atomicity: All-or-nothing transactions
  ✅ Consistency: Invariants maintained
  ✅ Isolation: Concurrent transactions don't interfere
  ✅ Durability: Committed data survives crashes

PREREQUISITES:
  - PostgreSQL 10+
  - psql or any PostgreSQL client

================================================================================
CONCEPT: ACID TRANSACTIONS
================================================================================

ACID = Atomicity, Consistency, Isolation, Durability

From DDIA (pp. 228-234):
  Transactions group several reads and writes into a logical unit.
  Either the entire transaction succeeds (commit) or it fails (abort/rollback).

================================================================================
STEP 1: CONNECT TO POSTGRESQL
================================================================================

  psql -U postgres -d postgres

================================================================================
STEP 2: SETUP TEST DATABASE
================================================================================

-- Create a test database for ACID demonstrations
DROP DATABASE IF EXISTS acid_demo;
CREATE DATABASE acid_demo;

\c acid_demo

-- Create tables for demonstration
DROP TABLE IF EXISTS accounts CASCADE;
DROP TABLE IF EXISTS transactions_log CASCADE;

-- Account table (for money transfer example)
CREATE TABLE accounts (
    account_id SERIAL PRIMARY KEY,
    account_name VARCHAR(50) NOT NULL,
    balance DECIMAL(10,2) NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Transaction log (to track all operations)
CREATE TABLE transactions_log (
    log_id SERIAL PRIMARY KEY,
    transaction_id VARCHAR(50),
    operation VARCHAR(20),
    account_id INTEGER,
    amount DECIMAL(10,2),
    balance_after DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Insert initial data
INSERT INTO accounts (account_name, balance) VALUES
    ('Alice', 1000.00),
    ('Bob', 1000.00);

================================================================================
STEP 3: DEMONSTRATE ATOMICITY
================================================================================

-- Atomicity: All-or-nothing execution

-- WITHOUT transaction (BAD - can lead to partial execution)
-- Let's see what happens if we don't use transactions

-- First, let's see current state
SELECT * FROM accounts;

-- With transaction (GOOD - atomic)
BEGIN;
    -- Step 1: Debit Alice
    UPDATE accounts SET balance = balance - 100 WHERE account_name = 'Alice';
    -- Step 2: Credit Bob
    UPDATE accounts SET balance = balance + 100 WHERE account_name = 'Bob';
COMMIT;

-- Verify: Both changes applied or neither
SELECT account_name, balance FROM accounts ORDER BY account_name;

-- Demonstrate ROLLBACK (simulating failure)
BEGIN;
    UPDATE accounts SET balance = balance - 500 WHERE account_name = 'Alice';
    -- Oops! Insufficient funds - let's rollback
    ROLLBACK;

-- Verify: No changes made
SELECT account_name, balance FROM accounts ORDER BY account_name;

-- KEY INSIGHT: Either ALL operations succeed or NONE do!

================================================================================
STEP 4: DEMONSTRATE CONSISTENCY
================================================================================

-- Consistency: Invariants are maintained

-- Example invariant: Total balance should always be 2000
-- (1000 + 1000 = 2000)

-- Check current total
SELECT SUM(balance) AS total_balance FROM accounts;

-- Try to violate consistency with a constraint
-- Add a CHECK constraint: balance cannot be negative
ALTER TABLE accounts ADD CONSTRAINT positive_balance CHECK (balance >= 0);

-- Try to withdraw more than balance (should fail)
BEGIN;
    UPDATE accounts SET balance = balance - 2000 WHERE account_name = 'Alice';
COMMIT;

-- This should fail due to constraint!
-- Let's see what happened
SELECT account_name, balance FROM accounts;

-- Another consistency example: Foreign key constraints
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS customers CASCADE;

CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
    amount DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Insert a customer first
INSERT INTO customers (name) VALUES ('John Doe');

-- Now insert an order (must reference existing customer)
INSERT INTO orders (customer_id, amount) VALUES (1, 99.99);

-- Try to insert order with non-existent customer (will fail!)
-- INSERT INTO orders (customer_id, amount) VALUES (999, 50.00);

-- KEY INSIGHT: Database enforces constraints (partial consistency)
-- Full consistency is APPLICATION'S RESPONSIBILITY!

================================================================================
STEP 5: DEMONSTRATE ISOLATION
================================================================================

-- Isolation: Concurrent transactions don't interfere

-- Let's simulate two concurrent transactions

-- Session 1: Start transaction
BEGIN;
    -- Update Alice's balance (lock the row)
    UPDATE accounts SET balance = balance - 50 WHERE account_name = 'Alice';

-- Session 2 (in another terminal): Try to read
-- Let's see what we can see from another session

-- First, let's understand PostgreSQL's default isolation level
SHOW transaction_isolation;

-- In PostgreSQL, default is "read committed"
-- This means:
--   - You see committed data
--   - You don't see uncommitted changes from other sessions

-- Let's demonstrate with a simple example
-- Terminal 1:
BEGIN;
    UPDATE accounts SET balance = balance + 1000 WHERE account_name = 'Bob';

-- Terminal 2 (simulate):
-- SELECT balance FROM accounts WHERE account_name = 'Bob';
-- Would see OLD value (1000), not the uncommitted change

-- Commit the change
COMMIT;

-- Now Terminal 2 would see the new value

-- Demonstrate READ COMMITTED behavior
SELECT account_name, balance FROM accounts;

-- KEY INSIGHT: PostgreSQL's default isolation prevents dirty reads!
-- You can only see committed data from other transactions

================================================================================
STEP 6: DEMONSTRATE DURABILITY
================================================================================

-- Durability: Committed data survives crashes

-- PostgreSQL ensures durability through:
-- 1. Write-Ahead Log (WAL)
-- 2. fsync on commit
-- 3. Replication

-- Let's verify WAL is enabled
SHOW wal_level;

-- Check if synchronous_commit is on (default)
SHOW synchronous_commit;

-- Demonstrate durability settings

-- Create table to test
DROP TABLE IF EXISTS durable_test CASCADE;

CREATE TABLE durable_test (
    id SERIAL PRIMARY KEY,
    data TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Insert with different durability settings

-- Default: synchronous_commit = on (durable)
INSERT INTO durable_test (data) VALUES ('Durable write');

-- Verify the write is persisted
SELECT * FROM durable_test;

-- Simulating crash: If we had async commit and crash, data might be lost
-- With synchronous_commit = on, data is guaranteed to be on disk

-- Checkpoint info
SHOW checkpoint_timeout;
SHOW max_wal_size;

-- KEY INSIGHT: PostgreSQL ensures durability by:
-- 1. Writing to WAL first
-- 2. Syncing to disk on commit
-- 3. Replaying WAL on crash recovery

================================================================================
STEP 7: DEMONSTRATE WRITE-AHEAD LOG (WAL)
================================================================================

-- WAL is the foundation of atomicity and durability

-- Let's see the WAL in action

-- Create a table to track operations
DROP TABLE IF EXISTS wal_demo CASCADE;

CREATE TABLE wal_demo (
    id SERIAL PRIMARY KEY,
    value INTEGER
);

-- Insert some data (this goes to WAL first)
INSERT INTO wal_demo (value) VALUES (1);
INSERT INTO wal_demo (value) VALUES (2);
INSERT INTO wal_demo (value) VALUES (3);

-- The WAL ensures these can be recovered after a crash
SELECT * FROM wal_demo;

-- Checkpoint: When PostgreSQL writes data to main tables
-- We can force a checkpoint
-- SELECT pg_checkpoint();

-- KEY INSIGHT:
-- 1. Every write goes to WAL first
-- 2. On commit, WAL is synced to disk
-- 3. On crash, PostgreSQL replays WAL to recover committed transactions
-- 4. Uncommitted transactions are rolled back

================================================================================
STEP 8: ERROR HANDLING AND RETRIES
================================================================================

-- When transactions fail, we need to handle errors properly

-- Create a table to demonstrate
DROP TABLE IF EXISTS retry_demo CASCADE;

CREATE TABLE retry_demo (
    id SERIAL PRIMARY KEY,
    counter INTEGER DEFAULT 0
);

INSERT INTO retry_demo (counter) VALUES (0);

-- Demonstrate deadlock handling
-- (This is a simplified example)

-- Create two tables for deadlock demo
DROP TABLE IF EXISTS table_a CASCADE;
DROP TABLE IF EXISTS table_b CASCADE;

CREATE TABLE table_a (id SERIAL PRIMARY KEY, value TEXT);
CREATE TABLE table_b (id SERIAL PRIMARY KEY, value TEXT);

INSERT INTO table_a (value) VALUES ('initial_a');
INSERT INTO table_b (value) VALUES ('initial_b');

-- In practice, PostgreSQL detects deadlocks and rolls back one transaction
-- The application should retry

-- Example of handling errors in application code:
-- BEGIN;
--     UPDATE table_a SET value = 'updated' WHERE id = 1;
--     -- If deadlock occurs, retry the transaction
-- COMMIT;

-- KEY INSIGHT:
-- - Transient errors (deadlock, timeout): Retry
-- - Permanent errors (constraint violation): Don't retry
-- - Use exponential backoff to avoid overwhelming the system

================================================================================
STEP 9: COMPARE ACID IMPLEMENTATIONS
================================================================================

-- Different databases implement ACID differently

-- Let's create a comparison

-- PostgreSQL: Full ACID by default
-- - Atomicity: WAL
-- - Consistency: Constraints, triggers
-- - Isolation: MVCC (Read Committed default)
-- - Durability: Synchronous commit, replication

-- Let's check PostgreSQL's settings
SELECT name, setting, unit, description
FROM pg_settings
WHERE name IN ('wal_level', 'synchronous_commit', 'max_wal_senders');

-- Create a summary table
DROP TABLE IF EXISTS acid_implementation CASCADE;

CREATE TABLE acid_implementation (
    property VARCHAR(20) PRIMARY KEY,
    description TEXT,
    postgres_implementation TEXT
);

INSERT INTO acid_implementation (property, description, postgres_implementation) VALUES
    ('Atomicity', 'All-or-nothing', 'Write-Ahead Log (WAL)'),
    ('Consistency', 'Invariants maintained', 'Constraints, Triggers'),
    ('Isolation', 'No interference', 'MVCC, Locking'),
    ('Durability', 'Survives crashes', 'WAL + fsync + replication');

SELECT * FROM acid_implementation;

================================================================================
STEP 10: PRACTICAL EXAMPLE - MONEY TRANSFER
================================================================================

-- Let's create a robust money transfer function

DROP FUNCTION IF EXISTS transfer_money(INTEGER, INTEGER, DECIMAL);

CREATE OR REPLACE FUNCTION transfer_money(
    from_account INTEGER,
    to_account INTEGER,
    amount DECIMAL
) RETURNS BOOLEAN AS $$
DECLARE
    from_balance DECIMAL;
    success BOOLEAN := FALSE;
BEGIN
    -- Check amount is positive
    IF amount <= 0 THEN
        RAISE EXCEPTION 'Transfer amount must be positive';
    END IF;

    -- Get current balance (with lock)
    SELECT balance INTO from_balance
    FROM accounts
    WHERE account_id = from_account
    FOR UPDATE;

    -- Check sufficient funds
    IF from_balance < amount THEN
        RAISE EXCEPTION 'Insufficient funds: has %, needs %', from_balance, amount;
    END IF;

    -- Debit from account
    UPDATE accounts
    SET balance = balance - amount
    WHERE account_id = from_account;

    -- Credit to account
    UPDATE accounts
    SET balance = balance + amount
    WHERE account_id = to_account;

    success := TRUE;
    RETURN success;

EXCEPTION
    WHEN OTHERS THEN
        -- Rollback is automatic
        RAISE;
END;
$$ LANGUAGE plpgsql;

-- Test the transfer function
SELECT * FROM accounts;

-- Successful transfer
SELECT transfer_money(1, 2, 100.00);

SELECT * FROM accounts;

-- Failed transfer (insufficient funds)
-- SELECT transfer_money(1, 2, 10000.00);

-- KEY INSIGHT: The function uses FOR UPDATE to lock rows
-- This prevents race conditions during the transfer

================================================================================
SUMMARY: ACID PROPERTIES
================================================================================

✅ ATOMICITY:
  - All writes succeed or all fail
  - Implemented via Write-Ahead Log (WAL)
  - Use BEGIN/COMMIT/ROLLBACK

✅ CONSISTENCY:
  - Invariants are maintained
  - Database enforces constraints
  - Application enforces business logic

✅ ISOLATION:
  - Concurrent transactions don't interfere
  - PostgreSQL uses MVCC
  - Default: Read Committed

✅ DURABILITY:
  - Committed data survives crashes
  - WAL + fsync ensures durability
  - Replication for extra safety

📌 KEY TRADE-OFFS:
  - Full ACID = More overhead (logging, locking)
  - Many systems relax for performance
  - Choose based on your workload

================================================================================
NEXT STEPS:
================================================================================

1. Try Chapter 7.2: Multi-Object Transactions
   - See how to maintain consistency across multiple tables

2. Try Chapter 7.3: Weak Isolation Levels
   - Understand Read Committed, Snapshot Isolation

3. Read DDIA pp. 228-252 for more theory

EOF
