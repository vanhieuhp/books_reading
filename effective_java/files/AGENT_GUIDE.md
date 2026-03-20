# Effective Java 3rd Edition — AI Agent Learning Guide

## Purpose
This guide instructs an AI agent on how to read each chapter markdown and generate rich, deep-dive learning content for a Java developer. Each chapter file contains structured metadata that the agent must use to produce all 7 learning modules below.

---

## Agent Instructions

When a user provides a chapter file (e.g. `ch02_creating_destroying_objects.md`), you must generate ALL 7 sections below in order. Do not skip any section. Tailor depth and complexity to the items listed in the chapter.

---

## 7 Required Output Sections

### 1. 📘 GUIDELINE
- Summarize the core principle of each item in 2–4 sentences
- State the rule clearly: what TO do and what NOT to do
- Highlight which items are most commonly violated in real codebases
- Group related items together when they share a principle

### 2. 💻 CODE EXAMPLE
- For every item, provide at least one BAD example (❌) and one GOOD example (✅)
- Add inline comments explaining each key line
- Use realistic, production-like scenarios (not just toy examples)
- Include compilation-ready Java code with proper imports where relevant
- For Java 8+ items, show before/after lambda/stream transformations

### 3. 🧠 EXPLAIN WHY
- Explain the underlying JVM or language mechanism that motivates the rule
- Reference specific Java specifications or JVM behavior where relevant
- Use analogies for abstract concepts (memory model, type erasure, etc.)
- Answer the question: "What goes wrong if I ignore this?"
- Include performance, security, and maintainability dimensions

### 4. 🏋️ EXERCISE
- Provide 3–5 hands-on coding exercises per chapter (not just Q&A)
- Each exercise must have: a problem statement, starter code, and expected outcome
- Include at least one refactoring exercise (fix the broken code)
- Include at least one design exercise (build something from scratch)
- Difficulty levels: Beginner / Intermediate / Advanced — label each

### 5. 🌍 USE CASE
- Show each item applied in a real-world system: e-commerce, banking, microservices, etc.
- Describe the scenario, the problem it solves, and the solution pattern
- Include a mini architecture note when relevant (e.g. "in a Spring Boot service...")
- Map items to popular frameworks: Spring, Hibernate, Jackson, Guava, etc.

### 6. 💡 ADVICE & RECOMMENDATIONS
- Give opinionated, senior-developer advice: when to bend the rules
- List common traps and gotchas that are NOT obvious from the rule alone
- Recommend tools: static analysis (SpotBugs, SonarQube, Checkstyle), IDE plugins
- Provide a "checklist" the developer can use during code review
- Reference related patterns (GOF design patterns, SOLID principles) where applicable

### 7. 🎯 INTERVIEW QUESTIONS
- Provide 8–12 interview questions per chapter ranging from Junior to Senior level
- Label each: [Junior] / [Mid] / [Senior] / [System Design]
- For each question, provide:
  - The question itself
  - What the interviewer is testing
  - A model answer (2–5 sentences)
  - A follow-up question
- Include at least 2 tricky/gotcha questions per chapter

---

## Tone & Style Rules
- Use **concrete > abstract**: always ground explanations in real code
- Use **short paragraphs**: max 4 lines per paragraph
- Use **emojis as section markers** for scanability
- Use **tables** for comparisons (e.g. checked vs unchecked exceptions)
- **Bold** the most important sentence in each explanation
- Always end with a "TL;DR" one-liner for each item

---

## Chapter File Format

Each chapter file follows this schema:

```
# Chapter N: Title
## Overview
## Items (structured list with metadata per item)
## Key Concepts
## Relationships (links to other chapters)
## Agent Prompt (customized instruction for this chapter)
```

The agent must read ALL sections before generating output. The `## Agent Prompt` section contains chapter-specific instructions that override or extend the defaults above.

---

## Output Format

Generate output as a well-structured markdown document with:
- A header per section (###)
- Fenced code blocks with `java` syntax highlighting
- Tables where comparisons are needed
- A summary card at the end of each chapter

Minimum output length: 800 words per chapter. Recommended: 1500–3000 words.

---

## Chapter Index

| File | Chapter | Items | Focus |
|------|---------|-------|-------|
| `ch02_creating_destroying_objects.md` | 2 | 1–9 | Object lifecycle |
| `ch03_methods_common_to_all_objects.md` | 3 | 10–14 | Object contracts |
| `ch04_classes_and_interfaces.md` | 4 | 15–25 | Type system design |
| `ch05_generics.md` | 5 | 26–33 | Type safety |
| `ch06_enums_and_annotations.md` | 6 | 34–41 | Special types |
| `ch07_lambdas_and_streams.md` | 7 | 42–48 | Functional Java |
| `ch08_methods.md` | 8 | 49–56 | API design |
| `ch09_general_programming.md` | 9 | 57–68 | Language idioms |
| `ch10_exceptions.md` | 10 | 69–77 | Error handling |
| `ch11_concurrency.md` | 11 | 78–84 | Thread safety |
| `ch12_serialization.md` | 12 | 85–90 | Object persistence |
