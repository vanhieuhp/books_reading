# Chapter 5: Generics — Interview Questions

> **Core Theme:** Prepare developers for technical interviews with questions that test real understanding. For each question: the question, what it tests, a model answer, and a follow-up.

---

## Q1 [Junior] — What is the difference between `List<String>` and `List<Object>`?

**Tests:** Understanding of Java's type system and generics invariance

**Model answer:** `List<String>` is a list that can only contain Strings. `List<Object>` is a list that can contain any Object. They're not the same type — `List<String>` is NOT a subtype of `List<Object>`. This is because if it were, you could add an Integer to what was supposed to be a list of Strings, causing a runtime crash. Generics are invariant in Java, unlike arrays which are covariant.

**Follow-up:** What about `List<?>` vs `List<Object>`?

---

## Q2 [Junior] — What is type erasure?

**Tests:** Understanding of how generics are implemented in Java

**Model answer:** Type erasure is how Java implements generics at the JVM level. The compiler removes all type parameters at compile time, replacing them with their bounds or `Object`. For example, `List<String>` becomes just `List`, and `<T extends Comparable<T>>` becomes `Comparable`. This happens because generics were added in Java 5 as a compile-time feature, and the JVM couldn't be changed for backward compatibility. The tradeoff is that you can't do `new T()` or `new T[]()` at runtime.

**Follow-up:** What problems does type erasure cause?

---

## Q3 [Mid] — Explain the PECS rule with an example.

**Tests:** Understanding of bounded wildcards and when to use them

**Model answer:** PECS stands for "Producer Extends, Consumer Super." If you're only reading from a collection (producing elements), use `? extends Type`. If you're only writing to a collection (consuming elements), use `? super Type`. For example, `processItems(List<? extends Item> items)` can read Items but not add them (because we don't know the actual type). Conversely, `addItems(List<? super Item> items)` can add Items but reading returns only Object. In a Spring service, if you have a method that reads from a list passed in, use extends. If you have a method that populates a list passed in, use super.

**Follow-up:** What happens if you try to write to a `? extends` collection?

---

## Q4 [Mid] — Why can't you create generic arrays like `new List<String>[]`?

**Tests:** Understanding of arrays vs generics type system differences

**Model answer:** Arrays in Java are reifiable — they know their component type at runtime. But generics are erased — type information doesn't exist at runtime. If you could create `new List<String>[]`, the runtime would only see `List[]`, and type safety would be violated. For example, you could store a `List<Integer>` in a `List<String>[]` array, and when you retrieved it and tried to iterate as Strings, you'd get a ClassCastException. Java forbids generic array creation to prevent this heap pollution. Use `List<List<String>>` or `List<ArrayList<String>>` instead.

**Follow-up:** What's heap pollution?

---

## Q5 [Mid] — What is the difference between `<T>` and `<?>` in Java generics?

**Tests:** Understanding of bounded vs unbounded wildcards

**Model answer:** `<T>` means "this is a specific type that will be determined later" — it's a type parameter that gets inferred or specified. `<?>` means "some unknown type" — it's a wildcard. When you use `<T>`, you can use T as a type in the method. With `?`, you can't use the unknown type in your code. For example, `List<T> list` lets you add elements of type T, but `List<?>` doesn't let you add anything (except null). Use `<T>` when you need to use the type, use `<?>` when you don't care what the type is but want flexibility.

**Follow-up:** When would you use `<? extends Number>` vs `<T extends Number>`?

---

## Q6 [Senior] — How would you implement a typesafe heterogeneous container?

**Tests:** Advanced generics knowledge and practical application

**Model answer:** Use `Class<T>` as a type token. The key is using `Class.cast()` instead of raw casts:
```java
public class Container {
    private final Map<Class<?>, Object> map = new HashMap<>();

    public <T> void put(Class<T> type, T value) {
        map.put(type, type.cast(value));  // Runtime type check!
    }

    public <T> T get(Class<T> type) {
        return type.cast(map.get(type));  // Safe cast!
    }
}
```
The `Class.cast()` method performs a runtime type check and throws if types don't match, unlike an unchecked cast which could fail silently.

**Follow-up:** How does Spring use this pattern?

---

## Q7 [Senior] — What is the difference between a generic method and a generic class?

**Tests:** Understanding of where type parameters can appear

**Model answer:** A generic class has type parameters at the class level: `class Box<T> { }`. Every instance of Box shares the same type. A generic method has type parameters in the method signature: `<T> T convert(String value, Class<T> type)`. Each method call can have different type arguments inferred. Generic methods are useful for static utilities and when the type should vary per call, not per object. You can also have both: a generic class with generic methods inside it.

**Follow-up:** Can you have a generic constructor?

---

## Q8 [Mid] — What does `@SafeVarargs` do and when is it safe to use?

**Tests:** Understanding of varargs with generics and when to suppress warnings

**Model answer:** `@SafeVarargs` suppresses the unchecked warning that appears when you use varargs with generic types. It's safe to use when: 1) the method doesn't store the varargs in a way that could cause heap pollution, and 2) the method doesn't throw exceptions based on the runtime type of the array elements. It's commonly used in JDK methods like `Arrays.asList()` and `Collections.addAll()`. It's NOT safe when you do something like store the varargs array in a collection, or try to cast elements to wrong types.

