================================================================================
  PostgreSQL Range Partitioning - DDIA Chapter 6.1
  Learn by doing: Hands-on partitioning with PostgreSQL
================================================================================

WHAT YOU'LL LEARN:
  ✅ How range partitioning works in PostgreSQL
  ✅ Why it's great for time-series data
  ✅ The hot spot problem with sequential keys
  ✅ How to prefix keys to avoid hot spots

PREREQUISITES:
  - PostgreSQL 10+ (native partitioning support)
  - psql or any PostgreSQL client

================================================================================
STEP 1: CONNECT TO POSTGRESQL
================================================================================

First, connect to your PostgreSQL database:

  psql -U postgres -d postgres

Or if you have a specific database:

  psql -U postgres -d mydb

================================================================================
STEP 2: CREATE RANGE-PARTITIONED TABLE
================================================================================

Run the following SQL commands:

-- Drop table if exists (for clean restart)
DROP TABLE IF EXISTS events CASCADE;

-- Create parent table with PARTITION BY RANGE
CREATE TABLE events (
    event_id BIGSERIAL,
    event_time TIMESTAMP NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    user_id BIGINT NOT NULL,
    payload JSONB,
    created_at TIMESTAMP DEFAULT NOW()
) PARTITION BY RANGE (event_time);

-- Create partitions for different time ranges
CREATE TABLE events_2024_jan PARTITION OF events
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE events_2024_feb PARTITION OF events
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

CREATE TABLE events_2024_mar PARTITION OF events
    FOR VALUES FROM ('2024-03-01') TO ('2024-04-01');

CREATE TABLE events_default PARTITION OF events
    DEFAULT;

-- Create indexes for performance
CREATE INDEX idx_events_time ON events (event_time);
CREATE INDEX idx_events_user ON events (user_id);
CREATE INDEX idx_events_type ON events (event_type);

================================================================================
STEP 3: INSERT DATA AND OBSERVE PARTITIONING
================================================================================

-- Insert data for January
INSERT INTO events (event_time, event_type, user_id, payload)
VALUES
    ('2024-01-15 10:00:00', 'login', 1, '{"browser": "chrome"}'),
    ('2024-01-20 14:30:00', 'purchase', 2, '{"amount": 99.99}'),
    ('2024-01-25 09:15:00', 'click', 1, '{"page": "/home"}');

-- Insert data for February
INSERT INTO events (event_time, event_type, user_id, payload)
VALUES
    ('2024-02-10 11:00:00', 'login', 3, '{"browser": "firefox"}'),
    ('2024-02-15 16:45:00', 'view', 2, '{"product_id": 123}');

-- Insert data for March
INSERT INTO events (event_time, event_type, user_id, payload)
VALUES
    ('2024-03-05 08:00:00', 'login', 4, '{"browser": "safari"}');

================================================================================
STEP 4: QUERY AND VERIFY PARTITION ROUTING
================================================================================

-- Check which partition data went to
SELECT
    relname AS partition_name,
    n_live_tup AS row_count
FROM pg_stat_user_tables
WHERE relname LIKE 'events%'
ORDER BY relname;

-- Explain query to see partition pruning
EXPLAIN ANALYZE
SELECT * FROM events
WHERE event_time BETWEEN '2024-01-01' AND '2024-01-31';

-- This should ONLY scan events_2024_jan partition!

-- Range query across multiple partitions
EXPLAIN ANALYZE
SELECT * FROM events
WHERE event_time BETWEEN '2024-01-15' AND '2024-02-15';

-- This should scan BOTH jan and feb partitions

================================================================================
STEP 5: THE HOT SPOT PROBLEM (Demonstration)
================================================================================

-- Create a table with sequential ID as partition key (BAD PRACTICE!)
DROP TABLE IF EXISTS orders_bad;
CREATE TABLE orders_bad (
    order_id BIGSERIAL,
    order_time TIMESTAMP DEFAULT NOW(),
    customer_id BIGINT,
    total DECIMAL(10,2)
) PARTITION BY RANGE (order_id);

