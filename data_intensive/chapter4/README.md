# Chapter 4: Encoding and Evolution

This directory contains learning materials and practical exercises for **Chapter 4** of "Designing Data-Intensive Applications" by Martin Kleppmann.

## 📚 Contents

- **[textbook.md](./textbook.md)** - Comprehensive textbook-style explanation of Chapter 4 concepts
- **[LEARNING_PLAN.md](./LEARNING_PLAN.md)** - Detailed 10-14 day learning plan with hands-on tasks

## 🎯 What You'll Learn

1. **Encoding Formats**: JSON, Protocol Buffers, Avro, Thrift
2. **Schema Evolution**: How to change schemas without breaking systems
3. **Compatibility**: Backward and forward compatibility patterns
4. **Dataflow Patterns**: Databases, REST APIs, gRPC, message queues

## 🚀 Quick Start

1. Read `textbook.md` for conceptual understanding
2. Follow `LEARNING_PLAN.md` for structured practice
3. Implement the hands-on exercises day by day

## 📁 Project Structure

```
chapter4/
├── textbook.md           # Concepts and theory
├── LEARNING_PLAN.md      # Step-by-step learning plan
├── README.md            # This file
└── [exercise directories will be created as you progress]
```

## 🔑 Key Concepts

### Encoding Formats

- **JSON**: Human-readable, web standard, no schema
- **Protocol Buffers**: Binary, schema-based, Google's format
- **Avro**: Binary, schema-based, best for evolution
- **Thrift**: Similar to Protobuf, includes RPC

### Compatibility

- **Backward Compatible**: New code reads old data ✅
- **Forward Compatible**: Old code reads new data ⚠️

### Dataflow Modes

- **Databases**: Schema evolution in stored data
- **Services**: REST (JSON) and RPC (Protobuf/gRPC)
- **Message Queues**: Async dataflow with schema evolution

## 📖 Learning Path

1. **Days 1-2**: Encoding fundamentals and JSON
2. **Days 3-6**: Protocol Buffers and Avro
3. **Days 7-8**: Schema evolution mastery
4. **Days 9-10**: Database evolution
5. **Days 11-12**: Service dataflow (REST & gRPC)
6. **Day 13**: Message queue patterns
7. **Day 14**: Wrap-up and decision framework

## 🛠️ Prerequisites

- Python 3.8+
- Basic understanding of data structures
- Familiarity with APIs (helpful but not required)

## 📝 Exercises

As you progress through the learning plan, you'll create:

- Encoding comparison demos
- JSON API implementations
- Protocol Buffers examples
- Avro schema evolution demos
- Database migration examples
- REST and gRPC services
- Message queue evolution patterns

## 🎓 Resources

- **Primary**: "Designing Data-Intensive Applications" - Chapter 4
- **Protocol Buffers**: https://developers.google.com/protocol-buffers
- **Avro**: https://avro.apache.org/docs/current/
- **gRPC**: https://grpc.io/docs/

## 💡 Tips

- Don't skip the hands-on exercises
- Compare formats side-by-side to see trade-offs
- Test compatibility scenarios thoroughly
- Document your learnings as you go

---

**Start with `textbook.md` to understand the concepts, then follow `LEARNING_PLAN.md` for hands-on practice!**
