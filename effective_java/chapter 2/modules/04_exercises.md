# Module 4: Exercises

## Chapter 2: Creating and Destroying Objects

This module provides hands-on exercises to reinforce your learning. Try to solve each exercise before looking at the solution.

---

## Exercise 1 — Refactoring: Constructor to Static Factory + Builder [Intermediate]

### Problem

You need to refactor a Spring Boot entity class that has 8+ constructor parameters into a clean pattern.

### Starter Code

```java
// BEFORE: This class has become unmaintainable
@Entity
@Table(name = "users")
public class User {
    @Id
    private String id;

    private String email;
    private String password;
    private String firstName;
    private String lastName;
    private String phoneNumber;
    private String address;
    private String city;
    private String country;
    private boolean emailVerified;
    private boolean active;
    private LocalDateTime createdAt;
    private LocalDateTime lastLoginAt;

    // Constructor with ALL parameters - impossible to read!
    public User(String id, String email, String password, String firstName,
                String lastName, String phoneNumber, String address, String city,
                String country, boolean emailVerified, boolean active,
                LocalDateTime createdAt, LocalDateTime lastLoginAt) {
        this.id = id;
        this.email = email;
        this.password = password;
        this.firstName = firstName;
        this.lastName = lastName;
        this.phoneNumber = phoneNumber;
        this.address = address;
        this.city = city;
        this.country = country;
        this.emailVerified = emailVerified;
        this.active = active;
        this.createdAt = createdAt;
        this.lastLoginAt = lastLoginAt;
    }

    // Getters and setters omitted...
}
```

### What You Need to Do

1. Convert this to use the **Builder pattern**
2. Add **validation** in the builder and constructor
3. Make the class **immutable** (no setters)
4. Add **static factory methods** for common creation scenarios

### Expected Outcome

```java
// After refactoring, usage should look like:
User user = User.builder()
    .id("user-123")
    .email("john@example.com")
    .password(encodedPassword)
    .firstName("John")
    .lastName("Doe")
    .city("New York")
    .country("USA")
    .emailVerified(false)
    .active(true)
    .build();

// Common scenarios via static factory:
User guest = User.createGuest("guest-" + UUID.randomUUID());
User unverified = User.createUnverified("unverified-" + UUID.randomUUID(), "email@test.com");
```

### Hint

Use Lombok's `@Builder` annotation to reduce boilerplate, but also understand what the annotation generates under the hood.

---

## Exercise 2 — Design: Dependency Injection-Friendly Service [Advanced]

### Problem

Design a Spring Boot service that follows proper dependency injection principles.

### Starter Code

```java
// PROBLEM: This violates DI principles - how do you test it?
@Service
public class OrderProcessor {
    // Hardcoded! Can't swap implementations
    private PaymentService paymentService = new StripePaymentService();
    private NotificationService notificationService = new EmailNotificationService();
    private InventoryService inventoryService = new DatabaseInventoryService();

    // How do you test with mock services?
    public void processOrder(Order order) {
        if (!inventoryService.checkAvailability(order.getItems())) {
            throw new IllegalStateException("Items not available");
        }

        paymentService.charge(order.getCustomer(), order.getTotal());
        notificationService.sendConfirmation(order.getCustomerEmail(), order);
    }
}
```

### What You Need to Do

1. Refactor to use **constructor injection**
2. Create **interfaces** for each service (not concrete classes)
3. Show how Spring would wire these up
4. Add **unit test** that uses mocks

### Expected Outcome

```java
// Service should depend on interfaces, not implementations
public interface PaymentService {
    void charge(Customer customer, Money amount);
}

public interface NotificationService {
    void sendConfirmation(String email, Order order);
}

// Spring config
@Configuration
public class PaymentConfig {
    @Bean
    public PaymentService stripePaymentService() {
        return new StripePaymentService();
    }
}

// Test with mocks
@Test
void testProcessOrder() {
    PaymentService mockPayment = mock(PaymentService.class);
    NotificationService mockNotify = mock(NotificationService.class);
    InventoryService mockInventory = mock(InventoryService.class);

    OrderProcessor processor = new OrderProcessor(mockPayment, mockNotify, mockInventory);
    // Test interactions...
}
```

### Hint

Think about: What if you need different payment providers in different environments? Constructor injection makes this trivial.