-- Create partitions by order_id ranges
CREATE TABLE orders_bad_p1 PARTITION OF orders_bad
    FOR VALUES FROM (1) TO (1000001);

CREATE TABLE orders_bad_p2 PARTITION OF orders_bad
    FOR VALUES FROM (1000001) TO (2000001);

-- Problem: All NEW orders go to the LAST partition!
-- This creates a "hot spot" - one partition handles all writes

-- Simulate high-volume writes to "now"
INSERT INTO orders_bad (customer_id, total)
SELECT
    generate_series(1, 10000) AS customer_id,
    random() * 1000 AS total
RETURNING order_id, order_time;

-- Check where data landed - almost ALL in last partition!
SELECT
    relname AS partition,
    n_live_tup AS rows
FROM pg_stat_user_tables
WHERE relname LIKE 'orders_bad%';

================================================================================
STEP 6: FIX HOT SPOTS WITH KEY PREFIXING
================================================================================

-- Solution: Use a composite key that spreads writes
-- Instead of: order_id (sequential)
-- Use: (date, order_id) or (hash, order_id)

DROP TABLE IF EXISTS orders_good;
CREATE TABLE orders_good (
    id BIGSERIAL,
    partition_key TEXT,  -- e.g., "2024-01" or hashed value
    order_time TIMESTAMP DEFAULT NOW(),
    customer_id BIGINT,
    total DECIMAL(10,2)
) PARTITION BY LIST (partition_key);

-- Create partitions by date prefix
CREATE TABLE orders_2024_01 PARTITION OF orders_good
    FOR VALUES IN ('2024-01');

CREATE TABLE orders_2024_02 PARTITION OF orders_good
    FOR VALUES IN ('2024-02');

CREATE TABLE orders_2024_03 PARTITION OF orders_good
    FOR VALUES IN ('2024-03');

-- When inserting, calculate the partition key
INSERT INTO orders_good (partition_key, customer_id, total)
SELECT
    to_char(CURRENT_DATE, 'YYYY-MM') AS partition_key,  -- "2024-03"
    generate_series(1, 1000) AS customer_id,
    random() * 500 AS total;

-- Now writes are distributed by month!

================================================================================
STEP 7: MAINTENANCE - ADD NEW PARTITIONS
================================================================================

-- Add a partition for April 2024
CREATE TABLE events_2024_apr PARTITION OF events
    FOR VALUES FROM ('2024-04-01') TO ('2024-05-01');

-- Add a partition for future (unbounded)
CREATE TABLE events_2024_may PARTITION OF events
    FOR VALUES FROM ('2024-05-01') TO ('2024-06-01');

-- Or create a "catch-all" for data outside expected ranges
-- (We already created events_default above)

================================================================================
STEP 8: PARTITION MAINTENANCE
================================================================================

-- Detach a partition (make it standalone)
ALTER TABLE events DETACH PARTITION events_2024_jan;

-- Drop old partition data (archive first!)
-- ALTER TABLE events DROP PARTITION events_2024_jan;

-- Rename partition for clarity
ALTER TABLE events_2024_jan RENAME TO events_2024_01;

-- Check partition information
SELECT
    schemaname,
    tablename,
    tableowner
FROM pg_tables
WHERE tablename LIKE 'events%'
ORDER BY tablename;

================================================================================
SUMMARY: KEY INSIGHTS
================================================================================

✅ Range Partitioning PROS:
  - Efficient range queries (only relevant partitions scanned)
  - Great for time-series data with natural time ranges
  - Easy to archive/delete old data by dropping partitions

❌ Range Partitioning CONS:
  - Hot spots when using sequential keys (all writes to one partition)
  - Must pre-create partitions (or use automation)
  - Uneven data distribution possible

📌 KEY RULE:
  Choose partition key based on your QUERY PATTERN
  - Time-range queries → partition by time
  - User-based queries → partition by user_id
  - Avoid sequential keys as partition keys!

================================================================================
NEXT STEPS:
================================================================================

1. Try Exercise 2: Hash Partitioning (02_hash_partitioning.sql)
2. Read README.md for more details
3. Experiment with your own data!

EOF
