================================================================================
  PostgreSQL Dynamic Partitioning - DDIA Chapter 6.3
  Learn by doing: Strategy 2 - Dynamic Partitioning
================================================================================

WHAT YOU'LL LEARN:
  ✅ How dynamic partitioning works (automatic split/merge)
  ✅ The cold-start problem and pre-splitting solution
  ✅ How partitions adapt to data size
  ✅ Trade-offs vs fixed partition strategy

PREREQUISITES:
  - PostgreSQL 10+ (native partitioning support)
  - psql or any PostgreSQL client

================================================================================
CONCEPT: DYNAMIC PARTITIONING
================================================================================

From DDIA (pp. 207-209):
  "Allow the number of partitions to vary with total data size.
   When a partition grows too large, it SPLITS into two smaller partitions.
   When a partition shrinks too much, it MERGES with a neighbor."

Key Points:
  - Partition count ADAPTS to data size
  - Split when too large, merge when too small
  - No need to guess partition count upfront
  - Trade-off: more complex, cold-start problem

Used by: HBase, MongoDB, RethinkDB

================================================================================
STEP 1: CONNECT TO POSTGRESQL
================================================================================

  psql -U postgres -d postgres

================================================================================
STEP 2: SETUP FOR DYNAMIC PARTITIONING
================================================================================

-- Dynamic partitioning in PostgreSQL requires manual management
-- but we can simulate the concepts

-- Drop existing tables
DROP TABLE IF EXISTS sensor_data CASCADE;
DROP TABLE IF EXISTS sensor_partitions CASCADE;

