# Java Concurrency: From Threads to Virtual Threads
### A Practical Textbook for Java Developers
*With Payment & Transaction System Examples — Phases 1–5 | 2026 Edition*

---

## Introduction

This textbook teaches Java concurrency from the ground up, assuming 4+ years of Java experience but zero concurrency background. Every concept is accompanied by real-world examples drawn from payment processing and transaction systems — one of the most concurrency-sensitive domains in software engineering.

**Structure:** Theory → Real-world payment scenario → Bad vs Good code → Exercises → Interview questions.

---

# Phase 1 — Thread Foundations
*Weeks 1–2: Understanding what a thread is, how the JVM manages threads, and the fundamentals of thread lifecycle and control.*

---

## 1.1 What Is a Thread?

A thread is the smallest unit of execution within a process. Every Java application starts with one thread — the main thread. Additional threads allow work to happen in parallel, sharing the same heap memory but each having its own stack, program counter, and local variables.

> **Payment World:** A payment gateway must process thousands of transactions per second. Without threads, each transaction would block the server until the previous one finished. With threads, the gateway can handle many transactions simultaneously — checking fraud rules, debiting accounts, and sending confirmations in parallel.

### Thread Lifecycle

| State | Description | Payment Example |
|---|---|---|
| NEW | Thread created but not yet started | Transaction object created, not submitted |
| RUNNABLE | Running or ready to run | Actively processing card authorization |
| BLOCKED | Waiting to acquire a lock | Waiting for database row lock on account |
| WAITING | Waiting indefinitely for notification | Waiting for fraud-check service response |
| TIMED_WAITING | Waiting for a limited time | Waiting max 5s for bank authorization |
| TERMINATED | Execution complete | Transaction recorded, thread finished |

---

## 1.2 Thread vs Runnable

There are two primary ways to create a thread in Java.

❌ **Bad — extending Thread** (couples task logic with threading):

```java
// BAD: Mixes thread management with business logic.
// Cannot extend another class; hard to reuse task.
public class PaymentProcessor extends Thread {
    private Payment payment;
    public PaymentProcessor(Payment payment) { this.payment = payment; }

    @Override
    public void run() {
        processPayment(payment); // business logic inside Thread subclass
    }
}

// Usage
new PaymentProcessor(payment).start(); // cannot reuse task with Executor later
```

✅ **Good — implementing Runnable** (separates task from thread):

```java
// GOOD: Task is decoupled from threading mechanism.
// Can run on a thread pool, virtual thread, or plain Thread.
public class PaymentTask implements Runnable {
    private final Payment payment;
    public PaymentTask(Payment payment) { this.payment = payment; }

    @Override
    public void run() {
        processPayment(payment);
    }
}

// Usage: works with Thread, ExecutorService, or virtual threads
new Thread(new PaymentTask(payment)).start();
executor.submit(new PaymentTask(payment));     // easy to switch later
```

---

## 1.3 Thread Control: sleep, join, interrupt

```java
// sleep — pause thread for a duration (throws InterruptedException)
Thread.sleep(1000); // wait 1 second before retrying payment

// join — wait for another thread to finish before continuing
Thread fraudCheck   = new Thread(new FraudCheckTask(txn));
Thread balanceCheck = new Thread(new BalanceCheckTask(txn));
fraudCheck.start();
balanceCheck.start();
fraudCheck.join();    // main thread waits here until fraud check finishes
balanceCheck.join();  // then waits for balance check
// Only now proceed to authorization

// interrupt — signal a thread to stop what it is doing
fraudCheck.interrupt(); // e.g., timeout expired — cancel the fraud check

// ALWAYS handle InterruptedException correctly:
try {
    Thread.sleep(5000);
} catch (InterruptedException e) {
    Thread.currentThread().interrupt(); // restore interrupt flag — never swallow!
    throw new RuntimeException("Payment check interrupted", e);
}
```

---

## 1.4 Race Conditions — The Core Problem

A race condition occurs when two or more threads access shared mutable state concurrently and the correctness of the result depends on the order of execution. This is the root cause of most concurrency bugs.

❌ **Bad — unsynchronized balance update (classic race):**

```java
public class BankAccount {
    private double balance = 1000.0;

    // DANGEROUS: Two threads calling debit() simultaneously
    // may both read balance=1000, both subtract 500,
    // and both write back 500 — losing one debit entirely!
    public void debit(double amount) {
        if (balance >= amount) {        // Thread A reads 1000
            balance = balance - amount; // Thread B also reads 1000 — race!
        }
    }
}
```

