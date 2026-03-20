package phase_jmm;

/**
 * ============================================================
 * THE VISIBILITY PROBLEM — Stale Reads in Multi-Threaded Code
 * ============================================================
 *
 * THE PHENOMENON:
 * ===============
 * Without proper synchronization, a write by Thread A to a shared variable
 * may NEVER be visible to Thread B — even after Thread A finishes writing.
 *
 * This happens because:
 *   1. Thread A writes to its CPU core's L1/L2 cache
 *   2. The value sits in the cache, not in main RAM
 *   3. Thread B runs on a DIFFERENT CPU core with its own cache
 *   4. Thread B's cache still holds the OLD value of the variable
 *   5. Thread B reads the stale cached value forever
 *
 * WHY IT'S HARD TO REPRODUCE:
 * ============================
 * - On a single-core CPU: all threads share the same cache → visibility "works"
 * - On an old machine with 2 cores: less contention, might "work"
 * - On a modern 8+ core machine: higher chance different threads land on
 *   different cores, cache incoherency becomes visible
 * - The JIT compiler can also hide the problem by keeping values in registers
 *   rather than cache, making the bug appear to "work" in testing
 *
 * HOW TO "FIX" THIS (badly):
 * ==========================
 * Adding Thread.sleep() or System.out.println() between the write and the read
 * often "fixes" the bug — NOT because those operations synchronize, but because
 * they give the OS scheduler a chance to migrate threads or flush caches.
 * This is NOT a real fix; it just makes the bug less likely to appear in tests.
 *
 * REAL FIXES (covered in later files):
 * ====================================
 *   1. Declare the variable as VOLATILE — see VolatileDemo.java
 *   2. Access the variable inside SYNCHRONIZED blocks — see SynchronizedVisibility.java
 *   3. Use atomic classes from java.util.concurrent.atomic
 *
 *
 * HOW TO RUN:
 * ===========
 *   cd phase_jmm
 *   javac VisibilityProblem.java
 *   java phase_jmm.VisibilityProblem
 *
 *   Try running it multiple times. On a multi-core machine, you should see
 *   the reader thread print 0 (stale value) even though the writer clearly
 *   set number = 42 before setting ready = true.
 *
 *   If you see "SUCCESS" printed, the visibility issue did not manifest this run.
 *   Run it 20 times (or increase TOTAL_RUNS) — the bug WILL appear.
 */
public class VisibilityProblem {

    // ============================================================
    // These fields are NOT volatile, NOT synchronized
    // They are plain shared mutable fields — the textbook visibility hazard
    // ============================================================

    /** The number we want to read. Written by writer, read by reader. */
    private static int number = 0;

    /** Flag written by writer, read by reader — should signal "read number now" */
    private static boolean ready = false;

    // ============================================================
    // WRITER THREAD
    // Writes number = 42, then sets ready = true
    // ============================================================
    private static class WriterTask implements Runnable {
        @Override
        public void run() {
            // According to program order, these two lines run in order:
            // Step 1: write to number
            // Step 2: write to ready
            // But WITHOUT happens-before guarantees, the CPU/JIT may reorder them.
            number = 42;      // STEP 1: Write to 'number'
            ready = true;     // STEP 2: Write to 'ready' (signals: "number is ready")
        }
    }

    // ============================================================
    // READER THREAD
    // Waits until ready == true, then reads number
    // ============================================================
    private static class ReaderTask implements Runnable {
        @Override
        public void run() {
            // Spin until ready becomes true
            // NOTE: without synchronization, the JIT compiler is free to:
            //   1. Hoist the read of 'ready' out of the loop (cache it in a register)
            //      while (!ready) { }  ← JIT might read 'ready' ONCE into a register
            //                           and never check the memory location again!
            //   2. Reorder the reads: check number first (still 0), then check ready
            //
            // We add a local variable to PREVENT the JIT from hoisting the read.
            // Without 'localReady', the JIT CAN optimize the loop to read ready once.
            boolean localReady = ready; // force a memory read each iteration
            while (!localReady) {
                // Tiny pause prevents the JIT from spinning forever in native code
                // (which would prevent the OS from scheduling the writer thread)
                Thread.yield(); // hint to OS scheduler — don't burn CPU

                // Re-read from memory every iteration (still no visibility guarantee!)
                localReady = ready;
            }

            // Now read the number
            // Without happens-before, this read might see the DEFAULT value (0),
            // even though the writer clearly wrote 42 first.
            // Possible outcomes:
            //   - Reader reads 0:  visibility problem! (stale cache or reordering)
            //   - Reader reads 42: "lucky" — the cache happened to sync in time
            System.out.println("Reader saw number = " + number);

            // Record the result
            if (number == 42) {
                recordSuccess();
            } else {
                recordFailure(number);
            }
        }
    }

