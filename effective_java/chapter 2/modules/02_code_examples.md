# Module 2: Code Examples

## Chapter 2: Creating and Destroying Objects

This module provides concrete code examples showing bad patterns and their corrections, tailored for Spring Boot microservices.

---

## Item 1 — Static Factory Methods

### Bad — Using constructors without clear naming

```java
// BAD: What does "1" mean? Is this seconds, milliseconds?
public class RateLimiter {
    private final int maxRequests;
    private final int timeWindow;

    public RateLimiter(int maxRequests, int timeWindow) {
        this.maxRequests = maxRequests;
        this.timeWindow = timeWindow;
    }
}

// Usage - confusing!
RateLimiter limiter = new RateLimiter(100, 60);
```

### Good — Using static factory methods with descriptive names

```java
// GOOD: Clear intent through naming
public class RateLimiter {
    private final int maxRequests;
    private final int timeUnitSeconds;

    // Private constructor - not for direct instantiation
    private RateLimiter(int maxRequests, int timeUnitSeconds) {
        this.maxRequests = maxRequests;
        this.timeUnitSeconds = timeUnitSeconds;
    }

    // Static factory methods with clear names
    public static RateLimiter perSecond(int maxRequests) {
        return new RateLimiter(maxRequests, 1);
    }

    public static RateLimiter perMinute(int maxRequests) {
        return new RateLimiter(maxRequests, 60);
    }

    public static RateLimiter perHour(int maxRequests) {
        return new RateLimiter(maxRequests, 3600);
    }
}

// Usage - self-documenting!
RateLimiter limiter = RateLimiter.perMinute(100);
RateLimiter strict = RateLimiter.perSecond(5);
```

---

## Item 2 — Builder Pattern

### Bad — Telescoping constructor (anti-pattern)

```java
// BAD: Hard to read, error-prone (which param is which?)
public class User {
    private final String id;
    private final String email;
    private final String firstName;
    private final String lastName;
    private final String phone;
    private final String address;
    private final boolean active;
    private final int age;
    private final List<String> roles;

    public User(String id, String email) {
        this(id, email, null, null, null, null, true, 0, Collections.emptyList());
    }

    public User(String id, String email, String firstName, String lastName) {
        this(id, email, firstName, lastName, null, null, true, 0, Collections.emptyList());
    }

    // ... 6 more constructors! Nightmarish
    public User(String id, String email, String firstName, String lastName,
                String phone, String address, boolean active, int age, List<String> roles) {
        this.id = id;
        this.email = email;
        this.firstName = firstName;
        this.lastName = lastName;
        this.phone = phone;
        this.address = address;
        this.active = active;
        this.age = age;
        this.roles = roles;
    }
}

// Usage - which constructor to use?
User user = new User("123", "john@example.com", "John", "Doe", null, null, true, 30, List.of("USER"));
```

### Good — Using Builder pattern

```java
// GOOD: Clear, fluent, type-safe construction
public class User {
    private final String id;
    private final String email;
    private final String firstName;
    private final String lastName;
    private final String phone;
    private final String address;
    private final boolean active;
    private final int age;
    private final List<String> roles;

    // Private constructor - only Builder can instantiate
    private User(Builder builder) {
        this.id = builder.id;
        this.email = builder.email;
        this.firstName = builder.firstName;
        this.lastName = builder.lastName;
        this.phone = builder.phone;
        this.address = builder.address;
        this.active = builder.active;
        this.age = builder.age;
        this.roles = builder.roles;
    }

    // Getters (no setters - immutable)
    public String getId() { return id; }
    public String getEmail() { return email; }
    // ... other getters

    // Static builder method
    public static Builder builder() {
        return new Builder();
    }

    public static class Builder {
        // Required fields
        private final String id;
        private final String email;

        // Optional fields - with sensible defaults
        private String firstName = null;
        private String lastName = null;
        private String phone = null;
        private String address = null;
        private boolean active = true;
        private int age = 0;
        private List<String> roles = Collections.emptyList();

        public Builder(String id, String email) {
            this.id = Objects.requireNonNull(id);
            this.email = Objects.requireNonNull(email);
        }

        public Builder firstName(String firstName) {
            this.firstName = firstName;
            return this;
        }

        public Builder lastName(String lastName) {
            this.lastName = lastName;
            return this;
        }

        // ... other fluent setters

        public User build() {
            return new User(this);
        }
    }
}

// Usage - crystal clear!
User user = User.builder("123", "john@example.com")
    .firstName("John")
    .lastName("Doe")
    .age(30)
    .roles(List.of("USER", "ADMIN"))
    .build();
```

### Modern Java 16+ — Use Records instead

```java
// Modern approach: Records for simple DTOs (Java 16+)
public record User(
    String id,
    String email,
    String firstName,
    String lastName,
    String phone,
    String address,
    boolean active,
    int age,
    List<String> roles
) {
    // Compact constructor for validation
    public User {
        Objects.requireNonNull(id, "id cannot be null");
        Objects.requireNonNull(email, "email cannot be null");
        roles = List.copyOf(roles); // Defensive copy
    }

    // Static factory method
    public static User create(String id, String email) {
        return new User(id, email, null, null, null, null, true, 0, List.of());
    }
}

// Usage - named parameters with Java 16+
User user = new User(
    "123",
    "john@example.com",
    "John",
    "Doe",
    null,
    null,
    true,
    30,
    List.of("USER")
);
```

