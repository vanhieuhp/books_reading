# Chapter 4: Stability Patterns

## Chapter Overview

Chapter 4 introduces the "heroes" of software stability - design patterns that counteract the anti-patterns introduced in Chapter 3. Michael Nygard presents proven solutions to the stability challenges every software system faces. These patterns are the foundation of building resilient, production-ready systems.

## The Patterns

### 1. Circuit Breaker

**The Concept**
Inspired by electrical circuit breakers, this pattern prevents requests from being sent to a failing service. When failures exceed a threshold, the circuit "trips" and all requests fail immediately instead of waiting and consuming resources.

**How It Works**

```
Normal Operation:
Request → Service → Response (OK)

After Failure Threshold:
Request → Circuit Breaker → Fail Fast (Circuit Open)
```

**Three States**
1. **Closed** - Normal operation, requests pass through
2. **Open** - Circuit has tripped, requests fail immediately
3. **Half-Open** - Testing if service has recovered

**Implementation Considerations**
- Threshold: How many failures before tripping?
- Timeout: How long before trying again?
- Half-open requests: How many to allow through?
- Custom handling: What happens when circuit is open?

**When to Use**
- External API calls
- Database connections
- Any service with potential for failure

**Example Configuration**
```
Failure Threshold: 5 failures
Timeout: 30 seconds
Half-open requests: 3
```

---

### 2. Bulkhead

**The Concept**
Named after the watertight compartments in ships, bulkheads isolate failures to prevent them from spreading across the system.

**How It Works**
- Divide resources into isolated partitions
- Failure in one partition doesn't affect others
- Critical resources get dedicated partitions

**Types of Bulkheads**

**Thread Pool Bulkhead**
```
Pool A (10 threads) → Service A
Pool B (10 threads) → Service B
Pool C (10 threads) → Service C
```
If Service A hangs, pools B and C continue working.

**Connection Pool Bulkhead**
```
Database A Pool (20 connections)
Database B Pool (20 connections)
```
Problems with Database A don't exhaust connections for Database B.

**Process Bulkhead**
- Run critical components in separate processes
- Failure in one process doesn't crash others

---

### 3. Timeout

**The Concept**
Every operation that can fail should have a maximum time it will wait. Infinite waits are invitations to cascading failures.

**Implementation Principles**
- Set timeouts at every boundary
- Timeouts should be proportional to the operation
- Handle timeout exceptions explicitly
- Consider different timeout values for different scenarios

**Timeout Strategy**

| Operation | Typical Timeout |
|-----------|-----------------|
| Database query | 1-5 seconds |
| External API call | 5-30 seconds |
| Internal service call | 1-3 seconds |
| Cache lookup | 100-500ms |
| User-facing request | 30-60 seconds |

**The Problem with Default Timeouts**
- Frameworks often have no default or infinite default
- You must explicitly configure all timeouts
- Too short = false failures
- Too long = slow recovery

---

### 4. Handshake

**The Concept**
A protocol between client and server where both acknowledge capacity limits and respect them.

**How It Works**
1. Client requests permission to send work
2. Server responds with current capacity
3. Client sends work within limits
4. Server accepts or rejects based on capacity

**Real-World Examples**
- TCP congestion control
- HTTP 429 "Too Many Requests"
- JMS message brokers with prefetch limits
- Database connection request queueing

**Benefits**
- Prevents overload before it happens
- Provides backpressure
- Allows graceful degradation
- Client knows immediately when to back off

---

### 5. Decoupling (Middleware)

**The Concept**
Insert middleware between components to manage communication, add resilience, and provide loose coupling.

**Types of Middleware**

**Message Queues**
- Asynchronous communication
- Natural buffering
- Automatic retry
- Load leveling

**API Gateways**
- Rate limiting
- Authentication
- Request routing
- Protocol translation

**Service Mesh**
- Traffic management
- Security
- Observability
- Circuit breaking

**Benefits**
- Isolation between components
- Asynchronous processing
- Natural buffering
- Easier scaling

---

### 6. Fail Fast

**The Concept**
Detect problems early and fail immediately rather than waiting and accumulating problems.

**Implementation**
- Validate inputs at system boundaries
- Check resource availability before operations
- Verify preconditions before execution
- Return errors immediately rather than queuing

**When to Fail Fast**
- Insufficient resources
- Invalid state
- Precondition violations
- Unavailable dependencies

**Benefits**
- Failures are isolated
- Problem source is clear
- Resources aren't wasted
- Recovery is faster

---

### 7. Let It Crash

**The Concept**
Rather than trying to handle every possible error, let the component crash and restart in a known good state.

**When to Use**
- Unrecoverable state
- Resource corruption
- Unknown error conditions
- Process is in zombie state

**Implementation**
- Supervisor processes that restart failed components
- Stateless components that can restart cleanly
- Health checks to detect problems
- Graceful shutdown procedures

**Benefits**
- Simple error handling
- Known good state on restart
- No complex recovery logic
- Faster recovery than trying to repair

---

### 8. Bulkheads (Redux)

**The Concept**
Isolate critical resources so that failure in one area doesn't bring down everything.

**Application Levels**

**Application Level**
- Separate thread pools for different operations
- Separate database connections for different features

**Process Level**
- Run critical services in separate processes
- Container isolation

**Infrastructure Level**
- Separate databases for different services
- Isolated network segments
- Redundant infrastructure

---

### 9. Stable Topology

**The Concept**
Design your system architecture to minimize the blast radius of any single failure.

**Principles**
- Reduce dependencies
- Avoid single points of failure
- Design for graceful degradation
- Plan for component failure

**Topology Patterns**
- Hub and spoke (central hub, isolated spokes)
- Mesh (services interconnected but isolated)
- Tiered (layers with clear boundaries)

---

## Pattern Comparison

| Pattern | Primary Benefit | Best For |
|---------|-----------------|----------|
| Circuit Breaker | Prevents cascade failures | External APIs, databases |
| Bulkhead | Limits blast radius | Critical resources |
| Timeout | Prevents resource accumulation | All external calls |
| Handshake | Backpressure | High-volume systems |
| Middleware | Decoupling | Distributed systems |
| Fail Fast | Early detection | Input validation |
| Let It Crash | Clean recovery | Stateless services |
| Stable Topology | Reduced dependencies | System architecture |

## Implementation Priority

1. **Timeouts** - Easiest to implement, immediate benefit
2. **Circuit Breakers** - Essential for external calls
3. **Bulkheads** - For critical resources
4. **Handshake** - For high-volume systems
5. **Stable Topology** - Architectural decision

## Actionable Takeaways

1. **Add Timeouts Now** - Audit your code and add timeouts to all external calls
2. **Implement Circuit Breakers** - Start with external API integrations
3. **Isolate Critical Resources** - Use bulkheads for databases and thread pools
4. **Design for Failure** - Assume components will fail and plan for it
5. **Test Your Patterns** - Deliberately inject failures to verify patterns work

---

*Next: Part II - Design for Production*
