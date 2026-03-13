================================================================================
  PostgreSQL Fixed Partition Rebalancing - DDIA Chapter 6.3
  Learn by doing: Strategy 1 - Fixed Number of Partitions
================================================================================

WHAT YOU'LL LEARN:
  ✅ How fixed partition count strategy works
  ✅ Why partition boundaries never change
  ✅ How rebalancing works (partition reassignment)
  ✅ The trade-off: must choose partition count upfront

PREREQUISITES:
  - PostgreSQL 10+ (native partitioning support)
  - psql or any PostgreSQL client

================================================================================
CONCEPT: FIXED PARTITION COUNT STRATEGY
================================================================================

From DDIA (pp. 203-207):
  "Fix the number of partitions by configuring the database before adding data.
   The partition count is set at database creation time and does not change."

Key Points:
  - Partition count is FIXED forever
  - Only partition-to-node ASSIGNMENTS change
  - Rebalancing = bulk file moves between nodes
  - Trade-off: must estimate partition count upfront

Used by: Riak, Elasticsearch, Couchbase

================================================================================
STEP 1: CONNECT TO POSTGRESQL
================================================================================

  psql -U postgres -d postgres

Or:

  psql -U postgres -d mydb

================================================================================
STEP 2: CREATE FIXED PARTITIONS (THE "FIXED" PART)
================================================================================

-- Drop existing tables
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS user_nodes CASCADE;

-- Create a lookup table for node assignments (simulates cluster state)
-- This is our "routing table" - which node owns which partition
CREATE TABLE user_nodes (
    partition_id INTEGER NOT NULL,
    node_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (partition_id)
);

-- Create the main partitioned table with FIXED partitions
-- We create 8 partitions (can be hundreds in production)
CREATE TABLE users (
    user_id BIGSERIAL,
    user_uuid UUID DEFAULT gen_random_uuid(),
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
) PARTITION BY HASH (user_uuid);

-- Create FIXED partitions (partition boundaries never change!)
CREATE TABLE users_p0 PARTITION OF users FOR VALUES WITH (MODULUS 8, REMAINDER 0);
CREATE TABLE users_p1 PARTITION OF users FOR VALUES WITH (MODULUS 8, REMAINDER 1);
CREATE TABLE users_p2 PARTITION OF users FOR VALUES WITH (MODULUS 8, REMAINDER 2);
CREATE TABLE users_p3 PARTITION OF users FOR VALUES WITH (MODULUS 8, REMAINDER 3);
CREATE TABLE users_p4 PARTITION OF users FOR VALUES WITH (MODULUS 8, REMAINDER 4);
CREATE TABLE users_p5 PARTITION OF users FOR VALUES WITH (MODULUS 8, REMAINDER 5);
CREATE TABLE users_p6 PARTITION OF users FOR VALUES WITH (MODULUS 8, REMAINDER 6);
CREATE TABLE users_p7 PARTITION OF users FOR VALUES WITH (MODULUS 8, REMAINDER 7);

-- Create indexes
CREATE INDEX idx_users_username ON users (username);
CREATE INDEX idx_users_email ON users (email);

================================================================================
STEP 3: SIMULATE NODE ASSIGNMENTS (INITIAL STATE)
================================================================================

-- In fixed partition strategy, partitions are assigned to nodes
-- These assignments CHANGE during rebalancing, but partitions stay the same

-- Initially, distribute 8 partitions across 4 nodes (round-robin)
INSERT INTO user_nodes (partition_id, node_id) VALUES
    (0, 0),  -- Partition 0 → Node 0
    (1, 1),  -- Partition 1 → Node 1
    (2, 2),  -- Partition 2 → Node 2
    (3, 3),  -- Partition 3 → Node 3
    (4, 0),  -- Partition 4 → Node 0
    (5, 1),  -- Partition 5 → Node 1
    (6, 2),  -- Partition 6 → Node 2
    (7, 3);  -- Partition 7 → Node 3

-- View current assignment
SELECT * FROM user_nodes ORDER BY partition_id;

================================================================================
STEP 4: INSERT DATA AND OBSERVE PARTITION DISTRIBUTION
================================================================================

-- Insert sample users
INSERT INTO users (username, email) VALUES
    ('alice', 'alice@example.com'),
    ('bob', 'bob@example.com'),
    ('charlie', 'charlie@example.com'),
    ('diana', 'diana@example.com'),
    ('eve', 'eve@example.com'),
    ('frank', 'frank@example.com'),
    ('grace', 'grace@example.com'),
    ('henry', 'henry@example.com');

