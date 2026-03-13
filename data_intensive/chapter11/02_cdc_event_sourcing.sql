-- ==============================================================================
-- Chapter 11: Stream Processing - Section 2
-- Databases and Streams: CDC, Event Sourcing, Log Compaction
-- ==============================================================================
-- Database: PostgreSQL
-- Focus: CDC Patterns + Event Sourcing Implementation
-- ==============================================================================

-- ==============================================================================
-- PART 1: Change Data Capture (CDC) Deep Dive
-- ==============================================================================

-- ==============================================================================
-- EXERCISE 2.1: CDC with Full Transaction Context
-- ==============================================================================
-- Question: How do we capture changes with transaction ordering?

-- Create source tables
DROP TABLE IF EXISTS orders CASCADE;
CREATE TABLE orders (
    order_id    SERIAL PRIMARY KEY,
    customer_id INT NOT NULL,
    total       DECIMAL(10,2) NOT NULL,
    status      VARCHAR(20) DEFAULT 'pending',
    created_at  TIMESTAMP DEFAULT NOW()
);

DROP TABLE IF EXISTS order_items CASCADE;
CREATE TABLE order_items (
    item_id     SERIAL PRIMARY KEY,
    order_id    INT REFERENCES orders(order_id),
    product_id  INT NOT NULL,
    quantity    INT NOT NULL,
    price       DECIMAL(10,2) NOT NULL
);

-- CDC events table with transaction ordering
DROP TABLE IF EXISTS cdc_transaction_log CASCADE;
CREATE TABLE cdc_transaction_log (
    log_id          BIGSERIAL PRIMARY KEY,
    tx_id           BIGINT NOT NULL,
    tx_timestamp    TIMESTAMP NOT NULL DEFAULT NOW(),
    table_name      VARCHAR(100) NOT NULL,
    operation       VARCHAR(10) NOT NULL,
    record_key      VARCHAR(100) NOT NULL,  -- Primary key as string
    before_data     JSONB,
    after_data      JSONB,
    sequence_num    INT NOT NULL  -- Order within transaction
);

-- Trigger function for orders table
CREATE OR REPLACE FUNCTION cdc_orders_capture()
RETURNS TRIGGER AS $$
DECLARE
    tx_id BIGINT := txid_current();
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO cdc_transaction_log (tx_id, table_name, operation, record_key, after_data, sequence_num)
        VALUES (tx_id, 'orders', 'INSERT', NEW.order_id::text, to_jsonb(NEW), 1);
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO cdc_transaction_log (tx_id, table_name, operation, record_key, before_data, after_data, sequence_num)
        VALUES (tx_id, 'orders', 'UPDATE', NEW.order_id::text, to_jsonb(OLD), to_jsonb(NEW), 1);
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO cdc_transaction_log (tx_id, table_name, operation, record_key, before_data, sequence_num)
        VALUES (tx_id, 'orders', 'DELETE', OLD.order_id::text, to_jsonb(OLD), 1);
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER orders_cdc_trigger
AFTER INSERT OR UPDATE OR DELETE ON orders
FOR EACH ROW EXECUTE FUNCTION cdc_orders_capture();

-- Trigger function for order_items table
CREATE OR REPLACE FUNCTION cdc_order_items_capture()
RETURNS TRIGGER AS $$
DECLARE
    tx_id BIGINT := txid_current();
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO cdc_transaction_log (tx_id, table_name, operation, record_key, after_data, sequence_num)
        VALUES (tx_id, 'order_items', 'INSERT', NEW.item_id::text, to_jsonb(NEW), 2);
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO cdc_transaction_log (tx_id, table_name, operation, record_key, before_data, after_data, sequence_num)
        VALUES (tx_id, 'order_items', 'UPDATE', NEW.item_id::text, to_jsonb(OLD), to_jsonb(NEW), 2);
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO cdc_transaction_log (tx_id, table_name, operation, record_key, before_data, sequence_num)
        VALUES (tx_id, 'order_items', 'DELETE', OLD.item_id::text, to_jsonb(OLD), 2);
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER order_items_cdc_trigger
AFTER INSERT OR UPDATE OR DELETE ON order_items
FOR EACH ROW EXECUTE FUNCTION cdc_order_items_capture();

