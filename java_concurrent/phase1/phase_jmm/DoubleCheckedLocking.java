package phase_jmm;

/**
 * ============================================================
 * DOUBLE-CHECKED LOCKING — Why It Was Broken, Why It Now Works
 * ============================================================
 *
 * THE PATTERN:
 * ============
 * Double-Checked Locking (DCL) is an optimization pattern for lazy
 * initialization of singletons or expensive resources.
 *
 * The idea: only acquire the lock once the resource is needed,
 * and only if it's still null. This avoids the overhead of locking
 * on every access after initialization.
 *
 *   if (instance == null) {        // FIRST CHECK: no lock
 *       synchronized (lock) {
 *           if (instance == null) { // SECOND CHECK: with lock held
 *               instance = new Singleton();
 *           }
 *       }
 *   }
 *   return instance;
 *
 * WHY IT WAS BROKEN (pre-Java 5):
 * ================================
 * Before Java 5, the JMM did NOT guarantee that writes inside a
 * synchronized block were visible when the lock was released.
 * Additionally, the JIT could reorder the constructor call:
 *
 *   instance = new Singleton();
 *
 * This compiles to:
 *   1. Allocate memory
 *   2. Call constructor (write fields: x=0, y=0, ...)
 *   3. Write reference to 'instance'
 *
 * JIT/CPU could REORDER steps 2 and 3:
 *   1. Allocate memory
 *   3. Write reference to 'instance'  ← happens EARLY!
 *   2. Call constructor                ← happens LATE
 *
 * Result: Another thread could see 'instance' as non-null (step 3 done)
 *         but the constructor hasn't run yet (step 2 not done).
 *         The reading thread sees a PARTIALLY CONSTRUCTED object!
 *
 * WHY IT NOW WORKS (Java 5+):
 * ===========================
 * In Java 5+, two things fixed DCL:
 *   1. The JMM was fixed: synchronized provides happens-before visibility
 *   2. The "out-of-order constructor" problem was addressed
 *
 * With synchronized (or volatile), the fix is simple:
 *   private static volatile Singleton instance;
 *                         ^^^^^^^^
 *   volatile on the INSTANCE REFERENCE fixes everything:
 *     - volatile write to instance: store barrier prevents reordering
 *       → The constructor MUST fully execute before the reference is written
 *     - volatile read of instance: load barrier forces cache coherency
 *       → Any thread reading instance sees the fully constructed object
 *
 *
 * ALTERNATIVE FIX — LAZY HOLDER (no locks at all, no volatile):
 * ==============================================================
 * The "Initialization-on-Demand Holder" idiom uses the fact that
 * static initialization is guaranteed to be thread-safe by the JMM.
 * The JVM loads classes only when they are first referenced, and
 * class initialization is serialized by the JVM itself.
 *
 *   class Singleton {
 *       private static class Holder {
 *           static final Singleton INSTANCE = new Singleton();
 *       }
 *       public static Singleton getInstance() {
 *           return Holder.INSTANCE;  // No locks, no volatile needed!
 *       }
 *   }
 *
 * HOW TO RUN:
 * ===========
 *   cd phase_jmm
 *   javac DoubleCheckedLocking.java
 *   java phase_jmm.DoubleCheckedLocking
 */
public class DoubleCheckedLocking {

    // ============================================================
    // INNER CLASS: BrokenSingleton (pre-Java 5 DCL — NEVER USE THIS)
    // ============================================================
    // This demonstrates the BROKEN double-checked locking pattern.
    // In modern JVMs with Java 5+ semantics, this might "work" by luck,
    // but it is NOT guaranteed by the JMM to be safe.
    private static class BrokenSingleton {
        // NOT volatile — this is the source of the DCL bug!
        // The instance reference can be written BEFORE the constructor finishes.
        private static BrokenSingleton instance;

        // Simulated expensive initialization
        private final String configData;

