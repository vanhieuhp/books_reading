================================================================================
  PostgreSQL List & Compound Partitioning - DDIA Chapter 6.1
  The "Best of Both Worlds" approach (Cassandra-style)
================================================================================

WHAT YOU'LL LEARN:
  ✅ List partitioning for categorical data
  ✅ Compound keys: hash partition key + sorted clustering key
  ✅ How to get efficient range queries WITHIN partitions
  ✅ Real-world use cases (social media, IoT, time-series)

================================================================================
PART 1: LIST PARTITIONING
================================================================================

List partitioning is great when you have discrete categories.

-- Example: E-commerce with regional data
DROP TABLE IF EXISTS products CASCADE;

CREATE TABLE products (
    product_id BIGSERIAL,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    region VARCHAR(20) NOT NULL,
    price DECIMAL(10,2),
    stock INTEGER DEFAULT 0
) PARTITION BY LIST (region);

-- Create partitions for specific regions
CREATE TABLE products_us PARTITION OF products
    FOR VALUES IN ('US', 'US-East', 'US-West', 'US-Central');

CREATE TABLE products_eu PARTITION OF products
    FOR VALUES IN ('EU', 'EU-West', 'EU-Central', 'EU-North');

CREATE TABLE products_asia PARTITION OF products
    FOR VALUES IN ('ASIA', 'APAC', 'China', 'Japan', 'India');

CREATE TABLE products_default PARTITION OF products
    DEFAULT;

-- Insert sample data
INSERT INTO products (name, category, region, price, stock)
VALUES
    ('Laptop', 'electronics', 'US', 999.99, 50),
    ('Laptop', 'electronics', 'EU', 899.99, 30),
    ('Phone', 'electronics', 'US', 699.99, 100),
    ('Phone', 'electronics', 'China', 599.99, 80),
    ('Shirt', 'clothing', 'US', 29.99, 200),
    ('Shirt', 'clothing', 'EU', 34.99, 150);

-- Query optimization: only one partition!
EXPLAIN ANALYZE
SELECT * FROM products WHERE region = 'US';

-- Must scan all partitions (region not in filter)
EXPLAIN ANALYZE
SELECT * FROM products WHERE category = 'electronics';

================================================================================
PART 2: COMPOUND KEYS - THE CASSANDRA APPROACH
================================================================================

This is the KEY CONCEPT from DDIA:
- Partition key → determines which partition (hashed)
- Clustering key → sorted within each partition

PostgreSQL doesn't have native "compound primary keys" like Cassandra,
but we can simulate this pattern!

-- ============================================================
-- USE CASE: Social Media Posts (like Cassandra)
-- ============================================================
-- Partition key: user_id (hashed) → which partition
-- Clustering key: created_at (sorted) → ordered within partition

DROP TABLE IF EXISTS user_posts CASCADE;

CREATE TABLE user_posts (
    id BIGSERIAL,
    user_id BIGINT NOT NULL,
    post_id BIGINT NOT NULL,
    content TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    likes INTEGER DEFAULT 0
) PARTITION BY HASH (user_id);

-- Create partitions
CREATE TABLE user_posts_p0 PARTITION OF user_posts
    FOR VALUES WITH (MODULUS 4, REMAINDER 0);

CREATE TABLE user_posts_p1 PARTITION OF user_posts
    FOR VALUES WITH (MODULUS 4, REMAINDER 1);

CREATE TABLE user_posts_p2 PARTITION OF user_posts
    FOR VALUES WITH (MODULUS 4, REMAINDER 2);

CREATE TABLE user_posts_p3 PARTITION OF user_posts
    FOR VALUES WITH (MODULUS 4, REMAINDER 3);

-- Create index on (user_id, created_at) for efficient range queries
CREATE INDEX idx_user_posts_user_time ON user_posts (user_id, created_at);

-- Insert posts for a few users
INSERT INTO user_posts (user_id, post_id, content, created_at, likes)
SELECT
    (random() * 10)::BIGINT AS user_id,  -- 0-10 users
    generate_series AS post_id,
    'Post content ' || generate_series AS content,
    '2024-01-01'::TIMESTAMP + (random() * 30)::INTEGER * INTERVAL '1 day' AS created_at,
    (random() * 100)::INTEGER AS likes
FROM generate_series(1, 1000);

-- ============================================================
-- THE MAGIC: Efficient range queries WITHIN a user
-- ============================================================

