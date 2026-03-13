================================================================================
  PostgreSQL Write Skew - DDIA Chapter 7.3
  Learn by doing: Understanding and Preventing Write Skew
================================================================================

COVERS:
  - Write skew anomaly
  - When write skew occurs
  - How to prevent write skew
  - Serializable isolation

================================================================================
STEP 1: CONNECT
================================================================================

  psql -U postgres -d postgres
  CREATE DATABASE write_skew_demo;
  \c write_skew_demo

================================================================================
STEP 2: SETUP
================================================================================

DROP TABLE IF EXISTS doctors CASCADE;
DROP TABLE IF EXISTS game_players CASCADE;

CREATE TABLE doctors (
    doctor_id SERIAL PRIMARY KEY,
    name VARCHAR(50),
    on_call BOOLEAN DEFAULT TRUE
);

CREATE TABLE game_players (
    player_id SERIAL PRIMARY KEY,
    name VARCHAR(50),
    health INTEGER DEFAULT 100,
    position VARCHAR(20)
);

INSERT INTO doctors (name, on_call) VALUES
    ('Dr. Alice', TRUE),
    ('Dr. Bob', TRUE);

INSERT INTO game_players (name, health, position) VALUES
    ('Player1', 50, 'defense'),
    ('Player2', 50, 'attack');

================================================================================
STEP 3: DEMONSTRATE WRITE SKEW
================================================================================

-- Write Skew: Two transactions read overlapping data, write different data

-- Rule: At least one doctor must be on call

-- Session 1: Alice checks if Bob is on call
BEGIN;
    SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;

    -- Check if we can go off call
    SELECT COUNT(*) FROM doctors WHERE on_call = TRUE;  -- Returns 2

-- Session 2: Bob also checks if Alice is on call
-- BEGIN;
--     SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;
--     SELECT COUNT(*) FROM doctors WHERE on_call = TRUE;  -- Returns 2

-- Session 1: Alice goes off call (seems safe - 2 doctors on call)
    UPDATE doctors SET on_call = FALSE WHERE name = 'Dr. Alice';
COMMIT;

-- Session 2: Bob also goes off call (seems safe - 2 doctors on call!)
--     UPDATE doctors SET on_call = FALSE WHERE name = 'Dr. Bob';
-- COMMIT;

-- Result: NO doctor on call! (Violation of business rule!)

SELECT * FROM doctors;

-- KEY: Both transactions saw the same initial state
-- Both thought it was safe to update
-- But combined effect violates constraint!

================================================================================
STEP 4: WHY IT HAPPENS
================================================================================

-- Write Skew pattern:
-- 1. Transaction A reads X and Y (overlapping set)
-- 2. Transaction B reads X and Y (same set)
-- 3. Transaction A modifies X based on its read
-- 4. Transaction B modifies Y based on its read
-- 5. Neither sees the other's change
-- 6. Combined effect violates constraint!

-- Example:
-- Initial: Doctor Alice=on_call, Doctor Bob=on_call (2 on call)
-- T1: Alice reads (2 on call) → OK to go off
-- T2: Bob reads (2 on call) → OK to go off
-- T1: Alice updates (1 on call)
-- T2: Bob updates (0 on call!) ← Violation!

================================================================================
STEP 5: PREVENT WITH SERIALIZABLE
================================================================================

-- Solution: Use SERIALIZABLE isolation level

-- Reset data
UPDATE doctors SET on_call = TRUE;

-- Session 1: SERIALIZABLE
BEGIN;
    SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;

    SELECT COUNT(*) FROM doctors WHERE on_call = TRUE;  -- 2

-- Session 2: SERIALIZABLE
-- BEGIN;
--     SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
--     SELECT COUNT(*) FROM doctors WHERE on_call = TRUE;  -- 2

-- Session 1: Update
    UPDATE doctors SET on_call = FALSE WHERE name = 'Dr. Alice';
COMMIT;

-- Session 2: Try to update
--     UPDATE doctors SET on_call = FALSE WHERE name = 'Dr. Bob';
-- COMMIT;

-- ERROR: could not serialize access due to read/write dependencies

-- KEY: SERIALIZABLE detects write skew and prevents it!

================================================================================
STEP 6: ANOTHER EXAMPLE - GAME PLAYERS
================================================================================

-- Rule: Both players must have health >= 0

-- Session 1: Player1 attacks (damages Player2)
BEGIN;
    SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;

    SELECT health FROM game_players WHERE name = 'Player2';  -- 50

-- Session 2: Player2 defends (heals self)
-- BEGIN;
--     SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;
--     SELECT health FROM game_players WHERE name = 'Player2';  -- 50

-- Session 1: Damage
    UPDATE game_players SET health = health - 60 WHERE name = 'Player2';
COMMIT;

-- Session 2: Heal
--     UPDATE game_players SET health = health + 30 WHERE name = 'Player2';
-- COMMIT;

-- Result: health = -10! (Below zero - violation!)

SELECT * FROM game_players;

-- With SERIALIZABLE: Would prevent this!

================================================================================
STEP 7: ALTERNATIVE SOLUTIONS
================================================================================

-- Option 1: SELECT FOR UPDATE with constraint check

-- Reset
UPDATE game_players SET health = 50;

-- Add constraint
ALTER TABLE game_players ADD CONSTRAINT health_check CHECK (health >= 0);

-- Now try to violate:
-- UPDATE game_players SET health = health - 60 WHERE name = 'Player2';
-- ERROR: new row violates check constraint!

-- Option 2: Explicit locking

CREATE OR REPLACE FUNCTION safe_attack(
    attacker VARCHAR,
    target VARCHAR,
    damage INTEGER
) RETURNS BOOLEAN AS $$
DECLARE
    target_health INTEGER;
BEGIN
    -- Lock target row
    SELECT health INTO target_health
    FROM game_players
    WHERE name = target
    FOR UPDATE;

    -- Check health
    IF target_health < damage THEN
        RAISE EXCEPTION 'Cannot attack: target health % < damage %', target_health, damage;
    END IF;

    -- Apply damage
    UPDATE game_players SET health = health - damage WHERE name = target;

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

SELECT safe_attack('Player1', 'Player2', 60);  -- Fails! Health < 60

-- Option 3: Use SERIALIZABLE

================================================================================
STEP 8: SUMMARY
================================================================================

✅ WRITE SKEW:
  - Two transactions read overlapping data
  - Both modify based on same initial state
  - Combined effect violates constraint

✅ PREVENTION:
  - SERIALIZABLE isolation level
  - Explicit constraints (CHECK)
  - SELECT FOR UPDATE + validation

✅ DETECTION:
  - PostgreSQL SSI detects write skew
  - Forces serialization failure

📌 WHEN TO USE SERIALIZABLE:
  - Business rules across multiple rows
  - Constraints that span multiple records
  - When correctness > performance

EOF
