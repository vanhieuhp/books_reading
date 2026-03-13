================================================================================
  PostgreSQL Read Committed - DDIA Chapter 7.3
  Learn by doing: Understanding Read Committed Isolation
================================================================================

COVERS:
  - Read Committed isolation level
  - How PostgreSQL implements it (MVCC)
  - What it prevents (dirty reads)
  - What it allows (non-repeatable reads)

================================================================================
STEP 1: CONNECT
================================================================================

  psql -U postgres -d postgres
  CREATE DATABASE read_committed_demo;
  \c read_committed_demo

================================================================================
STEP 2: SETUP
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

================================================================================
STEP 3: UNDERSTAND READ COMMITTED
================================================================================

-- Default isolation level in PostgreSQL
SHOW transaction_isolation;

-- Each statement sees committed data from other transactions

-- Session 1: Start transaction, update but don't commit
BEGIN;
    UPDATE accounts SET balance = balance - 100 WHERE name = 'Alice';

-- Session 2: Read Alice's balance
-- In READ COMMITTED: sees COMMITTED value (1000), not the uncommitted change (-100)

SELECT balance FROM accounts WHERE name = 'Alice';  -- Returns 1000

-- Session 1: Commit
COMMIT;

-- Session 2: Now sees committed change
SELECT balance FROM accounts WHERE name = 'Alice';  -- Returns 900

-- KEY: Read Committed prevents DIRTY reads!

================================================================================
STEP 4: DEMONSTRATE NO DIRTY READS
================================================================================

-- Dirty read: Reading uncommitted data from another transaction

-- PostgreSQL's Read Committed prevents dirty reads!

-- Transaction A: Uncommitted change
BEGIN;
    UPDATE accounts SET balance = 9999 WHERE name = 'Bob';

-- Transaction B: Try to read (in another session)
-- Would see OLD value (1000), not the uncommitted 9999

COMMIT;

-- After commit, new value is visible
SELECT * FROM accounts;

-- KEY INSIGHT: You can NEVER see uncommitted data in PostgreSQL!

================================================================================
STEP 5: NON-REPEATABLE READS ARE POSSIBLE
================================================================================

-- Non-repeatable read: Same query returns different results within transaction

-- Session 1: Start transaction
BEGIN;

    -- First read
    SELECT balance FROM accounts WHERE name = 'Alice';  -- Returns 900

-- Session 2: Update and commit
-- UPDATE accounts SET balance = 800 WHERE name = 'Alice';
-- COMMIT;

-- Session 1: Read again (in same transaction)
    SELECT balance FROM accounts WHERE name = 'Alice';  -- Returns 800! Different!

COMMIT;

-- KEY: Read Committed allows NON-REPEATABLE reads!

================================================================================
STEP 6: HOW IT WORKS - MVCC
================================================================================

-- PostgreSQL uses MVCC (Multi-Version Concurrency Control)

-- Each transaction sees a "snapshot" at statement start

-- View transaction details
SELECT txid_current(), now();

-- See row versions
SELECT xmin, xmax, * FROM accounts;

-- In Read Committed:
--   - Each statement gets a NEW snapshot
--   - Sees committed changes from OTHER transactions

-- Compare with REPEATABLE READ (next exercise)

================================================================================
STEP 7: PRACTICAL EXAMPLE
================================================================================

-- Real-world scenario: Balance transfer

-- Function to transfer with proper locking
CREATE OR REPLACE FUNCTION transfer_funds(
    from_account INTEGER,
    to_account INTEGER,
    amount DECIMAL
) RETURNS BOOLEAN AS $$
DECLARE
    from_balance DECIMAL;
BEGIN
    -- Check balance (with lock)
    SELECT balance INTO from_balance
    FROM accounts
    WHERE account_id = from_account
    FOR UPDATE;

    IF from_balance < amount THEN
        RAISE EXCEPTION 'Insufficient funds: %', from_balance;
    END IF;

    -- Debit
    UPDATE accounts SET balance = balance - amount WHERE account_id = from_account;

    -- Credit
    UPDATE accounts SET balance = balance + amount WHERE account_id = to_account;

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Test
SELECT transfer_funds(1, 2, 100);
SELECT * FROM accounts;

================================================================================
STEP 8: SUMMARY
================================================================================

✅ READ COMMITTED:
  - Default in PostgreSQL
  - Prevents dirty reads
  - Allows non-repeatable reads

✅ MVCC:
  - Each statement sees fresh snapshot
  - Multiple versions of rows
  - Readers don't block writers

❌ LIMITATION:
  - Same query in same transaction can return different results

EOF
