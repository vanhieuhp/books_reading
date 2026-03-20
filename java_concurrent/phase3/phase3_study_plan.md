# Phase 3 — Study Plan: java.util.concurrent Mastery
## Java Concurrency: From Threads to Virtual Threads (2026 Ed.)

---

```
📘 Book:  Java Concurrency: From Threads to Virtual Threads
📖 Topic: Phase 3 — java.util.concurrent Mastery Plan
🎯 Learning Objectives
   • Master every production-critical class in java.util.concurrent
   • Build muscle memory through targeted code labs
   • Connect each class to real payment/transaction system scenarios
   • Pass mid-to-senior Java concurrency interviews with confidence
   • Design production-grade concurrent systems from scratch
⏱ Estimated total time: 4 weeks (30–45 min/day, 5 days/week)
🧠 Prereqs: Phase 1 (Thread lifecycle, Runnable, sleep/join/interrupt, race conditions)
```

---

## Master Study Plan: Phase 3 — java.util.concurrent

### 📅 Week 1 — Thread Pools & Async Results
*Theme: "Never create threads manually in production."*

---

#### Day 1 — `ExecutorService` & Thread Pool Fundamentals

**🎯 Goals**
- Understand why thread creation is expensive
- Know every `Executors` factory method and when to use each
- Master graceful vs. force shutdown patterns

**📖 Read:** Section 3.1 (textbook lines 312–353)

**Study Notes**

| Factory Method | Pool Type | Use When |
|---|---|---|
| `newFixedThreadPool(n)` | Fixed-size | CPU-bound or known concurrency level |
| `newCachedThreadPool()` | Unlimited growth | Short-lived, bursty tasks (use with caution!) |
| `newSingleThreadExecutor()` | 1 thread | Sequential task queue, guaranteed ordering |
| `newScheduledThreadPool(n)` | Fixed + scheduling | Retries, scheduled retries, heartbeat |
| `newVirtualThreadPerTaskExecutor()` | VT per task (Java 21+) | I/O-bound, millions of concurrent tasks |

**⚠️ Common Misconception**
> "I'll just use `newCachedThreadPool()` — it auto-scales!"
Reality: Unlimited pool can spawn thousands of threads under load → OOM. Use `newFixedThreadPool` or bounded queues.

**Code Lab 1 (Day 1): Payment Service with Graceful Shutdown**
```java
// Goal: Build a PaymentService that handles 10k payments
// and shuts down gracefully — no lost transactions.

public class PaymentService {
    private final ExecutorService executor;

    public PaymentService() {
        // Rule of thumb: 2–4x CPU cores for I/O-bound work
        int threads = Runtime.getRuntime().availableProcessors() * 2;
        this.executor = Executors.newFixedThreadPool(threads);
    }

    public Future<PaymentResult> submitPayment(Payment payment) {
        return executor.submit(() -> processPayment(payment));
    }

    private PaymentResult processPayment(Payment payment) {
        // Simulate I/O: DB call + HTTP to bank
        return new PaymentResult(payment.getId(), Status.AUTHORIZED);
    }

    // ❌ WRONG: executor.shutdown(); // may lose pending tasks!
    // ✅ RIGHT: graceful shutdown with timeout
    public void shutdown() throws InterruptedException {
        executor.shutdown(); // stop accepting new tasks
        boolean terminated =
            executor.awaitTermination(30, TimeUnit.SECONDS);
        if (!terminated) {
            executor.shutdownNow(); // interrupt/kill remaining
            boolean forceKilled =
                executor.awaitTermination(10, TimeUnit.SECONDS);
            if (!forceKilled) {
                log.error("Executor did not terminate — {} tasks lost",
                    ((ThreadPoolExecutor) executor).getActiveCount());
            }
        }
    }
}
```

**🔬 Measure:** Add `System.nanoTime()` before/after processing 1,000 payments. Vary pool size (1, 2, 4, 8, 16, 100). Plot throughput vs. pool size.

---

#### Day 2 — `Callable` & `Future`

**🎯 Goals**
- Distinguish `Runnable` (no return, no checked exception) from `Callable<T>` (returns value, can throw)
- Master `Future.get()` with timeout — **never block forever**
- Handle `ExecutionException` without swallowing root cause

**📖 Read:** Section 3.2 (lines 356–378)

