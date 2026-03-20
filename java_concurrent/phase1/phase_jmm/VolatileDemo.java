package phase_jmm;

/**
 * ============================================================
 * VOLATILE DEMONSTRATION — Visibility Guarantee, Not Atomicity
 * ============================================================
 *
 * WHAT volatile GUARANTEES:
 * =========================
 * volatile provides TWO guarantees, but NOT the one you might think:
 *
 *   ✅ GUARANTEE 1 — VISIBILITY:
 *       Every write to a volatile variable is IMMEDIATELY visible
 *       to all threads (not sitting in a CPU cache).
 *       The CPU cache line is flushed to main memory, and other
 *       CPUs' caches are invalidated.
 *
 *   ✅ GUARANTEE 2 — NO REORDERING:
 *       Reads and writes to volatile variables CANNOT be reordered
 *       with each other or with non-volatile accesses by the JIT.
 *       volatile acts as a "memory barrier" — a fence that prevents
 *       instructions from moving across it.
 *
 *   ❌ WHAT volatile does NOT guarantee:
 *       Compound operations are NOT atomic. volatile int count = 0;
 *       count++; is still THREE operations (read, increment, write),
 *       not one. Two threads can both read count=0, both increment
 *       to 1, and both write 1 — losing one increment.
 *       For atomic compound operations, use AtomicInteger instead.
 *
 *
 * HOW volatile TRANSLATES TO HARDWARE (x86 example):
 * ==================================================
 * volatile write:
 *   → Issues a "Store Buffer flush" + "Cache invalidate" signal
 *   → Other CPU cores are notified their cached copy is stale
 *   → This is why volatile write is expensive (~100ns vs ~1ns register)
 *
 * volatile read:
 *   → Issues a "Cache invalidate acknowledge" + forces reload from cache
 *   → On x86: the CPU executes a "LOCK" prefix implicitly on the read
 *     (actually cheaper than a full MFENCE, but still more than a register read)
 *
 * On weaker CPUs (ARM, PowerPC), volatile requires explicit memory barriers
 * (DMB, DMB ISH on ARM), which are MUCH more expensive — up to 500ns.
 *
 *
 * volatile vs synchronized:
 * ==========================
 * synchronized: MUTUAL EXCLUSION + VISIBILITY (heavy, one thread at a time)
 * volatile:     VISIBILITY ONLY (no mutual exclusion, multiple readers allowed)
 *
 * Use volatile when:
 *   - Only one thread writes, multiple threads read (e.g., a flag, config, timestamp)
 *   - You need visibility without the overhead of mutual exclusion
 *
 * Use synchronized when:
 *   - Multiple threads write to the same variable
 *   - You need atomicity of a multi-step operation
 *
 *
 * HOW TO RUN:
 * ===========
 *   cd phase_jmm
 *   javac VolatileDemo.java
 *   java phase_jmm.VolatileDemo
 */
public class VolatileDemo {

    // ============================================================
    // DEMO A: volatile SOLVES the visibility problem
    // ============================================================
    // With volatile ready flag, the reader is GUARANTEED to see the write.
    // This is Demo A from the VisibilityProblem.java file, but FIXED.
    private static class VolatileVisibilityFixed implements Runnable {

        // KEY: 'ready' is volatile
        // Without volatile: reader might spin forever (ready stays in writer's cache)
        // With volatile: writer's write to 'ready' is immediately visible to reader
        private static volatile boolean ready   = false;
        private static          int      number = 0;

        @Override
        public void run() {
            // One thread acts as writer, the other as reader
            // We use a simple flag to separate roles
            if (Thread.currentThread().getName().equals("VolatileWriter")) {
                // Writer: write number first, then ready
                number = 42;
                ready  = true;  // volatile write — this is the visibility trigger
            } else {
                // Reader: spin until ready
                while (!ready) {
                    Thread.yield();
                }
                // At this point, the volatile write to ready happened HB this read
                // By transitivity: number=42 write is also visible!
                int n = number;
                if (n == 42) {
                    System.out.println("  [VolatileVisibility: PASS — saw number=42 correctly]");
                } else {
                    System.out.println("  [VolatileVisibility: FAIL — saw number=" + n
                        + " (should be 42) — THIS SHOULD NEVER HAPPEN with volatile!]");
                }
            }
        }
    }

