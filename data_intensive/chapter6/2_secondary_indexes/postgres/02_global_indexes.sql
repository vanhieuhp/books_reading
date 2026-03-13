-- ================================================================================
--   PostgreSQL Global Secondary Indexes - DDIA Chapter 6.2
--   Learn by doing: Term-Partitioned (Global) Indexes
-- ================================================================================

-- WHAT YOU'LL LEARN:
--   ✅ How global (term-partitioned) indexes work
--   ✅ Why reads are fast with global indexes
--   ✅ Why writes are slow (cross-partition updates)
--   ✅ Eventual consistency implications
--   ✅ How to implement global indexes in PostgreSQL

-- PREREQUISITES:
--   - PostgreSQL 10+ (native partitioning support)
--   - psql or any PostgreSQL client
--   - Completed 01_local_indexes.sql (recommended)

-- ================================================================================
-- CONCEPT: GLOBAL (TERM-PARTITIONED) INDEXES
-- ================================================================================

-- From DDIA (p. 214-217):
--   "Instead of each partition keeping a local index, a global index is
--    constructed that covers data from ALL partitions. However, the global
--    index is itself partitioned — but partitioned differently from the data.
--    It's partitioned by TERM (the indexed value)."
--
--   Write: ❌ Slow (must update index on different node)
--   Read:  ✅ Fast (query only ONE index partition)
--   Consistency: ⚠️ Eventually consistent (async updates)
--
-- Real-world systems using global indexes:
--   - DynamoDB (Global Secondary Indexes - GSI)
--   - Oracle (globally partitioned indexes)
--   - Riak (search feature)

-- NOTE: PostgreSQL doesn't have native "global secondary indexes" like DynamoDB.
-- This exercise demonstrates HOW TO IMPLEMENT them manually and shows the trade-offs.

-- ================================================================================
-- STEP 1: CONNECT TO POSTGRESQL
-- ================================================================================

--   psql -U postgres -d postgres

-- Or:

--   psql -U postgres -d mydb

-- ================================================================================
-- STEP 2: CREATE DATA PARTITIONS (THE ACTUAL DATA)
-- ================================================================================

-- Drop existing tables
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS products_by_color CASCADE;  -- Global index table
DROP TABLE IF EXISTS products_by_brand CASCADE; -- Global index table

-- Create main products table partitioned by product_id (hash)
-- This represents our "data" that we're indexing
CREATE TABLE products (
    product_id BIGSERIAL,
    product_uuid UUID DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    color VARCHAR(20) NOT NULL,
    brand VARCHAR(30) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    stock INTEGER DEFAULT 100,
    created_at TIMESTAMP DEFAULT NOW()
) PARTITION BY HASH (product_uuid);

-- Create 4 data partitions
CREATE TABLE products_p0 PARTITION OF products FOR VALUES WITH (MODULUS 4, REMAINDER 0);
CREATE TABLE products_p1 PARTITION OF products FOR VALUES WITH (MODULUS 4, REMAINDER 1);
CREATE TABLE products_p2 PARTITION OF products FOR VALUES WITH (MODULUS 4, REMAINDER 2);
CREATE TABLE products_p3 PARTITION OF products FOR VALUES WITH (MODULUS 4, REMAINDER 3);

-- Index on product table
CREATE INDEX idx_products_name ON products (name);

-- ================================================================================
-- STEP 3: CREATE GLOBAL INDEX TABLES (MANUAL IMPLEMENTATION)
-- ================================================================================

-- In PostgreSQL, we simulate global indexes using separate tables
-- These tables are PARTITIONED BY THE INDEXED VALUE (term), not by data key

-- Global index by COLOR (term-partitioned)
-- All "red" products go to one partition, all "blue" to another, etc.
CREATE TABLE products_by_color (
    color VARCHAR(20) NOT NULL,
    product_id BIGINT NOT NULL,
    product_uuid UUID NOT NULL,
    name VARCHAR(100) NOT NULL,
    brand VARCHAR(30) NOT NULL,
    price DECIMAL(10,2) NOT NULL
) PARTITION BY LIST (color);

-- Create partitions by COLOR (the indexed term)
CREATE TABLE products_by_color_red PARTITION OF products_by_color
    FOR VALUES IN ('red');
