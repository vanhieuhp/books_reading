# Chapter 13: Chaos Engineering

## Chapter Overview

Chapter 13 introduces the practice of Chaos Engineering - proactively breaking your own system to find weaknesses before users do. Michael Nygard presents the philosophy and practical techniques for building confidence in your system's resilience by deliberately introducing failures and observing how the system responds.

## What is Chaos Engineering?

### The Philosophy

**Traditional Approach**
- Test for known failures
- Verify expected behavior
- Prevent known problems
- Reactive to incidents

**Chaos Engineering**
- Proactively find unknown failures
- Verify system resilience
- Discover weaknesses
- Build confidence

### Why Chaos Engineering?

**The Problem with Traditional Testing**
- Tests only what you expect
- Can't test for unknown unknowns
- Production is unpredictable
- Complex systems fail in complex ways

**The Solution**
- Experiment in production
- Embrace failure
- Learn from chaos
- Build resilience

## Principles of Chaos Engineering

### 1. Assume Failure Will Happen

- Plan for failure
- Design for failure
- Accept failure
- Recover from failure

### 2. Inject Realistic Failures

- Hardware failures
- Network issues
- Dependency failures
- Resource exhaustion

### 3. Learn from Experiments

- Measure the impact
- Observe behavior
- Document findings
- Improve systems

### 4. Automate Experiments

- Run continuously
- Reproducible
- Consistent
- Scalable

## Chaos Engineering Process

### Step 1: Define Steady State

**What is Steady State?**
- Normal behavior
- Baseline metrics
- Expected performance
- Key behaviors

**How to Define**
- What matters to users?
- What are key metrics?
- What's acceptable performance?

**Examples**
- Response time < 500ms
- Error rate < 1%
- 99% of requests succeed

### Step 2: Hypothesize

**What to Hypothesize**
- "If network fails, system will..."
- "If service goes down, system will..."
- "If load increases, system will..."

**Good Hypotheses**
- Specific
- Testable
- Measurable
- Clear outcome

### Step 3: Design Experiment

**Experiment Elements**
- What to inject?
- How much?
- For how long?
- What to measure?

**Safety**
- Stop conditions
- Rollback plan
- Monitoring
- Communication

### Step 4: Run Experiment

**Steps**
1. Start monitoring
2. Inject failure
3. Observe behavior
4. Collect data
5. Stop injection
6. Analyze results

### Step 5: Analyze Results

**Questions**
- Did system behave as expected?
- What was the impact?
- Were assumptions correct?
- What can be improved?

### Step 6: Improve System

**Based on Findings**
- Fix discovered weaknesses
- Add monitoring
- Improve recovery
- Update design

## Types of Chaos

### 1. Infrastructure Chaos

**Examples**
- Kill a server
- Restart a server
- Network partition
- DNS failure
- Disk full
- CPU at 100%

**What to Test**
- Auto-restart
- Failover
- Data durability
- Recovery time

### 2. Application Chaos

**Examples**
- Kill a process
- Throw exceptions
- Add latency
- Consume memory
- Thread exhaustion

**What to Test**
- Graceful degradation
- Circuit breaking
- Error handling
- Recovery

### 3. Dependency Chaos

**Examples**
- External API down
- Database slow
- Cache unavailable
- Message queue full

**What to Test**
- Circuit breakers
- Fallbacks
- Timeouts
- Caching

### 4. Load Chaos

**Examples**
- Traffic spike
- Slow trickle
- Request flood
- Connection exhaustion

**What to Test**
- Auto-scaling
- Load shedding
- Backpressure
- Circuit breaking

## Implementing Chaos Engineering

### Tools

**Chaos Monkey**
- Originally Netflix
- Kills random instances
- EC2 focused
- Simple concept

**Chaos Mesh**
- Kubernetes native
- Multiple failure types
- YAML-based
- Active community

**Gremlin**
- Commercial
- Multiple platforms
- Safe by design
- Managed service

**Litmus**
- Kubernetes
- Cloud-native
- Open source
- Extensive documentation

### Building Your Own

**Simple Experiments**
- Kill a process
- Stop a container
- Block a port
- Fill disk

