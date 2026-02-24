# Leaderless Replication Exercises

This folder contains Python scripts that simulate how real databases like Cassandra, DynamoDB, and Riak handle leaderless replication, quorum math, and self-healing.

## Prerequisites

No external libraries are required! You only need the Python Standard Library (3.8+).

The scripts automatically configure your console for UTF-8 so you can see all the fun emoji output (✅, 💥, 📦) properly.

## Step 1: Quorum Math

Run the first script:
```bash
python 01_quorum_math.py
```

* **What to watch:** The script will simulate different values for `w` (Write Quorum) and `r` (Read Quorum) against a 3-node cluster, where one node randomly fails or lags behind. 
* **The "a-ha" moment:** Notice how a configuration of `w=2` and `r=2` is mathematically immune to a single node failure or lag. But if `w=1` and `r=1`, you'll start reading stale data!

## Step 2: Read Repair

Run the second script:
```bash
python 02_read_repair.py
```

* **What to watch:** Node C goes down during a write. When Node C comes back online, a client performs a read.
* **The "a-ha" moment:** Observe how the client notices Node C's data is outdated compared to Node A. The client then patches Node C in the background to "heal" the system. 

## Step 3: Sloppy Quorums & Hinted Handoff

Run the third script:
```bash
python 03_sloppy_quorums.py
```

* **What to watch:** Two out of the three nodes assigned to store a piece of data crash. With a strict quorum, the database would return an error. But with a "Sloppy Quorum," it temporarily writes to completely unrelated nodes in the cluster.
* **The "a-ha" moment:** Watch the "Hinted Handoff" in action. When the original nodes restart, the borrowed nodes automatically detect it and forward the data back where it belongs!

---

🎉 After running these 3 scripts, you've completed all the practical examples for Chapter 5! You are now a master of replication across Single-Leader, Multi-Leader, and Leaderless architectures.
