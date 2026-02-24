# Advanced Replication Concepts

This section covers the final, deepest-dive concepts from Chapter 5 of *Designing Data-Intensive Applications*.

If you've mastered Single-Leader, Multi-Leader, and Leaderless, these exercises cover the advanced edge cases that distributed systems engineers face.

## 🎯 Learning Objectives

1. **Replication Topologies:** Understand how multi-leader setups physically arrange their network connections (Circular vs Star vs All-to-All), and how a single broken connection affects the entire global database depending on the topology.
2. **"Happens-Before" & Concurrency:** Understand why timestamps (Last-Write-Wins) are dangerously flawed due to clock skew. Learn how Dynamo and Riak use **Version Vectors** (Vector Clocks) to mathematically prove if two writes happened concurrently, or if one caused the other.

## 📂 The Exercises

### 1. `01_topologies.py`
Simulates Circular vs All-to-All multi-leader replication. You'll see how a single offline node in a Circular topology breaks the entire chain, while All-to-All provides redundancy (but introduces the risk of messages arriving out of order).

### 2. `02_version_vectors.py`
The crowning achievement of Leaderless architecture. Implements the exact algorithm Dynamo uses to detect data conflicts. Instead of using `time.time()`, we use a map of `[node_identifier: counter]` to track causality and prove what "actually happened first" in the system.

## 📖 DDIA Reading Guide
* **Multi-Leader Replication Topologies:** pp. 175-176
* **Detecting Concurrent Writes (The "Happens-Before" relationship):** pp. 184-187
* **Version Vectors:** pp. 188-189
