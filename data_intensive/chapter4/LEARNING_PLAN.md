# Chapter 4: Encoding and Evolution - Deep Dive Learning Plan

This is your **step-by-step roadmap** to master Chapter 4 of "Designing Data-Intensive Applications".

---

## 📋 Overview

**Time commitment**: 10-14 days (2-3 hours per day)  
**Prerequisites**: Basic Python, understanding of data structures  
**Goal**: Master encoding formats, schema evolution, and dataflow patterns

---

## 🎯 Learning Objectives

By the end of this plan, you will:

1. ✅ Understand encoding formats (JSON, Protobuf, Avro, Thrift)
2. ✅ Master schema evolution and compatibility rules
3. ✅ Implement encoding/decoding in multiple formats
4. ✅ Build services with REST and gRPC
5. ✅ Handle schema evolution in databases and message queues
6. ✅ Choose the right format for different use cases

---

## 📅 Day-by-Day Plan

### **Day 1: Encoding Fundamentals**

**Concepts to learn:**
- What is encoding? (object → bytes → object)
- Text vs binary formats
- Performance implications
- Size comparison

**Hands-on task:**
Create `1_encoding_comparison/encoding_demo.py`:
- Define a complex data structure (nested dict with 10+ fields)
- Encode to: JSON, MessagePack, Pickle
- Compare: size (bytes), encoding time, decoding time
- Run with 1,000, 10,000, 100,000 records

**Deliverable:**
- Script that outputs comparison table
- Understanding: "Why binary formats exist"

**Time**: 2-3 hours

---

### **Day 2: JSON Deep Dive**

**Concepts to learn:**
- JSON encoding/decoding
- Number precision limits (2^53)
- Binary data handling (Base64)
- JSON Schema validation

**Hands-on task:**
Create `2_json_deep_dive/json_api.py`:
- Build Flask/FastAPI endpoint that accepts JSON
- Validate with JSON Schema
- Handle missing/extra fields
- Demonstrate number precision issues
- Handle Base64 encoded images

**Deliverable:**
- Working REST API with JSON
- Understanding: "JSON is readable but has limits"

**Time**: 2-3 hours

---

### **Day 3-4: Protocol Buffers**

**Concepts to learn:**
- `.proto` schema syntax
- Code generation (`protoc`)
- Field numbers and evolution
- Backward/forward compatibility

**Hands-on task:**
Create `3_protobuf/proto/` directory:

1. **Define schema** (`user.proto`):
   ```protobuf
   syntax = "proto3";
   
   message User {
     int32 id = 1;
     string name = 2;
     string email = 3;  // added in v2
   }
   ```

2. **Generate code**: `protoc --python_out=. user.proto`

3. **Implement** (`protobuf_demo.py`):
   - Serialize/deserialize User objects
   - Demonstrate backward compatibility (add field, old code works)
   - Demonstrate forward compatibility (remove field, new code handles it)
   - Compare size vs JSON

**Deliverable:**
- Working Protobuf implementation
- Understanding: "Protobuf enables safe schema evolution"

**Time**: 4-6 hours

---

### **Day 5-6: Apache Avro**

**Concepts to learn:**
- Avro schema (JSON format)
- Writer's schema vs reader's schema
- Schema resolution
- Schema Registry pattern

**Hands-on task:**
Create `4_avro/` directory:

1. **Define schemas**:
   - `user_v1.avsc` (id, name)
   - `user_v2.avsc` (id, name, email)

2. **Implement** (`avro_demo.py`):
   - Serialize with v1 schema
   - Deserialize with v2 schema (demonstrates evolution)
   - Show schema resolution in action
   - Compare with Protobuf

**Deliverable:**
- Working Avro implementation
- Understanding: "Avro excels at data pipelines"

**Time**: 4-6 hours

---

### **Day 7-8: Schema Evolution Mastery**

**Concepts to learn:**
- Adding fields (backward compatible)
- Removing fields (forward compatible)
- Renaming fields (tricky!)
- Changing types (requires migration)
- Field defaults

