# Chapter 3: Methods Common to All Objects — Exercises

> Hands-on practice to reinforce your understanding of equals, hashCode, toString, clone, and compareTo.

---

## Exercise 1 — Identify the Contract Violation [Intermediate]

**Problem:** Given a broken `equals` implementation, identify which of the 5 properties (Reflexive, Symmetric, Transitive, Consistent, Non-null) is violated.

**Starter code:**

```java
// This is a simplified version of a common bug
public class Point {
    private final int x;
    private final int y;

    public Point(int x, int y) {
        this.x = x;
        this.y = y;
    }

    // BUGGY equals implementation
    @Override
    public boolean equals(Object o) {
        if (o == null) return false;
        if (!(o instanceof Point)) return false;
        Point other = (Point) o;
        // Only compares x, ignoring y!
        return this.x == other.x;
    }

    // Missing hashCode - what else is wrong here?
}

// Test it:
public class ContractViolationTest {
    public static void main(String[] args) {
        Point p1 = new Point(1, 1);
        Point p2 = new Point(1, 2);
        Point p3 = new Point(1, 3);

        // Which contracts are broken?
        System.out.println("p1.equals(p1) = " + p1.equals(p1));           // Should be true
        System.out.println("p1.equals(p2) = " + p1.equals(p2));           // false (different y)
        System.out.println("p2.equals(p1) = " + p2.equals(p1));           // false (different y)

        // Transitivity test:
        // p1.equals(p2) = false, p2.equals(p3) = false
        // p1.equals(p3) = ?
        System.out.println("p1.equals(p3) = " + p1.equals(p3));
    }
}
```

**What you need to do:**
1. Run the code and note which contract properties are violated
2. Explain WHY each violated property causes problems
3. Fix the equals method to satisfy all 5 properties

**Expected outcome:**
- Reflexive: ✓ (true)
- Symmetric: ✓ (both directions return same result)
- Transitive: ✓ (if A=B and B=C, then A=C)
- Consistent: ✓ (repeated calls return same result)
- Non-null: ✓ (equals(null) returns false)

---

## Exercise 2 — Implement hashCode Correctly [Intermediate]

**Problem:** Write a correct `hashCode` method for a 3-field class without using `Objects.hash()`.

**Starter code:**

```java
import java.util.*;

public class Employee {
    private final String name;
    private final int employeeId;
    private final Department department;

    public Employee(String name, int employeeId, Department department) {
        this.name = name;
        this.employeeId = employeeId;
        this.department = department;
    }

    // equals uses all three fields
    @Override
    public boolean equals(Object o) {
        if (!(o instanceof Employee)) return false;
        Employee other = (Employee) o;
        return Objects.equals(name, other.name)
            && employeeId == other.employeeId
            && Objects.equals(department, other.department);
    }

    // TODO: Implement hashCode manually (NOT Objects.hash!)
    // Must be consistent with equals!
    // Hint: Start with a prime, multiply by 31, add each field's hash

    // Getters...
    public String getName() { return name; }
    public int getEmployeeId() { return employeeId; }
    public Department getDepartment() { return department; }
}

enum Department { ENGINEERING, SALES, MARKETING, HR }

public class HashCodeTest {
    public static void main(String[] args) {
        Employee e1 = new Employee("Alice", 100, Department.ENGINEERING);
        Employee e2 = new Employee("Alice", 100, Department.ENGINEERING);
        Employee e3 = new Employee("Alice", 100, Department.SALES);

        // Test: equal objects must have equal hash codes
        System.out.println("e1.equals(e2): " + e1.equals(e2));
        System.out.println("e1.hashCode() == e2.hashCode(): " + (e1.hashCode() == e2.hashCode()));

        // Test: different objects CAN have same hash (collision OK)
        System.out.println("e1.equals(e3): " + e1.equals(e3));
        System.out.println("e1.hashCode() == e3.hashCode(): " + (e1.hashCode() == e3.hashCode()));

        // Test: HashSet contains check
        Set<Employee> set = new HashSet<>();
        set.add(e1);
        System.out.println("Set contains e2: " + set.contains(e2));  // Must be true!
    }
}
```

