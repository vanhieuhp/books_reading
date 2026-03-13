# Trade-offs & When NOT to Use — Staff-Level Analysis

This section is critical for staff engineers. Knowing **when NOT** to apply patterns is as important as knowing when to use them. The anti-patterns in Chapter 3 represent failures, but the solutions (timeouts, circuit breakers, bulkheads) also have costs.

---

## 1. Timeouts: The Goldilocks Problem

### The Trade-off

| Too Short | Just Right | Too Long |
|-----------|------------|----------|
| False failures | Reliable success detection | Resources held too long |
| Retries overwhelm service | Quick failure detection | Cascading risk |
| Customer-visible errors | Customer gets error message | Slow degradation |

### When to Use Short Timeouts (< 1 second)

- **High-speed internal APIs** — Services in the same datacenter with known latency
- **Cache lookups** — If cache misses, fall back to database
- **Non-critical operations** — Analytics, logging where eventual consistency is fine
- **Idempotent retry-friendly operations** — Safe to retry

### When to Use Long Timeouts (> 30 seconds)

- **Batch operations** — Long-running data processing
- **External APIs with SLA** — Payment processors, legacy systems
- **Complex queries** — Report generation, exports
- **Human-in-the-loop processes** — Approval workflows

### When NOT to Use Timeouts

1. **Single-threaded synchronous processing** — If timeout kills the only worker
2. **Operations without fallback** — If timeout means data loss
3. **Testing environments** — Timeouts can make debugging harder

### Hidden Costs

- **Configuration complexity** — Different timeouts for different operations
- **Debugging difficulty** — Is it a timeout or actual failure?
- **Customer experience** — Timeout feels like "the system is broken"

---

## 2. Connection Pools: Sizing is Hard

### The Trade-off

| Too Small | Just Right | Too Large |
|-----------|------------|-----------|
| Request queuing | Optimal throughput | Resource waste |
| Underutilized DB | Balanced load | Too many connections |
| Lost concurrency | Good parallelism | Context switching overhead |

### How to Right-Size

```
Formula: pool_size = (core_count * 2) + effective_spindle_count

But adjust for:
- Expected concurrent requests
- Average query duration
- Database max connections
- Application instance count
```

### When to Use Small Pools (< 20)

- **Microservices with low traffic** — < 100 RPS
- **Database as bottleneck** — If DB can't handle more connections
- **Cost-sensitive environments** — Fewer connections = fewer DB licenses

### When to Use Large Pools (> 100)

- **High-throughput systems** — > 10,000 RPS
- **Read-heavy workloads** — Can use many connections efficiently
- **Connection pooling proxy** — PgBouncer, ProxySQL handling connection multiplexing

### When NOT to Use Connection Pools

1. **Serverless functions** — Cold starts make pooling ineffective
2. **Very low traffic** — Pool maintenance overhead not worth it
3. **Short-lived processes** — Batch jobs that run once and exit

### Hidden Costs

- **Monitoring complexity** — Need metrics on pool utilization
- **Connection leaks** — One bug can exhaust the pool
- **Load balancer confusion** — Health checks may show healthy while pool is exhausted

---

## 3. Circuit Breakers: Don't Break What Isn't Broken

### The Trade-off

| Always Closed | Just Right | Always Open |
|---------------|------------|-------------|
| Cascading failures | Normal → Open → Half-open | No functionality |
| System-wide outages | Fast failure detection | Broken user experience |
| Complex configuration | Tuned thresholds | No trust in downstream |

### When to Use Circuit Breakers

- **External APIs** — Third-party services you don't control
- **Non-critical dependencies** — Feature flags, recommendations
- **Eventually-consistent operations** — Cache misses, analytics

### When NOT to Use Circuit Breakers

1. **Critical internal services** — If downstream is essential, circuit breaker doesn't help
2. **Synchronous must-have operations** — If you can't proceed without the data
3. **Single points of failure** — Can't circuit-break your only database

### Hidden Costs

- **State management** — Need to track failure counts, timing
- **Testing complexity** — Hard to test circuit breaker scenarios
- **Partial failures** — User sees "partial" functionality
- **Configuration tuning** — Wrong thresholds = false positives or negatives

### The Circuit Breaker Paradox

> "If a service is so unreliable that you need a circuit breaker, maybe you shouldn't depend on it at all."

Circuit breakers are a **symptom fix**, not a root cause fix. If a service needs a circuit breaker, that's a **design smell** — the dependency shouldn't be synchronous.

---

## 4. Bulkheads: Isolation Has Costs

### The Trade-off

