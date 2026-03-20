# Module 7: Interview Questions

## Chapter 2: Creating and Destroying Objects

This module prepares you for technical interviews with questions testing real understanding of object creation and destruction in Java.

---

## Q1 [Junior] — What's wrong with this code?

```java
public class UserService {
    public static UserService getInstance() {
        return new UserService();
    }
}
```

**Tests:** Understanding of singleton pattern and static factory methods

**Model Answer:** This code creates a new instance every time `getInstance()` is called. It should store the instance in a static field and return the same instance. Also, it should be made thread-safe, or better yet, use Spring dependency injection instead of manual singleton pattern.

**Follow-up:** How would you make this thread-safe?

---

## Q2 [Junior] — What's the difference between constructor injection and setter injection in Spring?

**Tests:** Understanding of Spring DI and when to use each

**Model Answer:** Constructor injection is preferred because it enforces dependencies at creation time and makes the class immutable. Setter injection allows optional dependencies and circular dependencies but makes the class harder to test. In modern Spring, constructor injection with `@RequiredArgsConstructor` (Lombok) is the standard approach.

**Follow-up:** When would you use setter injection over constructor injection?

---

## Q3 [Mid] — Why should you avoid creating objects inside a loop?

**Tests:** Understanding of performance implications and garbage collection

**Model Answer:** Creating objects in loops generates unnecessary garbage that the GC must collect, causing:
1. Increased GC pressure and potential pauses
2. Memory allocation overhead
3. In tight loops, this can cause significant latency

Solutions include using StringBuilder for string concatenation, reusing objects, or moving invariant calculations outside the loop.

**Follow-up:** How does escape analysis help with object allocation?

---

## Q4 [Mid] — What's the problem with this code?

```java
public class Stack<T> {
    private Object[] elements = new Object[10];
    private int size = 0;

    public T pop() {
        return (T) elements[--size];
    }
}
```

**Tests:** Understanding of memory leaks and obsolete references (Item 7)

**Model Answer:** The popped elements remain in the array, holding references that prevent garbage collection. This is a memory leak - even though elements are "popped", they're still reachable from the array. The fix is to explicitly null out the reference: `elements[size] = null;`

**Follow-up:** How would WeakHashMap help prevent this type of leak?

---

## Q5 [Mid] — Why is the enum singleton preferred over other singleton implementations?

**Tests:** Understanding of thread safety, serialization, and reflection

**Model Answer:** Enum singletons are:
1. **Thread-safe by JVM guarantee** - the instance is created when the enum is loaded
2. **Serialization-safe** - JVM handles it automatically
3. **Reflection-safe** - can't be instantiated via reflection

The JVM guarantees exactly one instance, making it the simplest and safest singleton pattern.

**Follow-up:** How does double-checked locking work, and why does it need `volatile`?

---

## Q6 [Mid] — What happens if you forget to close a resource in a try-finally block and both the try and finally throw exceptions?

**Tests:** Understanding of exception handling and suppression

**Model Answer:** The exception from the finally block masks the original exception, making debugging difficult. You lose information about what went wrong in the try block. Try-with-resources handles this properly by chaining suppressed exceptions - both exceptions are preserved and the original is the primary exception.

**Follow-up:** How can you access suppressed exceptions in Java?

---

## Q7 [Senior] — Why should you avoid finalizers in Java?

**Tests:** Understanding of Java's resource management and finalizer pitfalls

**Model Answer:** Finalizers are:
1. **Not guaranteed to run** - JVM can exit without calling them
2. **Not immediate** - can be arbitrarily delayed
3. **Performance expensive** - objects with finalizers take longer to collect
4. **Exception-silencing** - exceptions in finalizers are ignored

Use try-with-resources or implement `AutoCloseable` instead.

**Follow-up:** What's the difference between finalize() and Cleaner in Java 9+?

---

## Q8 [Senior] — How does Spring manage bean lifecycle and when should you use @PostConstruct and @PreDestroy?

**Tests:** Spring bean lifecycle knowledge

**Model Answer:** Spring bean lifecycle:
1. Instantiation
2. Population of properties
3. **@PostConstruct** methods
4. Bean is ready for use
5. **@PreDestroy** methods (before destruction)
6. Bean is destroyed

@PostConstruct is for initialization logic, @PreDestroy for cleanup. These replace the need for finalizers in Spring beans.

**Follow-up:** What's the difference between @PreDestroy and DisposableBean?

---

## Q9 [Senior] — How would you implement a thread-safe cache with automatic expiration?

**Tests:** Design skills, memory management, Spring knowledge

**Model Answer:** Options include:
1. **ConcurrentHashMap with explicit cleanup** - manual removal
2. **WeakHashMap** - GC-based cleanup when keys are not referenced elsewhere
3. **Caffeine cache** - `CacheBuilder.newBuilder().expireAfterWrite()`
4. **Spring @Cacheable** - with TTL configuration

For production systems, use Caffeine or Spring Cache for automatic TTL management instead of building custom solutions.

**Follow-up:** What's the difference between expireAfterWrite and expireAfterAccess?

---

## Q10 [System Design] — Design a payment system that supports multiple payment providers

**Tests:** System design, patterns, DI

