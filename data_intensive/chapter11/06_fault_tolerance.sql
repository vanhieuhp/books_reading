-- ==============================================================================
-- Chapter 11: Stream Processing - Section 6
-- Fault Tolerance: Exactly-Once, Idempotent Processing, Checkpointing
-- ==============================================================================
-- Database: PostgreSQL
-- Focus: Fault Tolerance Patterns + Idempotent Design
-- ==============================================================================

-- ==============================================================================
-- PART 1: Understanding Processing Semantics
-- ==============================================================================

-- ==============================================================================
-- EXERCISE 6.1: At-Least-Once vs At-Most-Once vs Exactly-Once
-- ==============================================================================
-- Question: What's the difference between processing semantics?

-- Create event table for demonstration
DROP TABLE IF EXISTS events_for_processing CASCADE;
CREATE TABLE events_for_processing (
    event_id     SERIAL PRIMARY KEY,
    event_time   TIMESTAMP DEFAULT NOW(),
    payload      JSONB NOT NULL,
    processed    BOOLEAN DEFAULT FALSE,
    retry_count  INT DEFAULT 0
);

-- Insert sample events
INSERT INTO events_for_processing (payload) VALUES
    ('{"type": "order", "id": 1}'),
    ('{"type": "order", "id": 2}'),
    ('{"type": "order", "id": 3}');

-- ==============================================================================
-- AT-MOST-ONCE: Process without retry (may lose events)
-- Simulating: Read event, process, but don't track completion
-- Problem: If crash after processing but before marking complete, event is lost

-- Simulate processing (without tracking)
CREATE OR REPLACE FUNCTION process_at_most_once(p_event_id INT)
RETURNS VOID AS $$
BEGIN
    -- Simulate processing work
    RAISE NOTICE 'Processing event %', p_event_id;

    -- At-most-once: We process but don't track the result
    -- If we crash here, the event is lost forever
END;
$$ LANGUAGE plpgsql;

-- ==============================================================================
-- AT-LEAST-ONCE: Retry on failure (may duplicate)
-- Simulating: Track progress, retry on failure
-- Problem: If crash after marking complete but before finishing, event is reprocessed

-- Add tracking columns
ALTER TABLE events_for_processing ADD COLUMN IF NOT EXISTS processed_at TIMESTAMP;
ALTER TABLE events_for_processing ADD COLUMN IF NOT EXISTS processing_status VARCHAR(20);

CREATE OR REPLACE FUNCTION process_at_least_once(p_event_id INT)
RETURNS VOID AS $$
BEGIN
    -- Check if already processed
    IF EXISTS (
        SELECT 1 FROM events_for_processing
        WHERE event_id = p_event_id AND processed_at IS NOT NULL
    ) THEN
        RAISE NOTICE 'Event % already processed, skipping', p_event_id;
        RETURN;
    END IF;

    -- Mark as processing (prevents duplicate processing)
    UPDATE events_for_processing
    SET processing_status = 'processing'
    WHERE event_id = p_event_id;

    -- Simulate processing (might fail)
    RAISE NOTICE 'Processing event %', p_event_id;

    -- Mark as complete
    UPDATE events_for_processing
    SET processed_at = NOW(), processing_status = 'completed', processed = TRUE
    WHERE event_id = p_event_id;
END;
$$ LANGUAGE plpgsql;

-- Test at-least-once
SELECT process_at_least_once(1);

-- Simulate failure and retry
UPDATE events_for_processing SET processed_at = NULL, processing_status = NULL WHERE event_id = 1;
SELECT process_at_least_once(1);  -- Should detect and skip

-- ==============================================================================
-- EXACTLY-ONCE: Idempotent + Transactional (the goal)
-- ==============================================================================

-- ==============================================================================
-- PART 2: Idempotent Processing
-- ==============================================================================

-- ==============================================================================
-- EXERCISE 6.2: Idempotent Design Patterns
-- ==============================================================================
-- Question: How do we make processing idempotent (safe to retry)?

-- Create idempotent event tracking table
DROP TABLE IF EXISTS idempotent_events CASCADE;
CREATE TABLE idempotent_events (
    event_id         BIGSERIAL PRIMARY KEY,
    event_key        VARCHAR(100) UNIQUE NOT NULL,  -- Business key for idempotency
    event_time       TIMESTAMP DEFAULT NOW(),
    payload          JSONB NOT NULL,
    processed        BOOLEAN DEFAULT FALSE,
    processing_result JSONB
);

-- Insert same event twice with same key (simulating retry)
INSERT INTO idempotent_events (event_key, payload) VALUES
    ('order_123', '{"order_id": 123, "amount": 100}')