---

## Exercise 3 — Debug: Finding Memory Leaks [Advanced]

### Problem

A Spring Boot application's memory keeps growing until it crashes with OutOfMemoryError. Find the bug.

### Starter Code

```java
@Service
public class UserSessionService {
    // This cache is growing unbounded!
    private Map<String, UserSession> sessions = new HashMap<>();

    public void createSession(String sessionId, User user) {
        sessions.put(sessionId, new UserSession(user, LocalDateTime.now()));
    }

    public UserSession getSession(String sessionId) {
        return sessions.get(sessionId);
    }

    public void removeSession(String sessionId) {
        sessions.remove(sessionId);
    }

    // Sessions should expire after 30 minutes
    public void cleanupExpiredSessions() {
        LocalDateTime cutoff = LocalDateTime.now().minusMinutes(30);
        // BUG: This doesn't actually remove anything!
    }

    // Used by controller
    public int getActiveSessionCount() {
        return sessions.size();
    }
}
```

### What You Need to Do

1. Identify the **memory leak** in this code
2. Explain **why** sessions aren't being cleaned up
3. Fix the code to properly clean up expired sessions
4. Suggest a **better approach** for session management in Spring

### Expected Outcome

The solution should:
- Actually remove expired sessions when `cleanupExpiredSessions()` is called
- Or use `WeakHashMap` / external session store
- Handle the case where `cleanupExpiredSessions()` might be called infrequently

### Hint

What does `cleanupExpiredSessions()` actually do? Count the statements in the method body.

---

## Exercise 4 — Design: Immutable Value Object [Beginner]

### Problem

Create an immutable `Money` value object that represents currency amounts safely.

### Starter Code

```java
// PROBLEM: Mutable object can be changed after creation
public class Money {
    private BigDecimal amount;
    private String currency;

    public Money(BigDecimal amount, String currency) {
        this.amount = amount;
        this.currency = currency;
    }

    // No validation!
    // Can change after construction!
}

// Usage - what could go wrong?
Money price = new Money(new BigDecimal("99.99"), "USD");
price.setAmount(new BigDecimal("0.01")); // Dangerous!
price.setCurrency("EUR"); // Also dangerous!
```

### What You Need to Do

1. Make `Money` **immutable** (no setters, final fields)
2. Add **validation** in constructor
3. Add **static factory methods** for common currencies
4. Implement `equals()`, `hashCode()`, `toString()`
5. Make it work with **try-with-resources** pattern (implement AutoCloseable)

### Expected Outcome

```java
// Usage should be:
Money usd = Money.dollars(99.99);
Money eur = Money.euros(50.00);

// Immutable - no setters exist
// usd.setAmount(...) // Won't compile!

// Can use with try-with-resources (for resource management)
try (Money discount = Money.dollars(10.00)) {
    Money finalPrice = usd.subtract(discount);
}
```

### Hint

Use `BigDecimal` for money to avoid floating-point errors. Make the class `final` to prevent subclassing.

---

## Exercise 5 — Refactoring: Convert to try-with-resources [Intermediate]

### Problem

Convert error-prone try-finally code to try-with-resources.

### Starter Code

```java
// PROBLEM: What if close() throws? You lose the real exception!
public class FileProcessor {
    public String readFirstLine(String path) throws IOException {
        BufferedReader reader = null;
        try {
            reader = new BufferedReader(new FileReader(path));
            return reader.readLine();
        } finally {
            if (reader != null) {
                reader.close(); // Can throw and mask original exception!
            }
        }
    }

    // Another problematic pattern
    public void copyFile(String src, String dest) throws IOException {
        FileInputStream in = null;
        FileOutputStream out = null;
        try {
            in = new FileInputStream(src);
            out = new FileOutputStream(dest);
            // Copy data...
        } finally {
            if (in != null) in.close();  // Can mask!
            if (out != null) out.close(); // Can mask!
        }
    }
}
```

### What You Need to Do

1. Convert both methods to use **try-with-resources**
2. Show how **suppressed exceptions** work
3. Add proper error handling

### Expected Outcome

