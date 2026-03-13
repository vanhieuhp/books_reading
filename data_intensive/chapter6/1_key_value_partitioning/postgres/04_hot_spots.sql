================================================================================
  PostgreSQL Hot Spot Solutions - DDIA Chapter 6.1
  Handling skewed workloads in partitioned databases
================================================================================

WHAT YOU'LL LEARN:
  ✅ How to detect hot keys (keys with disproportionately high traffic)
  ✅ Key splitting as a solution
  ✅ Read/write trade-offs
  ✅ When to apply splitting

================================================================================
PART 1: UNDERSTANDING HOT SPOTS
================================================================================

A "hot spot" is a partition that receives disproportionately more traffic
than other partitions. This can happen with:

1. Sequential keys (auto-increment IDs) - all new writes go to last partition
2. Popular keys (celebrity user in social network)
3. Time-based keys - "today" gets all the writes
4. Zipfian distribution - some keys are vastly more popular

-- Let's create a scenario with a hot spot
DROP TABLE IF EXISTS page_views CASCADE;

CREATE TABLE page_views (
    id BIGSERIAL,
    page_id BIGINT NOT NULL,
    view_time TIMESTAMP DEFAULT NOW(),
    user_id BIGINT,
    duration INTEGER
) PARTITION BY HASH (page_id);

-- Create partitions
CREATE TABLE page_views_p0 PARTITION OF page_views
    FOR VALUES WITH (MODULUS 4, REMAINDER 0);

CREATE TABLE page_views_p1 PARTITION OF page_views
    FOR VALUES WITH (MODULUS 4, REMAINDER 1);

CREATE TABLE page_views_p2 PARTITION OF page_views
    FOR VALUES WITH (MODULUS 4, REMAINDER 2);

CREATE TABLE page_views_p3 PARTITION OF page_views
    FOR VALUES WITH (MODULUS 4, REMAINDER 3);

-- Simulate skewed data: page_id = 1 is VERY popular (hot key!)
-- 50% of all views go to page_id = 1
INSERT INTO page_views (page_id, user_id, duration)
SELECT
    CASE
        WHEN random() < 0.5 THEN 1  -- HOT page!
        ELSE (random() * 1000)::BIGINT
    END AS page_id,
    (random() * 10000)::BIGINT AS user_id,
    (random() * 300)::INTEGER AS duration
FROM generate_series(1, 10000);

-- Check distribution - one partition will have WAY more data!
SELECT
    relname AS partition,
    n_live_tup AS rows,
    ROUND(100.0 * n_live_tup / SUM(n_live_tup) OVER(), 2) AS percentage
FROM pg_stat_user_tables
WHERE relname LIKE 'page_views_p%'
ORDER BY rows DESC;

-- Result: One partition might have 50%+ of all rows!

================================================================================
PART 2: DETECTING HOT KEYS
================================================================================

-- Method 1: Query partition sizes
SELECT
    relname AS partition_name,
    n_live_tup AS row_count
FROM pg_stat_user_tables
WHERE relname LIKE 'page_views_p%'
ORDER BY n_live_tup DESC;

-- Method 2: Identify popular keys within each partition
-- This helps identify WHICH keys are hot

-- Create a view to see key distribution
CREATE OR REPLACE VIEW hot_keys_view AS
SELECT
    page_id,
    COUNT(*) AS view_count,
    COUNT(*) * 100.0 / SUM(COUNT(*)) OVER() AS percentage
FROM page_views
GROUP BY page_id
ORDER BY view_count DESC
LIMIT 20;

-- Check for hot keys
SELECT * FROM hot_keys_view;

-- Method 3: Monitor query patterns (in production)
-- Look for repeated queries on specific keys

================================================================================
PART 3: SOLUTION 1 - KEY SPLITTING (N+1 PATTERN)
================================================================================

The idea: Instead of one hot key, split it into N "virtual" keys.

Instead of: page_id = 1
Use: page_id = 1_0, page_id = 1_1, page_id = 1_2, ..., page_id = 1_9

-- Create a new table with split keys
DROP TABLE IF EXISTS page_views_split CASCADE;

CREATE TABLE page_views_split (
    id BIGSERIAL,
    page_id VARCHAR(50) NOT NULL,  -- Changed to TEXT to allow "1_0", "1_1", etc.
    view_time TIMESTAMP DEFAULT NOW(),
    user_id BIGINT,
    duration INTEGER
) PARTITION BY HASH (page_id);

-- Create partitions
CREATE TABLE page_views_split_p0 PARTITION OF page_views_split
    FOR VALUES WITH (MODULUS 4, REMAINDER 0);

