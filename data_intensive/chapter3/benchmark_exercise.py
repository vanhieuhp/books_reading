#!/usr/bin/env python3
"""
Tiny exercise: Compare performance of indexed vs reverse scan lookups.

Inserts 100k keys and times:
- get() with hash index (2_hash_index)
- get_latest() from reverse scan (1_log_append)
"""

import sys
import time
import importlib.util
from pathlib import Path

# Import modules from subdirectories (can't use normal import because dirs start with numbers)
base_dir = Path(__file__).parent

# Load logdb.py from 1_log_append
logdb_path = base_dir / "1_log_append" / "logdb.py"
logdb_spec = importlib.util.spec_from_file_location("logdb", logdb_path)
logdb_module = importlib.util.module_from_spec(logdb_spec)
logdb_module.__name__ = "logdb"  # Set module name explicitly
logdb_module.__file__ = str(logdb_path)  # Set file path
sys.modules["logdb"] = logdb_module  # Register in sys.modules before execution
logdb_spec.loader.exec_module(logdb_module)
LogDB = logdb_module.LogDB

# Load logdb_indexed.py from 2_hash_index
indexed_path = base_dir / "2_hash_index" / "logdb_indexed.py"
indexed_spec = importlib.util.spec_from_file_location("logdb_indexed", indexed_path)
indexed_module = importlib.util.module_from_spec(indexed_spec)
indexed_module.__name__ = "logdb_indexed"  # Set module name explicitly
indexed_module.__file__ = str(indexed_path)  # Set file path
sys.modules["logdb_indexed"] = indexed_module  # Register in sys.modules before execution
indexed_spec.loader.exec_module(indexed_module)
LogDBIndexed = indexed_module.LogDBIndexed


def format_time(seconds: float) -> str:
    """Format time in human-readable format."""
    if seconds < 0.001:
        return f"{seconds * 1_000_000:.2f} μs"
    elif seconds < 1:
        return f"{seconds * 1000:.2f} ms"
    else:
        return f"{seconds:.2f} s"


