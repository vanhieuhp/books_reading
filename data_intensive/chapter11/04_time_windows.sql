-- ==============================================================================
-- Chapter 11: Stream Processing - Section 4
-- Time and Windows: Tumbling, Hopping, Sliding, Session
-- ==============================================================================
-- Database: PostgreSQL
-- Focus: Conceptual Simulation + Window Functions
-- ==============================================================================

-- ==============================================================================
-- PART 1: Time Concepts - Event Time vs Processing Time
-- ==============================================================================

-- Create events with both event_time (when it happened) and processing_time (when it was received)
DROP TABLE IF EXISTS timed_events CASCADE;
CREATE TABLE timed_events (
    event_id        BIGSERIAL PRIMARY KEY,
    event_time      TIMESTAMP NOT NULL,        -- When event actually occurred
    processing_time TIMESTAMP NOT NULL DEFAULT NOW(),  -- When received/processed
    event_type      VARCHAR(50) NOT NULL,
    value           DECIMAL(10,2)
);

-- Insert events with out-of-order arrival (simulating real-world scenarios)
-- Note: event_time might be earlier than processing_time (due to buffering/network delay)
INSERT INTO timed_events (event_time, processing_time, event_type, value) VALUES
    ('2026-03-13 10:00:00', '2026-03-13 10:00:01', 'click', 10.00),  -- Normal: 1 sec delay
    ('2026-03-13 10:00:01', '2026-03-13 10:00:02', 'click', 15.00),  -- Normal: 1 sec delay
    ('2026-03-13 10:00:02', '2026-03-13 10:00:03', 'click', 20.00),  -- Normal: 1 sec delay
    -- Late event: device buffered for 30 seconds before sending
    ('2026-03-13 10:00:03', '2026-03-13 10:00:35', 'click', 25.00),
    ('2026-03-13 10:00:04', '2026-03-13 10:00:05', 'click', 30.00),
    ('2026-03-13 10:00:05', '2026-03-13 10:00:06', 'click', 35.00);

-- ==============================================================================
-- EXERCISE 4.1: Compare Event Time vs Processing Time Aggregations
-- ==============================================================================
-- Question: Why does it matter which time we use?

-- Aggregation by EVENT time (correct approach)
SELECT
    DATE_TRUNC('minute', event_time) as minute,
    COUNT(*) as event_count,
    SUM(value) as total_value
FROM timed_events
GROUP BY DATE_TRUNC('minute', event_time)
ORDER BY minute;

-- Aggregation by PROCESSING time (incorrect - can give wrong results)
SELECT
    DATE_TRUNC('minute', processing_time) as minute,
    COUNT(*) as event_count,
    SUM(value) as total_value
FROM timed_events
GROUP BY DATE_TRUNC('minute', processing_time)
ORDER BY minute;

-- ==============================================================================
-- PART 2: Tumbling Window (Fixed, Non-overlapping)
-- ==============================================================================

-- ==============================================================================
-- EXERCISE 4.2: Tumbling Window Implementation
-- ==============================================================================
-- Question: How do we implement non-overlapping fixed-size windows?

-- Create clickstream with more data
DROP TABLE IF EXISTS clickstream CASCADE;
CREATE TABLE clickstream (
    event_id   BIGSERIAL PRIMARY KEY,
    event_time TIMESTAMP NOT NULL DEFAULT NOW(),
    user_id    VARCHAR(50),
    event_type VARCHAR(50)
);

-- Insert events spanning several minutes
INSERT INTO clickstream (event_time, user_id, event_type) VALUES
    ('2026-03-13 10:00:00', 'user_1', 'click'),
    ('2026-03-13 10:00:01', 'user_2', 'click'),
    ('2026-03-13 10:00:02', 'user_1', 'click'),
    ('2026-03-13 10:00:15', 'user_3', 'click'),  -- New minute
    ('2026-03-13 10:00:30', 'user_1', 'click'),
    ('2026-03-13 10:00:45', 'user_2', 'click'),  -- New minute
    ('2026-03-13 10:01:00', 'user_1', 'click'),
    ('2026-03-13 10:01:15', 'user_3', 'click'),
    ('2026-03-13 10:01:30', 'user_2', 'click');

