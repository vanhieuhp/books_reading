# Section 2: Multi-Leader Replication

This section contains hands-on Python exercises demonstrating **Multi-Leader Replication**, based on Chapter 5 of *Designing Data-Intensive Applications* (DDIA).

## 🎯 Learning Objectives

By the end of these exercises, you will understand:
1. **Why Multi-Leader?** How having multiple leaders solves the write-bottleneck and high-latency cross-datacenter issues of the single-leader pattern.
2. **The Conflict Problem:** Why concurrent writes in a multi-leader system inevitably lead to data divergence.
3. **Conflict Resolution:** How different strategies (like Last Write Wins and Custom Merging) handle conflicts, and the trade-offs of each.
4. **CRDTs:** How Conflict-Free Replicated Data Types magically resolve conflicts mathematically.

## 📂 The Exercises

These exercises build on each other. Run them in order:

### 1. `01_basic_multi_leader.py`
* **Topic:** Multi-Datacenter Setup & Local Writes
* **Description:** Simulates two datacenters (e.g., US-East and EU-West), each with its own leader. Shows how users get ultra-fast local writes, and how leaders replicate their logs to each other in the background. Shows what happens when one datacenter goes offline (the other keeps working!).

### 2. `02_write_conflicts.py`
* **Topic:** Concurrent Writes and Last Write Wins (LWW)
* **Description:** The nightmare scenario! User A updates a record in the US, while User B concurrently updates the *same* record in the EU. Demonstrates how the system diverges, and how the naive "Last Write Wins" (LWW) approach blindly destroys data to restore consistency.

### 3. `03_custom_resolution.py`
* **Topic:** Application-Level Custom Merging
* **Description:** Instead of blindly deleting data with LWW, this exercise shows how to use domain knowledge to merge conflicts. You'll see examples like a shopping cart (union of items) and a collaborative text document (appending both users' edits).

### 4. `04_crdts.py`
* **Topic:** Conflict-Free Replicated Data Types
* **Description:** An introduction to CRDTs. Implements a simple Grow-Only Counter (G-Counter) and an Observed-Remove Set (OR-Set). Demonstrates how these mathematically proven data structures naturally converge without explicit conflict resolution logic.

## 📖 DDIA Reading Guide

These exercises map directly to the textbook:
* **Multi-Leader Replication:** pp. 168
* **Use Cases (Multi-datacenter, Offline clients):** pp. 168-171
* **Handling Write Conflicts:** pp. 171
* **Conflict Resolution Strategies:** pp. 173-174
* **CRDTs (Automatic Conflict Resolution):** pp. 174-175

## 🚀 Getting Started

Read the [`QUICKSTART.md`](QUICKSTART.md) file for instructions on running the code!