**Code Lab 2: Parallel Fraud + Balance Check**
```java
// Simulate a payment authorization: run fraud check and balance check
// in PARALLEL, collect both results, then decide.

public class ParallelAuthorization {
    private final ExecutorService executor =
        Executors.newFixedThreadPool(4);

    public AuthorizationResult authorize(Payment payment) {
        try {
            Callable<FraudScore> fraudTask   = () -> fraudService.check(payment);
            Callable<Boolean>    balanceTask = () -> balanceService.hasFunds(payment);

            // Submit both simultaneously — they run in PARALLEL
            Future<FraudScore> fraudFuture   = executor.submit(fraudTask);
            Future<Boolean>    balanceFuture = executor.submit(balanceTask);

            // ⚠️ KEY: Always use timeout — never call get() without it!
            FraudScore fraud   = fraudFuture.get(5, TimeUnit.SECONDS);
            Boolean   hasFunds = balanceFuture.get(5, TimeUnit.SECONDS);

            if (fraud.isRisky() || !hasFunds) {
                return AuthorizationResult.DECLINED;
            }
            return AuthorizationResult.APPROVED;

        } catch (TimeoutException e) {
            // ✅ Correct: don't swallow — propagate as business exception
            throw new PaymentTimeoutException("Authorization timed out", e);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt(); // restore interrupt flag!
            throw new PaymentException("Authorization interrupted", e);
        } catch (ExecutionException e) {
            // ⚠️ CRITICAL: ExecutionException wraps the REAL cause
            Throwable cause = e.getCause();
            log.error("Authorization service failed", cause);
            throw new PaymentException("Authorization error: " + cause.getMessage(), cause);
        }
    }

    // ❌ WRONG: swallowing the cause — what actually failed?
    // } catch (ExecutionException e) {
    //     log.error("Failed", e);    // e is just the wrapper!
    // }
}
```

**🔬 Measure:** Time sequential (fraud then balance) vs. parallel. At 100ms per check: sequential = 200ms, parallel ≈ 100ms. Show the speedup.

---

#### Day 3 — Week 1 Review & Consolidation

**✅ Self-Assessment Checklist**
- [ ] Can you explain why `new Thread().start()` doesn't scale?
- [ ] Can you write a graceful shutdown sequence from memory?
- [ ] Do you know why `Future.get()` without timeout is dangerous?
- [ ] Can you unwrap `ExecutionException` and log the real cause?
- [ ] Do you know which `Executors` factory to use for batch processing?

**🧪 Integration Exercise:** Build a `PaymentBatchProcessor` that:
1. Submits 1,000 payments to a fixed thread pool
2. Collects all `Future` results with 10s total timeout
3. Reports: total processed, total declined, total errors
4. Shuts down gracefully, measuring shutdown time

**Interview Drill (Day 3)**
> "What's the difference between `Runnable` and `Callable`? When would you use each?"

> "If you call `Future.get()` and it throws `ExecutionException`, how do you find the root cause?"

---

### 📅 Week 2 — Atomic Classes & Explicit Locks
*Theme: "CAS is fast until it isn't. Know when to use which."*

---

#### Day 4 — AtomicInteger, AtomicLong, AtomicReference

**🎯 Goals**
- Understand CAS (Compare-And-Swap) vs. synchronized — when each wins
- Master `incrementAndGet()`, `addAndGet()`, `compareAndSet()` (the "retry loop")
- Know the atomic field updaters for existing classes

**📖 Read:** Section 3.4 (lines 415–442)

**Mental Model: CAS vs. Lock**
```
Synchronized:   Thread grabs lock → does work → releases lock
                → other threads BLOCKED while waiting

CAS:            Thread reads value → computes new value
                → CAS(original, new) — succeeds only if no one changed it
                → if CAS fails: retry (optimistic — no blocking)

Performance:
  Low contention  → CAS wins (no context switching)
  High contention → synchronized wins (fewer retries)
  Ultra-high      → specialized data structures (ConcurrentHashMap striping)
```

