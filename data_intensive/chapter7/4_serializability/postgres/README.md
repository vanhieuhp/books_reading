# PostgreSQL Serializability - DDIA Chapter 7.4

---

## Quick Start

```bash
psql -U postgres -d postgres

\i 4_serializability/postgres/01_actual_serial_execution.sql
\i 4_serializability/postgres/02_two_phase_locking.sql
\i 4_serializability/postgres/03_serializable_snapshot_isolation.sql
\i 4_serializability/postgres/04_isolation_levels_comparison.sql
```

---

## SQL Files

| File | Description |
|------|-------------|
| `01_actual_serial_execution.sql` | Serial execution, Advisory locks |
| `02_two_phase_locking.sql` | 2PL, Deadlock handling |
| `03_serializable_snapshot_isolation.sql` | SSI, Conflict detection |
| `04_isolation_levels_comparison.sql` | Compare all levels |

---

## Key Commands

```sql
SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
SELECT pg_advisory_xact_lock(1);
SELECT * FROM table FOR UPDATE;
```

---

## References

- DDIA pp. 280-310