**Hands-on task:**
Create `5_schema_evolution/` directory:

1. **Create evolution sequence**:
   - Schema v1: `{id, name, age}`
   - Schema v2: `{id, name, age, email}` (add field)
   - Schema v3: `{id, name, email}` (remove age)
   - Schema v4: `{id, name, email, phone_number}` (rename email → phone_number)

2. **Implement compatibility tests** (`evolution_demo.py`):
   - Write data with v1, read with v2 (backward compatibility)
   - Write data with v2, read with v1 (forward compatibility)
   - Test all combinations
   - Document what works and what breaks

**Deliverable:**
- Comprehensive evolution demo
- Understanding: "Compatibility rules are strict but learnable"

**Time**: 4-6 hours

---

### **Day 9-10: Dataflow Through Databases**

**Concepts to learn:**
- How databases store encoded data
- SQL schema migrations
- Document databases and evolution
- Zero-downtime strategies

**Hands-on task:**
Create `6_database_evolution/` directory:

1. **SQL Database** (`sql_migration.py`):
   - Start with table: `users(id, name, email)`
   - Migration 1: Add `phone` (backward compatible)
   - Migration 2: Remove `age` (forward compatible - deprecate first)
   - Write code that handles old + new schemas

2. **Document Database** (`document_evolution.py`):
   - Use MongoDB or similar
   - Store documents with different schemas
   - Query that handles schema variations
   - Demonstrate evolution without migrations

**Deliverable:**
- Database evolution examples
- Understanding: "Databases need evolution strategies too"

**Time**: 4-6 hours

---

### **Day 11-12: Dataflow Through Services**

**Concepts to learn:**
- REST APIs: JSON over HTTP
- API versioning (URL, header, content negotiation)
- gRPC with Protobuf
- Service compatibility

**Hands-on task:**
Create `7_service_dataflow/` directory:

1. **REST Service** (`rest_api.py`):
   - Flask/FastAPI with JSON
   - Version via URL: `/v1/users`, `/v2/users`
   - Handle missing fields gracefully
   - Content negotiation

2. **gRPC Service** (`grpc_service/`):
   - Define `.proto` service
   - Generate server/client code
   - Implement service methods
   - Compare performance vs REST

**Deliverable:**
- Both REST and gRPC services
- Understanding: "REST vs RPC trade-offs"

**Time**: 6-8 hours

---

### **Day 13: Message-Passing Dataflow**

**Concepts to learn:**
- Message queues (Kafka, RabbitMQ)
- Producer/consumer independence
- Schema evolution in queues
- Schema Registry

**Hands-on task:**
Create `8_message_queue/` directory:

1. **Set up Kafka** (or use cloud service):
   - Install Kafka locally OR use Confluent Cloud

2. **Implement** (`kafka_evolution.py`):
   - Producer sends Avro messages with schema v1
   - Consumer reads with schema v2
   - Demonstrate: producer upgrades, old consumer still works
   - Use Schema Registry (Confluent) if possible

**Alternative**: Use RabbitMQ with JSON if Kafka is too complex

**Deliverable:**
- Working message queue with evolution
- Understanding: "Async dataflow needs evolution too"

**Time**: 4-6 hours

---

### **Day 14: Wrap-up and Decision Framework**

**Concepts to learn:**
- When to use JSON vs Protobuf vs Avro
- Decision criteria
- Real-world examples

**Hands-on task:**
Create `9_format_comparison/` directory:

1. **Build comparison matrix** (`comparison.md`):
   - Format | Readability | Performance | Evolution | Use Case
   - JSON | ⭐⭐⭐ | ⭐⭐ | ⭐ | Web APIs
   - Protobuf | ⭐ | ⭐⭐⭐ | ⭐⭐⭐ | RPC, Internal
   - Avro | ⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | Data Pipelines

2. **Create decision flowchart**:
   - Need human-readable? → JSON
   - Need performance? → Protobuf or Avro
   - Need best evolution? → Avro
   - Need RPC? → gRPC (Protobuf)