-- Create a table to track partition metadata
-- In dynamic partitioning, the system tracks which partitions exist
CREATE TABLE sensor_partitions (
    partition_id SERIAL PRIMARY KEY,
    partition_name VARCHAR(50) NOT NULL UNIQUE,
    min_time TIMESTAMP NOT NULL,
    max_time TIMESTAMP NOT NULL,
    row_count INTEGER DEFAULT 0,
    size_bytes BIGINT DEFAULT 0,
    status VARCHAR(20) DEFAULT 'active',  -- active, splitting, merging
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create the main partitioned table (initially with one partition)
CREATE TABLE sensor_data (
    sensor_id BIGINT NOT NULL,
    event_time TIMESTAMP NOT NULL,
    temperature DECIMAL(5,2),
    humidity DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT NOW()
) PARTITION BY RANGE (event_time);

-- Initially create ONE partition (cold start problem!)
-- This simulates the "cold start" - starts with minimal partitions
CREATE TABLE sensor_data_initial PARTITION OF sensor_data
    FOR VALUES FROM (MINVALUE) TO (MAXVALUE);

-- Insert initial partition record
INSERT INTO sensor_partitions (partition_name, min_time, max_time, status)
VALUES ('sensor_data_initial', '1900-01-01', '2100-01-01', 'active');

================================================================================
STEP 3: DEMONSTRATE THE COLD-START PROBLEM
================================================================================

-- In dynamic partitioning, the database starts with ONE partition
-- All writes go to that single partition → HOT SPOT!

-- Let's simulate this problem

-- Insert some initial data
INSERT INTO sensor_data (sensor_id, event_time, temperature, humidity)
SELECT
    (random() * 100)::bigint,
    '2024-01-01'::timestamp + (random() * interval '30 days'),
    20 + random() * 15,
    40 + random() * 30
FROM generate_series(1, 100);

-- Check partition stats
SELECT
    sp.partition_name,
    sp.row_count,
    sp.status
FROM sensor_partitions sp;

-- Check actual row distribution
SELECT
    relname AS table_name,
    n_live_tup AS rows
FROM pg_stat_user_tables
WHERE relname LIKE 'sensor_data%';

-- PROBLEM: All data is in ONE partition!
-- This creates a hot spot - all writes bottleneck there

================================================================================
STEP 4: PRE-SPLITTING SOLUTION
================================================================================

-- SOLUTION: Pre-split the table into multiple partitions
-- This prevents the cold-start hot spot

-- First, drop and recreate with pre-split partitions
DROP TABLE IF EXISTS sensor_data CASCADE;
DROP TABLE IF EXISTS sensor_partitions CASCADE;

-- Recreate partition tracking
CREATE TABLE sensor_partitions (
    partition_id SERIAL PRIMARY KEY,
    partition_name VARCHAR(50) NOT NULL UNIQUE,
    min_time TIMESTAMP NOT NULL,
    max_time TIMESTAMP NOT NULL,
    row_count INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create pre-split partitions (e.g., 8 partitions for 8 days)
CREATE TABLE sensor_data PARTITION BY RANGE (event_time);

-- Create 8 daily partitions (pre-split!)
CREATE TABLE sensor_data_2024_01_01 PARTITION OF sensor_data
    FOR VALUES FROM ('2024-01-01') TO ('2024-01-02');
CREATE TABLE sensor_data_2024_01_02 PARTITION OF sensor_data
    FOR VALUES FROM ('2024-01-02') TO ('2024-01-03');
CREATE TABLE sensor_data_2024_01_03 PARTITION OF sensor_data
    FOR VALUES FROM ('2024-01-03') TO ('2024-01-04');
CREATE TABLE sensor_data_2024_01_04 PARTITION OF sensor_data
    FOR VALUES FROM ('2024-01-04') TO ('2024-01-05');
CREATE TABLE sensor_data_2024_01_05 PARTITION OF sensor_data
    FOR VALUES FROM ('2024-01-05') TO ('2024-01-06');
CREATE TABLE sensor_data_2024_01_06 PARTITION OF sensor_data
    FOR VALUES FROM ('2024-01-06') TO ('2024-01-07');
CREATE TABLE sensor_data_2024_01_07 PARTITION OF sensor_data
    FOR VALUES FROM ('2024-01-07') TO ('2024-01-08');
CREATE TABLE sensor_data_2024_01_08 PARTITION OF sensor_data
    FOR VALUES FROM ('2024-01-08') TO ('2024-01-09');

-- Record partition metadata
INSERT INTO sensor_partitions (partition_name, min_time, max_time) VALUES
    ('sensor_data_2024_01_01', '2024-01-01', '2024-01-02'),
    ('sensor_data_2024_01_02', '2024-01-02', '2024-01-03'),
    ('sensor_data_2024_01_03', '2024-01-03', '2024-01-04'),
    ('sensor_data_2024_01_04', '2024-01-04', '2024-01-05'),
    ('sensor_data_2024_01_05', '2024-01-05', '2024-01-06'),
    ('sensor_data_2024_01_06', '2024-01-06', '2024-01-07'),
    ('sensor_data_2024_01_07', '2024-01-07', '2024-01-08'),
    ('sensor_data_2024_01_08', '2024-01-08', '2024-01-09');

-- Insert data across multiple days
INSERT INTO sensor_data (sensor_id, event_time, temperature, humidity)
SELECT
    (random() * 100)::bigint,
    '2024-01-01'::timestamp + (random() * interval '7 days'),
    20 + random() * 15,
    40 + random() * 30
FROM generate_series(1, 1000);

-- Check distribution now - data is spread across partitions!
SELECT
    relname AS partition,
    n_live_tup AS rows
FROM pg_stat_user_tables
WHERE relname LIKE 'sensor_data_2024%'
ORDER BY relname;

-- Now data is distributed! Pre-splitting solved the cold-start problem

================================================================================
STEP 5: DEMONSTRATE PARTITION SPLITTING
================================================================================

-- In dynamic partitioning, when a partition grows too large,
-- it SPLITS into two partitions

-- Let's simulate this by manually creating a new partition

-- First, let's see the current partition sizes
SELECT
    relname AS partition,
    n_live_tup AS rows,
    pg_total_relation_size(relid) AS size_bytes
FROM pg_stat_user_tables
WHERE relname LIKE 'sensor_data_2024%'
ORDER BY n_live_tup DESC;

-- Simulate: A partition has grown too large, need to split
-- Example: Split sensor_data_2024_01_01 into two

-- Step 1: Create new partition for the split
CREATE TABLE sensor_data_2024_01_01a PARTITION OF sensor_data
    FOR VALUES FROM ('2024-01-01') TO ('2024-01-01 12:00:00');

CREATE TABLE sensor_data_2024_01_01b PARTITION OF sensor_data
    FOR VALUES FROM ('2024-01-01 12:00:00') TO ('2024-01-02');

-- Step 2: Detach old partition (the one being split)
ALTER TABLE sensor_data DETACH PARTITION sensor_data_2024_01_01;

-- Step 3: Move data to new partitions (this is what the database does)
-- In real DB, this happens automatically
INSERT INTO sensor_data_2024_01_01a
SELECT * FROM sensor_data_2024_01_01
WHERE event_time < '2024-01-01 12:00:00';

INSERT INTO sensor_data_2024_01_01b
SELECT * FROM sensor_data_2024_01_01
WHERE event_time >= '2024-01-01 12:00:00';

-- Step 4: Drop old partition
DROP TABLE sensor_data_2024_01_01;

-- Step 5: Update metadata
UPDATE sensor_partitions
SET partition_name = 'sensor_data_2024_01_01a', max_time = '2024-01-01 12:00:00'
WHERE partition_name = 'sensor_data_2024_01_01';

INSERT INTO sensor_partitions (partition_name, min_time, max_time)
VALUES ('sensor_data_2024_01_01b', '2024-01-01 12:00:00', '2024-01-02');

-- Verify the split worked
SELECT
    relname AS partition,
    n_live_tup AS rows
FROM pg_stat_user_tables
WHERE relname LIKE 'sensor_data_2024%'
ORDER BY relname;

-- KEY INSIGHT: The original partition SPLIT into two!
-- This is what dynamic partitioning does automatically

================================================================================
STEP 6: DEMONSTRATE PARTITION MERGING
================================================================================

-- In dynamic partitioning, when a partition shrinks too small,
-- it MERGES with a neighbor

-- Let's simulate merging two small partitions

-- Create two small partitions for demo
CREATE TABLE sensor_data_2024_01_10 PARTITION OF sensor_data
    FOR VALUES FROM ('2024-01-10') TO ('2024-01-11');

CREATE TABLE sensor_data_2024_01_11 PARTITION OF sensor_data
    FOR VALUES FROM ('2024-01-11') TO ('2024-01-12');

-- Insert very little data (simulating low activity)
INSERT INTO sensor_data_2024_01_10 (sensor_id, event_time, temperature, humidity)
VALUES (1, '2024-01-10 10:00:00', 22.0, 50.0);

INSERT INTO sensor_data_2024_01_11 (sensor_id, event_time, temperature, humidity)
VALUES (2, '2024-01-11 10:00:00', 23.0, 51.0);

-- Both partitions are small - merge them!
-- Step 1: Create merged partition
CREATE TABLE sensor_data_2024_01_10_11 PARTITION OF sensor_data
    FOR VALUES FROM ('2024-01-10') TO ('2024-01-12');

-- Step 2: Detach old partitions
ALTER TABLE sensor_data DETACH PARTITION sensor_data_2024_01_10;
ALTER TABLE sensor_data DETACH PARTITION sensor_data_2024_01_11;

-- Step 3: Move data
INSERT INTO sensor_data_2024_01_10_11 SELECT * FROM sensor_data_2024_01_10;
INSERT INTO sensor_data_2024_01_10_11 SELECT * FROM sensor_data_2024_01_11;

-- Step 4: Drop old partitions
DROP TABLE sensor_data_2024_01_10;
DROP TABLE sensor_data_2024_01_11;

-- Verify merge
SELECT
    relname AS partition,
    n_live_tup AS rows
FROM pg_stat_user_tables
WHERE relname LIKE 'sensor_data_2024%'
ORDER BY relname;

-- KEY INSIGHT: Two small partitions MERGED into one!
-- This is what dynamic partitioning does automatically

================================================================================
STEP 7: COMPARE FIXED VS DYNAMIC PARTITIONING
================================================================================

-- Let's create a comparison to show the differences

-- FIXED: Partition count doesn't change
--   - Pros: Simple, predictable
--   - Cons: Must choose count upfront, can't adapt

-- DYNAMIC: Partition count changes
--   - Pros: Adapts to data size, no upfront guessing
--   - Cons: More complex, split/merge overhead

-- Create both to compare
DROP TABLE IF EXISTS fixed_users CASCADE;
DROP TABLE IF EXISTS dynamic_users CASCADE;

-- Fixed: 4 partitions, forever
CREATE TABLE fixed_users (
    user_id BIGSERIAL,
    user_uuid UUID DEFAULT gen_random_uuid(),
    username VARCHAR(50)
) PARTITION BY HASH (user_uuid);

CREATE TABLE fixed_users_p0 PARTITION OF fixed_users FOR VALUES WITH (MODULUS 4, REMAINDER 0);
CREATE TABLE fixed_users_p1 PARTITION OF fixed_users FOR VALUES WITH (MODULUS 4, REMAINDER 1);
CREATE TABLE fixed_users_p2 PARTITION OF fixed_users FOR VALUES WITH (MODULUS 4, REMAINDER 2);
CREATE TABLE fixed_users_p3 PARTITION OF fixed_users FOR VALUES WITH (MODULUS 4, REMAINDER 3);

-- Dynamic: Start with few, split/merge as needed
CREATE TABLE dynamic_users (
    user_id BIGSERIAL,
    user_uuid UUID DEFAULT gen_random_uuid(),
    username VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
) PARTITION BY RANGE (user_id);

-- Start with 1 partition (cold start!)
CREATE TABLE dynamic_users_1 PARTITION OF dynamic_users
    FOR VALUES FROM (1) TO (1000001);

-- Insert data and observe (in real DB, it would auto-split)
INSERT INTO fixed_users (username)
SELECT 'user_' || i FROM generate_series(1, 1000) i;

INSERT INTO dynamic_users (username)
SELECT 'user_' || i FROM generate_series(1, 1000) i;

-- Compare: Fixed has stable 4 partitions
SELECT 'Fixed: 4 partitions always' AS strategy,
       COUNT(*) AS partition_count
FROM pg_tables
WHERE tablename LIKE 'fixed_users_p%';

-- Dynamic has 1 partition (but would split with more data)
SELECT 'Dynamic: Started with 1, can split' AS strategy,
       COUNT(*) AS partition_count
FROM pg_tables
WHERE tablename LIKE 'dynamic_users%'
AND tablename LIKE '%_1';

================================================================================
STEP 8: REAL-WORLD PATTERN - TIME-BASED DYNAMIC PARTITIONING
================================================================================

-- Most common use case: Time-series data with dynamic partitioning

DROP TABLE IF EXISTS time_series_data CASCADE;

CREATE TABLE time_series_data (
    id BIGSERIAL,
    event_time TIMESTAMP NOT NULL,
    metric_name VARCHAR(50) NOT NULL,
    metric_value DECIMAL(10,2) NOT NULL,
    tags JSONB
) PARTITION BY RANGE (event_time);

-- Pre-create partitions for next 7 days
FOR day IN 0..6 LOOP
    EXECUTE format('
        CREATE TABLE time_series_data_%s PARTITION OF time_series_data
        FOR VALUES FROM (%L) TO (%L)',
        to_char(CURRENT_DATE + day, 'YYYY_MM_DD'),
        CURRENT_DATE + day,
        CURRENT_DATE + day + 1
    );
END LOOP;

-- Insert sample time-series data
INSERT INTO time_series_data (event_time, metric_name, metric_value)
SELECT
    CURRENT_DATE + (random() * interval '7 days'),
    (ARRAY['cpu', 'memory', 'disk', 'network'])[floor(random() * 4 + 1)],
    random() * 100
FROM generate_series(1, 1000);

-- Check distribution
SELECT
    relname AS partition,
    n_live_tup AS rows
FROM pg_stat_user_tables
WHERE relname LIKE 'time_series_data_2%'
ORDER BY relname;

-- This is how databases like HBase and MongoDB handle time-series!

================================================================================
SUMMARY: DYNAMIC PARTITIONING
================================================================================

✅ DYNAMIC PARTITIONING PROS:
  - Adapts to data size automatically
  - No need to guess partition count upfront
  - Good for growing datasets

❌ DYNAMIC PARTITIONING CONS:
  - Cold-start problem (starts with one partition)
  - Split/merge overhead
  - More complex to manage

⚠️  KEY SOLUTION - PRE-SPLITTING:
  Create initial partitions at table creation time
  to avoid the cold-start hot spot

📌 WHEN TO USE:
  - Time-series data (auto-split by time)
  - Unknown data growth patterns
  - When you can't predict partition count

================================================================================
NEXT STEPS:
================================================================================

1. Try Exercise 3: Consistent Hashing (03_consistent_hashing.sql)
   - See a different approach to rebalancing

2. Read DDIA pp. 207-209 for more theory

EOF
