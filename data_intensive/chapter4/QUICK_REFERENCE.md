# Chapter 4: Quick Reference Guide

A cheat sheet for encoding formats, compatibility rules, and decision-making.

---

## 📊 Format Comparison Matrix

| Format | Readability | Performance | Schema | Evolution | Best For |
|--------|-------------|-------------|--------|-----------|----------|
| **JSON** | ⭐⭐⭐ | ⭐⭐ | ❌ | ⭐ | Web APIs, human-readable data |
| **Protocol Buffers** | ⭐ | ⭐⭐⭐ | ✅ | ⭐⭐⭐ | RPC, internal services, performance |
| **Avro** | ⭐ | ⭐⭐⭐ | ✅ | ⭐⭐⭐⭐ | Data pipelines, data lakes, Kafka |
| **Thrift** | ⭐ | ⭐⭐⭐ | ✅ | ⭐⭐⭐ | RPC, cross-language services |
| **MessagePack** | ⭐ | ⭐⭐ | ❌ | ⭐ | Compact JSON alternative |

---

## 🔄 Compatibility Rules

### ✅ Safe Changes (Backward Compatible)

- **Add optional field** (with default value)
- **Remove optional field** (if old code ignores it)
- **Add new enum value** (if old code handles unknown)

### ⚠️ Risky Changes (Requires Migration)

- **Remove required field** → Make optional first, then remove
- **Change field type** → Requires data transformation
- **Rename field** → Use aliases if format supports it
- **Change field number** (Protobuf/Thrift) → Never do this!

### 🚫 Breaking Changes (Incompatible)

- **Remove field without default**
- **Change required to optional** (old code expects it)
- **Change field number** (Protobuf/Thrift)

---

## 📝 Protocol Buffers Quick Reference

### Schema Definition

```protobuf
syntax = "proto3";

message User {
  int32 id = 1;              // Field number (never change!)
  string name = 2;
  string email = 3;           // Optional by default in proto3
  repeated string tags = 4;   // Array/list
}
```

### Python Usage

```python
# Generate code: protoc --python_out=. user.proto
import user_pb2

# Create
user = user_pb2.User()
user.id = 1
user.name = "Alice"

# Serialize
data = user.SerializeToString()

# Deserialize
user2 = user_pb2.User()
user2.ParseFromString(data)
```

### Evolution Rules

- ✅ Add new field with new number
- ✅ Remove optional field
- ❌ Never change field numbers
- ❌ Never reuse field numbers

---

## 📝 Avro Quick Reference

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

### Python Usage

```python
import avro.schema
import avro.io
import io

# Load schema
schema = avro.schema.parse(open("user.avsc").read())

# Serialize
writer = avro.io.DatumWriter(schema)
bytes_writer = io.BytesIO()
encoder = avro.io.BinaryEncoder(bytes_writer)
writer.write({"id": 1, "name": "Alice"}, encoder)
data = bytes_writer.getvalue()

# Deserialize (can use different schema!)
reader_schema = avro.schema.parse(open("user_v2.avsc").read())
reader = avro.io.DatumReader(writer_schema=schema, reader_schema=reader_schema)
decoder = avro.io.BinaryDecoder(io.BytesIO(data))
user = reader.read(decoder)
```

### Evolution Rules

- ✅ Add field with default
- ✅ Remove field (reader ignores)
- ✅ Change field type (if compatible)
- ✅ Rename field (use aliases)

---

## 🌐 JSON Quick Reference

### Basic Usage

```python
import json

# Serialize
data = json.dumps({"id": 1, "name": "Alice"})

# Deserialize
obj = json.loads(data)
```

### JSON Schema Validation

```python
import jsonschema

schema = {
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "name": {"type": "string"}
    },
    "required": ["id", "name"]
}

jsonschema.validate(instance={"id": 1, "name": "Alice"}, schema=schema)
```

### Limitations

- Number precision: 2^53 limit
- No binary data (use Base64)
- No schema (use JSON Schema separately)
- Verbose (larger than binary)

---

## 🔌 gRPC Quick Reference

### Service Definition

```protobuf
syntax = "proto3";

service UserService {
  rpc GetUser (GetUserRequest) returns (User);
  rpc CreateUser (CreateUserRequest) returns (User);
}

message GetUserRequest {
  int32 id = 1;
}
```

