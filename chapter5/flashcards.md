# Chapter 5 Flashcards: The Un-virtualized Ground

## Card Set 1: Core Concepts

---

### Card 1.1
**Q: What is the "virtualized ground" problem in software systems?**

**A:**
The problem that the abstraction layers between your code and physical hardware introduce subtle but significant stability issues. Applications are often designed assuming "abstract resources" — infinite CPU, perfect network, reliable storage — but reality is different.

---

### Card 1.2
**Q: What does "CPU steal time" indicate?**

**A:**
CPU steal time measures how much time your virtual CPU spent waiting for the physical CPU while the hypervisor was servicing other VMs. High steal time = your VM is being starved by noisy neighbors or host overload.

---

### Card 1.3
**Q: Why does VM live migration cause latency spikes?**

**A:**
During live migration, the hypervisor must transfer memory state from one physical host to another. This causes:
- Increased I/O (memory pages being transferred)
- CPU overhead (hypervisor managing migration)
- Network overhead (migration traffic on virtual network)
Result: 50-200ms latency spikes visible to users.

---

### Card 1.4
**Q: What is memory overcommitment in virtualization?**

**A:**
The hypervisor allocates more virtual memory than physical memory exists. When VMs actually use this memory, the host must swap to disk, causing dramatic performance degradation (disk I/O is 100-1000x slower than RAM).

---

## Card Set 2: Failure Modes

---

### Card 2.1
**Q: How do hardware memory errors manifest as software bugs?**

**A:**
Single-bit memory errors (cosmic rays, aging hardware) can cause:
- Random crashes in application code
- Corrupted data in variables
- "Impossible" test failures that don't reproduce
- Intermittent, unexplainable behavior

---

### Card 2.2
**Q: What is the "Nine Nines" myth?**

**A:**
The misconception that 99.9999999% reliability (essentially perfect) is achievable with standard infrastructure. In reality:
- Consumer hardware fails regularly
- Even enterprise hardware has defined MTBF (Mean Time Between Failures)
- At scale, failures are statistical certainties

---

### Card 2.3
**Q: What are "noisy neighbors" in cloud computing?**

**A:**
Other tenants (VMs/containers) on the same physical hardware consuming disproportionate resources (CPU, I/O, network), causing performance degradation for your workloads without any change to your code.

---

### Card 2.4
**Q: Why is I/O wait time important to monitor?**

**A:**
High I/O wait indicates the CPU is waiting for disk operations. In virtualized environments, this can be caused by:
- Storage contention from other VMs
- Virtual disk I/O scheduling overhead
- Storage area network (SAN) congestion

---

## Card Set 3: Solutions & Patterns

---

### Card 3.1
**Q: What is a circuit breaker pattern and why is it relevant here?**

**A:**
A pattern that prevents cascading failures by "tripping" when a downstream service is failing. When infrastructure is overwhelmed (high latency, errors), the circuit opens and fast-fails rather than queuing more requests. This protects both your service and the struggling infrastructure.

---

### Card 3.2
**Q: Why should you use exponential backoff for retries?**

**A:**
Exponential backoff (100ms → 200ms → 400ms) gives infrastructure time to recover without overwhelming it. Immediate retries often fail for the same reason and can amplify the problem (thundering herd).

---

### Card 3.3
**Q: What infrastructure metrics should you always monitor?**

**A:**
- **CPU steal time** (hypervisor contention)
- **I/O wait** (disk performance)
- **Memory usage and pressure**
- **Network throughput and errors**
- **Disk latency**

---

### Card 3.4
**Q: How does graceful degradation help with infrastructure issues?**

**A:**
When infrastructure is struggling, reduce functionality rather than failing completely:
- Return cached data instead of fresh data
- Disable non-essential features
- Show degraded but functional UI
This keeps the system available during infrastructure stress.

---

## Card Set 4: Staff-Level Insights

---

### Card 4.1
**Q: How does understanding infrastructure variability affect cost modeling?**

**A:**
You must budget 20-30% "infrastructure tax" for virtualization overhead. Otherwise:
- Capacity planning will be undersized
- Cost projections will be wrong
- You'll be surprised by scaling limits

---

### Card 4.2
**Q: Why is "application portability" a myth across cloud providers?**

**A:**
Different clouds have different:
- Network latency profiles
- VM performance characteristics
- Storage performance
- Hypervisor behaviors

An app tuned for AWS may have 2x latency on GCP due to infrastructure differences.

---

### Card 4.3
**Q: What is the relationship between infrastructure visibility and MTTR?**

**A:**
If you don't monitor infrastructure metrics (steal, I/O wait), you can't identify the root cause of incidents. This increases Mean Time To Recovery because you're debugging blind. Infrastructure visibility directly impacts incident response speed.

---

### Card 4.4
**Q: How should you design staging environments to catch infrastructure issues?**

**A:**
Staging should mirror production infrastructure, not just application code:
- Same VM types/sizes
- Same network configuration
- Same load patterns
- Same monitoring
Otherwise, infrastructure issues only appear in production.

---

*Flashcards generated by Book Deep Learner - Staff/Senior Engineer Edition*