**Code Lab 3: Payment Metrics Collector**
```java
// Goal: Track payment processing metrics with zero locks
// Throughput target: 1 million increments/second

public class PaymentMetrics {
    // ❌ WRONG: synchronized increments — slower under high concurrency
    // private int totalProcessed;
    // public synchronized void increment() { totalProcessed++; }

    // ✅ RIGHT: AtomicLong — CAS-based, lock-free
    private final AtomicLong totalProcessed   = new AtomicLong(0);
    private final AtomicLong totalAmountCents = new AtomicLong(0);
    private final AtomicInteger activeWorkers = new AtomicInteger(0);

    public void recordPayment(long amountCents) {
        totalProcessed.incrementAndGet();     // returns new value
        totalAmountCents.addAndGet(amountCents);
    }

    public void workerJoined()  { activeWorkers.incrementAndGet(); }
    public void workerLeft()    { activeWorkers.decrementAndGet(); }

    // CAS retry loop: update max seen value
    private final AtomicLong maxTransaction = new AtomicLong(0);

    public void observeMax(long amount) {
        long current;
        do {
            current = maxTransaction.get();
            if (amount <= current) return; // no update needed
        } while (!maxTransaction.compareAndSet(current, amount));
        // If another thread updated it first → retry with new value
        // This is LOCK-FREE (threads never block each other)
        // but not WAIT-FREE (may retry many times under high contention)
    }

    // ⚠️ Hidden pitfall: the classic race still exists in wrong code:
    // if (maxTransaction.get() < amount) {        // Thread A reads 1000
    //     maxTransaction.set(amount);             // Thread B also reads 1000 — both set!
    // }                                           // Correct: use compareAndSet
}
```

**🔬 Measure:** Run 100 threads, each incrementing 100,000 times. Compare `synchronized counter` vs. `AtomicLong`. Expected: AtomicLong 3–5x faster under high contention.

**Bonus: AtomicFieldUpdater**
```java
// If you can't modify the class to add AtomicLong:
// Use AtomicLongFieldUpdater on existing POJOs

public class Transaction {
    volatile long amountCents; // must be volatile!
}

AtomicLongFieldUpdater<Transaction> updater =
    AtomicLongFieldUpdater.newUpdater(Transaction.class, "amountCents");

// Thread-safe update without changing the class:
updater.compareAndSet(tx, oldAmount, newAmount);
```

---

#### Day 5 — `ReentrantLock` & `Condition`

**🎯 Goals**
- Know why `ReentrantLock` exists beyond `synchronized` (tryLock, fairness, multiple conditions)
- Master the lock → try → unlock pattern with `finally`
- Use `Condition` for multiple independent wait sets

**📖 Read:** Section 3.3 (lines 381–411)

**Code Lab 4: Transfer Service with Timeout-based Deadlock Prevention**
```java
// ReentrantLock gives us tryLock() with timeout — key to deadlock prevention
// This replaces the synchronized + consistent ordering pattern from Phase 2

public class TransferService {
    private final Map<String, ReentrantLock> locks = new ConcurrentHashMap<>();

    public boolean transfer(String fromId, String toId, BigDecimal amount) {
        if (fromId.equals(toId)) return false;

        ReentrantLock lockA = locks.computeIfAbsent(fromId, k -> new ReentrantLock());
        ReentrantLock lockB = locks.computeIfAbsent(toId,   k -> new ReentrantLock());

        // Always lock in consistent order by ID to prevent deadlocks
        ReentrantLock first  = fromId.compareTo(toId) < 0 ? lockA : lockB;
        ReentrantLock second = fromId.compareTo(toId) < 0 ? lockB : lockA;

        try {
            // ❌ OLD WAY (Phase 2): synchronized — if timeout needed, impossible
            // synchronized (first) { synchronized (second) { ... } }

            // ✅ NEW WAY: tryLock with timeout — if can't get locks in 1s, abort
            if (first.tryLock(1, TimeUnit.SECONDS)) {
                try {
                    if (second.tryLock(1, TimeUnit.SECONDS)) {
                        try {
                            return executeTransfer(fromId, toId, amount);
                        } finally {
                            second.unlock();
                        }
                    }
                    // ⚠️ If we got first but not second: deadlock risk!
                    // tryLock gives us a clean exit instead of waiting forever
                } finally {
                    first.unlock();
                }
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
        return false; // timeout — caller should retry with backoff
    }

    // tryLock also enables fair locking (FIFO order):
    // new ReentrantLock(true) — threads get lock in order they requested
    // ⚠️ Fair locks are SLOWER due to queue management — use only when
    // fairness is legally required (e.g., financial processing)
}
```

**Condition — Multiple Wait Sets**
```java
// synchronized only has ONE wait set (on the object monitor)
// ReentrantLock + Condition = MULTIPLE independent wait sets

public class PaymentStateMachine {
    private final ReentrantLock lock = new ReentrantLock();
    private final Condition pending  = lock.newCondition();
    private final Condition approved = lock.newCondition();
    private final Condition declined = lock.newCondition();

    private String state = "PENDING";

    public void waitForApproval() throws InterruptedException {
        lock.lock();
        try {
            while ("PENDING".equals(state)) {
                approved.await(); // only wakes when state = APPROVED
            }
        } finally { lock.unlock(); }
    }

    public void approve() {
        lock.lock();
        try {
            state = "APPROVED";
            approved.signalAll(); // wake all threads waiting for approval
        } finally { lock.unlock(); }
    }
}
```

