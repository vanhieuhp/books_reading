# Real-World Use Cases — Stability Patterns in Production

This section documents how major tech companies apply stability patterns at scale.

---

## Use Case 1: Netflix — Circuit Breaker at Scale

### Problem
Netflix streams video to 200+ million subscribers globally. Their backend makes billions of calls daily between microservices. A single slow or failing service could cascade and bring down the entire streaming platform.

### Solution
Netflix pioneered the circuit breaker pattern, open-sourcing **Hystrix** (now in maintenance mode, replaced by **Resilience4j** and internal solutions).

**Implementation details:**
- Circuit breakers on every inter-service call
- Failure threshold: 50% error rate over 10 seconds (tuned per service)
- Timeout: Dynamic, calculated from historical p99 latency
- Fallback: Cached responses, degraded quality streams

### Scale / Impact
- **Billions** of circuit breaker calls daily
- Prevents cascading failures that would affect millions of users
- Enables "graceful degradation" (e.g., reducing video quality instead of failing entirely)

### Staff Insight
> *"At Netflix scale, even a 0.1% improvement in reliability prevents thousands of user-impacting incidents daily. The circuit breaker isn't just fault tolerance—it's the difference between a 5-minute degradation and a 5-hour outage."*

### Reusability
- Any system with multiple downstream dependencies
- API gateways, service meshes, microservice orchestrators
- Third-party API integrations

---

## Use Case 2: Amazon — Bulkhead Architecture for Reliability

### Problem
Amazon's e-commerce platform has thousands of services. A failure in product recommendations shouldn't affect checkout, and checkout failure shouldn't prevent users from viewing their cart.

### Solution
Amazon pioneered **service-oriented architecture** with strict bulkhead boundaries:

**Implementation details:**
- Separate thread pools per service (early 2000s)
- Later evolved to isolated processes/containers per service
- Separate databases for different domains (users, orders, products)
- Network segmentation to contain failures

### Scale / Impact
- 100+ million customers globally
- 99.99%+ uptime target for critical paths
- "Any sufficiently distributed system will experience partial failures"—Amazon designs for this reality

### Staff Insight
> *"The key insight: you can't prevent failures, but you can limit their blast radius. By isolating services, a failure in recommendations doesn't cascade to checkout. This architectural discipline is why Amazon can maintain 99.99% uptime while running thousands of services."*

### Reusability
- Any system with multiple independent services
- Multi-tenant SaaS platforms
- Systems with distinct failure domains

---

## Use Case 3: Stripe — Handshake for API Rate Limiting

### Problem
Stripe processes billions of dollars in payments daily. Their API receives massive traffic from millions of developers. Without proper backpressure, a single buggy client could exhaust server resources and affect all users.

### Solution
Stripe implements **handshake pattern** through their API:

**Implementation details:**
- Client must request API key with rate limit allocation
- Server responds with current capacity (429 responses when overloaded)
- Clients implement exponential backoff
- Usage-based pricing creates economic incentive for efficiency

**Technical implementation:**
- Token bucket algorithm for rate limiting
- Server-side queue with bounded capacity
- Client receives immediate feedback (no hanging requests)

### Scale / Impact
- Billions of API calls daily
- 99.999%+ uptime for payment processing
- Thousands of concurrent clients, each bounded

### Staff Insight
> *"Handshake isn't about limiting—it's about agreement. When clients know their limits and servers can enforce them, everyone wins. The client gets predictable behavior, the server stays healthy, and users never experience cascading failures from a single bad actor."*

### Reusability
- Public APIs with many clients
- Systems with usage spikes (e-commerce during Black Friday)
- Any system where client behavior needs to be controlled

---

## Use Case 4: Google — Timeout as First Line of Defense

### Problem
Google's internal microservices communicate extensively. A slow service can cause thread pool exhaustion across hundreds of dependent services. Before timeouts were standardized, a single bad deployment could bring down multiple teams' services.

### Solution
Google mandated **timeout policies** across their entire infrastructure:

**Implementation details:**
- Default timeout: 10 seconds for RPC calls
- Strict timeout enforcement at the infrastructure layer
- Timeout propagation through call chains
- "Deadline" concept (remaining time passed through context)

### Scale / Impact
- Billions of RPC calls per second internally
- Prevents "long tail" latency that degrades user experience
- Enables safe deployment (bad deployment times out instead of cascading)

### Staff Insight
> *"At Google's scale, the naive assumption that 'network is reliable' is fatal. Timeouts are the foundation—without them, nothing else matters because you'll just accumulate resources until you crash. Every engineer learns: if it can fail, it must have a timeout."*

### Reusability
- All inter-service communication
- Database operations
- Any I/O operation in production code

---

## Use Case 5: LinkedIn — Let It Crash with Supervision

### Problem
LinkedIn runs thousands of microservices. Traditional error handling tries to catch every exception, but complex recovery logic is error-prone and hard to maintain.

### Solution
LinkedIn adopted the **"Let It Crash"** pattern inspired by Erlang/OTP:

**Implementation details:**
- Stateless services that can restart cleanly
- Supervisor processes that detect failures and restart children
- Health checks to detect "zombie" processes
- Graceful shutdown to prevent orphaned work

**Implementation via Kubernetes:**
- Liveness probes detect stuck containers
- Pod restarts reset to known-good state
- Readiness probes prevent traffic to unhealthy instances

### Scale / Impact
- 800+ million members
- Thousands of microservices
- Mean time to recovery (MTTR) reduced from hours to minutes

### Staff Insight
> *"The radical insight: don't try to handle every error. If something goes wrong at the process level, the simplest solution is often to restart. Complex recovery logic introduces bugs; restart is simple and reliable. This is why containers and Kubernetes have become the standard— they embody 'let it crash' at the infrastructure level."*

### Reusability
- Stateless services
- Containerized microservices
- Systems where "reset" is safer than "repair"

---

## Pattern Application Summary

| Company | Primary Patterns | Scale | Key Insight |
|---------|-----------------|-------|--------------|
| Netflix | Circuit Breaker | Billions calls/day | Detect failure fast, fail fast |
| Amazon | Bulkhead | 100M+ users | Isolate failure domains |
| Stripe | Handshake | Billions API calls | Negotiate capacity limits |
| Google | Timeout | Billions RPC/sec | Foundation of all communication |
| LinkedIn | Let It Crash | 800M+ members | Restart > Repair |

---

## Common Thread

All these companies learned the same lesson:

> **"Production is not a happy path. It's a failure path with occasional success."**

Stability patterns aren't about preventing failure—they're about **containing failure** so that one problem doesn't become many.

---

## Discussion Questions for Your Team

1. **Map your dependencies**: Which services are in your critical path? Which are isolated?
2. **Find your blast radius**: If any single service fails, what's the maximum user impact?
3. **Identify timeouts**: Do all your inter-service calls have explicit timeouts?
4. **Test your resilience**: What happens when your database slows down by 10x? By 100x?
