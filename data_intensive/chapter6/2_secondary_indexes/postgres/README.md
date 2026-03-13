# PostgreSQL Secondary Indexes - Hands-On Learning

## DDIA Chapter 6.2: Partitioning and Secondary Indexes

This directory contains PostgreSQL exercises to help you understand secondary index concepts from "Designing Data-Intensive Applications".

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
   createdb secondary_indexes_demo
   psql -U postgres -d secondary_indexes_demo
   ```

### Run Exercise 1

```bash
psql -U postgres -d postgres -f 01_local_indexes.sql
```

---

## Exercises Overview

| Exercise | File | What You Learn |
|----------|------|----------------|
| 1 | `01_local_indexes.sql` | Local indexes: fast writes, slow reads (scatter/gather) |
| 2 | `02_global_indexes.sql` | Global indexes: slow writes, fast reads (term-partitioned) |

---

## Concepts Covered

### Local (Document-Partitioned) Indexes

Each partition maintains its own index covering only its documents.

```
Partition 0                    Partition 1
┌──────────────────┐          ┌──────────────────┐
│ Data:            │          │ Data:            │
│  car_191 (red)   │          │  car_768 (blue)  │
│  car_214 (black) │          │  car_893 (red)   │
│                  │          │                  │
│ Local Index:     │          │ Local Index:     │
│  red → [191]     │          │  red → [893]     │
│  black → [214]   │          │  blue → [768]    │
└──────────────────┘          └──────────────────┘

Query: "Find all red cars"
  → Query Partition 0: returns [car_191]
  → Query Partition 1: returns [car_893]
  → Merge: [car_191, car_893]
```

**Pros:**
- Writes are fast (single partition)
- No distributed transactions needed

**Cons:**
- Reads require scatter/gather (all partitions)
- Tail latency: slowest partition determines query time

**Used by:** MongoDB, Cassandra, Elasticsearch

---

### Global (Term-Partitioned) Indexes

One global index covers all data, but the index itself is partitioned by term.

```
Data Partitions:
  Partition 0: car_191 (red), car_214 (black)
  Partition 1: car_768 (blue), car_893 (red)

Global Index Partitions (by term):
  Index Partition A (a-r):
    black → [car_214 on Partition 0]
    blue  → [car_768 on Partition 1]

  Index Partition B (s-z):
    red   → [car_191 on Partition 0, car_893 on Partition 1]

Query: "Find all red cars"
  → Query Index Partition B only
  → Returns: [car_191 on P0, car_893 on P1]
  → Fetch from data partitions
```

**Pros:**
- Reads are fast (single index partition)
- No scatter/gather needed

**Cons:**
- Writes are slow (cross-partition update)
- Usually eventually consistent (async updates)

**Used by:** DynamoDB (GSI), Oracle, Riak

---

## The Trade-off

```
LOCAL INDEX:
  Write: ✅ Fast (one partition)
  Read:  ❌ Slow (all partitions)
  Consistency: ✅ Immediate

GLOBAL INDEX:
  Write: ❌ Slow (cross-partition)
  Read:  ✅ Fast (one partition)
  Consistency: ⏳ Eventual
```

---

## How to Verify Index Behavior

### 1. Check query plans for partition scanning

```sql
-- Local index: scans ALL partitions
EXPLAIN ANALYZE SELECT * FROM cars WHERE color = 'red';

-- Global index: scans only ONE partition
EXPLAIN ANALYZE SELECT * FROM products_by_color WHERE color = 'red';
```

### 2. Compare execution times

```sql
-- Time local index query
EXPLAIN (ANALYZE, TIMING) SELECT * FROM cars WHERE color = 'red';

-- Time global index query
EXPLAIN (ANALYZE, TIMING) SELECT * FROM products_by_color WHERE color = 'red';
```

### 3. Check partition stats

```sql
-- See how many rows in each partition
SELECT
    relname AS partition,
    n_live_tup AS rows
FROM pg_stat_user_tables
WHERE relname LIKE 'cars_p%'
ORDER BY relname;
```

---

## Real-World Systems Comparison

| System | Index Type | Use Case |
|--------|-----------|----------|
| MongoDB | Local | Sharded clusters |
| Cassandra | Local | High write throughput |
| Elasticsearch | Local | Full-text search |
| DynamoDB | Global (GSI) | AWS managed, auto-scale |
| Oracle | Global | Enterprise databases |

---

## Common Mistakes

### ❌ Using local indexes for read-heavy workloads
```sql
-- Every color query scans ALL partitions!
SELECT * FROM cars WHERE color = 'red';
```

### ❌ Using global indexes for write-heavy workloads
```sql
-- Every insert must update multiple index tables
-- Triggers add overhead to every write
```

---

## Next Steps

1. **Run both exercises** in order
2. **Experiment**: Change partition counts, query patterns
3. **Monitor**: Use `EXPLAIN ANALYZE` to see partition pruning
4. **Read DDIA**: Chapter 6, Section 2 for theory (pp. 208-217)
5. **Choose** the right approach for your workload:
   - Write-heavy → Local indexes
   - Read-heavy → Global indexes

---

## Troubleshooting

### "partition of ... does not exist"
Make sure you're creating partitions in the correct order:
```sql
CREATE TABLE cars_p0 PARTITION OF cars FOR VALUES WITH (MODULUS 4, REMAINDER 0);
```

### "trigger/function not found"
Run the SQL files in order - later exercises depend on earlier ones.

### Can't see partitions
Check `pg_tables`:
```sql
SELECT tablename FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;
```

---

## References

- [PostgreSQL Partitioning Documentation](https://www.postgresql.org/docs/current/ddl-partitioning.html)
- DDIA Chapter 6: "Partitioning"
- DynamoDB Global Secondary Indexes documentation
