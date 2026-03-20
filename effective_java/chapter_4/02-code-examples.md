# Chapter 4: Classes and Interfaces

## Items 15–25

---

## 💻 Module 2: Code Examples

This module provides production-ready code examples demonstrating both bad practices (❌) and good practices (✅) for each item.

---

### Item 15 & 16 — Visibility and Accessors

#### Item 15 — Minimize Accessibility

##### ❌ Bad — Exposing internal data in a Spring service:

```java
package com.example.bad;

import org.springframework.stereotype.Service;
import java.math.BigDecimal;
import java.util.*;

/**
 * BAD: Exposing internal state publicly violates encapsulation.
 * Anyone can modify discount rates without validation!
 */
@Service
public class OrderServiceBad {

    // This field is exposed directly — anyone can modify it!
    public Map<String, BigDecimal> discountRates = new HashMap<>();

    // Mutable internal state exposed directly
    public List<Order> pendingOrders = new ArrayList<>();

    public void applyDiscount(String customerId, BigDecimal discount) {
        // No validation! Can set negative discounts!
        discountRates.put(customerId, discount);
    }

    // Simple order class
    static class Order {
        private String id;
        private BigDecimal total;

        public Order(String id, BigDecimal total) {
            this.id = id;
            this.total = total;
        }

        public String getId() { return id; }
        public BigDecimal getTotal() { return total; }
    }
}
```

##### ✅ Good — Proper encapsulation:

```java
package com.example.good;

import org.springframework.stereotype.Service;
import java.math.BigDecimal;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CopyOnWriteArrayList;

/**
 * GOOD: Proper encapsulation with controlled access.
 * Validation, thread-safety, and immutable views.
 */
@Service
public class OrderServiceGood {

    // Private — only accessible through controlled methods
    private final Map<String, BigDecimal> discountRates = new ConcurrentHashMap<>();

    // Thread-safe internal state with accessor methods
    private final List<Order> pendingOrders = new CopyOnWriteArrayList<>();

    /**
     * Controlled mutation with comprehensive validation.
     */
    public void applyDiscount(String customerId, BigDecimal discount) {
        // Validation before mutation
        Objects.requireNonNull(customerId, "Customer ID cannot be null");
        Objects.requireNonNull(discount, "Discount cannot be null");

        if (discount.compareTo(BigDecimal.ZERO) < 0) {
            throw new IllegalArgumentException("Discount must be non-negative");
        }
        if (discount.compareTo(new BigDecimal("1.00")) > 0) {
            throw new IllegalArgumentException("Discount cannot exceed 100%");
        }

        discountRates.put(customerId, discount);
    }

    /**
     * Read-only access via unmodifiable view.
     * Caller cannot modify internal state.
     */
    public Map<String, BigDecimal> getDiscountRates() {
        return Collections.unmodifiableMap(discountRates);
    }

    /**
     * Returns unmodifiable copy of orders.
     */
    public List<Order> getPendingOrders() {
        return Collections.unmodifiableList(pendingOrders);
    }

    public void addOrder(Order order) {
        pendingOrders.add(Objects.requireNonNull(order));
    }

    // Simple order class
    public static class Order {
        private final String id;
        private final BigDecimal total;

        public Order(String id, BigDecimal total) {
            this.id = Objects.requireNonNull(id);
            this.total = Objects.requireNonNull(total);
        }

        public String getId() { return id; }
        public BigDecimal getTotal() { return total; }
    }
}
```

---

#### Item 16 — Public Classes Should Use Accessors

##### ❌ Bad — Public mutable field in a DTO:

```java
package com.example.bad;

/**
 * BAD: Public mutable fields - no validation, no encapsulation.
 * Can't add validation later without breaking existing clients.
 */
public class UserDtoBad {
    public String name;
    public String email;
    public List<String> roles;

    // Anyone can do this:
    // userDto.roles = null;  // Breaks downstream code
    // userDto.roles.add("admin");  // Modifies shared state!
}
```

