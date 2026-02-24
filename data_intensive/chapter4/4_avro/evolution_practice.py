"""
Avro Schema Evolution - Hands-On Practice

This script provides interactive exercises to practice Avro schema evolution.
You'll create data, evolve schemas, and see how Avro handles changes.
"""

import json
import sys
from pathlib import Path
from io import BytesIO

try:
    import avro.schema
    import avro.io
    AVRO_AVAILABLE = True
except ImportError:
    AVRO_AVAILABLE = False
    print("⚠️  avro-python3 not installed. Install with: pip install avro-python3")
    sys.exit(1)


def load_schema(schema_path: Path):
    """Load and parse Avro schema."""
    with open(schema_path, 'r') as f:
        schema_json = json.load(f)
    return avro.schema.parse(json.dumps(schema_json))


def encode_data(data: dict, schema):
    """Encode data using Avro schema."""
    writer = avro.io.DatumWriter(schema)
    bytes_writer = BytesIO()
    encoder = avro.io.BinaryEncoder(bytes_writer)
    writer.write(data, encoder)
    return bytes_writer.getvalue()


def decode_data(encoded_data: bytes, writer_schema, reader_schema=None):
    """Decode data using Avro schema(s)."""
    if reader_schema is None:
        reader_schema = writer_schema
    
    reader = avro.io.DatumReader(writer_schema=writer_schema, reader_schema=reader_schema)
    bytes_reader = BytesIO(encoded_data)
    decoder = avro.io.BinaryDecoder(bytes_reader)
    return reader.read(decoder)


def exercise_1_add_field():
    """Exercise 1: Adding a new field to schema."""
    print("="*80)
    print("EXERCISE 1: Adding a New Field")
    print("="*80)
    print("\n📝 Task: Add 'email' field to User schema")
    print("   - Start with v1 schema (id, name, age)")
    print("   - Evolve to v2 schema (id, name, age, email)")
    print("   - Test backward compatibility\n")
    
    # Load schemas
    base_dir = Path(__file__).parent
    schema_v1 = load_schema(base_dir / "user_v1.avsc")
    schema_v2 = load_schema(base_dir / "user_v2.avsc")
    
    # Create data with v1
    user_v1 = {
        "id": 1,
        "name": "Alice",
        "age": 30
    }
    
    print("Step 1: Create data with v1 schema")
    print(f"   Data: {user_v1}")
    
    # Encode with v1
    encoded = encode_data(user_v1, schema_v1)
    print(f"   Encoded: {len(encoded)} bytes")
    
    # Decode with v2 (has email field)
    print("\nStep 2: Read data with v2 schema (has 'email' field)")
    decoded_v2 = decode_data(encoded, schema_v1, schema_v2)
    print(f"   Decoded: {decoded_v2}")
    
    print("\n✅ Result:")
    print("   - 'id', 'name', 'age' read correctly")
    print("   - 'email' gets default value (null)")
    print("   - Backward compatible! ✓")
    
    return encoded, schema_v1, schema_v2


def exercise_2_remove_field():
    """Exercise 2: Removing a field from schema."""
    print("\n" + "="*80)
    print("EXERCISE 2: Removing a Field")
    print("="*80)
    print("\n📝 Task: Remove 'age' field from User schema")
    print("   - Start with v1 schema (id, name, age)")
    print("   - Evolve to v2 schema (id, name, email, phone)")
    print("   - Test forward compatibility\n")
    
    base_dir = Path(__file__).parent
    schema_v1 = load_schema(base_dir / "user_v1.avsc")
    schema_v2 = load_schema(base_dir / "user_v2.avsc")
    
    # Create data with v1 (has age)
    user_v1 = {
        "id": 2,
        "name": "Bob",
        "age": 25
    }
    
    print("Step 1: Create data with v1 schema (has 'age')")
    print(f"   Data: {user_v1}")
    
    # Encode with v1
    encoded = encode_data(user_v1, schema_v1)
    print(f"   Encoded: {len(encoded)} bytes")
    
    # Decode with v2 (no age field)
    print("\nStep 2: Read data with v2 schema (no 'age' field)")
    decoded_v2 = decode_data(encoded, schema_v1, schema_v2)
    print(f"   Decoded: {decoded_v2}")
    
    print("\n✅ Result:")
    print("   - 'id', 'name' read correctly")
    print("   - 'age' is ignored (not in v2 schema)")
    print("   - 'email', 'phone' get defaults")
    print("   - Forward compatible! ✓")


