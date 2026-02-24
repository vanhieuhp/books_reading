# Chapter 10: Batch Processing

This is a comprehensive summary of **Chapter 10: Batch Processing** from *Designing Data-Intensive Applications* by Martin Kleppmann.

---

## Introduction: The Three Types of Systems

Kleppmann categorizes data systems into three types:

1. **Services (Online Systems):** A client sends a request and waits for a response. Measured by response time and availability. Example: a web server.
2. **Batch Processing Systems (Offline Systems):** Takes a large amount of input data, runs a job that processes it, and produces output data. The user doesn't wait for it. Measured by **throughput** (how much data per unit of time). Example: building a search index from a web crawl.
3. **Stream Processing Systems (Near-real-time):** Like batch, but operates on events as they arrive, with low latency. Example: fraud detection on credit card transactions.

This chapter focuses on batch processing — the oldest and most well-understood paradigm.

---

# 1. Batch Processing with Unix Tools

Before Hadoop, before MapReduce, there was the **Unix philosophy**. Kleppmann starts here because Unix pipes embody the same design principles that make MapReduce powerful.

## The Unix Philosophy
1. **Make each program do one thing well.**
2. **Expect the output of every program to become the input of another.**
3. **Design and build software to be tried early.** (Prototype quickly.)
4. **Use tools in preference to unskilled help.** (Automate everything.)

### Example: Log Analysis with Unix Pipes
```bash
cat /var/log/nginx/access.log |
  awk '{print $7}' |       # Extract the URL field
  sort |                    # Sort alphabetically 
  uniq -c |                 # Count unique URLs
  sort -rn |                # Sort by count descending
  head -5                   # Top 5 URLs
```

This pipeline processes a multi-gigabyte log file efficiently because:
* Each tool reads stdin and writes stdout (a **uniform interface**).
* The sort utility automatically spills to disk if data doesn't fit in RAM.
* Unix manages the piping; tools run in parallel (pipeline parallelism).

### Key Principles from Unix
* **Immutable inputs:** The input file is not modified. The output is a new stream.
* **No side effects:** Each tool has no state; the same input always produces the same output.
* **Composability:** You can rearrange, add, or remove stages freely.
* **Separation of logic and wiring:** Each tool contains logic; the shell handles the plumbing.

These are exactly the same principles that MapReduce builds on, but at datacenter scale.

---

# 2. MapReduce and Distributed Filesystems

## HDFS (Hadoop Distributed File System)