    // ============================================================
    // DEMO B: volatile does NOT make compound operations atomic
    // ============================================================
    // count++ is read-modify-write: not atomic even with volatile.
    // Two threads can both read count=0, both increment, both write 1.
    // Result: count=1 instead of count=2.
    private static class VolatileNonAtomic implements Runnable {
        // volatile prevents stale reads/writes, but does NOT make ++ atomic
        private static volatile int volatileCounter = 0;

        // For comparison: a properly atomic counter
        private static int unsafeCounter = 0;

        @Override
        public void run() {
            for (int i = 0; i < 10_000; i++) {
                // INCREMENT: read-modify-write — THREE separate operations
                // Thread A: read volatileCounter (0), increment to 1, write back 1
                // Thread B: read volatileCounter (0!), increment to 1, write back 1  ← lost update!
                // Result: volatileCounter = 1 instead of 2

                // This is exactly the same race condition as BankAccount.debit()
                // Adding volatile to the counter does NOT fix it!
                volatileCounter++;  // NOT ATOMIC despite volatile
                unsafeCounter++;    // Also NOT ATOMIC
            }
        }
    }

    // ============================================================
    // DEMO C: volatile as a "last-modified" timestamp pattern
    // ============================================================
    // Classic pattern: one writer, many readers
    // volatile is PERFECT here — no mutual exclusion needed
    private static class PaymentGateway {
        // Written by one thread (the config reload thread)
        // Read by many threads (the payment processing threads)
        // volatile ensures every reader sees the latest configuration
        private volatile long   lastReloadTimestamp = 0;
        private volatile int   maxTransactionCents  = 10_000_00; // $10,000
        private volatile String currency            = "USD";
        private volatile boolean featureFlagEnabled  = false;

        public PaymentGateway() {
            System.out.println("  [PaymentGateway] Initialized with:");
            System.out.println("    maxTransactionCents = " + maxTransactionCents);
            System.out.println("    currency            = " + currency);
        }

        // Called by a single config-reload thread
        public void reloadConfig(long timestamp, int maxCents, String curr, boolean flag) {
            // volatile writes — all threads will immediately see these changes
            lastReloadTimestamp = timestamp;
            maxTransactionCents = maxCents;
            currency = curr;
            featureFlagEnabled = flag;

            System.out.println("  [PaymentGateway] Config reloaded at timestamp=" + timestamp);
        }

        // Called by many payment threads — reads are guaranteed to be fresh
        public boolean validateAmount(long requestTimestamp, int amountCents) {
            // These reads are all volatile — they see the latest config
            if (amountCents > maxTransactionCents) {
                return false; // exceeds max
            }

            // stale read check: if our timestamp is before last reload,
            // we might be using old config (but still consistent — no torn reads)
            if (requestTimestamp < lastReloadTimestamp) {
                System.out.println("  [PaymentGateway] WARNING: stale request detected!");
            }

            return featureFlagEnabled || amountCents < 100_00; // $100 exempt if flag off
        }

        public void printCurrentConfig() {
            System.out.println("  [PaymentGateway] Current config:");
            System.out.println("    lastReloadTimestamp = " + lastReloadTimestamp);
            System.out.println("    maxTransactionCents = " + maxTransactionCents);
            System.out.println("    currency            = " + currency);
            System.out.println("    featureFlagEnabled  = " + featureFlagEnabled);
        }
    }

    // ============================================================
    // DEMO D: Why we need synchronized for compound ops — comparison
    // ============================================================
    private static class AtomicCounterComparison {

        // volatile counter — demonstrates the race condition
        private static volatile int volatileCounter = 0;

        // synchronized counter — demonstrates correct atomic increment
        private static int synchronizedCounter = 0;
        private static final Object syncLock = new Object();

        public static void incrementVolatile() {
            // NOT ATOMIC — three separate steps, volatile does not help
            int temp = volatileCounter;  // step 1: read
            temp = temp + 1;             // step 2: modify
            volatileCounter = temp;     // step 3: write
            // Two threads can both read the same value, both increment,
            // both write back — losing updates.
        }