---

## Item 3 — Singleton Pattern

### Bad — Synchronized method (slow)

```java
// BAD: Unnecessarily slow due to synchronization
public class PaymentService {
    private static PaymentService instance;

    private PaymentService() {}

    // Every call acquires lock - performance killer
    public static synchronized PaymentService getInstance() {
        if (instance == null) {
            instance = new PaymentService();
        }
        return instance;
    }
}
```

### Good — Enum singleton (recommended)

```java
// RECOMMENDED: Simple, thread-safe, serialization-safe
public enum PaymentService {
    INSTANCE;

    private final PaymentGateway gateway;

    PaymentService() {
        // Initialize expensive resources
        this.gateway = new StripeGateway();
    }

    public void processPayment(Order order) {
        gateway.charge(order.getAmount(), order.getCurrency());
    }
}

// Usage
PaymentService.INSTANCE.processPayment(order);
```

### Good — Bill Pugh Singleton (with Spring)

```java
// GOOD: For Spring-managed beans, use Spring's mechanisms
@Service
@Scope(value = ConfigurableBeanFactory.SCOPE_SINGLETON)  // This is default!
public class OrderService {

    // Spring creates ONE instance, injects it everywhere needed
    private final PaymentService paymentService;

    @Autowired
    public OrderService(PaymentService paymentService) {
        this.paymentService = paymentService;
    }
}
```

---

## Item 4 — Noninstantiable Utility Class

### Bad — Missing private constructor

```java
// BAD: Can be accidentally instantiated
public class StringUtils {
    // Compiler generates public constructor!

    public static boolean isBlank(String str) {
        return str == null || str.trim().isEmpty();
    }
}
```

### Good — Private constructor

```java
// RECOMMENDED: Cannot be instantiated
public final class StringUtils {

    // Private constructor prevents instantiation
    private StringUtils() {
        throw new AssertionError("Cannot instantiate utility class");
    }

    public static boolean isBlank(String str) {
        return str == null || str.trim().isEmpty();
    }

    public static boolean isNotBlank(String str) {
        return !isBlank(str);
    }
}
```

---

## Item 5 — Dependency Injection

### Bad — Hardwired resources (anti-pattern in Spring)

```java
// BAD: Tightly coupled, impossible to test
@Service
public class OrderService {
    // Creating dependencies inside the class!
    private final PaymentService paymentService = new PaymentService();
    private final NotificationService notificationService = new NotificationService();

    public void placeOrder(Order order) {
        paymentService.charge(order.getAmount());
        notificationService.sendConfirmation(order.getCustomerEmail());
    }
}
```

### Good — Constructor injection (recommended for Spring)

```java
// GOOD: Dependencies injected from outside
@Service
public class OrderService {
    private final PaymentService paymentService;
    private final NotificationService notificationService;

    // Constructor injection - Spring handles creation
    @Autowired
    public OrderService(PaymentService paymentService,
                        NotificationService notificationService) {
        this.paymentService = paymentService;
        this.notificationService = notificationService;
    }

    public void placeOrder(Order order) {
        paymentService.charge(order.getAmount());
        notificationService.sendConfirmation(order.getCustomerEmail());
    }
}
```

### Modern — Lombok reduces boilerplate

```java
// Modern Spring: Use @RequiredArgsConstructor
@Service
@RequiredArgsConstructor  // Lombok generates constructor
public class OrderService {
    private final PaymentService paymentService;
    private final NotificationService notificationService;

    public void placeOrder(Order order) {
        paymentService.charge(order.getAmount());
        notificationService.sendConfirmation(order.getCustomerEmail());
    }
}
```

---

## Item 6 — Avoid Creating Unnecessary Objects

### Bad — Creating objects in loops

```java
// BAD: Creates 10,000 String objects!
public String buildLogMessage(List<String> parts) {
    String result = "";
    for (String part : parts) {
        result = result + part + ", ";  // New String each iteration!
    }
    return result;
}

// BAD: Autoboxing in loop
public int sumIntegers(List<Integer> numbers) {
    int sum = 0;
    for (Integer num : numbers) {  // Autoboxing each iteration!
        sum += num;
    }
    return sum;
}
```

### Good — Reuse and avoid boxing

```java
// GOOD: StringBuilder for concatenation
public String buildLogMessage(List<String> parts) {
    StringBuilder sb = new StringBuilder();
    for (String part : parts) {
        sb.append(part).append(", ");
    }
    return sb.toString();
}

// GOOD: Use primitive int
public int sumIntegers(List<Integer> numbers) {
    int sum = 0;
    for (int i = 0; i < numbers.size(); i++) {
        sum += numbers.get(i);  // Unboxing once per iteration
    }
    return sum;
}

// BETTER: Stream with primitives
public int sumIntegers(List<Integer> numbers) {
    return numbers.stream()
        .mapToInt(Integer::intValue)  // Primitive stream
        .sum();
}
```