3. **Write summary** (`chapter4_summary.md`):
   - Key learnings
   - When to use what
   - Common pitfalls

**Deliverable:**
- Decision framework
- Personal cheat sheet
- Understanding: "I know when to use what"

**Time**: 2-3 hours

---

## 🛠️ Tools and Setup

### Required Tools

1. **Python 3.8+**
2. **Protocol Buffers**:
   ```bash
   pip install protobuf
   # Install protoc compiler (OS-specific)
   ```

3. **Avro**:
   ```bash
   pip install avro-python3
   ```

4. **MessagePack**:
   ```bash
   pip install msgpack
   ```

5. **Web Framework** (for REST):
   ```bash
   pip install flask  # or fastapi
   ```

6. **gRPC**:
   ```bash
   pip install grpcio grpcio-tools
   ```

7. **Kafka** (optional, for Day 13):
   ```bash
   pip install kafka-python
   # OR use Confluent Cloud (free tier)
   ```

### Project Structure

```
chapter4/
├── textbook.md (this file)
├── LEARNING_PLAN.md
├── 1_encoding_comparison/
│   └── encoding_demo.py
├── 2_json_deep_dive/
│   ├── json_api.py
│   └── user_schema.json
├── 3_protobuf/
│   ├── proto/
│   │   └── user.proto
│   └── protobuf_demo.py
├── 4_avro/
│   ├── user_v1.avsc
│   ├── user_v2.avsc
│   └── avro_demo.py
├── 5_schema_evolution/
│   └── evolution_demo.py
├── 6_database_evolution/
│   ├── sql_migration.py
│   └── document_evolution.py
├── 7_service_dataflow/
│   ├── rest_api.py
│   └── grpc_service/
├── 8_message_queue/
│   └── kafka_evolution.py
└── 9_format_comparison/
    ├── comparison.md
    └── chapter4_summary.md
```

---

## ✅ Progress Checklist

Track your progress:

- [ ] Day 1: Encoding comparison demo complete
- [ ] Day 2: JSON API working
- [ ] Day 3-4: Protobuf implementation complete
- [ ] Day 5-6: Avro implementation complete
- [ ] Day 7-8: Schema evolution tests passing
- [ ] Day 9-10: Database evolution examples working
- [ ] Day 11-12: REST and gRPC services running
- [ ] Day 13: Message queue demo working
- [ ] Day 14: Decision framework complete

---

## 🎓 Learning Resources

### Books
- "Designing Data-Intensive Applications" - Chapter 4 (primary source)

### Documentation
- [Protocol Buffers Guide](https://developers.google.com/protocol-buffers)
- [Avro Documentation](https://avro.apache.org/docs/current/)
- [gRPC Documentation](https://grpc.io/docs/)

### Tools
- [Protobuf Compiler](https://grpc.io/docs/protoc-installation/)
- [Confluent Schema Registry](https://docs.confluent.io/platform/current/schema-registry/index.html)

---

## 🚀 Quick Start

1. **Read** `textbook.md` for concepts
2. **Follow** this learning plan day by day
3. **Implement** each hands-on task
4. **Review** your code and understand the "why"

---

## 💡 Tips for Success

1. **Don't skip the hands-on tasks** - Theory without practice won't stick
2. **Compare formats side-by-side** - You'll see the trade-offs clearly
3. **Test compatibility scenarios** - This is the hardest part to master
4. **Build real examples** - Use cases you understand (users, orders, etc.)
5. **Document your learnings** - Write notes on what works and what doesn't

---

## 🎯 Mastery Check

You've mastered Chapter 4 when you can:

- ✅ Explain why binary formats exist
- ✅ Choose between JSON, Protobuf, and Avro for a given use case
- ✅ Design schemas that evolve safely
- ✅ Implement backward and forward compatibility
- ✅ Handle schema evolution in databases and services
- ✅ Build REST and gRPC services
- ✅ Understand message queue evolution patterns

---

**Ready to start? Begin with Day 1!** 🚀