-- Test CDC with a transaction that spans multiple tables
BEGIN;
INSERT INTO orders (customer_id, total, status) VALUES (1, 99.99, 'pending')
RETURNING order_id;

INSERT INTO order_items (order_id, product_id, quantity, price)
SELECT order_id, 42, 2, 49.99 FROM orders WHERE customer_id = 1 ORDER BY order_id DESC LIMIT 1;

UPDATE orders SET status = 'confirmed' WHERE customer_id = 1
ORDER BY order_id DESC LIMIT 1;
COMMIT;

-- View CDC events - ordered by transaction and sequence
SELECT
    tx_id,
    tx_timestamp,
    table_name,
    operation,
    record_key,
    before_data,
    after_data
FROM cdc_transaction_log
ORDER BY tx_id, sequence_num;

-- ==============================================================================
-- PART 2: Event Sourcing Pattern
-- ==============================================================================

-- ==============================================================================
-- EXERCISE 2.2: Event Sourcing - Store Events, Derive State
-- ==============================================================================
-- Question: How do we implement event sourcing where events are the source of truth?

-- Event Store (the source of truth - immutable events)
DROP TABLE IF EXISTS event_store CASCADE;
CREATE TABLE event_store (
    event_id        BIGSERIAL PRIMARY KEY,
    aggregate_type  VARCHAR(50) NOT NULL,   -- e.g., 'Order', 'User', 'Account'
    aggregate_id    BIGINT NOT NULL,          -- ID of the entity
    event_type      VARCHAR(100) NOT NULL,   -- e.g., 'OrderCreated', 'PaymentReceived'
    event_data      JSONB NOT NULL,          -- The event payload
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMP DEFAULT NOW(),
    version         INT NOT NULL             -- For optimistic concurrency
);

-- Unique constraint: one event per aggregate in sequence
CREATE UNIQUE INDEX idx_event_store_aggregate_version
ON event_store(aggregate_type, aggregate_id, version);

-- ==============================================================================
-- EXERCISE 2.3: Event Sourcing - Reconstruct State from Events
-- ==============================================================================
-- Question: How do we reconstruct current state by replaying events?

-- Sample events for an Order aggregate
INSERT INTO event_store (aggregate_type, aggregate_id, event_type, event_data, version) VALUES
    ('Order', 1, 'OrderCreated', '{"customer_id": 1, "total": 150.00, "items": [{"product_id": 42, "qty": 2}]}', 1),
    ('Order', 1, 'PaymentReceived', '{"amount": 150.00, "payment_method": "credit_card"}', 2),
    ('Order', 1, 'OrderShipped', '{"carrier": "FedEx", "tracking_number": "FX123456789"}', 3),
    ('Order', 1, 'OrderDelivered', '{"delivered_at": "2026-03-13T10:30:00Z"}', 4);

-- Function to reconstruct current state from events
CREATE OR REPLACE FUNCTION reconstruct_order_state(p_order_id BIGINT)
RETURNS JSONB AS $$
DECLARE
    current_state JSONB := '{}';
    event_record RECORD;
BEGIN
    -- Apply each event in order to derive current state
    FOR event_record IN
        SELECT event_type, event_data
        FROM event_store
        WHERE aggregate_type = 'Order' AND aggregate_id = p_order_id
        ORDER BY version
    LOOP
        -- Apply event to derive state (simplified)
        current_state := current_state || event_record.event_data;

        -- Add the event type as a history field
        current_state := jsonb_set(current_state, '{history}', (
            COALESCE(current_state->'history', '[]'::jsonb) || to_jsonb(event_record.event_type)
        ));
    END LOOP;

    RETURN current_state;
