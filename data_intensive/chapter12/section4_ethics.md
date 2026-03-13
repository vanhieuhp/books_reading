# Chapter 12: Ethics of Data Systems - Discussion Exercises
Book: Designing Data-Intensive Applications
Section: 4. Doing the Right Thing: Ethics of Data Systems

---

## Overview

This section covers the ethical responsibilities of data engineers and the societal impact of data systems. Since this is a philosophical/policy topic rather than a technical one, these exercises are **discussion/analysis-based** rather than SQL-based.

---

## Exercise 1: Understanding Bias in Data Systems

### Background
Machine learning models are trained on historical data, which may reflect existing biases in society.

### Discussion Questions

1. **Historical Bias Discovery**
   - Consider a dataset of past loan approvals at a bank
   - If certain demographics were historically denied loans at higher rates, what happens when you train a model on this data?
   - How can you detect this bias before deploying the model?

2. **Proxy Discrimination**
   - Sometimes discrimination happens through "proxy variables"
   - Example: A model might not explicitly use race, but zip code correlates with race
   - How would you identify and mitigate proxy discrimination in your models?

3. **Your Task**: For each scenario below, identify:
   - What bias might exist in the training data?
   - What would be the impact when the model is deployed?
   - What mitigation strategies could you use?

   | Scenario | Potential Bias | Impact | Mitigation |
   |----------|---------------|--------|------------|
   | Credit scoring model | ? | ? | ? |
   | Hiring algorithm | ? | ? | ? |
   | Criminal risk assessment | ? | ? | ? |
   | Healthcare triage system | ? | ? | ? |

---

## Exercise 2: Surveillance and Privacy

### Background
The data architectures we've learned about (event logs, CDC, analytics warehouses) are powerful tools for tracking user behavior.

### Discussion Questions

1. **Data Minimization Principle**
   - The book argues for collecting only necessary data
   - Question: If you're building an e-commerce platform, what customer data do you **truly need** vs what would be **nice to have**?

2. **Purpose Limitation**
   - Data collected for one purpose (e.g., fraud detection) might be useful for another (e.g., marketing)
   - Is it ethical to use data for purposes other than why it was collected?
   - What consent would be needed?

3. **Right to be Forgotten**
   - GDPR gives users the right to request data deletion
   - Challenge: In an event log architecture, how would you delete all user data?
   - What if the data has already been derived into search indexes, caches, and analytics?

---

## Exercise 3: Feedback Loops and Self-Fulfilling Prophecies

### Background
Predictive systems can create feedback loops that amplify initial biases.

### Exercise: Map the Feedback Loop

Consider this scenario:
> A predictive policing algorithm flags certain neighborhoods as "high crime" areas. Police increase patrols in these areas. More arrests are made (due to increased presence, not increased crime). The algorithm sees more arrests and increases its prediction for these areas.

#### Your Task: Diagram and Analyze

```
┌─────────────────────────────────────────────────────────────┐
│                    FEEDBACK LOOP DIAGRAM                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   [Initial Data] ──► [Model Prediction] ──► [Action]       │
│        ▲                                              │     │
│        │                                              │     │
│        └──────────────────────────────────────────────┘     │
│                    (How the loop closes)                   │
└─────────────────────────────────────────────────────────────┘
```

**Questions:**
1. Where does the initial bias come from?
2. At what point does the model stop reflecting reality?
3. How would you break this feedback loop?
4. What metrics would you track to detect this problem?

---

## Exercise 4: The Engineer's Responsibility

### Background
Kleppmann argues that engineers are not just "implementing specifications" - they are making design decisions that affect millions of people.

### Reflection Exercise: Your Ethical Decision Framework

Answer these questions for yourself:

1. **Should We Build This?**
   - Before building a system, ask:
     - Who benefits from this system?
     - Who might be harmed?
     - Could this system be misused?
     - What happens if it fails or is attacked?

2. **Red Flags to Watch For**
   - Mark each as Red, Yellow, or Green:
     - [ ] "We just need the data for analytics, not identifying users"
     - [ ] "The algorithm is just a recommendation, humans still decide"
     - [ ] "Everyone else does it this way"
     - [ ] "We can always change it later"
     - [ ] "The lawyers approved it, so it's fine"

3. **Speaking Up**
   - What would you do if:
     - Your manager asks you to implement a feature you believe is unethical?
     - You discover your system is being used in ways you didn't intend?
     - A colleague suggests a "quick fix" that would create technical debt or ethical issues?

