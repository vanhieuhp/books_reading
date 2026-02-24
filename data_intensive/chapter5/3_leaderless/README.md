# Section 3: Leaderless Replication

This section contains hands-on Python exercises demonstrating **Leaderless (Dynamo-style) Replication**, based on Chapter 5 of *Designing Data-Intensive Applications* (DDIA).

## 🎯 Learning Objectives

By the end of these exercises, you will understand:
1. **Quorums:** How systems like Cassandra or DynamoDB ensure consistency without a leader by using the magic formula `w + r > n`.
2. **Self-Healing:** How Leaderless systems repair stale data on the fly using **Read Repair** when a client detects a discrepancy.
3. **High Availability:** How **Sloppy Quorums** and **Hinted Handoff** allow the database to keep accepting writes even when the intended destination nodes are completely offline.

## 📂 The Exercises

These exercises build on each other. Run them in order:

### 1. `01_quorum_math.py`
* **Topic:** Quorum Consistency (`w + r > n`)
* **Description:** Simulates writing across a cluster of 3 nodes, where one node might be slow or offline. You'll see how adjusting the Write Quorum (`w`) and Read Quorum (`r`) mathematically guarantees that a read will always overlap with the latest write, effectively hiding failures from the user.

### 2. `02_read_repair.py`
* **Topic:** Anti-Entropy via Read Repair
* **Description:** In leaderless systems, data can become stale on nodes that were offline during a write. This exercise demonstrates how the *client* acts as the repair mechanism: when reading from multiple nodes to satisfy quorum `r`, if the client notices one node has an older version, it actively writes the newer version back to that node to "heal" it.

### 3. `03_sloppy_quorums.py`
* **Topic:** Sloppy Quorums & Hinted Handoff 
* **Description:** What happens if so many nodes are offline that you can't even reach your Write Quorum (`w`)? Instead of returning an error, a **Sloppy Quorum** temporarily borrows *other* nodes in the cluster to accept the write. Once the original nodes come back online, the borrowed nodes perform a **Hinted Handoff** and pass the data back to its rightful owner.

## 📖 DDIA Reading Guide

These exercises map directly to the textbook:
* **Leaderless Replication Architecture:** pp. 177
* **Writing to the Database when a Node is Down:** pp. 177-178
* **Read Repair and Anti-Entropy:** pp. 178-179
* **Quorums for Reading and Writing:** pp. 179-183
* **Sloppy Quorums and Hinted Handoff:** pp. 183-184

## 🚀 Getting Started

Read the [`QUICKSTART.md`](QUICKSTART.md) file for instructions on running the code!