ON CONFLICT (event_key) DO NOTHING;

INSERT INTO idempotent_events (event_key, payload) VALUES
    ('order_123', '{"order_id": 123, "amount": 100}')
ON CONFLICT (event_key) DO NOTHING;

-- Check: Only one event was inserted despite duplicate attempt
SELECT * FROM idempotent_events;

-- ==============================================================================
-- EXERCISE 6.3: Idempotent Processing with Result Deduplication
-- ==============================================================================

-- Create order table for idempotent processing
DROP TABLE IF EXISTS orders_for_idempotency CASCADE;
CREATE TABLE orders_for_idempotency (
    order_id        VARCHAR(50) PRIMARY KEY,
    customer_id     INT NOT NULL,
    amount          DECIMAL(10,2) NOT NULL,
    status          VARCHAR(20) DEFAULT 'pending',
    created_at      TIMESTAMP DEFAULT NOW()
);

-- Create idempotent order processing function
CREATE OR REPLACE FUNCTION process_order_idempotent(
    p_order_id VARCHAR,
    p_customer_id INT,
    p_amount DECIMAL
) RETURNS JSONB AS $$
DECLARE
    result JSONB;
BEGIN
    -- Try to insert the order (idempotent: upsert)
    INSERT INTO orders_for_idempotency (order_id, customer_id, amount, status)
    VALUES (p_order_id, p_customer_id, p_amount, 'confirmed')
    ON CONFLICT (order_id) DO UPDATE
    SET
        amount = EXCLUDED.amount,  -- Update if different
        status = 'confirmed'
    RETURNING jsonb_build_object(
        'order_id', order_id,
        'status', status,
        'processed_at', NOW()
    ) INTO result;

    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Process the same order multiple times (simulating retries)
SELECT process_order_idempotent('order_001', 1, 100.00);
SELECT process_order_idempotent('order_001', 1, 100.00);  -- Duplicate, but idempotent
SELECT process_order_idempotent('order_001', 1, 150.00);  -- Update with new amount

-- Check results
SELECT * FROM orders_for_idempotency;

-- ==============================================================================
-- PART 3: Transactional Outbox Pattern
-- ==============================================================================

-- ==============================================================================
-- EXERCISE 6.4: Transactional Outbox Pattern
-- ==============================================================================
-- Question: How do we ensure events are published only after database commit?

-- Create the main entity table
DROP TABLE IF EXISTS accounts CASCADE;
CREATE TABLE accounts (
    account_id   SERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    balance     DECIMAL(15,2) DEFAULT 0,
    updated_at  TIMESTAMP DEFAULT NOW()
);

-- Create the outbox table (stores events to be published)
DROP TABLE IF EXISTS outbox CASCADE;
CREATE TABLE outbox (
    outbox_id    BIGSERIAL PRIMARY KEY,
    aggregate_id VARCHAR(100) NOT NULL,
    event_type   VARCHAR(100) NOT NULL,
    payload      JSONB NOT NULL,
    created_at   TIMESTAMP DEFAULT NOW(),
    published    BOOLEAN DEFAULT FALSE
);

-- Create function that atomically updates account AND creates outbox event
CREATE OR REPLACE FUNCTION transfer_funds(
    p_from_account INT,
    p_to_account INT,
    p_amount DECIMAL
) RETURNS VOID AS $$
DECLARE
    from_balance DECIMAL;
BEGIN
    -- Check balance
    SELECT balance INTO from_balance FROM accounts WHERE account_id = p_from_account;

    IF from_balance < p_amount THEN
        RAISE EXCEPTION 'Insufficient funds';
    END IF;

    -- Start transaction: debit
    UPDATE accounts
    SET balance = balance - p_amount, updated_at = NOW()
    WHERE account_id = p_from_account;

    -- Start transaction: credit
    UPDATE accounts
    SET balance = balance + p_amount, updated_at = NOW()
    WHERE account_id = p_to_account;

    -- Create outbox event (same transaction!)
    INSERT INTO outbox (aggregate_id, event_type, payload)
    VALUES
        (p_from_account::text, 'AccountDebited', jsonb_build_object(
            'account_id', p_from_account,
            'amount', p_amount,
            'timestamp', NOW()
        )),
        (p_to_account::text, 'AccountCredited', jsonb_build_object(
            'account_id', p_to_account,
            'amount', p_amount,
            'timestamp', NOW()
        ));

    -- Commit happens here - both account updates AND outbox events are atomic
    RAISE NOTICE 'Transfer completed and event created';
