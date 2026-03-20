# Chapter 6: Enums and Annotations

## Overview
Java provides two special-purpose type families: enums (a kind of class) and annotations (a kind of interface). This chapter explains how to use both families to write safer, more expressive, and more maintainable code — and how to avoid the anti-patterns they were designed to replace.

**Core Theme:** Enums replace fragile int constants with type-safe, feature-rich objects. Annotations replace error-prone naming conventions with compiler-verified metadata. Both are grossly underused by most Java developers.

**Why This Matters:** The `int` enum pattern is still pervasive in legacy Java code and even in system APIs. Understanding why enums are strictly superior — and how to exploit their full power — separates Java developers who write solid code from those who just write working code.

---

## Items

### Item 34 — Use enums instead of int constants
- **Rule:** Never use `public static final int` constants to represent a fixed set of values; use enums
- **Int enum problems:** No type safety (can pass any int), no namespace, no printable name, brittle (ordinals shift on reorder)
- **Enum superpowers:** Are full classes — they can have fields, constructors, methods, and implement interfaces
- **Constant-specific behavior:** Each enum constant can override a method — use an abstract method body per constant (strategy enum pattern)
- **Planet example:** `MERCURY(3.302e+23, 2.439e6)` — stores mass and radius, computes `surfaceGravity()` and `surfaceWeight()`
- **When to use abstract method per constant vs switch:** Prefer abstract method (compiler enforces all constants handle it); use switch only for external enums you don't control

### Item 35 — Use instance fields instead of ordinals
- **Rule:** Never derive a value associated with an enum from its ordinal (`ordinal()`)
- **Ordinal fragility:** The ordinal is the position in the declaration — reordering constants breaks ordinal-based logic silently
- **Correct approach:** Add an instance field in the constructor; use `ordinal()` only for data structures like `EnumSet` and `EnumMap` (their internal use only)
- **Example:** `SOLO(1), DUET(2), TRIO(3)` — the int is an instance field, not the ordinal

### Item 36 — Use EnumSet instead of bit fields
- **Rule:** When you need a set of enum values, use `EnumSet` instead of `int` bit fields
- **Bit field anti-pattern:** `public static final int STYLE_BOLD = 1 << 0` — hard to read, no type safety, printing is meaningless
- **EnumSet advantages:** Type-safe, readable, fast (uses bit vector internally), integrates with Java collections API
- **Usage:** `EnumSet.of(Style.BOLD, Style.ITALIC)` — looks like bit flags, IS a Set
- **Performance:** `EnumSet` operations are `O(1)` using long bit manipulation for enums with ≤64 constants

### Item 37 — Use EnumMap instead of ordinal indexing
- **Rule:** Never use `array[enum.ordinal()]` to map enum values to data; use `EnumMap`
- **Ordinal indexing bug:** Fragile to reordering; no bounds checking; loses type safety
- **EnumMap advantages:** Type-safe, fast (array-based internally), correctly prints its contents
- **Nested EnumMap:** `EnumMap<Phase, EnumMap<Phase, Transition>>` for two-dimensional enum lookups
- **Stream integration:** `stream.collect(groupingBy(plant -> plant.lifeCycle, () -> new EnumMap<>(...), toSet()))`

### Item 38 — Emulate extensible enums with interfaces
- **Rule:** Since enums cannot be extended, define an interface that enum types implement to simulate extensibility
- **Use case:** Extensible operation sets — basic ops (`PLUS`, `MINUS`) plus user-defined extensions
- **Pattern:** `interface Operation { double apply(double x, double y); }` — both `BasicOperation` and `ExtendedOperation` implement it
- **Client code:** Works with `Operation` interface — accepts any implementing enum type
- **Limitation:** Cannot inherit implementation from base enum type; must duplicate any shared methods

