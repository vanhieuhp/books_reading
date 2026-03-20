# Module 6: Advice & Recommendations

## Chapter 2: Creating and Destroying Objects

This module provides senior-developer judgment on when to bend the rules, common pitfalls, and a practical code review checklist for your Spring Boot codebase.

---

## When to Bend the Rules

### Item 1 — Static Factory Methods

**Be Flexible When:**
- You have a simple class with 1-3 parameters and clear intent
- The class is a value type where constructor is obvious
- You need overloading with different parameter types

**Be Strict When:**
- You need caching or instance control
- You need to return subtypes
- The constructor parameter names are unclear

### Item 2 — Builder Pattern

**Consider Alternatives:**
- **Java 16+ Records:** For DTOs with 3-8 fields, records are simpler
- **Named Parameters:** With Lombok's `@Builder`, you get named parameters automatically
- **Default Values:** Consider if most users use defaults, then use Telescoping carefully

**Skip Builder When:**
- The object is truly simple (1-3 fields)
- You're using Java 16+ records

### Item 3 — Singleton Pattern

**Consider Alternatives in Spring:**
- Spring beans are singletons by default — you rarely need manual singletons
- Use `@Scope(SCOPE_PROTOTYPE)` when you need new instances
- Use `@Scope(value = "session", proxyMode = TARGET_CLASS)` for session-scoped beans

**Prefer Spring DI Over Manual Singletons:**
```java
// Let Spring manage the singleton
@Service
public class MyService {
    // Spring creates ONE instance automatically
}
```

### Item 5 — Dependency Injection

**When Constructor Injection Isn't Possible:**
- Circular dependencies → use setter or field injection (temporary fix)
- Optional dependencies → setter injection with `@Autowired(required=false)`
- Complex initialization → `@PostConstruct`

### Item 6 — Avoiding Unnecessary Objects

**Acceptable Overhead:**
- Object pools for expensive resources (database connections)
- Temporary objects in business logic (not hot paths)
- Autoboxing in non-loop code

**Don't Optimize Prematurely:**
- String concatenation in single expressions
- Boxing in business logic
- Micro-optimizations that hurt readability

---

## Common Traps and Gotchas

### Trap 1: Builder Inheritance
```java
// Problem: Subclassing builders is tricky
class UserBuilder extends PersonBuilder { } // Doesn't work as expected

// Solution: Use composition or static factory in subclass
public static UserBuilder builder() { return new UserBuilder(); }
```

### Trap 2: Static Factory + Inheritance
```java
// Problem: Private constructor prevents subclassing
public class Animal {
    private Animal() {}  // Can't extend!
}

// Solution: Provide protected factory method
protected static Animal create() { return new Animal(); }
```

### Trap 3: Singleton + Serialization
```java
// Problem: Default serialization breaks singleton
class Singleton implements Serializable {
    private static final Singleton INSTANCE = new Singleton();
}
// After deserialization: INSTANCE != deserializedObject!

// Solution: Use enum or implement readResolve()
protected Object readResolve() { return INSTANCE; }
```

### Trap 4: DI + Circular Dependencies
```java
// Problem: Circular dependency
@Service
class A { @Autowired B b; }

@Service
class B { @Autowired A a; }  // Spring throws BeanCurrentlyInCreationException

// Solution: Use @Lazy or refactor
@Service
class A { @Lazy @Autowired B b; }
```

### Trap 5: try-with-resources + Checked Exceptions
```java
// Problem: Checked exceptions require handling
try (FileInputStream fis = new FileInputStream("file")) {
    // IOException must be declared or caught
}

// Solution: Wrap in utility method
public static FileInputStream openFile(String path) throws FileNotFoundException {
    return new FileInputStream(path);
}
```

---

## Tools and Recommendations

### Static Analysis Tools

| Tool | Checks For | Integration |
|------|-----------|-------------|
| **SpotBugs** | Unnecessary object creation, singleton issues | Maven/Gradle |
| **SonarQube** | Code smells, DI violations | CI/CD |
| **IntelliJ Inspections** | Local issues | IDE |
| **Error Prone** | Compile-time bugs | Compiler |

### Recommended IntelliJ Inspections

Enable these inspections:
1. **Service layer annotations** — verify @Service classes use DI
2. **Non-final static fields** — singleton detection
3. **MethodReferencesCanBeReplacedWithLambda** — modernization
4. **CanBePrimitive** — avoid unnecessary boxing