-- Check which partition each user landed in
SELECT
    user_id,
    username,
    -- Show which partition (based on hash)
    (hash_extended(gen_random_uuid()::text::bytea, 0) % 8) as partition_hint
FROM users
ORDER BY user_id;

-- Check row distribution across partitions
SELECT
    relname AS partition,
    n_live_tup AS rows
FROM pg_stat_user_tables
WHERE relname LIKE 'users_p%'
ORDER BY relname;

-- The key insight: partition boundaries NEVER change!
-- Only the node assignment (user_nodes) changes during rebalancing

================================================================================
STEP 5: DEMONSTRATE REBALANCING (PARTITION REASSIGNMENT)
================================================================================

-- Simulating what happens when we add a new node (Node 4)

-- Current state: 4 nodes, 8 partitions (2 partitions each)
-- New state: 5 nodes, need to redistribute

-- Step 1: Show current state
SELECT * FROM user_nodes ORDER BY partition_id;

-- Step 2: Rebalancing - reassign partitions to nodes
-- In fixed partition strategy, we MOVE ENTIRE PARTITIONS to new nodes

-- Rebalance: Give Node 4 two partitions (0 and 4)
UPDATE user_nodes SET node_id = 4 WHERE partition_id IN (0, 4);

-- Verify new assignment after rebalancing
SELECT * FROM user_nodes ORDER BY partition_id;

-- Count partitions per node
SELECT
    node_id,
    COUNT(*) AS partition_count
FROM user_nodes
GROUP BY node_id
ORDER BY node_id;

-- KEY INSIGHT:
-- The partitions (users_p0, users_p1, etc.) NEVER changed!
-- Only the mapping in user_nodes changed!

================================================================================
STEP 6: DEMONSTRATE THE BENEFIT - SIMPLE REBALANCING
================================================================================

-- In fixed partition strategy, rebalancing is simple:
-- 1. Copy entire partition file from old node to new node
-- 2. Update partition-to-node mapping
-- 3. Done!

-- Let's simulate this with a larger dataset

-- Insert more data to see distribution
INSERT INTO users (username, email)
SELECT
    'user_' || i,
    'user_' || i || '@example.com'
FROM generate_series(1, 1000) i;

-- Check distribution
SELECT
    relname AS partition,
    n_live_tup AS rows
FROM pg_stat_user_tables
WHERE relname LIKE 'users_p%'
ORDER BY relname;

-- Note: Each partition has roughly equal data (hash-based distribution)
-- This is the benefit of fixed partitions - balanced load!

================================================================================
STEP 7: THE CHALLENGE - CHOOSING PARTITION COUNT UPFRONT
================================================================================

-- The PROBLEM with fixed partitions:
-- You must guess the partition count at database creation time

-- If you choose TOO FEW:
--   - Each partition becomes too large
--   - Rebalancing takes longer (more data to move)
--   - Less parallelism

-- If you choose TOO MANY:
--   - Each partition is too small
--   - More overhead (more files to manage)
--   - Potential issues with metadata

-- Rule of thumb: Target 100MB - few GB per partition
-- Example: 1TB data → 10-100 partitions

-- Let's simulate the challenge

-- Create a larger table to demonstrate
DROP TABLE IF EXISTS events CASCADE;

CREATE TABLE events (
    event_id BIGSERIAL,
    event_uuid UUID DEFAULT gen_random_uuid(),
    event_type VARCHAR(50) NOT NULL,
    payload JSONB,
    created_at TIMESTAMP DEFAULT NOW()
) PARTITION BY HASH (event_uuid);