END;
$$ LANGUAGE plpgsql;

-- Reconstruct the current state
SELECT reconstruct_order_state(1) AS current_state;

-- ==============================================================================
-- EXERCISE 2.4: Event Sourcing - Append-Only with Version Check
-- ==============================================================================
-- Question: How do we prevent concurrent modifications in event sourcing?

-- Function to append event with optimistic concurrency control
CREATE OR REPLACE FUNCTION append_event(
    p_aggregate_type VARCHAR,
    p_aggregate_id BIGINT,
    p_event_type VARCHAR,
    p_event_data JSONB,
    p_expected_version INT
) RETURNS BIGINT AS $$
DECLARE
    new_version INT;
    new_event_id BIGINT;
BEGIN
    -- Check if the expected version matches
    IF p_expected_version IS NOT NULL THEN
        PERFORM 1 FROM event_store
        WHERE aggregate_type = p_aggregate_type
            AND aggregate_id = p_aggregate_id
            AND version = p_expected_version
        FOR UPDATE;

        IF NOT FOUND THEN
            RAISE EXCEPTION 'Version mismatch. Expected version %, but the event store has changed.',
                p_expected_version;
        END IF;
    END IF;

    -- Get the next version number
    SELECT COALESCE(MAX(version), 0) + 1 INTO new_version
    FROM event_store
    WHERE aggregate_type = p_aggregate_type AND aggregate_id = p_aggregate_id;

    -- Append the new event
    INSERT INTO event_store (aggregate_type, aggregate_id, event_type, event_data, version)
    VALUES (p_aggregate_type, p_aggregate_id, p_event_type, p_event_data, new_version)
    RETURNING event_id INTO new_event_id;

    RETURN new_event_id;
END;
$$ LANGUAGE plpgsql;

-- Test optimistic concurrency control
-- First, append an event
SELECT append_event('Order', 2, 'OrderCreated', '{"total": 99.99}', NULL);

-- Try to append with wrong version (will fail)
-- This simulates a concurrent modification
-- SELECT append_event('Order', 2, 'OrderShipped', '{"carrier": "UPS"}', 1);
-- The above will fail because current version is 2, not 1

-- Correct version to use
SELECT append_event('Order', 2, 'OrderShipped', '{"carrier": "UPS"}', 1);

-- ==============================================================================
-- PART 3: Log Compaction
-- ==============================================================================

-- ==============================================================================
-- EXERCISE 2.5: Log Compaction Simulation
-- ==============================================================================
-- Question: How does Kafka log compaction work in SQL?

-- Simulate a Kafka topic with multiple versions of the same key
DROP TABLE IF EXISTS kafka_topic_log CASCADE;
CREATE TABLE kafka_topic_log (
    partition   INT NOT NULL,
    offset     BIGINT NOT NULL,
    key        VARCHAR(100),
    value      JSONB,
    is_deleted BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (partition, offset)
);

-- Insert events (simulating multiple updates to the same key)
INSERT INTO kafka_topic_log (partition, offset, key, value) VALUES
    (0, 1, 'user_42', '{"action": "created", "name": "Alice"}'),
    (0, 2, 'user_42', '{"action": "update", "email": "alice@example.com"}'),
    (0, 3, 'user_42', '{"action": "update", "email": "alice.new@example.com", "phone": "123-456"}'),
    (0, 4, 'user_42', '{"action": "delete"}'),  -- Tombstone
    (0, 5, 'user_43', '{"action": "created", "name": "Bob"}'),
    (0, 6, 'user_43', '{"action": "update", "email": "bob@example.com"}');

-- BEFORE compaction: Show all events
SELECT partition, offset, key, value, is_deleted
FROM kafka_topic_log
ORDER BY partition, offset;

-- LOG COMPACTION: Keep only the latest event for each key
-- This is what Kafka does internally

