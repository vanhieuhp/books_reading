# Chapter 3: Methods Common to All Objects — Interview Questions

> Prepare for technical interviews with questions that test real understanding of Object methods.

---

## Q1 [Junior] — What is the difference between `==` and `equals()` in Java?

**Tests:** Understanding object identity vs value equality.

**Model answer:** The `==` operator compares object references (memory addresses) by default — it checks if two variables point to the exact same object in memory. The `equals()` method, when overridden, compares the logical content of objects. For example, two different `String` objects containing "hello" would be `==` (false) but `equals()` (true). The default `Object.equals()` simply delegates to `==`, so you must override it for value-based comparison.

**Follow-up:** When should you use `==` instead of `equals()`?

---

## Q2 [Junior] — What are the five properties of the `equals` contract?

**Tests:** Knowing the exact contract that must be maintained.

**Model answer:** The five properties are: **Reflexive** (x.equals(x) must return true), **Symmetric** (if x.equals(y) then y.equals(x)), **Transitive** (if x.equals(y) and y.equals(z), then x.equals(z)), **Consistent** (multiple calls return the same result), and **Non-null** (x.equals(null) must return false). Violating any of these can cause subtle bugs in collections.

**Follow-up:** Which property is hardest to maintain and why?

---

## Q3 [Mid] — Why must you always override `hashCode` when you override `equals`?

**Tests:** Understanding the relationship between equals and hashCode in hash-based collections.

**Model answer:** The contract states that if two objects are equal according to `equals()`, they must have the same `hashCode()`. If you override `equals` but not `hashCode`, the default `Object.hashCode()` (based on memory address) will differ for logically equal objects. This breaks hash-based collections: when you call `hashMap.get(key)` with an object that's equal to an existing key but has a different hashCode, the lookup fails and returns null — the object becomes "invisible" in the collection.

**Follow-up:** Can two unequal objects have the same hashCode?

---

## Q4 [Mid] — What happens if two keys have the same hashCode in a HashMap?

**Tests:** Understanding HashMap's internal bucket collision resolution.

**Model answer:** Java's HashMap uses **chaining** (linked list until Java 8, then balanced tree for O(n) → O(log n) improvement) to handle hash collisions. When two keys have the same hashCode, they go to the same bucket. During lookup, HashMap iterates through the bucket's entries, calling `equals()` on each key to find the exact match. This means collisions cause O(n) lookup within a bucket instead of O(1), but it still works correctly. In Java 8+, if a bucket has more than 8 entries with the same hash, it converts to a tree for O(log n) performance.

**Follow-up:** What's the difference between chaining and open addressing for collision resolution?

---

## Q5 [Mid] — Why is the default `toString()` not useful for debugging?

**Tests:** Understanding what the default toString returns and why it's insufficient.

**Model answer:** The default `Object.toString()` returns `ClassName@hashcode` in hexadecimal (e.g., `Order@7a81197d`). This tells you the class name and the object's hashCode, but nothing about the object's fields or state. In production debugging, seeing `Order@163b91` doesn't tell you which order failed, which customer, or what amount. Overriding toString with meaningful field values (e.g., `Order{id=123, customer="Acme", total=999.99}`) makes logs and error messages actionable.

**Follow-up:** Should you include all fields in toString, or exclude sensitive data?

---

## Q6 [Mid] — Why should you avoid implementing `Cloneable`?

**Tests:** Understanding why Cloneable is considered broken in Java.

**Model answer:** `Cloneable` is a "tagging interface" with no methods — it doesn't define a clone contract. The actual cloning behavior comes from `Object.clone()`, which creates an object without calling any constructor, bypassing validation and initialization logic. It performs a shallow copy, so mutable fields are shared between original and clone. Additionally, `clone()` throws checked `CloneNotSupportedException` even though you're overriding a method that already declares it. The recommended alternative is using copy constructors or copy factories, which are clearer, type-safe, and don't require suppressing exceptions.

**Follow-up:** When might Cloneable still be appropriate?

---

## Q7 [Mid] — What's wrong with using subtraction for integer comparison in compareTo?

**Tests:** Understanding integer overflow in comparison logic.

**Model answer:** Using `return a - b` for integer comparison causes overflow when values are near `Integer.MIN_VALUE`. For example, `Integer.MIN_VALUE - 1` overflows to `Integer.MAX_VALUE`, incorrectly suggesting a very small value is larger than a very large one. This breaks the transitivity property of the compareTo contract and corrupts TreeSet ordering or binary search results. The correct approach is `Integer.compare(a, b)`, which handles all edge cases properly.

**Follow-up:** Does this same problem apply to long values?

---

## Q8 [Senior] — How would you implement equals and hashCode for a JPA entity?

**Tests:** Understanding JPA/Hibernate-specific considerations.

**Model answer:** For JPA entities, use ID-based equality: `equals()` should check if the ID is non-null and equal, while `hashCode()` should return a constant for unsaved entities and the ID's hashCode for persisted ones. This is because JPA entities change state during their lifecycle (transient → managed → detached), and using business fields would cause inconsistent behavior in HashSet/HashMap before and after persistence. The ID is stable after persist and represents true identity in the database.

