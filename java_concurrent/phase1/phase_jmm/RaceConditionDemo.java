package phase_jmm;

/**
 * ============================================================
 * RACE CONDITION DEMONSTRATION — Data Race vs Synchronized
 * ============================================================
 *
 * WHAT IS A RACE CONDITION?
 * =========================
 * A race condition occurs when two or more threads access shared mutable
 * state concurrently, and at least one thread writes to that state, and
 * the correctness of the result depends on the order of execution.
 *
 * In JMM terms: there is NO happens-before relationship between the
 * accesses by different threads. Therefore, the JMM allows ANY outcome.
 *
 * Two types of races:
 *   1. DATA RACE (the technical JMM term):
 *      Two accesses to the same shared variable, at least one is a write,
 *      and there is NO happens-before relationship between them.
 *      → Undefined behavior under the JMM.
 *
 *   2. LOGIC RACE (the commonly described "race condition"):
 *      A correctness bug where the program's behavior depends on thread
 *      scheduling order, even if both accesses are technically synchronized.
 *      → This is a design flaw, not a JMM violation.
 *
 *
 * THE BANK ACCOUNT SCENARIO:
 * =========================
 * Starting balance: $1000
 * Thread A: debits $500
 * Thread B: debits $500
 * Expected final balance: $0
 *
 * With NO synchronization (DATA RACE):
 *   Step 1: Thread A reads balance = 1000
 *   Step 2: Thread B reads balance = 1000  ← same stale value!
 *   Step 3: Thread A writes balance = 500   (1000 - 500)
 *   Step 4: Thread B writes balance = 500   (1000 - 500) ← clobbers A's write!
 *   Final balance: $500  ← WRONG! Lost $500.
 *
 * With synchronized (MUTUAL EXCLUSION):
 *   Thread A acquires lock → reads 1000 → writes 500 → releases lock
 *   Thread B acquires lock → reads 500  → writes 0   → releases lock
 *   Final balance: $0  ← CORRECT!
 *
 *
 * THE JMM PERSPECTIVE:
 * ===================
 * Without happens-before:
 *   • Thread A's write to balance may not be visible to Thread B
 *   • Thread B may read a stale value
 *   • Thread B's write may clobber Thread A's write
 *   • The read-modify-write sequence is not atomic
 *
 * With happens-before (via synchronized):
 *   • Thread A's write to balance is guaranteed visible to Thread B
 *   • The reads and writes happen in a mutually exclusive order
 *   • The program has well-defined, deterministic behavior
 *
 *
 * HOW TO RUN:
 * ===========
 *   cd phase_jmm
 *   javac RaceConditionDemo.java
 *   java phase_jmm.RaceConditionDemo
 */
public class RaceConditionDemo {

    // ============================================================
    // PART A: Unsynchronized Bank Account (DATA RACE — BAD)
    // ============================================================
    private static class UnsafeBankAccount {
        // Shared mutable state — no synchronization
        private double balance;

        public UnsafeBankAccount(double initialBalance) {
            this.balance = initialBalance;
        }

        // ❌ DATA RACE on 'balance' field:
        // Two threads call debit() concurrently.
        // Thread A: reads balance=1000, subtracts, writes 500
        // Thread B: reads balance=1000 ← (same stale value! A hasn't written yet)
        //           subtracts, writes 500 ← (clobbers A's write!)
        // Result: balance=500 instead of 0. One debit is LOST.
        public void debit(double amount) {
            // RACE WINDOW: between reading balance and writing it back,
            // another thread can read the OLD balance value and overwrite
            // this thread's write.
            if (balance >= amount) {
                // Artificial delay AMPLIFIES the race window.
                // In real code, this would be a DB call, network I/O, etc.
                // which creates an even wider race window naturally.
                try { Thread.sleep(1); } catch (InterruptedException e) { }

                balance = balance - amount;
            }
        }

        public double getBalance() {
            return balance;
        }
    }

    // ============================================================
    // PART B: Synchronized Bank Account (SAFE)
    // ============================================================
    private static class SafeBankAccount {
        // Shared mutable state — synchronized methods ensure mutual exclusion
        private double balance;

