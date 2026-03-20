# Chapter 4: Classes and Interfaces

## Items 15–25

---

## 🧠 Module 3: Explain Why

This module builds deep understanding of the JVM and language mechanics behind each rule. Understanding the "why" helps you make better design decisions in novel situations.

---

## Item 15 — Minimize Accessibility

### The JVM Access Control System

Java provides four levels of access control, enforced at compile time and runtime:

| Modifier | Class | Package | Subclass | World |
|----------|-------|---------|----------|-------|
| `private` | ✅ | ❌ | ❌ | ❌ |
| package-private | ✅ | ✅ | ❌ | ❌ |
| `protected` | ✅ | ✅ | ✅ | ❌ |
| `public` | ✅ | ✅ | ✅ | ✅ |

**The key insight:** Access modifiers are not just suggestions — they're part of the Java type system. The compiler enforces them, and they form an implicit API contract.

### What Happens When You Expose Internals?

When you make a field `public`, you're committing to:
1. **Never changing its type** — existing clients depend on it
2. **Never adding validation** — you can't add checks without breaking clients
3. **Supporting all values** — you can't constrain the range without breaking clients

**The one-way door problem:** Once you publish a public field, you can't change your mind. Every piece of code that uses it is now coupled to your internal representation.

---

## Item 16 — Public Classes Should Use Accessors

### Why Getters and Setters Matter

JavaBean conventions (`getXxx()`/`setXxx()`) exist for a reason — they create a layer of indirection between internal state and external access.

**When public fields seem fine:**

- Truly immutable data (but use `final` fields instead!)
- Nested classes with no external exposure
- Private nested classes (but make them `private static`!)

**When accessors become necessary:**

- Any field that might need validation later
- Any field in a class that might become abstract
- Any field used by frameworks (Jackson, Hibernate, etc.)

### The Spring Boot Impact

In Spring Boot, you'll almost always need accessors because:
- Jackson needs getters to serialize
- Jackson needs setters (or `@JsonCreator`) to deserialize
- JPA/Hibernate needs setters to populate entities
- Testing frameworks need access to state

---

## Item 17 — Minimize Mutability

### Why Immutability Matters

**Immutable objects are inherently thread-safe.** This is the most important point in all of Effective Java.

When an object's state cannot change after construction:
- **No synchronization needed** — multiple threads can read without locks
- **No defensive copies needed** — you can share the reference freely
- **No.clone() needed** — you can always use the original
- **No aliasing problems** — no fear that someone else modified "your" object

### How the JVM Handles Immutability

The JVM provides no automatic enforcement of immutability. You must implement it manually:

1. **Don't provide setters** — once constructed, state never changes
2. **Make the class `final`** — prevents subclassing that could add mutable state
3. **Make all fields `private final`** — prevents external access and reassignment
4. **Defensive copies for mutable components** — if you hold a `List`, return `Collections.unmodifiableList()`

### The String Metaphor

String is the canonical immutable class in Java. When you do:

```java
String s = "hello";
s = s + " world";  // Creates NEW string, doesn't modify original
```

The original "hello" string is never modified. This is why:
- String concatenation in loops is slow (creates many objects)
- StringBuilder exists for mutable strings
- `String.intern()` can reuse string literals

**The same principle applies to your value objects.** When you "add" to a `Money` object, you're creating a new `Money`, not modifying the original.

### What Goes Wrong Without Immutability

Consider this common bug:

```java
Map<String, BigDecimal> prices = new HashMap<>();
prices.put("apple", BigDecimal.valueOf(1.00));

BigDecimal applePrice = prices.get("apple");
applePrice = applePrice.add(BigDecimal.valueOf(0.50));

// OOPS! Original map still has 1.00!
// Because BigDecimal is immutable, add() returns NEW object
System.out.println(prices.get("apple"));  // Still 1.00!
```

Immutable objects in mutable collections are actually safe — it's mutable objects in collections that cause problems.

---

## Item 18 — Favor Composition Over Inheritance

### The Encapsulation Problem

Inheritance creates **tight coupling** between parent and child. The child has access to all `protected` fields and methods, and depends on the internal implementation of the parent.

