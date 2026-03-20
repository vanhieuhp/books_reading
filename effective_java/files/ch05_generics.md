# Chapter 5: Generics

## Overview
Generics were added in Java 5 to provide compile-time type safety without sacrificing runtime performance. This chapter explains how to use them correctly — and why the interaction between generics and arrays, wildcards, and type erasure creates pitfalls that trip up even experienced developers.

**Core Theme:** Generics shift type errors from runtime (ClassCastException) to compile time. Use them to their full extent. Never use raw types. Master wildcards to write maximally flexible APIs.

**Why This Matters:** Incorrect use of generics leads to `ClassCastException` at runtime, unchecked cast warnings that hide real bugs, and APIs that are unnecessarily restrictive. Correct use produces self-documenting, safe code.

---

## Items

### Item 26 — Don't use raw types
- **Rule:** Never use raw types in new code — they exist only for source compatibility with pre-generics code
- **Raw type:** `List`, `Map`, `Set` (no type parameter) — loses all type safety
- **Correct:** `List<String>`, `Map<String, Integer>`, `Set<Object>`
- **Exception:** `instanceof` checks (`if (o instanceof Set)`) — type parameters are erased at runtime
- **Wildcard alternative:** Use `Set<?>` (unbounded wildcard) when you need a generic set but don't care about the type
- **`List` vs `List<Object>`:** `List<String>` is a subtype of `List` (raw), but NOT of `List<Object>` — this distinction matters

### Item 27 — Eliminate unchecked warnings
- **Rule:** Eliminate every unchecked warning if at all possible; if you can't, suppress with `@SuppressWarnings("unchecked")` at the narrowest scope and document why it's safe
- **Every unchecked warning is a potential `ClassCastException` at runtime**
- **Scope discipline:** Never `@SuppressWarnings` on a whole class or method — find the exact statement
- **Required comment:** Always add a comment above the annotation explaining why the cast is provably safe
- **Tool:** Enable `-Xlint:unchecked` in your build to see all warnings

### Item 28 — Prefer lists to arrays
- **Rule:** When you have a choice, use generic lists over arrays, especially in generic contexts
- **Arrays are COVARIANT:** `String[]` is a subtype of `Object[]` — this is unsound (ArrayStoreException at runtime)
- **Generics are INVARIANT:** `List<String>` is NOT a subtype of `List<Object>` — this is sound (compile-time error)
- **Arrays are REIFIED:** They know their element type at runtime and enforce it
- **Generics are ERASED:** Type parameters are erased at runtime — `List<String>` becomes `List` at runtime
- **Generic arrays are illegal:** `new List<String>[10]` does not compile — the two systems are fundamentally incompatible

### Item 29 — Favor generic types
- **Rule:** When writing new collection-like classes, make them generic from the start
- **Recipe:** Replace `Object[]` with `E[]` (or use `List<E>`); cast with `@SuppressWarnings` at declaration
- **Two approaches for generic arrays:**
  1. Cast array to `E[]`: `(E[]) new Object[16]` — cast at creation, suppress warning once
  2. Cast element at use: `(E) elements[index]` — suppress at each access, but `Object[]` field is explicit
- **Prefer Approach 1** for clarity; Approach 2 is necessary when the array is exposed (avoid leaking heap pollution)

### Item 30 — Favor generic methods
- **Rule:** Static utility methods in particular should be generic; it makes them safer and easier to use (no client casts needed)
- **Type inference:** Compiler infers type parameters from arguments — no need for `Collections.<String>emptyList()`
- **Generic singleton factory:** One object serves all type parameterizations (e.g. `Collections.emptyList()`)
- **Recursive type bound:** `<T extends Comparable<T>>` — used for methods that require elements to be mutually comparable

### Item 31 — Use bounded wildcards to increase API flexibility
- **Rule:** Use bounded wildcards for producer/consumer parameters to maximize API flexibility
- **PECS Mnemonic: Producer Extends, Consumer Super**
  - Producing (reading from) a collection: `<? extends T>` — you get T values out
  - Consuming (writing to) a collection: `<? super T>` — you put T values in
  - Both producing and consuming: exact type `T` — no wildcard
