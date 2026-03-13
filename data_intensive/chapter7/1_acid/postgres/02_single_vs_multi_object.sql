================================================================================
  PostgreSQL Single vs Multi-Object - DDIA Chapter 7.1
  Learn by doing: Understanding Transaction Scope
================================================================================

COVERS:
  - Single-object operations: Atomicity for one row
  - Multi-object operations: Atomicity across multiple tables
  - When to use each type
  - Trade-offs

================================================================================
STEP 1: CONNECT
================================================================================

  psql -U postgres -d postgres
  CREATE DATABASE single_multi_demo;
  \c single_multi_demo

================================================================================
STEP 2: SINGLE-OBJECT OPERATIONS
================================================================================

-- Single-object: Atomicity and isolation apply to ONE row

DROP TABLE IF EXISTS documents CASCADE;

CREATE TABLE documents (
    doc_id SERIAL PRIMARY KEY,
    title VARCHAR(100),
    content TEXT,
    status VARCHAR(20) DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Single INSERT is atomic
INSERT INTO documents (title, content) VALUES
    ('Doc 1', 'Content here');

-- Single UPDATE is atomic
UPDATE documents SET content = 'Updated content' WHERE doc_id = 1;

-- Even if crash mid-update, WAL ensures consistency

SELECT * FROM documents;

-- KEY: Single-object operations are ALWAYS atomic in PostgreSQL

================================================================================
STEP 3: MULTI-OBJECT NEED
================================================================================

-- Multi-object: Need to maintain consistency across tables

DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS profiles CASCADE;
DROP TABLE IF EXISTS sessions CASCADE;

CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE,
    email VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE profiles (
    profile_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    bio TEXT,
    avatar_url VARCHAR(200)
);

CREATE TABLE sessions (
    session_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    token VARCHAR(100),
    expires_at TIMESTAMP
);

-- PROBLEM: Creating user, profile, session should be atomic
-- Without transaction: could end up with orphaned data

-- BAD: Without transaction (can leave inconsistent state)
INSERT INTO users (username, email) VALUES ('john', 'john@test.com');
-- Crash here! User exists but no profile/session

-- GOOD: With transaction
BEGIN;
    INSERT INTO users (username, email) VALUES ('alice', 'alice@test.com');
    INSERT INTO profiles (user_id, bio) VALUES (currval('users_user_id_seq'), 'Bio here');
    INSERT INTO sessions (user_id, token, expires_at)
        VALUES (currval('users_user_id_seq'), 'token123', NOW() + interval '1 day');
COMMIT;

-- Verify all created together
SELECT u.username, p.bio, s.token
FROM users u
LEFT JOIN profiles p ON u.user_id = p.user_id
LEFT JOIN sessions s ON u.user_id = s.user_id
WHERE u.username = 'alice';

-- KEY INSIGHT: Multi-object transactions ensure consistency!

================================================================================
STEP 4: FOREIGN KEY + TRANSACTION
================================================================================

DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS customers CASCADE;
DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS products CASCADE;

CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100)
);

CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(customer_id),
    order_date TIMESTAMP DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'pending'
);

CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    price DECIMAL(10,2)
);

CREATE TABLE order_items (
    item_id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(order_id),
    product_id INTEGER REFERENCES products(product_id),
    quantity INTEGER,
    price DECIMAL(10,2)
);

-- Insert test data
INSERT INTO customers (name, email) VALUES
    ('John', 'john@test.com'),
    ('Jane', 'jane@test.com');

INSERT INTO products (name, price) VALUES
    ('Widget', 10.00),
    ('Gadget', 25.00);

-- Create order with items in transaction
BEGIN;
    INSERT INTO orders (customer_id) VALUES (1);
    INSERT INTO order_items (order_id, product_id, quantity, price)
        VALUES (currval('orders_order_id_seq'), 1, 2, 10.00);
    INSERT INTO order_items (order_id, product_id, quantity, price)
        VALUES (currval('orders_order_id_seq'), 2, 1, 25.00);
COMMIT;

-- Verify
SELECT o.order_id, c.name, p.name, oi.quantity
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN order_items oi ON o.order_id = oi.order_id
JOIN products p ON oi.product_id = p.product_id;

-- KEY: Transaction keeps all tables in sync!

================================================================================
STEP 5: DENORMALIZED DATA IN SYNC
================================================================================

-- In denormalized designs, same data exists in multiple places

DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS customers CASCADE;

CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100),
    total_orders INTEGER DEFAULT 0,
    total_spent DECIMAL(10,2) DEFAULT 0
);

CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(customer_id),
    amount DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Without transaction: totals can get out of sync!
INSERT INTO customers (name, email) VALUES ('Bob', 'bob@test.com');
INSERT INTO orders (customer_id, amount) VALUES (1, 100.00);
-- Forgot to update customer totals!

-- With transaction: atomic update
BEGIN;
    INSERT INTO orders (customer_id, amount) VALUES (2, 150.00);
    UPDATE customers SET
        total_orders = total_orders + 1,
        total_spent = total_spent + 150.00
    WHERE customer_id = 2;
COMMIT;

-- Verify totals
SELECT * FROM customers WHERE customer_id = 2;

-- KEY: Transaction ensures denormalized data stays in sync!

================================================================================
STEP 6: ERROR HANDLING IN TRANSACTIONS
================================================================================

-- Transactions can fail - need proper error handling

DROP TABLE IF EXISTS accounts CASCADE;

CREATE TABLE accounts (
    account_id SERIAL PRIMARY KEY,
    name VARCHAR(50),
    balance DECIMAL(10,2) DEFAULT 0
);

INSERT INTO accounts (name, balance) VALUES
    ('Account A', 1000),
    ('Account B', 1000);

-- Function with error handling
CREATE OR REPLACE FUNCTION safe_transfer(
    from_acc INTEGER,
    to_acc INTEGER,
    amount DECIMAL
) RETURNS BOOLEAN AS $$
DECLARE
    current_balance DECIMAL;
BEGIN
    -- Check balance first
    SELECT balance INTO current_balance
    FROM accounts WHERE account_id = from_acc;

    IF current_balance < amount THEN
        RAISE EXCEPTION 'Insufficient funds: % < %', current_balance, amount;
    END IF;

    -- Perform transfer
    UPDATE accounts SET balance = balance - amount WHERE account_id = from_acc;
    UPDATE accounts SET balance = balance + amount WHERE account_id = to_acc;

    RETURN TRUE;

EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'Transfer failed: %', SQLERRM;
        RETURN FALSE;
END;
$$ LANGUAGE plpgsql;

-- Test successful transfer
SELECT safe_transfer(1, 2, 100.00);
SELECT * FROM accounts;

-- Test failed transfer
SELECT safe_transfer(1, 2, 10000.00);

-- KEY: Proper error handling + transactions = robust code!

================================================================================
STEP 7: SAVEPOINTS FOR PARTIAL ROLLBACK
================================================================================

-- Savepoints allow partial rollback within a transaction

DROP TABLE IF EXISTS entries CASCADE;

CREATE TABLE entries (
    entry_id SERIAL PRIMARY KEY,
    name VARCHAR(50),
    status VARCHAR(20)
);

-- Start transaction
BEGIN;
    INSERT INTO entries (name, status) VALUES ('Entry 1', 'started');

    -- Create savepoint
    SAVEPOINT sp1;

    -- This might fail
    INSERT INTO entries (name, status) VALUES ('Entry 2', 'started');

    -- Rollback to savepoint (keep Entry 1)
    ROLLBACK TO SAVEPOINT sp1;

    -- Continue with other operations
    INSERT INTO entries (name, status) VALUES ('Entry 3', 'started');

COMMIT;

-- Entry 2 was rolled back, Entry 1 and 3 remain
SELECT * FROM entries;

-- KEY: Savepoints provide fine-grained control!

================================================================================
STEP 8: COMPARISON TABLE
================================================================================

DROP TABLE IF EXISTS operation_comparison CASCADE;

CREATE TABLE operation_comparison (
    aspect TEXT,
    single_object TEXT,
    multi_object TEXT
);

INSERT INTO operation_comparison VALUES
    ('Scope', 'One row/document', 'Multiple tables/rows'),
    ('Atomicity', 'Built-in (WAL)', 'Requires transaction'),
    ('Consistency', 'Row-level only', 'Cross-table possible'),
    ('Performance', 'Fast', 'Slower (coordination)'),
    ('Use Case', 'Simple updates', 'Complex business logic');

SELECT * FROM operation_comparison;

================================================================================
SUMMARY
================================================================================

✅ SINGLE-OBJECT:
  - Atomicity guaranteed by database (WAL)
  - Fast, simple
  - Good for simple CRUD

✅ MULTI-OBJECT:
  - All-or-nothing across tables
  - Maintains referential integrity
  - Required for complex business logic

📌 DECISION GUIDE:
  - Need consistency across tables? → Multi-object transaction
  - Simple row updates? → Single-object (auto-atomic)

EOF
