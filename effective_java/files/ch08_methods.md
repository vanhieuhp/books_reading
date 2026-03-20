# Chapter 8: Methods

## Overview
This chapter is about designing methods that are correct, robust, usable, and well-documented. It covers the full lifecycle of a method call: validating inputs, protecting internal state, choosing signature conventions, handling return values, and communicating through documentation.

**Core Theme:** A method's contract is a promise to callers. Validate inputs eagerly, protect state defensively, return sensible values (never null from collection methods), and document everything that callers need to know.

**Why This Matters:** Bad method design creates APIs that are easy to misuse and hard to use correctly. The best APIs make correct use easy and incorrect use hard or impossible at compile time.

---

## Items

### Item 49 — Check parameters for validity
- **Rule:** Validate all parameters at the start of each method and constructor; fail fast with a clear exception
- **For public methods:** Document constraints with `@throws` in Javadoc; throw `IllegalArgumentException`, `IndexOutOfBoundsException`, or `NullPointerException`
- **For private methods:** Use `assert` statements — they document the precondition for maintainers and can be enabled at test time
- **`Objects.requireNonNull()`:** Standard way to null-check parameters; returns the value (can be used inline)
- **Java 9 additions:** `Objects.checkIndex()`, `Objects.checkFromIndexSize()` for range checking
- **Exceptions:** Some methods (sort) must validate in the course of doing their work; explicitly expensive operations may defer validation if cost is prohibitive

### Item 50 — Make defensive copies when needed
- **Rule:** If a class has mutable components that come from or go to external code, make defensive copies
- **Attack pattern:** `Date` is mutable — a constructor that stores a `Date` reference can be mutated by the caller after construction, violating invariants
- **Two copy points:**
  1. Constructor: copy before storing (`new Date(date.getTime())`)
  2. Accessor: copy before returning (`return new Date(start.getTime())`)
- **Copy before validation:** Make the defensive copy, THEN validate the copy — prevents TOCTOU (time-of-check/time-of-use) race condition
- **Modern alternative:** Use `Instant` (immutable) instead of `Date` — eliminates the problem entirely
- **Cost consideration:** Defensive copying has a performance cost; internal packages may forgo it with documented trust

### Item 51 — Design method signatures carefully
- **Rule:** Method names, parameter types, and parameter counts must be chosen for clarity, consistency, and usability
- **Name carefully:** Follow Java naming conventions; be consistent within a package; be expressive
- **Don't overload excessively:** Provide convenience variants but don't create 7 overloads of the same operation
- **Parameter list length:** Aim for ≤4 parameters; use builder, helper class, or varargs to reduce
- **Prefer interface to class for parameter types:** Accept `Map` not `HashMap`; accept `List` not `ArrayList`
- **Prefer 2-element enum to boolean:** `Thermometer.newInstance(TemperatureScale.CELSIUS)` over `newInstance(true)` — readable at call site

### Item 52 — Use overloading judiciously
- **Rule:** Never write overloads where the same arguments could be passed to different overloads with different behavior
- **The key trap:** Overload selection is made at COMPILE TIME based on the declared type, not the runtime type
- **The `classify` disaster:** A method overloaded for `Set`, `List`, and `Collection` — called in a loop with a `Collection` variable always hits the `Collection` overload, even if the actual object is a `Set`
- **Safe overloading:** Overloads are safe when they have different numbers of params, or when they do the same thing (one delegates to the other)
- **`write(int)` vs `write(char)` in `PrintStream`:** This is a famous mistake in the JDK — you cannot fix it without breaking backward compatibility
- **Generics + autoboxing gotcha:** `List.remove(int index)` vs `List.remove(Object o)` — autoboxing makes these confusing

### Item 53 — Use varargs judiciously
- **Rule:** Varargs are excellent for methods that need a variable number of arguments; use carefully for performance-sensitive code
- **Minimum parameter enforcement:** If you need at least one argument, declare `(T first, T... rest)` — not `(T... args)` with a runtime check (moves error to runtime, not compile time)
- **Performance trap:** Varargs creates an array on every call; for frequently called methods, consider overloads for 0, 1, 2, 3 args with a fallback varargs
- **Real example:** `EnumSet.of()` provides overloads up to 5 elements for this exact reason

### Item 54 — Return empty collections or arrays, not nulls
- **Rule:** Never return `null` from a method that returns a collection, array, or string; return an empty one instead
- **Why null return is harmful:** Forces every caller to null-check; missed null check = `NullPointerException` in production
- **Performance myth:** Returning `null` to avoid creating an empty collection is premature optimization; empty collections can be cached
- **Correct patterns:**
  - Collections: `return Collections.emptyList()` / `return List.of()` (cached, immutable)
  - Arrays: `return new T[0]` once cached statically; or return zero-length array literal
