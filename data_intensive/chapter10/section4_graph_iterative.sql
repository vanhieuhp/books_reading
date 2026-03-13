-- =============================================================================
-- Section 4: Graph Processing & Iterative Algorithms
-- From "Designing Data-Intensive Applications" - Chapter 10: Batch Processing
-- =============================================================================
-- Concept: Pregel/BSP - iterative message passing between vertices
-- SQL: Recursive CTEs for graph traversal
-- Key: MapReduce is bad at iterative algorithms (reads/writes entire dataset each iteration)
--      Spark is better (in-memory), but graph-specific systems (Pregel) are best
-- =============================================================================

-- Setup: Social graph data (follower relationships)
DROP TABLE IF EXISTS followers;
CREATE TABLE followers (
    follower_id INT,
    followee_id INT,
    PRIMARY KEY (follower_id, followee_id)
);

-- Insert sample social graph
-- alice (1) follows bob (2), charlie (3)
-- bob (2) follows charlie (3)
-- charlie (3) follows alice (1)
-- diana (4) follows alice (1), bob (2), charlie (3)
-- eve (5) follows diana (4)
INSERT INTO followers (follower_id, followee_id) VALUES
(1, 2),  -- alice follows bob
(1, 3),  -- alice follows charlie
(2, 3),  -- bob follows charlie
(3, 1),  -- charlie follows alice
(4, 1),  -- diana follows alice
(4, 2),  -- diana follows bob
(4, 3),  -- diana follows charlie
(5, 4);  -- eve follows diana

-- User names for readability
DROP TABLE IF EXISTS user_names;
CREATE TABLE user_names (user_id INT, username VARCHAR(50));
INSERT INTO user_names VALUES
(1, 'alice'), (2, 'bob'), (3, 'charlie'), (4, 'diana'), (5, 'eve');

-- =============================================================================
-- EXERCISE 4-1: Recursive CTE - Find all reachable nodes (BFS traversal)
-- Pregel: Start from seed vertices, propagate messages iteratively
-- SQL: Recursive CTE mimics iterative graph traversal
-- =============================================================================
-- Find all users reachable from alice (direct + indirect followers)
-- Similar to: Starting from 'alice' vertex, traverse the graph
-- This is like Pregel's message passing model where vertices propagate to neighbors

-- PostgreSQL recursive CTE syntax
WITH RECURSIVE reachable AS (
    -- Base case: Start from alice (user_id = 1)
    SELECT 1 AS user_id, 0 AS distance
    FROM user_names
    WHERE user_id = 1

    UNION ALL

    -- Recursive case: Follow the graph (find who they follow)
    SELECT
        f.followee_id,
        r.distance + 1
    FROM reachable r
    JOIN followers f ON r.user_id = f.follower_id
    WHERE r.distance < 3  -- Limit depth (like max supersteps)
)
SELECT
    un.username,
    MIN(r.distance) AS min_distance
FROM reachable r
JOIN user_names un ON r.user_id = un.user_id
WHERE r.user_id != 1  -- Exclude starting node
GROUP BY un.username
ORDER BY min_distance;

-- =============================================================================
-- EXERCISE 4-2: Find followers of followers (2-hop network)
-- Pregel: Each superstep, vertices aggregate messages from incoming edges
-- SQL: Two-level recursive query
-- =============================================================================
-- Find everyone that alice can reach within 2 hops

WITH RECURSIVE two_hop AS (
    -- Base case: Direct followers
    SELECT
        f.followee_id AS user_id,
        1 AS hop
    FROM followers f
    WHERE f.follower_id = 1  -- alice

    UNION

    -- Second hop: Followers of followers
    SELECT
        f2.followee_id,
        2 AS hop
    FROM two_hop th
    JOIN followers f2 ON th.user_id = f2.follower_id
    WHERE th.hop = 1
)
SELECT DISTINCT
    un.username,
    th.hop
FROM two_hop th
JOIN user_names un ON th.user_id = un.user_id
WHERE th.user_id != 1
ORDER BY hop, username;

-- =============================================================================
-- EXERCISE 4-3: PageRank-style iteration (simplified)
-- Pregel: Each superstep, vertices aggregate incoming messages
-- SQL: Iterative computation with recursive CTE
-- =============================================================================
-- Simplified PageRank: Calculate influence score through iterations
-- In each iteration: a user's rank is distributed to who they follow

-- Initial setup: Each user starts with equal influence
DROP TABLE IF EXISTS user_ranks;
CREATE TABLE user_ranks AS
SELECT
    user_id,
    1.0 AS rank_score,
    1 AS iteration
FROM user_names;

-- Run iterations (simplified - in reality this would be more complex)
-- Each iteration: distribute rank to followees based on out-degree
WITH RECURSIVE page_rank_iteration AS (
    -- Initial ranks (iteration 1)
    SELECT
        user_id,
        1.0 AS rank
    FROM user_names

    UNION ALL

    -- Iterative update: rank flows to followees
    -- New rank for user = sum of (neighbor_rank / neighbor_out_degree)
    SELECT
        f.followee_id,
        SUM(pri.rank / outdegree.out_count) AS new_rank
    FROM page_rank_iteration pri
    JOIN followers f ON pri.user_id = f.follower_id
    JOIN (
        SELECT follower_id, COUNT(*) AS out_count
        FROM followers
        GROUP BY follower_id
    ) outdegree ON f.follower_id = outdegree.follower_id
    GROUP BY f.followee_id
    LIMIT 10  -- Limit iterations (supersteps) - in real PageRank this would iterate
)
SELECT
    un.username,
    pri.rank AS influence_score
