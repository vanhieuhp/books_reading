-- =============================================================================
-- Section 2: MapReduce Concepts (Map → Shuffle → Reduce)
-- From "Designing Data-Intensive Applications" - Chapter 10: Batch Processing
-- =============================================================================
-- Concept: Map (extract key-value) → Shuffle (sort/group by key) → Reduce (aggregate)
-- SQL: SELECT with GROUP BY handles both shuffle and reduce
-- =============================================================================

-- Setup: User activity data for join demonstrations
DROP TABLE IF EXISTS users;
CREATE TABLE users (
    user_id INT PRIMARY KEY,
    username VARCHAR(50),
    email VARCHAR(100),
    registration_date DATE,
    country VARCHAR(50)
);

DROP TABLE IF EXISTS user_activities;
CREATE TABLE user_activities (
    activity_id INT PRIMARY KEY,
    user_id INT,
    activity_type VARCHAR(50),  -- 'login', 'click', 'purchase', 'view'
    activity_timestamp TIMESTAMP,
    amount DECIMAL(10,2)
);

-- Insert users
INSERT INTO users (user_id, username, email, registration_date, country) VALUES
(1, 'alice', 'alice@example.com', '2023-01-15', 'USA'),
(2, 'bob', 'bob@example.com', '2023-02-20', 'UK'),
(3, 'charlie', 'charlie@example.com', '2023-03-10', 'USA'),
(4, 'diana', 'diana@example.com', '2023-04-05', 'Canada'),
(5, 'eve', 'eve@example.com', '2023-05-12', 'USA');

-- Insert activities (more for user 1 to demonstrate skew)
INSERT INTO user_activities (activity_id, user_id, activity_type, activity_timestamp, amount) VALUES
(1, 1, 'login', '2024-01-15 08:00:00', 0),
(2, 1, 'view', '2024-01-15 08:01:00', 0),
(3, 1, 'click', '2024-01-15 08:02:00', 0),
(4, 1, 'purchase', '2024-01-15 08:03:00', 99.99),
(5, 1, 'login', '2024-01-15 09:00:00', 0),
(6, 1, 'view', '2024-01-15 09:01:00', 0),
(7, 1, 'click', '2024-01-15 09:02:00', 0),
(8, 1, 'purchase', '2024-01-15 09:03:00', 149.99),
(9, 2, 'login', '2024-01-15 10:00:00', 0),
(10, 2, 'view', '2024-01-15 10:01:00', 0),
(11, 3, 'login', '2024-01-15 11:00:00', 0),
(12, 3, 'purchase', '2024-01-15 11:01:00', 79.99),
(13, 4, 'login', '2024-01-15 12:00:00', 0),
(14, 5, 'login', '2024-01-15 13:00:00', 0);

-- =============================================================================
-- EXERCISE 2-1: Map Phase - Emit key-value pairs
-- MapReduce: For each record, emit (key, value)
-- SQL: SELECT that extracts the key field
-- =============================================================================
-- In MapReduce, the Map phase transforms input records into key-value pairs.
-- Each record is processed independently and emits zero or more key-value pairs.

-- Example: Map each activity to (user_id, activity_type)
SELECT
    user_id AS key,
    activity_type AS value
FROM user_activities;

-- Alternative: Map to (user_id, 1) for counting
SELECT
    user_id AS map_key,
    1 AS map_value
FROM user_activities;

-- =============================================================================
-- EXERCISE 2-2: Shuffle + Reduce - Group by key and count
-- MapReduce: Shuffle groups by key, Reduce counts values
-- SQL: GROUP BY implements both shuffle and reduce
-- =============================================================================
-- The shuffle phase in MapReduce sorts all mapper outputs by key and groups them.
-- The reduce phase then processes all values for each key.

-- SQL's GROUP BY does both: shuffle (sort/group) + reduce (aggregate)
SELECT
    user_id,
    COUNT(*) AS activity_count  -- Reduce: count all values for each key
FROM user_activities
GROUP BY user_id;

-- =============================================================================
-- EXERCISE 2-3: Reduce with Multiple Aggregations
-- MapReduce: Multiple reducers for different metrics
-- SQL: Multiple aggregate functions in one GROUP BY
-- =============================================================================
-- In MapReduce, you might run multiple MapReduce jobs for different metrics.
-- SQL can compute multiple aggregations in a single pass.

SELECT
    user_id,
    COUNT(*) AS total_activities,
    SUM(CASE WHEN activity_type = 'purchase' THEN amount ELSE 0 END) AS total_revenue,
    COUNT(CASE WHEN activity_type = 'purchase' THEN 1 END) AS purchase_count,
    MAX(activity_timestamp) AS last_activity,
    AVG(CASE WHEN activity_type = 'purchase' THEN amount END) AS avg_purchase
FROM user_activities
GROUP BY user_id;

