# PostgreSQL ACID Properties - Hands-On Learning

## DDIA Chapter 7.1: The Meaning of ACID

---

## Quick Start

```bash
psql -U postgres -d postgres

# Run all exercises
\i 1_acid/postgres/01_acid_properties.sql
\i 1_acid/postgres/02_single_vs_multi_object.sql
```

---

## SQL Files

| File | Description |
|------|-------------|
| `01_acid_properties.sql` | Atomicity, Consistency, Isolation, Durability |
| `02_single_vs_multi_object.sql` | Single vs Multi-Object Transactions |

---

## Concepts Covered

### 1. Atomicity: All-or-Nothing

```sql
BEGIN;
    UPDATE accounts SET balance = balance - 100 WHERE name = 'Alice';
    UPDATE accounts SET balance = balance + 100 WHERE name = 'Bob';
COMMIT;
```

---

### 2. Consistency: Invariants

```sql
ALTER TABLE accounts ADD CHECK (balance >= 0);
```

---

### 3. Isolation: Concurrent Transactions

```sql
SHOW transaction_isolation;  -- Default: read committed
```

---

### 4. Durability: WAL

```sql
SHOW wal_level;
SHOW synchronous_commit;
```

---

## References

- [PostgreSQL Transaction Documentation](https://www.postgresql.org/docs/current/transactions.html)
- DDIA Chapter 7.1: pp. 228-244
