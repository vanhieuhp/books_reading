"""
Benchmark script for LSM Tree implementation.
Compares performance with different configurations.
"""

import time
import random
import string
import os
import shutil
from typing import Dict, List
from lsm_kv_enhanced import LSMKV


def generate_random_key(prefix: str = "key", length: int = 10) -> str:
    """Generate a random key."""
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    return f"{prefix}:{suffix}"


def generate_random_value() -> Dict:
    """Generate a random value."""
    return {
        "data": ''.join(random.choices(string.ascii_letters + string.digits, k=100)),
        "number": random.randint(1, 1000000),
        "float": random.random()
    }


def benchmark_writes(db: LSMKV, num_writes: int, key_prefix: str = "key") -> Dict:
    """Benchmark write performance."""
    print(f"  Writing {num_writes:,} keys...")
    
    keys = [generate_random_key(key_prefix) for _ in range(num_writes)]
    values = [generate_random_value() for _ in range(num_writes)]
    
    start_time = time.time()
    for key, value in zip(keys, values):
        db.put(key, value, durable=True)
    end_time = time.time()
    
    elapsed = end_time - start_time
    throughput = num_writes / elapsed if elapsed > 0 else 0
    
    return {
        "num_writes": num_writes,
        "elapsed_seconds": elapsed,
        "throughput_writes_per_sec": throughput,
        "avg_latency_ms": (elapsed / num_writes) * 1000 if num_writes > 0 else 0
    }


def benchmark_reads(db: LSMKV, keys: List[str], num_reads: int) -> Dict:
    """Benchmark read performance."""
    print(f"  Reading {num_reads:,} keys...")
    
    # Mix of existing and non-existing keys
    read_keys = []
    for _ in range(num_reads):
        if random.random() < 0.8:  # 80% existing keys
            read_keys.append(random.choice(keys))
        else:
            read_keys.append(generate_random_key("nonexistent"))
    
    start_time = time.time()
    found = 0
    for key in read_keys:
        value = db.get(key)
        if value is not None:
            found += 1
    end_time = time.time()
    
    elapsed = end_time - start_time
    throughput = num_reads / elapsed if elapsed > 0 else 0
    
    return {
        "num_reads": num_reads,
        "found": found,
        "not_found": num_reads - found,
        "elapsed_seconds": elapsed,
        "throughput_reads_per_sec": throughput,
        "avg_latency_ms": (elapsed / num_reads) * 1000 if num_reads > 0 else 0
    }


def benchmark_range_queries(db: LSMKV, num_queries: int = 100) -> Dict:
    """Benchmark range query performance."""
    print(f"  Running {num_queries} range queries...")
    
    total_time = 0
    total_keys_returned = 0
    
    for _ in range(num_queries):
        # Random start and end keys
        start = generate_random_key("key", 5)
        end = generate_random_key("key", 5)
        if start > end:
            start, end = end, start
        
        start_time = time.time()
        count = 0
        for key, value in db.scan(start, end):
            count += 1
        elapsed = time.time() - start_time
        
        total_time += elapsed
        total_keys_returned += count
    
    avg_time = total_time / num_queries if num_queries > 0 else 0
    avg_keys = total_keys_returned / num_queries if num_queries > 0 else 0
    
    return {
        "num_queries": num_queries,
        "total_time_seconds": total_time,
        "avg_time_per_query_ms": avg_time * 1000,
        "avg_keys_per_query": avg_keys
    }


def run_benchmark(config: Dict, num_writes: int = 10000, num_reads: int = 5000) -> Dict:
    """Run a complete benchmark with given configuration."""
    print(f"\n{'='*60}")
    print(f"Benchmark: {config['name']}")
    print(f"{'='*60}")
    print(f"Configuration:")
    for key, value in config.items():
        if key != 'name' and key != 'dir_path':
            print(f"  {key}: {value}")
    
    # Clean up old data
    dir_path = config.get('dir_path', 'benchmark_data')
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)
    
    # Create database
    db = LSMKV(**config)
    
    # Benchmark writes
    print("\n1. Write Benchmark")
    write_results = benchmark_writes(db, num_writes)
    print(f"   Throughput: {write_results['throughput_writes_per_sec']:,.0f} writes/sec")
    print(f"   Avg latency: {write_results['avg_latency_ms']:.2f} ms")
    
    # Get written keys for read benchmark
    # In real scenario, we'd track these, but for simplicity we'll generate similar keys
    written_keys = [generate_random_key("key") for _ in range(num_writes)]
    
    # Benchmark reads
    print("\n2. Read Benchmark")
    read_results = benchmark_reads(db, written_keys, num_reads)
    print(f"   Throughput: {read_results['throughput_reads_per_sec']:,.0f} reads/sec")
    print(f"   Avg latency: {read_results['avg_latency_ms']:.2f} ms")
    print(f"   Found: {read_results['found']}, Not found: {read_results['not_found']}")
    
    # Benchmark range queries
    print("\n3. Range Query Benchmark")
    range_results = benchmark_range_queries(db, num_queries=100)
    print(f"   Avg time per query: {range_results['avg_time_per_query_ms']:.2f} ms")
    print(f"   Avg keys per query: {range_results['avg_keys_per_query']:.1f}")
    
    # Get metrics
    metrics = db.get_metrics()
    stats = metrics.get_stats()
    
    print("\n4. Metrics")
    print(f"   Write amplification: {stats['amplification']['write']:.2f}x")
    print(f"   Read amplification: {stats['amplification']['read']:.2f}x")
    print(f"   Total flushes: {stats['operations']['flushes']}")
    print(f"   Total compactions: {stats['operations']['compactions']}")
    
    # Cleanup
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)
    
    return {
        "config": config,
        "write_results": write_results,
        "read_results": read_results,
        "range_results": range_results,
        "metrics": stats
    }


