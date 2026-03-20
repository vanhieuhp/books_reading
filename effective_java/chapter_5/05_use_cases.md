# Chapter 5: Generics — Use Cases

> **Core Theme:** Ground each item in a real production system so developers see immediate applicability. Map to popular Java frameworks (Spring, Hibernate, Jackson) where natural.

---

## Use Case: Item 26 — API Response DTOs

### Scenario
Your microservice returns paginated results from multiple endpoints. You want type safety across the board.

### Problem without This Item
```java
// Raw type - no type safety in your API responses!
@Data
public class ApiResponse {
    private Object data;  // Raw type!
    private int status;
    private String message;
}

// Usage leads to casting everywhere:
ApiResponse response = apiService.getUsers();
List<User> users = (List<User>) response.getData();  // Unsafe cast!
// What if someone changes the backend to return something else?
```

### Solution
```java
// Type-safe generic response
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

    public static <T> ApiResponse<T> error(int status, String message) {
        ApiResponse<T> response = new ApiResponse<>();
        response.setStatus(status);
        response.setMessage(message);
        return response;
    }
}

// Usage - type-safe and clear:
ApiResponse<List<User>> response = apiService.getUsers();
List<User> users = response.getData();  // No cast! Compiler catches mismatches!

// Controller:
@GetMapping("/users")
public ResponseEntity<ApiResponse<List<UserDto>>> getUsers() {
    List<UserDto> users = userService.findAll();
    return ResponseEntity.ok(ApiResponse.success(users));
}
```

### Framework Mapping
- Spring's `ResponseEntity<T>` is a perfect example
- Jackson's `ObjectMapper.readValue(json, Class<T>)` uses `Class<T>` tokens

---

## Use Case: Item 29 + 30 — Generic Service Layer

### Scenario
Create a base service class that handles CRUD operations for any entity.

### Solution
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

    public List<T> findAll() {
        return getRepository().findAll();
    }

    public void delete(T entity) {
        getRepository().delete(entity);
    }
}

// Concrete service for Users:
@Service
public class UserService extends BaseService<User, Long> {

    @Autowired
    private UserRepository userRepository;

    @Override
    protected Repository<User, Long> getRepository() {
        return userRepository;
    }

    // User-specific methods
    public Optional<User> findByEmail(String email) {
        return userRepository.findByEmail(email);
    }
}

// Concrete service for Orders:
@Service
public class OrderService extends BaseService<Order, UUID> {
    // Similar implementation...
}
```

### Framework Mapping
This is exactly how Spring Data JPA works! `JpaRepository<T, ID>` is a generic interface.

---

## Use Case: Item 31 — Flexible Service Layer (PECS)

### Scenario
Your payment service needs to process different payment types (CreditCard, PayPal, BankTransfer) uniformly.

### Problem without Wildcards
```java
// Only accepts exact type - inflexible!
public class PaymentProcessor {
    public void processPayments(List<Payment> payments) {
        for (Payment p : payments) {
            p.process();
        }
    }
}

// Can't reuse for subtypes!
List<CreditCardPayment> cardPayments = getCardPayments();
processor.processPayments(cardPayments);  // COMPILE ERROR!
```

### Solution
```java
// Producer: reads payments, doesn't modify the list -> extends
public class PaymentProcessor {

    public void processPayments(List<? extends Payment> payments) {
        for (Payment p : payments) {  // Can read as Payment
            p.process();
        }
    }

    // Consumer: adds payments to a collection -> super
    public void collectPayments(List<? super CreditCardPayment> destination) {
        destination.add(new CreditCardPayment());
        destination.add(new CreditCardPayment());
    }
}

// Usage - flexible!
List<CreditCardPayment> cards = getCardPayments();
processor.processPayments(cards);  // OK!

List<Payment> allPayments = new ArrayList<>();
processor.collectPayments(allPayments);  // OK - adds CreditCardPayment to Payment list!
```

---

## Use Case: Item 33 — Dynamic Field Mapping

### Scenario
You need to build a dynamic mapper that converts database entities to DTOs based on field configuration.

### Solution
```java
@Component
public class DynamicMapper {

    // Using Class<?> as key with type-safe casting
    private final Map<Class<?>, Function<?, ?>> typeSafeMappers = new HashMap<>();

    @SuppressWarnings("unchecked")
    public <S, D> void register(Class<S> sourceClass,
                                 Class<D> destClass,
                                 Function<S, D> mapper) {
        typeSafeMappers.put(sourceClass, (Function<?, ?>) mapper);
    }

    @SuppressWarnings("unchecked")
    public <S, D> D map(S source, Class<D> destClass) {
        Function<S, D> mapper = (Function<S, D>) typeSafeMappers.get(source.getClass());
        if (mapper == null) {
            throw new IllegalArgumentException("No mapper registered for " + source.getClass());
        }
        return mapper.apply(source);
    }
}

// Usage:
dynamicMapper.register(UserEntity.class, UserDto.class, UserDto::fromEntity);
dynamicMapper.register(OrderEntity.class, OrderDto.class, OrderDto::fromEntity);

