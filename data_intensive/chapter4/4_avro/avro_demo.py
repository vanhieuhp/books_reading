"""
Day 5-6: Apache Avro - Schema Evolution Champion

This script demonstrates:
1. Avro schema definition (JSON format)
2. Encoding/decoding with Avro
3. Writer's schema vs reader's schema
4. Schema evolution and resolution
5. Comparison with Protocol Buffers

Key concepts:
- Schema stored with data OR in registry
- Writer's schema: schema used to write data
- Reader's schema: schema used to read data
- Schema resolution: Avro resolves differences automatically
- Perfect for data pipelines and Kafka
"""

import json
import sys
from pathlib import Path
from io import BytesIO

# Try to import Avro
try:
    import avro.schema
    import avro.io
    AVRO_AVAILABLE = True
except ImportError:
    AVRO_AVAILABLE = False
    print("⚠️  Warning: avro-python3 not installed.")
    print("   Install with: pip install avro-python3")
    print("   Continuing with conceptual demonstration...\n")


def load_schema(schema_path: Path) -> dict:
    """Load Avro schema from JSON file."""
    with open(schema_path, 'r') as f:
        return json.load(f)


def demonstrate_avro_basics():
    """Demonstrate basic Avro encoding/decoding."""
    if not AVRO_AVAILABLE:
        print("="*80)
        print("APACHE AVRO BASICS (Conceptual)")
        print("="*80)
        print("""
Since avro-python3 is not available, here's what Avro does:

1. Schema Definition (JSON format):
   - Defines data structure in JSON
   - More readable than Protocol Buffers
   - Supports complex types (unions, maps, arrays)

2. Encoding:
   - Binary encoding (compact)
   - Schema can be stored with data OR in registry
   - Writer's schema used for encoding

3. Decoding:
   - Reader's schema used for decoding
   - Schema resolution handles differences
   - Unknown fields ignored, missing fields use defaults

4. Key Advantages:
   - Excellent schema evolution
   - Schema stored with data (self-describing)
   - Perfect for data pipelines
   - Great for Kafka with Schema Registry
        """)
        return
    
    print("="*80)
    print("APACHE AVRO BASICS")
    print("="*80)
    
    # Load schema
    schema_path = Path(__file__).parent / "user_v1.avsc"
    schema_json = load_schema(schema_path)
    schema = avro.schema.parse(json.dumps(schema_json))
    
    print("\n1. Loaded Avro Schema (v1):")
    print(json.dumps(schema_json, indent=2))
    
    # Create data
    user_data = {
        "id": 1,
        "name": "Alice",
        "age": 30
    }
    
    print("\n2. User Data:")
    print(f"   {user_data}")
    
    # Encode
    writer = avro.io.DatumWriter(schema)
    bytes_writer = BytesIO()
    encoder = avro.io.BinaryEncoder(bytes_writer)
    writer.write(user_data, encoder)
    encoded_data = bytes_writer.getvalue()
    
    print(f"\n3. Encoded to {len(encoded_data)} bytes")
    
    # Compare with JSON
    json_data = json.dumps(user_data).encode('utf-8')
    print(f"   JSON equivalent: {len(json_data)} bytes")
    size_savings = ((len(json_data) - len(encoded_data)) / len(json_data)) * 100
    print(f"   Avro saves: {size_savings:.1f}%")
    
    # Decode with same schema
    reader = avro.io.DatumReader(schema)
    bytes_reader = BytesIO(encoded_data)
    decoder = avro.io.BinaryDecoder(bytes_reader)
    decoded_data = reader.read(decoder)
    
    print("\n4. Decoded User Data:")
    print(f"   {decoded_data}")
    print("   ✓ Data integrity preserved")
    
    return schema, encoded_data, user_data