-- Tumbling Window: 1-minute non-overlapping windows
SELECT
    DATE_TRUNC('minute', event_time) as window_start,
    DATE_TRUNC('minute', event_time) + INTERVAL '1 minute' as window_end,
    COUNT(*) as click_count,
    COUNT(DISTINCT user_id) as unique_users
FROM clickstream
GROUP BY DATE_TRUNC('minute', event_time)
ORDER BY window_start;

-- Alternative: Explicit tumbling window using window function
SELECT
    window_start,
    window_start + INTERVAL '1 minute' as window_end,
    COUNT(*) as event_count
FROM (
    SELECT
        event_time,
        DATE_TRUNC('minute', event_time) as window_start
    FROM clickstream
) t
GROUP BY window_start
ORDER BY window_start;

-- ==============================================================================
-- PART 3: Hopping Window (Overlapping, Fixed Size, Sliding Interval)
-- ==============================================================================

-- ==============================================================================
-- EXERCISE 4.3: Hopping Window Implementation
-- ==============================================================================
-- Question: How do we create overlapping windows that slide by a fixed interval?

-- Create more granular data for better demonstration
DROP TABLE IF EXISTS sensor_readings CASCADE;
CREATE TABLE sensor_readings (
    reading_id  BIGSERIAL PRIMARY KEY,
    sensor_id   VARCHAR(50) NOT NULL,
    reading_time TIMESTAMP NOT NULL,
    temperature DECIMAL(5,2)
);

-- Insert sensor data every 10 seconds for 2 minutes
INSERT INTO sensor_readings (sensor_id, reading_time, temperature) VALUES
    ('sensor_1', '2026-03-13 10:00:00', 20.0),
    ('sensor_1', '2026-03-13 10:00:10', 20.5),
    ('sensor_1', '2026-03-13 10:00:20', 21.0),
    ('sensor_1', '2026-03-13 10:00:30', 21.5),
    ('sensor_1', '2026-03-13 10:00:40', 22.0),
    ('sensor_1', '2026-03-13 10:00:50', 22.5),
    ('sensor_1', '2026-03-13 10:01:00', 23.0),
    ('sensor_1', '2026-03-13 10:01:10', 23.5),
    ('sensor_1', '2026-03-13 10:01:20', 24.0),
    ('sensor_1', '2026-03-13 10:01:30', 24.5),
    ('sensor_1', '2026-03-13 10:01:40', 25.0),
    ('sensor_1', '2026-03-13 10:01:50', 25.5);

-- Hopping Window: 1-minute window, slides every 30 seconds
-- Window size = 1 minute, hop interval = 30 seconds
-- This creates overlapping windows

-- Generate hopping windows manually
-- Window 1: 10:00:00 - 10:01:00
-- Window 2: 10:00:30 - 10:01:30
-- Window 3: 10:01:00 - 10:02:00

WITH windows AS (
    SELECT
        generate_series(
            DATE_TRUNC('minute', MIN(reading_time)),
            DATE_TRUNC('minute', MAX(reading_time)) + INTERVAL '1 minute',
            INTERVAL '30 seconds'
        ) as window_start
    FROM sensor_readings
)
SELECT
    w.window_start,
    w.window_start + INTERVAL '1 minute' as window_end,
    COUNT(sr.reading_id) as reading_count,
    ROUND(AVG(sr.temperature), 2) as avg_temp,
    ROUND(MIN(sr.temperature), 2) as min_temp,
    ROUND(MAX(sr.temperature), 2) as max_temp
FROM windows w
LEFT JOIN sensor_readings sr
    ON sr.reading_time >= w.window_start
    AND sr.reading_time < w.window_start + INTERVAL '1 minute'