##### ✅ Good — Proper encapsulation in DTO:

```java
package com.example.good;

import java.util.List;
import java.util.Objects;

/**
 * GOOD: Immutable DTO with validation.
 * Modern Java: Consider using 'record' instead (Java 16+)
 */
public final class UserDtoGood {

    private final String name;
    private final String email;
    private final List<String> roles;

    /**
     * Constructor with validation and defensive copies.
     */
    public UserDtoGood(String name, String email, List<String> roles) {
        this.name = Objects.requireNonNull(name, "Name cannot be null");
        this.email = Objects.requireNonNull(email, "Email cannot be null");
        // Defensive copy - List.copyOf returns immutable copy
        this.roles = List.copyOf(roles);
    }

    // Getters only - no setters needed for immutable DTO
    public String getName() { return name; }
    public String getEmail() { return email; }

    // Returns immutable view - safe to expose
    public List<String> getRoles() { return roles; }

    @Override
    public String toString() {
        return "UserDtoGood{name='" + name + "', email='" + email + "', roles=" + roles + "}";
    }
}

/**
 * MODERN ALTERNATIVE (Java 16+): Use record
 *
 * public record UserDto(String name, String email, List<String> roles) {}
 *
 * Records automatically provide:
 * - Constructor with validation
 * - Immutable fields
 * - equals(), hashCode(), toString()
 * - Accessor methods: name(), email(), roles()
 */
```

---

### Item 17 — Minimize Mutability

##### ❌ Bad — Mutable value object:

```java
package com.example.bad;

import java.math.BigDecimal;
import java.util.Objects;

/**
 * BAD: Mutable value object - not thread-safe, dangerous in collections.
 */
public class MoneyBad {

    private BigDecimal amount;
    private String currency;

    public MoneyBad(BigDecimal amount, String currency) {
        this.amount = amount;
        this.currency = currency;
    }

    // Setters allow mutation - dangerous!
    public void setAmount(BigDecimal amount) { this.amount = amount; }
    public void setCurrency(String currency) { this.currency = currency; }

    public BigDecimal getAmount() { return amount; }
    public String getCurrency() { return currency; }

    // Problem: Can modify after adding to HashSet!
    // money.setAmount(BigDecimal.TEN); // HashSet now corrupted!
}
```

##### ✅ Good — Immutable value object:

```java
package com.example.good;

import java.math.BigDecimal;
import javamath.RoundingMode;
import java.util.Currency;
import java.util.Objects;

/**
 * GOOD: Immutable value object (Value Object pattern).
 * Thread-safe, safe in collections, easy to reason about.
 */
public final class Money {

    private final BigDecimal amount;
    private final Currency currency;

    /**
     * Private constructor - use factory method for validation.
     */
    private Money(BigDecimal amount, Currency currency) {
        this.amount = amount;
        this.currency = currency;
    }

    /**
     * Factory method with validation.
     */
    public static Money of(BigDecimal amount, Currency currency) {
        Objects.requireNonNull(amount, "Amount cannot be null");
        Objects.requireNonNull(currency, "Currency cannot be null");

        if (amount.compareTo(BigDecimal.ZERO) < 0) {
            throw new IllegalArgumentException("Amount cannot be negative");
        }

        // Normalize scale for consistency
        BigDecimal normalizedAmount = amount.setScale(
            currency.getDefaultFractionDigits(),
            RoundingMode.HALF_UP
        );

        return new Money(normalizedAmount, currency);
    }

    /**
     * Factory for zero amount.
     */
    public static Money zero(Currency currency) {
        return Money.of(BigDecimal.ZERO, currency);
    }

    /**
     * Pure operation - returns NEW instance, doesn't mutate!
     */
    public Money add(Money other) {
        if (!this.currency.equals(other.currency)) {
            throw new IllegalArgumentException(
                "Cannot add different currencies: " + currency + " and " + other.currency
            );
        }
        return new Money(this.amount.add(other.amount), this.currency);
    }

    public Money subtract(Money other) {
        if (!this.currency.equals(other.currency)) {
            throw new IllegalArgumentException(
                "Cannot subtract different currencies"
            );
        }
        return new Money(this.amount.subtract(other.amount), this.currency);
    }

    public Money multiply(int factor) {
        return new Money(
            this.amount.multiply(BigDecimal.valueOf(factor)),
            this.currency
        );
    }

    // Getters (no setters - immutable!)
    public BigDecimal getAmount() { return amount; }
    public Currency getCurrency() { return currency; }

    /**
     * Essential: equals/hashCode based on VALUE, not identity.
     */
    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        Money money = (Money) o;
        return Objects.equals(amount, money.amount) &&
               Objects.equals(currency, money.currency);
    }

    @Override
    public int hashCode() {
        return Objects.hash(amount, currency);
    }

    @Override
    public String toString() {
        return amount + " " + currency.getCurrencyCode();
    }
}
```

