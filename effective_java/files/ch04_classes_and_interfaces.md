# Chapter 4: Classes and Interfaces

## Overview
Classes and interfaces are the fundamental building blocks of Java programs. This is the longest and arguably most impactful chapter in the book. It covers information hiding, immutability, the composition-vs-inheritance decision, interface design, and nested classes — all of which have direct consequences on long-term system maintainability.

**Core Theme:** Design classes to be as small and unexposed as possible. Prefer interfaces and composition over inheritance. Make mutability the exception, not the rule.

**Why This Matters:** Bad class design creates coupling that is nearly impossible to undo once an API is public. The decisions in this chapter directly determine how easy your codebase will be to test, extend, and maintain 3 years later.

---

## Items

### Item 15 — Minimize the accessibility of classes and members
- **Rule:** Make each class and member as inaccessible as possible; start `private`, loosen only when necessary
- **Accessibility ladder:** `private` → package-private → `protected` → `public`
- **Public API contract:** Once public, a field/method becomes part of your API forever (backward compatibility)
- **Common mistake:** Making fields `protected` "for testing" — use package-private tests instead
- **Security note:** Public static final arrays are a security hole — the array contents are mutable even if the reference is final
- **Fix:** Return a defensive copy or use `Collections.unmodifiableList()`

### Item 16 — In public classes, use accessor methods, not public fields
- **Rule:** Public classes should never expose mutable fields; accessor/mutator methods preserve encapsulation
- **Exception:** Package-private or private nested classes may expose fields — less ceremony, no API impact
- **Violation example:** `java.awt.Point` (public fields) — Bloch acknowledges this as a mistake in the JDK
- **Why it matters:** Once you expose a field, you can't add validation, change representation, or add lazy evaluation

### Item 17 — Minimize mutability
- **Rule:** Classes should be immutable unless there's a compelling reason for mutability
- **5 Rules for Immutability:**
  1. No mutating methods
  2. Class cannot be extended (`final` class or private constructors)
  3. All fields `final`
  4. All fields `private`
  5. Exclusive access to any mutable components (defensive copies)
- **Benefits:** Simple, thread-safe, freely shareable, great building blocks for composites
- **Performance:** Immutable objects can share internals (`BigInteger.negate()`)
- **Drawback:** Separate object for each distinct value — mitigate with static factories + caching
- **Guideline:** If a class can't be made fully immutable, limit mutability as much as possible

### Item 18 — Favor composition over inheritance
- **Rule:** Inheritance is powerful but it violates encapsulation; prefer wrapping (composition + forwarding)
- **The classic failure:** Extending `HashSet` to count elements added → `addAll()` calls `add()` internally, causing double-counting
- **Self-use dependency:** Subclasses depend on implementation details of the parent, which can change in future releases
- **The fix:** Wrapper class (Decorator pattern) — hold an instance of the component, forward all calls
- **"IS-A" test:** Inheritance is appropriate ONLY when B truly IS-A A across all contexts, not just current use

### Item 19 — Design and document for inheritance or else prohibit it
- **Rule:** Either design a class for inheritance (document all self-use, provide hooks) or prohibit it (`final` or private constructors)
- **Self-use documentation:** "This implementation calls `add()` in `addAll()` — overriding `add()` affects `addAll()` behavior"
- **Hook methods:** `protected` methods that subclasses can override as well-defined extension points
- **Testing:** The only way to test a class designed for inheritance is to write actual subclasses
- **Restriction:** Constructors must not call overridable methods — they run before the subclass constructor

### Item 20 — Prefer interfaces to abstract classes
- **Rule:** Interfaces are the best tool for defining a type that can have multiple implementations
- **Interface advantages:** Existing classes can implement them easily; no place in hierarchy required; support mix-in types
- **Abstract class limitation:** Single-inheritance means adding an abstract class may force awkward hierarchies
- **Java 8+ default methods:** Interfaces can now provide default implementations — nearly closes the gap with abstract classes
- **Template method pattern:** When you need both interface + shared code, use interface + abstract skeletal implementation class (e.g. `AbstractList`)

### Item 21 — Design interfaces for posterity
- **Rule:** Think carefully before adding default methods to an existing interface — they can break existing implementations
- **The problem:** Default methods are injected into implementations without their knowledge or consent
- **Real example:** `Collection.removeIf()` default method broke Apache Commons `SynchronizedCollection` (not thread-safe)
- **Rule:** Use default methods for new interfaces; avoid adding them to existing interfaces unless absolutely necessary