def demonstrate_writer_reader_schemas():
    """Demonstrate writer's schema vs reader's schema."""
    if not AVRO_AVAILABLE:
        print("\n" + "="*80)
        print("WRITER'S SCHEMA vs READER'S SCHEMA (Conceptual)")
        print("="*80)
        print("""
This is Avro's superpower!

Writer's Schema: Schema used when data was written
Reader's Schema: Schema used when data is read

Key Insight:
- They can be DIFFERENT!
- Avro automatically resolves differences
- This enables schema evolution

Example:
- Writer (v1): {id, name, age}
- Reader (v2): {id, name, email}
- Avro resolves: reads id, name, email gets default (null)
        """)
        return
    
    print("\n" + "="*80)
    print("WRITER'S SCHEMA vs READER'S SCHEMA")
    print("="*80)
    
    # Write with v1 schema
    print("\n📝 Writing data with v1 schema:")
    schema_v1_path = Path(__file__).parent / "user_v1.avsc"
    schema_v1_json = load_schema(schema_v1_path)
    schema_v1 = avro.schema.parse(json.dumps(schema_v1_json))
    
    user_data = {
        "id": 1,
        "name": "Alice",
        "age": 30
    }
    
    writer = avro.io.DatumWriter(schema_v1)
    bytes_writer = BytesIO()
    encoder = avro.io.BinaryEncoder(bytes_writer)
    writer.write(user_data, encoder)
    encoded_data = bytes_writer.getvalue()
    
    print(f"   Schema: {json.dumps(schema_v1_json, indent=2)}")
    print(f"   Data: {user_data}")
    print(f"   Encoded: {len(encoded_data)} bytes")
    
    # Read with v2 schema (different schema!)
    print("\n📖 Reading data with v2 schema:")
    schema_v2_path = Path(__file__).parent / "user_v2.avsc"
    schema_v2_json = load_schema(schema_v2_path)
    schema_v2 = avro.schema.parse(json.dumps(schema_v2_json))
    
    print(f"   Schema: {json.dumps(schema_v2_json, indent=2)}")
    print("   Note: v2 has 'email' and 'phone' fields that v1 doesn't have!")
    
    # Use DatumReader with BOTH schemas
    reader = avro.io.DatumReader(writer_schema=schema_v1, reader_schema=schema_v2)
    bytes_reader = BytesIO(encoded_data)
    decoder = avro.io.BinaryDecoder(bytes_reader)
    decoded_data = reader.read(decoder)
    
    print(f"\n✅ Decoded data:")
    print(f"   {decoded_data}")
    print("\n   ✓ Avro automatically resolved schema differences!")
    print("   - 'id' and 'name' read correctly")
    print("   - 'age' from v1 is ignored (not in v2)")
    print("   - 'email' and 'phone' get default values (null)")


