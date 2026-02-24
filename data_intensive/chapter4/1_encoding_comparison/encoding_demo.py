"""
Day 1: Encoding Fundamentals - Text vs Binary Comparison

This script demonstrates the differences between text-based (JSON) and 
binary (MessagePack, Pickle) encoding formats.

Key concepts:
- Encoding: Converting objects to bytes
- Decoding: Converting bytes back to objects
- Size comparison: How much space each format uses
- Performance: How fast encoding/decoding is
"""

import json
import pickle
import time
import sys
from typing import Dict, List, Any

# Try to import msgpack, but make it optional for basic demo
try:
    import msgpack
    MSGPACK_AVAILABLE = True
except ImportError:
    MSGPACK_AVAILABLE = False
    print("⚠️  Warning: msgpack not installed. Install with: pip install msgpack")
    print("   Continuing with JSON and Pickle only...\n")


def create_sample_data(num_records: int = 1) -> List[Dict[str, Any]]:
    """
    Create sample data structures to encode.
    Uses realistic data with various types: strings, numbers, booleans, nested objects.
    """
    data = []
    for i in range(num_records):
        record = {
            "id": i,
            "name": f"User_{i}",
            "email": f"user{i}@example.com",
            "age": 20 + (i % 50),
            "active": i % 2 == 0,
            "score": 85.5 + (i % 15),
            "tags": ["premium", "verified", f"tier_{i % 3}"],
            "metadata": {
                "created_at": "2024-01-01T00:00:00Z",
                "last_login": f"2024-01-{(i % 28) + 1:02d}T12:00:00Z",
                "settings": {
                    "notifications": True,
                    "theme": "dark" if i % 2 == 0 else "light",
                    "language": "en"
                }
            },
            "preferences": {
                "newsletter": i % 3 != 0,
                "marketing": False,
                "analytics": True
            }
        }
        data.append(record)
    return data


def encode_json(data: List[Dict]) -> bytes:
    """Encode data to JSON (text-based format)."""
    return json.dumps(data).encode('utf-8')


def decode_json(data: bytes) -> List[Dict]:
    """Decode JSON data back to Python objects."""
    return json.loads(data.decode('utf-8'))


def encode_msgpack(data: List[Dict]) -> bytes:
    """Encode data to MessagePack (binary format, JSON-like)."""
    return msgpack.packb(data, use_bin_type=True)


def decode_msgpack(data: bytes) -> List[Dict]:
    """Decode MessagePack data back to Python objects."""
    return msgpack.unpackb(data, raw=False)


def encode_pickle(data: List[Dict]) -> bytes:
    """Encode data to Pickle (Python-specific binary format)."""
    return pickle.dumps(data)


def decode_pickle(data: bytes) -> List[Dict]:
    """Decode Pickle data back to Python objects."""
    return pickle.loads(data)


