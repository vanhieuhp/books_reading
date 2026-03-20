# Chapter 3: Methods Common to All Objects — Code Examples

> Real, production-like code examples showing what NOT to do and how to fix it.

---

## Item 10 — equals Contract Violations

### ❌ Bad — Breaking Symmetry with Type Mixing

```java
// CaseInsensitiveString compares ignoring case, but doesn't respect symmetry with String
public class CaseInsensitiveString {
    private final String value;

    public CaseInsensitiveString(String value) {
        this.value = Objects.requireNonNull(value);
    }

    @Override
    public boolean equals(Object o) {
        // BUG: This is NOT symmetric!
        // "hello".equals(cis) works, but cis.equals("hello") checks instanceof
        if (o instanceof CaseInsensitiveString) {
            return value.equalsIgnoreCase(((CaseInsensitiveString) o).value);
        }
        if (o instanceof String) {  // Mixing types = symmetry broken
            return value.equalsIgnoreCase((String) o);
        }
        return false;
    }
}

// Usage that fails:
CaseInsensitiveString cis = new CaseInsensitiveString("Hello");
String s = "hello";

cis.equals(s);   // true (compares with String)
s.equals(cis);  // false! (String doesn't know about CaseInsensitiveString)

// This breaks List.contains() because it uses the Object's equals
List<CaseInsensitiveString> list = new ArrayList<>();
list.add(cis);
list.contains(s);  // FALSE! Even though cis was added with "Hello"
// List.contains() calls s.equals(cis) = "hello".equals(cis) = false
```

### ✅ Good — Respect Symmetry (or Don't Mix Types)

```java
// Option 1: Don't mix with unrelated types
public final class CaseInsensitiveString {
    private final String value;

    public CaseInsensitiveString(String value) {
        this.value = Objects.requireNonNull(value);
    }

    @Override
    public boolean equals(Object o) {
        // Only compare with our own type - no mixing!
        if (!(o instanceof CaseInsensitiveString)) {
            return false;
        }
        return value.equalsIgnoreCase(((CaseInsensitiveString) o).value);
    }

    @Override
    public int hashCode() {
        // Must be consistent with equals
        return value.toLowerCase().hashCode();
    }
}

// Option 2: Use a record (Java 16+) - auto-generates correct equals
public record CaseInsensitiveString(String value) {
    public CaseInsensitiveString {
        Objects.requireNonNull(value);
    }

    @Override
    public boolean equals(Object o) {
        // Record generates this correctly, but you can override
        return o instanceof CaseInsensitiveString cis
            && value.equalsIgnoreCase(cis.value);
    }

    @Override
    public int hashCode() {
        return value.toLowerCase().hashCode();
    }
}
```

---

## Item 11 — hashCode Contract Violations

### ❌ Bad — Overriding equals but NOT hashCode

```java
// A simple User class - common mistake
public class User {
    private final String email;
    private final String name;

    public User(String email, String name) {
        this.email = email;
        this.name = name;
    }

    // equals overridden correctly
    @Override
    public boolean equals(Object o) {
        if (!(o instanceof User)) return false;
        User other = (User) o;
        return email.equals(other.email);
    }
    // BUG: No hashCode override!
    // Now equals uses email, but hashCode uses default Object.hashCode()
}

// This breaks HashMap/HashSet behavior:
User u1 = new User("alice@example.com", "Alice Smith");
User u2 = new User("alice@example.com", "Alice Jones");  // Equal to u1!

HashSet<User> users = new HashSet<>();
users.add(u1);
users.contains(u2);  // FALSE! Even though u2.equals(u1) is true!

// Why? HashSet looks up by hashCode first:
// - u1's hashCode = some random value (based on memory address)
// - u2's hashCode = different random value
// HashSet can't find u2 because it's in a different bucket!
```

### ✅ Good — Proper hashCode with equals

```java
public class User {
    private final String email;
    private final String name;

    public User(String email, String name) {
        this.email = email;
        this.name = name;
    }

    @Override
    public boolean equals(Object o) {
        if (!(o instanceof User)) return false;
        return email.equals(((User) o).email);
    }

    // Option 1: Use Objects.hash (simple, readable)
    @Override
    public int hashCode() {
        return Objects.hash(email);  // Must match fields in equals!
    }

    // Option 2: Manual computation (faster for hot paths)
    @Override
    public int hashCode() {
        int result = email.hashCode();
        // Don't include name - it's not in equals!
        return result;
    }

    // Option 3: Use a record (Java 16+) - auto-generates both
    // public record User(String email, String name) {}
    // equals checks ALL fields, hashCode generated automatically
}

// Now HashSet works correctly:
User u1 = new User("alice@example.com", "Alice Smith");
User u2 = new User("alice@example.com", "Alice Jones");

HashSet<User> users = new HashSet<>();
users.add(u1);
users.contains(u2);  // TRUE! Same email = same hashCode = found
```

