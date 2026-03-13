-- ================================================================================
--   PostgreSQL Local Secondary Indexes - DDIA Chapter 6.2
--   Learn by doing: Document-Partitioned (Local) Indexes
-- ================================================================================

-- WHAT YOU'LL LEARN:
--   ✅ How local (document-partitioned) indexes work
--   ✅ Why writes are fast with local indexes
--   ✅ Why reads require scatter/gather across partitions
--   ✅ How PostgreSQL implements local indexes on partitioned tables

-- PREREQUISITES:
--   - PostgreSQL 10+ (native partitioning support)
--   - psql or any PostgreSQL client
--   - Completed Chapter 6.1 exercises (recommended)

-- ================================================================================
-- CONCEPT: LOCAL (DOCUMENT-PARTITIONED) INDEXES
-- ================================================================================

-- From DDIA (p. 208-214):
--   "Each partition maintains its own secondary index, covering only the
--    documents within that partition."

--   Write: ✅ Fast (single partition)
--   Read:  ❌ Slow (scatter/gather all partitions)

-- Real-world systems using local indexes:
--   - MongoDB (sharded clusters)
--   - Cassandra (local secondary indexes)
--   - Elasticsearch (each shard has its own index)

-- ================================================================================
-- STEP 1: CONNECT TO POSTGRESQL
-- ================================================================================

--   psql -U postgres -d postgres

-- Or if you have a specific database:

--   psql -U postgres -d mydb

-- ================================================================================
-- STEP 2: CREATE PARTITIONED TABLE (DATA PARTITIONS)
-- ================================================================================

-- Drop existing tables for clean restart
DROP TABLE IF EXISTS cars CASCADE;

-- Create a partitioned table (data is partitioned by car_id)
-- This simulates a distributed database with multiple partitions
CREATE TABLE cars (
    car_id BIGSERIAL,
    car_uuid UUID DEFAULT gen_random_uuid(),
    color VARCHAR(20) NOT NULL,
    brand VARCHAR(30) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
) PARTITION BY HASH (car_uuid);

-- Create 4 partitions (simulating 4 database nodes)
CREATE TABLE cars_p0 PARTITION OF cars FOR VALUES WITH (MODULUS 4, REMAINDER 0);
CREATE TABLE cars_p1 PARTITION OF cars FOR VALUES WITH (MODULUS 4, REMAINDER 1);
CREATE TABLE cars_p2 PARTITION OF cars FOR VALUES WITH (MODULUS 4, REMAINDER 2);
CREATE TABLE cars_p3 PARTITION OF cars FOR VALUES WITH (MODULUS 4, REMAINDER 3);

-- Create LOCAL indexes on the color column
-- In PostgreSQL, indexes are automatically created on each partition
CREATE INDEX idx_cars_color ON cars (color);

-- Also index brand for more demo queries
CREATE INDEX idx_cars_brand ON cars (brand);
CREATE INDEX idx_cars_price ON cars (price);

-- ================================================================================
-- STEP 3: INSERT TEST DATA
-- ================================================================================

-- Insert cars with various colors
INSERT INTO cars (color, brand, price) VALUES
    ('red', 'Toyota', 25000),
    ('red', 'BMW', 45000),
    ('red', 'Ferrari', 200000),
    ('blue', 'Ford', 28000),
    ('blue', 'Honda', 22000),
    ('black', 'Tesla', 50000),
    ('black', 'Mercedes', 55000),
    ('silver', 'Toyota', 30000),
    ('white', 'Honda', 24000),
    ('white', 'Ford', 26000);
select * from cars;
-- Verify data distribution across partitions
SELECT
    relname AS partition_name,
    n_live_tup AS row_count
FROM pg_stat_user_tables
WHERE relname LIKE 'cars_p%'
ORDER BY relname;

-- ================================================================================
-- STEP 4: DEMONSTRATE LOCAL INDEX BEHAVIOR
-- ================================================================================

-- Check: Each partition has its own index on color
-- This is the LOCAL INDEX - each partition maintains its own index

-- List all indexes on car partitions
SELECT
    schemaname,
    tablename,
    indexname
FROM pg_indexes
WHERE tablename LIKE 'cars%'
ORDER BY tablename, indexname;

-- ================================================================================
-- STEP 5: DEMONSTRATE WRITE PERFORMANCE (FAST!)
-- ================================================================================

-- LOCAL INDEX: Writes are FAST because:
--   1. Data goes to ONE partition (based on hash)
--   2. Index update happens on the SAME partition
--   3. No cross-partition coordination needed

-- Measure write performance
-- \timing on

