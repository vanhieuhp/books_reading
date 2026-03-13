# Chapter 15: Adaptation (Architecture Evolution)

## Chapter Overview

This chapter focuses on how to evolve your architecture as your business grows. Michael Nygard addresses the challenge of building systems that can adapt to changing requirements, scale, and technology while maintaining stability. This is about strategic architecture decisions that enable long-term success.

## The Need for Adaptation

### Why Architecture Must Evolve

**Business Changes**
- New products
- New markets
- New channels
- New regulations

**Scale Changes**
- More users
- More data
- More requests
- More complexity

**Technology Changes**
- New frameworks
- New platforms
- New patterns
- New tools

**Team Changes**
- More developers
- New teams
- Distributed teams
- Skills evolution

## Signs You Need to Adapt

### Technical Signs

**1. Deployment Pain**
- Deployments take hours
- Deployments fail often
- Can't deploy frequently
- Rollback is hard

**2. Performance Issues**
- Slow responses
- Scaling doesn't help
- Database is bottleneck
- Resource utilization poor

**3. Development Slowdown**
- Code conflicts
- Long build times
- Testing takes forever
- Onboarding slow

**4. Reliability Issues**
- Frequent outages
- Cascading failures
- Hard to diagnose
- Recovery slow

### Business Signs

**1. Feature Velocity**
- Features take too long
- Can't ship quickly
- Competition faster
- Market changing

**2. Customer Issues**
- Complaints increasing
- Support tickets up
- Churn increasing
- Satisfaction down

**3. Scalability Limits**
- Hitting ceilings
- Can't grow
- Infrastructure limits
- Cost increasing

## Evolution Strategies

### 1. Modular Monolith

**What It Is**
- Single deployment
- Clear modules
- Boundaries defined
- Internal decoupling

**When to Use**
- Small teams
- Simple domain
- Fast iteration
- Starting point

**Benefits**
- Simple deployment
- Easy debugging
- Fast development
- Clear boundaries

### 2. Service Extraction

**What It Is**
- Extract modules to services
- One at a time
- Maintain compatibility
- Gradual transition

**When to Use**
- Team growing
- Modules independent
- Scaling needs
- Technology changes

**Process**
1. Identify boundary
2. Define contract
3. Extract service
4. Route traffic
5. Remove old code

### 3. Strangler Pattern

**What It Is**
- New system beside old
- Gradually migrate
- Feature by feature
- Old system fades away

**When to Use**
- Rewrite required
- Can't big bang
- Risk mitigation
- Gradual transition

**Process**
1. Build new alongside
2. Route some traffic
3. Increase traffic
4. Remove old
5. Decommission old

### 4. Branch by Abstraction

**What It Is**
- Create abstraction
- Change implementation
- No branch needed
- Feature flag control

**When to Use**
- Refactoring
- Technology change
- Gradual migration
- Safe changes

**Process**
1. Create abstraction
2. Implement new behind flag
3. Test new
4. Switch flag
5. Remove old

## Scaling Patterns

### 1. Horizontal Scaling

**What It Is**
- Add more instances
- Stateless services
- Load balancer
- Auto-scaling

**When to Use**
- Request-based load
- Stateless operations
- Cost-effective
- High availability

### 2. Vertical Scaling

**What It Is**
- Bigger machines
- More resources
- Single instance
- Hardware limits

**When to Use**
- Simple applications
- Database scaling
- Initial growth
- Quick wins

### 3. Database Scaling

**Read Scaling**
- Read replicas
- Caching
- CQRS
- Materialized views

**Write Scaling**
- Sharding
- Partitioning
- Distributed databases
- Event sourcing

### 4. Architectural Patterns

**CQRS**
- Separate read/write
- Optimize each
- Eventual consistency
- Complexity cost

**Event Sourcing**
- Store events
- Rebuild state
- Audit trail
- Complexity cost

**Saga Pattern**
- Distributed transactions
- Compensation
- Eventual consistency
- Complexity cost

## Technology Evolution

### When to Change Technology

**Signs**
- Technology EOL
- Better options
- Scaling limits
- Skills gap

**Considerations**
- Migration cost
- Learning curve
- Community support
- Long-term viability

### How to Evolve Technology

**1. Dual Running**
- Run both systems
- Route some traffic
- Verify behavior
- Gradually switch

**2. Facade Pattern**
- New system behind facade
- Old system continues
- Gradually move
- Remove facade

**3. strangler for Technology**
- Build new
- Route traffic
- Verify
- Remove old

### Common Technology Evolutions

**Database**
- Monolith → Distributed
- Relational → Polyglot
- On-premise → Cloud
- Bare metal → Containers

**Application**
- Monolith → Microservices
- Synchronous → Async
- REST → GraphQL
- Server → Serverless

**Infrastructure**
- Bare metal → VM → Container → Serverless
- Single zone → Multi-AZ → Multi-region
- Manual → Automated → Orchestrated

## Team Evolution

### Scaling Teams

**Conway's Law**
- "Organizations which design systems are constrained to produce designs which are copies of the communication structures of these organizations"

**Implications**
- Team structure affects architecture
- Architecture affects team structure
- Must evolve together

### Team Patterns

**1. Team per Service**
- Small team per service
- Full ownership
- Fast iteration
- Communication overhead

**2. Platform Teams**
- Infrastructure team
- Platform team
- Application teams
- Clear boundaries

**3. Squad Model**
- Cross-functional
- End-to-end ownership
- Clear mission
- Autonomy with alignment

### Enabling Teams

**Autonomy**
- Ownership
- Decision making
- Delivery
- Technical choice

**Alignment**
- Shared goals
- Clear boundaries
- Communication
- Standards

## Managing Evolution

### Portfolio Management

**What to Track**
- Technical debt
- Age of systems
- Risk factors
- Dependencies

**Decisions**
- What to build new
- What to maintain
- What to replace
- What to retire

### Investment Balance

**How to Balance**
- 70% maintenance
- 20% evolution
- 10% innovation

**Adjust for Context**
- Startup vs enterprise
- New vs legacy
- Stable vs changing

### Governance

**What to Govern**
- Architecture patterns
- Technology standards
- Security requirements
- Integration patterns

**How to Govern**
- Guidelines not rules
- Review not approval
- Coaching not control
- Standards with exceptions

## Common Pitfalls

### 1. Premature Optimization

**Problem**
- Scaling before needed
- Complex patterns early
- Over-engineering
- Wasted effort

**Solution**
- YAGNI
- Measure first
- Solve current problems
- Evolve as needed

### 2. Never Evolving

**Problem**
- Technical debt
- Legacy systems
- Unable to change
- High risk

**Solution**
- Regular refactoring
- Pay down debt
- Plan evolution
- Invest in future

### 3. Big Bang Rewrite

**Problem**
- Long timeline
- High risk
- Feature freeze
- Business disruption

**Solution**
- Incremental change
- strangler pattern
- Parallel running
- Gradual migration

### 4. Ignoring Team

**Problem**
- Architecture doesn't fit team
- Communication overhead
- Slow development
- Friction

**Solution**
- Consider team structure
- Evolve together
- Communication channels
- Conway's law

## Actionable Takeaways

1. **Monitor Technical Health** - Know when to evolve
2. **Plan for Evolution** - Architecture should adapt
3. **Start Simple** - Don't over-engineer
4. **Extract When Needed** - Modular before microservices
5. **Manage Technical Debt** - Pay down regularly
6. **Balance Investment** - Maintenance vs evolution
7. **Align Team and Architecture** - Conway's law
8. **Make Incremental Changes** - Avoid big bangs

---

*Next: Chapter 16 - The Systemic View*