    // ============================================================
    // Statistics tracking (synchronized so we can track across runs)
    // ============================================================
    private static int successCount = 0;
    private static int failureCount = 0;

    private static synchronized void recordSuccess() {
        successCount++;
    }

    private static synchronized void recordFailure(int seenValue) {
        failureCount++;
        System.out.println("  *** FAILURE: Reader saw number = " + seenValue
            + " (expected 42) — this is the VISIBILITY BUG in action!");
    }

    // ============================================================
    // Run one visibility test
    // ============================================================
    private static void runOnce() throws InterruptedException {
        // Reset state — critical: start with clean slate
        number = 0;
        ready  = false;

        Thread writer = new Thread(new WriterTask(), "Writer");
        Thread reader = new Thread(new ReaderTask(), "Reader");

        // Start reader first — it will spin waiting for ready=true
        reader.start();

        // Small delay ensures reader is spinning before writer starts
        // (makes the race condition more likely to manifest)
        Thread.sleep(10);

        // Start writer — it writes number=42 then ready=true
        writer.start();

        // Wait for both threads to finish
        writer.join();
        reader.join();
    }

    // ============================================================
    // MAIN
    // ============================================================
    public static void main(String[] args) throws InterruptedException {
        System.out.println();
        System.out.println("=".repeat(70));
        System.out.println("  VISIBILITY PROBLEM DEMONSTRATION");
        System.out.println("  Running multiple times to observe non-deterministic failures");
        System.out.println("=".repeat(70));
        System.out.println();
        System.out.println(
            "This program demonstrates a classic JMM visibility problem:\n" +
            "  Writer thread: writes number=42, then ready=true\n" +
            "  Reader thread: waits for ready=true, then reads number\n" +
            "\n" +
            "Expected (with proper synchronization): number always = 42\n" +
            "Actual (WITHOUT synchronization): number may be 0 (stale read!)\n"
        );
        System.out.println();

        int TOTAL_RUNS = 30;
        System.out.println("Running " + TOTAL_RUNS + " test iterations...\n");

        for (int i = 1; i <= TOTAL_RUNS; i++) {
            System.out.print("Run " + String.format("%2d", i) + "/" + TOTAL_RUNS + ": ");
            runOnce();
        }

        System.out.println();
        System.out.println("=".repeat(70));
        System.out.println("  SUMMARY");
        System.out.println("=".repeat(70));
        System.out.println("  Successes (read 42): " + successCount);
        System.out.println("  Failures (read 0):   " + failureCount);
        System.out.println();

        if (failureCount > 0) {
            System.out.println(
                "  VISIBILITY BUG CONFIRMED!\n" +
                "  The reader thread saw a stale value (0) even though\n" +
                "  the writer clearly wrote 42 before setting ready=true.\n" +
                "\n" +
                "  Why did this happen?\n" +
                "  1. Writer wrote number=42 to Core 0's cache\n" +
                "  2. That value never reached main RAM or Core 1's cache\n" +
                "  3. Reader (on Core 1) kept reading the OLD value (0) from its cache\n" +
                "  4. OR: the JIT/CPU reordered number=42 and ready=true\n" +
                "\n" +
                "  The fix: use volatile, synchronized, or atomic classes.\n" +
                "  See VolatileDemo.java and SynchronizedVisibility.java."
            );
        } else {
            System.out.println(
                "  NOTE: No failures observed this run.\n" +
                "  This does NOT mean the code is safe!\n" +
                "  The visibility bug is non-deterministic — it depends on\n" +
                "  cache state, CPU core assignment, JIT compilation timing, etc.\n" +
                "  Run on different hardware or increase TOTAL_RUNS.\n" +
                "\n" +
                "  The bug is guaranteed to exist by the JMM when there is no\n" +
                "  happens-before relationship between writer and reader."
            );
        }
    }
}
