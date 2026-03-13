# Chapter 15 Quick Reference: Architecture Adaptation

## Release It! by Michael Nygard

---

## The Core Insight

> **"Make incremental changes. Avoid big bangs."**

Architecture must evolve as your business, scale, technology, and team change. The key is knowing **when** and **how** to evolve.

---

## Evolution Strategies

| Strategy | When to Use | Key Benefit |
|----------|-------------|-------------|
| **Modular Monolith** | Team < 15, starting point | Simple deployment, clear boundaries |
| **Service Extraction** | Team > 15, independent modules | Team autonomy, independent scaling |
| **Strangler Pattern** | Rewrite needed, risk mitigation | Zero-downtime migration |
| **Branch by Abstraction** | Technology change | No branch needed, feature flag control |

---

## Signs You Need to Adapt

### Technical Signs
- Deployment pain (takes hours, fails often)
- Performance issues (slow responses, DB bottleneck)
- Development slowdown (conflicts, long builds)
- Reliability issues (frequent outages)

### Business Signs
- Feature velocity declining
- Customer complaints increasing
- Hitting scalability ceilings

---

## Scaling Patterns

### Horizontal Scaling
- Add more instances
- Stateless services
- Load balancer + auto-scaling

### Vertical Scaling
- Bigger machines
- More resources
- Hardware limits eventually

### Database Scaling
- **Read**: Replicas, caching, CQRS
- **Write**: Sharding, partitioning, distributed DBs

---

## Conway's Law

> "Organizations which design systems are constrained to produce designs which are copies of the communication structures of these organizations."

**Implication:** Your architecture will reflect your team structure. Don't fight it.

| Team Size | Recommended Approach |
|-----------|---------------------|
| < 10 | Monolith |
| 10-25 | Consider extraction |
| > 25 | Services likely help |

---

## Common Pitfalls

### 1. Premature Optimization
- **Problem**: Scaling before needed
- **Solution**: YAGNI, evolve as needed

### 2. Never Evolving
- **Problem**: Technical debt accumulation
- **Solution**: Regular refactoring, planned evolution

### 3. Big Bang Rewrite
- **Problem**: High risk, feature freeze
- **Solution**: Incremental changes, strangler pattern

### 4. Ignoring Team
- **Problem**: Architecture doesn't fit team
- **Solution**: Align team and architecture

---

## Investment Balance

- **70%** maintenance
- **20%** evolution
- **10%** innovation

Adjust for context (startup vs enterprise, new vs legacy)

---

## Key Takeaways

1. **Start simple** — modular monolith before microservices
2. **Extract when needed** — driven by concrete pain, not theory
3. **Team structure matters** — Conway's Law
4. **Incremental beats big bang** — always
5. **Technology evolves** — plan for it

---

## Bookmark

> **"Make incremental changes. Avoid big bangs."**

---

*Quick reference generated for Release It! Chapter 15: Adaptation (Architecture Evolution)*