| Shared (No Isolation) | Just Right | Over-Isolated |
|-----------------------|------------|---------------|
| Cascading failures | Failure containment | Resource waste |
| Simple configuration | Clear boundaries | Complex routing |
| Maximum resource use | Balanced | Underutilized resources |

### When to Use Bulkheads

- **Different failure domains** — Payment service vs. recommendation service
- **Different SLAs** — Critical path vs. nice-to-have
- **Different resource needs** — CPU-bound vs. I/O-bound
- **Team boundaries** — Different teams own different services

### When NOT to Use Bulkheads

1. **Monolithic applications** — Overhead not worth it
2. **Tightly coupled services** — Can't isolate what's coupled
3. **Very small systems** — Complexity > benefit
4. **Development/test environments** — Need simpler configuration

### Hidden Costs

- **Resource overhead** — Each bulkhead has its own pool
- **Routing complexity** — Need service discovery, load balancing per bulkhead
- **Monitoring complexity** — More metrics, more dashboards
- **Debugging difficulty** — Hard to trace across bulkheads

---

## 5. Retries: The Double-Edged Sword

### The Trade-off

| No Retries | Just Right | Aggressive Retries |
|------------|------------|--------------------|
| Lost requests | Graceful recovery | Retry storms |
| Single failure | Tolerance for blips | Amplified failures |
| Simpler code | Tuned backoff | Cascading overload |

### When to Use Retries

- **Transient failures** — Network blips, temporary overload
- **Idempotent operations** — Safe to retry
- **Eventually-consistent systems** — Write-behind, async processing
- **Non-critical operations** — Analytics, logging

### When NOT to Use Retries

1. **Non-idempotent operations** — Payment charges, sends
2. **Human-in-the-loop** — Approval workflows
3. **Synchronous critical path** — Can't proceed without success
4. **Already retrying upstream** — Don't double-retry

### Hidden Costs

- **Duplicate processing** — Idempotency keys needed
- **Resource consumption** — Retries use resources
- **Latency** — Each retry adds latency
- **Complexity** — Need idempotency, backoff, jitter

---

## 6. Backpressure: Making the Caller Wait

### The Trade-off

| No Backpressure | Just Right | Aggressive Backpressure |
|-----------------|------------|-------------------------|
| Resource exhaustion | Controlled degradation | User-visible errors |
| Unpredictable behavior | Predictable queuing | Customer complaints |
| Cascade to failure | Graceful slowdown | Lost work |

### When to Use Backpressure

- **Unbounded queues** — Prevent memory explosion
- **Resource limits** — When you can't scale infinitely
- **SLA protection** — Prevent long queuing delays

### When NOT to Use Backpressure

1. **Critical user requests** — Can't drop user input
2. **Low-traffic systems** — Overhead not worth it
3. **Consumer-driven systems** — Can't apply backpressure to producers

### Hidden Costs

- **User experience** — "Server busy" errors
- **Data loss** — Dropped requests = lost data
- **Complexity** — Need queue monitoring, timeout handling

---

## Summary Table: When to Use Each Pattern

| Pattern | Use When | Avoid When | Hidden Cost |
|---------|----------|------------|-------------|
| **Timeouts** | External calls, non-critical operations | Single-threaded, no fallback | Debugging complexity |
| **Connection Pools** | High concurrency, reusable connections | Serverless, short-lived processes | Leak potential |
| **Circuit Breakers** | Unreliable external services | Critical synchronous dependencies | State management |
| **Bulkheads** | Team boundaries, different SLAs | Monoliths, tightly coupled | Resource overhead |
| **Retries** | Transient failures, idempotent ops | Non-idempotent, critical path | Double processing |
| **Backpressure** | Unbounded queues, resource limits | Critical user requests | Data loss |

---

## The Staff Engineer's Decision Framework

When deciding whether to apply any resilience pattern, ask:

1. **What failure are we protecting against?** — Be specific
2. **What's the cost of the failure?** — Quantify if possible
3. **What's the cost of the protection?** — Complexity, overhead, latency
4. **Is there a simpler solution?** — Maybe just fix the underlying issue
5. **What's the operational complexity?** — Can the team maintain it?

> "The best code is the code you don't write. The second best is code that's simple to understand and operate."

---

## Final Thought: The Anti-Pattern to Anti-Patterns

The real anti-pattern is **over-engineering resilience** when simpler solutions exist:

- **Add circuit breaker** → Maybe just add a timeout
- **Add bulkhead** → Maybe just fix the slow dependency
- **Add retry with backoff** → Maybe the operation shouldn't be synchronous

**Start simple. Add complexity only when you have evidence it's needed.**

---

*Continue to Section 10: Chapter Summary & Review Hooks*
