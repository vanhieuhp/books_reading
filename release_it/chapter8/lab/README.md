# Chapter 8 Lab: Resilient HTTP Client

## Overview

This lab demonstrates the difference between **naive** and **resilient** HTTP clients, illustrating the key patterns from Chapter 8: Interconnect.

## Learning Objectives

By the end of this lab, you will:
1. Understand why naive HTTP clients can cause production incidents
2. Implement a circuit breaker pattern with state machine
3. Configure timeouts at multiple levels (connection, read, total)
4. Implement retry with exponential backoff
5. Observe circuit breaker behavior in action

---

## Prerequisites

- Go 1.18 or later
- Basic understanding of HTTP and networking

---

## Files

| File | Description |
|------|-------------|
| `naive_client.go` | HTTP client with NO resilience features |
| `resilient_client.go` | Production-grade client with all patterns |

---

## Lab Steps

### Step 1: Run the Naive Client

The naive client demonstrates what happens when you don't have resilience features:

```bash
go run naive_client.go
```

**What you'll see:**
- Test 1: Connecting to non-existent service → hangs for 2+ minutes
- Test 2: Connecting to slow service → waits 10 seconds

**The problems:**
1. ❌ No timeout → indefinite hang
2. ❌ No retry → single point of failure
3. ❌ No circuit breaker → resource exhaustion

---

### Step 2: Run the Resilient Client

The resilient client implements all Chapter 8 patterns:

```bash
go run resilient_client.go
```

**What you'll see:**
- First 5 requests fail → circuit opens
- Requests 6-10: "circuit breaker open" → fail fast (no waiting!)
- After timeout → half-open → tests recovery
- Successful tests → circuit closes

**The features:**
1. ✅ Explicit timeouts at multiple levels
2. ✅ Retry with exponential backoff
3. ✅ Circuit breaker to prevent cascade
4. ✅ Connection pooling

---

### Step 3: Compare Behavior

| Metric | Naive Client | Resilient Client |
|--------|-------------|------------------|
| Time to detect failure | 2+ minutes | < 1 second |
| Requests during outage | Continuously hammering | Stopped immediately |
| Recovery detection | Manual | Automatic |

---

## Key Code Patterns

### Circuit Breaker State Machine

```go
// Three states:
// CLOSED: Normal operation
// OPEN: Failing fast
// HALF-OPEN: Testing recovery
```

### Timeout Configuration

```go
config := ResilientClientConfig{
    ConnectTimeout:  5 * time.Second,
    ReadTimeout:    10 * time.Second,
    TotalTimeout:   30 * time.Second,
}
```

### Retry with Backoff

```go
// Exponential backoff: 500ms, 1s, 2s
delay := baseDelay * time.Duration(1<<attempt)
```

---

## Challenge Exercises

### Exercise 1: Add Metrics Export
Add Prometheus metrics for:
- Circuit state changes
- Retry count per request
- Request latency histogram

### Exercise 2: Bulkhead Pattern
Create separate connection pools per service to isolate failures:
- Service A pool: 10 connections
- Service B pool: 5 connections
- Failure in A doesn't affect B

### Exercise 3: Rate Limiting
Add a token bucket rate limiter:
- Max 100 requests/second
- Burst up to 50 requests
- Prevents overwhelming downstream

### Exercise 4: Deadline Propagation
Ensure deadlines propagate correctly:
- Client sets 30s timeout
- Request takes 10s so far
- Downstream gets 20s remaining

---

## Expected Output

### Naive Client
```
========================================
  NAIVE HTTP CLIENT DEMONSTRATION
========================================

--- Test 1: Connecting to non-existent service ---
Expected: Will hang for 2+ minutes (OS TCP timeout)

Result: Failed after 2m15.432s
Error: request failed: dial tcp [::1]:9999: connect: connection refused
```

### Resilient Client
```
========================================
  RESILIENT HTTP CLIENT DEMONSTRATION
========================================

--- Making 10 requests (first 5 will fail) ---

Request 1:
[CIRCUIT] State change: CLOSED -> OPEN
[CLIENT] Attempt 1 failed: server error: 500 (status: 500)
  Failed after 50.123ms

Request 2:
[CIRCUIT] OPEN - failing fast
[CLIENT] Circuit OPEN - failing fast, not attempting request
  Failed after 1.234ms
  Circuit state: OPEN
```

---

## Key Takeaways

> **Circuit breakers prevent cascade failures** by failing fast when downstream is unhealthy.

> **Timeouts are non-negotiable** — every network call needs explicit timeout.

> **Retry with backoff** helps recover from transient failures, but must be limited to avoid amplifying problems.

---

## Cleanup

```bash
# Kill any running servers
pkill -f "go run"
# Or on Windows
taskkill /F /IM go.exe
```

---

## Next Steps

1. Review the code in detail
2. Try the challenge exercises
3. Apply these patterns to your own services
4. Read Chapter 9 (Control Plane) to learn about service discovery
