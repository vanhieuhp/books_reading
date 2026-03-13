# PostgreSQL Request Routing - Hands-On Learning

## DDIA Chapter 6.4: Request Routing

This directory contains PostgreSQL exercises to help you understand request routing concepts from "Designing Data-Intensive Applications".

---

## Quick Start (15 minutes)

### Prerequisites

1. **Install PostgreSQL** (10 or later):
   ```bash
   # macOS
   brew install postgresql@15 && brew services start postgresql@15

   # Ubuntu/Debian
   sudo apt install postgresql postgresql-contrib
   ```

2. **Connect to PostgreSQL**:
   ```bash
   psql -U postgres -d postgres
   ```

### Run Exercises

```bash
# Exercise 1: Gossip Protocol (Decentralized)
psql -U postgres -d postgres -f 01_gossip_protocol.sql

# Exercise 2: ZooKeeper Coordination (Centralized)
psql -U postgres -d postgres -f 02_zookeeper_coordination.sql
```

---

## Exercises Overview

| Exercise | File | What You Learn |
|----------|------|----------------|
| 1 | `01_gossip_protocol.sql` | Decentralized routing, eventual consistency |
| 2 | `02_zookeeper_coordination.sql` | Centralized routing, strong consistency |

---

## Concepts Covered

### Approach 1: Gossip Protocol (Decentralized)

**Key Concept**: Nodes share routing info with each other; any node can handle requests.

```
Client Request Flow:
  1. Client → Any Node (via load balancer)
  2. If Node has partition → serve
  3. If not → Forward to correct node

Routing Update:
  - Node A talks to Node B (randomly)
  - Exchange routing tables
  - Over time, all nodes converge
```

**How Gossip Works:**
```
Round 1: Node 0 → Node 1 (share state)
Round 2: Node 1 → Node 2 (now Node 2 knows what Node 0 knew)
Round 3: Node 2 → Node 3 (all nodes converge)

Convergence: O(log N) rounds
```

**Pros:**
- No single point of failure
- Scales well
- Resilient to failures

**Cons:**
- Eventual consistency (routing may be briefly stale)
- May need extra hop (forwarding)
- Harder to debug

**Used by:** Cassandra, Riak, Dynamo

---

### Approach 2: ZooKeeper Coordination (Centralized)

**Key Concept**: Dedicated service tracks cluster state; routers subscribe to changes.

```
Client Request Flow:
  1. Client → Router
  2. Router queries ZooKeeper for partition location
  3. Router → Correct Node

Routing Update:
  - Partition moves
  - ZooKeeper updates immediately
  - Watches fire → all routers notified instantly
```

**The Watch Mechanism:**
```
1. Router registers watch on /partitions
2. Partition assignment changes in ZooKeeper
3. ZooKeeper immediately notifies router
4. Router updates local cache
```

**Pros:**
- Strong consistency (always current)
- Immediate notifications
- Simple to reason about

**Cons:**
- Coordination service is bottleneck
- Single point of failure (needs replication)
- Extra infrastructure

**Used by:** HBase, Kafka, MongoDB (config servers), SolrCloud

---

## The Trade-off

| Aspect | Gossip (Decentralized) | ZooKeeper (Centralized) |
|--------|----------------------|------------------------|
| **Architecture** | Peer-to-peer | Client-server |
| **Consistency** | Eventual | Strong |
| **Updates** | O(log N) propagation | Immediate (watches) |
| **Bottleneck** | None | Coordination service |
| **Latency** | Variable | Consistent |
| **Complexity** | Lower | Higher |

---

## Real-World Examples

### Cassandra (Gossip)
```
Client → Any Cassandra Node → (if needed) Forward → Correct Node

- Gossip protocol for cluster state
- Every node knows full partition map
- Client can contact any node
```

### MongoDB (Routing Tier)
```
Client → mongos (router) → Config Server → Correct Shard

- mongos is the routing tier
- Config servers store authoritative partition map
- Watches on config server changes
```

### HBase (ZooKeeper)
```
Client → ZooKeeper → Get Region Location → Region Server

- ZooKeeper tracks region (partition) locations
- Clients query ZooKeeper for region
- Watches fire on region moves
```

### DynamoDB (Cluster-Aware Client)
```
Client (smart driver) → Direct to correct node

- Client knows partition scheme
- Computes partition from key
- Direct connection (no router!)
```

---

## How to Verify Routing

### Check cluster state (ZooKeeper-style)

```sql
-- View all znodes
SELECT path, value FROM zk_znodes;

-- View active watches
SELECT * FROM zk_watches;

-- View router state
SELECT * FROM routing_tier;
```

### Check gossip state

```sql
-- View routing tables
SELECT * FROM gossip_state;

-- View gossip messages
SELECT * FROM gossip_messages;
```

### Compare routing paths

```sql
-- Gossip path: variable hops
SELECT * FROM route_request(contact_node, partition_id);

-- Centralized path: always one hop
SELECT * FROM centralized_routing WHERE partition_id = X;
```

---

## Common Mistakes

### ❌ Using gossip for consistency-critical apps
```sql
-- Routing may be briefly stale
-- Not suitable for financial transactions
```

### ❌ Using ZooKeeper for high-throughput writes
```sql
-- Router becomes bottleneck
-- Consider gossip for scale
```

### ❌ Not handling stale reads
```sql
-- In gossip, read after write may not see data
-- Must read from writer's partition directly
```

---

## Interview Questions

1. **What's the difference between gossip and ZooKeeper?**
   - Gossip: Decentralized, eventual consistency
   - ZooKeeper: Centralized, strong consistency

2. **Why does Cassandra use gossip?**
   - No single point of failure
   - Scales well
   - Works for P2P systems

3. **What is a ZooKeeper watch?**
   - Callback that fires on data change
   - Enables immediate notification

4. **Why might gossip need extra hops?**
   - Contacted node may not own the partition
   - Must forward to the correct node

---

## Next Steps

1. **Run both exercises** to understand both approaches
2. **Compare** latency, consistency, and complexity
3. **Read DDIA**: Chapter 6, Section 4 for theory (pp. 218-224)
4. **Review** Chapter 6 Summary: All 4 sections connect together

---

## Chapter 6 Summary

You've now completed all 4 sections of Chapter 6!

| Section | Topic | Key Concept |
|---------|-------|------------|
| 6.1 | Partitioning | Key-range vs Hash partitioning |
| 6.2 | Secondary Indexes | Local vs Global indexes |
| 6.3 | Rebalancing | Fixed vs Dynamic vs Consistent Hashing |
| 6.4 | Request Routing | Gossip vs ZooKeeper |

---

## Troubleshooting

### "function does not exist"
Make sure you're running exercises in order.

### "permission denied"
Run as PostgreSQL superuser or grant appropriate permissions.

### "connection refused"
Make sure PostgreSQL is running.

---

## References

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- DDIA Chapter 6: "Partitioning" (pp. 200-227)
- ZooKeeper Documentation
- Cassandra Gossip Protocol
