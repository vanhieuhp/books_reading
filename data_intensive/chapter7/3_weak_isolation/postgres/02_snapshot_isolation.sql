================================================================================
  PostgreSQL Snapshot Isolation - DDIA Chapter 7.3
  Learn by doing: Repeatable Read & Snapshot Isolation
================================================================================

COVERS:
  - Repeatable Read isolation level
  - Snapshot isolation behavior
  - Consistent reads within transactions
  - Phantom reads

================================================================================
STEP 1: CONNECT
================================================================================

  psql -U postgres -d postgres
  CREATE DATABASE snapshot_demo;
  \c snapshot_demo

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
    ('Bob', 1000),
    ('Charlie', 1000);

================================================================================
STEP 3: REPEATABLE READ
================================================================================

-- Set isolation level
SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;

-- Verify
SHOW transaction_isolation;

-- In REPEATABLE READ:
--   - Transaction sees snapshot from transaction START
--   - All statements see the SAME data
--   - Cannot see changes from other committed transactions

BEGIN;

    -- First read
    SELECT * FROM accounts WHERE name = 'Alice';  -- Balance: 1000

-- Session 2: UPDATE and COMMIT
-- UPDATE accounts SET balance = 2000 WHERE name = 'Alice';
-- COMMIT;

-- Session 1: Read again (in same transaction)
    SELECT * FROM accounts WHERE name = 'Alice';  -- Still returns 1000!

COMMIT;

-- KEY: REPEATABLE READ provides consistent snapshot!

================================================================================
STEP 4: DEMONSTRATE SNAPSHOT
================================================================================

-- Snapshot: View of data at transaction start

DROP TABLE IF EXISTS products CASCADE;

CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    name VARCHAR(50),
    price DECIMAL(10,2)
);

INSERT INTO products (name, price) VALUES
    ('Widget', 10.00),
    ('Gadget', 20.00);

-- Session 1: REPEATABLE READ
BEGIN;
    SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;

    -- Read all products
    SELECT COUNT(*) FROM products;  -- 2 products

-- Session 2: Insert new product
-- INSERT INTO products (name, price) VALUES ('Gizmo', 30.00);
-- COMMIT;

-- Session 1: Read again
    SELECT COUNT(*) FROM products;  -- Still 2! (snapshot)

COMMIT;

-- KEY: Snapshot isolation prevents non-repeatable reads!

================================================================================
STEP 5: PHANTOM READS
================================================================================

-- Phantom read: Query returns different number of rows

-- REPEATABLE READ can still have phantom reads!

BEGIN;
    SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;

    -- Initial query
    SELECT * FROM products WHERE price > 15;  -- 1 row

-- Session 2: Insert new product
-- INSERT INTO products (name, price) VALUES ('Expensive', 100.00);
-- COMMIT;

-- Session 1: Query again
    SELECT * FROM products WHERE price > 15;  -- 2 rows! (phantom!)

COMMIT;

-- To prevent phantoms, need SERIALIZABLE

================================================================================
STEP 6: HOW SNAPSHOT ISOLATION WORKS
================================================================================

-- PostgreSQL uses MVCC (Multi-Version Concurrency Control)

-- Each row has:
--   - xmin: Transaction that created it
--   - xmax: Transaction that deleted/updated it

-- See row versions
SELECT xmin, xmax, name, price FROM products;

-- In REPEATABLE READ:
--   - Transaction gets a "snapshot" at start
--   - Uses this snapshot for entire transaction
--   - Reads from snapshot, not current data

-- Update a row
UPDATE products SET price = 15.00 WHERE name = 'Widget';

-- Now see versions
SELECT xmin, xmax, name, price FROM products;

-- Old version still exists with xmax set!

================================================================================
STEP 7: PRACTICAL USE
================================================================================

-- Use REPEATABLE READ when:
--   - Need consistent reads within transaction
--   - Generating reports
--   - Financial calculations

-- Example: Monthly report
BEGIN;
    SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;

    -- All queries see same snapshot
    SELECT SUM(balance) FROM accounts;  -- Total at snapshot time
    SELECT COUNT(*) FROM accounts;        -- Count at snapshot time

COMMIT;

-- KEY: Useful for consistent reports!

================================================================================
STEP 8: COMPARISON
================================================================================

DROP TABLE IF EXISTS isolation_levels CASCADE;

CREATE TABLE isolation_levels (
    level TEXT,
    dirty_reads TEXT,
    non_repeatable_reads TEXT,
    phantom_reads TEXT
);

INSERT INTO isolation_levels VALUES
    ('Read Committed', '❌ Prevented', '✅ Possible', '✅ Possible'),
    ('Repeatable Read', '❌ Prevented', '❌ Prevented', '✅ Possible'),
    ('Serializable', '❌ Prevented', '❌ Prevented', '❌ Prevented');

SELECT * FROM isolation_levels;

================================================================================
SUMMARY
================================================================================

✅ REPEATABLE READ:
  - Snapshot from transaction start
  - Prevents non-repeatable reads
  - Still allows phantom reads

✅ SNAPSHOT ISOLATION:
  - See data as of transaction start
  - Consistent reads within transaction

📌 USE WHEN:
  - Need consistent reads
  - Generating reports
  - Financial calculations

EOF
