# Chapter 6: Partitioning (Sharding)

This is a comprehensive summary of **Chapter 6: Partitioning** from *Designing Data-Intensive Applications* by Martin Kleppmann.

---

## Introduction: Why Partition?

In Chapter 5 we learned about **Replication** — keeping identical copies of the same data on multiple machines. Replication helps with fault tolerance and read scalability, but every replica still has the *entire* dataset. What happens when your data gets so massive that a single machine can't store it all, or the write throughput exceeds what a single CPU can handle?

The answer is **Partitioning** (also known as **Sharding**): breaking the dataset into smaller pieces and distributing them across multiple nodes.

```
Before Partitioning (Single Node):
  ┌──────────────────────────────────┐
  │     Node A (ALL 100GB of data)    │  ← CPU maxed, disk full
  └──────────────────────────────────┘

After Partitioning (3 Nodes):
  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
  │ Node A (33GB) │ │ Node B (33GB) │ │ Node C (33GB) │
  │ Keys: A-H     │ │ Keys: I-R     │ │ Keys: S-Z     │
  └──────────────┘ └──────────────┘ └──────────────┘
```

* **Each piece of data belongs to exactly one partition.** (Unlike replication, where data is duplicated.)
* **Each node may store multiple partitions.** A single database server could hold 50 partitions while another holds 60.
* A query that operates on a single partition can be run on the node that holds that partition. A query that spans multiple partitions must run on multiple nodes and combine the results.

### Terminology Across Systems
The concept is universal but the naming varies wildly:

| System | Term |
|--------|------|
| General / DDIA | Partition |
| MongoDB, Elasticsearch | Shard |
| HBase | Region |
| Bigtable | Tablet |
| Cassandra, Riak | vnode (virtual node) |
| PostgreSQL (Citus) | Shard |

### Partitioning + Replication
In practice, partitioning is almost always combined with replication. Each partition is replicated across multiple nodes for fault tolerance. A common setup:

```
                      Partition 1             Partition 2            Partition 3
  Node A:             LEADER                  Follower               Follower
  Node B:             Follower                LEADER                 Follower
  Node C:             Follower                Follower               LEADER

  Each node is a leader for some partitions and a follower for others.
  This spreads the write load evenly.
```

The choice of partitioning scheme is mostly independent of the choice of replication scheme, so Chapter 6 focuses purely on partitioning logic.

---

# 1. Partitioning of Key-Value Data

The most fundamental question: given a record with a certain key, which partition should it go to?

**The Goal:** Spread data and query load **evenly** across nodes. If the distribution is unfair, a few partitions will carry a disproportionate load while others sit idle. A heavily loaded partition is called a **hot spot**.

Ideally we want to avoid hot spots — every node should handle an equal share of reads and writes. There are two dominant approaches to assigning keys to partitions.

## Strategy 1: Partitioning by Key Range

Assign a **continuous range** of keys to each partition, similar to how volumes of a printed encyclopedia cover letters A–Ce, Ce–G, G–K, and so on.

```
Sensor Data Example:
  Partition 1:  2024-01-01  to  2024-01-10
  Partition 2:  2024-01-11  to  2024-01-20
  Partition 3:  2024-01-21  to  2024-01-31

  → All sensor readings from Jan 1-10 go to Partition 1.
  → All sensor readings from Jan 11-20 go to Partition 2.
```

The range boundaries are **not necessarily evenly spaced**. If your data is not uniformly distributed (e.g., you have way more data for January than February), the boundaries must be chosen to equalize the data volume. Some databases set boundaries automatically; others require manual configuration.

**Within each partition, keys are sorted.** This means you can treat the partition like a mini-database with an efficient sorted index (like a B-tree or SSTable).

### Pros
* **Efficient range queries.** A query like `SELECT * FROM readings WHERE timestamp BETWEEN '2024-01-01' AND '2024-01-05'` only needs to contact the one partition whose range covers that interval. It can scan through consecutive keys very quickly.
* **Data locality.** Related keys live next to each other on disk, enabling fast sequential I/O.

### Cons — The Hot Spot Problem
* **Skewed writes cause hot spots.** If your key is a timestamp, ALL writes for "right now" go to one partition (the one whose range covers the current time), while all historical partitions sit idle. One node does all the work.