CREATE TABLE page_views_split_p1 PARTITION OF page_views_split
    FOR VALUES WITH (MODULUS 4, REMAINDER 1);

CREATE TABLE page_views_split_p2 PARTITION OF page_views_split
    FOR VALUES WITH (MODULUS 4, REMAINDER 2);

CREATE TABLE page_views_split_p3 PARTITION OF page_views_split
    FOR VALUES WITH (MODULUS 4, REMAINDER 3);

-- Insert data with key splitting for hot keys
-- For page_id = 1, we spread across 10 "sub-keys"
INSERT INTO page_views_split (page_id, user_id, duration)
SELECT
    CASE
        WHEN page_id = 1 THEN
            -- Split hot key into 10 parts
            '1_' || (random() * 9)::INTEGER::TEXT
        ELSE
            page_id::TEXT
    END AS page_id,
    user_id,
    duration
FROM (
    SELECT
        CASE
            WHEN random() < 0.5 THEN 1::BIGINT
            ELSE (random() * 1000)::BIGINT
        END AS page_id,
        (random() * 10000)::BIGINT AS user_id,
        (random() * 300)::INTEGER AS duration
    FROM generate_series(1, 10000)
) AS data;

-- Check distribution - NOW it's even!
SELECT
    relname AS partition,
    n_live_tup AS rows,
    ROUND(100.0 * n_live_tup / SUM(n_live_tup) OVER(), 2) AS percentage
FROM pg_stat_user_tables
WHERE relname LIKE 'page_views_split_p%'
ORDER BY rows DESC;

-- But to read ALL views for page 1, we need to query all split keys!
SELECT * FROM page_views_split
WHERE page_id IN ('1_0', '1_1', '1_2', '1_3', '1_4', '1_5', '1_6', '1_7', '1_8', '1_9');

-- This is the TRADE-OFF: reads are slower, but writes are distributed!

================================================================================
PART 4: SOLUTION 2 - READ REPLICAS (CACHE LAYER)
================================================================================

For READ-heavy hot spots, use caching/replicas:

-- Create a materialized view for the hot key
CREATE MATERIALIZED VIEW page_1_views AS
SELECT * FROM page_views WHERE page_id = 1;

-- Refresh periodically
REFRESH MATERIALIZED VIEW CONCURRENTLY page_1_views;

-- Or create a summary table
DROP TABLE IF EXISTS page_view_summary;
CREATE TABLE page_view_summary AS
SELECT
    page_id,
    COUNT(*) AS total_views,
    AVG(duration) AS avg_duration,
    COUNT(DISTINCT user_id) AS unique_users,
    MAX(view_time) AS last_view
FROM page_views
GROUP BY page_id;

-- Query summary instead of raw data
SELECT * FROM page_view_summary WHERE page_id = 1;

================================================================================
PART 5: SOLUTION 3 - REBALANCING PARTITIONS
================================================================================

When one partition is overloaded, add more partitions!

-- Current: 4 partitions
-- Problem: Partition 2 has 50% of data

-- Solution: Add 4 more partitions (now 8 total)
-- This changes the hash modulus!

-- Create new partitions for 8-way split
CREATE TABLE page_views_p4 PARTITION OF page_views
    FOR VALUES WITH (MODULUS 8, REMAINDER 4);

CREATE TABLE page_views_p5 PARTITION OF page_views
    FOR VALUES WITH (MODULUS 8, REMAINDER 5);

CREATE TABLE page_views_p6 PARTITION OF page_views
    FOR VALUES WITH (MODULUS 8, REMAINDER 6);

CREATE TABLE page_views_p7 PARTITION OF page_views
    FOR VALUES WITH (MODULUS 8, REMAINDER 7);

-- Note: This requires redistributing existing data!
-- In production, you'd use pg_repack or online rebalancing tools

-- Check new distribution
SELECT
    relname AS partition,
    n_live_tup AS rows
FROM pg_stat_user_tables
WHERE relname LIKE 'page_views_p%'
ORDER BY rows DESC;

================================================================================
PART 6: SOLUTION 4 - APPLICATION-LEVEL ROUTING
================================================================================

Use a router that sends traffic to different partitions:

-- Example: Random routing to split hot key reads
/*
Application Logic (pseudocode):

function get_page_views(page_id):
    if page_id == HOT_PAGE_ID:
        # Randomly pick one of N splits
        split_id = random(0, N-1)
        return query("SELECT * FROM page_views WHERE page_id = ?_?", page_id, split_id)
    else:
        return query("SELECT * FROM page_views WHERE page_id = ?", page_id)

function write_page_view(page_id):
    if page_id == HOT_PAGE_ID:
        # Round-robin across splits
        split_id = next_split()
        return write("INSERT INTO page_views VALUES (?, ?_?, ...)", page_id, split_id)
    else:
        return write("INSERT INTO page_views VALUES (?, ...)", page_id)
*/

