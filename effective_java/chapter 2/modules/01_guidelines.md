# Module 1: Guidelines

## Chapter 2: Creating and Destroying Objects

This module presents the core rules and guidelines from Items 1-9 of Effective Java. Each item provides a clear rule, anti-pattern, and TL;DR summary.

---

## Item 1 — Consider Static Factory Methods Instead of Constructors

✅ **Do:** Use static factory methods with descriptive names like `from()`, `of()`, `valueOf()`, `getInstance()`

❌ **Don't:** Rely solely on multiple constructors with different parameter lists, which can be confusing

💡 **Why it matters:** Static factory methods can return the same object (caching), return subtypes, and have meaningful names that clarify intent. Constructors can only return the exact implementing type.

**TL;DR:** Name your creation methods to reveal intent; don't rely on constructor overloading alone.

---

## Item 2 — Consider a Builder When Faced with Many Constructor Parameters

✅ **Do:** Use the Builder pattern for objects with many optional parameters or complex construction logic

❌ **Don't:** Use telescoping constructors (multiple constructors with progressively more parameters)

💡 **Why it matters:** Telescoping constructors become unmanageable with 4+ parameters. Builders provide readable, type-safe object construction with fluent API.

**TL;DR:** Use builders for complex objects; in Java 16+, consider `record` with named parameters instead.

---

## Item 3 — Enforce the Singleton Property with a Private Constructor or an Enum Type

✅ **Do:** Use enum singleton (`enum Singleton { INSTANCE }`) or private constructor with public static final field

❌ **Don't:** Use double-checked locking or synchronized methods - these are error-prone and unnecessary

💡 **Why it matters:** Singletons are overused but when needed, the enum pattern provides serialization and reflection safety automatically.

**TL;DR:** Prefer enum singletons; in Spring, use `@Scope(Singleton)` annotation instead of manual implementation.

---

## Item 4 — Enforce Noninstantiability with a Private Constructor

✅ **Do:** Add a private constructor to utility classes that shouldn't be instantiated

❌ **Don't:** Leave utility classes instantiable - they'll be accidentally used incorrectly

💡 **Why it matters:** Without a private constructor, the compiler generates a public no-arg constructor, allowing instantiation of classes like `Math` or `Collections`.

**TL;DR:** Always add `private` constructor to utility classes; throw an AssertionError if called.

---

## Item 5 — Prefer Dependency Injection to Hardwired Resources

✅ **Do:** Inject dependencies via constructor, setter, or factory methods (Spring's DI container)

❌ **Don't:** Use `new` to create dependencies inside classes or use static utility classes

💡 **Why it matters:** Hardwired resources make testing impossible and prevent swapping implementations. DI enables loose coupling, testability, and flexibility.

**TL;DR:** In Spring Boot, use constructor injection for mandatory dependencies; embrace the DI container.

---

## Item 6 — Avoid Creating Unnecessary Objects

✅ **Do:** Reuse immutable objects, use static factory methods, avoid auto-boxing in loops

❌ **Don't:** Create new objects in loops, use string concatenation in loops, or ignore autoboxing costs

💡 **Why it matters:** Excessive object creation increases GC pressure, causes pauses, and wastes memory. In high-throughput services, this directly impacts latency.

**TL;DR:** Reuse objects where possible; prefer primitives to boxed primitives; use StringBuilder for concatenation.

---

## Item 7 — Eliminate Obsolete Object References

✅ **Do:** Null out references when they're no longer needed, especially in caches and stack-like structures

❌ **Don't:** Let memory grow unbounded by holding references to objects that should be garbage collected

💡 **Why it matters:** Even with GC, you can have memory leaks from caches, listeners, and static collections holding references.

**TL;DR:** Explicitly null references in stack-like structures; use WeakHashMap for caches.

---

## Item 8 — Avoid Finalizers and Cleaners

✅ **Do:** Implement `AutoCloseable` and use try-with-resources for cleanup

❌ **Don't:** Put critical cleanup logic in `finalize()` or `Cleaner` - they're unreliable and non-deterministic

💡 **Why it matters:** Finalizers and cleaners are unpredictable, slow, and can be bypassed. They don't run promptly and may never run at all.

**TL;DR:** Use try-with-resources for deterministic cleanup; never rely on finalizers for critical resources.

---

## Item 9 — Prefer try-with-resources to try-finally

✅ **Do:** Use try-with-resources for any `AutoCloseable` resource

❌ **Don't:** Manually close resources in finally blocks - exception masking can hide real errors

💡 **Why it matters:** try-finally can mask exceptions and makes cleanup code verbose. try-with-resources handles multiple exceptions and ensures proper closing order.

**TL;DR:** Always use try-with-resources; declare resources in try header for automatic scope management.

---

## Summary Table

| Item | Core Principle | Most Common Violation |
|------|----------------|----------------------|
| 1 | Static factory > constructors | Using constructors for everything |
| 2 | Builder for complex objects | Telescoping constructors |
| 3 | Enum singletons | Manual singleton implementation |
| 4 | Private constructor for utilities | Public utility classes |
| 5 | Dependency injection | `new` for dependencies |
| 6 | Reuse objects | Creating in loops |
| 7 | Null obsolete references | Caches holding references |
| 8 | No finalizers | Cleanup in finalize() |
| 9 | try-with-resources | try-finally for resources |
