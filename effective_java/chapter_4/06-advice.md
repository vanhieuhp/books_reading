# Chapter 4: Classes and Interfaces

## Items 15–25

---

## 💡 Module 6: Advice & Recommendations

This module shares senior-developer judgment — the unwritten rules, edge cases, and "it depends" answers.

---

## Common Traps and Gotchas

### 1. The "I Need to Extend for Testing" Trap

**Situation:** You make a class non-final because "we need to mock it in tests."

**Better approach:** Use interfaces and mock the interface, not the concrete class.

```java
// BAD: Leaving class extensible just for testing
public class OrderService {
    // ...
}

// GOOD: Program to interface, mock the interface
public interface OrderService {
    Order findById(String id);
}

@Service
public class OrderServiceImpl implements OrderService {
    @Override
    public Order findById(String id) {
        // implementation
    }
}

// Test
@Test
void test() {
    OrderService mockService = mock(OrderService.class);
    when(mockService.findById("123")).thenReturn(testOrder);
    // Test with mock
}
```

---

### 2. Defensive Copies at Boundaries

Just because your class is immutable internally doesn't mean inputs are. Always copy mutable inputs in constructors and return copies of mutable outputs.

```java
public final class UserProfile {
    private final List<String> permissions;

    // Constructor: defensive copy INPUT
    public UserProfile(List<String> permissions) {
        this.permissions = List.copyOf(permissions);  // Immutable copy
    }

    // Getter: return immutable view of OUTPUT
    public List<String> getPermissions() {
        return permissions;  // Already immutable, safe to return
    }
}

// What if someone passes a mutable list?
List<String> perms = new ArrayList<>();
perms.add("ADMIN");
UserProfile profile = new UserProfile(perms);
perms.add("SUPER_ADMIN");  // Doesn't affect profile!
```

---

### 3. The equals/hashCode Trap with Mutable Fields

If you put mutable objects in a `HashSet` or `HashMap`, changing them after insertion breaks the collection.

```java
// DANGEROUS: Mutable key in HashMap
class Person {
    String name;
    int age;

    // Only compares name, not age!
    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        return o instanceof Person p && p.name.equals(name);
    }

    @Override
    public int hashCode() {
        return name.hashCode();
    }
}

Map<Person, String> map = new HashMap<>();
Person john = new Person("John", 25);
map.put(john, "Developer");

john.age = 30;  // Modifies key while in map!

String job = map.get(john);  // Returns null! Hash code changed!
```

**Fix:** Use immutable keys, or be very careful about when you modify objects in collections.

---

### 4. Serializable Immutable Classes

If your immutable class implements `Serializable`, you must ensure all fields are truly immutable.

```java
// DANGEROUS: Serializable but has mutable internal state
public final class User implements Serializable {
    private final String name;
    private final List<String> roles;  // Could be modified via reflection!

    public User(String name, List<String> roles) {
        this.name = name;
        this.roles = roles;
    }
}

// FIXED: Use immutable collections
public final class User implements Serializable {
    private final String name;
    private final List<String> roles;

    public User(String name, List<String> roles) {
        this.name = name;
        this.roles = List.copyOf(roles);  // Immutable!
    }
}
```

**Modern Java:** Use `List.of()`, `Map.of()`, `Set.of()` in Java 9+ — these create truly immutable collections.

---

### 5. Records vs Classes: When to Use What

Java 16+ records are perfect for some situations but not all.

| Use Records For | Use Classes For |
|-----------------|-----------------|
| DTOs | Entities with ID and lifecycle |
| Value objects | Objects with identity |
| Tuple-like types | Objects with complex behavior |
| Pure data holders | Mutable state when needed |

```java
// Perfect for records
public record UserDto(Long id, String name, String email) {}

// Keep as class - needs behavior
@Entity
public class User {
    @Id
    private Long id;
    private String name;
    private String email;

    // Complex behavior
    public void activate() { ... }
    public void deactivate() { ... }
}
```

---

## Recommended Tools

### Static Analysis

| Tool | What It Checks | Chapter 4 Relevance |
|------|----------------|---------------------|
| **SpotBugs** | Mutable fields, equals/hashCode issues | Items 16, 17 |
| **SonarQube** | Access control, class design | Items 15, 16, 17 |
| **Error Prone** | Bug patterns | All items |
| **IntelliJ Inspections** | Code style, design | All items |