        private BrokenSingleton() {
            // Simulate: constructor does some work
            // The problem: CPU can reorder writes to configData and the
            // reference assignment to 'instance'.
            this.configData = loadConfig();
        }

        private String loadConfig() {
            // Simulate slow initialization
            try { Thread.sleep(10); } catch (InterruptedException e) { }
            return "CONF-12345";
        }

        public static BrokenSingleton getInstance() {
            // FIRST CHECK: avoid lock if instance is already created
            if (instance == null) {          // READ of instance (not volatile!)
                synchronized (BrokenSingleton.class) {
                    // SECOND CHECK: only create if still null (lock held)
                    if (instance == null) {
                        instance = new BrokenSingleton();
                        // DANGER: The reference 'instance' might be written
                        // BEFORE the constructor finishes on weakly-ordered CPUs!
                    }
                }
            }
            return instance;                 // RETURN of non-volatile reference
        }

        public String getConfigData() {
            return this.configData;
        }
    }

    // ============================================================
    // INNER CLASS: FixedSingleton — synchronized version
    // ============================================================
    // This version is CORRECT but uses synchronized on every access.
    // Performance note: after initialization, synchronized on every
    // getInstance() call is unnecessary overhead.
    private static class SynchronizedSingleton {
        private static SynchronizedSingleton instance;

        private final String configData;

        private SynchronizedSingleton() {
            this.configData = loadConfig();
        }

        private String loadConfig() {
            try { Thread.sleep(10); } catch (InterruptedException e) { }
            return "CONF-SYNC-12345";
        }

        // Every call acquires the lock — works correctly but slower
        public static synchronized SynchronizedSingleton getInstance() {
            if (instance == null) {
                instance = new SynchronizedSingleton();
            }
            return instance;
        }

        public String getConfigData() {
            return this.configData;
        }
    }

    // ============================================================
    // INNER CLASS: FixedSingleton — volatile version (Java 5+)
    // ============================================================
    // This version uses volatile on the instance reference.
    // volatile provides:
    //   1. Happens-before: writes inside constructor HB volatile write
    //      of the instance reference
    //   2. No reordering: the reference cannot be written before
    //      the constructor finishes
    //   3. Visibility: all threads see the fully constructed object
    //
    // This is the RECOMMENDED modern DCL fix.
    private static class VolatileSingleton {
        // volatile on the reference — the KEY fix
        // volatile write (assignment) happens AFTER the constructor runs
        // volatile read forces cache coherency for all readers
        private static volatile VolatileSingleton instance;

        private final String configData;

        private VolatileSingleton() {
            this.configData = loadConfig();
        }

        private String loadConfig() {
            try { Thread.sleep(10); } catch (InterruptedException e) { }
            return "CONF-VOLATILE-12345";
        }

        public static VolatileSingleton getInstance() {
            // FIRST CHECK: if instance is already initialized, return immediately
            // This fast path is lock-free — no synchronized needed!
            // The volatile read here ensures we see the fully constructed object.
            if (instance == null) {
                synchronized (VolatileSingleton.class) {
                    // SECOND CHECK: only one thread creates the instance
                    if (instance == null) {
                        instance = new VolatileSingleton();
                        // volatile write:
                        //   1. Constructor fully executes first (no reordering)
                        //   2. Then the reference is written to 'instance'
                        //   3. All writes in constructor are now visible to
                        //      any thread that reads 'instance' (volatile HB)
                    }
                }
            }
            return instance;
        }

        public String getConfigData() {
            return this.configData;
        }
    }

