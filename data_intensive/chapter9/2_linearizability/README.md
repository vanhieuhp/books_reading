# Section 2: Linearizability

This section covers linearizability, the strongest single-object consistency model.

## 📚 Contents

- **[TEACHING_GUIDE.md](./TEACHING_GUIDE.md)** - Comprehensive teaching guide with concepts and examples
- **[01_linearizability_basics.py](./01_linearizability_basics.py)** - Code demonstrations of linearizability concepts
- **[README.md](./README.md)** - This file

## 🎯 Learning Objectives

After this section, you should understand:

1. **What Linearizability Is**
   - The system behaves as if there is only one copy of the data
   - Every operation takes effect atomically at some point between its start and end
   - Once a write completes, ALL subsequent reads see the new value

2. **Why Linearizability Matters**
   - Leader election: Prevent split-brain
   - Unique constraints: Exactly one user can register a username
   - Cross-channel dependencies: Ensure consistency across systems

3. **The CAP Theorem Trade-off**
   - During a network partition, choose Consistency or Availability
   - CP systems (ZooKeeper, etcd): Sacrifice availability
   - AP systems (Cassandra, DynamoDB): Sacrifice linearizability

4. **Performance Cost**
   - Linearizability requires quorum confirmation
   - Adds latency proportional to network distance
   - Many systems choose eventual consistency for performance

5. **Total Order**
   - Linearizability implies a total order of all operations
   - All clients see operations in the same order
   - This is why consensus algorithms (Raft, Paxos) are used

## 🔑 Key Concepts

### Linearizability

**Definition:** The system behaves as if there is only one copy of the data, and every operation takes effect atomically at some point between its start and end.

**Key Rule:** Once ANY client has seen a new value, ALL subsequent reads by ALL clients must also see that new value (or a newer one).

### Visual Example

```
Timeline:
         0ms          50ms         100ms         150ms
Client A: ──write(x=1)────────────────|
Client B:          ──read(x)────|
Client C:                   ──read(x)──────|

Linearizable: B reads 1, C reads 1
Non-Linearizable: B reads 0, C reads 1 (violates monotonicity)
```

### CAP Theorem

```
              ┌─────────────────────┐
              │   CAP Theorem       │
              └──────┬──────────────┘
                     │
          ┌──────────┼──────────────┐
          │          │              │
     Consistency  Availability   Partition
     (Linearizable) (Always respond) Tolerance
                                  (Must handle
                                   netsplits)

You cannot have all three. Since network partitions WILL happen,
you must choose between C and A during a partition:

  CP System (Consistent + Partition-tolerant):
    During a partition, some requests return errors.
    Examples: ZooKeeper, etcd, HBase, Spanner.

  AP System (Available + Partition-tolerant):
    During a partition, all requests get a response, but some may be stale.
    Examples: Cassandra, DynamoDB, CouchDB.
```

### Total Order

Linearizability implies a total order of all operations:

```
Operations in order:
1. Client A: write(x=1)
2. Client B: write(x=2)
3. Client C: read(x) → 2
4. Client D: write(x=3)
5. Client E: read(x) → 3

All clients see operations in this same order.
```

## 📖 Code Examples

### Example 1: Linearizable Store

```python
from chapter9_2_linearizability.linearizability_basics import LinearizableStore

store = LinearizableStore()

# Write x=1
store.write("client_a", "x", 1)

# Read x (must see 1)
read = store.read("client_b", "x")
print(f"Read result: {read.result}")  # 1
```

### Example 2: Non-Linearizable Store

```python
from chapter9_2_linearizability.linearizability_basics import NonLinearizableStore

store = NonLinearizableStore(num_replicas=3)

# Write to primary
store.write("client_a", "x", 1)

# Read from replica (may be stale)
read = store.read("client_b", "x", replica_id=1)
print(f"Read result: {read.result}")  # May be None (stale)

# Sync replicas
store.sync_replicas()

# Read again (now up-to-date)
read = store.read("client_c", "x", replica_id=1)
print(f"Read result: {read.result}")  # 1
```

### Example 3: CAP Theorem

```
Network Partition: 5 nodes split into 3 and 2
Quorum size: 3

Partition A (3 nodes): Has quorum → can make decisions
Partition B (2 nodes): No quorum → cannot make decisions

CP System: Partition B rejects requests (consistent but unavailable)
AP System: Partition B accepts requests (available but stale)
```

## 🚀 Running the Examples

### Run all demonstrations:

```bash
python 01_linearizability_basics.py
```