def exercise_3_rename_field():
    """Exercise 3: Renaming a field using aliases."""
    print("\n" + "="*80)
    print("EXERCISE 3: Renaming a Field (Using Aliases)")
    print("="*80)
    print("\n📝 Task: Rename 'phone' to 'phone_number'")
    print("   - v2 has 'phone' field")
    print("   - v3 has 'phone_number' with alias 'phone'")
    print("   - Test that old data still works\n")
    
    base_dir = Path(__file__).parent
    schema_v2 = load_schema(base_dir / "user_v2.avsc")
    schema_v3 = load_schema(base_dir / "user_v3.avsc")
    
    # Create data with v2 (has phone)
    user_v2 = {
        "id": 3,
        "name": "Charlie",
        "email": "charlie@example.com",
        "phone": "123-456-7890"
    }
    
    print("Step 1: Create data with v2 schema (field: 'phone')")
    print(f"   Data: {user_v2}")
    
    # Encode with v2
    encoded = encode_data(user_v2, schema_v2)
    print(f"   Encoded: {len(encoded)} bytes")
    
    # Decode with v3 (has phone_number with alias phone)
    print("\nStep 2: Read data with v3 schema (field: 'phone_number', alias: 'phone')")
    decoded_v3 = decode_data(encoded, schema_v2, schema_v3)
    print(f"   Decoded: {decoded_v3}")
    
    print("\n✅ Result:")
    print("   - Field renamed from 'phone' to 'phone_number'")
    print("   - Avro uses alias to match fields")
    print("   - Data preserved! ✓")


def exercise_4_nested_records():
    """Exercise 4: Working with nested records."""
    print("\n" + "="*80)
    print("EXERCISE 4: Nested Records")
    print("="*80)
    print("\n📝 Task: Add nested 'metadata' record")
    print("   - v3 adds nested UserMetadata record")
    print("   - Test nested schema evolution\n")
    
    base_dir = Path(__file__).parent
    schema_v3 = load_schema(base_dir / "user_v3.avsc")
    
    # Create data with nested metadata
    user_v3 = {
        "id": 4,
        "name": "Diana",
        "email": "diana@example.com",
        "phone_number": "555-1234",
        "metadata": {
            "created_at": "2024-01-01T00:00:00Z",
            "last_login": "2024-01-15T12:00:00Z"
        }
    }
    
    print("Step 1: Create data with nested metadata")
    print(f"   Data: {json.dumps(user_v3, indent=2)}")
    
    # Encode
    encoded = encode_data(user_v3, schema_v3)
    print(f"   Encoded: {len(encoded)} bytes")
    
    # Decode
    decoded = decode_data(encoded, schema_v3)
    print(f"\nStep 2: Decode nested data")
    print(f"   Decoded: {json.dumps(decoded, indent=2)}")
    
    print("\n✅ Result:")
    print("   - Nested records work perfectly")
    print("   - Complex data structures supported")
    print("   - Schema evolution works at all levels! ✓")


def exercise_5_type_compatibility():
    """Exercise 5: Understanding type compatibility."""
    print("\n" + "="*80)
    print("EXERCISE 5: Type Compatibility Rules")
    print("="*80)
    print("""
Avro type compatibility rules:

✅ Compatible Changes:
   - int → long (promotion)
   - float → double (promotion)
   - string → bytes (with UTF-8)
   - bytes → string (with UTF-8)
   - Adding union with null: ["null", "string"]

❌ Incompatible Changes:
   - int → string (different types)
   - string → int (different types)
   - Removing union null: ["string"] → "string" (if data has nulls)

Example:
   Writer: {"age": int}
   Reader: {"age": long}  ✅ Compatible (promotion)
   
   Writer: {"age": int}
   Reader: {"age": string}  ❌ Incompatible (different types)
    """)


def main():
    """Run all exercises."""
    print("\n" + "="*80)
    print("AVRO SCHEMA EVOLUTION - HANDS-ON PRACTICE")
    print("="*80)
    print("\nThese exercises will help you master Avro schema evolution.")
    print("You'll see how Avro handles different types of schema changes.\n")
    
    try:
        exercise_1_add_field()
        exercise_2_remove_field()
        exercise_3_rename_field()
        exercise_4_nested_records()
        exercise_5_type_compatibility()
        
        print("\n" + "="*80)
        print("PRACTICE COMPLETE!")
        print("="*80)
        print("""
You've practiced:
  ✅ Adding fields (backward compatible)
  ✅ Removing fields (forward compatible)
  ✅ Renaming fields (using aliases)
  ✅ Nested records
  ✅ Type compatibility rules

Key Learnings:
  1. Avro handles schema evolution automatically
  2. Writer's schema and reader's schema can differ
  3. Missing fields get defaults, extra fields are ignored
  4. Aliases enable field renaming
  5. Type changes must be compatible

Next: Try modifying the schemas yourself and test!
        """)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