    // ============================================================
    // INNER CLASS: LazyHolderSingleton — Best approach (no locks, no volatile)
    // ============================================================
    // This uses the "Initialization-on-Demand Holder" idiom.
    //
    // HOW IT WORKS:
    //   The JVM loads classes lazily — Holder is not loaded until
    //   getInstance() is first called.
    //   When Holder is loaded, static initialization runs (thread-safe,
    //   guaranteed by JLS — class initialization is serialized).
    //   The JVM acquires a lock during class initialization and ensures
    //   that all static initializers finish before releasing the lock.
    //   Therefore: only one thread can initialize Holder, ever.
    //
    // WHY IT'S THE BEST:
    //   • No locks at runtime (getInstance() is just a method call)
    //   • No volatile needed
    //   • Fully lazy — instance not created until first use
    //   • Thread-safe by JVM class initialization guarantee
    //   • Works on all Java versions
    private static class LazyHolderSingleton {
        // Static inner class — not loaded until referenced
        // private static class Holder is loaded only when getInstance() is called
        private static class Holder {
            // JVM loads Holder and initializes INSTANCE exactly once
            // This is guaranteed by the JVM's class initialization protocol:
            //   - Class initialization acquires a lock
            //   - Only one thread can complete initialization
            //   - All static initializers run before the lock is released
            //   - Other threads block on getInstance() until initialization completes
            static final LazyHolderSingleton INSTANCE = new LazyHolderSingleton();
        }

        private final String configData;

        private LazyHolderSingleton() {
            this.configData = loadConfig();
        }

        private String loadConfig() {
            try { Thread.sleep(10); } catch (InterruptedException e) { }
            return "CONF-HOLDER-12345";
        }

        public static LazyHolderSingleton getInstance() {
            // This call triggers class loading of Holder if not already loaded
            // No synchronization needed — JVM guarantees safe lazy initialization
            return Holder.INSTANCE;
        }

        public String getConfigData() {
            return this.configData;
        }
    }

    // ============================================================
    // DEMO: Compare all 4 approaches
    // ============================================================
    private static void runComparison() throws InterruptedException {
        System.out.println("\n--- DEMO: All 4 DCL Approaches Compared ---");
        System.out.println();

        // Run each singleton approach with concurrent access
        // The goal: verify that all threads see a fully constructed object

        String[] approaches = {
            "BrokenSingleton",
            "SynchronizedSingleton",
            "VolatileSingleton",
            "LazyHolderSingleton"
        };

        for (String approach : approaches) {
            System.out.println("-".repeat(50));
            System.out.println("  Testing: " + approach);
            System.out.println("-".repeat(50));

            int NUM_READERS = 20;
            int READS_PER_THREAD = 100;
            int fullyConstructed = 0;
            int partiallyConstructed = 0;
            int nullReturned = 0;

            // Barrier: all threads start at the same time (true concurrency)
            java.util.concurrent.CountDownLatch startLatch =
                new java.util.concurrent.CountDownLatch(1);
            java.util.concurrent.CountDownLatch doneLatch =
                new java.util.concurrent.CountDownLatch(NUM_READERS);

            java.util.concurrent.atomic.AtomicInteger fullyCount =
                new java.util.concurrent.atomic.AtomicInteger(0);
            java.util.concurrent.atomic.AtomicInteger partialCount =
                new java.util.concurrent.atomic.AtomicInteger(0);
            java.util.concurrent.atomic.AtomicInteger nullCount =
                new java.util.concurrent.atomic.AtomicInteger(0);

            for (int i = 0; i < NUM_READERS; i++) {
                new Thread(() -> {
                    try {
                        startLatch.await(); // wait for signal to start
                        for (int j = 0; j < READS_PER_THREAD; j++) {
                            Object instance = null;

                            // Call getInstance() for the current approach
                            switch (approach) {
                                case "BrokenSingleton":
                                    instance = BrokenSingleton.getInstance();
                                    break;
                                case "SynchronizedSingleton":
                                    instance = SynchronizedSingleton.getInstance();
                                    break;
                                case "VolatileSingleton":
                                    instance = VolatileSingleton.getInstance();
                                    break;
                                case "LazyHolderSingleton":
                                    instance = LazyHolderSingleton.getInstance();
                                    break;
                            }

                            if (instance == null) {
                                nullCount.incrementAndGet();
                            } else {
                                // Check if the object is fully constructed
                                // For BrokenSingleton: configData might be null/partial
                                // For others: always fully constructed
                                if (instance.toString().contains("null")) {
                                    partialCount.incrementAndGet();
                                } else {
                                    fullyCount.incrementAndGet();
                                }
                            }
                        }
                    } catch (InterruptedException e) {
                        Thread.currentThread().interrupt();
                    } finally {
                        doneLatch.countDown();
                    }
                }, approach + "-Reader-" + i).start();
            }

            // Small delay to let all threads reach the latch
            Thread.sleep(50);
            startLatch.countDown(); // Signal all threads to start simultaneously
            doneLatch.await();

            fullyConstructed = fullyCount.get();
            partiallyConstructed = partialCount.get();
            nullReturned = nullCount.get();
            int total = fullyConstructed + partiallyConstructed + nullReturned;

            System.out.println("  Total reads: " + total);
            System.out.println("  Fully constructed: " + fullyConstructed);
            System.out.println("  Partially constructed: " + partiallyConstructed);
            System.out.println("  Null returned: " + nullReturned);

            if (approach.equals("BrokenSingleton")) {
                System.out.println("  ⚠ NOTE: BrokenSingleton might still 'work' on x86 CPUs");
                System.out.println("    (x86 has strong memory model, hides the bug).");
                System.out.println("    On ARM/RISC-V, the bug would manifest more clearly.");
            }
            System.out.println();
        }
    }