CREATE TABLE products_by_color_blue PARTITION OF products_by_color
    FOR VALUES IN ('blue');
CREATE TABLE products_by_color_black PARTITION OF products_by_color
    FOR VALUES IN ('black');
CREATE TABLE products_by_color_silver PARTITION OF products_by_color
    FOR VALUES IN ('silver');
CREATE TABLE products_by_color_white PARTITION OF products_by_color
    FOR VALUES IN ('white');

-- Global index by BRAND (term-partitioned)
CREATE TABLE products_by_brand (
    brand VARCHAR(30) NOT NULL,
    product_id BIGINT NOT NULL,
    product_uuid UUID NOT NULL,
    name VARCHAR(100) NOT NULL,
    color VARCHAR(20) NOT NULL,
    price DECIMAL(10,2) NOT NULL
) PARTITION BY LIST (brand);

-- Create partitions by BRAND
CREATE TABLE products_by_brand_toyota PARTITION OF products_by_brand
    FOR VALUES IN ('Toyota');
CREATE TABLE products_by_brand_honda PARTITION OF products_by_brand
    FOR VALUES IN ('Honda');
CREATE TABLE products_by_brand_ford PARTITION OF products_by_brand
    FOR VALUES IN ('Ford');
CREATE TABLE products_by_brand_bmw PARTITION OF products_by_brand
    FOR VALUES IN ('BMW');
CREATE TABLE products_by_brand_tesla PARTITION OF products_by_brand
    FOR VALUES IN ('Tesla');

-- Create indexes on global index tables for fast lookups
CREATE INDEX idx_products_by_color_id ON products_by_color (product_id);
CREATE INDEX idx_products_by_brand_id ON products_by_brand (product_id);

-- ================================================================================
-- STEP 4: INSERT DATA AND POPULATE GLOBAL INDEXES
-- ================================================================================

-- Insert products into the main table
INSERT INTO products (name, color, brand, price, stock) VALUES
    ('Camry', 'red', 'Toyota', 25000, 50),
    ('Model S', 'black', 'Tesla', 50000, 30),
    ('F-150', 'blue', 'Ford', 35000, 40),
    ('Civic', 'silver', 'Honda', 22000, 60),
    ('X5', 'black', 'BMW', 55000, 20),
    ('Corolla', 'white', 'Toyota', 24000, 55),
    ('Mustang', 'red', 'Ford', 40000, 25),
    ('Prius', 'silver', 'Toyota', 28000, 45),
    ('Accord', 'black', 'Honda', 26000, 35),
    ('3 Series', 'blue', 'BMW', 38000, 28);

-- NOW: Manually populate the global indexes
-- This simulates what happens in a real system (either sync or async)

-- Populate color index
INSERT INTO products_by_color (color, product_id, product_uuid, name, brand, price)
SELECT color, product_id, product_uuid, name, brand, price
FROM products;

-- Populate brand index
INSERT INTO products_by_brand (brand, product_id, product_uuid, name, color, price)
SELECT brand, product_id, product_uuid, name, color, price
FROM products;

-- ================================================================================
-- STEP 5: DEMONSTRATE FAST READS WITH GLOBAL INDEX
-- ================================================================================

-- GLOBAL INDEX: Reads are FAST because:
--   1. Query goes directly to the index partition for that term
--   2. No need to scan all data partitions
--   3. Single partition access

-- Example 1: Find all RED products
-- Query the COLOR INDEX partition directly (not the main table)
EXPLAIN ANALYZE
SELECT * FROM products_by_color WHERE color = 'red';

-- Notice: Only scans products_by_color_red partition!
-- This is ONE partition, not all 4 data partitions

-- Compare with local index approach (scanning main table)
EXPLAIN ANALYZE
SELECT * FROM products WHERE color = 'red';

-- The main table query must scan ALL 4 partitions!

-- Example 2: Find all TOYOTA products
EXPLAIN ANALYZE
SELECT * FROM products_by_brand WHERE brand = 'Toyota';

-- Only scans products_by_brand_toyota partition!

-- Example 3: Find expensive products by color
EXPLAIN ANALYZE
SELECT * FROM products_by_color WHERE color = 'black' AND price > 50000;

-- Single partition access!

-- ================================================================================
-- STEP 6: DEMONSTRATE SLOW WRITES (INDEX MAINTENANCE)
-- ================================================================================