---

### Item 18 — Favor Composition Over Inheritance

##### ❌ Bad — Inheritance abuse:

```java
package com.example.bad;

import java.util.*;

/**
 * BAD: Extending a concrete class you don't control.
 * Fragile - changes to HashSet can break this!
 */
public class InstrumentedHashSetBad<E> extends HashSet<E> {

    private int addCount = 0;

    @Override
    public boolean add(E e) {
        addCount++;
        return super.add(e);
    }

    @Override
    public boolean addAll(Collection<? extends E> c) {
        addCount += c.size();  // BUG: If add() internally calls addAll, count is wrong!
        return super.addAll(c);
    }

    public int getAddCount() { return addCount; }
}

// Test showing the bug:
class TestInstrumented {
    public static void main(String[] args) {
        InstrumentedHashSetBad<String> set = new InstrumentedHashSetBad<>();
        set.addAll(Arrays.asList("a", "b", "c"));

        // Expected: 3, but if HashSet implementation changes...
        System.out.println("Count: " + set.getAddCount());
    }
}
```

##### ✅ Good — Composition with forwarding:

```java
package com.example.good;

import java.util.*;

/**
 * GOOD: Composition with forwarding - safe and flexible.
 * Uses delegation instead of inheritance.
 */
public class InstrumentedSet<E> implements Set<E> {

    private final Set<E> delegate;  // The underlying set
    private int addCount = 0;

    public InstrumentedSet(Set<E> delegate) {
        // Check that delegate is not null
        this.delegate = Objects.requireNonNull(delegate);
    }

    @Override
    public boolean add(E e) {
        addCount++;
        return delegate.add(e);
    }

    @Override
    public boolean addAll(Collection<? extends E> c) {
        // Count BEFORE calling delegate to avoid double-counting
        // if delegate.addAll() internally calls add()
        int countBefore = addCount;
        addCount += c.size();

        boolean result = delegate.addAll(c);

        // If addAll failed, rollback the count
        if (!result) {
            addCount = countBefore;
        }

        return result;
    }

    public int getAddCount() { return addCount; }

    // Forward all other methods to delegate

    @Override
    public int size() { return delegate.size(); }

    @Override
    public boolean isEmpty() { return delegate.isEmpty(); }

    @Override
    public boolean contains(Object o) { return delegate.contains(o); }

    @Override
    public Iterator<E> iterator() { return delegate.iterator(); }

    @Override
    public Object[] toArray() { return delegate.toArray(); }

    @Override
    public <T> T[] toArray(T[] a) { return delegate.toArray(a); }

    @Override
    public boolean remove(Object o) { return delegate.remove(o); }

    @Override
    public boolean containsAll(Collection<?> c) { return delegate.containsAll(c); }

    @Override
    public boolean removeAll(Collection<?> c) { return delegate.removeAll(c); }

    @Override
    public boolean retainAll(Collection<?> c) { return delegate.retainAll(c); }

    @Override
    public void clear() { delegate.clear(); }

    @Override
    public String toString() {
        return "InstrumentedSet{delegate=" + delegate + ", addCount=" + addCount + "}";
    }
}
```