END;
$$ LANGUAGE plpgsql;

-- Initialize accounts
INSERT INTO accounts (name, balance) VALUES
    ('Alice', 1000.00),
    ('Bob', 500.00);

-- Execute transfer (atomic: updates + outbox event)
SELECT transfer_funds(1, 2, 100.00);

-- Check accounts
SELECT * FROM accounts;

-- Check outbox (events ready to be published)
SELECT * FROM outbox;

-- ==============================================================================
-- EXERCISE 6.5: Outbox Event Publisher
-- ==============================================================================

-- Simulate publishing outbox events (and removing them after)
CREATE OR REPLACE FUNCTION publish_outbox_events()
RETURNS INT AS $$
DECLARE
    published_count INT;
BEGIN
    -- Get unpublished events
    -- In real implementation, this would send to Kafka/RabbitMQ

    -- Mark as published
    UPDATE outbox
    SET published = TRUE
    WHERE published = FALSE;

    GET DIAGNOSTICS published_count = ROW_COUNT;

    -- Optionally clean up published events
    -- DELETE FROM outbox WHERE published = TRUE;

    RETURN published_count;
END;
$$ LANGUAGE plpgsql;

SELECT publish_outbox_events() as events_published;

-- ==============================================================================
-- PART 4: Checkpoint and State Recovery
-- ==============================================================================

-- ==============================================================================
-- EXERCISE 6.6: Checkpoint Pattern (Simulating Flink)
-- ==============================================================================
-- Question: How do we periodically save state for recovery?

-- Create stream processor state table
DROP TABLE IF EXISTS processor_state CASCADE;
CREATE TABLE processor_state (
    processor_id    VARCHAR(100) NOT NULL,
    state_key       VARCHAR(100) NOT NULL,
    state_value     JSONB NOT NULL,
    checkpoint_time TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (processor_id, state_key)
);

-- Create event offset tracking
DROP TABLE IF EXISTS event_offsets CASCADE;
CREATE TABLE event_offsets (
    processor_id    VARCHAR(100) NOT NULL,
    topic           VARCHAR(100) NOT NULL,
    partition       INT NOT NULL,
    offset          BIGINT NOT NULL,
    checkpoint_time TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (processor_id, topic, partition)
);

-- Create events table
DROP TABLE IF EXISTS events_for_checkpoint CASCADE;
CREATE TABLE events_for_checkpoint (
    event_id   BIGSERIAL PRIMARY KEY,
    topic      VARCHAR(100) NOT NULL,
    partition  INT NOT NULL,
    payload    JSONB NOT NULL,
    processed  BOOLEAN DEFAULT FALSE
);

-- Insert sample events
INSERT INTO events_for_checkpoint (topic, partition, payload) VALUES
    ('orders', 0, '{"order_id": 1}'),
    ('orders', 0, '{"order_id": 2}'),
    ('orders', 0, '{"order_id": 3}'),
    ('orders', 0, '{"order_id": 4}'),
    ('orders', 0, '{"order_id": 5}');

-- Function to simulate processing with checkpoint
CREATE OR REPLACE FUNCTION process_with_checkpoint(
    p_processor_id VARCHAR,
    p_topic VARCHAR,
    p_partition INT
) RETURNS VOID AS $$
DECLARE
    current_offset BIGINT;
    event_record RECORD;
BEGIN
    -- Get current offset from checkpoint
    SELECT offset INTO current_offset
    FROM event_offsets
    WHERE processor_id = p_processor_id
        AND topic = p_topic
        AND partition = p_partition;

    -- If no checkpoint, start from beginning
    IF current_offset IS NULL THEN
        current_offset := 0;
    END IF;

    -- Process events after current offset
    FOR event_record IN
        SELECT event_id, payload
        FROM events_for_checkpoint
        WHERE topic = p_topic
            AND partition = p_partition
            AND event_id > current_offset
        ORDER BY event_id
        LIMIT 10  -- Process in batches
    LOOP
        -- Simulate processing
        RAISE NOTICE 'Processing event %', event_record.event_id;

        -- Update checkpoint (simulating periodic checkpointing)
        INSERT INTO event_offsets (processor_id, topic, partition, offset)
        VALUES (p_processor_id, p_topic, p_partition, event_record.event_id)
        ON CONFLICT (processor_id, topic, partition)
        DO UPDATE SET offset = EXCLUDED.offset, checkpoint_time = NOW();

        -- Mark event as processed
        UPDATE events_for_checkpoint
        SET processed = TRUE
        WHERE event_id = event_record.event_id;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Process events (creates checkpoints)