### Item 39 — Prefer annotations to naming patterns
- **Rule:** Always use marker or meta annotations over naming conventions for tools and frameworks
- **Naming pattern problems:** No type checking (misname `tetsFoo` and JUnit silently ignores it), no parameter passing, no restriction to specific elements
- **Annotation advantages:** Compiler verifies names, can carry parameters (`@Test(expected=IOException.class)`), can be restricted to method/class/field with `@Target`
- **Rolling your own:** Define annotation with `@interface`, use `@Retention` (runtime vs compile vs class) and `@Target`

### Item 40 — Consistently use the Override annotation
- **Rule:** Use `@Override` on every method intended to override a supertype method, without exception
- **Classic bug:** Overloading instead of overriding: `public boolean equals(MyType o)` — signature mismatch, never called
- **`@Override` catches it:** Compile error immediately if the method doesn't actually override anything
- **Interface methods:** In Java 8+, use `@Override` on methods that implement interface methods too — catches signature drift
- **IDE enforcement:** Configure IDE to warn/error on missing `@Override`

### Item 41 — Use marker interfaces to define types
- **Rule:** If you want to define a type (so clients can write methods that take that type), use a marker interface, not a marker annotation
- **Marker interface advantages:** Compile-time type checking; can be targeted to specific types via extends
- **Marker annotation advantages:** Part of the larger annotation framework; can be applied to non-class elements
- **Decision rule:** If the marker applies to anything other than a class/interface, or if you might add elements to it later → annotation. If you need it to act as a type → interface
- **Serializable** is the canonical marker interface

---

## Key Concepts

| Feature | Enum | Annotation |
|---|---|---|
| Replaces | int constants, bit fields | Naming patterns |
| Type safety | Full | Full |
| Can have methods/fields | Yes | Only elements |
| Extensible | Via interfaces | Via meta-annotations |
| Runtime access | Always | Depends on @Retention |

---

## Relationships to Other Chapters
- Item 23 (Ch 4): Class hierarchies replace tagged classes; enums (Item 34) are the clean solution for fixed sets
- Item 6 (Ch 2): `EnumSet`/`EnumMap` should replace int-based set logic
- Item 39 connects to Java's annotation processing framework and Spring's annotation-driven configuration

---

## Agent Prompt

When generating content for this chapter:

1. **Item 34 — Strategy Enum Pattern** — Implement the full `Operation` enum with constant-specific method bodies. Then extend it to a `Planet` enum with fields and methods. Show how the abstract method on the enum enforces that all constants provide an implementation.

2. **Item 36 — EnumSet vs Bit Fields** — Show a side-by-side comparison: the old `int` bit field approach (full of `<<` operators) vs the clean `EnumSet` approach. Show that `EnumSet` serializes to a readable string while bit fields print a meaningless integer.

3. **Item 40 — The @Override Bug** — Create the classic `equals` override bug (wrong parameter type), show it compiling and running silently, then add `@Override` and show the compile error.

4. **For exercises:**
   - Exercise 1 [Intermediate]: Extend the `Planet` enum to compute the time for an object to fall to the surface from a given height
   - Exercise 2 [Intermediate]: Refactor a `switch` on an int constant (payment types: CASH=0, CREDIT=1, CRYPTO=2) into a proper enum with per-constant behavior
   - Exercise 3 [Advanced]: Implement `@NonNull` annotation (with `@Target(PARAMETER)` and `@Retention(RUNTIME)`) and a validator that checks it via reflection
   - Exercise 4 [Beginner]: Replace an `int[][]` ordinal-indexed transition table with a nested `EnumMap`

5. **For use cases:**
   - Enums in Spring: `@RequestMapping` HTTP methods are enums; Spring's `@ConditionalOnProperty` is annotation-driven
   - `EnumSet` for permission systems (RBAC: `EnumSet<Permission>` per role)
   - `@Override` equivalents: `@Overrides` in Kotlin, override keyword enforcement

6. **For interview questions:** "Can an enum implement an interface in Java?" (many don't know the answer is yes). "What is the strategy enum pattern and when would you use it over a regular switch?"

7. **Advice:** Strongly recommend replacing all existing `int` constant patterns in legacy code during any refactoring pass. Include a checklist: "If you see `public static final int`, ask: should this be an enum?"
