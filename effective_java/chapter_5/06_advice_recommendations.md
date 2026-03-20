# Chapter 5: Generics — Advice & Recommendations

> **Core Theme:** Senior-developer judgment — the unwritten rules, the edge cases, the "it depends" answers. Tools, common traps, and a code review checklist.

---

## Senior Developer Insights

### 1. When to Use Raw Types (Rarely, But Sometimes)

There are a few legitimate uses of raw types:

- **Reading from `Class.getGenericSuperclass()`** in advanced reflection scenarios
- **Interoperating with legacy code** that predates generics
- **Runtime type checking** with `Class<?>`:

```java
// Sometimes raw type is needed for type checking
if (list instanceof List) {  // Raw type check
    // Process as raw list
}
```

> **Never in new code.**

### 2. The Diamond Operator is Your Friend

```java
// Don't repeat the type on the right side
Map<String, List<User>> usersByDepartment = new HashMap<>();  // Diamond operator

// Java 10+ can infer even more:
var users = new ArrayList<User>();  // Cleaner!
```

### 3. Be Careful with `List<?>` vs `List<Object>`

```java
List<?> wildcard = new ArrayList<String>();  // Type-safe: unknown type
List<Object> objects = new ArrayList<String>();  // COMPILE ERROR! Different types

// But both can hold anything:
wildcard.add(new Object());  // COMPILE ERROR! Can't add to ?
objects.add(new Object());   // OK!
```

**The key difference:** `?` means "some unknown type" — you can't add anything except null. `Object` means "any Object" — you can add anything.

### 4. Generic Static Methods vs. Static Generic Methods

```java
// Generic static method - type parameter before return type
public static <T> T of(Class<T> type) { ... }

// Static method in generic class - type parameter after class name
public class Container<E> {
    public static <E> Container<E> create() { ... }  // Both work, but different!
}
```

### 5. Beware of Bridge Methods

When you extend a generic class, the compiler generates "bridge methods" to maintain compatibility:

```java
// If you have:
class Node<T> {
    T data;
    void setData(T data) { this.data = data; }
}

class StringNode extends Node<String> {
    @Override
    void setData(String data) {  // Your override
        super.setData(data);
    }

    @Override
    public void setData(Object data) {  // Bridge method - generated!
        setData((String) data);
    }
}
```

You might see these in stack traces — they're synthetic methods, ignore them.

### 6. Type Inference in Java 10+

Use `var` to reduce verbosity:

```java
// Before:
List<User> users = new ArrayList<User>();
Map<String, List<Order>> orders = new HashMap<String, List<Order>>();

// Java 10+:
var users = new ArrayList<User>();
var orders = new HashMap<String, List<Order>>();
```

But be careful — `var` doesn't work with diamond inference in all cases:

```java
// This won't compile - need type on right side:
var users = new ArrayList<>();  // What type is this?

// Need to specify:
var users = new ArrayList<User>();
```

---

## Common Traps and Gotchas

### Trap 1: `List<List>` is NOT `List<List<Object>>`

```java
List<List> listOfLists = new ArrayList<>();
List<List<Object>> listOfObjectLists = listOfLists;  // COMPILE ERROR!

// They're different types:
// List<List> = "list of lists of unknown type"
// List<List<Object>> = "list of lists of Object"
```

### Trap 2: Generic Enums are Powerful but Tricky

```java
// Valid - enum can implement generic interface
enum Operation implements BinaryOperator<Integer> {
    PLUS { public Integer apply(Integer a, Integer b) { return a + b; } },
    MINUS { public Integer apply(Integer a, Integer b) { return a - b; } },
    TIMES { public Integer apply(Integer a, Integer b) { return a * b; } };
}

// Usage:
int result = Operation.PLUS.apply(5, 3);  // Returns 8
```

### Trap 3: `<?>` vs `Object`

| Aspect | `List<?>` | `List<Object>` |
|--------|-----------|----------------|
| Can add null? | Yes | Yes |
| Can add String? | No | Yes |
| Can add Integer? | No | Yes |
| Can read as String? | No (only Object) | Yes |
| Is subtype of List? | Yes | No |

### Trap 4: Varargs + Generics Warning

Java 7+ added `@SafeVarargs` to suppress the warning when safe. Only use it when:
1. You're just passing the varargs to another generic method
2. You don't store the varargs array anywhere

```java
// Safe:
@SafeVarargs
public static <T> List<T> listOf(T... elements) {
    return Arrays.asList(elements);  // Forwarding to safe JDK method
}

// Unsafe - storing the array:
@SafeVarargs
public static <T> void unsafe(T... elements) {
    List<T> list = Arrays.asList(elements);  // Array captured!
    // If you store 'list' somewhere, heap pollution!
}
```

### Trap 5: Multiple Type Parameters

Don't confuse position:

```java
// Class-level type parameter
class Repository<T, ID> { }  // T=entity, ID=key

// Method-level type parameter
public <T> T findById(Class<T> type) { }  // T inferred from parameter
```

