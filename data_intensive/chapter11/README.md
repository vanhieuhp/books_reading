# Chapter 11: Stream Processing - SQL Exercises

Welcome to the hands-on SQL exercises for learning **Chapter 11: Stream Processing** from *Designing Data-Intensive Applications*.

---

## 📚 Chapter Overview

This chapter covers:
1. **Event Streams** - Producers, consumers, messaging patterns
2. **Databases and Streams** - CDC, Event Sourcing, Log Compaction
3. **Processing Streams** - Analytics, aggregations, materialized views
4. **Time and Windows** - Tumbling, Hopping, Sliding, Session windows
5. **Stream Joins** - Stream-stream, Stream-table, Table-table joins
6. **Fault Tolerance** - Exactly-once, idempotent processing, checkpoints

---

## 📁 File Structure

```
chapter11/
├── 01_event_streams.sql        # Events, producers, consumers, offsets, CDC
├── 02_cdc_event_sourcing.sql   # CDC patterns, Event Sourcing, log compaction
├── 03_processing_streams.sql  # Aggregations, analytics, materialized views
├── 04_time_windows.sql         # Tumbling, Hopping, Sliding, Session windows
├── 05_stream_joins.sql         # Stream-stream, Stream-table, Table-table joins
├── 06_fault_tolerance.sql      # Exactly-once, idempotent patterns, checkpoints
└── README.md                   # This file
```

---

## 🚀 Getting Started

### Prerequisites
- PostgreSQL 12+ installed
- psql or any PostgreSQL client (pgAdmin, DBeaver, etc.)

### Setup
```bash
# Create a database for these exercises
createdb stream_processing

# Connect to the database
psql -d stream_processing
```

### Running Exercises
Execute SQL files in order (dependencies build on each other):

```bash
# Option 1: Run individual files
psql -d stream_processing -f 01_event_streams.sql

# Option 2: Run all at once
psql -d stream_processing -f 01_event_streams.sql
psql -d stream_processing -f 02_cdc_event_sourcing.sql
# ... etc
```

---

## 📋 Exercise Guide

### Section 1: Event Streams (`01_event_streams.sql`)

| Exercise | Concept | Key SQL Features |
|----------|---------|------------------|
| 1.1 | View event stream | SELECT, ORDER BY |
| 1.2 | Consumer offset tracking | JOIN, offset comparison |
| 1.3 | Commit offset after processing | UPDATE, transactions |
| 1.4 | Traditional queue (RabbitMQ) | FOR UPDATE SKIP LOCKED |
| 1.5 | Partition simulation | Table partitioning, hash |
| 1.6 | CDC with triggers | CREATE TRIGGER, CDC capture |
| 1.7 | Multiple consumer groups | Independent offsets |

**Learning Goal**: Understand log-based vs traditional message brokers

---

### Section 2: CDC & Event Sourcing (`02_cdc_event_sourcing.sql`)

| Exercise | Concept | Key SQL Features |
|----------|---------|------------------|
| 2.1 | CDC with transaction context | txid_current(), multi-table CDC |
| 2.2 | Event Sourcing basics | Event store, aggregate |
| 2.3 | Reconstruct state from events | Function, JSONB manipulation |
| 2.4 | Optimistic concurrency | Version checking, RAISE EXCEPTION |
| 2.5 | Log compaction | DELETE with subquery |
| 2.6 | Materialized views | CREATE MATERIALIZED VIEW |
| 2.7 | Refresh materialized view | REFRESH MATERIALIZED VIEW |
| 2.8 | Dual-write problem solution | CDC + cache pattern |

**Learning Goal**: Master CDC patterns and event sourcing implementation

---

### Section 3: Stream Processing (`03_processing_streams.sql`)

| Exercise | Concept | Key SQL Features |
|----------|---------|------------------|
| 3.1 | Basic aggregations | COUNT, SUM, AVG, GROUP BY |
| 3.2 | Real-time metrics | Materialized views |
| 3.3 | Pattern detection (CEP) | LAG, ROW_NUMBER, CTEs |
| 3.4 | Funnel analysis | Conditional aggregation |
| 3.5 | Moving averages | ROWS BETWEEN n PRECEDING |
| 3.6 | Alerting | Threshold comparisons |
| 3.7 | Event routing | JSONB matching |
| 3.8 | Real-time counters | UPSERT, idempotent |

**Learning Goal**: Implement stream analytics and processing patterns

---

### Section 4: Time Windows (`04_time_windows.sql`)

| Exercise | Concept | Key SQL Features |
|----------|---------|------------------|
| 4.1 | Event time vs processing time | DATE_TRUNC, timestamp comparison |
| 4.2 | Tumbling window | DATE_TRUNC + GROUP BY |
| 4.3 | Hopping window | generate_series, JOIN |
| 4.4 | Sliding window | ROWS BETWEEN, self-join |
| 4.5 | Session window | LAG, gap detection, cumulative sum |
| 4.6 | Late event handling | Watermark logic |
| 4.7 | Watermark implementation | Function with timestamp logic |
| 4.8 | Complex window aggregations | Multiple window types |

**Learning Goal**: Master all window types for time-based processing

---

### Section 5: Stream Joins (`05_stream_joins.sql`)