MapReduce reads and writes data on a **distributed filesystem**, most commonly **HDFS** (modeled after Google's GFS).

```
HDFS Architecture:
  ┌──────────────┐
  │  NameNode    │  (Tracks which blocks are on which DataNodes)
  └──────┬───────┘
         │
  ┌──────┼────────────────┐
  │      │                │
  ▼      ▼                ▼
┌──────┐ ┌──────┐ ┌──────┐
│DataN1│ │DataN2│ │DataN3│  (Store actual file blocks)
│Block │ │Block │ │Block │
│A, B  │ │A, C  │ │B, C  │  (Each block replicated 3x)
└──────┘ └──────┘ └──────┘
```

* Files are split into **blocks** (typically 128 MB each).
* Each block is **replicated** across 3 machines for fault tolerance.
* **NameNode** keeps metadata (file → block → DataNode mapping).
* **HDFS is designed for large files and sequential reads** — not random access.
* **Commodity hardware:** Unlike SAN/NAS storage, HDFS runs on cheap machines. Disk failures are expected and handled by replication.

## MapReduce: How It Works

MapReduce is a programming framework for batch processing on HDFS. A job has two stages:

### Step 1: Map
* The input file is split into chunks (one per HDFS block).
* A **Mapper function** is called once for each record in the input.
* The Mapper outputs zero or more key-value pairs.
* Mappers run in **parallel** across all nodes — one mapper per input split.

### Step 2: Reduce
* The framework **sorts and groups** all Mapper outputs by key. (This is the "shuffle.")
* All values for the same key are sent to the same **Reducer**.
* The Reducer function processes all values for a key and outputs the final result.

```
Example: Word Count

Input file (split across 3 nodes):
  "hello world"  "hello hadoop"  "world hello"

Map phase (run in parallel on 3 nodes):
  Mapper 1: ("hello", 1), ("world", 1)
  Mapper 2: ("hello", 1), ("hadoop", 1)
  Mapper 3: ("world", 1), ("hello", 1)

Shuffle (sort by key, group):
  "hadoop" → [1]
  "hello"  → [1, 1, 1]
  "world"  → [1, 1]

Reduce phase:
  Reducer("hadoop", [1])       → ("hadoop", 1)
  Reducer("hello", [1, 1, 1])  → ("hello", 3)
  Reducer("world", [1, 1])     → ("world", 2)

Output: hadoop:1, hello:3, world:2
```

### MapReduce Joins

A critical real-world use of MapReduce is **joining** datasets. Since data is spread across files, you can't do SQL-style joins directly. MapReduce provides several patterns:

#### Sort-Merge Join
1. Both datasets (e.g., Users and Activity Logs) are mapped to produce key-value pairs where the key is the join key (e.g., user_id).
2. The shuffle phase groups all records with the same user_id together.
3. The reducer sees both the user record and all their activity records, and joins them.

```
Users file:         Activity file:
  (user_1, Alice)     (user_1, "clicked button")
  (user_2, Bob)       (user_1, "viewed page")
                      (user_2, "logged in")

After shuffle (grouped by user_id):
  user_1 → [Alice, "clicked button", "viewed page"]
  user_2 → [Bob, "logged in"]

Reducer output:
  (Alice, ["clicked button", "viewed page"])
  (Bob, ["logged in"])
```

#### Broadcast Hash Join
If one dataset is small enough to fit in memory, it can be loaded into a hash map on every mapper. No shuffle needed — each mapper can join locally.

#### Partitioned Hash Join
If both datasets are partitioned the same way (same key, same number of partitions), each mapper only needs to read the corresponding partition from each dataset.

### Handling Skew (Hot Keys in MapReduce)
If one key has vastly more records than others (e.g., a celebrity user has millions of activity events), the reducer for that key becomes a bottleneck. Solutions:
* **Pig's Skewed Join:** Randomly distribute the hot key's records across multiple reducers; replicate the other side of the join to all of them.
* **Hive's Map-Side Join:** Detect hot keys in a sampling pass, then handle them specially.

---

# 3. Beyond MapReduce

MapReduce has significant limitations:
1. **Every job writes output to HDFS** — even intermediate results between jobs. This means lots of disk I/O and replication overhead.
2. **Multi-step workflows** (e.g., a chain of MapReduce jobs) are cumbersome. Each job must wait for the previous one to finish and write its output before starting.
3. **Mappers are often redundant.** Sometimes you just need a chain of sorts and aggregations without the full Map+Reduce formalism.

## Dataflow Engines: Spark, Tez, and Flink

Modern **dataflow engines** generalize MapReduce into a more flexible model:

* Instead of rigid Map→Shuffle→Reduce stages, they allow **arbitrary directed acyclic graphs (DAGs)** of operators.
* **Intermediate data stays in memory** (or on local disk) rather than being written to HDFS.
* Operators can be pipelined: the output of one operator is streamed directly to the input of the next, without materializing the full intermediate dataset.

```
MapReduce workflow (chained jobs):
  Job 1: Read HDFS → Map → Shuffle → Reduce → Write HDFS (💾)
  Job 2: Read HDFS (💾) → Map → Shuffle → Reduce → Write HDFS (💾)
  Job 3: Read HDFS (💾) → Map → Shuffle → Reduce → Write HDFS (💾)
  (Every intermediate result is written to disk and replicated!)

Spark DAG:
  Read HDFS → Map → Shuffle → Reduce → Map → Shuffle → Reduce → Write HDFS
  (Intermediate results kept in memory or on local disk. Much faster!)
```

### Apache Spark
* The most popular dataflow engine.
* Uses **RDDs (Resilient Distributed Datasets)** — fault-tolerant in-memory collections of data.
* If a partition of an RDD is lost (machine crash), Spark recomputes it from the original input data using the lineage graph (the DAG of transformations).
* **10-100x faster** than MapReduce for iterative algorithms (e.g., machine learning) because intermediate data stays in RAM.

### Apache Tez
* A dataflow engine designed to run on top of YARN (Hadoop's resource manager).
* Used by Hive and Pig as a backend execution engine (replacing MapReduce).

### Apache Flink
* A dataflow engine that treats **batch processing as a special case of stream processing** (a bounded stream). Unified model.

## Fault Tolerance in Dataflow Engines

MapReduce achieves fault tolerance by writing every intermediate result to HDFS. If a task fails, it simply re-reads the materialized input from disk.

Dataflow engines (like Spark) use a different approach:
* They track the **lineage** (sequence of operations) used to compute each partition.
* If a partition is lost, they **recompute it from scratch** by replaying the lineage from the original input file.
* For very long lineages, Spark allows you to **checkpoint** intermediate RDDs to HDFS — breaking the lineage chain.

---

# 4. Graphs and Iterative Processing

Some batch processing algorithms are **iterative** — they run the same computation repeatedly until convergence:
* **PageRank:** Google's original algorithm for ranking web pages. It iterates over the entire web graph multiple times.
* **Machine learning:** Training a model often involves many iterations (epochs) over the dataset.

MapReduce is terrible for this because each iteration requires reading/writing the entire dataset to HDFS. Spark handles it much better because intermediate data stays in memory.

### The Pregel Model (Bulk Synchronous Parallel)
For graph algorithms specifically, Google developed the **Pregel** model:
* The graph is partitioned across machines.
* Each vertex is a "unit of computation" that can send messages to its neighbors.
* Processing occurs in **supersteps**: in each superstep, every vertex processes incoming messages and sends new messages. After all vertices finish, the next superstep begins.
* Open-source implementations: **Apache Giraph**, **Spark GraphX**.

---

# Summary Cheat Sheet

```
┌────────────────────┬──────────────────────────────────────────────┐
│ Technology         │ Key Innovation                               │
├────────────────────┼──────────────────────────────────────────────┤
│ Unix Pipes         │ Composable, streaming, no side effects       │
│ MapReduce          │ Parallel batch processing on commodity HW    │
│ HDFS               │ Distributed FS with replication              │
│ Spark              │ In-memory DAG; 10-100x faster than MR        │
│ Tez                │ DAG engine for Hive/Pig on YARN              │
│ Flink              │ Unified batch + stream engine                │
│ Pregel             │ Graph-specific iterative processing model    │
└────────────────────┴──────────────────────────────────────────────┘
```

---

# Key Terminology

* **Batch Processing:** Processing a bounded dataset as a whole (not event-by-event).
* **MapReduce:** Two-phase (Map + Reduce) batch processing framework. Reads/writes HDFS.
* **HDFS:** Distributed file system. Files split into blocks, replicated across DataNodes.
* **Mapper:** Function that processes one input record and emits key-value pairs.
* **Reducer:** Function that processes all values for one key and emits final output.
* **Shuffle:** The MapReduce framework's sort-and-group step between Map and Reduce.
* **DAG (Directed Acyclic Graph):** A processing pipeline where operators can have multiple inputs and outputs, not just two rigid phases.
* **RDD (Resilient Distributed Dataset):** Spark's immutable, fault-tolerant in-memory data structure.
* **Lineage:** The chain of transformations from input to a derived dataset. Used for fault recovery.
* **Sort-Merge Join:** A MapReduce join pattern using the shuffle to bring matching records together.
* **Broadcast Hash Join:** Loading a small dataset into memory on every node to avoid shuffling.
* **Pregel / BSP:** Graph processing model where vertices exchange messages in synchronized supersteps.

---

# Interview-Level Questions

1. **What is the key design principle that Unix pipes and MapReduce share?**
   → Immutable inputs, no side effects, composability. Output of one stage flows into the input of the next. Each stage is a pure function.

2. **Why is MapReduce slower than Spark for iterative algorithms?**
   → MapReduce writes intermediate results to HDFS (disk + replication) after every job. Spark keeps intermediate data in memory (RDDs) and only writes the final output to HDFS.

3. **How does Spark handle fault tolerance without writing intermediate data to HDFS?**
   → Lineage. Spark tracks the sequence of transformations (the DAG) that produced each RDD partition. If a partition is lost, Spark recomputes it by replaying the transformations from the original input.

4. **What is the shuffle in MapReduce and why is it expensive?**
   → The shuffle sorts all mapper output by key and transfers it over the network to the correct reducer. It's expensive because: (a) all intermediate data must be written to disk, (b) network transfer of sorted data, (c) merging sorted runs at the reducer.

5. **What is a Sort-Merge Join in MapReduce?**
   → Both datasets emit key-value pairs using the join key. The shuffle groups records by key. The reducer sees all records from both datasets for the same key, performing the join locally.

6. **When would you use a Broadcast Hash Join instead of a Sort-Merge Join?**
   → When one dataset is small enough to fit in each mapper's memory. The small dataset is loaded into a hash map. No shuffle needed — each mapper joins locally. Much faster for star-schema joins (large fact table joined with small dimension tables).