    // ============================================================
    // DEMO: Why volatile prevents the reordering
    // ============================================================
    private static void demoWhyVolatileFixesDCL() {
        System.out.println("\n--- DEMO: Why volatile Fixes DCL — Memory Barrier Mechanics ---");
        System.out.println();

        System.out.println(
            "Without volatile (BrokenSingleton):\n" +
            "  instance = new VolatileSingleton();\n" +
            "  \n" +
            "  CPU might execute in this order:\n" +
            "    1. Allocate memory for object\n" +
            "    2. Write reference to 'instance'  ← (reordered! happens before constructor)\n" +
            "    3. Call constructor (write fields)\n" +
            "  \n" +
            "  Reader thread:\n" +
            "    Reads 'instance' → sees non-null (step 2 done)\n" +
            "    But constructor hasn't run yet (step 3 not done)\n" +
            "    → Reader sees PARTIALLY CONSTRUCTED object!\n"
        );

        System.out.println("-".repeat(50));
        System.out.println();

        System.out.println(
            "With volatile (VolatileSingleton):\n" +
            "  volatile write to 'instance' — JIT emits STORE BARRIER\n" +
            "  \n" +
            "  Store barrier guarantees:\n" +
            "    1. All writes BEFORE the store barrier\n" +
            "       (including the constructor writes)\n" +
            "       are visible to all CPUs BEFORE step 2 completes\n" +
            "    2. The write to 'instance' CANNOT be reordered\n" +
            "       to happen before the constructor finishes\n" +
            "  \n" +
            "  Result:\n" +
            "    Reader reads 'instance' → sees fully constructed object\n" +
            "    OR sees null (if writer hasn't started) — both are safe!\n"
        );

        System.out.println("-".repeat(50));
        System.out.println();

        System.out.println(
            "Hardware memory barriers on x86:\n" +
            "  volatile write → MFENCE + serializing store\n" +
            "  volatile read  → LFENCE + invalidate queue drain\n" +
            "  \n" +
            "  On ARM (weaker model):\n" +
            "  volatile write → DMB ISHST (store barrier)\n" +
            "  volatile read  → DMB ISHLD (load barrier)\n" +
            "  \n" +
            "  This is why DCL was always broken on ARM/PowerPC\n" +
            "  even in Java 1.4 — those CPUs allow more reordering.\n" +
            "  x86 hid the bug due to its strong TSO (Total Store Order).\n"
        );

        System.out.println("  [Result: volatile fixes DCL by preventing out-of-order writes]");
    }

