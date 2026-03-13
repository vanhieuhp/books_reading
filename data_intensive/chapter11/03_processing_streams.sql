-- ==============================================================================
-- Chapter 11: Stream Processing - Section 3
-- Processing Streams: Analytics, Aggregations, Materialized Views
-- ==============================================================================
-- Database: PostgreSQL
-- Focus: Conceptual Simulation + Real-time Analytics
-- ==============================================================================

-- ==============================================================================
-- PART 1: Stream Processing Fundamentals
-- ==============================================================================

-- Create a clickstream event table (simulating real-time events)
DROP TABLE IF EXISTS clickstream_events CASCADE;
CREATE TABLE clickstream_events (
    event_id     BIGSERIAL PRIMARY KEY,
    event_time   TIMESTAMP NOT NULL DEFAULT NOW(),
    session_id   VARCHAR(50) NOT NULL,
    user_id      VARCHAR(50),
    event_type   VARCHAR(50) NOT NULL,  -- page_view, click, purchase
    page_url     VARCHAR(500),
    product_id   INT,
    amount       DECIMAL(10,2),
    country      VARCHAR(50)
);

-- Insert sample clickstream data
INSERT INTO clickstream_events (event_time, session_id, user_id, event_type, page_url, product_id, amount, country) VALUES
    ('2026-03-13 10:00:00', 'sess_001', 'user_1', 'page_view', '/home', NULL, NULL, 'US'),
    ('2026-03-13 10:00:01', 'sess_001', 'user_1', 'page_view', '/products', NULL, NULL, 'US'),
    ('2026-03-13 10:00:02', 'sess_001', 'user_1', 'click', '/products/42', 42, NULL, 'US'),
    ('2026-03-13 10:00:03', 'sess_001', 'user_1', 'add_to_cart', '/cart', 42, 29.99, 'US'),
    ('2026-03-13 10:00:10', 'sess_002', 'user_2', 'page_view', '/home', NULL, NULL, 'UK'),
    ('2026-03-13 10:00:11', 'sess_002', 'user_2', 'page_view', '/products', NULL, NULL, 'UK'),
    ('2026-03-13 10:00:12', 'sess_002', 'user_2', 'purchase', '/checkout', 42, 29.99, 'UK'),
    ('2026-03-13 10:00:15', 'sess_003', NULL, 'page_view', '/home', NULL, NULL, 'DE'),
    ('2026-03-13 10:00:20', 'sess_004', 'user_3', 'page_view', '/home', NULL, NULL, 'US'),
    ('2026-03-13 10:00:21', 'sess_004', 'user_3', 'purchase', '/checkout', 99, 99.99, 'US');

-- ==============================================================================
-- EXERCISE 3.1: Basic Stream Aggregations
-- ==============================================================================
-- Question: How do we calculate metrics from a stream?

-- Count events per type
SELECT event_type, COUNT(*) as event_count
FROM clickstream_events
GROUP BY event_type
ORDER BY event_count DESC;

-- Total revenue from purchases
SELECT
    SUM(amount) as total_revenue,
    COUNT(*) as purchase_count,
    AVG(amount) as avg_order_value
FROM clickstream_events
WHERE event_type = 'purchase';

-- Events by country
SELECT country, COUNT(*) as event_count, SUM(amount) as revenue
FROM clickstream_events
GROUP BY country
ORDER BY revenue DESC NULLS LAST;

-- ==============================================================================
-- PART 2: Continuous Aggregation (Materialized View Pattern)
-- ==============================================================================

-- ==============================================================================
-- EXERCISE 3.2: Real-time Aggregation with Materialized Views
-- ==============================================================================
-- Question: How do we maintain real-time aggregates?

-- Create a materialized view for real-time metrics
DROP MATERIALIZED VIEW IF EXISTS real_time_metrics CASCADE;
CREATE MATERIALIZED VIEW real_time_metrics AS
SELECT
    -- Time-based metrics
    DATE_TRUNC('minute', event_time) as minute,

    -- Event counts
    COUNT(*) as total_events,
    COUNT(DISTINCT session_id) as unique_sessions,
    COUNT(DISTINCT user_id) as unique_users,

    -- Revenue metrics
    SUM(CASE WHEN event_type = 'purchase' THEN amount ELSE 0 END) as revenue,
    COUNT(CASE WHEN event_type = 'purchase' THEN 1 END) as purchase_count,

    -- Conversion funnel
    COUNT(CASE WHEN event_type = 'page_view' THEN 1 END) as page_views,
    COUNT(CASE WHEN event_type = 'click' THEN 1 END) as clicks,
    COUNT(CASE WHEN event_type = 'add_to_cart' THEN 1 END) as add_to_carts,
    COUNT(CASE WHEN event_type = 'purchase' THEN 1 END) as purchases