### ✅ Good — Caching Hash Code for Immutable Objects

```java
public final class User {
    private final String email;
    private final String name;
    private final List<Order> orders;  // Could be expensive to hash

    private transient int hashCode;  // Cache for immutable object

    public User(String email, String name, List<Order> orders) {
        this.email = email;
        this.name = name;
        this.orders = List.copyOf(orders);  // Immutable copy
    }

    @Override
    public int hashCode() {
        // Lazy initialization - compute once, cache forever
        if (hashCode == 0) {
            hashCode = Objects.hash(email, name);
        }
        return hashCode;
    }
}
```

---

## Item 12 — toString Contract

### ❌ Bad — Default toString is Useless

```java
// A typical entity class without toString
public class Order {
    private Long id;
    private String customerName;
    private BigDecimal amount;
    private LocalDateTime createdAt;
    private List<OrderItem> items;

    // Getters, setters, business methods...

    // NO toString override!
}

// In production:
Order order = new Order(123L, "Acme Corp", new BigDecimal("9999.99"), ...);
System.out.println(order);
// Output: Order@1a2b3c4d  <-- Completely useless for debugging!

// When this Order fails in processing, you see:
// ERROR: Order@1a2b3c4d failed to process
// Now what? You have NO idea which order, which customer, what amount...
```

### ✅ Good — Useful toString for Debugging

```java
// Option 1: Manual implementation
public class Order {
    private Long id;
    private String customerName;
    private BigDecimal amount;
    private LocalDateTime createdAt;
    private List<OrderItem> items;

    @Override
    public String toString() {
        return "Order{" +
                "id=" + id +
                ", customerName='" + customerName + '\'' +
                ", amount=" + amount +
                ", createdAt=" + createdAt +
                ", itemCount=" + (items != null ? items.size() : 0) +
                '}';
    }

    // For large objects, provide a summary version
    public String toSummary() {
        return String.format("Order#%d (%s: $%s)", id, customerName, amount);
    }
}

// Option 2: Use @ToString from Lombok
@ToString
public class Order {
    @ToString.Exclude  // Exclude from toString
    private Long id;  // Don't expose internal IDs in logs

    private String customerName;
    private BigDecimal amount;

    @ToString.Include(name = "total", rank = 1)  // Custom name, high priority
    private BigDecimal getFormattedAmount() {
        return amount;
    }
}

// Output: Order(customerName=Acme Corp, amount=9999.99, total=$9,999.99)
```

---

## Item 13 — clone() Problems

### ❌ Bad — Implementing Cloneable is Broken

```java
// A Stack class trying to use Cloneable
public class Stack implements Cloneable {
    private Object[] elements;
    private int size = 0;
    private static final int DEFAULT_CAPACITY = 16;

    public Stack() {
        this.elements = new Object[DEFAULT_CAPACITY];
    }

    public void push(Object e) {
        ensureCapacity();
        elements[size++] = e;
    }

    public Object pop() {
        if (size == 0) throw new EmptyStackException();
        return elements[--size];
    }

    private void ensureCapacity() {
        if (elements.length == size) {
            elements = Arrays.copyOf(elements, 2 * elements.length);
        }
    }

    // BUG: clone() does SHALLOW copy by default!
    @Override
    public Stack clone() {
        try {
            return (Stack) super.clone();  // Shallow copy - elements array is shared!
        } catch (CloneNotSupportedException e) {
            throw new AssertionError(e);  // Should never happen
        }
    }
}

// This causes silent data corruption:
Stack original = new Stack();
original.push(new ArrayList<String>());
original.push("hello");

Stack cloned = original.clone();
cloned.pop();  // Removes "hello" from BOTH stacks! (shallow copy)

List<?> list = (List<?>) cloned.pop();
list.add("corrupted");  // Now the original stack's list is corrupted too!
```

### ✅ Good — Use Copy Constructor Instead

```java
// Clean, safe copy using a copy constructor
public final class Stack<E> {
    private final Object[] elements;
    private final int size;

    public Stack() {
        this.elements = new Object[16];
        this.size = 0;
    }

    // Private copy constructor - enforces deep copy
    private Stack(Stack<E> other) {
        // Deep copy: create new array with copied elements
        this.elements = Arrays.copyOf(other.elements, other.elements.length);
        this.size = other.size;
    }

    public void push(E e) {
        Object[] newElements = Arrays.copyOf(elements, elements.length + 1);
        newElements[size++] = e;
        // Return new stack (immutable pattern) or mutate internally
    }

    public E pop() {
        if (size == 0) throw new EmptyStackException();
        @SuppressWarnings("unchecked")
        E result = (E) elements[--size];
        return result;
    }

    // Public copy factory for external use
    public Stack<E> copy() {
        return new Stack<>(this);
    }
}

// Usage:
Stack<Integer> original = new Stack<>();
original.push(42);

Stack<Integer> cloned = original.copy();
cloned.push(100);  // Original is untouched - completely independent

// OR for mutable version, use copy constructor internally:
public Stack(Stack<E> other) {
    this.elements = other.elements.clone();  // Shallow is OK for immutable elements
    this.size = other.size;
}
```

