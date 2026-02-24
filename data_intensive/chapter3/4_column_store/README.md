# Day 8-9: OLAP / Column Stores

Learn why column stores dominate analytical workloads!

## What You'll Learn

- **Row Store** = Great for "get one record" (OLTP)
- **Column Store** = Great for "sum over billions" (OLAP)
- Why compression works better with columns
- Why column stores win analytics queries

## Files

- `COLUMN_STORE_EXPLANATION.md` - Comprehensive explanation with visual diagrams
- `generate_dataset.py` - Generate CSV dataset (5 columns, 5M rows)
- `row_store_query.py` - Row-by-row approach (simulates OLTP)
- `column_store_query.py` - Column-by-column arrays approach (simulates OLAP)
- `benchmark_comparison.py` - Compare both approaches side-by-side

## Quick Start

### 1. Generate Dataset

```bash
cd 4_column_store
python generate_dataset.py
```

This creates `dataset_5m.csv` with 5 columns and 5,000,000 rows (~200-300 MB).

**Note:** This may take a few minutes. You can generate a smaller dataset for testing:

```bash
python generate_dataset.py 100000  # 100K rows (faster for testing)
```

### 2. Run Row Store Approach

```bash
python row_store_query.py dataset_5m.csv A
```

This simulates how a traditional row-oriented database (PostgreSQL, MySQL) would process the query.

**What happens:**
- Reads each row completely (all 5 columns)
- Checks if `type == 'A'`
- If match, adds `amount` to sum
- **Problem:** Must read ALL columns even though we only need 2!

### 3. Run Column Store Approach

```bash
python column_store_query.py dataset_5m.csv A
```

This simulates how a column-oriented database (ClickHouse, Apache Druid) would process the query.

**What happens:**
- Loads only `type` and `amount` columns as arrays
- Creates boolean mask where `type == 'A'`
- Filters `amount` array using mask
- Sums filtered amounts
- **Advantage:** Only reads 2 columns + vectorized operations!

### 4. Compare Both Approaches

```bash
python benchmark_comparison.py dataset_5m.csv A
```

This runs both approaches and shows:
- Execution time comparison
- Speedup factor
- Why column stores win for analytics

## Expected Results

On a typical machine, you should see:

```
Row Store:    ~15-30 seconds
Column Store: ~5-10 seconds
Speedup:      2-3x faster
```

**Why the difference?**
- Column store reads 40% less data (2 columns vs 5 columns)
- Better cache locality (similar values together)
- Vectorized operations (SIMD-friendly)

## Understanding the Results

### Row Store (OLTP)
```
Query: sum(amount) where type='A'

Process:
1. Read Row 1 → Parse all 5 columns → Check type → Add amount if match
2. Read Row 2 → Parse all 5 columns → Check type → Add amount if match
3. Read Row 3 → Parse all 5 columns → Check type → Add amount if match
...

I/O: Read 5M rows × 5 columns = 25M values
Time: O(n) where n = number of rows
```

### Column Store (OLAP)
```
Query: sum(amount) where type='A'

Process:
1. Load type column as array → [A, B, A, A, B, ...]
2. Load amount column as array → [100.50, 200.75, 150.25, ...]
3. Create mask: type == 'A' → [True, False, True, True, False, ...]
4. Filter amounts: amounts[mask] → [100.50, 150.25, 300.00, ...]
5. Sum filtered amounts → 550.75

I/O: Read 2 columns × 5M rows = 10M values (40% less!)
Time: O(n) but much faster (less data, vectorized)
```

## Key Concepts

### 1. Data Layout Matters
- **Row layout:** All columns of a row stored together
- **Column layout:** Each column stored as separate array
- Layout determines query performance!

### 2. I/O is the Bottleneck
- Reading from disk is 1000x slower than RAM
- Column stores read less data → faster queries
- Compression makes column stores even faster

### 3. Cache Locality
- CPU cache is 100x faster than RAM
- Column stores: similar values together → better cache hits
- Row stores: mixed data types → cache misses

### 4. Vectorization
- Modern CPUs can process 8-16 values simultaneously (SIMD)
- Column stores enable vectorized operations
- Row stores process one row at a time

## When to Use Each

### Use Row Store (OLTP) when:
- ✅ Get one complete record (e.g., "Get user #12345")
- ✅ Update individual records frequently
- ✅ Need ACID transactions
- ✅ Point lookups or small range scans

**Examples:** User profiles, shopping carts, bank accounts

### Use Column Store (OLAP) when:
- ✅ Aggregate over millions/billions of rows
- ✅ Only need a few columns from many rows
- ✅ Data is append-only (rarely updated)
- ✅ Analytical queries (SUM, COUNT, AVG, GROUP BY)

**Examples:** Sales analytics, log analysis, data warehousing

## Real-World Databases

- **OLTP (Row Stores):** PostgreSQL, MySQL, MongoDB
- **OLAP (Column Stores):** ClickHouse, Apache Druid, Snowflake, BigQuery
- **Hybrid:** Amazon Redshift (column store with row-like features)

## Dependencies

- Python 3.7+
- NumPy (optional, but recommended for better performance):
  ```bash
  pip install numpy
  ```

The column store implementation will work without NumPy, but it will be slower.

## Next Steps

1. Read `COLUMN_STORE_EXPLANATION.md` for detailed explanations
2. Experiment with different filter types (A, B, C, D, E)
3. Try generating different dataset sizes
4. Compare performance on your machine

## Troubleshooting

### "File not found" error
- Run `generate_dataset.py` first to create the dataset

### NumPy not installed
- Install with: `pip install numpy`
- Or the code will fall back to pure Python (slower)

### Dataset generation is slow
- This is normal! 5M rows takes a few minutes
- For testing, generate a smaller dataset: `python generate_dataset.py 100000`

## Summary

**Row Store:**
- Layout: All columns of a row stored together
- Best for: Getting one complete record
- Problem: Must read all columns even if you only need one

**Column Store:**
- Layout: Each column stored as separate array
- Best for: Aggregating over many rows
- Advantage: Only read columns you need + better compression

**The Trade-off:**
- Row stores = Fast point lookups, slow aggregations
- Column stores = Slow point lookups, fast aggregations

This is why modern data warehouses use column stores! 🚀
