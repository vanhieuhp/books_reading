# Chapter 5: Generics — Guidelines

> **Core Theme:** Generics enable you to write type-safe code that catches errors at compile time rather than runtime. This chapter covers Items 26–33: the rules for using generics correctly, avoiding raw types, understanding wildcards, and creating flexible, reusable APIs.

---

## Overview

Generics are one of Java's most powerful type system features. In Spring Boot microservices, you'll see generics everywhere: `List<T>`, `Map<K,V>`, `Repository<T, ID>`, `ResponseEntity<T>`, and countless other places.

**Why it matters:** Without generics, you'd rely on casts that fail at runtime. With generics, the compiler catches type mismatches before your code ever runs in production.

---

## Item 26 — Don't Use Raw Types

✅ **Do:** Always specify type parameters when using generic types (e.g., `List<String>`, `Map<Long, User>`)

❌ **Don't:** Use raw types like `List` without the type parameter

💡 **Why it matters:** Raw types bypass generic type checking, leading to `ClassCastException` at runtime — exactly the kind of bug that slips into production.

**TL;DR:** Raw types are a backward compatibility escape hatch; never use them in new code.

---

## Item 27 — Eliminate Unchecked Warnings

✅ **Do:** Fix every unchecked warning by adding type casts or redesigning your code

❌ **Don't:** Suppress warnings with `@SuppressWarnings("unchecked")` without understanding why

💡 **Why it matters:** Unchecked warnings are the compiler telling you it can't guarantee type safety. Ignoring them is like ignoring a fire alarm.

**TL;DR:** Every unchecked warning is a potential `ClassCastException` waiting to happen.

---

## Item 28 — Prefer Lists to Arrays

✅ **Do:** Use `List<E>` instead of `E[]` for type-safe generic collections

❌ **Don't:** Create generic arrays like `new List<E>[]`, `new E[]`, or `new List<String>[]`

💡 **Why it matters:** Arrays are **covariant** (a `String[]` is an `Object[]`), but generics are **invariant** (`List<String>` is NOT a `List<Object>`). This mismatch causes runtime crashes.

**TL;DR:** Arrays and generics don't mix well. Use `List<E>` everywhere.

---

## Item 29 — Favor Generic Types

✅ **Do:** Genericize your classes and interfaces to make them reusable across types

❌ **Don't:** Duplicate code for each type by using `Object` as a stand-in

💡 **Why it matters:** Generic types eliminate casting and enable compile-time type checking. A `Stack<E>` that works for any `E` is safer and more useful than a `Stack<Object>`.

**TL;DR:** Every class that holds or manages objects should be generic.

---

## Item 30 — Favor Generic Methods

✅ **Do:** Make utility methods generic when they operate on typed parameters

❌ **Don't:** Use `Object` parameters and cast inside generic methods

💡 **Why it matters:** Generic methods provide type safety without sacrificing flexibility. The `Collections.sort()` method works on any `List<T extends Comparable<? super T>>` — that's the power of generic methods.

**TL;DR:** Static utility methods are prime candidates for generics.

---

## Item 31 — Use Bounded Wildcards to Increase API Flexibility

✅ **Do:** Use `? extends T` for producer inputs and `? super T` for consumer inputs (PECS)

❌ **Don't:** Use exact types in method parameters when the method only reads from or writes to the collection

💡 **Why it matters:** Without wildcards, `List<Number>` can't accept `List<Integer>`. With `? extends Number`, it can. This is essential for flexible APIs.

**TL;DR:** PECS: Producer Extends, Consumer Super.

---

## Item 32 — Combine Generics and Varargs Judiciously

✅ **Do:** Be careful when mixing varargs with generic types — they can create unsafe arrays

❌ **Don't:** Add `@SafeVarargs` blindly; only use it when you're confident the method is type-safe

💡 **Why it matters:** Varargs create an array internally. Generic arrays are unsafe. This combination is the "danger zone" of generics.

**TL;DR:** Varargs + generics = potential heap pollution. Use with caution.

---

## Item 33 — Consider Typesafe Heterogeneous Containers

✅ **Do:** Use `Class<T>` as a type token to create type-safe containers that hold different types

❌ **Don't:** Use `Map<Class<?>, Object>` without proper type safety checks

💡 **Why it matters:** Standard containers are homogeneous (all elements are `E`). Sometimes you need heterogeneous (mixed types) but type-safe storage — use `Class<T>` keys.

**TL;DR:** Use `Class<T>` objects as type tokens for flexible, type-safe heterogeneous containers.

---

## Quick Reference Table

| Item | Rule | Common Violation | TL;DR |
|------|------|------------------|-------|
| 26 | No raw types | Using `List` instead of `List<T>` | Always use `<T>` |
| 27 | Fix warnings | Blindly suppressing unchecked | Every warning = bug |
| 28 | Lists > Arrays | Using `E[]` instead of `List<E>` | Arrays don't mix with generics |
| 29 | Generic types | Duplicating code for each type | `<T>` enables reuse |
| 30 | Generic methods | Using Object + casting | `<T>` for static utils |
| 31 | Bounded wildcards | Using exact types | PECS: extends/super |
| 32 | Varargs + generics | Abusing @SafeVarargs | Heap pollution risk |
| 33 | Heterogeneous containers | Raw casts to `T` | Use `Class<T>.cast()` |

---

## Modern Java Note (Java 16+)

**Records eliminate much generic boilerplate** for DTOs:
```java
// Instead of complex generic DTOs:
public class GenericResponse<T, E> {
    private T data;
    private E error;
    // constructor, getters, equals, hashCode, toString...
}

// Use records for simpler cases:
public record ApiResponse<T>(T data, String status) {}
```

Records automatically generate proper `equals()`, `hashCode()`, and `toString()`, reducing the need for manual generic type handling in many scenarios.
