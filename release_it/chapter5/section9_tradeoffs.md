# Section 9: Analysis — Trade-offs & When NOT to Use This

## When to Apply These Patterns (And When Not To)

Staff engineers know when **not** to apply a pattern. This section covers the nuanced decisions around infrastructure resilience.

---

## Pattern: Timeout with Retry

### ✅ Use This When

- **Operations are idempotent**: GET requests, read operations
- **Infrastructure is known to be variable**: Cloud environments, shared infrastructure
- **Latency is acceptable**: User can wait for retries
- **Failure is recoverable**: Downstream can handle duplicate requests

### ❌ Avoid This When

- **Operations are non-idempotent**: POST, DELETE, writes that can't be deduplicated
- **Strict latency requirements**: Financial trading, real-time gaming
- **Resource is already exhausted**: Retries will make it worse
- **Failure is certain**: Don't retry permanent failures (404, auth errors)

### Hidden Costs

| Cost | Impact |
|------|--------|
| **Increased latency** | Users wait for retries |
| **Resource consumption** | More CPU, memory, network |
| **Complexity** | Harder to debug, trace |
| **Cascading risk** | Retries during outage can worsen it |

---

## Pattern: Circuit Breaker

### ✅ Use This When

- **Single service dependency**: Clear failure domain
- **Failure is common**: Infrastructure is unreliable
- **Fallback exists**: Something useful to return
- **You need fast failure**: Waiting wastes resources

### ❌ Avoid This When

- **No clear failure domain**: Who does the circuit protect?
- **Failure is rare**: Overhead not worth it
- **No fallback available**: Users get nothing anyway
- **Distributed transactions**: Hard to know when to reset

### Hidden Costs

| Cost | Impact |
|------|--------|
| **False positives** | Circuit opens when it shouldn't |
| **State management** | Where does state live? |
| **Debugging difficulty** | "Why is circuit open?" |
| **Partial failures** | Harder to diagnose what's broken |

---

## Pattern: Graceful Degradation

### ✅ Use This When

- **Core vs. non-core services**: Some features are optional
- **Cached data available**: Fallback to stale data
- **Multiple redundancy**: You have alternatives
- **User tolerance**: Users accept reduced functionality

### ❌ Avoid This When

- **Everything is core**: No degradable features
- **Stale data is dangerous**: Financial, medical, safety-critical
- **Single point of failure**: Degradation reveals the problem
- **No monitoring**: You don't know degradation is happening

### Hidden Costs

| Cost | Impact |
|------|--------|
| **User confusion** | "Why does X work but Y doesn't?" |
| **Testing complexity** | Must test all degradation paths |
| **Operational burden** | More states to monitor |
| **Technical debt** | "Temporary" degradation becomes permanent |

---

## Pattern: Infrastructure Monitoring (CPU Steal, I/O Wait)

### ✅ Use This When

- **Running on shared infrastructure**: VMs, containers, cloud
- **Performance is critical**: Latency-sensitive workloads
- **You have actionability**: You can do something about it
- **SLA requirements**: P99 latency matters

### ❌ Avoid This When

- **Dedicated hardware**: No noisy neighbors possible
- **Batch workloads**: Who cares if it's slow?
- **No authority to change**: Infrastructure team owns VMs
- **Alert fatigue risk**: You'll ignore the alerts anyway

### Hidden Costs

| Cost | Impact |
|------|--------|
| **Metric explosion** | What to alert on? |
| **Alert fatigue** | Too many false positives |
| **Cost** | Monitoring infrastructure costs money |
| **Expertise** | Need people who understand these metrics |

---

## The Decision Framework

Use this flowchart to decide which pattern to apply:

```
                    ┌─────────────────────────┐
                    │ Is operation idempotent? │
                    └───────────┬─────────────┘
                                │
                    ┌───────────┴───────────┐
                    ▼                       ▼
                   YES                      NO
                    │                       │
                    ▼                       ▼
         ┌─────────────────┐    ┌──────────────────────┐
         │ Is latency      │    │ Can you deduplicate?  │
         │ acceptable?     │    └──────────┬───────────┘
         └───────┬─────────┘               │
                 │               ┌────────┴────────┐
          ┌──────┴──────┐       ▼                 ▼
          ▼             ▼       YES                NO
         YES           NO
          │             │
          ▼             ▼    ┌─────────────────────────┐
    ┌─────────────┐   ┌─────┴─────┐   DO NOT RETRY
    │ Add timeout │   │ Find      │
    │ + retry     │   │ alternative│
    │ + backoff   │   │ design    │
    └─────────────┘   └───────────┘
```

---

## Common Mistakes

### Mistake 1: Retrying Non-Idempotent Operations

```go
// ❌ BAD: Retry a DELETE request
func DeleteUser(id string) error {
    resp, err := http.Delete("/users/" + id)
    // If first request times out but DELETE succeeds,
    // retry will DELETE the user again!
    return err
}

// ✅ GOOD: Use idempotency keys
func DeleteUser(id string, idempotencyKey string) error {
    req, _ := http.NewRequest("DELETE", "/users/"+id, nil)
    req.Header.Set("Idempotency-Key", idempotencyKey)
    resp, err := http.DefaultClient.Do(req)
    return err
}
```

### Mistake 2: No Timeout on Retry Loop

```go
// ❌ BAD: Infinite retry loop
func naiveRetry() {
    for {
        err := doSomething()
        if err == nil {
            return
        }
        time.Sleep(time.Second)
    }
}

// ✅ GOOD: Respect context/cancellation
func retryWithLimit(ctx context.Context) error {
    for attempt := 0; attempt < maxRetries; attempt++ {
        err := doSomething()
        if err == nil {
            return nil
        }
        select {
        case <-ctx.Done():
            return ctx.Err()
        case <-time.After(backoff(attempt)):
        }
    }
    return ErrMaxRetriesExceeded
}
```

### Mistake 3: Circuit Breaker Without Fallback

```go
// ❌ BAD: Circuit opens, users get error
func GetData() (Data, error) {
    cb := NewCircuitBreaker()
    data, err := cb.Execute(fetchFromDB)
    if err != nil {
        return nil, err  // User gets nothing!
    }
    return data, nil
}

// ✅ GOOD: Circuit opens, users get fallback
func GetData() (Data, error) {
    cb := NewCircuitBreaker()
    data, err := cb.Execute(fetchFromDB)
    if err != nil {
        // Return stale cache instead of error
        return fetchFromCache()
    }
    return data, nil
}
```

### Mistake 4: Monitoring Without Actionability

```bash
# ❌ BAD: Alert on everything
ALERT cpu_steal > 0

# ✅ GOOD: Alert with actionability
ALERT cpu_steal > 10 AND duration > 5m
  THEN: Consider migrating to dedicated host
```

---

## The "Senior" Judgment

When reviewing infrastructure resilience designs, ask:

| Question | Why It Matters |
|----------|----------------|
| What's the finite resource? | That's what will fail first |
| What's the blast radius? | How much breaks when it fails? |
| What's the recovery path? | How do we fix it? |
| What's the alert? | Do we know it's happening? |
| Is there a fallback? | What do users see? |
| Is it testable? | How do we verify it works? |

---

## Summary

| Pattern | Use When | Avoid When |
|---------|----------|------------|
| Timeout + Retry | Idempotent ops, variable infra | Non-idempotent, latency-critical |
| Circuit Breaker | Clear failure domain, fallback exists | No clear domain, no fallback |
| Graceful Degradation | Core + non-core features, cache exists | All core, stale is dangerous |
| Infra Monitoring | Shared infra, performance critical | Dedicated hardware, batch workloads |

---

## Final Thought

> "The best code is the code you don't write. The second best is code that fails fast. The worst is code that fails slowly." — *Staff Engineer Proverb*

The patterns in this chapter help you fail fast when infrastructure fails. But always weigh the complexity cost against the failure risk.

---

*Next: [Section 10 - Chapter Summary](section10_summary.md)*
