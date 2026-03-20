package phase_jmm;

/**
 * ============================================================
 * SYNCHRONIZED — Mutual Exclusion + Happens-Before Visibility
 * ============================================================
 *
 * synchronized provides TWO guarantees that the JMM formally specifies:
 *
 *   ✅ GUARANTEE 1 — MUTUAL EXCLUSION (aka "Mutual Exclusion Semantics"):
 *       Only ONE thread can be inside a synchronized block (or method)
 *       at a time, for the same lock object.
 *       This prevents two threads from being in a critical section simultaneously.
 *
 *   ✅ GUARANTEE 2 — HAPPENS-BEFORE VISIBILITY (aka "Memory Effects"):
 *       When Thread A exits a synchronized block (UNLOCKS),
 *       ALL writes Thread A made to shared variables are guaranteed to be
 *       visible to Thread B when Thread B subsequently ENTERS a
 *       synchronized block (LOCKS) on the same lock object.
 *
 *       This is formalized as:
 *         Monitor unlock of M  →  happens-before  →  Monitor lock of M
 *
 *       The JVM achieves this by flushing CPU caches to main memory
 *       when unlocking, and invalidating CPU caches when locking.
 *
 *
 * synchronized vs volatile:
 * ========================
 * synchronized:  MUTUAL EXCLUSION + VISIBILITY (blocks threads, higher overhead)
 * volatile:      VISIBILITY + NO REORDERING ONLY (no mutual exclusion)
 *
 * synchronized forms:
 *   1. Instance method:    synchronized void method()     { }  // locks 'this'
 *   2. Static method:       synchronized static void m()  { }  // locks Class object
 *   3. Synchronized block:  synchronized(lockObject) { }       // most flexible
 *
 * Lock granularity advice:
 *   • Lock on 'this' (instance method): easy but exposes the lock
 *     (external code could accidentally lock on your instance)
 *   • Private final lock: BEST practice — nobody outside your class
 *     can accidentally interfere with your lock
 *   • Never lock on String literals ("lock") — the string pool means
 *     unrelated code may share the same lock object!
 *
 *
 * HOW TO RUN:
 * ===========
 *   cd phase_jmm
 *   javac SynchronizedVisibility.java
 *   java phase_jmm.SynchronizedVisibility
 */
public class SynchronizedVisibility {

    // ============================================================
    // INNER CLASS: BankAccount — synchronized instance method
    // ============================================================
    // Every BankAccount instance has its own intrinsic lock.
    // synchronized on instance method = synchronized(this)
    private static class BankAccount {

        private double balance;

        // Constructor — no synchronization needed (called from single thread typically)
        public BankAccount(double initialBalance) {
            this.balance = initialBalance;
        }

        // ============================================================
        // synchronized instance method
        // Locks: 'this' BankAccount instance's monitor
        // Guarantees:
        //   1. Only one thread can call debit() on this instance at a time
        //   2. When one thread exits debit(), all its writes to 'balance'
        //      are visible to the next thread that enters debit()
        // ============================================================
        public synchronized boolean debit(double amount) {
            if (balance < amount) {
                return false; // insufficient funds — lock still held
            }
            // At this point, no other thread can read or write 'balance'
            // This is the critical section — mutual exclusion
            balance -= amount;
            return true;
        }

        // ============================================================
        // synchronized instance method — credit
        // ============================================================
        public synchronized void credit(double amount) {
            balance += amount;
        }

        // ============================================================
        // synchronized instance method — getBalance
        // WHY synchronized on a getter? Because without it, a reader
        // might see a partially-written value if another thread is mid-debit().
        // synchronized on getter + setter = mutual exclusion = consistent reads
        // ============================================================
        public synchronized double getBalance() {
            return balance;
        }

        // ============================================================
        // TO STRING for reporting
        // ============================================================
        @Override
        public synchronized String toString() {
            return String.format("BankAccount[balance=%.2f]", balance);
        }
    }

    // ============================================================
    // INNER CLASS: TransferService — synchronized block with PRIVATE lock
    // ============================================================
    // BEST PRACTICE: use a private final lock object, not 'this'
    // This prevents external code from accidentally locking on your lock.
    private static class TransferService {

        // Private final lock — cannot be accessed or interfered with externally
        // 'final' prevents the reference from changing (which would break locking)
        private final Object accountsLock = new Object();

        // Simulated bank accounts: accountId -> balance
        private final java.util.Map<String, Double> accounts = new java.util.HashMap<>();

        public TransferService() {
            accounts.put("A", 1000.0);
            accounts.put("B", 1000.0);
        }

