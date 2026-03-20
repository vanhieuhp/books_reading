package phase_jmm;

/**
 * ============================================================
 * HAPPENS-BEFORE DEMONSTRATION — All 6 JMM Ordering Rules
 * ============================================================
 *
 * THE CORE CONCEPT:
 * =================
 * "If action A happens-before action B, then:
 *    1. All writes by A are guaranteed to be visible to reads by B
 *    2. The execution order of A -> B is preserved (no reordering)"
 *
 * If there is NO happens-before relationship between two actions,
 * the JMM allows ANY outcome — the compiler, CPU, and caches are free
 * to do whatever they want. This is the root of ALL concurrency bugs.
 *
 * THE 6 HAPPENS-BEFORE RULES:
 * ===========================
 *
 *   RULE 1: PROGRAM ORDER (same thread)
 *   ------------------------------------
 *   In the same thread, statement A happens-before statement B
 *   in program order (top-to-bottom, left-to-right).
 *
 *   RULE 2: MONITOR LOCK
 *   --------------------
 *   Unlock of monitor M happens-before every subsequent lock of M.
 *   (If Thread A unlocks, Thread B locking the same monitor sees A's writes.)
 *
 *   RULE 3: VOLATILE
 *   ----------------
 *   Write to volatile V happens-before every subsequent read of V.
 *   (Not just "before" — the JMM enforces total order on volatile accesses.)
 *
 *   RULE 4: THREAD START
 *   --------------------
 *   Thread.start() happens-before the first action in the started thread.
 *   (All setup done in main thread is visible to the new thread.)
 *
 *   RULE 5: THREAD JOIN
 *   -------------------
 *   All actions in Thread T happen-before Thread.join() returns.
 *   (When join() returns, all of T's writes are visible to the joining thread.)
 *
 *   RULE 6: TRANSITIVITY
 *   --------------------
 *   If A happens-before B, and B happens-before C,
 *   then A happens-before C.
 *   (This chains the rules together.)
 *
 * HOW TO RUN:
 * ===========
 *   cd phase_jmm
 *   javac HappensBeforeDemo.java
 *   java phase_jmm.HappensBeforeDemo
 *
 *   Each demonstration prints whether the HB relationship was satisfied.
 */
public class HappensBeforeDemo {

    // ============================================================
    // SHARED STATE — no synchronization
    // ============================================================
    private static int counter      = 0;
    private static boolean dataReady = false;
    private static String  message  = null;

    // ============================================================
    // VOLATILE versions — demonstrate Rule 3
    // ============================================================
    private static volatile int       volatileCounter = 0;
    private static volatile boolean   volatileReady   = false;
    private static volatile String    volatileMessage = null;

    // ============================================================
    // LOCK versions — demonstrate Rule 2
    // ============================================================
    private static final Object lockA = new Object();
    private static int lockProtectedCounter = 0;
    private static String lockProtectedMessage = null;

    // ============================================================
    // DEMONSTRATION 1: Program Order (Rule 1)
    // ============================================================
    // Within a single thread, operations happen in program order.
    // This rule ALWAYS holds — even in the absence of synchronization.
    private static void demonstrateProgramOrder() {
        System.out.println("\n--- DEMO 1: Program Order (Rule 1) ---");

        int a = 1;
        int b = 2;
        int c = a + b; // guaranteed to see a=1 and b=2

        System.out.println("  Within one thread, reads always see prior writes in program order.");
        System.out.println("  a=1, b=2, c=a+b = " + c + " — always correct within a thread.");
        System.out.println("  This is the ONLY rule that requires NO synchronization.");
        System.out.println("  [Result: PASS — Program order is always preserved within a thread]");
    }

