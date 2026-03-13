# PostgreSQL Partitioning - Hands-On Learning
## DDIA Chapter 6.1: Partitioning of Key-Value Data

This directory contains PostgreSQL exercises to help you understand database partitioning concepts from "Designing Data-Intensive Applications".

---

## Quick Start (15 minutes)

### Prerequisites

1. **Install PostgreSQL** (10 or later for native partitioning):
   - **macOS**: `brew install postgresql@15` then `brew services start postgresql@15`
   - **Ubuntu/Debian**: `sudo apt install postgresql postgresql-contrib`
   - **Windows**: Download from https://www.postgresql.org/download/windows/

2. **Connect to PostgreSQL**:
   ```bash
   # Start psql
   psql -U postgres

   # Or create a database first
   createdb partitioning_demo
   psql -U postgres -d partitioning_demo
   ```

### Run Exercise 1

```bash
psql -U postgres -d postgres -f 01_range_partitioning.sql
```

---

## Exercises Overview

| Exercise | File | What You Learn |
|----------|------|----------------|
| 1 | `01_range_partitioning.sql` | Range partitioning, time-series data, hot spots |
| 2 | `02_hash_partitioning.sql` | Hash partitioning, even distribution, query trade-offs |
| 3 | `03_compound_keys.sql` | List partitioning, compound keys, Cassandra-style |
| 4 | `04_hot_spots.sql` | Detecting and solving hot spot problems |

---

## Detailed Walkthrough

### Exercise 1: Range Partitioning

**Concept**: Keys are assigned to partitions based on continuous ranges.

```sql
-- Create range-partitioned table
CREATE TABLE events (
    event_time TIMESTAMP NOT NULL,
    ...
) PARTITION BY RANGE (event_time);

-- Partitions cover specific time ranges
CREATE TABLE events_jan PARTITION OF events
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

**When to use**:
- Time-series data
- Range queries are common
- Data has natural ordering

**Trade-off**: Sequential keys create hot spots!

---

### Exercise 2: Hash Partitioning

**Concept**: Hash function distributes keys uniformly across partitions.

```sql
CREATE TABLE users (
    user_id BIGINT NOT NULL,
    ...
) PARTITION BY HASH (user_id);

-- 4 partitions using modulus
CREATE TABLE users_p0 PARTITION OF users
    FOR VALUES WITH (MODULUS 4, REMAINDER 0);
```

**When to use**:
- Even distribution is critical
- Point queries by key
- No range query requirements

**Trade-off**: Range queries scan ALL partitions!

---

### Exercise 3: Compound Keys (Best of Both!)

**Concept**: Hash partition key + sorted clustering key (Cassandra-style).

```sql
-- Partition by user_id (hashed), sort by created_at
CREATE TABLE user_posts (
    user_id BIGINT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    ...
) PARTITION BY HASH (user_id);

-- Create index for efficient range queries WITHIN a user
CREATE INDEX idx_posts_user_time ON user_posts (user_id, created_at);
```

**Query that is EFFICIENT**:
```sql
-- Only scans ONE partition, uses index for sorted results
SELECT * FROM user_posts
WHERE user_id = 5
ORDER BY created_at DESC
LIMIT 10;
```

---

### Exercise 4: Hot Spot Solutions

**Problem**: Some keys get all the traffic (e.g., "today" in time-series).

**Solution**: Key splitting

```sql
-- Instead of page_id = 1
-- Use page_id = "1_0", "1_1", "1_2", ... (spread across partitions)

-- To read all: query all split keys
SELECT * FROM page_views WHERE page_id IN ('1_0', '1_1', ..., '1_9');
```

---

## How to Verify Partitioning Works

### 1. Check which partitions have data

```sql
SELECT
    relname AS partition,
    n_live_tup AS rows
FROM pg_stat_user_tables
WHERE relname LIKE 'events%'
ORDER BY relname;
```

### 2. Verify partition pruning (query only relevant partitions)

```sql
EXPLAIN ANALYZE
SELECT * FROM events
WHERE event_time BETWEEN '2024-01-01' AND '2024-01-31';
```

Look for "Index Only Scan using events_jan_idx" (only scans jan partition!)

### 3. Check full table scan (bad for range queries with hash partitioning)

```sql
EXPLAIN ANALYZE
SELECT * FROM users
WHERE user_id BETWEEN 100 AND 200;
```

Look for "Seq Scan on users_p0", "Seq Scan on users_p1", etc. (ALL partitions!)

---

## Partition Types in PostgreSQL

| Type | Keyword | Example |
|------|---------|---------|
| Range | `PARTITION BY RANGE` | `FOR VALUES FROM (1) TO (100)` |
| List | `PARTITION BY LIST` | `FOR VALUES IN ('US', 'EU')` |
| Hash | `PARTITION BY HASH` | `FOR VALUES WITH (MODULUS 4, REMAINDER 0)` |

---

## Common Mistakes

### ❌ Bad: Sequential ID as partition key
```sql
-- All new rows go to LAST partition!
CREATE TABLE orders PARTITION BY RANGE (order_id);
```

### ✅ Good: Composite with time
```sql
-- Spread by year-month prefix
CREATE TABLE orders PARTITION BY LIST (to_char(order_date, 'YYYY-MM'));
```

### ❌ Bad: Range query on hash-partitioned table
```sql
-- Must scan ALL partitions!
SELECT * FROM users WHERE user_id BETWEEN 100 AND 200;
```

---

## Real-World Systems Comparison

| System | Partition Strategy | Use Case |
|--------|-------------------|----------|
| PostgreSQL | Range, List, Hash | General purpose |
| Cassandra | Compound keys | High write throughput |
| HBase | Range (regions) | Time-series, HDFS |
| DynamoDB | Hash | AWS managed, auto-scale |
| MongoDB | Shard keys | Flexible |

---

## Next Steps

1. **Run all 4 exercises** in order
2. **Experiment**: Change partition counts, data distributions
3. **Monitor**: Use `EXPLAIN ANALYZE` to see partition pruning
4. **Read DDIA**: Chapter 6, Section 1 for theory
5. **Try**: Partition your own tables!

---

## Troubleshooting

### "relation does not exist"
Make sure you're running the SQL in the correct database:
```sql
\c mydatabase
\i 01_range_partitioning.sql
```

### "partition of ..." error
Ensure partition key matches parent table exactly:
```sql
-- Parent: TIMESTAMP
-- Child: must also be TIMESTAMP
CREATE TABLE events_jan PARTITION OF events
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

### Can't see partitions
Check `pg_tables`:
```sql
SELECT tablename FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;
```

---

## Questions?

1. Check inline comments in each SQL file
2. Run with `EXPLAIN ANALYZE` to see what's happening
3. Compare with Python examples in parent directory

---

## References

- [PostgreSQL Partitioning Documentation](https://www.postgresql.org/docs/current/ddl-partitioning.html)
- DDIA Chapter 6: "Partitioning"
- "Cassandra: The Definitive Guide" - Compound primary keys
