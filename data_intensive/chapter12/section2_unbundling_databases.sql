-- =============================================================================
-- CHAPTER 12: Unbundling Databases - SQL Exercises
-- Book: Designing Data-Intensive Applications
-- Section: 2. Unbundling Databases
-- =============================================================================

-- This exercise demonstrates how to "unbundle" a monolithic database into
-- specialized systems connected by event logs.

-- =============================================================================
-- EXERCISE 1: Traditional Database vs Unbundled Architecture
-- =============================================================================

-- In a traditional database, ALL features are bundled together:
-- - Storage engine
-- - Primary key index
-- - Secondary indexes
-- - Caching
-- - Full-text search
-- - Replication
-- - Analytics

-- Let's simulate the UNBUNDLED approach:
-- Each "feature" becomes a separate specialized system.

-- -----------------------------------------------------------------------------
-- System 1: Primary Storage (PostgreSQL) - stores the authoritative data
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS products CASCADE;
CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    category VARCHAR(50),
    stock_quantity INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- -----------------------------------------------------------------------------
-- System 2: Search Index (simulating Elasticsearch) - optimized for text search
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS products_search;
CREATE TABLE products_search (
    search_id SERIAL PRIMARY KEY,
    product_id INTEGER,
    name VARCHAR(200),
    description_textvector TSVECTOR,  -- Full-text search vector
    category VARCHAR(50),
    price DECIMAL(10,2),
    indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create GIN index for full-text search
DROP INDEX IF EXISTS idx_products_search_fts;
CREATE INDEX idx_products_search_fts ON products_search USING GIN(description_textvector);

-- -----------------------------------------------------------------------------
-- System 3: Cache (simulating Redis) - low-latency reads
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS products_cache;
CREATE TABLE products_cache (
    cache_key VARCHAR(100) PRIMARY KEY,
    product_id INTEGER,
    name VARCHAR(200),
    price DECIMAL(10,2),
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

-- -----------------------------------------------------------------------------
-- System 4: Analytics (simulating Data Warehouse) - aggregations
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS products_analytics;
CREATE TABLE products_analytics (
    analytics_id SERIAL PRIMARY KEY,
    category VARCHAR(50),
    total_products INTEGER DEFAULT 0,
    avg_price DECIMAL(10,2),
    min_price DECIMAL(10,2),
    max_price DECIMAL(10,2),
    total_stock INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- EXERCISE 2: The Event Log (Change Data Capture)
-- =============================================================================

-- This is the "backbone" that connects all systems - like Kafka!

DROP TABLE IF EXISTS product_events;
CREATE TABLE product_events (
    event_id SERIAL PRIMARY KEY,
    event_type VARCHAR(20) NOT NULL,  -- INSERT, UPDATE, DELETE
    entity_id INTEGER NOT NULL,
    payload JSONB NOT NULL,
    event_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed BOOLEAN DEFAULT FALSE
);

-- Trigger function to capture all changes
CREATE OR REPLACE FUNCTION record_product_event()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO product_events (event_type, entity_id, payload)
    VALUES (
        TG_OP,
        COALESCE(NEW.product_id, OLD.product_id),
        to_jsonb(COALESCE(NEW, OLD))
    );
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Apply triggers
DROP TRIGGER IF EXISTS trg_product_insert ON products;
CREATE TRIGGER trg_product_insert
AFTER INSERT ON products
FOR EACH ROW EXECUTE FUNCTION record_product_event();

DROP TRIGGER IF EXISTS trg_product_update ON products;
CREATE TRIGGER trg_product_update
AFTER UPDATE ON products
FOR EACH ROW EXECUTE FUNCTION record_product_event();

DROP TRIGGER IF EXISTS trg_product_delete ON products;
CREATE TRIGGER trg_product_delete
AFTER DELETE ON products
FOR EACH ROW EXECUTE FUNCTION record_product_event();

-- =============================================================================
-- EXERCISE 3: Stream Processors (Deriving Data from Event Log)
-- =============================================================================

-- Each "derived system" is updated by processing the event log.
-- This is analogous to Kafka Streams, Flink, or similar stream processors.

-- -----------------------------------------------------------------------------
-- Stream Processor 1: Search Indexer
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION process_search_indexer()
RETURNS void AS $$
DECLARE
    event_record RECORD;
BEGIN
    FOR event_record IN
        SELECT event_id, event_type, entity_id, payload
        FROM product_events
        WHERE processed = FALSE
        ORDER BY event_id
    LOOP
        IF event_record.event_type = 'INSERT' THEN
            INSERT INTO products_search (product_id, name, description_textvector, category, price)
            VALUES (
                event_record.payload->>'product_id',
                event_record.payload->>'name',
                to_tsvector('english', COALESCE(event_record.payload->>'description', '')),
                event_record.payload->>'category',
                (event_record.payload->>'price')::DECIMAL
            );
        ELSIF event_record.event_type = 'UPDATE' THEN
            UPDATE products_search
            SET name = event_record.payload->>'name',
                description_textvector = to_tsvector('english', COALESCE(event_record.payload->>'description', '')),
                category = event_record.payload->>'category',
                price = (event_record.payload->>'price')::DECIMAL,
                indexed_at = CURRENT_TIMESTAMP
            WHERE product_id = (event_record.payload->>'product_id')::INTEGER;
        ELSIF event_record.event_type = 'DELETE' THEN
            DELETE FROM products_search WHERE product_id = event_record.entity_id;
        END IF;

        UPDATE product_events SET processed = TRUE WHERE event_id = event_record.event_id;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- -----------------------------------------------------------------------------
-- Stream Processor 2: Cache Manager
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION process_cache_manager()
RETURNS void AS $$
DECLARE
    event_record RECORD;
    cache_key TEXT;
BEGIN
    FOR event_record IN
        SELECT event_id, event_type, entity_id, payload
        FROM product_events
        WHERE processed = FALSE
        ORDER BY event_id
    LOOP
        cache_key := 'product:' || event_record.entity_id;

        IF event_record.event_type IN ('INSERT', 'UPDATE') THEN
            INSERT INTO products_cache (cache_key, product_id, name, price, expires_at)
            VALUES (
                cache_key,
                event_record.payload->>'product_id',
                event_record.payload->>'name',
                (event_record.payload->>'price')::DECIMAL,
                CURRENT_TIMESTAMP + INTERVAL '1 hour'
            )
            ON CONFLICT (cache_key) DO UPDATE SET
                name = EXCLUDED.name,
                price = EXCLUDED.price,
                cached_at = CURRENT_TIMESTAMP,
                expires_at = CURRENT_TIMESTAMP + INTERVAL '1 hour';
        ELSIF event_record.event_type = 'DELETE' THEN
            DELETE FROM products_cache WHERE cache_key = event_record.entity_id::TEXT;
        END IF;

        UPDATE product_events SET processed = TRUE WHERE event_id = event_record.event_id;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- -----------------------------------------------------------------------------
-- Stream Processor 3: Analytics Aggregator
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION process_analytics_aggregator()
RETURNS void AS $$
BEGIN
    -- Recalculate analytics from the primary table
    -- In production, you'd do incremental updates!
    TRUNCATE products_analytics;

    INSERT INTO products_analytics (category, total_products, avg_price, min_price, max_price, total_stock)
    SELECT
        category,
        COUNT(*) as total_products,
        AVG(price) as avg_price,
        MIN(price) as min_price,
        MAX(price) as max_price,
        SUM(stock_quantity) as total_stock
    FROM products
    GROUP BY category;

    -- Mark all events as processed
    UPDATE product_events SET processed = TRUE WHERE processed = FALSE;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- EXERCISE 4: Demonstrate Unbundled Architecture
-- =============================================================================

-- Step 1: Insert a product (only to primary!)
INSERT INTO products (name, description, price, category, stock_quantity)
VALUES (
    'Wireless Headphones',
    'High-quality wireless headphones with noise cancellation and 20-hour battery life',
    199.99,
    'Electronics',
    50
);

-- Step 2: Process the event log through all stream processors
SELECT 'Processing search indexer' as processor, process_search_indexer() as result;
SELECT 'Processing cache manager' as processor, process_cache_manager() as result;
SELECT 'Processing analytics aggregator' as processor, process_analytics_aggregator() as result;

-- Step 3: Query each "system" to see the derived data

-- Primary Storage (OLTP)
SELECT 'Primary Storage' as system, * FROM products;

-- Search Index (Full-Text Search)
SELECT 'Search Index' as system, product_id, name, category, price FROM products_search;

-- Cache (Low-Latency)
SELECT 'Cache' as system, * FROM products_cache;

-- Analytics (Aggregations)
SELECT 'Analytics' as system, * FROM products_analytics;

-- =============================================================================
-- EXERCISE 5: Full-Text Search Demo (Elasticsearch simulation)
-- =============================================================================

-- Now let's demonstrate the power of unbundled search!

-- Insert more products
INSERT INTO products (name, description, price, category, stock_quantity) VALUES
('Bluetooth Speaker', 'Portable waterproof speaker with deep bass', 79.99, 'Electronics', 100),
('Laptop Stand', 'Ergonomic adjustable aluminum laptop stand', 49.99, 'Accessories', 200),
('USB-C Hub', '7-in-1 USB-C hub with HDMI and card reader', 39.99, 'Electronics', 150),
('Mechanical Keyboard', 'RGB mechanical keyboard with Cherry MX switches', 149.99, 'Electronics', 75);

-- Process events
SELECT process_search_indexer();
SELECT process_cache_manager();
SELECT process_analytics_aggregator();

-- Full-text search queries
-- Search for "speaker" (should find Bluetooth Speaker)
SELECT 'Search: speaker' as query, product_id, name, category, price
FROM products_search
WHERE description_textvector @@ plainto_tsquery('english', 'speaker')
ORDER BY product_id;

-- Search for "wireless" (should find Wireless Headphones)
SELECT 'Search: wireless' as query, product_id, name, category, price
FROM products_search
WHERE description_textvector @@ plainto_tsquery('english', 'wireless')
ORDER BY product_id;

-- Search for "keyboard" (should find Mechanical Keyboard)
SELECT 'Search: keyboard' as query, product_id, name, category, price
FROM products_search
WHERE description_textvector @@ plainto_tsquery('english', 'keyboard')
ORDER BY product_id;

-- =============================================================================
-- EXERCISE 6: Demonstrate Independent Scaling
-- =============================================================================

-- One key benefit: each system can be scaled independently!
-- Let's simulate "catching up" after lag

-- Simulate: Search index is behind (lagging)
-- Add more products
INSERT INTO products (name, description, price, category, stock_quantity) VALUES
('Webcam HD', '1080p HD webcam with built-in microphone', 89.99, 'Electronics', 60),
('Monitor Arm', 'Gas spring monitor arm for 27-inch displays', 129.99, 'Accessories', 40);

-- But don't process search indexer yet!
-- The search index is "lagging behind"

-- Cache is up to date (processed immediately)
SELECT process_cache_manager();

-- Analytics is also up to date
SELECT process_analytics_aggregator();

-- Show the lag
SELECT 'Products in Primary' as source, COUNT(*) as count FROM products
UNION ALL
SELECT 'Products in Search' as source, COUNT(*) as count FROM products_search
UNION ALL
SELECT 'Products in Cache' as source, COUNT(*) as count FROM products_cache;

-- Now "catch up" the search index
SELECT process_search_indexer();

-- Verify they're now consistent
SELECT 'Products in Search (after catchup)' as source, COUNT(*) as count FROM products_search;

-- =============================================================================
-- EXERCISE 7: "Database Inside Out" - Externalized Components
-- =============================================================================

-- This demonstrates the concept of "turning the database inside out"

/*
Traditional Database:
  [Storage] + [Index] + [Cache] + [Replication] all bundled together

Unbundled Architecture:
  [PostgreSQL Storage] → Event Log → [Elasticsearch Index]
  [PostgreSQL Storage] → Event Log → [Redis Cache]
  [PostgreSQL Storage] → Event Log → [PostgreSQL Analytics]
  [PostgreSQL Storage] → Event Log → [Kafka Replication]

Each component is now:
- Independently scalable
- Replaceable (swap Elasticsearch for Solr, etc.)
- Debuggable (you can see exactly what's in each system)
- Optimized for its specific use case
*/

-- Show current state of all systems
SELECT '=== FINAL STATE ===' as info;

SELECT 'Primary Storage' as system, COUNT(*) as records FROM products
UNION ALL
SELECT 'Search Index', COUNT(*) FROM products_search
UNION ALL
SELECT 'Cache', COUNT(*) FROM products_cache
UNION ALL
SELECT 'Analytics', COUNT(*) FROM products_analytics;

-- =============================================================================
-- PRACTICE EXERCISES FOR YOU:
-- =============================================================================

/*
Exercise A: Add a "recommendations" derived system that tracks which products
            are frequently bought together (simulating collaborative filtering).

Exercise B: Add a "price history" system that tracks all price changes over time.

Exercise C: Simulate a "rebuilding" scenario - drop and recreate the search index,
            then replay all events to rebuild it.

Exercise D: Add latency simulation - make the search indexer processing slower
            and show how it falls behind, then catches up.
*/

-- =============================================================================
-- SUMMARY
-- =============================================================================

/*
KEY TAKEAWAYS from this exercise:

1. UNBUNDLING: Instead of one database that does everything, use multiple
   specialized systems, each optimized for a specific access pattern.

2. DATABASE INSIDE OUT: The internal components of a database (indexes,
   cache, replication) become external services that you can choose.

3. EVENT LOG AS BACKBONE: The event log (Kafka) connects all systems,
   providing total ordering and replayability.

4. INDEPENDENT SCALING: Each derived system can scale independently.
   The search index might need 10 nodes, while analytics needs 100.

5. DERIVED DATA: Each system (search, cache, analytics) is DERIVED from
   the primary source. They can all be rebuilt from the event log.

This is how modern data platforms work: Kafka + Debezium + Elasticsearch
+ Redis + Snowflake/Databricks!
*/
