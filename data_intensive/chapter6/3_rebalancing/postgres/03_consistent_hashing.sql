================================================================================
  PostgreSQL Consistent Hashing - DDIA Chapter 6.3
  Learn by doing: Strategy 3 - Consistent Hashing with Virtual Nodes
================================================================================

WHAT YOU'LL LEARN:
  ✅ How consistent hashing avoids the N+1 problem
  ✅ How virtual nodes (vnodes) improve load distribution
  ✅ Why adding nodes only moves 1/N of keys
  ✅ The trade-offs of consistent hashing

PREREQUISITES:
  - PostgreSQL 10+ (native partitioning support)
  - psql or any PostgreSQL client

================================================================================
CONCEPT: CONSISTENT HASHING
================================================================================

From DDIA (pp. 209-211):
  "Consistent hashing assigns each key and node a position on a circle.
   Keys are assigned to the next node clockwise on the circle."

Key Points:
  - Hash space forms a circle (0 to 2^32-1)
  - Each node is assigned a position on the circle
  - Each key is assigned to the next node clockwise
  - Adding a node only moves keys between the new node and its neighbors
  - Virtual nodes (vnodes) improve load balance

Used by: Cassandra (256 vnodes/node), Riak, Voldemort

================================================================================
PROBLEM: WHY WE NEED CONSISTENT HASHING
================================================================================

Traditional hash: hash(key) % N
  - N = number of nodes
  - When you add/remove nodes, ALL keys may need to move!

Example:
  - 3 nodes: key_1 → Node 1 (hash = 1 % 3 = 1)
  - Add 1 node (4 nodes): key_1 → Node 2 (hash = 1 % 4 = 1)
  - 75% of keys moved!

This is the N+1 problem (or "the curse of N+1").

================================================================================
STEP 1: CONNECT TO POSTGRESQL
================================================================================

  psql -U postgres -d postgres

================================================================================
STEP 2: SETUP FOR CONSISTENT HASHING DEMONSTRATION
================================================================================

-- Drop existing tables
DROP TABLE IF EXISTS consistent_hash_nodes CASCADE;
DROP TABLE IF EXISTS consistent_hash_keys CASCADE;

