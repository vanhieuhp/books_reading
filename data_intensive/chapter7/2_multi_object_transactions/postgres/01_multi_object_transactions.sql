================================================================================
  PostgreSQL Multi-Object Transactions - DDIA Chapter 7.2
  Learn by doing: Single vs Multi-Object Transactions
================================================================================

WHAT YOU'LL LEARN:
  ✅ Single-object atomicity
  ✅ Multi-object transactions for consistency
  ✅ Foreign key maintenance
  ✅ Error handling and retries

PREREQUISITES:
  - PostgreSQL 10+
  - psql or any PostgreSQL client

================================================================================
CONCEPT: SINGLE VS MULTI-OBJECT TRANSACTIONS
================================================================================

From DDIA (pp. 244-250):

Single-object: Atomicity for ONE row/document
Multi-object: Atomicity for MULTIPLE rows/tables

================================================================================
STEP 1: CONNECT TO POSTGRESQL
================================================================================

  psql -U postgres -d postgres

================================================================================
STEP 2: SETUP TEST DATABASE
================================================================================

  CREATE DATABASE multi_object_demo;
  \c multi_object_demo

================================================================================
STEP 3: SINGLE-OBJECT ATOMICITY
================================================================================

-- PostgreSQL guarantees atomicity for single objects (rows)

DROP TABLE IF EXISTS documents CASCADE;

CREATE TABLE documents (
    doc_id SERIAL PRIMARY KEY,
    title VARCHAR(100),
    content TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Single-object write: atomic
INSERT INTO documents (title, content) VALUES
    ('Test Doc', 'This is the content');

-- What if power fails during update?
-- PostgreSQL uses Write-Ahead Log (WAL) to ensure atomicity

-- Update a document (single object)
UPDATE documents SET content = 'Updated content' WHERE doc_id = 1;

-- Even large documents are atomic
-- If crash occurs, WAL ensures either full update or rollback

SELECT * FROM documents;

-- KEY INSIGHT: Single-object atomicity is built-in!
-- But it can't maintain consistency across MULTIPLE objects

================================================================================
STEP 4: THE PROBLEM - MULTI-OBJECT CONSISTENCY
================================================================================

-- Example: User registration with profile

DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS profiles CASCADE;

CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE profiles (
    profile_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    bio TEXT,
    avatar_url VARCHAR(200)
);

-- PROBLEM: Without multi-object transaction

-- This could leave orphaned data:
INSERT INTO users (username, email) VALUES ('john', 'john@example.com');
-- Crash here! User exists but no profile

-- Or: User created, profile not created (inconsistent state)

SELECT * FROM users;
SELECT * FROM profiles;

-- KEY INSIGHT: Need multi-object transaction for consistency!

================================================================================
STEP 5: MULTI-OBJECT TRANSACTION SOLUTION
================================================================================

-- SOLUTION: Use a transaction to wrap both operations

BEGIN;
    -- Step 1: Create user
    INSERT INTO users (username, email) VALUES ('alice', 'alice@example.com');
    -- Get the user_id
    -- Step 2: Create profile with same user_id
    INSERT INTO profiles (user_id, bio) VALUES (currval('users_user_id_seq'), 'Hello, I am Alice!');
COMMIT;

-- Verify: Both created or both rolled back
SELECT u.*, p.bio
FROM users u
LEFT JOIN profiles p ON u.user_id = p.user_id
WHERE u.username = 'alice';

-- Now demonstrate failure case
BEGIN;
    INSERT INTO users (username, email) VALUES ('bob', 'bob@example.com');
    -- This will fail due to unique constraint
    INSERT INTO users (username, email) VALUES ('bob', 'bob2@example.com');
COMMIT;

-- Verify: Neither was committed
SELECT * FROM users WHERE username = 'bob';

-- KEY INSIGHT: Either BOTH succeed or BOTH fail!

================================================================================
STEP 6: FOREIGN KEY CONSTRAINTS IN TRANSACTIONS
================================================================================

-- Foreign keys help maintain referential integrity

DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS customers CASCADE;

CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
    total DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Without transaction: Can create orphaned orders!
INSERT INTO customers (name) VALUES ('John');
INSERT INTO orders (customer_id, total) VALUES (1, 99.99);

-- Delete the customer - what happens to the order?
DELETE FROM customers WHERE customer_id = 1;

-- With foreign key constraint (ON DELETE RESTRICT by default)
-- Can't delete customer while orders exist

-- Let's recreate with proper constraint
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS customers CASCADE;

CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id) ON DELETE RESTRICT,
    total DECIMAL(10,2) NOT NULL
);

INSERT INTO customers (name) VALUES ('John');
INSERT INTO orders (customer_id, total) VALUES (1, 99.99);

-- Try to delete - will fail!
-- DELETE FROM customers WHERE customer_id = 1;

-- Or use CASCADE: Delete orders when customer deleted
DROP TABLE orders;
CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    total DECIMAL(10,2) NOT NULL
);

INSERT INTO orders (customer_id, total) VALUES (1, 99.99);
DELETE FROM customers WHERE customer_id = 1;

-- Orders are automatically deleted too
SELECT * FROM orders;

-- KEY INSIGHT: Use constraints + transactions together!

================================================================================
STEP 7: BATCH OPERATIONS WITH TRANSACTIONS
================================================================================

-- Example: Process a batch of orders

DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS products CASCADE;

CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    stock INTEGER DEFAULT 0,
    price DECIMAL(10,2)
);

CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INTEGER,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE order_items (
    item_id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(order_id),
    product_id INTEGER REFERENCES products(product_id),
    quantity INTEGER,
    price DECIMAL(10,2)
);

