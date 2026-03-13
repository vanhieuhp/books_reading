# Chapter 8: Interconnect

## Chapter Overview

Chapter 8 addresses the complex reality of network interconnect - how services, databases, and external systems communicate. Michael Nygard explores the challenges of DNS, load balancers, firewalls, and the networks that connect everything. Understanding interconnect is essential because network boundaries are where many failures occur.

## The Network Boundary

### What Happens at Boundaries

At every boundary between systems:
- Protocols translate
- Addresses resolve
- Connections establish
- Trust validates
- Traffic routes

### Types of Interconnect

**Internal**
- Service-to-service communication
- Database connections
- Internal APIs
- Message queues

**External**
- Third-party APIs
- Customer integrations
- Partner systems
- Public internet traffic

## DNS

### DNS Fundamentals

**How DNS Works**
1. Client queries local resolver
2. Resolver queries root server
3. Root points to TLD server
4. TLD points to authoritative server
5. Authoritative returns IP address
6. Client caches result

**TTL (Time To Live)**
- How long to cache the result
- Lower = faster changes
- Higher = more stable
- Must balance flexibility vs. performance

### DNS Challenges

**DNS Failures**
- When DNS fails, nothing works
- No graceful degradation
- Hard to diagnose
- Cascading impact

**DNS-based Attacks**
- DNS amplification
- DNS spoofing
- DDoS on DNS providers

**Common DNS Problems**
- Long TTL causing stale records
- Low TTL causing cache misses
- DNS provider failures
- Geographic routing issues

### DNS Best Practices

1. **Multiple DNS Providers**
   - Use at least two
   - Different networks
   - Regular testing

2. **Appropriate TTLs**
   - Low TTL for dynamic environments
   - Higher TTL for stability
   - Plan for changes

3. **Monitoring**
   - DNS resolution time
   - DNS failure rates
   - Record changes

4. **Fallback**
   - Multiple A records
   - CNAME chains
   - Client-side fallback

## Load Balancers

### Types of Load Balancing

**Layer 4 (Transport)**
- Based on IP and port
- Faster, simpler
- No content awareness
- Examples: HAProxy (basic), AWS NLB

**Layer 7 (Application)**
- Based on URL, headers, cookies
- Content-aware routing
- More expensive
- Examples: HAProxy (advanced), AWS ALB, Nginx

**DNS-based**
- Geographic routing
- Round-robin
- Health check integration
- Example: Route 53

### Load Balancing Algorithms

| Algorithm | Description | Use Case |
|----------|-------------|----------|
| Round Robin | Sequential | Equal instances |
| Least Connections | Fewest active | Variable workloads |
| IP Hash | Consistent client | Session affinity |
| Weighted | Capacity-based | Different instance sizes |
| Adaptive | Real-time load | Dynamic environments |

### Load Balancer Challenges

**Single Point of Failure**
- Load balancer itself must be highly available
- Active-passive or active-active
- Multiple AZs

**Health Check Design**
- How to determine healthy?
- What to check?
- How often?
- Timeout handling?

**Session Affinity**
- Also called "sticky sessions"
- Not always needed
- Adds complexity
- Can cause imbalance

**SSL Termination**
- CPU intensive
- Certificate management
- Protocol choices

## Firewalls

### Firewall Basics

**What Firewalls Do**
- Filter traffic based on rules
- Allow/deny by IP, port, protocol
- Stateful vs stateless
- Network and application layer

### Firewall Challenges

**Rule Complexity**
- Thousands of rules
- Conflicting permissions
- Hard to audit
- Documentation drift

**Latency**
- Packet inspection adds latency
- Deep packet inspection more
- Rule optimization needed

**Fail Open vs. Fail Closed**
- Fail open: Allow on error (dangerous)
- Fail closed: Deny on error (safe but disruptive)

### Firewall Best Practices

1. **Minimal Rules**
   - Only what's needed
   - Deny by default
   - Regular review

2. **Explicit Logging**
   - Log denied traffic
   - Alert on anomalies
   - Retention policies

3. **Testing**
   - Regular penetration testing
   - Rule validation
   - Simulated attacks

## Network Segmentation

### Why Segment

**Security**
- Limit blast radius
- Isolate sensitive data
- Compliance requirements

**Performance**
- Reduce contention
- Prioritize traffic
- QoS implementation

**Reliability**
- Isolate failures
- Contain problems
- Independent scaling

### Segmentation Strategies

**DMZ**
- Public-facing services
- Limited access
- Additional layer

**VPCs**
- Cloud network isolation
- Private subnets
- Transit gateways

**Service Mesh**
- Service-to-service encryption
- Fine-grained control
- Observability

## Circuit Breaking at Network Level

### Network Circuit Breakers

**Beyond Application Circuit Breakers**
- Hardware failures
- Network partitions
- ISP outages
- CDN failures

### Strategies

1. **Multiple Providers**
   - Multiple internet connections
   - Different ISPs
   - Automatic failover

2. **Geographic Distribution**
   - Multiple regions
   - CDN for static content
   - DNS-based failover

3. **Redundant Paths**
   - Multiple routes
   - Diverse paths
   - No single points

## Connection Management

### Connection Pools

**Why Pools**
- Connection setup is expensive
- Limits prevent overload
- Reuse improves performance

**Pool Sizing**
- Too small = contention
- Too large = resource waste
- Monitor utilization

**Pool Problems**
- Leaks
- Exhaustion
- Stale connections

### Timeouts

**Critical Timeouts**
- Connection timeout
- Read timeout
- Write timeout
- Total timeout

**Timeout Best Practices**
- Always set timeouts
- Different timeouts for different operations
- Handle timeout errors explicitly

## Modern Interconnect Patterns

### API Gateways

**What They Provide**
- Single entry point
- Authentication
- Rate limiting
- Request routing
- Protocol translation

### Service Mesh

**Benefits**
- mTLS everywhere
- Fine-grained traffic control
- Observability
- Retry/timeout handling

### CDN

**For Static Content**
- Reduce latency
- Offload traffic
- DDoS protection

## Common Pitfalls

### DNS Pitfalls
1. Single DNS provider
2. TTL too high (can't change) or too low (cache misses)
3. No monitoring
4. Wildcard certificates on wrong domain

### Load Balancer Pitfalls
1. No health checks
2. Health checks too simple
3. Single load balancer
4. No SSL monitoring

### Firewall Pitfalls
1. Overly permissive rules
2. No logging
3. Firewall as single point
4. Not testing rules

### Network Pitfalls
1. No redundancy
2. Ignoring latency
3. Oversubscribing bandwidth
4. No segmentation

## Actionable Takeaways

1. **Design for Network Failure** - Nothing is guaranteed
2. **Multiple DNS Providers** - Don't rely on one
3. **Health Checks Matter** - Design them carefully
4. **Monitor Everything** - Network metrics are crucial
5. **Use Timeouts** - Every network call needs timeout
6. **Segment Your Network** - Limit blast radius
7. **Test Failures** - Kill connections, observe behavior

---

*Next: Chapter 9 - Control Plane*