### Generate Code

```bash
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. user.proto
```

### Server (Python)

```python
import grpc
from concurrent import futures
import user_pb2
import user_pb2_grpc

class UserService(user_pb2_grpc.UserServiceServicer):
    def GetUser(self, request, context):
        return user_pb2.User(id=request.id, name="Alice")

server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
user_pb2_grpc.add_UserServiceServicer_to_server(UserService(), server)
server.add_insecure_port('[::]:50051')
server.start()
```

### Client (Python)

```python
import grpc
import user_pb2
import user_pb2_grpc

channel = grpc.insecure_channel('localhost:50051')
stub = user_pb2_grpc.UserServiceStub(channel)
response = stub.GetUser(user_pb2.GetUserRequest(id=1))
```

---

## 🗄️ Database Evolution Patterns

### SQL Migration (Backward Compatible)

```sql
-- Add optional column
ALTER TABLE users ADD COLUMN phone VARCHAR(20) NULL;

-- Remove column (two-step: deprecate, then remove)
-- Step 1: Stop writing to column
-- Step 2: After all old code updated, drop column
ALTER TABLE users DROP COLUMN age;
```

### Document Database (Schema-less)

```python
# MongoDB example - different schemas coexist
db.users.insert_one({"id": 1, "name": "Alice"})  # v1
db.users.insert_one({"id": 2, "name": "Bob", "email": "bob@example.com"})  # v2

# Query handles both
for user in db.users.find():
    # Handle missing fields gracefully
    email = user.get("email", "no-email")
```

---

## 📨 Message Queue Evolution

### Kafka with Avro

```python
from confluent_kafka import Producer, Consumer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer, AvroDeserializer

# Producer (schema v1)
schema_registry = SchemaRegistryClient({'url': 'http://localhost:8081'})
avro_serializer = AvroSerializer(schema_registry, schema_v1)
producer = Producer({'bootstrap.servers': 'localhost:9092'})
producer.produce('users', value=avro_serializer(user_data, schema_v1))

# Consumer (schema v2 - can read v1 data!)
avro_deserializer = AvroDeserializer(schema_registry, schema_v2)
consumer = Consumer({'bootstrap.servers': 'localhost:9092', 'group.id': 'mygroup'})
# Consumer automatically resolves schema differences
```

---

## 🎯 Decision Framework

### When to Use JSON?

- ✅ Web APIs (human-readable)
- ✅ Configuration files
- ✅ Logging
- ✅ When readability > performance

### When to Use Protocol Buffers?

- ✅ Internal services (performance critical)
- ✅ gRPC services
- ✅ Mobile apps (small payloads)
- ✅ When you need strong typing

### When to Use Avro?

- ✅ Data pipelines
- ✅ Kafka topics
- ✅ Data lakes
- ✅ When schema evolution is critical
- ✅ When you need schema registry

### When to Use Thrift?

- ✅ Cross-language RPC
- ✅ When you need RPC framework included
- ✅ Facebook-style architectures

---

## 🚨 Common Pitfalls

1. **Using pickle for cross-service communication** → Security risk!
2. **Changing Protobuf field numbers** → Breaks compatibility!
3. **Removing required fields without migration** → Breaks old code!
4. **No schema versioning strategy** → Chaos!
5. **Assuming all clients upgrade together** → Never happens!

---

## 📚 Key Takeaways

1. **Schema-based formats** (Protobuf, Avro) enable safe evolution
2. **Field numbers/tags** are critical - never change them
3. **Backward compatibility** is easier than forward compatibility
4. **JSON is readable** but binary formats are faster
5. **Avro excels** at data pipelines with evolution
6. **Protobuf excels** at RPC and internal services
7. **Always plan** for schema evolution from the start

---

## 🔗 Useful Commands

```bash
# Generate Protobuf code
protoc --python_out=. user.proto

# Generate gRPC code
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. user.proto

# Validate Avro schema
python -c "import avro.schema; avro.schema.parse(open('user.avsc').read())"

# Install dependencies
pip install -r requirements.txt
```

---

**Keep this reference handy as you work through the exercises!**
