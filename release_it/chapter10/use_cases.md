# Section 5: Real-World Use Cases

## How Real Systems Apply These Patterns

---

## Use Case 1: Netflix — Handling Traffic Spikes with Zuul and Adaptive Load Shedding

### Problem
Netflix experiences massive traffic spikes during prime-time streaming hours and special events (e.g., new season releases). Traditional autoscaling couldn't keep up with sudden viewership spikes.

### Solution
Netflix built **Zuul** as their edge gateway with sophisticated load shedding:

1. **Circuit Breakers**: Zuul uses Hystrix (now Resilience4j) to prevent cascade failures to backend services
2. **Adaptive Throttling**: Per-client rate limiting based on historical patterns
3. **Request Buffering**: Queue requests with timeout, reject excess early
4. **Canary Deployments**: Gradually shift traffic to validate new code

### Scale / Impact
- **Peak traffic**: Millions of concurrent streams
- **Load shedding threshold**: Dynamically adjusted based on backend health
- **Recovery time**: Sub-second failover to alternate regions

### Lesson
> Load shedding must be at the **edge** (API gateway), not deep in the backend. Rejecting traffic closer to the client preserves backend capacity for legitimate requests.

---

## Use Case 2: Amazon — Prime Day Traffic Management

### Problem
Amazon's Prime Day generates traffic spikes that can exceed normal levels by 10-100x. The 2015 Prime Day experienced significant outages due to underestimated load.

### Solution
Amazon implemented comprehensive resilience:

1. **Pre-warming**: Reserve capacity days before known events
2. **Graceful Degradation**: Disable non-essential features (recommendations, reviews) under load
3. **Circuit Breakers**: All service-to-service calls protected
4. **Bulkheads**: Isolate critical path from auxiliary services
5. **Redundancy**: Multi-region failover

### Scale / Impact
- **Traffic spike**: 100x normal on checkout flow
- **Load shedding**: Returns 503 with Retry-After for non-critical services
- **Customer impact**: <1% error rate during peak

### Lesson
> **Capacity planning for known events is not optional**. Pre-warming instances before Prime Day is now standard practice.

---

## Use Case 3: Slack — Handling Workspace Migration Storms

### Problem
Slack experiences periodic "migration storms" when enterprise workspaces migrate between regions, causing sudden load spikes on backend services.

### Solution
Slack implemented:

1. **Progressive Rollout**: Migrate workspaces in batches with rate limiting
2. **Circuit Breakers**: Prevent migration traffic from affecting regular usage
3. **Load Shedding**: Return errors fast for migration traffic when system is stressed
4. **Exponential Backoff**: Client-side retries with jitter built into SDK

### Scale / Impact
- **Migration batches**: 50 workspaces at a time
- **Error rate during migration**: <0.1%
- **Recovery**: Automatic, no manual intervention

### Lesson
> **Every system has predictable spikes** (batch jobs, cron jobs, migrations). Design for them, don't just rely on autoscaling.

---

## Summary Table

| Company | Primary Challenge | Solution | Key Pattern |
|---------|------------------|----------|-------------|
| Netflix | Streaming spikes | Zuul gateway | Edge load shedding |
| Amazon | Prime Day | Pre-warming + degradation | Capacity planning |
| Slack | Migration storms | Circuit breakers + batch limits | Predictable spikes |

---

## Common Threads

All three companies share these practices:

1. **Design for peak, not average**
2. **Load shed at the edge**
3. **Circuit breakers everywhere**
4. **Pre-warm for known events**
5. **Monitor queue depth and error rates**

---

## Continue To

- **Section 6**: Core → Leverage Multipliers → `leverage_multipliers.md`
- **Section 7**: Code Lab → `code_lab.md`
- **Section 8**: Case Study → `case_study.md`
