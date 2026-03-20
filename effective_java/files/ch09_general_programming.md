# Chapter 9: General Programming

## Overview
This chapter covers the practical day-to-day programming decisions that distinguish clear, efficient Java from verbose, buggy, or slow Java. It's the "craft" chapter — how to write each line of code with good judgment.

**Core Theme:** Know the language, know the libraries, and choose the right tool at every level: the right variable scope, the right loop form, the right data type, the right abstraction. Don't reinvent what the JDK already provides.

**Why This Matters:** These items are cumulative. Each one is individually minor, but a codebase that violates all of them becomes difficult to read, profile, and maintain. Strong Java developers internalize these as automatic habits.

---

## Items

### Item 57 — Minimize the scope of local variables
- **Rule:** Declare variables at the point of first use; initialize with a meaningful value; prefer for-loops to while-loops for loop-scoped variables
- **Why:** Narrow scope reduces the chance of accidental reuse, makes code easier to understand, and reduces bugs from variables used outside their intended context
- **For-loop advantage:** Iterator variable scoped to the loop; can reuse variable name `i` in subsequent loops without risk
- **While-loop danger:** Loop variable declared before the loop can accidentally be reused after the loop
- **Minimize declarations:** Extract methods if you need to reduce variable scope significantly

### Item 58 — Prefer for-each loops to traditional for loops
- **Rule:** Use the enhanced for-each loop for all iteration where you don't need the index or explicit iterator control
- **Benefits:** Cleaner, less error-prone (no off-by-one), works for any `Iterable`, hides iterator details
- **The nested loop bug:** `for (int i = 0; i < suits.length; i++) for (int j = 0; j < ranks.length; j++) deck.add(suits[j].of(ranks[i]))` — note the bug: `suits[j]` should be `suits[i]`; for-each makes this impossible
- **When NOT to use for-each:**
  1. Destructive filtering (removing elements during iteration — use `removeIf()`)
  2. Transformation (replacing elements — need index access)
  3. Parallel iteration (iterating multiple collections in lockstep — need explicit iterators)

### Item 59 — Know and use the libraries
- **Rule:** Know the contents of `java.lang`, `java.util`, `java.io` and their subpackages; don't reinvent what's already there
- **The random number bug:** Naïve `Math.abs(random.nextInt()) % n` has two bugs: `Integer.MIN_VALUE` overflows; small n gets skewed distribution. Use `ThreadLocalRandom.current().nextInt(n)`
- **Java 7+:** Use `ThreadLocalRandom` (not `Random`) for performance; use `SecureRandom` for security-sensitive contexts
- **Know Collections:** `Collections.sort`, `Collections.shuffle`, `Collections.frequency`, `Collections.disjoint`, `Arrays.sort`, `Arrays.binarySearch`
- **New in each release:** Every Java version adds important utilities. Read the release notes. Java 8 added streams. Java 9 added `List.of()`, `Map.of()`. Java 11 added `String.strip()`, `String.isBlank()`
- **Transfer files (Java 9+):** `inputStream.transferTo(outputStream)` — no manual buffer loop needed

### Item 60 — Avoid float and double if exact answers are required
- **Rule:** Use `BigDecimal`, `int`, or `long` for monetary calculations; never `float` or `double`
- **The floating-point problem:** `1.03 - 0.42` = `0.6100000000000001` — binary floating-point cannot represent most decimal fractions exactly
- **Classic bug:** `System.out.println(1.00 - 9 * 0.10)` → `0.09999999999999998`
- **`BigDecimal` pros:** Exact decimal arithmetic
- **`BigDecimal` cons:** Less convenient than primitives, slower, verbose
- **Alternative:** Work in cents (int/long) — multiply by 100, use integer arithmetic, divide for display
- **`BigDecimal` rounding:** Must specify a `RoundingMode` for division; `HALF_UP` for standard financial rounding

### Item 61 — Prefer primitive types to boxed primitives
- **Rule:** Use primitives (`int`, `long`, `double`) over boxed equivalents (`Integer`, `Long`, `Double`) whenever possible
- **Three key differences:**
  1. Primitives have only values; boxed can be `null`
  2. Primitives are more time- and space-efficient
  3. Primitives can't cause `NullPointerException`; boxed can
