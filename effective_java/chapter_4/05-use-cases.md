# Chapter 4: Classes and Interfaces

## Items 15–25

---

## 🌍 Module 5: Use Cases

Real-world scenarios demonstrating how these items apply in production systems.

---

### Use Case: Item 17 — Immutable DTOs in Spring REST APIs

**Scenario:** You're building a Spring Boot microservice that returns user data via REST API. You initially use mutable DTOs with setters.

**Problem without this item:**
- Mutable DTOs can be accidentally modified after construction
- Jackson will serialize whatever state exists at serialization time
- If your entity has lazy-loaded relationships and you accidentally access them during serialization, you get `LazyInitializationException`
- Mutable state makes your API responses unpredictable

**Solution:** Use immutable DTOs (or Java records in Java 16+):

```java
// Immutable DTO - only way to create is via constructor
public record UserResponse(
    Long id,
    String username,
    String email,
    List<String> roles,
    Instant createdAt
) {
    // Factory method with validation
    public static UserResponse from(User user) {
        return new UserResponse(
            user.getId(),
            user.getUsername(),
            user.getEmail(),
            List.copyOf(user.getRoles()),  // Defensive copy
            user.getCreatedAt()
        );
    }
}

// Controller uses it
@RestController
public class UserController {

    private final UserService userService;

    @GetMapping("/users/{id}")
    public UserResponse getUser(@PathVariable Long id) {
        User user = userService.findById(id);
        return UserResponse.from(user);  // Clean conversion
    }
}
```

**Framework mapping:**
- **Jackson** works seamlessly with records — just add `@JsonCreator` if you need deserialization
- **Spring MVC** returns records automatically as JSON
- **Lombok** has `@Value` for immutable classes if you're on Java < 16
- **MapStruct** generates immutable mappers with `@Mapping` annotations

---

### Use Case: Item 18 — Composition in Spring Data

**Scenario:** You need to add audit logging to all repository operations without modifying every repository.

**Problem without this item:**
- If you extend `JpaRepository` to add logging, you'd need to override every method
- If Spring Data adds new methods in an update, your audit code gets bypassed
- Inheritance creates tight coupling to Spring Data internals

**Solution:** Use composition with AOP or Spring's delegation:

```java
// Composition: wrap any repository
public class AuditingRepository<T, ID> implements Repository<T, ID> {

    private final Repository<T, ID> delegate;
    private final AuditService auditService;
    private final String entityName;

    public AuditingRepository(Repository<T, ID> delegate,
                              AuditService auditService,
                              Class<T> entityClass) {
        this.delegate = delegate;
        this.auditService = auditService;
        this.entityName = entityClass.getSimpleName();
    }

    @Override
    public Optional<T> findById(ID id) {
        return delegate.findById(id);
    }

    @Override
    public <S extends T> S save(S entity) {
        boolean isNew = entityName + " save audit" != null; // Simplified
        String action = isNew ? "CREATED" : "UPDATED";
        auditService.log(entityName, action, entity);
        return delegate.save(entity);
    }

    @Override
    public void delete(T entity) {
        auditService.log(entityName, "DELETED", entity);
        delegate.delete(entity);
    }

    // Forward other methods
    @Override
    public long count() { return delegate.count(); }
}

// Use with Spring
@Configuration
class AuditConfig {

    @Bean
    public RepositoryFactoryBean<?, ?, ?> auditingRepositoryFactory(
            EntityManagerFactory emf,
            AuditService auditService) {
        // Configure to wrap repositories with auditing
    }
}
```

**Framework mapping:**
- **Spring Data** uses composition internally with `RepositoryDelegates`
- **Spring AOP** can also solve this with `@Aspect` and `@Around` advice
- **Project Reactor** uses composition everywhere — `Mono` and `Flux` transform via composition

---

### Use Case: Item 24 — Static Factory in Service Layer

**Scenario:** Creating domain objects from DTOs in a Spring service layer.

**Problem without this item:**
- Constructor overloads become confusing
- What does `new Order(total, currency)` mean? Is currency optional?
- Can't validate or transform during construction
- Can't return cached instances or subtypes

**Solution:** Use named factory methods:

```java
public final class Order {

    private final String id;
    private final Money total;
    private final List<OrderItem> items;
    private final Customer customer;
    private final OrderStatus status;

    // Private constructor - must use factory
    private Order(Builder builder) {
        this.id = builder.id;
        this.total = builder.total;
        this.items = List.copyOf(builder.items);  // Immutable copy
        this.customer = builder.customer;
        this.status = builder.status;
    }

    // Static factory from request DTO
    public static Order fromCreateRequest(CreateOrderRequest request) {
        return Order.builder()
            .id(generateOrderId())
            .total(calculateTotal(request.getItems(), request.getCurrency()))
            .items(request.getItems().stream()
                .map(ItemMapper::toDomain)
                .collect(Collectors.toList()))
            .customer(request.getCustomer())
            .status(OrderStatus.PENDING)
            .build();
    }

    // Static factory from another order (e.g., for reordering)
    public static Order createReorder(Order original) {
        return Order.builder()
            .id(generateOrderId())
            .total(original.getTotal())
            .items(original.getItems())
            .customer(original.getCustomer())
            .status(OrderStatus.PENDING)
            .build();
    }

    // Builder pattern
    public static Builder builder() { return new Builder(); }

    public static class Builder {
        private String id;
        private Money total;
        private List<OrderItem> items = new ArrayList<>();
        private Customer customer;
        private OrderStatus status = OrderStatus.DRAFT;

        public Builder id(String id) { this.id = id; return this; }
        // ... other setters

        public Order build() {
            // Validation before construction
            Objects.requireNonNull(total, "Total is required");
            Objects.requireNonNull(customer, "Customer is required");
            if (items.isEmpty()) throw new IllegalArgumentException("Order must have items");
            return new Order(this);
        }
    }
}
```

**Framework mapping:**
- **MapStruct** can generate mappers that call static factory methods
- **Lombok** has `@Builder` for fluent builder patterns
- **Spring's** `ObjectMapper` can be configured to use factory methods via `@JsonCreator`

---

### Use Case: Item 20 — Interface with Default Methods

**Scenario:** Building a plugin system where multiple processors handle different payment types.

**Problem without this item:**
- Using abstract class means only one inheritance path
- Can't combine multiple behaviors
- Adding new methods to interface breaks existing implementations

**Solution:** Use interface with default methods:

```java
public interface PaymentProcessor {

    /**
     * Process a payment.
     */
    PaymentResult process(Payment payment);

    /**
     * Refund a payment.
     */
    RefundResult refund(Payment payment);

    /**
     * Check if this processor supports the given payment type.
     * Default: supports all types.
     */
    default boolean supports(PaymentType type) {
        return true;
    }

    /**
     * Validate payment before processing.
     * Default implementation provided.
     */
    default ValidationResult validate(Payment payment) {
        if (payment == null) {
            return ValidationResult.invalid("Payment cannot be null");
        }
        if (payment.amount().compareTo(BigDecimal.ZERO) <= 0) {
            return ValidationResult.invalid("Amount must be positive");
        }
        return ValidationResult.valid();
    }

    /**
     * Get processor name for logging.
     */
    String getProcessorName();
}

// Implementation only needs to implement what it specializes
@Service
@Qualifier("stripe")
public class StripePaymentProcessor implements PaymentProcessor {

    @Override
    public PaymentResult process(Payment payment) {
        if (!validate(payment).isValid()) {
            return PaymentResult.failure("Invalid payment");
        }
        // Stripe-specific implementation
        return new PaymentResult(Status.SUCCESS, "txn_xxx");
    }

    @Override
    public RefundResult refund(Payment payment) {
        return new RefundResult(Status.SUCCESS, "re_xxx");
    }

    @Override
    public boolean supports(PaymentType type) {
        return type == PaymentType.CREDIT_CARD;
    }

    @Override
    public String getProcessorName() {
        return "Stripe";
    }
}

// Chaining processors - compose them!
@Service
public class CompositePaymentProcessor implements PaymentProcessor {

    private final List<PaymentProcessor> processors;

    public CompositePaymentProcessor(List<PaymentProcessor> processors) {
        this.processors = processors;
    }

    @Override
    public PaymentResult process(Payment payment) {
        PaymentProcessor processor = processors.stream()
            .filter(p -> p.supports(payment.type()))
            .findFirst()
            .orElseThrow(() -> new UnsupportedOperationException("No processor for " + payment.type()));

        return processor.process(payment);
    }

    // Default implementations delegate to first supporting processor
}
```

---

### Use Case: Item 22 — Static Nested Classes in Spring

**Scenario:** You have a `UserService` that needs to build complex queries with multiple criteria.

**Problem without this item:**
- Nonstatic inner classes hold unnecessary reference to outer service
- Memory leaks if query builders escape to other threads
- Confusion about what fields are accessible

**Solution:** Use static nested classes:

