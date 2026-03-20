# Module 3: Explain Why

## Chapter 2: Creating and Destroying Objects

This module explains the JVM mechanics and language design decisions behind each rule. Understanding the "why" helps you make better decisions.

---

## Item 1 — Static Factory Methods

### Why constructors are limited

When you call `new MyClass(args)`, the JVM allocates memory and invokes the constructor directly. There's no opportunity to:
- Return a cached instance
- Return a subtype
- Apply naming conventions

**The constructor's job is fixed:** It always creates a new object of exactly that type.

### What goes wrong if you ignore this

Without static factory methods, you can't implement caching:

```java
// Without factory - always creates new objects
new BigDecimal("0.00")  // New object each time

// With factory - reuses cached instances
BigDecimal.valueOf(0.00)  // Returns cached BigDecimal.ZERO
```

In high-throughput microservices, creating millions of identical `BigDecimal` objects causes GC pressure and latency spikes.

### The JVM mechanism

Static methods are invoked via `invokestatic` bytecode, not `invokespecial` (which constructors use). This allows the JVM to:
- Inline the call if it's final
- Cache the returned object
- Perform escape analysis to allocate on stack instead of heap

**Bottom line:** Static factories give you control over object creation, enabling performance optimizations impossible with constructors.

---

## Item 2 — Builder Pattern

### Why telescoping constructors fail

The JVM doesn't track parameter names at runtime. When you call:

```java
new User("123", "john@example.com", "John", "Doe", null, null, true, 30, List.of());
```

All parameters are positional. The compiler can't warn you if you swap `firstName` and `lastName`. IDEs can help, but it's not enforced.

### What goes wrong if you ignore this

- **Parameter confusion:** Swap `age` and `active` accidentally
- **Readability:** What does `100, 60` mean?
- **Maintainability:** Adding a 10th parameter means another constructor
- **Immutability:** Telescoping constructors need setters to fill in optional fields

### The JVM mechanism

Builder uses a separate `Builder` class with individual setter methods. Each setter returns `this`, enabling fluent chaining. The JVM sees:
- `builder.firstName("John")` → returns same Builder instance
- `builder.build()` → invokes private constructor with Builder as parameter

**Modern Java:** Records (Java 16+) solve this differently - they generate `equals()`, `hashCode()`, `toString()` and accessors automatically, with compact constructors for validation.

---

## Item 3 — Singleton Pattern

### Why synchronization is problematic

The JVM's memory model has a subtle ordering problem:

```java
// This can fail! Not thread-safe
if (instance == null) {     // Thread A sees null
    instance = new Singleton();  // Thread B might also see null
}
```

`new Singleton()` is actually THREE operations:
1. Allocate memory
2. Call constructor
3. Assign reference

The JVM can reorder steps 2 and 3. Thread A might see a non-null reference but uninitialized object.

### The double-checked locking fix (and why it's complex)

```java
// The fix - volatile prevents reordering
private static volatile Singleton instance;

public static Singleton getInstance() {
    if (instance == null) {
        synchronized (Singleton.class) {
            if (instance == null) {
                instance = new Singleton();
            }
        }
    }
    return instance;
}
```

`volatile` prevents instruction reordering via a memory barrier. But this is complex and easy to get wrong.

### Why enum wins

**Enum singletons are inherently thread-safe.** The JVM guarantees:
- Singleton is created when the class is loaded (no race condition)
- Serialization is handled automatically
- Reflection can't create new instances (enums can't be instantiated)

```java
// JVM ensures this runs exactly once, before any thread accesses INSTANCE
public enum Singleton {
    INSTANCE;
}
```

---

## Item 4 — Noninstantiable Utility Classes

### Why the compiler generates a constructor

In Java, if you don't declare any constructor, the compiler generates a default no-arg constructor:

```java
// What the compiler sees:
public class Math {
    public Math() {}  // Generated automatically!
}
```

This allows `new Math()`, which makes no sense for a utility class.

### What goes wrong if you ignore this

- Accidental instantiation wastes memory
- Semantic confusion - what does `new Math()` mean?
- Subclassing utility classes (violates intent)

### The JVM mechanism

Private constructors aren't accessible via reflection (with certain protections) or bytecode. The `invokespecial` instruction fails with `IllegalAccessError` if the constructor is private and not accessible from the calling context.

---

## Item 5 — Dependency Injection

### Why hardwired dependencies fail

When you write:

```java
class OrderService {
    private PaymentService payment = new PaymentService();
}
```

You're creating a **compile-time coupling**. The `OrderService` class now literally cannot exist without `PaymentService`.

### What goes wrong if you ignore this

