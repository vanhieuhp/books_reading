# Chapter 9, Section 5: Membership and Coordination Services

## Overview

This section covers **coordination services** — specialized systems that help distributed applications coordinate their behavior. The primary example is **ZooKeeper**, which provides:

- **Linearizable writes** via consensus (ZAB algorithm)
- **Ephemeral nodes** for failure detection
- **Watches** for reactive updates
- **Leader election** and distributed locks
- **Service discovery** and membership tracking

## Key Concepts

### What is a Coordination Service?

A coordination service is a small, highly reliable key-value store optimized for:
- Configuration management
- Leader election
- Distributed locks
- Service discovery
- Failure detection

It is **NOT** a general-purpose database. It's designed for metadata and coordination, not application data.

### ZooKeeper Architecture

```
┌─────────────────────────────────────────┐
│         ZooKeeper Cluster               │
├─────────────────────────────────────────┤
│  Leader (ZAB consensus)                 │
│  ├─ Follower 1                          │
│  ├─ Follower 2                          │
│  └─ Follower 3                          │
└─────────────────────────────────────────┘
         ▲
         │ Clients connect to any node
         │
    ┌────┴────┬────────┬────────┐
    │          │        │        │
  App 1      App 2    App 3    App 4
```

### Key Features

#### 1. Linearizable Writes
- All writes go through the leader
- Writes are totally ordered via ZAB consensus
- Once a write completes, all subsequent reads see the new value

#### 2. Serializable Reads (Not Linearizable by Default!)
- Reads can be served by any replica
- Reads might be stale
- To get linearizable reads, use the `sync` operation first

#### 3. Ephemeral Nodes
- A ZNode can be marked "ephemeral"
- If the client that created it disconnects, ZooKeeper automatically deletes it
- Perfect for leader election and failure detection

#### 4. Watches
- Clients can subscribe to changes on a ZNode
- When the ZNode changes, ZooKeeper pushes a notification
- Avoids polling and enables reactive updates

## Use Cases

### 1. Leader Election
```
Leader creates: /election/leader (ephemeral)
If leader crashes → node disappears → new election triggered
```

### 2. Service Discovery
```
Service registers: /services/database/node1 (ephemeral)
Clients watch: /services/database
When node1 crashes → watch fires → clients update routing
```

### 3. Distributed Locks
```
Client creates: /locks/resource (ephemeral)
Other clients wait for deletion
When holder crashes → lock auto-released
```

### 4. Configuration Management
```
Store config in: /config/database_url
Clients watch for changes
When config updates → clients get notified
```

## Real-World Examples

- **HBase**: Uses ZooKeeper for leader election and region server tracking
- **Kafka**: Uses ZooKeeper for broker coordination and topic management
- **Solr**: Uses ZooKeeper for cluster state and leader election
- **Hadoop**: Uses ZooKeeper for NameNode HA (High Availability)

## Files in This Section

- **README.md** (this file) — Overview and key concepts
- **TEACHING_GUIDE.md** — Deep explanations and learning progression
- **zookeeper_basics.py** — Basic ZooKeeper operations
- **leader_election.py** — Implementing leader election
- **service_discovery.py** — Service registration and discovery
- **distributed_locks.py** — Implementing distributed locks
- **failure_detection.py** — Detecting node failures via ephemeral nodes

## Quick Start

See [QUICKSTART.md](QUICKSTART.md) for hands-on examples.

## Key Takeaways

1. **Coordination services are specialized** — Not general-purpose databases
2. **Ephemeral nodes enable failure detection** — Auto-cleanup on disconnect
3. **Watches enable reactive updates** — No polling needed
4. **Linearizable writes, serializable reads** — Understand the difference
5. **ZooKeeper is the industry standard** — Used by Kafka, HBase, Hadoop, etc.

## Further Reading

- DDIA Chapter 9: "Consistency and Consensus"
- ZooKeeper documentation: https://zookeeper.apache.org/
- ZooKeeper paper: "ZooKeeper: Wait-free Coordination for Internet-scale Systems"