---

## Exercise 5: Privacy-Preserving Techniques

### Technical Exercise (SQL-Inspired)

While we can't implement full privacy-preserving tech in this exercise, let's think about the concepts:

1. **Data Anonymization**
   ```sql
   -- Original (PII exposed)
   SELECT name, email, address, purchase_history FROM users;

   -- Anonymized (generalized)
   SELECT
     CONCAT(LEFT(name, 1), '.') as name_init,
     SUBSTRING(email, POSITION('@' IN email) + 1) as email_domain,
     CONCAT(address, ' (city removed)') as location,
     COUNT(*) as total_purchases
   FROM users
   GROUP BY user_id;
   ```

2. **Differential Privacy** (conceptual)
   - Adding "noise" to query results so individual records can't be identified
   - Trade-off: Privacy vs Accuracy
   - Question: Would you accept 5% inaccuracy in exchange for guaranteed privacy?

3. **Federated Learning** (conceptual)
   - Train models on distributed data without centralizing it
   - Question: What are the challenges of this approach?

---

## Exercise 6: Real-World Case Analysis

### Your Task: Analyze a Data Ethics Scenario

Choose one of these real-world scenarios (or find your own) and analyze it:

1. **Cambridge Analytica / Facebook**
   - How did data collected for "research" get used for political targeting?
   - What went wrong in the data governance?

2. **Amazon Hiring Algorithm**
   - Amazon scrapped an AI hiring tool that was biased against women
   - What training data caused this bias?

3. **COMPAS Recidivism Algorithm**
   - Used to predict criminal recidivism
   - Found to be biased against Black defendants
   - The "accuracy" was similar for both groups - so what was the problem?

4. **Social Credit Score**
   - China's social credit system
   - What are the ethical implications of scoring citizens?

### Analysis Template

```
SCENARIO: [Name]

1. WHAT HAPPENED?
   -

2. WHAT DATA WAS INVOLVED?
   -

3. WHAT WAS THE ETHICAL ISSUE?
   -

4. WHO WAS HARMED?
   -

5. HOW COULD IT HAVE BEEN PREVENTED?
   -

6. WHAT WOULD YOU HAVE DONE DIFFERENTLY?
   -
```

---

## Exercise 7: Building Ethical Systems - Practical Steps

### Action Items

For your own projects, consider:

1. **Data Audit**
   - [ ] What data do we collect?
   - [ ] Why do we need each piece of data?
   - [ ] How long do we keep it?
   - [ ] Who has access?

2. **Impact Assessment**
   - [ ] Who will use this system?
   - [ ] How could it be misused?
   - [ ] What happens if it's wrong?
   - [ ] Is there any way to appeal or correct errors?

3. **Transparency**
   - [ ] Can users understand how decisions affecting them are made?
   - [ ] Can we explain why a model made a particular decision?
   - [ ] Do we tell users what data we have about them?

4. **Security**
   - [ ] What happens if this data is breached?
   - [ ] How are we protecting sensitive information?
   - [ ] What's our incident response plan?

---

## Summary

### Key Ethical Principles

| Principle | Description | Practical Action |
|-----------|-------------|------------------|
| **Data Minimization** | Collect only what you need | Audit your data collection |
| **Purpose Limitation** | Use data only for stated purpose | Document use cases |
| **User Control** | Let users see/correct/delete their data | Build user dashboards |
| **Informed Consent** | Users understand what's collected | Clear privacy policies |
| **Fairness** | Check for bias in decisions | Audit models regularly |
| **Transparency** | Explain how systems work | Document algorithms |
| **Security** | Protect data from breaches | Implement security best practices |

### The Big Question

> "The question is not just 'Can we build it?' but 'Should we build it?'"

As data engineers, we have the power to build systems that affect millions. With that power comes responsibility.

---

## Further Reading

- "Weapons of Math Destruction" by Cathy O'Neil
- "Artificial Unintelligence" by Meredith Broussard
- "Ethics for the Information Age" by Mike Quinn
- GDPR (General Data Protection Regulation)
- ACM Code of Ethics

---

## Discussion Prompts for Group Study

1. What's the most unethical data practice you've encountered in a product?
2. How do you balance business needs with user privacy?
3. Should engineers have the right to refuse working on projects they find unethical?
4. How do you explain technical trade-offs to non-technical stakeholders?
5. What's the hardest ethical decision you've had to make in your career?
