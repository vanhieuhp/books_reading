================================================================================
  PostgreSQL Error Handling & Retries - DDIA Chapter 7.2
  Learn by doing: Handling Transaction Failures
================================================================================

COVERS:
  - Idempotency: Avoiding double execution
  - Exponential backoff: Handling transient errors
  - Transient vs permanent errors
  - Retry patterns

================================================================================
STEP 1: CONNECT
================================================================================

  psql -U postgres -d postgres
  CREATE DATABASE error_handling_demo;
  \c error_handling_demo

================================================================================
STEP 2: SETUP TABLES
================================================================================

DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS order_events CASCADE;

CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INTEGER,
    total DECIMAL(10,2),
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE order_events (
    event_id SERIAL PRIMARY KEY,
    order_id INTEGER,
    event_type VARCHAR(50),
    payload JSONB,
    processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

================================================================================
STEP 3: IDEMPOTENCY
================================================================================

-- Idempotent operations can be safely retried

-- Create idempotent order function
CREATE OR REPLACE FUNCTION create_order_idempotent(
    p_order_id VARCHAR(50),
    p_customer_id INTEGER,
    p_total DECIMAL
) RETURNS INTEGER AS $$
DECLARE
    v_order_id INTEGER;
BEGIN
    -- Check if order already exists
    SELECT order_id INTO v_order_id
    FROM orders
    WHERE order_id = p_order_id;

    -- If exists, return existing ID (idempotent!)
    IF FOUND THEN
        RAISE NOTICE 'Order % already exists, returning existing', p_order_id;
        RETURN v_order_id;
    END IF;

    -- Create new order
    INSERT INTO orders (customer_id, total, status)
    VALUES (p_customer_id, p_total, 'confirmed')
    RETURNING order_id INTO v_order_id;

    RETURN v_order_id;
END;
$$ LANGUAGE plpgsql;

-- Test idempotency
SELECT create_order_idempotent('ORD-001', 1, 100.00);  -- Creates
SELECT create_order_idempotent('ORD-001', 1, 100.00);  -- Returns existing (idempotent!)

-- KEY: Idempotent = safe to retry!

================================================================================
STEP 4: TRANSIENT VS PERMANENT ERRORS
================================================================================

-- Transient errors: Can be retried
-- - Deadlock
-- - Network timeout
-- - Temporary overload
-- - Lock wait timeout

-- Permanent errors: Don't retry
-- - Constraint violation
-- - Invalid data
-- - Permission denied

-- Function to demonstrate error classification
CREATE OR REPLACE FUNCTION classify_error(p_error_code VARCHAR)
RETURNS TEXT AS $$
BEGIN
    RETURN CASE
        -- Transient errors (retry)
        WHEN p_error_code IN ('40001', '40P01', '57014') THEN 'TRANSIENT - Retry'
        -- Permanent errors (don't retry)
        WHEN p_error_code IN ('23505', '23503', '42501') THEN 'PERMANENT - Do not retry'
        ELSE 'UNKNOWN'
    END;
END;
$$ LANGUAGE plpgsql;

-- Test
SELECT classify_error('23505') AS duplicate_key;      -- Permanent
SELECT classify_error('23503') AS foreign_key;        -- Permanent
SELECT classify_error('40P01') AS deadlock;           -- Transient
SELECT classify_error('57014') AS cancel_query;       -- Transient

================================================================================
STEP 5: EXPONENTIAL BACKOFF
================================================================================

-- In application code, implement exponential backoff:

-- Example pattern (pseudo-code):
/*
   retry_count = 0
   max_retries = 3

   while retry_count < max_retries:
       try:
           execute_transaction()
           break
       except TransientError as e:
           retry_count += 1
           sleep(min(100 * 2^retry_count, 1000))  # 100ms, 200ms, 400ms
*/

-- PostgreSQL: Use advisory locks for coordination
CREATE TABLE processing_queue (
    id SERIAL PRIMARY KEY,
    task_name VARCHAR(100),
    status VARCHAR(20) DEFAULT 'pending',
    attempts INTEGER DEFAULT 0
);

INSERT INTO processing_queue (task_name) VALUES
    ('task_1'), ('task_2'), ('task_3');

-- Process with backoff simulation
CREATE OR REPLACE FUNCTION process_with_backoff(p_task_id INTEGER)
RETURNS VOID AS $$
DECLARE
    v_attempts INTEGER;
    v_delay_ms INTEGER;
BEGIN
    -- Get current attempts
    SELECT attempts INTO v_attempts
    FROM processing_queue WHERE id = p_task_id;

    -- Calculate delay (exponential backoff)
    v_delay_ms := 100 * POWER(2, v_attempts);
    RAISE NOTICE 'Attempt %, waiting % ms', v_attempts + 1, v_delay_ms;

    -- Simulate processing
    -- In real code: perform work here

    -- Update attempts
    UPDATE processing_queue
    SET attempts = attempts + 1,
        status = 'completed'
    WHERE id = p_task_id;
END;
$$ LANGUAGE plpgsql;

-- Test
SELECT process_with_backoff(1);
SELECT process_with_backoff(1);
SELECT process_with_backoff(1);

-- KEY: Backoff prevents overwhelming the system!

================================================================================
STEP 6: DEADLOCK HANDLING
================================================================================

-- Deadlocks: PostgreSQL automatically detects and resolves

DROP TABLE IF EXISTS account_a CASCADE;
DROP TABLE IF EXISTS account_b CASCADE;

CREATE TABLE account_a (id SERIAL PRIMARY KEY, balance DECIMAL(10,2));
CREATE TABLE account_b (id SERIAL PRIMARY KEY, balance DECIMAL(10,2));

INSERT INTO account_a (balance) VALUES (1000);
INSERT INTO account_b (balance) VALUES (1000);

-- In two sessions:
-- Session 1: UPDATE account_a SET balance = balance - 100 WHERE id = 1;
-- Session 2: UPDATE account_b SET balance = balance - 100 WHERE id = 1;
-- Session 1: UPDATE account_b SET balance = balance + 100 WHERE id = 1;  (waits)
-- Session 2: UPDATE account_a SET balance = balance + 100 WHERE id = 1;  (DEADLOCK!)

-- PostgreSQL detects and rolls back ONE transaction automatically

-- Best practice: Always acquire locks in same order!

-- Function to safely transfer with consistent locking
CREATE OR REPLACE FUNCTION safe_transfer(
    from_id INTEGER,
    to_id INTEGER,
    amount DECIMAL
) RETURNS BOOLEAN AS $$
BEGIN
    -- Always lock lower ID first to prevent deadlock
    IF from_id < to_id THEN
        PERFORM pg_advisory_lock(from_id);
        PERFORM pg_advisory_lock(to_id);
    ELSE
        PERFORM pg_advisory_lock(to_id);
        PERFORM pg_advisory_lock(from_id);
    END IF;

    -- Perform transfer (with balance check)
    UPDATE account_a SET balance = balance - amount
    WHERE id = from_id AND balance >= amount;

    IF NOT FOUND THEN
        PERFORM pg_advisory_unlock(from_id);
        PERFORM pg_advisory_unlock(to_id);
        RAISE EXCEPTION 'Insufficient funds or invalid account';
    END IF;

    UPDATE account_b SET balance = balance + amount WHERE id = to_id;

    -- Release locks
    IF from_id < to_id THEN
        PERFORM pg_advisory_unlock(from_id);
        PERFORM pg_advisory_unlock(to_id);
    ELSE
        PERFORM pg_advisory_unlock(to_id);
        PERFORM pg_advisory_unlock(from_id);
    END IF;

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

================================================================================
STEP 7: RETRY WITH TRANSACTION
================================================================================

-- Application-level retry pattern

-- In application code:
/*
   def execute_with_retry(func, max_retries=3):
       for attempt in range(max_retries):
           try:
               return func()
           except Exception as e:
               if attempt == max_retries - 1:
                   raise
               if is_transient_error(e):
                   sleep(backoff(attempt))
               else:
                   raise
*/

-- PostgreSQL function with manual retry logic
CREATE OR REPLACE FUNCTION execute_with_retry(
    p_attempts INTEGER DEFAULT 3
) RETURNS TEXT AS $$
DECLARE
    v_attempt INTEGER := 0;
    v_success BOOLEAN := FALSE;
BEGIN
    WHILE v_attempt < p_attempts AND NOT v_success LOOP
        BEGIN
            v_attempt := v_attempt + 1;
            RAISE NOTICE 'Attempt % of %', v_attempt, p_attempts;

            -- Simulate work
            INSERT INTO processing_queue (task_name, status)
            VALUES ('retry_test_' || v_attempt, 'done');

            v_success := TRUE;

        EXCEPTION
            WHEN OTHERS THEN
                IF v_attempt >= p_attempts THEN
                    RAISE EXCEPTION 'All attempts failed: %', SQLERRM;
                END IF;
                RAISE NOTICE 'Attempt % failed: %, retrying...', v_attempt, SQLERRM;
        END;
    END LOOP;

    RETURN 'Success after ' || v_attempt || ' attempts';
END;
$$ LANGUAGE plpgsql;

SELECT execute_with_retry(3);

================================================================================
STEP 8: SUMMARY
================================================================================

✅ IDEMPOTENCY:
  - Same result no matter how many times executed
  - Essential for safe retries

✅ TRANSIENT ERRORS:
  - Deadlock, timeout, overload
  - Should be retried

✅ PERMANENT ERRORS:
  - Constraint violation, invalid data
  - Don't retry

✅ EXPONENTIAL BACKOFF:
  - Wait longer each retry
  - Prevents overwhelming system

EOF
