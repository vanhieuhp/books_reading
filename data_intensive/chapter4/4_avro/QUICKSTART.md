# Avro Quick Start

## 🚀 Get Started in 3 Steps

### Step 1: Install Avro

```bash
pip install avro-python3
```

**Important**: Use `avro-python3`, not `avro` (they're different packages)

### Step 2: Run the Demo

```bash
cd chapter4/4_avro
python3 avro_demo.py
```

### Step 3: Practice

```bash
python3 evolution_practice.py
```

## 📊 What You'll Learn

1. **Avro Schema Syntax**: JSON-based schema definition
2. **Encoding/Decoding**: Serialize and deserialize data
3. **Schema Evolution**: Writer's schema vs reader's schema
4. **Compatibility**: How Avro handles schema changes

## 🎯 Key Concepts

### Schema Definition (JSON)

```json
{
  "type": "record",
  "name": "User",
  "fields": [
    {"name": "id", "type": "int"},
    {"name": "name", "type": "string"},
    {"name": "email", "type": ["null", "string"], "default": null}
  ]
}
```

### Encoding/Decoding

```python
import avro.schema
import avro.io
from io import BytesIO

# Load schema
schema = avro.schema.parse(open("user.avsc").read())

# Encode
writer = avro.io.DatumWriter(schema)
bytes_writer = BytesIO()
encoder = avro.io.BinaryEncoder(bytes_writer)
writer.write({"id": 1, "name": "Alice"}, encoder)
data = bytes_writer.getvalue()

# Decode
reader = avro.io.DatumReader(schema)
bytes_reader = BytesIO(data)
decoder = avro.io.BinaryDecoder(bytes_reader)
user = reader.read(decoder)
```

### Writer's Schema vs Reader's Schema

**This is Avro's superpower!**

```python
# Write with v1 schema
writer_schema = load_schema("user_v1.avsc")  # {id, name, age}
data = encode(user_data, writer_schema)

# Read with v2 schema (different!)
reader_schema = load_schema("user_v2.avsc")  # {id, name, email}
user = decode(data, writer_schema, reader_schema)
# ✅ Works! Avro resolves differences automatically
```

## 💡 Quick Examples

### Adding a Field

```python
# v1: {id, name}
# v2: {id, name, email}

# Write with v1
data = encode({"id": 1, "name": "Alice"}, schema_v1)

# Read with v2
user = decode(data, schema_v1, schema_v2)
# Result: {"id": 1, "name": "Alice", "email": null}
# ✅ email gets default value
```

### Removing a Field

```python
# v1: {id, name, age}
# v2: {id, name}

# Write with v1
data = encode({"id": 1, "name": "Alice", "age": 30}, schema_v1)

# Read with v2
user = decode(data, schema_v1, schema_v2)
# Result: {"id": 1, "name": "Alice"}
# ✅ age is ignored
```

### Renaming a Field (Aliases)

```json
// v2 schema
{"name": "phone", "type": "string"}

// v3 schema
{"name": "phone_number", "type": "string", "aliases": ["phone"]}
```

Avro uses the alias to match fields!

## ⚠️ Important Rules

1. **New fields need defaults**
   ```json
   {"name": "email", "type": ["null", "string"], "default": null}
   ```

2. **Type changes must be compatible**
   - `int` → `long` ✅
   - `int` → `string` ❌

3. **Use unions for optional fields**
   ```json
   {"name": "email", "type": ["null", "string"], "default": null}
   ```

## 🎯 Avro vs Protocol Buffers

| Feature | Avro | Protobuf |
|---------|------|----------|
| Schema Format | JSON | .proto |
| Schema Storage | With data or registry | Separate |
| Evolution | Excellent | Good |
| Use Case | Pipelines, Kafka | RPC, Services |
| Self-describing | ✅ Yes | ❌ No |

## 🐛 Troubleshooting

### "No module named 'avro'"

```bash
pip install avro-python3
```

### "SchemaParseException"

- Check JSON syntax
- Ensure required fields: `type`, `name`, `fields`
- Validate field types

### Type errors

- Use unions for nullable: `["null", "string"]`
- Check type compatibility
- Defaults required for new fields

## 📚 Next Steps

After completing:

1. ✅ Understand Avro basics
2. ✅ Know schema evolution
3. ✅ Ready for advanced evolution (Day 7-8)

**Ready?** Run the demos and practice!