> **Exercise 1.1 — Reproduce the Race:** Create a BankAccount with balance=1000. Launch 100 threads each calling `debit(10)`. Print the final balance. Run it 10 times. You will observe different wrong answers each run. This non-determinism is the hallmark of a race condition.

---

## 1.5 Interview Questions — Phase 1

| Level | Question | Key Point in Answer |
|---|---|---|
| Junior | What is a thread? | Lightweight execution unit sharing heap with other threads in the same process |
| Junior | Thread vs Runnable — which to prefer? | Runnable — decouples task from thread, allows future use with ExecutorService |
| Mid | What are the 6 thread states? | NEW, RUNNABLE, BLOCKED, WAITING, TIMED_WAITING, TERMINATED — know transitions |
| Mid | What is a race condition? | Non-deterministic result from unsynchronized shared mutable state access |
| Mid | What happens if you ignore InterruptedException? | The interrupt flag is cleared; the thread cannot be cancelled — always restore it |
| Senior | What is a daemon thread? | Background thread that dies when all non-daemon threads finish; never use for transactions |

---

# Phase 2 — Synchronization
*Weeks 3–4: Coordinating access to shared state with locks, visibility guarantees, and inter-thread signaling.*

---

## 2.1 The synchronized Keyword

`synchronized` ensures only one thread executes a block or method at a time by acquiring the object's intrinsic lock (monitor). It provides two guarantees: **mutual exclusion** (only one thread at a time) and **memory visibility** (changes are flushed to main memory).

✅ **Good — synchronized method on BankAccount:**

```java
public class BankAccount {
    private double balance;

    public BankAccount(double initial) { this.balance = initial; }

    // Only one thread can execute this at a time per BankAccount instance
    public synchronized boolean debit(double amount) {
        if (balance < amount) {
            return false; // insufficient funds
        }
        balance -= amount; // safe: no other thread can be here simultaneously
        return true;
    }

    public synchronized void credit(double amount) {
        balance += amount;
    }

    public synchronized double getBalance() {
        return balance; // synchronized getter ensures visibility
    }
}
```

> **Payment World — Transfer Between Accounts:** A funds transfer requires debiting one account and crediting another — both under a lock. Locking on a single account is not enough; you need to acquire both locks in a consistent order to avoid deadlock. See section 2.4.

---

## 2.2 The volatile Keyword

`volatile` guarantees **memory visibility** — every write to a volatile variable is immediately visible to all threads. It does **NOT** provide mutual exclusion. Use it only for simple flags or state indicators, never for compound operations like check-then-act.

```java
public class PaymentGateway {
    // volatile: any thread writing 'running' immediately visible to others
    private volatile boolean running = true;

    public void processLoop() {
        while (running) { // thread A reads fresh value every time
            processNextTransaction();
        }
    }

    public void shutdown() {
        running = false; // thread B writes; thread A sees it immediately
    }
}

// ❌ WRONG use of volatile — compound operation is not atomic:
private volatile int transactionCount = 0;
transactionCount++; // read-modify-write: THREE operations, not atomic!
// Use AtomicInteger instead (Phase 3).
```

---

## 2.3 wait() / notify() — Producer-Consumer

`wait()` releases the lock and suspends the calling thread until another thread calls `notify()` or `notifyAll()` on the same object. This is the classic mechanism for inter-thread signaling.

✅ **Payment Queue — blocking producer-consumer:**

```java
public class TransactionQueue {
    private final Queue<Transaction> queue = new LinkedList<>();
    private final int capacity;

    public TransactionQueue(int capacity) { this.capacity = capacity; }

    // Called by payment intake threads (producers)
    public synchronized void enqueue(Transaction txn) throws InterruptedException {
        while (queue.size() == capacity) {
            wait(); // release lock, sleep until notified
        }
        queue.add(txn);
        notifyAll(); // wake processor threads waiting for work
    }

    // Called by transaction processor threads (consumers)
    public synchronized Transaction dequeue() throws InterruptedException {
        while (queue.isEmpty()) {
            wait(); // no work available, sleep
        }
        Transaction txn = queue.poll();
        notifyAll(); // wake intake threads waiting to add
        return txn;
    }
}
// KEY: Always use while (not if) for the wait condition — spurious wakeups!
```

---

## 2.4 Deadlock, Livelock, and Starvation