---

#### Day 6 — Week 2 Review & StampedLock Preview

**✅ Self-Assessment Checklist**
- [ ] Can you explain CAS in terms a junior developer would understand?
- [ ] Do you know the difference between lock-free and wait-free?
- [ ] Can you write a retry loop with `compareAndSet` from memory?
- [ ] Do you know when to prefer `ReentrantLock.tryLock()` over `synchronized`?
- [ ] Can you name 3 things `ReentrantLock` does that `synchronized` cannot?

**🔑 Bonus: StampedLock (advanced, Java 8+)**
```java
// StampedLock: read-optimized — multiple readers, exclusive writer
// Better than ReentrantReadWriteLock: optimistic read mode

StampedLock lock = new StampedLock();

// Pessimistic read (like RWLock read)
long stamp = lock.readLock();
try {
    return balance;
} finally { lock.unlockRead(stamp); }

// ✅ Optimistic read — no lock! Check validity after.
// Use when reads are much more frequent than writes
public double getBalanceOptimistic() {
    long stamp = lock.tryOptimisticRead();
    double balance = this.balance;  // read without lock
    if (!lock.validate(stamp)) {    // if write happened concurrently
        stamp = lock.readLock();     // retry as pessimistic read
        try { return this.balance; }
        finally { lock.unlockRead(stamp); }
    }
    return balance;
}
```

**Interview Drill (Day 6)**
> "AtomicLong.incrementAndGet() uses CAS. Under 10,000 concurrent threads all incrementing the same counter, what happens to performance?"

> "When would you use `Condition` instead of `Object.wait()/notify()`?"

---

### 📅 Week 3 — Concurrent Collections
*Theme: "The right data structure eliminates 80% of synchronization needs."*

---

#### Day 7 — `ConcurrentHashMap`

**🎯 Goals**
- Understand internal segmentation (pre-Java 8) vs. CAS + synchronized buckets (Java 8+)
- Master `compute()`, `merge()`, `computeIfAbsent()` — the "atomic read-modify-write" methods
- Know why `Collections.synchronizedMap()` is almost never the right answer

**📖 Read:** Section 3.5 (lines 445–455)

**Code Lab 5: Session Token Cache with Atomic Updates**
```java
// ConcurrentHashMap is NOT just a thread-safe HashMap
// Its atomic methods (compute, merge) eliminate the need for
// synchronized blocks around read-modify-write patterns

public class TokenCache {
    private final ConcurrentHashMap<String, SessionToken> cache =
        new ConcurrentHashMap<>();

    // ❌ OLD WAY (requires synchronization):
    // public void updateToken(String userId, Token newToken) {
    //     synchronized (cache) {
    //         cache.put(userId, newToken); // atomic put, but...
    //     }
    //     // Still has TOCTOU race between get and compute
    // }

    // ✅ NEW WAY: atomic compute — read + modify + write in ONE operation
    public void recordPayment(String userId, long amountCents) {
        cache.compute(userId, (key, existing) -> {
            // This lambda runs atomically — no race between read and write
            if (existing == null) {
                return new SessionToken(1, amountCents);
            }
            return existing.withNewPayment(amountCents);
        });
    }

    // computeIfAbsent — perfect for lazy initialization with caching
    public SessionToken getOrCreate(String userId) {
        // Only invokes the lambda if the key is absent — thread-safe
        return cache.computeIfAbsent(userId, id -> new SessionToken(id));
    }

    // merge — atomic "upsert" with conflict resolution
    public void mergePayment(String userId, long amount) {
        cache.merge(userId, new SessionToken(1, amount),
            (existing, newToken) -> existing.merge(newToken));
    }

    // ⚠️ DON'T do this — iterating over ConcurrentHashMap while
    // another thread modifies it is safe (weakly consistent)
    // but the iterator may not see recent updates
    for (Map.Entry<String, SessionToken> e : cache.entrySet()) {
        // Safe to READ but don't remove with map.remove(key) —
        // use cache.remove(key, expectedValue) instead
    }

    // Atomic remove — only removes if value matches (perfect for CAS-like remove)
    cache.remove(userId, expectedToken); // only removes if still the same
}
```