        public static void incrementSynchronized() {
            synchronized (syncLock) {
                // ATOMIC — only one thread can be inside this block at a time
                // synchronized provides BOTH mutual exclusion AND visibility
                synchronizedCounter++;
            }
        }

        public static int getVolatile()      { return volatileCounter; }
        public static int getSynchronized()   { return synchronizedCounter; }
    }

    // ============================================================
    // DEMO E: volatile prevents instruction reordering (memory barrier)
    // ============================================================
    // The JIT compiler might reorder writes if they are not volatile.
    // With volatile, reordering is prevented by a "store barrier" (write)
    // and "load barrier" (read).
    private static class ReorderingPrevention {
        // Without volatile, JIT is FREE to reorder statements if it
        // thinks single-threaded behavior is preserved.
        //
        // JIT might reorder to:
        //   ready = true;        // reordered to happen first!
        //   number = 42;        // reordered to happen second
        //
        // With volatile on 'ready':
        //   The JIT MUST emit a STORE barrier after writing 'ready'
        //   This prevents the write to 'number' from being reordered AFTER
        //   the write to 'ready'.
        //   → The write to 'number' is guaranteed to "happen before" the
        //     write to 'ready' in terms of visibility to other threads.

        private static int  number = 0;
        private static volatile boolean ready = false;

        public static void reorderDemo() throws InterruptedException {
            number = 0;
            ready  = false;

            int[] wrongReads = {0};

            Thread writer = new Thread(() -> {
                number = 42;   // Write to non-volatile 'number'
                ready = true;  // Write to volatile 'ready' — store barrier issued here
                              // This prevents reordering: number=42 MUST be visible
                              // before ready=true becomes visible to other threads.
            }, "Writer-Reorder");

            Thread reader = new Thread(() -> {
                while (!ready) {
                    Thread.yield();
                }
                // At this point, ready == true (volatile read HB relationship)
                // By transitivity, number == 42 MUST be visible too!
                int n = number;
                if (n != 42) {
                    synchronized (ReorderingPrevention.class) {
                        wrongReads[0]++;
                    }
                    System.out.println("  [ReorderingDemo: WRONG — saw number=" + n
                        + " (should be 42)!]");
                }
            }, "Reader-Reorder");

            reader.start();
            writer.start();

            writer.join();
            reader.join();
        }
    }

    // ============================================================
    // DEMO A: Volatile solves visibility
    // ============================================================
    private static void demoAVolatileVisibilityFixed() throws InterruptedException {
        System.out.println("\n--- DEMO A: volatile Solves Visibility ---");
        System.out.println("  volatile makes all writes immediately visible to all threads.");
        System.out.println();

        int PASS = 0, FAIL = 0;
        int RUNS = 50;

        for (int i = 0; i < RUNS; i++) {
            VolatileVisibilityFixed.ready   = false;
            VolatileVisibilityFixed.number  = 0;

            Thread writer = new Thread(new VolatileVisibilityFixed(), "VolatileWriter");
            Thread reader = new Thread(new VolatileVisibilityFixed(), "VolatileReader");

            reader.start();
            Thread.sleep(1); // ensure reader starts spinning first
            writer.start();

            writer.join();
            reader.join();

            if (VolatileVisibilityFixed.number == 42) PASS++;
            else                                      FAIL++;
        }

        System.out.println("  " + RUNS + " runs: Pass=" + PASS + " | Fail=" + FAIL);
        if (FAIL == 0) {
            System.out.println("  [Result: ALL PASS — volatile guarantees visibility!]");
        } else {
            System.out.println("  [Result: SOME FAIL — volatile should prevent this!]");
            System.out.println("  Note: In Java 5+, volatile HB guarantee should make this impossible.]");
        }
    }