**Follow-up:** Can you use `@SuppressWarnings("unchecked")` instead?

---

## Q9 [Senior] — How do bounded type parameters work with multiple bounds?

**Tests:** Understanding of complex generic bounds

**Model answer:** You can have multiple bounds using `&`: `<T extends A & B & C>`. This means T must be a subtype of all listed types. If one bound is a class, it must come first. For example, `<T extends Comparable & Serializable>` means T must implement both interfaces. When using multiple bounds, the compiler uses the first bound for erasure, so you can only instantiate T at the location of the first bound. In practice, this is most useful when combining interfaces like `Comparable`, `Serializable`, or custom interfaces.

**Follow-up:** Can you have a bound that's both a class and interfaces?

---

## Q10 [System Design] — Design a type-safe repository pattern in Java using generics

**Tests:** Applying generics to real-world architecture

**Model answer:** I'd create a base generic repository interface and implementation:
```java
// Base interface
public interface BaseRepository<T, ID> {
    T save(T entity);
    Optional<T> findById(ID id);
    List<T> findAll();
    void delete(T entity);
}

// Generic JPA implementation
public class JpaRepository<T, ID> implements BaseRepository<T, ID> {
    private final Class<T> entityClass;
    private final EntityManager em;

    public JpaRepository(Class<T> entityClass, EntityManager em) {
        this.entityClass = entityClass;
    }

    @Override
    public T save(T entity) {
        return em.merge(entity);
    }

    @Override
    public Optional<T> findById(ID id) {
        return Optional.ofNullable(em.find(entityClass, id));
    }
}
```
The key insight is using `Class<T>` as a constructor parameter to capture the type at instantiation time. This is exactly how Spring Data JPA works internally.

**Follow-up:** How would you add type-safe query methods?

---

## Q11 [Junior] — What will be the output?

```java
List<String> strings = new ArrayList<>();
List<Object> objects = strings;  // Does this compile?
```

**Tests:** Understanding of generics subtyping rules

**Model answer:** This does NOT compile. Even though String is a subtype of Object, `List<String>` is NOT a subtype of `List<Object>`. This is intentional — if it were allowed, you could do `objects.add(42)` and then read from `strings.get(0)` expecting a String, causing a runtime crash. This is called "invariance" in generics, contrast with arrays which are "covariant."

**Follow-up:** How would you make a method that accepts both List<String> and List<Object>?

---

## Q12 [Senior] — What is the "Get and Put Principle"?

**Tests:** Understanding of wildcard usage patterns