**Comparison: ConcurrentHashMap vs. Everything Else**
```
Collections.synchronizedMap()  → 1 lock for entire map. ~100x slower at high concurrency
ConcurrentHashMap             → 16+ segment locks (old) or CAS buckets (new). Scales.
Hashtable                    → 1 lock. Deprecated for concurrent use.
```

---

#### Day 8 — Queues: `LinkedBlockingQueue`, `ConcurrentLinkedQueue`

**🎯 Goals**
- Understand bounded vs. unbounded queues and backpressure
- Master `put()` (blocks) vs. `offer()` (non-blocking with capacity check)
- Know when to use `LinkedBlockingQueue` vs. `ConcurrentLinkedQueue`

**📖 Read:** Section 3.5 + textbook's TransactionQueue example (lines 223–251)

**Code Lab 6: Transaction Processing Pipeline with Backpressure**
```java
// Bounded queue = built-in backpressure
// When queue is full, producers BLOCK instead of flooding the system

public class TransactionProcessor {
    private final BlockingQueue<Transaction> queue;

    public TransactionProcessor(int capacity) {
        // Bounded = backpressure. When capacity is reached, put() blocks.
        // This naturally throttles producers without external rate limiting.
        this.queue = new LinkedBlockingQueue<>(capacity);
    }

    // Producer side — BLOCKS if queue is full
    public void submit(Transaction txn) throws InterruptedException {
        queue.put(txn); // blocks until space available
        // Contrast: queue.offer(txn, 5, TimeUnit.SECONDS) — timeout instead
        // Contrast: queue.offer(txn) — returns false immediately, no block
    }

    // Consumer side — BLOCKS if queue is empty
    public Transaction next() throws InterruptedException {
        return queue.take(); // blocks until work available
        // Contrast: queue.poll(5, TimeUnit.SECONDS) — timeout
    }

    // ⚠️ CRITICAL: LinkedBlockingQueue uses TWO separate locks
    // (one for head, one for tail) — allows simultaneous put + take!
    // This is why it outperforms synchronized LinkedList by ~2x

    // Architecture:
    // Producer threads ──put()──► [LinkedBlockingQueue] ──take()──► Consumer threads
    //                          (bounded: 10k items)
    //                          backpressure when full
}
```

**When to use which queue:**
```
LinkedBlockingQueue      → Bounded producer-consumer with backpressure
ConcurrentLinkedQueue    → Lock-free unbounded (no backpressure — watch OOM!)
PriorityBlockingQueue   → Priority-based consumer ordering (high-value first)
ArrayBlockingQueue      → Bounded with array backing (fixed size, lower memory)
SynchronousQueue        → Zero-capacity — handoff semantics (thread rendezvous)
DelayQueue              → Elements only available after delay (scheduled retries)
```

---

#### Day 9 — Synchronization Utilities Deep Dive

**🎯 Goals**
- `CountDownLatch` = one-shot barrier (fire once, wait for N events)
- `CyclicBarrier` = reusable barrier (N threads meet, then release, repeat)
- `Semaphore` = permits-based rate limiting

**📖 Read:** Section 3.6 (lines 460–484)

**Code Lab 7: End-of-Day Settlement with CountDownLatch**
```java
// Scenario: Settlement requires ALL of these to complete before releasing funds:
// 1. Fraud review of all today's transactions
// 2. Balance reconciliation across all accounts
// 3. KYC compliance check
// 4. Regulatory reporting

public class SettlementService {
    private final ExecutorService executor = Executors.newFixedThreadPool(4);

    public SettlementReport runEndOfDaySettlement(List<Transaction> txns)
            throws InterruptedException {

        CountDownLatch latch = new CountDownLatch(4);
        SettlementReport report = new SettlementReport();

        executor.submit(() -> {
            try { report.fraudResults = runFraudReview(txns); }
            finally { latch.countDown(); }
        });
        executor.submit(() -> {
            try { report.balanceResults = reconcileBalances(txns); }
            finally { latch.countDown(); }
        });
        executor.submit(() -> {
            try { report.kycResults = runKycChecks(txns); }
            finally { latch.countDown(); }
        });
        executor.submit(() -> {
            try { report.regulatoryResults = generateRegulatoryReport(txns); }
            finally { latch.countDown(); }
        });

        // Wait up to 1 hour for ALL 4 tasks to complete
        boolean allDone = latch.await(1, TimeUnit.HOURS);
        if (!allDone) {
            throw new SettlementTimeoutException("Settlement exceeded 1 hour SLA");
        }
        return report;
    }

    // ⚠️ CountDownLatch is ONE-SHOT: after countdown reaches 0, it cannot be reused
    // ✅ For repeated sync points: use CyclicBarrier instead
}
```

