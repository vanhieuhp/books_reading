# Chapter 5: Generics — Overview

> **Chapter Theme:** Master the type system to catch bugs at compile time.

---

## Items Covered (26–33)

| Item | Title | Key Concept |
|------|-------|-------------|
| Item 26 | Don't Use Raw Types | Always use `<T>` |
| Item 27 | Eliminate Unchecked Warnings | Every warning = potential bug |
| Item 28 | Prefer Lists to Arrays | Arrays + generics = danger |
| Item 29 | Favor Generic Types | Reusable classes need `<T>` |
| Item 30 | Favor Generic Methods | Static utils need `<T>` |
| Item 31 | Use Bounded Wildcards | PECS: extends/super |
| Item 32 | Combine Generics and Varargs Judiciously | Heap pollution risk |
| Item 33 | Consider Typesafe Heterogeneous Containers | Use `Class<T>.cast()` |

---

## Quick Reference

### PECS Rule
- **Producer** (reading): `List<? extends T>` → can read T, can't write
- **Consumer** (writing): `List<? super T>` → can write T, reads as Object

### Type Erasure
- Generics exist only at compile time
- `<T>` becomes `Object` at runtime
- Can't create `new T()` or `new T[]()`

### Safe Patterns
- Use `Class<T>` tokens for heterogeneous containers
- Use `@SafeVarargs` only when forwarding varargs
- Use `Class.cast()` instead of unchecked casts

---

## Learning Path

| Step | File | Focus |
|------|------|-------|
| 1 | `01_guidelines.md` | Core rules and quick reference |
| 2 | `02_code_examples.md` | Patterns in action |
| 3 | `03_explain_why.md` | JVM mechanics |
| 4 | `04_exercises.md` | Hands-on practice |
| 5 | `05_use_cases.md` | Real Spring Boot scenarios |
| 6 | `06_advice_recommendations.md` | Senior insights |
| 7 | `07_interview_questions.md` | Interview prep |

---

## Exercises Summary

| # | Title | Difficulty | Tests |
|---|-------|-----------|-------|
| 1 | Fix Raw Type Bug | Beginner | Item 26 |
| 2 | Generic Repository | Intermediate | Item 29 |
| 3 | Wildcard Debug | Intermediate | Item 31 |
| 4 | Typesafe Event Bus | Advanced | Item 33 |
| 5 | Fix Generic Method | Beginner | Item 27 |
| 6 | PECS Refactoring | Intermediate | Item 31 |
| 7 | Generic Builder | Advanced | Items 26-33 |

---

## Framework Mapping

| Pattern | Item | Spring/Hibernate |
|---------|------|------------------|
| Generic Response DTO | 26 | `ResponseEntity<T>` |
| Generic Service | 29 | `JpaRepository<T, ID>` |
| Generic Methods | 30 | `Collections.sort()` |
| Bounded Wildcards | 31 | `List<? extends Entity>` |
| Safe Varargs | 32 | `Arrays.asList()` |
| Type Tokens | 33 | `ObjectMapper.readValue()` |

---

## Modern Java (16+)

- **Records** eliminate generic DTO boilerplate
- **Sealed classes** work well with generics for exhaustive switching
- **Pattern matching** reduces need for some casts
- **Var** works with generics: `var users = new ArrayList<User>()`

---

## Next Steps

1. Read through `01_guidelines.md` to understand the rules
2. Study `02_code_examples.md` for patterns
3. Do exercises in `04_exercises.md`
4. Review `06_advice_recommendations.md` for senior insights
5. Practice interview questions in `07_interview_questions.md`