GROUP BY w.window_start
ORDER BY w.window_start;

-- ==============================================================================
-- PART 4: Sliding Window (All Events Within Duration)
-- ==============================================================================

-- ==============================================================================
-- EXERCISE 4.4: Sliding Window Implementation
-- ==============================================================================
-- Question: How do we calculate metrics over a sliding time window?

-- Simulate sliding window using window functions
-- For each event, calculate the average over the last 30 seconds

SELECT
    reading_time,
    temperature,
    -- Sliding window: last 3 readings (approximately 30 seconds at 10s intervals)
    AVG(temperature) OVER (
        ORDER BY reading_time
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ) as sliding_avg_30s,
    -- Sliding window: last 5 readings (approximately 50 seconds)
    AVG(temperature) OVER (
        ORDER BY reading_time
        ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
    ) as sliding_avg_50s
FROM sensor_readings
ORDER BY reading_time;

-- Alternative: True time-based sliding window
-- This is harder in pure SQL but we can simulate with self-join
SELECT
    r1.reading_time,
    r1.temperature,
    ROUND(AVG(r2.temperature), 2) as avg_temp_last_50s
FROM sensor_readings r1
JOIN sensor_readings r2
    ON r2.reading_time >= r1.reading_time - INTERVAL '50 seconds'
    AND r2.reading_time <= r1.reading_time
WHERE r1.sensor_id = 'sensor_1'
GROUP BY r1.reading_id, r1.reading_time, r1.temperature
ORDER BY r1.reading_time;

-- ==============================================================================
-- PART 5: Session Window (Activity-based)
-- ==============================================================================

-- ==============================================================================
-- EXERCISE 4.5: Session Window Implementation
-- ==============================================================================
-- Question: How do we group events by user activity sessions?

-- Create user activity data with gaps
DROP TABLE IF EXISTS user_activity CASCADE;
CREATE TABLE user_activity (
    activity_id  BIGSERIAL PRIMARY KEY,
    user_id      VARCHAR(50) NOT NULL,
    event_time   TIMESTAMP NOT NULL,
    event_type   VARCHAR(50)
);

-- Insert user activity with sessions separated by gaps
-- Session 1: 10:00 - 10:02 (user_1 active)
-- Gap: 30 minutes
-- Session 2: 10:32 - 10:35 (user_1 active again)
INSERT INTO user_activity (user_id, event_time, event_type) VALUES
    ('user_1', '2026-03-13 10:00:00', 'page_view'),
    ('user_1', '2026-03-13 10:00:10', 'click'),
    ('user_1', '2026-03-13 10:00:20', 'click'),
    ('user_1', '2026-03-13 10:32:00', 'page_view'),  -- New session (30 min gap)
    ('user_1', '2026-03-13 10:32:10', 'add_to_cart'),
    ('user_1', '2026-03-13 10:32:20', 'purchase'),
    ('user_2', '2026-03-13 10:00:00', 'page_view'),
    ('user_2', '2026-03-13 10:00:30', 'click'),
    ('user_2', '2026-03-13 10:01:00', 'page_view');

-- Session Window Implementation with gap detection
-- Gap threshold: 30 minutes of inactivity = new session

WITH ordered_activity AS (
    SELECT
        user_id,
        event_time,
        LAG(event_time) OVER (
            PARTITION BY user_id
            ORDER BY event_time
        ) as prev_event_time
    FROM user_activity
),
session_starts AS (
    SELECT
        user_id,
        event_time,
        CASE
            WHEN prev_event_time IS NULL THEN 1
            WHEN (event_time - prev_event_time) > INTERVAL '30 minutes' THEN 1
            ELSE 0
        END as is_new_session
    FROM ordered_activity
),
session_ids AS (
    SELECT
        user_id,
        event_time,
        SUM(is_new_session) OVER (
            PARTITION BY user_id
            ORDER BY event_time
        ) as session_id
    FROM session_starts
)
SELECT
    user_id,
    session_id,
    MIN(event_time) as session_start,
    MAX(event_time) as session_end,
    MAX(event_time) - MIN(event_time) as session_duration,
    COUNT(*) as event_count
