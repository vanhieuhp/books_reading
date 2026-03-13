================================================================================
  PostgreSQL Gossip Protocol - DDIA Chapter 6.4
  Learn by doing: Decentralized Request Routing
================================================================================

WHAT YOU'LL LEARN:
  ✅ How gossip protocol spreads information across nodes
  ✅ Why it's decentralized (no single point of failure)
  ✅ The trade-off: eventual consistency
  ✅ How Cassandra uses gossip for routing

PREREQUISITES:
  - PostgreSQL 10+ (native partitioning support)
  - psql or any PostgreSQL client
  - Basic understanding of partitioning (from Chapter 6.1-6.3)

================================================================================
CONCEPT: GOSSIP PROTOCOL
================================================================================

From DDIA (pp. 218-220):
  "Gossip protocols are used for peer-to-peer communication between nodes.
   Each node periodically exchanges state information with a few other nodes.
   Over time, all nodes converge to the same state."

Key Points:
  - Decentralized (no coordinator)
  - Eventual consistency (routing table may be stale briefly)
  - Scales well (O(log N) convergence)
  - Resilient to failures

Used by: Cassandra, Riak, Dynamo

================================================================================
STEP 1: CONNECT TO POSTGRESQL
================================================================================

  psql -U postgres -d postgres

================================================================================
STEP 2: SETUP FOR GOSSIP SIMULATION
================================================================================

-- We'll simulate gossip protocol using PostgreSQL
-- Each "node" will have a routing table that gets updated

-- Drop existing tables
DROP TABLE IF EXISTS gossip_nodes CASCADE;
DROP TABLE IF EXISTS gossip_state CASCADE;
DROP TABLE IF EXISTS gossip_messages CASCADE;