| Exercise | Concept | Key SQL Features |
|----------|---------|------------------|
| 5.1 | Stream-stream join | Time-windowed JOIN |
| 5.2 | Left join for conversions | LEFT JOIN with conditions |
| 5.3 | Sequence pattern detection | Multi-stream correlation |
| 5.4 | Stream-table enrichment | JOIN with reference table |
| 5.5 | LATERAL join | CROSS JOIN LATERAL |
| 5.6 | Table-table materialized view | JOIN + MATERIALIZED VIEW |
| 5.7 | Incremental view maintenance | Trigger-based updates |
| 5.8 | Point-in-time join | Time range in JOIN |
| 5.9 | Multi-stream join | Multiple CTEs |
| 5.10 | Slowly changing dimension | SCD Type 2 |

**Learning Goal**: Implement all three types of stream joins

---

### Section 6: Fault Tolerance (`06_fault_tolerance.sql`)

| Exercise | Concept | Key SQL Features |
|----------|---------|------------------|
| 6.1 | Processing semantics | Function simulation |
| 6.2 | Idempotent design | UNIQUE constraint, UPSERT |
| 6.3 | Idempotent orders | ON CONFLICT DO UPDATE |
| 6.4 | Transactional outbox | Atomic DB + event |
| 6.5 | Outbox publisher | Event publishing pattern |
| 6.6 | Checkpoint pattern | Offset tracking |
| 6.7 | Idempotent producer | Sequence deduplication |
| 6.8 | Transactional processing | Atomic offset + output |
| 6.9 | Microbatching | Batch grouping |

**Learning Goal**: Implement exactly-once semantics patterns

---

## 🔑 Key PostgreSQL Features Used

| Feature | Purpose |
|---------|---------|
| Window Functions | ROW_NUMBER, LAG, LEAD, AVG OVER |
| JSONB | Flexible event payloads |
| Materialized Views | Pre-computed aggregations |
| Triggers | CDC capture |
| UPSERT (INSERT ON CONFLICT) | Idempotent processing |
| CTEs | Readable stream logic |
| Array Functions | Event buffering |
| Table Partitioning | Partition simulation |

---

## ✅ Self-Check Questions

After completing each section, verify your understanding:

### Section 1: Event Streams
- [ ] What's the difference between Kafka (log-based) and RabbitMQ (traditional)?
- [ ] How does consumer offset work?
- [ ] What is CDC and how do triggers enable it?

### Section 2: CDC & Event Sourcing
- [ ] How does Event Sourcing differ from traditional database storage?
- [ ] What is log compaction and why is it useful?
- [ ] How does CDC solve the dual-write problem?

### Section 3: Stream Processing
- [ ] How do materialized views enable real-time analytics?
- [ ] What is Complex Event Processing (CEP)?
- [ ] How do you calculate moving averages in SQL?

### Section 4: Time Windows
- [ ] What's the difference between tumbling and hopping windows?
- [ ] How do session windows handle gaps in activity?
- [ ] What are watermarks and why are they needed?

### Section 5: Stream Joins
- [ ] What's a stream-stream join used for?
- [ ] How do you enrich events with reference data?
- [ ] How do you maintain a joined materialized view?

### Section 6: Fault Tolerance
- [ ] What's the difference between at-least-once and exactly-once?
- [ ] How does the transactional outbox pattern work?
- [ ] How do checkpoints enable state recovery?

---

## 🎯 Interview Questions from This Chapter

1. **What is the fundamental difference between Kafka and RabbitMQ?**
2. **What is Change Data Capture (CDC) and why is it important?**
3. **Explain the difference between event time and processing time.**
4. **What are the three types of stream joins?**
5. **How does Kafka achieve exactly-once semantics?**
6. **What is Event Sourcing and how does it differ from a traditional database?**

---

## 🧹 Cleanup

To clean up all tables created during exercises:

```sql
DROP TABLE IF EXISTS
    event_stream, consumer_offsets, traditional_queue, partitioned_events,
    cdc_events, users, replay_consumer,
    orders, order_items, cdc_transaction_log, event_store,
    kafka_topic_log, product_events, accounts, account_changes, account_cache,
    clickstream_events, login_events, metrics_stream, alert_thresholds,
    stream_subscriptions, real_time_counters,
    timed_events, clickstream, sensor_readings, user_activity,
    events_with_lateness, watermark_config, window_metrics,
    ad_impressions, ad_clicks, login_events, purchase_events,
    user_profiles, order_events, products, cart_events,
    customers, orders, cdc_log, customer_order_summary,
    page_views, add_to_carts, purchases, customers_scd, orders_with_time,
    events_for_processing, idempotent_events, orders_for_idempotency,
    accounts, outbox, processor_state, event_offsets, events_for_checkpoint,
    producer_sequence, consumer_offset, input_events, output_events,
    transaction_offset, microbatch_events
CASCADE;

DROP MATERIALIZED VIEW IF EXISTS
    product_current_state, real_time_metrics, customer_order_summary
CASCADE;
```

---

## 📖 Additional Resources

- [PostgreSQL Window Functions](https://www.postgresql.org/docs/current/functions-window.html)
- [PostgreSQL Materialized Views](https://www.postgresql.org/docs/current/rules-materializedviews.html)
- [Kafka Documentation](https://kafka.apache.org/documentation/)
- [Debezium CDC](https://debezium.io/documentation/)

---

**Happy Learning! 🎓**