-- Create compacted version (simulating Kafka's log compaction)
DROP TABLE IF EXISTS kafka_topic_compacted CASCADE;
CREATE TABLE kafka_topic_compacted AS
SELECT partition, offset, key, value, is_deleted
FROM kafka_topic_log
WHERE 1=1;  -- Placeholder, we'll populate correctly

-- Actually perform compaction: keep latest event per key
DELETE FROM kafka_topic_log
WHERE (partition, offset) NOT IN (
    SELECT partition, MAX(offset)
    FROM kafka_topic_log
    GROUP BY partition, key
);

-- AFTER compaction: Only latest event per key remains
SELECT partition, offset, key, value
FROM kafka_topic_log
ORDER BY partition, offset;

-- ==============================================================================
-- PART 4: Materialized Views for Derived Data
-- ==============================================================================

-- ==============================================================================
-- EXERCISE 2.6: Materialized View from Event Stream
-- ==============================================================================
-- Question: How do we maintain a read-optimized view from events?

-- Create the event source table
DROP TABLE IF EXISTS product_events CASCADE;
CREATE TABLE product_events (
    event_id    BIGSERIAL PRIMARY KEY,
    event_time  TIMESTAMP DEFAULT NOW(),
    product_id  INT NOT NULL,
    event_type  VARCHAR(50) NOT NULL,
    event_data  JSONB NOT NULL
);

-- Insert sample product events
INSERT INTO product_events (product_id, event_type, event_data) VALUES
    (1, 'ProductCreated', '{"name": "Laptop", "price": 999.99, "category": "electronics"}'),
    (2, 'ProductCreated', '{"name": "Mouse", "price": 29.99, "category": "electronics"}'),
    (1, 'PriceChanged', '{"old_price": 999.99, "new_price": 899.99}'),
    (1, 'InventoryUpdated', '{"quantity": 50}'),
    (2, 'InventoryUpdated', '{"quantity": 100}'),
    (1, 'PriceChanged', '{"old_price": 899.99, "new_price": 849.99}'),
    (3, 'ProductCreated', '{"name": "Keyboard", "price": 79.99, "category": "electronics"}');

-- Create materialized view: current product state
DROP MATERIALIZED VIEW IF EXISTS product_current_state CASCADE;
CREATE MATERIALIZED VIEW product_current_state AS
SELECT
    product_id,
    (SELECT event_data->>'name' FROM product_events pe2
     WHERE pe2.product_id = pe1.product_id AND event_type = 'ProductCreated'
     ORDER BY event_id LIMIT 1) as name,
    (SELECT event_data->>'new_price' FROM product_events pe2
     WHERE pe2.product_id = pe1.product_id AND event_type = 'PriceChanged'
     ORDER BY event_id DESC LIMIT 1) as current_price,
    (SELECT event_data->>'quantity' FROM product_events pe2
     WHERE pe2.product_id = pe1.product_id AND event_type = 'InventoryUpdated'
     ORDER BY event_id DESC LIMIT 1) as current_inventory
FROM (SELECT DISTINCT product_id FROM product_events) pe1;

-- View the materialized state
SELECT * FROM product_current_state;

-- ==============================================================================
-- EXERCISE 2.7: Refresh Materialized View (Simulating Stream Processing)
-- ==============================================================================
-- Question: How do we keep the materialized view in sync?

-- Add more events
INSERT INTO product_events (product_id, event_type, event_data) VALUES
    (1, 'InventoryUpdated', '{"quantity": 45}'),
    (2, 'PriceChanged', '{"old_price": 29.99, "new_price": 24.99}');

-- Old state (stale)
SELECT * FROM product_current_state;

-- Refresh to get new state (simulating periodic stream processing)
REFRESH MATERIALIZED VIEW product_current_state;

-- New state (up to date)
SELECT * FROM product_current_state;

-- ==============================================================================
-- PART 5: Dual-Write Problem Solution with CDC
-- ==============================================================================

-- ==============================================================================
-- EXERCISE 2.8: Solve Dual-Write Problem Using CDC
-- ==============================================================================
-- Problem: Without CDC, app writes to DB + cache (dual-write)
-- If one fails, data becomes inconsistent
-- Solution: Single source of truth (DB), derive cache from CDC

-- Source database table
DROP TABLE IF EXISTS accounts CASCADE;
CREATE TABLE accounts (
    account_id   SERIAL PRIMARY KEY,
    customer_name VARCHAR(100) NOT NULL,
    balance      DECIMAL(15,2) DEFAULT 0,
    updated_at   TIMESTAMP DEFAULT NOW()
);

-- CDC event table
DROP TABLE IF EXISTS account_changes CASCADE;
CREATE TABLE account_changes (
    change_id    BIGSERIAL PRIMARY KEY,
    account_id   INT NOT NULL,
    operation    VARCHAR(10) NOT NULL,
    old_balance  DECIMAL(15,2),
    new_balance  DECIMAL(15,2),
    changed_at   TIMESTAMP DEFAULT NOW()
);

-- Trigger to capture changes
CREATE OR REPLACE FUNCTION capture_account_changes()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO account_changes (account_id, operation, new_balance)
        VALUES (NEW.account_id, 'INSERT', NEW.balance);
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO account_changes (account_id, operation, old_balance, new_balance)
        VALUES (NEW.account_id, 'UPDATE', OLD.balance, NEW.balance);
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER account_cdc_trigger
AFTER INSERT OR UPDATE ON accounts
FOR EACH ROW EXECUTE FUNCTION capture_account_changes();

-- Simulate cache table (e.g., Redis equivalent)
DROP TABLE IF EXISTS account_cache CASCADE;
CREATE TABLE account_cache (
    account_id   INT PRIMARY KEY,
    customer_name VARCHAR(100),
    balance      DECIMAL(15,2),
    cached_at    TIMESTAMP DEFAULT NOW()
);

-- Simulate CDC consumer: Apply changes to cache
-- This is how you'd process Kafka events to update Elasticsearch/Redis

-- Initial load from source
INSERT INTO account_cache (account_id, customer_name, balance)
SELECT account_id, customer_name, balance FROM accounts;

-- Simulate processing CDC events to update cache
-- This runs whenever a new CDC event arrives
INSERT INTO account_changes (account_id, operation, old_balance, new_balance)
VALUES (99, 'INSERT', NULL, 1000.00);

-- Consumer processes the change and updates cache
WITH latest_change AS (
    SELECT account_id, operation, new_balance
    FROM account_changes
    WHERE account_id = 99
    ORDER BY change_id DESC
    LIMIT 1
)
INSERT INTO account_cache (account_id, balance)
VALUES (99, (SELECT new_balance FROM latest_change))
ON CONFLICT (account_id) DO UPDATE
    SET balance = EXCLUDED.balance,
        cached_at = NOW();

SELECT * FROM account_cache;

-- ==============================================================================
-- SUMMARY: CDC vs Event Sourcing
-- ==============================================================================

/*
┌─────────────────────────────────────────────────────────────────────────────┐
│ Aspect              │ CDC                              │ Event Sourcing     │
├─────────────────────────────────────────────────────────────────────────────┤
│ Source              │ Database WAL (low-level)        │ App events         │
│ Granularity         │ Row changes (INSERT/UPDATE)    │ Business events    │
│ Intent              │ Extract data from DB            │ Primary storage   │
│ Immutability        │ WAL compacted/truncated        │ Permanent log     │
│ State Reconstruction│ N/A (DB is source of truth)    │ Replay events     │
│ Schema              │ Follows table schema           │ Domain-driven     │
└─────────────────────────────────────────────────────────────────────────────┘
*/

-- Clean up for next section
-- DROP TABLE IF EXISTS orders, order_items, cdc_transaction_log, event_store,
--     kafka_topic_log, product_events, accounts, account_changes, account_cache CASCADE;
-- DROP MATERIALIZED VIEW IF EXISTS product_current_state;
