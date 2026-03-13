# PostgreSQL Multi-Object Transactions - DDIA Chapter 7.2

---

## Quick Start

```bash
psql -U postgres -d postgres

\i 2_multi_object_transactions/postgres/01_multi_object_transactions.sql
\i 2_multi_object_transactions/postgres/02_error_handling.sql
```

---

## SQL Files

| File | Description |
|------|-------------|
| `01_multi_object_transactions.sql` | Single vs Multi-Object, FK constraints |
| `02_error_handling.sql` | Idempotency, Retries, Deadlocks |