##### Modern Alternative — Using Guava's ForwardingSet:

```java
package com.example.modern;

import com.google.common.collect.ForwardingSet;
import java.util.HashSet;
import java.util.Set;

/**
 * EVEN BETTER: Use Guava's ForwardingSet to reduce boilerplate.
 */
public class InstrumentedSetGuava<E> extends ForwardingSet<E> {

    private int addCount = 0;
    private final Set<E> delegate;

    public InstrumentedSetGuava(Set<E> delegate) {
        this.delegate = delegate;
    }

    @Override
    protected Set<E> delegate() {
        return delegate;
    }

    @Override
    public boolean add(E element) {
        addCount++;
        return super.add(element);
    }

    @Override
    public boolean addAll(Collection<? extends E> elements) {
        addCount += elements.size();
        return super.addAll(elements);
    }

    public int getAddCount() { return addCount; }
}
```

---

### Item 20 — Prefer Interfaces to Abstract Classes

##### ❌ Bad — Using abstract class when interface + default would work:

```java
package com.example.bad;

/**
 * BAD: Abstract class restricts users to single inheritance.
 * Cannot extend this AND another class.
 */
public abstract class AbstractPaymentProcessorBad {

    protected abstract PaymentResult process(Payment payment);
    protected abstract RefundResult refund(Payment payment);

    // Common code - but this locks users into single inheritance
    protected void logTransaction(Payment payment) {
        System.out.println("Processing: " + payment.getId());
    }
}

// If user wants to also extend some other base class, they're stuck!
class MyProcessor extends AbstractPaymentProcessorBad {
    // Can't extend anything else
}
```

##### ✅ Good — Interface with default methods:

```java
package com.example.good;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.UUID;

/**
 * GOOD: Interface with default methods - flexible and extensible.
 */
public interface PaymentProcessor {

    PaymentResult process(Payment payment);
    RefundResult refund(Payment payment);

    /**
     * Default method provides common functionality.
     * Can be overridden if needed.
     */
    default void logTransaction(Payment payment) {
        System.out.println("[" + Instant.now() + "] Processing payment: " + payment.getId());
    }

    /**
     * Default method with implementation - optional behavior.
     */
    default boolean supports(PaymentType type) {
        return true;  // Default: supports all types
    }

    /**
     * Static method - utility method related to the interface.
     */
    static PaymentProcessor noOp() {
        return new PaymentProcessor() {
            @Override
            public PaymentResult process(Payment payment) {
                return PaymentResult.failure("No-op processor");
            }

            @Override
            public RefundResult refund(Payment payment) {
                return RefundResult.failure("No-op processor");
            }
        };
    }
}

// Multiple implementations - can implement other interfaces too!
@Service
@Qualifier("stripe")
class StripeProcessor implements PaymentProcessor, Loggable {

    @Override
    public PaymentResult process(Payment payment) {
        // Stripe-specific implementation
        return new PaymentResult(Status.SUCCESS, "txn_" + UUID.randomUUID());
    }

    @Override
    public RefundResult refund(Payment payment) {
        return new RefundResult(Status.SUCCESS, "re_" + UUID.randomUUID());
    }
}

@Service
@Qualifier("paypal")
class PayPalProcessor implements PaymentProcessor {

    @Override
    public PaymentResult process(Payment payment) {
        return new PaymentResult(Status.SUCCESS, "PAY-" + UUID.randomUUID());
    }

    @Override
    public RefundResult refund(Payment payment) {
        return new RefundResult(Status.SUCCESS, "REF-" + UUID.randomUUID());
    }
}

// Supporting classes
record Payment(String id, BigDecimal amount, String currency, PaymentType type) {}
record PaymentResult(Status status, String transactionId) {
    public static PaymentResult failure(String reason) {
        return new PaymentResult(Status.FAILURE, reason);
    }
}
record RefundResult(Status status, String refundId) {
    public static RefundResult failure(String reason) {
        return new RefundResult(Status.FAILURE, reason);
    }
}
enum Status { SUCCESS, FAILURE }
enum PaymentType { CREDIT_CARD, DEBIT_CARD, PAYPAL, CRYPTO }
interface Loggable { void log(String message); }
```