FROM clickstream_events
GROUP BY DATE_TRUNC('minute', event_time);

-- View current metrics
SELECT * FROM real_time_metrics ORDER BY minute;

-- ==============================================================================
-- PART 3: Complex Event Processing (CEP) Pattern
-- ==============================================================================

-- ==============================================================================
-- EXERCISE 3.3: Pattern Detection in Stream
-- ==============================================================================
-- Question: How do we detect patterns like "3 failed login attempts in 5 minutes"?

-- Create login attempt events
DROP TABLE IF EXISTS login_events CASCADE;
CREATE TABLE login_events (
    event_id     BIGSERIAL PRIMARY KEY,
    event_time   TIMESTAMP NOT NULL DEFAULT NOW(),
    user_id      VARCHAR(50) NOT NULL,
    ip_address   VARCHAR(50),
    status       VARCHAR(20) NOT NULL,  -- success, failed
    failure_reason VARCHAR(100)
);

-- Insert sample login events (user_1 has 3 failed attempts)
INSERT INTO login_events (event_time, user_id, ip_address, status, failure_reason) VALUES
    ('2026-03-13 10:00:00', 'user_1', '192.168.1.1', 'failed', 'wrong_password'),
    ('2026-03-13 10:00:01', 'user_1', '192.168.1.1', 'failed', 'wrong_password'),
    ('2026-03-13 10:00:02', 'user_1', '192.168.1.1', 'failed', 'wrong_password'),
    ('2026-03-13 10:00:10', 'user_2', '10.0.0.1', 'success', NULL),
    ('2026-03-13 10:00:15', 'user_1', '192.168.1.1', 'success', NULL);  -- Successful after failures

-- Detect users with 3+ failed attempts within 5 minutes
WITH failed_logins AS (
    SELECT
        user_id,
        event_time,
        ip_address,
        LAG(event_time) OVER (PARTITION BY user_id ORDER BY event_time) as prev_failure_time,
        ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY event_time) as fail序号
    FROM login_events
    WHERE status = 'failed'
),
failure_streaks AS (
    SELECT
        user_id,
        event_time,
        ip_address,
        prev_failure_time,
        CASE
            WHEN prev_failure_time IS NULL OR (event_time - prev_failure_time) > INTERVAL '5 minutes'
            THEN 1
            ELSE 0
        END as new_streak
    FROM failed_logins
),
streak_counts AS (
    SELECT
        user_id,
        event_time,
        SUM(new_streak) OVER (PARTITION BY user_id ORDER BY event_time) as streak_id
    FROM failure_streaks
)
SELECT
    user_id,
    MIN(event_time) as streak_start,
    MAX(event_time) as streak_end,
    COUNT(*) as failed_attempts,
    MAX(ip_address) as ip_address
FROM streak_counts
GROUP BY user_id, streak_id
HAVING COUNT(*) >= 3;

-- ==============================================================================
-- PART 4: Funnel Analysis
-- ==============================================================================

-- ==============================================================================
-- EXERCISE 3.4: Conversion Funnel Analysis
-- ==============================================================================
-- Question: How do we track user progression through a conversion funnel?

-- Analyze funnel: page_view -> add_to_cart -> purchase
WITH user_funnel AS (
    SELECT
        session_id,
        MAX(CASE WHEN event_type = 'page_view' THEN 1 ELSE 0 END) as viewed_product,
        MAX(CASE WHEN event_type = 'add_to_cart' THEN 1 ELSE 0 END) as added_to_cart,
        MAX(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END) as purchased
    FROM clickstream_events
    GROUP BY session_id
)
SELECT
    COUNT(*) as total_sessions,
    SUM(viewed_product) as viewed_product_count,
    SUM(added_to_cart) as added_to_cart_count,
    SUM(purchased) as purchased_count,
    -- Funnel conversion rates
    ROUND(SUM(added_to_cart)::numeric / NULLIF(SUM(viewed_product), 0) * 100, 2) as view_to_cart_rate,
    ROUND(SUM(purchased)::numeric / NULLIF(SUM(added_to_cart), 0) * 100, 2) as cart_to_purchase_rate,
    ROUND(SUM(purchased)::numeric / NULLIF(SUM(viewed_product), 0) * 100, 2) as overall_conversion_rate
FROM user_funnel;

-- ==============================================================================
-- PART 5: Stream Analytics - Moving Averages & Percentiles
-- ==============================================================================

-- ==============================================================================
-- EXERCISE 3.5: Calculate Moving Averages and Percentiles
-- ==============================================================================
-- Question: How do we calculate rolling metrics over a stream?