-- GLOBAL INDEX: Writes are SLOW because:
--   1. Insert into data partition (fast)
--   2. Insert into ALL relevant index partitions (slow!)
--   3. If index is on different node, requires network call

-- Let's demonstrate the write overhead

\timing on

-- Insert a new product
INSERT INTO products (name, color, brand, price, stock)
VALUES ('New Model', 'red', 'Tesla', 60000, 15)
RETURNING product_id, product_uuid;

-- Now manually update the global indexes (this is the SLOW part!)
-- In a real system, this would be done via triggers or application code

-- Get the product_id from the insert above
-- Then insert into global index tables

\timing off

-- In production, you'd use a TRIGGER to keep indexes in sync
-- Let's create triggers for automatic index maintenance

-- ================================================================================
-- STEP 7: AUTOMATE INDEX MAINTENANCE WITH TRIGGERS
-- ================================================================================

-- Create trigger function to maintain color index
CREATE OR REPLACE FUNCTION sync_products_by_color()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO products_by_color (color, product_id, product_uuid, name, brand, price)
        VALUES (NEW.color, NEW.product_id, NEW.product_uuid, NEW.name, NEW.brand, NEW.price);
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        -- Delete old entry
        DELETE FROM products_by_color WHERE product_id = OLD.product_id;
        -- Insert new entry
        INSERT INTO products_by_color (color, product_id, product_uuid, name, brand, price)
        VALUES (NEW.color, NEW.product_id, NEW.product_uuid, NEW.name, NEW.brand, NEW.price);
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        DELETE FROM products_by_color WHERE product_id = OLD.product_id;
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Create trigger
DROP TRIGGER IF EXISTS products_color_sync ON products;
CREATE TRIGGER products_color_sync
AFTER INSERT OR UPDATE OR DELETE ON products
FOR EACH ROW EXECUTE FUNCTION sync_products_by_color();

-- Do the same for brand index
CREATE OR REPLACE FUNCTION sync_products_by_brand()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO products_by_brand (brand, product_id, product_uuid, name, color, price)
        VALUES (NEW.brand, NEW.product_id, NEW.product_uuid, NEW.name, NEW.color, NEW.price);
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        DELETE FROM products_by_brand WHERE product_id = OLD.product_id;
        INSERT INTO products_by_brand (brand, product_id, product_uuid, name, color, price)
        VALUES (NEW.brand, NEW.product_id, NEW.product_uuid, NEW.name, NEW.color, NEW.price);
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        DELETE FROM products_by_brand WHERE product_id = OLD.product_id;
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS products_brand_sync ON products;
CREATE TRIGGER products_brand_sync
AFTER INSERT OR UPDATE OR DELETE ON products
FOR EACH ROW EXECUTE FUNCTION sync_products_by_brand();

-- ================================================================================
-- STEP 8: TEST TRIGGER-BASED INDEX SYNCHRONIZATION
-- ================================================================================

-- Insert a new product - triggers will auto-update indexes
INSERT INTO products (name, color, brand, price, stock)
VALUES ('Test Car', 'red', 'Toyota', 30000, 10);

-- Verify it appears in the global index
SELECT * FROM products_by_color WHERE color = 'red';
SELECT * FROM products_by_brand WHERE brand = 'Toyota';

-- Update the product - indexes should update automatically
UPDATE products SET color = 'blue' WHERE name = 'Test Car';

-- Verify index was updated
SELECT * FROM products_by_color WHERE name = 'Test Car';
SELECT * FROM products_by_brand WHERE name = 'Test Car';

-- Delete the product - indexes should delete automatically
DELETE FROM products WHERE name = 'Test Car';

-- Verify it was removed from indexes
SELECT * FROM products_by_color WHERE name = 'Test Car';

-- ================================================================================
-- STEP 9: DEMONSTRATE EVENTUAL CONSISTENCY (ASYNC UPDATES)
-- ================================================================================

-- In real-world systems like DynamoDB, global indexes are updated ASYNC
-- This creates a "consistency window" where data exists but isn't indexed yet

-- PostgreSQL with triggers is SYNCHRONOUS (immediately consistent)
-- To simulate ASYNC behavior, we can disable triggers temporarily

-- Scenario: Write succeeds, but index update is delayed

