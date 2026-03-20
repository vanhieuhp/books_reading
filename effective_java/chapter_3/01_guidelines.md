# Chapter 3: Methods Common to All Objects — Guidelines

> **Core Theme:** Every Java class inherits from `Object`. This chapter covers the five non-final methods that have explicit general contracts: `equals`, `hashCode`, `toString`, `clone`, and `Comparable.compareTo`. Violating these contracts produces bugs that are subtle, hard to reproduce, and often dangerous.

---

## Overview

Java's object contract system relies on these five methods working correctly. Many critical Java APIs (collections, hashing, sorting) depend on them. **Break the contract → break the ecosystem.**

A broken `equals` or `hashCode` can make objects invisible in a `HashMap`. A bad `compareTo` can corrupt a `TreeSet`. These bugs rarely throw exceptions — they just silently produce wrong answers.

---

## Item 10 — Obey the General Contract When Overriding equals

✅ **Do:** Override `equals` only when logical equality differs from object identity (value classes), and the class doesn't have a parent that already provides it.

❌ **Don't:** Override `equals` for classes that represent unique entities (like `Thread`, `ThreadPoolExecutor`), or mix incompatible types in the comparison.

💡 **Why it matters:** The equals contract has 5 properties that MUST all hold: **Reflexive**, **Symmetric**, **Transitive**, **Consistent**, and **Non-null**. Breaking symmetry is the most common bug — especially when mixing types.

**TL;DR:** If you override equals, you MUST maintain all 5 contract properties; the hardest is transitivity when adding value components to subclasses.

---

## Item 11 — Always Override hashCode When You Override equals

✅ **Do:** Override `hashCode` whenever you override `equals`. Use `Objects.hash()` or follow the 31× multiplier recipe.

❌ **Don't:** Override `equals` without also overriding `hashCode`, or create hash codes that change during an object's lifetime (if the object is used as a HashMap key).

💡 **Why it matters:** Equal objects MUST have equal hash codes. If you break this, objects become "invisible" in hash-based collections — `HashSet.contains()` returns false for objects that are logically equal.

**TL;DR:** The hashCode/equals contract is ironclad: `a.equals(b) → a.hashCode() == b.hashCode()`.

---

## Item 12 — Always Override toString

✅ **Do:** Override `toString` to return a useful, human-readable representation of the object, including all significant fields.

❌ **Don't:** Leave `toString` at the default `ClassName@hashcode` format for any class used in logging, debugging, or error messages.

💡 **Why it matters:** The default format `PhoneNumber@163b91` tells you nothing. A good `toString` makes production log analysis dramatically easier.

**TL;DR:** If you'd ever print/log the object, override toString — your future self debugging production issues will thank you.

---

## Item 13 — Override clone Judiciously

✅ **Do:** Prefer copy constructors (`new Stack(otherStack)`) or copy factories (`Stack.copyOf(original)`) over implementing `Cloneable`.

❌ **Don't:** Implement `Cloneable` just because you need to copy objects — it's broken by design: it creates objects without calling constructors, isn't type-safe, and defaults to shallow copy.

💡 **Why it matters:** The `Cloneable` interface is a "tag interface" with no methods. The cloning contract is specified only in `Object.clone()` Javadoc, not in the interface itself. This is a design flaw.

**TL;DR:** Copy constructors are clearer, type-safe, and don't require catching `CloneNotSupportedException`.

---

## Item 14 — Consider Implementing Comparable

✅ **Do:** Implement `Comparable<T>` for any class with a natural ordering. Use `Comparator.comparing()` chains for complex orderings.

❌ **Don't:** Use subtraction (`return a - b`) for integer comparison — it overflows for large negative values like `Integer.MIN_VALUE`.

💡 **Why it matters:** `compareTo` powers `TreeMap`, `TreeSet`, `Collections.sort()`, and binary search. Broken comparison breaks sorting and lookups silently.

**TL;DR:** Always use `Integer.compare(a, b)` or `Comparator.comparingInt()` — never subtraction.

---

## Quick Reference Table

| Method | Override Trigger | Common Bug | Correct Tool |
|--------|------------------|------------|--------------|
| `equals` | Value-based identity | Asymmetry with subtypes | Records, @AutoValue |
| `hashCode` | Always with equals | Missing override → lost in HashMap | `Objects.hash()` |
| `toString` | Always for meaningful types | Default @hex useless in logs | IDE / Lombok |
| `clone` | Rarely — use copy constructors | Shallow copy of mutable fields | Copy constructor |
| `compareTo` | Natural orderings | Subtraction overflow | `Integer.compare()` |

---

## Modern Java Note (Java 16+)

**Use `record` for value classes** — it automatically generates correct `equals()`, `hashCode()`, and `toString()`:

```java
// Instead of writing this manually:
public final class Money {
    private final BigDecimal amount;
    private final String currency;
    // equals, hashCode, toString, constructor...
}

// Use this:
public record Money(BigDecimal amount, String currency) {}
```

Records are the modern solution that eliminates most of the boilerplate and bugs from this chapter.
