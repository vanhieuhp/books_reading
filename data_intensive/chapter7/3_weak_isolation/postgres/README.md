# PostgreSQL Weak Isolation - DDIA Chapter 7.3

---

## Quick Start

```bash
psql -U postgres -d postgres

\i 3_weak_isolation/postgres/01_read_committed.sql
\i 3_weak_isolation/postgres/02_snapshot_isolation.sql
\i 3_weak_isolation/postgres/03_lost_updates.sql
\i 3_weak_isolation/postgres/04_write_skew.sql
```

---

## SQL Files

| File | Description |
|------|-------------|
| `01_read_committed.sql` | Read Committed, MVCC |
| `02_snapshot_isolation.sql` | Repeatable Read, Snapshot |
| `03_lost_updates.sql` | Lost Update anomaly, prevention |
| `04_write_skew.sql` | Write Skew anomaly, prevention |

---

## Isolation Levels

| Level | Dirty Read | Non-Repeatable | Phantom |
|-------|-----------|----------------|---------|
| Read Committed | ✅ | ❌ | ❌ |
| Repeatable Read | ✅ | ✅ | ❌ |
| Serializable | ✅ | ✅ | ✅ |

---

## References

- DDIA pp. 252-280