### Fixing the Timestamp Hot Spot
The traditional fix is to **prefix the timestamp** with another dimension:
```
Key = sensor_name + "_" + timestamp
  → "temperature_east_2024-01-15T10:30:00"
  → "humidity_west_2024-01-15T10:30:00"
```

Now writes for "right now" are spread across multiple sensors and thus multiple partitions. **But the trade-off is:** if you want to fetch readings from ALL sensors for a given time range, you need to issue a separate range query to each partition and merge the results.

### Real-World Users
* **HBase:** Row keys are byte-strings sorted lexicographically. Partitions (regions) have configurable split points.
* **Bigtable:** Uses key ranges. Google's original MapReduce paper describes this.
* **RethinkDB:** Key range partitioning.
* **MongoDB (before v2.4):** Originally used key ranges only. Now supports hash-based too.

---

## Strategy 2: Partitioning by Hash of Key

To avoid the hot spot problem, many distributed databases use a **hash function** to scramble the keys before assigning them to partitions.

A good hash function takes skewed, clustered data and distributes it **uniformly** across an output range:

```
hash("user_001") → 0x3A2F   → Partition 1
hash("user_002") → 0xDF40   → Partition 3
hash("user_003") → 0x7E12   → Partition 2
```

Even though the user IDs are sequential (001, 002, 003), their hash values are scattered across the partition space. Hot spots are essentially eliminated for typical workloads.

### How partitions are assigned
The hash function produces a number (e.g., 0 to 2^31). This range is divided among partitions:
```
Hash Range:         0 ──────────────── 2^31
Partition 1:        |=====|
Partition 2:               |=====|
Partition 3:                      |=====|
```