**Code Lab 8: Rate-Limited Payment API with Semaphore**
```java
// Scenario: External payment processor allows max 20 concurrent connections.
// 100 payment threads want to call it. Use Semaphore to limit concurrency.

public class RateLimitedPaymentGateway {
    private final Semaphore permits = new Semaphore(20);
    private final ExternalPaymentApi api;

    public PaymentResult callApi(Payment payment) throws PaymentException {
        boolean acquired = false;
        try {
            // ❌ WRONG: permits.acquire() without timeout
            // If API is down, all 20 permits held forever → total outage
            // ✅ RIGHT: acquire with timeout — fail fast after 2 seconds

            acquired = permits.tryAcquire(2, TimeUnit.SECONDS);
            if (!acquired) {
                throw new RateLimitException("API limit: waited > 2s for slot");
            }
            return api.process(payment);

        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new PaymentException("Interrupted during API call", e);
        } finally {
            if (acquired) {
                permits.release(); // ⚠️ ALWAYS in finally — even on exception!
            }
        }
    }

    // Alternative: blocking acquire with interrupt
    // permits.acquire();
    // try { api.process(payment); }
    // finally { permits.release(); }
}
```

---

#### Day 10 — Week 3 Review

**✅ Self-Assessment Checklist**
- [ ] Can you name when to use `compute()` vs `computeIfAbsent()` on CHM?
- [ ] Do you know the difference between `put()` and `offer()` on BlockingQueue?
- [ ] Can you explain why bounded queues provide natural backpressure?
- [ ] Can you explain why `CountDownLatch` cannot be reused?
- [ ] Do you know how Semaphore relates to connection pooling?

**Interview Drill (Day 10)**
> "Design a system where 10 producer threads submit tasks and 5 consumer threads process them. Use a bounded queue. Show both blocking and non-blocking submission options."

> "Why does ConcurrentHashMap's `computeIfAbsent` have a known deadlock pitfall with recursive calls?"

---

### 📅 Week 4 — Integration, Patterns & Interview Prep
*Theme: "Connect the pieces into production systems."*

---

#### Day 11 — Exercise 3.1: Rate Limiter Lab

**🧪 Full Lab: Payment Rate Limiter with Throughput Measurement**
```
Goal: Build PaymentRateLimiter allowing max 20 concurrent API calls.
      Simulate 100 payments (200ms each). Measure throughput.

Success criteria:
  - Semaphore limits to exactly 20 concurrent calls
  - Threads waiting > 2s fail-fast with RateLimitException
  - Throughput: ~100 payments/second (5 batches × 20)
  - Compare: without limiter (100 in ~200ms) vs. with limiter (~5s)
```

```java
public class PaymentRateLimiter {
    private final Semaphore limiter = new Semaphore(20);
    private final ExecutorService executor =
        Executors.newFixedThreadPool(100);

    public List<PaymentResult> processAll(List<Payment> payments)
            throws InterruptedException {
        List<Future<PaymentResult>> futures = new ArrayList<>();

        for (Payment p : payments) {
            Future<PaymentResult> f = executor.submit(() -> {
                if (!limiter.tryAcquire(2, TimeUnit.SECONDS)) {
                    throw new RateLimitException("Timeout waiting for slot");
                }
                try {
                    return callPaymentApi(p); // 200ms I/O
                } finally {
                    limiter.release();
                }
            });
            futures.add(f);
        }

        // Collect results with timeout
        List<PaymentResult> results = new ArrayList<>();
        for (Future<PaymentResult> f : futures) {
            results.add(f.get(30, TimeUnit.SECONDS));
        }
        return results;
    }
}
```

**Expected measurement:**
```
Without limiter:  100 × 200ms = ~200ms total (all run immediately)
With limiter:     100 × 200ms / 20 = ~1000ms total (batched in groups of 20)
Throughput drop:  intentional — we traded raw speed for system stability
```

---

#### Day 12 — Exercise 3.2: Parallel Authorization System

**🧪 Full Lab: Parallel 3-Way Authorization**
```
Goal: Process 1000 transactions. For each:
  1. Run fraud check, balance check, KYC in PARALLEL
  2. Only authorize if ALL 3 pass
  3. Collect results in ConcurrentHashMap<txnId, result>
  4. Graceful shutdown
```

