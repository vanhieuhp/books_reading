# Chapter 4: Classes and Interfaces

## Items 15–25

---

## 🏋️ Module 4: Exercises

Practice makes permanent. These exercises are designed to reinforce the principles through hands-on coding.

---

### Exercise 1 — Refactoring to Immutability [Intermediate]

**Problem:** The `UserProfile` class is mutable and not thread-safe. Refactor it to be immutable.

**Starter code:**

```java
public class UserProfile {
    private String username;
    private String email;
    private List<String> permissions;
    private LocalDateTime createdAt;

    public UserProfile(String username, String email) {
        this.username = username;
        this.email = email;
        this.permissions = new ArrayList<>();
        this.createdAt = LocalDateTime.now();
    }

    public void setUsername(String username) { this.username = username; }
    public void setEmail(String email) { this.email = email; }

    public void addPermission(String permission) {
        this.permissions.add(permission);
    }

    public String getUsername() { return username; }
    public String getEmail() { return email; }
    public List<String> getPermissions() { return permissions; }
    public LocalDateTime getCreatedAt() { return createdAt; }
}
```

**What you need to do:**
1. Make the class immutable (final class, private final fields, no setters)
2. Add validation in the constructor
3. Add a `withPermission()` method that returns a NEW instance with the added permission
4. Ensure the `permissions` list is properly encapsulated (defensive copy)
5. Add a static factory method with validation

**Expected outcome:**

```java
// Usage example
UserProfile profile = UserProfile.create("john", "john@example.com");
UserProfile adminProfile = profile.withPermission("ADMIN");

// Original is unchanged
assert profile.getPermissions().size() == 0;
assert adminProfile.getPermissions().size() == 1;

// Thread-safe - can be safely shared
```

**Hint:** Use `List.copyOf()` for immutable lists, and create new instances for modifications.

---

### Exercise 2 — Fixing Inheritance Issues [Advanced]

**Problem:** The `SecureHashSet` extends `HashSet` and overrides methods, but it has a subtle bug. Find and fix it.

**Starter code:**

```java
public class SecureHashSet<E> extends HashSet<E> {

    private int addOperations = 0;

    @Override
    public boolean add(E e) {
        addOperations++;
        return super.add(e);
    }

    @Override
    public boolean addAll(Collection<? extends E> c) {
        addOperations += c.size();
        return super.addAll(c);
    }

    public int getAddOperations() { return addOperations; }
}

// Test it
public class TestSecureHashSet {
    public static void main(String[] args) {
        SecureHashSet<String> set = new SecureHashSet<>();

        // Test 1: Add single element
        set.add("a");
        System.out.println("After add: " + set.getAddOperations()); // Should be 1

        // Test 2: Add collection
        set.addAll(Arrays.asList("b", "c"));
        System.out.println("After addAll: " + set.getAddOperations()); // Should be 3

        // Test 3: BUG - Add empty collection!
        set.addAll(Arrays.asList());
        System.out.println("After empty addAll: " + set.getAddOperations()); // BUG: Shows 3, should be 3!
    }
}
```

**What you need to do:**
1. Identify the bug when adding an empty collection (the counter still increments even though nothing was added!)
2. Explain why this happens
3. Refactor using **composition** instead of inheritance to fix this properly

**Expected outcome:** After fixing, adding an empty collection should NOT increment the counter.

**Hint:** What if `addAll` adds fewer elements than requested (e.g., duplicates)? Count the actual added elements, not the requested size.

---

### Exercise 3 — Design a Value Object [Beginner]

**Problem:** Design an immutable `Address` value object for a shipping system.

**Starter code:**

```java
// TODO: Design this class
public class Address {
    // TODO: Add fields: street, city, state, zipCode, country
    // TODO: Make it immutable
    // TODO: Add validation
    // TODO: Add equals/hashCode
}
```

**What you need to do:**
1. Add fields for US-style address (street1, street2, city, state, zipCode, country)
2. Make it immutable:
   - `private final` fields
   - No setters
   - Defensive copies for any mutable fields
3. Add validation in constructor:
   - Street cannot be blank
   - City cannot be blank
   - State must be 2-letter code (e.g., "CA", "NY")
   - ZipCode must be 5 digits
   - Country must be valid ISO code
4. Implement proper `equals()` and `hashCode()` based on value
5. Add a factory method `from(String address)` that parses a multi-line address string
6. Add a `toShippingLabel()` method that formats the address for shipping

**Expected outcome:**

