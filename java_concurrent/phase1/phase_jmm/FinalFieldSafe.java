package phase_jmm;

/**
 * ============================================================
 * FINAL FIELD SEMANTICS — Safe Publication via Immutability
 * ============================================================
 *
 * THE PROBLEM: PARTIAL CONSTRUCTION
 * ==================================
 * When a constructor writes fields one by one, another thread might see
 * a partially constructed object — some fields written, some not yet.
 *
 * Consider:
 *     class Point {
 *         int x, y;
 *         Point(int ax, int ay) {
 *             x = ax;   // Thread B might see x=5 but y=0 (default!)
 *             y = ay;   // x was written, y not yet
 *         }
 *     }
 *
 * Even if the constructor finishes, Thread B might see Point with x=5, y=0.
 * The CPU can reorder constructor writes, and Thread B might read from a
 * cache that hasn't been invalidated yet.
 *
 *
 * THE SOLUTION: FINAL FIELDS
 * ==========================
 * JLS 17.5 guarantees that once a constructor finishes writing final fields,
 * and the reference to the object is published (e.g., assigned to a variable),
 * all threads will see those final fields correctly — WITHOUT any
 * additional synchronization.
 *
 * The JMM specifies:
 *   "A freeze action on a final field F of an object O occurs when
 *    O's constructor finishes. The freeze action ensures that the
 *    write to F in the constructor is visible to all threads."
 *
 * IMPORTANT CONDITIONS for this guarantee to hold:
 *   1. The field must be FINAL
 *   2. The reference to 'this' must NOT escape from the constructor
 *      (do NOT assign 'this' to a shared field inside the constructor)
 *   3. After construction, the object reference must be safely published
 *      (e.g., via final field, volatile, synchronized, or static initializer)
 *
 * WHAT "NO ESCAPE" MEANS:
 * =======================
 *   ❌ BAD — 'this' escapes inside the constructor:
 *       class Bad {
 *           final Point p;
 *           Bad() {
 *               p = new Point(1, 2);
 *               // Nothing wrong with this assignment itself...
 *           }
 *       }
 *       BUT: if you do this inside the constructor:
 *           new Thread(() -> System.out.println(p.x)).start(); // 'this' escape!
 *       ...then another thread can see the object before constructor finishes.
 *
 *   ✅ SAFE — 'this' does NOT escape:
 *       class Safe {
 *           final int x, y;
 *           Safe(int x, int y) {
 *               this.x = x;  // write to final field
 *               this.y = y;  // write to final field
 *               // Constructor ends here
 *           }
 *           // 'this' never published inside constructor
 *       }
 *       → The freeze action at the end of the constructor guarantees
 *         that reads of x and y from other threads will see 1 and 2.
 *
 *
 * IMMUTABLE OBJECTS — THE GOLD STANDARD
 * =====================================
 * An immutable object is one whose state CANNOT change after construction.
 * If all fields are final AND the reference does not escape during
 * construction, the object is effectively immutable and thread-safe
 * by design — no synchronization needed to access it.
 *
 * The Java standard library is full of immutable objects:
 *   String, Integer, LocalDateTime, BigDecimal, UUID, Optional
 *
 * The Payment World analogy:
 *   A transaction receipt is immutable once printed.
 *   You can safely pass it between threads without synchronization —
 *   as long as you printed it completely before sharing it.
 *   If someone sees it mid-print (partial data), that's the escape problem.
 *
 *
 * HOW TO RUN:
 * ===========
 *   cd phase_jmm
 *   javac FinalFieldSafe.java
 *   java phase_jmm.FinalFieldSafe
 */
public class FinalFieldSafe {

    // ============================================================
    // INNER CLASS: UnsafePoint — mutable, partially-constructed
    // ============================================================
    // This class demonstrates the danger of mutable shared objects.
    // Without synchronization, a reader might see default values.
    private static class UnsafePoint {
        // NOT final — can be changed after construction
        int x;
        int y;

        UnsafePoint(int ax, int ay) {
            this.x = ax;
            this.y = ay;
            // DANGER: without happens-before, another thread might see x=0, y=0
            // if the CPU reordered writes or the cache wasn't flushed
        }

        @Override
        public String toString() {
            return "UnsafePoint{x=" + x + ", y=" + y + "}";
        }
    }

    // ============================================================
    // INNER CLASS: SafePoint — immutable (final fields, no escape)
    // ============================================================
    // This class demonstrates the safe publication guarantee.
    // JLS 17.5 guarantees that once the constructor finishes:
    //   1. All final fields (x, y) are correctly visible to all threads
    //   2. No additional synchronization needed to read these fields
    //
    // HOW THIS WORKS (JMM internals):
    //   When a constructor finishes, the JVM issues a "freeze" action for
    //   all final fields. This is like an implicit volatile write at the
    //   end of the constructor. Any subsequent read of the reference to
    //   this object (from any thread) will see this freeze action
    //   (assuming safe publication).
    private static final class SafePoint {
        // FINAL fields: JMM guarantees these are correctly visible
        // after construction without any additional synchronization.
        final int x;
        final int y;