-- This requires application-level logic but gives you control

================================================================================
PART 7: PRACTICAL EXAMPLE - SOCIAL MEDIA USER
================================================================================

Scenario: User 42 is a "celebrity" with millions of followers
- All reads for user 42 go to one partition
- That partition is overloaded with reads

Solution: Split user 42 into multiple partitions

-- Create user posts with splitting support
DROP TABLE IF EXISTS user_timeline CASCADE;

CREATE TABLE user_timeline (
    id BIGSERIAL,
    user_id VARCHAR(50) NOT NULL,  -- Can be "42_0", "42_1", etc.
    post_id BIGINT NOT NULL,
    content TEXT,
    created_at TIMESTAMP DEFAULT NOW()
) PARTITION BY HASH (user_id);

-- Create partitions
CREATE TABLE user_timeline_p0 PARTITION OF user_timeline
    FOR VALUES WITH (MODULUS 4, REMAINDER 0);

CREATE TABLE user_timeline_p1 PARTITION OF user_timeline
    FOR VALUES WITH (MODULUS 4, REMAINDER 1);

CREATE TABLE user_timeline_p2 PARTITION OF user_timeline
    FOR VALUES WITH (MODULUS 4, REMAINDER 2);

CREATE TABLE user_timeline_p3 PARTITION OF user_timeline
    FOR VALUES WITH (MODULUS 4, REMAINDER 3);

-- Write function that automatically splits hot users
-- In PostgreSQL, we can use a function

CREATE OR REPLACE FUNCTION get_partition_key(
    p_user_id BIGINT,
    p_is_hot BOOLEAN DEFAULT FALSE,
    p_hot_split_count INTEGER DEFAULT 10
) RETURNS TEXT AS $$
BEGIN
    IF p_is_hot THEN
        -- Split into multiple keys
        RETURN p_user_id || '_' || (random() * (p_hot_split_count - 1))::INTEGER;
    ELSE
        RETURN p_user_id::TEXT;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Insert normal user
INSERT INTO user_timeline (user_id, post_id, content)
VALUES
    (get_partition_key(1, false), 1, 'Normal user post'),
    (get_partition_key(2, false), 2, 'Another normal user');

-- Insert hot user (will be split across multiple keys)
-- Note: In real app, you'd use the function with is_hot=true
INSERT INTO user_timeline (user_id, post_id, content)
SELECT
    '42_' || generate_series % 10 AS user_id,  -- Split user 42
    generate_series AS post_id,
    'Celebrity post ' || generate_series AS content
FROM generate_series(1, 1000);

-- Check distribution
SELECT
    relname AS partition,
    n_live_tup AS rows
FROM pg_stat_user_tables
WHERE relname LIKE 'user_timeline_p%'
ORDER BY rows DESC;

-- To read all posts by user 42, query all splits:
SELECT * FROM user_timeline
WHERE user_id LIKE '42_%'
ORDER BY created_at DESC
LIMIT 100;

================================================================================
SUMMARY: HOT SPOT SOLUTIONS
================================================================================

✅ DETECTION:
  - Monitor partition sizes
  - Identify keys with disproportionate traffic pg
  - Use_stat_user_tables

✅ SOLUTIONS:
  1. Key Splitting: Divide hot key into N sub-keys
     - Writes: Distributed ✓
     - Reads: Must query all N keys ✗

  2. Read Replicas/Cache: Serve reads from cache
     - Reads: Fast ✓
     - Complexity: More infrastructure ✗

  3. Rebalancing: Add more partitions
     - Distribution: Even ✓
     - Complexity: Data migration ✗

  4. Application Routing: Custom logic
     - Control: Full ✓
     - Complexity: Application changes ✗

📌 WHEN TO USE WHAT:
  - Write-heavy hot spots → Key splitting
  - Read-heavy hot spots → Caching/replicas
  - General overload → Rebalancing
  - Need control → Application routing

📌 KEY INSIGHT FROM DDIA:
  "Today, most data systems are not able to automatically compensate for
   such a highly skewed workload, so it's the responsibility of the
   application to reduce the skew."

================================================================================
NEXT STEPS:
================================================================================

1. Run all exercises in psql to see partition pruning in action
2. Try different partition counts and data distributions
3. Monitor with EXPLAIN ANALYZE to see which partitions are scanned

Happy partitioning! 🚀

EOF