// Type-safe at runtime!
UserDto userDto = dynamicMapper.map(userEntity, UserDto.class);
OrderDto orderDto = dynamicMapper.map(orderEntity, OrderDto.class);
```

### Framework Mapping
- Spring's `ModelMapper` uses this pattern
- Jackson's `ObjectMapper` with `TypeReference` is similar

---

## Use Case: Item 28 + 32 — Safe Varargs Utilities

### Scenario
You're building utility methods that accept multiple elements for logging, caching, or configuration.

### Problem
Varargs with generics can cause heap pollution if not careful.

### Solution
```java
// Safe utility class
public final class CacheUtils {

    // Safe: just forwarding to another generic method
    @SafeVarargs
    public static <K, V> Map<K, V> mapOf(Map.Entry<K, V>... entries) {
        Map<K, V> map = new HashMap<>();
        for (Map.Entry<K, V> entry : entries) {
            map.put(entry.getKey(), entry.getValue());
        }
        return map;
    }

    // Alternative: accept List instead of varargs
    public static <K, V> Map<K, V> mapOf(List<Map.Entry<K, V>> entries) {
        Map<K, V> map = new HashMap<>();
        for (Map.Entry<K, V> entry : entries) {
            map.put(entry.getKey(), entry.getValue());
        }
        return map;
    }

    // Entry factory for type safety
    @SafeVarargs
    public static <K, V> Map.Entry<K, V> entry(K key, V... values) {
        if (values.length != 1) {
            throw new IllegalArgumentException("Exactly one value required");
        }
        return Map.entry(key, values[0]);
    }
}

// Usage:
Map<String, Integer> config = CacheUtils.mapOf(
    Map.entry("maxConnections", 100),
    Map.entry("timeout", 30)
);
```

---

## Use Case: Item 27 — Type-Safe JSON Parsing

### Scenario
You're building a JSON utility that parses JSON into Java objects, like a simplified Jackson.

### Solution
```java
public class JsonParser {

    // Uses Class<T> as type token
    public <T> T parse(String json, Class<T> clazz) {
        // Parse JSON to intermediate representation
        Map<String, Object> parsed = parseJsonToMap(json);

        // Convert to target type using Class.cast() for safety
        return convert(parsed, clazz);
    }

    private <T> T convert(Map<String, Object> map, Class<T> clazz) {
        if (clazz == String.class) {
            return clazz.cast(map.get("value").toString());
        } else if (clazz == Integer.class) {
            return clazz.cast(((Number) map.get("value")).intValue());
        } else if (clazz == List.class) {
            @SuppressWarnings("unchecked")
            T result = (T) map.get("value");
            return result;
        }
        // For complex objects, you'd use reflection or a proper parser
        throw new IllegalArgumentException("Unsupported type: " + clazz);
    }

    private Map<String, Object> parseJsonToMap(String json) {
        // Simplified - imagine this actually parses JSON
        return new HashMap<>();
    }
}

// Usage:
String json = "{\"name\": \"Alice\", \"age\": 30}";
User user = parser.parse(json, User.class);  // Type-safe!
```

---

## Use Case: Generic Repository with Specification Pattern

### Scenario
You need a flexible query system that can build dynamic queries, similar to Spring Data JPA Specifications.

### Solution
```java
// Generic specification interface
public interface Specification<T> {
    boolean isSatisfiedBy(T candidate);
}

// Generic repository with specification support
public class SpecificationRepository<T> {
    private final List<T> storage = new ArrayList<>();

    public void add(T item) {
        storage.add(item);
    }

    public List<T> findAll(Specification<T> spec) {
        return storage.stream()
            .filter(spec::isSatisfiedBy)
            .collect(Collectors.toList());
    }
}

// Concrete specifications
public class UserSpecifications {
    public static Specification<User> hasAgeGreaterThan(int minAge) {
        return user -> user.getAge() > minAge;
    }

    public static Specification<User> hasNameStartingWith(String prefix) {
        return user -> user.getName().startsWith(prefix);
    }

    public static Specification<User> isAdult() {
        return hasAgeGreaterThan(18);
    }
}

// Usage:
SpecificationRepository<User> repo = new SpecificationRepository<>();
repo.add(new User("Alice", 25));
repo.add(new User("Bob", 17));

List<User> adults = repo.findAll(UserSpecifications.isAdult());
List<User> olderThan21 = repo.findAll(UserSpecifications.hasAgeGreaterThan(21));
```

---

## Framework Reference Summary

| Pattern | Item | Spring/Hibernate Equivalent |
|---------|------|---------------------------|
| Generic Response DTO | 26 | `ResponseEntity<T>` |
| Generic Service | 29 | `JpaRepository<T, ID>` |
| Generic Methods | 30 | `Collections.sort()` |
| Bounded Wildcards | 31 | `List<? extends Entity>` |
| Safe Varargs | 32 | `Arrays.asList()` |
| Type Tokens | 33 | `ObjectMapper.readValue()` |
