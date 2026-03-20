# Chapter 3: Methods Common to All Objects — Advice & Recommendations

> Senior developer insights, edge cases, and unwritten rules for working with Object methods.

---

## Opinionated Recommendations

### When to Be Strict (Don't Bend These Rules)

1. **Always override equals/hashCode together** — Never override one without the other. This is an ironclad rule.

2. **Use ID-based equality for JPA entities** — Hibernate's persistence context depends on correct equals/hashCode. Use the database ID (after it's assigned).

3. **Make value objects immutable** — If you're overriding equals/hashCode for value semantics, make the class final or use `record`. Mutable value objects with equals/hashCode are a recipe for disaster.

4. **Prefer Comparable over Comparator for natural order** — If there's a single natural ordering, implement `Comparable<T>`. Use `Comparator` for multiple orderings.

### When You Can Bend the Rules

1. **Classes representing services (not data)** — `Thread`, `ExecutorService`, `InputStream` — these represent processes, not values. Default identity equality is correct.

2. **Utility classes with only static methods** — No instance, so no equality needed.

3. **Enums** — Already have correct equals/hashCode (singleton pattern). Don't override.

---

## Common Traps and Gotchas

### Trap 1: Using Business Fields for Entity Equality (JPA)

```java
// WRONG for JPA entities:
@Entity
class Order {
    @Id Long id;  // Database ID
    String orderNumber;  // Business key

    // Using business key for equals - BREAKS after persistence!
    @Override
    public boolean equals(Object o) {
        return o instanceof Order && orderNumber.equals(((Order)o).orderNumber);
    }
    @Override
    public int hashCode() { return orderNumber.hashCode(); }
}

// Why it's wrong:
// 1. Before @Id is assigned (pre-persist): new Order() has id=null
//    Two transient orders with same orderNumber are "equal"
// 2. After persist: both get different IDs, but equals still uses orderNumber
//    HashSet behavior is inconsistent (before/after persist)

// CORRECT for JPA:
@Override
public boolean equals(Object o) {
    if (this == o) return true;
    if (o == null || getClass() != o.getClass()) return false;
    Order order = (Order) o;
    return id != null && id.equals(order.id);
}

@Override
public int hashCode() {
    // For unsaved entities (id=null), return constant
    // This ensures consistent behavior in HashSet before/after persist
    return id != null ? id.hashCode() : 0;
}
```

### Trap 2: Hash Code Changes During Object Lifetime

```java
// WRONG - hashCode changes if fields change!
class MutablePerson {
    String name;
    int age;

    @Override
    public int hashCode() {
        return Objects.hash(name, age);  // Changes if name/age changes!
    }
}

// Problem: Can't use as HashMap key!
Map<MutablePerson, Order> orders = new HashMap<>();
MutablePerson p = new MutablePerson("John", 30);
orders.put(p, order1);
p.setAge(31);  // Modifies object!
orders.get(p);  // Returns null! Different hashCode now!
```

**Solution:** Only use immutable objects as HashMap keys, or use `IdentityHashMap` for mutable keys.

### Trap 3: Float/Double in hashCode

```java
// WRONG:
@Override
public int hashCode() {
    return Float.hashCode(price);  // Float.hashCode != equals logic!
}

// CORRECT - match equals:
@Override
public boolean equals(Object o) {
    if (!(o instanceof Product)) return false;
    // Float.compare handles NaN and -0.0 correctly
    return Float.compare(price, ((Product)o).price) == 0;
}

@Override
public int hashCode() {
    // Float.hashCode works IF equals uses Float.compare
    return Float.hashCode(price);
}
```

### Trap 4: Collection Fields in equals/hashCode

```java
// WRONG - mutable collection in equals:
class Team {
    Set<String> members;

    @Override
    public boolean equals(Object o) {
        // Calling members.equals() on mutable set - DANGER!
        return o instanceof Team && members.equals(((Team)o).members);
    }

    @Override
    public int hashCode() {
        return members.hashCode();  // Changes if set changes!
    }
}

// CORRECT:
class Team {
    private final Set<String> members;  // Immutable set!

    // Defensive copy in constructor
    public Team(Collection<String> members) {
        this.members = Set.copyOf(members);  // Immutable copy!
    }

    @Override
    public boolean equals(Object o) {
        if (!(o instanceof Team)) return false;
        return members.equals(((Team)o).members);  // Safe now
    }

    @Override
    public int hashCode() {
        return members.hashCode();  // Stable now
    }
}
```