- **Do not use wildcards in return types** — it forces wildcards on the caller side
- **Comparables/Comparators:** Always use `Comparable<? super T>` and `Comparator<? super T>` in APIs

### Item 32 — Combine generics and varargs judiciously
- **Rule:** Understand that varargs + generics create heap pollution; only use `@SafeVarargs` when the method is genuinely safe
- **The problem:** `T... args` creates an array at the call site; generic array creation is unsound
- **When is it safe?** The method does nothing that stores something of a different type into the varargs array and doesn't expose the array to untrusted code
- **`@SafeVarargs`** annotation suppresses the warning and promises the caller the method is safe
- **Alternative:** Use `List<T>` as the parameter type instead of `T...` — `List.of(a, b, c)` at the call site

### Item 33 — Consider typesafe heterogeneous containers
- **Rule:** When you need a container that maps types to instances of those types, parameterize the key, not the container
- **Pattern:** `Map<Class<?>, Object>` with typed `put` and `get` methods using `Class.cast()`
- **Usage:** Plugin systems, annotation processors, typed registry maps
- **Limitation:** Cannot use with non-reifiable types like `List<String>.class` (due to erasure)
- **Bounded type token:** `<T extends Annotation> T getAnnotation(Class<T> annotationType)` — seen in Java's reflection API

---

## Key Concepts

| Concept | Description | Rule |
|---|---|---|
| Type Erasure | Generics are compile-time only; `List<String>` becomes `List` at runtime | Never rely on type params at runtime |
| PECS | Producer Extends, Consumer Super | Wildcard selection rule |
| Covariance (arrays) | `String[]` is `Object[]` — unsound | Avoid mixing generics + arrays |
| Invariance (generics) | `List<String>` is NOT `List<Object>` — sound | Use wildcards for flexibility |
| Heap Pollution | Mixing raw/generic types can corrupt heap | Eliminate all unchecked warnings |

---

## Relationships to Other Chapters
- Item 26 raw types connect to Item 23 (Ch 4): both about type safety
- Item 28 lists vs arrays: prefer `List<E>` when building generic types (Item 29)
- Item 32 varargs: relates to Item 53 (Ch 8) about varargs usage generally
- PECS (Item 31) is essential for understanding Java's own Collections API design

---

## Agent Prompt

When generating content for this chapter:

1. **PECS Deep Dive** — This is the hardest concept for most developers. Create a step-by-step walkthrough with a `Stack<E>` example: a `pushAll(Iterable<? extends E>)` producer and a `popAll(Collection<? super E>)` consumer. Show what compilation error you get WITHOUT the wildcard and why.

2. **Type Erasure Visualization** — Show what the compiler actually produces after type erasure for a generic method. Show the bridge method. This demystifies "why can't I do `new T()`" and "why can't I do `T.class`".

3. **Item 28 — Covariance Bug** — Demonstrate the `ArrayStoreException` that covariant arrays allow at runtime. Then show that the equivalent generics code catches it at compile time.

4. **For exercises:**
   - Exercise 1 [Intermediate]: Implement a generic `Pair<A, B>` class with a static factory method
   - Exercise 2 [Advanced]: Implement a generic `max(List<? extends T> list)` method using recursive type bound
   - Exercise 3 [Advanced]: Build a typesafe heterogeneous container `Favorites` (from the book) and extend it with a `getFavoritesOfType(Class<T>)` method
   - Exercise 4 [Intermediate]: Fix 5 unchecked warnings in a given snippet, with correct `@SuppressWarnings` placement and comments

5. **For interview questions:** Include "Explain type erasure and why generic arrays are forbidden in Java" (tests deep understanding), and "What is the difference between `List<?>` and `List<Object>`?" (common gotcha).

6. **For use cases:**
   - PECS in Spring's `CrudRepository<T, ID>` design
   - Typesafe heterogeneous container in `HttpSession.getAttribute()`
   - Generic methods in `Collections.sort()`, `Collections.max()`, and `Stream.collect()`

7. **Advice:** Give a strong opinion on when NOT to use wildcards (return types, fields). Recommend tools: IntelliJ's generic type inference hints, SpotBugs for unchecked cast detection.
