# Section 4: SQL / Database Angle

## The Database as Cascade Amplifier

In Chapter 2's incident, the database was both the **trigger** (NULL value in an unexpected column) and the **amplifier** (connection pool exhaustion). Understanding the database perspective is critical because databases are the most common bottleneck in cascading failures.

---

## 4.1: The Connection Leak — What the SQL Layer Saw

### Before the Fix: Connection Leak Under Exception

```sql
-- Context: The application was running queries like this.
-- The problem was NOT the query — it was how connections were managed.

-- This query is perfectly fine:
SELECT name FROM users WHERE id = '12345';

-- But when the application threw an exception AFTER getting the connection
-- and BEFORE closing it, the connection was leaked.

-- To see the damage, a DBA would check active connections:
SELECT
    pid,
    state,
    query,
    age(clock_timestamp(), query_start) AS query_duration,
    wait_event_type,
    wait_event
FROM pg_stat_activity
WHERE datname = 'mydb'
ORDER BY query_start;

-- Expected output during cascade:
--  pid  |  state  |           query             | query_duration | wait_event_type | wait_event
-- ------+---------+-----------------------------+----------------+-----------------+------------
--  1001 |  idle   | SELECT name FROM users...   | 00:05:23       | Client          | ClientRead
--  1002 |  idle   | SELECT name FROM users...   | 00:04:58       | Client          | ClientRead
--  1003 |  idle   | SELECT name FROM users...   | 00:04:31       | Client          | ClientRead
--  ...  |  ...    | ...                         | ...            | ...             | ...
--  1020 |  idle   | SELECT name FROM users...   | 00:00:12       | Client          | ClientRead
-- (20 rows — ALL connections in use, ALL idle — waiting for client that will never come back)

-- staff-level: The key insight is "state = idle" + "wait_event = ClientRead".
-- These connections are waiting for the APPLICATION to send the next command.
-- The application has crashed/thrown an exception and will NEVER send another command.
-- These connections are dead weight but look "in use" to the pool.
```

### How to Detect Connection Leaks in PostgreSQL

```sql
-- MONITORING QUERY: Find leaked connections
-- Run this in production to detect the cascade pattern in real-time.

-- 1. Connections that have been idle for too long (likely leaked)
SELECT
    count(*) AS leaked_count,
    max(age(clock_timestamp(), state_change)) AS longest_idle,
    min(age(clock_timestamp(), state_change)) AS shortest_idle
FROM pg_stat_activity
WHERE datname = 'mydb'
  AND state = 'idle'
  AND age(clock_timestamp(), state_change) > interval '30 seconds';

-- 2. Connection pool pressure — are we near the limit?
SELECT
    max_conn,
    used,
    max_conn - used AS available,
    ROUND(100.0 * used / max_conn, 1) AS pct_used
FROM (
    SELECT
        setting::int AS max_conn,
        (SELECT count(*) FROM pg_stat_activity) AS used
    FROM pg_settings
    WHERE name = 'max_connections'
) t;

-- 3. Per-application breakdown (who's consuming connections?)
SELECT
    application_name,
    count(*) AS connections,
    count(*) FILTER (WHERE state = 'idle') AS idle,
    count(*) FILTER (WHERE state = 'active') AS active,
    count(*) FILTER (WHERE state = 'idle in transaction') AS idle_in_tx,
    avg(age(clock_timestamp(), query_start))
        FILTER (WHERE state = 'active') AS avg_query_time
FROM pg_stat_activity
WHERE datname = 'mydb'
GROUP BY application_name
ORDER BY connections DESC;
```

---

## 4.2: Query Timeout Configuration

### PostgreSQL Statement Timeout

```sql
-- ✅ SET QUERY TIMEOUT AT SESSION LEVEL
-- This prevents any single query from running longer than 5 seconds.
-- If the query exceeds this, PostgreSQL cancels it and returns an error.

SET statement_timeout = '5s';

-- For a single transaction:
BEGIN;
SET LOCAL statement_timeout = '3s';
SELECT name FROM users WHERE id = '12345';
COMMIT;

-- At the DATABASE level (affects all new sessions):
ALTER DATABASE mydb SET statement_timeout = '10s';

-- At the ROLE level (per-application — best practice):
-- staff-level: Different applications need different timeouts.
-- Your web app needs 3s. Your batch job needs 300s.
ALTER ROLE webapp SET statement_timeout = '5s';
ALTER ROLE batch_processor SET statement_timeout = '300s';
```

### Idle-In-Transaction Timeout

```sql
-- ✅ CRITICAL: Prevent connections that start a transaction and never finish.
-- This is the exact pattern from Chapter 2 — application throws exception
-- mid-transaction, connection is abandoned with an open transaction.
-- That open transaction holds locks and prevents VACUUM.

SET idle_in_transaction_session_timeout = '30s';

-- At the database level:
ALTER DATABASE mydb SET idle_in_transaction_session_timeout = '60s';

-- staff-level: idle_in_transaction is MORE dangerous than idle.
-- An idle connection just wastes a slot.
-- An idle-in-transaction connection wastes a slot AND holds locks AND
-- prevents autovacuum from cleaning up dead tuples → table bloat → slow queries.
```

---

## 4.3: Connection Pool Sizing — The Math

### The HikariCP Formula