-- Create more sample data for time-series analysis
DROP TABLE IF EXISTS metrics_stream CASCADE;
CREATE TABLE metrics_stream (
    event_id     BIGSERIAL PRIMARY KEY,
    event_time   TIMESTAMP NOT NULL DEFAULT NOW(),
    metric_name  VARCHAR(50) NOT NULL,
    metric_value DECIMAL(10,2) NOT NULL
);

-- Insert sample metrics
INSERT INTO metrics_stream (event_time, metric_name, metric_value) VALUES
    ('2026-03-13 10:00:00', 'response_time', 120.5),
    ('2026-03-13 10:00:01', 'response_time', 145.2),
    ('2026-03-13 10:00:02', 'response_time', 98.7),
    ('2026-03-13 10:00:03', 'response_time', 180.3),
    ('2026-03-13 10:00:04', 'response_time', 110.1),
    ('2026-03-13 10:00:05', 'response_time', 132.8),
    ('2026-03-13 10:00:06', 'response_time', 95.4),
    ('2026-03-13 10:00:07', 'response_time', 156.9),
    ('2026-03-13 10:00:08', 'response_time', 142.1),
    ('2026-03-13 10:00:09', 'response_time', 108.6);

-- Calculate 3-event moving average
SELECT
    event_id,
    event_time,
    metric_value,
    AVG(metric_value) OVER (
        ORDER BY event_time
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ) as moving_avg_3,
    -- 5-event moving average
    AVG(metric_value) OVER (
        ORDER BY event_time
        ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
    ) as moving_avg_5
FROM metrics_stream
ORDER BY event_time;

-- Calculate percentile (approximate using window functions)
SELECT
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY metric_value) as p50,
    PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY metric_value) as p90,
    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY metric_value) as p99,
    AVG(metric_value) as avg_value,
    MIN(metric_value) as min_value,
    MAX(metric_value) as max_value
FROM metrics_stream;

-- ==============================================================================
-- PART 6: Real-time Alerting Pattern
-- ==============================================================================

-- ==============================================================================
-- EXERCISE 3.6: Detect Threshold Violations
-- ==============================================================================
-- Question: How do we trigger alerts when metrics exceed thresholds?

-- Create a threshold configuration table
DROP TABLE IF EXISTS alert_thresholds CASCADE;
CREATE TABLE alert_thresholds (
    metric_name   VARCHAR(50) PRIMARY KEY,
    threshold     DECIMAL(10,2) NOT NULL,
    operator      VARCHAR(10) NOT NULL,  -- '>', '<', '>=', '<='
    alert_message VARCHAR(200)
);

INSERT INTO alert_thresholds (metric_name, threshold, operator, alert_message) VALUES
    ('response_time', 150.0, '>', 'Response time exceeded 150ms'),
    ('error_rate', 5.0, '>', 'Error rate exceeded 5%'),
    ('cpu_usage', 80.0, '>', 'CPU usage exceeded 80%');

-- Simulate real-time metric checks
WITH current_metrics AS (
    SELECT
        metric_name,
        AVG(metric_value) as current_value
    FROM metrics_stream
    WHERE event_time > NOW() - INTERVAL '30 seconds'
    GROUP BY metric_name
)
SELECT
    cm.metric_name,
    cm.current_value,
    at.threshold,
    at.alert_message,
    CASE
        WHEN at.operator = '>' AND cm.current_value > at.threshold THEN 'TRIGGERED'
        WHEN at.operator = '<' AND cm.current_value < at.threshold THEN 'TRIGGERED'
        WHEN at.operator = '>=' AND cm.current_value >= at.threshold THEN 'TRIGGERED'
        WHEN at.operator = '<=' AND cm.current_value <= at.threshold THEN 'TRIGGERED'
        ELSE 'OK'
    END as alert_status
FROM current_metrics cm
JOIN alert_thresholds at ON cm.metric_name = at.metric_name;

-- ==============================================================================
-- PART 7: Search on Streams (Inverse Query Pattern)
-- ==============================================================================

-- ==============================================================================
-- EXERCISE 3.7: Content-Based Routing / Event Routing
-- ==============================================================================
-- Question: How do we filter and route events based on content?

-- Create a subscription table (stored queries)
DROP TABLE IF EXISTS stream_subscriptions CASCADE;
CREATE TABLE stream_subscriptions (
    subscription_id SERIAL PRIMARY KEY,
    subscriber_name VARCHAR(100),
    filter_criteria JSONB NOT NULL,  -- The "query" to match against events
    created_at      TIMESTAMP DEFAULT NOW()
);