**Model answer:** The Get and Put principle is another way to remember PECS: use `? extends` when you're only getting (reading) values out, and use `? super` when you're only putting (writing) values in. Don't use extends when you need to add, and don't use super when you need to read anything other than Object. For a copy operation, the source should use extends (it's a producer) and the destination should use super (it's a consumer): `void copy(List<? extends T> src, List<? super T> dst)`.

**Follow-up:** What about when you both read and write?

---

## Q13 [Mid] — What is the "diamond operator" and why is it useful?

**Tests:** Knowledge of Java 7+ syntax sugar

**Model answer:** The diamond operator `<>` is syntax sugar that lets you avoid repeating type parameters on the right side of an assignment:
```java
Map<String, List<User>> users = new HashMap<>();  // Diamond operator
```
Instead of:
```java
Map<String, List<User>> users = new HashMap<String, List<User>>();
```
The compiler infers the type from the left side. This reduces verbosity and makes code more maintainable — if you change the type on the left, you don't need to change the right.

**Follow-up:** Does the diamond operator work in all contexts?

---

## Q14 [Senior] — Can you use `var` with generics in Java 10+?

**Tests:** Understanding of Java 10+ type inference

**Model answer:** You can use `var` with generics, but there's a catch:
```java
var users = new ArrayList<User>();  // Works - infers ArrayList<User>
var map = new HashMap<String, List<Integer>>();  // Works - infers all types
```
However, you can't use the diamond operator with `var`:
```java
var users = new ArrayList<>();  // Won't compile - can't infer type!
```
The compiler needs the type information on the right side to infer `var`. This is a common mistake.

**Follow-up:** What's the difference between `var` and `?` in Java?

---

## Q15 [Mid] — What is a "bridge method" in Java generics?

**Tests:** Understanding of compiler-generated methods

**Model answer:** Bridge methods are synthetic methods generated by the compiler when you extend a generic class. They're needed to maintain backward compatibility. For example:
```java
class Node<T> {
    void setData(T data) { }
}

class StringNode extends Node<String> {
    @Override
    void setData(String data) { }  // Your actual method

    @Override
    void setData(Object data) {    // Bridge method - generated!
        setData((String) data);
    }
}
```
The bridge method converts `Object` to `String` and calls your override. You might see these in stack traces — ignore them.

**Follow-up:** Why does the compiler generate these automatically?

---

## Q16 [System Design] — How would you design a type-safe event bus using generics?

**Tests:** Advanced generic patterns for event systems

**Model answer:** I'd use `Class<T>` as type tokens for handler registration:
```java
public class EventBus {
    private final Map<Class<?>, Consumer<?>> handlers = new ConcurrentHashMap<>();

    public <T> void register(Class<T> eventType, Consumer<T> handler) {
        handlers.put(eventType, handler);
    }

    public <T> void publish(T event) {
        Consumer<T> handler = (Consumer<T>) handlers.get(event.getClass());
        if (handler != null) {
            handler.accept(event);
        }
    }
}
```
This provides compile-time type safety for handlers while allowing runtime dispatch. For hierarchical events, you'd use a recursive lookup with the type hierarchy.

**Follow-up:** How would you handle event inheritance (e.g., UserEvent -> CreatedEvent, DeletedEvent)?

---

## Summary: Interview Focus Areas

| Level | Key Questions |
|-------|--------------|
| **Junior** | Raw types, type erasure, invariance vs covariance, diamond operator |
| **Mid** | PECS, bounded wildcards, @SafeVarargs, multiple bounds |
| **Senior** | Heterogeneous containers, bridge methods, type tokens, complex design |
| **System Design** | Repository patterns, event bus, generic utilities |

### Most Common Gotcha Questions

1. **Why can't you create generic arrays?** — Tests understanding of type erasure + covariance
2. **PECS in practice** — Many developers memorize but don't understand
3. **Type erasure limitations** — What can't you do at runtime with generics?

### Top 3 Questions to Master

1. **Explain PECS** — Must know cold
2. **Type erasure** — Must understand JVM mechanics
3. **Typesafe heterogeneous container** — Must be able to implement