| Problem | What Happens | Payment Example | Prevention |
|---|---|---|---|
| Deadlock | Thread A holds lock X, waits for Y. Thread B holds Y, waits for X. Both frozen forever. | Transfer: thread locks Account A then waits for B. Another thread locks B, waits for A. | Always acquire account locks in consistent ID order (low ID first). |
| Livelock | Threads keep responding to each other but make no progress. | Two transfers keep retrying and backing off at the same time. | Add randomized backoff delay before retry. |
| Starvation | A low-priority thread never gets CPU or lock access. | High-frequency micro-payment threads starving a settlement thread. | Use fair locks: `new ReentrantLock(true)`. |

✅ **Deadlock prevention — consistent lock ordering for transfers:**

```java
public void transfer(BankAccount from, BankAccount to, double amount) {
    // Always lock the lower-ID account first to prevent circular waits
    BankAccount first  = from.getId() < to.getId() ? from : to;
    BankAccount second = from.getId() < to.getId() ? to   : from;

    synchronized (first) {
        synchronized (second) {
            if (from.getBalance() >= amount) {
                from.debit(amount);
                to.credit(amount);
            }
        }
    }
}
// With consistent ordering, no two threads can form a circular lock dependency.
```

---

## 2.5 Exercises — Phase 2

> **Exercise 2.1 [Intermediate] — Fix the Deadlock:** Two `transfer()` methods each lock accounts in different orders causing a deadlock. Reproduce it with two threads: T1 transfers A→B, T2 transfers B→A simultaneously. Then fix using consistent lock ordering. Verify with `jstack`: run the buggy version, see `DEADLOCK` in the dump.

> **Exercise 2.2 [Intermediate] — Bounded Transaction Queue:** Implement `TransactionQueue` from scratch using `wait`/`notifyAll`. Capacity = 5. Run 10 producer threads each submitting 3 transactions and 3 consumer threads each processing until empty. Assert every transaction is processed exactly once.

---

## 2.6 Interview Questions — Phase 2

| Level | Question | Key Point |
|---|---|---|
| Mid | What two guarantees does synchronized provide? | Mutual exclusion + memory visibility (happens-before) |
| Mid | synchronized vs volatile? | volatile: visibility only, no atomicity. synchronized: both, but heavier. |
| Mid | Why use while instead of if with wait()? | Spurious wakeups — condition may not actually be true when thread wakes up |
| Senior | How do you prevent deadlock in a funds transfer? | Consistent lock ordering by account ID; or use tryLock with timeout |
| Senior | What is a livelock vs deadlock? | Deadlock: frozen. Livelock: active but looping, no progress made. |
| Senior | What is lock striping? | ConcurrentHashMap technique: multiple locks over segments to reduce contention |

---

# Phase 3 — java.util.concurrent
*Weeks 5–6: The high-level concurrency toolkit that replaces most hand-rolled synchronization. This is the phase you'll use most in production payment systems.*

---

## 3.1 ExecutorService and Thread Pools

Managing threads manually is error-prone and inefficient. `ExecutorService` provides a pool of reusable threads and a queue of tasks. Creating a new thread per payment request does not scale — thread creation is expensive.

❌ **Bad — new Thread per payment:**

```java
// Creates thousands of threads under load — JVM will crash
for (Payment p : incomingPayments) {
    new Thread(() -> process(p)).start(); // unbounded thread creation
}
```

✅ **Good — fixed thread pool:**

```java
public class PaymentService {
    // Pool size = number of CPU cores (CPU-bound work)
    // For I/O-bound (DB calls, HTTP): use 2x-4x core count
    private final ExecutorService executor =
        Executors.newFixedThreadPool(Runtime.getRuntime().availableProcessors() * 2);

    public Future<PaymentResult> submitPayment(Payment payment) {
        return executor.submit(() -> {
            return processPayment(payment); // runs on pool thread
        });
    }

    public void shutdown() {
        executor.shutdown(); // stop accepting new tasks
        try {
            if (!executor.awaitTermination(30, TimeUnit.SECONDS)) {
                executor.shutdownNow(); // force-cancel remaining tasks
            }
        } catch (InterruptedException e) {
            executor.shutdownNow();
            Thread.currentThread().interrupt();
        }
    }
}
```

---

## 3.2 Future and Callable