-- Insert many cars - each write goes to only ONE partition
INSERT INTO cars (color, brand, price)
SELECT
    (ARRAY['red', 'blue', 'black', 'silver', 'white'])[floor(random() * 5 + 1)],
    (ARRAY['Toyota', 'Honda', 'Ford', 'BMW', 'Tesla'])[floor(random() * 5 + 1)],
    floor(random() * 50000 + 20000)
FROM generate_series(1, 1000);

-- \timing off

-- Check that data is distributed across partitions
SELECT
    relname AS partition,
    n_live_tup AS rows
FROM pg_stat_user_tables
WHERE relname LIKE 'cars_p%'
ORDER BY relname;

-- ================================================================================
-- STEP 6: DEMONSTRATE READ PERFORMANCE (SLOW - Scatter/Gather)
-- ================================================================================

-- LOCAL INDEX: Reads are SLOW because:
--   1. Database doesn't know which partition has matching rows
--   2. Must query ALL partitions
--   3. Merge results together (scatter/gather)

-- First, let's see the query plan for a search by color
EXPLAIN ANALYZE
SELECT * FROM cars WHERE color = 'red';

-- Notice: It scans ALL partitions (cars_p0, cars_p1, cars_p2, cars_p3)
-- This is the SCATTER/GATHER pattern!

-- Another example: Search by brand
EXPLAIN ANALYZE
SELECT * FROM cars WHERE brand = 'Toyota';

-- Again: ALL partitions are scanned!

-- Range query: All partitions scanned
EXPLAIN ANALYZE
SELECT * FROM cars WHERE price BETWEEN 20000 AND 30000;

-- ================================================================================
-- STEP 7: DEMONSTRATE QUERY WITHOUT INDEX
-- ================================================================================

-- If we query by a column WITHOUT an index, it still scans all partitions
EXPLAIN ANALYZE
SELECT * FROM cars WHERE car_id > 100;

-- This is expensive because it must touch ALL partitions

-- ================================================================================
-- STEP 8: COMPARE WITH PRIMARY KEY LOOKUP (FAST!)
-- ================================================================================

-- Primary key lookups are FAST because:
--   1. car_id determines the partition (via car_uuid hash)
--   2. Only ONE partition is accessed

EXPLAIN ANALYZE
SELECT * FROM cars WHERE car_id = 5;

-- Notice: Only ONE partition is scanned! (Partition pruning works for PK)

-- ================================================================================
-- STEP 9: SIMULATE SCATTER/GATHER LATENCY
-- ================================================================================

-- In a real distributed system, scatter/gather adds network latency
-- Let's simulate this with a simple timing test

-- Time a query that hits ONE partition (by car_id)
EXPLAIN (ANALYZE, BUFFERS, TIMING)
SELECT * FROM cars WHERE car_id = 10;

-- Time a query that hits ALL partitions (by color)
EXPLAIN (ANALYZE, BUFFERS, TIMING)
SELECT * FROM cars WHERE color = 'red';

-- Compare: The color query takes longer because it touches all partitions

-- ================================================================================
-- STEP 10: PRACTICAL EXAMPLE - CAR DEALERSHIP
-- ================================================================================

-- Real-world scenario: A car dealership database

-- Find all red cars
SELECT color, brand, price FROM cars WHERE color = 'red';

-- Find all Toyota cars
SELECT color, brand, price FROM cars WHERE brand = 'Toyota';

-- Find expensive cars (price > 40000)
SELECT color, brand, price FROM cars WHERE price > 40000 ORDER BY price DESC;

-- All these queries SCAN ALL PARTITIONS because they use secondary indexes!

-- ================================================================================
-- SUMMARY: LOCAL INDEXES
-- ================================================================================

-- ✅ LOCAL INDEX PROS:
--   - Writes are FAST (single partition, no cross-partition coordination)
--   - Index is immediately consistent (sync update)
--   - Simple to implement
--
-- ❌ LOCAL INDEX CONS:
--   - Reads require SCATTER/GATHER (query ALL partitions)
--   - Tail latency: slowest partition determines query time
--   - Not suitable for read-heavy workloads
--
-- 📌 KEY RULE:
--   Local indexes are BEST for WRITE-HEAVY workloads:
--   - IoT sensors, event logs, analytics
--   - Applications that write more than they read

-- ================================================================================
-- NEXT STEPS:
-- ================================================================================

-- 1. Try Exercise 2: Global Indexes (02_global_indexes.sql)
--    - See the opposite trade-off: fast reads, slow writes
--
-- 2. Compare the two approaches:
--    - Run both exercises and measure query times
--    - Understand when to use each approach
--
-- 3. Read DDIA Chapter 6.2 for more theory (pp. 208-217)

-- EOF
--