        public SafeBankAccount(double initialBalance) {
            this.balance = initialBalance;
        }

        // ✅ synchronized method:
        //   1. Acquires the intrinsic lock on 'this' SafeBankAccount instance
        //   2. Reads balance
        //   3. Checks >= amount
        //   4. Subtracts and writes back
        //   5. Releases the lock
        //
        // While Thread A is inside debit(), Thread B CANNOT enter debit()
        // because the lock is held. Thread B is BLOCKED until A releases.
        //
        // JMM guarantee: When A exits and B enters (HB relationship via monitor lock):
        //   → All of A's writes to 'balance' are visible to B
        //   → B sees A's updated balance, not a stale value
        public synchronized boolean debit(double amount) {
            if (balance < amount) {
                return false; // insufficient funds — lock still held
            }
            // At this point, no other thread can be inside this method
            balance = balance - amount;
            return true; // explicit success — caller knows what happened
        }

        public synchronized double getBalance() {
            return balance;
        }
    }

    // ============================================================
    // PART C: Bank Account using AtomicLong (LOCK-FREE, CAS-based)
    // ============================================================
    // Alternative: use AtomicLong for lock-free thread safety.
    // Uses hardware CAS (Compare-And-Swap) — not a lock at all.
    // Works by: read value → compute new value → CAS(current, new)
    //           If another thread changed it in between, CAS fails → retry
    private static class AtomicBankAccount {
        // private volatile long balance;  // volatile needed for visibility
        // BUT: AtomicLong already handles this internally with CAS
        private final java.util.concurrent.atomic.AtomicLong balance;

        public AtomicBankAccount(double initialBalance) {
            // Store balance as cents to avoid floating-point issues
            this.balance = new java.util.concurrent.atomic.AtomicLong(
                (long) (initialBalance * 100)
            );
        }

        // Uses CAS loop — lock-free but thread-safe
        public boolean debit(double amount) {
            long amountCents = (long) (amount * 100);
            long current;
            long newBalance;

            do {
                current = balance.get();         // read current value
                if (current < amountCents) {
                    return false; // insufficient funds — no CAS needed
                }
                newBalance = current - amountCents;
                // CAS: only succeeds if nobody else changed 'balance' to something else
                // If another thread changed it, current != balance.get() → retry
            } while (!balance.compareAndSet(current, newBalance));

            return true; // CAS succeeded — debit applied
        }

        public double getBalance() {
            return balance.get() / 100.0;
        }
    }

