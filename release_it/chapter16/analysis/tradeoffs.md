# Analysis: Trade-offs & When NOT to Apply

Staff engineers know when **not** to apply a pattern. This section covers the nuances Chapter 16 doesn't explicitly call out.

---

## Use This When

### Systems Thinking
- **Complex distributed systems** with multiple services and teams
- **Post-incident analysis** where root cause isn't immediately obvious
- **Architectural reviews** for new features or services
- **Capacity planning** that involves multiple dependencies

### Feedback Loop Design
- **Auto-scaling** configurations
- **Circuit breaker** tuning
- **Alert threshold** setting
- **Deployment strategies** (canary, blue-green)

### Organizational Patterns
- **Team restructuring** discussions
- **Process changes** (on-call, incident response)
- **Hiring strategy** (generalists vs. specialists)
- **Technical debt prioritization**

---

## Avoid This When

### Systems Thinking
- **Early-stage startups** (1-3 engineers) — component reasoning is fine
- **Simple monoliths** — over-engineering for systems that don't need it
- **Prototypes/MVPs** — speed matters more than sustainability initially
- **When you need to move fast** — systems thinking takes time upfront

**Why**: The cost of systemic thinking is analysis paralysis. Not every system needs the same rigor.

### Feedback Loop Design
- **When you lack observability** — you can't tune what you can't measure
- **For one-off operations** — manual intervention is fine
- **When latency is critical** — feedback loops add overhead
- **With insufficient data** — thresholds should be data-driven, not guessed

**Why**: Poorly designed feedback loops cause more harm than good (oscillation, flapping).

### Organizational Patterns
- **When team is already functional** — don't fix what isn't broken
- **During major product launches** — stability > improvement
- **Without leadership buy-in** — changes will be reverted
- **When the cost > benefit** — sometimes silos are fine

**Why**: Organizational change is expensive. Don't refactor org structure just for ideological reasons.

---

## Hidden Costs

### Systems Thinking
| Cost | Description |
|------|-------------|
| **Analysis paralysis** | Over-thinking interactions slows decisions |
| **Communication overhead** | More stakeholders, more meetings |
| **Complexity tax** | Documenting relationships adds work |
| **Inflexibility** | Too much coupling to current structure |

### Feedback Loops
| Cost | Description |
|------|-------------|
| **Tuning effort** | Finding the right thresholds takes iteration |
| **Monitoring burden** | Feedback loops need monitoring too |
| **Latency** | Every feedback loop adds response time |
| **Oscillation risk** | Badly tuned loops amplify problems |

### Organizational Patterns
| Cost | Description |
|------|-------------|
| **Transition friction** | Changing how people work is hard |
| **Political capital** | Organizational change requires sponsorship |
| **Temporary inefficiency** | New patterns take time to gel |
| **Resistance** | Not everyone wants to change |

---

## Real-World Trade-off Examples

### Example 1: To Adopt Chaos Engineering or Not?

**Context**: Mid-size company (50 engineers), 15 microservices

| Factor | Go Chaos Engineering | Don't |
|--------|---------------------|-------|
| **Observability maturity** | ✅ Metrics, logging, tracing in place | ❌ Basic logging only |
| **On-call load** | High — want to find issues proactively | Low — infrequent incidents |
| **Leadership support** | ✅ CTO enthusiastic | ❌ Wants feature velocity |
| **Team readiness** | ✅ SRE team advocates | ❌ Dev team resistant |

**Decision**: Adopt gradually — start with game days, not full chaos platform.

### Example 2: Breaking Down Silos

**Context**: Large enterprise (500 engineers), 3 main departments

| Factor | Break Silos | Keep Silos |
|--------|-------------|------------|
| **Current velocity** | Low (handoffs slow) | High (specialization) |
| **Incident frequency** | High (unclear ownership) | Low (clear ownership) |
| **Innovation** | Stifled (no cross-team) | Thriving (deep expertise) |
| **Engineering culture** | Open to change | Risk-averse |

**Decision**: Partial break — create cross-functional "tiger teams" for key initiatives while maintaining some specialization.

### Example 3: Auto-scaling Threshold Tuning

**Context**: E-commerce platform, AWS, variable traffic

| Threshold | Pro | Con |
|-----------|-----|-----|
| **Aggressive (0.5)** | Never over-provisioned | Risk of under-provisioning during traffic spikes |
| **Conservative (0.9)** | Always enough capacity | Wasted money during low traffic |
| **Balanced (0.7)** | Reasonable trade-off | Still needs tuning during special events |

**Decision**: Start conservative (0.7), tune based on 3 months of data.

---

## Key Takeaway

> **The right answer depends on context.** Chapter 16 gives you the mental model, but the specific decisions require:
> - Data (metrics, incident history)
> - Stakeholder input (business priorities)
> - Experiment (try, measure, iterate)

Systems thinking is not about having all the answers — it's about asking the right questions.