def format_size(size_bytes: int) -> str:
    """Format byte size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def format_time(seconds: float) -> str:
    """Format time in appropriate units."""
    if seconds < 0.001:
        return f"{seconds * 1_000_000:.2f} μs"
    elif seconds < 1:
        return f"{seconds * 1000:.2f} ms"
    else:
        return f"{seconds:.2f} s"


def benchmark_encoding(data: List[Dict], num_iterations: int = 100) -> Dict[str, Any]:
    """
    Benchmark encoding and decoding for different formats.
    
    Returns a dictionary with:
    - size: Size of encoded data in bytes
    - encode_time: Average encoding time
    - decode_time: Average decoding time
    - total_time: Total time for encode + decode
    """
    results = {}
    
    # Test JSON
    print("  Testing JSON...", end="", flush=True)
    start = time.time()
    json_data = encode_json(data)
    json_encode_time = time.time() - start
    
    start = time.time()
    for _ in range(num_iterations):
        decode_json(json_data)
    json_decode_time = (time.time() - start) / num_iterations
    
    results['JSON'] = {
        'size': len(json_data),
        'encode_time': json_encode_time,
        'decode_time': json_decode_time,
        'total_time': json_encode_time + json_decode_time,
        'data': json_data
    }
    print(" ✓")
    
    # Test MessagePack (if available)
    if MSGPACK_AVAILABLE:
        print("  Testing MessagePack...", end="", flush=True)
        start = time.time()
        msgpack_data = encode_msgpack(data)
        msgpack_encode_time = time.time() - start
        
        start = time.time()
        for _ in range(num_iterations):
            decode_msgpack(msgpack_data)
        msgpack_decode_time = (time.time() - start) / num_iterations
        
        results['MessagePack'] = {
            'size': len(msgpack_data),
            'encode_time': msgpack_encode_time,
            'decode_time': msgpack_decode_time,
            'total_time': msgpack_encode_time + msgpack_decode_time,
            'data': msgpack_data
        }
        print(" ✓")
    
    # Test Pickle
    print("  Testing Pickle...", end="", flush=True)
    start = time.time()
    pickle_data = encode_pickle(data)
    pickle_encode_time = time.time() - start
    
    start = time.time()
    for _ in range(num_iterations):
        decode_pickle(pickle_data)
    pickle_decode_time = (time.time() - start) / num_iterations
    
    results['Pickle'] = {
        'size': len(pickle_data),
        'encode_time': pickle_encode_time,
        'decode_time': pickle_decode_time,
        'total_time': pickle_encode_time + pickle_decode_time,
        'data': pickle_data
    }
    print(" ✓")
    
    return results


def print_comparison_table(results: Dict[str, Any], num_records: int):
    """Print a formatted comparison table."""
    print("\n" + "="*80)
    print(f"ENCODING COMPARISON RESULTS ({num_records:,} records)")
    print("="*80)
    
    # Find baseline (JSON) for relative comparisons
    json_size = results['JSON']['size']
    json_encode_time = results['JSON']['encode_time']
    json_decode_time = results['JSON']['decode_time']
    
    print(f"\n{'Format':<15} {'Size':<15} {'Size vs JSON':<15} {'Encode Time':<15} {'Decode Time':<15}")
    print("-" * 80)
    
    formats_to_show = ['JSON', 'Pickle']
    if MSGPACK_AVAILABLE:
        formats_to_show.insert(1, 'MessagePack')
    
    for format_name in formats_to_show:
        r = results[format_name]
        size_ratio = (r['size'] / json_size) * 100 if json_size > 0 else 0
        size_diff = ((r['size'] - json_size) / json_size) * 100 if json_size > 0 else 0
        
        size_vs_json = f"{size_diff:+.1f}%" if format_name != 'JSON' else "baseline"
        
        print(f"{format_name:<15} "
              f"{format_size(r['size']):<15} "
              f"{size_vs_json:<15} "
              f"{format_time(r['encode_time']):<15} "
              f"{format_time(r['decode_time']):<15}")
    
    print("\n" + "="*80)
    print("KEY INSIGHTS:")
    print("="*80)
    
    # Size comparison
    smallest = min(results.items(), key=lambda x: x[1]['size'])
    largest = max(results.items(), key=lambda x: x[1]['size'])
    print(f"\n📦 Size:")
    print(f"   • Smallest: {smallest[0]} ({format_size(smallest[1]['size'])})")
    print(f"   • Largest: {largest[0]} ({format_size(largest[1]['size'])})")
    
    if MSGPACK_AVAILABLE and 'MessagePack' in results:
        size_savings = ((json_size - results['MessagePack']['size']) / json_size) * 100
        print(f"   • MessagePack saves {size_savings:.1f}% vs JSON")
    
    # Speed comparison
    fastest_encode = min(results.items(), key=lambda x: x[1]['encode_time'])
    fastest_decode = min(results.items(), key=lambda x: x[1]['decode_time'])
    print(f"\n⚡ Speed:")
    print(f"   • Fastest encode: {fastest_encode[0]} ({format_time(fastest_encode[1]['encode_time'])})")
    print(f"   • Fastest decode: {fastest_decode[0]} ({format_time(fastest_decode[1]['decode_time'])})")
    
    # Human readability
    print(f"\n👁️  Human Readable:")
    print(f"   • JSON: ✅ Yes (can read with text editor)")
    if MSGPACK_AVAILABLE:
        print(f"   • MessagePack: ❌ No (binary format)")
    print(f"   • Pickle: ❌ No (binary format, Python-specific)")
    
    # Cross-language support
    print(f"\n🌐 Cross-Language Support:")
    print(f"   • JSON: ✅ Yes (supported everywhere)")
    if MSGPACK_AVAILABLE:
        print(f"   • MessagePack: ✅ Yes (libraries for many languages)")
    print(f"   • Pickle: ❌ No (Python only)")
    
    # Security
    print(f"\n🔒 Security:")
    print(f"   • JSON: ✅ Safe (no code execution)")
    if MSGPACK_AVAILABLE:
        print(f"   • MessagePack: ✅ Safe (no code execution)")
    print(f"   • Pickle: ⚠️  WARNING (can execute arbitrary code!)")
    
    print("\n" + "="*80)


def demonstrate_readability():
    """Show the difference in human readability."""
    print("\n" + "="*80)
    print("HUMAN READABILITY DEMONSTRATION")
    print("="*80)
    
    sample = [{"id": 1, "name": "Alice", "active": True}]
    
    print("\n📄 JSON (Human Readable):")
    json_str = json.dumps(sample, indent=2)
    print(json_str)
    
    if MSGPACK_AVAILABLE:
        print("\n📦 MessagePack (Binary - First 50 bytes):")
        msgpack_data = encode_msgpack(sample)
        print(msgpack_data[:50])
        print("... (binary data, not human readable)")
    
    print("\n📦 Pickle (Binary - First 50 bytes):")
    pickle_data = encode_pickle(sample)
    print(pickle_data[:50])
    print("... (binary data, Python-specific)")


def main():
    """Main function to run the encoding comparison demo."""
    print("="*80)
    print("DAY 1: ENCODING FUNDAMENTALS - TEXT VS BINARY")
    print("="*80)
    print("\nThis demo compares JSON, MessagePack, and Pickle encoding formats.")
    print("You'll see differences in size, speed, readability, and safety.\n")
    
    # Test with different data sizes
    test_sizes = [1, 100, 1000, 10000]
    
    for num_records in test_sizes:
        print(f"\n{'='*80}")
        print(f"Testing with {num_records:,} records...")
        print(f"{'='*80}")
        
        data = create_sample_data(num_records)
        print(f"Created {num_records:,} sample records")
        print("Benchmarking encoding/decoding...")
        
        results = benchmark_encoding(data, num_iterations=100 if num_records < 1000 else 10)
        print_comparison_table(results, num_records)
        
        # Only show readability demo for small dataset
        if num_records == 1:
            demonstrate_readability()
        
        # Ask if user wants to continue (for large datasets)
        if num_records < 10000:
            print(f"\n✓ Completed {num_records:,} records test")
        else:
            print(f"\n✓ Completed all tests!")
            break
    
    print("\n" + "="*80)
    print("CONCLUSION")
    print("="*80)
    print("""
Key Takeaways:

1. 📦 Binary formats (MessagePack, Pickle) are typically smaller than JSON
   → Saves bandwidth and storage

2. ⚡ Binary formats are often faster to encode/decode
   → Better performance for high-throughput systems

3. 👁️  JSON is human-readable, binary formats are not
   → JSON is better for debugging and manual inspection

4. 🌐 JSON and MessagePack work across languages
   → Pickle is Python-only (not suitable for cross-service communication)

5. 🔒 Security matters: Pickle can execute arbitrary code
   → Never use Pickle for untrusted data or cross-service communication

6. 🎯 Choose based on use case:
   - Web APIs → JSON (readability, universal support)
   - Internal services → MessagePack or Protocol Buffers (performance)
   - Python-only, trusted data → Pickle (convenience)
   - Cross-service → JSON or MessagePack (never Pickle!)
    """)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting...")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
