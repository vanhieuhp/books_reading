# Chapter 13: Chaos Engineering - Learning Resources

A curated collection of tools, articles, videos, and further reading to master chaos engineering.

---

## 🛠️ Chaos Engineering Tools

### Open Source

| Tool | Description | Best For |
|------|-------------|----------|
| [Chaos Mesh](https://chaos-mesh.org/) | Kubernetes-native chaos engineering platform | Containerized workloads |
| [Litmus](https://litmuschaos.io/) | Cloud-native chaos engineering | Kubernetes, Cloud platforms |
| [Chaos Monkey](https://github.com/Netflix/chaosmonkey) | Original Netflix tool - kills random instances | AWS/EC2 workloads |
| [Chaos Gorilla](https://github.com/Netflix/chaosgorilla) | Netflix's network partition simulator | AWS availability zones |
| [Pumba](https://github.com/alexei-led/pumba) | Docker/Kubernetes chaos testing | Container-level chaos |
| [Kube-monkey](https://github.com/asobti/kube-monkey) | Kubernetes pod terminator | K8s random pod kills |
| [PowerfulSeal](https://github.com/bloomberg/powerfulseal) | Kubernetes chaos engine | Policy-based chaos |
| [Sock Shop](https://github.com/microservices-demo/microservices-demo) | Demo app with chaos experiments | Learning/testing |

### Commercial

| Tool | Description | Pricing |
|------|-------------|---------|
| [Gremlin](https://www.gremlin.com/) | Enterprise chaos platform | Paid (free tier available) |
| [ChaosIQ](https://chaosiq.com/) | Enterprise chaos management | Paid |
| [Datadog Chaos Engineering](https://www.datadoghq.com/chaos/) | Integrated with Datadog | Paid (part of platform) |
| [AWS Fault Injection Simulator](https://aws.amazon.com/fis/) | AWS-native chaos | AWS users |
| [Azure Chaos Studio](https://azure.microsoft.com/services/chaos-studio/) | Azure-native chaos | Azure users |
| [GCP Chaos](https://github.com/GoogleCloudPlatform/chaos-eng-prod) | GCP chaos experiments | GCP users |

---

## 📚 Books

### Primary

- **"Release It!"** (Michael Nygard) — *Chapter 13: Chaos Engineering* ⭐ This chapter
- **"Site Reliability Engineering"** (Google) — Chapter 6: "Handling Overload", Chapter 22: "Chaos Engineering"
- **"The Site Reliability Workbook"** (Google) — Chapter 11: "Chaos Engineering"

### Further Reading

- **"Designing Data-Intensive Applications"** (Kleppmann) — Distributed systems failure modes
- **"Chaos Engineering"** (Krisk) — Comprehensive guide to chaos engineering principles
- **"Database Reliability Engineering"** (Campbell & Majumdar) — Chaos for data systems

---

## 🎬 Videos & Conferences

### Must-Watch

| Video | Speaker | Conference | Year |
|-------|---------|------------|------|
| [Principles of Chaos Engineering](https://www.youtube.com/watch?v=6iJ7tW-6IQQ) | Casey Rosenthal | QCon | 2018 |
| [Chaos Engineering at Netflix Scale](https://www.youtube.com/watch?v=6H_2pRBtajU) | Netflix Engineers | various | 2019 |
| [Building a Chaos Engineering Program](https://www.youtube.com/watch?v=3G8f7tDkcYQ) | Kolton Andrus | SREcon | 2019 |
| [Game Days: Learning from Failure](https://www.youtube.com/watch?v=wK8LOu7qC50) | Google SRE | SREcon | 2018 |
| [Running Game Days with Chaos Mesh](https://www.youtube.com/watch?v=4aZexMCL960) | Chaos Mesh Team | KubeCon | 2020 |

### Conference Talks

- **Chaos Conf** (by Gremlin) — Annual chaos engineering conference
- **SREcon** — Focus on reliability engineering
- **KubeCon/CloudNativeCon** — Kubernetes chaos tools

---

## 📰 Articles & Blog Posts

### Foundational

- [Principles of Chaos Engineering](https://principlesofchaos.org/) — Official formal definition
- [Chaos Engineering (Wikipedia)](https://en.wikipedia.org/wiki/Chaos_engineering) — Overview
- [Chaos Architecture (ThoughtWorks)](https://www.thoughtworks.com/insights/articles/chaos-architecture) — Design patterns

### Netflix

- [Chaos Engineering - A History](https://netflixtechblog.com/chaos-engineering-a-history-8f9c3838e0b7)
- [Chaos Monkey: The Randomness in Your Pocket](https://netflixtechblog.com/chaos-monkey-the-randomness-in-your-pocket-b5e2c9084c63)
- [Chaos Engineering: Breaking Things on Purpose](https://netflixtechblog.com/chaos-engineering-break-things-on-purpose-5b989b9c0d0d)

### Google

- [SRE Book: Handling Overload](https://sre.google/sre-book/handling-overload/)
- [Running Game Days](https://sre.google/workbook/game-days/)

### Others

- [Introduction to Chaos Engineering](https://www.gremlin.com/community/tutorials/introduction-to-chaos-engineering/)
- [How to Run a Game Day](https://www.gremlin.com/community/tutorials/how-to-run-a-game-day/)
- [Getting Started with Chaos Mesh](https://chaos-mesh.org/docs/basic-features/)

---

## 🧪 Practice Environments

### For Learning

1. **Sock Shop** (Weaveworks)
   - Docker/Kubernetes demo app
   - Pre-built chaos experiments
   - https://github.com/microservices-demo/microservices-demo

2. **Docker Lab** (This course)
   - Docker-compose based
   - Simple chaos injection
   - See `lab/` folder

3. **Katacoda**
   - Free interactive labs
   - Kubernetes chaos
   - https://www.katacoda.com/

### For Certification

- [Gremlin Certified Chaos Engineer](https://www.gremlin.com/certifications/chaos-engineer/)
- Free training + exam

---

## 📊 Metrics & Key Metrics

### Chaos-Specific Metrics

| Metric | Definition | Target |
|--------|------------|--------|
| **MTTR** | Mean Time To Recovery | < 5 minutes |
| **MTTD** | Mean Time To Detection | < 1 minute |
| **Blast Radius** | Scope of impact | Minimize |
| **Experiment Success Rate** | % passing | > 80% |
| **Detection Rate** | Time to detect failure | < 30 seconds |

### Availability Targets

| Availability | Downtime/Year | Downtime/Month |
|--------------|---------------|----------------|
| 99% | 3.65 days | 7.3 hours |
| 99.9% | 8.76 hours | 43.8 minutes |
| 99.99% | 52.6 minutes | 4.38 minutes |
| 99.999% | 5.26 minutes | 26.3 seconds |

---

## 🔄 Experiment Templates

### Basic Experiments

```
1. Pod Kill
   - Target: Non-critical deployment
   - Hypothesis: System will failover within 60s
   - Metrics: Error rate, recovery time

2. Network Latency
   - Target: Database connection
   - Hypothesis: p99 latency < 2s
   - Metrics: Latency percentiles, error rate

3. Resource Exhaustion
   - Target: Memory/CPU
   - Hypothesis: System degrades gracefully
   - Metrics: Error rate, latency

4. Dependency Failure
   - Target: External API
   - Hypothesis: Circuit breaker triggers
   - Metrics: Error rate, fallback usage
```

### Advanced Experiments

```
1. Multi-Region Failover
   - Hypothesis: Traffic fails over automatically
   - RTO: < 5 minutes
   - RPO: < 1 minute

2. Data Center Loss
   - Hypothesis: No data loss, automatic failover
   - RTO: < 10 minutes
   - RPO: 0

3. Cascading Failure
   - Hypothesis: Failure containment prevents cascade
   - Blast radius: < 1 service
   - Recovery: < 5 minutes
```

---

## 📋 Quick Reference

### The Chaos Engineering Loop

```
┌─────────────────┐
│ Define Steady   │  What does "normal" look like?
│     State       │  (Metrics, thresholds)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Hypothesize   │  What will happen when X fails?
│                 │  (Testable prediction)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Design Exp.   │  What to break? How to measure?
│                 │  (Safety, abort conditions)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Run Experiment│  Inject failure, observe behavior
│                 │  (Monitor, collect data)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Analyze Results │  Did system behave as expected?
│                 │  (Compare to hypothesis)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Improve System │  Fix weaknesses, iterate
│                 │  (Automation, coverage)
└────────┬────────┘
         │
         ▼
      (Repeat)
```

### Safety Checklist

- [ ] Define steady state
- [ ] Write hypothesis
- [ ] Set abort conditions
- [ ] Plan rollback
- [ ] Notify stakeholders
- [ ] Verify monitoring
- [ ] Have stop button
- [ ] Document findings

---

*Generated for Release It! Chapter 13*
*Last Updated: 2026-03-13*