```sql
-- staff-level: Connection pool sizing is not guesswork. There's a formula.
--
-- pool_size = Tn × (Cm − 1) + 1
--   Tn = number of threads (or concurrent requests)
--   Cm = number of simultaneous connections needed per request
--
-- Example: 20 threads, each request needs exactly 1 connection:
--   pool_size = 20 × (1 - 1) + 1 = 1  (minimum, but too small for safety)
--
-- In practice, add headroom:
--   pool_size = Tn × Cm + buffer
--   pool_size = 20 × 1 + 5 = 25
--
-- PostgreSQL's max_connections must be >= sum of all pools:
--   If you have 3 app instances, each with pool_size = 25:
--   max_connections >= 75 + 25 (for admin/monitoring) = 100

-- Check your current PostgreSQL limits:
SHOW max_connections;  -- default: 100

-- Check current usage vs limits:
SELECT
    setting AS max_connections,
    numbackends AS current_connections,
    setting::int - numbackends AS available
FROM pg_settings, pg_stat_database
WHERE pg_settings.name = 'max_connections'
  AND pg_stat_database.datname = 'mydb';
```

### Connection Pool Monitoring Table

```sql
-- ✅ CREATE A MONITORING TABLE for connection pool metrics.
-- Your application should periodically INSERT pool stats.
-- This lets you correlate connection usage with incidents.

CREATE TABLE IF NOT EXISTS connection_pool_metrics (
    id             BIGSERIAL PRIMARY KEY,
    recorded_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    app_instance   TEXT NOT NULL,       -- hostname or pod name
    pool_name      TEXT NOT NULL,       -- 'primary', 'read-replica', etc.
    total_conns    INT NOT NULL,        -- total pool size
    active_conns   INT NOT NULL,        -- currently executing queries
    idle_conns     INT NOT NULL,        -- available for use
    waiting_threads INT NOT NULL,       -- threads waiting for a connection
    max_wait_ms    BIGINT,              -- longest wait time
    timeout_count  INT DEFAULT 0        -- connections that timed out
);

-- Index for time-range queries:
CREATE INDEX idx_pool_metrics_time ON connection_pool_metrics (recorded_at DESC);

-- Query to detect cascade pattern:
-- staff-level: The canary signal is waiting_threads > 0 AND active_conns = total_conns.
-- This means the pool is full AND threads are waiting → cascade imminent.

SELECT
    recorded_at,
    app_instance,
    active_conns,
    waiting_threads,
    max_wait_ms,
    CASE
        WHEN waiting_threads > 0 AND active_conns = total_conns
        THEN '🔴 CASCADE IMMINENT'
        WHEN active_conns::float / total_conns > 0.8
        THEN '🟡 HIGH UTILIZATION'
        ELSE '🟢 HEALTHY'
    END AS status
FROM connection_pool_metrics
WHERE recorded_at > NOW() - INTERVAL '5 minutes'
ORDER BY recorded_at DESC;
```

---

## 4.4: Defensive SQL Patterns

### NULL-Safe Queries

```sql
-- ✅ Handle NULL at the SQL level — don't push the problem to application code.

-- Instead of:
SELECT name FROM users WHERE id = '12345';
-- Returns: NULL (application throws NullPointerException)

-- Use COALESCE:
SELECT COALESCE(name, 'UNKNOWN') AS name FROM users WHERE id = '12345';
-- Returns: 'UNKNOWN' (always a non-null value)

-- For multiple fallbacks:
SELECT COALESCE(display_name, username, email, 'anonymous') AS name
FROM users WHERE id = '12345';
```

### Query Performance Under Cascade

```sql
-- During a cascade, you'll see queries stacking up.
-- Use EXPLAIN ANALYZE to understand WHY queries are slow.

EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT name FROM users WHERE id = '12345';

-- Normal output:
--  Index Scan using users_pkey on users  (cost=0.29..8.31 rows=1 width=32)
--    (actual time=0.015..0.016 rows=1 loops=1)
--    Index Cond: (id = '12345'::text)
--    Buffers: shared hit=3
--  Planning Time: 0.052 ms
--  Execution Time: 0.031 ms

-- During cascade (lock contention):
--  Index Scan using users_pkey on users  (cost=0.29..8.31 rows=1 width=32)
--    (actual time=4523.105..4523.106 rows=1 loops=1)    ← 4.5 SECONDS!
--    Index Cond: (id = '12345'::text)
--    Buffers: shared hit=3
--  Planning Time: 12045.230 ms                           ← 12 SECONDS just to plan!
--  Execution Time: 4523.158 ms

-- staff-level: Planning time > 1s indicates lock contention or catalog bloat.
-- The query is simple, but it's waiting for locks held by idle-in-transaction sessions.
-- These are the leaked connections from the cascade.
```

---

## Key Database Insights for Cascade Prevention

| Defense | SQL/DB Setting | Why It Works |
|---|---|---|
| Query timeout | `statement_timeout = '5s'` | Prevents slow queries from holding connections |
| Transaction timeout | `idle_in_transaction_session_timeout = '30s'` | Kills leaked connections automatically |
| Connection limits | `max_connections = 100` | Database won't accept more than it can handle |
| Pool sizing | `MaximumPoolSize = 25` | Application doesn't overwhelm database |
| NULL handling | `COALESCE(col, default)` | Prevents NULL from propagating to application |
| Lock monitoring | `pg_stat_activity` | Detect cascade at database level |

---

[← Previous: Section 3](./section_03_code_examples.md) | [Next: Section 5 — Real-World Use Cases →](./section_05_real_world_cases.md)
