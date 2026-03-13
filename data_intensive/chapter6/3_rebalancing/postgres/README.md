# PostgreSQL Rebalancing - Hands-On Learning

## DDIA Chapter 6.3: Rebalancing Partitions

This directory contains PostgreSQL exercises to help you understand partition rebalancing concepts from "Designing Data-Intensive Applications".

---

## Quick Start (20 minutes)

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
   createdb rebalancing_demo
   psql -U postgres -d rebalancing_demo
   ```

### Run Exercises

```bash
# Exercise 1: Fixed Partition Count
psql -U postgres -d postgres -f 01_fixed_partitions.sql

# Exercise 2: Dynamic Partitioning
psql -U postgres -d postgres -f 02_dynamic_partitioning.sql

# Exercise 3: Consistent Hashing
psql -U postgres -d postgres -f 03_consistent_hashing.sql
```

---

## Exercises Overview

| Exercise | File | What You Learn |
|----------|------|----------------|
| 1 | `01_fixed_partitions.sql` | Fixed partition count, partition reassignment |
| 2 | `02_dynamic_partitioning.sql` | Auto split/merge, cold-start problem |
| 3 | `03_consistent_hashing.sql` | Hash ring, vnodes, minimal data movement |

---

## Concepts Covered

### Strategy 1: Fixed Number of Partitions

**Key Concept**: Partition count is fixed forever; only assignments change.

```
Initial (4 nodes, 8 partitions):
  Node 0: partitions [0, 4]
  Node 1: partitions [1, 5]
  Node 2: partitions [2, 6]
  Node 3: partitions [3, 7]

After adding Node 4:
  Node 0: partitions [0, 5]
  Node 1: partitions [1, 6]
  Node 2: partitions [2, 7]
  Node 3: partitions [3]
  Node 4: partitions [4]  ← new!

KEY: Partitions (P0-P7) NEVER changed!
```

**Pros:**
- Simple rebalancing (just copy partition files)
- Predictable performance

**Cons:**
- Must choose partition count upfront
- Can't adapt to data growth

**Used by:** Riak, Elasticsearch, Couchbase

---

### Strategy 2: Dynamic Partitioning

**Key Concept**: Partitions split when too large, merge when too small.

```
Growth scenario:
  Start: 1 partition (all data)
         ↓ Split
  2 partitions (equal size)
         ↓ Split
  4 partitions...
         ↓ Split
  N partitions (auto-adjusted)
```

**The Cold-Start Problem:**
- New database starts with ONE partition
- All writes bottleneck there → hot spot!

**Solution: Pre-splitting**
- Create many partitions at table creation time
- Prevents hot spot

**Pros:**
- Adapts to data size
- No need to guess partition count

**Cons:**
- Split/merge overhead
- More complex

**Used by:** HBase, MongoDB, RethinkDB

---

### Strategy 3: Consistent Hashing

**Key Concept**: Nodes on a ring; keys go to next node clockwise.

```
Hash Ring (0-360 degrees):
  Node-A @ 0°   Node-B @ 120°   Node-C @ 240°
       ↓             ↓              ↓
  Keys 0-120   Keys 120-240   Keys 240-360

Adding Node-D @ 60°:
  - Only keys between 0°-60° need to move
  - ~1/N of keys move
```

**Virtual Nodes (vnodes):**
- Each physical node has multiple positions on ring
- Better load distribution
- Cassandra uses 256 vnodes/node!

**Pros:**
- Adding nodes only moves 1/N keys
- Good load distribution with vnodes

**Cons:**
- More complex
- Uneven without vnodes

**Used by:** Cassandra, Riak, Voldemort

---

## The Trade-offs

| Strategy | Rebalancing | Data Movement | Complexity |
|----------|-------------|---------------|------------|
| Fixed | Copy files | Can be large | Simple |
| Dynamic | Split/merge | Varies | Medium |
| Consistent Hash | Minimal | ~1/N keys | Complex |

---

## How to Verify Rebalancing

### 1. Check partition distribution

```sql
SELECT
    relname AS partition,
    n_live_tup AS rows
FROM pg_stat_user_tables
WHERE relname LIKE 'users_p%'
ORDER BY relname;
```

### 2. Check partition metadata

```sql
SELECT * FROM pg_partitions
WHERE tablename = 'users'
ORDER BY partitionname;
```

### 3. Monitor rebalancing progress

```sql
-- Check for locks during partition operations
SELECT * FROM pg_locks WHERE relation = 'users'::regclass;
```

---

## Real-World Systems Comparison

| System | Rebalancing Strategy | Notes |
|--------|---------------------|-------|
| Cassandra | Consistent Hashing | 256 vnodes/node |
| Riak | Consistent Hashing | Fixed partitions |
| HBase | Dynamic | Split by size |
| MongoDB | Dynamic | Pre-split recommended |
| Elasticsearch | Fixed | Bulk file moves |
| DynamoDB | Consistent Hashing | Managed by AWS |

---

## Common Mistakes

### ❌ Fixed: Choosing wrong partition count
```sql
-- Too few: partitions too large
CREATE TABLE events PARTITION BY HASH (id);
-- Only 2 partitions created!
```

### ❌ Dynamic: Not pre-splitting
```sql
-- Cold start problem!
CREATE TABLE events PARTITION BY RANGE (time);
-- Only one partition initially
```

### ❌ Consistent: Not using vnodes
```sql
-- Uneven distribution without vnodes!
-- Each node has only 1 position on the ring
```

---

## Next Steps

1. **Run all three exercises** in order
2. **Experiment**: Change partition counts, simulate node failures
3. **Read DDIA**: Chapter 6, Section 3 for theory (pp. 203-215)
4. **Move to**: Section 4 - Request Routing

---

## Troubleshooting

### "partition ... does not exist"
Make sure you're creating partitions after the parent table.

### "cannot drop table used by partition"
You must detach partitions before dropping the parent table.

### "Check constraint conflict"
Partition bounds must not overlap.

---

## References

- [PostgreSQL Partitioning Documentation](https://www.postgresql.org/docs/current/ddl-partitioning.html)
- DDIA Chapter 6: "Rebalancing Partitions" (pp. 203-215)
- Cassandra Architecture: Consistent Hashing
- HBase Region Splitting
