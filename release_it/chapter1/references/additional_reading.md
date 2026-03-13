# Chapter 1: Living in Production - Additional Reading

## Books

### 1. Antifragile: Things That Gain from Disorder
**Author**: Nassim Nicholas Taleb
**Why**: The conceptual foundation for antifragility that Nygard references
**Key Concepts**: Antifragility, via negativa, barbell strategy

### 2. Site Reliability Engineering
**Author**: Google
**URL**: https://sre.google/sre-book/table-of-contents/
**Why**: Google's approach to production operations
**Key Concepts**: Error budgets, SLOs, SLAs, toil reduction

### 3. The Site Reliability Workbook
**Author**: Google
**URL**: https://sre.google/workbook/table-of-contents/
**Why**: Practical SRE implementation
**Key Concepts**: Incident management, post-mortems, chaos engineering

### 4. Chaos Engineering
**Author**: Casey Rosenthal, Lorin Hochstein
**Why**: Netflix's approach to finding production gaps
**Key Concepts**: Chaos experiments, steady state, blast radius

### 5. Designing Data-Intensive Applications
**Author**: Martin Kleppmann
**Why**: Deep dive into distributed systems challenges
**Key Concepts**: Reliability, scalability, maintainability

---

## Articles & Papers

### Production Readiness

1. **"The AWS outage: what we learned"**
   - Summary of major cloud outages and lessons

2. **"Google's Site Reliability Engineering"**
   - Original SRE paper/approach

3. **"The Evolution of Site Reliability Engineering at Google"**
   - How SRE evolved over time

### Chaos Engineering

1. **"Chaos Engineering" (Netflix Tech Blog)**
   - https://netflix.github.io/chaosmonkey/
   - How Netflix builds confidence in systems

2. **"Principles of Chaos Engineering"**
   - https://principlesofchaos.org/
   - Formal definition and principles

3. **"Chaos Engineering - Gremlin Blog"**
   - Practical chaos engineering guide

### Production Operations

1. **"The Three Ways" - The Phoenix Project**
   - DevOps principles for production systems

2. **"Observability at Google"**
   - How Google does logging, metrics, tracing

3. **"Incident Management at Google"**
   - Handling production incidents

---

## Videos & Talks

### Must-Watch

1. **"Production-Oriented Development"**
   - Talks on building for production from day one

2. **"Chaos Engineering: The History of Netflix's Simian Army"**
   - How chaos engineering evolved at Netflix

3. **"Site Reliability Engineering: Google's Experience"**
   - Google SRE team sharing experience

---

## Tools Mentioned in Chapter

### Observability

- **OpenTelemetry**: Open standard for observability
- **Prometheus**: Metrics collection
- **Jaeger**: Distributed tracing
- **ELK Stack**: Logging

### Chaos Engineering

- **Chaos Monkey**: Netflix's original chaos tool
- **Gremlin**: Commercial chaos engineering platform
- **Litmus**: Kubernetes chaos engineering
- **Pumba**: Docker chaos engineering

### Infrastructure

- **Docker**: Environment parity
- **Terraform**: Infrastructure as Code
- **Kubernetes**: Container orchestration

---

## Related Public Incidents

### Famous Production Failures

1. **Knight Capital (2012)**: $440M loss from deployment error
2. **AWS us-east-1 (2011)**: Multiple days outage
3. **GitHub (2012)**: Service degradation
4. **Target (2013)**: Data breach via HVAC vendor
5. **Facebook (2019)**: Multi-hour outage
6. **Fastly (2021)**: CDN outage affecting major sites

---

## Next Steps

After mastering Chapter 1 concepts:

1. Read Chapter 2: Case Study - The Exception That Chain-Reacted
2. Implement one chaos engineering experiment
3. Audit your systems for production gaps
4. Create a production readiness checklist for your team

---

*Additional reading list for Release It! Chapter 1*
