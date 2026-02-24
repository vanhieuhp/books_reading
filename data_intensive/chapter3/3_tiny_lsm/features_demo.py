"""
Interactive demonstration of all advanced features.
Run this to see each feature in action with explanations.
"""

import os
import shutil
import time
from lsm_kv_enhanced import LSMKV


def print_section(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def demo_bloom_filter():
    """Demonstrate bloom filter impact."""
    print_section("1. BLOOM FILTER DEMONSTRATION")
    
    print("\n📊 Understanding Bloom Filter Performance")
    print("\n⚠️  Important: Bloom filters help when you have MANY SSTables!")
    print("   With few SSTables, loading overhead can outweigh benefits.")
    
    # Clean up
    for dir_path in ["demo_no_bloom", "demo_with_bloom"]:
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)
    
    print("\n" + "-" * 70)
    print("SCENARIO 1: Small Dataset (Few SSTables)")
    print("-" * 70)
    print("\n   This shows why bloom filter can be slower with few SSTables...")
    
    # Create databases
    db_no_bloom = LSMKV(
        dir_path="demo_no_bloom",
        flush_threshold=100,  # Creates ~10 SSTables
        enable_bloom_filter=False
    )
    
    db_with_bloom = LSMKV(
        dir_path="demo_with_bloom",
        flush_threshold=100,  # Creates ~10 SSTables
        enable_bloom_filter=True,
        bloom_capacity=100
    )
    
    print("\n✍️  Writing 1000 keys to both databases...")
    keys = [f"user:{i}" for i in range(1000)]
    for key in keys:
        db_no_bloom.put(key, {"id": key})
        db_with_bloom.put(key, {"id": key})
    
    print(f"   ✓ Created {len(db_no_bloom.sst_ids)} SSTables")
    
    # Test reads - mostly non-existent keys
    print("\n🔍 Testing reads (90% non-existing keys - high miss rate):")
    test_keys = keys[:100] + [f"nonexistent:{i}" for i in range(900)]
    
    # Without bloom filter
    start = time.time()
    for key in test_keys:
        db_no_bloom.get(key)
    time_no_bloom = time.time() - start
    
    # With bloom filter
    start = time.time()
    for key in test_keys:
        db_with_bloom.get(key)
    time_with_bloom = time.time() - start
    
    print(f"\n   Without bloom filter: {time_no_bloom*1000:.2f} ms")
    print(f"   With bloom filter:    {time_with_bloom*1000:.2f} ms")
    improvement = (1 - time_with_bloom/time_no_bloom) * 100
    print(f"   Improvement:           {improvement:+.1f}%")
    
    if improvement < 0:
        print("\n   ⚠️  Bloom filter is slower! Why?")
        print("      - Loading bloom filters from disk has overhead")
        print("      - With only ~10 SSTables, overhead > benefit")
        print("      - Each SSTable load reads index + bloom filter file")
    
    print("\n" + "-" * 70)
    print("SCENARIO 2: Large Dataset (Many SSTables)")
    print("-" * 70)
    print("\n   This shows when bloom filter actually helps...")
    
    # Clean up and create new databases
    shutil.rmtree("demo_no_bloom")
    shutil.rmtree("demo_with_bloom")
    
    db_no_bloom = LSMKV(
        dir_path="demo_no_bloom",
        flush_threshold=50,  # Creates ~40 SSTables (more SSTables!)
        enable_bloom_filter=False
    )
    
    db_with_bloom = LSMKV(
        dir_path="demo_with_bloom",
        flush_threshold=50,  # Creates ~40 SSTables
        enable_bloom_filter=True,
        bloom_capacity=50
    )
    
    print("\n✍️  Writing 2000 keys to both databases...")
    keys = [f"user:{i}" for i in range(2000)]
    for key in keys:
        db_no_bloom.put(key, {"id": key})
        db_with_bloom.put(key, {"id": key})
    
    print(f"   ✓ Created {len(db_no_bloom.sst_ids)} SSTables")
    print("   (More SSTables = more opportunities for bloom filter to help)")
    
    # Test reads - mostly non-existent keys
    print("\n🔍 Testing reads (95% non-existing keys - very high miss rate):")
    test_keys = keys[:100] + [f"nonexistent:{i}" for i in range(1900)]
    
    # Without bloom filter
    start = time.time()
    for key in test_keys:
        db_no_bloom.get(key)
    time_no_bloom = time.time() - start
    
    # With bloom filter
    start = time.time()
    for key in test_keys:
        db_with_bloom.get(key)
    time_with_bloom = time.time() - start
    
    print(f"\n   Without bloom filter: {time_no_bloom*1000:.2f} ms")
    print(f"   With bloom filter:    {time_with_bloom*1000:.2f} ms")
    improvement = (1 - time_with_bloom/time_no_bloom) * 100
    print(f"   Improvement:           {improvement:+.1f}%")
    
    if improvement > 0:
        print("\n   ✅ Bloom filter is faster! Why?")
        print("      - More SSTables = more skips possible")
        print("      - High miss rate = bloom filter skips most SSTables")
        print("      - Benefit (skipping SSTables) > Overhead (loading filters)")
    else:
        print("\n   ⚠️  Still slower - this is because we're loading from disk each time")
        print("      In production, SSTables are cached in memory!")
    
    print("\n" + "-" * 70)
    print("KEY INSIGHTS")
    print("-" * 70)
    print("\n💡 Bloom filters help when:")
    print("   1. Many SSTables (50+) - more opportunities to skip")
    print("   2. High miss rate - most keys don't exist")
    print("   3. Cached SSTables - bloom filter in memory (no disk I/O)")
    print("   4. Large SSTables - skipping saves more time")
    print("\n💡 Bloom filters hurt when:")
    print("   1. Few SSTables (<10) - overhead > benefit")
    print("   2. Low miss rate - most keys exist, can't skip much")
    print("   3. Loading from disk each time - I/O overhead")
    print("   4. Small SSTables - skipping doesn't save much time")
    
    print("\n📚 This is why production systems (RocksDB, LevelDB) use bloom filters:")
    print("   - Thousands of SSTables across many levels")
    print("   - Most queries don't find keys (high miss rate)")
    print("   - SSTables cached in memory")
    print("   - Large SSTables (MBs to GBs)")
    
    # Cleanup
    shutil.rmtree("demo_no_bloom")
    shutil.rmtree("demo_with_bloom")


