-- =============================================================================
-- CHAPTER 12: Data Integration - SQL Exercises
-- Book: Designing Data-Intensive Applications
-- Section: 1. Data Integration: The Central Challenge
-- =============================================================================

-- This exercise demonstrates the dual-write problem and the correct approach
-- using a single source of truth with an event log.

-- =============================================================================
-- EXERCISE 1: Understanding the Dual-Write Problem
-- =============================================================================

-- The dual-write problem occurs when an application writes to multiple systems
-- simultaneously. If one write fails, the systems become inconsistent.

-- Let's simulate this scenario:

-- Step 1: Create a "primary" database (our source of truth)
DROP TABLE IF EXISTS orders_primary CASCADE;
CREATE TABLE orders_primary (
    order_id SERIAL PRIMARY KEY,
    customer_name VARCHAR(100),
    amount DECIMAL(10,2),
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Step 2: Create a "search index" (simulating Elasticsearch)
DROP TABLE IF EXISTS orders_search_index;
CREATE TABLE orders_search_index (
    search_id SERIAL PRIMARY KEY,
    order_id INTEGER,
    customer_name VARCHAR(100),
    amount DECIMAL(10,2),
    status VARCHAR(20),
    indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Step 3: Simulate a DUAL-WRITE (the WRONG approach)
-- In this scenario, we insert into BOTH tables. But what if the second fails?

-- First, let's successfully write to primary
INSERT INTO orders_primary (customer_name, amount, status)
VALUES ('Alice Smith', 150.00, 'pending')
RETURNING order_id, customer_name, amount, status;

-- Now simulate a "failed" write to search index (network error, etc.)
-- We'll mark this as failed by not executing it, but show what happens:

-- INSERT INTO orders_search_index (order_id, customer_name, amount, status)
-- VALUES (currval('orders_primary_order_id_seq'), 'Alice Smith', 150.00, 'pending');
-- ^ This might fail due to network issues!

-- RESULT: Primary has the order, but search index doesn't!
-- This is INCONSISTENT data.

-- Query to check inconsistency:
SELECT 'Primary Table' as source, order_id, customer_name, amount, status
FROM orders_primary
UNION ALL
SELECT 'Search Index' as source, order_id, customer_name, amount, status
FROM orders_search_index;

-- =============================================================================
-- EXERCISE 2: The Correct Approach - Single Source of Truth with Event Log
-- =============================================================================

-- Instead of dual writes, we use an EVENT LOG (like Kafka/CDC):
-- Application → Primary DB → Event Log → Derived Systems

-- Step 1: Create the event log (change stream)
DROP TABLE IF EXISTS order_events CASCADE;
CREATE TABLE order_events (
    event_id SERIAL PRIMARY KEY,
    event_type VARCHAR(20) NOT NULL,  -- 'INSERT', 'UPDATE', 'DELETE'
    entity_type VARCHAR(20) NOT NULL,  -- 'order'
    entity_id INTEGER NOT NULL,
    payload JSONB NOT NULL,
    event_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed BOOLEAN DEFAULT FALSE
);

-- Step 2: Create a trigger to automatically capture changes to the event log
-- This simulates CDC (Change Data Capture)

-- Function to record events
CREATE OR REPLACE FUNCTION record_order_event()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO order_events (event_type, entity_type, entity_id, payload)
    VALUES (
        TG_OP,  -- 'INSERT', 'UPDATE', or 'DELETE'
        'order',
        NEW.order_id,
        to_jsonb(NEW)
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger for INSERT
DROP TRIGGER IF EXISTS trg_order_insert ON orders_primary;
CREATE TRIGGER trg_order_insert
AFTER INSERT ON orders_primary
FOR EACH ROW
EXECUTE FUNCTION record_order_event();

-- Apply trigger for UPDATE
DROP TRIGGER IF EXISTS trg_order_update ON orders_primary;
CREATE TRIGGER trg_order_update
AFTER UPDATE ON orders_primary
FOR EACH ROW
EXECUTE FUNCTION record_order_event();

-- Apply trigger for DELETE
DROP TRIGGER IF EXISTS trg_order_delete ON orders_primary;
CREATE TRIGGER trg_order_delete
AFTER DELETE ON orders_primary
FOR EACH ROW
EXECUTE FUNCTION record_order_event();

-- Step 3: Now derive data from the event log (simulating stream processor)

-- Function to sync search index from event log
CREATE OR REPLACE FUNCTION sync_search_index()
RETURNS void AS $$
DECLARE
    event_record RECORD;
BEGIN
    -- Process unprocessed events
    FOR event_record IN
        SELECT event_id, event_type, payload
        FROM order_events
        WHERE processed = FALSE
        ORDER BY event_id
    LOOP
        IF event_record.event_type = 'INSERT' THEN
            INSERT INTO orders_search_index (order_id, customer_name, amount, status)
            VALUES (
                (event_record.payload->>'order_id')::INTEGER,
                event_record.payload->>'customer_name',
                (event_record.payload->>'amount')::DECIMAL,
                event_record.payload->>'status'
            );
        ELSIF event_record.event_type = 'UPDATE' THEN
            UPDATE orders_search_index
            SET customer_name = event_record.payload->>'customer_name',
                amount = (event_record.payload->>'amount')::DECIMAL,
                status = event_record.payload->>'status',
                indexed_at = CURRENT_TIMESTAMP
            WHERE order_id = (event_record.payload->>'order_id')::INTEGER;
        ELSIF event_record.event_type = 'DELETE' THEN
            DELETE FROM orders_search_index
            WHERE order_id = (event_record.payload->>'order_id')::INTEGER;
        END IF;

        -- Mark event as processed
        UPDATE order_events SET processed = TRUE WHERE event_id = event_record.event_id;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- EXERCISE 3: Demonstrate the Correct Pattern
-- =============================================================================

-- Now let's write to PRIMARY only, and let the event log handle the rest

-- Insert a new order (only to primary!)
INSERT INTO orders_primary (customer_name, amount, status)
VALUES ('Bob Johnson', 250.00, 'confirmed')
RETURNING order_id, customer_name, amount, status;

-- Check the event log - the trigger automatically captured it!
SELECT * FROM order_events ORDER BY event_id DESC LIMIT 5;

-- Now "process" the event log to update the search index
SELECT sync_search_index();

-- Verify both tables are now consistent!
SELECT 'Primary Table' as source, order_id, customer_name, amount, status
FROM orders_primary
WHERE order_id = 2
UNION ALL
SELECT 'Search Index' as source, order_id, customer_name, amount, status
FROM orders_search_index
WHERE order_id = 2;

-- Update the order - again, only write to primary!
UPDATE orders_primary
SET status = 'shipped'
WHERE order_id = 2;

-- Process events again
SELECT sync_search_index();

-- Verify the update propagated
SELECT 'Primary Table' as source, order_id, customer_name, amount, status
FROM orders_primary
WHERE order_id = 2
UNION ALL
SELECT 'Search Index' as source, order_id, customer_name, amount, status
FROM orders_search_index
WHERE order_id = 2;

-- =============================================================================
-- EXERCISE 4: Demonstrate Event Replay (Rebuilding Derived Data)
-- =============================================================================

-- Key benefit: You can rebuild ANY derived system by replaying the event log!

-- 1. Clear the search index (simulating rebuilding from scratch)
DELETE FROM orders_search_index;

-- 2. Reset all events to unprocessed
UPDATE order_events SET processed = FALSE;

-- 3. Replay ALL events
SELECT sync_search_index();

-- 4. Verify search index is rebuilt!
SELECT * FROM orders_search_index ORDER BY order_id;
SELECT * FROM orders_primary ORDER BY order_id;

-- =============================================================================
-- EXERCISE 5: Total Ordering with Event Log
-- =============================================================================

-- The event log provides TOTAL ORDERING of all changes.
-- This is crucial for consistency in distributed systems.

-- Insert multiple orders concurrently (simulated with different timestamps)
INSERT INTO orders_primary (customer_name, amount, status) VALUES ('Carol', 100, 'pending');
INSERT INTO orders_primary (customer_name, amount, status) VALUES ('David', 200, 'pending');
INSERT INTO orders_primary (customer_name, amount, status) VALUES ('Eve', 300, 'pending');

-- Process events
SELECT sync_search_index();

-- The event log shows the exact order of operations
SELECT event_id, event_type, entity_id, payload->>'customer_name' as customer, event_timestamp
FROM order_events
WHERE event_type = 'INSERT'
ORDER BY event_id;

-- =============================================================================
-- PRACTICE EXERCISES FOR YOU:
-- =============================================================================

/*
Exercise A: Add a cache table (Redis simulation) and extend the sync function
            to also update the cache when orders change.

Exercise B: Add a "analytics" table that stores total order value per customer
            and update it via the event log.

Exercise C: Simulate a "lagging" consumer - what happens if the search index
            falls behind? Show that it can catch up eventually.

Exercise D: Add a "failed" event handling - what happens if the search index
            update fails? How would you handle dead letters?
*/

-- =============================================================================
-- SUMMARY
-- =============================================================================

/*
KEY TAKEAWAYS from this exercise:

1. DUAL-WRITE IS DANGEROUS: Writing to multiple systems directly can cause
   inconsistency if one write fails or if there's a race condition.

2. SINGLE SOURCE OF TRUTH: Write to ONE system (the primary database), and
   derive all other systems from it.

3. EVENT LOG PATTERN: Use a change log (CDC) to capture all changes.
   Derived systems consume from this log at their own pace.

4. TOTAL ORDERING: The event log provides a total order of all writes,
   preventing race conditions.

5. REPLAYABILITY: Any derived system can be rebuilt from scratch by
   replaying the event log.

This is exactly how Kafka, Debezium, and similar CDC tools work in production!
*/