```java
ExecutorService executor = Executors.newFixedThreadPool(4);

// Callable returns a value (unlike Runnable)
Callable<FraudScore> fraudTask = () -> fraudService.check(transaction);
Callable<Boolean>    balTask   = () -> balanceService.hasFunds(transaction);

Future<FraudScore> fraudFuture = executor.submit(fraudTask);
Future<Boolean>    balFuture   = executor.submit(balTask);

// Both tasks run in parallel. get() blocks until result is ready.
FraudScore score  = fraudFuture.get(5, TimeUnit.SECONDS); // 5s timeout
Boolean hasFunds  = balFuture.get(5, TimeUnit.SECONDS);

if (score.isClean() && hasFunds) {
    authorizePayment(transaction);
}

// IMPORTANT: Always handle TimeoutException and ExecutionException
// ExecutionException wraps exceptions thrown inside the task
```

---

## 3.3 ReentrantLock and Condition

`ReentrantLock` offers more control than `synchronized`: `tryLock()` with timeout, fair locking, and multiple `Condition` objects per lock. In payment systems, `tryLock()` prevents deadlocks by giving up after a timeout.

```java
public class AccountLockService {
    private final Map<String, ReentrantLock> locks = new ConcurrentHashMap<>();

    public boolean transferWithTimeout(String fromId, String toId, BigDecimal amount) {
        ReentrantLock lockA = locks.computeIfAbsent(fromId, k -> new ReentrantLock());
        ReentrantLock lockB = locks.computeIfAbsent(toId,   k -> new ReentrantLock());

        try {
            // Try to acquire both locks within 1 second — no deadlock possible
            if (lockA.tryLock(1, TimeUnit.SECONDS)) {
                try {
                    if (lockB.tryLock(1, TimeUnit.SECONDS)) {
                        try {
                            return doTransfer(fromId, toId, amount);
                        } finally { lockB.unlock(); }
                    }
                } finally { lockA.unlock(); }
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
        return false; // could not acquire locks in time — caller should retry
    }
}
```

---

## 3.4 Atomic Classes

Atomic classes use hardware-level compare-and-swap (CAS) operations for lock-free thread safety on single variables. Faster than `synchronized` for simple counters and references.

```java
public class PaymentMetrics {
    private final AtomicLong  totalProcessed = new AtomicLong(0);
    private final AtomicLong  totalAmount    = new AtomicLong(0);
    private final AtomicInteger activeWorkers = new AtomicInteger(0);

    public void recordPayment(long amountCents) {
        totalProcessed.incrementAndGet();     // atomic: no lock needed
        totalAmount.addAndGet(amountCents);   // atomic add
    }

    // CAS example: update max transaction seen
    private final AtomicLong maxTransaction = new AtomicLong(0);
    public void updateMax(long amount) {
        long current;
        do {
            current = maxTransaction.get();
            if (amount <= current) return; // no update needed
        } while (!maxTransaction.compareAndSet(current, amount));
        // CAS: only updates if value is still 'current' — retries if another
        // thread changed it; this is lock-free, not wait-free
    }
}
```

---

## 3.5 Concurrent Collections

| Collection | Use Case | Payment Example |
|---|---|---|
| ConcurrentHashMap | Thread-safe map, high read concurrency | Session cache of active payment tokens |
| CopyOnWriteArrayList | Read-heavy, rare writes | List of active payment processors (rarely changes) |
| LinkedBlockingQueue | Bounded producer-consumer queue | Transaction queue with backpressure (capacity limit) |
| PriorityBlockingQueue | Ordered processing by priority | High-value transactions processed first |
| ConcurrentLinkedQueue | Lock-free unbounded queue | Audit log event queue |

---

## 3.6 Synchronization Utilities

```java
// CountDownLatch — wait for N tasks to complete
// Use: wait for fraud check + balance check + KYC before authorizing
CountDownLatch latch = new CountDownLatch(3);
executor.submit(() -> { fraudCheck(txn);   latch.countDown(); });
executor.submit(() -> { balanceCheck(txn); latch.countDown(); });
executor.submit(() -> { kycCheck(txn);     latch.countDown(); });
latch.await(10, TimeUnit.SECONDS); // wait max 10s for all 3

// Semaphore — limit concurrent access (rate limiting)
// Use: max 10 concurrent connections to payment processor API
Semaphore apiLimit = new Semaphore(10);
apiLimit.acquire();
try {
    callExternalPaymentAPI(txn);
} finally {
    apiLimit.release(); // ALWAYS release in finally
}

// CyclicBarrier — sync a batch of threads at a checkpoint
// Use: end-of-day batch settlement — all threads must finish their
// segment before reconciliation starts
CyclicBarrier barrier = new CyclicBarrier(4, () -> startReconciliation());
// Each of the 4 worker threads calls barrier.await() when done
```

