================================================================================
  PostgreSQL ZooKeeper Coordination - DDIA Chapter 6.4
  Learn by doing: Centralized Request Routing
================================================================================

WHAT YOU'LL LEARN:
  ✅ How ZooKeeper provides centralized coordination
  ✅ The concept of "watches" for immediate notifications
  ✅ Strong consistency in routing
  ✅ Trade-offs: bottleneck vs consistency

PREREQUISITES:
  - PostgreSQL 10+ (native partitioning support)
  - psql or any PostgreSQL client
  - Understanding of gossip protocol (exercise 1)

================================================================================
CONCEPT: ZOOKEEPER COORDINATION
================================================================================

From DDIA (pp. 220-224):
  "Many distributed databases use a separate coordination service like
   ZooKeeper to keep track of cluster state."

Key Points:
  - Centralized source of truth
  - Strong consistency (immediate updates)
  - Watches for instant notifications
  - Trade-off: Bottleneck if not replicated

Used by: HBase, Kafka, MongoDB (config servers), SolrCloud

================================================================================
STEP 1: CONNECT TO POSTGRESQL
================================================================================

  psql -U postgres -d postgres

================================================================================
STEP 2: SETUP FOR ZOOKEEPER SIMULATION
================================================================================

-- We'll simulate ZooKeeper's coordination using PostgreSQL
-- ZooKeeper is essentially a distributed key-value store with watches

-- Drop existing tables
DROP TABLE IF EXISTS zk_election CASCADE;
DROP TABLE IF EXISTS zk_watches CASCADE;
DROP TABLE IF EXISTS zk znodes CASCADE;
DROP TABLE IF EXISTS routing_tier CASCADE;