- **`Optional` is not a substitute here** — `Optional` is for when "no result" is meaningful, not for collections

### Item 55 — Return optionals judiciously
- **Rule:** Return `Optional<T>` from a method when it is possible that no result exists and the caller must deal with that case; never return `Optional` from collection/array return types or from methods with performance constraints
- **`Optional` purpose:** Makes the absence of a result part of the API contract — forces callers to handle both cases
- **Getting the value:**
  - `opt.get()` — throws `NoSuchElementException` if empty (use sparingly)
  - `opt.orElse(default)` — return default if empty
  - `opt.orElseGet(Supplier)` — lazy default (use when default is expensive)
  - `opt.orElseThrow(Supplier)` — throw custom exception if empty
  - `opt.ifPresent(Consumer)` — action only if present
- **Never:** Use `Optional` as a field type, method parameter type, or map value
- **Container types (List, Stream, array) should return empty not Optional**

### Item 56 — Write doc comments for all exposed API elements
- **Rule:** Document every public class, interface, method, constructor, and field with a Javadoc comment
- **Method contract must document:**
  - Preconditions (`@param`, `@throws` for precondition violations)
  - Postconditions (`@return`)
  - Side effects (thread-safety, state changes)
  - `@throws` for all checked AND unchecked exceptions the method can throw
- **`{@code}` vs `<code>`:** Use `{@code}` for code in docs — it escapes HTML and enables syntax highlighting
- **`@implSpec`:** Documents the self-use of the method for subclass implementors (Java 8+)
- **Summary fragment:** First sentence is the summary; must be a fragment, not a sentence; should be distinct per method
- **Thread-safety:** Must be documented in the class-level Javadoc

---

## Key Concepts

| Practice | When | Why |
|---|---|---|
| Fail-fast validation | Start of every method | Find bugs at the source |
| Defensive copies | Mutable in/out params | Preserve invariants |
| Enum over boolean | 2-option parameters | Readable call sites |
| Empty over null | Collection/array returns | Eliminate null checks |
| Optional return | Single value may not exist | Forces caller to handle absence |
| Document everything | All public API | API usability and maintainability |

---

## Relationships to Other Chapters
- Item 6 (Ch 2): Defensive copies (Item 50) are sometimes necessary even though Item 6 says avoid unnecessary objects
- Item 17 (Ch 4): Immutable objects (Item 17) eliminate the need for defensive copies (Item 50)
- Item 69 (Ch 10): Parameter validation (Item 49) and exception type choice (Item 70)
- Item 10 (Ch 3): `equals` must handle null (non-null contract) — connects to Item 49

---

## Agent Prompt

When generating content for this chapter:

1. **Item 50 — TOCTOU Race Condition** — Demonstrate the "copy before validate" rule with a concrete multithreaded example. Show the vulnerability: validate first, then another thread mutates the object, then you store the now-invalid copy.

2. **Item 51 — Builder vs Parameter Object vs Varargs** — Generate a decision guide with concrete examples: "Given a method with N parameters, should I use overloads, a helper class, a builder, or varargs?"

3. **Item 52 — Compile-Time Overload Selection** — This is the most counterintuitive item in the chapter. Create a complete runnable example that demonstrates the `Collection.classify()` problem step-by-step. Show the debug output. Then show the fix (rename the methods).

4. **Item 55 — Optional Anti-Patterns Gallery** — List 5 common `Optional` abuses with code examples and explanations: using it as a field, as a parameter, calling `get()` without `isPresent()`, returning `Optional<List<T>>`, using `Optional` in a performance-critical inner loop.

5. **For exercises:**
   - Exercise 1 [Beginner]: Add correct parameter validation to 3 buggy methods (each missing a different check)
   - Exercise 2 [Intermediate]: Fix a `Period` class whose constructor stores `Date` references (immutability violation) using defensive copies
   - Exercise 3 [Intermediate]: Refactor a method returning `null` on failure to use `Optional` correctly, then rewrite its callers
   - Exercise 4 [Advanced]: Write complete Javadoc for a `BinarySearch` class with `@param`, `@return`, `@throws`, `@implSpec`

6. **For use cases:**
   - Item 54 in Spring Data: `findById()` returns `Optional<T>` — the model answer for repository design
   - Item 49 in REST controllers: Spring's `@Valid` annotation as a framework-level parameter validator
   - Item 52: The `java.util.Date` constructors with similar names are a real-world overloading mess

7. **For interview questions:** "When would you use `Optional.orElse()` vs `Optional.orElseGet()`?" (tests understanding of lazy evaluation). "What's the problem with overloading and autoboxing in the Collections API?" (tests Item 52 knowledge).
