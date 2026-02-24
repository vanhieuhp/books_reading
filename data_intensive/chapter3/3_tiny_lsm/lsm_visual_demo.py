"""
Interactive visualization of LSM Tree operations.
Run this to see step-by-step what happens during writes, reads, and compaction.
"""

from lsm_kv import LSMKV
import os
import json
from pathlib import Path

def print_section(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def show_memtable(db):
    """Display current memtable state"""
    print("\n📝 MEMTABLE:")
    if not db.mem:
        print("  (empty)")
    else:
        print(f"  Keys: {len(db.mem)}")
        for key in sorted(db.mem.keys())[:10]:  # Show first 10
            entry = db.mem[key]
            status = "🗑️ DELETED" if entry["t"] == 1 else "✓"
            value = entry["v"]
            print(f"    {status} {key} = {value}")
        if len(db.mem) > 10:
            print(f"    ... and {len(db.mem) - 10} more")

def show_wal(db):
    """Display WAL contents"""
    print("\n📋 WAL (Write-Ahead Log):")
    if not os.path.exists(db.wal_path):
        print("  (does not exist)")
        return
    
    with open(db.wal_path, "rb") as f:
        lines = f.readlines()
    
    if not lines:
        print("  (empty)")
    else:
        print(f"  Entries: {len(lines)}")
        for i, line in enumerate(lines[-5:], 1):  # Show last 5
            rec = json.loads(line)
            op = rec.get("op", "?")
            key = rec.get("k", "?")
            if op == "PUT":
                print(f"    {i}. PUT {key}")
            elif op == "DEL":
                print(f"    {i}. DEL {key}")
        if len(lines) > 5:
            print(f"    ... and {len(lines) - 5} more")

def show_sstables(db):
    """Display SSTable information"""
    print("\n💾 SSTABLES (newest → oldest):")
    if not db.sst_ids:
        print("  (none)")
        return
    
    print(f"  Count: {len(db.sst_ids)}")
    for i, sst_id in enumerate(db.sst_ids, 1):
        dat_path, idx_path = db._sst_paths(sst_id)
        
        # Count records in SSTable
        record_count = 0
        if os.path.exists(dat_path):
            with open(dat_path, "rb") as f:
                record_count = sum(1 for _ in f)
        
        # Load sparse index
        index_entries = 0
        if os.path.exists(idx_path):
            with open(idx_path, "r") as f:
                idx_data = json.load(f)
                index_entries = len(idx_data)
        
        print(f"    {i}. {sst_id[:20]}...")
        print(f"       Records: {record_count}, Index entries: {index_entries}")

def show_manifest(db):
    """Display manifest"""
    print("\n📄 MANIFEST:")
    if not os.path.exists(db.manifest_path):
        print("  (does not exist)")
        return
    
    with open(db.manifest_path, "r") as f:
        data = json.load(f)
    
    sst_ids = data.get("sst_ids", [])
    print(f"  SSTable IDs: {len(sst_ids)}")
    for i, sst_id in enumerate(sst_ids[:5], 1):
        print(f"    {i}. {sst_id[:30]}...")
    if len(sst_ids) > 5:
        print(f"    ... and {len(sst_ids) - 5} more")

def demonstrate_write_path():
    """Demonstrate the write path"""
    print_section("WRITE PATH DEMONSTRATION")
    
    # Create fresh database with small threshold
    db_dir = "lsm_demo_data"
    if os.path.exists(db_dir):
        import shutil
        shutil.rmtree(db_dir)
    
    db = LSMKV(dir_path=db_dir, flush_threshold=3, sparse_step=2)
    
    print("\n🔹 Step 1: Write 3 keys (below threshold)")
    db.put("user:1", {"name": "Alice"})
    db.put("user:2", {"name": "Bob"})
    db.put("user:3", {"name": "Charlie"})
    
    show_memtable(db)
    show_wal(db)
    show_sstables(db)
    
    print("\n🔹 Step 2: Write 4th key (triggers flush!)")
    db.put("user:4", {"name": "David"})
    
    show_memtable(db)
    show_wal(db)
    show_sstables(db)
    
    print("\n🔹 Step 3: Overwrite a key")
    db.put("user:2", {"name": "Bob Updated"})
    
    show_memtable(db)
    
    print("\n🔹 Step 4: Delete a key (tombstone)")
    db.delete("user:3")
    
    show_memtable(db)
    
    print("\n🔹 Step 5: Write more to trigger another flush")
    db.put("user:5", {"name": "Eve"})
    db.put("user:6", {"name": "Frank"})
    db.put("user:7", {"name": "Grace"})
    
    show_memtable(db)
    show_sstables(db)

def demonstrate_read_path():
    """Demonstrate the read path"""
    print_section("READ PATH DEMONSTRATION")
    
    db_dir = "lsm_demo_data"
    if not os.path.exists(db_dir):
        print("Run write path demo first!")
        return
    
    db = LSMKV(dir_path=db_dir, flush_threshold=3, sparse_step=2)
    
    print("\n🔍 Reading keys:")
    
    # Read from memtable
    print("\n1. Read 'user:7' (should be in memtable):")
    result = db.get("user:7")
    print(f"   Result: {result}")
    
    # Read from SSTable
    print("\n2. Read 'user:1' (should be in SSTable):")
    result = db.get("user:1")
    print(f"   Result: {result}")
    
    # Read overwritten key
    print("\n3. Read 'user:2' (was overwritten, newer value should win):")
    result = db.get("user:2")
    print(f"   Result: {result}")
    
    # Read deleted key
    print("\n4. Read 'user:3' (was deleted, should return None):")
    result = db.get("user:3")
    print(f"   Result: {result}")
    
    # Read non-existent key
    print("\n5. Read 'user:999' (doesn't exist):")
    result = db.get("user:999")
    print(f"   Result: {result}")

def demonstrate_compaction():
    """Demonstrate compaction"""
    print_section("COMPACTION DEMONSTRATION")
    
    db_dir = "lsm_demo_data"
    if not os.path.exists(db_dir):
        print("Run write path demo first!")
        return
    
    db = LSMKV(dir_path=db_dir, flush_threshold=3, sparse_step=2)
    
    print("\n📊 Before compaction:")
    show_sstables(db)
    
    # Show what's in each SSTable
    print("\n🔍 Contents of SSTables:")
    for i, sst_id in enumerate(db.sst_ids, 1):
        print(f"\n  SSTable {i} ({sst_id[:20]}...):")
        sst = db._load_sstable(sst_id)
        dat_path = db._sst_paths(sst_id)[0]
        with open(dat_path, "rb") as f:
            for j, line in enumerate(f, 1):
                rec = json.loads(line)
                status = "🗑️" if rec["t"] == 1 else "✓"
                print(f"    {j}. {status} {rec['k']} = {rec.get('v', 'DELETED')}")
    
    print("\n🔄 Compacting two oldest SSTables...")
    db.compact_two_oldest()
    
    print("\n📊 After compaction:")
    show_sstables(db)
    
    print("\n🔍 Contents after compaction:")
    for i, sst_id in enumerate(db.sst_ids, 1):
        print(f"\n  SSTable {i} ({sst_id[:20]}...):")
        sst = db._load_sstable(sst_id)
        dat_path = db._sst_paths(sst_id)[0]
        with open(dat_path, "rb") as f:
            for j, line in enumerate(f, 1):
                rec = json.loads(line)
                status = "🗑️" if rec["t"] == 1 else "✓"
                print(f"    {j}. {status} {rec['k']} = {rec.get('v', 'DELETED')}")

def demonstrate_sparse_index():
    """Demonstrate how sparse index works"""
    print_section("SPARSE INDEX DEMONSTRATION")
    
    db_dir = "lsm_demo_data"
    if not os.path.exists(db_dir):
        print("Run write path demo first!")
        return
    
    db = LSMKV(dir_path=db_dir, flush_threshold=3, sparse_step=2)
    
    if not db.sst_ids:
        print("No SSTables exist. Run write demo first!")
        return
    
    # Get first SSTable
    sst_id = db.sst_ids[0]
    sst = db._load_sstable(sst_id)
    
    print(f"\n📇 SSTable: {sst_id[:30]}...")
    print(f"   Sparse step: {db.sparse_step} (index every {db.sparse_step} keys)")
    
    print(f"\n📑 Sparse Index Entries:")
    for i, (key, offset) in enumerate(sst.sparse_index.entries, 1):
        print(f"   {i}. Key: {key}, Offset: {offset}")
    
    print(f"\n🔍 Lookup example:")
    test_key = "user:2"
    start_offset = sst.sparse_index.find_start_offset(test_key)
    print(f"   Looking for: {test_key}")
    print(f"   Start offset: {start_offset}")
    print(f"   (Will scan from this offset forward)")
    
    # Show what's at that offset
    dat_path = db._sst_paths(sst_id)[0]
    with open(dat_path, "rb") as f:
        f.seek(start_offset)
        print(f"\n   Records starting from offset {start_offset}:")
        for i, line in enumerate(f, 1):
            if i > 5:  # Show first 5
                break
            rec = json.loads(line)
            status = "🗑️" if rec["t"] == 1 else "✓"
            print(f"     {i}. {status} {rec['k']} = {rec.get('v', 'DELETED')}")

def main():
    """Run all demonstrations"""
    print("\n" + "=" * 60)
    print("  LSM TREE VISUALIZATION DEMO")
    print("=" * 60)
    print("\nThis demo will show you:")
    print("  1. Write path (WAL → Memtable → Flush)")
    print("  2. Read path (Memtable → SSTables)")
    print("  3. Compaction (merge SSTables)")
    print("  4. Sparse index (how lookups work)")
    
    input("\nPress Enter to start...")
    
    try:
        demonstrate_write_path()
        input("\n\nPress Enter to continue to read path demo...")
        
        demonstrate_read_path()
        input("\n\nPress Enter to continue to compaction demo...")
        
        demonstrate_compaction()
        input("\n\nPress Enter to continue to sparse index demo...")
        
        demonstrate_sparse_index()
        
        print("\n" + "=" * 60)
        print("  DEMO COMPLETE!")
        print("=" * 60)
        print("\nCheck the 'lsm_demo_data' directory to see the actual files:")
        print("  - wal.log: Write-ahead log")
        print("  - manifest.json: SSTable metadata")
        print("  - sst_*.dat: SSTable data files")
        print("  - sst_*.idx: Sparse index files")
        
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
