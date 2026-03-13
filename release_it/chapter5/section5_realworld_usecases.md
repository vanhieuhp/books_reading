# Section 5: Real-World Use Cases

## How Industry Leaders Handle Infrastructure Variability

This section examines how major tech companies have dealt with the challenges described in Chapter 5 - the hidden complexity of virtualization and hardware failures.

---

## Use Case 1: Netflix — Chaos Engineering with Chaos Monkey

### Problem
Netflix's microservices architecture runs on AWS EC2, which means:
- Shared infrastructure with noisy neighbors
- Variable performance during VM migration
- Hardware failures in data centers

Traditional testing couldn't catch infrastructure-related failures because staging didn't match production's infrastructure behavior.

### Solution
Netflix pioneered **Chaos Engineering** - deliberately injecting failures to test resilience:

| Tool | Purpose |
|------|---------|
| Chaos Monkey | Terminates random instances |
| Chaos Gorilla | Simulates entire availability zone failure |
| Latency Monkey | Introduces network delays |
| Conformity Monkey | Finds and kills non-conformant instances |

### Implementation Details
- Runs in production during business hours
- Engineers must opt-out, not opt-in
- Designed to find "hidden" infrastructure problems

### Results
- **95% of experiments** revealed previously unknown failure modes
- Reduced mean time to recovery (MTTR) by 50%+
- Build confidence in auto-scaling and self-healing systems

### Staff-Level Lesson
> "The best time to find out your infrastructure assumptions are wrong is not during a customer-impacting outage."

---

## Use Case 2: Google — Borg and Zone-Level Failures

### Problem
Google runs at massive scale across multiple data centers. Their internal research showed:
- Hardware failures are **not if but when** events
- VMs can be relocated silently by hypervisor
- Network partitioning between zones is more common than expected

### Solution
Google's Borg system (predecessor to Kubernetes) implements:

1. **Workload spreading** - Distribute across failure domains
2. **Health checking** - Liveness probes detect infrastructure issues
3. **Preemption** - Lower priority jobs can be killed to make room
4. **Zone awareness** - Applications declare zone preferences

### Key Metrics Tracked
| Metric | Threshold | Action |
|--------|-----------|--------|
| CPU steal time | > 5% | Alert + consider migration |
| I/O wait | > 15% | Investigate storage |
| Memory pressure | > 80% | Add resources or scale |
| Network errors | > 1% | Check network health |

### Results
- Achieved 99.99%+ availability for critical services
- Zero-downtime upgrades across millions of containers
- Automated recovery from hardware failures in < 60 seconds

### Staff-Level Lesson
> "Design for failure at the infrastructure layer, not the application layer."

---

## Use Case 3: Amazon Web Services (AWS) — Multi-Tenant Reality

### Problem
AWS customers share infrastructure. When one tenant's workload spikes, it can affect neighbors - a phenomenon called the **"noisy neighbor" problem**.

AWS needed to provide isolation while maintaining cost efficiency.

### Solution
AWS introduced multiple tiers of isolation:

| Instance Type | Isolation Level | Use Case |
|--------------|-----------------|----------|
| Dedicated Instances | Physical hardware | Compliance, performance |
| Dedicated Hosts | Full server | Licensing, predictable performance |
| Isolated Tenants | Separate infrastructure | Highest security |

### AWS Observable Behaviors
For EC2, AWS publishes:
- **CPU Credits** - Burstable instances can run out
- **Network Performance** - Low/Medium/High/10 Gbps
- **EBS Volume Types** - Different I/O characteristics
- **Placement Groups** - Low-latency cluster networking

### Customer Experience
- Customers learned to:
  - Monitor CPU steal time (hidden metric!)
  - Use placement groups for latency-sensitive workloads
  - Choose instance types based on performance requirements
  - Design for variable performance, not guaranteed performance

### Staff-Level Lesson
> "Cloud providers sell reliability, but you rent it. Your SLA with customers must account for cloud limitations."

---

## Use Case 4: Uber — Infrastructure-Aware Scaling

### Problem
Uber's massive scale (millions of rides daily) meant:
- Infrastructure costs were significant
- Traffic patterns vary dramatically by time/region
- Database I/O became a bottleneck during surge pricing

### Solution
Uber built **infrastructure-aware auto-scaling**:

1. **Database load detection** - Scale based on DB metrics, not just request count
2. **Predictive scaling** - Pre-scale before expected traffic spikes
3. **Gradual rollout** - New instances roll out slowly to catch issues
4. **Canary deployments** - Small percentage of traffic to new instances

### Key Insight
```
Traditional: scale when CPU > 70%
Infrastructure-aware: scale when CPU > 70% AND DB connections < 80%
                    AND I/O wait < 10%
```

### Results
- Reduced infrastructure costs by 30%
- 50% fewer incidents during traffic spikes
- Improved P99 latency by 40%

### Staff-Level Lesson
> "Auto-scaling masks problems until they become incidents. Infrastructure-aware scaling reveals them early."

---

## Use Case 5: Cloudflare — Handling Network Variability

### Problem
Cloudflare runs a global network serving millions of websites. They discovered:
- Network paths between data centers vary in latency
- Some routes are highly variable (jitter)
- Packet loss correlates with specific network paths

### Solution
Cloudflare implemented:

1. **Multi-path routing** - Use multiple paths simultaneously
2. **Real-time network health** - Measure latency per route
3. **Traffic shifting** - Move traffic away from problematic paths
4. **Anycast routing** - Distribute load geographically

### Technical Details
- Measures RTT every 10ms per connection
- Routes around network issues automatically
- BGP anycast provides natural load distribution

### Results
- 99.999% uptime across network
- < 50ms latency for 95% of requests globally
- Automatic recovery from network failures in < 30 seconds

### Staff-Level Lesson
> "Network is the most variable infrastructure component. Design for 10x latency variance."

---

## Summary Table

| Company | Primary Challenge | Solution | Key Metric |
|---------|------------------|----------|------------|
| Netflix | Unknown failure modes | Chaos Engineering | MTTR |
| Google | Hardware failures | Borg + health checks | Availability |
| AWS | Noisy neighbors | Instance tiers | CPU steal |
| Uber | Traffic spikes | Infra-aware scaling | DB load |
| Cloudflare | Network variability | Multi-path routing | Jitter |

---

## Common Patterns Across All Use Cases

1. **Assume failure** - Design for infrastructure problems
2. **Measure everything** - You can't fix what you don't measure
3. **Fail fast** - Circuit breakers prevent cascading failures
4. **Automate recovery** - Humans are too slow
5. **Test in production** - Staging never matches reality

---

*Next: [Section 6 - Core → Leverage Multipliers](section6_leverage_multipliers.md)*