**Advanced Experiments**
- Network delay
- Packet loss
- DNS failures
- CPU spike

### Experiment Design

**Start Small**
- Non-critical services
- Off-hours
- Staging first
- Low impact

**Scale Up**
- More services
- Production
- Business hours
- Full impact

**Safety First**
- Stop button
- Clear rollback
- Communication
- Monitoring

## Measuring Chaos

### Key Metrics

**1. MTTR (Mean Time To Recovery)**
- Time from failure to recovery
- Lower is better
- Target: < 5 minutes

**2. Availability**
- Percentage uptime
- Target: 99.9%+
- Measures impact

**3. Blast Radius**
- How far did failure spread?
- Smaller is better
- Isolation matters

**4. Detection Time**
- How long to detect failure?
- Lower is better
- Monitoring matters

### What to Measure

| Metric | Why | Target |
|--------|-----|--------|
| Recovery time | Speed | < 5 min |
| Error rate | Impact | < 1% |
| Data loss | Durability | 0 |
| Customer impact | Business | 0 |

## Common Experiments

### Experiment 1: Kill a Service

**Setup**
- Identify non-critical service
- Ensure monitoring
- Define success criteria

**Action**
- Kill service instance
- Observe failover
- Measure recovery

**Hypothesis**
- "Service will failover in < 1 minute"

### Experiment 2: Network Partition

**Setup**
- Identify services
- Define partition
- Set up monitoring

**Action**
- Block network between services
- Observe behavior
- Measure impact

**Hypothesis**
- "Services will fail gracefully with partial functionality"

### Experiment 3: Dependency Failure

**Setup**
- Identify external dependency
- Set up circuit breaker monitoring
- Define fallback behavior

**Action**
- Make dependency unavailable
- Observe system
- Measure degradation

**Hypothesis**
- "System will serve cached data with < 1% error rate"

### Experiment 4: Load Spike

**Setup**
- Define baseline load
- Set up auto-scaling monitoring
- Define success criteria

**Action**
- Spike traffic 10x
- Observe scaling
- Measure performance

**Hypothesis**
- "Auto-scaler will add capacity within 3 minutes"

## Challenges and Pitfalls

### Common Mistakes

1. **Too Aggressive**
   - Start small
   - Build confidence
   - Don't break everything

2. **No Monitoring**
   - Can't measure impact
   - Don't know outcome
   - No learning

3. **No Rollback**
   - Can't stop
   - Turned into real outage
   - Lost trust

4. **Blast Radius Too Big**
   - Broke production
   - Customer impact
   - No confidence building

### Avoiding Pitfalls

1. **Start in Staging**
   - Learn process
   - Safe environment
   - Build confidence

2. **Communicate**
   - Tell people
   - On-call aware
   - No surprises

3. **Have Stop Button**
   - Always can abort
   - Quick rollback
   - Safety first

4. **Measure Everything**
   - Before and after
   - Impact analysis
   - Learning

## Building a Chaos Program

### Getting Started

1. **Define Steady State**
   - What matters?
   - Key metrics?
   - Normal behavior?

2. **Identify First Experiment**
   - Simple
   - Low impact
   - Learn process

3. **Run in Staging**
   - Safe environment
   - No customer impact
   - Build confidence

4. **Document Results**
   - What happened?
   - What learned?
   - What fixed?

### Scaling Up

1. **Automate**
   - Run regularly
   - CI/CD integration
   - Continuous

2. **Production**
   - When ready
   - Small at first
   - Build trust

3. **Broader Scope**
   - More services
   - More failure types
   - More chaos

4. **Culture**
   - Normalize failure
   - Learn from it
   - Build resilience

## Actionable Takeaways

1. **Start Small** - One experiment, low impact
2. **Define Steady State** - Know what "normal" looks like
3. **Hypothesize** - What do you expect to happen?
4. **Measure Everything** - Before, during, after
5. **Have Stop Button** - Always can abort
6. **Communicate** - Tell people what you're doing
7. **Learn and Improve** - Fix what you discover
8. **Make It Continuous** - Regular experiments, automated

---

*Next: Part IV - The Systemic Perspective*