---

## 3.7 Exercises — Phase 3

> **Exercise 3.1 [Intermediate] — Payment Rate Limiter:** Build a `PaymentRateLimiter` using `Semaphore` that allows at most 20 concurrent calls to an external payment API. Simulate 100 payment threads. Each payment takes ~200ms. Measure throughput with and without the limiter. Add a timeout so threads waiting more than 2 seconds fail-fast.

> **Exercise 3.2 [Advanced] — Parallel Authorization:** Given a list of 1000 transactions, use `ExecutorService` to run fraud check, balance check, and KYC check in parallel for each transaction using `CountDownLatch`. Collect results into a `ConcurrentHashMap` keyed by transaction ID. Shutdown the executor gracefully.

---

## 3.8 Interview Questions — Phase 3

| Level | Question | Key Point |
|---|---|---|
| Mid | What pool types does Executors provide? | Fixed, Cached, Single, ScheduledThreadPool — know when to use each |
| Mid | Future.get() vs Future.get(timeout)? | get() blocks forever; get(timeout) throws TimeoutException — always use timeout |
| Mid | ConcurrentHashMap vs Collections.synchronizedMap? | CHM uses segment locking (high concurrency); synchronizedMap locks the whole map |
| Senior | When would you use Semaphore in a payment system? | Rate limiting API calls to external processors, DB connection pool management |
| Senior | CountDownLatch vs CyclicBarrier? | Latch: one-shot countdown. Barrier: reusable, triggers action when all arrive. |
| Senior | What is lock-free programming? | CAS-based operations (AtomicXxx) avoid blocking but still require retry loops |

---

# Phase 4 — Advanced Patterns
*Weeks 7–8: Async pipelines, the Java Memory Model, and the patterns senior engineers use in production.*

---

## 4.1 CompletableFuture — Async Pipelines

`CompletableFuture` enables composable, non-blocking async workflows. In payment systems, authorization involves multiple I/O steps that can be chained and composed rather than sequentially blocked on.

```java
public CompletableFuture<PaymentResult> processPayment(Payment payment) {
    return CompletableFuture
        // Step 1: async fraud check
        .supplyAsync(() -> fraudService.check(payment), executor)

        // Step 2: if fraud check passes, async balance check
        .thenComposeAsync(fraudResult -> {
            if (fraudResult.isRisky()) {
                return CompletableFuture.completedFuture(PaymentResult.DECLINED);
            }
            return CompletableFuture.supplyAsync(
                () -> balanceService.check(payment), executor);
        }, executor)

        // Step 3: if balance ok, authorize with bank
        .thenComposeAsync(balResult -> {
            if (!balResult.hasFunds()) {
                return CompletableFuture.completedFuture(PaymentResult.INSUFFICIENT);
            }
            return CompletableFuture.supplyAsync(
                () -> bankClient.authorize(payment), executor);
        }, executor)

        // Error handling: catch any step failure
        .exceptionally(ex -> {
            log.error("Payment pipeline failed", ex);
            return PaymentResult.ERROR;
        });
}

// Run multiple checks in PARALLEL and wait for all:
CompletableFuture<FraudScore> fraud   = CompletableFuture.supplyAsync(...);
CompletableFuture<Boolean>    balance = CompletableFuture.supplyAsync(...);
CompletableFuture<KycStatus>  kyc     = CompletableFuture.supplyAsync(...);

CompletableFuture.allOf(fraud, balance, kyc)
    .thenRun(() -> authorize(fraud.join(), balance.join(), kyc.join()));
```

---

## 4.2 ForkJoinPool — Divide and Conquer

`ForkJoinPool` uses work-stealing — idle threads steal tasks from busy threads' queues. It is designed for recursive, CPU-intensive tasks. It also powers parallel streams.