def demo_range_queries():
    """Demonstrate range queries."""
    print_section("2. RANGE QUERY DEMONSTRATION")
    
    print("\n📊 Creating database and writing keys...")
    
    if os.path.exists("demo_range"):
        shutil.rmtree("demo_range")
    
    db = LSMKV(dir_path="demo_range", flush_threshold=50)
    
    # Write keys in a pattern
    print("\n✍️  Writing keys: user:1 to user:100, item:1 to item:50")
    for i in range(1, 101):
        db.put(f"user:{i}", {"name": f"User {i}", "id": i})
    for i in range(1, 51):
        db.put(f"item:{i}", {"name": f"Item {i}", "id": i})
    
    print("   ✓ Keys written and flushed")
    
    # Range query: users only
    print("\n🔍 Range Query 1: All users from user:10 to user:30")
    print("   Results:")
    count = 0
    for key, value in db.scan("user:10", "user:30"):
        print(f"     {key}: {value['name']}")
        count += 1
    print(f"   ✓ Found {count} keys")
    
    # Range query: open-ended
    print("\n🔍 Range Query 2: All keys from 'item:' to end")
    print("   Results:")
    count = 0
    for key, value in db.scan("item:", None):
        if count < 5:  # Show first 5
            print(f"     {key}: {value['name']}")
        count += 1
    if count > 5:
        print(f"     ... and {count - 5} more")
    print(f"   ✓ Found {count} keys")
    
    # Compare with multiple gets
    print("\n⚡ Performance Comparison:")
    print("   Range query vs Multiple gets:")
    
    # Range query
    start = time.time()
    list(db.scan("user:1", "user:50"))
    range_time = time.time() - start
    
    # Multiple gets
    start = time.time()
    for i in range(1, 51):
        db.get(f"user:{i}")
    gets_time = time.time() - start
    
    print(f"   Range query:  {range_time*1000:.2f} ms")
    print(f"   Multiple gets: {gets_time*1000:.2f} ms")
    print(f"   Speedup:       {gets_time/range_time:.1f}x faster")
    
    print("\n💡 Key Insight: Range queries are much more efficient than multiple gets!")
    
    # Cleanup
    shutil.rmtree("demo_range")