This will show:
1. Linearizability vs Non-Linearizability
2. Total Order of Operations
3. CAP Theorem Trade-off
4. Performance Cost of Linearizability
5. Compare-and-Set (CAS) Requirements

## 💡 Experiments

### Experiment 1: Understand the CAP Trade-off

Edit `01_linearizability_basics.py` and modify the `demonstrate_cap_theorem()` function:

```python
# Try different partition sizes
for partition_a_size in [1, 2, 3, 4]:
    partition_b_size = 5 - partition_a_size
    quorum = 3

    a_has_quorum = partition_a_size >= quorum
    b_has_quorum = partition_b_size >= quorum

    print(f"Partition {partition_a_size}-{partition_b_size}: "
          f"A={a_has_quorum}, B={b_has_quorum}")
```

### Experiment 2: Measure Latency Difference

Create a new script to measure the latency difference:

```python
import time

# Linearizable write (2 round-trips)
network_latency = 0.050  # 50ms
linearizable_latency = 2 * network_latency

# Non-linearizable write (1 round-trip)
non_linearizable_latency = 1 * network_latency

print(f"Linearizable: {linearizable_latency * 1000:.0f}ms")
print(f"Non-linearizable: {non_linearizable_latency * 1000:.0f}ms")
print(f"Difference: {linearizable_latency / non_linearizable_latency:.1f}x slower")
```

### Experiment 3: Simulate Compare-and-Set

Create a new script to simulate CAS operations:

```python
from chapter9_2_linearizability.linearizability_basics import LinearizableStore

store = LinearizableStore()

# Simulate two clients trying to register the same username
def cas_register(store, client_id, username):
    current = store.data.get("username")
    if current is None:
        store.write(client_id, "username", username)
        return True
    return False

# Client A registers
success_a = cas_register(store, "client_a", "alice")
print(f"Client A: {success_a}")  # True

# Client B tries to register same username
success_b = cas_register(store, "client_b", "alice")
print(f"Client B: {success_b}")  # False
```

## 🎓 Interview Questions

1. **What is linearizability and how does it differ from serializability?**
   - Linearizability: single-object, real-time ordering guarantee
   - Serializability: multi-object, transaction isolation (no real-time guarantee)
   - Strict Serializability = both

2. **Explain the CAP theorem. What does a CP system sacrifice?**
   - During a network partition, choose Consistency or Availability
   - CP system (e.g., ZooKeeper): Sacrifices availability
   - Rejects requests on the minority side of a partition

3. **Why is linearizability expensive?**
   - Every write must wait for quorum confirmation
   - Adds latency proportional to network distance
   - Many systems choose eventual consistency for performance

4. **How does compare-and-set (CAS) require linearizability?**
   - CAS: "Set value only if it's currently X"
   - Used for unique constraints
   - Without linearizability: Both writes succeed, undefined result
   - With linearizability: Exactly one succeeds

5. **What is the relationship between linearizability and total order?**
   - Linearizability implies a total order of all operations
   - All clients see operations in the same order
   - This is why consensus algorithms are used

## 📚 Key Terminology

| Term | Definition |
|------|-----------|
| **Linearizability** | Behaves as if one copy of data; operations are atomic and globally ordered |
| **Total Order** | Every pair of events is ordered (no concurrency) |
| **Partial Order** | Some events are ordered; concurrent events are incomparable |
| **Quorum** | Majority of nodes (more than half) |
| **Split-Brain** | Two nodes both think they're the leader |
| **CAP Theorem** | During a network partition, choose Consistency or Availability |
| **Compare-and-Set (CAS)** | Atomic operation: "Set value only if it's currently X" |
| **Consensus Algorithm** | Algorithm to get all nodes to agree on a value (Raft, Paxos) |
| **Total Order Broadcast** | Protocol ensuring all nodes deliver messages in the same order |

## 🔗 Related Concepts

- **Raft Consensus Algorithm** - Uses quorums for leader election
- **Paxos Algorithm** - Classic consensus algorithm
- **Google Spanner** - Uses TrueTime for clock synchronization
- **Byzantine Generals Problem** - Classic problem in distributed systems
- **CAP Theorem** - Consistency, Availability, Partition tolerance trade-offs

## 📖 Further Reading

- Chapter 9 of "Designing Data-Intensive Applications" by Martin Kleppmann
- Raft consensus algorithm: https://raft.github.io/
- Google Spanner paper: https://research.google/pubs/spanner-googles-globally-distributed-database/
- Paxos algorithm: Leslie Lamport's papers
- CAP Theorem: Gilbert and Lynch's proof

---

**Start with [TEACHING_GUIDE.md](./TEACHING_GUIDE.md) to begin your learning journey!**
