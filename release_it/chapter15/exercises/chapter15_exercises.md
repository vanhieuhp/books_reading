# Chapter 15 Exercises: Architecture Adaptation

## Release It! by Michael Nygard

---

## Exercise Set Overview

These exercises are designed for senior/staff engineers to apply the concepts from Chapter 15. They test understanding of evolution strategies, trade-offs, and real-world application.

---

## Exercise 1: Evolution Strategy Selection

**Difficulty:** ⭐⭐ (Medium)

### Scenario

You're a staff engineer at a mid-sized startup. Your system is a monolith with these characteristics:

- **Team**: 12 developers
- **Deployment**: Weekly, takes 45 minutes, 15% failure rate
- **Performance**: p99 latency 800ms at 50K DAU
- **Database**: PostgreSQL, CPU at 65%
- **Incidents**: 3-4 per month

### Tasks

1. **Calculate trouble score** using the metrics from the course
2. **Recommend an evolution strategy** with reasoning
3. **List the specific steps** you would take
4. **Identify what metrics** you'd track to know when to evolve further

### Deliverable

```markdown
## My Recommendation

### Trouble Score: __/100

### Recommended Strategy: __

### Reasoning:
1. ...
2. ...

### Action Steps:
1. ...
2. ...

### Metrics to Track:
- ...
```

---

## Exercise 2: Service Extraction Planning

**Difficulty:** ⭐⭐⭐ (Hard)

### Scenario

Your team has decided to extract the "billing" module from your monolith. The module currently:

- Shares the same PostgreSQL database as other modules
- Has direct database calls from multiple other modules
- Is called 10,000 times per hour during peak
- Has its own data that other modules need read access to

### Tasks

1. **Design the contract** between billing service and consumers
2. **Plan the data migration** - how do you handle the shared database?
3. **Plan the traffic migration** - how do you route from monolith to service?
4. **Identify failure modes** - what could go wrong and how do you handle it?
5. **Estimate timeline** - how long would this take?

### Deliverable

```markdown
## Service Extraction Plan: Billing Module

### 1. Contract Design
- API endpoints: ...
- Data model: ...
- Authentication: ...

### 2. Data Migration Strategy
- Phase 1: ...
- Phase 2: ...
- Phase 3: ...

### 3. Traffic Migration
- % to new service: ...

### 4. Failure Modes
| Failure | Detection | Mitigation |
|---------|-----------|------------|
| ... | ... | ... |

### 5. Timeline Estimate
- Weeks: ...
```

---

## Exercise 3: Conway's Law Application

**Difficulty:** ⭐⭐⭐⭐ (Very Hard)

### Scenario

You're advising a 200-person engineering organization. They've been trying to adopt microservices for 2 years but are struggling:

- 150 microservices but 40% of deploys cause incidents
- Teams blame each other for integration issues
- Average time from code to production: 3 weeks
- Developer satisfaction: 2.5/5

### Tasks

1. **Diagnose** what's wrong from a Conway's Law perspective
2. **Recommend** team structure changes (if any)
3. **Design** an evolution path to fix the issues
4. **Identify** metrics to track improvement

### Deliverable

```markdown
## Conway's Law Analysis

### Current Problem Diagnosis:
- Team structure: ...
- Architecture: ...
- The mismatch: ...

### Recommended Team Structure:
```
[Org chart or description]
```

### Evolution Path:
1. Phase 1 (0-3 months): ...
2. Phase 2 (3-6 months): ...
3. Phase 3 (6-12 months): ...

### Success Metrics:
- Deploy success rate: ...
- Time to production: ...
- Developer satisfaction: ...
```

---

## Exercise 4: Strangler Pattern Design

**Difficulty:** ⭐⭐⭐ (Hard)

### Scenario

You need to migrate from an on-prem MySQL database to DynamoDB. The constraints are:

- Zero downtime required
- 1 million requests per day
- Some queries are complex joins that don't map well to DynamoDB
- You need to maintain data consistency

### Tasks

1. **Design a strangler pattern** for this migration
2. **Handle the data synchronization** between MySQL and DynamoDB
3. **Plan the traffic migration** strategy
4. **Handle queries that don't map** to DynamoDB

### Deliverable

```markdown
## Strangler Pattern Design: MySQL → DynamoDB

### Architecture:
[Diagram or description]

### Data Synchronization Strategy:
- Approach: ...
- Tooling: ...
- Consistency: ...

### Traffic Migration:
- Initial: ...
- Growth: ...
- Final: ...

### Complex Query Handling:
- Option A: ...
- Option B: ...

### Rollback Plan:
- Trigger: ...
- Process: ...
```

---

## Exercise 5: Decision Framework

**Difficulty:** ⭐⭐⭐⭐⭐ (Expert)

### Scenario

Create a decision framework (like the one in the course) that can be used to recommend evolution strategies. Your framework should:

1. Accept system metrics as input
2. Return a recommended strategy with confidence
3. Include at least 5 different scenarios
4. Be implementable in code

### Tasks

1. **Define the metrics** your framework considers
2. **Create decision rules** for each strategy
3. **Implement the framework** in Python or Go
4. **Test with at least 5 scenarios**

### Deliverable

```python
# evolution_decision_framework.py
# (Your implementation)

# Test scenarios with expected outputs
def test_framework():
    scenarios = [
        # (name, metrics, expected_strategy)
        ("Small team, healthy", ..., ...),
        ...
    ]

    for name, metrics, expected in scenarios:
        result = recommend_strategy(metrics)
        assert result == expected, f"Failed: {name}"
```

---

## Exercise 6: Real-World Analysis

**Difficulty:** ⭐⭐⭐⭐ (Very Hard)

### Task

Research a real company's architecture evolution (not Netflix or Amazon). Examples:

- Uber
- Spotify
- Airbnb
- Stripe
- Shopify

For your chosen company:

1. **Identify** the evolution stages they went through
2. **Analyze** what triggered each evolution
3. **Evaluate** if their decisions aligned with Chapter 15 principles
4. **Extract** lessons applicable to your own organization

### Deliverable

```markdown
## Company: [Name]

### Evolution Stages:
| Stage | Years | Architecture | Trigger |
|-------|-------|--------------|---------|
| 1 | ... | ... | ... |
| 2 | ... | ... | ... |

### Analysis:
- Aligned with Chapter 15: ...
- Deviations from principles: ...

### Lessons Learned:
1. ...
2. ...
```

---

## Answers & Discussion

> Note: These exercises don't have single "correct" answers. The goal is to apply the frameworks and reasoning from the chapter. Discuss with peers to compare approaches.

### Quick Reference: Decision Framework

| Team Size | Trouble Score | Recommended Strategy |
|-----------|---------------|---------------------|
| < 10 | < 30 | Stay modular monolith |
| < 10 | > 30 | Add modular boundaries |
| 10-25 | < 40 | Modularize first |
| 10-25 | > 40 | Service extraction |
| > 25 | Any | Service extraction (consider strangler if DB bottleneck) |

---

*Exercises generated for Release It! Chapter 15: Adaptation (Architecture Evolution)*
