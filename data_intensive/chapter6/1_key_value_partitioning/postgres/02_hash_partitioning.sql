================================================================================
  PostgreSQL Hash Partitioning - DDIA Chapter 6.1
  Hands-on practice with hash-based partitioning
================================================================================

WHAT YOU'LL LEARN:
  ✅ How hash partitioning distributes keys uniformly
  ✅ Why it eliminates hot spots
  ✅ Why range queries become slower (must scan all partitions)
  ✅ When to use hash partitioning

================================================================================
STEP 1: CREATE HASH-PARTITIONED TABLE
================================================================================

-- Drop existing table
DROP TABLE IF EXISTS users CASCADE;

-- Create parent table with PARTITION BY HASH
CREATE TABLE users (
    user_id BIGSERIAL,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'active'
) PARTITION BY HASH (user_id);

-- PostgreSQL hash partitioning uses a modulus
-- Number of partitions = 4 (you can choose any number)
-- Each partition gets keys where: hash(key) % num_partitions = partition_index

-- Create 4 hash partitions
CREATE TABLE users_p0 PARTITION OF users
    FOR VALUES WITH (MODULUS 4, REMAINDER 0);

CREATE TABLE users_p1 PARTITION OF users
    FOR VALUES WITH (MODULUS 4, REMAINDER 1);

CREATE TABLE users_p2 PARTITION OF users
    FOR VALUES WITH (MODULUS 4, REMAINDER 2);

CREATE TABLE users_p3 PARTITION OF users
    FOR VALUES WITH (MODULUS 4, REMAINDER 3);

-- Create indexes
CREATE INDEX idx_users_username ON users (username);
CREATE INDEX idx_users_email ON users (email);

================================================================================
STEP 2: UNDERSTAND HOW HASH PARTITIONING WORKS
================================================================================

-- PostgreSQL uses this formula internally:
-- partition_index = hash(key) % num_partitions

-- Let's verify by inserting users and checking where they land
INSERT INTO users (username, email)
VALUES
    ('alice', 'alice@example.com'),
    ('bob', 'bob@example.com'),
    ('charlie', 'charlie@example.com'),
    ('david', 'david@example.com'),
    ('eve', 'eve@example.com');

-- Check distribution - should be roughly even
SELECT
    schemaname,
    tablename,
    tableowner
FROM pg_tables
WHERE tablename LIKE 'users_p%';

-- More detailed: check row counts
SELECT
    'users_p0' AS partition, COUNT(*) AS rows FROM users_p0
UNION ALL
SELECT 'users_p1', COUNT(*) FROM users_p1
UNION ALL
SELECT 'users_p2', COUNT(*) FROM users_p2
UNION ALL
SELECT 'users_p3', COUNT(*) FROM users_p3;

-- Or use pg_stat_user_tables
SELECT
    relname AS partition,
    n_live_tup AS rows
FROM pg_stat_user_tables
WHERE relname LIKE 'users_p%'
ORDER BY relname;

================================================================================
STEP 3: INSERT LARGE DATASET TO SEE DISTRIBUTION
================================================================================

-- Insert 10,000 users and see how they're distributed
INSERT INTO users (username, email)
SELECT
    'user_' || generate_series AS username,
    'user_' || generate_series || '@example.com' AS email
FROM generate_series(1, 10000);

-- Check distribution - should be VERY even (within ~1-2%)
SELECT
    relname AS partition,
    n_live_tup AS rows,
    ROUND(100.0 * n_live_tup / SUM(n_live_tup) OVER(), 2) AS percentage
FROM pg_stat_user_tables
WHERE relname LIKE 'users_p%'
ORDER BY relname;

-- Expected: ~2500 rows each (25% each for 4 partitions)

================================================================================
STEP 4: QUERY BEHAVIOR - POINT QUERIES ARE EFFICIENT
================================================================================

-- Point query by user_id - uses ONLY one partition!
EXPLAIN ANALYZE
SELECT * FROM users WHERE user_id = 5000;

-- This is efficient because PostgreSQL knows which partition to check

-- Query by username - must scan ALL partitions (no partition pruning)
EXPLAIN ANALYZE
SELECT * FROM users WHERE username = 'user_5000';

-- This scans ALL 4 partitions!

================================================================================
STEP 5: THE PROBLEM - RANGE QUERIES ARE SLOW
================================================================================

-- Range query - MUST scan ALL partitions!
EXPLAIN ANALYZE
SELECT * FROM users
WHERE user_id BETWEEN 1000 AND 2000;

-- Notice: "Seq Scan on users_p0" etc. - scans ALL partitions
-- This is the MAIN TRADEOFF of hash partitioning

-- Compare with range partitioning:
-- Range: range query might only hit 1-2 partitions
-- Hash: range query ALWAYS hits ALL partitions

================================================================================
STEP 6: HASH PARTITIONING WITH STRING KEYS
================================================================================

-- You can hash any data type! Let's try with username
DROP TABLE IF EXISTS user_sessions CASCADE;

CREATE TABLE user_sessions (
    session_id BIGSERIAL,
    username VARCHAR(50) NOT NULL,
    session_token UUID DEFAULT gen_random_uuid(),
    created_at TIMESTAMP DEFAULT NOW()
) PARTITION BY HASH (username);

-- Create partitions
CREATE TABLE user_sessions_p0 PARTITION OF user_sessions
    FOR VALUES WITH (MODULUS 4, REMAINDER 0);

CREATE TABLE user_sessions_p1 PARTITION OF user_sessions
    FOR VALUES WITH (MODULUS 4, REMAINDER 1);

CREATE TABLE user_sessions_p2 PARTITION OF user_sessions
    FOR VALUES WITH (MODULUS 4, REMAINDER 2);