**Model Answer:** Design approach:
1. **Interface** for payment operations (`PaymentGateway`)
2. **Implementations** for each provider (`StripeGateway`, `PayPalGateway`)
3. **Factory** or Spring's DI to select provider
4. **Strategy pattern** for runtime selection

```java
public interface PaymentGateway {
    PaymentResult charge(Money amount);
}

@Service
public class PaymentService {
    private final Map<String, PaymentGateway> gateways;

    @Autowired
    public PaymentService(Map<String, PaymentGateway> gateways) {
        this.gateways = gateways;
    }

    public PaymentResult pay(String provider, Money amount) {
        return gateways.get(provider).charge(amount);
    }
}
```

**Follow-up:** How would you add circuit breaker pattern to handle provider failures?

---

## Q11 [Junior] — What's wrong with this utility class?

```java
public class StringUtils {
    public static boolean isEmpty(String s) {
        return s == null || s.length() == 0;
    }
}
```

**Tests:** Understanding of Item 4 - noninstantiable utility classes

**Model Answer:** The class can be accidentally instantiated. Add a private constructor to prevent instantiation:

```java
private StringUtils() {
    throw new AssertionError("Utility class - do not instantiate");
}
```

**Follow-up:** Why make the class final as well?

---

## Q12 [Mid] — What's the advantage of the Builder pattern over telescoping constructors?

**Tests:** Understanding of Item 2 and code readability

**Model Answer:** Builder pattern advantages:
1. **Readable code** - named parameters
2. **Type-safe** - compiler catches wrong types
3. **Flexible** - optional parameters without many constructors
4. **Validatable** - validation in single place
5. **Immutable** - supports immutable objects

Telescoping constructors become unmanageable with 4+ parameters and offer no type safety.

**Follow-up:** How do Java 16+ records compare to builders for DTOs?

---

## Q13 [Senior] — Gotcha Question: What does this code output?

```java
public class Main {
    public static void main(String[] args) {
        String a = "hello";
        String b = "hello";
        String c = new String("hello");

        System.out.println(a == b);
        System.out.println(a == c);
        System.out.println(a.equals(c));
    }
}
```

**Tests:** String interning and object identity vs equality

**Model Answer:**
- `a == b` → **true** (string literal pool - same reference)
- `a == c` → **false** (new object created)
- `a.equals(c)` → **true** (content equals)

This demonstrates the difference between identity (`==`) and equality (`equals()`), and how string literals are interned.

**Follow-up:** When would you use String.intern()?

---

## Q14 [System Design] — How would you design a session management system for a distributed microservice architecture?

**Tests:** Distributed systems, caching, memory management

**Model Answer:** Key considerations:
1. **Don't store sessions in-memory** - requires sticky sessions
2. **Use shared session store** - Redis, Memcached, or database
3. **Session token** - JWT or opaque token
4. **Expiration** - TTL in cache
5. **Weak references** - if in-memory caching is needed

For Spring: `@EnableRedisHttpSession` or JWT tokens with stateless authentication.

**Follow-up:** What's the difference between stateful and stateless authentication?

---

## Q15 [Mid] — Gotcha Question: What exception does this throw?

```java
public class Calculator {
    public static int divide(int a, int b) {
        return a / b;
    }

    public static void main(String[] args) {
        divide(1, 0);
    }
}
```

**Tests:** Understanding of arithmetic exceptions and integer division

**Model Answer:** It throws `ArithmeticException` (unchecked) - not a checked exception. Integer division by zero throws ArithmeticException, while floating-point division returns Infinity.

**Follow-up:** What happens when you divide `Integer.MIN_VALUE` by `-1`?

---

## Quick Reference

| Question | Level | Key Concept |
|----------|-------|------------|
| Q1 | Junior | Singleton pattern |
| Q2 | Junior | Spring DI |
| Q3 | Mid | Object creation, GC |
| Q4 | Mid | Memory leaks |
| Q5 | Mid | Enum singleton |
| Q6 | Mid | Exception handling |
| Q7 | Senior | Finalizers |
| Q8 | Senior | Spring lifecycle |
| Q9 | Senior | Caching |
| Q10 | System Design | Strategy + DI |
| Q11 | Junior | Utility classes |
| Q12 | Mid | Builder pattern |
| Q13 | Senior | String interning |
| Q14 | System Design | Session management |
| Q15 | Mid | Arithmetic exceptions |

---

## Answers to Gotcha Questions

### Q7 Follow-up: finalize() vs Cleaner

- **finalize()**: Legacy, runs on GC thread, deprecated in Java 9+
- **Cleaner**: Java 9+, runs on separate thread, more control, but still non-deterministic

### Q9 Follow-up: expireAfterWrite vs expireAfterAccess

- **expireAfterWrite**: Entry expires after write, regardless of access
- **expireAfterAccess**: Entry expires after last access - good for LRU caches

### Q13 Follow-up: When to use String.intern()

Rarely needed. Use cases:
- Reduce memory for many duplicate strings
- Custom classloader string pooling
- But has overhead and isn't always beneficial

### Q15 Follow-up: Integer.MIN_VALUE / -1

```java
System.out.println(Integer.MIN_VALUE / -1); // Throws ArithmeticException
```

Because `Integer.MIN_VALUE = -2^31` and `Integer.MAX_VALUE = 2^31 - 1`, the result overflows to overflow, throwing ArithmeticException.