```java
public class ParallelAuthorizationSystem {
    private final ExecutorService executor =
        Executors.newFixedThreadPool(50); // I/O-bound: 2x cores
    private final ConcurrentHashMap<String, AuthorizationResult> results =
        new ConcurrentHashMap<>();

    public void processAll(List<Transaction> txns) throws InterruptedException {
        CountDownLatch latch = new CountDownLatch(txns.size());

        for (Transaction txn : txns) {
            executor.submit(() -> {
                try {
                    AuthorizationResult result = authorize(txn);
                    results.put(txn.getId(), result);
                } finally {
                    latch.countDown();
                }
            });
        }

        // Wait for all 1000 authorizations
        boolean allDone = latch.await(5, TimeUnit.MINUTES);
        if (!allDone) {
            log.error("{} transactions still pending after 5 min timeout",
                latch.getCount());
        }
    }

    private AuthorizationResult authorize(Transaction txn)
            throws InterruptedException {
        CountDownLatch checkLatch = new CountDownLatch(3);
        AtomicReference<FraudScore> fraud    = new AtomicReference<>();
        AtomicBoolean               hasFunds = new AtomicBoolean(false);
        AtomicBoolean               kycOk    = new AtomicBoolean(false);

        executor.submit(() -> {
            try { fraud.set(fraudService.check(txn)); }
            finally { checkLatch.countDown(); }
        });
        executor.submit(() -> {
            try { hasFunds.set(balanceService.hasFunds(txn)); }
            finally { checkLatch.countDown(); }
        });
        executor.submit(() -> {
            try { kycOk.set(kycService.isCompliant(txn)); }
            finally { checkLatch.countDown(); }
        });

        checkLatch.await(10, TimeUnit.SECONDS);

        if (fraud.get().isRisky() || !hasFunds.get() || !kycOk.get()) {
            return AuthorizationResult.DECLINED;
        }
        return AuthorizationResult.APPROVED;
    }
}
```

---

#### Day 13 — Cross-Class Design: High-Throughput Payment Gateway

**🏗 System Design: Putting It All Together**

```
┌─────────────────────────────────────────────────────────────────────┐
│                  Payment Gateway Architecture                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  HTTP Request ──► VirtualThreads/ThreadPool ──► Route by type       │
│                           │                                          │
│            ┌──────────────┼──────────────┐                          │
│            ▼              ▼              ▼                          │
│     FraudCheck      BalanceCheck     KycCheck                        │
│   (Parallel via    (Parallel via    (Parallel via                   │
│    CountDownLatch)  CountDownLatch)  CountDownLatch)                │
│            │              │              │                           │
│            └──────────────┼──────────────┘                          │
│                           ▼                                         │
│                 ConcurrentHashMap<txnId, result>                    │
│                           │                                         │
│            ┌──────────────┴──────────────┐                          │
│            ▼                             ▼                          │
│   Semaphore(20) per API            LinkedBQ(capacity=1000)          │
│   External Payment Processor       Internal audit log               │
│                                                                      │
│  Metrics: AtomicLong(totalProcessed), AtomicLong(totalAmount)        │
└─────────────────────────────────────────────────────────────────────┘
```

**Key design decisions:**
```
Thread pool size:    Runtime.availableProcessors() × 2   (I/O-bound)
Rate limiting:       Semaphore(20) on external API calls
Result collection:   ConcurrentHashMap (lock-free reads)
Atomic counters:     AtomicLong for metrics (no lock needed)
Parallel checks:     CountDownLatch(3) for fraud+balance+KYC
Backpressure:        LinkedBlockingQueue(1000) between stages
```

---

#### Day 14 — Interview Prep Day

**All Phase 3 Interview Questions with Full Answers**

