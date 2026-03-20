# Module 5: Use Cases

## Chapter 2: Creating and Destroying Objects

This module grounds each item in real-world Spring Boot microservice scenarios. These are the patterns you'll encounter daily in production codebases.

---

## Use Case: Item 1 in Payment Gateway Service

### Scenario

You're building a payment gateway microservice that needs to handle different payment methods (credit card, PayPal, bank transfer). Each payment method has different validation and processing logic.

### Problem without Static Factory

```java
// Without static factory - confusing constructor usage
PaymentProcessor cardProcessor = new PaymentProcessor(PaymentType.CREDIT_CARD, true);
PaymentProcessor paypalProcessor = new PaymentProcessor(PaymentType.PAYPAL, false);
PaymentProcessor bankProcessor = new PaymentProcessor(PaymentType.BANK_TRANSFER, true);

// What do the boolean parameters mean?!?
```

### Solution with Static Factory

```java
public class PaymentProcessor {
    private final PaymentType type;
    private final boolean supportsRefund;
    private final Map<String, Object> config;

    // Private constructor - use factories
    private PaymentProcessor(PaymentType type, boolean supportsRefund, Map<String, Object> config) {
        this.type = type;
        this.supportsRefund = supportsRefund;
        this.config = config;
    }

    // Static factories with clear names
    public static PaymentProcessor forCreditCard() {
        return new PaymentProcessor(
            PaymentType.CREDIT_CARD,
            true,
            Map.of("gateway", "stripe", "timeout", 30)
        );
    }

    public static PaymentProcessor forPayPal() {
        return new PaymentProcessor(
            PaymentType.PAYPAL,
            false,
            Map.of("gateway", "paypal", "timeout", 60)
        );
    }

    public static PaymentProcessor forBankTransfer() {
        return new PaymentProcessor(
            PaymentType.BANK_TRANSFER,
            true,
            Map.of("gateway", "swift", "timeout", 120)
        );
    }
}

// Usage - crystal clear!
PaymentProcessor card = PaymentProcessor.forCreditCard();
PaymentProcessor paypal = PaymentProcessor.forPayPal();
```

### Framework Mapping

- **Spring Integration:** Use `@ConfigurationProperties` to bind configuration to factory methods
- **Strategy Pattern:** Static factories often return different strategy implementations

---

## Use Case: Item 2 in Order Service DTO

### Scenario

You're building an e-commerce order service with complex order objects that have many optional fields: billing address, shipping address, discount codes, gift messages, etc.

### Problem without Builder

```java
// Telescoping constructor nightmare
Order order = new Order(
    "order-123",           // id
    "customer-456",        // customerId
    List.of(item1, item2), // items
    new BigDecimal("99.99"), // subtotal
    new BigDecimal("10.00"), // discount
    new BigDecimal("89.99"), // total
    "USD",                  // currency
    "John",                 // billingFirstName
    "Doe",                  // billingLastName
    "123 Main St",          // billingAddress1
    null,                   // billingAddress2
    "NYC",                  // billingCity
    "NY",                   // billingState
    "10001",                // billingZip
    "USA",                  // billingCountry
    "John",                 // shippingFirstName
    "Doe",                  // shippingLastName
    "123 Main St",          // shippingAddress1
    null,                   // shippingAddress2
    "NYC",                  // shippingCity
    "NY",                   // shippingState
    "10001",                // shippingZip
    "USA",                  // shippingCountry
    "Leave at door",        // deliveryInstructions
    "gift",                 // orderType
    null,                   // giftMessage
    null                    // couponCode
);
```

### Solution with Builder

```java
// Clean, readable, type-safe
Order order = Order.builder()
    .id("order-123")
    .customerId("customer-456")
    .items(List.of(item1, item2))
    .subtotal(new BigDecimal("99.99"))
    .discount(new BigDecimal("10.00"))
    .currency("USD")
    .billingAddress(Address.builder()
        .firstName("John")
        .lastName("Doe")
        .street1("123 Main St")
        .city("NYC")
        .state("NY")
        .zip("10001")
        .country("USA")
        .build())
    .shippingAddress(Address.builder()
        .firstName("John")
        .lastName("Doe")
        .street1("123 Main St")
        .city("NYC")
        .state("NY")
        .zip("10001")
        .country("USA")
        .build())
    .deliveryInstructions("Leave at door")
    .orderType(OrderType.GIFT)
    .giftMessage("Happy Birthday!")
    .build();
```