    // ============================================================
    // DEMO A: Unsafe Bank Account — shows the race condition
    // ============================================================
    private static void demoAUnsafeAccount() throws InterruptedException {
        System.out.println("\n--- DEMO A: Unsafe Bank Account (DATA RACE) ---");
        System.out.println("  This demonstrates the classic race condition.");
        System.out.println("  Initial balance: $1000.00");
        System.out.println("  Two threads each debit $500.00.");
        System.out.println("  Expected final balance: $0.00");
        System.out.println("  Actual final balance: often $500.00 (LOST UPDATE!)");
        System.out.println();

        final int NUM_EXPERIMENTS = 10;
        final int THREADS_PER_EXP = 2;
        final double DEBIT_AMOUNT = 500.0;
        final double INITIAL_BALANCE = 1000.0;

        int[] losses = new int[NUM_EXPERIMENTS];
        int[] correct = new int[NUM_EXPERIMENTS];

        for (int exp = 0; exp < NUM_EXPERIMENTS; exp++) {
            final UnsafeBankAccount account = new UnsafeBankAccount(INITIAL_BALANCE);

            Thread[] threads = new Thread[THREADS_PER_EXP];
            for (int i = 0; i < THREADS_PER_EXP; i++) {
                threads[i] = new Thread(() -> {
                    account.debit(DEBIT_AMOUNT);
                }, "UnsafeDebit-" + i);
            }

            for (Thread t : threads) t.start();
            for (Thread t : threads) t.join();

            double finalBalance = account.getBalance();
            double expectedBalance = INITIAL_BALANCE - (THREADS_PER_EXP * DEBIT_AMOUNT);

            if (Math.abs(finalBalance - expectedBalance) > 0.01) {
                losses[exp] = 1;
                System.out.println("  Experiment " + (exp + 1) + ": EXPECTED $"
                    + String.format("%.2f", expectedBalance)
                    + " | ACTUAL $"
                    + String.format("%.2f", finalBalance)
                    + " ← LOST UPDATE!");
            } else {
                correct[exp] = 1;
                System.out.println("  Experiment " + (exp + 1) + ": $"
                    + String.format("%.2f", finalBalance) + " ← correct (lucky run)");
            }
        }

        int totalLosses = 0, totalCorrect = 0;
        for (int i = 0; i < NUM_EXPERIMENTS; i++) { totalLosses += losses[i]; totalCorrect += correct[i]; }

        System.out.println();
        System.out.println("  Summary over " + NUM_EXPERIMENTS + " experiments:");
        System.out.println("    Correct: " + totalCorrect + " | Lost updates: " + totalLosses);
        System.out.println();

        if (totalLosses > 0) {
            System.out.println("  [Result: RACE CONDITION CONFIRMED — data race causes lost updates]");
            System.out.println();
            System.out.println("  WHY DID THIS HAPPEN?");
            System.out.println("    Thread A and B both called debit() simultaneously.");
            System.out.println("    Both threads read balance=1000 (before the other wrote back).");
            System.out.println("    Both passed the 'balance >= amount' check.");
            System.out.println("    Both wrote back balance=500.");
            System.out.println("    One debit was silently lost.");
            System.out.println();
            System.out.println("  JMM EXPLAINS WHY THIS IS LEGAL (and dangerous):");
            System.out.println("    There is NO happens-before relationship between the");
            System.out.println("    two threads' accesses to 'balance'.");
            System.out.println("    The JMM allows the outcome: $500 (wrong).");
            System.out.println("    This is undefined behavior at the JMM level.");
        } else {
            System.out.println("  [No losses observed — but the race still exists!]");
            System.out.println("  Try increasing THREADS_PER_EXP to amplify contention.");
        }
    }

    // ============================================================
    // DEMO B: Safe Bank Account — synchronized fixes the race
    // ============================================================
    private static void demoBSafeAccount() throws InterruptedException {
        System.out.println("\n--- DEMO B: Safe Bank Account (synchronized) ---");
        System.out.println("  Same scenario as Demo A, but with synchronized methods.");
        System.out.println("  Initial balance: $1000.00");
        System.out.println("  Two threads each debit $500.00.");
        System.out.println("  Expected final balance: $0.00");
        System.out.println();

        final int NUM_EXPERIMENTS = 10;
        final double DEBIT_AMOUNT = 500.0;
        final double INITIAL_BALANCE = 1000.0;

        int allCorrect = 0;

        for (int exp = 0; exp < NUM_EXPERIMENTS; exp++) {
            final SafeBankAccount account = new SafeBankAccount(INITIAL_BALANCE);

            Thread[] threads = new Thread[2];
            for (int i = 0; i < 2; i++) {
                final int threadId = i;
                threads[i] = new Thread(() -> {
                    boolean ok = account.debit(DEBIT_AMOUNT);
                    if (!ok) {
                        System.out.println("  Experiment " + (exp + 1)
                            + ": Thread-" + threadId + " FAILED (insufficient funds)");
                    }
                }, "SafeDebit-" + i);
            }

            for (Thread t : threads) t.start();
            for (Thread t : threads) t.join();

            double finalBalance = account.getBalance();
            double expectedBalance = INITIAL_BALANCE - (2 * DEBIT_AMOUNT);

            if (Math.abs(finalBalance - expectedBalance) < 0.01) {
                allCorrect++;
            } else {
                System.out.println("  Experiment " + (exp + 1) + ": WRONG! Got $"
                    + String.format("%.2f", finalBalance) + " (expected $0.00)");
            }
        }

        System.out.println();
        System.out.println("  Summary over " + NUM_EXPERIMENTS + " experiments:");
        System.out.println("    Correct: " + allCorrect + "/" + NUM_EXPERIMENTS);
        System.out.println();

        if (allCorrect == NUM_EXPERIMENTS) {
            System.out.println("  [Result: PERFECT — synchronized eliminated all race conditions]");
            System.out.println();
            System.out.println("  HOW synchronized FIXED IT:");
            System.out.println("    1. Thread A enters debit(): acquires lock on account");
            System.out.println("    2. Thread B tries to enter debit(): BLOCKED (lock held by A)");
            System.out.println("    3. Thread A: reads balance=1000, writes balance=500, exits");
            System.out.println("    4. Thread A's UNLOCK happens-before Thread B's LOCK (Rule 2)");
            System.out.println("    5. Thread B enters: reads balance=500, writes balance=0, exits");
            System.out.println("    6. Final balance = $0.00 — correct!");
            System.out.println();
            System.out.println("  The happens-before relationship between the synchronized");
            System.out.println("  blocks guarantees that B sees A's write to 'balance'.");
        } else {
            System.out.println("  [Result: FAILURE — should NEVER happen with synchronized]");
        }
    }