```java
// Payment reconciliation: sum all transaction amounts in parallel
public class ReconciliationTask extends RecursiveTask<BigDecimal> {
    private static final int THRESHOLD = 1000; // process directly if <= 1000 txns
    private final List<Transaction> transactions;
    private final int start, end;

    @Override
    protected BigDecimal compute() {
        int size = end - start;
        if (size <= THRESHOLD) {
            // Base case: sum directly
            return transactions.subList(start, end).stream()
                .map(Transaction::getAmount)
                .reduce(BigDecimal.ZERO, BigDecimal::add);
        }
        // Recursive case: split and fork
        int mid = start + size / 2;
        ReconciliationTask left  = new ReconciliationTask(transactions, start, mid);
        ReconciliationTask right = new ReconciliationTask(transactions, mid,  end);
        left.fork();                           // submit left to pool
        BigDecimal rightResult = right.compute(); // compute right on current thread
        BigDecimal leftResult  = left.join();     // wait for left
        return leftResult.add(rightResult);
    }
}

ForkJoinPool pool  = new ForkJoinPool();
BigDecimal total   = pool.invoke(new ReconciliationTask(allTxns, 0, allTxns.size()));
```

---

## 4.3 Java Memory Model (JMM)

The JMM defines when writes by one thread are visible to reads by another. The key concept is **happens-before**: if action A happens-before B, then A's effects are visible to B.

| Happens-Before Rule | Payment Example |
|---|---|
| Thread start: `start()` HB all actions in that thread | Setting up transaction context before `thread.start()` |
| Monitor: unlock HB subsequent lock of same monitor | Releasing account lock; next thread sees all changes |
| volatile write HB subsequent volatile read | Writing `running=false` is immediately seen by worker threads |
| Thread join: all actions in T HB `thread.join()` return | All transaction writes visible after `fraudThread.join()` |

> **Why This Matters:** Without a happens-before relationship, the JVM and CPU are free to reorder instructions for performance. A write in one thread may never be seen by another thread without the right synchronization. This is why `volatile` is not enough for compound operations — it provides visibility but not mutual exclusion.

---

## 4.4 ThreadLocal — Per-Thread Context

```java
// In a payment system, each request has a transaction ID.
// ThreadLocal gives each thread its own isolated copy — no sharing needed.
public class TransactionContext {
    private static final ThreadLocal<String> txnId = new ThreadLocal<>();

    public static void set(String id) { txnId.set(id); }
    public static String get()        { return txnId.get(); }
    public static void clear()        { txnId.remove(); } // CRITICAL: always clean up!
}

// In request handler:
try {
    TransactionContext.set(generateTxnId());
    processPayment(payment); // all downstream code can read txnId
} finally {
    TransactionContext.clear(); // prevent memory leak in thread pools
}
// WARNING: ThreadLocal leaks in thread pools if not cleared in finally block!
```

---

## 4.5 Exercises — Phase 4

> **Exercise 4.1 [Advanced] — Payment Pipeline:** Build a `CompletableFuture`-based payment pipeline with 3 async stages: (1) fraud check, (2) balance check, (3) bank authorization. Stages 1 and 2 should run in parallel; stage 3 only runs if both pass. Add a 10-second overall timeout. Handle errors at each stage with fallback behavior.

> **Exercise 4.2 [Advanced] — End-of-Day Reconciliation:** Implement `ReconciliationTask` using `ForkJoinPool` to sum 1 million transaction amounts. Measure wall-clock time vs a sequential sum. What threshold gives best performance on your machine?

---

## 4.6 Interview Questions — Phase 4

| Level | Question | Key Point |
|---|---|---|
| Mid | thenApply vs thenCompose? | thenApply: sync transform. thenCompose: flat-maps a Future-returning function (async chain) |
| Senior | What is happens-before? | Guarantee that writes in action A are visible to action B — the JMM's ordering primitive |
| Senior | When does ForkJoinPool outperform a fixed thread pool? | CPU-bound recursive divide-and-conquer; badly suited for I/O-bound tasks |
| Senior | ThreadLocal memory leak scenario? | Thread pool reuses threads; if `ThreadLocal.remove()` not called, old context leaks to next request |
| System Design | Design async payment authorization handling 10k TPS | CompletableFuture pipeline + fixed pool, backpressure via Semaphore, circuit breaker pattern |

---

# Phase 5 — Modern Java (Java 21+)
*Weeks 9–10: Virtual threads, structured concurrency, and parallel streams — the future of Java concurrency.*

---

## 5.1 Virtual Threads (Project Loom — Java 21)

Virtual threads are lightweight threads managed by the JVM rather than the OS. You can create millions of them. They are designed for I/O-bound workloads — exactly what payment systems need (DB calls, HTTP to banks, fraud APIs).