**What you need to do:**
1. Implement `hashCode()` using the classic formula: `result = 31 * result + fieldHash`
2. Handle null fields safely (use `Objects.hashCode()` or ternary)
3. Verify the HashSet test passes

**Expected outcome:**
- `e1.equals(e2)` = true, `e1.hashCode() == e2.hashCode()` = true
- `set.contains(e2)` = true

---

## Exercise 3 — Refactor Cloneable to Copy Constructor [Advanced]

**Problem:** Refactor a class that implements `Cloneable` to use a safer copy constructor pattern.

**Starter code:**

```java
import java.util.*;

// This is a common pattern that's error-prone
public class Order implements Cloneable {
    private String orderId;
    private Customer customer;  // Mutable object!
    private List<OrderItem> items;  // Mutable list!
    private Date createdAt;  // Mutable Date!

    public Order(String orderId, Customer customer, List<OrderItem> items) {
        this.orderId = orderId;
        this.customer = customer;
        this.items = new ArrayList<>(items);  // Defensive copy
        this.createdAt = new Date();  // New object
    }

    // BUGGY clone - shallow copy problem!
    @Override
    public Order clone() {
        try {
            return (Order) super.clone();
            // Problem: customer, items, createdAt are SHARED!
        } catch (CloneNotSupportedException e) {
            throw new AssertionError(e);
        }
    }

    // Mutators that change internal state
    public void addItem(OrderItem item) {
        items.add(item);
    }

    public void updateCustomerName(String name) {
        customer.setName(name);  // Modifies shared object!
    }

    // Getters...
}

class Customer {
    private String name;
    public Customer(String name) { this.name = name; }
    public void setName(String name) { this.name = name; }
    public String getName() { return name; }
}

class OrderItem {
    private String product;
    private int quantity;
    public OrderItem(String product, int quantity) {
        this.product = product;
        this.quantity = quantity;
    }
}
```

**What you need to do:**
1. Create a **copy constructor** that performs deep copies of mutable fields
2. Remove the `Cloneable` implementation and `clone()` method
3. Show that modifying the copy doesn't affect the original

**Expected outcome:**

```java
// Test:
Order original = new Order("O123", new Customer("Acme"),
    Arrays.asList(new OrderItem("Widget", 5)));
Order copy = new Order(original);  // Copy constructor

copy.addItem(new OrderItem("Gadget", 10));
copy.updateCustomerName("NewCorp");

// Original should be unchanged:
System.out.println(original.getItems().size());  // 1 (not 2!)
System.out.println(original.getCustomer().getName());  // "Acme" (not "NewCorp"!)
```

---

## Exercise 4 — Multi-Level Comparator Chain [Beginner]

**Problem:** Write a comparator chain that sorts Person objects by last name, then first name, then age.

**Starter code:**

```java
import java.util.*;

public class Person {
    private final String firstName;
    private final String lastName;
    private final int age;

    public Person(String firstName, String lastName, int age) {
        this.firstName = firstName;
        this.lastName = lastName;
        this.age = age;
    }

    // Getters
    public String getFirstName() { return firstName; }
    public String getLastName() { return lastName; }
    public int getAge() { return age; }

    @Override
    public String toString() {
        return String.format("%s %s (age %d)", firstName, lastName, age);
    }
}

public class ComparatorChainTest {
    public static void main(String[] args) {
        List<Person> people = Arrays.asList(
            new Person("John", "Smith", 30),
            new Person("Jane", "Smith", 25),
            new Person("John", "Smith", 25),
            new Person("Bob", "Adams", 30),
            new Person("Alice", "Adams", 25)
        );

        // TODO: Create comparator that sorts by:
        // 1. Last name (ascending)
        // 2. First name (ascending)
        // 3. Age (ascending)

        // Apply and print
    }
}
```

**What you need to do:**
1. Use `Comparator.comparing()` and `thenComparingInt()`
2. Sort the list
3. Print the sorted output

**Expected output:**
```
Alice Adams (age 25)
Bob Adams (age 30)
John Smith (age 25)
John Smith (age 30)
Jane Smith (age 25)
```

---