### Good — Static factory methods for immutability

```java
// GOOD: Reuse immutable objects via static factory
public class CacheService {
    // Reuse Boolean.TRUE and Boolean.FALSE
    public Boolean getCachedValue(String key) {
        return Boolean.TRUE;  // Don't use "new Boolean(true)"
    }

    // Prefer List.of() to new ArrayList<>()
    public List<String> getDefaultRoles() {
        return List.of("USER");  // Immutable, no allocation
    }
}
```

---

## Item 7 — Eliminate Obsolete References

### Bad — Memory leak in stack implementation

```java
// BAD: Pop doesn't null out references
public class Stack<T> {
    private Object[] elements;
    private int size = 0;

    public void push(T elem) {
        ensureCapacity();
        elements[size++] = elem;
    }

    public T pop() {
        if (size == 0) throw new EmptyStackException();
        return (T) elements[--size];  // Reference still held in array!
    }

    private void ensureCapacity() {
        if (elements.length == size) {
            elements = Arrays.copyOf(elements, 2 * size + 1);
        }
    }
}
```

### Good — Null out obsolete references

```java
// GOOD: Clear references when popped
public class Stack<T> {
    private Object[] elements;
    private int size = 0;

    public void push(T elem) {
        ensureCapacity();
        elements[size++] = elem;
    }

    public T pop() {
        if (size == 0) throw new EmptyStackException();
        T result = (T) elements[--size];
        elements[size] = null;  // Allow GC!
        return result;
    }
}
```

### Good — WeakHashMap for caches

```java
// GOOD: Use WeakHashMap for cache that doesn't prevent GC
public class UserCache {
    private final Map<String, User> cache = new WeakHashMap<>();

    public User getUser(String userId) {
        return cache.computeIfAbsent(userId, this::loadUser);
    }

    private User loadUser(String userId) {
        // Expensive database call
        return userRepository.findById(userId);
    }
}
```

---

## Item 8 — Avoid Finalizers

### Bad — Using finalizer for cleanup

```java
// BAD: Finalizers are unreliable
public class DatabaseConnection implements Connection {
    private final String url;

    public DatabaseConnection(String url) {
        this.url = url;
        // Acquire expensive resource
    }

    // NEVER rely on this for cleanup!
    @Override
    protected void finalize() throws Throwable {
        try {
            // Close resource - but this may NEVER run!
            close();
        } finally {
            super.finalize();
        }
    }
}
```

### Good — Use try-with-resources

```java
// GOOD: Deterministic cleanup
public class DatabaseConnection implements AutoCloseable {
    private final String url;
    private boolean closed = false;

    public DatabaseConnection(String url) {
        this.url = url;
    }

    @Override
    public void close() {
        if (!closed) {
            // Actually close the connection
            closed = true;
        }
    }
}

// Usage - guaranteed cleanup
try (DatabaseConnection conn = new DatabaseConnection(url)) {
    conn.executeQuery("SELECT * FROM users");
} // Automatically closed
```

### Good — Spring's @PreDestroy

```java
// GOOD: For Spring-managed beans
@Component
public class MyService implements DisposableBean {
    private final Connection connection;

    @PostConstruct
    public void init() {
        // Initialize expensive resource
        connection = createConnection();
    }

    @PreDestroy  // Called when bean is destroyed
    public void cleanup() {
        if (connection != null) {
            connection.close();
        }
    }
}
```

---

## Item 9 — try-with-resources

### Bad — try-finally (masking exceptions)

```java
// BAD: Exception in close() masks original exception
public String readFirstLine(String path) throws IOException {
    BufferedReader reader = new BufferedReader(new FileReader(path));
    try {
        return reader.readLine();
    } finally {
        reader.close();  // Can throw, masking original exception!
    }
}
```

### Good — try-with-resources

```java
// GOOD: Suppressed exceptions handled correctly
public String readFirstLine(String path) throws IOException {
    try (BufferedReader reader = new BufferedReader(new FileReader(path))) {
        return reader.readLine();
    } // Both close() and original exception preserved
}

// GOOD: Multiple resources
public void copyFiles(String src, String dest) throws IOException {
    try (
        FileInputStream in = new FileInputStream(src);
        FileOutputStream out = new FileOutputStream(dest)
    ) {
        byte[] buffer = new byte[8192];
        int bytesRead;
        while ((bytesRead = in.read(buffer)) != -1) {
            out.write(buffer, 0, bytesRead);
        }
    }
}
```

### Good — Spring's Resource interfaces are AutoCloseable

```java
// GOOD: RestTemplate is AutoCloseable (since Spring 5)
try (RestTemplate restTemplate = new RestTemplate()) {
    String result = restTemplate.getForObject(url, String.class);
} // Properly closed

// GOOD: Use @Slf4j with try-with-resources for logging
try (var ignored = new CloseableLogContext("Processing order {}", orderId)) {
    orderService.process(order);
}
```