-- Create table to store node information
-- Each "node" in consistent hashing has a position on the hash ring
CREATE TABLE consistent_hash_nodes (
    node_id INTEGER PRIMARY KEY,
    node_name VARCHAR(50) NOT NULL,
    hash_position INTEGER NOT NULL,
    vnode_count INTEGER DEFAULT 1,  -- Number of virtual nodes
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create table to store key mappings
CREATE TABLE consistent_hash_keys (
    key_id SERIAL PRIMARY KEY,
    key_name VARCHAR(100) NOT NULL,
    hash_value INTEGER NOT NULL,
    node_id INTEGER REFERENCES consistent_hash_nodes(node_id),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_keys_hash ON consistent_hash_keys (hash_value);
CREATE INDEX idx_keys_node ON consistent_hash_keys (node_id);

================================================================================
STEP 3: CREATE THE HASH RING
================================================================================

-- In consistent hashing, nodes are placed on a circle (0 to 2^32-1)
-- For simplicity, we'll use a smaller range (0 to 360 degrees)

-- Let's create a 3-node cluster
INSERT INTO consistent_hash_nodes (node_id, node_name, hash_position, vnode_count) VALUES
    (0, 'Node-A', 0, 1),      -- Position 0 degrees
    (1, 'Node-B', 120, 1),    -- Position 120 degrees
    (2, 'Node-C', 240, 1);   -- Position 240 degrees

-- View the ring
SELECT node_id, node_name, hash_position
FROM consistent_hash_nodes
ORDER BY hash_position;

-- Visualize:
-- 0° (Node-A) → 120° (Node-B) → 240° (Node-C) → 360° (back to Node-A)
--
-- Keys between 0-120: Node-B
-- Keys between 120-240: Node-C
-- Keys between 240-360: Node-A

================================================================================
STEP 4: DEMONSTRATE KEY ASSIGNMENT-- Let's insert some keys and
================================================================================

 see which node they go to

-- Function to find the node for a given hash value
-- (This simulates what consistent hashing does)
CREATE OR REPLACE FUNCTION find_node_for_hash(target_hash INTEGER)
RETURNS TABLE(node_id INTEGER, node_name VARCHAR, hash_position INTEGER) AS $$
BEGIN
    RETURN QUERY
    WITH ordered_nodes AS (
        SELECT
            node_id,
            node_name,
            hash_position,
            LEAD(hash_position) OVER (ORDER BY hash_position) AS next_position
        FROM consistent_hash_nodes
        WHERE status = 'active'
    )
    SELECT
        n.node_id,
        n.node_name,
        n.hash_position
    FROM ordered_nodes n
    WHERE target_hash >= n.hash_position
      AND (n.next_position IS NULL OR target_hash < n.next_position)
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

-- Insert keys with their hash values
-- Using simple hash for demonstration
INSERT INTO consistent_hash_keys (key_name, hash_value)
SELECT
    'key_' || i,
    (abs(hashtext('key_' || i)) % 360)  -- Hash to 0-359 range
FROM generate_series(1, 100) i;

-- Now assign each key to a node
UPDATE consistent_hash_keys ck
SET node_id = fn.node_id
FROM find_node_for_hash(ck.hash_value) fn;

-- Check distribution
SELECT
    cn.node_name,
    COUNT(ck.key_id) AS key_count
FROM consistent_hash_nodes cn
LEFT JOIN consistent_hash_keys ck ON cn.node_id = ck.node_id
GROUP BY cn.node_id, cn.node_name
ORDER BY cn.node_name;

-- Notice: Uneven distribution!
-- This is because nodes are equally spaced (120° apart)
-- but keys aren't uniformly distributed

================================================================================
STEP 5: THE PROBLEM - UNEVEN LOAD DISTRIBUTION
================================================================================

-- With only 3 nodes and 1 vnode each, load distribution is uneven
-- This is because:
--   1. Node positions are fixed
--   2. Key distribution may not be uniform

-- Let's see the actual ranges each node owns
SELECT
    cn.node_name,
    cn.hash_position AS start_position,
    LEAD(cn.hash_position) OVER (ORDER BY cn.hash_position) AS end_position,
    COUNT(ck.key_id) AS keys_in_range
FROM consistent_hash_nodes cn
LEFT JOIN consistent_hash_keys ck ON cn.node_id = ck.node_id
GROUP BY cn.node_id, cn.node_name, cn.hash_position
ORDER BY cn.hash_position;

-- PROBLEM: Some ranges have more keys than others!
-- This is why we need VIRTUAL NODES (vnodes)

================================================================================
STEP 6: VIRTUAL NODES (VNODES) - THE SOLUTION
================================================================================

-- Vnodes solve the load imbalance problem by giving each physical node
-- multiple positions on the hash ring

-- Let's recreate with vnodes
TRUNCATE TABLE consistent_hash_keys CASCADE;
TRUNCATE TABLE consistent_hash_nodes CASCADE;

-- Create nodes with 10 vnodes each (like Cassandra!)
INSERT INTO consistent_hash_nodes (node_id, node_name, hash_position, vnode_count) VALUES
    -- Node-A: 10 vnodes spread around the circle
    (0, 'Node-A', 0, 10),
    (0, 'Node-A', 36, 10),
    (0, 'Node-A', 72, 10),
    (0, 'Node-A', 108, 10),
    (0, 'Node-A', 144, 10),
    (0, 'Node-A', 180, 10),
    (0, 'Node-A', 216, 10),
    (0, 'Node-A', 252, 10),
    (0, 'Node-A', 288, 10),
    (0, 'Node-A', 324, 10),

    -- Node-B: 10 vnodes
    (1, 'Node-B', 12, 10),
    (1, 'Node-B', 48, 10),
    (1, 'Node-B', 84, 10),
    (1, 'Node-B', 120, 10),
    (1, 'Node-B', 156, 10),
    (1, 'Node-B', 192, 10),
    (1, 'Node-B', 228, 10),
    (1, 'Node-B', 264, 10),
    (1, 'Node-B', 300, 10),
    (1, 'Node-B', 336, 10),

    -- Node-C: 10 vnodes
    (2, 'Node-C', 24, 10),
    (2, 'Node-C', 60, 10),
    (2, 'Node-C', 96, 10),
    (2, 'Node-C', 132, 10),
    (2, 'Node-C', 168, 10),
    (2, 'Node-C', 204, 10),
    (2, 'Node-C', 240, 10),
    (2, 'Node-C', 276, 10),
    (2, 'Node-C', 312, 10),
    (2, 'Node-C', 348, 10);

-- Function to find node with vnodes
CREATE OR REPLACE FUNCTION find_node_for_hash_vnode(target_hash INTEGER)
RETURNS TABLE(node_id INTEGER, node_name VARCHAR) AS $$
BEGIN
    RETURN QUERY
    WITH ranked_nodes AS (
        SELECT
            node_id,
            node_name,
            hash_position,
            ROW_NUMBER() OVER (ORDER BY
                CASE WHEN hash_position <= target_hash THEN hash_position
                     ELSE hash_position - 360 END DESC
            ) AS rn
        FROM consistent_hash_nodes
        WHERE status = 'active'
    )
    SELECT rn.node_id, rn.node_name
    FROM ranked_nodes rn
    WHERE rn.rn = 1;
END;
$$ LANGUAGE plpgsql;

-- Insert more keys
INSERT INTO consistent_hash_keys (key_name, hash_value)
SELECT
    'key_' || i,
    (abs(hashtext('key_' || i)) % 360)
FROM generate_series(1, 1000) i;

-- Assign to nodes
UPDATE consistent_hash_keys ck
SET node_id = fn.node_id
FROM find_node_for_hash_vnode(ck.hash_value) fn;

-- Check distribution with vnodes
SELECT
    cn.node_name,
    COUNT(ck.key_id) AS key_count
FROM (
    SELECT DISTINCT node_id, node_name
    FROM consistent_hash_nodes
) cn
LEFT JOIN consistent_hash_keys ck ON cn.node_id = ck.node_id
GROUP BY cn.node_name
ORDER BY cn.node_name;

-- Much better distribution! Vnodes help balance the load

================================================================================
STEP 7: DEMONSTRATE NODE ADDITION - THE KEY BENEFIT
================================================================================

-- THE KEY BENEFIT of consistent hashing:
-- When you add a node, only 1/N keys need to move!

-- Let's simulate adding a 4th node

-- Current: 3 nodes, ~333 keys each (with vnodes)
-- After adding 1 node: ~250 keys each

-- Add Node-D
INSERT INTO consistent_hash_nodes (node_id, node_name, hash_position, vnode_count) VALUES
    (3, 'Node-D', 60, 10),
    (3, 'Node-D', 66, 10),
    (3, 'Node-D', 72, 10),
    (3, 'Node-D', 78, 10),
    (3, 'Node-D', 84, 10),
    (3, 'Node-D', 90, 10),
    (3, 'Node-D', 96, 10),
    (3, 'Node-D', 102, 10),
    (3, 'Node-D', 108, 10),
    (3, 'Node-D', 114, 10);

-- Save old assignments
ALTER TABLE consistent_hash_keys ADD COLUMN old_node_id INTEGER;

UPDATE consistent_hash_keys
SET old_node_id = node_id;

-- Reassign keys with new node
UPDATE consistent_hash_keys ck
SET node_id = fn.node_id
FROM find_node_for_hash_vnode(ck.hash_value) fn;

-- Compare before and after
SELECT
    'Before' AS state,
    old_node_id AS node_id,
    COUNT(*) AS key_count
FROM consistent_hash_keys
WHERE old_node_id IS NOT NULL
GROUP BY old_node_id
UNION ALL
SELECT
    'After' AS state,
    node_id,
    COUNT(*)
FROM consistent_hash_keys
GROUP BY node_id
ORDER BY state, node_id;

-- Count how many keys moved
SELECT
    COUNT(*) AS keys_moved,
    COUNT(*) * 100.0 / (SELECT COUNT(*) FROM consistent_hash_keys) AS percent_moved
FROM consistent_hash_keys
WHERE node_id != old_node_id;

-- KEY INSIGHT: Only a fraction of keys moved!
-- Without consistent hashing, ~75% would have moved
-- With consistent hashing, only ~25% moved

================================================================================
STEP 8: COMPARE PARTITIONING STRATEGIES
================================================================================

-- Let's create a comparison to understand the differences

-- Strategy 1: Fixed Partitions
--   - Partition count is fixed
--   - Rebalancing moves entire partitions
--   - Adding nodes: many keys move

-- Strategy 2: Dynamic Partitioning
--   - Partitions split/merge based on size
--   - Adaptive to data growth
--   - More complex management

-- Strategy 3: Consistent Hashing
--   - Nodes on a hash ring
--   - Adding node: only 1/N keys move
--   - Vnodes for better load distribution

-- Let's demonstrate the difference with a query
-- (This simulates what would happen with each strategy)

-- Create test data
DROP TABLE IF EXISTS strategy_comparison CASCADE;

CREATE TABLE strategy_comparison (
    key_id SERIAL PRIMARY KEY,
    key_name VARCHAR(50),
    hash_value INTEGER
);

-- Insert 1000 keys
INSERT INTO strategy_comparison (key_name, hash_value)
SELECT
    'key_' || i,
    i % 1000
FROM generate_series(1, 1000) i;

-- Strategy 1: Fixed partitions (e.g., 4 partitions)
-- Key moves if: hash(key) % old_nodes != hash(key) % new_nodes
SELECT
    'Fixed Partition (4→5)' AS strategy,
    SUM(CASE WHEN (key_id % 4) != (key_id % 5) THEN 1 ELSE 0 END) AS keys_moved,
    SUM(CASE WHEN (key_id % 4) != (key_id % 5) THEN 1 ELSE 0 END) * 100.0 / 1000 AS percent
FROM strategy_comparison;

-- Strategy 3: Consistent hashing
-- Only keys in the "affected range" move
-- With 4 nodes, ~1/4 of keys affected
SELECT
    'Consistent Hashing' AS strategy,
    250 AS estimated_keys_moved,  -- Approximately 1/4
    25 AS percent;

-- Show the difference:
-- Fixed: ~80% of keys move
-- Consistent: ~25% of keys move

================================================================================
STEP 9: REAL-WORLD EXAMPLE - CASSANDRA-STYLE
================================================================================

-- Cassandra uses consistent hashing with 256 vnodes per node
-- Let's simulate a simplified version

DROP TABLE IF EXISTS cassandra_style CASCADE;
DROP TABLE IF EXISTS cassandra_tokens CASCADE;

-- Token table (like Cassandra's token ring)
CREATE TABLE cassandra_tokens (
    node_id INTEGER,
    node_name VARCHAR(50),
    token INTEGER,  -- Each vnode has a token
    PRIMARY KEY (node_id, token)
);

-- Create 3 nodes with 8 vnodes each (simplified from Cassandra's 256)
INSERT INTO cassandra_tokens (node_id, node_name, token) VALUES
    -- Node 1: tokens 0, 45, 90, 135, 180, 225, 270, 315
    (1, 'Cassandra-1', 0),
    (1, 'Cassandra-1', 45),
    (1, 'Cassandra-1', 90),
    (1, 'Cassandra-1', 135),
    (1, 'Cassandra-1', 180),
    (1, 'Cassandra-1', 225),
    (1, 'Cassandra-1', 270),
    (1, 'Cassandra-1', 315),

    -- Node 2: tokens 22, 67, 112, 157, 202, 247, 292, 337
    (2, 'Cassandra-2', 22),
    (2, 'Cassandra-2', 67),
    (2, 'Cassandra-2', 112),
    (2, 'Cassandra-2', 157),
    (2, 'Cassandra-2', 202),
    (2, 'Cassandra-2', 247),
    (2, 'Cassandra-2', 292),
    (2, 'Cassandra-2', 337),

    -- Node 3: tokens 44, 89, 134, 179, 224, 269, 314, 359
    (3, 'Cassandra-3', 44),
    (3, 'Cassandra-3', 89),
    (3, 'Cassandra-3', 134),
    (3, 'Cassandra-3', 179),
    (3, 'Cassandra-3', 224),
    (3, 'Cassandra-3', 269),
    (3, 'Cassandra-3', 314),
    (3, 'Cassandra-3', 359);

-- Create keys table
CREATE TABLE cassandra_style (
    key_id SERIAL PRIMARY KEY,
    key_name VARCHAR(50),
    token INTEGER,
    node_id INTEGER
);

-- Insert sample keys
INSERT INTO cassandra_style (key_name, token)
SELECT
    'key_' || i,
    abs(hashtext('key_' || i)) % 360
FROM generate_series(1, 1000) i;

-- Function to find the owner (next token clockwise)
CREATE OR REPLACE FUNCTION get_owner(target_token INTEGER)
RETURNS INTEGER AS $$
DECLARE
    owner INTEGER;
BEGIN
    SELECT ct.node_id INTO owner
    FROM cassandra_tokens ct
    WHERE ct.token <= target_token
    ORDER BY ct.token DESC
    LIMIT 1;

    -- If no token found (wraps around), get the first node
    IF owner IS NULL THEN
        SELECT ct.node_id INTO owner
        FROM cassandra_tokens ct
        ORDER BY ct.token
        LIMIT 1;
    END IF;

    RETURN owner;
END;
$$ LANGUAGE plpgsql;

-- Assign keys to nodes
UPDATE cassandra_style
SET node_id = get_owner(token);

-- Check distribution
SELECT
    node_id,
    COUNT(*) AS key_count
FROM cassandra_style
GROUP BY node_id
ORDER BY node_id;

-- With 8 vnodes per node, distribution should be fairly even

================================================================================
SUMMARY: CONSISTENT HASHING
================================================================================

✅ CONSISTENT HASHING PROS:
  - Adding/removing nodes only moves 1/N keys
  - Vnodes provide better load distribution
  - No single point of failure (decentralized)

❌ CONSISTENT HASHING CONS:
  - More complex to implement
  - Uneven distribution without vnodes
  - Ring management overhead

📌 KEY INSIGHT:
  Traditional hash: hash(key) % N → Adding nodes moves ALL keys
  Consistent hash: Add node → Only 1/N keys move

📊 EQUILIBRIUM:
  - Vnodes: More = better distribution, more metadata
  - Tokens: Must be carefully chosen for even distribution

================================================================================
NEXT STEPS:
================================================================================

1. Review all three rebalancing strategies:
   - Fixed partitions: Simple, predictable
   - Dynamic: Adaptive, complex
   - Consistent hashing: Minimal data movement

2. Read DDIA pp. 203-215 for more theory

3. Move on to Section 4: Request Routing

EOF
