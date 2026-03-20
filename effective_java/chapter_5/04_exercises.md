# Chapter 5: Generics — Exercises

> **Core Theme:** Force active recall and hands-on coding. Each exercise has: Problem statement, Starter code, Expected outcome. Exercise types: Refactoring, Design, Debug.

---

## Exercise 1 — Fix the Raw Type Bug [Beginner]

### Problem
This Spring service has a bug caused by raw types. Find and fix it.

### Starter Code
```java
@Service
public class OrderService {

    private List orders = new ArrayList();  // BUG HERE

    public void addOrder(Object order) {
        orders.add(order);
    }

    public Order getOrder(int index) {
        return (Order) orders.get(index);
    }
}

// In a controller somewhere:
orderService.addOrder(new Order());
orderService.addOrder("not an order");  // BUG: This shouldn't compile!
```

### What You Need to Do
1. Fix the raw type usage
2. Explain why the current code is dangerous

### Expected Outcome
Code should not compile when trying to add a non-Order object.

---

## Exercise 2 — Design a Generic Repository [Intermediate]

### Problem
Create a simple in-memory repository that works with any entity type, similar to Spring Data JPA.

### Starter Code
```java
// TODO: Make this generic so it works with any entity type
public class InMemoryRepository {
    private Map<Long, Object> storage = new HashMap<>();
    private Long idCounter = 1L;

    public Object save(Object entity) {
        Long id = idCounter++;
        storage.put(id, entity);
        return entity;
    }

    public Object findById(Long id) {
        return storage.get(id);
    }

    public List<Object> findAll() {
        return new ArrayList<>(storage.values());
    }
}
```

### What You Need to Do
1. Add proper type parameters to make it type-safe
2. Ensure `save()` returns the saved entity with its ID
3. Make `findById()` return `Optional<T>` (like Spring Data)

### Expected Outcome
```java
InMemoryRepository<User, Long> userRepo = new InMemoryRepository<>();
User saved = userRepo.save(new User("Alice"));
User found = userRepo.findById(1L).get();  // No casts!
```

---

## Exercise 3 — Debug the Wildcard Error [Intermediate]

### Problem
This code doesn't compile. Fix it using proper wildcard types.

### Starter Code
```java
@Service
public class ReportGenerator {

    public void generateReport(List<SalesData> salesData) {
        // Process sales data...
    }

    public void generateReport(List<MarketingData> marketingData) {
        // Process marketing data...
    }
}

// Controller:
@RestController
public class ReportController {

    @Autowired
    private ReportGenerator generator;

    @GetMapping("/report/sales")
    public void salesReport(List<SalesData> data) {
        generator.generateReport(data);  // Works
    }

    @GetMapping("/report/marketing")
    public void marketingReport(List<MarketingData> data) {
        generator.generateReport(data);  // Works
    }

    // New requirement - unified endpoint:
    @GetMapping("/report/all")
    public void allReports(List<?> data) {
        // Can't pass to generator! How to fix?
        generator.generateReport(data);  // COMPILE ERROR
    }
}
```

### What You Need to Do
1. Modify `ReportGenerator` to accept any type of data
2. Use bounded wildcards appropriately
3. Consider: should the method read from or write to the list?

### Expected Outcome
The `/report/all` endpoint should work for both `SalesData` and `MarketingData`.

---

## Exercise 4 — Create a Typesafe Event Bus [Advanced]

### Problem
Spring's `ApplicationEventPublisher` is great, but what if you want type-safe event handling without casting?

### Starter Code
```java
// TODO: Create a type-safe event bus
public class EventBus {
    private Map<Class<?>, List<Object>> handlers = new HashMap<>();

    public <T> void registerHandler(Class<T> eventType, Consumer<T> handler) {
        // Store the handler
    }

    public <T> void publish(T event) {
        // Find and invoke handlers for this event type
    }
}
```

### What You Need to Do
1. Implement the registry using `Class<T>` as a type token
2. Implement `publish()` to dispatch events to the correct handlers
3. Handle the case where no handler is registered
4. **Bonus:** Add support for wildcard handlers (e.g., handle all `UserEvent` subtypes)

