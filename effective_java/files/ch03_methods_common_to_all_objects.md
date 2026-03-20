# Chapter 3: Methods Common to All Objects

## Overview
Every Java class inherits from `Object`. This chapter covers the five non-final methods that have explicit general contracts: `equals`, `hashCode`, `toString`, `clone`, and `Comparable.compareTo`. Violating these contracts produces bugs that are subtle, hard to reproduce, and often dangerous.

**Core Theme:** The contracts for these methods exist because many critical Java APIs (collections, sorting, hashing) depend on them. Break the contract → break the ecosystem.

**Why This Matters:** A broken `equals` or `hashCode` can make objects invisible in a `HashMap`. A bad `compareTo` can corrupt a `TreeSet`. These bugs rarely throw exceptions — they just silently produce wrong answers.

---

## Items

### Item 10 — Obey the general contract when overriding equals
- **Rule:** Only override `equals` when logical equality differs from object identity and the class doesn't have a parent that already provides it
- **The 5 properties (must ALL hold):**
  - *Reflexive:* `x.equals(x)` → true
  - *Symmetric:* `x.equals(y)` → `y.equals(x)`
  - *Transitive:* `x.equals(y)` and `y.equals(z)` → `x.equals(z)`
  - *Consistent:* repeated calls return same result
  - *Non-null:* `x.equals(null)` → false
- **Most violated:** Symmetry — especially when mixing types (e.g. `String` vs `MyString`)
- **Transitivity trap:** Cannot be fixed when adding value component to a subclass while preserving `equals`; prefer composition
- **Automatic tools:** Use `@AutoValue`, `record`, or IDE generation; then verify with hand-check

### Item 11 — Always override hashCode when you override equals
- **Rule:** Equal objects must return equal hash codes. This is a hard requirement for hash-based collections.
- **Classic bug:** Override `equals` but not `hashCode` → `HashSet.contains()` returns false for a logically equal object
- **Good hash formula:** Use `Objects.hash(field1, field2, ...)` or follow the 31× multiplier recipe
- **Performance note:** Cache hash code in immutable objects if it's expensive to compute
- **Null safety:** `Objects.hash` handles nulls; manual computation must guard against NPE

### Item 12 — Always override toString
- **Rule:** Override `toString` to return a useful, human-readable representation of the object
- **Default is useless:** `PhoneNumber@163b91` tells you nothing
- **Format specification:** If you specify the format in Javadoc, provide a matching static factory; if not, warn callers not to depend on it
- **What to include:** All significant fields, or a summary for large objects
- **Logging benefit:** A good `toString` makes production log analysis dramatically easier

### Item 13 — Override clone judiciously
- **Rule:** Avoid implementing `Cloneable` entirely; prefer copy constructors or copy factories
- **Why `Cloneable` is broken:** The contract is specified only in `Object.clone()` Javadoc, not in the interface; it creates objects without calling a constructor; it's not type-safe
- **The deep copy problem:** `clone()` does a shallow copy by default; mutable fields must be manually deep-copied
- **Exception handling:** `clone()` declares `CloneNotSupportedException` but you must suppress it in your override
- **Safe alternative:** `public Stack(Stack<E> s)` — copy constructor; or `public static Stack<E> newInstance(Stack<E> s)` — copy factory

### Item 14 — Consider implementing Comparable
- **Rule:** Implement `Comparable<T>` for any class with a natural ordering; use `Comparator.comparing()` chains for complex orderings
- **compareTo contract:** Same reflexive/symmetric/transitive rules as equals; strongly recommended that `(x.compareTo(y) == 0) == x.equals(y)`
- **Subtraction anti-pattern:** Never use `return a - b` for integer comparison — overflows for large negative values
- **Correct approach:** `Integer.compare(a, b)` or `Comparator.comparingInt()`
- **Comparator chains:** `Comparator.comparing(PhoneNumber::areaCode).thenComparingInt(PhoneNumber::prefix)`

---

## Key Concepts

| Method | Override Trigger | Common Bug | Correct Tool |
|---|---|---|---|
| `equals` | Value-based identity | Asymmetry with subtypes | Records, @AutoValue |
| `hashCode` | Always with equals | Missing override → lost in HashMap | `Objects.hash()` |
| `toString` | Always for meaningful types | Default @hex useless in logs | IDE / Lombok |
| `clone` | Rarely — use copy constructors | Shallow copy of mutable fields | Copy constructor |
| `compareTo` | Natural orderings | Subtraction overflow | `Integer.compare()` |

---

## Relationships to Other Chapters
- Item 17 (Ch 4): Immutable classes make `equals`/`hashCode` simpler and safer
- Item 34 (Ch 6): Enums implement `Comparable` automatically
- Item 65 (Ch 9): Reflection-based equality frameworks relate to `equals` contract
- Item 10 fundamentally underpins Java's Collections framework behavior

---

## Agent Prompt

When generating content for this chapter, focus on:

1. **Item 10 Symmetry Bug Demo** — Write a concrete example of a broken symmetric `equals` between `CaseInsensitiveString` and `String`. Show exactly what fails in a `List.contains()` call and why.

2. **Item 11 HashMap Demo** — Create a step-by-step visualization of what happens when you put an object in a `HashMap` then look it up after overriding `equals` but NOT `hashCode`. Show the bucket math.

3. **Item 14 Subtraction Trap** — Demonstrate with `Integer.MIN_VALUE` exactly how `return a - b` causes overflow. Show the correct `Integer.compare(a, b)` replacement.

4. **For exercises:**
   - Exercise 1: Given a broken `equals` implementation, identify which of the 5 properties is violated
   - Exercise 2: Implement a correct `hashCode` for a 3-field class manually (without `Objects.hash`)
   - Exercise 3: Refactor a `Cloneable` class to use a copy constructor instead
   - Exercise 4: Write a multi-level `Comparator` chain for a `Person` class (by last name, then first name, then age)

5. **For interview questions:** Include the famous "What happens if two keys have the same hashCode in a HashMap?" question (tests understanding of chaining vs. open addressing in Java's implementation).

6. **For use cases:** Map `Comparable` and `Comparator` to real sorting in JPA queries, Spring Data `Sort` objects, and `TreeMap` usage in a cache implementation.

7. **For advice:** Give strong guidance on using Java `record` (Java 16+) as the modern solution that auto-generates correct `equals`/`hashCode`/`toString` for value classes.