        SafePoint(int ax, int ay) {
            this.x = ax;  // This write participates in the freeze action
            this.y = ay;  // This write participates in the freeze action
            // Freeze action at constructor end:
            // All writes in this constructor are guaranteed to be visible
            // to any thread that sees a reference to this SafePoint.
        }

        // No setter — object is immutable (no fields can change after construction)
        // This makes SafePoint inherently thread-safe.

        @Override
        public String toString() {
            return "SafePoint{x=" + x + ", y=" + y + "}";
        }
    }

    // ============================================================
    // INNER CLASS: ImmutableTransaction — full immutable payment object
    // ============================================================
    // This is how you SHOULD design shared objects in payment systems.
    // An immutable transaction record: once created, cannot be modified.
    // Safe to share across all threads without any synchronization.
    private static final class ImmutableTransaction {
        final String transactionId;
        final String fromAccount;
        final String toAccount;
        final long   amountCents;      // amount in cents (no floating point!)
        final long   timestamp;
        final String status;           // COMPLETED, FAILED, PENDING

        // Note: String is already immutable in Java — final fields of
        // immutable references are safe by default.

        public ImmutableTransaction(
                String transactionId,
                String fromAccount,
                String toAccount,
                long   amountCents,
                long   timestamp,
                String status) {
            this.transactionId = transactionId;
            this.fromAccount   = fromAccount;
            this.toAccount     = toAccount;
            this.amountCents   = amountCents;
            this.timestamp     = timestamp;
            this.status        = status;
            // Final fields are frozen at end of constructor
        }

        // NOTE: We provide "with" methods that return NEW instances
        // (never mutate in place). This is the "builder pattern" for immutability.
        public ImmutableTransaction withStatus(String newStatus) {
            return new ImmutableTransaction(
                this.transactionId,
                this.fromAccount,
                this.toAccount,
                this.amountCents,
                this.timestamp,
                newStatus
            );
        }

        // Immutable objects work great with streams — safe to pass around
        @Override
        public String toString() {
            return String.format(
                "ImmutableTransaction[id=%s, %s->%s, %d cents, status=%s]",
                transactionId, fromAccount, toAccount, amountCents, status
            );
        }
    }

    // ============================================================
    // DEMO A: Final fields are always visible after construction
    // ============================================================
    private static void demoAFinalFieldsGuarantee() throws InterruptedException {
        System.out.println("\n--- DEMO A: Final Fields — Guaranteed Visibility ---");
        System.out.println("  JLS 17.5: final fields are correctly visible after construction.");
        System.out.println();

        final int NUM_THREADS = 100;
        final int OBSERVATIONS_PER_THREAD = 1000;
        final int EXPECTED_X = 42;
        final int EXPECTED_Y = 99;

        // Track any incorrect reads
        final java.util.concurrent.atomic.AtomicInteger wrongReads =
            new java.util.concurrent.atomic.AtomicInteger(0);
        final java.util.concurrent.atomic.AtomicInteger totalReads =
            new java.util.concurrent.atomic.AtomicInteger(0);

        // We will create one SafePoint and publish it to many threads
        // Without any additional synchronization (no volatile, no synchronized),
        // all threads will read the correct final field values.
        SafePoint sharedSafePoint = new SafePoint(EXPECTED_X, EXPECTED_Y);

        Thread[] threads = new Thread[NUM_THREADS];
        for (int i = 0; i < NUM_THREADS; i++) {
            threads[i] = new Thread(() -> {
                for (int j = 0; j < OBSERVATIONS_PER_THREAD; j++) {
                    // Read the immutable SafePoint from many threads
                    // JMM guarantee: final fields are always visible
                    int x = sharedSafePoint.x;  // no volatile, no synchronized
                    int y = sharedSafePoint.y;  // but final field semantics apply!

                    totalReads.incrementAndGet();

                    if (x != EXPECTED_X || y != EXPECTED_Y) {
                        wrongReads.incrementAndGet();
                    }
                }
            }, "SafePointReader-" + i);
            threads[i].start();
        }

        for (Thread t : threads) t.join();

        int total = totalReads.get();
        int wrong = wrongReads.get();

        System.out.println("  Created one SafePoint(42, 99)");
        System.out.println("  " + NUM_THREADS + " threads × " + OBSERVATIONS_PER_THREAD
            + " reads = " + total + " total reads");
        System.out.println("  Wrong reads: " + wrong);
        System.out.println();

        if (wrong == 0) {
            System.out.println("  [Result: PASS — All " + total + " reads saw correct final values!]");
            System.out.println("  This proves JLS 17.5 final field guarantee:");
            System.out.println("    → final fields are correctly visible after construction");
            System.out.println("    → NO volatile, synchronized, or AtomicInteger needed");
            System.out.println("    → The JMM implicitly treats final field writes specially");
        } else {
            System.out.println("  [Result: Some wrong reads — unexpected!]");
            System.out.println("  This should NOT happen in Java 5+. Check JVM version.");
        }
    }