-- Insert products
INSERT INTO products (name, stock, price) VALUES
    ('Widget', 100, 9.99),
    ('Gadget', 50, 19.99),
    ('Gizmo', 200, 4.99);

-- Process order in a transaction
BEGIN;
    -- Create order
    INSERT INTO orders (customer_id) VALUES (1);

    -- Get order_id
    INSERT INTO order_items (order_id, product_id, quantity, price)
    VALUES (currval('orders_order_id_seq'), 1, 2, 9.99),
           (currval('orders_order_id_seq'), 2, 1, 19.99);

    -- Update stock
    UPDATE products SET stock = stock - 2 WHERE product_id = 1;
    UPDATE products SET stock = stock - 1 WHERE product_id = 2;

    -- Mark order as processed
    UPDATE orders SET status = 'processed' WHERE order_id = currval('orders_order_id_seq');
COMMIT;

-- Verify all changes applied together
SELECT * FROM orders;
SELECT * FROM order_items;
SELECT * FROM products WHERE product_id IN (1, 2);

-- KEY INSIGHT: Transaction ensures ALL or NOTHING!

================================================================================
STEP 8: ERROR HANDLING AND RETRIES
================================================================================

-- When transactions fail, proper handling is crucial

-- Create function with error handling
DROP FUNCTION IF EXISTS safe_order_create(INTEGER, INTEGER[]);

CREATE OR REPLACE FUNCTION safe_order_create(
    p_customer_id INTEGER,
    p_product_ids INTEGER[]
) RETURNS INTEGER AS $$
DECLARE
    v_order_id INTEGER;
    v_product_id INTEGER;
BEGIN
    BEGIN
        -- Create order
        INSERT INTO orders (customer_id, status)
        VALUES (p_customer_id, 'pending')
        RETURNING order_id INTO v_order_id;

        -- Add items
        FOREACH v_product_id IN ARRAY p_product_ids
        LOOP
            INSERT INTO order_items (order_id, product_id, quantity, price)
            VALUES (v_order_id, v_product_id, 1,
                   (SELECT price FROM products WHERE product_id = v_product_id));
        END LOOP;

        -- Update status
        UPDATE orders SET status = 'processed' WHERE order_id = v_order_id;

        RETURN v_order_id;

    EXCEPTION
        WHEN OTHERS THEN
            -- Rollback automatic on exception
            RAISE NOTICE 'Order creation failed: %', SQLERRM;
            RETURN NULL;
    END;
END;
$$ LANGUAGE plpgsql;

-- Test successful order
SELECT safe_order_create(1, ARRAY[1, 3]);

-- Test failed order (invalid product)
-- SELECT safe_order_create(1, ARRAY[999]);

-- KEY INSIGHT: Handle errors gracefully, let caller retry

================================================================================
STEP 9: TRANSACTION ISOLATION IMPACT
================================================================================

-- Isolation level affects multi-object transactions

-- Default: READ COMMITTED
SHOW transaction_isolation;

-- In READ COMMITTED:
-- - Each statement sees snapshot at start of statement
-- - Can see changes from committed transactions

-- Example: Two concurrent transactions

-- Transaction A: Transfer money
BEGIN;
    UPDATE accounts SET balance = balance - 100 WHERE account_name = 'Alice';
    -- (doesn't commit yet)

-- Transaction B: Read balance (in another session)
-- Would see Alice's ORIGINAL balance (before A's update)
-- Because A hasn't committed yet

-- Commit Transaction A
COMMIT;

-- Now Transaction B would see new balance

-- With READ COMMITTED, you can see inconsistent state temporarily
-- But with proper locking, you can prevent this

================================================================================
STEP 10: PRACTICAL PATTERNS
================================================================================

-- Pattern 1: Saga Pattern (for distributed systems)

-- Since PostgreSQL doesn't support distributed transactions,
-- Use compensating transactions

-- Example: Transfer between two databases
-- 1. Debit from source (local transaction)
-- 2. Credit to destination (separate transaction)
-- If step 2 fails, reverse step 1 (compensating transaction)

-- Pattern 2: Two-Phase Commit (2PC)

-- PostgreSQL doesn't have native 2PC, but you can simulate:

-- Prepare phase:
--   - Lock all resources
--   - Validate all can succeed

-- Commit phase:
--   - Apply all changes
--   - Release locks

-- Pattern 3: Eventual Consistency

-- For high-performance systems:
-- 1. Write to local DB
-- 2. Send event to message queue
-- 3. Other services process event
-- 4. If failed, retry or compensate

-- This is used by microservices and NoSQL systems

================================================================================
SUMMARY: MULTI-OBJECT TRANSACTIONS
================================================================================

✅ SINGLE-OBJECT:
  - Atomicity guaranteed by database
  - Fast, no coordination overhead
  - Can't maintain cross-object consistency

✅ MULTI-OBJECT:
  - All-or-nothing across multiple tables
  - Maintains foreign key integrity
  - Requires explicit BEGIN/COMMIT

⚠️ TRADE-OFFS:
  - More overhead (locking, coordination)
  - Risk of deadlocks
  - Not available in all databases (Cassandra, MongoDB pre-4.0)

📌 USE CASES:
  - Financial transactions (always use multi-object)
  - User registration with profile
  - Order processing with inventory

📌 ALTERNATIVES:
  - Saga pattern for distributed systems
  - Eventual consistency for high scale
  - Single-object with application-level补偿

================================================================================
NEXT STEPS:
================================================================================

1. Try Chapter 7.3: Weak Isolation Levels
   - Understand Read Committed vs Snapshot Isolation

2. Learn about:
   - Isolation levels and their anomalies
   - Lost updates, write skew

3. Read DDIA pp. 244-262 for more theory

EOF
