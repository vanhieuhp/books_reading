# Chapter 5: Generics — Code Examples

> **Core Theme:** Show the pattern in action with real, production-like code — not toy examples. For every item: one bad example and one good example with inline comments explaining why.

---

## Item 26 — Raw Types

### ❌ Bad — Using raw type `List`:

```java
// Raw type loses type safety
public class UserService {
    // PROBLEM: List without type parameter - no compile-time safety
    private List users = new ArrayList();  // RAW TYPE - BAD!

    public void addUser(Object user) {
        users.add(user);  // Accepts ANY object!
    }

    public User getUser(int index) {
        // Cast required - throws ClassCastException at runtime if wrong type
        return (User) users.get(index);  // UNCHECKED CAST - DANGEROUS!
    }
}
```

### ✅ Good — Using parameterized `List<User>`:

```java
// Proper generic type - compile-time safety
public class UserService {
    // Type parameter provides safety at compile time
    private List<User> users = new ArrayList<>();  // DIAMOND OPERATOR

    public void addUser(User user) {
        users.add(user);  // Only accepts User - compile error otherwise!
    }

    public User getUser(int index) {
        return users.get(index);  // NO CAST NEEDED - already typed!
    }
}
```

---

## Item 27 — Unchecked Warnings

### ❌ Bad — Suppressing warning without understanding:

```java
// BAD: Blindly suppressing warnings hides bugs!
@SuppressWarnings("unchecked")
public <T> T parseValue(Object value, Class<T> type) {
    // This compiles but the warning exists for a reason
    return (T) value;  // UNCHECKED CAST - may fail at runtime!
}
```

### ✅ Good — Fixing the design to eliminate the warning:

```java
// GOOD: Proper generic method - no unchecked warnings
public <T> T parseValue(Object value, Class<T> type) {
    if (value == null) {
        return null;
    }

    // type.cast() is the correct way - no unchecked warning
    return type.cast(value);  // Safe runtime cast with Class<T>
}
```

---

## Item 28 — Lists vs Arrays

### ❌ Bad — Using generic arrays:

```java
// COMPILER ERROR: Generic array creation is forbidden!
// Why? Arrays are reifiable, generics are erased.
// This would violate type safety at runtime.

public class Favorites {
    // THIS DOESN'T COMPILE:
    private final Class<?>[] types = new Class<?>[]{};  // BAD!

    // Workaround using Object[] - but unsafe!
    private Object[] favoriteArray = new Object[10];  // UNSAFE!
}
```

### ✅ Good — Using lists instead:

```java
// Lists are generic-friendly - no array type safety issues
public class Favorites {
    // List is fully type-safe with generics
    private final Map<Class<?>, Object> favorites = new HashMap<>();

    public <T> void setFavorite(Class<T> type, T instance) {
        // Type-safe: only stores and retrieves correct types
        favorites.put(type, type.cast(instance));
    }

    public <T> T getFavorite(Class<T> type) {
        // No cast needed - already typed as T
        return type.cast(favorites.get(type));
    }
}
```

---

## Item 29 — Generic Types

### ❌ Bad — Non-generic stack using Object:

```java
// BEFORE: Non-generic stack - requires casting everywhere
public class Stack {
    private Object[] elements;
    private int size = 0;

    public void push(Object e) {
        elements[size++] = e;
    }

    public Object pop() {
        if (size == 0) throw new EmptyStackException();
        return elements[--size];  // Returns Object - caller must cast!
    }
}

// Usage:
Stack stack = new Stack();
stack.push("hello");
String s = (String) stack.pop();  // Required cast - unsafe!
stack.push(42);
Integer i = (Integer) stack.pop();  // Runtime error if you forget cast!
```

### ✅ Good — Generic stack:

