-- ==============================================================================
-- Chapter 11: Stream Processing - Section 1
-- Event Streams, Producers, Consumers, and Messaging Patterns
-- ==============================================================================
-- Database: PostgreSQL
-- Focus: Conceptual Simulation + CDC Patterns
-- ==============================================================================

-- ==============================================================================
-- PART 1: Basic Event Stream Simulation
-- ==============================================================================

-- Create an event stream table (simulating a Kafka topic)
-- In Kafka, this would be a topic with partitions
-- Here we simulate with a single partition for learning

DROP TABLE IF EXISTS event_stream CASCADE;
CREATE TABLE event_stream (
    event_id     BIGSERIAL PRIMARY KEY,
    event_time   TIMESTAMP NOT NULL DEFAULT NOW(),
    topic        VARCHAR(100) NOT NULL,
    key          VARCHAR(100),           -- Partition key (e.g., user_id)
    payload      JSONB NOT NULL,         -- Event data
    processed    BOOLEAN DEFAULT FALSE
);

-- Create index for efficient consumer offset tracking
CREATE INDEX idx_event_stream_topic_offset ON event_stream(topic, event_id);

-- Insert sample events (simulating producers)
INSERT INTO event_stream (event_time, topic, key, payload) VALUES
    ('2026-03-13 10:00:00', 'user_events', 'user_1', '{"action": "login", "user_id": 1}'),
    ('2026-03-13 10:00:01', 'user_events', 'user_2', '{"action": "click", "button_id": "buy_now"}'),
    ('2026-03-13 10:00:02', 'user_events', 'user_1', '{"action": "view", "page": "/products"}'),
    ('2026-03-13 10:00:03', 'user_events', 'user_3', '{"action": "login", "user_id": 3}'),
    ('2026-03-13 10:00:04', 'user_events', 'user_1', '{"action": "add_to_cart", "product_id": 42}'),
    ('2026-03-13 10:00:05', 'order_events', 'order_1', '{"action": "created", "total": 99.99}'),
    ('2026-03-13 10:00:06', 'user_events', 'user_2', '{"action": "purchase", "order_id": 101}');

-- ==============================================================================
-- EXERCISE 1.1: View the event stream
-- ==============================================================================
-- Question: What does the raw event stream look like?
-- Run this to see all events in order

SELECT * FROM event_stream ORDER BY event_id;

-- ==============================================================================
-- PART 2: Consumer Offset Simulation
-- ==============================================================================

-- In Kafka, each consumer maintains an offset (position in the log)
-- Let's simulate consumer groups with their own offsets

DROP TABLE IF EXISTS consumer_offsets;
CREATE TABLE consumer_offsets (
    consumer_group VARCHAR(100) NOT NULL,
    topic          VARCHAR(100) NOT NULL,
    offset         BIGINT NOT NULL,  -- Last processed event_id
    last_updated   TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (consumer_group, topic)
);

-- Consumer Group A is at offset 3 (has processed events 1-3)
INSERT INTO consumer_offsets (consumer_group, topic, offset) VALUES
    ('analytics_service', 'user_events', 3),
    ('notification_service', 'user_events', 2),
    ('analytics_service', 'order_events', 1);

-- ==============================================================================
-- EXERCISE 1.2: Simulate a consumer reading from the stream
-- ==============================================================================
-- Question: How does a consumer get "unprocessed" events?

-- Consumer reads events AFTER their current offset
SELECT es.*
FROM event_stream es
JOIN consumer_offsets co
    ON es.topic = co.topic
WHERE co.consumer_group = 'analytics_service'
    AND es.topic = 'user_events'
    AND es.event_id > co.offset
ORDER BY es.event_id;

-- ==============================================================================
-- EXERCISE 1.3: Simulate consumer committing offset after processing
-- ==============================================================================
-- Question: How do we update the consumer's offset after processing?

-- Simulate processing event_id 4 and committing the offset
UPDATE consumer_offsets
SET offset = 4, last_updated = NOW()
WHERE consumer_group = 'analytics_service' AND topic = 'user_events';

-- Verify the offset was updated
SELECT * FROM consumer_offsets WHERE consumer_group = 'analytics_service';

-- Now the next query will show only unprocessed events (id > 4)
SELECT es.event_id, es.event_time, es.payload
FROM event_stream es
JOIN consumer_offsets co ON es.topic = co.topic
WHERE co.consumer_group = 'analytics_service'
    AND es.topic = 'user_events'
    AND es.event_id > co.offset;

-- ==============================================================================
-- PART 3: Log-Based vs Traditional Message Broker Simulation
-- ==============================================================================

-- LOG-BASED (Kafka-style): Messages persist after consumption
-- Messages can be replayed by resetting offset

-- Traditional Message Broker (RabbitMQ-style):
-- Messages are "consumed" and deleted