| | Platform Thread | Virtual Thread |
|---|---|---|
| Managed by | OS | JVM |
| Stack size | ~1MB fixed | Grows/shrinks dynamically |
| Max practical count | ~10,000 | Millions |
| Best for | CPU-bound work | I/O-bound work (DB, HTTP) |
| Created via | `new Thread()` | `Thread.ofVirtual().start()` |

```java
// Java 21: virtual thread per payment request

// Old way — thread pool (limits concurrency to pool size)
ExecutorService pool = Executors.newFixedThreadPool(200);
pool.submit(() -> processPayment(payment));

// New way — virtual thread per task (JDK 21+)
// Each payment gets its own virtual thread; JVM schedules them efficiently
ExecutorService virtualExecutor = Executors.newVirtualThreadPerTaskExecutor();
virtualExecutor.submit(() -> processPayment(payment));

// Or directly:
Thread.ofVirtual().start(() -> processPayment(payment));

// KEY DIFFERENCE: Virtual threads block cheaply.
// When a virtual thread blocks on DB call or HTTP, the carrier
// (OS) thread is released to run other virtual threads.
// A platform thread sitting blocked on I/O wastes an OS resource.
// A virtual thread blocked on I/O costs almost nothing.

// CAVEAT: Do NOT use virtual threads for CPU-intensive work.
// For reconciliation (pure computation), keep using ForkJoinPool.
```

---

## 5.2 Structured Concurrency (Java 21 Preview)

Structured concurrency treats a group of tasks as a single unit of work. If any task fails or the scope is cancelled, all tasks are cancelled. This is much safer than managing individual `Future` objects.

```java
// Structured concurrency: run fraud + balance check as a unit.
// If either fails, the other is automatically cancelled.
try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {
    StructuredTaskScope.Subtask<FraudScore> fraud =
        scope.fork(() -> fraudService.check(payment));
    StructuredTaskScope.Subtask<Boolean> balance =
        scope.fork(() -> balanceService.hasFunds(payment));

    scope.join()           // wait for both subtasks
         .throwIfFailed(); // propagate exception if either failed

    // Both succeeded — safe to access results
    FraudScore score = fraud.get();
    Boolean hasFunds = balance.get();
    authorize(payment, score, hasFunds);
}
// The scope auto-cancels remaining tasks on exception or scope exit.
// Contrast with allOf(): if fraud.get() throws, balance task is abandoned
// (still running) — structured concurrency is leak-proof.
```

---

## 5.3 Parallel Streams — When to Use and When Not To

```java
List<Transaction> transactions = loadDailyTransactions(); // 500,000 items

// Parallel stream: uses ForkJoinPool.commonPool() internally
BigDecimal total = transactions.parallelStream()
    .filter(t -> t.getStatus() == COMPLETED)
    .map(Transaction::getAmount)
    .reduce(BigDecimal.ZERO, BigDecimal::add);

// GOOD use cases for parallel streams:
// - Large data sets (500k+ items)
// - CPU-bound operations (calculations, not DB calls)
// - Stateless, associative operations (reduce, collect)

// BAD use cases (avoid parallel streams):
// - I/O operations inside the stream (DB calls, HTTP) — blocks common pool
// - Small collections (overhead > speedup)
// - Order-sensitive operations (findFirst behaves unexpectedly)
// - Shared mutable state inside lambda (race condition!)

// ❌ NEVER do this — calls DB from inside parallel stream:
transactions.parallelStream()
    .forEach(t -> database.save(t)); // blocks common ForkJoinPool threads!
```

---

## 5.4 Debugging Concurrency Issues

| Tool | What It Shows | How to Use |
|---|---|---|
| `jstack <pid>` | Thread dump: all thread states, stack traces, deadlock detection | Run while app is hanging; look for BLOCKED threads and `Found one Java-level deadlock` |
| VisualVM | Live thread count, CPU usage per thread, heap dump | Attach to JVM process; Threads tab shows real-time state transitions |
| `jcmd <pid> Thread.print` | Same as jstack but via jcmd tool | Useful when jstack is unavailable; works inside containers |
| Java Flight Recorder | Low-overhead production profiling: lock contention, thread park/unpark | `jcmd <pid> JFR.start duration=60s`; analyze in JMC |

---

## 5.5 Top Concurrency Anti-Patterns