```java
// AFTER: Type-safe generic stack
public class Stack<E> {
    private Object[] elements;  // Use Object[] to avoid generic array

    public Stack() {
        this.elements = new Object[16];  // Initial capacity
    }

    public void push(E e) {
        elements[size++] = e;  // Type-checked at compile time!
    }

    public E pop() {
        if (size == 0) throw new EmptyStackException();
        @SuppressWarnings("unchecked")
        E result = (E) elements[--size];  // Unchecked but safe - explained below
        return result;
    }

    public boolean isEmpty() {
        return size == 0;
    }
}

// Usage:
Stack<String> stringStack = new Stack<>();
stringStack.push("hello");
String s = stringStack.pop();  // No cast needed! Type-safe!
```

---

## Item 30 — Generic Methods

### ❌ Bad — Non-generic utility method:

```java
// BEFORE: Using Object and casting - error-prone
public class ObjectUtils {
    public static Object first(Object collection) {
        // Terrible: what if it's not a List?
        return ((List<?>) collection).get(0);  // All unsafe!
    }
}
```

### ✅ Good — Generic method:

```java
// AFTER: Proper generic method
public class CollectionUtils {

    // Generic method with bounded type parameter
    public static <T> T first(List<T> list) {
        if (list == null || list.isEmpty()) {
            throw new IllegalArgumentException("List cannot be null or empty");
        }
        return list.get(0);  // Already type T - no cast!
    }

    // Generic method with bounds - works with any Comparable
    public static <T extends Comparable<T>> T min(List<T> list) {
        if (list == null || list.isEmpty()) {
            throw new IllegalArgumentException("List cannot be null or empty");
        }

        T minimum = list.get(0);
        for (T element : list) {
            if (element.compareTo(minimum) < 0) {
                minimum = element;
            }
        }
        return minimum;
    }
}

// Usage - type inference makes it clean:
List<String> names = Arrays.asList("Alice", "Bob", "Charlie");
String first = CollectionUtils.first(names);  // Type inferred as String
```

---

## Item 31 — Bounded Wildcards (PECS)

### ❌ Bad — Using exact types limits flexibility:

```java
// BEFORE: Inflexible API - can only accept exact type
public class Inventory {
    // Only accepts List<Product>, not List<Electronics> or List<Clothing>
    public void addProducts(List<Product> products) {
        for (Product p : products) {
            p.getName();
        }
    }
}

// This won't compile! List<Electronics> is not List<Product>
// inventory.addProducts(electronicsProducts);
```

### ✅ Good — Using wildcards for flexibility:

```java
// AFTER: Flexible API using PECS
public class Inventory {

    // Producer: reads from the list -> use ? extends Product
    public void processProducts(List<? extends Product> products) {
        for (Product p : products) {  // Can read as Product
            p.getName();  // Product methods work
            // p.setPrice(100);  // ERROR: Can't write! Don't know exact type
        }
    }

    // Consumer: writes to the list -> use ? super Product
    public void addProducts(List<? super Electronics> destination) {
        // Can add Electronics or subtypes to any supertype list
        destination.add(new Laptop());  // OK: Laptop extends Electronics
        destination.add(new Phone());   // OK: Phone extends Electronics

        // Reading as Object is safe but loses type info
        Object obj = destination.get(0);  // OK but not useful
    }
}

// Usage - now flexible!
List<Electronics> electronics = new ArrayList<>();
List<Clothing> clothing = new ArrayList<>();

Inventory inventory = new Inventory();
inventory.processProducts(electronics);  // OK: List<Electronics> extends List<? extends Product>
inventory.processProducts(clothing);    // OK: List<Clothing> extends List<? extends Product>
```

---

## Item 32 — Generics + Varargs

### ❌ Bad — Unsafe varargs with generics:

```java
// DANGEROUS: Generic varargs can cause heap pollution
public class DangerousUtils {
    // This generates unchecked warning - and for good reason!
    @SafeVarargs  // WRONG to use here - method is NOT safe!
    public static <T> void dangerous(T... elements) {
        Object[] array = elements;  // Heap pollution: T[] is really Object[]
        array[0] = "not an integer";  // Overwrites the "Integer" element!
    }
}

// What happens:
List<Integer> intList = new ArrayList<>();
dangerous(intList);  // Compiles but can corrupt your list!
```