-- Create "znode" table (ZooKeeper's data model)
-- Each znode is like a file in a hierarchical filesystem
CREATE TABLE zk_znodes (
    path VARCHAR(200) PRIMARY KEY,  -- /path/to/znode
    value JSONB,                     -- Data stored at this znode
    version INTEGER DEFAULT 0,        -- Incremented on every change
    ephemeral BOOLEAN DEFAULT FALSE,  -- Delete when session ends?
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create table for "watches" (notifications)
-- This simulates ZooKeeper's watch mechanism
CREATE TABLE zk_watches (
    watch_id SERIAL PRIMARY KEY,
    znode_path VARCHAR(200) REFERENCES zk_znodes(path),
    client_id VARCHAR(50),           -- Who's watching?
    triggered_at TIMESTAMP DEFAULT NOW()
);

-- Create routing tier that subscribes to ZooKeeper
CREATE TABLE routing_tier (
    router_id INTEGER PRIMARY KEY,
    router_name VARCHAR(50),
    status VARCHAR(20) DEFAULT 'active',
    partition_map_version INTEGER DEFAULT 0,
    last_sync TIMESTAMP DEFAULT NOW()
);

================================================================================
STEP 3: SETUP ZOOKEEPER-LIKE STATE
================================================================================

-- Initialize ZooKeeper state (like /cluster, /partitions, /election)

-- /cluster/nodes - List of active nodes
INSERT INTO zk_znodes (path, value) VALUES
    ('/cluster/nodes', jsonb_build_array(
        jsonb_build_object('node_id', 0, 'ip', '10.0.0.1', 'status', 'UP'),
        jsonb_build_object('node_id', 1, 'ip', '10.0.0.2', 'status', 'UP'),
        jsonb_build_object('node_id', 2, 'ip', '10.0.0.3', 'status', 'UP'),
        jsonb_build_object('node_id', 3, 'ip', '10.0.0.4', 'status', 'UP')
    ));

-- /partitions/assignment - Who owns which partition
INSERT INTO zk_znodes (path, value) VALUES
    ('/partitions/assignment', jsonb_build_object(
        0, 0, 1, 1, 2, 2, 3, 3,
        4, 0, 5, 1, 6, 2, 7, 3,
        8, 0, 9, 1, 10, 2, 11, 3
    ));

-- /election - Leader election (for active partitioning)
INSERT INTO zk_znodes (path, value) VALUES
    ('/election/leader', jsonb_build_object('leader_id', 0, 'term', 1));

-- View initial state
SELECT path, value FROM zk_znodes ORDER BY path;

================================================================================
STEP 4: DEMONSTRATE ZOOKEEPER'S WATCH MECHANISM
================================================================================

-- ZooKeeper's key feature: Watches
-- When a znode changes, all watching clients are notified immediately

-- Let's simulate this

-- Step 1: Router registers a watch on /partitions/assignment
INSERT INTO zk_watches (znode_path, client_id) VALUES
    ('/partitions/assignment', 'router_1'),
    ('/partitions/assignment', 'router_2');

-- View active watches
SELECT * FROM zk_watches;

-- Step 2: Something changes (partition rebalancing)
-- Update the partition assignment
UPDATE zk_znodes
SET value = jsonb_build_object(
    0, 0, 1, 1, 2, 2, 3, 3,
    4, 0, 5, 1, 6, 2, 7, 3,
    8, 0, 9, 1, 10, 2, 11, 4  -- Partition 11 now on Node 4!
),
version = version + 1,
updated_at = NOW()
WHERE path = '/partitions/assignment';

-- Step 3: Watches are triggered (notifications sent)
UPDATE zk_watches
SET triggered_at = NOW()
WHERE znode_path = '/partitions/assignment';

-- View triggered watches
SELECT * FROM zk_watches WHERE triggered_at IS NOT NULL;

-- KEY INSIGHT: Watches fire IMMEDIATELY when data changes!
-- This is different from gossip (which is eventual)

================================================================================
STEP 5: DEMONSTRATE STRONG CONSISTENCY
================================================================================

-- ZooKeeper provides strong consistency
-- Read after write returns the latest value

-- Let's simulate this

-- Function to simulate ZooKeeper write
CREATE OR REPLACE FUNCTION zk_write(znode_path VARCHAR, new_value JSONB)
RETURNS VOID AS $$
BEGIN
    UPDATE zk_znodes
    SET value = new_value,
        version = version + 1,
        updated_at = NOW()
    WHERE path = znode_path;

    -- Trigger watches (simulate immediate notification)
    UPDATE zk_watches
    SET triggered_at = NOW()
    WHERE znode_path = znode_path;
END;
$$ LANGUAGE plpgsql;

-- Function to simulate ZooKeeper read (always latest)
CREATE OR REPLACE FUNCTION zk_read(znode_path VARCHAR)
RETURNS JSONB AS $$
DECLARE
    result JSONB;
BEGIN
    SELECT value INTO result
    FROM zk_znodes
    WHERE path = znode_path;

    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Write then immediately read - always consistent!
SELECT zk_write('/cluster/nodes', jsonb_build_array(
    jsonb_build_object('node_id', 0, 'ip', '10.0.0.1', 'status', 'UP'),
    jsonb_build_object('node_id', 1, 'ip', '10.0.0.2', 'status', 'UP'),
    jsonb_build_object('node_id', 2, 'ip', '10.0.0.3', 'status', 'DOWN'),  -- Node 2 is DOWN!
    jsonb_build_object('node_id', 3, 'ip', '10.0.0.4', 'status', 'UP')
));

-- Read immediately - guaranteed to see the update!
SELECT zk_read('/cluster/nodes') AS read_after_write;

-- Compare to gossip: In gossip, you might read stale data briefly
-- In ZooKeeper, reads are ALWAYS consistent

================================================================================
STEP 6: DEMONSTRATE ROUTING TIER SYNC
================================================================================

-- The routing tier uses ZooKeeper to stay in sync

-- Create routers
INSERT INTO routing_tier (router_id, router_name) VALUES
    (1, 'Router-1'),
    (2, 'Router-2');

-- Simulate router syncing with ZooKeeper
CREATE OR REPLACE FUNCTION sync_router_with_zk(router_id INTEGER)
RETURNS VOID AS $$
DECLARE
    partition_map JSONB;
    map_version INTEGER;
BEGIN
    -- Get latest partition map from ZooKeeper
    SELECT value, version INTO partition_map, map_version
    FROM zk_znodes
    WHERE path = '/partitions/assignment';

    -- Update router's local copy
    UPDATE routing_tier
    SET partition_map_version = map_version,
        last_sync = NOW()
    WHERE router_id = router_id;

    -- In real system, router would also fetch partition data
    RAISE NOTICE 'Router % synced to version %', router_id, map_version;
END;
$$ LANGUAGE plpgsql;

-- Routers sync with ZooKeeper
SELECT sync_router_with_zk(1);
SELECT sync_router_with_zk(2);

-- View router state
SELECT * FROM routing_tier;

-- KEY INSIGHT: All routers have the SAME view of partition assignment!
-- Because ZooKeeper is the source of truth

================================================================================
STEP 7: DEMONSTRATE NODE FAILURE HANDLING
================================================================================

-- ZooKeeper handles node failures immediately

-- Step 1: Node 2 fails
SELECT zk_write('/cluster/nodes', jsonb_build_array(
    jsonb_build_object('node_id', 0, 'ip', '10.0.0.1', 'status', 'UP'),
    jsonb_build_object('node_id', 1, 'ip', '10.0.0.2', 'status', 'UP'),
    jsonb_build_object('node_id', 2, 'ip', '10.0.0.3', 'status', 'DOWN'),
    jsonb_build_object('node_id', 3, 'ip', '10.0.0.4', 'status', 'UP')
));

-- Step 2: Routers get notified via watch
SELECT sync_router_with_zk(1);
SELECT sync_router_with_zk(2);

-- Step 3: Rebalance partitions (move from failed node)
SELECT zk_write('/partitions/assignment', jsonb_build_object(
    0, 0, 1, 1, 2, 3, 3, 3,  -- Node 2's partitions moved to Node 3
    4, 0, 5, 1, 6, 3, 7, 3,
    8, 0, 9, 1, 10, 3, 11, 3
));

-- Step 4: Routers get notified immediately
SELECT sync_router_with_zk(1);
SELECT sync_router_with_zk(2);

-- View final router state
SELECT router_id, partition_map_version, last_sync FROM routing_tier;

-- KEY INSIGHT: All routers update IMMEDIATELY!
-- No eventual consistency window like in gossip

================================================================================
STEP 8: COMPARE GOSSIP VS ZOOKEEPER
================================================================================

-- Let's create a side-by-side comparison

-- Create comparison table
DROP TABLE IF EXISTS routing_comparison CASCADE;

CREATE TABLE routing_comparison (
    metric VARCHAR(50) PRIMARY KEY,
    gossip_value TEXT,
    zookeeper_value TEXT
);

INSERT INTO routing_comparison (metric, gossip_value, zookeeper_value) VALUES
    ('Architecture', 'Decentralized (peer-to-peer)', 'Centralized (coordination service)'),
    ('Consistency', 'Eventual (may be briefly stale)', 'Strong (always current)'),
    ('Failure Detection', 'Gossip-based (slower)', 'ZooKeeper heartbeat (faster)'),
    ('Routing Updates', 'O(log N) propagation time', 'Immediate (via watches)'),
    ('Bottleneck Risk', 'None', 'Coordination service (needs replication)'),
    ('Complexity', 'Lower (no extra service)', 'Higher (ZooKeeper cluster needed)'),
    ('Latency', 'Variable (may forward)', 'Consistent (always one hop)'),
    ('Used By', 'Cassandra, Riak', 'HBase, Kafka, MongoDB');

-- View comparison
SELECT * FROM routing_comparison;

================================================================================
STEP 9: REAL-WORLD PATTERN - HBase-STYLE
================================================================================

-- HBase uses ZooKeeper for:
--   1. Cluster metadata (which regions are where)
--   2. Leader election (for HMaster)
--   3. Region server registration

-- Let's simulate a simplified HBase-style setup

DROP TABLE IF EXISTS hbase_znodes CASCADE;
DROP TABLE IF EXISTS region_servers CASCADE;

-- ZooKeeper stores region (partition) locations
CREATE TABLE hbase_znodes (
    znode_path VARCHAR(100) PRIMARY KEY,
    data JSONB,
    version INTEGER DEFAULT 0
);

-- Region server registration
CREATE TABLE region_servers (
    server_id SERIAL PRIMARY KEY,
    hostname VARCHAR(50),
    port INTEGER,
    status VARCHAR(20) DEFAULT 'ACTIVE',
    regions JSONB DEFAULT '[]'::jsonb,
    last_heartbeat TIMESTAMP DEFAULT NOW()
);

-- Register region servers in ZooKeeper
INSERT INTO hbase_znodes (znode_path, data) VALUES
    ('/hbase/master', jsonb_build_object('master', 'hmaster1', 'status', 'active')),
    ('/hbase/rs', jsonb_build_array(
        jsonb_build_object('hostname', 'rs1', 'port', 60020),
        jsonb_build_object('hostname', 'rs2', 'port', 60020),
        jsonb_build_object('hostname', 'rs3', 'port', 60020)
    ));

-- Insert region servers
INSERT INTO region_servers (hostname, port, regions) VALUES
    ('rs1', 60020, '["region1", "region2"]'),
    ('rs2', 60020, 'region3'),
    ('rs3', 60020, '["region4", "region5"]');

-- Simulate client looking up region
CREATE OR REPLACE FUNCTION hbase_lookup_region(row_key VARCHAR)
RETURNS TABLE(hostname VARCHAR, port INTEGER) AS $$
DECLARE
    rs_info JSONB;
BEGIN
    -- In reality, this would be a two-step process:
    -- 1. Get region location from -ROOT- (or meta table in new versions)
    -- 2. Connect to region server

    -- Simplified: just return a random region server
    SELECT rs.hostname, rs.port INTO hostname, port
    FROM region_servers rs
    ORDER BY random()
    LIMIT 1;

    RETURN;
END;
$$ LANGUAGE plpgsql;

-- Client lookup
SELECT * FROM hbase_lookup_region('row_key_123');

-- This is how HBase/MongoDB work:
--   Client → ZooKeeper → Get region/shard location → Connect directly

================================================================================
STEP 10: WHEN TO USE ZOOKEEPER
================================================================================

-- Use ZooKeeper when:
--   ✅ Strong consistency is critical
--   ✅ You need immediate failure detection
--   ✅ You have a dedicated operations team
--   ✅ You can tolerate the coordination service bottleneck

-- Use Gossip when:
--   ✅ Eventual consistency is acceptable
--   ✅ You want to avoid single point of contention
--   ✅ You want simpler operations
--   ✅ You're building a P2P system

-- Hybrid approach (like MongoDB):
--   - Config servers (centralized ZooKeeper-like) for metadata
--   - mongos routers for query routing
--   - Shards handle actual data

================================================================================
SUMMARY: ZOOKEEPER COORDINATION
================================================================================

✅ ZOOKEEPER PROS:
  - Strong consistency (always current)
  - Immediate notifications via watches
  - Simple failure detection
  - Authoritative source of truth

❌ ZOOKEEPER CONS:
  - Coordination service is a bottleneck
  - Needs its own replication/HA
  - Additional infrastructure to manage
  - Extra hop in query path

⚠️  KEY TRADE-OFF:
  Strong consistency vs Scalability
    - ZooKeeper: Strong, but limits scaling
    - Gossip: Eventual, but scales better

📌 REAL-WORLD USAGE:
  - HBase: Region location, Master election
  - Kafka: Broker leadership, partition leadership
  - SolrCloud: Shard leadership
  - MongoDB: Config servers (similar concept)

================================================================================
NEXT STEPS:
================================================================================

1. Review both routing approaches:
   - Gossip: Decentralized, eventual
   - ZooKeeper: Centralized, strong

2. Read DDIA pp. 218-224 for more theory

3. You now understand all of Chapter 6:
   - Partitioning strategies
   - Secondary indexes
   - Rebalancing
   - Request routing

EOF