- **The `==` trap:** `Integer a = new Integer(127); Integer b = new Integer(127); a == b` → `false` — object identity, not value
- **Cache range:** `Integer.valueOf(-128 to 127)` is cached — `==` works by coincidence in this range only
- **The silent NPE:** `Long sum = 0L; sum += 1` — unboxes, adds, reboxes; if `sum` were `null`, NPE here
- **Performance trap:** `Long sum = 0L; for (long i = 0; i < Integer.MAX_VALUE; i++) sum += i;` — creates 2 billion `Long` instances

### Item 62 — Avoid strings where other types are more appropriate
- **Rule:** Don't use `String` as a substitute for a richer type when a proper type exists
- **String as value type antipattern:** `String compoundKey = className + "#" + i.next()` — no type safety, no equals, parsing required
- **String as capability (key) antipattern:** Using string keys for scoped naming (like thread-local variables) — use `ThreadLocal<T>` with a proper type key
- **String as enum antipattern:** `if (type.equals("CREDIT"))` — should be an enum
- **String as aggregate antipattern:** `String employee = name + "#" + dob + "#" + salary` — should be a class
- **When String IS appropriate:** Text that is truly textual in nature — user input, file contents, messages

### Item 63 — Beware the performance of string concatenation
- **Rule:** For concatenating more than a trivial number of strings, use `StringBuilder`
- **The O(n²) problem:** Each `+` creates a new `String` — concatenating n strings takes O(n²) time and space
- **Benchmark reality:** Concatenating 100 strings with `+` in a loop is ~100× slower than `StringBuilder`
- **String.join():** Good for fixed-size joining: `String.join(", ", list)` — correct performance
- **Java 9+ JEP 280:** Compiler optimizes `+` in non-loop contexts with `invokedynamic` — but loops are NOT optimized
- **Streams:** `stream.collect(joining(", "))` — uses `StringBuilder` internally

### Item 64 — Refer to objects by their interfaces
- **Rule:** Use interface types for variables, parameters, return types, and fields; use implementation types only for constructors
- **Example:** `List<Subscriber> subscribers = new ArrayList<>()` — NOT `ArrayList<Subscriber>`
- **Why:** Flexibility to swap implementations; `new LinkedList<>()` instead of `ArrayList<>` requires only one line change
- **When NOT to:** When the implementation offers methods not in the interface (e.g. `LinkedBlockingDeque` vs `Queue`) — but reconsider if you're using those methods
- **Value classes exception:** `String`, `BigInteger`, `BigDecimal` — rarely multiple implementations; using the class type is fine

### Item 65 — Prefer interfaces to reflection
- **Rule:** Use reflection only for specialized framework code (dependency injection, serialization, testing tools); never use it in general application code
- **Reflection costs:**
  - Loses compile-time type checking (errors at runtime)
  - Loses all generic type safety
  - Very slow (10–100× slower than direct calls)
  - Bypasses access control
- **Legitimate use:** Instantiate a class by name from configuration, then access it through a known interface
- **Pattern:** `Class<?> cls = Class.forName(name); Object instance = cls.getDeclaredConstructor().newInstance(); MyInterface obj = (MyInterface) instance;`
- **Annotation processing, ORM, DI frameworks** must use reflection; application code generally should not

### Item 66 — Use native methods judiciously
- **Rule:** Avoid JNI (Java Native Interface) in new code except when absolutely necessary
- **Three legitimate use cases:** Platform-specific facilities, legacy native libraries, performance-critical math (rarely justified)
- **Why native methods are dangerous:** Not type-safe, not garbage-collected, platform-specific, debugging is extremely hard, JVM cannot optimize across native boundary
- **Performance alternative:** Modern JVMs have closed most performance gaps with native code; profile before concluding native is needed

### Item 67 — Optimize judiciously
- **Rule:** Don't optimize prematurely; write clear correct code first, then profile and optimize only proven bottlenecks
- **"More computing sins are committed in the name of efficiency..."** — Knuth's warning
- **API design must consider performance:** Bad API decisions that invite poor performance are hard to fix later (e.g. returning a mutable object forces defensive copies everywhere)
- **Profile, don't guess:** Use JProfiler, async-profiler, or JFR (Java Flight Recorder) to find actual bottlenecks
- **Algorithmic complexity first:** No JVM optimization saves O(n²) code from O(n log n) code
- **Micro-benchmarks:** Use JMH (Java Microbenchmark Harness); naive benchmarking is unreliable due to JIT warmup