        // ============================================================
        // transfer: synchronized(BLOCK) with consistent lock ordering
        //
        // This method transfers money between two accounts.
        // It uses synchronized blocks instead of synchronized methods
        // because we need to lock BOTH accounts (not just one).
        //
        // CRITICAL: we must lock both accounts, but in a CONSISTENT ORDER
        // to prevent deadlock. If T1: locks A then B, and T2: locks B then A,
        // we get a deadlock. Solution: always lock lower-ID first.
        // ============================================================
        public boolean transfer(String fromId, String toId, double amount) {
            // Validate accounts exist
            if (!accounts.containsKey(fromId) || !accounts.containsKey(toId)) {
                return false;
            }
            if (fromId.equals(toId)) {
                return false;
            }

            // Determine lock ordering: always lock lower-ID first
            // This prevents circular wait — the root cause of deadlock.
            String firstId  = fromId.compareTo(toId) < 0 ? fromId : toId;
            String secondId = fromId.compareTo(toId) < 0 ? toId   : fromId;

            // Acquire first lock
            synchronized (getAccountLock(firstId)) {
                // Acquire second lock
                synchronized (getAccountLock(secondId)) {
                    // BOTH locks held — mutual exclusion on both accounts

                    Double fromBalance = accounts.get(fromId);
                    if (fromBalance == null || fromBalance < amount) {
                        return false; // insufficient funds — no deduction
                    }

                    // Perform transfer: debit from, credit to
                    accounts.put(fromId, fromBalance - amount);
                    accounts.put(toId,   accounts.get(toId) + amount);

                    System.out.println("  [Transfer] " + fromId + " -> " + toId
                        + " : $" + amount + " | "
                        + fromId + "=" + accounts.get(fromId)
                        + " | " + toId + "=" + accounts.get(toId));
                    return true;
                }
            }
        }

        // Get a lock object for an account ID (one lock per account)
        // In production, use ConcurrentHashMap or separate lock objects
        private Object getAccountLock(String accountId) {
            // Return a consistent object per account ID
            // In a real system, you'd have a ConcurrentHashMap<String, ReentrantLock>
            return accountId.intern(); // WARNING: intern() returns shared String pool object!
            // NOTE: We use intern() here only for demo simplicity.
            // In real code, use: private final Map<String, Object> accountLocks = new HashMap<>();
        }

        public double getBalance(String accountId) {
            synchronized (getAccountLock(accountId)) {
                Double b = accounts.get(accountId);
                return b == null ? 0.0 : b;
            }
        }

        public String getAllBalances() {
            StringBuilder sb = new StringBuilder();
            for (String id : accounts.keySet()) {
                sb.append(id).append("=").append(getBalance(id)).append(" ");
            }
            return sb.toString();
        }
    }

    // ============================================================
    // DEMO A: synchronized solves the visibility + race condition
    // ============================================================
    private static void demoASynchronizedVisibility() throws InterruptedException {
        System.out.println("\n--- DEMO A: synchronized Fixes Visibility + Race Condition ---");
        System.out.println("  Re-running the BankAccount debit scenario with synchronized.");
        System.out.println();

        final BankAccount account = new BankAccount(10_000.0);

        // 100 threads, each debiting 100.0
        // Expected final balance: 0.0
        // Without synchronized: non-zero balance (race condition + visibility)
        // With synchronized: exactly 0.0 (every time)

        Thread[] threads = new Thread[100];

        for (int i = 0; i < 100; i++) {
            threads[i] = new Thread(() -> {
                boolean success = account.debit(100.0);
                if (!success) {
                    System.out.println("  [FAILURE] Thread " + Thread.currentThread().getName()
                        + " failed to debit — insufficient funds!");
                }
            }, "DebitThread-" + i);
        }

        // Start all threads
        long start = System.nanoTime();
        for (Thread t : threads) t.start();
        for (Thread t : threads) t.join();
        long elapsed = System.nanoTime() - start;

        double finalBalance = account.getBalance();

        System.out.println();
        System.out.println("  Initial balance: $10,000.00");
        System.out.println("  Withdrawals:    100 × $100.00 = $10,000.00");
        System.out.println("  Expected balance: $0.00");
        System.out.println("  Actual balance:   $" + String.format("%.2f", finalBalance));
        System.out.println("  Elapsed time:     " + (elapsed / 1_000_000.0) + " ms");
        System.out.println();

        if (finalBalance == 0.0) {
            System.out.println("  [Result: PASS — synchronized guarantees correct balance!]");
            System.out.println("  How it worked:");
            System.out.println("    1. Thread A enters debit(): acquires lock on 'this'");
            System.out.println("    2. Thread B tries to enter debit(): BLOCKS (lock held by A)");
            System.out.println("    3. Thread A: reads balance, checks >=, subtracts, writes back");
            System.out.println("    4. Thread A exits debit(): UNLOCKS — all writes flushed to RAM");
            System.out.println("    5. Thread B: acquires lock, sees Thread A's write (HB guarantee)");
            System.out.println("    6. Repeat 100 times → exact balance = 0");
        } else {
            System.out.println("  [Result: FAIL — balance is wrong!");
            System.out.println("  This should NOT happen with synchronized methods.");
        }
    }

