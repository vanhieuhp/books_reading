# Chapter 3: Methods Common to All Objects — Use Cases

> Real-world scenarios in Spring Boot microservices where these methods matter.

---

## Use Case: Item 10 & 11 — Entity Equality in JPA/Hibernate

**Scenario:** You're building an Order Management microservice with JPA entities. You override `equals` and `hashCode` for an `Order` entity.

**Problem without this item:**
```java
// Entity without proper equals/hashCode
@Entity
public class Order {
    @Id @GeneratedValue
    private Long id;
    private String orderNumber;
    private BigDecimal total;

    // NO equals/hashCode!
}

// Problem in code:
Order order1 = new Order();
order1.setId(1L);
order1.setOrderNumber("ORD-001");

Order order2 = new Order();
order2.setId(1L);
order2.setOrderNumber("ORD-001");

Set<Order> orders = new HashSet<>();
orders.add(order1);
orders.contains(order2);  // FALSE! Different object identity

// Also: Hibernate session issues!
// Entity in persistence context:
// order1 and order2 are different objects, but represent same database row
```

**Solution:**
```java
@Entity
public class Order {
    @Id @GeneratedValue
    private Long id;
    private String orderNumber;
    private BigDecimal total;

    // Use ID-based equality for JPA entities
    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof Order)) return false;
        Order other = (Order) o;
        return id != null && id.equals(other.id);
    }

    @Override
    public int hashCode() {
        // Use a constant for new entities (id == null)
        return getClass().hashCode();
    }
}
```

**Framework mapping:**
- **JPA/Hibernate:** Entity equality should be ID-based (after persistence)
- **Spring Data:** `Repository.save()` uses equals/hashCode for merge vs persist decisions
- **Why it matters:** Without proper equals, `HashSet<Order>` in your service layer breaks

---

## Use Case: Item 12 — Logging in Spring Boot

**Scenario:** You're debugging a production issue. An order failed to process, but the log shows only the default `Order@163b91`.

**Problem without this item:**
```java
// Controller
@RestController
public class OrderController {

    @PostMapping("/orders")
    public ResponseEntity<Order> createOrder(@RequestBody OrderRequest req) {
        Order order = orderService.process(req);
        log.info("Created order: {}", order);  // Useless log!
        return ResponseEntity.ok(order);
    }
}

// Service
@Service
public class OrderService {
    public Order process(OrderRequest req) {
        // Processing logic...
        if (failed) {
            log.error("Order failed: {}", order);  // Order@7a81197d
            // What order? Which customer? How much?
            throw new OrderProcessingException("Failed");
        }
    }
}

// Log output:
// ERROR: Order failed: com.myapp.Order@1a2b3c4d
// ↑ Completely useless for debugging!
```

**Solution:**
```java
@Entity
public class Order {
    @Id @GeneratedValue
    private Long id;
    private String orderNumber;
    private String customerName;
    private BigDecimal total;
    private OrderStatus status;

    @Override
    public String toString() {
        return String.format(
            "Order{id=%d, orderNumber='%s', customer='%s', total=%s, status=%s}",
            id, orderNumber, customerName, total, status
        );
    }
}

// OR use Lombok:
@ToString(of = {"id", "orderNumber", "customerName", "total", "status"})
@Entity
public class Order { ... }

// Now log output is useful:
// INFO: Created order: Order{id=123, orderNumber='ORD-001, customer='Acme Corp', total=99.99, status=PROCESSED}
// ERROR: Order failed: Order{id=456, orderNumber='ORD-002', customer='TechCo', total=1500.00, status=FAILED}
```

**Framework mapping:**
- **Spring Boot:** `log.info("{}", object)` calls toString
- **Jackson:** Serializes objects to JSON — good toString = readable JSON logs
- **Actuator:** `/health` endpoint shows entity info in thread dumps

---

## Use Case: Item 13 — Copying DTOs in REST APIs

**Scenario:** You need to create a copy of a request object to modify it during processing without affecting the original.

**Problem without this item:**
```java
// Request DTO
public class OrderRequest {
    private String customerName;
    private List<OrderItemDto> items;
    private String promoCode;

    // Getters, setters...
}

// Service - accidentally mutates the request
@Service
public class OrderService {
    public Order processOrder(OrderRequest request) {
        // Developer adds a default item to "fix" missing data
        request.getItems().add(defaultItem());  // Mutates original!

        // Later code expects original request...
        // Bug: original request is now modified!
    }
}
```

**Solution:**
```java
// Use a copy constructor or builder
public class OrderRequest {
    private String customerName;
    private List<OrderItemDto> items;
    private String promoCode;

    // Regular constructor
    public OrderRequest(String customerName, List<OrderItemDto> items, String promoCode) {
        this.customerName = customerName;
        this.items = new ArrayList<>(items);  // Defensive copy
        this.promoCode = promoCode;
    }

    // Copy constructor - the safe pattern
    public OrderRequest(OrderRequest other) {
        this.customerName = other.customerName;
        this.items = new ArrayList<>(other.items);  // Deep copy of list!
        this.promoCode = other.promoCode;
    }

    // OR use record (Java 16+)
    public record OrderRequest(String customerName, List<OrderItemDto> items, String promoCode) {
        // Records are immutable - no copy needed!
    }
}

@Service
public class OrderService {
    public Order processOrder(OrderRequest request) {
        // Create a working copy
        OrderRequest workingCopy = new OrderRequest(request);

        // Modify freely
        workingCopy.getItems().add(defaultItem());

        // Original request is untouched
    }
}
```

