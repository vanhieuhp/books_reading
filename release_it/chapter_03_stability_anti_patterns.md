# Chapter 3: Stability Anti-Patterns

## Chapter Overview

Chapter 3 introduces the "villains" of software stability - anti-patterns that systematically cause or contribute to system failures. Michael Nygard identifies and explains the common patterns that lead to unstable, fragile systems. Understanding these anti-patterns is essential before learning the corresponding patterns that solve them.

## The Anti-Patterns

### 1. Integration Points

**The Problem**
Integration points - where your code touches external systems - are the most fragile parts of any system. They represent boundaries where your control ends and the unpredictable begins.

**Why It's Dangerous**
- External systems can fail independently
- Network latency is variable and often poor
- You don't control the external system's behavior
- A single slow integration point can slow your entire system

**Common Manifestations**
- Database calls without timeouts
- HTTP requests to third-party APIs
- Message queue producers/consumers
- File system operations
- DNS lookups

**The Fix (Preview)**
- Timeouts on every external call
- Circuit breakers (covered in Chapter 4)
- Bulkheads to isolate failures

---

### 2. Resource Exhaustion

**The Problem**
Every system has finite resources: memory, connections, threads, file handles, bandwidth. When these resources are exhausted, the system fails - often catastrophically.

**Why It's Dangerous**
- Resource exhaustion often causes cascading failures
- It can happen gradually (memory leak) or suddenly (connection spike)
- Once exhausted, recovery is difficult
- Traditional monitoring often misses it until it's too late

**Common Manifestations**

**Connection Pool Exhaustion**
- Database connections not properly released
- Too many concurrent requests
- Long-running transactions holding connections

**Thread Pool Exhaustion**
- Blocking I/O without timeouts
- Thread pool too small for the workload
- Deadlocks between threads

**Memory Exhaustion**
- Memory leaks
- Unbounded caches
- Loading too much data into memory

**File Handle Exhaustion**
- Not closing files or connections
- Too many open files
- Socket exhaustion

**The Fix (Preview)**
- Set appropriate limits on all pools
- Monitor utilization levels
- Implement backpressure
- Use timeouts on all operations

---

### 3. Cascading Failures

**The Problem**
A failure in one component triggers failures in other components, causing a chain reaction that brings down the entire system.

**Why It's Dangerous**
- A single point of failure becomes a system-wide failure
- Recovery becomes impossible because everything is failing
- The original problem becomes irrelevant as secondary failures overwhelm

**How It Happens**
1. Component A depends on Component B
2. Component B becomes slow or unavailable
3. Component A waits for B, consuming resources
4. Component A runs out of resources
5. Component A fails
6. Components that depend on A also fail
7. Repeat until system is down

**Common Triggers**
- Timeouts without circuit breakers
- Retry storms
- Load spikes during outages
- Connection pool exhaustion

**The Fix (Preview)**
- Circuit breakers
- Bulkheads
- Bulkhead patterns
- Graceful degradation

---

### 4. Users as Load Generators

**The Problem**
Using production users to discover performance and stability problems is a catastrophic approach to testing.

**Why It's Dangerous**
- Users encounter problems first
- You have no control over the load
- Problems are discovered at the worst possible time
- Recovery is hampered by ongoing user activity

**This Includes**
- A/B testing in production without proper monitoring
- Rolling out new features without canary testing
- Deploying untested code to all users simultaneously

**The Fix (Preview)**
- Load testing in non-production environments
- Canary deployments
- Feature flags

---

### 5. Unbalanced Capacities

**The Problem**
When different components of a system have mismatched capacities, the weakest component determines overall system capacity.

**Why It's Dangerous**
- Expensive resources are wasted on the strong components
- The system is bottlenecked by the weakest link
- Scaling the wrong component wastes money

**Common Examples**
- Database can handle 1000 queries/second, application can send 10000
- Web servers can handle 10000 requests/second, but database can only handle 1000
- Network bandwidth exceeds database throughput

**The Fix (Preview)**
- Capacity planning
- Load testing
- Appropriate scaling

---

### 6. Slow Responses

**The Problem**
Slow responses consume resources and can trigger cascading failures.

**Why It's Dangerous**
- Slow responses hold connections, threads, and memory
- Clients may retry, doubling the load
- Timeout handling becomes critical
- User experience degrades significantly

**The Fix (Preview)**
- Timeouts everywhere
- Circuit breakers
- Fail fast

---

### 7. Self-Denial Attacks

**The Problem**
When a system experiences issues, certain behaviors can make things worse rather than better.

**Common Examples**

**Aggressive Retries**
- Immediate retries without backoff
- Retry storms that overwhelm recovering services
- No jitter in retry timing

**Growing Timeouts**
- When things are slow, waiting longer makes it worse
- Timeouts that increase during load

**The Fix (Preview)**
- Exponential backoff
- Jitter in retries
- Circuit breakers

---

## Summary Table

| Anti-Pattern | Symptom | Root Cause | Prevention |
|--------------|---------|------------|------------|
| Integration Points | Slow/blocked operations | External dependencies | Timeouts, circuit breakers |
| Resource Exhaustion | System unresponsive | Unbounded resource usage | Pool limits, monitoring |
| Cascading Failures | System-wide outage | Failure propagation | Bulkheads, circuit breakers |
| Users as Load Generators | Production incidents | Lack of testing | Load testing, canary deploys |
| Unbalanced Capacities | Unexpected bottlenecks | Poor capacity planning | Load testing, monitoring |
| Slow Responses | High latency | Blocking operations | Timeouts, async processing |
| Self-Denial Attacks | Amplified failures | Poor retry logic | Backoff, jitter |

## Actionable Takeaways

1. **Audit Your Integration Points** - Identify every external call and add timeouts
2. **Set Resource Limits** - Configure pool sizes for all resources
3. **Plan for Cascading Failures** - Implement circuit breakers and bulkheads
4. **Test Under Load** - Find bottlenecks before production
5. **Implement Proper Retry Logic** - Use exponential backoff with jitter

---

*Next: Chapter 4 - Stability Patterns*