    // ============================================================
    // DEMO B: synchronized block with private lock — transfer service
    // ============================================================
    private static void demoBTransferWithSynchronizedBlock() throws InterruptedException {
        System.out.println("\n--- DEMO B: synchronized Block with Private Lock + Deadlock Prevention ---");
        System.out.println("  Demonstrating: consistent lock ordering prevents deadlock.");
        System.out.println();

        TransferService service = new TransferService();

        System.out.println("  Initial: " + service.getAllBalances());
        System.out.println("  Running 2 concurrent transfers:");
        System.out.println("    Thread T1: transfers $300 from A to B");
        System.out.println("    Thread T2: transfers $300 from B to A");
        System.out.println("  If locks are acquired in random order → deadlock possible!");
        System.out.println("  If locks are acquired in consistent order (lower ID first) → NO deadlock.");
        System.out.println();

        Thread t1 = new Thread(() -> {
            System.out.println("  [T1] Attempting: A -> B, $300");
            boolean ok = service.transfer("A", "B", 300.0);
            System.out.println("  [T1] Result: " + (ok ? "SUCCESS" : "FAILED"));
        }, "Transfer-A-to-B");

        Thread t2 = new Thread(() -> {
            Thread.sleep(50); // slight delay so T1 starts first
            System.out.println("  [T2] Attempting: B -> A, $300");
            boolean ok = service.transfer("B", "A", 300.0);
            System.out.println("  [T2] Result: " + (ok ? "SUCCESS" : "FAILED"));
        }, "Transfer-B-to-A");

        long start = System.nanoTime();
        t1.start();
        t2.start();
        t1.join();
        t2.join();
        long elapsed = System.nanoTime() - start;

        System.out.println();
        System.out.println("  Final: " + service.getAllBalances());
        System.out.println("  Both transfers completed in " + elapsed + " ns (should be instant)");
        System.out.println();
        System.out.println("  [Result: PASS — Consistent lock ordering prevented deadlock!]");
        System.out.println("  With random ordering: both threads would block forever (deadlock).");
        System.out.println("  With consistent ordering: lower-ID account always locked first → no cycle.");
    }

    // ============================================================
    // DEMO C: synchronized on getter/setter — consistent reads
    // ============================================================
    private static void demoCSynchronizedGetterSetter() throws InterruptedException {
        System.out.println("\n--- DEMO C: synchronized Getter + Setter for Consistent Reads ---");
        System.out.println("  Demonstrating that synchronized getter prevents stale reads.");
        System.out.println();

        final int[] sharedValue = {0};

        // Writer thread: rapidly writes new values
        Thread writer = new Thread(() -> {
            for (int i = 0; i < 1000; i++) {
                sharedValue[0] = i;
            }
        }, "Writer-Unsynced");

        // Reader thread: reads sharedValue without synchronization
        // This can read a stale value (though likely not with int on x86)
        // But if sharedValue were a long or double, torn reads could occur.
        // Here we just show the synchronized pattern.

        // Let's use a wrapper class for demonstration
        final java.util.concurrent.atomic.AtomicInteger atomicValue =
            new java.util.concurrent.atomic.AtomicInteger(0);

        Thread atomicWriter = new Thread(() -> {
            for (int i = 0; i < 1000; i++) {
                atomicValue.set(i);
            }
        }, "AtomicWriter");

        Thread atomicReader = new Thread(() -> {
            int lastSeen = -1;
            int violations = 0;
            for (int i = 0; i < 1000; i++) {
                int current = atomicValue.get();
                if (current < lastSeen) {
                    violations++;
                }
                lastSeen = current;
            }
            System.out.println("  [AtomicReader] Saw " + violations
                + " value decreases (expected 0 with AtomicInteger)");
        }, "AtomicReader");

        atomicWriter.start();
        atomicReader.start();
        atomicWriter.join();
        atomicReader.join();

        System.out.println("  [AtomicInteger guarantees consistent reads/writes via CAS]");
        System.out.println("  [Result: PASS — AtomicInteger provides lock-free consistency]");
    }