    // ============================================================
    // DEMONSTRATION 2: Monitor Lock (Rule 2)
    // ============================================================
    // Unlock of monitor M happens-before every subsequent lock of M.
    //
    // Scenario:
    //   Thread A: writes to shared state, then UNLOCKS
    //   Thread B: LOCKS, then reads shared state
    //   HB relationship: Thread A's write -> Thread A's unlock -> Thread B's lock -> Thread B's read
    //   Therefore: Thread B is guaranteed to see Thread A's write.
    private static void demonstrateMonitorLock() throws InterruptedException {
        System.out.println("\n--- DEMO 2: Monitor Lock (Rule 2) ---");
        System.out.println("  Rule: Unlock of monitor M happens-before subsequent lock of M.");
        System.out.println();

        lockProtectedCounter = 0;
        lockProtectedMessage = null;

        Thread writer = new Thread(() -> {
            // CRITICAL: All writes must be inside the synchronized block
            // because happens-before applies to LOCK/UNLOCK, not to
            // statements adjacent to the synchronized block.
            synchronized (lockA) {
                lockProtectedCounter = 42;
                lockProtectedMessage = "Hello from writer!";
                // End of synchronized block = UNLOCK happens here
                // JMM guarantees all writes above are flushed to main memory
                // before the lock is released.
            }
        }, "Writer-Lock");

        Thread reader = new Thread(() -> {
            // Spin until writer finishes
            while (lockProtectedCounter == 0) {
                Thread.yield();
            }
            // Now acquire the SAME lock
            // JMM guarantee: this lock acquisition sees all writes
            // from the writer's synchronized block (because of Rule 2).
            synchronized (lockA) {
                System.out.println("  Reader acquired lock — seeing counter = " + lockProtectedCounter);
                System.out.println("  Reader acquired lock — seeing message = '" + lockProtectedMessage + "'");

                boolean pass = (lockProtectedCounter == 42)
                    && ("Hello from writer!".equals(lockProtectedMessage));

                System.out.println("  [Result: " + (pass ? "PASS" : "FAIL") + " — Lock HB guarantee worked!]");
            }
        }, "Reader-Lock");

        writer.start();
        reader.start();
        writer.join();
        reader.join();
    }

    // ============================================================
    // DEMONSTRATION 3: Volatile (Rule 3)
    // ============================================================
    // Write to volatile V happens-before every subsequent read of V.
    //
    // In this demo:
    //   Writer writes: volatileMessage = "Hello", volatileReady = true
    //   Reader reads: while(!volatileReady), then print(volatileMessage)
    //
    // Because 'ready' is volatile:
    //   Writer's write to 'message' happens-before write to 'ready'
    //   Write to 'ready'  happens-before READ of 'ready' (Rule 3)
    //   By transitivity (Rule 6): message write happens-before ready read
    //   And: ready read happens-before message read (program order in reader)
    //   Therefore: Reader sees the message correctly.
    private static void demonstrateVolatile() throws InterruptedException {
        System.out.println("\n--- DEMO 3: Volatile (Rule 3) ---");
        System.out.println("  Rule: Write to volatile V happens-before subsequent read of V.");
        System.out.println();

        // Reset volatile state
        volatileMessage = null;
        volatileReady   = false;

        // Tracking (synchronized for safe counting)
        final Object countLock = new Object();
        int[] passCount = {0};
        int[] failCount = {0};

        Runnable writer = () -> {
            // Write to message FIRST (in program order)
            volatileMessage = "Hello from volatile writer!";
            // Write to volatile flag SECOND (in program order)
            volatileReady = true;
            // JMM guarantee: the write to message is visible when
            // the write to ready becomes visible to any other thread.
        };

        Runnable reader = () -> {
            // Spin wait for the volatile flag
            while (!volatileReady) {
                Thread.yield();
            }
            // At this point: volatile write (ready=true) HB this volatile read
            // By transitivity: the write to volatileMessage is also visible!

            String msg = volatileMessage;
            boolean pass = ("Hello from volatile writer!".equals(msg));

            synchronized (countLock) {
                if (pass) passCount[0]++;
                else      failCount[0]++;
            }

            if (!pass) {
                System.out.println("  *** FAILURE: saw message = '" + msg
                    + "' — volatile HB relationship did NOT hold!");
            }
        };

        int RUNS = 50;
        Thread[] writers = new Thread[RUNS];
        Thread[] readers = new Thread[RUNS];

        for (int i = 0; i < RUNS; i++) {
            writers[i] = new Thread(writer, "VolatileWriter-" + i);
            readers[i] = new Thread(reader, "VolatileReader-" + i);

            readers[i].start();  // start reader first (spins on ready)
            writers[i].start();  // start writer (writes then sets ready)
        }

        for (Thread t : writers) t.join();
        for (Thread t : readers) t.join();

        System.out.println("  " + RUNS + " concurrent reader/writer pairs tested.");
        System.out.println("  Passes: " + passCount[0] + " | Failures: " + failCount[0]);

        if (failCount[0] == 0) {
            System.out.println("  [Result: ALL PASS — Volatile HB rule guarantees visibility!]");
        } else {
            System.out.println("  [Result: SOME FAIL — Unexpected!");
            System.out.println("   Note: volatile SHOULD guarantee visibility in Java 5+.");
            System.out.println("   If failures occur, check JVM version and flags.]");
        }
    }

