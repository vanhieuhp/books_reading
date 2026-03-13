-- =============================================================================
-- CHAPTER 12: Correctness - SQL Exercises
-- Book: Designing Data-Intensive Applications
-- Section: 3. Correctness: Aiming for Correctness
-- =============================================================================

-- This exercise demonstrates correctness concepts: end-to-end argument,
-- timeliness vs integrity, idempotency, and constraint enforcement.

-- =============================================================================
-- EXERCISE 1: End-to-End Argument
-- =============================================================================

-- The End-to-End Argument states that reliability features at the lower levels
-- are NOT sufficient - the application must also implement end-to-end checks.

-- Let's simulate a scenario: money transfer between accounts
-- (like in Chapter 7, but focusing on end-to-end correctness)

-- Account table with balances
DROP TABLE IF EXISTS accounts CASCADE;
CREATE TABLE accounts (
    account_id SERIAL PRIMARY KEY,
    owner_name VARCHAR(100),
    balance DECIMAL(15,2) DEFAULT 0.00,
    version INTEGER DEFAULT 0  -- For optimistic locking
);

-- Transaction log (to track all operations for auditing)
DROP TABLE IF EXISTS transaction_log CASCADE;
CREATE TABLE transaction_log (
    transaction_id SERIAL PRIMARY KEY,
    transaction_type VARCHAR(20),  -- 'DEPOSIT', 'WITHDRAWAL', 'TRANSFER'
    from_account_id INTEGER,
    to_account_id INTEGER,
    amount DECIMAL(15,2),
    status VARCHAR(20) DEFAULT 'PENDING',  -- PENDING, COMPLETED, FAILED
    request_id VARCHAR(100) UNIQUE,  -- Client-generated unique ID for idempotency
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Insert initial accounts
INSERT INTO accounts (owner_name, balance) VALUES
    ('Alice', 1000.00),
    ('Bob', 500.00),
    ('Charlie', 750.00);

SELECT * FROM accounts;

-- =============================================================================
-- EXERCISE 2: Idempotency - The Key to Exactly-Once Processing
-- =============================================================================

-- Idempotency means an operation can be safely applied multiple times with
-- the same result. This is crucial for exactly-once processing.

-- Let's create an idempotent transfer function
-- The client provides a unique request_id, and we check if it's already processed

CREATE OR REPLACE FUNCTION idempotent_transfer(
    p_from_account_id INTEGER,
    p_to_account_id INTEGER,
    p_amount DECIMAL(15,2),
    p_request_id VARCHAR(100)
) RETURNS VARCHAR(100) AS $$
DECLARE
    v_from_balance DECIMAL(15,2);
    v_to_balance DECIMAL(15,2);
    v_transaction_id INTEGER;
BEGIN
    -- Check if this request was already processed (idempotency check!)
    IF EXISTS (SELECT 1 FROM transaction_log WHERE request_id = p_request_id AND status = 'COMPLETED') THEN
        RETURN 'DUPLICATE_REQUEST: This request has already been processed';
    END IF;

    -- Check if there's a pending request (in case of retry after timeout)
    IF EXISTS (SELECT 1 FROM transaction_log WHERE request_id = p_request_id AND status = 'PENDING') THEN
        RETURN 'REQUEST_IN_PROGRESS: This request is being processed';
    END IF;

    -- Create pending transaction record
    INSERT INTO transaction_log (transaction_type, from_account_id, to_account_id, amount, request_id, status)
    VALUES ('TRANSFER', p_from_account_id, p_to_account_id, p_amount, p_request_id, 'PENDING')
    RETURNING transaction_id INTO v_transaction_id;

    -- Get current balances with row locking (SELECT FOR UPDATE)
    SELECT balance INTO v_from_balance FROM accounts WHERE account_id = p_from_account_id FOR UPDATE;
    SELECT balance INTO v_to_balance FROM accounts WHERE account_id = p_to_account_id FOR UPDATE;

    -- Check sufficient funds
    IF v_from_balance < p_amount THEN
        UPDATE transaction_log SET status = 'FAILED' WHERE transaction_id = v_transaction_id;
        RETURN 'INSUFFICIENT_FUNDS';
    END IF;

    -- Perform the transfer
    UPDATE accounts SET balance = balance - p_amount, version = version + 1 WHERE account_id = p_from_account_id;
    UPDATE accounts SET balance = balance + p_amount, version = version + 1 WHERE account_id = p_to_account_id;

    -- Mark transaction as completed
    UPDATE transaction_log SET status = 'COMPLETED', completed_at = CURRENT_TIMESTAMP WHERE transaction_id = v_transaction_id;

    RETURN 'SUCCESS: Transfer completed';
END;
$$ LANGUAGE plpgsql;

-- Test 1: Normal transfer
SELECT idempotent_transfer(1, 2, 100.00, 'req-001') as result;

-- Check accounts after transfer
SELECT account_id, owner_name, balance FROM accounts WHERE account_id IN (1, 2);

-- Check transaction log
SELECT * FROM transaction_log;

-- Test 2: Try to process the SAME request again (duplicate)
-- This should be rejected due to idempotency!
SELECT idempotent_transfer(1, 2, 100.00, 'req-001') as result;

-- Test 3: Retry with different request ID (simulating client retry with new ID)
-- This SHOULD succeed because it's a new request
SELECT idempotent_transfer(1, 2, 50.00, 'req-002') as result;

-- Show final state
SELECT account_id, owner_name, balance FROM accounts ORDER BY account_id;
SELECT * FROM transaction_log;

-- =============================================================================
-- EXERCISE 3: Timeliness vs Integrity
-- =============================================================================

-- Timeliness: How quickly can you see the latest data?
-- Integrity: Is the data correct?

-- These two properties are often in tension. Let's demonstrate:

-- Scenario: Account balance lookup
-- Option A: Strong consistency (read from primary) - SLOW but CORRECT
-- Option B: Eventual consistency (read from replica/cache) - FAST but potentially STALE

-- Create a "stale" replica for demonstration
DROP TABLE IF EXISTS accounts_replica;
CREATE TABLE accounts_replica AS SELECT * FROM accounts;

-- This represents what a replica might show (out of sync)
-- Let's simulate it being 5 minutes behind
UPDATE accounts_replica SET balance = balance - 50.00 WHERE account_id = 1;  -- Simulate a transfer that happened but isn't reflected yet

-- Query 1: Strong consistency (read from primary)
SELECT 'Strong Consistency (Primary)' as approach, account_id, owner_name, balance
FROM accounts WHERE account_id = 1;

-- Query 2: Eventual consistency (read from replica - might be stale!)
SELECT 'Eventual Consistency (Replica)' as approach, account_id, owner_name, balance
FROM accounts_replica WHERE account_id = 1;

-- The replica shows $50 less - it's stale!
-- But this is ACCEPTABLE for timeliness - the data will eventually be consistent

-- =============================================================================
-- EXERCISE 4: Integrity Constraints Must Be Strong
-- =============================================================================

-- Integrity is more important than timeliness. Let's enforce this.

-- Example: Bank account cannot go negative
-- This is a CRITICAL integrity constraint

ALTER TABLE accounts ADD CONSTRAINT chk_balance_non_negative
CHECK (balance >= 0);

-- Try to withdraw more than balance (should fail!)
DO $$
BEGIN
    -- This should fail due to the check constraint
    UPDATE accounts SET balance = balance - 2000 WHERE account_id = 1;
EXCEPTION
    WHEN check_violation THEN
        RAISE NOTICE 'Constraint prevented negative balance!';
END $$;

-- Verify balance is still correct
SELECT * FROM accounts WHERE account_id = 1;

-- =============================================================================
-- EXERCISE 5: Fencing Tokens - Preventing Zombie Processes
-- =============================================================================

-- Fencing tokens prevent stale operations from "zombie" processes that were
-- thought to be dead but actually completed later (from Chapter 8).

-- Create a table for processing locks with fencing
DROP TABLE IF EXISTS processing_locks CASCADE;
CREATE TABLE processing_locks (
    lock_id SERIAL PRIMARY KEY,
    resource_name VARCHAR(100),
    process_id VARCHAR(100),
    fence_token INTEGER,
    acquired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    completed BOOLEAN DEFAULT FALSE
);

-- Function to acquire lock with fencing
CREATE OR REPLACE FUNCTION acquire_fenced_lock(
    p_resource_name VARCHAR(100),
    p_process_id VARCHAR(100)
) RETURNS INTEGER AS $$
DECLARE
    v_fence_token INTEGER;
    v_existing_token INTEGER;
BEGIN
    -- Get the highest fence token for this resource
    SELECT MAX(fence_token) INTO v_existing_token
    FROM processing_locks
    WHERE resource_name = p_resource_name AND completed = FALSE;

    -- New token is always higher
    v_fence_token := COALESCE(v_existing_token, 0) + 1;

    -- Insert the lock
    INSERT INTO processing_locks (resource_name, process_id, fence_token, expires_at)
    VALUES (p_resource_name, p_process_id, v_fence_token, CURRENT_TIMESTAMP + INTERVAL '10 minutes')
    RETURNING fence_token INTO v_fence_token;

    RETURN v_fence_token;
END;
$$ LANGUAGE plpgsql;

-- Function to execute with fence token validation
CREATE OR REPLACE FUNCTION execute_with_fence(
    p_resource_name VARCHAR(100),
    p_process_id VARCHAR(100),
    p_operation VARCHAR(100)
) RETURNS VARCHAR(100) AS $$
DECLARE
    v_fence_token INTEGER;
    v_current_token INTEGER;
BEGIN
    -- Acquire lock and get fence token
    v_fence_token := acquire_fenced_lock(p_resource_name, p_process_id);

    -- Simulate some processing
    RAISE NOTICE 'Process % executing with fence token % for operation: %',
        p_process_id, v_fence_token, p_operation;

    -- Check that our fence token is still valid
    SELECT MAX(fence_token) INTO v_current_token
    FROM processing_locks
    WHERE resource_name = p_resource_name AND completed = FALSE;

    -- If someone else got a higher token, we're a zombie!
    IF v_fence_token < v_current_token THEN
        RETURN 'ZOMBIE_DETECTED: Stale process, aborting!';
    END IF;

    -- Mark as completed
    UPDATE processing_locks
    SET completed = TRUE
    WHERE fence_token = v_fence_token AND resource_name = p_resource_name;

    RETURN 'SUCCESS: Operation completed with fence token ' || v_fence_token;
END;
$$ LANGUAGE plpgsql;

-- Test fencing
SELECT execute_with_fence('order-123', 'process-1', 'process_order') as result;
SELECT execute_with_fence('order-123', 'process-2', 'process_order') as result;
SELECT execute_with_fence('order-123', 'process-1', 'process_order') as result;

SELECT * FROM processing_locks;

-- =============================================================================
-- EXERCISE 6: Uniqueness Constraints in Distributed Systems
-- =============================================================================

-- Enforcing uniqueness across multiple systems requires careful design.

-- Option 1: Single leader (all uniqueness checks go through one database)
DROP TABLE IF EXISTS user_accounts CASCADE;
CREATE TABLE user_accounts (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,  -- Unique constraint
    email VARCHAR(100) UNIQUE NOT NULL,    -- Unique constraint
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- This works because PostgreSQL handles the uniqueness

-- Option 2: Distributed uniqueness with coordination
-- (This would require ZooKeeper, etc. - demonstrating the concept)

DROP TABLE IF EXISTS uniqueness_tokens CASCADE;
CREATE TABLE uniqueness_tokens (
    token_id SERIAL PRIMARY KEY,
    token_value VARCHAR(100) UNIQUE NOT NULL,
    service_name VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Simulate acquiring uniqueness from a coordination service
CREATE OR REPLACE FUNCTION acquire_unique_token(
    p_token_value VARCHAR(100),
    p_service_name VARCHAR(50)
) RETURNS BOOLEAN AS $$
BEGIN
    INSERT INTO uniqueness_tokens (token_value, service_name)
    VALUES (p_token_value, p_service_name);
    RETURN TRUE;
EXCEPTION
    WHEN unique_violation THEN
        RETURN FALSE;  -- Token already exists
END;
$$ LANGUAGE plpgsql;

-- Test uniqueness acquisition
SELECT acquire_unique_token('user-alice', 'user-service') as result;
SELECT acquire_unique_token('user-alice', 'user-service') as result;  -- Should fail
SELECT acquire_unique_token('user-bob', 'user-service') as result;    -- Should succeed

-- =============================================================================
-- EXERCISE 7: Eventual Consistency with Conflict Resolution
-- =============================================================================

-- When multiple systems can accept writes, conflicts can occur.
-- Let's demonstrate conflict detection and resolution.

DROP TABLE IF EXISTS inventory CASCADE;
CREATE TABLE inventory (
    item_id SERIAL PRIMARY KEY,
    item_name VARCHAR(100),
    quantity INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source_system VARCHAR(50)  -- 'warehouse-a', 'warehouse-b', etc.
);

-- Regional inventory tables (simulating distributed systems)
DROP TABLE IF EXISTS inventory_west CASCADE;
DROP TABLE IF EXISTS inventory_east CASCADE;

CREATE TABLE inventory_west AS SELECT * FROM inventory WHERE 1=0;
CREATE TABLE inventory_east AS SELECT * FROM inventory WHERE 1=0;

-- Initialize inventory
INSERT INTO inventory (item_name, quantity, source_system) VALUES
    ('Widget A', 100, 'central'),
    ('Widget B', 50, 'central');

-- Simulate regional updates
INSERT INTO inventory_west (item_id, item_name, quantity, source_system)
SELECT item_id, item_name, quantity + 10, 'warehouse-west' FROM inventory;

INSERT INTO inventory_east (item_id, item_name, quantity, source_system)
SELECT item_id, item_name, quantity - 5, 'warehouse-east' FROM inventory;

-- Show conflicts
SELECT 'West' as region, * FROM inventory_west
UNION ALL
SELECT 'East', * FROM inventory_east;

-- Conflict resolution: Last writer wins
CREATE OR REPLACE FUNCTION resolve_inventory_conflicts()
RETURNS void AS $$
BEGIN
    -- Update central inventory with latest regional values
    -- In reality, you'd use vector clocks or version vectors
    -- Here we just take the sum for simplicity

    UPDATE inventory i
    SET quantity = (
        SELECT COALESCE(w.quantity, 0) + COALESCE(e.quantity, 0)
        FROM inventory_west w
        LEFT JOIN inventory_east e ON w.item_id = e.item_id
        WHERE w.item_id = i.item_id
    ),
    last_updated = CURRENT_TIMESTAMP
    FROM inventory_west w
    WHERE i.item_id = w.item_id;
END;
$$ LANGUAGE plpgsql;

SELECT resolve_inventory_conflicts();
SELECT * FROM inventory;

-- =============================================================================
-- PRACTICE EXERCISES FOR YOU:
-- =============================================================================

/*
Exercise A: Implement a "two-phase commit" pattern to ensure atomic updates
            across multiple tables.

Exercise B: Add "compensating transactions" - if a multi-step operation fails
            halfway through, roll back the completed steps.

Exercise C: Implement "read-your-writes" consistency - ensure that after a write,
            subsequent reads see that write.

Exercise D: Create a "conflict-free replicated data type" (CRDT) simulation
            for a counter that can be updated from multiple locations.
*/

-- =============================================================================
-- SUMMARY
-- =============================================================================

/*
KEY TAKEAWAYS from this exercise:

1. END-TO-END ARGUMENT: Lower-level guarantees (transactions, TCP) are NOT
   sufficient. Applications must implement their own correctness checks.

2. IDEMPOTENCY: Use unique request IDs to make operations safe to retry.
   This is essential for exactly-once processing.

3. TIMELINESS vs INTEGRITY: Integrity (correctness) is MORE important than
   timeliness (freshness). Use strong consistency for integrity, eventual
   consistency for timeliness.

4. FENCING TOKENS: Prevent zombie processes from performing stale operations
   by requiring each operation to present an ever-increasing token.

5. UNIQUE CONSTRAINTS: In distributed systems, uniqueness requires coordination
   (single leader, distributed lock, or consensus algorithm).

6. CONFLICT RESOLUTION: When multiple systems can accept writes, conflicts
   are inevitable. Choose a strategy: last-writer-wins, CRDTs, or manual resolution.

These concepts are essential for building reliable distributed systems!
*/