-- Find all posts for user 5, sorted by time
-- This is EFFICIENT because user_id is the partition key!
EXPLAIN ANALYZE
SELECT * FROM user_posts
WHERE user_id = 5
ORDER BY created_at DESC
LIMIT 10;

-- This only scans ONE partition (where user_id = 5 hashes to)

-- Range query within a user's posts
EXPLAIN ANALYZE
SELECT * FROM user_posts
WHERE user_id = 3
  AND created_at BETWEEN '2024-01-10' AND '2024-01-20';

-- ============================================================
-- USE CASE: IoT Sensor Data
-- ============================================================

DROP TABLE IF EXISTS sensor_readings CASCADE;

CREATE TABLE sensor_readings (
    id BIGSERIAL,
    sensor_id BIGINT NOT NULL,
    reading_time TIMESTAMP NOT NULL,
    temperature DECIMAL(5,2),
    humidity DECIMAL(5,2),
    battery_level DECIMAL(5,2)
) PARTITION BY HASH (sensor_id);

-- Create partitions
CREATE TABLE sensor_readings_p0 PARTITION OF sensor_readings
    FOR VALUES WITH (MODULUS 4, REMAINDER 0);

CREATE TABLE sensor_readings_p1 PARTITION OF sensor_readings
    FOR VALUES WITH (MODULUS 4, REMAINDER 1);

CREATE TABLE sensor_readings_p2 PARTITION OF sensor_readings
    FOR VALUES WITH (MODULUS 4, REMAINDER 2);

CREATE TABLE sensor_readings_p3 PARTITION OF sensor_readings
    FOR VALUES WITH (MODULUS 4, REMAINDER 3);

-- Create index for efficient time-range queries within a sensor
CREATE INDEX idx_sensor_time ON sensor_readings (sensor_id, reading_time);

-- Simulate IoT data: 100 sensors, 1000 readings each
INSERT INTO sensor_readings (sensor_id, reading_time, temperature, humidity, battery_level)
SELECT
    (random() * 100)::BIGINT AS sensor_id,
    '2024-01-01'::TIMESTAMP + (random() * 30)::INTEGER * INTERVAL '1 hour'
        + (random() * 3600)::INTEGER * INTERVAL '1 second' AS reading_time,
    20 + (random() * 15)::DECIMAL(5,2) AS temperature,
    40 + (random() * 40)::DECIMAL(5,2) AS humidity,
    100 - (random() * 30)::DECIMAL(5,2) AS battery_level
FROM generate_series(1, 10000);

-- Query: All readings for sensor 42 in a time range
-- EFFICIENT! Only one partition, indexed by time
EXPLAIN ANALYZE
SELECT * FROM sensor_readings
WHERE sensor_id = 42
  AND reading_time BETWEEN '2024-01-10' AND '2024-01-15'
ORDER BY reading_time;

================================================================================
PART 3: SUBPARTITIONING (Composite Partitioning)
================================================================================

PostgreSQL supports subpartitioning - partition by one key, then sub-partition.

-- Example: Partition by region, then subpartition by month
DROP TABLE IF EXISTS sales CASCADE;

CREATE TABLE sales (
    sale_id BIGSERIAL,
    sale_date DATE NOT NULL,
    region VARCHAR(20) NOT NULL,
    product_id BIGINT,
    amount DECIMAL(10,2)
) PARTITION BY RANGE (sale_date);

-- Create partitions by month
CREATE TABLE sales_2024_q1 PARTITION OF sales
    FOR VALUES FROM ('2024-01-01') TO ('2024-04-01')
    PARTITION BY LIST (region);

-- Subpartition Q1 by region
CREATE TABLE sales_2024_q1_us PARTITION OF sales_2024_q1
    FOR VALUES IN ('US', 'US-East', 'US-West');

CREATE TABLE sales_2024_q1_eu PARTITION OF sales_2024_q1
    FOR VALUES IN ('EU', 'UK', 'Germany');

CREATE TABLE sales_2024_q1_asia PARTITION OF sales_2024_q1
    FOR VALUES IN ('China', 'Japan', 'India');

-- Create Q2 partition
CREATE TABLE sales_2024_q2 PARTITION OF sales
    FOR VALUES FROM ('2024-04-01') TO ('2024-07-01')
    PARTITION BY LIST (region);