**The fragile base class problem:** If the parent class changes (even to fix a bug), the child can silently break.

### Real-World Example

```java
// JDK's HashSet has addAll() implemented as:
// public boolean addAll(Collection<? extends E> c) {
//     boolean modified = false;
//     for (E e : c)
//         if (add(e))
//             modified = true;
//     return modified;
// }

// If HashSet changed to:
// public boolean addAll(Collection<? extends E> c) {
//     return addAll(c);  // Recursive! Would stack overflow
// }

// Your InstrumentedHashSet that overrides both add() and addAll()
// would break because addAll() now calls add() twice!
```

### Why Composition Works

With composition, you only depend on the **public interface** of the delegate:

```java
class InstrumentedSet<E> implements Set<E> {
    private final Set<E> delegate;  // Only depends on Set interface

    @Override
    public boolean add(E e) {
        count++;
        return delegate.add(e);  // Calls public method only
    }
}
```

If `HashSet` changes its internal implementation, you're safe — you only call public methods.

### When Inheritance Is Appropriate

Inheritance is correct when there's a true **is-a** relationship:
- `ArrayList` **is a** `List` — inherits implementation
- `HashMap` **is a** `Map` — inherits implementation
- `RuntimeException` **is a** `Exception` — inherits type

Not appropriate:
- `InstrumentedHashSet` **is not a** `HashSet` — it adds behavior
- `ValidatingAccount` **is not a** `Account` — it adds validation

---

## Item 19 — Design for Inheritance or Prohibit It

### The Self-Use Problem

When you design a class for inheritance, you must document which methods call which other methods:

```java
public abstract class IntSequence {
    /** Returns true if has more elements. */
    public abstract boolean hasNext();

    /** Returns next element. Subclasses: don't override! */
    public int next() {
        if (!hasNext()) {
            throw new NoSuchElementException();
        }
        return doNext();  // Template method pattern
    }

    /** Override to provide element. */
    protected abstract int doNext();
}
```

If a subclass overrides `hasNext()`, the behavior of `next()` changes — but only if you know about this dependency!

### The Solution

1. **Make the class `final`** if you don't intend for it to be subclassed
2. **Document self-use patterns** if you allow subclassing
3. **Use `@throws` in Javadoc** for overridable methods
4. **Consider factory methods** instead of constructors for subclasses

---

## Item 20 — Prefer Interfaces to Abstract Classes

### Why Interfaces Are More Flexible

In Java, a class can only have **one direct superclass**, but can implement **many interfaces**:

```java
// Can extend one class, implement many interfaces
class MyClass extends BaseClass implements InterfaceA, InterfaceB, InterfaceC {
}
```

**Abstract classes force single inheritance** — you can't inherit from two abstract classes.

### Default Methods Changed Everything

Before Java 8, interfaces could only declare methods — implementations lived in abstract classes. With default methods:

```java
interface PaymentProcessor {
    PaymentResult process(Payment payment);

    // Now you can provide default implementations!
    default void logTransaction(Payment payment) {
        System.out.println("Processing: " + payment.getId());
    }

    default boolean supportsType(PaymentType type) {
        return true;  // Default implementation
    }
}
```

**This is essentially multiple inheritance** — you can inherit default implementations from multiple interfaces!

### When Abstract Classes Are Still Needed

Abstract classes are appropriate when:
- You need shared **instance fields** (not constants)
- You need **protected constructors** for construction logic
- You're creating a **legacy hierarchy** that can't be changed

---

## Item 21 — Use Interfaces Only to Define Types

### The Interface Segregation Principle

An interface should define **one contract** — one "can-do" relationship. If you put constants in an interface, you're violating the Single Responsibility Principle.

**The constant interface anti-pattern:**

```java
interface Constants {
    String API_KEY = "secret";  // Pollutes implementing classes!
}

class MyService implements Constants {
    void doSomething() {
        String key = API_KEY;  // Confusing - where did this come from?
    }
}
```

### Proper Separation

- **Constants** → Utility classes (`Math.PI`, `Integer.MAX_VALUE`)
- **Types** → Interfaces that define behavior
- **Shared code** → Default methods in interfaces

