#!/usr/bin/env python3
"""
Visual demonstration of Row Store vs Column Store.

This creates a small example dataset and shows step-by-step how each
approach processes the query sum(amount) where type='A'.
"""

import csv
import io
from pathlib import Path


def create_demo_data():
    """Create a small demo dataset (10 rows)."""
    data = [
        [1, "Alice", "A", 100.50, "2024-01-01"],
        [2, "Bob", "B", 200.75, "2024-01-02"],
        [3, "Charlie", "A", 150.25, "2024-01-03"],
        [4, "David", "A", 300.00, "2024-01-04"],
        [5, "Eve", "B", 250.50, "2024-01-05"],
        [6, "Frank", "A", 175.75, "2024-01-06"],
        [7, "Grace", "C", 400.00, "2024-01-07"],
        [8, "Henry", "A", 125.25, "2024-01-08"],
        [9, "Ivy", "B", 275.50, "2024-01-09"],
        [10, "Jack", "A", 225.00, "2024-01-10"],
    ]
    return data


def visualize_row_store(data, filter_type="A"):
    """Visualize row-by-row processing."""
    print("=" * 80)
    print("ROW STORE APPROACH: Process Row-by-Row")
    print("=" * 80)
    print()
    print("Data Layout (Row Store):")
    print("┌─────────────────────────────────────────────────────────────┐")
    print("│ Row 1: [id=1, name=Alice, type=A, amount=100.50, date=...] │")
    print("│ Row 2: [id=2, name=Bob, type=B, amount=200.75, date=...]   │")
    print("│ Row 3: [id=3, name=Charlie, type=A, amount=150.25, ...]    │")
    print("│ ...                                                         │")
    print("└─────────────────────────────────────────────────────────────┘")
    print()
    print("Query: sum(amount) where type='A'")
    print()
    print("Processing:")
    print("-" * 80)
    
    total = 0.0
    matches = []
    
    for i, row in enumerate(data, 1):
        row_id, name, row_type, amount, date = row
        
        print(f"Row {i}:")
        print(f"  Read: [id={row_id}, name={name}, type={row_type}, amount={amount}, date={date}]")
        print(f"  ⚠️  Must read ALL 5 columns, even though we only need 'type' and 'amount'!")
        
        if row_type == filter_type:
            total += amount
            matches.append((i, amount))
            print(f"  ✅ type='{row_type}' matches! Add {amount} to sum")
        else:
            print(f"  ❌ type='{row_type}' doesn't match, skip")
        print()
    
    print("-" * 80)
    print(f"Result: sum = ${total:.2f}")
    print(f"Matched rows: {len(matches)}")
    print()
    print("⚠️  Problem: Read ALL 5 columns for every row!")
    print("   Data read: 10 rows × 5 columns = 50 values")
    print()
    
    return total, matches