### Hash Functions — An Important Detail
You should **NOT** use Java's `Object.hashCode()` or Python's `hash()` because they may give different results in different processes (they're non-deterministic by design). Databases use well-defined, deterministic hash functions like:
* **MD5** (MongoDB uses this)
* **MurmurHash** (Cassandra uses Murmur3)
* **xxHash**, **FNV**

These functions don't need to be cryptographically strong — they just need to uniformly distribute data.

### Pros
* **Excellent at eliminating hot spots** for most workloads.
* Queries for a known key are efficient: compute `hash(key)`, find the right partition, done.

### Cons — Loss of Efficient Range Queries
* **Range queries are impossible on the main key.** Since `hash("user_001")` and `hash("user_002")` land on completely different partitions, a query like `WHERE user_id BETWEEN 'user_001' AND 'user_100'` must be sent to ALL partitions (scatter/gather). This is expensive.
* In MongoDB, if you use hash-based sharding, range queries on the shard key are sent to all shards. In Riak, Couchbase, and Voldemort, range queries on the primary key are simply not supported.

### Real-World Users
* **Cassandra:** Uses Murmur3 hash partitioner.
* **Riak:** Uses consistent hashing.
* **Voldemort:** Hash-based.
* **Redis Cluster:** Hash slots (CRC16).
* **DynamoDB:** Hash-based partitioning.

---

## Hybrid Approach: Compound Primary Keys (Cassandra)

Cassandra uses a brilliant compromise between key range and hash partitioning.

A table can declare a **compound primary key** of several columns, e.g.,  `PRIMARY KEY (user_id, timestamp)`.

* The **first column** (`user_id`) is hashed to determine the partition. This ensures even distribution across nodes.
* The **remaining columns** (`timestamp`) are used as a **sorted (concatenated) index within that partition**. Data within the partition is physically stored in sorted order by these columns.

```
Partition for hash(user_42):
  ┌──────────────────────────────────────────┐
  │ user_42 │ 2024-01-01 │ "logged in"       │
  │ user_42 │ 2024-01-02 │ "updated profile" │
  │ user_42 │ 2024-01-03 │ "posted comment"  │
  │ user_42 │ 2024-01-04 │ "logged out"      │
  └──────────────────────────────────────────┘
  
  Query: "Give me user_42's activity from Jan 1 to Jan 3"
  → Hash user_42 → go to one partition → do an efficient range scan. ✅ FAST!

  Query: "Give me ALL users' activity from Jan 1 to Jan 3"
  → You need to scatter/gather across ALL partitions. ❌ SLOW.
```

This pattern is extremely powerful for social media feeds, IoT sensor data, and time-series workloads.

---

## Handling Skewed Workloads and Hot Spots (The "Celebrity" Problem)

Hashing evenly distributes keys, but what if **millions of requests all target the exact same key**?

**Example:** On a social media site, a celebrity post ID (e.g., `post_8932`) goes viral. Millions of users read, like, and comment on `post_8932`. Since the hash of `post_8932` maps to exactly one partition, that partition becomes an extreme hot spot.

The database cannot automatically fix this. As Kleppmann puts it: *"Today, most data systems are not able to automatically compensate for such a highly skewed workload, so it's the responsibility of the application to reduce the skew."*

### The Application-Level Fix: Key Splitting
Append a random number (e.g., 00-99) to the hot key:
```
Instead of writing to:  "post_8932"
Write to one of:        "post_8932_00", "post_8932_01", ... "post_8932_99"
```

This splits the single hot partition's load across up to 100 partitions.

**Trade-off:** Reading data for `post_8932` now requires querying all 100 split keys from their respective partitions and merging the results. You should only apply this for keys you *know* are hot (e.g., you bookkeep a list of currently-trending post IDs). For the vast majority of keys with normal traffic, the overhead of splitting and merging is not worth it.

---

# 2. Partitioning and Secondary Indexes

Everything above assumes you are accessing data by its primary key. But most applications also need **secondary indexes** — queries that search by value rather than key:
* "Find all cars where `color = 'red'`"
* "Find all users in `city = 'San Francisco'`"
* "Find all orders with `status = 'pending'` and `total > $100`"

Secondary indexes are the bread and butter of relational databases and document databases (e.g., Elasticsearch is basically a secondary index engine). But secondary indexes **don't map neatly to partitions**, since a "red car" could be stored in any partition. The challenge is keeping the index in sync as data is scattered.

There are two fundamentally different approaches.

## Approach 1: Document-Partitioned Indexes (Local Indexes)

Each partition maintains its **own** secondary index, covering only the documents within that partition.

```
  Partition 0                         Partition 1
  ┌──────────────────────┐            ┌──────────────────────┐
  │ Data:                │            │ Data:                │
  │  doc 191 (red car)   │            │  doc 768 (blue car)  │
  │  doc 214 (black car) │            │  doc 893 (red car)   │
  │                      │            │                      │
  │ Local Index:         │            │ Local Index:         │
  │  color:red → [191]   │            │  color:red → [893]   │
  │  color:black → [214] │            │  color:blue → [768]  │
  └──────────────────────┘            └──────────────────────┘
```

### Writing is Fast & Simple
When you add a red car to Partition 0, you only need to update Partition 0's local index. No network calls to other partitions. The write is entirely local to one node.

### Reading Requires Scatter/Gather
When you search for `color = 'red'`, the database doesn't know which partitions contain red cars. It must send the query to **every single partition**, collect the results, and merge them.

```
Client query: "Find all red cars"
  → Send to Partition 0:  returns [doc 191]
  → Send to Partition 1:  returns [doc 893]
  → Send to Partition 2:  returns []
  → ...
  → Send to Partition N:  returns [...]
  
  Merge: [doc 191, doc 893, ...]
```

This scatter/gather approach makes **read queries on secondary indexes expensive**, especially if you have hundreds of partitions. A single slow partition can create high **tail latency** — the overall query takes as long as the slowest partition response.

### Real-World Users
* **MongoDB**: Local indexes on each shard.
* **Cassandra**: Each partition has its own secondary index.
* **Elasticsearch**: Each shard is a complete Lucene index.
* **Riak**: Local indexes.
* **VoltDB**: Local indexes.

This approach is also called a **local index** because each partition's index only covers documents stored locally.

---

## Approach 2: Term-Partitioned Indexes (Global Indexes)

Instead of each partition keeping a local index, a **global index** is constructed that covers data from *all* partitions. However, we can't store a global index on a single node (that would be a single point of failure and a bottleneck). So the global index is itself **partitioned** — but partitioned differently from the data.

```
  Data partitions:
    Partition 0 (primary data):  doc 191 (color: red),    doc 214 (color: black)
    Partition 1 (primary data):  doc 768 (color: blue),   doc 893 (color: red)

  Global Index partitions (by term):
    Index Partition A (handles terms a-r):
      color:black → [doc 214 on Partition 0]
      color:blue  → [doc 768 on Partition 1]
    
    Index Partition B (handles terms s-z):
      color:red   → [doc 191 on Partition 0, doc 893 on Partition 1]
```

The index can be partitioned by the **term** itself (useful for range scans on the term, e.g., "find all cars with colors between `red` and `silver`") or by a **hash of the term** (for more even distribution).

### Reading is Fast
A query for `color = 'red'` only needs to go to the one index partition that holds the "red" term. No scatter/gather needed. Very efficient!

### Writing is Slow and Complex
When you insert a new red car into Data Partition 0, you must also update the Global Index Partition that holds the "red" term — which may be on a completely different node. A single document write can affect multiple secondary index partitions, potentially requiring a **distributed transaction** across several nodes.

Because distributed transactions are complex and slow, global secondary indexes are almost always **updated asynchronously**. This means: if you write a red car, it may not appear in search results for a fraction of a second (or longer under heavy load). The index is **eventually consistent**.

### Real-World Users
* **DynamoDB:** Global Secondary Indexes (GSI) — updated asynchronously. Amazon's documentation explicitly notes that GSIs are eventually consistent.
* **Oracle:** Supports both local and global partitioned indexes.
* **Riak:** Search feature uses a term-partitioned global index.
* **Google Cloud Spanner:** Global indexes.

---

## Comparison Table: Local vs. Global Indexes

| Aspect | Local (Document-Partitioned) | Global (Term-Partitioned) |
|--------|------------------------------|--------------------------|
| **Write speed** | ⭐⭐⭐ Fast (single partition) | ⭐ Slow (cross-partition update) |
| **Read speed** | ⭐ Slow (scatter/gather ALL) | ⭐⭐⭐ Fast (single index lookup) |
| **Consistency** | Immediately consistent locally | Usually eventually consistent |
| **Complexity** | Simple | Complex (distributed updates) |
| **Best for** | Write-heavy workloads | Read-heavy search workloads |

---

# 3. Rebalancing Partitions

Over time, things change:
1. **Higher query throughput:** You want to add more CPUs to handle the load.
2. **Dataset growth:** You need more RAM and disk to store everything.
3. **Machine failures:** A node dies and its load must be picked up by another node.

All of these situations require **moving data between nodes** — a process called **rebalancing**.

### Requirements for Rebalancing
After rebalancing, the following MUST be true:
1. **Load is shared fairly** across all nodes in the cluster (including any new nodes).
2. **The database must continue accepting reads and writes** while rebalancing is in progress.
3. **Only the minimum necessary data is moved** between nodes, to minimize network and disk I/O.

---

## How NOT to Do It: hash(key) mod N

A tempting but terrible idea: use `hash(key) % number_of_nodes` to assign keys to nodes.

**Why it fails catastrophically:** The number of nodes changes! If you go from 10 to 11 nodes:
* `hash(key) % 10 = 3` → key was on Node 3
* `hash(key) % 11 = 7` → key must now move to Node 7

This affects *nearly every key in the database*. Adding a single node causes ~90% of all data to be shuffled across the network. This is wildly impractical.

```
Before (10 nodes):   hash("alice") % 10 = 3   → Node 3
After  (11 nodes):   hash("alice") % 11 = 7   → Node 7  💥 MOVED!
                     hash("bob")   % 10 = 1   → Node 1
                     hash("bob")   % 11 = 9   → Node 9  💥 MOVED!
                     (Most keys move! Disaster.)
```

---

## Strategy 1: Fixed Number of Partitions

Create **many more partitions than there are nodes**, and keep the number of partitions fixed forever.

**Example:** Create 1,000 partitions for a 10-node cluster. Each node handles 100 partitions.

```
Before (10 nodes, 1000 partitions):
  Node 1:  Partitions {1-100}
  Node 2:  Partitions {101-200}
  ...
  Node 10: Partitions {901-1000}

After adding Node 11:
  Node 11 "steals" a few partitions from each existing node:
  Node 1:  Partitions {1-91}          ← gave away 9 partitions
  Node 2:  Partitions {101-191}       ← gave away 9 partitions
  ...
  Node 11: Partitions {92-100, 192-200, ..., ~91 partitions}
```

The partitions themselves **never change their boundaries**. Only the assignment of partitions to nodes changes. This means rebalancing is just a bulk file move — copy entire partition files from one node to another. Simple!

### How Many Partitions Should You Create?
This must be decided **at database creation time** and (in most implementations) never changed.
* **Too few partitions:** Each partition gets huge. Moving a single partition during rebalancing takes too long and is too expensive.
* **Too many partitions:** Each partition is tiny nut the management overhead grows: tracking partition state, replication state, leader elections, etc. for 100,000 partitions instead of 100 is expensive.

The right number depends on dataset size and hardware. A good rule of thumb: each partition should be between **100MB and a few GB**.

### Real-World Users
* **Riak:** 64 partitions by default (configurable at creation).
* **Elasticsearch:** You define the number of shards per index at index creation time.
* **Couchbase:** 1,024 vBuckets by default.
* **Voldemort:** Fixed partition count.

---

## Strategy 2: Dynamic Partitioning

With key range partitioning, a fixed number of partitions with fixed boundaries can be very inconvenient — if the boundaries are wrong, you end up with wildly uneven partitions.

**Dynamic partitioning** solves this. Partitions split and merge automatically based on their size:

1. When a partition's data exceeds a **configured threshold** (e.g., 10 GB in HBase), it **splits** into two partitions, each containing approximately half the data.
2. If lots of data is deleted and a partition shrinks below a threshold, it can be **merged** with an adjacent partition.

```
Initial state (1 partition):
  [───────────── Partition 1 (0.5 GB) ─────────────]

After lots of inserts (partition grows to 10 GB → SPLIT):
  [─── Partition 1a (5 GB) ───][─── Partition 1b (5 GB) ───]

After even more inserts (partition 1b grows to 10 GB → SPLIT AGAIN):
  [─── Partition 1a (5 GB) ───][── P1b-L (5GB) ──][── P1b-R (5GB) ──]
```

### The Cold-Start Problem
When a brand-new database starts, it has **only one partition** because there is no data yet. All writes hit a single node until the first split threshold is reached. This can be a bottleneck!

**Solution: Pre-splitting.** HBase and MongoDB allow you to configure an initial set of partition boundaries at database creation time, so the database starts with several partitions from day one.

### Pros
* The number of partitions **adapts automatically** to the total data volume.
* Works equally well for key range and hash partitioning.

### Real-World Users
* **HBase:** Dynamic region splitting is the core mechanism.
* **MongoDB:** Dynamic splitting for range-partitioned collections.
* **RethinkDB:** Automatic split/merge.

---

## Strategy 3: Partitioning Proportionally to Nodes

With a fixed partition count, the size of each partition grows proportionally to the total dataset size (because partitions are fixed while data grows). With dynamic partitioning, the number of partitions is proportional to the dataset size.

A third option: make the number of partitions proportional to the **number of nodes**. In other words, have a fixed number of **partitions per node**.

**Example:** Cassandra uses 256 partitions per node by default.

When a new node joins the cluster:
1. It randomly selects a fixed number (256) of existing partitions.
2. It splits each selected partition in half.
3. It takes ownership of one half; the other half stays on the old node.

This means: if you have 10 nodes, you have 2,560 partitions. If you grow to 20 nodes, you have 5,120 partitions (each one is roughly half the size). The system scales smoothly.

### Pros
* Partition size stays relatively stable as the cluster grows.
* No need to guess the right number of partitions upfront.

### Real-World Users
* **Cassandra:** 256 vnodes per node by default.
* **Ketama:** Consistent hashing with virtual nodes.

---

## Rebalancing Comparison Table

| Strategy | # Partitions | When to Use | Used By |
|----------|-------------|-------------|---------|
| Fixed # of partitions | Constant (chosen upfront) | When you can estimate dataset growth | Riak, Elasticsearch, Couchbase |
| Dynamic partitioning | Grows/shrinks with data | Key range partitioning; unknown data size | HBase, MongoDB, RethinkDB |
| Per-node partitioning | Grows with node count | Consistent hashing setups | Cassandra |

---

## Automatic vs. Manual Rebalancing

Should rebalancing happen fully automatically, or should a human approve partition moves?

* **Fully automatic:** Convenient, but risky. If the system *incorrectly* detects a node as dead (due to a temporary network blip), it might start a massive, unnecessary rebalancing operation. This floods the network with data transfers, which makes the already-overloaded network even slower, which triggers *more* incorrect failure detections — a cascading failure.
* **Manual approval (recommended by DDIA):** The database suggests a rebalancing plan, but a human administrator reviews and approves it before execution. This adds a delay but prevents catastrophic cascading failures.

Couchbase, Riak, and Voldemort generate suggested partition assignments automatically but require an administrator to commit them.

---

# 4. Request Routing (Service Discovery)

We've discussed how data is spread across partitions. But when a client wants to read or write key `"foo"`, which node should it connect to? The client must figure out: *"Key `foo` lives on Partition 7, and Partition 7 is currently hosted on Node B at IP 10.0.3.42."*

This is a specific instance of the general problem of **Service Discovery**.

There are three fundamental approaches:

```
Approach 1: Contact Any Node (Proxy)
  ┌────────┐
  │ Client │
  └────┬───┘
       │
       ▼ (connects to random node)
  ┌────────┐    forward    ┌────────┐
  │ Node A │ ────────────► │ Node C │ (owns partition for key "foo")
  └────────┘               └────────┘

Approach 2: Routing Tier
  ┌────────┐
  │ Client │
  └────┬───┘
       │
       ▼
  ┌──────────────┐   route   ┌────────┐
  │ Routing Tier │ ────────► │ Node C │
  │ (partition-  │           └────────┘
  │  aware proxy)│
  └──────────────┘

Approach 3: Client is Cluster-Aware
  ┌────────────────┐
  │ Client         │
  │ (knows that    │ ──────────────────► ┌────────┐
  │  key "foo"     │     direct          │ Node C │
  │  is on Node C) │                     └────────┘
  └────────────────┘
```

### Approach 1: Contact Any Node (Gossip-Based)
The client connects to any node via a round-robin load balancer. If that node doesn't own the requested key, it forwards the request to the correct node, gets the response, and passes it back to the client.

* **Used by:** Cassandra, Riak.
* **How nodes know the routing:** Gossip protocol. Nodes constantly exchange information about which node owns which partitions. Every node has a full routing table.

### Approach 2: Routing Tier (Proxy)
A dedicated routing layer sits between clients and the database. It maintains a complete mapping of partitions to nodes. Clients talk only to the router; the router forwards to the correct node.

* **Used by:** MongoDB (the `mongos` router process).
* **How the router knows:** MongoDB uses dedicated **config servers** — a replicated set of nodes that store the authoritative partition map.

### Approach 3: Cluster-Aware Client
The client library itself is aware of the partitioning scheme and connects directly to the correct node. No intermediaries needed.

* **Used by:** Datastax Cassandra driver, some Kafka client libraries.
* **Complexity:** Requires a smart client driver that stays up-to-date as partitions are rebalanced.

---

## ZooKeeper and Friends: Keeping Routing Up-to-Date

The fundamental challenge: when partitions are rebalanced (moved between nodes), every routing layer must be updated **immediately**. Otherwise, clients' requests go to the wrong node.

Many systems use a **coordination service** like **ZooKeeper**, **etcd**, or **Consul** to solve this:

```
  ┌──────────────┐         ┌───────────┐
  │  ZooKeeper   │◄────────│  Node A   │  Registers: "I own Partitions 1-100"
  │ (Coordination│◄────────│  Node B   │  Registers: "I own Partitions 101-200"
  │  Service)    │◄────────│  Node C   │  Registers: "I own Partitions 201-300"
  └──────┬───────┘         └───────────┘
         │
         │ Notifies (push / watch)
         ▼
  ┌──────────────┐
  │ Routing Tier │  Always knows the latest partition assignment.
  │ or Client    │
  └──────────────┘
```

1. Each database node registers itself in ZooKeeper, announcing which partitions it owns.
2. The routing tier (or client) **subscribes** to ZooKeeper for changes ("watches").
3. When a partition moves from Node A to Node B (due to rebalancing or failure recovery), ZooKeeper notifies all subscribers instantly.

### Which Databases Use What?
| Database | Routing Method |
|----------|---------------|
| HBase | ZooKeeper for region assignment |
| Kafka | ZooKeeper for partition leadership (moving to KRaft) |
| SolrCloud | ZooKeeper for shard routing |
| MongoDB | Config servers (custom, similar concept to ZK) |
| Cassandra | Gossip protocol (no central coordinator) |
| Riak | Gossip protocol (no central coordinator) |
| CockroachDB | Gossip + range metadata |

**Cassandra and Riak take a different approach:** They use a **gossip protocol** instead of a centralized coordinator. Nodes periodically exchange messages with each other, sharing their knowledge of partition assignments. Over time, all nodes converge on a consistent routing table. This avoids a single point of failure (no ZooKeeper dependency) but means routing information takes slightly longer to propagate after a change.

---

# Summary Cheat Sheet

```
┌─────────────────────────────────────────────────────────────────────┐
│                     CHAPTER 6 DECISION TREE                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Step 1: Choose a Partitioning Strategy                             │
│  ├─ Need range queries?            → Key Range Partitioning         │
│  ├─ Need even load distribution?   → Hash Partitioning              │
│  └─ Need both?                     → Compound Key (hash + range)    │
│                                                                     │
│  Step 2: Handle Secondary Indexes                                   │
│  ├─ Write-heavy?                   → Local Index (scatter/gather)   │
│  └─ Read/Search-heavy?             → Global Index (async updates)   │
│                                                                     │
│  Step 3: Choose a Rebalancing Strategy                              │
│  ├─ Know your final dataset size?  → Fixed # of partitions          │
│  ├─ Unknown growth?                → Dynamic partitioning           │
│  └─ Cluster growth is the driver?  → Per-node partitioning          │
│                                                                     │
│  Step 4: Route Requests                                             │
│  ├─ Simple setup?                  → Any-node proxy                 │
│  ├─ Need control?                  → Routing tier + ZooKeeper       │
│  └─ Max performance?               → Cluster-aware client           │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

# Key Terminology

* **Partition / Shard:** A subset of the total dataset, stored and served by one node.
* **Hot Spot:** A partition receiving disproportionately more read/write traffic.
* **Key Range Partitioning:** Assigning contiguous key ranges to partitions. Enables range scans but risks hot spots.
* **Hash Partitioning:** Hashing keys to assign them to partitions. Distributes evenly but destroys range query efficiency.
* **Compound Key:** First part hashed (for distribution), remaining parts sorted (for efficient within-partition range queries).
* **Local Index:** Each partition indexes only its own data. Writes fast, reads require scatter/gather.
* **Global Index:** One index covers all data, partitioned by term. Reads fast, writes slow (async).
* **Scatter/Gather:** Sending a query to all partitions and merging results. Expensive.
* **Rebalancing:** Moving partitions between nodes when the cluster changes.
* **Pre-Splitting:** Creating multiple empty partitions at database creation to avoid the cold-start single-partition bottleneck.
* **Gossip Protocol:** A decentralized protocol where nodes share routing state by chatting with each other.
* **ZooKeeper:** A centralized coordination service that tracks partition assignments and notifies routers of changes.

---

# Interview-Level Questions

1. **What is the difference between partitioning and replication?**
   → Replication: copies of the same data on multiple nodes (for fault tolerance). Partitioning: splitting different data across multiple nodes (for scalability).

2. **Why is `hash(key) % N` a terrible strategy for partitioning?**
   → Adding or removing a single node changes the modulo for almost every key, causing massive data movement.

3. **How does Cassandra's compound primary key work?**
   → First column is hashed (determines partition). Remaining columns are sorted within the partition (enables efficient range queries within a single partition key).

4. **What is the scatter/gather problem?**
   → With document-partitioned (local) secondary indexes, a search query must be sent to ALL partitions and results merged. A single slow partition creates tail latency for the entire query.

5. **When would you choose a global index over a local index?**
   → When reads/searches are far more common than writes, and you can tolerate eventual consistency on the index. DynamoDB's Global Secondary Indexes are a classic example.

6. **How does ZooKeeper help with request routing?**
   → Database nodes register their partition ownership in ZooKeeper. Routing tiers subscribe to changes. When a partition moves (rebalancing), ZooKeeper pushes the update to all subscribers immediately.

7. **How does Cassandra route requests without ZooKeeper?**
   → Gossip protocol. Every node knows the full partition map. Clients can contact any node; if it doesn't own the data, it proxies the request to the correct node.

8. **What is the "celebrity" problem and how do you fix it?**
   → A single extremely popular key (e.g., a viral post) causes a hot spot even with hash partitioning. Fix: append a random suffix to split the key across multiple partitions. Trade-off: reads must query all split keys and merge.