def demonstrate_schema_evolution():
    """Demonstrate schema evolution scenarios."""
    if not AVRO_AVAILABLE:
        print("\n" + "="*80)
        print("SCHEMA EVOLUTION SCENARIOS (Conceptual)")
        print("="*80)
        print("""
Avro handles schema evolution beautifully:

1. Adding Fields:
   - Writer (v1): {id, name}
   - Reader (v2): {id, name, email}
   - Result: ✅ email gets default value

2. Removing Fields:
   - Writer (v2): {id, name, email}
   - Reader (v1): {id, name}
   - Result: ✅ email is ignored

3. Renaming Fields:
   - Writer: {phone}
   - Reader: {phone_number} with alias "phone"
   - Result: ✅ Avro resolves using alias

4. Changing Types:
   - Must be compatible (int → long ✅, string → int ❌)
        """)
        return
    
    print("\n" + "="*80)
    print("SCHEMA EVOLUTION SCENARIOS")
    print("="*80)
    
    # Scenario 1: Adding fields (backward compatible)
    print("\n" + "-"*80)
    print("SCENARIO 1: Adding Fields (Backward Compatible)")
    print("-"*80)
    
    schema_v1_path = Path(__file__).parent / "user_v1.avsc"
    schema_v1_json = load_schema(schema_v1_path)
    schema_v1 = avro.schema.parse(json.dumps(schema_v1_json))
    
    # Write with v1
    user_v1 = {"id": 1, "name": "Alice", "age": 30}
    writer_v1 = avro.io.DatumWriter(schema_v1)
    bytes_writer = BytesIO()
    encoder = avro.io.BinaryEncoder(bytes_writer)
    writer_v1.write(user_v1, encoder)
    data_v1 = bytes_writer.getvalue()
    
    # Read with v2 (has email and phone)
    schema_v2_path = Path(__file__).parent / "user_v2.avsc"
    schema_v2_json = load_schema(schema_v2_path)
    schema_v2 = avro.schema.parse(json.dumps(schema_v2_json))
    
    reader_v2 = avro.io.DatumReader(writer_schema=schema_v1, reader_schema=schema_v2)
    bytes_reader = BytesIO(data_v1)
    decoder = avro.io.BinaryDecoder(bytes_reader)
    result_v2 = reader_v2.read(decoder)
    
    print(f"   Written with v1: {user_v1}")
    print(f"   Read with v2:    {result_v2}")
    print("   ✅ New fields (email, phone) get default values")
    
    # Scenario 2: Removing fields (forward compatible)
    print("\n" + "-"*80)
    print("SCENARIO 2: Removing Fields (Forward Compatible)")
    print("-"*80)
    
    # Write with v2
    user_v2 = {"id": 2, "name": "Bob", "email": "bob@example.com", "phone": "123-456-7890"}
    writer_v2 = avro.io.DatumWriter(schema_v2)
    bytes_writer = BytesIO()
    encoder = avro.io.BinaryEncoder(bytes_writer)
    writer_v2.write(user_v2, encoder)
    data_v2 = bytes_writer.getvalue()
    
    # Read with v1 (doesn't have email, phone)
    reader_v1 = avro.io.DatumReader(writer_schema=schema_v2, reader_schema=schema_v1)
    bytes_reader = BytesIO(data_v2)
    decoder = avro.io.BinaryDecoder(bytes_reader)
    result_v1 = reader_v1.read(decoder)
    
    print(f"   Written with v2: {user_v2}")
    print(f"   Read with v1:    {result_v1}")
    print("   ✅ Extra fields (email, phone) are ignored")
    
    # Scenario 3: Renaming fields (using aliases)
    print("\n" + "-"*80)
    print("SCENARIO 3: Renaming Fields (Using Aliases)")
    print("-"*80)
    
    schema_v3_path = Path(__file__).parent / "user_v3.avsc"
    schema_v3_json = load_schema(schema_v3_path)
    schema_v3 = avro.schema.parse(json.dumps(schema_v3_json))
    
    # Write with v2 (has "phone")
    user_v2_phone = {"id": 3, "name": "Charlie", "email": "charlie@example.com", "phone": "987-654-3210"}
    writer_v2_phone = avro.io.DatumWriter(schema_v2)
    bytes_writer = BytesIO()
    encoder = avro.io.BinaryEncoder(bytes_writer)
    writer_v2_phone.write(user_v2_phone, encoder)
    data_v2_phone = bytes_writer.getvalue()
    
    # Read with v3 (has "phone_number" with alias "phone")
    reader_v3 = avro.io.DatumReader(writer_schema=schema_v2, reader_schema=schema_v3)
    bytes_reader = BytesIO(data_v2_phone)
    decoder = avro.io.BinaryDecoder(bytes_reader)
    result_v3 = reader_v3.read(decoder)
    
    print(f"   Written with v2: {user_v2_phone} (field: 'phone')")
    print(f"   Read with v3:    {result_v3} (field: 'phone_number')")
    print("   ✅ Field renamed using alias")


def compare_with_protobuf():
    """Compare Avro with Protocol Buffers."""
    print("\n" + "="*80)
    print("AVRO vs PROTOCOL BUFFERS")
    print("="*80)
    
    comparison = """
Key Differences:

1. Schema Format:
   ✅ Avro: JSON (human-readable, easier to write)
   ⚠️  Protobuf: .proto files (more compact, needs compiler)

2. Schema Storage:
   ✅ Avro: Stored with data OR in registry (self-describing)
   ⚠️  Protobuf: Schema not stored with data (needs separate management)

3. Schema Evolution:
   ✅ Avro: Excellent (writer's schema vs reader's schema)
   ✅ Protobuf: Good (field numbers enable evolution)

4. Type System:
   ✅ Avro: Rich (unions, maps, arrays, nested records)
   ⚠️  Protobuf: Good (but less flexible unions)

5. Use Cases:
   ✅ Avro: Data pipelines, Kafka, data lakes, analytics
   ✅ Protobuf: RPC, internal services, mobile apps

6. Performance:
   ✅ Both: Similar (compact binary encoding)
   ✅ Both: Fast encoding/decoding

7. Language Support:
   ✅ Avro: Many languages (Java, Python, C++, etc.)
   ✅ Protobuf: Many languages (more mature tooling)

When to Choose:

Choose Avro if:
  - Building data pipelines
  - Using Kafka (with Schema Registry)
  - Need self-describing data
  - Schema evolution is critical
  - Working with data lakes

Choose Protobuf if:
  - Building RPC services (gRPC)
  - Need mature tooling
  - Internal services
  - Mobile apps (small payloads)
  - Want code generation
    """
    print(comparison)


