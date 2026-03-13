# Lab 1: Mapping Feedback Loops in a Microservice Architecture

## 🎯 Goal

Map out all feedback loops (positive and negative) in a hypothetical microservice architecture. Identify which loops are working correctly and which could cause problems.

## ⏱ Time
~20-25 minutes

## 🛠 Requirements

- Pen and paper (or a diagramming tool like draw.io, Lucidchart)
- Understanding of basic microservice patterns

---

## Scenario: E-Commerce Platform Architecture

You're architecting an e-commerce platform with the following services:

```
                    ┌──────────────┐
                    │   Gateway    │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │ Catalog  │ │   Cart   │ │   User   │
        │ Service  │ │ Service  │ │ Service  │
        └────┬─────┘ └────┬─────┘ └────┬─────┘
             │            │            │
             └────────────┼────────────┘
                          │
                          ▼
                   ┌──────────────┐
                   │   Order     │
                   │   Service   │
                   └──────┬───────┘
                          │
              ┌───────────┼───────────┐
              ▼           ▼           ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │  Payment │ │  Stock   │ │   Ship   │
        │ Service  │ │ Service  │ │ Service  │
        └──────────┘ └──────────┘ └──────────┘
```

---

## Step 1: Identify Feedback Loops

For each service pair, identify if there's a feedback relationship:

### Example:
| From | To | Type | Feedback Loop |
|------|-----|------|---------------|
| Payment | Order | Negative | If payment fails, order is cancelled → reduces load on payment |

### Your Turn:

Complete the table for all service interactions:

| From | To | Type | Feedback Loop |
|------|-----|------|---------------|
| Catalog | Gateway | ? | ? |
| Cart | Gateway | ? | ? |
| Order | Cart | ? | ? |
| Order | Catalog | ? | ? |
| Payment | Order | ? | ? |
| Stock | Order | ? | ? |
| Ship | Order | ? | ? |

---

## Step 2: Classify as Positive or Negative

For each feedback loop you identified, classify as:

- **Positive (Reinforcing)**: Amplifies a trend (good or bad)
- **Negative (Balancing)**: Counteracts change, maintains stability

---

## Step 3: Identify Potential Problems

Answer these questions:

1. **Which positive feedback loops could cause cascading failures?**
   - Hint: Look for "success breeds success" or "failure breeds failure" patterns

2. **Which negative feedback loops might oscillate due to delays?**
   - Hint: Look for places where there's latency between action and effect

3. **Where are the "invisible" feedback loops (humans in the loop)?**
   - Example: On-call engineer gets paged → manually restarts service → could cause more alerts

---

## Step 4: Design Improvements

For each problem identified, propose a design change:

| Problem | Current Behavior | Proposed Fix | Why It Works |
|---------|-----------------|--------------|--------------|
| Example: Payment retries amplify failures | Failed payment → immediate retry → more load → more failures | Add circuit breaker + exponential backoff | Breaks the positive feedback loop |
| ? | ? | ? | ? |

---

## Expected Output

Your deliverable should include:

1. **A diagram** showing all services and their feedback connections
2. **Classification table** with + (positive) or - (negative) for each loop
3. **Risk analysis** identifying 3 most dangerous feedback loops
4. **Mitigation plan** for each risk

---

## Staff-Level Extension

If you're done early, consider:

1. **Model it**: Write a simple simulation (Python) of one feedback loop to see how it behaves under load

2. **Real-world comparison**: Research a real incident (e.g., the Knight Capital flash crash) and identify which feedback loops failed

3. **Organizational feedback loops**: What happens when:
   - On-call engineer is woken up repeatedly?
   - Developer gets bug bounty reports?
   - Ops team keeps firefighting?

---

## Solution Hints (Don't peek until you've tried!)

### Step 1 hints:
- Catalog → Gateway: Negative (too many requests → rate limit)
- Cart → Gateway: Positive (more items → more requests)
- Order → Cart: Negative (order completes → cart clears)
- Payment → Order: Negative (payment fails → order cancels)

### Step 2 hints:
- Positive: Cart → Gateway (more items = more requests = more load)
- Negative: Most service-to-service interactions (prevent overload)

### Step 3 hints:
- Positive feedback danger: Retries without backoff!
- Oscillation danger: Auto-scaling with delay
- Human feedback: Alert fatigue → burnout → more mistakes
