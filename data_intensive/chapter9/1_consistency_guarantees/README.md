# Chapter 9, Section 1: Consistency Guarantees

## Quick Start

This directory contains code examples and a teaching guide for understanding consistency guarantees in distributed systems.

### Files

- **TEACHING_GUIDE.md** — Comprehensive guide covering all consistency models
- **eventual_consistency.py** — Code examples for eventual consistency
- **linearizability.py** — Code examples for linearizability
- **causal_consistency.py** — Code examples for causal consistency

### Running the Examples

```bash
# Run eventual consistency examples
python eventual_consistency.py

# Run linearizability examples
python linearizability.py

# Run causal consistency examples
python causal_consistency.py
```

## Consistency Models at a Glance

### Eventual Consistency (Weakest)
- **Promise:** Replicas eventually converge
- **Stale reads:** Yes, unbounded
- **Latency:** Low
- **Use case:** Caches, social media feeds
- **Examples:** Cassandra, DynamoDB

### Causal Consistency (Middle)
- **Promise:** Respects "happened before" relationships
- **Stale reads:** No (for causally related events)
- **Latency:** Medium
- **Use case:** Collaborative editing, message threads
- **Examples:** Git, Riak

### Linearizability (Strongest)
- **Promise:** Behaves like a single copy of data
- **Stale reads:** No
- **Latency:** High
- **Use case:** Leader election, unique constraints
- **Examples:** ZooKeeper, etcd, Spanner

## Key Concepts

### 1. Eventual Consistency

```python
# Write returns immediately
node_a.write("x", 1)

# Read might return stale data
value = node_b.read("x")  # Might be None or 0
```

**Problem:** Stale reads can confuse users.

**Solution:** Use read-your-writes consistency or read from primary.

### 2. Linearizability

```python
# Write waits for quorum
node_a.write("x", 1)  # Waits for majority to acknowledge

# Read checks quorum
value = node_b.read("x")  # Guaranteed to be 1
```

**Benefit:** Strong consistency guarantees.

**Cost:** Higher latency (quorum coordination).

### 3. Causal Consistency

```python
# Vector clocks track causality
event1 = node_a.write("x", 1)
node_a.send_event_to_peer("Node-B", event1)

event2 = node_b.write("y", 2)  # Depends on event1
node_b.send_event_to_peer("Node-C", event2)

# Node-C sees event1 before event2 (causal order)
```

**Benefit:** Respects causality without full coordination.

**Cost:** More complex (vector clocks).

## The CAP Theorem

During a network partition, choose between:

- **CP (Consistent + Partition-tolerant):** Reject requests on minority side
  - Examples: ZooKeeper, etcd
  - Sacrifices availability

- **AP (Available + Partition-tolerant):** Accept requests, but sacrifice consistency
  - Examples: Cassandra, DynamoDB
  - Sacrifices linearizability

## Learning Path

1. **Start with TEACHING_GUIDE.md** — Read the overview and key concepts
2. **Run eventual_consistency.py** — See stale reads in action
3. **Run linearizability.py** — Understand quorum-based coordination
4. **Run causal_consistency.py** — Learn how vector clocks work
5. **Review the comparison table** — Understand trade-offs

## Interview Questions

1. What is the difference between eventual consistency and linearizability?
2. Why can't you use eventual consistency for leader election?
3. What is the CAP theorem?
4. How does causal consistency differ from linearizability?
5. Why is linearizability expensive?

See TEACHING_GUIDE.md for detailed answers.

## Real-World Systems

| System | Consistency | Use Case |
|--------|-------------|----------|
| Cassandra | Eventual | Time-series data, analytics |
| DynamoDB | Eventual | Web applications, caches |
| ZooKeeper | Linearizable | Leader election, coordination |
| etcd | Linearizable | Kubernetes state storage |
| Git | Causal | Version control |
| Spanner | Linearizable + Causal | Global transactions |

## Key Takeaways

1. **No "best" consistency model** — Choose based on your needs
2. **Stronger consistency = Higher latency** — Trade-off is unavoidable
3. **CAP theorem is about partitions** — Not about consistency in general
4. **Causality is cheaper than linearizability** — Use when possible
5. **Understand your use case** — Different applications need different guarantees

## Further Reading

- DDIA Chapter 9: "Consistency and Consensus"
- Lamport's "Time, Clocks, and the Ordering of Events in a Distributed System"
- Vector Clocks paper
- CAP Theorem paper