DROP TABLE IF EXISTS traditional_queue CASCADE;
CREATE TABLE traditional_queue (
    message_id   SERIAL PRIMARY KEY,
    payload      TEXT NOT NULL,
    status       VARCHAR(20) DEFAULT 'pending',  -- pending, processed
    consumer_id  VARCHAR(50)
);

INSERT INTO traditional_queue (payload) VALUES
    ('Message 1'), ('Message 2'), ('Message 3'), ('Message 4'), ('Message 5');

-- EXERCISE 1.4: Simulate traditional queue consumption
-- Question: What happens when a consumer takes a message?

-- Consumer A claims a message (SELECT FOR UPDATE to prevent other consumers getting same)
BEGIN;
SELECT message_id, payload
FROM traditional_queue
WHERE status = 'pending'
ORDER BY message_id
LIMIT 1
FOR UPDATE SKIP LOCKED;

-- Simulate processing and acknowledging (deleting)
-- In RabbitMQ, message is deleted after ACK
-- Here we mark as processed (simulating deletion)
UPDATE traditional_queue
SET status = 'processed', consumer_id = 'worker_1'
WHERE message_id = 1;
COMMIT;

-- The message is now "gone" - can't be replayed
SELECT * FROM traditional_queue WHERE message_id = 1;

-- ==============================================================================
-- PART 4: Partition Simulation
-- ==============================================================================

-- Kafka partitions events by key for scalability
-- Let's simulate partitioning by user_id

DROP TABLE IF EXISTS partitioned_events CASCADE;
CREATE TABLE partitioned_events (
    partition    INT NOT NULL,
    offset       BIGINT NOT NULL,
    event_time   TIMESTAMP NOT NULL,
    key          VARCHAR(100),           -- user_id
    payload      JSONB NOT NULL,
    PRIMARY KEY (partition, offset)
) PARTITION BY LIST (partition);

-- Create partitions
CREATE TABLE partitioned_events_p0 PARTITION OF partitioned_events
    FOR VALUES IN (0);
CREATE TABLE partitioned_events_p1 PARTITION OF partitioned_events
    FOR VALUES IN (1);
CREATE TABLE partitioned_events_p2 PARTITION OF partitioned_events
    FOR VALUES IN (2);

