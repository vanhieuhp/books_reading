# Chapter 11: Stream Processing

This is a comprehensive summary of **Chapter 11: Stream Processing** from *Designing Data-Intensive Applications* by Martin Kleppmann.

---

## Introduction: From Batch to Real-Time

Chapter 10 covered **batch processing**: taking a large, bounded dataset, running a computation on it, and producing a derived output. But batch jobs have inherent latency — you must wait for the entire dataset to be collected and the job to finish before seeing results.

**Stream processing** is the real-time counterpart: instead of waiting for a complete dataset, you process events **as they arrive**, one at a time (or in micro-batches), with low latency (milliseconds to seconds).

```
Batch Processing:
  [Dataset collected over 24 hours] → [Job runs for 2 hours] → [Results]
  Total latency: ~26 hours

Stream Processing:
  Event arrives → [Processed immediately] → [Result in milliseconds]
  Total latency: ~100ms
```

---

# 1. Transmitting Event Streams

## Events and Event Streams

In stream processing, the fundamental unit of data is an **event**: a small, immutable, timestamped record of something that happened.

* A user clicked a button (timestamp, user_id, button_id)
* A sensor reported a temperature (timestamp, sensor_id, value)
* A database row was updated (timestamp, table, old_value, new_value)

A **producer** (also called publisher or sender) generates events. A **consumer** (subscriber or recipient) processes them. Related events are typically grouped into a **topic** or **stream**.

## Messaging Systems

How do producers and consumers communicate? There are several patterns:

### Direct Point-to-Point Messaging
The producer sends events directly to the consumer over a TCP connection (e.g., Unix sockets, ZeroMQ, UDP multicast).
* **Pros:** Very low latency.
* **Cons:** If the consumer crashes or is too slow, events are lost. No durability.

### Message Brokers (Message Queues)
A dedicated server (the broker) receives events from producers, stores them, and delivers them to consumers.

```
Producer ──► [Message Broker] ──► Consumer A
                    │
                    └──────────► Consumer B
```

There are two fundamentally different philosophies:

#### Traditional Message Brokers (RabbitMQ, ActiveMQ)
* Messages are assigned to consumers, and once **acknowledged** (processed), they are **deleted** from the broker.
* If a consumer crashes before acknowledging, the message is redelivered to another consumer.
* **Message ordering** is NOT guaranteed when multiple consumers read from the same queue (because redeliveries may arrive out of order).
* Best for: **task queues** (distributing work across workers).

```
Queue model:
  Producer → [Queue: msg1, msg2, msg3] → Consumer A gets msg1
                                        → Consumer B gets msg2
                                        → Consumer A gets msg3
  Each message is processed by exactly ONE consumer.
  Messages are deleted after acknowledgment.
```

#### Log-Based Message Brokers (Apache Kafka, Amazon Kinesis)
* Events are appended to a **durable, ordered log** (like a replication log in a database).
* The log is **partitioned** for scalability, and each partition maintains strict ordering.
* Consumers read from the log at their own pace by maintaining an **offset** (a position in the log).
* Messages are **NOT deleted** after being read. They remain in the log for a configurable retention period (e.g., 7 days, or forever).
* Multiple consumers can read the same log independently (each with their own offset).

```
Kafka Topic (3 partitions):
  Partition 0: [msg0, msg3, msg6, msg9, ...]   ← Consumer Group A, offset=4
  Partition 1: [msg1, msg4, msg7, msg10, ...]  ← Consumer Group A, offset=3
  Partition 2: [msg2, msg5, msg8, msg11, ...]  ← Consumer Group A, offset=5

  Consumer Group B reads the same partitions independently:
  Partition 0: offset=2 (lagging behind Group A)
```

### Why Kafka Changed Everything
The log-based approach has massive advantages over traditional brokers:

1. **Replay:** A consumer can re-read old messages by resetting its offset. This is impossible with RabbitMQ (messages are deleted). Replay enables fixing bugs, rebuilding derived data, or auditing.
2. **Multiple consumers:** Each consumer group has an independent offset. Adding a new consumer doesn't affect existing ones. (With RabbitMQ, adding a consumer splits the messages.)
3. **Ordering:** Within a partition, messages are strictly ordered. This is crucial for database change events (you must apply INSERT before UPDATE).
4. **Durability:** Messages are written to disk and replicated. Even if the broker crashes, data is safe.
5. **Backpressure:** If a consumer is slow, it just falls behind on its offset. The broker doesn't need to drop messages or block the producer.

---

# 2. Databases and Streams

Kleppmann makes a profound observation: **a database's replication log IS a stream of events.** Every INSERT, UPDATE, and DELETE that happens in a database is an event that changes the state of the data.

## Change Data Capture (CDC)

**Change Data Capture** means capturing every write to a database and making it available as a stream of events.

```
Application writes → [PostgreSQL] → WAL (Write-Ahead Log)
                                          │
                                          ▼
                              [CDC Connector (e.g., Debezium)]
                                          │
                                          ▼
                                    [Kafka Topic]
                                     │         │
                                     ▼         ▼
                               [Search Index] [Cache]
                               (Elasticsearch) (Redis)
```

### Why CDC is Transformative
* **Derived data stays in sync:** Your Elasticsearch index, Redis cache, and analytics warehouse are all derived from the same stream of database changes. They are **eventually consistent** with the source database.
* **No dual-write problem:** Without CDC, applications often write to both the database AND the cache/index (dual write). If one write succeeds and the other fails (or the order is wrong), data becomes inconsistent. CDC eliminates this by having a single source of truth (the database), with everything else derived from its change stream.
* **Decoupling:** Downstream consumers don't need to know about the application's database schema or queries. They just subscribe to the change stream.

### CDC Tools
| Tool | Source Database |
|------|----------------|
| Debezium | PostgreSQL, MySQL, MongoDB, SQL Server |
| Maxwell | MySQL |
| Bottled Water | PostgreSQL |
| DynamoDB Streams | DynamoDB |
| MongoDB Change Streams | MongoDB |

## Event Sourcing

**Event Sourcing** is a design pattern (from the Domain-Driven Design community) that is closely related to CDC but takes the idea further.

Instead of storing the **current state** of the data (like a traditional database), you store the **immutable log of all events** that ever happened.

```
Traditional database (stores current state):
  Orders table: { id: 42, status: 'shipped', total: $100 }

Event Sourcing (stores the full history):
  Event 1: OrderCreated   { id: 42, total: $100 }
  Event 2: PaymentReceived { id: 42, amount: $100 }
  Event 3: OrderShipped    { id: 42, carrier: "FedEx" }
```

The current state is derived by **replaying** all events from the beginning. You can always rebuild the state from scratch, or build entirely new views from the same event log.

### Key Differences: CDC vs Event Sourcing
| Aspect | CDC | Event Sourcing |
|--------|-----|---------------|
| Source | Database WAL (low-level) | Application events (domain-level) |
| Granularity | Row changes (INSERT/UPDATE/DELETE) | Business events (OrderPlaced, PaymentReceived) |
| Intent | Extract data from existing DB | Primary storage model is the event log |
| Immutability | WAL is typically compacted/truncated | Event log is the permanent source of truth |

## Log Compaction
Event logs can grow unboundedly. **Log compaction** (used by Kafka) keeps only the **latest value** for each key, discarding older versions. This is similar to how an LSM-tree (Chapter 3) compacts its SSTables.

```
Before Compaction:
  user_42: created → user_42: updated email → user_42: updated name → user_42: deleted

After Compaction:
  user_42: deleted (only the latest event for this key is kept)
```

This allows a new consumer to "catch up" by reading the compacted log rather than replaying the entire history.

---

# 3. Processing Streams

Once you have a stream of events, what can you do with it?

1. **Write to a database, cache, or search index** (derived data).
2. **Push to users** (email, notification, real-time dashboard).
3. **Process and produce another stream** (stream transformation).