```java
@Service
public class UserService {

    private final UserRepository userRepository;

    public UserService(UserRepository userRepository) {
        this.userRepository = userRepository;
    }

    // STATIC: Doesn't need UserService instance
    public static class UserQuery {
        private String name;
        private String email;
        private List<String> roles;
        private Integer minAge;
        private Integer maxAge;

        public UserQuery name(String name) { this.name = name; return this; }
        public UserQuery email(String email) { this.email = email; return this; }
        public UserQuery roles(List<String> roles) { this.roles = roles; return this; }
        public UserQuery ageRange(Integer min, Integer max) {
            this.minAge = min; this.maxAge = max; return this;
        }

        public Specification<User> toSpecification() {
            return (root, query, cb) -> {
                List<Predicate> predicates = new ArrayList<>();

                if (name != null) {
                    predicates.add(cb.like(root.get("name"), "%" + name + "%"));
                }
                if (email != null) {
                    predicates.add(cb.equal(root.get("email"), email));
                }
                if (roles != null && !roles.isEmpty()) {
                    predicates.add(root.get("roles").in(roles));
                }
                if (minAge != null) {
                    predicates.add(cb.greaterThanOrEqualTo(root.get("age"), minAge));
                }
                if (maxAge != null) {
                    predicates.add(cb.lessThanOrEqualTo(root.get("age"), maxAge));
                }

                return cb.and(predicates.toArray(new Predicate[0]));
            };
        }
    }

    public UserQuery query() {
        return new UserQuery();  // Factory method
    }

    public List<User> find(UserQuery query) {
        return userRepository.findAll(query.toSpecification());
    }
}

// Usage - clean and clear
@Service
public class UserSearchService {

    private final UserService userService;

    public List<User> search(String name, List<String> roles) {
        UserService.UserQuery query = userService.query()
            .name(name)
            .roles(roles)
            .ageRange(18, 65);

        return userService.find(query);
    }
}
```

---

### Use Case: Item 23 — Sealed Classes Instead of Tagged Classes

**Scenario:** Modeling different types of orders in an e-commerce system.

**Problem without this item:**
- Tagged class with `orderType` field is error-prone
- Easy to forget handling a type in switch statements
- No compile-time safety for exhaustive matching

**Solution:** Use sealed classes (Java 17+):

```java
// Sealed interface - defines the hierarchy
public sealed interface Order permits
        StandardOrder, ExpressOrder, SubscriptionOrder {

    String getId();
    Money getTotal();
    Instant getCreatedAt();

    // Common behavior
    default boolean isActive() {
        return getCreatedAt().isAfter(Instant.now().minusSeconds(30 * 24 * 60 * 60));
    }
}

// Final class - standard order
public final class StandardOrder implements Order {
    private final String id;
    private final Money total;
    private final Instant createdAt;
    private final List<OrderItem> items;

    public StandardOrder(String id, Money total, List<OrderItem> items) {
        this.id = id;
        this.total = total;
        this.createdAt = Instant.now();
        this.items = List.copyOf(items);
    }

    // Accessors
    public String getId() { return id; }
    public Money getTotal() { return total; }
    public Instant getCreatedAt() { return createdAt; }
    public List<OrderItem> getItems() { return items; }
}

// Final class - express order
public final class ExpressOrder implements Order {
    private final String id;
    private final Money total;
    private final Instant createdAt;
    private final Instant deliveryDeadline;

    public ExpressOrder(String id, Money total, Instant deliveryDeadline) {
        this.id = id;
        this.total = total;
        this.createdAt = Instant.now();
        this.deliveryDeadline = deliveryDeadline;
    }

    public String getId() { return id; }
    public Money getTotal() { return total; }
    public Instant getCreatedAt() { return createdAt; }
    public Instant getDeliveryDeadline() { return deliveryDeadline; }
}

// Final class - subscription order
public final class SubscriptionOrder implements Order {
    private final String id;
    private final Money total;
    private final Instant createdAt;
    private final Period billingPeriod;

    public SubscriptionOrder(String id, Money total, Period billingPeriod) {
        this.id = id;
        this.total = total;
        this.createdAt = Instant.now();
        this.billingPeriod = billingPeriod;
    }

    public String getId() { return id; }
    public Money getTotal() { return total; }
    public Instant getCreatedAt() { return createdAt; }
    public Period getBillingPeriod() { return billingPeriod; }
}

// Exhaustive switch - compiler ensures all cases handled!
class OrderProcessor {

    public String getShippingLabel(Order order) {
        return switch (order) {
            case StandardOrder so -> formatStandard(so);
            case ExpressOrder eo -> formatExpress(eo);
            case SubscriptionOrder so -> formatSubscription(so);
            // Compiler error if you forget a case!
        };
    }
}
```

---

## Framework Quick Reference

| Pattern | Spring | Hibernate/JPA | Jackson | Guava |
|---------|--------|---------------|---------|-------|
| Immutable DTO | `@Value` | - | Records | `ImmutableList` |
| Composition | `@Bean` delegation | `Wrapper` entities | `@JsonDeserialize` | `ForwardingList` |
| Static Factory | `@Bean` methods | `EntityManager` | `@JsonCreator` | `Lists.newArrayList()` |
| Interface default | `default` methods | - | - | `FluentIterable` |
| Sealed classes | Record DTOs | - | `@JsonSubTypes` | - |

---

## Key Takeaways

1. **Spring loves interfaces** — use them for all contracts
2. **Records are perfect for DTOs** — embrace immutability
3. **Composition over inheritance** — especially for cross-cutting concerns
4. **Static nested classes** for builders, queries, and DTOs
5. **Sealed classes** replace tagged classes elegantly