-- Create 100 partitions (simulating production)
-- In PostgreSQL, we'd need to create each manually:
-- For demo, let's create 16 partitions
CREATE TABLE events_p00 PARTITION OF events FOR VALUES WITH (MODULUS 16, REMAINDER 0);
CREATE TABLE events_p01 PARTITION OF events FOR VALUES WITH (MODULUS 16, REMAINDER 1);
CREATE TABLE events_p02 PARTITION OF events FOR VALUES WITH (MODULUS 16, REMAINDER 2);
CREATE TABLE events_p03 PARTITION OF events FOR VALUES WITH (MODULUS 16, REMAINDER 3);
CREATE TABLE events_p04 PARTITION OF events FOR VALUES WITH (MODULUS 16, REMAINDER 4);
CREATE TABLE events_p05 PARTITION OF events FOR VALUES WITH (MODULUS 16, REMAINDER 5);
CREATE TABLE events_p06 PARTITION OF events FOR VALUES WITH (MODULUS 16, REMAINDER 6);
CREATE TABLE events_p07 PARTITION OF events FOR VALUES WITH (MODULUS 16, REMAINDER 7);
CREATE TABLE events_p08 PARTITION OF events FOR VALUES WITH (MODULUS 16, REMAINDER 8);
CREATE TABLE events_p09 PARTITION OF events FOR VALUES WITH (MODULUS 16, REMAINDER 9);
CREATE TABLE events_p10 PARTITION OF events FOR VALUES WITH (MODULUS 16, REMAINDER 10);
CREATE TABLE events_p11 PARTITION OF events FOR VALUES WITH (MODULUS 16, REMAINDER 11);
CREATE TABLE events_p12 PARTITION OF events FOR VALUES WITH (MODULUS 16, REMAINDER 12);
CREATE TABLE events_p13 PARTITION OF events FOR VALUES WITH (MODULUS 16, REMAINDER 13);
CREATE TABLE events_p14 PARTITION OF events FOR VALUES WITH (MODULUS 16, REMAINDER 14);
CREATE TABLE events_p15 PARTITION OF events FOR VALUES WITH (MODULUS 16, REMAINDER 15);

-- Insert sample data
INSERT INTO events (event_type, payload)
SELECT
    (ARRAY['click', 'view', 'purchase', 'login'])[floor(random() * 4 + 1)],
    jsonb_build_object('data', 'sample')
FROM generate_series(1, 1000);

-- Check distribution (should be roughly equal)
SELECT
    relname AS partition,
    n_live_tup AS rows
FROM pg_stat_user_tables
WHERE relname LIKE 'events_p%'
ORDER BY relname;

================================================================================
STEP 8: PRACTICAL DEMONSTRATION - REBALANCING WORKFLOW
================================================================================

-- Let's simulate a real rebalancing scenario

-- Current: 4 nodes, 8 partitions (2 each)
-- Goal: Add 1 more node (5 nodes), redistribute

-- First, let's see the current state
SELECT
    node_id,
    array_agg(partition_id) as partitions
FROM user_nodes
GROUP BY node_id
ORDER BY node_id;

-- Simulate rebalancing algorithm (round-robin reassignment)
-- This is what a database would do automatically

-- Reset to initial state for demo
TRUNCATE TABLE user_nodes;
INSERT INTO user_nodes (partition_id, node_id) VALUES
    (0, 0), (1, 1), (2, 2), (3, 3),
    (4, 0), (5, 1), (6, 2), (7, 3);

-- Now add Node 4 and rebalance
-- Strategy: Give each node 1-2 partitions, round-robin
-- New assignment: 5 nodes, 8 partitions

WITH new_assignments AS (
    SELECT
        partition_id,
        (partition_id + 1) / 2 AS new_node  -- Simple algorithm
    FROM generate_series(0, 7) AS partition_id
)
UPDATE user_nodes u
SET node_id = n.new_node
FROM new_assignments n
WHERE u.partition_id = n.partition_id;

-- Show new distribution
SELECT
    node_id,
    array_agg(partition_id) as partitions,
    COUNT(*) as count
FROM user_nodes
GROUP BY node_id
ORDER BY node_id;

-- KEY INSIGHT: The PARTITIONS (users_p0-p7) NEVER changed!
-- Only the user_nodes mapping changed!

================================================================================
SUMMARY: FIXED PARTITION COUNT STRATEGY
================================================================================

✅ FIXED PARTITION PROS:
  - Simple rebalancing (just move partition files)
  - Predictable performance (known number of partitions)
  - Easy to reason about

❌ FIXED PARTITION CONS:
  - Must choose partition count upfront (hard to get right)
  - Cannot adapt to changing data size
  - If data grows beyond estimate, must manually add partitions

📌 KEY RULE:
  - Partition boundaries NEVER change
  - Only node assignments change during rebalancing
  - Choose partition count based on expected data size

📊 EQUILIBRIUM:
  - Too few partitions → large partitions, slow rebalancing
  - Too many partitions → overhead, metadata explosion
  - Just right → 100MB-2GB per partition

================================================================================
NEXT STEPS:
================================================================================

1. Try Exercise 2: Dynamic Partitioning (02_dynamic_partitioning.sql)
   - See how partitions can split/merge automatically

2. Compare the two approaches:
   - Fixed: Simple, but must guess partition count
   - Dynamic: Adaptive, but more complex

3. Read DDIA pp. 203-207 for more theory

EOF