| Anti-Pattern | What Goes Wrong | Fix |
|---|---|---|
| Swallowing InterruptedException | Thread can never be cancelled; shutdown hangs | Always call `Thread.currentThread().interrupt()` in catch |
| Locking on String literals | String pool means unrelated code shares the same lock | Use a dedicated lock object: `new Object()` |
| Double-checked locking without volatile | Without volatile, partially constructed object visible | Declare field volatile or use initialization-on-demand holder |
| Too-fine-grained locking | Excessive context switching overwhelms benefit | Use ConcurrentHashMap or lock striping instead |
| Not cleaning up ThreadLocal | Thread pool leaks request context across requests | Always call `remove()` in a finally block |
| Calling blocking code on ForkJoinPool | Parallel streams stall because common pool threads are blocked | Never do I/O inside parallel streams; use separate executor |

---

## 5.6 Exercises — Phase 5

> **Exercise 5.1 [Advanced] — Virtual Thread Payment Server:** Build a simple payment processing server. Version A: fixed thread pool of 100 threads. Version B: virtual thread per task. Simulate 5000 concurrent payment requests, each taking 200ms (simulated I/O with `Thread.sleep`). Measure throughput and latency for both. Explain the difference.

> **Exercise 5.2 [Advanced] — Find the Bug:** The code below uses a parallel stream to record payment results. Find 2 concurrency bugs and fix them:
> ```java
> List<String> results = new ArrayList<>();
> transactions.parallelStream().forEach(t -> {
>     results.add(process(t));  // bug 1: ArrayList not thread-safe
>     database.save(t);         // bug 2: blocking I/O inside parallel stream
> });
> ```
> Fix 1: use `Collections.synchronizedList()` or collect with `Collectors.toList()`. Fix 2: move DB saves to a sequential stream or a dedicated executor.

---

## 5.7 Interview Questions — Phase 5

| Level | Question | Key Point |
|---|---|---|
| Mid | What is a virtual thread? | JVM-managed lightweight thread; hundreds of thousands possible; ideal for I/O-bound tasks |
| Mid | When should you NOT use virtual threads? | CPU-bound work — they still need carrier threads; use ForkJoinPool instead |
| Senior | Virtual threads vs reactive programming? | Virtual threads write sync-style code that scales like reactive; less complexity, similar throughput |
| Senior | What is structured concurrency and why is it safer? | Groups related tasks; cancels remaining tasks on failure; no orphaned/leaked tasks like with raw Future |
| Senior | How do you detect a deadlock in production? | jstack or JFR; look for BLOCKED threads all waiting on each other with circular dependency |
| System Design | Design a payment system handling 50k TPS on Java 21 | Virtual thread per request + structured concurrency for parallel checks + DB connection pool |

---

# Quick Reference — Concurrency Cheat Sheet

## When to Use What

| Scenario | Best Tool |
|---|---|
| Run a task on a thread | `ExecutorService.submit(Runnable/Callable)` |
| Wait for a result | `Future.get(timeout)` |
| Chain async steps | `CompletableFuture` |
| Rate-limit API calls | `Semaphore` |
| Wait for N tasks to all complete | `CountDownLatch` or `CompletableFuture.allOf()` |
| Simple thread-safe counter | `AtomicInteger` / `AtomicLong` |
| Thread-safe map with high reads | `ConcurrentHashMap` |
| Bounded work queue | `LinkedBlockingQueue` |
| Lock with timeout / fair lock | `ReentrantLock` |
| Per-thread request context | `ThreadLocal` (remember `remove()`!) |
| I/O-bound high concurrency (Java 21) | Virtual threads |
| CPU-bound parallel computation | `ForkJoinPool` / parallel streams |
| Group related concurrent tasks safely | `StructuredTaskScope` (Java 21) |

---

## Key Rules to Never Break

1. **Never swallow `InterruptedException`** — always call `Thread.currentThread().interrupt()`
2. **Always use `while` not `if` with `wait()`** — spurious wakeups are real
3. **Always release locks in `finally` blocks** — `lock.unlock()` and `semaphore.release()`
4. **Always clean up `ThreadLocal`** — call `remove()` in a finally block in thread pools
5. **Never do I/O inside parallel streams** — it blocks the shared ForkJoinPool
6. **Always use a timeout on `Future.get()`** — never block indefinitely
7. **Acquire multiple locks in consistent order** — always lowest ID first to prevent deadlock

---

*Java Concurrency Textbook — 2026 Edition | All Phases | Payment & Transaction Systems*