# Chapter 6, Section 4: Request Routing (Service Discovery)

## Overview

This section covers **how distributed databases route client requests to the correct partition** when data is spread across multiple nodes.

**The Core Problem:**
```
Client wants to read key "user_42"
  ↓
Which partition does "user_42" belong to?
  ↓
Which node owns that partition?
  ↓
How do we find that node?
```

This is the **Service Discovery** problem.

---

## Three Fundamental Routing Approaches

### Approach 1: Contact Any Node (Gossip-Based)

**Architecture:**
```
Client → Random Node → (if needed) Forward to correct node
```

**How it works:**
1. Client connects to any node via load balancer
2. If that node doesn't own the partition, it forwards the request
3. Nodes use **gossip protocol** to share routing information
4. Every node has a complete routing table

**Pros:**
- Simple client (no routing knowledge needed)
- Decentralized (no single point of failure)
- Gossip protocol eventually converges

**Cons:**
- Extra network hop if you contact the wrong node
- Routing table may be stale (eventual consistency)

**Used by:** Cassandra, Riak

---

### Approach 2: Routing Tier (Proxy)

**Architecture:**
```
Client → Routing Tier → Correct Node
```

**How it works:**
1. Dedicated routing layer sits between clients and database
2. Routing tier maintains complete partition-to-node mapping
3. Clients always talk to the router
4. Router forwards to correct node
5. Router gets partition map from **config servers** (like ZooKeeper)

**Pros:**
- Client is simple (just talks to router)
- Router has authoritative routing table
- Always routes to correct node (no extra hops)

**Cons:**
- Routing tier is a bottleneck
- Routing tier is a single point of failure (needs replication)
- Extra network hop through router

**Used by:** MongoDB (mongos), HBase (via ZooKeeper)

---

### Approach 3: Cluster-Aware Client

**Architecture:**
```
Client (knows routing) → Correct Node (direct)
```

**How it works:**
1. Client library is aware of partitioning scheme
2. Client computes which partition owns the key
3. Client connects directly to correct node
4. No intermediaries needed

**Pros:**
- No extra hops (direct to correct node)
- No routing tier bottleneck
- Highest performance

**Cons:**
- Client must stay up-to-date with routing changes
- Client library is more complex
- Requires smart driver

**Used by:** Cassandra (with Datastax driver), Kafka clients

---

## Comparison Table

| Aspect | Any Node (Gossip) | Routing Tier | Cluster-Aware Client |
|--------|-------------------|--------------|----------------------|
| **Client Complexity** | Low | Low | High |
| **Network Hops** | 1-2 | 2 | 1 |
| **Routing Consistency** | Eventual | Strong | Eventual |
| **Bottleneck Risk** | None | Router | None |
| **Decentralized** | Yes | No | Yes |
| **Latency** | Variable | Consistent | Lowest |

---

## Gossip Protocol (Decentralized)

**How it works:**
1. Each node maintains a local routing table
2. Nodes periodically pick a random peer
3. Nodes exchange their routing tables
4. Over time, all nodes converge on the same routing table

**Convergence:**
- Takes O(log N) rounds to reach all nodes
- Exponential propagation (each round doubles the number of informed nodes)
- Example: 1000 nodes converge in ~10 rounds

**Advantages:**
- No central coordinator (no single point of failure)
- Scales well (peer-to-peer)
- Resilient to network partitions

**Disadvantages:**
- Eventual consistency (routing may be stale)
- Takes time to propagate changes
- Harder to reason about

---

## ZooKeeper (Centralized Coordination)

**How it works:**
1. Nodes register partition ownership in ZooKeeper
2. Routing tier subscribes to changes (watches)
3. When partition moves, ZooKeeper notifies all subscribers
4. Routing tier updates immediately

**Architecture:**
```
Nodes → ZooKeeper ← Routing Tier / Client
         (coordinator)
```

**Advantages:**
- Strong consistency (immediate updates)
- Simple to reason about
- Centralized source of truth

**Disadvantages:**
- ZooKeeper is a single point of failure (needs replication)
- Routing tier is a bottleneck
- Extra network hop through routing tier

**Used by:**
- HBase: ZooKeeper for region assignment
- Kafka: ZooKeeper for partition leadership
- MongoDB: Config servers (similar concept)
- SolrCloud: ZooKeeper for shard routing

