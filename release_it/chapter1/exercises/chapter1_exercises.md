# Chapter 1: Living in Production - Exercises

## Exercise Set 1: Production Gap Analysis

### Exercise 1.1: Identify Production Gaps in Your Code

**Task**: Review one of your recent projects and identify at least 3 potential production gaps.

**Format**:

| Component | Production Gap | Axis (Time/Scale/Diversity) | Risk Level |
|-----------|---------------|---------------------------|------------|
|           |               |                           |            |

**Sample Answer**:
| Component | Production Gap | Axis | Risk Level |
|-----------|---------------|------|------------|
| User cache | Unbounded growth | Time | High |
| API client | No timeout | Scale | Critical |
| User input | No validation | Diversity | High |

---

### Exercise 1.2: Map Your Staging Environment

**Task**: Document how your staging environment differs from production.

Create a comparison table:

| Aspect | Staging | Production | Gap Risk |
|--------|---------|------------|----------|
| Data volume | | | |
| Load profile | | | |
| Dependencies | | | |
| Monitoring | | | |
| Infrastructure | | | |

---

## Exercise Set 2: Design for Production

### Exercise 2.1: Production Readiness Checklist

**Task**: Create a production readiness checklist for a new service.

Include items for:
- [ ] Observability (logging, metrics, tracing)
- [ ] Error handling
- [ ] Timeouts and retries
- [ ] Graceful shutdown
- [ ] Resource limits
- [ ] Configuration management
- [ ] Security considerations
- [ ] Backup and recovery
- [ ] Capacity planning
- [ ] Incident response plan

---

### Exercise 2.2: Antifragility Design

**Task**: For each failure scenario, design how your system should respond:

| Failure Scenario | Detection | Containment | Recovery | Learning |
|-----------------|-----------|-------------|----------|----------|
| Database connection pool exhausted | | | | |
| Third-party API timeout | | | | |
| Memory leak detected | | | | |
| Cache invalidation failure | | | | |

---

## Exercise Set 3: Scale Thinking

### Exercise 3.1: 10x Scale Analysis

**Task**: Take a current feature and analyze what breaks at 10x scale.

**Feature**: _______________

| Resource | Current | 10x Scale | Failure Mode | Mitigation |
|----------|---------|-----------|--------------|------------|
| Database connections | | | | |
| Memory usage | | | | |
| API latency | | | | |
| Storage | | | | |

---

### Exercise 3.2: Unknown Unknowns Brainstorming

**Task**: For your system, list 5 "impossible" scenarios that could still happen:

1. _______________
2. _______________
3. _______________
4. _______________
5. _______________

For each, consider:
- How would you detect it?
- How would you contain it?
- How would you recover?

---

## Exercise Set 4: Real-World Application

### Exercise 4.1: Incident Post-Mortem Analysis

**Task**: Think of a production incident you've experienced (or research a famous one).

Apply the chapter concepts:

| Concept | How It Applies |
|---------|----------------|
| Production Gap | |
| Axis 1 (Time) | |
| Axis 2 (Scale) | |
| Axis 3 (Diversity) | |
| QA Fallacy | |
| Antifragility | |

---

### Exercise 4.2: Design Review Framework

**Task**: Create a 5-question "production readiness" design review template.

Questions to include:
1. How does this fail in production?
2. What are the unknown unknowns?
3. How do we observe this in production?
4. What's the blast radius if this fails?
5. How do we recover automatically?

---

## Exercise Answers (Self-Assessment)

### Exercise 1.1: Sample Answers

Potential production gaps to look for:
- Unbounded caches (Time)
- No timeouts on external calls (Scale)
- Missing input validation (Diversity)
- Unbounded queues (Scale)
- No circuit breakers (Scale)
- Missing graceful shutdown (Time)
- Hardcoded configurations (Diversity)
- No correlation IDs in logs (Observability)

### Exercise 2.1: Production Readiness Checklist

**Minimum Viable**:
- Structured logging
- Basic metrics (CPU, memory, request rate)
- Health check endpoint
- Graceful shutdown
- Timeouts on external calls

**Production Ready**:
- Distributed tracing
- Detailed metrics per endpoint
- Alerting thresholds
- Circuit breakers
- Feature flags
- Chaos engineering tested
- Runbook documented

---

## Additional Challenges

### Challenge 1: Chaos Engineering Lite

Implement one chaos engineering experiment in your staging environment:
- Terminate a random instance
- Introduce latency between services
- Simulate database failure
- Trigger cache invalidation

Document what you learn.

### Challenge 2: Observability Audit

Can you find all logs related to a single user request in less than 5 minutes?

If not, what's missing?

### Challenge 3: Failure Injection

Add deliberate failure injection to your codebase:
- Random timeouts
- Random errors
- Latency injection

Test that your error handling works correctly.

---

*Exercises designed for staff/senior engineers to apply Chapter 1 concepts*
