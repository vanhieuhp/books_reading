# Chapter 11: Concurrency

## Overview
Writing concurrent programs is among the hardest tasks in software engineering. Java provides rich concurrency primitives, but using them correctly requires deep understanding of the Java Memory Model, happens-before relationships, and the subtle ways that shared mutable state can go wrong. This chapter gives the essential rules and the tools to apply them.

**Core Theme:** Shared mutable state is the root cause of almost all concurrency bugs. The best solution is to eliminate it: make objects immutable, use message passing, or confine state to a single thread. When shared mutable state is unavoidable, synchronize it correctly and completely.

**Why This Matters:** Concurrency bugs are among the hardest to reproduce, diagnose, and fix. They may appear only under high load, only on specific hardware, or only once in a million executions. Prevention through correct design is the only reliable strategy.

---

## Items

### Item 78 — Synchronize access to shared mutable data
- **Rule:** When multiple threads access mutable data, synchronize ALL accesses — both reads and writes
- **The visibility problem:** Without synchronization, one thread's writes may not be visible to another thread — the JIT compiler can hoist reads out of loops, reorder writes, or keep values in registers
- **The stopping thread bug:** A background thread checks `stopRequested` in a loop; the main thread sets it to `true`. Without `volatile` or `synchronized`, the loop may never terminate (JIT hoists the read)
- **`volatile`:** Guarantees visibility but NOT atomicity — reads/writes to the field are never cached; only use for simple flags (single writes, reads)
- **`synchronized`:** Guarantees BOTH mutual exclusion AND visibility; required for compound operations (`check-then-act`, `read-modify-write`)
- **`AtomicLong`, `AtomicInteger`:** Correct for atomic increments without `synchronized`; from `java.util.concurrent.atomic`
- **Best solution:** Make the data immutable; eliminate the sharing

### Item 79 — Avoid excessive synchronization
- **Rule:** Inside a `synchronized` block, never invoke a method that is designed to be overridden, and never invoke a method provided by a client
- **Alien methods inside sync blocks:** Can cause liveness failures (deadlock) or safety failures (data corruption from re-entrant calls)
- **Open call:** Calling alien methods outside a `synchronized` block — safe
- **The Observer bug:** A set of observers is iterated inside a synchronized block; one observer tries to remove itself, causing a `ConcurrentModificationException` (or deadlock)
- **Fix 1:** Copy the observer list before iterating (snapshot under lock, iterate without lock)
- **Fix 2:** Use `CopyOnWriteArrayList` — the iteration uses a snapshot automatically
- **Performance:** Too much synchronization causes contention, which kills throughput; use `java.util.concurrent` collections for concurrent access

### Item 80 — Prefer executors, tasks, and streams to threads
- **Rule:** Use the Executor Framework (`ExecutorService`) for managing thread execution; never manage threads directly in application code
- **Why not raw threads:** Thread creation is expensive; unmanaged threads can exhaust system resources; thread pools are reusable; executor separates task submission from execution
- **Key executor factories:**
  - `Executors.newSingleThreadExecutor()` — single background thread
  - `Executors.newFixedThreadPool(n)` — fixed pool
  - `Executors.newCachedThreadPool()` — elastic pool (good for short tasks)
  - `Executors.newScheduledThreadPool(n)` — timed/recurring tasks
- **Tasks not threads:** Submit `Runnable` or `Callable<T>`; get back `Future<T>`
- **Fork-Join (Java 7+):** For divide-and-conquer tasks; `ForkJoinPool.commonPool()` is used by parallel streams
- **Virtual threads (Java 21+):** `Executors.newVirtualThreadPerTaskExecutor()` — lightweight threads; changes the economics of concurrency dramatically

### Item 81 — Prefer concurrency utilities to wait and notify
- **Rule:** Use the high-level concurrency utilities in `java.util.concurrent` instead of the low-level `wait` and `notify`
- **Why wait/notify is hard:** Must be called inside synchronized block; spurious wakeups must be handled; timing issues between notify and wait; extremely easy to get wrong
- **Three categories of concurrency utilities:**
  1. **Executor framework** (Item 80) — thread management
  2. **Concurrent collections** — `ConcurrentHashMap`, `CopyOnWriteArrayList`, `BlockingQueue`
  3. **Synchronizers** — `CountDownLatch`, `Semaphore`, `CyclicBarrier`, `Phaser`, `Exchanger`
- **`ConcurrentHashMap`:** Use instead of `HashMap` + manual synchronization; much better performance
- **`BlockingQueue`:** Canonical producer-consumer implementation; blocks producer when full, blocks consumer when empty
- **`CountDownLatch`:** One or more threads wait for N other threads to complete; classic test harness pattern
- **If you MUST use wait/notify:** Always use wait in a loop checking the condition; always use `notifyAll` instead of `notify`

### Item 82 — Document thread safety
- **Rule:** Every class must document its thread-safety level; clients cannot make safe assumptions without this documentation
- **Five levels of thread safety:**
  1. **Immutable** — instances appear constant; no external sync needed (e.g. `String`, `Long`, `BigInteger`)
  2. **Unconditionally thread-safe** — mutable but internally synchronized; safe without external sync (e.g. `ConcurrentHashMap`, `AtomicLong`)
  3. **Conditionally thread-safe** — some methods require external synchronization (e.g. `Collections.synchronizedMap`; iteration requires sync on the map)
  4. **Not thread-safe** — mutable; clients must synchronize externally (e.g. `ArrayList`, `HashMap`)
  5. **Thread-hostile** — unsafe even with external sync; avoid (e.g. calling `System.setOut` while other threads use it)
