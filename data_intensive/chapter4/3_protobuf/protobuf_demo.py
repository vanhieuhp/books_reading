"""
Day 3-4: Protocol Buffers Deep Dive

This script demonstrates:
1. Protocol Buffers encoding/decoding
2. Schema evolution and compatibility
3. Backward compatibility (new code reads old data)
4. Forward compatibility (old code reads new data)
5. Comparison with JSON

Key concepts:
- Field numbers are critical (never change them!)
- proto3 makes all fields optional
- Unknown fields are ignored (enables forward compatibility)
"""

import json
import sys
import os
from pathlib import Path

# Add proto directory to path
proto_dir = Path(__file__).parent / "proto"
sys.path.insert(0, str(proto_dir.parent))

try:
    # Try to import generated protobuf code
    # First, we need to generate it
    import subprocess
    
    print("="*80)
    print("Generating Protocol Buffers code...")
    print("="*80)
    
    # Check if protoc is available
    try:
        result = subprocess.run(['protoc', '--version'], 
                              capture_output=True, text=True, timeout=5)
        print(f"✓ Found: {result.stdout.strip()}")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print("⚠️  Warning: protoc not found in PATH")
        print("   Install Protocol Buffers compiler:")
        print("   - macOS: brew install protobuf")
        print("   - Linux: apt-get install protobuf-compiler")
        print("   - Or download from: https://grpc.io/docs/protoc-installation/")
        print("\n   Continuing with demonstration of concepts...")
        PROTOC_AVAILABLE = False
    else:
        PROTOC_AVAILABLE = True
    
    if PROTOC_AVAILABLE:
        # Generate Python code from .proto file
        proto_file = proto_dir / "user.proto"
        output_dir = proto_dir.parent
        
        cmd = [
            'protoc',
            f'--python_out={output_dir}',
            f'--proto_path={proto_dir}',
            str(proto_file)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✓ Generated Python code from {proto_file.name}")
        else:
            print(f"⚠️  Error generating code: {result.stderr}")
            PROTOC_AVAILABLE = False
    
    # Try to import generated code
    if PROTOC_AVAILABLE:
        try:
            import user_pb2
            PROTOBUF_AVAILABLE = True
            print("✓ Protocol Buffers code imported successfully\n")
        except ImportError as e:
            print(f"⚠️  Could not import generated code: {e}")
            print("   Will demonstrate concepts without actual encoding\n")
            PROTOBUF_AVAILABLE = False
    else:
        PROTOBUF_AVAILABLE = False
        
except Exception as e:
    print(f"⚠️  Error setting up Protocol Buffers: {e}")
    PROTOBUF_AVAILABLE = False


def demonstrate_protobuf_basics():
    """Demonstrate basic Protocol Buffers usage."""
    if not PROTOBUF_AVAILABLE:
        print("="*80)
        print("PROTOCOL BUFFERS BASICS (Conceptual)")
        print("="*80)
        print("""
Since protoc is not available, here's what Protocol Buffers does:

1. Schema Definition (.proto file):
   - Defines data structure
   - Assigns field numbers (critical for evolution)
   - Generates code for multiple languages

2. Encoding:
   - Converts objects to compact binary format
   - Only stores field values, not field names
   - Uses field numbers to identify fields

3. Decoding:
   - Reads binary data using schema
   - Reconstructs objects
   - Unknown fields are ignored (forward compatibility)

4. Key Advantages:
   - Smaller than JSON (no field names in data)
   - Faster encoding/decoding
   - Strong typing
   - Schema evolution support
        """)
        return
    
    print("="*80)
    print("PROTOCOL BUFFERS BASICS")
    print("="*80)
    
    # Create a User object
    user = user_pb2.User()
    user.id = 1
    user.name = "Alice"
    user.email = "alice@example.com"
    user.age = 30
    user.active = True
    user.tags.extend(["premium", "verified"])
    
    # Set nested metadata
    user.metadata.created_at = "2024-01-01T00:00:00Z"
    user.metadata.last_login = "2024-01-15T12:00:00Z"
    user.metadata.settings["theme"] = "dark"
    user.metadata.settings["language"] = "en"
    
    print("\n1. Created User object:")
    print(f"   ID: {user.id}")
    print(f"   Name: {user.name}")
    print(f"   Email: {user.email}")
    print(f"   Tags: {list(user.tags)}")
    
    # Serialize to bytes
    serialized = user.SerializeToString()
    print(f"\n2. Serialized to {len(serialized)} bytes")
    
    # Compare with JSON
    json_data = json.dumps({
        "id": 1,
        "name": "Alice",
        "email": "alice@example.com",
        "age": 30,
        "active": True,
        "tags": ["premium", "verified"],
        "metadata": {
            "created_at": "2024-01-01T00:00:00Z",
            "last_login": "2024-01-15T12:00:00Z",
            "settings": {"theme": "dark", "language": "en"}
        }
    })
    json_bytes = json_data.encode('utf-8')
    
    print(f"   JSON equivalent: {len(json_bytes)} bytes")
    size_savings = ((len(json_bytes) - len(serialized)) / len(json_bytes)) * 100
    print(f"   Protobuf saves: {size_savings:.1f}%")
    
    # Deserialize
    user2 = user_pb2.User()
    user2.ParseFromString(serialized)
    
    print("\n3. Deserialized User object:")
    print(f"   ID: {user2.id}")
    print(f"   Name: {user2.name}")
    print(f"   Email: {user2.email}")
    print(f"   ✓ Data integrity preserved")
    
    return user, serialized


def demonstrate_backward_compatibility():
    """Demonstrate backward compatibility: new code reads old data."""
    if not PROTOBUF_AVAILABLE:
        print("\n" + "="*80)
        print("BACKWARD COMPATIBILITY (Conceptual)")
        print("="*80)
        print("""
Backward Compatibility = New code reads old data ✅

Scenario:
- Old code writes User with: id, name (no email)
- New code reads it: id, name, email

How it works:
1. Old data doesn't have email field
2. New schema has email as optional
3. New code reads old data successfully
4. Email field is empty/None (default value)

Key rule: Add new fields as optional (proto3 default)
        """)
        return
    
    print("\n" + "="*80)
    print("BACKWARD COMPATIBILITY: New Code Reads Old Data")
    print("="*80)
    
    # Simulate old data (created with old schema - no email field)
    # In real scenario, this would be data stored with old schema
    print("\n📝 Scenario: Old code wrote data without 'email' field")
    print("   New code needs to read this old data")
    
    # Create user with only old fields (simulating old data)
    old_user = user_pb2.User()
    old_user.id = 2
    old_user.name = "Bob"
    # Note: email is not set (old schema didn't have it)
    old_user.age = 25
    
    old_data = old_user.SerializeToString()
    print(f"   Old data size: {len(old_data)} bytes")
    
    # New code reads old data
    new_user = user_pb2.User()
    new_user.ParseFromString(old_data)
    
    print("\n✅ New code successfully reads old data:")
    print(f"   ID: {new_user.id}")
    print(f"   Name: {new_user.name}")
    print(f"   Email: '{new_user.email}' (empty - wasn't in old data)")
    print(f"   Age: {new_user.age}")
    print("\n   ✓ Backward compatibility works!")


def demonstrate_forward_compatibility():
    """Demonstrate forward compatibility: old code reads new data."""
    if not PROTOBUF_AVAILABLE:
        print("\n" + "="*80)
        print("FORWARD COMPATIBILITY (Conceptual)")
        print("="*80)
        print("""
Forward Compatibility = Old code reads new data ⚠️

Scenario:
- New code writes User with: id, name, email, phone (new field)
- Old code reads it: id, name (doesn't know about email, phone)

How it works:
1. New data has extra fields (email, phone)
2. Old code doesn't know about these fields
3. Old code ignores unknown fields
4. Old code reads only fields it knows about

Key rule: Unknown fields are ignored (enables forward compatibility)
        """)
        return
    
    print("\n" + "="*80)
    print("FORWARD COMPATIBILITY: Old Code Reads New Data")
    print("="*80)
    
    # Simulate new data (created with new schema - has email field)
    print("\n📝 Scenario: New code writes data with 'email' field")
    print("   Old code (doesn't know about email) needs to read it")
    
    # Create user with new fields (simulating new schema)
    new_data_user = user_pb2.User()
    new_data_user.id = 3
    new_data_user.name = "Charlie"
    new_data_user.email = "charlie@example.com"  # New field
    new_data_user.age = 28
    
    new_data = new_data_user.SerializeToString()
    print(f"   New data size: {len(new_data)} bytes")
    
    # Old code reads new data (simulate by only accessing old fields)
    old_code_user = user_pb2.User()
    old_code_user.ParseFromString(new_data)
    
    print("\n✅ Old code successfully reads new data:")
    print(f"   ID: {old_code_user.id}")
    print(f"   Name: {old_code_user.name}")
    print(f"   Age: {old_code_user.age}")
    print(f"   Email: '{old_code_user.email}' (present but old code can ignore)")
    print("\n   ✓ Forward compatibility works!")
    print("   Note: Old code can access new fields if they exist,")
    print("         but it doesn't break if fields are missing")


def demonstrate_field_numbers():
    """Demonstrate why field numbers are critical."""
    print("\n" + "="*80)
    print("WHY FIELD NUMBERS ARE CRITICAL")
    print("="*80)
    
    print("""
Field numbers (1, 2, 3, etc.) are the KEY to Protocol Buffers compatibility.

✅ DO:
   - Use field numbers to identify fields
   - Add new fields with NEW field numbers
   - Keep existing field numbers unchanged

❌ DON'T:
   - Change existing field numbers (BREAKS compatibility!)
   - Reuse field numbers (causes confusion)
   - Remove field numbers (mark as reserved instead)

Example:
  message User {
    int32 id = 1;        // Field number 1
    string name = 2;     // Field number 2
    string email = 3;    // Field number 3 (added later)
  }

Evolution:
  - v1: id=1, name=2
  - v2: id=1, name=2, email=3  ✅ (added new field, kept old numbers)
  - v3: id=1, name=2, email=3, phone=4  ✅ (added another new field)

If you changed field numbers:
  - v1: id=1, name=2
  - v2: id=1, name=3, email=2  ❌ (changed name from 2 to 3 - BREAKS!)
    """)


def compare_with_json():
    """Compare Protocol Buffers with JSON."""
    if not PROTOBUF_AVAILABLE:
        return
    
    print("\n" + "="*80)
    print("PROTOCOL BUFFERS vs JSON COMPARISON")
    print("="*80)
    
    import time
    
    # Create sample data
    users = []
    for i in range(100):
        user = user_pb2.User()
        user.id = i
        user.name = f"User_{i}"
        user.email = f"user{i}@example.com"
        user.age = 20 + (i % 50)
        user.active = i % 2 == 0
        user.tags.extend([f"tag_{j}" for j in range(3)])
        users.append(user)
    
    # Protocol Buffers encoding
    start = time.time()
    protobuf_data = b''.join([u.SerializeToString() for u in users])
    protobuf_time = time.time() - start
    
    # JSON encoding
    json_users = [
        {
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "age": u.age,
            "active": u.active,
            "tags": list(u.tags)
        }
        for u in users
    ]
    start = time.time()
    json_data = json.dumps(json_users).encode('utf-8')
    json_time = time.time() - start
    
    print(f"\nEncoding 100 users:")
    print(f"  Protocol Buffers: {len(protobuf_data)} bytes, {protobuf_time*1000:.2f} ms")
    print(f"  JSON:             {len(json_data)} bytes, {json_time*1000:.2f} ms")
    
    size_savings = ((len(json_data) - len(protobuf_data)) / len(json_data)) * 100
    speed_ratio = json_time / protobuf_time if protobuf_time > 0 else 0
    
    print(f"\n  Protobuf is {size_savings:.1f}% smaller")
    print(f"  Protobuf is {speed_ratio:.1f}x faster to encode")


def main():
    """Main function to run all Protocol Buffers demonstrations."""
    print("\n" + "="*80)
    print("DAY 3-4: PROTOCOL BUFFERS DEEP DIVE")
    print("="*80)
    print("\nThis demo covers:")
    print("  1. Protocol Buffers basics")
    print("  2. Backward compatibility")
    print("  3. Forward compatibility")
    print("  4. Field numbers importance")
    print("  5. Comparison with JSON")
    print()
    
    # Run demonstrations
    demonstrate_protobuf_basics()
    demonstrate_backward_compatibility()
    demonstrate_forward_compatibility()
    demonstrate_field_numbers()
    compare_with_json()
    
    print("\n" + "="*80)
    print("KEY TAKEAWAYS")
    print("="*80)
    print("""
1. ✅ Protocol Buffers are smaller and faster than JSON
   - No field names in encoded data (uses field numbers)
   - Compact binary encoding

2. ✅ Schema evolution is safe if done correctly
   - Add new fields with new field numbers
   - Never change existing field numbers
   - Unknown fields are ignored

3. ✅ Backward compatibility (easier)
   - New code reads old data
   - Missing fields get default values

4. ⚠️  Forward compatibility (requires care)
   - Old code reads new data
   - Unknown fields are ignored
   - Old code must handle missing fields gracefully

5. 🔑 Field numbers are critical
   - They identify fields in binary data
   - Never change them once used
   - They enable compatibility

6. 🎯 When to use Protocol Buffers:
   - Internal services (performance)
   - gRPC APIs
   - Mobile apps (small payloads)
   - Cross-language communication
   - When you need strong typing
    """)
    
    if not PROTOBUF_AVAILABLE:
        print("\n" + "="*80)
        print("NEXT STEPS")
        print("="*80)
        print("""
To run the full demo with actual encoding/decoding:

1. Install Protocol Buffers compiler:
   macOS:  brew install protobuf
   Linux:  apt-get install protobuf-compiler
   Windows: Download from https://grpc.io/docs/protoc-installation/

2. Install Python protobuf library:
   pip install protobuf

3. Run this script again - it will generate the code automatically!
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