SELECT process_with_checkpoint('processor_1', 'orders', 0);

-- Check current offset (checkpoint)
SELECT * FROM event_offsets;

-- Simulate failure and restart - processor resumes from checkpoint
SELECT process_with_checkpoint('processor_1', 'orders', 0);

-- Check processed events
SELECT COUNT(*) as processed_count FROM events_for_checkpoint WHERE processed = TRUE;

-- ==============================================================================
-- PART 5: Kafka Exactly-Once Semantics Simulation
-- ==============================================================================

-- ==============================================================================
-- EXERCISE 6.7: Idempotent Producer Pattern
-- ==============================================================================
-- Question: How does Kafka achieve exactly-once with idempotent producers?

-- Create Kafka-like producer tracking
DROP TABLE IF EXISTS producer_sequence CASCADE;
CREATE TABLE producer_sequence (
    producer_id     VARCHAR(100) NOT NULL,
    topic           VARCHAR(100) NOT NULL,
    partition       INT NOT NULL,
    sequence_num    BIGINT NOT NULL,
    event_id        BIGINT NOT NULL,
    acknowledged    BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (producer_id, topic, partition, sequence_num)
);

-- Create consumer offset tracking (like Kafka consumer group)
DROP TABLE IF EXISTS consumer_offset CASCADE;
CREATE TABLE consumer_offset (
    consumer_group  VARCHAR(100) NOT NULL,
    topic           VARCHAR(100) NOT NULL,
    partition       INT NOT NULL,
    offset          BIGINT NOT NULL,
    PRIMARY KEY (consumer_group, topic, partition)
);

-- Simulate idempotent producer: same sequence number = same message (dedup)
CREATE OR REPLACE FUNCTION idempotent_produce(
    p_producer_id VARCHAR,
    p_topic VARCHAR,
    p_partition INT,
    p_sequence_num BIGINT,
    p_payload JSONB
) RETURNS VOID AS $$
BEGIN
    -- Try to insert - will fail if same producer+partition+sequence exists
    INSERT INTO producer_sequence (producer_id, topic, partition, sequence_num, event_id)
    SELECT p_producer_id, p_topic, p_partition, p_sequence_num, (SELECT MAX(event_id) + 1 FROM events_for_checkpoint)
    ON CONFLICT DO NOTHING;

    -- If insert succeeded, it's a new message
    -- If insert failed, it's a duplicate (already sent)
    RAISE NOTICE 'Producer % sent sequence % to partition %: %',
        p_producer_id, p_sequence_num, p_partition,
        CASE WHEN FOUND THEN 'NEW' ELSE 'DUPLICATE' END;
END;
$$ LANGUAGE plpgsql;

-- Test idempotent production
SELECT idempotent_produce('producer_1', 'orders', 0, 1, '{"order": 1}');
SELECT idempotent_produce('producer_1', 'orders', 0, 1, '{"order": 1}');  -- Duplicate
SELECT idempotent_produce('producer_1', 'orders', 0, 2, '{"order": 2}');  -- New

-- ==============================================================================
-- EXERCISE 6.8: Transactional Consumer-Producer
-- ==============================================================================
-- Question: How do we atomically commit offset AND output?

-- Create input and output tables (simulating read Kafka, write Kafka)
DROP TABLE IF EXISTS input_events CASCADE;
CREATE TABLE input_events (
    event_id   SERIAL PRIMARY KEY,
    payload    JSONB NOT NULL,
    processed  BOOLEAN DEFAULT FALSE
);

DROP TABLE IF EXISTS output_events CASCADE;
CREATE TABLE output_events (
    output_id  SERIAL PRIMARY KEY,
    input_event_id INT,
    result     JSONB NOT NULL
);

DROP TABLE IF EXISTS transaction_offset CASCADE;
CREATE TABLE transaction_offset (
    consumer_group VARCHAR(100) PRIMARY KEY,
    offset        BIGINT NOT NULL
);

-- Insert input events
INSERT INTO input_events (payload) VALUES
    ('{"value": 10}'),
    ('{"value": 20}'),
    ('{"value": 30}');

-- Transactional processing: atomically process + commit offset
CREATE OR REPLACE FUNCTION transactional_process(p_consumer_group VARCHAR)
RETURNS VOID AS $$
DECLARE
    current_offset BIGINT;
    event_record RECORD;
