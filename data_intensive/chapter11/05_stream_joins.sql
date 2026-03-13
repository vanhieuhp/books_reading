-- ==============================================================================
-- Chapter 11: Stream Processing - Section 5
-- Stream Joins: Stream-Stream, Stream-Table, Table-Table
-- ==============================================================================
-- Database: PostgreSQL
-- Focus: Conceptual Simulation + CDC Pattern Implementation
-- ==============================================================================

-- ==============================================================================
-- PART 1: Stream-Stream Join (Window Join)
-- ==============================================================================

-- ==============================================================================
-- EXERCISE 5.1: Stream-Stream Join - Ad Impressions and Clicks
-- ==============================================================================
-- Question: How do we correlate events from two streams within a time window?

-- Create ad impression stream
DROP TABLE IF EXISTS ad_impressions CASCADE;
CREATE TABLE ad_impressions (
    impression_id   BIGSERIAL PRIMARY KEY,
    event_time      TIMESTAMP NOT NULL,
    user_id         VARCHAR(50) NOT NULL,
    ad_id           VARCHAR(50) NOT NULL,
    campaign_id     VARCHAR(50),
    impressions     INT DEFAULT 1
);

-- Create ad click stream
DROP TABLE IF EXISTS ad_clicks CASCADE;
CREATE TABLE ad_clicks (
    click_id        BIGSERIAL PRIMARY KEY,
    event_time      TIMESTAMP NOT NULL,
    user_id         VARCHAR(50) NOT NULL,
    ad_id           VARCHAR(50) NOT NULL,
    click_type      VARCHAR(20)  -- 'banner', 'video', 'text'
);

-- Insert sample data: impressions and clicks from same users
INSERT INTO ad_impressions (event_time, user_id, ad_id, campaign_id) VALUES
    ('2026-03-13 10:00:00', 'user_1', 'ad_001', 'campaign_a'),
    ('2026-03-13 10:00:01', 'user_2', 'ad_002', 'campaign_a'),
    ('2026-03-13 10:00:02', 'user_3', 'ad_001', 'campaign_b'),
    ('2026-03-13 10:00:10', 'user_1', 'ad_003', 'campaign_a'),
    ('2026-03-13 10:00:15', 'user_2', 'ad_002', 'campaign_a');

INSERT INTO ad_clicks (event_time, user_id, ad_id, click_type) VALUES
    ('2026-03-13 10:00:05', 'user_1', 'ad_001', 'banner'),  -- Clicked within 5 sec of impression
    ('2026-03-13 10:00:20', 'user_2', 'ad_002', 'text'),    -- Clicked after 19 sec
    ('2026-03-13 10:00:30', 'user_1', 'ad_003', 'video'),  -- Clicked within 20 sec
    ('2026-03-13 10:01:00', 'user_4', 'ad_001', 'banner');  -- Different user

-- Join impressions with clicks within 1 hour window
SELECT
    i.impression_id,
    i.user_id,
    i.ad_id,
    i.event_time as impression_time,
    c.click_id,
    c.event_time as click_time,
    EXTRACT(EPOCH FROM (c.event_time - i.event_time)) as time_to_click_seconds
FROM ad_impressions i
JOIN ad_clicks c
    ON i.user_id = c.user_id
    AND i.ad_id = c.ad_id
    AND c.event_time >= i.event_time
    AND c.event_time <= i.event_time + INTERVAL '1 hour';

-- ==============================================================================
-- EXERCISE 5.2: Stream-Stream Join with All Impressions (Left Join)
-- ==============================================================================
-- Question: How do we find all impressions and their click status?

SELECT
    i.impression_id,
    i.user_id,
    i.ad_id,
    i.event_time as impression_time,
    CASE WHEN c.click_id IS NOT NULL THEN 'clicked' ELSE 'no_click' END as conversion_status,
    c.click_time,
    EXTRACT(EPOCH FROM (c.event_time - i.event_time)) as time_to_click_seconds
FROM ad_impressions i
LEFT JOIN ad_clicks c
    ON i.user_id = c.user_id
    AND i.ad_id = c.ad_id
    AND c.event_time >= i.event_time
    AND c.event_time <= i.event_time + INTERVAL '1 hour';

-- ==============================================================================
-- EXERCISE 5.3: Detect Sequence Patterns in Streams
-- ==============================================================================
-- Question: How do we detect a sequence of events in a stream?