FROM session_ids
GROUP BY user_id, session_id
ORDER BY user_id, session_id;

-- ==============================================================================
-- PART 6: Handling Late Events (Watermarks)
-- ==============================================================================

-- ==============================================================================
-- EXERCISE 4.6: Watermark and Late Event Handling
-- ==============================================================================
-- Question: How do we handle events that arrive after their window closed?

-- Create events with late arrivals
DROP TABLE IF EXISTS events_with_lateness CASCADE;
CREATE TABLE events_with_lateness (
    event_id     BIGSERIAL PRIMARY KEY,
    event_time   TIMESTAMP NOT NULL,
    received_at  TIMESTAMP NOT NULL DEFAULT NOW(),
    value        DECIMAL(10,2)
);

INSERT INTO events_with_lateness (event_time, received_at, value) VALUES
    ('2026-03-13 10:00:00', '2026-03-13 10:00:01', 10.00),  -- On time
    ('2026-03-13 10:00:10', '2026-03-13 10:00:11', 20.00),  -- On time
    ('2026-03-13 10:00:05', '2026-03-13 10:00:20', 15.00),  -- Late! Arrived 15s after event time
    ('2026-03-13 10:00:20', '2026-03-13 10:00:21', 30.00);  -- On time

-- Define watermark: events within 30 seconds are accepted
-- Window: 1 minute tumbling

-- First, let's see all events in each window (without late handling)
SELECT
    DATE_TRUNC('minute', event_time) as window,
    SUM(value) as total_value,
    COUNT(*) as event_count
FROM events_with_lateness
GROUP BY DATE_TRUNC('minute', event_time)
ORDER BY window;

-- Now with late event handling (events within watermark are included)
-- Late events go to a special "late" window or are reprocessed

-- Simulate: 30-second watermark allows late events into correct window
-- Events arriving within 30 seconds of their event_time are considered "on time"

-- Add late_event_flag
SELECT
    DATE_TRUNC('minute', event_time) as window,
    SUM(value) as total_value,
    COUNT(*) as event_count,
    -- Late events (received more than 30s after event_time)
    COUNT(CASE WHEN (received_at - event_time) > INTERVAL '30 seconds' THEN 1 END) as late_events
FROM events_with_lateness
GROUP BY DATE_TRUNC('minute', event_time)
ORDER BY window;

-- ==============================================================================
-- PART 7: Watermarks in Practice
-- ==============================================================================

-- ==============================================================================
-- EXERCISE 4.7: Practical Watermark Pattern
-- ==============================================================================
-- Question: How do we implement watermarks for practical stream processing?

-- Create a watermark configuration
DROP TABLE IF EXISTS watermark_config CASCADE;
CREATE TABLE watermark_config (
    stream_name   VARCHAR(50) PRIMARY KEY,
    watermark_ms  BIGINT NOT NULL,  -- Max allowed lateness in milliseconds
    description   VARCHAR(200)
);

INSERT INTO watermark_config (stream_name, watermark_ms, description) VALUES
    ('clickstream', 30000, '30 second watermark for click events'),
    ('sensor_data', 5000, '5 second watermark for sensor readings'),
    ('payment_events', 60000, '60 second watermark for payment processing');

-- Function to apply watermark to a stream
CREATE OR REPLACE FUNCTION apply_watermark(
    p_stream_name VARCHAR,
    p_event_time TIMESTAMP,
    p_processing_time TIMESTAMP
) RETURNS VARCHAR AS $$
DECLARE
    wm_config RECORD;
    latency_ms BIGINT;
