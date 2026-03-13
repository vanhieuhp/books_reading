# Chapter 12: Adaptation

## Chapter Overview

Chapter 12 explores how systems change over time and how to handle versioning and deployments in a production environment. Michael Nygard addresses the reality that software is never "done" - it must continuously evolve while maintaining stability. This chapter covers strategies for managing change without causing disruptions.

## The Reality of Change

### Why Adaptation Matters

**Systems Evolve**
- New features
- Bug fixes
- Infrastructure changes
- Dependency updates
- Security patches

**Change is Risky**
- Deployments cause outages
- Changes introduce bugs
- Dependencies break
- Backward compatibility issues

### The Challenge

**Requirements**
- Deploy frequently
- Deploy safely
- Deploy fast
- Rollback quickly

**Reality**
- Risk increases with size
- Testing can't catch everything
- Interactions are complex
- Rollback can be hard

## Versioning

### API Versioning

**Why Version**
- Contracts with consumers
- Enable changes
- Support multiple versions
- Graceful migration

### Versioning Strategies

**1. URL Path**
```
/api/v1/users
/api/v2/users
```
- Explicit
- Clear which version
- Requires routing

**2. Header**
```
Accept: application/vnd.api.v1+json
```
- URL stays clean
- Flexible
- Less visible

**3. Query Parameter**
```
/api/users?version=1
```
- Simple
- Easy to test
- Caching issues

### Version Compatibility

**Breaking vs. Non-Breaking**

*Non-Breaking*
- Add new fields
- Add new endpoints
- Make optional fields optional
- Add response fields

*Breaking*
- Remove fields
- Change field types
- Change validation
- Remove endpoints

### Database Versioning

**The Problem**
- Schema changes
- Data migrations
- Rollback complexity
- Downtime concerns

**Solutions**
- Migration scripts
- Backward compatible schemas
- Feature flags for data
- Blue-green databases

## Deployment Strategies

### 1. Big Bang Deployment

**Process**
- Deploy to all at once
- Immediate switch
- All or nothing

**Pros**
- Simple
- Fast
- Complete quickly

**Cons**
- Risky
- Hard to rollback
- No canary

### 2. Rolling Deployment

**Process**
- Replace instances one at a time
- Gradual rollout
- Same version across fleet

**Pros**
- No downtime
- Lower risk
- Simple

**Cons**
- Slow
- Mixed versions
- Hard to rollback

### 3. Blue-Green Deployment

**Process**
- Two identical environments
- Switch traffic at once
- Immediate rollback

**Pros**
- Instant switch
- Easy rollback
- Complete test

**Cons**
- Double resources
- Database complexity
- State synchronization

### 4. Canary Deployment

**Process**
- Small percentage to new version
- Monitor metrics
- Gradual increase

**Pros**
- Real traffic testing
- Fast rollback
- Data-driven

**Cons**
- Complex setup
- Requires good metrics
- Route management

### 5. Feature Flags

**Process**
- Code ships with flags off
- Toggle on per user/percentage
- Instant rollback

**Pros**
- Decouple deploy from release
- Granular control
- Fast rollback

**Cons**
- Code complexity
- Technical debt
- Flag management

## Deployment Architecture

### Deployment Pipeline

**Stages**
1. **Commit** - Code pushed
2. **Build** - Compile, package
3. **Test** - Unit, integration
4. **Stage** - Deploy to staging
5. **Production** - Deploy to prod
6. **Monitor** - Watch metrics

### Deployment Patterns

**Immutable Infrastructure**
- Don't modify running instances
- Replace with new
- Consistent
- Reproducible

**Phoenix Servers**
- Regular rebuilds
- Clean state
- No config drift
- Regular updates

### Rollback Strategies

**Automatic Rollback**
- Trigger on metrics
- Fast response
- No manual intervention

**Manual Rollback**
- Decision-based
- More control
- Slower

**Database Rollback**
- Migrate data back
- Complicated
- Rarely needed

## Handling Dependencies

### Dependency Management

**Types of Dependencies**
- Direct (your code)
- Framework (Spring, Rails)
- Library (external)
- Infrastructure (database, queue)
- Service (external API)

### Dependency Updates

**Strategies**
- Patch regularly
- Test in isolation
- Staged rollout
- Feature flags for risky changes

### Handling External API Changes

**What Can Change**
- Response format
- Authentication
- Rate limits
- Endpoints

**Strategies**
- Version your clients
- Abstract integrations
- Mock for testing
- Monitor changes

## Continuous Delivery

### What is CD?

**Definition**
- Automated deployment pipeline
- Deploy on every change
- Fast feedback
- High confidence

### CD Principles

1. **Build Once**
   - Same artifact through pipeline
   - Proven in staging = proven in prod

2. **Deploy Same Way**
   - Same process staging → prod
   - Reproducible
   - Tested

3. **Artifact-Based**
   - Immutable artifacts
   - Versioned
   - Traceable

4. **Feature Flags**
   - Decouple deploy from release
   - Enable gradual rollout

### CD Pipeline Design

**Fast Feedback**
- Unit tests in seconds
- Integration in minutes
- Deploy in minutes

**Reliable Pipeline**
- Idempotent
- Retry-able
- Well-logged

## Adaptation at Scale

### Multi-Team Coordination

**Challenges**
- Shared dependencies
- Deployment order
- Communication
- Testing integration

**Solutions**
- API contracts
- Versioning strategy
- Feature flags
- Communication channels

### Managing Technical Debt

**Types**
- Code debt
- Test debt
- Infrastructure debt
- Documentation debt

**Strategies**
- Track it
- Pay it down
- Prevent new debt
- Balance with features

## Common Pitfalls

### Versioning Pitfalls
1. Breaking changes without versioning
2. Too many versions
3. No deprecation strategy
4. Version proliferation

### Deployment Pitfalls
1. Manual deployments
2. No rollback plan
3. Deploying on Friday
4. No canarying

### Dependency Pitfalls
1. Outdated dependencies
2. No dependency management
3. Not testing updates
4. No abstraction layer

## Actionable Takeaways

1. **Version Your APIs** - Plan for change
2. **Implement Feature Flags** - Decouple deploy from release
3. **Automate Deployments** - Remove manual steps
4. **Use Canary Deployments** - Test with real traffic
5. **Plan Rollbacks** - Know how to undo
6. **Keep Dependencies Updated** - Don't fall behind
7. **Monitor Deployments** - Watch for problems
8. **Build CD Pipeline** - Automate everything

---

*Next: Chapter 13 - Chaos Engineering*
