# Chapter 4: Classes and Interfaces

## Effective Java — Items 15–25

Welcome to Chapter 4! This folder contains comprehensive learning materials for mastering class and interface design in Java.

---

## 📚 Learning Modules

| Module | Description |
|--------|-------------|
| [01-guidelines.md](./01-guidelines.md) | Quick reference of all 11 items with do/don't rules |
| [02-code-examples.md](./02-code-examples.md) | Production-ready code examples (bad vs good) |
| [03-deep-dive.md](./03-deep-dive.md) | JVM mechanics and "why" behind each rule |
| [04-exercises.md](./04-exercises.md) | Hands-on coding exercises |
| [05-use-cases.md](./05-use-cases.md) | Real-world scenarios with Spring/Hibernate |
| [06-advice.md](./06-advice.md) | Senior developer tips and code review checklist |
| [07-interview-questions.md](./07-interview-questions.md) | Interview prep with model answers |

---

## 🎯 Learning Path

```
1. Start with: 01-guidelines.md
   → Get the rules straight

2. Read: 02-code-examples.md
   → See the patterns in action

3. Understand: 03-deep-dive.md
   → Learn the "why"

4. Practice: 04-exercises.md
   → Apply what you learned

5. Apply: 05-use-cases.md
   → See real-world applications

6. Review: 06-advice.md
   → Get senior tips

7. Prepare: 07-interview-questions.md
   → Test your knowledge
```

---

## 📋 Items Covered

| Item | Topic | Key Takeaway |
|------|-------|--------------|
| 15 | Minimize Accessibility | Start private, relax only when needed |
| 16 | Accessors, Not Public Fields | Getters enable future changes |
| 17 | Minimize Mutability | Immutability = thread safety |
| 18 | Composition Over Inheritance | Delegation > inheritance |
| 19 | Design for Inheritance or Prohibit It | Document or make final |
| 20 | Prefer Interfaces to Abstract Classes | Flexibility over code reuse |
| 21 | Use Interfaces Only to Define Types | Don't put constants in interfaces |
| 22 | Favor Static Member Classes | Avoid memory leaks |
| 23 | Prefer Class Hierarchies to Tagged Classes | Let types work for you |
| 24 | Static Factory Methods Over Constructors | Named creation |
| 25 | One Top-Level Class Per File | One public class = one file |

---

## 🔗 Related Chapters

- **Chapter 2** — Creating Objects (Items 1-9): Static factories, builders, dependency injection
- **Chapter 3** — Common Methods (Items 10-14): equals, hashCode, toString
- **Chapter 5** — Generics (Items 26-33): Type parameters and wildcards
- **Chapter 6** — Enums & Annotations (Items 34-41): Sealed classes, pattern matching

---

## 🛠️ Quick Examples

### Immutable DTO (Java 16+)
```java
// Just one line!
public record UserDto(Long id, String name, String email) {}
```

### Value Object
```java
public final class Money {
    private final BigDecimal amount;
    private final Currency currency;

    public Money add(Money other) { /* returns new instance */ }
}
```

### Static Factory
```java
public static Payment of(BigDecimal amount, Currency currency) {
    return new Payment(amount, currency, PaymentMethod.STANDARD, null);
}
```

### Composition
```java
public class InstrumentedSet<E> implements Set<E> {
    private final Set<E> delegate;
    // Forward all methods to delegate
}
```

---

## ✅ Code Review Checklist

Copy this to your code reviews:

- [ ] Fields are `private` (unless documented reason)
- [ ] Mutable collections use defensive copies
- [ ] Class is `final` or inheritance is documented
- [ ] "Is-a" relationship is true for inheritance
- [ ] Interfaces define types, not constants
- [ ] Static nested classes when outer ref not needed
- [ ] No tagged classes (use sealed/hierarchy)
- [ ] Static factories for semantic clarity
- [ ] One public class per file

---

## 📖 Further Reading

- *Effective Java, 3rd Edition* by Joshua Bloch — Chapter 4
- *Design Patterns* (GoF) — Strategy, Decorator, Composite
- *Java Concurrency in Practice* — Immutability and thread safety
- *Domain-Driven Design* — Value Objects and Entities

---

## Progress

- [x] Module 1: Guidelines
- [x] Module 2: Code Examples
- [x] Module 3: Deep Dive
- [x] Module 4: Exercises
- [x] Module 5: Use Cases
- [x] Module 6: Advice & Recommendations
- [x] Module 7: Interview Questions

---

*Generated for learning Effective Java, Chapter 4*