---

### Item 21 — Use Interfaces Only to Define Types

##### ❌ Bad — Interface pollution:

```java
package com.example.bad;

/**
 * BAD: Constants in interface - bad practice.
 * Pollutes the namespace of any class that implements this.
 */
public interface OrderConstantsBad {

    String DEFAULT_CURRENCY = "USD";
    int MAX_ITEMS_PER_ORDER = 100;
    double TAX_RATE = 0.08;
    String ORDER_PREFIX = "ORD-";

    // This is NOT defining a type! It's just a utility bucket.
}

// If someone implements this, they inherit all these constants:
// Which is confusing and pollutes their namespace
class BadOrderService implements OrderConstantsBad {
    void process() {
        // Can access DEFAULT_CURRENCY, but it's not a behavior!
        String currency = DEFAULT_CURRENCY;
    }
}
```

##### ✅ Good — Separate constants from types:

```java
package com.example.good;

/**
 * GOOD: Constants in utility class - proper separation of concerns.
 */
public final class OrderConstants {

    // Private constructor prevents instantiation
    private OrderConstants() {
        throw new AssertionError("Cannot instantiate constants class");
    }

    public static final String DEFAULT_CURRENCY = "USD";
    public static final int MAX_ITEMS_PER_ORDER = 100;
    public static final java.math.BigDecimal TAX_RATE = new java.math.BigDecimal("0.08");
    public static final String ORDER_PREFIX = "ORD-";
}

/**
 * GOOD: Interface only defines behavior (the "can-do" relationship).
 */
public interface OrderValidator {

    /**
     * Validates an order and returns the result.
     */
    ValidationResult validate(Order order);

    /**
     * Validates with common defaults applied.
     * Default method provides implementation - override if custom behavior needed.
     */
    default ValidationResult validateWithDefaults(Order order) {
        if (order == null) {
            return ValidationResult.failure("Order cannot be null");
        }
        if (order.getItems() == null || order.getItems().isEmpty()) {
            return ValidationResult.failure("Order must have at least one item");
        }
        return validate(order);
    }
}

/**
 * Implementation provides specific validation logic.
 */
class BusinessOrderValidator implements OrderValidator {

    @Override
    public ValidationResult validate(Order order) {
        // Business-specific validation
        if (order.getTotal().compareTo(java.math.BigDecimal.ZERO) <= 0) {
            return ValidationResult.failure("Order total must be positive");
        }
        if (order.getItems().size() > OrderConstants.MAX_ITEMS_PER_ORDER) {
            return ValidationResult.failure(
                "Order exceeds maximum items: " + OrderConstants.MAX_ITEMS_PER_ORDER
            );
        }
        return ValidationResult.success();
    }
}

// Supporting classes
record Order(String id, java.math.BigDecimal total, java.util.List<OrderItem> items) {}
record OrderItem(String productId, int quantity, java.math.BigDecimal price) {}
record ValidationResult(boolean valid, String errorMessage) {
    public static ValidationResult success() {
        return new ValidationResult(true, null);
    }
    public static ValidationResult failure(String message) {
        return new ValidationResult(false, message);
    }
}
```

---

### Item 22 — Favor Static Member Classes Over Nonstatic

##### ❌ Bad — Unnecessary nonstatic inner class:

```java
package com.example.bad;

/**
 * BAD: Unnecessary nonstatic inner class holds reference to outer instance.
 * Can cause memory leaks if Handler is passed around.
 */
public class OrderProcessorBad {

    private final String merchantId;
    private int processedCount = 0;

    // PROBLEM: Nonstatic - holds reference to OrderProcessor instance!
    public class OrderHandler {

        public void handle(Order order) {
            // Can access merchantId - but why should it?
            // Can access processedCount - but shouldn't need to
            processedCount++;
            processWithMerchant(order);
        }
    }

    public OrderHandler createHandler() {
        return new OrderHandler();
    }

    private void processWithMerchant(Order order) {
        System.out.println("Processing " + order + " for " + merchantId);
    }
}

class Order {
    private final String id;
    public Order(String id) { this.id = id; }
    public String getId() { return id; }
}
```

##### ✅ Good — Static inner class:

```java
package com.example.good;

/**
 * GOOD: Static inner class - no reference to outer instance.
 * Appropriate when you don't need access to outer instance.
 */
public class OrderProcessorGood {

    private final String merchantId;
    private int processedCount = 0;

    // STATIC: No reference to outer instance - lighter and safer
    public static class OrderHandler {

        private final String handlerId;

        public OrderHandler(String handlerId) {
            this.handlerId = handlerId;
        }

        public void handle(Order order) {
            // No access to merchantId - that's correct!
            // No access to processedCount - clean separation
            processOrder(order);
        }

        private void processOrder(Order order) {
            System.out.println("Handler " + handlerId + " processing " + order.getId());
        }
    }

    public static OrderHandler createHandler(String id) {
        return new OrderHandler(id);
    }

    // WHEN TO USE NONSTATIC: When you NEED the outer instance
    /**
     * This inner class NEEDS nonstatic because it processes orders
     * FOR THIS SPECIFIC processor instance.
     */
    public class OrderBatchProcessor {

        public int processBatch(java.util.List<Order> orders) {
            // NEEDS access to merchantId and processedCount
            return (int) orders.stream()
                .filter(order -> processWithMerchant(order))
                .count();
        }

        private boolean processWithMerchant(Order order) {
            processedCount++;
            return true;
        }
    }

    public OrderBatchProcessor createBatchProcessor() {
        return new OrderBatchProcessor();
    }
}

class Order {
    private final String id;
    public Order(String id) { this.id = id; }
    public String getId() { return id; }
}
```

---

### Item 24 — Use Static Factory Methods Instead of Constructors

##### ❌ Bad — Constructor overloads are confusing:

```java
package com.example.bad;

import java.math.BigDecimal;
import java.util.Currency;

/**
 * BAD: Constructor overloads are confusing.
 * What does each constructor mean?
 */
public class PaymentBad {

    private BigDecimal amount;
    private Currency currency;
    private PaymentMethod method;
    private String reference;

    // Ambiguous - what do parameters mean?
    public PaymentBad(BigDecimal amount) { }
    public PaymentBad(BigDecimal amount, Currency currency) { }
    public PaymentBad(BigDecimal amount, Currency currency, PaymentMethod method) { }
    public PaymentBad(BigDecimal amount, Currency currency, PaymentMethod method, String reference) { }

    // Client code is confusing:
    // new Payment(BigDecimal.TEN) - what currency? What method?
    // new Payment(BigDecimal.TEN, Currency.getInstance("USD"), null, null) - error-prone!
}
```

##### ✅ Good — Named factory methods:

```java
package com.example.good;

import java.math.BigDecimal;
import java.util.Currency;
import java.util.Objects;

/**
 * GOOD: Named static factory methods clearly convey intent.
 */
public final class Payment {

    private final BigDecimal amount;
    private final Currency currency;
    private final PaymentMethod method;
    private final String reference;

    /**
     * Private constructor - must use factory methods.
     */
    private Payment(BigDecimal amount, Currency currency,
                   PaymentMethod method, String reference) {
        this.amount = Objects.requireNonNull(amount);
        this.currency = Objects.requireNonNull(currency);
        this.method = Objects.requireNonNull(method);
        this.reference = reference;
    }

    // === Static Factory Methods ===

    /**
     * Create standard payment with default method.
     */
    public static Payment of(BigDecimal amount, Currency currency) {
        return new Payment(amount, currency, PaymentMethod.STANDARD, null);
    }

    /**
     * Create payment with specific method.
     */
    public static Payment of(BigDecimal amount, Currency currency, PaymentMethod method) {
        return new Payment(amount, currency, method, null);
    }

    /**
     * Create payment with custom reference.
     */
    public static Payment withReference(BigDecimal amount, Currency currency, String reference) {
        return new Payment(amount, currency, PaymentMethod.STANDARD, reference);
    }

    /**
     * Create payment from Order entity - semantic conversion.
     */
    public static Payment from(Order order) {
        return new Payment(
            order.getTotal(),
            order.getCurrency(),
            order.getPreferredMethod(),
            order.getId()
        );
    }

    /**
     * Can return cached instances - singleton-like behavior.
     */
    public static Payment zero(Currency currency) {
        // Could cache common values like this
        return new Payment(BigDecimal.ZERO, currency, PaymentMethod.NONE, "ZERO");
    }

    // Getters
    public BigDecimal getAmount() { return amount; }
    public Currency getCurrency() { return currency; }
    public PaymentMethod getMethod() { return method; }
    public String getReference() { return reference; }

    @Override
    public String toString() {
        return "Payment{amount=" + amount + ", currency=" + currency +
               ", method=" + method + ", reference='" + reference + "'}";
    }
}

// Supporting classes
enum PaymentMethod { STANDARD, EXPRESS, NONE }
record Order(String id, BigDecimal total, Currency currency, PaymentMethod preferredMethod) {}
```

---

### Item 25 — Limit Source Files to a Single Top-Level Class

##### ❌ Bad — Multiple top-level classes:

```java
// File: Order.java - BAD: Two public classes in one file!

package com.example.bad;

// This is the "main" class
public class Order {
    private String id;

    public Order(String id) { this.id = id; }
}

// PROBLEM: This should be in its own file: Customer.java
public class Customer {
    private String name;

    public Customer(String name) { this.name = name; }
}

/*
 * Compilation issues:
 * - javac Order.java creates: Order.class, Customer.class
 * - But customer can't find Order without importing it
 * - IDE confusion about which class is "main"
 * - Cannot have two public classes with same name in package
 */
```

##### ✅ Good — One public class per file:

```java
// File: Order.java
package com.example.good;

public final class Order {
    private final String id;

    public Order(String id) {
        this.id = Objects.requireNonNull(id);
    }

    public String getId() { return id; }
}

// File: Customer.java - Separate file!
package com.example.good;

public final class Customer {
    private final String name;

    public Customer(String name) {
        this.name = Objects.requireNonNull(name);
    }

    public String getName() { return name; }
}

// File: OrderProcessor.java - Another file!
package com.example.good;

import java.util.Objects;

public class OrderProcessor {

    public Order createOrder(String id) {
        return new Order(id);
    }
}
```

---

## Summary Table

| Item | Bad Pattern | Good Pattern |
|------|-------------|--------------|
| 15 | Public fields | Private + accessors |
| 16 | Public mutable fields | Immutable DTOs |
| 17 | Mutable value objects | Immutable Money, Address |
| 18 | Extend HashSet | Composition + delegation |
| 19 | Non-final without docs | Document or make final |
| 20 | Abstract class for reuse | Interface + default methods |
| 21 | Constants in interface | Separate utility class |
| 22 | Nonstatic inner class | Static unless needed |
| 23 | Tagged classes | Separate subclasses |
| 24 | Constructor overloads | Named factory methods |
| 25 | Multiple classes per file | One class per file |
