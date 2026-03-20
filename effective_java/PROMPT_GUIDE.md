# 🎯 Effective Java Tutor — Prompt Guide
> How to talk to your agent to get the most out of every session

---

## 🗺️ Overview — 5 Ways to Use the Agent

| Mode | When to use | Example trigger |
|---|---|---|
| **Full Chapter Study** | Starting a new chapter from scratch | `"Teach me Chapter 7 — Lambdas and Streams"` |
| **Single Item Deep Dive** | One concept is confusing or important | `"Deep dive on Item 18 — composition over inheritance"` |
| **Targeted Module** | You only need one type of output | `"Give me exercises only for Chapter 5 — Generics"` |
| **Interview Prep** | Preparing for a Java technical interview | `"Interview prep for Chapter 11 — Concurrency"` |
| **Real-world Mapping** | You're working on a feature and want Bloch's take | `"I'm designing a caching layer — which items apply?"` |

---

## 📘 Mode 1: Full Chapter Study

Use this when you're ready to learn an entire chapter end-to-end.
The agent will generate all **7 learning modules** in sequence.

### Basic Trigger
```
Teach me Chapter [N] — [Topic]
```

### Power-Up Versions (add context to get better output)

**Tell the agent your level:**
```
I'm a mid-level Java developer with 3 years of experience.
Teach me Chapter 4 — Classes and Interfaces.
Assume I know the basics of OOP but haven't read Effective Java before.
```

**Tell the agent your goal:**
```
I have a Java interview at [Company] in 2 weeks.
Teach me Chapter 11 — Concurrency with extra focus on interview questions
and the most commonly tested gotchas.
```

**Tell the agent your context:**
```
I'm working on a Spring Boot microservice codebase.
Teach me Chapter 2 — Creating and Destroying Objects.
Map every example to Spring patterns where possible (e.g. @Bean, @Autowired).
```

**Tell the agent what to skip:**
```
Teach me Chapter 9 — General Programming.
I already know Items 57–63 well. Focus on Items 64–68 (reflection, optimization, naming).
```

### All 11 Chapter Triggers (copy-paste ready)
```
Teach me Chapter 2  — Creating and Destroying Objects
Teach me Chapter 3  — Methods Common to All Objects
Teach me Chapter 4  — Classes and Interfaces
Teach me Chapter 5  — Generics
Teach me Chapter 6  — Enums and Annotations
Teach me Chapter 7  — Lambdas and Streams
Teach me Chapter 8  — Methods
Teach me Chapter 9  — General Programming
Teach me Chapter 10 — Exceptions
Teach me Chapter 11 — Concurrency
Teach me Chapter 12 — Serialization
```

---

## 🔬 Mode 2: Single Item Deep Dive

Use this when you want maximum depth on one specific item or concept.
The agent will scope all 7 modules to that one item — making each section 2× richer.

### Basic Trigger
```
Deep dive on Item [N]
```

### Power-Up Versions

**Ask for the "why" first:**
```
Explain Item 17 — Minimize Mutability.
I already know what it says. I want to understand WHY at the JVM level —
memory model, garbage collection, thread safety — not just the rule.
```

**Ask for the "when to break the rule":**
```
Explain Item 18 — Favor Composition over Inheritance.
When is inheritance actually the RIGHT call?
Give me the full decision framework, not just "prefer composition."
```

**Ask for a real-world application:**
```
Explain Item 42 — Prefer Lambdas to Anonymous Classes.
Show me this specifically in the context of Spring's functional bean registration
and WebFlux reactive pipelines.
```

**Ask for a comparison:**
```
Compare Item 70 (checked vs unchecked exceptions) with how
Spring handles exceptions in its DataAccessException hierarchy.
Which approach does Spring use and why?
```

### Targeted Item Prompts (copy-paste ready)
```
Deep dive on Item 1  — Static factory methods
Deep dive on Item 2  — Builder pattern
Deep dive on Item 3  — Singleton with enum
Deep dive on Item 10 — equals contract
Deep dive on Item 11 — hashCode contract
Deep dive on Item 17 — Immutability
Deep dive on Item 18 — Composition over inheritance
Deep dive on Item 26 — Don't use raw types
Deep dive on Item 31 — PECS wildcards
Deep dive on Item 34 — Enums over int constants
Deep dive on Item 42 — Lambdas over anonymous classes
Deep dive on Item 45 — Use streams judiciously
Deep dive on Item 55 — Return Optional judiciously
Deep dive on Item 69 — Exceptions for exceptional conditions
Deep dive on Item 78 — Synchronize shared mutable data
Deep dive on Item 85 — Prefer alternatives to serialization
```