## Uses of Stream Processing

### Complex Event Processing (CEP)
Searching for specific patterns in a stream of events. Like a regular expression, but for events over time.
* "Alert me if a user makes 3 failed login attempts within 5 minutes."
* "Detect a sequence: temperature > 100°C, followed by pressure drop, within 10 seconds."

### Stream Analytics
Continuous aggregation over time windows:
* "What is the 99th percentile response time over the last 5 minutes?"
* "How many events per second are we processing?"

### Materialized Views on Streams
Maintaining a read-optimized view (like a database table or search index) that is kept up-to-date by processing the event stream. Every INSERT, UPDATE, DELETE in the stream is applied to the materialized view.

### Search on Streams
The inverse of a database query: instead of running a query against stored data, you store the query (a set of search criteria) and run every event against it. Events that match are delivered to the subscriber.

---

# 4. Time and Windows

Time is the biggest source of complexity in stream processing. When an event says `timestamp: 10:00:05`, does that mean:
* **Event time:** When the event actually occurred (according to the device that generated it).
* **Processing time:** When the stream processor received and processed the event.

These can differ significantly (a mobile device might buffer events for minutes before sending them). **Correct stream processing uses event time**, but this introduces a problem: events can arrive **out of order** or **late**.

## Types of Windows

### Tumbling Window (Fixed)
Non-overlapping, fixed-size time intervals.
```
|-----1min-----|-----1min-----|-----1min-----|
  events here    events here    events here
```

### Hopping Window (Overlapping)
Fixed-size windows that slide by a fixed interval.
```
|-----5min window-----|
    |-----5min window-----|
        |-----5min window-----|
  (hop = 1 min, window = 5 min)
```

### Sliding Window
A window that captures all events within a fixed duration of each other. Unlike hopping, sliding windows don't have fixed boundaries — they're defined relative to each event.

### Session Window
A dynamically sized window that groups all events from the same user that occur close together in time. A session ends after a period of inactivity (e.g., 30 minutes of no events).
```
User A: [click, click, click, ──30min gap──, click, click]
         └──── Session 1 ────┘                └ Session 2 ┘
```

---

# 5. Stream Joins

Joining streams is harder than joining in batch because the data is unbounded and arrives continuously.

### Stream-Stream Join (Window Join)
Join two event streams based on a time window. Example: match an ad impression event with a subsequent ad click event for the same user, within 1 hour.
* The processor must buffer events from both streams (e.g., indexed by user_id), and produce a match when corresponding events arrive.

### Stream-Table Join (Enrichment)
Enrich a stream event with data from a database. Example: for each order event, look up the customer's name and address.
* The processor can either query the database for each event (slow) or maintain a **local copy** of the database table (fast), kept up-to-date via CDC.

### Table-Table Join (Materialized View Maintenance)
Both inputs are CDC streams from database tables. The processor maintains a materialized view that joins the two tables and updates the view whenever either table changes.
* Example: a "timeline cache" on a social network. When a user posts, the post is added to all followers' timelines. When a user unfollows, their timeline is updated.

---

# 6. Fault Tolerance in Stream Processing

Batch processing achieves fault tolerance by rerunning failed jobs (inputs are immutable files on HDFS). Stream processing is trickier because the input is an infinite, continuous stream.

### Microbatching (Spark Streaming)
Break the stream into small batches (e.g., 1 second each). Each micro-batch is processed as a batch job. If a batch fails, rerun it.
* **Pros:** Reuses batch processing fault tolerance.
* **Cons:** Minimum latency equals the batch interval (e.g., 1 second).

### Checkpointing (Flink)
Periodically snapshot the state of all stream operators.
* If a failure occurs, restore from the last checkpoint and replay events from that point.
* Apache Flink uses the **Chandy-Lamport** distributed snapshot algorithm.