## Exercise 5 — Fix the Subtraction Bug [Intermediate]

**Problem:** This comparator has a bug that causes incorrect ordering with extreme values.

**Starter code:**

```java
import java.util.*;

public class Account {
    private final String id;
    private final long balance;  // Can be very large (long, not int!)

    public Account(String id, long balance) {
        this.id = id;
        this.balance = balance;
    }

    public long getBalance() { return balance; }
    public String getId() { return id; }
}

// BUGGY comparator - what's wrong?
class BalanceComparator implements Comparator<Account> {
    @Override
    public int compare(Account a, Account b) {
        // This looks innocent but has a subtle bug!
        return (int) (a.getBalance() - b.getBalance());
    }
}

public class SubtractionBugTest {
    public static void main(String[] args) {
        Account veryNegative = new Account("A", Long.MIN_VALUE);
        Account veryPositive = new Account("B", Long.MAX_VALUE);
        Account zero = new Account("C", 0);

        BalanceComparator cmp = new BalanceComparator();

        System.out.println("MIN vs MAX: " + cmp.compare(veryNegative, veryPositive));
        // Should be negative (MIN < MAX)

        System.out.println("MAX vs MIN: " + cmp.compare(veryPositive, veryNegative));
        // Should be positive (MAX > MIN)

        // Test with TreeSet
        TreeSet<Account> accounts = new TreeSet<>(cmp);
        accounts.add(veryNegative);
        accounts.add(veryPositive);
        accounts.add(zero);

        System.out.println("First: " + accounts.first().getId());  // Should be MIN
        System.out.println("Last: " + accounts.last().getId());    // Should be MAX

        // The ordering might be completely wrong due to overflow!
    }
}
```

**What you need to do:**
1. Run the code and observe what's wrong
2. Fix the comparator using `Long.compare()` instead of subtraction
3. Verify the TreeSet ordering is correct

**Expected outcome:**
- MIN_VALUE < 0 < MAX_VALUE
- TreeSet first = MIN_VALUE, last = MAX_VALUE

---

## Solutions

### Exercise 1 Solution

```java
// Fixed equals - compare ALL significant fields
@Override
public boolean equals(Object o) {
    if (o == null) return false;
    if (!(o instanceof Point)) return false;
    Point other = (Point) o;
    return this.x == other.x && this.y == other.y;
}

// Fixed hashCode - consistent with equals
@Override
public int hashCode() {
    return Objects.hash(x, y);  // Or manual: 31 * x + y
}
```

### Exercise 2 Solution

```java
@Override
public int hashCode() {
    int result = 17;
    result = 31 * result + (name == null ? 0 : name.hashCode());
    result = 31 * result + employeeId;
    result = 31 * result + (department == null ? 0 : department.hashCode());
    return result;
}
```

### Exercise 3 Solution

```java
// Remove Cloneable, add copy constructor
public class Order {
    private String orderId;
    private Customer customer;
    private List<OrderItem> items;
    private Date createdAt;

    // Regular constructor
    public Order(String orderId, Customer customer, List<OrderItem> items) {
        this.orderId = orderId;
        this.customer = new Customer(customer.getName());  // Copy!
        this.items = new ArrayList<>(items);  // Already defensive copy
        this.createdAt = new Date();  // New Date
    }

    // Copy constructor - the safe way to copy!
    public Order(Order other) {
        this.orderId = other.orderId;
        this.customer = new Customer(other.customer.getName());  // Deep copy!
        this.items = new ArrayList<>(other.items);  // New list with same items
        this.createdAt = new Date(other.createdAt.getTime());  // New Date
    }
}
```

### Exercise 4 Solution

```java
Comparator<Person> comparator = Comparator
    .comparing(Person::getLastName)
    .thenComparing(Person::getFirstName)
    .thenComparingInt(Person::getAge);

people.sort(comparator);
people.forEach(System.out::println);
```

### Exercise 5 Solution

```java
// FIXED - use Long.compare!
class BalanceComparator implements Comparator<Account> {
    @Override
    public int compare(Account a, Account b) {
        return Long.compare(a.getBalance(), b.getBalance());
    }
}
```
