# Chapter 5: Generics — Explain Why

> **Core Theme:** Build deep understanding of the JVM and language mechanics behind each rule. Explain "what goes wrong" with specific failure modes. Use analogies for abstract concepts.

---

## The Foundation: Type Erasure

Every generic type in Java undergoes **type erasure** at runtime. This means:
- `List<String>` becomes just `List` at runtime
- `Map<Long, User>` becomes `Map`
- Type parameters `<T>` become `Object` (or the bound, like `Comparable<T>` → `Comparable`)

This is called **type erasure** and it's why generics are sometimes called "syntactic sugar" — they exist only at compile time.

### Why does Java do this?

**Backward compatibility.** Generics were added in Java 5 (2004), and the JVM couldn't be changed. So the compiler handles all the type checking, and the JVM just sees the raw types.

Think of it like a translator at a UN conference. The translator (compiler) checks that everyone is speaking the same language. But once the speech gets into the room (runtime), there's no translator — everyone just hears the original language. That's type erasure.

---

## Why Raw Types Are Dangerous (Item 26)

When you use a raw type like `List` instead of `List<String>`, you're telling the compiler: "I know what I'm doing, don't check."

```java
List rawList = new ArrayList();
rawList.add(42);           // Adds an Integer
rawList.add("hello");     // Adds a String

// Later in your code - runtime disaster:
for (String s : rawList) {  // ClassCastException on the Integer!
    System.out.println(s);
}
```

### The Compile-Time Safety Net

The compile-time check is your safety net. Raw types throw away that net. In a Spring Boot app, this could mean a bug in your service layer crashes the whole request.

**Key insight:** The more generic your code, the more bugs the compiler catches. Raw types are like removing all safety guards from a machine.

---

## Why Arrays Don't Mix with Generics (Item 28)

### Arrays are Covariant, Generics are Invariant

**Arrays in Java are reifiable** — they know their component type at runtime:
```java
String[] arr = new String[10];
System.out.println(arr.getClass());  // class [Ljava.lang.String;

// Runtime type check works:
Object[] objArr = arr;  // OK: String[] IS an Object[]
objArr[0] = 42;         // RuntimeException: ArrayStoreException!
```

**But generics are non-reifiable** — the type parameter disappears:
```java
List<String> list = new ArrayList<>();
// At runtime, this is just a List - no type info!

// This doesn't work - generics aren't covariant:
List<Object> objList = list;  // COMPILE ERROR! Even though String IS an Object!
```

### The Type Safety Problem

Imagine if generic arrays were allowed:
```java
// If this were allowed:
List<String>[] stringArray = new List<String>[10];
Object[] objArray = stringArray;  // Covariance!

objArray[0] = new ArrayList<Integer>();  // Add Integer list!
String s = stringArray[0].get(0);  // ClassCastException!
```

**The workaround:** Use `Object[]` internally in generic classes (like our `Stack<E>` example), but never expose it publicly. The cast inside `pop()` is unchecked but safe because no external code can inject wrong-typed elements.

---

## Bounded Wildcards: The Producer/Consumer Rule (Item 31)

Wildcards exist because **generics are invariant**. Even though `Integer` extends `Number`, `List<Integer>` does NOT extend `List<Number>`.

### Why Invariance Exists

Imagine if it did:
```java
List<Integer> integers = new ArrayList<>();
List<Number> numbers = integers;  // If this were allowed...

numbers.add(3.14);  // Add a Double to what we thought was a List<Integer>!
Integer i = integers.get(0);  // ClassCastException!
```

### How Wildcards Restore Flexibility

Bounded wildcards restore flexibility while maintaining safety:
- `List<? extends Number>` = "A list of some specific subtype of Number"
- `List<? super Integer>` = "A list of some supertype of Integer"

### The Get/Put Principle

| Operation | Wildcard | What You Can Do |
|-----------|----------|-----------------|
| Read (produce) | `? extends T` | Read as T (or Object) |
| Write (consume) | `? super T` | Write T (or subtypes) |
| Both | None (exact type) | Read and write |

**Analogy:** Think of a box with a question mark on it:
- `? extends Number` = "A box labeled 'contains some kind of Number'" — you can take Numbers OUT but can't put anything IN (you don't know what specific type it needs)
- `? super Number` = "A box that accepts Number or its parents" — you can put Numbers IN but when you take things out, you only know it's an Object

---

## Heterogeneous Containers: The Class<T> Pattern (Item 33)

When you need a container that holds different types, the trick is to use `Class<T>` as a **type token**:

```java
// Class<T> carries type information at runtime
public <T> void store(Class<T> type, T item) {
    // type is a runtime representation of the type parameter!
}
```

### Why Class<T> Works

`Class<T>` is special because:
1. It's reifiable — `Class<String>` exists at runtime (unlike `List<String>`)
2. It provides `cast()` method for safe runtime type checking
3. It's the standard way to bridge compile-time and runtime type info

In Spring, you'll see this pattern everywhere:
- `objectMapper.readValue(json, MyClass.class)`
- `repository.findById(id)`
- Dependency injection uses `Class<T>` tokens

### The cast() Method

```java
public <T> T get(Class<T> type) {
    // Class.cast() performs a runtime check
    return type.cast(favorites.get(type));
}

// vs unchecked cast:
return (T) favorites.get(type);  // DANGEROUS - no runtime check!
```

The difference: `Class.cast()` throws `ClassCastException` if types don't match, while the raw cast might fail silently or in unexpected places.

---

## The Unchecked Cast in Generic Classes

You might wonder: why does our `Stack<E>` use `(E) elements[--size]` if generic arrays are forbidden?

The answer: **it's safe because of how the class is designed.**

No external code can put a wrong-typed element into the stack. The only place elements go in is `push(E e)`, which enforces the type at compile time. So the cast inside `pop()` can never actually fail — it's an "unchecked" warning for technical reasons, but the code is logically type-safe.

This is one of the rare cases where `@SuppressWarnings("unchecked")` is appropriate — inside a generic class, when you've ensured safety through design.

---

## Heap Pollution (Item 32)

Heap pollution occurs when a variable of a parameterized type refers to an object of a different type. This can cause subtle runtime bugs.

### Example of Heap Pollution

```java
List<String> strings = new ArrayList<>();
List rawList = strings;  // Heap pollution: raw List holds String List!
rawList.add(42);        // Adds Integer to what String List!
String s = strings.get(0);  // ClassCastException!
```

### Varargs Complication

When you use varargs with generics:
```java
@SafeVarargs
public static <T> void dangerous(T... elements) {
    Object[] array = elements;  // Heap pollution point!
    array[0] = "corrupted!";   // Can corrupt other references!
}
```

The varargs parameter creates an array internally. If that array escapes (is stored or passed to non-generic code), heap pollution occurs.

---

## Summary: The Mental Model

| Concept | Key Insight |
|---------|-------------|
| Type erasure | Generics exist only at compile time |
| Raw types | Disable all generic safety checks |
| Invariance | `List<String>` is not `List<Object>` |
| PECS | Extends for reading, super for writing |
| Type tokens | `Class<T>` bridges compile and runtime |
| Heap pollution | When generic and raw types mix incorrectly |

**The bottom line:** Generics give you compile-time safety. Every time you bypass them (raw types, unchecked casts, unsafe varargs), you're trading that safety for convenience. Make that trade consciously.
