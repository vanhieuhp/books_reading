# Chapter 4: Classes and Interfaces

## Items 15–25

---

## 🎯 Module 7: Interview Questions

These questions test your understanding of class design principles. Each question includes what interviewers are testing, model answers, and follow-up questions.

---

### Q1 [Junior] — What is the difference between `private`, `package-private`, `protected`, and `public`?

**Tests:** Understanding Java access modifiers and basic encapsulation.

**Model answer:** `private` restricts access to the declaring class only. Package-private (the default, no modifier) allows access within the same package. `protected` adds subclass access beyond package boundaries. `public` makes the member accessible from anywhere. For maximum safety, start with the most restrictive access level (`private`) and relax only when there's a proven need.

**Follow-up:** When would you intentionally use package-private for a class?

---

### Q2 [Junior] — Why should classes be immutable, and how do you make a class immutable in Java?

**Tests:** Understanding immutability patterns and their benefits.

**Model answer:** Immutable classes are inherently thread-safe because their state cannot change after construction — no synchronization is needed for safe sharing. They're also easier to reason about, cannot be corrupted by aliasing, and are safe to use in collections. To make a class immutable: declare it `final`, make all fields `private final`, don't provide setters, use defensive copies for mutable components, and ensure all constructors validate input.

**Follow-up:** What are the trade-offs of immutability in terms of memory and performance?

---

### Q3 [Mid] — Why is composition generally preferred over inheritance?

**Tests:** Understanding design principles and coupling.

**Model answer:** Inheritance creates tight coupling between parent and child classes — changes to the parent (even bug fixes) can silently break children. Composition allows loose coupling; you only depend on the public interface of the delegated object. Composition also enables runtime behavior changes through dependency injection, whereas inheritance is fixed at compile time.

**Follow-up:** How would you implement the decorator pattern using composition?

---

### Q4 [Mid] — What is the difference between an abstract class and an interface in Java?

**Tests:** Understanding Java type system and modern interface capabilities.

**Model answer:** Abstract classes can have state (fields) and constructor logic; interfaces in Java 8+ can have default methods but no instance state. A class can implement multiple interfaces but extend only one class. Interfaces define "can-do" contracts; abstract classes are for "is-a" relationships with shared implementation. With default methods, interfaces can now provide implementations too.

**Follow-up:** How do default methods in interfaces solve some limitations of abstract classes?

---

### Q5 [Mid] — What is a static factory method? Why would you use it instead of a constructor?

**Tests:** Understanding object creation patterns.

**Model answer:** Static factory methods are named methods that return instances, like `List.of()` or `Optional.of()`. They have advantages: meaningful names (`valueOf` vs confusing constructor overloads), can cache instances (singleton/flyweight), can return subtypes, and can return `null` or Optional instead of throwing. Constructors are still needed to actually build the object.

**Follow-up:** What are the naming conventions for static factory methods?

---

### Q6 [Mid] — What is the difference between a static nested class and a nonstatic inner class in Java?

**Tests:** Understanding nested class semantics and memory implications.

**Model answer:** A static nested class doesn't hold an implicit reference to the outer instance, while a nonstatic inner class does. This means inner classes can accidentally prevent garbage collection of their outer instances (memory leaks). Use static nested classes unless you specifically need access to the outer instance's fields.

**Follow-up:** What are some common sources of memory leaks related to nonstatic inner classes?

---

### Q7 [Senior] — Explain the concept of a "value object" and when you would use one.

**Tests:** Understanding domain-driven design and immutable types.

**Model answer:** A value object represents a value rather than an entity — it's defined by its attributes, not by identity. Two value objects with the same attributes are considered equal. They're immutable, side-effect-free, and often small. Examples include `Money`, `Address`, `PhoneNumber`. They're ideal for ensuring domain invariants and making code thread-safe.

**Follow-up:** How would you implement equals/hashCode for a value object with floating-point fields?

---

### Q8 [Senior] — How do you design for inheritance if you decide to allow it?

**Tests:** Understanding inheritance design and documentation.

**Model answer:** If allowing subclassing, document which methods call which other methods (the self-use pattern). Use `@throws` documentation for overridable methods. Consider providing hook methods — final methods that call overridable methods in a defined sequence. In modern Java, consider using sealed classes to explicitly control who can subclass.

**Follow-up:** What is the "chicken-and-egg" problem with clone() and how does composition help?

---

### Q9 [Senior] — How do you handle a situation where you need to extend a class you don't control?

**Tests:** Understanding composition patterns and API design.

**Model answer:** You cannot safely extend a class you don't control — you don't know its implementation details and changes can break your subclass. Instead, use composition: wrap the class in your own class that implements the same interface, and delegate calls to the wrapped instance. This is the GoF Decorator pattern and is how most modern frameworks work.

