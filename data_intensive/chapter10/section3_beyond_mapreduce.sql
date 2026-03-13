-- =============================================================================
-- Section 3: Beyond MapReduce - DAGs, In-Memory Processing
-- From "Designing Data-Intensive Applications" - Chapter 10: Batch Processing
-- =============================================================================
-- Concept: Spark DAG - operators pipelined without writing intermediate to disk
-- SQL: Multiple CTEs chained together (no intermediate tables needed)
-- Key Difference from MapReduce: Intermediate data stays in memory (not HDFS)
-- =============================================================================

-- Setup: Order data for complex pipeline
DROP TABLE IF EXISTS orders;
CREATE TABLE orders (
    order_id INT PRIMARY KEY,
    customer_id INT,
    order_date DATE,
    status VARCHAR(20),  -- 'pending', 'completed', 'cancelled'
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
(3, 101, '2024-01-16', 'pending', 75.00),
(4, 103, '2024-01-16', 'cancelled', 50.00),
(5, 102, '2024-01-17', 'completed', 300.00),
(6, 104, '2024-01-17', 'completed', 120.00),
(7, 101, '2024-01-18', 'completed', 90.00);

INSERT INTO order_items (item_id, order_id, product_id, quantity, unit_price) VALUES
(1, 1, 1001, 2, 25.00),
(2, 1, 1002, 1, 100.00),
(3, 2, 1001, 4, 25.00),
(4, 2, 1003, 2, 50.00),
(5, 3, 1001, 3, 25.00),
(6, 4, 1002, 1, 50.00),
(7, 5, 1003, 6, 50.00),
(8, 6, 1001, 1, 25.00),
(9, 6, 1002, 1, 95.00),
(10, 7, 1001, 3, 30.00);

-- =============================================================================
-- EXERCISE 3-1: DAG with CTEs - Pipelined operations (no intermediate tables)
-- Spark: Read → Filter → Map → Aggregate → Filter → Write
-- SQL: Chained CTEs (each CTE feeds into the next, in-memory pipeline)
-- =============================================================================
-- In Spark, a DAG represents a pipeline of transformations without materializing
-- intermediate results to disk. SQL CTEs do the same - each step feeds into the next.

-- Equivalent to Spark DAG with multiple transformations:
-- Read → Filter (Map with WHERE) → Join (Map with enrich) → Aggregate (Reduce) → Filter → Write

-- Step 1: Read and Filter (MapReduce: Map phase with filtering)
WITH filtered_orders AS (
    SELECT
        order_id,
        customer_id,
        total_amount,
        status
    FROM orders
    WHERE status = 'completed'
),

-- Step 2: Join with items (Map: enrich with more data)
order_details AS (
    SELECT
        f.order_id,
        f.customer_id,
        f.total_amount,
        oi.product_id,
        oi.quantity,
        oi.unit_price,
        (oi.quantity * oi.unit_price) AS line_total
    FROM filtered_orders f
    JOIN order_items oi ON f.order_id = oi.order_id
),

-- Step 3: Aggregate by customer (Reduce phase)
customer_summary AS (
    SELECT
        customer_id,
        COUNT(DISTINCT order_id) AS order_count,
        SUM(total_amount) AS total_revenue,
        SUM(line_total) AS items_total
    FROM order_details
    GROUP BY customer_id
),

-- Step 4: Filter final results (Post-reduce filtering)
top_customers AS (
    SELECT
        customer_id,
        order_count,
        total_revenue
    FROM customer_summary
    WHERE order_count >= 2
    ORDER BY total_revenue DESC
)

SELECT * FROM top_customers;

-- =============================================================================
-- EXERCISE 3-2: Window Functions - Pipelined aggregations without grouping
-- Spark: Can apply aggregations while keeping individual rows
-- SQL: Window functions (OVER clause)
-- =============================================================================
-- Window functions are like Spark's transformations that don't reduce the row count.
-- They compute aggregations across a "window" of rows while keeping each row.

-- Compare each order to customer's average (window function)
SELECT
    o.order_id,
    o.customer_id,
    o.total_amount,
    AVG(o.total_amount) OVER (PARTITION BY o.customer_id) AS customer_avg,
    o.total_amount - AVG(o.total_amount) OVER (PARTITION BY o.customer_id) AS diff_from_avg,
    RANK() OVER (PARTITION BY o.customer_id ORDER BY o.total_amount DESC) AS order_rank
FROM orders o
WHERE o.status = 'completed';

-- =============================================================================
-- EXERCISE 3-3: Running Total - Cumulative aggregations (streaming-style)
-- Spark: Can compute running totals without grouping all data
-- SQL: Window functions with ORDER BY (cumulative)
-- =============================================================================
-- Running totals simulate stream processing within batch SQL
-- Similar to Spark's mapPartitions with running state

SELECT
    order_id,
    order_date,
    total_amount,
    SUM(total_amount) OVER (ORDER BY order_date, order_id) AS running_total,
    COUNT(*) OVER (ORDER BY order_date, order_id) AS running_count,
    AVG(total_amount) OVER (ORDER BY order_date, order_id ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_avg
FROM orders
WHERE status = 'completed'
ORDER BY order_date, order_id;

-- =============================================================================
-- EXERCISE 3-4: Multiple Window Functions - Multiple aggregations in one pass
-- Spark: Can cache RDD and run multiple transformations
-- SQL: Multiple window functions in one query
-- =============================================================================
-- Like Spark caching an RDD and applying multiple operations

SELECT
    order_id,
    customer_id,
    total_amount,
    -- Different windows, same data
    RANK() OVER (PARTITION BY customer_id ORDER BY total_amount DESC) AS by_customer,
    RANK() OVER (ORDER BY total_amount DESC) AS global_rank,
    SUM(total_amount) OVER (PARTITION BY customer_id) AS customer_total,
    total_amount / SUM(total_amount) OVER (PARTITION BY customer_id) * 100 AS pct_of_customer
FROM orders
WHERE status = 'completed';

-- =============================================================================
-- EXERCISE 3-5: Multi-Level Aggregation (Similar to Spark's multiple passes)
-- Spark: Can cache intermediate RDDs for multiple operations
-- SQL: Materialized subquery or CTE with multiple consumers
-- =============================================================================
-- Create base aggregation once, use multiple times (like caching an RDD)

WITH daily_stats AS (
    SELECT
        order_date,
        COUNT(*) AS order_count,
        SUM(total_amount) AS daily_revenue,
        AVG(total_amount) AS avg_order_value
    FROM orders
    WHERE status = 'completed'
    GROUP BY order_date
)

SELECT
    -- Query 1: Daily metrics
    ds.order_date,
    ds.order_count,
    ds.daily_revenue,
    -- Query 2: Compare to overall average (uses same base)
    ds.daily_revenue / (SELECT AVG(daily_revenue) FROM daily_stats) AS ratio_to_avg
FROM daily_stats ds
ORDER BY ds.order_date;

-- =============================================================================
-- EXERCISE 3-6: In-Memory vs Disk - CTE vs Temp Table
-- Spark: RDDs stay in memory; can checkpoint to disk for very long lineages
-- SQL: CTEs are optimization hints (may be inlined); temp tables force materialization
-- =============================================================================
-- This demonstrates the difference between in-memory (CTE) and disk (temp table)

-- CTE: Optimizer may keep in memory or inline (Spark-like behavior)
WITH in_memory_calc AS (
    SELECT customer_id, SUM(total_amount) AS total
    FROM orders
    WHERE status = 'completed'
    GROUP BY customer_id
)
SELECT * FROM in_memory_calc WHERE total > 100;

-- Temp table: Forces materialization to disk (MapReduce-like behavior)
DROP TABLE IF EXISTS temp_agg;
CREATE TEMP TABLE temp_agg AS
SELECT customer_id, SUM(total_amount) AS total
FROM orders
WHERE status = 'completed'
GROUP BY customer_id;

SELECT * FROM temp_agg WHERE total > 100;

-- =============================================================================
-- SUMMARY: Spark/DAG to SQL Mapping
-- =============================================================================
/*
┌─────────────────────────────────────────────────────────────────────────────┐
│ Spark/DAG Concept              │ SQL Equivalent                             │
├─────────────────────────────────────────────────────────────────────────────┤
│ DAG (Directed Acyclic Graph)  │ Chained CTEs                               │
│ RDD (in-memory data)          │ CTEs stay in memory (optimization)         │
│ map() transformation          │ SELECT with column transformations         │
│ filter() transformation       │ WHERE clause                               │
│ reduceByKey()                │ GROUP BY + aggregate functions              │
│ join()                       │ JOIN clause                                │
│ flatMap()                    │ SELECT with UNNEST/explode                 │
│ cache() / persist()          │ CTEs or temp tables                        │
│ checkpoint()                 │ Temp tables (materialized)                 │
│ Window functions             │ OVER clause (non-reducing aggregations)     │
│ Actions (collect, count)     │ Final SELECT                               │
└─────────────────────────────────────────────────────────────────────────────┘

Key Difference from MapReduce:
- MapReduce: Each job writes to HDFS (disk I/O + replication)
- Spark DAG: Operators pipelined in memory, only final write to disk
- Result: 10-100x faster for iterative algorithms
*/