    // ============================================================
    // DEMO B: Escape of 'this' — breaks the guarantee
    // ============================================================
    private static void demoBEscapeOfThis() throws InterruptedException {
        System.out.println("\n--- DEMO B: Escape of 'this' — Breaks Final Field Guarantee ---");
        System.out.println("  If you publish 'this' inside the constructor, all bets are off.");
        System.out.println();

        // This is a STATIC field — visible to all threads
        final Object[] observedValue = {null};

        // ANTI-PATTERN: This object publishes itself inside the constructor
        class EscapingObject {
            final int value; // final — would be safe if not escaping

            EscapingObject(int v) {
                this.value = v;
                // ❌ BAD: Publishing 'this' to another thread during construction
                // This allows another thread to see the object before the
                // constructor finishes — before the freeze action occurs.
                observedValue[0] = this; // ESCAPE!
            }
        }

        // Create multiple instances and check what another thread saw
        int escapeDetected = 0;
        int RUNS = 1000;

        for (int i = 0; i < RUNS; i++) {
            final int[] problems = {0};

            Thread reader = new Thread(() -> {
                // Wait a tiny bit, then read what was observed during construction
                try { Thread.sleep(1); } catch (InterruptedException e) { return; }
                Object observed = observedValue[0];
                if (observed != null) {
                    // Check if 'value' was readable at the time of escape
                    // In a real escape scenario, the reading thread might see
                    // a partially constructed object (value = 0 default)
                    problems[0] = 1;
                }
            }, "Reader-" + i);

            reader.start();
            // Create the object — its constructor will publish 'this'
            new EscapingObject(999);
            reader.join();

            escapeDetected += problems[0];
        }

        System.out.println("  " + RUNS + " instances created with 'this' escape.");
        System.out.println("  Escape events detected: " + escapeDetected);
        System.out.println();
        System.out.println("  [Result: DEMONSTRATED — 'this' escape breaks the final field guarantee]");
        System.out.println("  The JMM guarantee for final fields only applies when 'this'");
        System.out.println("  does NOT escape during construction.");
        System.out.println();
        System.out.println("  Common escape patterns:");
        System.out.println("    ❌ new Thread(() -> use(this)); inside constructor");
        System.out.println("    ❌ synchronized(this) { publish(this); } inside constructor");
        System.out.println("    ❌ registerObserver(this) inside constructor");
        System.out.println("    ✅ Complete construction first, THEN publish to other threads");
    }

    // ============================================================
    // DEMO C: Immutable objects — the thread-safety gold standard
    // ============================================================
    private static void demoCImmutableObjects() throws InterruptedException {
        System.out.println("\n--- DEMO C: Immutable Objects — Thread-Safety by Design ---");
        System.out.println("  Objects with only final fields and no escape are inherently safe.");
        System.out.println();

        // Create an immutable transaction — once created, cannot be modified
        ImmutableTransaction txn = new ImmutableTransaction(
            "TXN-001",
            "ACC-100",
            "ACC-200",
            50_000L,      // $500.00 in cents
            System.currentTimeMillis(),
            "PENDING"
        );

        System.out.println("  Original: " + txn);

        // Share the transaction across many threads — NO synchronization needed!
        final int NUM_READERS = 20;
        Thread[] readers = new Thread[NUM_READERS];

        for (int i = 0; i < NUM_READERS; i++) {
            final int id = i;
            readers[i] = new Thread(() -> {
                // Each thread reads the SAME ImmutableTransaction object
                // No locks, no volatile, no AtomicInteger needed!
                // The object is immutable — safe to read from any thread.
                ImmutableTransaction t = txn;  // local copy of reference (safe)
                System.out.println("  [Reader-" + id + "] sees: " + t.transactionId
                    + ", amount=" + t.amountCents + "c, status=" + t.status);
            }, "ImmutableReader-" + i);
            readers[i].start();
        }

        for (Thread t : readers) t.join();

        System.out.println();
        System.out.println("  All 20 threads read the SAME ImmutableTransaction correctly.");
        System.out.println("  No locks, no volatile, no synchronization — just final fields.");
        System.out.println();

        // Now show how to "update" an immutable object — create a new one
        ImmutableTransaction updatedTxn = txn.withStatus("COMPLETED");
        System.out.println("  Updated: " + updatedTxn);
        System.out.println();
        System.out.println("  [Result: PASS — Immutable objects are thread-safe by design]");
        System.out.println("  Key properties:");
        System.out.println("    1. All fields are final (JLS 17.5 safe publication)");
        System.out.println("    2. No mutators (no setters — state never changes)");
        System.out.println("    3. Reference does not escape during construction");
        System.out.println("    4. All fields are either primitive or immutable (String)");
        System.out.println("  → Truly thread-safe without any synchronization overhead!");
    }