### ✅ Modern — Use record for Immutable Value Types

```java
// Java 16+ record - auto-generates correct equals, hashCode, toString
public record Money(BigDecimal amount, String currency) {
    // Auto-generated:
    // - equals: compares all fields
    // - hashCode: based on all fields
    // - toString: "Money[amount=100, currency=USD]"

    // Add validation
    public Money {
        if (amount == null || amount.compareTo(BigDecimal.ZERO) < 0) {
            throw new IllegalArgumentException("Amount must be non-negative");
        }
    }

    // Add business methods
    public Money add(Money other) {
        if (!this.currency.equals(other.currency)) {
            throw new IllegalArgumentException("Cannot add different currencies");
        }
        return new Money(this.amount.add(other.amount), this.currency);
    }
}

// Immutable - no clone needed!
```

---

## Item 14 — compareTo Pitfalls

### ❌ Bad — Subtraction Overflow

```java
// WRONG: Using subtraction for comparison
public class AgeComparator implements Comparator<Person> {
    @Override
    public int compare(Person a, Person b) {
        // BUG: Overflow with extreme values!
        return a.getAge() - b.getAge();
    }
}

// This fails silently:
Person young = new Person("Young", -2000000000);  // age = -2 billion
Person old = new Person("Old", 2000000000);        // age = 2 billion

int result = young.getAge() - old.getAge();
// Expected: negative (young < old)
// Actual: overflow! Returns POSITIVE because:
// -2,000,000,000 - 2,000,000,000 = -4,000,000,000
// But int can only hold -2,147,483,648 to 2,147,483,647
// So it wraps to positive!

// This breaks TreeSet ordering and binary search!
TreeSet<Person> set = new TreeSet<>(new AgeComparator());
set.add(young);
set.add(old);
set.contains(young);  // May return false - ordering is wrong!
```

### ✅ Good — Using Integer.compare

```java
// CORRECT: Use Integer.compare
public class AgeComparator implements Comparator<Person> {
    @Override
    public int compare(Person a, Person b) {
        // Handles all edge cases correctly, including Integer.MIN_VALUE
        return Integer.compare(a.getAge(), b.getAge());
    }
}

// CORRECT: Use Comparator.comparingInt (Java 8+)
Comparator<Person> byAge = Comparator.comparingInt(Person::getAge);

// CORRECT: Chain comparators for multi-level sorting
Comparator<Person> comparator = Comparator
    .comparing(Person::getLastName)           // Primary: last name
    .thenComparing(Person::getFirstName)       // Secondary: first name
    .thenComparingInt(Person::getAge);        // Tertiary: age

// Usage:
List<Person> people = Arrays.asList(
    new Person("Smith", "John", 30),
    new Person("Smith", "Jane", 25),
    new Person("Smith", "John", 25),  // Same name, different age
    new Person("Adams", "Bob", 30)
);

people.sort(comparator);
// Output: sorted by lastName, then firstName, then age
// [Adams Bob 30, Smith Jane 25, Smith John 25, Smith John 30]
```

### ✅ Good — Proper compareTo Implementation

```java
// Implementing Comparable directly (natural ordering)
public final class PhoneNumber implements Comparable<PhoneNumber> {
    private final int areaCode;
    private final int prefix;
    private final int lineNum;

    public PhoneNumber(int areaCode, int prefix, int lineNum) {
        this.areaCode = areaCode;
        this.prefix = prefix;
        this.lineNum = lineNum;
    }

    @Override
    public int compareTo(PhoneNumber other) {
        // Compare area codes first
        int result = Integer.compare(this.areaCode, other.areaCode);
        if (result != 0) return result;

        // Then prefix
        result = Integer.compare(this.prefix, other.prefix);
        if (result != 0) return result;

        // Finally line number
        return Integer.compare(this.lineNum, other.lineNum);
    }

    // Can also use Comparator for flexibility
    public static final Comparator<PhoneNumber> BY_AREA_CODE =
        Comparator.comparingInt(PhoneNumber::getAreaCode);

    public static final Comparator<PhoneNumber> BY_NUMBER =
        Comparator.comparingInt(PhoneNumber::getAreaCode)
            .thenComparingInt(PhoneNumber::getPrefix)
            .thenComparingInt(PhoneNumber::getLineNum);
}

// TreeSet uses natural ordering by default:
TreeSet<PhoneNumber> contacts = new TreeSet<>();
contacts.add(new PhoneNumber(650, 555, 1234));
contacts.add(new PhoneNumber(650, 555, 0001));
// Ordered correctly: (650) 555-0001 comes before (650) 555-1234
```