def demo_leveled_compaction():
    """Demonstrate leveled compaction."""
    print_section("3. LEVELED COMPACTION DEMONSTRATION")
    
    print("\n📊 Creating database with leveled compaction...")
    
    if os.path.exists("demo_leveled"):
        shutil.rmtree("demo_leveled")
    
    db = LSMKV(
        dir_path="demo_leveled",
        flush_threshold=50,  # Small threshold to trigger flushes quickly
        use_leveled_compaction=True,
        max_sstables_per_level=3  # Compact when 3+ SSTables in level
    )
    
    print("\n✍️  Writing keys in batches to trigger flushes and compactions...")
    print("   (This will create multiple SSTables and trigger compactions)")
    
    for batch in range(5):
        print(f"\n   Batch {batch + 1}: Writing 100 keys...")
        for i in range(100):
            db.put(f"key:{batch*100 + i}", {"batch": batch, "id": i})
        
        # Show level structure
        level_sizes = [len(level) for level in db.levels]
        print(f"   Level structure: {level_sizes} (Level 0 has {level_sizes[0] if level_sizes else 0} SSTables)")
        
        # Check if compaction happened
        if len(db.levels) > 1:
            print(f"   ✓ Level 1 has {len(db.levels[1])} SSTables (from compaction)")
    
    print("\n📈 Final Level Structure:")
    for level_num, level in enumerate(db.levels):
        print(f"   Level {level_num}: {len(level)} SSTables")
        if len(level) > 0:
            # Show first SSTable ID
            print(f"      First SSTable: {level[0][:30]}...")
    
    print("\n💡 Key Insight: SSTables are organized into levels, with automatic compaction!")
    print("   - Level 0: Newest SSTables (from memtable flushes)")
    print("   - Level 1+: Older SSTables (from compactions)")
    print("   - Compaction happens automatically when levels get too large")
    
    # Cleanup
    shutil.rmtree("demo_leveled")


def demo_metrics():
    """Demonstrate metrics tracking."""
    print_section("4. METRICS TRACKING DEMONSTRATION")
    
    print("\n📊 Creating database and running workload...")
    
    if os.path.exists("demo_metrics"):
        shutil.rmtree("demo_metrics")
    
    db = LSMKV(dir_path="demo_metrics", flush_threshold=100)
    
    print("\n✍️  Running workload:")
    print("   - Writing 500 keys")
    print("   - Reading 300 keys")
    print("   - Deleting 50 keys")
    
    # Write
    keys = [f"key:{i}" for i in range(500)]
    for key in keys:
        db.put(key, {"value": f"data for {key}"})
    
    # Read
    import random
    read_keys = random.sample(keys, 300) + [f"nonexistent:{i}" for i in range(100)]
    for key in read_keys:
        db.get(key)
    
    # Delete
    delete_keys = random.sample(keys, 50)
    for key in delete_keys:
        db.delete(key)
    
    print("   ✓ Workload complete")
    
    # Show metrics
    print("\n📈 Metrics Summary:")
    db.print_stats()
    
    # Detailed metrics
    metrics = db.get_metrics()
    print("\n📊 Detailed Metrics:")
    print(f"   Write count:        {metrics.write_count:,}")
    print(f"   Read count:         {metrics.read_count:,}")
    print(f"   Delete count:       {metrics.delete_count:,}")
    print(f"   Flush count:        {metrics.flush_count:,}")
    print(f"   Compaction count:   {metrics.compaction_count:,}")
    print(f"\n   Write amplification: {metrics.get_write_amplification():.2f}x")
    print(f"   Read amplification:  {metrics.get_read_amplification():.2f}x")
    print(f"\n   Avg write latency:   {metrics.get_avg_write_latency():.2f} ms")
    print(f"   Avg read latency:    {metrics.get_avg_read_latency():.2f} ms")
    print(f"   P95 write latency:    {metrics.get_p95_write_latency():.2f} ms")
    print(f"   P95 read latency:     {metrics.get_p95_read_latency():.2f} ms")
    
    print("\n💡 Key Insight: Metrics help you understand:")
    print("   - How many operations occurred")
    print("   - Performance characteristics (latencies)")
    print("   - Resource usage (amplification)")
    print("   - Where optimizations might help")
    
    # Cleanup
    shutil.rmtree("demo_metrics")