---

## The Rebalancing Challenge

When partitions are rebalanced (moved between nodes), **every routing layer must be updated immediately**. Otherwise, clients' requests go to the wrong node.

**Example: Adding a new node**
```
Before (10 nodes, 1000 partitions):
  Node 1: Partitions {1-100}
  Node 2: Partitions {101-200}
  ...

After adding Node 11:
  Node 11 "steals" partitions from each existing node
  Node 1: Partitions {1-91}        ← gave away 9 partitions
  Node 2: Partitions {101-191}     ← gave away 9 partitions
  ...
  Node 11: Partitions {92-100, 192-200, ...}
```

**How routing tables stay in sync:**
- **Gossip:** Changes propagate gradually (O(log N) rounds)
- **ZooKeeper:** Changes propagate instantly (watches fire)

---

## Real-World Examples

### Cassandra (Gossip Protocol)
- Uses consistent hashing with virtual nodes
- Every node knows the full partition map
- Clients can contact any node; if it doesn't own the data, it proxies
- Gossip protocol keeps all nodes in sync

### MongoDB (Routing Tier + Config Servers)
- `mongos` router process sits between clients and shards
- Config servers store authoritative partition map
- Router queries config servers to find correct shard
- Multiple routers for redundancy

### HBase (ZooKeeper)
- Regions (partitions) are tracked in ZooKeeper
- Region servers register their regions
- Clients query ZooKeeper to find correct region server
- ZooKeeper notifies clients of region moves

### DynamoDB (Cluster-Aware Client)
- Client library knows the partition scheme
- Client computes which partition owns the key
- Client connects directly to correct node
- Client updates routing table periodically

---

## Key Insights from DDIA

1. **The routing problem is fundamental:** Every distributed database must solve it.

2. **Three trade-offs:**
   - Gossip: Decentralized but eventual consistency
   - Routing tier: Centralized but bottleneck risk
   - Cluster-aware client: Best performance but complex

3. **Consistency vs. Performance:**
   - ZooKeeper: Strong consistency, but extra hop
   - Gossip: Eventual consistency, but no bottleneck

4. **Rebalancing is complex:** Moving partitions requires updating routing tables everywhere.

5. **No perfect solution:** Each approach has trade-offs. Choose based on your workload.

---

## Exercises

### Exercise 1: Gossip Protocol (`01_gossip_protocol.py`)
- Simulate how gossip spreads routing information
- Measure convergence time
- Show how clients route requests
- Compare with centralized routing

### Exercise 2: ZooKeeper Coordination (`02_zookeeper_coordination.py`)
- Simulate ZooKeeper registration and watches
- Show how routing tier stays in sync
- Compare with gossip protocol
- Demonstrate immediate consistency

---

## Interview Questions

1. **What is the difference between gossip and ZooKeeper?**
   - Gossip: Decentralized, eventual consistency, no bottleneck
   - ZooKeeper: Centralized, strong consistency, bottleneck risk

2. **Why can't clients just use `hash(key) % num_nodes`?**
   - Adding/removing nodes changes the hash for almost every key
   - Causes massive data movement (90%+ of keys move)

3. **How does Cassandra route requests without a central coordinator?**
   - Gossip protocol: Every node knows the full partition map
   - Clients can contact any node; it proxies if needed

4. **What is a "watch" in ZooKeeper?**
   - A callback that fires when something changes
   - Routing tier subscribes to partition changes
   - ZooKeeper notifies routing tier instantly

5. **Why does MongoDB use a routing tier instead of cluster-aware clients?**
   - Simpler for clients (no routing logic needed)
   - Easier to manage (centralized control)
   - Trade-off: Extra network hop and bottleneck risk

---

## Summary

**Request routing** is how distributed databases find the correct node for a given key. There are three approaches:

1. **Gossip Protocol** (Cassandra, Riak): Decentralized, eventual consistency
2. **Routing Tier** (MongoDB, HBase): Centralized, strong consistency
3. **Cluster-Aware Client** (Cassandra driver, Kafka): Direct routing, best performance

Each has trade-offs between consistency, performance, and complexity. The choice depends on your workload and requirements.

**Key takeaway:** There's no perfect solution. Every distributed database makes different trade-offs based on its design goals.