    // ============================================================
    // DEMO C: Atomic Bank Account — lock-free thread safety
    // ============================================================
    private static void demoCAtomicAccount() throws InterruptedException {
        System.out.println("\n--- DEMO C: Atomic Bank Account (Lock-Free CAS) ---");
        System.out.println("  Same scenario, but using AtomicLong with CAS (Compare-And-Swap).");
        System.out.println("  No locks, no synchronized — but still thread-safe.");
        System.out.println();

        final int NUM_THREADS = 10;
        final double DEBIT_AMOUNT = 100.0;
        final double INITIAL_BALANCE = 1000.0;

        AtomicBankAccount account = new AtomicBankAccount(INITIAL_BALANCE);
        Thread[] threads = new Thread[NUM_THREADS];

        for (int i = 0; i < NUM_THREADS; i++) {
            threads[i] = new Thread(() -> {
                boolean ok = account.debit(DEBIT_AMOUNT);
                if (!ok) {
                    System.out.println("  Thread " + Thread.currentThread().getName()
                        + " FAILED — insufficient funds");
                }
            }, "AtomicDebit-" + i);
            threads[i].start();
        }

        for (Thread t : threads) t.join();

        double finalBalance   = account.getBalance();
        double expectedBalance = INITIAL_BALANCE - (NUM_THREADS * DEBIT_AMOUNT);

        System.out.println();
        System.out.println("  Expected: $" + String.format("%.2f", expectedBalance));
        System.out.println("  Actual:   $" + String.format("%.2f", finalBalance));
        System.out.println();

        if (Math.abs(finalBalance - expectedBalance) < 0.01) {
            System.out.println("  [Result: PERFECT — AtomicLong CAS eliminated race condition]");
            System.out.println();
            System.out.println("  HOW CAS WORKS (Compare-And-Swap):");
            System.out.println("    Thread A: read balance=1000");
            System.out.println("    Thread B: read balance=1000  ← (same value as A)");
            System.out.println("    Thread A: CAS(1000, 900) → SUCCEEDS, balance=900");
            System.out.println("    Thread B: CAS(1000, 900) → FAILS (balance changed to 900!)");
            System.out.println("               → Thread B retries: read balance=900");
            System.out.println("               → Thread B: CAS(900, 800) → SUCCEEDS");
            System.out.println("    Final balance: $800 — CORRECT!");
            System.out.println();
            System.out.println("  CAS vs synchronized:");
            System.out.println("    synchronized: blocks threads, forces them to wait");
            System.out.println("    CAS: threads attempt the operation, retry if it fails");
            System.out.println("    CAS wins at low contention; synchronized wins at high contention");
            System.out.println("    Both provide happens-before guarantees (via different mechanisms)");
        } else {
            System.out.println("  [Result: WRONG — AtomicLong should prevent this]");
        }
    }