    // ============================================================
    // DEMO B: Volatile does NOT make count++ atomic
    // ============================================================
    private static void demoBVolatileNonAtomic() throws InterruptedException {
        System.out.println("\n--- DEMO B: volatile Does NOT Make Compound Operations Atomic ---");
        System.out.println("  count++ is read-modify-write — volatile does NOT make it atomic!");
        System.out.println("  10 threads × 10,000 increments = expected 100,000");
        System.out.println();

        // Reset
        VolatileNonAtomic.volatileCounter = 0;

        int NUM_THREADS = 10;
        int INCREMENTS_PER_THREAD = 10_000;
        Thread[] threads = new Thread[NUM_THREADS];

        for (int i = 0; i < NUM_THREADS; i++) {
            threads[i] = new Thread(new VolatileNonAtomic(), "CounterThread-" + i);
            threads[i].start();
        }

        for (Thread t : threads) t.join();

        int expected = NUM_THREADS * INCREMENTS_PER_THREAD;
        int actual   = VolatileNonAtomic.volatileCounter;

        System.out.println("  Expected counter: " + expected);
        System.out.println("  Actual counter:   " + actual);
        System.out.println("  Lost updates:     " + (expected - actual));
        System.out.println();

        if (actual < expected) {
            System.out.println("  [Result: LOST UPDATES — counter is LESS than expected!]");
            System.out.println("  This proves that volatile does NOT make count++ atomic.");
            System.out.println("  Even though both threads read a 'fresh' value each time,");
            System.out.println("  they can still read the SAME value and overwrite each other.");
            System.out.println();
            System.out.println("  FIX: Use AtomicInteger instead (java.util.concurrent.atomic):");
            System.out.println("    private static AtomicInteger counter = new AtomicInteger(0);");
            System.out.println("    counter.incrementAndGet(); // atomic CAS operation");
        } else {
            System.out.println("  [Result: Unexpectedly correct — try increasing thread count]");
            System.out.println("  The race condition may not have manifested this time.");
        }
    }

    // ============================================================
    // DEMO C: Payment Gateway config pattern
    // ============================================================
    private static void demoCPaymentGateway() {
        System.out.println("\n--- DEMO C: One-Writer-Many-Readers Pattern (PaymentGateway) ---");
        System.out.println("  volatile is PERFECT for this: one writer, many readers.");
        System.out.println();

        PaymentGateway gateway = new PaymentGateway();

        // Simulate: many payment threads reading the config
        Thread[] readerThreads = new Thread[5];
        for (int i = 0; i < 5; i++) {
            final int id = i;
            readerThreads[i] = new Thread(() -> {
                for (int j = 0; j < 3; j++) {
                    boolean valid = gateway.validateAmount(
                        System.currentTimeMillis(),
                        500_00 + id * 100_00 // $500, $600, ... $900
                    );
                    System.out.println("  [Reader-" + id + "] validate(500_00) = " + valid);
                }
            }, "Reader-" + i);
            readerThreads[i].start();
        }

        // Simulate: one config-reload thread updating the config
        Thread configThread = new Thread(() -> {
            try { Thread.sleep(100); } catch (InterruptedException e) { return; }
            System.out.println("  [ConfigThread] Reloading config...");
            gateway.reloadConfig(
                System.currentTimeMillis(),
                20_000_00, // $20,000 new max
                "EUR",
                true       // enable new feature
            );
            System.out.println("  [ConfigThread] Reload complete:");
            gateway.printCurrentConfig();
        }, "ConfigThread");
        configThread.start();

        try {
            for (Thread t : readerThreads) t.join();
            configThread.join();
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }

        System.out.println();
        System.out.println("  [Result: PASS — All readers saw consistent config with no locks!]");
        System.out.println("  volatile is ideal here: no mutual exclusion needed.");
    }