def demo_combined_features():
    """Demonstrate all features working together."""
    print_section("5. COMBINED FEATURES DEMONSTRATION")
    
    print("\n📊 Creating fully optimized database...")
    print("   - Bloom filter: Enabled")
    print("   - Leveled compaction: Enabled")
    print("   - Metrics: Enabled")
    
    if os.path.exists("demo_combined"):
        shutil.rmtree("demo_combined")
    
    db = LSMKV(
        dir_path="demo_combined",
        flush_threshold=100,
        enable_bloom_filter=True,
        use_leveled_compaction=True,
        max_sstables_per_level=3
    )
    
    print("\n✍️  Writing 1000 keys...")
    for i in range(1000):
        db.put(f"user:{i}", {"name": f"User {i}", "id": i})
    print("   ✓ Keys written")
    
    print("\n🔍 Testing reads (with bloom filter optimization)...")
    import random
    test_keys = [f"user:{i}" for i in random.sample(range(1000), 200)]
    start = time.time()
    for key in test_keys:
        db.get(key)
    read_time = time.time() - start
    print(f"   ✓ Read 200 keys in {read_time*1000:.2f} ms")
    
    print("\n🔍 Testing range query...")
    start = time.time()
    results = list(db.scan("user:100", "user:200"))
    range_time = time.time() - start
    print(f"   ✓ Scanned 101 keys in {range_time*1000:.2f} ms")
    print(f"   Found {len(results)} keys")
    
    print("\n📈 Performance Metrics:")
    metrics = db.get_metrics()
    print(f"   Total writes:        {metrics.write_count:,}")
    print(f"   Total reads:         {metrics.read_count:,}")
    print(f"   Write amplification: {metrics.get_write_amplification():.2f}x")
    print(f"   Read amplification:  {metrics.get_read_amplification():.2f}x")
    print(f"   Avg read latency:    {metrics.get_avg_read_latency():.2f} ms")
    
    print("\n💡 Key Insight: All features work together to optimize performance!")
    print("   - Bloom filter: Reduces unnecessary SSTable reads")
    print("   - Leveled compaction: Organizes data efficiently")
    print("   - Range queries: Efficient bulk operations")
    print("   - Metrics: Track and optimize performance")
    
    # Cleanup
    shutil.rmtree("demo_combined")


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 70)
    print("  LSM TREE ADVANCED FEATURES - INTERACTIVE DEMONSTRATION")
    print("=" * 70)
    print("\nThis demo will show you:")
    print("  1. Bloom Filter - How it speeds up reads")
    print("  2. Range Queries - Efficient bulk operations")
    print("  3. Leveled Compaction - Automatic data organization")
    print("  4. Metrics Tracking - Performance monitoring")
    print("  5. Combined Features - All features working together")
    
    input("\nPress Enter to start...")
    
    try:
        demo_bloom_filter()
        input("\n\nPress Enter to continue to range queries demo...")
        
        demo_range_queries()
        input("\n\nPress Enter to continue to leveled compaction demo...")
        
        demo_leveled_compaction()
        input("\n\nPress Enter to continue to metrics demo...")
        
        demo_metrics()
        input("\n\nPress Enter to continue to combined features demo...")
        
        demo_combined_features()
        
        print("\n" + "=" * 70)
        print("  DEMONSTRATION COMPLETE!")
        print("=" * 70)
        print("\nNext steps:")
        print("  1. Read FEATURES_TUTORIAL.md for detailed explanations")
        print("  2. Experiment with the code")
        print("  3. Run benchmarks: python benchmark.py --compare")
        print("  4. Try the practice exercises in the tutorial")
        
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