**Follow-up:** How does the Decorator pattern differ from the Proxy pattern?

---

### Q10 [System Design] — How would you design the domain model for an e-commerce system where orders can have different states and behaviors?

**Tests:** Applying class design principles to real-world problems.

**Model answer:** Use an interface or abstract base class for `Order`, with separate concrete classes or strategy implementations for different order types. Use the State pattern for order status transitions. Prefer composition for adding behaviors (like `ShippingService`, `PaymentProcessor`) over inheritance. Use value objects for `Money`, `Address`, `LineItem`. Consider sealed classes for exhaustive handling.

**Follow-up:** How would you handle order validation differently for various order types while keeping the code maintainable?

---

### Q11 [System Design] — In a microservices architecture, how do you ensure consistency when passing data between services?

**Tests:** Understanding distributed systems and immutable data patterns.

**Model answer:** Use immutable DTOs (or records) for all inter-service communication. This ensures the receiving service can't accidentally modify data. Version your APIs, and consider using schema registries. For eventual consistency, use idempotent operations and event sourcing. Records with explicit schemas make backward compatibility easier to manage.

**Follow-up:** How would you handle backward compatibility when adding fields to DTOs?

---

### Q12 [Gotcha] — What happens if you put a mutable object into a HashMap, modify it after insertion, and then try to retrieve it?

**Tests:** Understanding the internal workings of collections and hash-based containers.

**Model answer:** The object becomes unfindable. HashMap uses `hashCode()` to determine bucket location. If the hash code changes after insertion, the object is in the wrong bucket. The `containsKey()` will return false, `get()` will return null, and the object is effectively "lost" in the map despite being there.

**Follow-up:** How would you fix this while still needing mutable keys?

---

### Q13 [Gotcha] — Can you make a truly immutable class in Java even if it has a Date field?

**Tests:** Deep understanding of immutability and mutable fields.

**Model answer:** Yes, but it requires care. The `Date` object itself is mutable, so you must never expose the internal Date. In constructors, store a defensive copy. In getters, return a defensive copy. This applies to any mutable field — collections, Dates, arrays, and any object that can be modified.

```java
public final class Event {
    private final LocalDateTime timestamp;  // Better: use immutable type

    // If you must use mutable:
    private final Date mutableDate;

    public Event(Date date) {
        this.mutableDate = new Date(date.getTime());  // Defensive copy
    }

    public Date getDate() {
        return new Date(mutableDate.getTime());  // Defensive copy
    }
}
```

**Follow-up:** Why is `java.time` (LocalDateTime, Instant) preferred over `java.util.Date`?

---

### Q14 [Advanced] — How would you implement a singleton in Java, and what's the best approach?

**Tests:** Understanding object creation patterns and thread safety.

**Model answer:** The safest approaches are: (1) Use an enum with a single instance — immune to reflection and serialization attacks. (2) Use a private constructor with a static factory method that uses lazy initialization with synchronization or holder pattern. The enum approach is Bloch's recommended method.

```java
// Best approach
public enum Singleton {
    INSTANCE;

    public void doSomething() { }
}
```

**Follow-up:** Why is the double-checked locking pattern useful, and how does it work?

---

### Q15 [Advanced] — Explain the relationship between the Builder pattern and effective class design.

**Tests:** Understanding creational patterns and their connection to class design principles.

**Model answer:** The Builder pattern supports effective class design by: (1) enabling validation before construction, (2) making immutable classes practical by separating construction from the API, (3) providing readable construction for classes with many parameters, (4) allowing optional parameters without constructor overloads. It complements static factory methods and makes immutable classes easier to create.

**Follow-up:** How does Lombok's @Builder differ from manually implementing a builder?

---

## Answer Quick Reference

| Question | Key Concept |
|----------|-------------|
| Q1 | Access modifiers hierarchy |
| Q2 | Immutability benefits and implementation |
| Q3 | Composition vs inheritance trade-offs |
| Q4 | Abstract classes vs interfaces |
| Q5 | Static factory method advantages |
| Q6 | Static vs nonstatic nested classes |
| Q7 | Value object pattern |
| Q8 | Designing for inheritance |
| Q9 | Composition over inheritance |
| Q10 | Domain model design |
| Q11 | Microservices data consistency |
| Q12 | HashMap mutability gotcha |
| Q13 | Defensive copies |
| Q14 | Singleton implementations |
| Q15 | Builder pattern benefits |

---

## Preparation Tips

1. **Know the items by number** — interviewers may reference items directly
2. **Be ready to code** — expect to write small code snippets
3. **Explain trade-offs** — show you understand when to bend the rules
4. **Connect to real code** — reference your Spring/framework experience
5. **Know modern Java** — mention records, sealed classes where relevant
