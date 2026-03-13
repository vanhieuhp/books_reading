# Real-World Use Cases

## Use Case 1: Netflix's Instance Lifecycle Management at Scale

### Problem
Netflix operates thousands of microservice instances across multiple AWS regions. During a typical deployment, hundreds of instances are restarted simultaneously, causing connection storms that overwhelmed their Cassandra clusters and caused region-wide outages.

### Solution
Netflix implemented a sophisticated instance lifecycle management system:

1. **Staggered Rolling Updates**: Instead of restarting all instances at once, they implemented a "wave" deployment system where only 1-5% of instances in a region restart at a time.

2. **Asgard**: Their deployment system built on AWS Auto Scaling Groups with custom logic to:
   - Track instance health before proceeding to next wave
   - Implement exponential backoff between waves (5s, 10s, 20s, 40s...)
   - Add jitter to prevent synchronized retries
   - Automatic rollback if error rate exceeds threshold

3. **Zuul**: Their edge gateway implements gradual traffic shifting:
   - New instances start with 0% weight
   - Weight increases by 10% every 30 seconds
   - If error rate spikes, weight immediately drops to 0%

### Outcome
- Deployment time increased from 3 minutes to 15 minutes
- But: Zero production incidents caused by deployments in 3+ years
- Rollback time reduced from 30 minutes to 90 seconds
- Database connection pool exhaustion reduced by 99%

### Lesson
**Fast deployment velocity is meaningless if it causes outages.** The additional deployment time is paid back 100x in reduced incident frequency and severity.

---

## Use Case 2: Google's Container Instance Management with Borg

### Problem
Google runs billions of containers across their fleet. Early versions of Borg (their container orchestrator) had aggressive liveness checks that caused restart loops during brief GC pauses, making it impossible to run stable workloads.

### Solution
Google implemented a sophisticated health check system:

1. **Two-Probe System**:
   - **Readiness probe**: Checks if container should receive traffic (dependency availability)
   - **Liveness probe**: Checks if container should be restarted (process health)

2. **Configurable Thresholds**:
   - Initial delay: Wait 60 seconds before first check (allow startup)
   - Period: Check every 10 seconds (not every second)
   - Timeout: 5 second timeout for check to respond
   - Failure threshold: 3 consecutive failures before restart
   - Success threshold: 1 success to mark healthy

3. **The "Don't Restart" Rule**:
   - Liveness failures never immediately restart
   - Instead, they trigger investigation and logging
   - Actual restart only after repeated failures with human review

### Outcome
- GC pause-induced restarts reduced from 100s/day to near zero
- "Unhealthy" instances no longer cause cascade failures
- Staff can confidently run jobs with "restartable" flag disabled

### Lesson
**The default Kubernetes health check settings are designed for generic workloads.** Production systems need tuned values that account for startup time, expected GC behavior, and business requirements.

---

## Use Case 3: Shopify's Graceful Shutdown for E-Commerce

### Problem
Shopify handles millions of dollars in transactions per hour. During deployments or scale-down events, their Ruby on Rails instances were killed abruptly, causing:
- Shopping cart data loss
- Payment processing failures
- Customer-visible 500 errors

### Solution
Shopify implemented a comprehensive graceful shutdown system:

1. **SIGTERM Handling**:
   - All Rails processes intercept SIGTERM
   - Immediately stop accepting new connections
   - Wait up to 30 seconds for in-flight requests

2. **Request Draining**:
   - Track in-flight requests with Redis
   - If request count > 0 after 25 seconds, extend to 35 seconds
   - After 30 seconds, force kill (with logging)

3. **Connection Management**:
   - Database connections returned to pool before exit
   - Redis connections closed gracefully
   - Sidekiq workers finish current job (or acknowledge)

4. **Load Balancer Integration**:
   - Nginx configured with `proxy_connect_timeout` equal to drain timeout
   - AWS ALB deregistration delay = drain timeout + buffer

5. **Service Discovery**:
   - Deregister from etcd/consul before shutdown
   - 10-second delay between deregistration and process exit

### Outcome
- Customer-facing errors during deployments reduced by 99%
- Shopping cart abandonment during deploys: 0.001% → 0%
- Zero lost transactions due to abrupt termination in 4+ years
- Deployment frequency increased (engineers no longer fear deploys)

### Lesson
**Graceful shutdown isn't just technical hygiene—it's customer trust.** Every 500 error during a deployment is a customer who might never come back.

---

## Summary Table

| Company | Challenge | Solution | Impact |
|---------|-----------|----------|--------|
| Netflix | Connection storms during deployment | Wave-based deployment + gradual traffic shifting | Zero deployment incidents |
| Google | Liveness probe restart loops | Two-probe system with tuned thresholds | 99% reduction in restart loops |
| Shopify | Transaction loss during shutdown | Comprehensive drain + load balancer integration | Zero lost transactions |