### Exactly-Once Semantics
The holy grail: every event is processed exactly once, even after failures.
* **At-least-once:** Easy (just retry). But may cause duplicates.
* **At-most-once:** Easy (don't retry). But may lose events.
* **Exactly-once:** Hard. Requires idempotent operations or transactional output.

Kafka Streams and Flink achieve exactly-once by combining:
1. Transactional writes to Kafka (atomically commit offsets and output messages).
2. Idempotent producers (deduplication using sequence numbers).

---

# Summary Cheat Sheet

```
┌────────────────────┬──────────────────────────────────────────────┐
│ Concept            │ Key Idea                                     │
├────────────────────┼──────────────────────────────────────────────┤
│ Event              │ An immutable, timestamped record of a fact   │
│ Log-Based Broker   │ Ordered, durable, replayable (Kafka)         │
│ Traditional Broker │ Message deleted after consumption (RabbitMQ) │
│ CDC                │ Database changes as a stream                 │
│ Event Sourcing     │ Store events, derive state                   │
│ Stream Join        │ Join unbounded data: stream-stream,          │
│                    │ stream-table, table-table                    │
│ Windowing          │ Tumbling, hopping, sliding, session          │
│ Exactly-Once       │ Transactional + idempotent processing        │
└────────────────────┴──────────────────────────────────────────────┘
```

---

# Key Terminology

* **Event:** An immutable record of something that happened.
* **Topic / Stream:** A named collection of related events.
* **Producer / Consumer:** An event sender / receiver.
* **Offset:** A consumer's position in a log-based stream.
* **Message Broker:** A server that routes events from producers to consumers.
* **CDC (Change Data Capture):** Extracting database changes as a stream of events.
* **Event Sourcing:** Storing the full history of events as the primary data model.
* **Log Compaction:** Keeping only the latest event per key in a Kafka topic.
* **Event Time vs Processing Time:** When an event happened vs when it was processed.
* **Tumbling Window:** Non-overlapping fixed-size time intervals.
* **Session Window:** Dynamic window based on user activity gaps.
* **Exactly-Once:** Every event is processed exactly once despite failures (requires idempotency or transactions).
* **Microbatching:** Treating a stream as a sequence of small batches (Spark Streaming).
* **Checkpointing:** Periodically saving operator state for fault recovery (Flink).

---

# Interview-Level Questions

1. **What is the fundamental difference between Kafka and RabbitMQ?**
   → Kafka is a log-based broker: messages are appended to an ordered log, retained durably, and can be replayed. RabbitMQ is a traditional broker: messages are deleted after acknowledgment, and cannot be replayed. Kafka is designed for event streaming; RabbitMQ for task distribution.

2. **What is Change Data Capture (CDC) and why is it important?**
   → CDC captures every write to a database as a stream of events. It eliminates the dual-write problem (writing to both DB and cache/index), keeps derived systems (Elasticsearch, Redis) in sync, and decouples producers from consumers.

3. **Explain the difference between event time and processing time.**
   → Event time is when the event actually occurred (set by the source device). Processing time is when the stream processor received it. They differ due to network delays, buffering, and out-of-order arrival. Correct windowing must use event time, but must handle late arrivals.

4. **What are the three types of stream joins?**
   → (1) Stream-Stream (window join): correlate events from two streams within a time window. (2) Stream-Table (enrichment): look up reference data for each event. (3) Table-Table (materialized view): maintain a join of two tables using their CDC streams.

5. **How does Kafka achieve exactly-once semantics?**
   → Idempotent producers (deduplicate using sequence numbers per partition) + transactional writes (atomically commit consumer offsets and output messages in a single Kafka transaction). Combined, these ensure each event is effectively processed exactly once.

6. **What is Event Sourcing and how does it differ from a traditional database?**
   → Event Sourcing stores the full history of domain events (OrderCreated, PaymentReceived) as the primary data model. Current state is derived by replaying events. A traditional database stores only the current state, overwriting previous values. Event Sourcing provides a complete audit trail and the ability to rebuild any view from scratch.
