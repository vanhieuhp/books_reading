#!/usr/bin/env python3
"""
Visual demonstration of how hash index works.
Shows step-by-step what happens when you write and read data.
"""

import sys
import importlib.util
from pathlib import Path

# Import the indexed database
base_dir = Path(__file__).parent
indexed_path = base_dir / "2_hash_index" / "logdb_indexed.py"
indexed_spec = importlib.util.spec_from_file_location("logdb_indexed", indexed_path)
indexed_module = importlib.util.module_from_spec(indexed_spec)
indexed_module.__name__ = "logdb_indexed"
indexed_module.__file__ = str(indexed_path)
sys.modules["logdb_indexed"] = indexed_module
indexed_spec.loader.exec_module(indexed_module)
LogDBIndexed = indexed_module.LogDBIndexed

import os
import json


def show_file_content(filepath: str):
    """Show file content with byte offsets."""
    if not os.path.exists(filepath):
        print("  (file doesn't exist yet)")
        return
    
    print("  File content:")
    with open(filepath, "rb") as f:
        offset = 0
        while True:
            line = f.readline()
            if not line:
                break
            line_str = line.decode('utf-8', errors='replace').rstrip()
            print(f"    Offset {offset:6d}: {line_str}")
            offset = f.tell()


def show_index(index: dict):
    """Show index contents."""
    print("  Index (in memory):")
    if not index:
        print("    (empty)")
        return
    for key, offset in sorted(index.items()):
        print(f"    '{key}' → offset {offset}")


def main():
    print("=" * 80)
    print("HASH INDEX DEMONSTRATION")
    print("=" * 80)
    print()
    
    # Clean up
    demo_file = "demo_indexed.log"
    if os.path.exists(demo_file):
        os.remove(demo_file)
    
    # Create database
    db = LogDBIndexed(demo_file)
    print("Created LogDBIndexed instance")
    print(f"  Initial index: {db.index}")
    print()
    
    # Step 1: Write first record
    print("=" * 80)
    print("STEP 1: Write user:1")
    print("=" * 80)
    db.put("user:1", {"name": "Alice", "age": 24})
    print("After put('user:1', {...}):")
    show_index(db.index)
    show_file_content(demo_file)
    print()
    
    # Step 2: Write second record
    print("=" * 80)
    print("STEP 2: Write user:2")
    print("=" * 80)
    db.put("user:2", {"name": "Bob", "age": 21})
    print("After put('user:2', {...}):")
    show_index(db.index)
    show_file_content(demo_file)
    print()
    
    # Step 3: Overwrite user:1
    print("=" * 80)
    print("STEP 3: Overwrite user:1 (update age to 25)")
    print("=" * 80)
    db.put("user:1", {"name": "Alice", "age": 25})
    print("After put('user:1', {...}) again:")
    show_index(db.index)
    print("  ⚠️  Notice: user:1 now points to NEW offset (latest write wins!)")
    show_file_content(demo_file)
    print("  ⚠️  Notice: Old user:1 record still in file, but index points to latest!")
    print()
    
    # Step 4: Read user:1
    print("=" * 80)
    print("STEP 4: Read user:1 using index")
    print("=" * 80)
    print("Calling db.get('user:1'):")
    print()
    
    # Show what happens internally
    key = "user:1"
    offset = db.index.get(key)
    print(f"  1. Look up '{key}' in index:")
    print(f"     index.get('{key}') → {offset}")
    print()
    
    print(f"  2. Jump to offset {offset} in file:")
    print(f"     f.seek({offset})")
    print()
    
    with open(demo_file, "rb") as f:
        f.seek(offset)
        line = f.readline()
        line_str = line.decode('utf-8', errors='replace').rstrip()
        print(f"  3. Read one line:")
        print(f"     f.readline() → '{line_str}'")
        print()
        
        parts = line.rstrip(b'\n').split(b'\t', 2)
        if len(parts) == 3:
            _, key_b, value_b = parts
            value = json.loads(value_b.decode('utf-8'))
            print(f"  4. Parse and return:")
            print(f"     value = {value}")
            print()
    
    result = db.get("user:1")
    print(f"  ✅ Result: {result}")
    print(f"  ✅ Got latest value (age: 25), not old one (age: 24)!")
    print()
    
    # Step 5: Show the difference
    print("=" * 80)
    print("STEP 5: Compare with reverse scan (no index)")
    print("=" * 80)
    print("Without index, to find user:1, you would:")
    print("  1. Start at END of file")
    print("  2. Read backwards line by line")
    print("  3. Check each line: 'Is this user:1?'")
    print("  4. Stop when found (might read many lines!)")
    print()
    print("With index:")
    print("  1. Look up in index → get offset")
    print("  2. Jump directly to offset")
    print("  3. Read ONE line")
    print("  ✅ Much faster!")
    print()
    
    # Step 6: Show file size and index size
    print("=" * 80)
    print("STEP 6: Memory vs Disk")
    print("=" * 80)
    file_size = os.path.getsize(demo_file) if os.path.exists(demo_file) else 0
    index_size = len(db.index)
    
    print(f"  File size (on disk): {file_size} bytes")
    print(f"  Index size (in memory): {index_size} entries")
    print()
    print("  Trade-off:")
    print("    - File: Persistent, but slow to search")
    print("    - Index: Fast to search, but uses RAM")
    print()
    
    # Step 7: Show what happens with many keys
    print("=" * 80)
    print("STEP 7: Performance with many keys")
    print("=" * 80)
    print("Adding 10 more keys...")
    for i in range(3, 13):
        db.put(f"user:{i}", {"name": f"User{i}", "age": 20 + i})
    
    print(f"  Total keys: {len(db.index)}")
    print(f"  File size: {os.path.getsize(demo_file)} bytes")
    print()
    print("To find user:10:")
    print("  Without index: Read ~10 lines (scan from end)")
    print("  With index: Read 1 line (direct jump)")
    print()
    print("To find user:1 in file with 1,000,000 keys:")
    print("  Without index: Read ~1,000,000 lines (worst case)")
    print("  With index: Read 1 line (always!)")
    print()
    
    # Cleanup
    if os.path.exists(demo_file):
        os.remove(demo_file)
    
    print("=" * 80)
    print("KEY TAKEAWAY")
    print("=" * 80)
    print("""
Hash index = Dictionary that maps keys to file positions

Write: Append to file + update index
Read:  Look up key → jump to offset → read one line

Result: O(1) lookups instead of O(n) scans!

The index is like a GPS - it tells you exactly where to find each key!
""")


if __name__ == "__main__":
    main()
