================================================================================
  PostgreSQL Lost Updates - DDIA Chapter 7.3
  Learn by doing: Understanding and Preventing Lost Updates
================================================================================

COVERS:
  - Lost update anomaly
  - Read-modify-write cycle
  - SELECT FOR UPDATE to prevent lost updates
  - Optimistic vs pessimistic locking

================================================================================
STEP 1: CONNECT
================================================================================

  psql -U postgres -d postgres
  CREATE DATABASE lost_update_demo;
  \c lost_update_demo

================================================================================
STEP 2: SETUP
================================================================================

DROP TABLE IF EXISTS counters CASCADE;
DROP TABLE IF EXISTS bank_accounts CASCADE;

CREATE TABLE counters (
    counter_id SERIAL PRIMARY KEY,
    name VARCHAR(50),
    value INTEGER DEFAULT 0
);

CREATE TABLE bank_accounts (
    account_id SERIAL PRIMARY KEY,
    account_name VARCHAR(50),
    balance DECIMAL(10,2) DEFAULT 1000
);

INSERT INTO counters (name, value) VALUES ('page_views', 0), ('clicks', 0);
INSERT INTO bank_accounts (account_name, balance) VALUES ('Alice', 1000), ('Bob', 1000);

================================================================================
STEP 3: DEMONSTRATE LOST UPDATE
================================================================================

-- Lost Update: Two transactions read, modify, write - one overwrites the other

-- Session 1: Read counter
BEGIN;
    SELECT value FROM counters WHERE name = 'page_views';  -- Returns 0

-- Session 2: Read counter (same value)
-- BEGIN;
    SELECT value FROM counters WHERE name = 'page_views';  -- Returns 0

-- Session 1: Increment and write
    UPDATE counters SET value = value + 1 WHERE name = 'page_views';
COMMIT;

-- Session 2: Increment and write (based on stale read!)
    UPDATE counters SET value = value + 1 WHERE name = 'page_views';
-- COMMIT;

-- Expected: value = 2
-- Actual: value = 1 (LOST UPDATE!)

SELECT * FROM counters;

-- KEY: One update was LOST!

================================================================================
STEP 4: WHY IT HAPPENS
================================================================================

-- Read-Modify-Write cycle:
-- 1. READ: SELECT value (0)
-- 2. MODIFY: value = value + 1 (1)
-- 3. WRITE: UPDATE ... SET value = 1

-- If two transactions do this simultaneously:
-- T1: READ (value=0)
-- T2: READ (value=0)  -- Same value!
-- T1: WRITE (value=1)
-- T2: WRITE (value=1)  -- Overwrites T1's update!

-- Result: Lost update!

================================================================================
STEP 5: PREVENT WITH SELECT FOR UPDATE
================================================================================

-- Solution: Lock the row during read

-- Reset counter
UPDATE counters SET value = 0 WHERE name = 'page_views';

-- Session 1: Lock the row
BEGIN;
    SELECT value FROM counters WHERE name = 'page_views' FOR UPDATE;
    -- Row is now LOCKED

-- Session 2: Try to lock same row
-- BEGIN;
--     SELECT value FROM counters WHERE name = 'page_views' FOR UPDATE;
--     -- WAITS until Session 1 commits!

-- Session 1: Update
    UPDATE counters SET value = value + 1 WHERE name = 'page_views';
COMMIT;

-- Session 2: Now can proceed
--     UPDATE counters SET value = value + 1 WHERE name = 'page_views';
-- COMMIT;

SELECT * FROM counters;  -- Now value = 2!

-- KEY: SELECT FOR UPDATE prevents lost updates!

================================================================================
STEP 6: PRACTICAL EXAMPLE - BANK ACCOUNT
================================================================================

-- Bank transfer with proper locking

CREATE OR REPLACE FUNCTION transfer_with_lock(
    from_account INTEGER,
    to_account INTEGER,
    amount DECIMAL
) RETURNS BOOLEAN AS $$
DECLARE
    from_balance DECIMAL;
BEGIN
    -- Lock both accounts in consistent order
    IF from_account < to_account THEN
        PERFORM pg_advisory_lock(from_account);
        PERFORM pg_advisory_lock(to_account);
    ELSE
        PERFORM pg_advisory_lock(to_account);
        PERFORM pg_advisory_lock(from_account);
    END IF;

    -- Check balance
    SELECT balance INTO from_balance
    FROM bank_accounts
    WHERE account_id = from_account
    FOR UPDATE;

    IF from_balance < amount THEN
        RAISE EXCEPTION 'Insufficient funds';
    END IF;

    -- Transfer
    UPDATE bank_accounts SET balance = balance - amount WHERE account_id = from_account;
    UPDATE bank_accounts SET balance = balance + amount WHERE account_id = to_account;

    -- Release locks
    IF from_account < to_account THEN
        PERFORM pg_advisory_unlock(from_account);
        PERFORM pg_advisory_unlock(to_account);
    ELSE
        PERFORM pg_advisory_unlock(to_account);
        PERFORM pg_advisory_unlock(from_account);
    END IF;

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Test
SELECT transfer_with_lock(1, 2, 100);
SELECT * FROM bank_accounts;

================================================================================
STEP 7: OPTIMISTIC VS PESSIMISTIC LOCKING
================================================================================

-- Pessimistic locking: Lock before read (what we just did)
-- - SELECT FOR UPDATE
-- - Assumes conflicts are common

-- Optimistic locking: Detect conflicts at commit time
-- - Add version column
-- - Check version hasn't changed

DROP TABLE IF EXISTS optimistic_users CASCADE;

CREATE TABLE optimistic_users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50),
    email VARCHAR(100),
    version INTEGER DEFAULT 1
);

INSERT INTO optimistic_users (username, email) VALUES ('alice', 'alice@test.com');

-- Optimistic update: Check version hasn't changed
CREATE OR REPLACE FUNCTION update_email_optimistic(
    p_user_id INTEGER,
    p_new_email VARCHAR,
    p_expected_version INTEGER
) RETURNS BOOLEAN AS $$
BEGIN
    UPDATE optimistic_users
    SET email = p_new_email, version = version + 1
    WHERE user_id = p_user_id AND version = p_expected_version;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Concurrent modification detected!';
    END IF;

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Test
SELECT update_email_optimistic(1, 'alice@new.com', 1);  -- Success
SELECT update_email_optimistic(1, 'alice@another.com', 1);  -- Fails! Version changed

================================================================================
STEP 8: SUMMARY
================================================================================

✅ LOST UPDATE:
  - Two transactions read same value
  - Both modify independently
  - One overwrites the other's change

✅ SOLUTIONS:
  - SELECT FOR UPDATE (pessimistic)
  - Optimistic locking with version

✅ PESSIMISTIC:
  - Lock before read
  - Blocks other transactions
  - Good for high contention

✅ OPTIMISTIC:
  - Check at commit time
  - No blocking
  - Good for low contention

EOF