---

## 🏋️ Mode 3: Targeted Module

Use this when you only need one type of output — exercises, interview questions,
code examples, etc. The agent generates that module at 2× depth.

### Module-Specific Triggers

**📘 Guidelines only — quick rules reference:**
```
Give me the guidelines summary for Chapter 5 — Generics.
Just the rules: what to do, what not to do, TL;DR per item.
```

**💻 Code examples only — pattern library:**
```
Show me code examples for all items in Chapter 7 — Lambdas and Streams.
For each item: one bad example and one good example with comments.
Use an e-commerce order processing scenario throughout.
```

**🧠 Explain Why only — deep theory:**
```
Explain the JVM mechanics behind Chapter 5 — Generics.
Focus on type erasure, heap pollution, and why generic arrays are forbidden.
Use analogies — I want intuition, not just rules.
```

**🏋️ Exercises only — practice mode:**
```
Give me exercises for Chapter 11 — Concurrency.
I want: 1 refactoring exercise, 1 debug exercise, 1 design-from-scratch exercise.
Make them Advanced difficulty — production-level scenarios.
```

**🌍 Use Cases only — real-world mapping:**
```
Show me real-world use cases for Chapter 10 — Exceptions.
Map each item to: Spring REST controllers, database transactions,
and microservice error handling patterns.
```

**💡 Advice only — senior dev opinion:**
```
Give me senior developer advice for Chapter 4 — Classes and Interfaces.
Focus on: when to break the rules, common code review mistakes,
and how Java records and sealed classes change the recommendations.
```

**🎯 Interview Questions only — prep mode:**
```
Give me interview questions for Chapter 11 — Concurrency.
I want: 3 Junior, 4 Mid, 3 Senior, 2 System Design questions.
For each: the question, what it tests, a model answer, and a follow-up.
Mark the 2 trickiest gotcha questions clearly.
```

---

## 🎯 Mode 4: Interview Prep

Use this when preparing for a specific interview. The agent generates
targeted questions with model answers and follow-ups.

### Single Chapter Interview Prep
```
Interview prep for Chapter [N] — [Topic].
Level: [Junior / Mid / Senior / Staff]
Company type: [startup / big tech / fintech / enterprise]
```

**Example:**
```
Interview prep for Chapter 11 — Concurrency.
Level: Senior.
I'm interviewing at a fintech company that processes high-frequency trades.
Focus on questions about thread safety in stateful services and
the tradeoffs between synchronization strategies.
```

### Full Book Interview Prep (all chapters)
```
I have a Java technical interview in [timeframe].
Give me a condensed interview guide covering ALL chapters of Effective Java.
For each chapter: top 3 questions a Senior interviewer would ask,
the gotcha question they use to filter candidates, and the model answer.
```

### Role-Specific Interview Prep
```
I'm interviewing for a [role] position. Which chapters of Effective Java
are most important for this role, and what questions should I expect?

Roles to try:
- Backend Java developer at a startup
- Java platform/infrastructure engineer
- Android developer (Java)
- Java API designer at a library company
- Senior engineer at a company migrating from Java 8 to Java 17+
```

---

## 🌍 Mode 5: Real-World Mapping

Use this when you're working on actual code and want Bloch's guidance applied to it.

### By Technology Stack
```
I'm building a [description]. Which items from Effective Java apply most directly?
Give me the top 5 items with code examples in my context.

Examples:
- "I'm building a Spring Boot REST API with PostgreSQL"
- "I'm designing a Java SDK for external developers"
- "I'm refactoring a legacy Java 8 codebase to Java 17"
- "I'm building a Kafka consumer service that processes financial events"
- "I'm writing a multithreaded batch processing job"
```

### By Problem Pattern
```
I keep seeing this pattern in my codebase: [paste code or describe pattern].
Which items from Effective Java address this?
Show me the refactored version following Bloch's recommendations.
```

### By Code Review
```
I'm doing a code review and found this: [paste code].
Which Effective Java items does this violate?
Give me: the violations, why they matter, and the corrected version.
```

### By Design Decision
```
I need to decide: [design question].
What does Effective Java say about this? Give me:
1. The relevant items
2. Bloch's recommendation
3. When you'd make the other choice
4. A code example of both approaches

Example questions:
- "Should I use an abstract class or interface for my base repository?"
- "Should this enum have abstract methods or use a switch statement?"
- "Should I return Optional or throw an exception from this lookup method?"
- "Should I use checked or unchecked exceptions in my service layer?"
```

