# Chapter 7: Lambdas and Streams

## Overview
Java 8 introduced the single most transformative set of language features since generics: lambdas, method references, functional interfaces, and the Stream API. This chapter teaches you to use them idiomatically — and, crucially, when NOT to use them.

**Core Theme:** Lambdas and streams are tools, not religion. Use them where they make code clearer and more composable. Recognize when iterative code is more readable and stick with it.

**Why This Matters:** Overuse of streams produces incomprehensible "stream spaghetti" that's harder to debug and maintain than the loop it replaced. Underuse misses genuine opportunities for readable, parallelizable data pipelines. The line between the two is judgment, and this chapter teaches that judgment.

---

## Items

### Item 42 — Prefer lambdas to anonymous classes
- **Rule:** Use lambdas instead of anonymous classes for functional interface implementations
- **Anonymous class problems:** Verbose, noisy, obscures intent, discouraged as of Java 8
- **Lambda advantages:** Concise, readable, the intent is clear
- **Lambda limits:** Cannot obtain a reference to itself (no `this`); cannot add documentation; max ~3 lines before readability suffers
- **When anonymous classes are still needed:** Non-functional interfaces (multiple abstract methods); when you need `this`; when lambda behavior needs to survive serialization (lambdas have questionable serialization)
- **Enum and anonymous class:** Still needed for constant-specific class bodies in enums that have state

### Item 43 — Prefer method references to lambdas
- **Rule:** Use method references wherever they are shorter and clearer than the equivalent lambda; use lambdas where the method reference is confusing
- **5 types of method references:**
  1. Static: `Integer::parseInt` = `str -> Integer.parseInt(str)`
  2. Bound instance: `Instant.now()::isAfter` = `t -> Instant.now().isAfter(t)`
  3. Unbound instance: `String::toLowerCase` = `str -> str.toLowerCase()`
  4. Constructor: `TreeMap::new` = `() -> new TreeMap<>()`
  5. Unbound arbitrary instance: `String::compareToIgnoreCase`
- **When lambda is better:** `action -> execute(action)` is cleaner than `GoshThisClassNameIsHumongous::action`
- **IDE support:** IntelliJ/Eclipse will suggest method references automatically

### Item 44 — Favor the use of standard functional interfaces
- **Rule:** Check `java.util.function` before writing a custom functional interface; use the 43 standard interfaces
- **The 6 basic families:**
  - `UnaryOperator<T>`: `T apply(T t)` — single operand, same return type
  - `BinaryOperator<T>`: `T apply(T t1, T t2)` — two operands, same return type
  - `Predicate<T>`: `boolean test(T t)` — returns boolean
  - `Function<T, R>`: `R apply(T t)` — transforms type
  - `Supplier<T>`: `T get()` — factory / no-arg
  - `Consumer<T>`: `void accept(T t)` — operation without return
- **When to write custom:** When it will be commonly used, benefits from a name, or has a strong contract (e.g. `Comparator<T>`)
- **Always annotate custom functional interfaces with `@FunctionalInterface`**

