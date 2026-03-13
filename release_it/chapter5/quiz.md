# Chapter 5 Quiz: The Un-virtualized Ground

## Quiz: Testing Your Infrastructure Knowledge

---

## Section A: Core Concepts (Multiple Choice)

### Question A1
**What does "CPU steal time" measure in a virtualized environment?**

A) The time your application spends in user mode
B) The time your vCPU waits for physical CPU while hypervisor services other VMs
C) The time spent in system calls
D) The time waiting for garbage collection

**Answer: B** — CPU steal time measures how much your virtual CPU waited for the physical CPU. High steal time means your VM is being starved by other VMs.

---

### Question A2
**Which of these is NOT a virtualization overhead?**

A) Virtual CPU scheduling overhead
B) Virtual network latency
C) Direct hardware access (passthrough)
D) Memory overcommitment causing swapping

**Answer: C** — Direct hardware access (passthrough) bypasses virtualization overhead. The others all add latency and variability.

---

### Question A3
**What is the "Nine Nines" myth?**

A) That you can achieve 99.9999999% reliability with consumer hardware
B) That nine developers can maintain a system
C) That you need nine redundant servers
D) That VMs have nine layers of abstraction

**Answer: A** — The myth is that 99.9999999% reliability is achievable with standard infrastructure. In reality, hardware fails regularly at scale.

---

## Section B: Failure Modes (True/False)

### Question B1
**True or False: Hardware memory errors always crash the system immediately.**

**Answer: False** — Memory errors can cause subtle corruption, random crashes, or "impossible" bugs without immediately crashing the system.

---

### Question B2
**True or False: VM live migration is instantaneous and transparent to applications.**

**Answer: False** — Live migration causes latency spikes (50-200ms) as memory is transferred between hosts.

---

### Question B3
**True or False: If your application has no errors, infrastructure is not the problem.**

**Answer: False** — Infrastructure issues often manifest as latency, not errors. Timeouts, slow responses, and p99 tail issues are often infrastructure-driven.

---

### Question B4
**True or False: "Noisy neighbors" only affect CPU, not storage or network.**

**Answer: False** — Noisy neighbors can affect CPU, memory, storage I/O, and network bandwidth. Any shared resource can be contested.

---

## Section C: Solutions (Multiple Choice)

### Question C1
**Which pattern prevents cascading failures when infrastructure is overwhelmed?**

A) Retry with backoff
B) Circuit breaker
C) Caching
D) Load balancing

**Answer: B** — Circuit breakers trip when a service is failing, preventing more requests from overwhelming it (cascading failure).

---

### Question C2
**Why is exponential backoff preferred over immediate retries?**

A) It's easier to implement
B) It gives infrastructure time to recover and prevents thundering herd
C) It uses less memory
D) It always succeeds on the first try

**Answer: B** — Exponential backoff prevents overwhelming struggling infrastructure with immediate retry storms.

---

### Question C3
**What should you monitor to detect infrastructure issues BEFORE they cause outages?**

A) Only application error rates
B) CPU steal time, I/O wait, memory pressure
C) Only network throughput
D) Developer productivity metrics

**Answer: B** — Infrastructure metrics (CPU steal, I/O wait, memory pressure) reveal problems before they impact users.

---

### Question C4
**What is "graceful degradation"?**

A) Turning off servers during low traffic
B) Reducing functionality to stay available when infrastructure is strained
C) Running the system at lower performance intentionally
D) Using cheaper infrastructure

**Answer: B** — Graceful degradation means reducing functionality (caching, disabling features) to keep the system available during infrastructure stress.

---

## Section D: Staff-Level Scenarios (Scenario-Based)

### Question D1
**Scenario: Your p99 latency spiked from 100ms to 500ms yesterday, but there were no code deployments. What might be the cause, and how would you investigate?**

**Answer:**
Possible causes:
- VM migration or host maintenance
- Noisy neighbor on shared infrastructure
- Hardware issues (memory errors, disk failures)
- Storage I/O contention

Investigation:
1. Check CPU steal time (was host overloaded?)
2. Check I/O wait (was storage contended?)
3. Check if any VM migrations occurred
4. Check hardware health metrics (SMART, memory errors)
5. Review cloud provider status/advisor alerts

---

### Question D2
**Scenario: You're designing a latency-sensitive service (<50ms p99) for AWS. What infrastructure considerations should you address?**

**Answer:**
- Use dedicated instances or dedicated hosts (reduce noisy neighbors)
- Pin to specific vCPU-to-physical CPU mappings
- Monitor CPU steal time and alert on anomalies
- Use provisioned IOPS for storage (predictable I/O)
- Design for variability: timeouts, retries, circuit breakers
- Run in multiple AZs for resilience
- Mirror production infrastructure in staging

---

### Question D3
**Scenario: Your team says "we don't need redundancy, our data center is reliable." How do you respond as a staff engineer?**

**Answer:**
- At scale, hardware failure is statistical certainty (not if, but when)
- "Reliable" data centers still have MTBF — Mean Time Between Failures
- Single points of failure (SPOF) cause outages when hardware fails
- Even enterprise hardware has failure rates; redundancy is about surviving failures, not preventing them
- Cost of downtime >> cost of redundancy
- Example: A single database failure took down an entire company for hours

---

### Question D4
**Scenario: You notice your staging performs great but production is slow. What infrastructure difference might explain this?**

**Answer:**
- Staging may have different VM types/sizes
- Staging may have dedicated resources vs. shared production
- Production may have more traffic/contention
- Network topology may differ (latency between services)
- Storage may be different (SSD vs. HDD, provisioned IOPS vs. standard)
- Monitoring may be different (production sees real workload)

---

## Section E: Fill in the Blank

### Question E1
**The practice of injecting failures into production to find hidden issues is called __________.**

**Answer:** Chaos Engineering (or Chaos Monkey at Netflix)

---

### Question E2
**When a hypervisor allocates more virtual memory than physical memory exists, this is called __________.**

**Answer:** Memory overcommitment

---

### Question E3
**The pattern that stops waiting after a fixed time and fails is called a __________.**

**Answer:** Timeout

---

### Question E4
**To handle infrastructure variability, you should budget an overhead of _________% for infrastructure "tax".**

**Answer:** 20-30%

---

## Scoring Guide

| Score | Level |
|-------|-------|
| 90-100% | Staff Engineer — You understand infrastructure deeply |
| 70-89% | Senior Engineer — Solid understanding, review weak areas |
| 50-69% | Mid-level — Review chapter, focus on staff-level insights |
| <50% | Review the chapter again, especially failure modes |

---

*Quiz generated by Book Deep Learner - Staff/Senior Engineer Edition*