### ✅ Good — Safe varargs pattern:

```java
// SAFE: When varargs are just for passing to other generic methods
public class SafeUtils {

    // Safe: we're just forwarding the varargs to another generic method
    @SafeVarargs
    public static <T> List<T> listOf(T... elements) {
        // Arrays.asList is already annotated @SafeVarargs in the JDK
        return Arrays.asList(elements);
    }

    // Alternative without @SafeVarargs - just use List directly
    @SafeVarargs
    public static <T> List<T> immutableListOf(T... elements) {
        return List.of(elements);  // Java 9+ immutable list
    }
}

// Even safer: just accept List instead of varargs when possible
public static <T> List<T> safeListOf(List<T> elements) {
    return new ArrayList<>(elements);  // No varargs, no problem
}
```

---

## Item 33 — Typesafe Heterogeneous Containers

### ❌ Bad — Unsafe heterogeneous container:

```java
// UNSAFE: No type guarantees - ClassCastException at runtime
public class UnsafeFavorites {
    private final Map<Class<?>, Object> favorites = new HashMap<>();

    public <T> void set(Class<T> type, T instance) {
        favorites.put(type, instance);  // Stores as Object - type info lost!
    }

    public <T> T get(Class<T> type) {
        // DANGEROUS: Cast without runtime check!
        return (T) favorites.get(type);  // Unchecked cast!
    }
}

// What can go wrong:
UnsafeFavorites f = new UnsafeFavorites();
f.set(String.class, "hello");
f.set(Integer.class, 42);

// Bug: type mismatch not caught until runtime!
Integer number = f.get(Integer.class);  // OK
String text = f.get(Integer.class);     // ClassCastException! But only at runtime!
```

### ✅ Good — Typesafe heterogeneous container:

```java
// SAFE: Using Class.cast() for runtime type checking
public class TypesafeFavorites {
    private final Map<Class<?>, Object> favorites = new HashMap<>();

    public <T> void set(Class<T> type, T instance) {
        // Class.cast() provides runtime type checking
        favorites.put(type, type.cast(instance));
    }

    public <T> T get(Class<T> type) {
        // Class.cast() is safe: throws if type doesn't match
        return type.cast(favorites.get(type));
    }
}

// Usage:
TypesafeFavorites f = new TypesafeFavorites();
f.set(String.class, "hello");
f.set(Integer.class, 42);

// Now this is caught at compile time!
String s = f.get(String.class);   // OK: returns String
Integer i = f.get(Integer.class); // OK: returns Integer

// COMPILE ERROR: Type mismatch caught at compile time!
String bad = f.get(Integer.class);  // Compile error!
```

---

## Spring Boot Examples

### Generic Service Layer (Item 29)

```java
// Base generic service - reusable for any entity type!
public abstract class BaseService<T, ID> {

    protected abstract Repository<T, ID> getRepository();

    public T save(T entity) {
        return getRepository().save(entity);
    }

    public Optional<T> findById(ID id) {
        return getRepository().findById(id);
    }
}

// Concrete service for Users:
@Service
public class UserService extends BaseService<User, Long> {

    @Override
    protected Repository<User, Long> getRepository() {
        return userRepository;
    }
}
```

### Generic API Response (Item 26 + 29)

```java
@Data
public class ApiResponse<T> {
    private T data;
    private int status;
    private String message;

    public static <T> ApiResponse<T> success(T data) {
        ApiResponse<T> response = new ApiResponse<>();
        response.setData(data);
        response.setStatus(200);
        return response;
    }
}

// Controller:
@GetMapping("/users")
public ResponseEntity<ApiResponse<List<UserDto>>> getUsers() {
    List<UserDto> users = userService.findAll();
    return ResponseEntity.ok(ApiResponse.success(users));
}
```
