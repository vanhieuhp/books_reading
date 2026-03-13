================================================================================
  PostgreSQL Actual Serial Execution - DDIA Chapter 7.4
  Learn by doing: True Serial Execution
================================================================================

COVERS:
  - Actual serial execution concept
  - Advisory locks for serialization
  - Sequence-based serialization
  - When to use serial execution

================================================================================
STEP 1: CONNECT
================================================================================

  psql -U postgres -d postgres
  CREATE DATABASE serial_execution_demo;
  \c serial_execution_demo

================================================================================
STEP 2: SETUP
================================================================================

DROP TABLE IF EXISTS counters CASCADE;
DROP TABLE IF EXISTS processing_jobs CASCADE;

CREATE TABLE counters (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50),
    value INTEGER DEFAULT 0
);

CREATE TABLE processing_jobs (
    job_id SERIAL PRIMARY KEY,
    job_name VARCHAR(100),
    status VARCHAR(20) DEFAULT 'pending',
    result TEXT
);

INSERT INTO counters (name, value) VALUES ('total', 0), ('processed', 0);
INSERT INTO processing_jobs (job_name, status) VALUES ('job_1', 'pending'), ('job_2', 'pending');

================================================================================
STEP 3: SERIAL EXECUTION CONCEPT
================================================================================

-- Actual serial execution: Run one transaction at a time

-- In PostgreSQL: Use advisory locks to enforce serial execution

-- Example: Process jobs one at a time
CREATE OR REPLACE FUNCTION process_job_serial(p_job_id INTEGER)
RETURNS TEXT AS $$
DECLARE
    v_result TEXT;
BEGIN
    -- Acquire exclusive lock (serial execution)
    PERFORM pg_advisory_xact_lock(1);  -- Lock ID 1

    -- Simulate processing
    v_result := 'Job ' || p_job_id || ' processed at ' || NOW();

    -- Update job status
    UPDATE processing_jobs
    SET status = 'completed', result = v_result
    WHERE job_id = p_job_id;

    -- Update counter
    UPDATE counters SET value = value + 1 WHERE name = 'processed';

    RETURN v_result;
END;
$$ LANGUAGE plpgsql;

-- Test serial execution
SELECT process_job_serial(1);
SELECT process_job_serial(2);

SELECT * FROM processing_jobs;
SELECT * FROM counters;

-- KEY: Advisory locks ensure only ONE transaction runs at a time!

================================================================================
STEP 4: USING SEQUENCES FOR SERIALIZATION
================================================================================

-- Sequences in PostgreSQL are inherently serial

CREATE SEQUENCE order_number_seq;

-- Multiple transactions getting next value:
-- T1: SELECT nextval('order_number_seq') → 1
-- T2: SELECT nextval('order_number_seq') → 2
-- T3: SELECT nextval('order_number_seq') → 3

-- Each gets unique, increasing number

SELECT nextval('order_number_seq');
SELECT nextval('order_number_seq');
SELECT nextval('order_number_seq');

-- Use sequences for serial IDs

================================================================================
STEP 5: PRACTICAL PATTERN - IDEMPOTENT PROCESSING
================================================================================

-- Use advisory lock for idempotent processing

CREATE OR REPLACE FUNCTION process_with_idempotency(
    p_key VARCHAR
) RETURNS TEXT AS $$
DECLARE
    v_key_hash BIGINT;
    v_result TEXT;
BEGIN
    -- Generate lock ID from key
    v_key_hash := hashtext(p_key);

    -- Acquire lock
    PERFORM pg_advisory_xact_lock(v_key_hash);

    -- Check if already processed
    SELECT result INTO v_result
    FROM processing_jobs
    WHERE job_name = p_key AND status = 'completed';

    IF FOUND THEN
        RETURN 'Already processed: ' || v_result;
    END IF;

    -- Process
    v_result := 'Processed: ' || p_key || ' at ' || NOW()::text;

    -- Store result
    INSERT INTO processing_jobs (job_name, status, result)
    VALUES (p_key, 'completed', v_result);

    RETURN v_result;
END;
$$ LANGUAGE plpgsql;

-- Test idempotent processing
SELECT process_with_idempotency('order_123');
SELECT process_with_idempotency('order_123');  -- Same key - returns cached result
SELECT process_with_idempotency('order_456');

-- KEY: Idempotent + serial = correct concurrent processing!

================================================================================
STEP 6: WHEN TO USE SERIAL EXECUTION
================================================================================

-- Use serial execution when:
-- - Correctness is critical
-- - Concurrent access causes race conditions
-- - Operations must be atomic

-- Example: Inventory allocation
DROP TABLE IF EXISTS inventory CASCADE;

CREATE TABLE inventory (
    item_id SERIAL PRIMARY KEY,
    item_name VARCHAR(50),
    quantity INTEGER DEFAULT 10,
    reserved INTEGER DEFAULT 0
);

INSERT INTO inventory (item_name, quantity) VALUES
    ('Widget', 10),
    ('Gadget', 5);

CREATE OR REPLACE FUNCTION reserve_item(
    p_item_id INTEGER,
    p_quantity INTEGER
) RETURNS BOOLEAN AS $$
DECLARE
    v_available INTEGER;
BEGIN
    -- Serial execution
    PERFORM pg_advisory_xact_lock(p_item_id);

    -- Check availability
    SELECT quantity - reserved INTO v_available
    FROM inventory
    WHERE item_id = p_item_id;

    IF v_available < p_quantity THEN
        RAISE EXCEPTION 'Insufficient quantity: % < %', v_available, p_quantity;
    END IF;

    -- Reserve
    UPDATE inventory SET reserved = reserved + p_quantity
    WHERE item_id = p_item_id;

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Test
SELECT reserve_item(1, 3);
SELECT reserve_item(1, 8);  -- Will fail (only 7 left)

SELECT * FROM inventory;

================================================================================
STEP 7: SUMMARY
================================================================================

✅ ACTUAL SERIAL EXECUTION:
  - One transaction at a time
  - No concurrency
  - Maximum correctness

✅ ADVISORY LOCKS:
  - pg_advisory_xact_lock()
  - Application-controlled serialization
  - No table locks

✅ USE CASES:
  - Idempotent processing
  - Inventory allocation
  - Critical sections

❌ TRADE-OFF:
  - No parallelism
  - Lower throughput

EOF