def compare_configurations():
    """Compare different configurations."""
    configs = [
        {
            "name": "Baseline (no bloom filter, size-tiered compaction)",
            "dir_path": "benchmark_baseline",
            "flush_threshold": 1000,
            "sparse_step": 50,
            "enable_bloom_filter": False,
            "use_leveled_compaction": False,
        },
        {
            "name": "With Bloom Filter",
            "dir_path": "benchmark_bloom",
            "flush_threshold": 1000,
            "sparse_step": 50,
            "enable_bloom_filter": True,
            "use_leveled_compaction": False,
        },
        {
            "name": "With Leveled Compaction",
            "dir_path": "benchmark_leveled",
            "flush_threshold": 1000,
            "sparse_step": 50,
            "enable_bloom_filter": False,
            "use_leveled_compaction": True,
            "max_sstables_per_level": 4,
        },
        {
            "name": "Full Optimized (Bloom + Leveled)",
            "dir_path": "benchmark_optimized",
            "flush_threshold": 1000,
            "sparse_step": 50,
            "enable_bloom_filter": True,
            "use_leveled_compaction": True,
            "max_sstables_per_level": 4,
        },
    ]
    
    results = []
    for config in configs:
        try:
            result = run_benchmark(config, num_writes=5000, num_reads=2000)
            results.append(result)
        except Exception as e:
            print(f"Error in benchmark {config['name']}: {e}")
            import traceback
            traceback.print_exc()
    
    # Print comparison
    print("\n" + "="*60)
    print("COMPARISON SUMMARY")
    print("="*60)
    
    print(f"\n{'Configuration':<40} {'Write (ops/s)':<15} {'Read (ops/s)':<15} {'Read Latency (ms)':<18}")
    print("-" * 90)
    
    for result in results:
        config_name = result['config']['name']
        write_throughput = result['write_results']['throughput_writes_per_sec']
        read_throughput = result['read_results']['throughput_reads_per_sec']
        read_latency = result['read_results']['avg_latency_ms']
        
        print(f"{config_name:<40} {write_throughput:>12,.0f}   {read_throughput:>12,.0f}   {read_latency:>15.2f}")
    
    print("\n" + "="*60)
    print("Key Insights:")
    print("="*60)
    
    if len(results) >= 2:
        baseline = results[0]
        optimized = results[-1] if len(results) > 1 else None
        
        if optimized:
            write_improvement = ((optimized['write_results']['throughput_writes_per_sec'] / 
                                baseline['write_results']['throughput_writes_per_sec']) - 1) * 100
            read_improvement = ((optimized['read_results']['throughput_reads_per_sec'] / 
                               baseline['read_results']['throughput_reads_per_sec']) - 1) * 100
            
            print(f"Write throughput improvement: {write_improvement:+.1f}%")
            print(f"Read throughput improvement: {read_improvement:+.1f}%")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Benchmark LSM Tree implementation")
    parser.add_argument("--writes", type=int, default=10000, help="Number of writes")
    parser.add_argument("--reads", type=int, default=5000, help="Number of reads")
    parser.add_argument("--compare", action="store_true", help="Compare different configurations")
    
    args = parser.parse_args()
    
    if args.compare:
        compare_configurations()
    else:
        # Single benchmark
        config = {
            "name": "Default Configuration",
            "dir_path": "benchmark_data",
            "flush_threshold": 1000,
            "sparse_step": 50,
            "enable_bloom_filter": True,
            "use_leveled_compaction": True,
        }
        run_benchmark(config, num_writes=args.writes, num_reads=args.reads)