def demonstrate_schema_registry_concept():
    """Explain Schema Registry pattern."""
    print("\n" + "="*80)
    print("SCHEMA REGISTRY PATTERN")
    print("="*80)
    
    explanation = """
Schema Registry is a central service that stores Avro schemas.

How it works:

1. Producer writes data:
   - Serializes data with schema
   - Sends schema ID (not full schema) + data to Kafka
   - Schema Registry stores the schema

2. Consumer reads data:
   - Receives schema ID + data from Kafka
   - Fetches schema from Schema Registry using ID
   - Deserializes with fetched schema (or uses its own reader schema)

Benefits:

✅ Schema versioning
✅ Schema evolution management
✅ Smaller messages (schema ID instead of full schema)
✅ Centralized schema management
✅ Compatibility checking

Example Flow:

Producer:
  1. Register schema v1 in Schema Registry → get schema ID (e.g., 42)
  2. Serialize data with schema v1
  3. Send to Kafka: {schema_id: 42, data: <binary>}

Consumer:
  1. Receive from Kafka: {schema_id: 42, data: <binary>}
  2. Fetch schema v1 from Registry (ID 42)
  3. OR use own reader schema (v2) for evolution
  4. Deserialize data

Tools:
  - Confluent Schema Registry (most popular)
  - Apache Kafka Schema Registry
  - Custom implementations
    """
    print(explanation)


def main():
    """Main function to run all Avro demonstrations."""
    print("\n" + "="*80)
    print("DAY 5-6: APACHE AVRO - SCHEMA EVOLUTION CHAMPION")
    print("="*80)
    print("\nThis demo covers:")
    print("  1. Avro basics (schema, encoding, decoding)")
    print("  2. Writer's schema vs reader's schema")
    print("  3. Schema evolution scenarios")
    print("  4. Comparison with Protocol Buffers")
    print("  5. Schema Registry pattern")
    print()
    
    # Run demonstrations
    demonstrate_avro_basics()
    demonstrate_writer_reader_schemas()
    demonstrate_schema_evolution()
    compare_with_protobuf()
    demonstrate_schema_registry_concept()
    
    print("\n" + "="*80)
    print("KEY TAKEAWAYS")
    print("="*80)
    print("""
1. ✅ Avro schemas are JSON (human-readable)
   - Easier to write than Protocol Buffers
   - Self-documenting

2. ✅ Writer's schema vs reader's schema
   - They can be different!
   - Avro resolves differences automatically
   - This is Avro's superpower

3. ✅ Excellent schema evolution
   - Adding fields: ✅ (get defaults)
   - Removing fields: ✅ (ignored)
   - Renaming fields: ✅ (use aliases)
   - Changing types: ⚠️ (must be compatible)

4. ✅ Schema Registry pattern
   - Centralized schema management
   - Used with Kafka
   - Enables schema versioning

5. 🎯 When to use Avro:
   - Data pipelines
   - Kafka topics
   - Data lakes
   - Analytics workloads
   - When schema evolution is critical

6. 🔑 Key advantage over Protobuf:
   - Schema stored with data (self-describing)
   - Better for long-term data storage
   - Perfect for data pipelines
    """)
    
    if not AVRO_AVAILABLE:
        print("\n" + "="*80)
        print("NEXT STEPS")
        print("="*80)
        print("""
To run the full demo with actual encoding/decoding:

1. Install Avro Python library:
   pip install avro-python3

2. Run this script again - it will encode/decode data!

Note: For Schema Registry, you'll need:
  - Kafka (or Confluent Cloud)
  - Confluent Schema Registry
  - confluent-kafka library
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
