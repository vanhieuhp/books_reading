================================================================================
  PostgreSQL Serializable Snapshot Isolation - DDIA Chapter 7.4
  Learn by doing: SSI Implementation
================================================================================

COVERS:
  - SSI (Serializable Snapshot Isolation) concept
  - How PostgreSQL implements serializability
  - Conflict detection
  - Handling serialization failures

================================================================================
STEP 1: CONNECT
================================================================================

  psql -U postgres -d postgres
  CREATE DATABASE ssi_demo;
  \c ssi_demo

================================================================================
STEP 2: SETUP
================================================================================

DROP TABLE IF EXISTS accounts CASCADE;
DROP TABLE IF EXISTS inventory CASCADE;

CREATE TABLE accounts (
    account_id SERIAL PRIMARY KEY,
    name VARCHAR(50),
    balance DECIMAL(10,2) DEFAULT 1000
);

CREATE TABLE inventory (
    item_id SERIAL PRIMARY KEY,
    name VARCHAR(50),
    quantity INTEGER DEFAULT 10
);

INSERT INTO accounts (name, balance) VALUES
    ('Alice', 1000), ('Bob', 1000);

INSERT INTO inventory (name, quantity) VALUES
    ('Widget', 10), ('Gadget', 5);

================================================================================
STEP 3: SERIALIZABLE ISOLATION
================================================================================

-- Set isolation level to SERIALIZABLE
SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;

-- Verify
SHOW transaction_isolation;

-- In SERIALIZABLE:
-- - PostgreSQL uses SSI (Serializable Snapshot Isolation)
-- - Detects potential serialization conflicts
-- - May require retry

BEGIN;
    -- All reads in this transaction see snapshot from start
    SELECT * FROM accounts;
COMMIT;

================================================================================
STEP 4: SSI CONFLICT DETECTION
================================================================================

-- SSI detects conflicts between concurrent transactions

-- Example: Write-After-Read conflict

-- Session 1: Read
BEGIN;
    SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;

    SELECT balance FROM accounts WHERE name = 'Alice';  -- 1000

-- Session 2: Write based on same read
-- BEGIN;
--     SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
--     UPDATE accounts SET balance = balance + 100 WHERE name = 'Alice';
-- COMMIT;

-- Session 1: Write
    UPDATE accounts SET balance = balance - 100 WHERE name = 'Alice';
COMMIT;

-- With SSI, PostgreSQL detects the conflict and may abort!

================================================================================
STEP 5: PRACTICAL EXAMPLE
================================================================================

-- Use SERIALIZABLE for business rules

-- Rule: Account balance cannot go negative

BEGIN;
    SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;

    -- Read current balance
    SELECT balance FROM accounts WHERE name = 'Alice';  -- 1000

-- Another transaction might change the balance
-- BEGIN;
--     UPDATE accounts SET balance = balance - 500 WHERE name = 'Alice';
-- COMMIT;

-- Try to update based on old read
    UPDATE accounts SET balance = balance - 600 WHERE name = 'Alice';
    -- If balance changed, this might fail!

COMMIT;

-- Check result
SELECT * FROM accounts;

-- KEY: SSI prevents incorrect results from race conditions!

================================================================================
STEP 6: SERIALIZATION FAILURES
================================================================================

-- When SSI detects conflict, it raises an error

-- Example conflict:
-- T1: Read X
-- T2: Write X
-- T1: Write X  ← Conflict!

-- PostgreSQL returns:
-- ERROR: could not serialize access due to read/write dependencies

-- Application must retry the transaction

-- Function with automatic retry
CREATE OR REPLACE FUNCTION transfer_with_retry(
    from_acc INTEGER,
    to_acc INTEGER,
    amount DECIMAL,
    max_retries INTEGER DEFAULT 3
) RETURNS TEXT AS $$
DECLARE
    v_attempt INTEGER := 0;
    v_success BOOLEAN := FALSE;
    v_result TEXT;
BEGIN
    WHILE v_attempt < max_retries AND NOT v_success LOOP
        BEGIN
            v_attempt := v_attempt + 1;

            -- Perform transfer
            UPDATE accounts SET balance = balance - amount WHERE account_id = from_acc;
            UPDATE accounts SET balance = balance + amount WHERE account_id = to_acc;

            v_result := 'Success on attempt ' || v_attempt;
            v_success := TRUE;

        EXCEPTION
            WHEN OTHERS THEN
                IF SQLERRM LIKE '%serialize%' THEN
                    RAISE NOTICE 'Serialization conflict, attempt % of %, retrying...', v_attempt, max_retries;
                ELSE
                    RAISE;
                END IF;
        END;
    END LOOP;

    IF NOT v_success THEN
        RAISE EXCEPTION 'Failed after % attempts', max_retries;
    END IF;

    RETURN v_result;
END;
$$ LANGUAGE plpgsql;

-- Test (may need retry)
-- SELECT transfer_with_retry(1, 2, 100);

================================================================================
STEP 7: WHEN TO USE SERIALIZABLE
================================================================================

-- Use SERIALIZABLE when:
-- - Correctness > performance
-- - Business rules must be enforced
-- - Conflicts are rare

-- Don't use when:
-- - High contention
-- - Many concurrent updates
-- - Performance critical

-- Check current isolation
SELECT current_setting('transaction_isolation');

================================================================================
STEP 8: SUMMARY
================================================================================

✅ SSI:
  - Serializable Snapshot Isolation
  - PostgreSQL's serializable implementation
  - Detects conflicts
  - May require retry

✅ CONFLICTS:
  - Read-write dependencies
  - Write-write dependencies
  - SSI detects these

✅ RETRY:
  - Serialization failure = retry
  - Application must handle
  - Exponential backoff recommended

📌 CHOOSE SERIALIZABLE WHEN:
  - Correctness is critical
  - Business rules across rows
  - Can tolerate retries

EOF
