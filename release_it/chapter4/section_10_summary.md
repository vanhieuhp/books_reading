# Chapter 4: Stability Patterns — Summary & Review

---

## ✅ Key Takeaways (5 bullets, Staff Framing)

1. **Timeouts are non-negotiable foundation** — Every I/O operation must have a timeout. No timeouts = resource accumulation = cascading failure. At scale, even 0.1% of requests hanging can exhaust your entire connection pool.

2. **Circuit breaker is stateful protection** — Not a try-catch wrapper. It remembers history and transitions through Closed → Open → Half-Open states. The "half-open" testing phase is critical—it prevents premature recovery or premature re-opening.

3. **Bulkheads isolate blast radius** — Divide resources by criticality. Authentication gets its own pool; analytics gets a smaller one. A slow analytics query shouldn't block users from logging in.

4. **Patterns compose together** — Timeout + Circuit Breaker + Bulkhead = defense in depth. Each pattern catches what the others miss. Alone, each has gaps; together, they're comprehensive.

5. **Design for failure, not success** — Production is a failure path with occasional success. Assume components will fail. Plan for it. Test it.

---

## 🔁 Review Questions

### Question 1: State Machine Logic
**If a circuit breaker has a failure threshold of 5 and receives 7 consecutive failures, how many state transitions occur? What states does it go through?**

<details>
<summary>Answer</summary>

1. **5th failure**: Transitions from CLOSED → OPEN
2. No more transitions until timeout
3. After timeout: OPEN → HALF-OPEN (automatic on timeout check)
4. If test request fails in half-open: HALF-OPEN → OPEN
5. If test request succeeds: HALF-OPEN → CLOSED

So: Up to 3 transitions (CLOSED→OPEN, OPEN→HALF-OPEN, then either HALF-OPEN→CLOSED or HALF-OPEN→OPEN)
</details>

---

### Question 2: Timeout Selection
**You have an external payment API with p50 latency of 200ms and p99 of 2 seconds. What timeout would you set, and why?**

<details>
<summary>Answer</summary>

**Suggested timeout: 3-5 seconds**

Rationale:
- p99 = 2s means 1% of requests take longer than 2s
- Setting timeout at p99 would cause 1% false failures
- Setting at 5x p99 (10s) would be too slow to detect real issues
- 3-5 seconds catches genuine failures while allowing for natural variance
- Also consider: if payment service is that slow, user experience is degraded anyway
</details>

---

### Question 3: Bulkhead Design
**Design the bulkhead strategy for an e-commerce checkout flow that includes: inventory check, payment processing, and order confirmation. How would you size the pools?**

<details>
<summary>Answer</summary>

**Suggested approach:**

| Operation | Pool Size | Queue | Timeout | Rationale |
|-----------|-----------|-------|---------|-----------|
| Inventory | 20 | 50 | 2s | High volume, can queue briefly |
| Payment | 10 | 0 | 10s | Critical, small pool, fail fast if overwhelmed |
| Order Confirmation | 5 | 100 | 30s | Low priority, can queue longer |

**Key insight**: Payment is most critical—smallest pool, shortest timeout. Inventory can handle more load. Order confirmation can queue extensively.
</details>

---

### Question 4: Anti-Pattern Detection
**Your service's p50 latency is 50ms but p99 is 30 seconds. What stability pattern is likely missing, and how would you diagnose?**

<details>
<summary>Answer</summary>

**Likely missing: Timeouts or circuit breakers**

Diagnosis steps:
1. Check if all external calls have timeouts
2. Look for long-running database queries
3. Check connection pool utilization
4. Look for any service with high error rates
5. Check if circuit breakers are configured

**The 30-second p99 suggests some requests are blocking for a very long time**—classic sign of no timeout or timeout set to infinity.
</details>

---

### Question 5: Design Question
**How would you design a system that calls three external APIs in parallel, where each API has different reliability characteristics (99.9%, 99%, 95% availability)?**

<details>
<summary>Answer</summary>

**Design approach:**

1. **Separate circuit breakers** for each API:
   - High-reliability API (99.9%): Higher threshold (10 failures), longer timeout
   - Medium (99%): Medium threshold (5 failures), standard timeout
   - Low (95%): Lower threshold (3 failures), aggressive circuit breaking

2. **Separate bulkheads** by reliability:
   - Don't let the unreliable API exhaust resources for reliable ones

3. **Timeout proportional to reliability**:
   - More reliable = can wait longer
   - Less reliable = fail faster

4. **Fallback strategy**:
   - For critical operations: require all APIs
   - For non-critical: use "best effort" with fallbacks

5. **Aggregated response**:
   - Use timeout.Timeout() to wait for fastest N of M responses
</details>

---

## 🔗 Connect Forward: What's Next?

Chapter 4's stability patterns unlock the next chapter:

> **Next: Part II - Design for Production**

The stability patterns you learned here become the foundation for:
- **Capacity Planning** (Chapter 6) — Timeouts and bulkheads determine resource needs
- **Security** (Chapter 8) — Circuit breakers prevent credential brute-forcing
- **Scaling** (Chapter 12) — Bulkheads enable independent scaling of components

---

## 📌 Bookmark: The ONE Sentence Worth Memorizing

> **"Defend your system against failures it will inevitably encounter. Build for the crash, not for the happy path."**
>
> — Michael Nygard, *Release It!* (paraphrased from core philosophy)

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────┐
│ STABILITY PATTERNS QUICK REFERENCE                       │
├─────────────────────────────────────────────────────────┤
│ Pattern      │ Purpose              │ When to Use       │
├─────────────────────────────────────────────────────────┤
│ Timeout     │ Prevent hanging      │ EVERY external    │
│             │ requests             │ call              │
├─────────────────────────────────────────────────────────┤
│ Circuit     │ Stop calling         │ External APIs,    │
│ Breaker     │ failing services     │ databases         │
├─────────────────────────────────────────────────────────┤
│ Bulkhead    │ Limit blast         │ Critical          │
│             │ radius              │ resources         │
├─────────────────────────────────────────────────────────┤
│ Handshake   │ Backpressure        │ High-volume       │
│             │ negotiation         │ systems           │
├─────────────────────────────────────────────────────────┤
│ Let It      │ Clean recovery      │ Stateless         │
│ Crash       │ via restart         │ services          │
├─────────────────────────────────────────────────────────┤
│ Stable      │ Minimize failure    │ Architecture      │
│ Topology    │ impact              │ design            │
└─────────────────────────────────────────────────────────┘

IMPLEMENTATION ORDER (priority):
1. Timeouts (easiest, highest impact)
2. Circuit breakers (essential for external calls)
3. Bulkheads (critical resources)
4. Handshake (high-volume systems)
5. Stable topology (architectural decision)
```

---

## Files in This Chapter

| File | Description |
|------|-------------|
| `section_00_session_overview.md` | Session card and core concepts |
| `section_03_code_examples.md` | Production-grade Go implementations |
| `section_05_real_world_cases.md` | Netflix, Amazon, Stripe, Google, LinkedIn |
| `section_07_code_lab.md` | Build a circuit breaker step-by-step |
| `section_08_case_study.md` | GitHub 2012 outage deep dive |
| `visualizations.py` | Generate architecture diagrams |
| `README.md` | Quick reference and navigation |
