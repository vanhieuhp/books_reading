#!/usr/bin/env python3
"""
Benchmark comparison: Row Store vs Column Store

This script runs both approaches and compares their performance,
demonstrating why column stores win for analytical queries.
"""

import sys
import time
import subprocess
from pathlib import Path


def run_command(cmd: list) -> tuple[float, str]:
    """Run a command and return execution time and output."""
    start = time.time()
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent
    )
    elapsed = time.time() - start
    
    output = result.stdout + result.stderr
    return elapsed, output


def benchmark_comparison(csv_file: str = "dataset_5m.csv", filter_type: str = "A"):
    """
    Run both approaches and compare performance.
    
    Args:
        csv_file: Path to CSV dataset
        filter_type: Type to filter by
    """
    print("=" * 80)
    print("OLAP / COLUMN STORE BENCHMARK")
    print("=" * 80)
    print()
    print(f"Dataset: {csv_file}")
    print(f"Query: sum(amount) where type='{filter_type}'")
    print()
    
    if not Path(csv_file).exists():
        print(f"❌ Error: File '{csv_file}' not found.")
        print("   Run: python generate_dataset.py")
        return
    
    file_size = Path(csv_file).stat().st_size / (1024 * 1024)  # MB
    print(f"Dataset size: {file_size:.2f} MB")
    print()
    
    # Import the query functions
    sys.path.insert(0, str(Path(__file__).parent))
    from row_store_query import sum_amounts_row_store
    from column_store_query import sum_amounts_column_store
    
    print("=" * 80)
    print("APPROACH 1: ROW STORE (Row-by-Row)")
    print("=" * 80)
    print("Simulates: PostgreSQL, MySQL (traditional OLTP databases)")
    print()
    
    row_start = time.time()
    row_result = sum_amounts_row_store(csv_file, filter_type)
    row_time = time.time() - row_start
    
    print()
    print("=" * 80)
    print("APPROACH 2: COLUMN STORE (Column-by-Column Arrays)")
    print("=" * 80)
    print("Simulates: ClickHouse, Apache Druid, Snowflake (OLAP databases)")
    print()
    
    col_start = time.time()
    try:
        col_result = sum_amounts_column_store(csv_file, filter_type, use_numpy=True)
    except ImportError:
        print("⚠️  NumPy not available, using pure Python...")
        col_result = sum_amounts_column_store(csv_file, filter_type, use_numpy=False)
    col_time = time.time() - col_start
    
    print()
    print("=" * 80)
    print("PERFORMANCE COMPARISON")
    print("=" * 80)
    print()
    
    # Verify results match
    if abs(row_result - col_result) < 0.01:
        print("✅ Results match! (Both approaches computed the same sum)")
    else:
        print(f"⚠️  Results differ: Row={row_result:.2f}, Column={col_result:.2f}")
    
    print()
    print(f"{'Metric':<30} {'Row Store':<20} {'Column Store':<20} {'Speedup':<15}")
    print("-" * 85)
    print(f"{'Execution Time':<30} {row_time:<20.2f} {col_time:<20.2f} {row_time/col_time:<15.2f}x")
    print(f"{'Throughput (rows/sec)':<30} {'N/A':<20} {'N/A':<20} {'N/A':<15}")
    print()
    
    if col_time < row_time:
        speedup = row_time / col_time
        print(f"🚀 Column Store is {speedup:.2f}x FASTER!")
        print()
        print("Why Column Store Wins:")
        print("  ✅ Only reads 2 columns (type, amount) instead of all 5")
        print("  ✅ Better cache locality (similar values together)")
        print("  ✅ Vectorized operations (SIMD-friendly)")
        print("  ✅ Less I/O (40% less data to read)")
    else:
        print("⚠️  Row Store was faster (unusual for analytical queries)")
        print("   This might happen with very small datasets or if NumPy isn't available")
    
    print()
    print("=" * 80)
    print("KEY INSIGHTS")
    print("=" * 80)
    print()
    print("Row Store (OLTP):")
    print("  ✅ Great for: 'Get user #12345's complete profile'")
    print("  ❌ Poor for: 'Sum all sales amounts for product type X'")
    print("  Problem: Must read ALL columns even if you only need 2")
    print()
    print("Column Store (OLAP):")
    print("  ❌ Poor for: 'Get user #12345's complete profile'")
    print("  ✅ Great for: 'Sum all sales amounts for product type X'")
    print("  Advantage: Only read columns you need + better compression")
    print()
    print("Real-World Databases:")
    print("  • OLTP (Row Stores): PostgreSQL, MySQL, MongoDB")
    print("  • OLAP (Column Stores): ClickHouse, Apache Druid, Snowflake, BigQuery")
    print("  • Hybrid: Amazon Redshift (column store with row-like features)")
    print()


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
        filter_type = sys.argv[2] if len(sys.argv) > 2 else "A"
    else:
        csv_file = "dataset_5m.csv"
        filter_type = "A"
    
    benchmark_comparison(csv_file, filter_type)


if __name__ == "__main__":
    main()