### Item 45 — Use streams judiciously
- **Rule:** Use streams for data transformation pipelines; use iteration for block-level logic
- **Streams are great for:** Transforming sequences, filtering elements, aggregating (count, sum, min, max), grouping, collecting
- **Streams are bad for:**
  - Modifying local variables in scope (lambdas can't assign to non-final locals)
  - Using checked exceptions
  - Needing `return`, `break`, or `continue` from the enclosing block
  - Reading and writing to the same element during traversal
- **Readability test:** If you find yourself naming intermediate stream results, it's a sign iteration may be clearer
- **char streams are broken:** `"hello".chars()` returns `IntStream`, not `Stream<Character>`

### Item 46 — Prefer side-effect-free functions in streams
- **Rule:** Stream pipelines must use pure functions (no side effects in intermediate operations); use `forEach` ONLY to report results, not to compute them
- **The `forEach` antipattern:** Using `forEach` to populate a map or list instead of using `collect()` — misuses the stream API
- **Collectors knowledge:** Know `toList()`, `toSet()`, `toMap()`, `groupingBy()`, `joining()`, `counting()`, `partitioningBy()`
- **`groupingBy` is the most powerful Collector** — produces a `Map<K, List<V>>` and supports downstream collectors
- **`toMap` with merge function:** Required when keys might duplicate: `toMap(keyFn, valFn, (old, new) -> old)`

### Item 47 — Prefer Collection to Stream as a return type
- **Rule:** For public methods that return a sequence, prefer `Collection` (or subtype) over `Stream` or `Iterable`
- **Why:** `Collection` provides both `stream()` (for stream users) and `iterator()` / for-each (for iteration users)
- **Stream is not Iterable (gotcha):** `Stream<T>` has `iterator()` but does NOT implement `Iterable<T>` — you cannot for-each a stream directly
- **When Stream is appropriate:** Only when the sequence is too large to hold in memory (power set example) or when the caller will clearly always use stream operations
- **When Iterable is appropriate:** Only when the caller will clearly never use stream operations (unlikely)

### Item 48 — Use caution when making streams parallel
- **Rule:** Do not parallelize a stream pipeline unless there is genuine reason to believe it will improve performance, you have measured it, and the computation is safe to parallelize
- **When parallelism helps:** ArrayList, HashMap, HashSet, ConcurrentHashMap, arrays, int ranges, long ranges — sources with good splitting characteristics and cheap split/merge
- **When parallelism hurts:** LinkedList, Stream.iterate, limit(), findFirst() — poor splitting; also when operations have side effects or depend on ordering
- **Safety requirements:** The pipeline must be stateless, non-interfering, and associative (for reduce/collect operations)
- **Parallel + ordered:** `findFirst()`, `limit()`, and other encounter-order operations kill parallelism performance
- **Benchmark, don't guess:** Use JMH to measure before and after

---

## Key Concepts

| Concept | Item | Rule |
|---|---|---|
| Lambda vs Anonymous Class | 42 | Lambda for functional; anonymous for non-functional |
| Method Reference Types | 43 | Prefer over lambda when shorter/clearer |
| Standard Functional Interfaces | 44 | Use `java.util.function` first |
| Stream vs Iteration | 45 | Streams for pipelines; loops for block logic |
| Pure Functions | 46 | No side effects in stream operations |
| Return Type | 47 | Return `Collection`, not `Stream` |
| Parallel Safety | 48 | Measure before parallelizing |

---

## Relationships to Other Chapters
- Item 42: Replaces anonymous classes from Item 24 (Ch 4)
- Item 44: `Comparator` is a functional interface connecting to Item 14 (Ch 3)
- Item 45: Stream pipelines need the immutability discipline from Item 17 (Ch 4)
- Item 48: Connects deeply to Chapter 11 (Concurrency) — parallel streams use the fork-join pool

---

## Agent Prompt

When generating content for this chapter:

1. **Item 45 — Stream vs Loop Decision Table** — Generate a detailed decision table covering: checked exceptions, local variable mutation, early exit (break/return), debugging ease, readability with 1 operation vs 5+ operations. Make this a printable reference card.

2. **Item 46 — Collectors Deep Dive** — Show `groupingBy` with downstream collectors: `groupingBy(classifier, counting())`, `groupingBy(classifier, summingInt(fn))`, `groupingBy(outer, groupingBy(inner))`. These are powerful patterns most developers don't know.

3. **Item 48 — Parallel Stream Pitfall Demo** — Show a concrete example where parallelizing a stream with `limit()` or `findFirst()` actually makes it slower. Use `System.nanoTime()` measurements to illustrate.

4. **For exercises:**
   - Exercise 1 [Beginner]: Rewrite 5 anonymous `Runnable`/`Comparator` implementations as lambdas, then as method references
   - Exercise 2 [Intermediate]: Rewrite a word-frequency counter (using a for loop + Map) as a stream pipeline using `Collectors.groupingBy` + `Collectors.counting()`
   - Exercise 3 [Advanced]: Build a stream pipeline that reads a CSV, groups rows by a category field, computes the average of a numeric field per group, and returns a `Map<String, Double>`
   - Exercise 4 [Advanced]: Find the performance crossover point where `parallelStream()` beats `stream()` for summing a list of longs (use JMH or manual timing)

5. **For use cases:**
   - Streams in Spring Data: `findAll().stream().filter().collect()` patterns
   - Functional interfaces in Spring: `BeanFactory`, `ApplicationContext` lambda-style configuration
   - `Predicate` composition in `Stream.filter(predicate1.and(predicate2))`

6. **For interview questions:** "What is the difference between `map` and `flatMap`?" (extremely common). "Can you explain what a terminal operation is, and why you can only run a stream pipeline once?" (tests deep understanding).

7. **Advice:** Give a strong opinion on the "flat stream pipeline" style (everything in one expression) vs breaking into named variables. Recommend the named variable approach for all but the simplest pipelines. Also warn about the common mistake of collecting to a list and then streaming again — compose the pipeline instead.
