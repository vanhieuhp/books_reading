# Multi-Leader Replication Exercises

This folder contains Python scripts that simulate how real databases handle multi-datacenter setups, offline synchronization, and conflict resolution using multiple leaders.

## Prerequisites

No external libraries are required! You only need the Python Standard Library (3.8+).

If your console prints garbled characters instead of ✅ or 🔄, the scripts are configured to automatically force UTF-8 output on Windows, so that shouldn't happen.

## Step 1: Multi-Datacenter Setup

Run the first script:
```bash
python 01_basic_multi_leader.py
```

* **What to watch:** Notice how users in the US write to the US leader, and users in the EU write to the EU leader, getting extremely low latency.
* **The "a-ha" moment:** See what happens when the connection between the datacenters breaks (network partition). Both sites keep working normally! This is impossible in Single-Leader.

## Step 2: Write Conflicts & LWW

Run the second script:
```bash
python 02_write_conflicts.py
```

* **What to watch:** The system accepts two conflicting edits (one in US, one in EU) at exactly the same time.
* **The "a-ha" moment:** Observe how "Last Write Wins" (LWW) permanently deletes one of the user's edits to force the databases back into sync. LWW means data loss.

## Step 3: Custom Merging

Run the third script:
```bash
python 03_custom_resolution.py
```

* **What to watch:** Instead of throwing away data like LWW, this script shows how your application logic can intelligently merge concurrent updates.
* **The "a-ha" moment:** Watch how shopping cart items from both users are successfully unioned, preserving everyone's data.

## Step 4: CRDTs

Run the final script:
```bash
python 04_crdts.py
```

* **What to watch:** CRDTs are data structures that inherently resolve conflicts perfectly without manual code or custom application logic.
* **The "a-ha" moment:** Watch the G-Counter mathematically prove that `(A + B) = (B + A)`.

---

After running these 4 scripts, you've mastered Multi-Leader! You can now move on to the final replication pattern: **Leaderless Replication**.