-- Create login and purchase events
DROP TABLE IF EXISTS login_events CASCADE;
CREATE TABLE login_events (
    event_id   BIGSERIAL PRIMARY KEY,
    event_time TIMESTAMP NOT NULL,
    user_id    VARCHAR(50) NOT NULL,
    ip_address VARCHAR(50)
);

DROP TABLE IF EXISTS purchase_events CASCADE;
CREATE TABLE purchase_events (
    event_id   BIGSERIAL PRIMARY KEY,
    event_time TIMESTAMP NOT NULL,
    user_id    VARCHAR(50) NOT NULL,
    amount     DECIMAL(10,2)
);

INSERT INTO login_events (event_time, user_id, ip_address) VALUES
    ('2026-03-13 10:00:00', 'user_1', '192.168.1.1'),
    ('2026-03-13 10:00:05', 'user_2', '10.0.0.1'),
    ('2026-03-13 10:00:10', 'user_1', '192.168.1.1'),
    ('2026-03-13 10:01:00', 'user_3', '172.16.0.1');

INSERT INTO purchase_events (event_time, user_id, amount) VALUES
    ('2026-03-13 10:00:02', 'user_1', 99.99),
    ('2026-03-13 10:00:15', 'user_1', 149.99),
    ('2026-03-13 10:00:30', 'user_2', 50.00);

-- Detect: users who logged in and made a purchase within 10 minutes
SELECT
    l.user_id,
    l.event_time as login_time,
    p.event_time as purchase_time,
    p.amount,
    EXTRACT(EPOCH FROM (p.event_time - l.event_time)) as minutes_after_login
FROM login_events l
JOIN purchase_events p
    ON l.user_id = p.user_id
    AND p.event_time >= l.event_time
    AND p.event_time <= l.event_time + INTERVAL '10 minutes';

-- ==============================================================================
-- PART 2: Stream-Table Join (Enrichment)
-- ==============================================================================

-- ==============================================================================
-- EXERCISE 5.4: Stream-Table Join - Enrich Events with Reference Data
-- ==============================================================================
-- Question: How do we enrich stream events with data from a database table?

-- Create reference table (e.g., user profiles)
DROP TABLE IF EXISTS user_profiles CASCADE;
CREATE TABLE user_profiles (
    user_id      VARCHAR(50) PRIMARY KEY,
    username     VARCHAR(100) NOT NULL,
    email        VARCHAR(100),
    country      VARCHAR(50),
    tier         VARCHAR(20) DEFAULT 'free',  -- free, premium, enterprise
    created_at   TIMESTAMP DEFAULT NOW()
);

-- Create order events stream
DROP TABLE IF EXISTS order_events CASCADE;
CREATE TABLE order_events (
    event_id     BIGSERIAL PRIMARY KEY,
    event_time   TIMESTAMP NOT NULL DEFAULT NOW(),
    order_id     VARCHAR(50) NOT NULL,
    user_id      VARCHAR(50) NOT NULL,
    amount       DECIMAL(10,2) NOT NULL,
    status       VARCHAR(20) DEFAULT 'pending'
);

-- Insert reference data
INSERT INTO user_profiles (user_id, username, email, country, tier) VALUES
    ('user_1', 'alice', 'alice@example.com', 'US', 'premium'),
    ('user_2', 'bob', 'bob@example.com', 'UK', 'free'),
    ('user_3', 'charlie', 'charlie@example.com', 'US', 'enterprise');

-- Insert order events
INSERT INTO order_events (event_time, order_id, user_id, amount, status) VALUES
    ('2026-03-13 10:00:00', 'order_001', 'user_1', 150.00, 'completed'),
    ('2026-03-13 10:00:01', 'order_002', 'user_2', 25.00, 'completed'),
    ('2026-03-13 10:00:02', 'order_003', 'user_3', 500.00, 'pending'),
    ('2026-03-13 10:00:03', 'order_004', 'user_1', 75.00, 'completed');

-- Enrich orders with user profile data
SELECT
    o.order_id,
    o.event_time,
    o.amount,
    o.status,
    u.username,
    u.email,
    u.country,
    u.tier,
    CASE
        WHEN u.tier = 'enterprise' THEN o.amount * 0.9  -- 10% discount
        WHEN u.tier = 'premium' THEN o.amount * 0.95   -- 5% discount
        ELSE o.amount
    END as discounted_amount
FROM order_events o
JOIN user_profiles u ON o.user_id = u.user_id;

-- ==============================================================================
-- EXERCISE 5.5: Stream-Table Join with LATERAL (Per-Row Lookup)
-- ==============================================================================
-- Question: How do we perform per-row lookups efficiently?