-- Insert sample data
INSERT INTO sales (sale_date, region, product_id, amount)
VALUES
    ('2024-01-15', 'US', 1, 100.00),
    ('2024-02-20', 'EU', 2, 150.00),
    ('2024-03-10', 'China', 3, 200.00),
    ('2024-04-05', 'US', 1, 120.00),
    ('2024-05-15', 'UK', 2, 180.00);

-- Check the partition structure
SELECT
    schemaname,
    tablename
FROM pg_tables
WHERE tablename LIKE 'sales%'
ORDER BY tablename;

-- Query: Sales in US for Q1
EXPLAIN ANALYZE
SELECT * FROM sales
WHERE region = 'US'
  AND sale_date BETWEEN '2024-01-01' AND '2024-03-31';

================================================================================
PART 4: REAL-WORLD PATTERNS
================================================================================

-- ============================================================
-- PATTERN 1: Time-series with entity ID (Most Common!)
-- ============================================================
-- Great for: logs, events, metrics
-- Partition by: (year, entity_id)
-- Sort by: timestamp

DROP TABLE IF EXISTS application_logs CASCADE;

CREATE TABLE application_logs (
    id BIGSERIAL,
    service_name VARCHAR(50) NOT NULL,
    log_time TIMESTAMP NOT NULL,
    level VARCHAR(10) NOT NULL,
    message TEXT
) PARTITION BY HASH (service_name);

-- Create partitions
CREATE TABLE logs_p0 PARTITION OF application_logs
    FOR VALUES WITH (MODULUS 4, REMAINDER 0);

CREATE TABLE logs_p1 PARTITION OF application_logs
    FOR VALUES WITH (MODULUS 4, REMAINDER 1);

CREATE TABLE logs_p2 PARTITION OF application_logs
    FOR VALUES WITH (MODULUS 4, REMAINDER 2);

CREATE TABLE logs_p3 PARTITION OF application_logs
    FOR VALUES WITH (MODULUS 4, REMAINDER 3);

-- Index for time-range queries within a service
CREATE INDEX idx_logs_service_time ON application_logs (service_name, log_time);

-- ============================================================
-- PATTERN 2: Multi-tenant applications
-- ============================================================
-- Partition by tenant_id to isolate data and reduce contention

DROP TABLE IF EXISTS tenant_data CASCADE;

CREATE TABLE tenant_data (
    id BIGSERIAL,
    tenant_id BIGINT NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id BIGINT NOT NULL,
    data JSONB,
    created_at TIMESTAMP DEFAULT NOW()
) PARTITION BY HASH (tenant_id);

-- Create partitions
CREATE TABLE tenant_data_p0 PARTITION OF tenant_data
    FOR VALUES WITH (MODULUS 4, REMAINDER 0);

CREATE TABLE tenant_data_p1 PARTITION OF tenant_data
    FOR VALUES WITH (MODULUS 4, REMAINDER 1);

CREATE TABLE tenant_data_p2 PARTITION OF tenant_data
    FOR VALUES WITH (MODULUS 4, REMAINDER 2);

CREATE TABLE tenant_data_p3 PARTITION OF tenant_data
    FOR VALUES WITH (MODULUS 4, REMAINDER 3);

-- Index for tenant + entity lookups
CREATE INDEX idx_tenant_entity ON tenant_data (tenant_id, entity_type, entity_id);

================================================================================
SUMMARY: COMPOUND/CASSANDRA-STYLE PARTITIONING
================================================================================

✅ BEST OF BOTH WORLDS:
  - Hash on partition key → even distribution, no hot spots
  - Sorted on clustering key → efficient range queries WITHIN partition

❌ TRADE-OFFS:
  - Cross-partition queries are slow (must scan all partitions)
  - Need to design based on access patterns

📌 CASSANDRA-STYLE DESIGN:
  1. Identify your most common query pattern
  2. Use that field as partition key (hashed)
  3. Use time-ordered field as clustering key (sorted)
  4. Create indexes for other common queries

📌 REAL-WORLD EXAMPLES:
  - User posts: PRIMARY KEY (user_id, created_at)
  - Sensor data: PRIMARY KEY (sensor_id, timestamp)
  - Order items: PRIMARY KEY (order_id, product_id)
  - Event logs: PRIMARY KEY (service, timestamp)

================================================================================
NEXT STEPS:
================================================================================

1. Try Exercise 4: Hot Spot Solutions (04_hot_spots.sql)
2. Compare the query plans
3. Design your own partitioning strategy!

EOF
