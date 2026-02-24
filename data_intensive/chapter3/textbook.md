Cool — **Chapter 3 (Storage & Retrieval)** is where DDIA stops being “app design” and starts being “how databases actually work”.

I’ll teach it in a way you can *practice*, not just read: **concept → mental model → mini experiments → a toy storage engine**.

---

## What Chapter 3 is really about

When you do:

```sql
SELECT ... WHERE key = ?
```

Chapter 3 explains what happens behind the scenes:

* how data is laid out on disk
* how indexes find data fast
* why writes are often “append-only”
* why compaction exists
* why reads can be fast even when data is huge

The core theme:

> Storage engines optimize a trade-off between **write performance**, **read performance**, and **space amplification**.

---

# Chapter 3 topics you must master

You’ll meet two “families” of storage engines:

## 1) B-Tree family (classic OLTP)

* Used by many relational DBs
* Updates in-place (conceptually)
* Great for point lookups + range queries
* Index is a tree of disk pages

**Key ideas**

* pages (fixed-size blocks)
* page splits/merges
* random I/O vs caching
* write-ahead log (WAL) for crash safety

## 2) LSM-Tree family (Log-Structured Merge)

* Used by RocksDB, LevelDB, Cassandra internals, etc.
* Writes are fast (append)
* Reads may check multiple places
* Compaction merges sorted files in background

**Key ideas**

* WAL + memtable
* SSTables (sorted string tables)
* compaction
* bloom filters (avoid unnecessary disk reads)
* write amplification

---

# A practical learning plan for Chapter 3 (7–10 days)

## Day 1 — “Disk reality” + append-only logs

**Learn**

* sequential vs random I/O
* why appending is cheap
* why updates-in-place are expensive

**Practice**

* Write a tiny append-only log file writer/reader in Python
* Record: `put(key,value)` lines

Outcome: you *feel* why logs are used.

---

## Day 2 — Hash index vs range queries

**Learn**

* hash index: fast point lookup, bad at ranges
* range queries require order

**Practice**

* Build an in-memory hash index mapping `key → file_offset`
* Support:

  * `get(key)` fast
  * `scan(prefix)` is painful (you’ll see why)

---

## Day 3–4 — B-Tree mental model (pages + fanout)

**Learn**

* data stored in pages
* B-tree node contains many keys (high fanout)
* search is log base ~100 (very shallow)

**Practice**

* Implement a simplified B-tree in memory (optional)
  OR (easier & more realistic):
* Use Postgres/SQLite and compare performance with/without index:

  * insert 1M rows
  * query by key
  * query by range

You’ll see why indexes matter.

---

## Day 5–7 — Build a tiny LSM KV-store (best practice task)

This is the “I truly understand Chapter 3” project.

### Features to implement (minimal but real)

1. **WAL** (write-ahead log)
2. **Memtable** (in-memory sorted map)
3. Flush memtable to disk as an **SSTable** (sorted file)
4. `get(key)` searches:

   * memtable first
   * then newest SSTable → oldest
5. **Compaction**:

   * merge two SSTables into one (drop overwritten keys)

### Optional upgrades (very DDIA)

* Bloom filter per SSTable
* Sparse index (key every N lines)
* Tombstones for deletes

---

## Day 8–9 — OLAP / column stores (why they’re different)

**Learn**

* row store = great for “get one record”
* column store = great for “sum over billions”
* compression works better with columns

**Practice**

* Create a dataset (csv) with 5 columns, 5M rows
* Implement 2 ways to compute `sum(amount) where type=...`:

  * row-by-row
  * column-by-column arrays
    You’ll see why column stores win analytics.

---

## Day 10 — Wrap-up: choose engine by workload

Make a decision guide for yourself:

* OLTP + range queries → B-tree
* write-heavy + log/stream ingestion → LSM
* analytics aggregations → column store / OLAP system

---

# The “Chapter 3 cheat sheet” (what you should remember)

* **WAL**: crash safety; “write log first”
* **Index**: structure that reduces disk reads
* **B-tree**: optimized for read + range queries, page-based
* **LSM**: optimized for writes, compaction later
* **Compaction**: pays the cost later; causes write amplification
* **Bloom filter**: avoids reading SSTables that definitely don’t contain the key
* **Row vs column**: row for transactions, column for analytics

---

# How we’ll do it together (teaching style)

If you want, we can go step-by-step like this:

1. I give you a tiny task (20–40 lines)
2. You implement
3. You paste code
4. I review like a senior and explain “what part of DB it represents”

---

## Pick your Chapter 3 practice path (no wrong answer)

A) **Hands-on build**: toy LSM KV-store in Python (most learning)
B) **SQL experiments**: Postgres indexing + explain plans (more DB practical)
C) **Both** (fastest mastery)

Reply with **A / B / C** and I’ll start Lesson 1 immediately with the first concrete task + code skeleton.