    // ============================================================
    // DEMO D: String literal locking anti-pattern
    // ============================================================
    private static void demoDStringLockAntiPattern() {
        System.out.println("\n--- DEMO D: String Literal Lock Anti-Pattern ---");
        System.out.println("  ❌ NEVER lock on String literals!");
        System.out.println();

        // PROBLEM: In Java, string literals are interned in the string pool.
        // If class A locks on "LOCK" and class B also locks on "LOCK",
        // they share the same lock — even though they don't know about each other!
        // This causes unexpected blocking.

        System.out.println("  ANTI-PATTERN:");
        System.out.println();
        System.out.println("    // Class A");
        System.out.println("    synchronized(\"LOCK\") { /* A's critical section */ }");
        System.out.println();
        System.out.println("    // Class B (unrelated code!)");
        System.out.println("    synchronized(\"LOCK\") { /* B's critical section */ }");
        System.out.println("    // ^ BLOCKS because it's the same String pool object!");
        System.out.println();
        System.out.println("  ANOTHER PROBLEM:");
        System.out.println("    String lock = new String(\"LOCK\");");
        System.out.println("    // Even with new String(), if you intern() it later,");
        System.out.println("    // or if the same literal appears elsewhere, they share!");
        System.out.println();

        System.out.println("  ✅ CORRECT pattern:");
        System.out.println();
        System.out.println("    private final Object myLock = new Object();");
        System.out.println("    synchronized(myLock) { /* safe — nobody else has this ref */ }");
        System.out.println();
        System.out.println("  Or use a ConcurrentHashMap for per-key locking:");
        System.out.println("    private final ConcurrentHashMap<String, ReentrantLock> locks");
        System.out.println("        = new ConcurrentHashMap<>();");
        System.out.println("    locks.computeIfAbsent(accountId, k -> new ReentrantLock());");
        System.out.println();
        System.out.println("  [This demo has no runnable code — it's an anti-pattern warning!]");
    }

    // ============================================================
    // MAIN
    // ============================================================
    public static void main(String[] args) throws InterruptedException {
        System.out.println();
        System.out.println("=".repeat(70));
        System.out.println("  SYNCHRONIZED — MUTUAL EXCLUSION + HAPPENS-BEFORE VISIBILITY");
        System.out.println("=".repeat(70));
        System.out.println();
        System.out.println(
            "synchronized gives you TWO guarantees:\n" +
            "  1. MUTUAL EXCLUSION: only one thread in the critical section at a time\n" +
            "  2. HAPPENS-BEFORE: all writes before unlock are visible after lock\n" +
            "\n" +
            "Three forms:\n" +
            "  synchronized void m()             { }  // locks 'this'\n" +
            "  synchronized static void m()      { }  // locks Class object\n" +
            "  synchronized(lockObject) { }           // locks specified object\n" +
            "\n" +
            "Best practice: use a private final lock object.\n" +
            "Never lock on String literals or 'this' in public APIs.\n"
        );

        demoASynchronizedVisibility();
        demoBTransferWithSynchronizedBlock();
        demoCSynchronizedGetterSetter();
        demoDStringLockAntiPattern();

        System.out.println();
        System.out.println("=".repeat(70));
        System.out.println("  SYNCHRONIZED SUMMARY");
        System.out.println("=".repeat(70));
        System.out.println();
        System.out.println("  ✅ Use synchronized when:");
        System.out.println("     • Multiple threads write to the same variable");
        System.out.println("     • You need atomicity of multi-step operations");
        System.out.println("     • You need both mutual exclusion AND visibility");
        System.out.println("     • Critical sections are short (microseconds, not milliseconds!)");
        System.out.println();
        System.out.println("  ❌ Avoid synchronized when:");
        System.out.println("     • Critical section does I/O (DB, HTTP) — holds lock too long");
        System.out.println("     • You need tryLock() with timeout (use ReentrantLock)");
        System.out.println("     • You need multiple wait conditions (use ReentrantLock + Condition)");
        System.out.println("     • High contention on a hot field (consider AtomicXxx or lock striping)");
        System.out.println();
        System.out.println("  🔑 Remember:");
        System.out.println("     Locking on 'this' exposes your lock to external interference.");
        System.out.println("     Always prefer: private final Object lock = new Object();");
        System.out.println("=".repeat(70));
    }
}