-- Disable triggers (simulating async index update)
ALTER TABLE products DISABLE TRIGGER products_color_sync;
ALTER TABLE products DISABLE TRIGGER products_brand_sync;

-- Insert a product - it goes to the main table
INSERT INTO products (name, color, brand, price, stock)
VALUES ('Async Car', 'white', 'Tesla', 70000, 5)
RETURNING product_id, name, color;

-- Check main table: product EXISTS
SELECT product_id, name, color FROM products WHERE name = 'Async Car';

-- Check global index: product NOT YET VISIBLE (consistency window!)
SELECT * FROM products_by_color WHERE name = 'Async Car';
SELECT * FROM products_by_brand WHERE name = 'Async Car';

-- Now "flush" the async updates (re-enable triggers)
ALTER TABLE products ENABLE TRIGGER products_color_sync;
ALTER TABLE products ENABLE TRIGGER products_brand_sync;

-- The product now appears in the index (after the "flush")

-- ================================================================================
-- STEP 10: COMPARE READ PERFORMANCE
-- ================================================================================

-- Scenario 1: Query by PRIMARY KEY (fastest - single partition)
EXPLAIN ANALYZE
SELECT * FROM products WHERE product_id = 1;

-- Scenario 2: Query by LOCAL INDEX (scans all partitions)
EXPLAIN ANALYZE
SELECT * FROM products WHERE color = 'red';

-- Scenario 3: Query by GLOBAL INDEX (single index partition)
EXPLAIN ANALYZE
SELECT p.* FROM products p
INNER JOIN products_by_color idx ON p.product_id = idx.product_id
WHERE idx.color = 'red';

-- Compare the plans:
-- - Scenario 1: Single partition scan
-- - Scenario 2: All 4 partitions scanned (scatter/gather)
-- - Scenario 3: Single index partition scanned (fast!)

-- ================================================================================
-- STEP 11: PRACTICAL QUERIES USING GLOBAL INDEXES
-- ================================================================================

-- Find all red products with price > 30000
SELECT p.* FROM products p
INNER JOIN products_by_color idx ON p.product_id = idx.product_id
WHERE idx.color = 'red' AND p.price > 30000;

-- Find all Toyota products under 25000
explain analyze
SELECT p.* FROM products p
INNER JOIN products_by_brand idx ON p.product_id = idx.product_id
WHERE idx.brand = 'Toyota' AND p.price < 25000;

-- Find products by multiple colors (may need multiple partitions)
explain analyze
SELECT p.* FROM products p
INNER JOIN products_by_color idx ON p.product_id = idx.product_id
WHERE idx.color IN ('red', 'blue');

-- ================================================================================
-- SUMMARY: GLOBAL INDEXES
-- ================================================================================

-- ✅ GLOBAL INDEX PROS:
--   - Reads are FAST (single index partition, no scatter/gather)
--   - Efficient for complex queries
--   - No tail latency problem
--
-- ❌ GLOBAL INDEX CONS:
--   - Writes are SLOW (must update index on different node)
--   - Usually eventually consistent (async updates)
--   - More complex to implement and maintain

-- ⚠️  KEY TRADE-OFF:
--   Write:  Local (fast) vs Global (slow)
--   Read:   Local (slow) vs Global (fast)

-- 📌 WHEN TO USE:
--   - Global indexes: READ-HEAVY workloads (search, e-commerce)
--   - Local indexes:   WRITE-HEAVY workloads (IoT, logs, events)
--
-- ================================================================================
-- COMPARISON WITH LOCAL INDEXES
-- ================================================================================
--
-- | Aspect            | Local Index        | Global Index       |
-- |------------------|-------------------|-------------------|
-- | Write Speed      | Fast (single node)| Slow (cross-node) |
-- | Read Speed       | Slow (all nodes)  | Fast (one node)   |
-- | Consistency      | Immediate         | Eventual          |
-- | Implementation   | Simple            | Complex           |
-- | Best For         | Write-heavy       | Read-heavy        |
--
-- ================================================================================
-- NEXT STEPS:
-- ================================================================================

-- 1. Compare with Local Indexes (01_local_indexes.sql)
-- 2. Run EXPLAIN ANALYZE on both approaches
-- 3. Read DDIA Chapter 6.2 for more theory
-- 4. Consider which approach fits your use case
--
-- EOF