    // ============================================================
    // DEMO D: JMM Formal Analysis — why data race = undefined
    // ============================================================
    private static void demoDJMMLegalOutcomes() {
        System.out.println("\n--- DEMO D: JMM Formal — Why Data Race = Undefined Behavior ---");
        System.out.println();

        System.out.println(
            "The Java Memory Model (JLS 17.4) formally defines:\n" +
            "\n" +
            "  'A program is DATA RACE-FREE if all accesses to the same\n" +
            "   shared variable are ordered by happens-before.'\n" +
            "\n" +
            "  'If a program contains a data race, the JMM allows\n" +
            "   ALL possible outcomes, including no outcomes.'\n" +
            "\n" +
            "For our Bank Account with two concurrent debits:\n" +
            "\n" +
            "  Shared variable: 'balance'\n" +
            "  Thread A: balance = balance - 500\n" +
            "  Thread B: balance = balance - 500\n" +
            "\n" +
            "There is NO happens-before between Thread A and Thread B's accesses.\n" +
            "\n" +
            "Therefore, the JMM allows:\n" +
            "  • balance = 0   (A before B, or B before A) — correct\n" +
            "  • balance = 500 (both read 1000, second write wins) — lost update\n" +
            "  • balance = 1000 (both writes lost? — theoretically allowed!)\n" +
            "\n" +
            "The fact that we often see $500 in practice is NOT a guarantee.\n" +
            "It's a reflection of x86's strong memory model, which happens\n" +
            "to make some outcomes more likely than others — but NOT guaranteed.\n"
        );

        System.out.println("  [Conclusion: Any concurrent write to shared mutable state");
        System.out.println("   without happens-before = undefined behavior. ALWAYS synchronize.]");
    }

    // ============================================================
    // MAIN
    // ============================================================
    public static void main(String[] args) throws InterruptedException {
        System.out.println();
        System.out.println("=".repeat(70));
        System.out.println("  RACE CONDITION — DATA RACE vs SYNCHRONIZED vs ATOMIC");
        System.out.println("=".repeat(70));
        System.out.println();
        System.out.println(
            "A DATA RACE exists when two threads access the same shared variable,\n" +
            "at least one access is a write, and there is NO happens-before\n" +
            "relationship between those accesses.\n" +
            "\n" +
            "A program with a data race has UNDEFINED BEHAVIOR under the JMM.\n" +
            "It might appear to work on your machine. It might fail in production.\n" +
            "It might fail only on ARM, only under load, only on a Tuesday.\n" +
            "\n" +
            "The fix: establish a happens-before relationship.\n" +
            "  • synchronized blocks — mutual exclusion + happens-before\n" +
            "  • AtomicXxx classes — lock-free CAS with happens-before\n" +
            "  • volatile fields — happens-before for simple reads/writes\n"
        );

        demoAUnsafeAccount();
        System.out.println();
        demoBSafeAccount();
        System.out.println();
        demoCAtomicAccount();
        demoDJMMLegalOutcomes();

        System.out.println();
        System.out.println("=".repeat(70));
        System.out.println("  RACE CONDITION SUMMARY");
        System.out.println("=".repeat(70));
        System.out.println();
        System.out.println("  DATA RACE (JMM definition):");
        System.out.println("    Two accesses to the same variable, at least one a write,");
        System.out.println("    with NO happens-before relationship.");
        System.out.println("    → UNDEFINED BEHAVIOR — anything can happen.");
        System.out.println();
        System.out.println("  Three ways to fix it:");
        System.out.println("    1. synchronized: mutual exclusion + happens-before");
        System.out.println("       Use when: multiple threads write, critical sections are short");
        System.out.println();
        System.out.println("    2. AtomicXxx (CAS): lock-free, retry-based");
        System.out.println("       Use when: single variable, low-to-medium contention");
        System.out.println();
        System.out.println("    3. Immutable objects: no writes = no race");
        System.out.println("       Use when: design allows it (transaction records, value objects)");
        System.out.println();
        System.out.println("  Remember:");
        System.out.println("    • synchronized is NOT just about mutual exclusion");
        System.out.println("    • It's also about VISIBILITY — ensuring writes by thread A");
        System.out.println("      are visible to thread B when B acquires the same lock");
        System.out.println("    • This visibility guarantee is formalized as happens-before");
        System.out.println("=".repeat(70));
    }
}