---

## 🔄 Follow-Up Prompts (use after any response)

### Go Deeper
```
Go deeper on [specific part of the response].
I didn't fully understand [concept]. Explain it differently — use an analogy.
```

### Challenge the Answer
```
You said [X]. But what about [counterexample or edge case]?
When would [the anti-pattern you described] actually be the right choice?
```

### Apply to My Code
```
Now apply this to my actual situation: [paste your code or describe it].
What would you change and why?
```

### Extend the Exercise
```
I finished Exercise [N]. Make it harder — add [constraint or new requirement].
Now I need it to be thread-safe / work with generics / handle null inputs.
```

### Check Your Understanding
```
I'll explain [concept] back to you. Tell me where I'm wrong or incomplete:
[your explanation]
```

### Generate Variations
```
Give me 3 more code examples of [pattern] — different domains this time.
I've seen the banking example. Show me: e-commerce, healthcare, and DevOps tooling.
```

---

## 🧭 Study Path Recommendations

Use these prompts to ask the agent to plan your learning journey.

### For Beginners
```
I'm new to Effective Java. I have [X hours/days] to study.
Build me a study plan: which chapters to do first, in what order,
and how much time to spend on each. My goal is [goal].
```

### For Interview Prep (2 weeks)
```
I have 2 weeks before a Java interview at a [company type].
Prioritize Effective Java chapters by interview relevance for this role.
Give me a day-by-day study plan with: what to read, what prompts to use,
and which exercises to complete each day.
```

### For Code Quality Improvement
```
My team writes Java but doesn't follow Effective Java conventions.
Which 5 chapters would give us the biggest improvement in code quality
with the least learning investment?
Rank them and explain why.
```

### For a Specific Java Version Migration
```
My team is migrating from Java 8 to Java 17.
Which Effective Java items become more important, less important,
or change their recommendation in Java 17?
Focus on: records, sealed classes, pattern matching, text blocks.
```

---

## ⚡ Quick Reference — All Prompts in One Place

```
# FULL CHAPTER
Teach me Chapter [2-12] — [Title]

# SINGLE ITEM
Deep dive on Item [1-90]

# GUIDELINES ONLY
Give me the guidelines summary for Chapter [N]

# CODE EXAMPLES ONLY
Show me code examples for all items in Chapter [N]. Domain: [your domain]

# EXERCISES ONLY
Give me exercises for Chapter [N]. Difficulty: [Beginner/Intermediate/Advanced]

# INTERVIEW QUESTIONS ONLY
Give me interview questions for Chapter [N]. Level: [Junior/Mid/Senior]

# FULL BOOK INTERVIEW PREP
Give me a condensed interview guide covering ALL chapters of Effective Java

# REAL-WORLD MAPPING
I'm building a [system]. Which Effective Java items apply most?

# CODE REVIEW
Which Effective Java items does this code violate? [paste code]

# DESIGN DECISION
What does Effective Java say about [design choice]?

# STUDY PLAN
Build me a study plan for Effective Java. Goal: [goal]. Time: [timeframe]
```

---

## 💬 Conversation Starter Templates

Copy any of these to start a session immediately:

**Template A — Full chapter, give context:**
```
I'm a [level] Java developer working on [type of project].
Teach me Chapter [N] — [Title].
Pay extra attention to [specific concern: interview / code quality / Spring integration / etc.].
```

**Template B — Specific item, problem-first:**
```
I've been struggling with [concept] in my codebase.
I think it relates to Item [N] in Effective Java.
Explain this item fully with all 7 modules, and apply the examples to [my context].
```

**Template C — Interview prep, scoped:**
```
I have a Java interview in [timeframe] at a [company type].
Focus on Chapter [N] — [Title]. 
Generate deep interview questions at [level] difficulty with model answers.
Also flag the 2–3 gotcha questions that trip up candidates at this level.
```

**Template D — Code review / apply now:**
```
Here's code from my current project:

[paste your code]

Review it against Effective Java principles. Tell me:
1. Which items it violates
2. Why each violation matters
3. The corrected version with inline comments
```

**Template E — Decision support:**
```
I'm deciding between [Option A] and [Option B] for [situation].
What do Items [X] and [Y] from Effective Java say about this?
Give me a recommendation with the tradeoffs clearly laid out.
```