### Expected Outcome
```java
EventBus bus = new EventBus();

bus.registerHandler(UserCreatedEvent.class, event ->
    System.out.println("User created: " + event.getUsername()));

bus.registerHandler(OrderPlacedEvent.class, event ->
    System.out.println("Order placed: " + event.getOrderId()));

// Publishing dispatches to correct handlers
bus.publish(new UserCreatedEvent("alice"));
bus.publish(new OrderPlacedEvent(12345L));
```

---

## Exercise 5 — Fix the Generic Method [Beginner]

### Problem
This utility method has an unchecked warning. Fix it properly.

### Starter Code
```java
public class JsonUtils {

    // This generates an unchecked warning - fix it!
    @SuppressWarnings("unchecked")
    public static <T> T fromJson(String json, Class<T> clazz) {
        // Simplified JSON parsing - imagine this calls Jackson
        // PROBLEM: We're casting without type checking!
        return (T) parseToObject(json);  // UNSAFE!
    }

    private static Object parseToObject(String json) {
        // Placeholder - returns some parsed object
        return new Object();
    }
}
```

### What You Need to Do
1. Fix the unsafe cast using `Class.cast()`
2. Add proper null handling
3. Make the method safer for edge cases

### Expected Outcome
No unchecked warnings, and the method should throw a proper exception if types don't match at runtime (not a cryptic `ClassCastException`).

---

## Exercise 6 — PECS Refactoring [Intermediate]

### Problem
Refactor this method to use proper wildcards based on its usage pattern.

### Starter Code
```java
public class DataProcessor {

    // TODO: What kind of wildcard should this use?
    // The method only READS from the collection to calculate statistics
    public double calculateAverage(List<Number> numbers) {
        if (numbers.isEmpty()) return 0.0;

        double sum = 0.0;
        for (Number n : numbers) {
            sum += n.doubleValue();
        }
        return sum / numbers.size();
    }
}

// Usage:
List<Integer> integers = Arrays.asList(1, 2, 3);
List<Double> doubles = Arrays.asList(1.0, 2.0, 3.0);

processor.calculateAverage(integers);  // COMPILE ERROR!
processor.calculateAverage(doubles);   // COMPILE ERROR!
```

### What You Need to Do
1. Determine the correct wildcard based on whether the method is a producer or consumer
2. Apply PECS rule
3. Verify it works with both `List<Integer>` and `List<Double>`

### Expected Outcome
```java
// Both should compile now:
processor.calculateAverage(integers);  // OK
processor.calculateAverage(doubles);   // OK
```

---

## Exercise 7 — Generic Builder [Advanced]

### Problem
Create a type-safe builder pattern that works with generics.

### Starter Code
```java
// TODO: Make this builder type-safe
public class Builder {
    private Map<String, Object> properties = new HashMap<>();

    public Builder set(String key, Object value) {
        properties.put(key, value);
        return this;
    }

    public Object build() {
        return properties;
    }
}

// Current usage - no type safety:
Builder b = new Builder();
b.set("name", "Alice")
 .set("age", 30)
 .set("active", true);

// When building, we lose all type information!
String name = (String) b.build().get("name");  // Unsafe cast!
```

### What You Need to Do
1. Create a generic builder that maintains type safety
2. The builder should enforce that "name" is always a String
3. The builder should enforce that "age" is always an Integer

### Expected Outcome
```java
// Type-safe builder:
UserBuilder b = new UserBuilder();
b.name("Alice").age(30).active(true);
User user = b.build();  // Returns fully-typed User object!
```

---

## Answer Key (Mini)

### Exercise 1
```java
private List<Order> orders = new ArrayList<>();
public void addOrder(Order order) { ... }
```

### Exercise 2
```java
public class InMemoryRepository<T, ID> {
    private Map<ID, T> storage = new HashMap<>();
    // ...
}
```

### Exercise 3
Use `List<? extends ReportData>` in the method signature.

### Exercise 5
```java
return clazz.cast(parseToObject(json));
```

### Exercise 6
Use `List<? extends Number>` (producer: only reads).

### Exercise 7
Use a typed interface: `UserBuilder name(String name)`, `UserBuilder age(Integer age)`.
