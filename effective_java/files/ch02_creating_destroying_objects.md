# Chapter 2: Creating and Destroying Objects

## Overview
This chapter covers the entire lifecycle of Java objects — from instantiation strategies to garbage collection readiness. It establishes foundational patterns that affect API design, memory efficiency, and code clarity throughout an entire codebase.

**Core Theme:** Prefer expressive, controlled object creation over raw constructors. Eliminate unnecessary object creation and resource leaks.

**Why This Matters:** Poor object creation patterns are one of the most common sources of Java performance issues, API rigidity, and subtle bugs in production systems.

---

## Items

### Item 1 — Consider static factory methods instead of constructors
- **Rule:** Prefer named static factory methods over public constructors for object creation
- **Key Benefits:** Descriptive names, instance caching, subtype returns, reduced verbosity
- **Anti-pattern:** `new Boolean(true)` — creates a new object every time
- **Pattern:** `Boolean.valueOf(true)` — returns a cached instance
- **Common names:** `of`, `from`, `valueOf`, `getInstance`, `newInstance`, `create`, `get[Type]`
- **Drawback:** Classes with only static factories and no public constructors cannot be subclassed; harder to find in Javadoc

### Item 2 — Consider a builder when faced with many constructor parameters
- **Rule:** Use the Builder pattern when a class has 4+ parameters, especially optional ones
- **Anti-patterns:** Telescoping constructors (unreadable), JavaBeans (thread-unsafe mid-construction)
- **Builder Benefits:** Readable, immutable objects, fluent API, compile-time safety
- **Note:** Builder is especially useful with class hierarchies (abstract builder + concrete builder)
- **When NOT to use:** Simple 1–3 parameter classes where a constructor is perfectly readable

### Item 3 — Enforce the singleton property with a private constructor or an enum type
- **Rule:** Prefer single-element enum for singletons over private constructor + static field
- **Enum singleton advantages:** Serialization-safe, reflection-proof, thread-safe by default
- **Private constructor approach:** Still vulnerable to reflection attacks via `setAccessible(true)`
- **Use case:** Stateless service objects, configuration holders, registry objects

### Item 4 — Enforce noninstantiability with a private constructor
- **Rule:** Utility classes (only static methods/fields) must have a private constructor + `throw AssertionError()`
- **Why:** Java provides a default public no-arg constructor if none is declared
- **Common mistake:** Abstract class does NOT prevent instantiation — it can be subclassed

### Item 5 — Prefer dependency injection to hardwiring resources
- **Rule:** Classes that depend on external resources should receive them via constructor injection
- **Anti-pattern:** `this.lexicon = Lexicon.INSTANCE` inside a class — hardwires dependency, kills testability
- **DI Benefits:** Testable (mockable), reusable, flexible
- **Variant:** Pass a `Supplier<T>` factory for lazy resource creation

### Item 6 — Avoid creating unnecessary objects
- **Rule:** Reuse objects when possible; never create new objects when an existing one will do
- **Worst offender:** `new String("literal")` — always wrong
- **Autoboxing trap:** `Long sum = 0L; sum += i` — creates millions of `Long` instances
- **Reuse pattern:** Compile regex `Pattern` once and cache it instead of `String.matches()` in a loop
- **Note:** This is an optimization item — don't obsessively pre-optimize; measure first

### Item 7 — Eliminate obsolete object references
- **Rule:** Null out references to objects that are no longer needed, especially in self-managed memory
- **Classic case:** Stack implementation that shrinks but keeps references in the backing array
- **Other sources:** Caches (use `WeakHashMap`), listeners/callbacks (use weak references)
- **Rule of thumb:** Nulling out is the exception, not the norm — only for self-managed memory pools

### Item 8 — Avoid finalizers and cleaners
- **Rule:** Never use finalizers; use cleaners only as a safety net or for non-critical native resources
- **Why finalizers are dangerous:** No guaranteed execution time, JVM may never run them, performance cost, exception swallowing, security attack vector (finalizer attack)
- **Correct pattern:** Implement `AutoCloseable` and use `try-with-resources`
- **Cleaner use:** Can act as a "backup" close, but should not be relied upon

### Item 9 — Prefer try-with-resources to try-finally
- **Rule:** Always use `try-with-resources` for resources that must be closed (`InputStream`, `Connection`, etc.)
- **Why try-finally fails:** If both `try` block and `finally` block throw, the first exception is silently swallowed
- **try-with-resources:** Correctly suppresses secondary exceptions (accessible via `getSuppressed()`)
- **Requirement:** Resource must implement `AutoCloseable`

---

## Key Concepts

| Concept | Item | JVM Impact |
|---|---|---|
| Static factory caching | 1 | Reduces GC pressure |
| Builder pattern | 2 | Enables immutability |
| Enum singleton | 3 | Thread-safe, serialization-safe |
| Autoboxing cost | 6 | Hidden object allocation |
| Memory leak via reference | 7 | Prevents GC collection |
| AutoCloseable | 8, 9 | Deterministic resource cleanup |

---

## Relationships to Other Chapters
- Item 17 (Ch 4): Immutability pairs with Builder (Item 2)
- Item 82 (Ch 11): Thread safety of singletons (Item 3)
- Item 50 (Ch 8): Defensive copies relate to Item 6 (when copies ARE necessary)

---

## Agent Prompt

When generating content for this chapter, pay special attention to:

1. **Item 1 vs Item 2 decision tree** — generate a flowchart-style guide: "When should I use a static factory? When a Builder? When a plain constructor?"

2. **Item 6 autoboxing trap** — this is a very common performance bug. Generate a micro-benchmark example showing the performance difference between `Long` and `long` in a summation loop.

3. **Item 9 — show the suppressed exception problem** with a concrete example of try-finally losing an exception, then show how try-with-resources correctly preserves it.

4. **For exercises:** Include one exercise where students must refactor a "telescoping constructor" class (4+ constructors) into a Builder pattern step by step.

5. **For interview questions:** Include the classic "What's wrong with `new String(\"hello\")`?" and the trickier "Explain the finalizer attack and how enums prevent it."

6. **For use cases:** Map Item 5 (DI) to Spring `@Autowired`, showing how the pattern scales from manual DI to framework DI.

7. **Advice:** Give a strong opinion on `Optional` as a factory method return type (foreshadowing Item 55 in Ch 8).
