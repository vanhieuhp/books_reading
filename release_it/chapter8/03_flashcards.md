# Chapter 8: Interconnect — Flashcards

## Card Set 1: DNS Fundamentals

### Card 1.1
**Q: What are the 6 operations that happen at every network boundary?**

**A:**
1. Protocol translation
2. Address resolution (DNS)
3. Connection establishment
4. Trust validation
5. Traffic routing
6. Translation back (response)

---

### Card 1.2
**Q: Why is low TTL on DNS records a double-edged sword?**

**A:**
- **Good**: Enables fast failover when you need to change IPs
- **Bad**: Increases DNS lookup traffic, adds latency from cache misses
- **Best practice**: Use lower TTL (5-15 min) for dynamic environments, higher (hours) for stable ones

---

### Card 1.3
**Q: What are the three common DNS failures that cause production incidents?**

**A:**
1. **Single provider failure** — No redundancy
2. **Stale cache** — High TTL prevents quick recovery
3. **Provider outage** — No monitoring means slow detection

---

## Card Set 2: Load Balancers

### Card 2.1
**Q: What's the difference between Layer 4 (L4) and Layer 7 (L7) load balancing?**

**A:**
- **L4**: Routes based on IP/port only. Faster, simpler, no content awareness
- **L7**: Routes based on URL, headers, cookies. Can do content-based routing, more expensive

Use L4 for high-throughput TCP/RPC, L7 for HTTP APIs needing path-based routing.

---

### Card 2.2
**Q: Why can health checks be dangerous if poorly designed?**

**A:**
- **Too simple**: Pass if port is open but app is hung
- **Too aggressive**: Cause flapping (false positives)
- **Too lenient**: Don't detect real failures quickly
- **Wrong endpoint**: Check /health instead of /health/ready

---

### Card 2.3
**Q: What are the trade-offs of session affinity (sticky sessions)?**

**A:**
- **Pros**: Enables caching, simplifies state management
- **Cons**: Can cause imbalanced load, makes scaling harder, limits failure isolation

---

## Card Set 3: Circuit Breakers

### Card 3.1
**Q: Why does a circuit breaker need BOTH a failure threshold AND a timeout?**

**A:**
- **Threshold alone**: Once open, stays open forever
- **Timeout alone**: Too sensitive, opens on transient blips
- **Together**: Opens after N failures, tries again after timeout

---

### Card 3.2
**Q: What are the three states of a circuit breaker?**

**A:**
1. **CLOSED**: Normal operation, requests flow
2. **OPEN**: Failing fast, requests return error immediately
3. **HALF-OPEN**: Testing recovery, limited requests allowed

---

### Card 3.3
**Q: Where should circuit breakers be placed in a microservices architecture?**

**A:**
- **Every network boundary**:
  - Service-to-service calls
  - Database connections
  - External API calls
  - DNS resolution
  - Load balancer health checks

---

## Card Set 4: Connection Management

### Card 4.1
**Q: What's the relationship between pool size, latency, and throughput?**

**A:**
- **Pool too small**: Requests wait for connections (queuing latency)
- **Pool too large**: Resource waste, increased memory, connection churn
- **Optimal**: Where throughput plateaus but latency is lowest

Rule of thumb: Size based on backend capacity, not frontend demand.

---

### Card 4.2
**Q: What are the four critical timeouts every network call needs?**

**A:**
1. **Connection timeout** — How long to establish connection
2. **Read timeout** — How long to wait for response
3. **Write timeout** — How long to send request
4. **Total timeout** — End-to-end budget

---

### Card 4.3
**Q: What causes connection pool exhaustion and how do you detect it?**

**A:**
**Causes**:
- Leaked connections (not returned to pool)
- Backend is slow (connections held too long)
- Pool sized too small for demand
- Network issues (connections stuck in TIME_WAIT)

**Detection**:
- Monitor pool utilization %
- Track waiters (threads waiting for connection)
- Alert on pool exhaustion

---

## Card Set 5: Firewalls & Segmentation

### Card 5.1
**Q: What's the difference between fail-open and fail-closed firewalls?**

**A:**
- **Fail-open**: On error, allow traffic (dangerous! Security risk)
- **Fail-close**: On error, deny traffic (safe but can break things)

Most should be fail-closed for security.

---

### Card 5.2
**Q: Why is network segmentation important for reliability?**

**A:**
- **Limits blast radius**: Failure in one segment doesn't affect others
- **Isolates failures**: Contain problems, prevent cascade
- **Independent scaling**: Each segment scales on its own
- **Security**: Isolate sensitive data, compliance requirements

---

## Card Set 6: Modern Patterns

### Card 6.1
**Q: What problems does a service mesh solve?**

**A:**
- **mTLS everywhere**: Automatic encryption between services
- **Observability**: Request traces across services
- **Traffic control**: Canary, blue-green, A/B deployments
- **Retry/timeout**: Centralized handling, no per-service code

---

### Card 6.2
**Q: Why is DNS-based load balancing different from L4/L7?**

**A:**
- **DNS-based**: Geographic routing, round-robin at DNS level
- **Advantages**: No infrastructure to manage, global by default
- **Disadvantages**: DNS caching negates quick changes, less control
- **Use for**: Geographic routing to nearest region

---

### Card 6.3
**Q: When should you use CDN for static content?**

**A:**
- **Yes**: Static assets (JS, CSS, images), global users, high traffic
- **No**: Dynamic content, personalized data, real-time updates

Benefits: Reduces latency, offloads origin, DDoS protection

---

## Card Set 7: Staff-Level Synthesis

### Card 7.1
**Q: A senior engineer is designing a new service that calls 3 external APIs. What interconnect decisions should they make upfront?**

**A:**
1. **Circuit breaker per API** (different thresholds based on reliability)
2. **Connection pool per API** (isolate blast radius)
3. **Different timeouts** (critical vs. optional APIs)
4. **Multiple DNS providers** for each API domain
5. **Retry strategy** with exponential backoff per API
6. **Monitoring**: DNS resolution time, connection pool health, circuit state

---

### Card 7.2
**Q: Your incident post-mortem shows "connection pool exhausted" as root cause. What systemic fixes prevent recurrence?**

**A:**
1. **Right-size pools**: Profile actual backend capacity
2. **Circuit breakers**: Stop hammering failing backend
3. **Backpressure**: Reject new requests when pool is full
4. **Timeouts**: Don't hold connections forever
5. **Monitoring**: Alert on pool utilization > 80%
6. **Load testing**: Verify pool can handle expected load

---

### Card 7.3
**Q: How do you convince leadership to invest in DNS redundancy?**

**A:**
- Calculate **total cost of DNS failure**: (users affected) × (SLA penalty per hour) × (expected downtime)
- Compare to **cost of redundancy**: 2 DNS providers × annual cost
- Show **precedent**: Reference GitHub 2016, other major DNS outages
- **Risk calculus**: Even 99.9% DNS = 8.76 hours/year downtime

---

*Flashcards generated for Release It! Chapter 8 - Interconnect*