### Framework Mapping

- **Lombok:** Use `@Builder` annotation (reduces boilerplate)
- **Jackson:** Builder pattern works well with JSON serialization
- **Records (Java 16+):** Consider records for simpler DTOs

---

## Use Case: Item 3 in Configuration Service

### Scenario

You need a singleton configuration service that loads application configuration once and makes it available everywhere.

### Problem without Proper Singleton

```java
// Spring @Component without singleton consideration
@Component
public class ConfigService {
    private Map<String, String> config;

    @PostConstruct
    public void init() {
        // Loads from database - runs for EVERY bean instance!
        this.config = loadConfigFromDatabase();
    }
}

// If someone does this, you get multiple instances with multiple DB calls!
ConfigService service1 = context.getBean(ConfigService.class);
ConfigService service2 = context.getBean(ConfigService.class);
// service1 != service2 in rare edge cases
```

### Solution with Enum Singleton

```java
// Simple, thread-safe, serialization-safe
public enum ConfigService {
    INSTANCE;

    private Map<String, String> config;

    ConfigService() {
        // Load configuration once
        this.config = loadConfigFromDatabase();
    }

    private Map<String, String> loadConfigFromDatabase() {
        // Expensive initialization
        return Map.of(
            "max.retries", "3",
            "timeout.seconds", "30",
            "feature.enabled", "true"
        );
    }

    public String getConfig(String key) {
        return config.get(key);
    }
}

// Usage
String timeout = ConfigService.INSTANCE.getConfig("timeout.seconds");
```

### Spring Way

```java
// Modern Spring - let Spring handle singleton
@Service
public class ConfigService {
    private final Map<String, String> config;

    @Autowired
    public ConfigService(@Value("${app.config.*}") Map<String, String> config) {
        this.config = config;
    }

    public String getConfig(String key) {
        return config.get(key);
    }
}
```

---

## Use Case: Item 4 in Utility Classes

### Scenario

You have utility classes for string manipulation, date formatting, and collection utilities that shouldn't be instantiated.

### Problem without Private Constructor

```java
// Can be accidentally instantiated - wastes memory
StringUtils utils = new StringUtils();
DateUtils dates = new DateUtils();
```

### Solution with Private Constructor

```java
// Cannot be instantiated
public final class StringUtils {

    private StringUtils() {
        throw new AssertionError("Utility class - do not instantiate");
    }

    public static boolean isBlank(String str) {
        return str == null || str.trim().isEmpty();
    }

    public static String capitalize(String str) {
        if (isBlank(str)) return str;
        return str.substring(0, 1).toUpperCase() + str.substring(1);
    }
}

// Spring's Collections utility class works the same way
List<String> unmodifiable = Collections.unmodifiableList(original);
// Collections has private constructor!
```

---

## Use Case: Item 5 in Spring Boot Service

### Scenario

A service that depends on multiple external services (payment, notification, shipping) needs to be testable.

### Problem with Hardwired Dependencies

```java
@Service
public class OrderService {
    // BAD: Can't swap for mocks in tests
    private StripePaymentService paymentService = new StripePaymentService();
    private EmailNotificationService notificationService = new EmailNotificationService();

    public void placeOrder(Order order) {
        // Test can't verify this interaction without real services
        paymentService.charge(order.getCustomer(), order.getAmount());
        notificationService.send(order.getCustomerEmail(), "Order confirmed");
    }
}
```

### Solution with Dependency Injection