```java
Address addr = Address.builder()
    .street("123 Main St")
    .city("San Francisco")
    .state("CA")
    .zipCode("94102")
    .country("US")
    .build();

System.out.println(addr.toShippingLabel());
// 123 Main St
// San Francisco, CA 94102
// UNITED STATES
```

**Hint:** Use `java.time.Country` or validate against a set of valid codes.

---

### Exercise 4 — Interface Design with Default Methods [Advanced]

**Problem:** Design a notification system interface that supports multiple notification types.

**Starter code:**

```java
public interface NotificationService {
    // TODO: Define methods for sending notifications
}
```

**What you need to do:**
1. Define an interface with methods for:
   - `sendNotification(User user, String message)`
   - `sendEmail(Email email)`
   - `sendSms(PhoneNumber phone, String message)`
   - `sendPushNotification(Device device, String message)`
2. Add default methods for:
   - A `validate()` method that checks user/email/phone validity
   - A `batchSend()` method that sends to multiple users
3. Create two implementations:
   - `EmailNotificationService` - simulates email sending
   - `MultiChannelNotificationService` - combines email, SMS, push
4. Demonstrate how Spring would inject different implementations

**Expected outcome:** Should have a clean interface with sensible defaults, and multiple implementations that can be swapped.

---

### Exercise 5 — Debug: The Memory Leak [Advanced]

**Problem:** This Spring component has a memory leak. Find and fix it.

**Starter code:**

```java
@Component
public class OrderCache {

    private Map<String, Order> cache = new HashMap<>();

    public void addOrder(Order order) {
        cache.put(order.getId(), order);
    }

    public Order getOrder(String id) {
        return cache.get(id);
    }

    // This inner class is the problem!
    public class OrderIterator implements Iterator<Order> {

        private Iterator<Map.Entry<String, Order>> iterator;

        public OrderIterator() {
            this.iterator = cache.entrySet().iterator();
        }

        @Override
        public boolean hasNext() {
            return iterator.hasNext();
        }

        @Override
        public Order next() {
            return iterator.next().getValue();
        }
    }

    public OrderIterator iterator() {
        return new OrderIterator();
    }
}
```

**What you need to do:**
1. Identify the memory leak
2. Explain why it happens
3. Fix it using static nested class
4. Consider thread-safety issues in the cache itself

**Expected outcome:** The class should not hold unnecessary references to the enclosing `OrderCache` instance.

---

## Solution Outlines

### Exercise 1 — Immutability Solution

```java
public final class UserProfile {

    private final String username;
    private final String email;
    private final List<String> permissions;
    private final LocalDateTime createdAt;

    private UserProfile(String username, String email, List<String> permissions, LocalDateTime createdAt) {
        this.username = username;
        this.email = email;
        this.permissions = permissions;
        this.createdAt = createdAt;
    }

    public static UserProfile create(String username, String email) {
        Objects.requireNonNull(username, "Username cannot be null");
        Objects.requireNonNull(email, "Email cannot be null");
        if (username.isBlank()) throw new IllegalArgumentException("Username cannot be blank");
        if (!email.contains("@")) throw new IllegalArgumentException("Invalid email");

        return new UserProfile(username, email, List.of(), LocalDateTime.now());
    }

    // Returns NEW instance with added permission
    public UserProfile withPermission(String permission) {
        List<String> newPermissions = new ArrayList<>(this.permissions);
        newPermissions.add(permission);
        return new UserProfile(this.username, this.email,
            List.copyOf(newPermissions), this.createdAt);
    }

    // Getters (no setters!)
}
```

### Exercise 2 — Composition Solution

```java
public class SecureHashSet<E> implements Set<E> {

    private final Set<E> delegate;
    private int addOperations = 0;

    public SecureHashSet(Set<E> delegate) {
        this.delegate = delegate;
    }

    @Override
    public boolean add(E e) {
        if (delegate.add(e)) {
            addOperations++;
            return true;
        }
        return false;
    }

    @Override
    public boolean addAll(Collection<? extends E> c) {
        int countBefore = addOperations;
        boolean modified = delegate.addAll(c);
        addOperations = countBefore + (modified ? c.size() : 0);
        return modified;
    }

    // Forward all other methods...
}
```

---

## Difficulty Legend

| Symbol | Meaning |
|--------|---------|
| [Beginner] | Basic concept application |
| [Intermediate] | Requires combining multiple concepts |
| [Advanced] | Complex design decisions, hidden bugs |

---

## Next Steps

After completing these exercises:
- Review your solutions against the guidelines in Module 1
- Compare with the code examples in Module 2
- Apply these patterns in your next coding task