-- Create table to store node information
-- Each node maintains its own view of the cluster
CREATE TABLE gossip_nodes (
    node_id INTEGER PRIMARY KEY,
    node_name VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'UP',  -- UP, DOWN, JOINING, LEAVING
    is_local BOOLEAN DEFAULT FALSE,  -- Is this the node we're connected to?
    last_heartbeat TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create table for routing information
-- Each node has its own copy of this (eventually consistent)
CREATE TABLE gossip_state (
    node_id INTEGER REFERENCES gossip_nodes(node_id),
    partition_id INTEGER NOT NULL,
    owner_node_id INTEGER NOT NULL,
    version INTEGER DEFAULT 1,  -- Incremented on updates
    updated_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (node_id, partition_id)
);

-- Create message log (simulates gossip messages sent)
CREATE TABLE gossip_messages (
    message_id SERIAL PRIMARY KEY,
    from_node_id INTEGER,
    to_node_id INTEGER,
    payload JSONB,
    sent_at TIMESTAMP DEFAULT NOW()
);

================================================================================
STEP 3: SETUP CLUSTER STATE
================================================================================

-- Create a 4-node cluster
INSERT INTO gossip_nodes (node_id, node_name) VALUES
    (0, 'Node-0'),
    (1, 'Node-1'),
    (2, 'Node-2'),
    (3, 'Node-3');

-- Create initial routing state
-- Each node "knows" about all partitions
-- Initially, partitions are evenly distributed

-- Node-0's view: partitions 0-2 owned by Node-0, 3-5 by Node-1, etc.
INSERT INTO gossip_state (node_id, partition_id, owner_node_id) VALUES
    -- Node-0's routing table
    (0, 0, 0), (0, 1, 0), (0, 2, 0), (0, 3, 1), (0, 4, 1), (0, 5, 1),
    (0, 6, 2), (0, 7, 2), (0, 8, 2), (0, 9, 3), (0, 10, 3), (0, 11, 3),

    -- Node-1's routing table (same initial state)
    (1, 0, 0), (1, 1, 0), (1, 2, 0), (1, 3, 1), (1, 4, 1), (1, 5, 1),
    (1, 6, 2), (1, 7, 2), (1, 8, 2), (1, 9, 3), (1, 10, 3), (1, 11, 3),

    -- Node-2's routing table
    (2, 0, 0), (2, 1, 0), (2, 2, 0), (2, 3, 1), (2, 4, 1), (2, 5, 1),
    (2, 6, 2), (2, 7, 2), (2, 8, 2), (2, 9, 3), (2, 10, 3), (2, 11, 3),

    -- Node-3's routing table
    (3, 0, 0), (3, 1, 0), (3, 2, 0), (3, 3, 1), (3, 4, 1), (3, 5, 1),
    (3, 6, 2), (3, 7, 2), (3, 8, 2), (3, 9, 3), (3, 10, 3), (3, 11, 3);

-- View initial state
SELECT * FROM gossip_state ORDER BY node_id, partition_id;

================================================================================
STEP 4: SIMULATE GOSSIP MESSAGE EXCHANGE
================================================================================

-- Gossip protocol:
-- 1. Each node picks a random peer to talk to
-- 2. They exchange their routing tables
-- 3. Each node updates its view based on newer information

-- Function to simulate one gossip round
CREATE OR REPLACE FUNCTION gossip_round(source_node INTEGER, target_node INTEGER)
RETURNS void AS $$
DECLARE
    s_version INTEGER;
    t_version INTEGER;
BEGIN
    -- Get the latest version from source's state
    SELECT MAX(version) INTO s_version
    FROM gossip_state
    WHERE node_id = source_node;

    -- Get the latest version from target's state
    SELECT MAX(version) INTO t_version
    FROM gossip_state
    WHERE node_id = target_node;

    -- If source has newer info, update target
    -- This simulates the "merge" step of gossip
    INSERT INTO gossip_messages (from_node_id, to_node_id, payload)
    VALUES (
        source_node,
        target_node,
        jsonb_build_object(
            'source_version', s_version,
            'target_version', t_version,
            'action', CASE WHEN s_version > t_version THEN 'update' ELSE 'no_change' END
        )
    );

    -- Simulate state propagation (simplified)
    -- In real gossip, only newer versions propagate
    UPDATE gossip_state gs
    SET owner_node_id = gs2.owner_node_id,
        version = gs2.version + 1,
        updated_at = NOW()
    FROM gossip_state gs2
    WHERE gs.partition_id = gs2.partition_id
      AND gs.node_id = target_node
      AND gs2.node_id = source_node
      AND gs2.version > gs.version;
END;
$$ LANGUAGE plpgsql;

-- Simulate gossip rounds
SELECT gossip_round(0, 1);  -- Node-0 talks to Node-1
SELECT gossip_round(1, 2);  -- Node-1 talks to Node-2
SELECT gossip_round(2, 3);  -- Node-2 talks to Node-3
SELECT gossip_round(3, 0);  -- Node-3 talks to Node-0

-- Check message log (what was communicated)
SELECT * FROM gossip_messages;

-- Check if routing tables are starting to converge
SELECT node_id, COUNT(*) as entries, MAX(version) as max_version
FROM gossip_state
GROUP BY node_id
ORDER BY node_id;

================================================================================
STEP 5: DEMONSTRATE EVENTUAL CONSISTENCY
================================================================================

-- Key property: Eventual consistency
-- Routing tables may be temporarily inconsistent

-- Let's make a change and see how gossip propagates it

-- Change: Partition 0 moves from Node-0 to Node-3
-- (simulating rebalancing)

-- Update Node-0's view first (the "source" of truth)
UPDATE gossip_state
SET owner_node_id = 3, version = version + 1
WHERE node_id = 0 AND partition_id = 0;

-- Other nodes don't know yet (this is the "inconsistency window")
SELECT
    node_id,
    partition_id,
    owner_node_id,
    version
FROM gossip_state
WHERE partition_id = 0
ORDER BY node_id;

-- Now simulate gossip - this will propagate the change
SELECT gossip_round(0, 1);  -- Node-0 tells Node-1

-- Check again - Node-1 should now know
SELECT
    node_id,
    partition_id,
    owner_node_id,
    version
FROM gossip_state
WHERE partition_id = 0
ORDER BY node_id;

-- Continue gossip to propagate to all nodes
SELECT gossip_round(1, 2);
SELECT gossip_round(2, 3);

-- Now check - all nodes should have the same view
SELECT
    node_id,
    partition_id,
    owner_node_id,
    version
FROM gossip_state
WHERE partition_id = 0
ORDER BY node_id;

-- KEY INSIGHT: All nodes eventually converge to the same state!
-- This is eventual consistency

================================================================================
STEP 6: DEMONSTRATE DECENTRALIZED ROUTING
================================================================================

-- In gossip-based systems, any node can handle any request
-- If the contacted node doesn't own the partition, it forwards

-- Let's simulate this

-- Function to route a request (like a database client would do)
CREATE OR REPLACE FUNCTION route_request(
    contact_node INTEGER,
    key_partition INTEGER
) RETURNS TABLE(contact_node INTEGER, owner_node INTEGER, hops INTEGER) AS $$
DECLARE
    owner INTEGER;
    actual_owner INTEGER;
BEGIN
    -- Step 1: Ask contact node who owns the partition
    SELECT owner_node_id INTO owner
    FROM gossip_state
    WHERE node_id = contact_node AND partition_id = key_partition;

    -- Step 2: If contact node doesn't own it, forward to actual owner
    IF owner != contact_node THEN
        -- Simulate forwarding (1 hop)
        RETURN QUERY SELECT contact_node, owner, 1;
    ELSE
        -- Direct (0 hops)
        RETURN QUERY SELECT contact_node, owner, 0;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Test: Request for partition 0, contacting different nodes
SELECT 'Contact Node-0' AS scenario, * FROM route_request(0, 0);
SELECT 'Contact Node-1' AS scenario, * FROM route_request(1, 0);
SELECT 'Contact Node-2' AS scenario, * FROM route_request(2, 0);
SELECT 'Contact Node-3' AS scenario, * FROM route_request(3, 0);

-- Notice: Some contacts require forwarding (extra hop)
-- This is the trade-off of gossip-based routing

================================================================================
STEP 7: SIMULATE NODE FAILURE
================================================================================

-- Gossip protocol handles failures gracefully

-- Mark Node-2 as DOWN
UPDATE gossip_nodes
SET status = 'DOWN'
WHERE node_id = 2;

-- Other nodes will eventually learn about this via gossip
-- Let's simulate the propagation

-- First, check who thinks Node-2 is alive
-- (We'd need to track this, but for now let's see the concept)

-- Simulate gossip about the failure
INSERT INTO gossip_messages (from_node_id, to_node_id, payload)
VALUES (0, 1, '{"type": "node_failure", "failed_node": 2}');

-- In real systems, nodes mark each other as down after missing heartbeats
-- This is how Cassandra handles failure detection

================================================================================
STEP 8: COMPARE GOSSIP VS CENTRALIZED
================================================================================

-- Let's create a comparison

-- GOSSIP (Decentralized):
--   - Any node can be contacted
--   - Eventual consistency (routing may be briefly stale)
--   - No single point of failure
--   - Extra hop sometimes needed

-- CENTRALIZED (e.g., ZooKeeper):
--   - Single routing tier
--   - Strong consistency (routing always current)
--   - Single point of failure (needs replication)
--   - Always one hop (but through router)

-- Simulate both approaches

-- Create centralized routing table
DROP TABLE IF EXISTS centralized_routing CASCADE;

CREATE TABLE centralized_routing (
    partition_id INTEGER PRIMARY KEY,
    owner_node_id INTEGER,
    version INTEGER DEFAULT 1,
    updated_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO centralized_routing (partition_id, owner_node_id)
SELECT partition_id, owner_node_id
FROM gossip_state
WHERE node_id = 0
LIMIT 12;

-- Compare query paths

-- Gossip path: Client → Any Node → (maybe) → Owner
--   SELECT owner_node_id FROM gossip_state WHERE node_id = contact AND partition_id = X

-- Centralized path: Client → Router → Owner
--   SELECT owner_node_id FROM centralized_routing WHERE partition_id = X

-- The key difference:
--   - Gossip: Any node can answer, but may forward
--   - Centralized: Router always knows, but is bottleneck

================================================================================
STEP 9: REAL-WORLD PATTERN - CASSANDRA-STYLE
================================================================================

-- Cassandra uses gossip for:
--   1. Cluster membership (who's in the cluster)
--   2. Partition-to-node mapping (routing)
--   3. Failure detection (who's down)

-- Let's simulate a simplified Cassandra-style setup

DROP TABLE IF EXISTS cassandra_cluster CASCADE;
DROP TABLE IF EXISTS cassandra_routing CASCADE;

-- Cluster membership
CREATE TABLE cassandra_cluster (
    node_id INTEGER PRIMARY KEY,
    host_id UUID DEFAULT gen_random_uuid(),
    ip_address VARCHAR(20),
    status VARCHAR(20) DEFAULT 'NORMAL',
    datacenter VARCHAR(20),
    rack VARCHAR(20),
    gossip_state VARCHAR(20) DEFAULT 'NORMAL',
    heartbeat_state INTEGER DEFAULT 0
);

INSERT INTO cassandra_cluster (node_id, ip_address, datacenter, rack) VALUES
    (0, '10.0.0.1', 'dc1', 'rack1'),
    (1, '10.0.0.2', 'dc1', 'rack1'),
    (2, '10.0.0.3', 'dc1', 'rack2'),
    (3, '10.0.0.4', 'dc2', 'rack1');

-- Routing information (what each node knows)
CREATE TABLE cassandra_routing (
    node_id INTEGER,
    partition_key VARCHAR(50),
    token_range_start INTEGER,
    token_range_end INTEGER,
    owner_node_id INTEGER,
    PRIMARY KEY (node_id, partition_key)
);

-- Insert routing info (simplified)
INSERT INTO cassandra_routing (node_id, partition_key, token_range_start, token_range_end, owner_node_id) VALUES
    (0, 'key_a', 0, 85, 0),
    (0, 'key_n', 85, 170, 1),
    (0, 'key_z', 255, 340, 2),
    (1, 'key_a', 0, 85, 0),
    (1, 'key_n', 85, 170, 1),
    (1, 'key_z', 255, 340, 2),
    (2, 'key_a', 0, 85, 0),
    (2, 'key_n', 85, 170, 1),
    (2, 'key_z', 255, 340, 2),
    (3, 'key_a', 0, 85, 0),
    (3, 'key_n', 85, 170, 1),
    (3, 'key_z', 255, 340, 2);

-- Query: How would a client find the owner of a key?
CREATE OR REPLACE FUNCTION find_key_owner_cassandra(contact_node INTEGER, key_name VARCHAR)
RETURNS INTEGER AS $$
DECLARE
    token_val INTEGER;
    owner INTEGER;
BEGIN
    token_val := abs(hashtext(key_name)) % 340;

    -- Find the owner using the token range
    SELECT cr.owner_node_id INTO owner
    FROM cassandra_routing cr
    WHERE cr.node_id = contact_node
      AND cr.token_range_start <= token_val
      AND token_val < cr.token_range_end
    LIMIT 1;

    RETURN owner;
END;
$$ LANGUAGE plpgsql;

-- Test routing
SELECT find_key_owner_cassandra(0, 'apple') AS owner_for_apple;
SELECT find_key_owner_cassandra(1, 'banana') AS owner_for_banana;
SELECT find_key_owner_cassandra(2, 'cherry') AS owner_for_cherry;

================================================================================
SUMMARY: GOSSIP PROTOCOL
================================================================================

✅ GOSSIP PROS:
  - Decentralized (no single point of failure)
  - Scales well (O(log N) convergence)
  - Resilient to node failures
  - Simple to reason about

❌ GOSSIP CONS:
  - Eventual consistency (briefly stale routing)
  - May need extra hop (forwarding)
  - Harder to debug (distributed state)

📌 KEY INSIGHT:
  Gossip is the foundation of decentralized distributed systems:
    - Cassandra: Cluster state, routing, failure detection
    - Riak: Cluster membership
    - Dynamo: Eventual consistency

⚠️  TRADE-OFF:
  Decentralized (gossip) vs Centralized (ZooKeeper)
    - Gossip: Resilient, eventually consistent
    - ZooKeeper: Consistent, potential bottleneck

================================================================================
NEXT STEPS:
================================================================================

1. Try Exercise 2: ZooKeeper Coordination (02_zookeeper_coordination.sql)
   - See the centralized approach

2. Compare gossip vs ZooKeeper approaches
   - When to use each?

3. Read DDIA pp. 218-224 for more theory

EOF