```java
// Clean, safe resource management
public String readFirstLine(String path) throws IOException {
    try (BufferedReader reader = new BufferedReader(new FileReader(path))) {
        return reader.readLine();
    }
}

public void copyFile(String src, String dest) throws IOException {
    try (
        FileInputStream in = new FileInputStream(src);
        FileOutputStream out = new FileOutputStream(dest)
    ) {
        // Copy data...
    }
}
```

### Hint

Remember: any object implementing `AutoCloseable` can be used with try-with-resources.

---

## Solutions

### Exercise 1 Solution

```java
@Entity
@Table(name = "users")
@Builder
@NoArgsConstructor(access = AccessLevel.PRIVATE)
@AllArgsConstructor(access = AccessLevel.PRIVATE)  // Only builder can call
public class User {
    @Id
    private String id;

    private String email;
    private String password;
    private String firstName;
    private String lastName;
    private String phoneNumber;
    private String address;
    private String city;
    private String country;
    private boolean emailVerified;
    private boolean active;
    private LocalDateTime createdAt;
    private LocalDateTime lastLoginAt;

    // Static factory methods
    public static User createGuest(String id) {
        return builder()
            .id(id)
            .active(true)
            .emailVerified(false)
            .createdAt(LocalDateTime.now())
            .build();
    }

    public static User createUnverified(String id, String email) {
        return builder()
            .id(id)
            .email(email)
            .active(true)
            .emailVerified(false)
            .createdAt(LocalDateTime.now())
            .build();
    }
}
```

### Exercise 2 Solution

```java
// Interfaces define contracts
public interface PaymentService {
    void charge(Customer customer, Money amount);
}

public interface NotificationService {
    void sendConfirmation(String email, Order order);
}

public interface InventoryService {
    boolean checkAvailability(List<OrderItem> items);
}

// Constructor injection
@Service
@RequiredArgsConstructor
public class OrderProcessor {
    private final PaymentService paymentService;
    private final NotificationService notificationService;
    private final InventoryService inventoryService;

    public void processOrder(Order order) {
        if (!inventoryService.checkAvailability(order.getItems())) {
            throw new IllegalStateException("Items not available");
        }

        paymentService.charge(order.getCustomer(), order.getTotal());
        notificationService.sendConfirmation(order.getCustomerEmail(), order);
    }
}
```

### Exercise 3 Solution

```java
@Service
public class UserSessionService {
    // FIX 1: Use WeakHashMap - GC can collect entries when no other references
    private Map<String, WeakReference<UserSession>> sessions = new WeakHashMap<>();

    // FIX 2: Properly clean up
    public void cleanupExpiredSessions() {
        LocalDateTime cutoff = LocalDateTime.now().minusMinutes(30);

        // Need to iterate and check expiration
        sessions.entrySet().removeIf(entry -> {
            UserSession session = entry.getValue().get();
            if (session == null) return true;  // Reference was GC'd
            return session.getCreatedAt().isBefore(cutoff);
        });
    }

    // BETTER: Use Spring Session or external store
    // @EnableRedisHttpSession
    // Or use ConcurrentHashMap with explicit TTL cleanup
}
```

### Exercise 4 Solution

```java
public final class Money implements AutoCloseable {
    private final BigDecimal amount;
    private final String currency;

    // Private constructor
    private Money(BigDecimal amount, String currency) {
        this.amount = Objects.requireNonNull(amount);
        this.currency = Objects.requireNonNull(currency);

        if (amount.compareTo(BigDecimal.ZERO) < 0) {
            throw new IllegalArgumentException("Amount cannot be negative");
        }
    }

    // Static factory methods
    public static Money dollars(BigDecimal amount) {
        return new Money(amount, "USD");
    }

    public static Money euros(BigDecimal amount) {
        return new Money(amount, "EUR");
    }

    // Immutable operations - return new Money
    public Money add(Money other) {
        if (!this.currency.equals(other.currency)) {
            throw new IllegalArgumentException("Currency mismatch");
        }
        return new Money(this.amount.add(other.amount), this.currency);
    }

    public Money subtract(Money other) {
        return add(new Money(other.amount.negate(), other.currency));
    }

    // AutoCloseable - for resource-like usage pattern (unusual but valid)
    @Override
    public void close() {
        // Could release resources if Money held them (e.g., currency service)
    }

    // equals, hashCode, toString...
}
```

### Exercise 5 Solution

See "Expected Outcome" section above — that's the solution!