FROM page_rank_iteration pri
JOIN user_names un ON pri.user_id = un.user_id
ORDER BY pri.rank DESC;

-- Note: Full PageRank requires:
-- 1. Multiple iterations (supersteps)
-- 2. Damping factor (teleportation)
-- 3. Convergence detection
-- This demonstrates the concept of iterative rank distribution

-- =============================================================================
-- EXERCISE 4-4: Finding Shortest Path (Dijkstra-style)
-- Pregel: Vertices exchange distance messages in each superstep
-- SQL: Recursive CTE for shortest path finding
-- =============================================================================
-- Find shortest path from eve (5) to charlie (3)
-- Path: eve → diana → alice → charlie

-- Actual query to find path from eve to charlie
WITH RECURSIVE find_path AS (
    -- Base case: Start from eve
    SELECT
        5 AS start_user,
        5 AS current_user,
        ARRAY['eve'] AS path,
        0 AS distance

    UNION ALL

    -- Recursive: Follow connections
    SELECT
        fp.start_user,
        f.followee_id,
        fp.path || un.username,
        fp.distance + 1
    FROM find_path fp
    JOIN followers f ON fp.current_user = f.follower_id
    JOIN user_names un ON f.followee_id = un.user_id
    -- Avoid cycles: don't revisit users already in path
    WHERE un.username != ALL(fp.path)
    AND fp.distance < 5  -- Max depth limit
)
SELECT
    path,
    distance
FROM find_path
WHERE current_user = 3  -- charlie
ORDER BY distance
LIMIT 1;

-- =============================================================================
-- EXERCISE 4-5: Count reachable nodes at each depth
-- Pregel: Can count messages at each superstep
-- SQL: Recursive CTE with depth tracking
-- =============================================================================
-- Count how many users are reachable at each distance from alice

WITH RECURSIVE depth_counts AS (
    -- Start from alice
    SELECT 1 AS user_id, 0 AS depth

    UNION ALL

    -- Traverse to followers
    SELECT
        f.followee_id,
        dc.depth + 1
    FROM depth_counts dc
    JOIN followers f ON dc.user_id = f.follower_id
    WHERE dc.depth < 3
)
SELECT
    depth,
    COUNT(DISTINCT user_id) AS reachable_count
FROM depth_counts
WHERE user_id != 1  -- Exclude alice herself
GROUP BY depth
ORDER BY depth;

-- =============================================================================
-- EXERCISE 4-6: Detect cycles in graph
-- Pregel: Can detect if vertices receive messages they've already seen
-- SQL: Recursive CTE can detect cycles
-- =============================================================================
-- Find if there are cycles in the follower graph

WITH RECURSIVE find_cycles AS (
    -- Start from each user
    SELECT
        user_id AS start_user,
        user_id AS current_user,
        ARRAY[user_id] AS path,
        FALSE AS has_cycle
    FROM user_names

    UNION ALL

    -- Follow connections
    SELECT
        fc.start_user,
        f.followee_id,
        fc.path || f.followee_id,
        f.followee_id = ANY(fc.path)  -- Cycle if already in path
    FROM find_cycles fc
    JOIN followers f ON fc.current_user = f.follower_id
    WHERE
        NOT fc.has_cycle  -- Stop if cycle already found
        AND array_length(fc.path, 1) < 5  -- Limit depth
)
SELECT DISTINCT
    start_user,
    CASE WHEN has_cycle THEN 'Has Cycle' ELSE 'No Cycle' END AS cycle_status
FROM find_cycles
WHERE has_cycle = TRUE;

-- =============================================================================
-- EXERCISE 4-7: Mutual/Reciprocal connections
-- Pregel: Can check bidirectional edges
-- SQL: Self-join to find mutual follows
-- =============================================================================
-- Find mutual followers (A follows B and B follows A)

SELECT
    un1.username AS user_a,
    un2.username AS user_b
FROM followers f1
JOIN followers f2 ON
    f1.follower_id = f2.followee_id
    AND f1.followee_id = f2.follower_id
JOIN user_names un1 ON f1.follower_id = un1.user_id
JOIN user_names un2 ON f1.followee_id = un2.user_id
WHERE f1.follower_id < f1.followee_id;  -- Avoid duplicates

-- =============================================================================
-- SUMMARY: Pregel/BSP to SQL Mapping
-- =============================================================================
/*
┌─────────────────────────────────────────────────────────────────────────────┐
│ Pregel/BSP Concept            │ SQL Equivalent                                │
├─────────────────────────────────────────────────────────────────────────────┤
│ Superstep (iteration)        │ Recursive CTE iteration                      │
│ Vertex                      │ Table row                                    │
│ Edge                        │ Foreign key / relationship table              │
│ Message passing             │ JOIN in recursive case                      │
│ Vertex program              │ Aggregation in recursive case                │
│ Bulk Synchronous Parallel   │ Recursive CTE with UNION ALL                 │
│ PageRank                    │ Iterative recursive CTE with rank distribution│
│ Shortest path               │ Recursive CTE with path tracking             │
│ Connected components       │ Recursive CTE with union-find pattern         │
│ Cycle detection            │ Check if node in current path array          │
└─────────────────────────────────────────────────────────────────────────────┘

Why MapReduce is bad for graphs:
- Each iteration reads/writes entire graph to HDFS
- Graph algorithms need many iterations (PageRank: 20-30)
- Spark is better (in-memory), but Pregel is optimal

Key SQL pattern for iterative algorithms:
  WITH RECURSIVE cte AS (
      SELECT ... -- base case (initial state)

      UNION ALL

      SELECT ... -- recursive case
      FROM cte JOIN edges ON ...
  )
  SELECT * FROM cte;
*/
