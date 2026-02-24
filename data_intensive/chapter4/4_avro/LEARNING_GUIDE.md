# Avro Learning Guide - Days 5-6

## 📚 Complete Learning Path

This guide will take you from Avro basics to schema evolution mastery.

---

## Part 1: Understanding Avro (30 minutes)

### What is Avro?

Apache Avro is a data serialization system that:
- Uses JSON for schema definitions (human-readable!)
- Stores schemas with data OR in a registry
- Enables excellent schema evolution
- Perfect for data pipelines and Kafka

### Why Avro?

**Advantages:**
- ✅ JSON schemas (easier than Protocol Buffers)
- ✅ Self-describing data (schema with data)
- ✅ Excellent schema evolution
- ✅ Perfect for data pipelines
- ✅ Used with Kafka Schema Registry

**When to use:**
- Data pipelines
- Kafka topics
- Data lakes
- Analytics workloads
- When schema evolution is critical

---

## Part 2: Avro Basics (1 hour)

### Step 1: Schema Definition

Avro schemas are JSON files (`.avsc`):

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
- `type: "record"` = object/struct
- `fields` = array of field definitions
- Each field has `name` and `type`

### Step 2: Encoding Data

```python
import avro.schema
import avro.io
from io import BytesIO

# Load schema
schema = avro.schema.parse(open("user.avsc").read())

# Create data
user_data = {"id": 1, "name": "Alice", "age": 30}

# Encode
writer = avro.io.DatumWriter(schema)
bytes_writer = BytesIO()
encoder = avro.io.BinaryEncoder(bytes_writer)
writer.write(user_data, encoder)
encoded = bytes_writer.getvalue()
```

### Step 3: Decoding Data

```python
# Decode
reader = avro.io.DatumReader(schema)
bytes_reader = BytesIO(encoded)
decoder = avro.io.BinaryDecoder(bytes_reader)
decoded = reader.read(decoder)
```

**Practice:** Run `avro_demo.py` to see this in action!

---

## Part 3: Writer's Schema vs Reader's Schema (1 hour)

### The Key Concept

**Writer's Schema**: Schema used when data was written  
**Reader's Schema**: Schema used when data is read

**They can be DIFFERENT!** This is Avro's superpower.

### Example

```python
# Write with v1 schema
writer_schema = load_schema("user_v1.avsc")  # {id, name, age}
data = encode(user_data, writer_schema)

# Read with v2 schema (different!)
reader_schema = load_schema("user_v2.avsc")  # {id, name, email}
user = decode(data, writer_schema, reader_schema)
```

**What happens:**
- `id` and `name` are read correctly (match in both schemas)
- `age` is ignored (not in reader schema)
- `email` gets default value (null)

**Result:** ✅ It works! Avro resolves differences automatically.

**Practice:** See `demonstrate_writer_reader_schemas()` in `avro_demo.py`

---

## Part 4: Schema Evolution (2 hours)

### Scenario 1: Adding Fields (Backward Compatible)

**v1 Schema:**
```json
{"fields": [{"name": "id", "type": "int"}, {"name": "name", "type": "string"}]}
```

**v2 Schema:**
```json
{"fields": [
  {"name": "id", "type": "int"},
  {"name": "name", "type": "string"},
  {"name": "email", "type": ["null", "string"], "default": null}
]}
```

**Test:**
- Write data with v1
- Read with v2
- Result: ✅ `email` gets default value (null)

**Rule:** New fields must have defaults!

### Scenario 2: Removing Fields (Forward Compatible)

**v1 Schema:** `{id, name, age}`  
**v2 Schema:** `{id, name}`

**Test:**
- Write data with v1 (has `age`)
- Read with v2 (no `age`)
- Result: ✅ `age` is ignored

**Rule:** Old code can ignore new fields

### Scenario 3: Renaming Fields (Using Aliases)

**v2 Schema:**
```json
{"name": "phone", "type": "string"}
```

**v3 Schema:**
```json
{"name": "phone_number", "type": "string", "aliases": ["phone"]}
```

**Test:**
- Write with v2 (field: `phone`)
- Read with v3 (field: `phone_number`)
- Result: ✅ Avro matches using alias

**Rule:** Use aliases to rename fields

### Practice Exercises

Run `evolution_practice.py` to practice all scenarios!

---

## Part 5: Type Compatibility (30 minutes)

### Compatible Changes ✅

- `int` → `long` (promotion)
- `float` → `double` (promotion)
- `string` → `bytes` (with UTF-8)
- `bytes` → `string` (with UTF-8)

### Incompatible Changes ❌

- `int` → `string` (different types)
- `string` → `int` (different types)
- Removing union null if data has nulls

### Unions for Optional Fields

```json
{"name": "email", "type": ["null", "string"], "default": null}
```

This means: `email` can be `null` OR `string`

---

## Part 6: Schema Registry Pattern (30 minutes)

### What is Schema Registry?

Central service that stores Avro schemas.

### How It Works

1. **Producer:**
   - Registers schema → gets schema ID (e.g., 42)
   - Serializes data with schema
   - Sends to Kafka: `{schema_id: 42, data: <binary>}`

2. **Consumer:**
   - Receives `{schema_id: 42, data: <binary>}`
   - Fetches schema from registry (ID 42)
   - OR uses own reader schema for evolution
   - Deserializes data

### Benefits

- ✅ Schema versioning
- ✅ Centralized management
- ✅ Smaller messages (ID instead of full schema)
- ✅ Compatibility checking

### Tools

- **Confluent Schema Registry** (most popular)
- Used with Kafka
- REST API for schema management

---

## Part 7: Comparison with Protocol Buffers (30 minutes)

### Key Differences

| Feature | Avro | Protobuf |
|---------|------|-----------|
| Schema Format | JSON | .proto |
| Schema Storage | With data or registry | Separate |
| Evolution | Excellent | Good |
| Self-describing | ✅ Yes | ❌ No |
| Use Case | Pipelines, Kafka | RPC, Services |
| Code Generation | Optional | Required |

### When to Choose

**Choose Avro if:**
- Building data pipelines
- Using Kafka
- Need self-describing data
- Schema evolution is critical

**Choose Protobuf if:**
- Building RPC services (gRPC)
- Need code generation
- Internal services
- Mobile apps

---

## 🎯 Learning Checklist

- [ ] Understand Avro schema syntax (JSON)
- [ ] Can encode/decode data with Avro
- [ ] Understand writer's schema vs reader's schema
- [ ] Know how to add fields (backward compatible)
- [ ] Know how to remove fields (forward compatible)
- [ ] Know how to rename fields (using aliases)
- [ ] Understand type compatibility rules
- [ ] Know Schema Registry pattern
- [ ] Can compare Avro with Protobuf
- [ ] Know when to use Avro

---

## 📝 Practice Exercises

1. **Modify Schemas:**
   - Add new fields to `user_v2.avsc`
   - Test backward compatibility
   - See how defaults work

2. **Test Type Changes:**
   - Try `int` → `long` (should work)
   - Try `int` → `string` (should fail)
   - Understand compatibility rules

3. **Create Nested Schemas:**
   - Add more nested records
   - Test evolution of nested structures

4. **Real-World Practice:**
   - Use your own data structures
   - Evolve schemas over time
   - Test compatibility

---

## 🚀 Next Steps

After mastering Avro:

1. ✅ You understand schema evolution
2. ✅ You know when to use Avro
3. ✅ Ready for Day 7-8: Advanced Schema Evolution

**Continue learning!** 🎓