### Item 68 — Adhere to generally accepted naming conventions
- **Rule:** Follow the naming conventions of The Java Language Specification exactly
- **Package:** lowercase dot-separated reverse domain: `com.google.inject`
- **Class/Interface/Enum/Annotation:** UpperCamelCase: `ThreadLocalRandom`, `Runnable`
- **Method/Field:** lowerCamelCase: `getName`, `ensureCapacity`
- **Constant field:** SCREAMING_SNAKE_CASE: `MIN_VALUE`, `NEGATIVE_INFINITY`
- **Type parameter:** Single uppercase letter: `T` (type), `E` (element), `K`/`V` (key/value), `X` (exception), `R` (return)
- **Grammatical conventions:** Classes are nouns; methods are verbs; boolean getters start with `is`/`has`/`can`; conversion methods are `toType()` or `asType()`

---

## Key Concepts

| Habit | Item | Impact |
|---|---|---|
| Variable scope | 57 | Readability, fewer bugs |
| for-each | 58 | Prevents iterator bugs |
| Use library APIs | 59 | Correctness, performance |
| int/long for money | 60 | Exact decimal arithmetic |
| Prefer primitives | 61 | Performance, null safety |
| StringBuilder | 63 | O(n) vs O(n²) string building |
| Code to interfaces | 64 | Flexibility, testability |

---

## Relationships to Other Chapters
- Item 59 (libraries): Many items in Ch 7 (Streams) are library usages enabled by Item 59's philosophy
- Item 64 (interfaces): Connects directly to Item 20 (Ch 4) — prefer interfaces to abstract classes
- Item 61 (primitives): Autoboxing cost described in Item 6 (Ch 2)
- Item 67 (optimization): Connects to Item 48 (Ch 7) — parallel streams as an optimization tool

---

## Agent Prompt

When generating content for this chapter:

1. **Item 61 — The Autoboxing Performance Demo** — Write the `Long` vs `long` summation benchmark. Show both the time difference and the GC pressure difference (number of objects allocated). Make this concrete with actual numbers.

2. **Item 63 — String Concatenation O(n²) Proof** — Demonstrate with timing code that 10,000 string concatenations with `+` is dramatically slower than `StringBuilder`. Then show `String.join()` and `StringJoiner` as idiomatic alternatives.

3. **Item 59 — Library Anti-Pattern Gallery** — List 5 things developers commonly reinvent that are in the JDK: random numbers (wrong), copying files (manual loop), string splitting (wrong handling of edge cases), sorting (reinventing mergesort), date arithmetic (manual calendar math). Show the JDK solution for each.

4. **For exercises:**
   - Exercise 1 [Beginner]: Rewrite 3 while-loops as for-each loops; identify which cannot be converted and explain why
   - Exercise 2 [Intermediate]: Fix a financial calculation that uses double arithmetic (showing the floating-point error); rewrite with BigDecimal and again with int cents
   - Exercise 3 [Intermediate]: Profile a string-building method that uses `+` in a loop; rewrite with StringBuilder; measure speedup
   - Exercise 4 [Advanced]: Replace a reflection-based method invocation with an interface-based design

5. **For use cases:**
   - Item 59: Spring's `StringUtils` and `CollectionUtils` — but prefer JDK equivalents in Java 11+
   - Item 60: Java Money API (`javax.money`) for enterprise financial applications
   - Item 64: Dependency injection is possible only because code is written against interfaces, not implementations

6. **For interview questions:** "What is the performance difference between `String`, `StringBuilder`, and `StringBuffer`?" (classic). "Explain the `Integer` cache and when `==` comparison works for boxed integers and when it doesn't." (gotcha).

7. **Advice:** Give a practical checklist for code review focused on this chapter: "Does every collection/loop use for-each? Are any string concatenations in loops? Are there any `Double`/`Float` comparisons in financial logic? Are variables declared at their use point?"