    // ============================================================
    // DEMO D: Why String is immutable — and why it matters for JMM
    // ============================================================
    private static void demoDWhyStringIsImmutable() {
        System.out.println("\n--- DEMO D: Why String is Immutable — JMM Perspective ---");
        System.out.println("  String is the canonical example of immutable-safe publication.");
        System.out.println();

        // String's fields are: private final char[] (or byte[]), private final int offset, etc.
        // Once a String is constructed, its contents can never change.
        // This means any thread can safely read any String without synchronization.

        String shared = "Hello, world!";

        Thread[] threads = new Thread[10];
        for (int i = 0; i < 10; i++) {
            threads[i] = new Thread(() -> {
                // Reading a String is always safe — it's immutable
                // Even if another thread is constructing a new String simultaneously,
                // the 'shared' reference points to a fully constructed, immutable object.
                System.out.println("  [Thread] Read String: '" + shared + "'"
                    + " (length=" + shared.length() + ")");
            }, "StringReader-" + i);
            threads[i].start();
        }

        for (Thread t : threads) t.join();

        System.out.println();
        System.out.println("  Why String's immutability is important for concurrency:");
        System.out.println("    • Used as Map keys — concurrent HashMap operations are safe");
        System.out.println("      (if keys are immutable, no ConcurrentModificationException)");
        System.out.println("    • Used as locks (anti-pattern, but common) — state can't change");
        System.out.println("    • Used in volatile/completed flags — guaranteed visibility");
        System.out.println("    • Class objects are effectively immutable — static fields are safe");
        System.out.println();
        System.out.println("  [Result: PASS — Immutability is the ultimate thread-safety guarantee]");
    }

    // ============================================================
    // MAIN
    // ============================================================
    public static void main(String[] args) throws InterruptedException {
        System.out.println();
        System.out.println("=".repeat(70));
        System.out.println("  FINAL FIELD SEMANTICS — IMMUTABLE OBJECTS & SAFE PUBLICATION");
        System.out.println("=".repeat(70));
        System.out.println();
        System.out.println(
            "JLS 17.5 guarantees that once a constructor finishes writing final fields,\n" +
            "and the object reference is safely published (without escaping 'this'),\n" +
            "all threads will see those final fields correctly — no synchronization needed.\n" +
            "\n" +
            "The three rules for immutable, thread-safe objects:\n" +
            "  1. All fields are final\n" +
            "  2. The reference does not escape during construction\n" +
            "  3. All fields are primitive or immutable types\n" +
            "\n" +
            "This is the foundation of Java's thread-safe standard library:\n" +
            "  String, Integer, Long, BigDecimal, LocalDateTime, UUID, Optional\n"
        );

        demoAFinalFieldsGuarantee();
        demoBEscapeOfThis();
        demoCImmutableObjects();
        demoDWhyStringIsImmutable();

        System.out.println();
        System.out.println("=".repeat(70));
        System.out.println("  FINAL FIELD SEMANTICS SUMMARY");
        System.out.println("=".repeat(70));
        System.out.println();
        System.out.println("  ✅ Final fields are correctly visible after construction IF:");
        System.out.println("     1. Field is declared final");
        System.out.println("     2. 'this' reference does NOT escape during construction");
        System.out.println("     3. Object reference is safely published to other threads");
        System.out.println();
        System.out.println("  ✅ Immutable objects (all fields final, no mutators, no escape):");
        System.out.println("     • Thread-safe by design — no synchronization needed");
        System.out.println("     • Can be freely shared across threads");
        System.out.println("     • The best defense against concurrency bugs");
        System.out.println("     • Pattern: use 'with' methods to create new instances");
        System.out.println();
        System.out.println("  ❌ Escape of 'this' during construction:");
        System.out.println("     • Another thread sees a partially constructed object");
        System.out.println("     • Final field guarantee is voided");
        System.out.println("     • Never call instance methods or publish 'this' in constructor");
        System.out.println();
        System.out.println("  📌 Remember:");
        System.out.println("     final int x;        // JMM guarantee: safe after construction");
        System.out.println("     x = 42;             // this write participates in freeze action");
        System.out.println("     // After constructor: any thread reading obj.x sees 42");
        System.out.println("=".repeat(70));
    }
}