-- Create product catalog
DROP TABLE IF EXISTS products CASCADE;
CREATE TABLE products (
    product_id   INT PRIMARY KEY,
    name         VARCHAR(100) NOT NULL,
    category     VARCHAR(50),
    price        DECIMAL(10,2) NOT NULL,
    stock        INT DEFAULT 0
);

-- Create cart events
DROP TABLE IF EXISTS cart_events CASCADE;
CREATE TABLE cart_events (
    event_id     BIGSERIAL PRIMARY KEY,
    event_time   TIMESTAMP NOT NULL DEFAULT NOW(),
    session_id   VARCHAR(50) NOT NULL,
    product_id   INT NOT NULL,
    quantity     INT NOT NULL
);

-- Insert products
INSERT INTO products (product_id, name, category, price, stock) VALUES
    (1, 'Laptop', 'electronics', 999.99, 50),
    (2, 'Mouse', 'electronics', 29.99, 200),
    (3, 'Keyboard', 'electronics', 79.99, 150),
    (4, 'Monitor', 'electronics', 299.99, 30);

-- Insert cart events
INSERT INTO cart_events (event_time, session_id, product_id, quantity) VALUES
    ('2026-03-13 10:00:00', 'sess_001', 1, 1),
    ('2026-03-13 10:00:01', 'sess_001', 2, 2),
    ('2026-03-13 10:00:02', 'sess_002', 3, 1),
    ('2026-03-13 10:00:03', 'sess_003', 4, 1);

-- LATERAL join: for each cart event, look up product details
SELECT
    c.event_id,
    c.session_id,
    c.product_id,
    c.quantity,
    p.name,
    p.price,
    p.stock,
    (p.price * c.quantity) as total_price,
    CASE
        WHEN p.stock >= c.quantity THEN 'IN_STOCK'
        WHEN p.stock > 0 THEN 'LOW_STOCK'
        ELSE 'OUT_OF_STOCK'
    END as availability
FROM cart_events c
CROSS JOIN LATERAL (
    SELECT * FROM products WHERE product_id = c.product_id
) p;

-- ==============================================================================
-- PART 3: Table-Table Join (Materialized View Maintenance)
-- ==============================================================================

-- ==============================================================================
-- EXERCISE 5.6: Table-Table Join - Maintain Joined Materialized View
-- ==============================================================================
-- Question: How do we maintain a materialized view that joins two CDC streams?

-- Create source tables (simulating database tables)
DROP TABLE IF EXISTS customers CASCADE;
CREATE TABLE customers (
    customer_id  SERIAL PRIMARY KEY,
    name         VARCHAR(100) NOT NULL,
    email        VARCHAR(100),
    country      VARCHAR(50)
);

DROP TABLE IF EXISTS orders CASCADE;
CREATE TABLE orders (
    order_id     SERIAL PRIMARY KEY,
    customer_id  INT REFERENCES customers(customer_id),
    order_date   TIMESTAMP DEFAULT NOW(),
    total        DECIMAL(10,2)
);

-- CDC event log (simulating Debezium/Kafka)
DROP TABLE IF EXISTS cdc_log CASCADE;
CREATE TABLE cdc_log (
    log_id       BIGSERIAL PRIMARY KEY,
    table_name   VARCHAR(50) NOT NULL,
    operation    VARCHAR(10) NOT NULL,
    record_id    INT NOT NULL,
    old_data     JSONB,
    new_data     JSONB,
    change_time  TIMESTAMP DEFAULT NOW()
);

-- Insert initial data
INSERT INTO customers (name, email, country) VALUES
    ('Alice', 'alice@example.com', 'US'),
    ('Bob', 'bob@example.com', 'UK'),
    ('Charlie', 'charlie@example.com', 'US');

INSERT INTO orders (customer_id, total) VALUES
    (1, 100.00),
    (1, 150.00),
    (2, 75.00),
    (3, 200.00);

-- Create materialized view: customer with order summary
DROP MATERIALIZED VIEW IF EXISTS customer_order_summary CASCADE;
CREATE MATERIALIZED VIEW customer_order_summary AS
SELECT
    c.customer_id,
    c.name,
    c.email,
    c.country,
    COUNT(o.order_id) as order_count,
    COALESCE(SUM(o.total), 0) as total_spent,
    COALESCE(AVG(o.total), 0) as avg_order_value,
    MAX(o.order_date) as last_order_date
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.name, c.email, c.country;

