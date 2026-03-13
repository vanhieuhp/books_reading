# Section 9: Analysis — Trade-offs & When NOT to Use This

## Staff-Level Trade-off Analysis

---

## Use Load Shedding When:

### ✅ Condition 1: You Have Predictable Traffic Patterns
- Known peak times (e-commerce during holidays)
- Scheduled events (product launches, marketing campaigns)
- Batch job windows

**Why**: You can tune thresholds based on historical data.

### ✅ Condition 2: Core vs. Non-Core Functions Are Clear
- You know which requests are critical (checkout, login)
- You know which can be degraded (recommendations, search)

**Why**: Load shedding requires knowing what to protect.

### ✅ Condition 3: Clients Can Handle 503 Gracefully
- Your mobile/web app shows friendly error messages
- API consumers implement retry with backoff

**Why**: Rejected requests will fail. Make sure failure is graceful.

---

## Avoid Load Shedding When:

### ❌ Condition 1: Traffic Is Unpredictable (Novel Product)
- Early-stage product with unknown traffic patterns
- Viral potential you want to capture

**Why**: You might shed legitimate traffic you could have served.

### ❌ Condition 2: All Requests Are Equally Critical
- No way to prioritize checkout over browsing
- Every request is a revenue opportunity

**Why**: Shedding any request is revenue loss.

### ❌ Condition 3: Clients Don't Handle Rejection Well
- Legacy clients without retry logic
- Users will blame bugs, not load

**Why**: Rejection feels like a bug to users.

---

## Hidden Costs (What the Book Might Not Say)

### 1. Operational Complexity

| Cost | Description |
|------|-------------|
| Tuning effort | Thresholds require ongoing tuning |
| Monitoring | Need to monitor shedding events |
| On-call | Need to respond to shedding alerts |
| Testing | Load testing is required to validate |

**Staff insight**: Load shedding adds 2-3 hours/week of operational work. Budget for it.

### 2. Team Skill Requirements

- **SRE/DevOps**: Must understand the patterns
- **Development**: Must implement fallbacks
- **Product**: Must define priorities

**Staff insight**: If your team is already stretched thin, adding load shedding might cause more harm than good.

### 3. Migration Path

| Scenario | Approach |
|----------|----------|
| New service | Add from day one |
| Existing service | Add incrementally, behind feature flag |
| Acquisition/integration | Gradual rollout |

**Staff insight**: Retrofitting load shedding is harder than building it in. Plan ahead.

---

## Circuit Breaker Trade-offs

### When to Use Circuit Breakers

| Condition | Use CB? |
|-----------|---------|
| Multiple downstream services | ✅ Yes |
| Critical path depends on external service | ✅ Yes |
| Service has known failure modes | ✅ Yes |

### When Circuit Breakers May Be Overkill

| Condition | Avoid CB? |
|-----------|-----------|
| Single, reliable dependency | ❌ Overhead |
| Simple CRUD service | ❌ Unnecessary |
| Development/staging | ❌ Adds complexity |

### Hidden Costs of Circuit Breakers

1. **Configuration complexity**: Threshold, timeout, half-open settings all need tuning
2. **Fallback implementation**: Every breaker needs a fallback (more code)
3. **Testing difficulty**: Breakers are hard to test in integration
4. **Debugging**: "Why did the breaker open?" requires tracing

---

## Retry with Backoff Trade-offs

### The Retry Storm Danger

The biggest trade-off is between **resilience** and **amplification**:

| Retry Policy | Resilience | Amplification Risk |
|--------------|------------|---------------------|
| No retry | Low | None |
| Immediate retry | Medium | High |
| Linear backoff | High | Medium |
| Exponential backoff | High | Low |
| Exponential + jitter | Highest | Lowest |

### When NOT to Use Exponential Backoff

1. **Idempotent operations only**: Don't retry non-idempotent mutations
2. **User-facing requests**: Long backoff frustrates users
3. **Monitoring/debugging**: Retries can mask root cause

---

## Pre-warming Trade-offs

### When Pre-warming Makes Sense

| Scenario | Pre-warm? |
|----------|-----------|
| Known marketing event | ✅ Yes |
| Black Friday | ✅ Yes |
| Product launch | ✅ Yes |
| Regular traffic | ❌ No |

### The Cost Calculation

```
Pre-warming cost = extra_instances × hourly_rate × hours_prewarmed
Outage cost = revenue_per_minute × downtime_minutes

Prewarm when: prewarm_cost < outage_cost × probability_of_spike
```

---

## Summary: Decision Matrix

| Pattern | Use When | Avoid When |
|---------|----------|------------|
| Load shedding | Predictable peaks, clear priorities | Early product, all critical |
| Circuit breaker | Multiple deps, critical path | Single reliable service |
| Exponential backoff + jitter | Most cases | Non-idempotent ops |
| Pre-warming | Known events | Regular traffic |

---

## Staff Engineer Takeaway

> **Every resilience pattern has a cost.** The question is not "should I use this?" but "is the cost worth the protection for my specific situation?"

---

## Continue To

- **Section 10**: Summary → `summary.md`