**Framework mapping:**
- **Spring MVC:** `@RequestBody` objects are shared — defensive copy before modifying
- **Feign Client:** Responses are shared — copy before mutation

---

## Use Case: Item 14 — Sorting in Spring Data

**Scenario:** You need to sort queries in a Spring Data repository and use custom ordering in business logic.

**Problem without this item:**
```java
// Entity
@Entity
public class Product {
    private String name;
    private BigDecimal price;
    private Integer stock;
    // No compareTo!
}

// Repository
public interface ProductRepository extends JpaRepository<Product, Long> {
    List<Product> findByCategory(String category, Sort sort);
}

// Service - broken sorting!
@Service
public class ProductService {
    public List<Product> getProducts(String category) {
        // User wants sorted by price - but compareTo isn't defined!
        // This relies on natural ordering which doesn't exist
        return productRepo.findByCategory(category, Sort.by("price"));
    }

    // TreeSet use case - broken natural ordering
    public void cacheProducts(Set<Product> products) {
        // TreeSet needs compareTo for ordering!
        // But Product doesn't implement Comparable
        Set<Product> cached = new TreeSet<>(products);  // May throw ClassCastException!
    }
}
```

**Solution:**
```java
@Entity
public class Product implements Comparable<Product> {
    private String name;
    private BigDecimal price;
    private Integer stock;

    // Natural ordering: by name, then price
    @Override
    public int compareTo(Product other) {
        int result = this.name.compareTo(other.name);
        if (result != 0) return result;
        // Use BigDecimal.compareTo for proper ordering (not equals!)
        return this.price.compareTo(other.price);
    }
}

// OR use a separate Comparator for flexibility
@Service
public class ProductService {
    // Sort by price ascending
    public List<Product> getProductsByPrice(String category) {
        return productRepo.findByCategory(category,
            Sort.by(Sort.Direction.ASC, "price"));
    }

    // Complex sort: category, then price, then name
    public List<Product> getProductsComplex(String category) {
        return productRepo.findByCategory(category,
            Sort.by(
                Sort.Direction.ASC, "category",
                Sort.Direction.ASC, "price",
                Sort.Direction.ASC, "name"
            ));
    }

    // TreeSet with explicit comparator
    public TreeSet<Product> cacheWithComparator() {
        Comparator<Product> byPrice = Comparator
            .comparing(Product::getPrice)
            .thenComparing(Product::getName);
        return new TreeSet<>(byPrice);
    }
}
```

**Framework mapping:**
- **Spring Data JPA:** `Sort.by("field")` uses property paths, not compareTo
- **TreeSet/TreeMap:** Use compareTo when no Comparator provided
- **Collections.sort():** Uses compareTo
- **Stream.sorted():** Can use natural ordering or provide Comparator

---

## Use Case: Caching with hashCode — Redis/Hazelcast

**Scenario:** You're implementing a distributed cache. Objects used as cache keys must have proper hashCode.

**Problem without this item:**
```java
// Cache key without proper equals/hashCode
public class CacheKey {
    private String tableName;
    private Long entityId;

    // equals uses both fields, but hashCode is broken!
    @Override
    public boolean equals(Object o) {
        if (!(o instanceof CacheKey)) return false;
        CacheKey other = (CacheKey) o;
        return tableName.equals(other.tableName) && entityId.equals(other.entityId);
    }

    // BUG: hashCode doesn't include entityId!
    @Override
    public int hashCode() {
        return tableName.hashCode();  // WRONG!
    }
}

// Using with Hazelcast/Redis:
@Service
public class CacheService {
    @Cacheable(value = "entities", key = "new CacheKey(#tableName, #id)")
    public Object getEntity(String tableName, Long id) {
        return db.find(tableName, id);
    }
}

// Problem:
// CacheKey("users", 1L) and CacheKey("users", 2L) have SAME hashCode!
// They go to same bucket - cache lookup fails silently!
```

**Solution:**
```java
public class CacheKey {
    private final String tableName;
    private final Long entityId;

    public CacheKey(String tableName, Long entityId) {
        this.tableName = tableName;
        this.entityId = entityId;
    }

    @Override
    public boolean equals(Object o) {
        if (!(o instanceof CacheKey)) return false;
        CacheKey other = (CacheKey) o;
        return Objects.equals(tableName, other.tableName)
            && Objects.equals(entityId, other.entityId);
    }

    @Override
    public int hashCode() {
        return Objects.hash(tableName, entityId);  // Correct!
    }
}

// OR use record (Java 16+):
public record CacheKey(String tableName, Long entityId) {}
    // Auto-generates correct equals and hashCode!
```

**Framework mapping:**
- **Hazelcast/Redis:** Keys must honor equals/hashCode contract
- **ConcurrentHashMap:** Cache implementation uses hashCode for bucketing
- **Guava Cache:** Same requirement

---

## Summary: Spring Boot Framework Mapping

| Method | Spring/Hibernate Context | Common Pitfall |
|--------|-------------------------|----------------|
| `equals` | JPA entities, Set operations | Using business fields instead of ID for entities |
| `hashCode` | Cache keys, HashSet/Map | Inconsistent with equals — objects "lost" in cache |
| `toString` | Logging, exceptions, JSON | Default `@hex` useless in production logs |
| `clone` | DTO copying | Avoid — use copy constructors instead |
| `compareTo` | TreeSet, Collections.sort | Not implementing for sortable entities |