### Item 22 — Use interfaces only to define types
- **Rule:** Interfaces should define a type that clients can use; they should not export constants
- **Constant interface antipattern:** `interface PhysicalConstants { double AVOGADROS_NUMBER = 6.022e23; }` — implementing just to use constants pollutes the class's API
- **Correct alternatives:** Non-instantiable utility class with `static final` fields; or enum types for related constants
- **Exception:** If constants are tightly bound to a class/interface, they belong there directly

### Item 23 — Prefer class hierarchies to tagged classes
- **Rule:** Tagged classes (with a `kind` or `type` field) are verbose, error-prone, and wasteful; replace with class hierarchies
- **Tagged class problems:** Multiple representations in one class, irrelevant fields per tag, switch statements scattered everywhere
- **The fix:** Abstract base class with one concrete subclass per tag variant
- **Real-world map:** This is the "Replace Type Code with Subclasses" refactoring from Fowler's Refactoring

### Item 24 — Favor static member classes over nonstatic
- **Rule:** Unless you need access to the enclosing instance, make nested classes `static`
- **4 types of nested classes:**
  - Static member class: has no reference to enclosing instance
  - Nonstatic member class: implicitly holds reference to enclosing instance (memory leak risk)
  - Anonymous class: limited to one-expression use; largely replaced by lambdas
  - Local class: rarely used
- **Memory leak:** Nonstatic inner class holds enclosing instance → prevents GC even if the enclosing object should be collected

### Item 25 — Limit source files to a single top-level class
- **Rule:** Never put multiple top-level class definitions in one `.java` file
- **Danger:** The compiler accepts multiple top-level classes in one file, but the result is order-dependent compilation behavior
- **The bug:** Two source files that each define the same class — which one wins depends on which file the compiler processes first
- **Fix:** Always one file per top-level class; nested/inner classes are fine

---

## Key Concepts

| Topic | Item(s) | Core Decision |
|---|---|---|
| Accessibility | 15, 16 | Start private, open only what's needed |
| Immutability | 17 | Default to immutable; mutability is a privilege |
| Composition vs Inheritance | 18, 19 | Inherit only true IS-A; compose everything else |
| Interface vs Abstract Class | 20, 21, 22 | Interfaces for types; abstract classes for implementation sharing |
| Nested Classes | 24 | Static unless enclosing access is required |

---

## Relationships to Other Chapters
- Item 2 (Ch 2): Builder pattern produces immutable objects (Item 17)
- Item 34 (Ch 6): Enums are the right solution for Item 23 (tagged classes)
- Item 78 (Ch 11): Immutability (Item 17) is the best concurrency strategy
- Item 42 (Ch 7): Anonymous classes replaced by lambdas (Item 24)

---

## Agent Prompt

When generating content for this chapter:

1. **Item 18 — The HashSet Count Bug** — This is one of the most illustrative examples in the entire book. Implement the broken `InstrumentedHashSet` that double-counts, explain exactly why at the JVM level, then show the correct `InstrumentedSet` wrapper using composition.

2. **Item 17 — Immutability and Thread Safety** — Show a direct comparison: a mutable `BankAccount` class vs an immutable version. Demonstrate that the immutable version requires zero synchronization while the mutable one requires it everywhere.

3. **Item 20 — Skeletal Implementation Pattern** — Implement a mini `AbstractList`-style example. Show how interface + abstract skeletal class gives the best of both worlds.

4. **For exercises:**
   - Exercise 1 [Intermediate]: Refactor a tagged `Shape` class (with `CIRCLE`/`RECTANGLE` kind field) into a proper hierarchy
   - Exercise 2 [Advanced]: Build an immutable `Range<T extends Comparable<T>>` class from scratch following all 5 immutability rules
   - Exercise 3 [Intermediate]: Identify and fix the memory leak in a nonstatic inner class event listener
   - Exercise 4 [Beginner]: Fix the public static final array vulnerability using `Collections.unmodifiableList()`

5. **For use cases:**
   - Map Item 18 to the Decorator pattern in Spring Security (filter chains)
   - Map Item 17 to Java's `String`, `BigInteger`, and Kotlin's `data class`
   - Map Item 20 to Spring's `AbstractApplicationContext` skeletal implementation

6. **For interview questions:** Include "What is the difference between a default method in an interface and an abstract method in an abstract class?" and the deeper "If interfaces can now have default methods, is there still a reason to use abstract classes?"

7. **Advice:** Give strong opinion on `record` (Java 16+) as the modern answer to Items 15, 16, 17 for value types. Also address Lombok `@Value` as an alternative.