-- Insert events (they'll be routed to partitions based on key hash)
INSERT INTO partitioned_events (partition, offset, event_time, key, payload)
SELECT
    (abs(hashtext(key)) % 3) as partition,  -- Simple hash partition
    row_number() OVER () as offset,
    NOW() + (interval '1 second' * row_number() OVER ()) as event_time,
    key,
    payload::jsonb
FROM (VALUES
    ('user_1', '{"action": "login"}'),
    ('user_2', '{"action": "click"}'),
    ('user_3', '{"action": "login"}'),
    ('user_1', '{"action": "view"}'),
    ('user_2', '{"action": "purchase"}'),
    ('user_3', '{"action": "click"}'),
    ('user_1', '{"action": "logout"}')
) AS data(key, payload);

-- ==============================================================================
-- EXERCISE 1.5: Query events by partition
-- Question: How are events distributed across partitions?
-- ==============================================================================

SELECT partition, COUNT(*) as event_count
FROM partitioned_events
GROUP BY partition
ORDER BY partition;

-- View events in partition 0
SELECT * FROM partitioned_events_p0 ORDER BY offset;

-- ==============================================================================
-- PART 5: CDC Pattern - Tracking Changes
-- ==============================================================================

-- Simulate Change Data Capture (CDC) from a database
-- This creates an audit trail similar to database WAL

DROP TABLE IF EXISTS users CASCADE;
CREATE TABLE users (
    user_id   SERIAL PRIMARY KEY,
    name      VARCHAR(100) NOT NULL,
    email     VARCHAR(100),
    status    VARCHAR(20) DEFAULT 'active'
);

-- The CDC event log (similar to Debezium output)
DROP TABLE IF EXISTS cdc_events CASCADE;
CREATE TABLE cdc_events (
    event_id      BIGSERIAL PRIMARY KEY,
    table_name    VARCHAR(100) NOT NULL,
    operation     VARCHAR(10) NOT NULL,  -- INSERT, UPDATE, DELETE
    before_state  JSONB,                  -- State before change
    after_state   JSONB,                 -- State after change
    tx_id         BIGINT,                -- Transaction ID
    event_time    TIMESTAMP DEFAULT NOW()
);

-- Trigger function to capture all changes
CREATE OR REPLACE FUNCTION capture_user_changes()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO cdc_events (table_name, operation, after_state, tx_id)
        VALUES ('users', 'INSERT', to_jsonb(NEW), txid_current());
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO cdc_events (table_name, operation, before_state, after_state, tx_id)
        VALUES ('users', 'UPDATE', to_jsonb(OLD), to_jsonb(NEW), txid_current());
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO cdc_events (table_name, operation, before_state, tx_id)
        VALUES ('users', 'DELETE', to_jsonb(OLD), txid_current());
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Attach trigger to users table
CREATE TRIGGER user_cdc_trigger
AFTER INSERT OR UPDATE OR DELETE ON users
FOR EACH ROW EXECUTE FUNCTION capture_user_changes();

-- ==============================================================================
-- EXERCISE 1.6: Test CDC capture
-- Question: What events are captured when we modify the table?
-- ==============================================================================

-- Insert a user
INSERT INTO users (name, email) VALUES ('Alice', 'alice@example.com');

-- Update the user
UPDATE users SET email = 'alice.new@example.com' WHERE name = 'Alice';

-- Delete the user
DELETE FROM users WHERE name = 'Alice';

-- View all captured CDC events
SELECT
    event_id,
    operation,
    before_state->>'name' as name_before,
    after_state->>'name' as name_after,
    before_state->>'email' as email_before,
    after_state->>'email' as email_after,
    event_time
FROM cdc_events
ORDER BY event_id;

-- ==============================================================================
-- PART 6: Consumer Replay Pattern
-- ==============================================================================

-- Kafka allows replaying events by resetting offset
-- Let's simulate this with a "replay" consumer

DROP TABLE IF EXISTS replay_consumer CASCADE;
CREATE TABLE replay_consumer (
    consumer_name VARCHAR(100) PRIMARY KEY,
    topic         VARCHAR(100),
    replay_from   BIGINT,  -- Reset to this offset
    last_offset   BIGINT DEFAULT 0
);

-- Consumer wants to replay from the beginning
INSERT INTO replay_consumer (consumer_name, topic, replay_from, last_offset)
VALUES ('replay_consumer', 'user_events', 0, 0)
ON CONFLICT (consumer_name) DO UPDATE
    SET replay_from = 0, last_offset = 0;

-- Simulate replay: read events from offset 0 again
-- This demonstrates Kafka's replay capability
SELECT
    rc.consumer_name,
    es.event_id,
    es.event_time,
    es.payload,
    'REPLAY' as read_type
FROM replay_consumer rc
JOIN event_stream es ON es.topic = rc.topic
WHERE es.event_id > rc.replay_from
    AND es.event_id <= rc.replay_from + 3  -- Replay first 3 events
ORDER BY es.event_id;

-- ==============================================================================
-- PART 7: Multiple Consumer Groups (Independent Consumption)
-- ==============================================================================

-- Each consumer group maintains its own offset
-- This is a key Kafka advantage over traditional queues

-- Add more consumer groups
INSERT INTO consumer_offsets (consumer_group, topic, offset)
VALUES
    ('fraud_detection', 'user_events', 0),
    ('analytics', 'user_events', 0)
ON CONFLICT (consumer_group, topic) DO NOTHING;

-- EXERCISE 1.7: All consumers read the same events independently
-- Question: Can different consumer groups process events at different rates?

-- Fraud detection is behind (only processed 2 events)
UPDATE consumer_offsets SET offset = 2 WHERE consumer_group = 'fraud_detection';

-- Analytics is ahead (processed 5 events)
UPDATE consumer_offsets SET offset = 5 WHERE consumer_group = 'analytics';

-- Each sees different "unprocessed" events
SELECT 'fraud_detection' as consumer, event_id FROM event_stream
WHERE topic = 'user_events' AND event_id > 2
UNION ALL
SELECT 'analytics' as consumer, event_id FROM event_stream
WHERE topic = 'user_events' AND event_id > 5
ORDER BY consumer, event_id;

-- ==============================================================================
-- SUMMARY: Key Concepts Demonstrated
-- ==============================================================================

/*
┌─────────────────────────────────────────────────────────────────────────────┐
│ Concept                    │ SQL Implementation                            │
├─────────────────────────────────────────────────────────────────────────────┤
│ Event Stream               │ event_stream table with event_id as offset    │
│ Producer                  │ INSERT into event_stream                       │
│ Consumer                  │ SELECT + UPDATE offset                         │
│ Log-Based Broker          │ Messages persist, not deleted after read      │
│ Traditional Broker        │ Messages marked 'processed' (deleted)         │
│ Partitioning              │ PostgreSQL table partitioning                 │
│ CDC                       │ Triggers capture INSERT/UPDATE/DELETE         │
│ Replay                    │ Reset consumer offset to replay events        │
│ Consumer Groups           │ Multiple offset rows per topic                │
└─────────────────────────────────────────────────────────────────────────────┘
*/

-- Clean up for next section
-- DROP TABLE IF EXISTS event_stream, consumer_offsets, traditional_queue,
--     partitioned_events, cdc_events, users, replay_consumer CASCADE;