def main():
    print("=" * 80)
    print("BENCHMARK: Indexed vs Reverse Scan Lookups")
    print("=" * 80)
    print()

    # Clean up old files
    log_file = base_dir / "1_log_append" / "data.log"
    indexed_file = base_dir / "2_hash_index" / "data_indexed.log"
    
    if log_file.exists():
        log_file.unlink()
        print(f"✓ Cleaned up {log_file}")
    if indexed_file.exists():
        indexed_file.unlink()
        print(f"✓ Cleaned up {indexed_file}")
    print()

    # Initialize databases
    print("Initializing databases...")
    db_log = LogDB(str(base_dir / "1_log_append" / "data.log"))
    db_indexed = LogDBIndexed(str(base_dir / "2_hash_index" / "data_indexed.log"))
    print("✓ Databases initialized\n")

    # Insert 100k keys
    num_keys = 100_000
    print(f"Inserting {num_keys:,} keys (user:1 to user:{num_keys})...")
    
    start_insert = time.time()
    for i in range(1, num_keys + 1):
        key = f"user:{i}"
        value = {"name": f"User{i}", "age": 20 + (i % 50), "id": i}
        
        # Insert into both databases
        db_log.put(key, value)
        db_indexed.put(key, value)
        
        # Progress indicator
        if i % 10_000 == 0:
            elapsed = time.time() - start_insert
            rate = i / elapsed
            print(f"  Progress: {i:,}/{num_keys:,} ({i*100/num_keys:.1f}%) - "
                  f"{rate:.0f} inserts/sec")
    
    insert_time = time.time() - start_insert
    print(f"✓ Inserted {num_keys:,} keys in {format_time(insert_time)}")
    print(f"  Average: {insert_time/num_keys*1000:.2f} ms per insert\n")

    # Build index for indexed database
    print("Building hash index...")
    start_build = time.time()
    db_indexed.build_index()
    build_time = time.time() - start_build
    print(f"✓ Index built in {format_time(build_time)}")
    print(f"  Index size: {len(db_indexed.index):,} entries\n")

    # Get file sizes
    log_size = log_file.stat().st_size if log_file.exists() else 0
    indexed_size = indexed_file.stat().st_size if indexed_file.exists() else 0
    print(f"File sizes:")
    print(f"  Log append: {log_size / 1024 / 1024:.2f} MB")
    print(f"  Indexed:    {indexed_size / 1024 / 1024:.2f} MB")
    print()

    # Test lookups - sample of keys
    test_keys = [
        "user:1",           # First key
        "user:50000",       # Middle key
        "user:100000",      # Last key
        "user:99999",       # Second to last
        "user:12345",       # Random middle
    ]

    print("=" * 80)
    print("PERFORMANCE TEST: Single Lookups")
    print("=" * 80)
    print()

    # Test indexed get()
    print("Testing indexed get() (hash index)...")
    indexed_times = []
    for key in test_keys:
        start = time.time()
        result = db_indexed.get(key)
        elapsed = time.time() - start
        indexed_times.append(elapsed)
        print(f"  {key}: {format_time(elapsed)} - {result is not None}")
    
    avg_indexed = sum(indexed_times) / len(indexed_times)
    print(f"  Average: {format_time(avg_indexed)}\n")

    # Test reverse scan get_latest()
    print("Testing reverse scan get_latest() (no index)...")
    scan_times = []
    for key in test_keys:
        start = time.time()
        result = db_log.get_latest(key)
        elapsed = time.time() - start
        scan_times.append(elapsed)
        print(f"  {key}: {format_time(elapsed)} - {result is not None}")
    
    avg_scan = sum(scan_times) / len(scan_times)
    print(f"  Average: {format_time(avg_scan)}\n")

    # Performance comparison
    speedup = avg_scan / avg_indexed if avg_indexed > 0 else float('inf')
    print("=" * 80)
    print("RESULTS SUMMARY")
    print("=" * 80)
    print(f"Indexed get():     {format_time(avg_indexed)} (average)")
    print(f"Reverse scan:      {format_time(avg_scan)} (average)")
    print(f"Speedup:           {speedup:.1f}x faster with index")
    print()

    # Bulk lookup test
    print("=" * 80)
    print("BULK LOOKUP TEST: 1000 random keys")
    print("=" * 80)
    print()

    import random
    random_keys = [f"user:{random.randint(1, num_keys)}" for _ in range(1000)]

    # Test indexed bulk lookups
    print("Testing indexed get() on 1000 random keys...")
    start = time.time()
    indexed_results = []
    for key in random_keys:
        result = db_indexed.get(key)
        indexed_results.append(result)
    indexed_bulk_time = time.time() - start
    print(f"✓ Completed in {format_time(indexed_bulk_time)}")
    print(f"  Average: {format_time(indexed_bulk_time / 1000)} per lookup")
    print(f"  Throughput: {1000 / indexed_bulk_time:.0f} lookups/sec\n")

    # Test reverse scan bulk lookups
    print("Testing reverse scan get_latest() on 1000 random keys...")
    start = time.time()
    scan_results = []
    for key in random_keys:
        result = db_log.get_latest(key)
        scan_results.append(result)
    scan_bulk_time = time.time() - start
    print(f"✓ Completed in {format_time(scan_bulk_time)}")
    print(f"  Average: {format_time(scan_bulk_time / 1000)} per lookup")
    print(f"  Throughput: {1000 / scan_bulk_time:.0f} lookups/sec\n")

    # Final comparison
    bulk_speedup = scan_bulk_time / indexed_bulk_time if indexed_bulk_time > 0 else float('inf')
    print("=" * 80)
    print("FINAL COMPARISON")
    print("=" * 80)
    print(f"Indexed (1000 lookups):    {format_time(indexed_bulk_time)}")
    print(f"Reverse scan (1000):       {format_time(scan_bulk_time)}")
    print(f"Speedup:                   {bulk_speedup:.1f}x faster with index")
    print()
    print("=" * 80)
    print("KEY TAKEAWAY")
    print("=" * 80)
    print("""
Indexes dramatically speed up lookups:
- Hash index: O(1) lookup - direct seek to offset
- Reverse scan: O(n) lookup - must scan from end until found

The larger the file, the bigger the performance difference!
""")


if __name__ == "__main__":
    main()