BEGIN
    -- Get current offset
    SELECT offset INTO current_offset
    FROM transaction_offset
    WHERE consumer_group = p_consumer_group;

    IF current_offset IS NULL THEN
        current_offset := 0;
    END IF;

    -- Process next event
    FOR event_record IN
        SELECT event_id, payload
        FROM input_events
        WHERE event_id > current_offset
        ORDER BY event_id
        LIMIT 1
    LOOP
        -- Process (transform)
        INSERT INTO output_events (input_event_id, result)
        VALUES (event_record.event_id, jsonb_build_object(
            'input', event_record.payload,
            'processed', TRUE,
            'timestamp', NOW()
        ));

        -- Atomically update offset (simulating Kafka transaction)
        INSERT INTO transaction_offset (consumer_group, offset)
        VALUES (p_consumer_group, event_record.event_id)
        ON CONFLICT (consumer_group)
        DO UPDATE SET offset = EXCLUDED.offset;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Execute transactional processing
SELECT transactional_process('group_1');
SELECT transactional_process('group_1');  -- Process next event
SELECT transactional_process('group_1');  -- Process third event

-- Check results
SELECT * FROM output_events;
SELECT * FROM transaction_offset;

-- ==============================================================================
-- PART 6: Microbatching Simulation
-- ==============================================================================

-- ==============================================================================
-- EXERCISE 6.9: Microbatching Pattern (Spark Streaming style)
-- ==============================================================================
-- Question: How do we simulate microbatches in PostgreSQL?

-- Create microbatch events
DROP TABLE IF EXISTS microbatch_events CASCADE;
CREATE TABLE microbatch_events (
    event_id     SERIAL PRIMARY KEY,
    event_time   TIMESTAMP DEFAULT NOW(),
    value        DECIMAL(10,2) NOT NULL,
    batch_id     INT,
    processed    BOOLEAN DEFAULT FALSE
);

-- Insert events
INSERT INTO microbatch_events (value) VALUES
    (10), (20), (30), (40), (50), (60), (70), (80), (90), (100);

-- Assign events to microbatches (simulating Spark's DStream)
WITH batched AS (
    SELECT
        event_id,
        value,
        (ROW_NUMBER() OVER (ORDER BY event_id) - 1) / 3 as batch_num  -- 3 events per batch
    FROM microbatch_events
)
UPDATE microbatch_events me
SET batch_id = batched.batch_num
FROM batched
WHERE me.event_id = batched.event_id;

-- View batches
SELECT batch_id, COUNT(*), SUM(value) as batch_sum
FROM microbatch_events
GROUP BY batch_id
ORDER BY batch_id;

-- Process each batch (simulating Spark job per batch)
CREATE OR REPLACE FUNCTION process_microbatch(p_batch_id INT)
RETURNS VOID AS $$
BEGIN
    -- Simulate batch processing
    UPDATE microbatch_events
    SET processed = TRUE
    WHERE batch_id = p_batch_id;

    RAISE NOTICE 'Processed microbatch %', p_batch_id;
END;
$$ LANGUAGE plpgsql;

-- Process batches sequentially
SELECT process_microbatch(0);
SELECT process_microbatch(1);
SELECT process_microbatch(2);

-- Check progress
SELECT batch_id, COUNT(*) as total, SUM(CASE WHEN processed THEN 1 ELSE 0 END) as processed
FROM microbatch_events
GROUP BY batch_id;

-- ==============================================================================
-- SUMMARY: Fault Tolerance Patterns
-- ==============================================================================

/*
┌─────────────────────────────────────────────────────────────────────────────┐
│ Pattern                │ Description                    │ Implementation     │
├─────────────────────────────────────────────────────────────────────────────┤
│ At-Most-Once          │ Process without retry          │ No tracking        │
│ At-Least-Once         │ Track & retry on failure      │ Status tracking    │
│ Exactly-Once          │ Idempotent + transactional     │ UPSERT + TX        │
│ Idempotent Processing │ Safe to retry                 │ UNIQUE constraint  │
│ Transactional Outbox  │ Atomic DB write + event       │ Single TX          │
│ Checkpointing         │ Periodic state snapshot       │ Offset tracking    │
│ Microbatching         │ Small batches for reliability │ Batch grouping     │
│ Idempotent Producer   │ Deduplicate by sequence       │ UNIQUE constraint  │
└─────────────────────────────────────────────────────────────────────────────┘
*/

-- Clean up
-- DROP TABLE IF EXISTS events_for_processing, idempotent_events,
--     orders_for_idempotency, accounts, outbox, processor_state,
--     event_offsets, events_for_checkpoint, producer_sequence,
--     consumer_offset, input_events, output_events, transaction_offset,
--     microbatch_events CASCADE;
