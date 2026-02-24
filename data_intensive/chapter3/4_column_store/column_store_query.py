#!/usr/bin/env python3
"""
Column Store Approach: Load columns as arrays and compute sum(amount) where type=...

This simulates how a column-oriented database (like ClickHouse, Apache Druid)
would process an analytical query - it only reads the columns it needs and
processes them as arrays (vectorized operations).
"""

import csv
import sys
import time
from pathlib import Path
import numpy as np


def sum_amounts_column_store(csv_file: str, filter_type: str, use_numpy: bool = True) -> float:
    """
    Compute sum(amount) where type=filter_type using column-by-column approach.
    
    This approach:
    1. Load only 'type' and 'amount' columns as arrays
    2. Create boolean mask where type == filter_type
    3. Use mask to filter amounts array
    4. Sum filtered amounts
    
    Advantage: Only read 2 columns instead of all 5! Plus, we can use
    vectorized operations (SIMD) for better performance.
    
    Args:
        csv_file: Path to CSV file
        filter_type: Type to filter by (e.g., "A", "B", "C")
        use_numpy: If True, use NumPy for vectorized operations (faster)
    
    Returns:
        Sum of amounts where type matches filter_type
    """
    print(f"Column Store Approach: Computing sum(amount) where type='{filter_type}'")
    print("=" * 70)
    
    start_time = time.time()
    
    # Step 1: Load only the columns we need (type and amount)
    print("Step 1: Loading columns (type, amount) as arrays...")
    load_start = time.time()
    
    types = []
    amounts = []
    
    with open(csv_file, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Only read the 2 columns we need!
            types.append(row["type"])
            amounts.append(float(row["amount"]))
    
    load_time = time.time() - load_start
    num_rows = len(types)
    print(f"  Loaded {num_rows:,} rows in {load_time:.2f}s")
    print(f"  ✅ Only read 2 columns (type, amount) instead of all 5!")
    print()
    
    # Step 2: Convert to NumPy arrays for vectorized operations
    if use_numpy:
        print("Step 2: Converting to NumPy arrays for vectorized operations...")
        convert_start = time.time()
        types_array = np.array(types)
        amounts_array = np.array(amounts)
        convert_time = time.time() - convert_start
        print(f"  Converted in {convert_time:.2f}s")
        print()
        
        # Step 3: Create boolean mask (vectorized comparison)
        print(f"Step 3: Creating boolean mask (type == '{filter_type}')...")
        mask_start = time.time()
        mask = types_array == filter_type
        mask_time = time.time() - mask_start
        matches = np.sum(mask)
        print(f"  Found {matches:,} matching rows in {mask_time:.4f}s")
        print(f"  ✅ Vectorized comparison (SIMD-friendly)!")
        print()
        
        # Step 4: Filter and sum (vectorized operations)
        print("Step 4: Filtering amounts and computing sum...")
        sum_start = time.time()
        filtered_amounts = amounts_array[mask]
        total = np.sum(filtered_amounts)
        sum_time = time.time() - sum_start
        print(f"  Sum computed in {sum_time:.4f}s")
        print(f"  ✅ Vectorized sum (SIMD-friendly)!")
        print()
    else:
        # Pure Python approach (slower, but shows the concept)
        print("Step 2: Creating boolean mask and filtering (pure Python)...")
        mask_start = time.time()
        filtered_amounts = [
            amount for type_val, amount in zip(types, amounts)
            if type_val == filter_type
        ]
        mask_time = time.time() - mask_start
        matches = len(filtered_amounts)
        print(f"  Found {matches:,} matching rows in {mask_time:.4f}s")
        print()
        
        print("Step 3: Computing sum...")
        sum_start = time.time()
        total = sum(filtered_amounts)
        sum_time = time.time() - sum_start
        print(f"  Sum computed in {sum_time:.4f}s")
        print()
    
    elapsed = time.time() - start_time
    
    print("=" * 70)
    print(f"✅ Query completed!")
    print(f"   Rows processed: {num_rows:,}")
    print(f"   Rows matched: {matches:,}")
    print(f"   Sum: ${total:,.2f}")
    print(f"   Total time: {elapsed:.2f} seconds")
    print(f"   Throughput: {num_rows/elapsed:,.0f} rows/second")
    print()
    print("✅ Advantage: Only read 2 columns instead of all 5!")
    print("✅ Advantage: Vectorized operations (SIMD) for better performance!")
    print("✅ Advantage: Better cache locality (similar values together)!")
    
    return float(total)


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        csv_file = "dataset_5m.csv"
        filter_type = "A"
        use_numpy = True
    elif len(sys.argv) == 2:
        csv_file = sys.argv[1]
        filter_type = "A"
        use_numpy = True
    elif len(sys.argv) == 3:
        csv_file = sys.argv[1]
        filter_type = sys.argv[2]
        use_numpy = True
    else:
        csv_file = sys.argv[1]
        filter_type = sys.argv[2]
        use_numpy = sys.argv[3].lower() == "true"
    
    if not Path(csv_file).exists():
        print(f"Error: File '{csv_file}' not found.")
        print("Run generate_dataset.py first to create the dataset.")
        sys.exit(1)
    
    try:
        result = sum_amounts_column_store(csv_file, filter_type, use_numpy)
        return result
    except ImportError:
        print("Error: NumPy not installed. Install with: pip install numpy")
        print("Trying without NumPy...")
        result = sum_amounts_column_store(csv_file, filter_type, use_numpy=False)
        return result


if __name__ == "__main__":
    main()
