# Day 3-4: Protocol Buffers Deep Dive

## 🎯 Learning Objectives

By completing this exercise, you will:

1. Understand Protocol Buffers schema syntax (`.proto` files)
2. Generate code from `.proto` files using `protoc`
3. Encode and decode data with Protocol Buffers
4. Understand backward compatibility (new code reads old data)
5. Understand forward compatibility (old code reads new data)
6. Learn why field numbers are critical
7. Compare Protocol Buffers with JSON

## 📋 What You'll Build

1. **Schema Definition**: `.proto` file defining User message
2. **Code Generation**: Python code generated from schema
3. **Encoding/Decoding Demo**: Serialize and deserialize data
4. **Compatibility Tests**: Demonstrate schema evolution
5. **Performance Comparison**: Protobuf vs JSON

## 🚀 Setup

### Prerequisites

1. **Install Protocol Buffers Compiler**:

   **macOS:**
   ```bash
   brew install protobuf
   ```

   **Linux (Ubuntu/Debian):**
   ```bash
   sudo apt-get install protobuf-compiler
   ```

   **Windows:**
   - Download from: https://github.com/protocolbuffers/protobuf/releases
   - Or use: `choco install protoc`

2. **Install Python Library**:
   ```bash
   pip install protobuf
   ```

3. **Verify Installation**:
   ```bash
   protoc --version
   # Should show: libprotoc 3.x.x or similar
   ```

### Run the Demo

```bash
cd chapter4/3_protobuf
python3 protobuf_demo.py
```

The script will:
1. Check if `protoc` is available
2. Generate Python code from `.proto` file
3. Run encoding/decoding demonstrations
4. Show compatibility examples
5. Compare with JSON

## 📊 What You'll See

### 1. Protocol Buffers Basics

- Creating User objects
- Serializing to bytes
- Deserializing back to objects
- Size comparison with JSON

### 2. Backward Compatibility

**Scenario**: New code reads old data
- Old data: `{id: 1, name: "Alice"}` (no email)
- New schema: `{id, name, email}`
- Result: ✅ New code reads old data successfully

### 3. Forward Compatibility

**Scenario**: Old code reads new data
- New data: `{id: 1, name: "Alice", email: "alice@example.com"}`
- Old schema: `{id, name}` (doesn't know about email)
- Result: ✅ Old code reads new data (ignores unknown fields)

### 4. Field Numbers

Understanding why field numbers (1, 2, 3, etc.) are critical:
- They identify fields in binary data
- Never change them once used
- They enable compatibility

## 🎓 Key Concepts

### Schema Definition

```protobuf
syntax = "proto3";

message User {
  int32 id = 1;        // Field number 1
  string name = 2;     // Field number 2
  string email = 3;    // Field number 3
}
```

### Code Generation

```bash
protoc --python_out=. user.proto
```

This generates `user_pb2.py` with Python classes.

### Encoding/Decoding

```python
import user_pb2

# Create and encode
user = user_pb2.User()
user.id = 1
user.name = "Alice"
data = user.SerializeToString()

# Decode
user2 = user_pb2.User()
user2.ParseFromString(data)
```

### Schema Evolution Rules

✅ **Safe Changes:**
- Add new field with new field number
- Remove optional field (if old code ignores it)
- Change field name (field number stays same)

❌ **Breaking Changes:**
- Change field number
- Change field type (int32 → string)
- Remove required field

## 💡 Exercises to Try

1. **Modify the Schema**:
   - Add a new field to `user.proto`
   - Regenerate code
   - Test backward compatibility

2. **Test Forward Compatibility**:
   - Create data with new schema
   - Try to read with old code
   - See how unknown fields are handled

3. **Compare Sizes**:
   - Create large data structures
   - Compare Protobuf vs JSON sizes
   - Measure encoding/decoding speed

4. **Nested Messages**:
   - Add more nested messages
   - Test complex data structures

## 🔍 Understanding the Results

### Size Comparison

- **Protocol Buffers**: Smaller (no field names, binary encoding)
- **JSON**: Larger (field names included, text encoding)

Typical savings: 20-40% smaller

### Performance Comparison

- **Protocol Buffers**: Faster encoding/decoding
- **JSON**: Slower (string parsing, UTF-8 encoding)

Typical speedup: 2-5x faster

### Compatibility

- **Backward Compatible**: ✅ Easy (new code reads old data)
- **Forward Compatible**: ⚠️ Requires care (old code reads new data)

## ⚠️ Important Rules

1. **Never change field numbers** - This breaks compatibility!
2. **Never reuse field numbers** - Causes confusion
3. **Use new field numbers for new fields** - Enables evolution
4. **Mark removed fields as reserved** - Prevents accidental reuse

## 📚 Next Steps

After completing this exercise:

1. ✅ You understand Protocol Buffers basics
2. ✅ You know how schema evolution works
3. ✅ You understand compatibility rules
4. ✅ Ready for Day 5-6: Apache Avro

## 🐛 Troubleshooting

### "protoc: command not found"

Install Protocol Buffers compiler (see Setup section).

### "ModuleNotFoundError: No module named 'google.protobuf'"

```bash
pip install protobuf
```

### "ImportError: No module named 'user_pb2'"

The script should generate this automatically. If not:
```bash
cd chapter4/3_protobuf
protoc --python_out=. proto/user.proto
```

### Script shows conceptual demo only

This happens if `protoc` is not found. Install it to see full encoding/decoding.

## 📖 Additional Resources

- [Protocol Buffers Guide](https://developers.google.com/protocol-buffers/docs/overview)
- [Python Tutorial](https://developers.google.com/protocol-buffers/docs/pythontutorial)
- [Language Guide](https://developers.google.com/protocol-buffers/docs/proto3)
