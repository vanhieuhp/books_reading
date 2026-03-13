# Case Study Templates by Domain

## Distributed Systems Case Studies

### Netflix — Chaos Engineering & Resilience
- **Hystrix circuit breaker**: Cascading failures → bulkhead pattern
- **Chaos Monkey**: Random instance termination → resilience culture
- **EVCache (memcached-based)**: Cross-region replication latency trade-offs

### Google — Spanner & Consistency
- **TrueTime API**: External consistency without coordination overhead
- **F1 database migration**: MySQL → Spanner, schema changes at scale
- **Bigtable → Spanner**: When strong consistency justified the cost

### Amazon / AWS
- **Dynamo paper (2007)**: Eventual consistency, vector clocks, sloppy quorum
- **S3 eventual consistency → strong consistency (2020)**: Engineering story
- **Aurora Global Database**: Replication across regions, RPO/RTO trade-offs

### Uber
- **Schemaless (MySQL at scale)**: Cell-based architecture, unbounded data growth
- **Ringpop**: Consistent hashing for service discovery
- **MySQL → TiDB migration**: HTAP trade-offs at ride-sharing scale

### Meta/Facebook
- **TAO (graph cache)**: Social graph, read-heavy, eventual consistency acceptable
- **Cassandra origin**: Write-heavy workload, no SPOF requirement
- **Haystack (photo storage)**: Object storage metadata overhead elimination

---

## Database Case Studies

### Indexing Trade-offs
- **Postgres B-tree vs GIN vs GiST**: Full-text search at Stack Overflow scale
- **MySQL covering indexes**: Shopify's order query optimization
- **Partial indexes**: Filtering inactive rows, Notion's approach

### Schema Evolution
- **Stripe**: Zero-downtime schema migrations at payment scale
- **GitHub**: Large table migrations (hundreds of millions of rows)
- **Braintree**: Adding columns to hot tables without locking

---

## Concurrency Case Studies

### Go Runtime
- **Docker daemon**: goroutine leak patterns, context cancellation
- **Kubernetes controller-manager**: Work queue, rate limiting, backoff
- **etcd**: Raft consensus, leader election in Go

### Java/JVM
- **Aeron messaging**: Lock-free algorithms, off-heap memory
- **Disruptor pattern**: LMAX exchange, ring buffer, false sharing

---

## Case Study Template for Any Topic

When generating a case study for a book chapter, use this template:

```
🏢 Organization: [Real company name]
📅 Year: [When this occurred/was published]
🔥 The Problem:
  - Context: [What they were building / their scale]
  - Pain point: [What broke or couldn't scale]
  - Why the existing solution failed: [Root cause]

🧩 Chapter Concept Applied:
  - Which exact concept from the chapter addresses this
  - Why this concept was the right tool

🔧 Solution:
  - What they actually built
  - Key design decisions made
  - What they had to give up (trade-offs)

📈 Outcome:
  - Quantified improvement (latency, cost, reliability)
  - Operational changes required

💡 Staff Insight:
  - What a staff engineer would generalize from this
  - The principle behind the solution (not just the solution itself)

🔁 Reusability Pattern:
  - Template: "When [condition], apply [concept] to achieve [outcome]"
  - Where else in your system you might see this pattern
```

---

## Finding Real Case Studies
- **High Scalability blog** (highscalability.com): Architecture breakdowns
- **AWS Architecture blog**: Production pattern write-ups
- **Google SRE book / Workbook**: Incident analysis, reliability patterns
- **DDIA (Designing Data-Intensive Applications)**: Martin Kleppmann's research compilation
- **InfoQ / QCon talks**: Real engineering decisions with context
- **Netflix Tech Blog**: Chaos, streaming, data engineering
- **Uber Engineering Blog**: Distributed systems, data platform
- **Stripe Engineering Blog**: Payments, reliability, migrations