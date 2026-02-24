# Protocol Buffers Quick Start

## 🚀 Get Started in 3 Steps

### Step 1: Install Protocol Buffers Compiler

**macOS:**
```bash
brew install protobuf
```

**Linux:**
```bash
sudo apt-get install protobuf-compiler
```

**Verify:**
```bash
protoc --version
```

### Step 2: Install Python Library

```bash
pip3 install protobuf
```

### Step 3: Run the Demo

```bash
cd chapter4/3_protobuf
python3 protobuf_demo.py
```

Or use the setup script:
```bash
./setup.sh
python3 protobuf_demo.py
```

## 📊 What You'll Learn

1. **Schema Definition**: How to write `.proto` files
2. **Code Generation**: How `protoc` generates Python code
3. **Encoding**: How to serialize objects to bytes
4. **Decoding**: How to deserialize bytes to objects
5. **Compatibility**: How schema evolution works

## 🎯 Key Concepts

### Field Numbers Are Critical

```protobuf
message User {
  int32 id = 1;      // Field number 1 - NEVER change this!
  string name = 2;   // Field number 2 - NEVER change this!
  string email = 3;  // Field number 3 - NEW field, new number
}
```

**Why?** Field numbers identify fields in binary data. Changing them breaks compatibility!

### Backward Compatibility

✅ **New code reads old data**
- Old data: `{id: 1, name: "Alice"}` (no email)
- New schema: `{id, name, email}`
- Result: Works! Email is empty/default

### Forward Compatibility

✅ **Old code reads new data**
- New data: `{id: 1, name: "Alice", email: "alice@example.com"}`
- Old schema: `{id, name}` (doesn't know email)
- Result: Works! Old code ignores unknown email field

## 💡 Quick Examples

### Create and Encode

```python
import user_pb2

user = user_pb2.User()
user.id = 1
user.name = "Alice"
user.email = "alice@example.com"

# Serialize to bytes
data = user.SerializeToString()
```

### Decode

```python
user2 = user_pb2.User()
user2.ParseFromString(data)
print(user2.name)  # "Alice"
```

### Size Comparison

```python
# Protobuf: ~50 bytes
# JSON: ~80 bytes
# Savings: ~37%
```

## ⚠️ Common Mistakes

1. **Changing field numbers** ❌
   ```protobuf
   // WRONG - breaks compatibility!
   message User {
     int32 id = 2;  // Changed from 1 to 2
   }
   ```

2. **Reusing field numbers** ❌
   ```protobuf
   // WRONG - causes confusion!
   message User {
     int32 id = 1;
     string name = 1;  // Reused number 1
   }
   ```

3. **Changing field types** ❌
   ```protobuf
   // WRONG - breaks compatibility!
   message User {
     string id = 1;  // Changed from int32 to string
   }
   ```

## ✅ Best Practices

1. **Add new fields with new numbers** ✅
2. **Keep old field numbers unchanged** ✅
3. **Mark removed fields as reserved** ✅
4. **Use descriptive field names** ✅
5. **Document schema changes** ✅

## 🐛 Troubleshooting

### "protoc: command not found"

Install it (see Step 1 above).

### "No module named 'user_pb2'"

The script generates this automatically. If it doesn't:
```bash
protoc --python_out=. proto/user.proto
```

### Script shows "conceptual demo"

This means `protoc` isn't installed. Install it to see full encoding/decoding.

## 📚 Next Steps

After completing this:

1. ✅ Understand Protocol Buffers
2. ✅ Know schema evolution rules
3. ✅ Ready for Avro (Day 5-6)

**Ready?** Run the demo and explore!