-- View initial state
SELECT * FROM customer_order_summary;

-- ==============================================================================
-- EXERCISE 5.7: Update Materialized View from CDC
-- ==============================================================================
-- Question: How do we update the materialized view when source tables change?

-- Simulate new order being placed
INSERT INTO orders (customer_id, total) VALUES (1, 250.00);

-- Old view is stale
SELECT * FROM customer_order_summary WHERE customer_id = 1;

-- Refresh the view
REFRESH MATERIALIZED VIEW customer_order_summary;

-- Updated view
SELECT * FROM customer_order_summary WHERE customer_id = 1;

-- ==============================================================================
-- EXERCISE 5.8: Incremental View Maintenance (Advanced)
-- ==============================================================================
-- Question: How do we implement incremental updates instead of full refresh?

-- Create a change log table for tracking changes
DROP TABLE IF EXISTS view_change_log CASCADE;
CREATE TABLE view_change_log (
    change_id     BIGSERIAL PRIMARY KEY,
    change_type   VARCHAR(10) NOT NULL,  -- INSERT, UPDATE, DELETE
    customer_id   INT,
    order_id      INT,
    total         DECIMAL(10,2),
    change_time   TIMESTAMP DEFAULT NOW()
);

-- Function to incrementally update the summary
CREATE OR REPLACE FUNCTION update_customer_summary()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        -- Add new order to summary
        UPDATE customer_order_summary
        SET
            order_count = order_count + 1,
            total_spent = total_spent + NEW.total,
            avg_order_value = (total_spent + NEW.total) / (order_count + 1),
            last_order_date = NEW.order_date
        WHERE customer_id = NEW.customer_id;
        RETURN NEW;

    ELSIF TG_OP = 'DELETE' THEN
        -- Remove order from summary
        UPDATE customer_order_summary
        SET
            order_count = order_count - 1,
            total_spent = total_spent - OLD.total,
            last_order_date = (
                SELECT MAX(order_date) FROM orders
                WHERE customer_id = OLD.customer_id AND order_id != OLD.order_id
            )
        WHERE customer_id = OLD.customer_id;
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Attach trigger to orders table
CREATE TRIGGER orders_summary_update
AFTER INSERT OR DELETE ON orders
FOR EACH ROW EXECUTE FUNCTION update_customer_summary();

-- Test incremental update
INSERT INTO orders (customer_id, total) VALUES (2, 100.00);

-- View is automatically updated!
SELECT * FROM customer_order_summary WHERE customer_id = 2;

-- ==============================================================================
-- PART 4: Complex Join Scenarios
-- ==============================================================================

-- ==============================================================================
-- EXERCISE 5.9: Multi-Stream Join with Time Windows
-- ==============================================================================
-- Question: How do we join multiple streams with time windows?

-- Create three event streams
DROP TABLE IF EXISTS page_views CASCADE;
CREATE TABLE page_views (
    event_id    BIGSERIAL PRIMARY KEY,
    event_time  TIMESTAMP NOT NULL,
    user_id     VARCHAR(50),
    page        VARCHAR(100)
);

DROP TABLE IF EXISTS add_to_carts CASCADE;
CREATE TABLE add_to_carts (
    event_id    BIGSERIAL PRIMARY KEY,
    event_time  TIMESTAMP NOT NULL,
    user_id     VARCHAR(50),
    product_id  INT,
    price       DECIMAL(10,2)
);

DROP TABLE IF EXISTS purchases CASCADE;
CREATE TABLE purchases (
    event_id    BIGSERIAL PRIMARY KEY,
    event_time  TIMESTAMP NOT NULL,
    user_id     VARCHAR(50),
    product_id  INT,
    amount      DECIMAL(10,2)
);

-- Insert correlated events
INSERT INTO page_views (event_time, user_id, page) VALUES
    ('2026-03-13 10:00:00', 'user_1', '/products/1'),
    ('2026-03-13 10:00:05', 'user_1', '/products/2'),
    ('2026-03-13 10:00:10', 'user_2', '/products/1');

INSERT INTO add_to_carts (event_time, user_id, product_id, price) VALUES
    ('2026-03-13 10:00:02', 'user_1', 1, 99.99),
    ('2026-03-13 10:00:15', 'user_2', 1, 99.99);

INSERT INTO purchases (event_time, user_id, product_id, amount) VALUES
    ('2026-03-13 10:00:08', 'user_1', 1, 99.99);

