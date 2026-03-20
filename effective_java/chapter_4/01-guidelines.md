# Chapter 4: Classes and Interfaces

## Items 15–25

---

## 📘 Module 1: Guidelines

Chapter 4 focuses on **class design** — how to structure classes and interfaces for maximum reusability, maintainability, and safety. These are the rules that separate amateur code from professional-grade Java.

---

### Item 15 — Minimize Accessibility (Visibility)

✅ **Do:** Make each class or member as inaccessible as possible — private first, then package-private, then protected, then public.

❌ **Don't:** Expose fields publicly via public fields, especially mutable ones.

💡 **Why it matters:** Exposing internals breaks encapsulation, locks you into implementations, and makes thread-safety harder.

**TL;DR:** Start with `private` and only relax when absolutely necessary.

---

### Item 16 — Public Classes Should Use Accessors, Not Public Fields

✅ **Do:** Use private fields with public getter/setter methods in public classes.

❌ **Don't:** Give public classes public mutable fields.

💡 **Why it matters:** You can't change behavior, validate input, or maintain invariants without methods.

**TL;DR:** Public fields are a one-way door — you can never add validation later without breaking clients.

---

### Item 17 — Minimize Mutability

✅ **Do:** Make classes immutable whenever possible — final class, all fields private final, no setters, defensive copies.

❌ **Don't:** Allow classes to be modified after construction without clear documentation.

💡 **Why it matters:** Immutable objects are inherently thread-safe, can be freely shared, and make reasoning about code easy.

**TL;DR:** Immutability is the foundation of concurrent correctness.

---

### Item 18 — Favor Composition Over Inheritance

✅ **Do:** Use composition (has-a) and forwarding methods instead of extending classes.

❌ **Don't:** Inherit from concrete classes outside your package — it's a ticking time bomb.

💡 **Why it matters:** Inheritance breaks encapsulation — changes to the superclass can silently break subclasses.

**TL;DR:** Inheritance is coupling; composition is flexibility.

---

### Item 19 — Design for Inheritance or Prohibit It

✅ **Do:** Document the self-use pattern if you allow subclassing, or make the class final/sealed.

❌ **Don't:** Leave a class non-final without documenting how methods call each other.

💡 **Why it matters:** Undocumented self-use breaks subclasses in subtle, hard-to-debug ways.

**TL;DR:** Undocumented inheritance is a trap for future maintainers.

---

### Item 20 — Prefer Interfaces to Abstract Classes

✅ **Do:** Define types using interfaces — they allow multiple implementation and are easier to evolve.

❌ **Don't:** Use abstract classes when you could use interfaces + default methods.

💡 **Why it matters:** You can only extend one abstract class but implement many interfaces.

**TL;DR:** Interfaces are the future; abstract classes are for legacy hierarchies.

---

### Item 21 — Use Interfaces Only to Define Types

✅ **Do:** Interfaces should define a type — a contract of behavior.

❌ **Don't:** Add static methods or constants to interfaces that aren't part of the type's contract.

💡 **Why it matters:** Interface pollution confuses implementers and bloats the API.

**TL;DR:** An interface is a "can-do" relationship, not a utility bucket.

---

### Item 22 — Favor Static Member Classes Over Nonstatic

✅ **Do:** Make nested classes static unless you need the enclosing instance.

❌ **Don't:** Create nonstatic inner classes unnecessarily — they hold an implicit reference to the outer instance.

💡 **Why it matters:** Nonstatic classes cause memory leaks and are heavier than necessary.

**TL;DR:** Static nested classes are just top-level classes in disguise.

---

### Item 23 — Prefer Class Hierarchies to Tagged Classes

✅ **Do:** Use inheritance properly — separate classes for separate concepts, linked by a common interface or abstract class.

❌ **Don't:** Use a single class with a `type` tag field to represent multiple variants.

💡 **Why it matters:** Tagged classes are verbose, error-prone, and forgetful — each method must handle every tag.

**TL;DR:** Let the type system work for you — don't fight it.

---

### Item 24 — Use Static Factory Methods Instead of Constructors

✅ **Do:** Provide named static factory methods that convey meaning (e.g., `from()`, `of()`, `valueOf()`).

❌ **Don't:** Just use constructors when a factory method would clarify intent or add flexibility.

💡 **Why it matters:** Factories can cache instances, return subtypes, and have meaningful names.

**TL;DR:** Constructors are for creation; factories are for semantic clarity and control.

---

### Item 25 — Limit Source Files to a Single Top-Level Class

✅ **Do:** Keep exactly one public class per Java file, matching the filename.

❌ **Don't:** Put multiple top-level classes in one file — causes confusion and compilation issues.

💡 **Why it matters:** One class per file prevents ambiguity and compilation conflicts.

**TL;DR:** One public class per file — the filename is the contract.

---

## Quick Reference

| Item | Rule | Common Violation |
|------|------|-----------------|
| 15 | Minimize accessibility | Public fields in DTOs |
| 16 | Use accessors | Public mutable fields |
| 17 | Minimize mutability | Mutable entities |
| 18 | Composition over inheritance | Extending concrete classes |
| 19 | Design for inheritance | Non-final without docs |
| 20 | Interfaces over abstract classes | Using abstract for shared code |
| 21 | Interfaces define types | Constants in interfaces |
| 22 | Static member classes | Nonstatic inner classes |
| 23 | Class hierarchies | Tagged classes |
| 24 | Static factory methods | Only constructors |
| 25 | One class per file | Multiple top-level classes |

---

## Related Chapters

- **Chapter 2** (Items 1-9): Static factories, builders, dependency injection
- **Chapter 3** (Items 10-14): equals, hashCode, toString for immutable objects
- **Chapter 5** (Items 26-33): Generics with interfaces
- **Chapter 6** (Items 34-41): Enums and sealed classes

---

## Modern Java (Java 16+)

| Traditional | Modern Alternative |
|-------------|-------------------|
| Immutable class with getters | `record` |
| Abstract class hierarchies | `sealed interface` |
| Tagged classes | `sealed classes + pattern matching` |