CREATE TABLE user_sessions_p3 PARTITION OF user_sessions
    FOR VALUES WITH (MODULUS 4, REMAINDER 3);

-- Insert data
INSERT INTO user_sessions (username)
SELECT 'user_' || generate_series
FROM generate_series(1, 1000);

-- Check distribution
SELECT
    relname AS partition,
    n_live_tup AS rows
FROM pg_stat_user_tables
WHERE relname LIKE 'user_sessions_p%'
ORDER BY relname;

-- Query by specific username - only one partition!
EXPLAIN ANALYZE
SELECT * FROM user_sessions WHERE username = 'user_500';

================================================================================
STEP 7: COMPARING RANGE vs HASH - PRACTICAL EXAMPLE
================================================================================

-- Let's create the SAME data with both strategies and compare

-- === RANGE PARTITIONING ===
DROP TABLE IF EXISTS orders_range CASCADE;
CREATE TABLE orders_range (
    order_id BIGINT,
    order_date DATE NOT NULL,
    customer_id BIGINT,
    total DECIMAL(10,2)
) PARTITION BY RANGE (order_id);

-- Partitions by ID ranges
CREATE TABLE orders_range_p1 PARTITION OF orders_range
    FOR VALUES FROM (1) TO (2501);

CREATE TABLE orders_range_p2 PARTITION OF orders_range
    FOR VALUES FROM (2501) TO (5001);

CREATE TABLE orders_range_p3 PARTITION OF orders_range
    FOR VALUES FROM (5001) TO (7501);

CREATE TABLE orders_range_p4 PARTITION OF orders_range
    FOR VALUES FROM (7501) TO (10001);

-- === HASH PARTITIONING ===
DROP TABLE IF EXISTS orders_hash CASCADE;
CREATE TABLE orders_hash (
    order_id BIGINT,
    order_date DATE NOT NULL,
    customer_id BIGINT,
    total DECIMAL(10,2)
) PARTITION BY HASH (order_id);

-- Same number of partitions
CREATE TABLE orders_hash_p1 PARTITION OF orders_hash
    FOR VALUES WITH (MODULUS 4, REMAINDER 0);

CREATE TABLE orders_hash_p2 PARTITION OF orders_hash
    FOR VALUES WITH (MODULUS 4, REMAINDER 1);

CREATE TABLE orders_hash_p3 PARTITION OF orders_hash
    FOR VALUES WITH (MODULUS 4, REMAINDER 2);

CREATE TABLE orders_hash_p4 PARTITION OF orders_hash
    FOR VALUES WITH (MODULUS 4, REMAINDER 3);

-- Insert same data into both
INSERT INTO orders_range (order_id, order_date, customer_id, total)
SELECT
    generate_series AS order_id,
    '2024-01-01'::DATE + (random() * 30)::INTEGER AS order_date,
    (random() * 1000)::BIGINT AS customer_id,
    (random() * 500)::DECIMAL(10,2) AS total
FROM generate_series(1, 10000);

INSERT INTO orders_hash (order_id, order_date, customer_id, total)
SELECT * FROM orders_range;

-- Check distribution - both should be even
SELECT 'Range Partitioning' AS strategy, relname AS partition, n_live_tup AS rows
FROM pg_stat_user_tables
WHERE relname LIKE 'orders_range_p%'
UNION ALL
SELECT 'Hash Partitioning', relname, n_live_tup
FROM pg_stat_user_tables
WHERE relname LIKE 'orders_hash_p%'
ORDER BY 1, 2;

================================================================================
STEP 8: QUERY PERFORMANCE COMPARISON
================================================================================

-- POINT QUERY: Find order_id = 5000
-- Range: Efficient! Only one partition
EXPLAIN ANALYZE
SELECT * FROM orders_range WHERE order_id = 5000;

-- Hash: Efficient! Only one partition
EXPLAIN ANALYZE
SELECT * FROM orders_hash WHERE order_id = 5000;

-- RANGE QUERY: Find orders 1000-2000
-- Range: EFFICIENT! Only relevant partitions
EXPLAIN ANALYZE
SELECT * FROM orders_range WHERE order_id BETWEEN 1000 AND 2000;

-- Hash: SLOW! Must scan ALL partitions
EXPLAIN ANALYZE
SELECT * FROM orders_hash WHERE order_id BETWEEN 1000 AND 2000;

-- CUSTOMER QUERIES: All orders for customer_id = 100
-- Both: MUST scan ALL partitions (customer_id is not the partition key)
EXPLAIN ANALYZE
SELECT * FROM orders_range WHERE customer_id = 100;

EXPLAIN ANALYZE
SELECT * FROM orders_hash WHERE customer_id = 100;

================================================================================
SUMMARY: HASH PARTITIONING TRADE-OFFS
================================================================================

✅ Hash Partitioning PROS:
  - Even data distribution (no hot spots)
  - Great for point queries by partition key
  - Works well with high-cardinality keys

❌ Hash Partitioning CONS:
  - Range queries MUST scan ALL partitions
  - Cannot efficiently do "ORDER BY" across partitions
  - Adding partitions requires reshuffling data

📌 WHEN TO USE HASH PARTITIONING:
  - High-cardinality keys (user IDs, session IDs, UUIDs)
  - Point queries by specific key
  - No range query requirements
  - Want to avoid hot spots

📌 WHEN TO USE RANGE PARTITIONING:
  - Time-series data
  - Range queries are common
  - Natural ordering in your data

================================================================================
NEXT STEPS:
================================================================================

1. Try Exercise 3: List Partitioning (03_list_partitioning.sql)
2. Try Exercise 4: Handling Hot Spots (04_hot_spots.sql)
3. Compare with the Python examples from DDIA

EOF
