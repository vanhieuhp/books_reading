# Day 5-6: Apache Avro - Schema Evolution Champion

## 🎯 Learning Objectives

By completing this exercise, you will:

1. Understand Avro schema syntax (JSON format)
2. Encode and decode data with Avro
3. Master writer's schema vs reader's schema concept
4. Understand schema evolution and resolution
5. Learn the Schema Registry pattern
6. Compare Avro with Protocol Buffers
7. Know when to use Avro vs other formats

## 📋 What You'll Build

1. **Avro Schemas**: Three versions showing evolution (v1, v2, v3)
2. **Encoding/Decoding Demo**: Serialize and deserialize data
3. **Evolution Examples**: See how schemas evolve safely
4. **Practice Exercises**: Hands-on schema evolution scenarios
5. **Comparison**: Avro vs Protocol Buffers

## 🚀 Setup

### Prerequisites

1. **Install Avro Python Library**:
   ```bash
   pip install avro-python3
   ```

2. **Verify Installation**:
   ```python
   import avro.schema
   import avro.io
   ```

### Run the Demos

```bash
cd chapter4/4_avro

# Main demo
python3 avro_demo.py

# Practice exercises
python3 evolution_practice.py
```

## 📊 What You'll Learn

### 1. Avro Schema Basics

Avro schemas are written in JSON (unlike Protocol Buffers):

```json
{
  "type": "record",
  "name": "User",
  "fields": [
    {"name": "id", "type": "int"},
    {"name": "name", "type": "string"},
    {"name": "age", "type": "int"}
  ]
}
```

**Key Points:**
- Human-readable JSON format
- Self-documenting
- Supports complex types (unions, maps, arrays, nested records)

### 2. Writer's Schema vs Reader's Schema

This is Avro's superpower!

- **Writer's Schema**: Schema used when data was written
- **Reader's Schema**: Schema used when data is read
- **They can be different!** Avro resolves differences automatically

**Example:**
- Writer (v1): `{id, name, age}`
- Reader (v2): `{id, name, email}`
- Result: ✅ Avro reads `id` and `name`, `email` gets default (null), `age` is ignored

### 3. Schema Evolution

Avro handles schema changes beautifully:

**✅ Adding Fields** (Backward Compatible):
- Writer: `{id, name}`
- Reader: `{id, name, email}`
- Result: `email` gets default value

**✅ Removing Fields** (Forward Compatible):
- Writer: `{id, name, age}`
- Reader: `{id, name}`
- Result: `age` is ignored

**✅ Renaming Fields** (Using Aliases):
- Writer: `{phone}`
- Reader: `{phone_number}` with alias `"phone"`
- Result: Avro matches using alias

**⚠️ Changing Types** (Must be Compatible):
- `int` → `long` ✅ (promotion)
- `int` → `string` ❌ (incompatible)

### 4. Schema Registry Pattern

Schema Registry is a central service for managing Avro schemas:

**How it works:**
1. Producer registers schema → gets schema ID
2. Producer sends: `{schema_id: 42, data: <binary>}`
3. Consumer receives schema ID, fetches schema from registry
4. Consumer deserializes with fetched schema (or uses own reader schema)

**Benefits:**
- Schema versioning
- Centralized management
- Smaller messages (ID instead of full schema)
- Compatibility checking

**Tools:**
- Confluent Schema Registry (most popular)
- Used with Kafka

## 🎓 Key Concepts

### Schema Storage

**Two Approaches:**

1. **Schema with Data** (Self-describing):
   - Schema stored alongside data
   - Data is self-describing
   - Good for data lakes, long-term storage

2. **Schema Registry**:
   - Schema stored in central registry
   - Data references schema by ID
   - Good for Kafka, streaming

### Type System

Avro supports rich types:

- **Primitives**: int, long, float, double, boolean, string, bytes, null
- **Complex**: record, enum, array, map, union, fixed
- **Unions**: `["null", "string"]` (nullable string)

### Schema Resolution

Avro automatically resolves schema differences:

1. **Matching fields**: Read directly
2. **Missing fields**: Use default values
3. **Extra fields**: Ignore
4. **Renamed fields**: Use aliases to match

## 💡 Exercises to Try

1. **Modify Schemas**:
   - Add new fields to `user_v2.avsc`
   - Test backward compatibility
   - See how defaults work

2. **Test Type Changes**:
   - Try changing `int` to `long` (should work)
   - Try changing `int` to `string` (should fail)
   - Understand compatibility rules

3. **Create Nested Schemas**:
   - Add more nested records
   - Test evolution of nested structures

4. **Practice with Real Data**:
   - Use your own data structures
   - Evolve schemas over time
   - Test compatibility

## 🔍 Understanding the Results

### Size Comparison

- **Avro**: Compact binary encoding
- **JSON**: Larger (text-based, field names included)
- Typical savings: 20-40% smaller than JSON

### Performance

- **Avro**: Fast encoding/decoding
- **JSON**: Slower (string parsing)
- Similar to Protocol Buffers

### Schema Evolution

- **Avro**: Excellent (writer's schema vs reader's schema)
- **Protocol Buffers**: Good (field numbers)
- **JSON**: Poor (no schema, no evolution support)

## ⚠️ Important Rules

1. **Default values required** for new fields
   - New fields must have defaults
   - Enables backward compatibility

2. **Type compatibility matters**
   - Some type changes are compatible (int → long)
   - Others are not (int → string)

3. **Aliases for renaming**
   - Use aliases to rename fields
   - Enables smooth transitions

4. **Union types for optional fields**
   - `["null", "string"]` = optional string
   - Allows null values

## 📚 Next Steps

After completing this exercise:

1. ✅ You understand Avro schemas
2. ✅ You know writer's vs reader's schema
3. ✅ You understand schema evolution
4. ✅ Ready for Day 7-8: Schema Evolution Mastery

## 🐛 Troubleshooting

### "ModuleNotFoundError: No module named 'avro'"

```bash
pip install avro-python3
```

Note: Use `avro-python3`, not `avro` (different packages)

### "SchemaParseException"

Check your schema JSON:
- Must be valid JSON
- Required fields: type, name, fields
- Field types must be valid Avro types

### "Type mismatch" errors

- Check type compatibility rules
- int → long ✅, int → string ❌
- Use unions for nullable types: `["null", "string"]`

## 📖 Additional Resources

- [Avro Documentation](https://avro.apache.org/docs/current/)
- [Avro Python API](https://avro.apache.org/docs/current/api/python/index.html)
- [Schema Evolution](https://avro.apache.org/docs/current/spec.html#Schema+Resolution)
- [Confluent Schema Registry](https://docs.confluent.io/platform/current/schema-registry/index.html)

## 🎯 When to Use Avro

**Choose Avro if:**
- ✅ Building data pipelines
- ✅ Using Kafka (with Schema Registry)
- ✅ Working with data lakes
- ✅ Need self-describing data
- ✅ Schema evolution is critical
- ✅ Analytics workloads

**Don't use Avro if:**
- ❌ Building RPC services (use Protobuf/gRPC)
- ❌ Need code generation (Protobuf is better)
- ❌ Mobile apps (Protobuf is smaller)

## 💡 Key Takeaways

1. **Avro schemas are JSON** - Human-readable, easy to write
2. **Writer's schema vs reader's schema** - They can differ!
3. **Excellent evolution** - Adding/removing fields works smoothly
4. **Schema Registry** - Centralized schema management for Kafka
5. **Self-describing** - Schema can be stored with data
6. **Perfect for pipelines** - Great for data lakes and analytics