BEGIN
    -- Get watermark config
    SELECT watermark_ms INTO wm_config
    FROM watermark_config
    WHERE stream_name = p_stream_name;

    IF NOT FOUND THEN
        RETURN 'UNKNOWN_STREAM';
    END IF;

    -- Calculate latency
    latency_ms := EXTRACT(EPOCH FROM (p_processing_time - p_event_time)) * 1000;

    -- Determine if event is on-time or late
    IF latency_ms <= wm_config.watermark_ms THEN
        RETURN 'ON_TIME';
    ELSE
        RETURN 'LATE';
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Test watermark function
SELECT
    event_time,
    received_at,
    value,
    apply_watermark('clickstream', event_time, received_at) as watermark_status,
    EXTRACT(EPOCH FROM (received_at - event_time)) * 1000 as latency_ms
FROM events_with_lateness;

-- ==============================================================================
-- PART 8: Windowed Aggregations with Multiple Metrics
-- ==============================================================================

-- ==============================================================================
-- EXERCISE 4.8: Complex Window Aggregation
-- ==============================================================================
-- Question: How do we calculate multiple metrics across different window types?

-- Create comprehensive metrics table
DROP TABLE IF EXISTS window_metrics CASCADE;
CREATE TABLE window_metrics (
    metric_id    BIGSERIAL PRIMARY KEY,
    event_time   TIMESTAMP NOT NULL,
    metric_type  VARCHAR(50) NOT NULL,
    value        DECIMAL(10,2) NOT NULL
);

INSERT INTO window_metrics (event_time, metric_type, value) VALUES
    ('2026-03-13 10:00:00', 'response_time', 100),
    ('2026-03-13 10:00:01', 'response_time', 150),
    ('2026-03-13 10:00:02', 'response_time', 200),
    ('2026-03-13 10:00:03', 'cpu_usage', 50),
    ('2026-03-13 10:00:04', 'cpu_usage', 60),
    ('2026-03-13 10:00:05', 'response_time', 120),
    ('2026-03-13 10:00:10', 'response_time', 110),
    ('2026-03-13 10:00:11', 'response_time', 130),
    ('2026-03-13 10:00:20', 'response_time', 90);

-- Multiple window aggregations in one query
SELECT
    metric_type,
    -- Tumbling window (1 minute)
    DATE_TRUNC('minute', event_time) as tumbling_window,
    -- Hopping window (start of each minute)
    DATE_TRUNC('minute', event_time) as hopping_window,
    -- Count in last 3 events (sliding)
    COUNT(*) OVER (
        PARTITION BY metric_type
        ORDER BY event_time
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ) as sliding_count_3,
    -- Avg in last 3 events (sliding)
    ROUND(AVG(value) OVER (
        PARTITION BY metric_type
        ORDER BY event_time
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ), 2) as sliding_avg_3
FROM window_metrics
ORDER BY event_time;

-- ==============================================================================
-- SUMMARY: Window Types
-- ==============================================================================

/*
┌─────────────────────────────────────────────────────────────────────────────┐
│ Window Type    │ Description                    │ SQL Implementation        │
├─────────────────────────────────────────────────────────────────────────────┤
│ Tumbling       │ Fixed, non-overlapping         │ DATE_TRUNC + GROUP BY     │
│ Hopping        │ Fixed size, sliding interval   │ generate_series + JOIN    │
│ Sliding        │ All events within duration     │ ROWS BETWEEN n PRECEDING │
│ Session        │ Activity-based, gap threshold  │ LAG + SUM for session ID │
│ Watermark      │ Late event threshold           │ Compare timestamps        │
└─────────────────────────────────────────────────────────────────────────────┘

Key SQL Functions:
- DATE_TRUNC(): Truncate timestamp to precision
- ROWS BETWEEN: Sliding window frame specification
- LAG/LEAD: Access previous/next rows
- generate_series(): Create time buckets
- INTERVAL: Time arithmetic
*/

-- Clean up for next section
-- DROP TABLE IF EXISTS timed_events, clickstream, sensor_readings,
--     user_activity, events_with_lateness, watermark_config, window_metrics CASCADE;