-- =============================================================================
-- EXERCISE 2-4: Sort-Merge Join (MapReduce Pattern)
-- Both datasets emit key-value pairs with join key
-- Shuffle groups by join key
-- Reduce performs the join
-- =============================================================================
-- In MapReduce Sort-Merge Join:
-- 1. Map both datasets to (join_key, record)
-- 2. Shuffle groups by join_key (all matching records together)
-- 3. Reducer sees both sides and performs the join

-- SQL equivalent: JOIN + GROUP BY
SELECT
    u.user_id,
    u.username,
    u.email,
    COUNT(a.activity_id) AS total_activities,
    COALESCE(SUM(a.amount), 0) AS total_revenue
FROM users u
LEFT JOIN user_activities a ON u.user_id = a.user_id
GROUP BY u.user_id, u.username, u.email;

-- =============================================================================
-- EXERCISE 2-5: Broadcast Hash Join (Small table fit in memory)
-- MapReduce: Load small table into hash map on each mapper
-- SQL: In PostgreSQL this is automatically optimized for small tables
-- =============================================================================
-- When one dataset is small (dimension table), it can be broadcast to all nodes.

-- Create small dimension table
DROP TABLE IF EXISTS countries;
CREATE TABLE countries (
    country_code VARCHAR(2) PRIMARY KEY,
    country_name VARCHAR(50),
    region VARCHAR(50)
);

INSERT INTO countries (country_code, country_name, region) VALUES
('USA', 'United States', 'North America'),
('UK', 'United Kingdom', 'Europe'),
('CA', 'Canada', 'North America');

-- The query planner will use hash join (broadcast) for small table
SELECT
    u.username,
    u.country,
    c.country_name,
    c.region
FROM users u
JOIN countries c ON u.country = c.country_code;

-- =============================================================================
-- EXERCISE 2-6: Partitioned Hash Join
-- Both datasets partitioned the same way (same key, same partition count)
-- Each mapper only reads corresponding partition from each dataset
-- =============================================================================
-- In SQL: Both tables partitioned on the same key

-- Create partitioned version (simulated)
DROP TABLE IF EXISTS orders;
CREATE TABLE orders (
    order_id INT PRIMARY KEY,
    customer_id INT,
    order_date DATE,
    status VARCHAR(20),
    total_amount DECIMAL(10,2)
);

DROP TABLE IF EXISTS order_items;
CREATE TABLE order_items (
    item_id INT PRIMARY KEY,
    order_id INT,
    product_id INT,
    quantity INT,
    unit_price DECIMAL(10,2)
);

INSERT INTO orders (order_id, customer_id, order_date, status, total_amount) VALUES
(1, 101, '2024-01-15', 'completed', 150.00),
(2, 102, '2024-01-15', 'completed', 200.00),
(3, 101, '2024-01-16', 'pending', 75.00);

INSERT INTO order_items (item_id, order_id, product_id, quantity, unit_price) VALUES
(1, 1, 1001, 2, 25.00),
(2, 1, 1002, 1, 100.00),
(3, 2, 1001, 4, 25.00);

-- Partitioned join: Both tables partitioned on order_id
SELECT
    o.order_id,
    o.customer_id,
    oi.product_id,
    oi.quantity
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id;

-- =============================================================================
-- EXERCISE 2-7: Handling Skew (Hot Keys)
-- Problem: User 1 has many more activities than others (celebrity user)
-- Solution: Distribute hot key records across multiple reducers
-- SQL: Manual partitioning for hot keys
-- =============================================================================
-- Detect skew: See the distribution
SELECT
    user_id,
    COUNT(*) AS activity_count
FROM user_activities
GROUP BY user_id
ORDER BY activity_count DESC;

-- Handle skew by splitting hot users manually (simulating Pig's Skewed Join)
-- Split into "hot" (user_id = 1) and "normal" partitions
SELECT
    'hot_partition' AS partition_type,
    user_id,
    COUNT(*) AS activity_count
FROM user_activities
WHERE user_id = 1
GROUP BY user_id

UNION ALL

SELECT
    'normal_partition' AS partition_type,
    user_id,
    COUNT(*) AS activity_count
FROM user_activities
WHERE user_id != 1
GROUP BY user_id;

-- =============================================================================
-- SUMMARY: MapReduce to SQL Mapping
-- =============================================================================
/*
┌─────────────────────────────────────────────────────────────────────────────┐
│ MapReduce Phase         │ SQL Equivalent                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│ Map: Extract key-value │ SELECT key, value FROM table                     │
│ Shuffle: Group by key  │ GROUP BY key                                     │
│ Reduce: Aggregate      │ COUNT(*), SUM(col), etc.                         │
│ Sort-Merge Join        │ JOIN + GROUP BY                                  │
│ Broadcast Hash Join    │ JOIN (small table broadcast)                     │
│ Partitioned Join       │ JOIN on partitioned key                          │
│ Handle Hot Keys        │ Split query by hot key (UNION ALL)               │
└─────────────────────────────────────────────────────────────────────────────┘

MapReduce Word Count Example:
  Map: (word, 1) for each word
  Shuffle: group by word
  Reduce: SUM(count) for each word

  SQL: SELECT word, COUNT(*) FROM table GROUP BY word
*/