---

## Modern Java: Records and Sealed Classes (Java 16+)

### Records

Records eliminate much generic boilerplate for DTOs:

```java
// Instead of complex generic DTOs:
public class GenericResponse<T, E> {
    private T data;
    private E error;
    // constructor, getters, equals, hashCode, toString...
}

// Use records for simpler cases:
public record ApiResponse<T>(T data, String status) {}

// Records automatically generate:
// - Constructor
// - equals(), hashCode(), toString()
// - Accessor methods (data(), status())
```

### Sealed Classes

Sealed classes work well with generics for type-safe heterogeneous containers:

```java
// Define allowed subtypes
public sealed class Shape permits Circle, Square, Rectangle {
    abstract double area();
}

public final class Circle extends Shape {
    double radius;
    @Override double area() { return Math.PI * radius * radius; }
}

public final class Square extends Shape {
    double side;
    @Override double area() { return side * side; }
}

// Now the compiler knows ALL subtypes - exhaustive switch:
double calculate(Shape s) {
    return switch(s) {
        case Circle c -> c.area();
        case Square sq -> sq.area();
        case Rectangle r -> r.length * r.width;
        // Compiler ensures exhaustive!
    };
}
```

---

## Tools for Generics

### IDE Inspections

- **IntelliJ** will catch raw types, suggest diamond operator, and warn about unchecked operations
- **Eclipse** has similar warnings

### Static Analysis Tools

- **SpotBugs/Error Prone:** Can detect generic-related bugs
- **SonarQube:** Has rules for generic usage
  - `S3512` — Type parameters should be parametric
  - `S2325` — Wildcard types should not be used in return types

### Build Tools

```xml
<!-- Maven compiler plugin -->
<plugin>
    <groupId>org.apache.maven.plugins</groupId>
    <artifactId>maven-compiler-plugin</artifactId>
    <configuration>
        <!-- Enable all warnings -->
        <compilerArgument>-Xlint:all</compilerArgument>
        <!-- Treat warnings as errors -->
        <failOnWarning>true</failOnWarning>
    </configuration>
</plugin>
```

---

## When to Break the Rules

### When to Use Raw Types

1. **Legacy interoperability** — working with pre-generics libraries
2. **Class literal** — `List.class` is valid, but `List<String>.class` is not

```java
// Valid:
Class<List> listClass = List.class;
Class<List<String>> listStringClass = null;  // Won't compile!

// Reflection pattern:
public <T> void load(Class<T> clazz) {
    // Class<T> is the pattern, not List<String>.class
}
```

### When to Use Unchecked Warnings

1. **Inside generic class implementation** — where you've ensured safety through design
2. **When using `Class.cast()`** — technically generates warning but is correct

```java
// Appropriate suppression location:
public E pop() {
    if (size == 0) throw new EmptyStackException();
    @SuppressWarnings("unchecked")  // Safe because push() enforces type
    E result = (E) elements[--size];
    return result;
}
```

### When NOT to Use PECS

When you need **both** reading and writing, use exact types:

```java
// Can't use wildcards here - need both read and write
public void process(List<Number> numbers) {
    numbers.add(42);    // Writing
    Number n = numbers.get(0);  // Reading
}
```

---

## 📋 Code Review Checklist

For every PR involving generics, verify:

- [ ] **No raw types** — `List` without `<User>`, `Map` without `<K,V>`
- [ ] **No unchecked warnings** suppressed without explanation
- [ ] **Arrays replaced with `List<E>`** where appropriate (especially for public APIs)
- [ ] **Generic classes used** for reusable components (repositories, services, DTOs)
- [ ] **Generic methods** for static utilities
- [ ] **PECS rule followed** — `extends` for producers, `super` for consumers
- [ ] **@SafeVarargs** only used when truly safe (just forwarding varargs)
- [ ] **Class<T> tokens** used for heterogeneous containers
- [ ] **Diamond operator** used to reduce redundancy
- [ ] **Generic type bounds** appropriate for the use case

### Quick Code Review Questions

1. **Is this class/type parameterizable?** If it holds objects, make it generic.
2. **Does this method need to be generic?** If it operates on typed parameters, probably yes.
3. **Should this use wildcards?** Check: is it a producer (read-only) or consumer (write-only)?
4. **Is there an unchecked warning?** If yes, either fix the design or document why it's safe.
5. **Is `Class<T>` being used?** For heterogeneous types, this is the pattern.

---

## Summary

| Pattern | When to Use | Red Flag |
|---------|-------------|----------|
| Raw types | Legacy interop only | New code with `List` |
| Generic class | Any class holding objects | Duplicated code for each type |
| Generic method | Static utilities, operations on types | Using Object + casts |
| `? extends` | Reading from collection | Adding to collection |
| `? super` | Writing to collection | Only reading |
| `@SafeVarargs` | Forwarding to safe method | Storing varargs array |
| `Class<T>` | Heterogeneous container | Raw casts to T |
