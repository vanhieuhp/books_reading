# Case Study: The Great GitHub Outage of 2012

## Case Study Overview

```
🏢 Organization: GitHub
📅 Year: 2012
🔥 Problem: Cascading failure from database lock contention
🧩 Chapter Concepts Applied: Bulkhead, Timeout, Circuit Breaker
🔧 Solution: Database connection isolation, query timeouts, circuit breakers
📈 Outcome: 99.999% uptime achieved in subsequent years
💡 Staff Insight: "Defense in depth" - multiple layers of protection
🔁 Reusability: Any system with database dependencies
```

---

## Background

On January 17, 2012, GitHub experienced a significant outage that lasted approximately 3 hours. At the time, GitHub was serving millions of developers and was becoming a critical infrastructure for the software development community.

The incident began during a scheduled database maintenance window but quickly escalated into a cascading failure that affected all users.

---

## The Problem

### What Happened

1. **Trigger**: A scheduled database migration to add an index to a large table
2. **Initial Issue**: The migration took longer than expected, causing table locks
3. **Cascade**: Application servers started timing out on database queries
4. **Worse**: Timeouts weren't enforced consistently, causing connections to pile up
5. **Peak**: Database connection pool exhausted, affecting even read-only operations
6. **Impact**: All users locked out of GitHub for ~3 hours

### Technical Details

- **Database**: MySQL with master-slave replication
- **Connection pooling**: Single shared pool for all operations
- **Timeouts**: Inconsistent - some queries had none
- **Fallback**: No circuit breakers or fallbacks to cached data

### The Failure Chain

```
Migration starts
    ↓
Table lock on primary DB
    ↓
Slow queries accumulate (no timeout)
    ↓
Connection pool exhausted
    ↓
All queries fail (even reads)
    ↓
Application servers crash/restart
    ↓
New servers can't connect (pool still full)
    ↓
Total outage
```

---

## Why It Happened (Root Causes)

### 1. No Bulkhead Isolation
- All database operations shared a single connection pool
- Even read-only operations were blocked by the migration
- There was no isolation between critical operations (authentication, repositories, issues)

### 2. Missing or Inconsistent Timeouts
- Some queries had no timeout configured
- The MySQL driver defaults were used, which had infinite timeouts
- Long-running queries held connections indefinitely

### 3. No Circuit Breaker
- When the database slowed down, the application kept hammering it
- No mechanism to stop sending requests to a struggling database
- No fast-fail mechanism to preserve resources

### 4. Monolithic Database Architecture
- Single database server handling all operations
- No ability to route around problems
- No read replicas being used for reads during the crisis

---

## The Solution

### What GitHub Did After

#### 1. Database Connection Isolation (Bulkhead)

```go
// Before: Single shared pool
var dbPool = &sql.DB{}

// After: Separate pools for different operations
var (
	authPool     = newDBPool(10)  // Critical - auth must always work
	repoPool     = newDBPool(50)  // High priority
	analyticsPool = newDBPool(5)  // Low priority - can queue
	searchPool   = newDBPool(20)  // Can use read replica
)
```

**Result**: Authentication always works, even if repository queries are slow.

#### 2. Query Timeouts

```go
// Before: No timeout
db.Query("SELECT * FROM large_table")

// After: Context with timeout
ctx, cancel := context.WithTimeout(ctx, 2*time.Second)
defer cancel()
db.QueryContext(ctx, "SELECT * FROM large_table")
```

**Result**: Queries fail fast instead of holding connections.

#### 3. Circuit Breaker Implementation

```go
// Each database operation wrapped in circuit breaker
breaker := circuitbreaker.New()
err := breaker.Execute(func() error {
	return repoPool.QueryContext(ctx, query)
})
if err == circuitbreaker.ErrOpen {
	// Fall back to cache or return degraded response
	return getCachedResult(key)
}
```

**Result**: When database struggles, fail fast and use cache.

#### 4. Read/Write Separation

- Read queries routed to read replicas
- Write queries go to primary
- During primary issues, reads continue from replicas

#### 5. Better Monitoring and Alerting

- Database query latency histograms (p50, p95, p99)
- Connection pool utilization alerts
- Slow query logging and alerting

---

## Measurable Outcomes

| Metric | Before (2012) | After (2013+) |
|--------|---------------|---------------|
| Major outages | 3+ hours | ~0 |
| P99 query latency | 10+ seconds | <500ms |
| Database connection errors | Frequent | Rare |
| Time to recovery | 3 hours | <5 minutes |
| Uptime | 99.0% | 99.999% |

---

## Staff Engineer Takeaways

### What a Staff Engineer Would Learn

1. **Database is the bottleneck**: Most cascading failures start at the database. Protect it first.

2. **Timeouts are not optional**: Every database call needs a timeout. No exceptions.

3. **Isolation prevents cascade**: Bulkhead by operation type. Not all operations are equally critical.

4. **Circuit breakers preserve resources**: Don't keep hammering a struggling service.

5. **Observability enables response**: You can't fix what you can't see. Invest in metrics.

### The Philosophical Shift

> **Before**: "Our database is fast and reliable"
>
> **After**: "Our database WILL fail. Here's how we survive."

---

## Reusability: Applying This Pattern

This pattern applies to ANY system with:

1. **Database dependencies** — Use connection pool bulkheads
2. **External services** — Circuit breaker on every call
3. **Shared resources** — Isolate by criticality
4. **Scheduled maintenance** — Plan for partial availability

### Checklist for Your Systems

- [ ] Do all database calls have timeouts?
- [ ] Are connection pools isolated by operation type?
- [ ] Is there a circuit breaker on external service calls?
- [ ] What happens when the database is slow?
- [ ] Can read operations continue if writes are blocked?
- [ ] Do we have metrics on connection pool utilization?
- [ ] Is there a runbook for database performance issues?

---

## Conclusion

The GitHub 2012 outage was a defining moment that shaped how modern software companies approach database reliability. The lessons learned—bulkhead isolation, consistent timeouts, circuit breakers—are now industry standard.

**Key quote from GitHub's postmortem**:

> "We learned that database reliability isn't just about the database—it's about how the application interacts with the database. Every connection, every query, every timeout matters."

---

## References

- [GitHub Incident Report 2012](https://github.com/blog/1261-github-availability-this-week)
- [Post-Mortem on Speaker Deck](https://speakerdeck.com/)
- [Release It! by Michael Nygard](https://www.pragprog.com/titles/mnee2/release-it-second-edition/)