```java
@Override
public boolean equals(Object o) {
    if (this == o) return true;
    if (o == null || getClass() != o.getClass()) return false;
    Order order = (Order) o;
    return id != null && id.equals(order.id);
}

@Override
public int hashCode() {
    return id != null ? id.hashCode() : getClass().hashCode();
}
```

**Follow-up:** What happens if you use business fields (like orderNumber) for equals in a JPA entity?

---

## Q9 [Senior] — Can you make a mutable object work as a HashMap key? How?

**Tests:** Understanding the relationship between mutability and hashCode stability.

**Model answer:** You can use a mutable object as a HashMap key only if the hashCode remains stable while the object is in the map. This requires that the fields used in hashCode don't change after insertion, or you use `IdentityHashMap` (which uses `==` instead of `equals`/`hashCode`). However, this is generally discouraged because it's error-prone — modifying a key while it's in a HashMap will cause the lookup to fail (returning null) since the hashCode changes but the object stays in the wrong bucket. The safest approach is to use immutable keys.

**Follow-up:** What does IdentityHashMap do differently?

---

## Q10 [Senior] — How does Java 16+ records change how you implement equals/hashCode/toString?

**Tests:** Knowledge of modern Java features.

**Model answer:** Java records automatically generate `equals()`, `hashCode()`, and `toString()` based on all fields. For value objects, this eliminates boilerplate and guarantees correct implementations. Records are also automatically `final` and implement a canonical constructor. This is the recommended approach for DTOs, value objects, and response objects. However, records shouldn't be used for JPA entities (which need mutable ID-based equality) or when you need custom construction logic that's complex.

```java
// Auto-generates equals/hashCode/toString
public record Money(BigDecimal amount, String currency) {}
```

**Follow-up:** Can records implement interfaces or extend other classes?

---

## Q11 [System Design] — Design a cache system that uses custom objects as keys. What considerations must you account for?

**Tests:** System design thinking with Object method implications.

**Model answer:** Key considerations: **(1)** Keys must be immutable or their hashCode must remain stable while cached — otherwise lookups fail. **(2)** equals/hashCode must be correctly implemented to avoid invisible cache entries. **(3)** Consider memory: the key object's memory footprint affects cache density. **(4)** For distributed caches (Redis, Hazelcast), keys need serialization — consider using simple types or ensuring custom equals/hashCode survive serialization. **(5)** For weak references, the key type may need to implement equals/hashCode correctly to enable proper cleanup. **(6)** Consider cache size and eviction — hash collisions affect performance in large caches.

**Follow-up:** How would you handle a scenario where the key object must be mutable?

---

## Q12 [Gotcha] — What does this code output and why?

```java
String s1 = new String("hello");
String s2 = new String("hello");

System.out.println(s1 == s2);
System.out.println(s1.equals(s2));
System.out.println(s1.hashCode() == s2.hashCode());
```

**Tests:** Understanding the difference between == and equals for Strings, and String's hashCode.

**Model answer:** Output is: `false`, `true`, `true`. The `==` operator compares references — s1 and s2 are different objects in memory, so false. The `equals()` method compares content — both contain "hello", so true. String overrides hashCode to be content-based (for consistency with equals), so both have the same hashCode. This is a classic gotcha: beginners often use `==` to compare Strings and get unexpected results.

**Follow-up:** What about `String.intern()` — how does that change things?

---

## Quick Reference Table

| Level | Count | Focus Areas |
|-------|-------|-------------|
| Junior | 2 | Basics: == vs equals, contract properties |
| Mid | 5 | HashMap internals, toString, Cloneable, compareTo overflow, equals/hashCode pairing |
| Senior | 4 | JPA entities, mutability, records, deep understanding |
| System Design | 1 | Cache design with custom keys |
| Gotcha | 1 | Tricky edge case |

---

## Answer Key (for self-study)

| Q# | Answer Summary |
|----|---------------|
| 1 | `==` = reference, `equals()` = value (when overridden) |
| 2 | Reflexive, Symmetric, Transitive, Consistent, Non-null |
| 3 | Equal objects must have equal hashCode — breaks HashMap otherwise |
| 4 | Same bucket → chain (list/tree) → O(n) or O(log n) lookup |
| 5 | Default = `Class@hex` — no state info, useless for debugging |
| 6 | Tag interface, no constructor call, shallow copy, exception handling |
| 7 | Subtraction overflow: MIN_VALUE - 1 → MAX_VALUE (wrong!) |
| 8 | ID-based equality for JPA — business fields break before/after persist |
| 9 | Yes, but hashCode must stay stable, or use IdentityHashMap |
| 10 | Records auto-generate all three — use for value objects |
| 11 | Immutability, equals/hashCode correctness, serialization, memory |
| 12 | false, true, true — reference vs value vs content-based hashCode |