- **`@GuardedBy` annotation:** Documents which lock protects a field; from `java.util.concurrent.locks` or JCIP
- **Lock documentation:** If the class uses a private lock object, document which operations require it

### Item 83 — Use lazy initialization judiciously
- **Rule:** Use lazy initialization only when it genuinely improves performance, and use the correct idiom for the context
- **Lazy initialization risks:** Race conditions; complex correctness proof; may not actually help if almost always initialized
- **For static fields:** Use the lazy initialization holder class idiom (initialization-on-demand):
  ```java
  private static class FieldHolder {
      static final FieldType field = computeExpensiveField();
  }
  static FieldType getField() { return FieldHolder.field; }
  ```
- **For instance fields:** Use double-check idiom with `volatile`:
  ```java
  private volatile FieldType field;
  FieldType getField() {
      FieldType result = field;
      if (result == null) {
          synchronized(this) {
              if (field == null) field = result = compute();
          }
      }
      return result;
  }
  ```
- **For repeated initialization tolerance (instance):** Single-check idiom (weaker; field can initialize multiple times on different threads — only if idempotent and not a correctness concern)

### Item 84 — Don't depend on the thread scheduler
- **Rule:** Any correct and performant program must not depend on the thread scheduler for correctness or performance
- **Thread.yield():** Has no guaranteed behavior; `yield` is a hint that may be completely ignored; using it to "help" threads take turns is a code smell
- **Thread priorities:** Highly platform-dependent; do not use to control scheduling; definitely not for correctness
- **The correct approach:** Keep the number of runnable threads close to the number of processors; threads that are waiting should be blocked (not spinning or yielding)
- **Busy-waiting:** A thread that loops checking a condition without blocking is a runnable thread that wastes CPU and may actually starve other threads
- **Fix for busy-waiting:** Use `wait`/`notify`, `CountDownLatch`, `BlockingQueue`, or a `ScheduledExecutorService`

---

## Key Concepts

| Problem | Root Cause | Correct Solution |
|---|---|---|
| Visibility failure | No synchronization on read | `volatile` or `synchronized` |
| Atomicity failure | Non-atomic compound op | `synchronized` or Atomic classes |
| Deadlock | Circular lock dependencies | Consistent lock ordering, open calls |
| Livelock | Threads keep signaling each other | Backoff, timeouts |
| Starvation | Thread never gets scheduled | Avoid thread priorities; use executor |

| Utility | Purpose | Replaces |
|---|---|---|
| `ConcurrentHashMap` | Concurrent key-value store | `HashMap` + `synchronized` |
| `BlockingQueue` | Producer-consumer | Manual `wait`/`notify` |
| `CountDownLatch` | One-time barrier | Manual `wait`/`notify` |
| `AtomicLong` | Atomic counter/accumulator | `synchronized` increment |
| `ExecutorService` | Thread pool management | Raw `Thread` creation |

---

## Relationships to Other Chapters
- Item 17 (Ch 4): Immutability is the ultimate concurrency solution — immutable objects need no synchronization
- Item 6 (Ch 2): Shared objects in thread-local scenarios connect to scope management
- Item 46 (Ch 7): Parallel streams (Item 48) use the common `ForkJoinPool` — Item 80 context
- Item 76 (Ch 10): Failure atomicity is even more critical in concurrent contexts

---

## Agent Prompt

When generating content for this chapter:

1. **Item 78 — The JIT Hoisting Demo** — Write the `StopThread` example from the book verbatim. Show that without `volatile`, the loop runs forever (or explain the JIT optimization that causes it). Then show both the `volatile` fix and the `synchronized` fix, explaining the difference.

2. **Item 79 — The Deadlock Scenario** — Create a step-by-step narrative of how the observer pattern + synchronized block creates a deadlock: Thread A holds the lock and calls an alien observer; the observer tries to acquire the same lock from Thread B. Draw the lock dependency graph.

3. **Item 81 — CountDownLatch Timing Harness** — Implement the classic concurrent timing harness from the book: N worker threads wait for a start signal, execute a task, then count down. The main thread starts the clock, releases the start signal, waits for all workers, stops the clock. Show the complete implementation.

4. **For exercises:**
   - Exercise 1 [Intermediate]: Fix a broken `++counter` in a multithreaded context; use `synchronized`, then `AtomicInteger`, then show LongAdder for high-contention
   - Exercise 2 [Advanced]: Implement a thread-safe lazy-initialized singleton using: (a) synchronized method, (b) double-check locking with volatile, (c) holder class idiom. Compare performance
   - Exercise 3 [Advanced]: Reproduce a deadlock with two threads locking on two resources in opposite order; fix it by enforcing lock ordering
   - Exercise 4 [Advanced]: Build a thread-safe bounded blocking queue from scratch using `synchronized` + `wait`/`notifyAll`, then replace with `ArrayBlockingQueue`

5. **For use cases:**
   - `ConcurrentHashMap` in a request counter service (high-read, occasional-write)
   - `ExecutorService` in a Spring Boot `@Async` service equivalent
   - `CountDownLatch` in integration test setup (wait for N services to initialize)
   - Virtual threads (Java 21) for massively concurrent I/O-bound services

6. **For interview questions:** "Explain the Java Memory Model and what 'happens-before' means." (Senior). "What is the difference between `volatile` and `synchronized`?" (Mid). The gotcha: "Why is double-checked locking broken without `volatile`?" (tests deep JMM understanding).

7. **Advice:** Give a strong hierarchy of approaches: (1) Make data immutable, (2) confine data to one thread, (3) use `java.util.concurrent` utilities, (4) use `synchronized` carefully. Reserve raw `wait`/`notify` only for situations where nothing else works. Include a concurrency code review checklist.
