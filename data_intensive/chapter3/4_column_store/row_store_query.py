#!/usr/bin/env python3
"""
Row Store Approach: Read CSV row-by-row and compute sum(amount) where type=...

This simulates how a traditional row-oriented database (like PostgreSQL) would
process an analytical query - it must read entire rows even if we only need
a few columns.
"""

import csv
import sys
import time
from pathlib import Path


def sum_amounts_row_store(csv_file: str, filter_type: str) -> float:
    """
    Compute sum(amount) where type=filter_type using row-by-row approach.
    
    This approach:
    1. Reads each row completely (all 5 columns)
    2. Checks if type matches filter
    3. If match, adds amount to sum
    
    Problem: Even though we only need 'type' and 'amount', we must read
    ALL columns (id, name, type, amount, date) for every row!
    
    Args:
        csv_file: Path to CSV file
        filter_type: Type to filter by (e.g., "A", "B", "C")
    
    Returns:
        Sum of amounts where type matches filter_type
    """
    total = 0.0
    rows_processed = 0
    rows_matched = 0
    
    print(f"Row Store Approach: Computing sum(amount) where type='{filter_type}'")
    print("=" * 70)
    
    start_time = time.time()
    
    with open(csv_file, "r") as f:
        reader = csv.DictReader(f)  # Read as dictionary (row-oriented)
        
        for row in reader:
            rows_processed += 1
            
            # We must read ALL columns to check type and get amount
            # Even though we don't need id, name, or date!
            if row["type"] == filter_type:
                amount = float(row["amount"])
                total += amount
                rows_matched += 1
            
            # Progress indicator
            if rows_processed % 1_000_000 == 0:
                elapsed = time.time() - start_time
                print(f"  Processed {rows_processed:,} rows ({rows_matched:,} matched) - {elapsed:.2f}s")
    
    elapsed = time.time() - start_time
    
    print("=" * 70)
    print(f"✅ Query completed!")
    print(f"   Rows processed: {rows_processed:,}")
    print(f"   Rows matched: {rows_matched:,}")
    print(f"   Sum: ${total:,.2f}")
    print(f"   Time: {elapsed:.2f} seconds")
    print(f"   Throughput: {rows_processed/elapsed:,.0f} rows/second")
    print()
    print("⚠️  Note: Read ALL 5 columns for every row, even though we only needed 2!")
    
    return total


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        csv_file = "dataset_5m.csv"
        filter_type = "A"
    elif len(sys.argv) == 2:
        csv_file = sys.argv[1]
        filter_type = "A"
    else:
        csv_file = sys.argv[1]
        filter_type = sys.argv[2]
    
    if not Path(csv_file).exists():
        print(f"Error: File '{csv_file}' not found.")
        print("Run generate_dataset.py first to create the dataset.")
        sys.exit(1)
    
    result = sum_amounts_row_store(csv_file, filter_type)
    return result


if __name__ == "__main__":
    main()