    // ============================================================
    // DEMONSTRATION 4: Thread Start (Rule 4)
    // ============================================================
    // Thread.start() happens-before the first action in the started thread.
    //
    // Scenario:
    //   Main thread: sets up important data, then calls t.start()
    //   Thread t: reads the important data
    //   HB: main thread's writes -> t.start() call -> t's first action
    //   Therefore: thread t sees the data set up before it started.
    private static void demonstrateThreadStart() throws InterruptedException {
        System.out.println("\n--- DEMO 4: Thread Start (Rule 4) ---");
        System.out.println("  Rule: Thread.start() happens-before first action in started thread.");
        System.out.println();

        // These are set BEFORE thread.start() is called
        final long importantData = 0xDEADBEEF_L;
        final String importantMsg = "Setup in main thread before start()";

        // Flag to track if the thread saw correct values
        final Object resultLock = new Object();
        boolean[] sawCorrectValues = {false};

        // The new thread reads data that was set up BEFORE start()
        Thread worker = new Thread(() -> {
            // This is the FIRST action in this thread
            // JMM guarantee: sees all writes made in main thread
            // BEFORE start() was called.
            if (importantData == 0xDEADBEEF_L && "Setup in main thread before start()".equals(importantMsg)) {
                synchronized (resultLock) {
                    sawCorrectValues[0] = true;
                }
                System.out.println("  Worker thread: saw correct values (0xDEADBEEF and setup message).");
                System.out.println("  [PASS — Thread.start() HB guarantee worked!]");
            } else {
                System.out.println("  Worker thread: saw INCORRECT values — Thread.start() HB broken!");
                System.out.println("  [FAIL — This should NEVER happen in Java 5+]");
            }
        }, "Worker-Thread");

        // Set up data BEFORE starting the thread
        // All of these writes happen-before worker.start() (Rule 4)
        // Therefore, all of these writes are visible to the worker thread.

        worker.start();  // Thread.start() happens-before first action in worker
        worker.join();
    }

    // ============================================================
    // DEMONSTRATION 5: Thread Join (Rule 5)
    // ============================================================
    // All actions in Thread T happen-before Thread.join() returns.
    //
    // Scenario:
    //   Thread t: computes a result, writes it to shared state
    //   Main thread: calls t.join()
    //   HB: t's writes -> t's final action -> join() returns -> main reads
    //   Therefore: main thread sees t's computation result after join().
    private static void demonstrateThreadJoin() throws InterruptedException {
        System.out.println("\n--- DEMO 5: Thread Join (Rule 5) ---");
        System.out.println("  Rule: All actions in Thread T happen-before Thread.join() returns.");
        System.out.println();

        final long[] sharedResult = {-1};
        final String[] sharedMsg  = {null};

        Thread computer = new Thread(() -> {
            // Compute something expensive
            long sum = 0;
            for (int i = 0; i < 100_000; i++) {
                sum += i;
            }

            // Write results
            sharedResult[0] = sum;                   // Will be 4999950000
            sharedMsg[0] = "Computed in worker thread";

            System.out.println("  Worker: computed result = " + sum);
        }, "Computer-Thread");

        computer.start();

        // join() blocks until computer thread finishes
        // JMM guarantee: all writes made by computer thread are
        // visible when join() returns (Rule 5).
        computer.join();

        // At this point, we are GUARANTEED to see the writes from computer thread
        long expectedSum = 4_999_950_000L;

        boolean pass = (sharedResult[0] == expectedSum)
            && ("Computed in worker thread".equals(sharedMsg[0]));

        System.out.println("  Main thread: after join(), sees result = " + sharedResult[0]);
        System.out.println("  Main thread: after join(), sees msg   = '" + sharedMsg[0] + "'");
        System.out.println("  [Result: " + (pass ? "PASS" : "FAIL") + " — Thread.join() HB guarantee worked!]");
    }

