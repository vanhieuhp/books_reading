-- =============================================================================
-- Section 1: Unix Philosophy & Pipeline
-- From "Designing Data-Intensive Applications" - Chapter 10: Batch Processing
-- =============================================================================
-- Concept: Unix pipes (cat | awk | sort | uniq -c | sort -rn)
-- SQL Equivalent: SELECT → GROUP BY → ORDER BY pipeline
-- =============================================================================

-- Setup: Sample web server access log data
DROP TABLE IF EXISTS access_logs;
CREATE TABLE access_logs (
    log_id INT PRIMARY KEY,
    timestamp TIMESTAMP,
    ip_address VARCHAR(15),
    url VARCHAR(255),
    status_code INT,
    response_time_ms INT
);

-- Insert sample data (mimicking nginx access.log)
INSERT INTO access_logs (log_id, timestamp, ip_address, url, status_code, response_time_ms) VALUES
(1, '2024-01-15 10:00:00', '192.168.1.1', '/api/users', 200, 45),
(2, '2024-01-15 10:00:01', '192.168.1.2', '/api/products', 200, 120),
(3, '2024-01-15 10:00:02', '192.168.1.1', '/api/users', 200, 50),
(4, '2024-01-15 10:00:03', '192.168.1.3', '/api/home', 200, 25),
(5, '2024-01-15 10:00:04', '192.168.1.2', '/api/products', 200, 110),
(6, '2024-01-15 10:00:05', '192.168.1.1', '/api/users', 404, 30),
(7, '2024-01-15 10:00:06', '192.168.1.4', '/api/home', 200, 28),
(8, '2024-01-15 10:00:07', '192.168.1.2', '/api/products', 500, 200),
(9, '2024-01-15 10:00:08', '192.168.1.1', '/api/users', 200, 48),
(10, '2024-01-15 10:00:09', '192.168.1.3', '/api/home', 200, 22);

-- =============================================================================
-- EXERCISE 1-1: Unix awk equivalent - Extract a field (the URL)
-- Unix: awk '{print $7}' access.log
-- SQL: SELECT url FROM logs
-- =============================================================================
-- The Unix 'awk' command extracts a specific field from each line.
-- In SQL, we simply SELECT the column we want.

SELECT url FROM access_logs;

-- =============================================================================
-- EXERCISE 1-2: Unix sort equivalent - Sort URLs alphabetically
-- Unix: sort access.log
-- SQL: SELECT url FROM logs ORDER BY url
-- =============================================================================
-- The Unix 'sort' command orders lines alphabetically.
-- SQL's ORDER BY does the same thing.

SELECT url FROM access_logs ORDER BY url;

-- =============================================================================
-- EXERCISE 1-3: Unix uniq -c equivalent - Count unique URLs
-- Unix: cat access.log | awk '{print $7}' | sort | uniq -c
-- SQL: SELECT url, COUNT(*) as request_count
-- =============================================================================
-- Unix pipeline: cat → awk (extract field) → sort → uniq -c (count duplicates)
-- SQL equivalent: GROUP BY url and COUNT(*)

SELECT url, COUNT(*) AS request_count
FROM access_logs
GROUP BY url;

-- =============================================================================
-- EXERCISE 1-4: Complete Unix pipeline equivalent - Top 5 URLs by request count
-- Unix: cat access.log | awk '{print $7}' | sort | uniq -c | sort -rn | head -5
-- SQL: Complete pipeline with GROUP BY → ORDER BY → LIMIT
-- =============================================================================
-- Full pipeline breakdown:
-- 1. cat access.log          → SELECT (read all data)
-- 2. awk '{print $7}'       → SELECT url (extract field)
-- 3. sort                    → GROUP BY url (group by key)
-- 4. uniq -c                 → COUNT(*) (count per group)
-- 5. sort -rn                → ORDER BY count DESC (sort descending)
-- 6. head -5                 → LIMIT 5 (take top 5)

SELECT url, COUNT(*) AS request_count
FROM access_logs
GROUP BY url
ORDER BY request_count DESC
LIMIT 5;

-- =============================================================================
-- EXERCISE 1-5: Multiple pipelines - Top IPs by total response time
-- Demonstrates: Multiple aggregation levels in one query
-- =============================================================================
-- Similar to running multiple different pipelines on the same data

SELECT
    ip_address,
    COUNT(*) AS total_requests,
    SUM(response_time_ms) AS total_response_time,
    AVG(response_time_ms) AS avg_response_time
FROM access_logs
GROUP BY ip_address
ORDER BY total_response_time DESC;

-- =============================================================================
-- EXERCISE 1-6: Pipeline with filtering - Status code distribution
-- Unix: grep "404" access.log | awk '{print $9}' | sort | uniq -c
-- SQL: WHERE → GROUP BY → COUNT
-- =============================================================================
-- Adding WHERE clause is like using 'grep' before the pipeline

SELECT
    status_code,
    COUNT(*) AS occurrence_count
FROM access_logs
GROUP BY status_code
ORDER BY occurrence_count DESC;

-- =============================================================================
-- EXERCISE 1-7: Chained transformations - URLs with error responses
-- Unix: cat log | awk '$9 ~ /[45]../ {print $7}' | sort | uniq -c
-- SQL: WHERE → SELECT → GROUP BY
-- =============================================================================
-- Filter for 4xx/5xx errors, then extract URL, then count

SELECT
    url,
    COUNT(*) AS error_count,
    status_code
FROM access_logs
WHERE status_code >= 400
GROUP BY url, status_code
ORDER BY error_count DESC;

-- =============================================================================
-- SUMMARY: Unix to SQL Mapping
-- =============================================================================
/*
┌─────────────────────────────────────────────────────────────────────────────┐
│ Unix Command              │ SQL Equivalent                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│ cat file                  │ SELECT * FROM table                            │
│ awk '{print $N}'         │ SELECT column FROM table                       │
│ sort                     │ ORDER BY column                                │
│ uniq                     │ DISTINCT (or GROUP BY for unique rows)        │
│ uniq -c                  │ GROUP BY + COUNT(*)                            │
│ grep pattern             │ WHERE column LIKE/= pattern                    │
│ head -N                  │ LIMIT N                                        │
│ tail -N                  │ OFFSET + LIMIT N                               │
│ wc -l                    │ COUNT(*)                                       │
│ cat | cmd1 | cmd2 | cmd3 │ SELECT → WHERE → GROUP BY → ORDER BY          │
└─────────────────────────────────────────────────────────────────────────────┘
*/