### IntelliJ Inspections to Enable

```
Settings → Editor → Inspections:
☑ Serializable class with non-transient non-serializable instance field
☑ Method with same name as class (non-static factory hint)
☑ Non-final field in immutable class
☑ Public array in immutable class
☑ Private field not assigned in constructor (could be final)
```

---

## When to Bend the Rules

### Rule: "Make classes immutable"

**Bend it when:**
- You need lazy initialization (immutable objects can't cache expensive computations)
- You're building a cache (need to update entries)
- Performance analysis shows mutable is significantly faster
- The class is a pure data transfer with no invariants

### Rule: "Prefer composition over inheritance"

**Bend it when:**
- You're extending a framework class (Hibernate, Spring)
- The "is-a" relationship is truly valid
- You control both the parent and child classes
- Performance is critical (composition has overhead)

### Rule: "Use interfaces over abstract classes"

**Bend it when:**
- You need shared instance state
- You're creating a framework (like Spring)
- The class hierarchy is stable and won't change

---

## SOLID Connections

Chapter 4 items directly support SOLID principles:

| Principle | Chapter 4 Connection |
|-----------|---------------------|
| **S**ingle Responsibility | Item 21 (interfaces define types) |
| **O**pen/Closed | Item 17 (immutability) |
| **L**iskov Substitution | Item 19 (design for inheritance) |
| **I**nterface Segregation | Item 21 (interfaces define types) |
| **D**ependency Inversion | Item 20 (prefer interfaces) |

---

## Modern Java Impact

| Feature | Impact on Chapter 4 |
|---------|---------------------|
| **Records (Java 16+)** | Item 17 — records are immutable by default, auto-generate equals/hashCode/toString |
| **Sealed Classes (Java 17+)** | Items 19, 20 — refine inheritance control, replace tagged classes |
| **Pattern Matching (Java 16+)** | Item 23 — cleaner hierarchies with switch expressions |
| **Text Blocks (Java 15+)** | Item 21 — cleaner interface constants documentation |
| **Switch Expressions (Java 14+)** | Item 23 — exhaustive switch on sealed classes |

### Migration Path

```
// Before: Mutable class
public class User {
    private String name;
    public void setName(String name) { this.name = name; }
}

// After: Record (Java 16+)
public record User(String name) { }

// Before: Tagged class
class Shape {
    enum Type { CIRCLE, RECTANGLE }
    Type type;
    double radius;
    double width, height;
}

// After: Sealed class (Java 17+)
sealed interface Shape permits Circle, Rectangle {
    double area();
}
```

---

## 📋 Code Review Checklist

Use this checklist when reviewing code for Chapter 4 items:

- [ ] **Item 15:** Are all fields `private` unless there's a compelling reason otherwise?
- [ ] **Item 16:** Are mutable collections defensively copied on input/output?
- [ ] **Item 17:** Is the class `final` or are there documented reasons for it not to be?
- [ ] **Item 18:** Is inheritance used only when "is-a" relationship is truly met?
- [ ] **Item 19:** Are inheritance contracts documented or is the class final/sealed?
- [ ] **Item 20:** Are interfaces used to define types, not abstract classes for code reuse?
- [ ] **Item 21:** Are constants in utility classes, not interfaces?
- [ ] **Item 22:** Are static nested classes used when the outer reference isn't needed?
- [ ] **Item 23:** Are tagged classes replaced with proper hierarchies or sealed classes?
- [ ] **Item 24:** Are static factories used for semantic clarity over constructors?
- [ ] **Item 25:** Is there exactly one public class per source file?

---

## Key Principles Summary

1. **Start with maximum encapsulation** — relax access only when necessary
2. **Immutability is the default** — mutable is the exception
3. **Composition over inheritance** — loose coupling wins
4. **Interfaces define contracts** — abstract classes are for shared code
5. **Static factories over constructors** — named creation is clearer
6. **One class per file** — it's not just style, it's maintainability

---

## Further Reading

- *Effective Java, 3rd Edition* by Joshua Bloch — Chapter 4
- *Design Patterns* by Gamma, Helm, Johnson, Vlissides — Strategy, Decorator, Composite
- *Java Concurrency in Practice* by Brian Goetz — Immutability and thread safety
- *Domain-Driven Design* by Eric Evans — Value Objects and Entities