---

## Item 22 — Favor Static Member Classes Over Nonstatic

### Memory Implications

A **nonstatic inner class** holds an implicit reference to its enclosing instance:

```java
class Outer {
    class Inner { }  // Holds reference to Outer instance
}

Outer outer = new Outer();
Outer.Inner inner = outer.new Inner();
// 'inner' keeps 'outer' alive in memory!
```

This can cause **memory leaks** if the inner class escapes via:
- Being stored in a static collection
- Being returned from a method
- Being passed to another thread

### When to Use Nonstatic

Use nonstatic (inner) classes only when:
- You need access to the enclosing instance's fields
- You're implementing a callback or listener that needs context
- You're using the **local class** pattern in a method

---

## Item 23 — Prefer Class Hierarchies to Tagged Classes

### The Problem with Tagged Classes

```java
class Figure {
    enum Shape { CIRCLE, RECTANGLE }

    Shape shape;  // Tag field

    // For circles:
    double radius;

    // For rectangles:
    double length;
    double width;

    double area() {
        switch (shape) {
            case CIRCLE:
                return Math.PI * radius * radius;
            case RECTANGLE:
                return length * width;
            default:
                throw new AssertionError(shape);
        }
    }
}
```

**Problems:**
- Verbose — fields for all variants in one class
- Error-prone — must handle all tags in every method
- Fragile — adding a new variant requires changing every method
- No compile-time type safety — you can set radius on a RECTANGLE

### The Hierarchy Solution

```java
sealed interface Figure permits Circle, Rectangle {
    double area();
}

final class Circle implements Figure {
    private final double radius;
    public double area() { return Math.PI * radius * radius; }
}

final class Rectangle implements Figure {
    private final double length;
    private final double width;
    public double area() { return length * width; }
}
```

Now the compiler enforces:
- All variants are known (sealed)
- Each class has only its relevant fields
- Pattern matching works cleanly

---

## Item 24 — Use Static Factory Methods Instead of Constructors

### Named Constructors

Constructors have no intrinsic meaning — they just build objects. Factory methods can **communicate intent**:

```java
// What does this mean?
new Payment(BigDecimal.TEN, Currency.getInstance("USD"))

// Much clearer!
Payment.of(BigDecimal.TEN, Currency.getInstance("USD"))
Payment.zero(Currency.getInstance("USD"))
Payment.from(order)
```

### Factory Method Advantages

1. **Named constructors** — convey meaning
2. **Can return subtypes** — return the optimal implementation
3. **Can cache instances** — singleton, flyweight patterns
4. **Can return null** — or Optional (unlike constructors)
5. **Can have multiple with different names** — unlike overloaded constructors

### Common Naming Conventions

- `from()` — conversion from another type
- `of()` — convenient instance creation
- `valueOf()` — alternative to constructors
- `getInstance()` — singleton or cached instances
- `newInstance()` — creates new instance each time

---

## Item 25 — Limit Source Files to a Single Top-Level Class

### Why This Matters

Java requires:
- One `public` class per file
- Filename must match the public class name
- File can contain multiple non-public classes (but don't do this!)

**Confusion arises when:**
- IDE shows multiple classes in one file
- Searching for "class X" finds the wrong file
- Git shows changes in unrelated classes

---

## The Thread Safety Story

Many of these items (17, 18, 22) connect to **thread safety**:

- **Immutable objects** → inherently thread-safe (Item 17)
- **Composition** → avoids race conditions in inheritance (Item 18)
- **Static nested classes** → no accidental reference capture (Item 22)

**The lesson:** Design decisions in class structure have ripple effects into concurrency.

---

## Summary: The Philosophy

Chapter 4 is really about one thing: **Managing complexity through controlled access and clear contracts.**

- Minimize accessibility → Reduce coupling
- Use accessors → Maintain flexibility
- Minimize mutability → Enable safe sharing
- Composition over inheritance → Loose coupling
- Interfaces over abstract classes → Flexibility
- Static factories → Clear intent

These principles compound — applying them consistently makes your codebase easier to understand, test, and maintain.