```java
// Interface defines contract
public interface PaymentService {
    void charge(Customer customer, Money amount);
}

public interface NotificationService {
    void send(String email, String message);
}

// Implementation
@Service
public class StripePaymentService implements PaymentService {
    @Override
    public void charge(Customer customer, Money amount) {
        // Stripe API call
    }
}

// Constructor injection - testable!
@Service
@RequiredArgsConstructor
public class OrderService {
    private final PaymentService paymentService;
    private final NotificationService notificationService;

    public void placeOrder(Order order) {
        paymentService.charge(order.getCustomer(), order.getAmount());
        notificationService.send(order.getCustomerEmail(), "Order confirmed");
    }
}

// Test - easy to mock!
@ExtendWith(MockitoExtension.class)
class OrderServiceTest {

    @Mock
    private PaymentService paymentService;

    @Mock
    private NotificationService notificationService;

    @InjectMocks
    private OrderService orderService;

    @Test
    void placeOrder_chargesAndNotifies() {
        Order order = Order.builder()
            .customer(new Customer("c1", "test@example.com"))
            .amount(Money.dollars(100))
            .build();

        orderService.placeOrder(order);

        verify(paymentService).charge(any(), any());
        verify(notificationService).send(eq("test@example.com"), any());
    }
}
```

### Framework Mapping

- **Spring:** `@Autowired` constructor injection
- **Jakarta/CDI:** `@Inject`
- **Guice:** `@Inject` annotation

---

## Use Case: Item 6 in High-Throughput API

### Scenario

A REST API handling 10,000 requests/second that creates unnecessary objects in request handling.

### Problem with Object Creation

```java
@RestController
public class UserController {

    @GetMapping("/users/{id}")
    public UserDto getUser(@PathVariable String id) {
        // Creates new BigDecimal each time for same values!
        BigDecimal defaultLimit = new BigDecimal("100.00");
        String defaultRole = new String("USER");  // Redundant!

        User user = userService.findById(id);
        return new UserDto(
            user.getId(),
            user.getName(),
            user.getEmail(),
            defaultLimit,
            defaultRole
        );
    }
}
```

### Solution - Reuse Objects

```java
@RestController
public class UserController {

    // Reuse immutable objects - defined once
    private static final BigDecimal DEFAULT_LIMIT = new BigDecimal("100.00");
    private static final String DEFAULT_ROLE = "USER";  // String interned by default!

    @GetMapping("/users/{id}")
    public UserDto getUser(@PathVariable String id) {
        User user = userService.findById(id);
        return new UserDto(
            user.getId(),
            user.getName(),
            user.getEmail(),
            DEFAULT_LIMIT,       // Reused
            DEFAULT_ROLE         // Reused
        );
    }
}
```

### Framework Mapping

- **Spring:** Use `@ControllerAdvice` for shared objects
- **Jackson:** Use static final for reusable serializers
- **Modern Java:** Use records for DTOs

---

## Use Case: Item 7 in Cache Service

### Scenario

A caching service that holds references to objects, potentially causing memory leaks.

### Problem with Cache Not Cleaning Up

```java
@Service
public class UserCacheService {
    // Grows unbounded - memory leak!
    private Map<String, User> userCache = new HashMap<>();

    public User getUser(String id) {
        User user = userCache.get(id);
        if (user == null) {
            user = userRepository.findById(id).orElse(null);
            if (user != null) {
                userCache.put(id, user);  // Never removed!
            }
        }
        return user;
    }
}
```

### Solution with WeakHashMap

```java
@Service
public class UserCacheService {
    // WeakReference allows GC when no other references exist
    private Map<String, WeakReference<User>> userCache = new WeakHashMap<>();

    public Optional<User> getUser(String id) {
        WeakReference<User> ref = userCache.get(id);
        User user = ref != null ? ref.get() : null;

        if (user == null) {
            user = userRepository.findById(id).orElse(null);
            if (user != null) {
                userCache.put(id, new WeakReference<>(user));
            }
        }
        return Optional.ofNullable(user);
    }
}

// Better: Use Spring Cache with TTL
@Service
public class UserCacheServiceWithSpring {
    @Cacheable(value = "users", key = "#id")
    public User getUser(String id) {
        return userRepository.findById(id).orElse(null);
    }
}
```

### Framework Mapping

- **Spring Cache:** Use `@Cacheable` with TTL configuration
- **Caffeine:** `Cache<String, User> caffeine.build()`
- **Guava:** `CacheBuilder.newBuilder().expireAfterWrite()`