def visualize_column_store(data, filter_type="A"):
    """Visualize column-by-column processing."""
    print("=" * 80)
    print("COLUMN STORE APPROACH: Process Column-by-Column")
    print("=" * 80)
    print()
    print("Data Layout (Column Store):")
    print("┌──────────┬──────────┬──────────┬──────────┬──────────┐")
    print("│ id       │ name     │ type     │ amount   │ date     │")
    print("├──────────┼──────────┼──────────┼──────────┼──────────┤")
    for row in data[:5]:
        print(f"│ {row[0]:<8} │ {row[1]:<8} │ {row[2]:<8} │ {row[3]:<8.2f} │ {row[4]:<8} │")
    print("│ ...      │ ...      │ ...      │ ...      │ ...      │")
    print("└──────────┴──────────┴──────────┴──────────┴──────────┘")
    print()
    print("Stored as separate arrays:")
    print()
    
    # Extract columns
    ids = [row[0] for row in data]
    names = [row[1] for row in data]
    types = [row[2] for row in data]
    amounts = [row[3] for row in data]
    dates = [row[4] for row in data]
    
    print(f"ids    = {ids}")
    print(f"names  = {names}")
    print(f"types  = {types}")
    print(f"amounts = {amounts}")
    print(f"dates  = {dates}")
    print()
    
    print("Query: sum(amount) where type='A'")
    print()
    print("Processing:")
    print("-" * 80)
    print("Step 1: Load only the columns we need (type, amount)")
    print(f"  types  = {types}")
    print(f"  amounts = {amounts}")
    print(f"  ✅ Only read 2 columns instead of all 5!")
    print()
    
    print("Step 2: Create boolean mask (type == 'A')")
    mask = [t == filter_type for t in types]
    print(f"  mask = {mask}")
    print(f"  ✅ Vectorized comparison (SIMD-friendly)!")
    print()
    
    print("Step 3: Filter amounts using mask")
    filtered_amounts = [amount for i, amount in enumerate(amounts) if mask[i]]
    print(f"  filtered_amounts = {filtered_amounts}")
    print(f"  ✅ Only touched 2 columns!")
    print()
    
    print("Step 4: Sum filtered amounts")
    total = sum(filtered_amounts)
    print(f"  sum = {filtered_amounts[0]}", end="")
    for amt in filtered_amounts[1:]:
        print(f" + {amt}", end="")
    print(f" = ${total:.2f}")
    print()
    
    print("-" * 80)
    print(f"Result: sum = ${total:.2f}")
    print(f"Matched rows: {len(filtered_amounts)}")
    print()
    print("✅ Advantage: Only read 2 columns (type, amount)!")
    print("   Data read: 2 columns × 10 rows = 20 values (60% less!)")
    print("✅ Advantage: Better cache locality (similar values together)")
    print("✅ Advantage: Vectorized operations (SIMD-friendly)")
    print()
    
    return total, filtered_amounts


def main():
    """Main demonstration."""
    print("=" * 80)
    print("ROW STORE vs COLUMN STORE - VISUAL DEMONSTRATION")
    print("=" * 80)
    print()
    
    # Create demo data
    data = create_demo_data()
    
    print("Demo Dataset (10 rows):")
    print("-" * 80)
    for row in data:
        print(f"  {row}")
    print()
    
    filter_type = "A"
    
    # Row store approach
    row_total, row_matches = visualize_row_store(data, filter_type)
    
    print()
    print()
    
    # Column store approach
    col_total, col_matches = visualize_column_store(data, filter_type)
    
    # Comparison
    print("=" * 80)
    print("COMPARISON")
    print("=" * 80)
    print()
    print(f"{'Metric':<30} {'Row Store':<25} {'Column Store':<25}")
    print("-" * 80)
    print(f"{'Result':<30} ${row_total:<24.2f} ${col_total:<24.2f}")
    print(f"{'Rows matched':<30} {len(row_matches):<25} {len(col_matches):<25}")
    print(f"{'Columns read':<30} {'5 (all)':<25} {'2 (type, amount)':<25}")
    print(f"{'Values read':<30} {'50 (10×5)':<25} {'20 (10×2)':<25}")
    print()
    
    if abs(row_total - col_total) < 0.01:
        print("✅ Both approaches produce the same result!")
    else:
        print("⚠️  Results differ (shouldn't happen!)")
    
    print()
    print("=" * 80)
    print("KEY INSIGHTS")
    print("=" * 80)
    print()
    print("Row Store:")
    print("  • Must read ALL columns of each row")
    print("  • Good for: 'Get user #12345's complete profile'")
    print("  • Poor for: 'Sum amounts where type=A' (analytics)")
    print()
    print("Column Store:")
    print("  • Only read columns you need")
    print("  • Good for: 'Sum amounts where type=A' (analytics)")
    print("  • Poor for: 'Get user #12345's complete profile' (point lookup)")
    print()
    print("At scale (5M rows):")
    print("  • Row Store: Read 25M values (5M rows × 5 columns)")
    print("  • Column Store: Read 10M values (5M rows × 2 columns)")
    print("  • Speedup: 2-3x faster + better compression!")
    print()


if __name__ == "__main__":
    main()