-- Subscribers want different event types
INSERT INTO stream_subscriptions (subscriber_name, filter_criteria) VALUES
    ('Analytics Team', '{"event_type": "purchase"}'),
    ('Support Team', '{"event_type": ["add_to_cart", "purchase"], "country": "US"}'),
    ('Fraud Detection', '{"event_type": "purchase", "amount": {"$gt": 100}}');

-- Function to match events against subscriptions
CREATE OR REPLACE FUNCTION match_subscriptions(p_event JSONB)
RETURNS TABLE (subscription_id INT, subscriber_name VARCHAR) AS $$
BEGIN
    RETURN QUERY
    SELECT s.subscription_id, s.subscriber_name
    FROM stream_subscriptions s
    WHERE
        -- Check if event_type matches
        (s.filter_criteria->>'event_type' = p_event->>'event_type'
         OR s.filter_criteria->>'event_type' LIKE '%' || (p_event->>'event_type') || '%'
        )
        OR p_event->>'event_type' = ANY(
            CASE
                WHEN jsonb_typeof(s.filter_criteria->'event_type') = 'array'
                THEN array(SELECT jsonb_array_elements_text(s.filter_criteria->'event_type'))
                ELSE ARRAY[s.filter_criteria->>'event_type']
            END
        );
END;
$$ LANGUAGE plpgsql;

-- Test event matching
SELECT match_subscriptions('{"event_type": "purchase", "amount": 150.00, "country": "US"}'::jsonb);

-- ==============================================================================
-- PART 8: Maintaining Derived State
-- ==============================================================================

-- ==============================================================================
-- EXERCISE 3.8: Real-time Counter / State Maintenance
-- ==============================================================================
-- Question: How do we maintain counters that update in real-time?

-- Create a real-time counter table
DROP TABLE IF EXISTS real_time_counters CASCADE;
CREATE TABLE real_time_counters (
    counter_key   VARCHAR(100) PRIMARY KEY,
    counter_value BIGINT DEFAULT 0,
    last_event_id BIGINT DEFAULT 0,
    updated_at    TIMESTAMP DEFAULT NOW()
);

-- Function to process events and update counters (idempotent)
CREATE OR REPLACE FUNCTION process_event_and_update_counter(
    p_event_id BIGINT,
    p_event_type VARCHAR,
    p_counter_key VARCHAR
) RETURNS VOID AS $$
BEGIN
    -- Idempotent: only process if we haven't seen this event
    INSERT INTO real_time_counters (counter_key, counter_value, last_event_id)
    VALUES (p_counter_key, 1, p_event_id)
    ON CONFLICT (counter_key) DO UPDATE
    SET
        counter_value = real_time_counters.counter_value +
            CASE WHEN real_time_counters.last_event_id < EXCLUDED.last_event_id THEN 1 ELSE 0 END,
        last_event_id = GREATEST(real_time_counters.last_event_id, EXCLUDED.last_event_id),
        updated_at = NOW()
    WHERE real_time_counters.last_event_id < EXCLUDED.last_event_id;
END;
$$ LANGUAGE plpgsql;

-- Process sample events
SELECT process_event_and_update_counter(1, 'page_view', 'total_page_views');
SELECT process_event_and_update_counter(2, 'page_view', 'total_page_views');
SELECT process_event_and_update_counter(3, 'click', 'total_clicks');

-- Check counters
SELECT * FROM real_time_counters;

-- ==============================================================================
-- SUMMARY: Stream Processing Patterns
-- ==============================================================================

/*
┌─────────────────────────────────────────────────────────────────────────────┐
│ Pattern                  │ SQL Implementation                              │
├─────────────────────────────────────────────────────────────────────────────┤
│ Basic Aggregation       │ COUNT, SUM, AVG with GROUP BY                   │
│ Real-time Metrics       │ Materialized Views with REFRESH                  │
│ Pattern Detection       │ Window functions + CTEs for sequence detection   │
│ Funnel Analysis         │ Conditional aggregation with CASE               │
│ Moving Averages         │ ROWS BETWEEN n PRECEDING window function        │
│ Percentiles             │ PERCENTILE_CONT() window function               │
│ Alerting                │ Threshold comparison with current values         │
│ Event Routing           │ JSONB matching against subscription filters      │
│ Real-time Counters      │ UPSERT with idempotent processing                │
└─────────────────────────────────────────────────────────────────────────────┘
*/

-- Clean up for next section
-- DROP TABLE IF EXISTS clickstream_events, login_events, metrics_stream,
--     alert_thresholds, stream_subscriptions, real_time_counters CASCADE;
-- DROP MATERIALIZED VIEW IF EXISTS real_time_metrics;