---

## Use Case: Item 8 in Database Connection

### Scenario

A service that manages database connections and needs deterministic cleanup.

### Problem with Finalizers

```java
// BAD: Finalizer may never run!
public class DatabaseConnection {
    private Connection connection;

    public DatabaseConnection(String url) throws SQLException {
        this.connection = DriverManager.getConnection(url);
    }

    // DON'T DO THIS!
    @Override
    protected void finalize() throws Throwable {
        close();  // Unreliable!
    }
}
```

### Solution with AutoCloseable

```java
public class DatabaseConnection implements AutoCloseable {
    private final Connection connection;
    private boolean closed = false;

    public DatabaseConnection(String url) throws SQLException {
        this.connection = DriverManager.getConnection(url);
    }

    @Override
    public void close() {
        if (!closed) {
            try {
                connection.close();
            } catch (SQLException e) {
                throw new RuntimeException("Failed to close connection", e);
            }
            closed = true;
        }
    }
}

// Usage in Spring - use @PreDestroy instead of finalize
@Component
public class JdbcUserRepository implements DisposableBean {

    private DatabaseConnection connection;

    @PostConstruct
    public void init() throws SQLException {
        connection = new DatabaseConnection(dbUrl);
    }

    @Override
    public void destroy() {
        // Deterministic cleanup
        closeQuietly(connection);
    }

    private void closeQuietly(AutoCloseable c) {
        try {
            if (c != null) c.close();
        } catch (Exception ignored) {}
    }
}
```

### Framework Mapping

- **Spring:** Implement `DisposableBean` or use `@PreDestroy`
- **Jakarta EE:** Use `@PreDestroy`
- **try-with-resources:** Use in application code

---

## Use Case: Item 9 in File Processing

### Scenario

A batch job that reads from one file, processes, and writes to another.

### Problem with try-finally

```java
// PROBLEM: Exception masking
public void processFile(String inputPath, String outputPath) throws IOException {
    BufferedReader reader = new BufferedReader(new FileReader(inputPath));
    BufferedWriter writer = new BufferedWriter(new FileWriter(outputPath));
    try {
        String line;
        while ((line = reader.readLine()) != null) {
            writer.write(process(line));
        }
    } finally {
        // If writer.close() fails, you lose the original exception!
        reader.close();
        writer.close();
    }
}
```

### Solution with try-with-resources

```java
public void processFile(String inputPath, String outputPath) throws IOException {
    // Resources closed in reverse order automatically
    try (
        BufferedReader reader = new BufferedReader(new FileReader(inputPath));
        BufferedWriter writer = new BufferedWriter(new FileWriter(outputPath))
    ) {
        String line;
        while ((line = reader.readLine()) != null) {
            writer.write(process(line));
            writer.newLine();
        }
        // Both closed automatically, exceptions properly chained
    }
}

// Spring Boot way - read with Resource
@Service
public class FileProcessingService {

    public void processFile(@Value("classpath:data/input.txt") Resource input) throws IOException {
        try (InputStream is = input.getInputStream();
             BufferedReader reader = new BufferedReader(new InputStreamReader(is))) {
            // Process
        }
    }
}
```

### Framework Mapping

- **Spring:** Most Spring resources implement `AutoCloseable`
- **Jackson:** `ObjectMapper` is closeable
- **HTTP Client:** `CloseableHttpClient` implements `AutoCloseable`

---

## Summary Table

| Item | Use Case | Spring Framework Solution |
|------|----------|-------------------------|
| 1 | Payment processor factory | `@ConfigurationProperties` |
| 2 | Complex order DTO | `@Builder` (Lombok) or records |
| 3 | Config singleton | Spring beans (default scope) |
| 4 | Utility classes | No change needed |
| 5 | External service dependency | Constructor injection |
| 6 | High-throughput API | Static finals, caching |
| 7 | User cache | `@Cacheable` with TTL |
| 8 | Database connections | `@PreDestroy`, try-with-resources |
| 9 | File processing | try-with-resources |