    // ============================================================
    // DEMONSTRATION 6: Transitivity (Rule 6) — The Chainsaw
    // ============================================================
    // This demonstrates that the HB rules COMPOSE (chain together).
    // This is what makes the JMM usable in practice.
    //
    // Scenario — three threads with a chain of HB relationships:
    //   Thread A: writes to volatileShared (volatile write — Rule 3)
    //   Thread B: reads volatileShared, then writes to regularShared
    //             (volatile read — Rule 3, program order — Rule 1)
    //   Thread C: reads regularShared after Thread.join(B)
    //             (join — Rule 5, program order — Rule 1)
    //
    // Chain: A(write volatile) HB B(read volatile) HB B(write regular) HB join(B) HB C(read regular)
    // Therefore: C is guaranteed to see A's write!
    private static void demonstrateTransitivity() throws InterruptedException {
        System.out.println("\n--- DEMO 6: Transitivity (Rule 6) — Chaining HB Relationships ---");
        System.out.println("  Rule: If A HB B and B HB C, then A HB C.");
        System.out.println();
        System.out.println("  Chain: VolatileWrite(A) HB VolatileRead(B) HB WriteRegular(B)"
            + " HB join(B) HB ReadRegular(C)");
        System.out.println();

        // Set by Thread A
        volatile long threadAResult = 0;

        // Read by Thread B, then written; read by Thread C
        long threadBResult = 0;

        // Thread A: volatile write
        Thread threadA = new Thread(() -> {
            threadAResult = 123456789L;
            // This volatile write happens-before Thread B's volatile read
        }, "Thread-A");

        // Thread B: volatile read, then regular write
        Thread threadB = new Thread(() -> {
            // Spin until thread A does the write
            while (threadAResult == 0) {
                Thread.yield();
            }
            // At this point, volatile read of threadAResult gives us A's write
            // (Rule 3: Volatile read HB relationship)
            threadBResult = threadAResult * 2; // 123456789L * 2
            // This regular write happens-before join() returns (Rule 5)
        }, "Thread-B");

        // Thread C: joins B, then reads threadBResult
        Thread threadC = new Thread(() -> {
            try {
                threadB.join(); // join() returns only after B finishes (Rule 5)
                // All of B's writes (including threadBResult) are now visible
                // By transitivity: A's write to threadAResult is also visible!

                boolean pass = (threadBResult == 246913578L);

                System.out.println("  Thread C: after join(B), sees threadBResult = " + threadBResult);
                System.out.println("  Thread C: sees 123456789 * 2 = 246913578");
                System.out.println("  [Result: " + (pass ? "PASS" : "FAIL")
                    + " — Transitivity chained HB across 3 threads!]");
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        }, "Thread-C");

        threadA.start();
        threadB.start();
        threadC.start();

        threadA.join();
        threadB.join();
        threadC.join();
    }

    // ============================================================
    // DEMONSTRATION 7: NO happens-before — anything can happen
    // ============================================================
    // This demonstrates why the ABSENCE of an HB relationship is dangerous.
    // Two threads reading/writing shared state with NO synchronization:
    //   Writer: writes to X, then writes to Y
    //   Reader: reads Y, then reads X
    //
    // Without any HB relationship:
    //   - The JIT/CPU can reorder Writer's writes
    //   - The Reader can see X and Y from different points in Writer's timeline
    //   - The Reader might see Y's NEW value but X's OLD value
    private static void demonstrateNoHappensBefore() throws InterruptedException {
        System.out.println("\n--- DEMO 7: NO Happens-Before — Dangerous Territory ---");
        System.out.println("  Without any HB relationship, the JMM allows ANY outcome.");
        System.out.println();

        int[] x = {0};
        int[] y = {0};

        // We run this multiple times to show non-determinism
        int anomalies = 0;
        int RUNS = 1000;

        for (int run = 0; run < RUNS; run++) {
            x[0] = 0;
            y[0] = 0;

            Thread writer = new Thread(() -> {
                x[0] = 1;  // Write X first
                y[0] = 1;  // Write Y second (in program order)
            }, "Writer-NoHB");

            Thread reader = new Thread(() -> {
                // Read Y first, then X (opposite order from writer)
                int readY = y[0];
                int readX = x[0];

                // "Anomaly": we see Y=1 (new) but X=0 (old)
                // This can ONLY happen if there is no HB relationship.
                if (readY == 1 && readX == 0) {
                    synchronized (HappensBeforeDemo.class) {
                        anomalies++;
                    }
                }
            }, "Reader-NoHB");

            reader.start();
            writer.start();

            writer.join();
            reader.join();
        }

        System.out.println("  Ran " + RUNS + " iterations of unsynchronized writer/reader.");
        System.out.println("  Anomalies (Y=1 but X=0): " + anomalies + "/" + RUNS);
        System.out.println();

        if (anomalies > 0) {
            System.out.println("  [Result: ANOMALY DETECTED!]");
            System.out.println("  Without any HB, the reader can see writes in an ORDER");
            System.out.println("  that differs from program order — the JMM allows this!");
            System.out.println();
            System.out.println("  This is called 'out-of-order execution' and is legal");
            System.out.println("  at the JMM level when no HB relationship exists.");
        } else {
            System.out.println("  [No anomalies in " + RUNS + " runs.]");
            System.out.println("  This does NOT mean the code is safe!");
            System.out.println("  The JMM still allows anomalies — they just didn't");
            System.out.println("  manifest this time. Increase RUNS or run on more cores.");
        }
    }

    // ============================================================
    // MAIN
    // ============================================================
    public static void main(String[] args) throws InterruptedException {
        System.out.println();
        System.out.println("=".repeat(70));
        System.out.println("  HAPPENS-BEFORE — THE 6 JMM ORDERING RULES");
        System.out.println("=".repeat(70));
        System.out.println();
        System.out.println(
            "The happens-before (HB) relationship is the core of the Java Memory Model.\n" +
            "It is a ORDERING guarantee: if A HB B, then:\n" +
            "  1. All writes by A are visible to reads by B (VISIBILITY)\n" +
            "  2. A cannot be reordered AFTER B (ORDERING)\n" +
            "\n" +
            "If there is NO HB relationship, anything can happen.\n" +
            "That is why every concurrent bug you've ever seen exists.\n"
        );

        demonstrateProgramOrder();
        demonstrateMonitorLock();
        demonstrateVolatile();
        demonstrateThreadStart();
        demonstrateThreadJoin();
        demonstrateTransitivity();
        demonstrateNoHappensBefore();

        System.out.println();
        System.out.println("=".repeat(70));
        System.out.println("  SUMMARY OF HAPPENS-BEFORE RULES");
        System.out.println("=".repeat(70));
        System.out.println();
        System.out.println("  Rule 1 — Program Order:");
        System.out.println("    A happens-before B within the same thread (top-to-bottom)");
        System.out.println();
        System.out.println("  Rule 2 — Monitor Lock:");
        System.out.println("    Unlock of monitor M happens-before subsequent lock of M");
        System.out.println();
        System.out.println("  Rule 3 — Volatile:");
        System.out.println("    Write to volatile V happens-before every subsequent read of V");
        System.out.println();
        System.out.println("  Rule 4 — Thread Start:");
        System.out.println("    Thread.start() happens-before first action in started thread");
        System.out.println();
        System.out.println("  Rule 5 — Thread Join:");
        System.out.println("    All actions in Thread T happen-before Thread.join() returns");
        System.out.println();
        System.out.println("  Rule 6 — Transitivity:");
        System.out.println("    If A HB B and B HB C, then A HB C (rules chain together)");
        System.out.println();
        System.out.println("=".repeat(70));
    }
}
