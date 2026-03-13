# Case Study: Healthcare.gov Launch Failure (2013)

## Overview

| Field | Value |
|-------|-------|
| **Organization** | US Federal Government (CMS - Centers for Medicare & Medicaid Services) |
| **Year** | 2013 |
| **Impact** | $90B+ program; millions unable to enroll; massive political and public fallout |
| **Root Cause** | Untested code, inadequate capacity planning, unrealistic timeline, contractor issues |

---

## What Happened

The Affordable Care Act (ACA), commonly known as Obamacare, required a new health insurance marketplace (Healthcare.gov). The launch date was set by political timeline—October 1, 2013—rather than technical readiness.

### Timeline

| Date | Event |
|------|-------|
| March 2010 | Affordable Care Act signed into law |
| July 2012 | CMS begins vendor contracting |
| September 2013 | Late-stage testing reveals critical issues |
| October 1, 2013 | Launch day - system crashes |
| October 2013 | Emergency "tech surge" to fix issues |
| December 2013 | Site stabilizes, enrollment exceeds expectations |

### The Technical Disaster

On October 1, 2013, when the site launched:

- **Registration system crashed immediately**
- Users encountered error messages
- Database couldn't handle the load
- External contractors couldn't fix issues quickly due to poor code quality
- Estimated 6-7% of attempted enrollments succeeded initially

---

## Chapter Concepts Applied

### 1. Unrealistic Timeline (Chapter 14: Organizational Pressure)

**Problem**: Political deadline fixed; technical input ignored

- The launch date was set by political pressure (open enrollment period)
- Technical warnings about readiness were overridden
- No feature freeze or code freeze was enforced

**What Should Have Happened**:
- Technical team should have been able to push back on launch date
- Launch readiness gates should have been enforced
- Feature scope should have been reduced to meet timeline

---

### 2. No Load Testing (Chapter 14: Technical Shortcuts)

**Problem**: System tested with "synthetic" load, not real user behavior

- Testing used artificially low load assumptions
- Didn't simulate actual user behavior patterns
- Database capacity severely underestimated

**The Numbers**:
- Designed for ~50,000 concurrent users
- 250,000+ attempted on day one
- Real traffic was 5-10x what was planned for

**What Should Have Happened**:
- Load testing with realistic traffic patterns
- Capacity planning based on marketing projections (not minimums)
- Gradual rollout to manage risk

---

### 3. Silos and Contractor Issues (Chapter 14: Silos)

**Problem**: Multiple contractors, no unified ownership, communication failures

- 55+ contractors working on the project
- Different companies, different codebases, no unified vision
- CGI Federal was the primary contractor
- Responsibility boundaries were unclear

**What Should Have Happened**:
- Unified technical ownership
- Clear escalation paths
- Cross-functional teams including ops/security from day one

---

### 4. Technical Debt (Chapter 14: Technical Debt)

**Problem**: Legacy code pressed into new service

- Code quality was inconsistent
- Poor error handling
- No proper modular design
- "Spaghetti code" from multiple contractors

**What Should Have Happened**:
- Code quality gates in CI/CD
- Architectural review before implementation
- Technical debt tracking and addressing

---

### 5. Success Theater (Chapter 14: Organizational Failure)

**Problem**: "Ready" declared despite known issues

- Leadership declared system ready despite internal warnings
- Testing results were not properly communicated
- Risk assessments were ignored

**What Should Have Happened**:
- Honest assessment of risks communicated to leadership
- Go/no-go decision based on actual readiness
- Transparency about technical limitations

---

## The Technical Details

### Infrastructure Issues

- **Database**: Oracle, with connection issues from day one
- **Capacity**: Severely under-provisioned
- **CDN**: Not properly configured for static assets

### Code Quality Issues

- Poor error handling
- No graceful degradation
- Inadequate logging
- Missing circuit breakers

### Testing Issues

- "Automated testing" was incomplete
- User testing was insufficient
- Integration testing didn't simulate production

---

## The Fix

After the initial failure, a massive "tech surge" was launched:

1. **White House took direct oversight**
2. **QSSI (Quality Software Services, Inc.) took technical lead**
3. **Weekend and holiday work for fixes**
4. **Beta testers brought in for feedback**
5. **Insurance companies given offline enrollment options**

### Results

| Metric | October 2013 | December 2013 |
|--------|-------------|---------------|
| Success Rate | ~6-7% | ~80%+ |
| Daily Enrollments | ~1,000 | ~30,000+ |
| System Availability | Sporadic | Stable |

By end of open enrollment (March 2014):
- 8 million enrolled
- Exceeded expectations

---

## Staff-Level Insights

### What Went Right

1. **Rapid Response**: The administration quickly acknowledged the problem and threw resources at it
2. **Adaptation**: Added offline enrollment options, phone support
3. **Iterative Fixes**: Fixed critical issues first, then stabilized

### Key Lessons for Staff Engineers

1. **Political deadlines must account for technical reality**
   - Push back on unrealistic dates
   - Provide data on what's achievable
   - Offer alternatives (phased rollout, reduced scope)

2. **Volume testing with real traffic patterns is essential**
   - Don't test with artificial loads
   - Simulate realistic user behavior
   - Plan for worst-case, not best-case

3. **Contractor handoffs create knowledge gaps**
   - Ensure documentation
   - Unified architecture ownership
   - Clear responsibility boundaries

4. **"Going live" without adequate rollback is catastrophic**
   - Always have rollback plan
   - Test rollback procedure
   - Know when to rollback

---

## Reusability Template

**Before any high-profile public launch, apply these checks:**

```markdown
1. Load test with realistic traffic patterns
   - Use actual production traffic if possible
   - Test failure modes, not just success

2. Verify rollback procedure works
   - Document it
   - Test it
   - Know time to rollback

3. Include real user scenarios in testing
   - Not just synthetic tests
   - Include actual user workflows
   - Test error paths

4. Have dedicated incident response team on standby
   - Pre-designated roles
   - Communication templates ready
   - Escalation paths clear

5. Don't accept political deadlines without technical review
   - Provide data-driven input
   - Offer alternatives
   - Document risks
```

---

## Related Chapter Concepts

This case study directly illustrates:

- **Chapter 14**: Launch failures are organizational before technical
- **Chapter 3**: Stability anti-patterns (integration sprawl, cascading failures)
- **Chapter 4**: Stability patterns (circuit breakers, bulkheads)
- **Chapter 13**: Chaos engineering (finding weaknesses before launch)

---

## References

- [Healthcare.gov Wikipedia](https://en.wikipedia.org/wiki/Healthcare.gov)
- [The Healthcare.gov Failure - MIT Technology Review](https://www.technologyreview.com/2013/11/05/178182/healthcaregov-what-went-wrong/)
- [GAO Report on Healthcare.gov](https://www.gao.gov/products/GAO-14-694)

---

*Case study compiled for Chapter 14: The Trampled Product Launch*
*From "Release It!" by Michael Nygard*