| Level | Question | Full Answer |
|---|---|---|
| **Mid** | What pool types does `Executors` provide? | `newFixedThreadPool(n)`, `newCachedThreadPool()`, `newSingleThreadExecutor()`, `newScheduledThreadPool(n)`, `newVirtualThreadPerTaskExecutor()`. Fixed = bounded concurrency; Cached = unlimited growth (dangerous); Single = guaranteed ordering |
| **Mid** | `Future.get()` vs `Future.get(timeout)`? | `get()` blocks forever — if task never completes, thread hangs forever. `get(timeout)` throws `TimeoutException` — always use this in production |
| **Mid** | `ConcurrentHashMap` vs `Collections.synchronizedMap()`? | CHM uses per-segment locking or CAS — high concurrency. synchronizedMap uses single lock — entire map locked on every operation. CHM 10–100× faster under contention |
| **Senior** | When would you use `Semaphore` in a payment system? | Rate limiting external API calls (max N concurrent connections). DB connection pool sizing. Limiting parallel file writes. Prevents resource exhaustion from burst traffic |
| **Senior** | `CountDownLatch` vs `CyclicBarrier`? | Latch: one-shot countdown → `countDown()` can only decrease. Used for "wait for N tasks to finish" (settlement, batch completion). Barrier: reusable → threads `await()` at a point, all released together, resets. Used for phased computation |
| **Senior** | What is lock-free programming? | Programming with CAS operations (`AtomicXxx.compareAndSet`) — threads never block each other. Lower latency under low contention. Higher CPU cost under high contention (retry loops). Not wait-free — retries still cost CPU |
| **Senior** | `AtomicInteger.incrementAndGet()` — how does it differ from `i++`? | `i++` is 3 ops (read, increment, write) with race between steps. `incrementAndGet()` is a single CAS — atomic by hardware. Under extreme contention, CAS fails and retries — but no threads are blocked |

**Whiteboard Design Question**
> "Design the concurrent components of a payment system that processes 50k TPS."

```
Answer framework:
1. Virtual threads / fixed thread pool for I/O concurrency
2. ConcurrentHashMap for session/token state
3. Semaphore for external API rate limiting
4. LinkedBlockingQueue for backpressure between pipeline stages
5. AtomicLong for metrics (no lock needed)
6. CountDownLatch for multi-service parallel checks
7. ForkJoinPool for CPU-bound reconciliation
```

---

#### Day 15 — Spaced Repetition & Assessment

**🔁 1-Week Review Questions (answer without looking up docs):**

1. Write the shutdown sequence for `ExecutorService` from memory. What happens if you skip `awaitTermination`?

2. Write a CAS retry loop that updates the maximum value seen, using `AtomicLong`.

3. How do you prevent deadlock when acquiring two locks on two accounts in unknown order?

4. `ConcurrentHashMap.compute()` — why is it safer than synchronized + map.get/put?

5. What's the difference between `BlockingQueue.take()` and `BlockingQueue.poll()`?

6. When would `CountDownLatch` fail you that `CyclicBarrier` would handle?

**📌 The ONE sentence worth memorizing from Phase 3:**
> *"Every java.util.concurrent class exists to solve a specific concurrency problem — choosing the right one eliminates synchronization code you would otherwise have to write and maintain yourself."*

---

## 📊 Progress Tracking Template

```
┌──────────────────────────────────────────────────────────────────┐
│  Phase 3 Mastery Tracker                                          │
├────────┬──────────────┬────────────┬────────────┬────────────────┤
│  Day   │  Topic       │  Read      │  Lab Done  │  Interview Q   │
├────────┼──────────────┼────────────┼────────────┼────────────────┤
│  1     │ ExecutorSvc  │  §3.1      │  [ ]       │  [ ]           │
│  2     │ Future/Call  │  §3.2      │  [ ]       │  [ ]           │
│  3     │ Week 1 Review│  —         │  [ ]       │  [ ]           │
│  4     │ AtomicXxx    │  §3.4      │  [ ]       │  [ ]           │
│  5     │ ReentrantLock│  §3.3      │  [ ]       │  [ ]           │
│  6     │ Week 2 Review│  —         │  [ ]       │  [ ]           │
│  7     │ CHM          │  §3.5      │  [ ]       │  [ ]           │
│  8     │ Queues       │  §3.5      │  [ ]       │  [ ]           │
│  9     │ Sync Utils   │  §3.6      │  [ ]       │  [ ]           │
│  10    │ Week 3 Review│  —         │  [ ]       │  [ ]           │
│  11    │ Ex 3.1       │  —         │  [ ]       │  [ ]           │
│  12    │ Ex 3.2       │  —         │  [ ]       │  [ ]           │
│  13    │ System Design│  —         │  [ ]       │  [ ]           │
│  14    │ Interview    │  §3.7-3.8  │  —         │  [ ]           │
│  15    │ Assessment    │  All       │  [ ]       │  [ ]           │
└────────┴──────────────┴────────────┴────────────┴────────────────┘
```

---

**🔗 Connect Forward:** Phase 3 classes form the foundation for Phase 4's `CompletableFuture` pipelines and Phase 5's virtual threads. Mastering `ExecutorService` + concurrent collections now makes Phase 4's async composition feel natural.