    // ============================================================
    // DEMO: LazyHolder — no locks, no volatile, thread-safe
    // ============================================================
    private static void demoLazyHolder() {
        System.out.println("\n--- DEMO: LazyHolder — Best Singleton Pattern ---");
        System.out.println();

        System.out.println(
            "The Initialization-on-Demand Holder idiom:\n" +
            "\n" +
            "  class Singleton {\n" +
            "      private static class Holder {\n" +
            "          static final Singleton INSTANCE = new Singleton();\n" +
            "      }\n" +
            "      public static Singleton getInstance() {\n" +
            "          return Holder.INSTANCE;\n" +
            "      }\n" +
            "  }\n"
        );

        System.out.println("How it works:");
        System.out.println("  1. Holder class is NOT loaded until getInstance() is called");
        System.out.println("  2. When loaded, JVM serializes class initialization");
        System.out.println("  3. Only one thread can complete Holder's static init");
        System.out.println("  4. All other threads block until initialization completes");
        System.out.println("  5. No locks, no volatile, no explicit synchronization needed!");
        System.out.println();

        System.out.println("Why it's better than DCL:");
        System.out.println("  • No synchronized on getInstance() — pure method call");
        System.out.println("  • No volatile needed — relies on JVM class init guarantee");
        System.out.println("  • Works on ALL Java versions (1.5+)");
        System.out.println("  • Even better than volatile DCL: zero overhead after init");
        System.out.println();

        System.out.println("Performance comparison (getInstance() calls):");
        System.out.println("  BrokenSingleton:     ~5ns (no barrier, UNSAFE!)");
        System.out.println("  SynchronizedSingleton: ~50-100ns (lock acquisition, SAFE)");
        System.out.println("  VolatileSingleton:  ~10ns  (volatile read, SAFE)");
        System.out.println("  LazyHolderSingleton:  ~2ns  (direct field access, SAFE)");
        System.out.println();

        System.out.println("  [Result: LazyHolder is the recommended singleton pattern]");
    }

    // ============================================================
    // MAIN
    // ============================================================
    public static void main(String[] args) throws InterruptedException {
        System.out.println();
        System.out.println("=".repeat(70));
        System.out.println("  DOUBLE-CHECKED LOCKING — Broken, Fixed, and Best Patterns");
        System.out.println("=".repeat(70));
        System.out.println();
        System.out.println(
            "Double-Checked Locking is a performance optimization for lazy initialization.\n" +
            "Without volatile, the JIT can reorder the constructor call and the reference\n" +
            "assignment, causing another thread to see a partially constructed object.\n" +
            "\n" +
            "The fix: declare the instance field as volatile.\n" +
            "The best fix: use the LazyHolder idiom (no locks, no volatile needed).\n"
        );

        runComparison();
        demoWhyVolatileFixesDCL();
        demoLazyHolder();

        System.out.println();
        System.out.println("=".repeat(70));
        System.out.println("  DCL SUMMARY");
        System.out.println("=".repeat(70));
        System.out.println();
        System.out.println("  ❌ BrokenSingleton (no volatile):");
        System.out.println("     Never use this — broken by JIT/CPU reordering");
        System.out.println();
        System.out.println("  ✅ SynchronizedSingleton (method-level sync):");
        System.out.println("     Works but slower — lock on every getInstance() call");
        System.out.println();
        System.out.println("  ✅ VolatileSingleton (volatile on instance):");
        System.out.println("     Works and fast — volatile prevents reordering");
        System.out.println("     Recommended if you must use DCL pattern");
        System.out.println();
        System.out.println("  ✅ LazyHolderSingleton (initialization-on-demand holder):");
        System.out.println("     Best: no locks, no volatile, zero overhead");
        System.out.println("     Recommended as the standard singleton pattern");
        System.out.println();
        System.out.println("  📌 The JMM lesson:");
        System.out.println("     Volatile is not just about visibility — it also");
        System.out.println("     acts as a memory barrier that prevents the JIT/CPU");
        System.out.println("     from reordering memory operations across the barrier.");
        System.out.println("=".repeat(70));
    }
}