### Trap 5: Forgetting hashCode When Using Objects.hash

```java
// This is easy to forget but critical:
class User {
    String email;
    String name;

    @Override
    public boolean equals(Object o) {
        return o instanceof User && email.equals(((User)o).email);
    }

    // Easy to forget! But MUST override hashCode if equals is overridden
    @Override
    public int hashCode() {
        return Objects.hash(email);  // Don't include name!
    }
}
```

---

## Tools and Recommendations

### Static Analysis Tools

| Tool | What It Catches | Integration |
|------|----------------|--------------|
| **SpotBugs/Error Prone** | Inconsistent equals/hashCode | Maven/Gradle |
| **SonarQube** | Rule: "equals and hashCode should be overridden together" | CI/CD |
| **IntelliJ Inspections** | Highlights missing hashCode when equals is overridden | IDE |
| **Lombok @Data** | Auto-generates both together (but be careful with entities!) | Compile-time |
| **AutoValue (Google)** | Immutable value types with correct equals/hashCode | Annotation processor |

### Recommended Approach

```java
// For simple value classes:
public record Money(BigDecimal amount, String currency) {
    // Auto-generates equals, hashCode, toString!
}

// For entities (JPA):
@Entity
class Order {
    @Id @GeneratedValue
    private Long id;

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        Order order = (Order) o;
        return id != null && id.equals(order.id);
    }

    @Override
    public int hashCode() {
        return id != null ? id.hashCode() : getClass().hashCode();
    }
}

// For complex values without records:
class Product {
    String name;
    BigDecimal price;
    List<String> tags;

    @Override
    public boolean equals(Object o) {
        // Generated by IDE or AutoValue
    }

    @Override
    public int hashCode() {
        // Generated by IDE or AutoValue
    }
}
```

---

## Modern Java: Records (Java 16+)

**Records completely change the game** for this chapter:

```java
// Before Java 16 - manual work:
public final class Money {
    private final BigDecimal amount;
    private final String currency;

    public Money(BigDecimal amount, String currency) {
        this.amount = amount;
        this.currency = currency;
    }

    // Boilerplate: getters, equals, hashCode, toString, constructor...
}

// Java 16+ - automatic:
public record Money(BigDecimal amount, String currency) {
    // Auto-generates:
    // - All fields as private final
    // - Canonical constructor
    // - Getters: amount(), currency()
    // - equals() - compares all fields
    // - hashCode() - based on all fields
    // - toString() - "Money[amount=10, currency=USD]"
}

// Can still add validation:
public record Money(BigDecimal amount, String currency) {
    public Money {
        if (amount == null || amount.compareTo(BigDecimal.ZERO) < 0) {
            throw new IllegalArgumentException("Amount must be positive");
        }
    }

    // Can add methods:
    public Money add(Money other) {
        return new Money(amount.add(other.amount), currency);
    }
}
```

**When to use records:**
- DTOs
- Value objects
- Response objects
- Any class where you want value equality

**When NOT to use records:**
- JPA entities (need mutable ID-based equality)
- Classes with complex construction logic
- When you need to change equality after construction

---

## Code Review Checklist

For each class you review, check:

- [ ] **equals/hashCode pairs:** If one is overridden, is the other also overridden?
- [ ] **equals consistency:** Does `a.equals(b)` imply `a.hashCode() == b.hashCode()`?
- [ ] **Entity equality:** For JPA entities, is equals based on ID (after persist)?
- [ ] **Immutability:** If used in HashMap/HashSet, is the class immutable (or are fields stable)?
- [ ] **Null safety:** Does equals handle nulls safely? Does hashCode?
- [ ] **Collection fields:** Are collections in equals/hashCode immutable or defensive-copied?
- [ ] **toString:** Is it useful? Would it help debug a production issue?
- [ ] **compareTo consistency:** Does `compareTo(x,y) == 0` imply `x.equals(y)`?
- [ ] **No subtraction:** For integer comparison, using `Integer.compare()`, not `-`?
- [ ] **clone alternative:** If Cloneable is implemented, is there a better alternative (copy constructor)?

---

## Related Patterns

| Pattern | Applies To | Description |
|---------|------------|-------------|
| **Value Object** | Item 10-12 | Objects that are equal by value, not identity |
| **Entity** | Item 10-11 | Objects with identity tied to database ID |
| **Builder** | Item 2 | For complex object construction |
| **Factory Method** | Item 1 | Alternative to constructors |
| **Decorator** | Item 18 | Composition over inheritance |