-- Find users who viewed -> added to cart -> purchased within 10 minutes
WITH viewed AS (
    SELECT user_id, product_id, event_time as view_time
    FROM page_views WHERE page LIKE '/products/%'
),
carted AS (
    SELECT user_id, product_id, event_time as cart_time
    FROM add_to_carts
),
purchased AS (
    SELECT user_id, product_id, event_time as purchase_time
    FROM purchases
)
SELECT
    v.user_id,
    v.view_time,
    c.cart_time,
    p.purchase_time,
    EXTRACT(EPOCH FROM (c.cart_time - v.view_time)) as view_to_cart_sec,
    EXTRACT(EPOCH FROM (p.purchase_time - c.cart_time)) as cart_to_purchase_sec
FROM viewed v
JOIN carted c ON v.user_id = c.user_id AND v.product_id = c.product_id
JOIN purchased p ON c.user_id = p.user_id AND c.product_id = p.product_id
WHERE c.cart_time >= v.view_time
    AND c.cart_time <= v.view_time + INTERVAL '10 minutes'
    AND p.purchase_time >= c.cart_time
    AND p.purchase_time <= c.cart_time + INTERVAL '10 minutes';

-- ==============================================================================
-- EXERCISE 5.10:cdc_derived_dataJoin with Slowly Changing Dimension
-- ==============================================================================
-- Question: How do we handle enrichment when reference data changes?

-- Create customer table with version tracking (SCD Type 2)
DROP TABLE IF EXISTS customers_scd CASCADE;
CREATE TABLE customers_scd (
    customer_id   INT NOT NULL,
    name          VARCHAR(100),
    tier          VARCHAR(20),
    valid_from   TIMESTAMP NOT NULL,
    valid_to     TIMESTAMP,
    is_current   BOOLEAN DEFAULT TRUE
);

-- Insert customer with historical versions
INSERT INTO customers_scd (customer_id, name, tier, valid_from, valid_to, is_current) VALUES
    (1, 'Alice', 'free', '2026-01-01', '2026-02-01', FALSE),
    (1, 'Alice', 'premium', '2026-02-01', NULL, TRUE);

-- Create order events
DROP TABLE IF EXISTS orders_with_time CASCADE;
CREATE TABLE orders_with_time (
    order_id     SERIAL PRIMARY KEY,
    customer_id  INT NOT NULL,
    order_time   TIMESTAMP NOT NULL,
    amount       DECIMAL(10,2)
);

INSERT INTO orders_with_time (customer_id, order_time, amount) VALUES
    (1, '2026-01-15', 50.00),   -- When Alice was 'free'
    (1, '2026-02-15', 100.00),  -- When Alice became 'premium'
    (1, '2026-03-01', 150.00);  -- Alice is still 'premium'

-- Join orders with correct customer tier at order time (point-in-time join)
SELECT
    o.order_id,
    o.order_time,
    o.amount,
    c.name,
    c.tier as customer_tier_at_order
FROM orders_with_time o
JOIN customers_scd c
    ON o.customer_id = c.customer_id
    AND o.order_time >= c.valid_from
    AND (c.valid_to IS NULL OR o.order_time < c.valid_to)
ORDER BY o.order_time;

-- ==============================================================================
-- SUMMARY: Stream Join Types
-- ==============================================================================

/*
┌─────────────────────────────────────────────────────────────────────────────┐
│ Join Type           │ Description                    │ SQL Pattern          │
├─────────────────────────────────────────────────────────────────────────────┤
│ Stream-Stream      │ Correlate events from          │ JOIN ON time window  │
│                    │ two streams within time         │                      │
│ Stream-Table       │ Enrich stream with              │ JOIN with reference  │
│                    │ reference data                  │ table                 │
│ Table-Table       │ Maintain materialized view     │ Trigger-based or     │
│                    │ from joined tables              │ REFRESH MATERIALIZED │
│                    │                                 │ VIEW                 │
│ LATERAL Join       │ Per-row correlated             │ CROSS JOIN LATERAL   │
│                    │ subquery                        │                      │
│ Point-in-Time      │ Join with historical           │ Time range condition │
│                    │ version of reference data       │ in JOIN              │
└─────────────────────────────────────────────────────────────────────────────┘
*/

-- Clean up for next section
-- DROP TABLE IF EXISTS ad_impressions, ad_clicks, login_events, purchase_events,
--     user_profiles, order_events, products, cart_events, customers, orders,
--     cdc_log, customer_order_summary, page_views, add_to_carts, purchases,
--     customers_scd, orders_with_time CASCADE;