### Checkstyle Rules

```xml
<!-- Checkstyle configuration for Effective Java -->
<module name="AvoidEscapedUnicodeCharacters"/>
<module name="FinalClass"/>
<module name="MutableStaticVariable"/>
<module name="NoWhitespaceAfter"/>
```

---

## Modern Java Impact

### Java 16+ Records

Records fundamentally change Items 1, 2, and 4:

```java
// Item 2: Records as alternatives to builders
// Before: Builder pattern
User user = User.builder()
    .name("John")
    .email("john@example.com")
    .build();

// After: Records (Java 16+)
record User(String name, String email) {}

// Compact constructor for validation
record User(String name, String email) {
    User {
        Objects.requireNonNull(name);
        Objects.requireNonNull(email);
    }
}
```

**When to use records vs builders:**
- Use **records** for: DTOs, value objects, data carriers
- Use **builders** for: Complex objects with validation, optional fields, builder-specific logic

### Java 17+ Sealed Classes

Sealed classes don't directly impact Chapter 2, but they work well with static factories for controlled instantiation:

```java
// Control who can extend your types
public sealed class Payment permits CreditCardPayment, PayPalPayment {
    public abstract Money amount();
}

public final class CreditCardPayment extends Payment { ... }
public final class PayPalPayment extends Payment { ... }

// Factory method can return sealed types
public static Payment create(String type) {
    return switch(type) {
        case "card" -> new CreditCardPayment(...);
        case "paypal" -> new PayPalPayment(...);
    };
}
```

### Java 21+ Virtual Threads

Virtual threads (Project Loom) change some advice:
- Object creation is cheaper (stack allocation)
- Thread-local variables work differently
- But memory leaks still matter for heap

---

## 📋 Code Review Checklist

Use this checklist when reviewing Spring Boot code for Chapter 2 compliance:

### Object Creation

- [ ] **Item 1:** Do creation methods have descriptive names (`from()`, `of()`, `valueOf()`)?
- [ ] **Item 2:** Do classes with 4+ parameters use Builder or records?
- [ ] **Item 2:** Are builders tested for invalid input?
- [ ] **Item 4:** Do utility classes have private constructors?

### Singletons and DI

- [ ] **Item 3:** Are singletons implemented via enum or Spring's scope?
- [ ] **Item 3:** Is the singleton thread-safe?
- [ ] **Item 5:** Are dependencies injected via constructor/setter (not `new`)?
- [ ] **Item 5:** Are interfaces used for dependencies, not concrete classes?

### Resource Management

- [ ] **Item 6:** Are objects reused in loops where possible?
- [ ] **Item 6:** Are primitives used instead of boxed types in hot paths?
- [ ] **Item 7:** Are caches cleaned up (TTL, WeakHashMap)?
- [ ] **Item 8:** Is cleanup handled via try-with-resources or @PreDestroy?
- [ ] **Item 9:** Are all resources in try-with-resources?

### Spring Boot Specific

- [ ] **Constructor injection** used for required dependencies?
- [ ] **`@RequiredArgsConstructor`** (Lombok) reducing boilerplate?
- [ ] **`@Scope`** used correctly for non-singleton beans?
- [ ] **No `new` keywords** inside @Service classes?
- [ ] **DTOs** using records or immutable classes?

---

## SOLID Connections

Chapter 2 patterns support SOLID principles:

| Principle | Chapter 2 Support |
|-----------|------------------|
| **S**ingle Responsibility | Static factories separate creation from business logic |
| **O**pen/Closed | Builders allow extension without modification |
| **L**iskov Substitution | Static factories can return subtypes |
| **I**nterface Segregation | DI depends on interfaces, not implementations |
| **D**ependency Inversion | Item 5 is the core DI principle |

---

## Summary

1. **Static factories** over constructors when you need naming, caching, or polymorphism
2. **Builders** for complex objects; use records for simple DTOs
3. **Singletons** - let Spring handle them; use enum if you must
4. **Utility classes** - private constructor always
5. **Dependency injection** - always, no `new` inside services
6. **Object reuse** - but don't over-optimize
7. **Memory leaks** - clean up caches and obsolete references
8. **No finalizers** - use try-with-resources or @PreDestroy
9. **try-with-resources** - always, no manual close()
