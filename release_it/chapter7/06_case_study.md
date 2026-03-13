# Case Study: The "Friendly" Incident - How a Simple Deployment Crashed a Major Platform

---

## Organization
**Company**: A major SaaS platform (anonymized due to NDA)
**Year**: 2019
**Context**: E-commerce platform processing $50M+ in monthly GMV

---

## Problem: The Friendly Deployment That Went Wrong

On a Tuesday afternoon, the engineering team deployed a "routine" update to their order processing service. The deployment was marked "low risk" - it only changed a few lines of logging code. What followed was a 45-minute outage that affected 200,000+ customers.

### Timeline

| Time | Event |
|------|-------|
| 2:00 PM | Deployment begins (rolling update) |
| 2:03 PM | First instances start restarting |
| 2:05 PM | Database connection pool exhausted |
| 2:07 PM | Orders fail - customers see 500 errors |
| 2:12 PM | Engineers roll back to previous version |
| 2:35 PM | Service recovers |
| 2:45 PM | Post-incident analysis begins |

### Root Cause Analysis

The investigation revealed the deployment triggered **three compounding failures**:

1. **Connection Storm**: All 50 instances restarted simultaneously. Each instance tried to create 20 database connections = 1,000 connection requests in 3 seconds.

2. **Missing Graceful Shutdown**: The service didn't properly handle SIGTERM. Instead of draining in-flight requests, it was killed abruptly (by Kubernetes liveness probe failure, which we'll explain).

3. **Aggressive Liveness Probe**: The Kubernetes liveness probe was set to check every 1 second, with a failure threshold of 3. During a brief GC pause (normal in Go), the probe failed 3 times = instance killed and restarted = more connection attempts = more load = more GC pauses = cascade.

---

## Chapter Concepts Applied

### 1. Instance Lifecycle - The Four Phases

The incident touched all four phases:

- **Startup**: Connection storm during instance initialization
- **Serving**: Abrupt termination before completing requests
- **Shutdown**: No graceful shutdown = in-flight orders failed
- **Failure**: Liveness probe failure caused restart loops

### 2. Connection Storms

```
Root cause: All 50 instances started at once
  ↓
Database received 1000 connection requests (50 × 20)
  ↓
Pool exhausted, new requests rejected
  ↓
Failed orders, cascade begins
```

### 3. Graceful Shutdown

The service had NO graceful shutdown implementation:
- No SIGTERM handler
- No in-flight request tracking
- No drain timeout
- Kubernetes liveness probe killed the process mid-request

### 4. Health Checks

The liveness probe was **too aggressive**:
- Checked every 1 second (should be 10+ seconds)
- Threshold of 3 failures (should be 3+ seconds of failures)
- No initial delay (should wait for startup to complete)

---

## Solution: What They Fixed

### Fix 1: Graceful Shutdown Implementation

```go
// Added SIGTERM handler
func (s *Server) SetupGracefulShutdown() {
    sigChan := make(chan os.Signal, 1)
    signal.Notify(sigChan, syscall.SIGTERM, syscall.SIGINT)

    go func() {
        <-sigChan
        log.Println("Received shutdown signal")
        s.GracefulShutdown()
    }()
}

func (s *Server) GracefulShutdown() {
    // Stop accepting new requests
    s.mu.Lock()
    s.shuttingDown = true
    s.mu.Unlock()

    // Wait for in-flight with timeout
    ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
    defer cancel()

    s.WaitForDrain(ctx)

    // Close connections
    s.db.Close()
    s.redis.Close()

    // Exit cleanly
    os.Exit(0)
}
```

### Fix 2: Tuned Kubernetes Health Checks

```yaml
# Before (wrong)
livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 0
  periodSeconds: 1
  failureThreshold: 3

# After (correct)
livenessProbe:
  httpGet:
    path: /health/liveness
    port: 8080
  initialDelaySeconds: 60  # Wait for startup
  periodSeconds: 10       # Check every 10s, not every 1s
  failureThreshold: 3      # 3 failures × 10s = 30s before restart

readinessProbe:
  httpGet:
    path: /health/readiness
    port: 8080
  initialDelaySeconds: 10  # Quick readiness after init
  periodSeconds: 5         # Check more frequently for routing
  failureThreshold: 2      # 2 failures = 10s to mark unhealthy
```

### Fix 3: Staggered Deployment

```yaml
# Added rolling update strategy with maxSurge
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 1        # Add 1 extra instance during update
    maxUnavailable: 0  # Never have fewer than desired
```

This ensures:
- Only 1 instance restarts at a time
- Total capacity stays at 100% during deployment
- Database sees at most 20 new connections (1 instance × 20)

---

## Outcome

| Metric | Before | After |
|--------|--------|-------|
| Deployment incidents/month | 2-3 | 0 |
| Average outage duration | 45 min | 0 |
| Orders affected per deployment | ~200K | 0 |
| MTTR | 45 min | N/A |

---

## Staff Insight: What a Staff Engineer Would Take From This

### The "Small Change" Fallacy

This incident started with a "trivial" logging change. The lesson: **any deployment can cause outages**. The risk isn't in the code change - it's in the system's ability to handle change. Staff engineers focus on system resilience, not code safety.

### Defense in Depth

Multiple failures compounded:
1. Simultaneous restarts (deployment config)
2. No graceful shutdown (application code)
3. Aggressive health checks (orchestration config)

Any ONE of these being correct would have prevented the outage. Defense in depth means assuming each layer will fail.

### The Cost of Speed

The team wanted "fast deployments" (all at once = 3 minutes vs. staggered = 15 minutes). But the "fast" deployment cost 45 minutes of outage + customer trust + engineering time investigating. Fast != good.

### Health Checks Are Critical

Most teams spend zero time tuning health checks. But liveness probes can CAUSE outages if misconfigured. The Go GC pause that triggered this incident was normal - 50ms. The probe was too sensitive to handle normal behavior.

---

## Reusability: How to Apply This Pattern Elsewhere

### For Your Own Services

1. **Always implement graceful shutdown**: It's not optional, even for "simple" services
2. **Test health checks in staging**: Set up chaos to verify probe behavior
3. **Stagger deployments**: Use maxSurge: 1, maxUnavailable: 0 in Kubernetes
4. **Monitor connection pools**: Alert when approaching limits
5. **Document startup time**: Track and alert on regression

### For Platform Teams

1. **Provide templates**: Give teams working graceful shutdown implementations
2. **Set sensible defaults**: Kubernetes defaults are too aggressive
3. **Build deployment tooling**: That enforces staggered rollout
4. **Create observability**: Dashboards for deployment health

### For Incident Review

Ask these questions:
1. Did graceful shutdown work correctly?
2. Were health checks too aggressive?
3. Was the deployment too fast (simultaneous restarts)?
4. Did connection pools get exhausted?
5. Was there a circuit breaker that should have fired?

---

## Conclusion

This incident is a textbook example of why Chapter 7 matters. The "simple" deployment failed because the team had ignored instance lifecycle fundamentals:

- No graceful shutdown
- No staggered startup
- No proper health checks
- No connection pool protection

After implementing these patterns, the team went 18 months without a single deployment-related incident. The 12 minutes of "extra" deployment time paid for itself many times over.