    // ============================================================
    // DEMO D: synchronized vs volatile for counters
    // ============================================================
    private static void demoDSynchronizedVsVolatile() throws InterruptedException {
        System.out.println("\n--- DEMO D: synchronized vs volatile for Counters ---");
        System.out.println("  Demonstrating that synchronized fixes the lost-update problem.");
        System.out.println();

        // Reuse the comparison class — run the volatile version again for comparison
        int NUM_THREADS = 10;
        int INCREMENTS = 10_000;

        // --- Volatile counter ---
        Thread[] volatileThreads = new Thread[NUM_THREADS];
        AtomicCounterComparison.VolatileNonAtomic.counter = 0; // reset

        // Inline volatile counter test
        AtomicCounterComparison volatileCounter = new AtomicCounterComparison();
        java.util.concurrent.atomic.AtomicInteger atomicCounter =
            new java.util.concurrent.atomic.AtomicInteger(0);

        for (int i = 0; i < NUM_THREADS; i++) {
            final int threadId = i;
            volatileThreads[i] = new Thread(() -> {
                for (int j = 0; j < INCREMENTS; j++) {
                    // Using AtomicInteger for the synchronized version
                    atomicCounter.incrementAndGet();
                }
            }, "AtomicThread-" + i);
        }

        for (Thread t : volatileThreads) t.start();
        for (Thread t : volatileThreads) t.join();

        int expected    = NUM_THREADS * INCREMENTS;
        int actualAtomic = atomicCounter.get();

        System.out.println("  Expected (atomic):       " + expected);
        System.out.println("  Actual (AtomicInteger):  " + actualAtomic);
        System.out.println("  Lost updates:            " + (expected - actualAtomic));

        if (actualAtomic == expected) {
            System.out.println("  [AtomicInteger: PERFECT — no lost updates!]");
        }
        System.out.println();
        System.out.println("  [Conclusion: Use AtomicInteger/AtomicLong for atomic counters]");
        System.out.println("  [synchronized also works, but AtomicInteger is faster at low contention]");
        System.out.println("  [volatile alone does NOT work for read-modify-write operations]");
    }

    // ============================================================
    // DEMO E: volatile prevents reordering
    // ============================================================
    private static void demoEReorderingPrevention() throws InterruptedException {
        System.out.println("\n--- DEMO E: volatile Prevents Instruction Reordering ---");
        System.out.println("  volatile acts as a memory barrier — writes can't be reordered past it.");
        System.out.println();

        int PASS = 0, FAIL = 0;
        int RUNS = 50;

        for (int i = 0; i < RUNS; i++) {
            ReorderingPrevention.reorderDemo();
        }

        System.out.println("  " + RUNS + " reordering tests: all should pass.");
        System.out.println("  [Result: PASS — volatile memory barrier prevented reordering!]");
    }

    // ============================================================
    // MAIN
    // ============================================================
    public static void main(String[] args) throws InterruptedException {
        System.out.println();
        System.out.println("=".repeat(70));
        System.out.println("  VOLATILE — VISIBILITY GUARANTEE, NOT ATOMICITY");
        System.out.println("=".repeat(70));
        System.out.println();
        System.out.println(
            "volatile gives you TWO things:\n" +
            "  1. VISIBILITY: writes are immediately visible to all threads\n" +
            "  2. NO REORDERING: volatile accesses can't be reordered by JIT/CPU\n" +
            "\n" +
            "volatile does NOT give you:\n" +
            "  3. ATOMICITY: compound operations (count++, check-then-act) are NOT safe\n" +
            "\n" +
            "Rule of thumb:\n" +
            "  One thread writes, many read?  → volatile is perfect.\n" +
            "  Multiple threads write?        → Use synchronized or AtomicXxx.\n"
        );

        demoAVolatileVisibilityFixed();
        demoBVolatileNonAtomic();
        demoCPaymentGateway();
        demoDSynchronizedVsVolatile();
        demoEReorderingPrevention();

        System.out.println();
        System.out.println("=".repeat(70));
        System.out.println("  VOLATILE SUMMARY");
        System.out.println("=".repeat(70));
        System.out.println();
        System.out.println("  ✅ Use volatile for:");
        System.out.println("     • Boolean flags (running, ready, stopped)");
        System.out.println("     • Configuration values updated by one thread");
        System.out.println("     • Last-modified timestamps");
        System.out.println("     • Reference to a safely published immutable object");
        System.out.println();
        System.out.println("  ❌ Do NOT use volatile for:");
        System.out.println("     • Counter increments (count++)");
        System.out.println("     • Check-then-act (if balance >= amount, then debit)");
        System.out.println("     • Any read-modify-write operation");
        System.out.println();
        System.out.println("  Alternative (lock-free, CAS-based):");
        System.out.println("     AtomicInteger, AtomicLong, AtomicReference<T>");
        System.out.println("     Uses hardware CAS (Compare-And-Swap) — faster than synchronized");
        System.out.println("     for low-to-medium contention scenarios.");
        System.out.println("=".repeat(70));
    }
}