- **Testing:** You can't test `OrderService` without a real `PaymentService`
- **Flexibility:** Can't swap `StripeGateway` for `PayPalGateway` without code changes
- **Lifecycle:** Who manages the `PaymentService` lifecycle?

### The JVM mechanism

Dependency injection moves object creation to a container (Spring). At runtime:
- Spring creates beans following a dependency graph
- Beans are proxies that handle lifecycle
- Circular dependencies are detected and rejected

This inversion of control (IoC) decouples "what" from "how".

---

## Item 6 — Avoiding Unnecessary Objects

### Why object creation has cost

Every `new` involves:
1. Allocating memory on the heap
2. Running constructor code
3. GC tracking the object

For short-lived objects, the cost is allocation + GC. In tight loops, this adds up.

### What goes wrong if you ignore this

```java
// This creates 1 million String objects!
String s = "";
for (int i = 0; i < 1_000_000; i++) {
    s += "x";  // New String each iteration
}
```

Each `+=` creates a new `StringBuilder`, appends, converts back to String. **O(n²) memory allocation!**

### The JVM mechanism

- **String constant pool:** JVM deduplicates String literals and `String.intern()`
- **Escape analysis:** HotSpot can allocate objects on stack if they don't escape the method
- **TLAB (Thread Local Allocation Buffer):** Reduces allocation contention
- **GC generations:** Young GC is fast, but still not free

**Boxing penalties:** `Integer` vs `int` involves heap allocation for each boxed value. In loops, prefer primitives.

---

## Item 7 — Eliminating Obsolete References

### Why GC doesn't collect everything

The Garbage Collector can only collect objects that are **unreachable** from GC roots:
- Stack frames (local variables)
- Static fields
- JNI references

If you hold a reference to an object in a collection, it's reachable - even if you'll never use it again.

### What goes wrong if you ignore this

```java
public class Stack {
    private Object[] elements = new Object[100];
    private int size = 0;

    public Object pop() {
        return elements[--size];  // Element still in array!
    }
}
```

This stack "leaks" - all popped elements remain in the array, preventing GC. A large stack holding millions of "popped" objects = OutOfMemoryError.

### The JVM mechanism

- **Weak references:** `WeakReference` doesn't prevent GC
- **Soft references:** GC may collect when memory is low
- **Phantom references:** For post-GC cleanup
- **WeakHashMap:** Keys are held via WeakReference

---

## Item 8 — Avoiding Finalizers

### Why finalizers are unreliable

Finalizers have serious problems:
1. **Not guaranteed to run:** JVM can exit without calling them
2. **Not immediate:** Can run arbitrarily delayed
3. **Performance cost:** Finalizable objects take longer to collect
4. **Exception swallowing:** If finalize() throws, the exception is ignored

### What goes wrong if you ignore this

```java
// Resource leaked! Finalizer might never run
class DatabaseConnection {
    @Override
    protected void finalize() throws Throwable {
        close();  // Unreliable!
    }
}
```

In production, you might exhaust database connections before GC runs finalize().

### The JVM mechanism

Finalizer is run by a dedicated daemon thread (`Finalizer`). The queue can grow unbounded if objects finalize slowly or throw exceptions. This is why Java 7 introduced try-with-resources as a better alternative.

---

## Item 9 — try-with-resources

### Why try-finally masks exceptions

```java
try {
    throw new IOException("Primary exception");
} finally {
    close(); // If this throws, original exception is LOST!
}
```

When both try and finally throw, the finally exception **suppresses** the original. In Java 7+, suppressed exceptions are chained, but try-finally doesn't expose this nicely.

### What goes wrong if you ignore this

You lose debugging information. When a file can't be opened because a directory doesn't exist, but close() also fails, you only see the close() error.

### The JVM mechanism

try-with-resources generates bytecode that:
1. Implements `AutoCloseable`
2. Calls `close()` in reverse order (last opened = first closed)
3. Chains suppressed exceptions properly
4. Uses `Throwable.addSuppressed()`

The JVM sees this as a structured pattern and can optimize it better than manual finally blocks.

---

## Summary

| Item | JVM Mechanism | Failure Mode |
|------|--------------|-------------|
| 1 | Static vs constructor bytecode | No caching, no polymorphism |
| 2 | Parameter erasure | Wrong parameter values |
| 3 | Memory model reordering | Partially initialized objects |
| 4 | Default constructor generation | Accidental instantiation |
| 5 | Object graph coupling | Untestable code |
| 6 | Heap allocation, GC | Memory bloat, latency |
| 7 | Reachability | Memory leaks |
| 8 | Finalizer thread | Resource leaks |
| 9 | Exception chaining | Lost errors |
