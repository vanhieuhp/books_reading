package phase_jmm;

/**
 * ============================================================
 * HARDWARE MEMORY ARCHITECTURE — Why the JMM exists
 * ============================================================
 *
 * This file does NOT run anything — it is a visual walkthrough
 * of what actually happens inside modern multi-core hardware.
 *
 * Modern multi-core CPUs do NOT read and write directly to main RAM.
 * Every core has its own cache hierarchy. This creates three fundamental
 * problems that the Java Memory Model was designed to solve:
 *
 *   PROBLEM 1: VISIBILITY   — Thread A writes to shared variable,
 *                               Thread B never sees it (stale cache)
 *
 *   PROBLEM 2: REORDERING    — CPU/compiler reorders operations for
 *                               performance, breaking program semantics
 *
 *   PROBLEM 3: PARTIAL PUBLICATION — A thread sees a partially
 *                               constructed object (half-written fields)
 *
 * HARDWARE MEMORY HIERARCHY:
 * ==========================
 *
 *   ┌──────────────────────────────────────────────────────────────┐
 *   │                         CPU CORE 0                           │
 *   │  ┌─────────────┐  ┌─────────────┐  ┌──────────────────────┐  │
 *   │  │  Registers  │  │  L1 Cache   │  │      L2 Cache        │  │
 *   │  │  (~1ns)      │  │  (~64KB)    │  │      (~256KB–2MB)    │  │
 *   │  │  fastest     │  │  ~1–3ns     │  │      ~3–10ns        │  │
 *   │  └─────────────┘  └─────────────┘  └──────────────────────┘  │
 *   └──────────────────────────────────────────────────────────────┘
 *                              │
 *   ┌──────────────────────────────────────────────────────────────┐
 *   │                         CPU CORE 1                           │
 *   │  ┌─────────────┐  ┌─────────────┐  ┌──────────────────────┐  │
 *   │  │  Registers  │  │  L1 Cache   │  │      L2 Cache        │  │
 *   │  └─────────────┘  └─────────────┘  └──────────────────────┘  │
 *   └──────────────────────────────────────────────────────────────┘
 *                              │
 *   ┌──────────────────────────────────────────────────────────────┐
 *   │                    L3 Cache (SHARED)                          │
 *   │                    (~8–64MB, ~10–20ns)                        │
 *   │                    All cores share this cache                 │
 *   └──────────────────────────────────────────────────────────────┘
 *                              │
 *                              ▼
 *   ┌──────────────────────────────────────────────────────────────┐
 *   │                    Main Memory (RAM)                           │
 *   │                    (~16–256GB, ~80–100ns latency)            │
 *   │                    Shared by all cores                        │
 *   └──────────────────────────────────────────────────────────────┘
 *
 *
 * THE THREE PROBLEMS IN DETAIL:
 * =============================
 *
 * ------------------------------------------------------------------
 * PROBLEM 1 — VISIBILITY (Stale Reads)
 * ------------------------------------------------------------------
 *
 *   Thread A (Core 0)          Thread B (Core 1)
 *   ─────────────────          ─────────────────
 *   Writes x = 42
 *   (goes into Core 0 L1)
 *                              Reads x
 *                              (Core 1 L1 has OLD value 0)
 *                              → B sees 0, not 42!
 *
 *   This is NOT visible to Thread B until the cache line is flushed
 *   to main RAM AND Core 1's cache invalidates and reloads.
 *   This can take thousands of CPU cycles.
 *
 *   RESULT: Without JMM guarantees, a write in Thread A may never
 *           be seen by Thread B — even after Thread A "finishes".
 *
 * ------------------------------------------------------------------
 * PROBLEM 2 — INSTRUCTION REORDERING
 * ------------------------------------------------------------------
 *
 *   The JIT compiler AND the CPU hardware may REORDER memory operations
 *   for performance, as long as single-threaded behavior is preserved.
 *
 *   Consider this code:
 *
 *     Writer Thread:
 *       1. number = 42;      // write A
 *       2. ready = true;     // write B
 *
 *   The JIT or CPU might reorder to:
 *       1. ready = true;     // write B  ← reordered!
 *       2. number = 42;      // write A
 *
 *   Why? If writes are to different memory locations (different cache
 *   lines), the CPU can issue them out of order to minimize stalls.
 *
 *   Reader Thread (running concurrently):
 *       while (!ready) { }    // spins until ready == true
 *       print(number);        // reads 42
 *
 *   If reordering happened on the writer:
 *     → Reader sees ready=true and exits the loop
 *     → But number might still be 0 (the old value) because that
 *       write hasn't propagated yet!
 *
 *   This is NOT a bug in the CPU — it's allowed as long as
 *   single-threaded execution is correct. But it BREAKS multi-threaded
 *   code that relies on program order between threads.
 *
 *   JMM RULE that fixes this:
 *     volatile write to 'ready' happens-before volatile read of 'ready'
 *     → The JMM guarantees the write to 'number' is visible before/with
 *       the write to 'ready' (transitivity of happens-before)
 *
 * ------------------------------------------------------------------
 * PROBLEM 3 — PARTIAL CONSTRUCTION (Escape of 'this')
 * ------------------------------------------------------------------
 *
 *   When you write:
 *       instance = new Singleton();
 *
 *   This compiles to THREE separate CPU operations:
 *     1. Allocate memory for Singleton object
 *     2. Call constructor (write fields: x=0, y=0, etc.)
 *     3. Write reference to 'instance' variable
 *
 *   The CPU may reorder steps 2 and 3:
 *     1. Allocate memory
 *     3. Write reference to 'instance'     ← happens EARLY!
 *     2. Call constructor                  ← happens LATE
 *
 *   If another thread reads 'instance' after step 3 but during step 2,
 *   it sees a PARTIALLY CONSTRUCTED object with default field values!
 *
 *   JMM RULE that fixes this:
 *     Final fields: the JMM guarantees that all final field writes
 *     in the constructor happen-before the reference to the object
 *     escapes to any other thread (JLS 17.5).
 *     → BUT: do NOT assign 'this' to a shared variable inside the
 *       constructor — that breaks the guarantee.
 *
 *
 * HOW THE JMM SOLVES THESE PROBLEMS:
 * ==================================
 *
 * The JMM defines "happens-before" relationships — mathematical ordering
 * rules that guarantee visibility of writes between threads.
 *
 * Key happens-before rules:
 *
 *   1. PROGRAM ORDER within same thread:
 *      Every action in a thread happens-before the next action in program order
 *
 *   2. MONITOR LOCK:
 *      Unlock of monitor M happens-before every subsequent lock of M
 *
 *   3. VOLATILE:
 *      Write to volatile V happens-before every subsequent read of V
 *
 *   4. THREAD START:
 *      Thread.start() happens-before the first action in the started thread
 *
 *   5. THREAD JOIN:
 *      All actions in Thread T happen-before Thread.join() returns
 *
 *   6. TRANSITIVITY:
 *      If A happens-before B, and B happens-before C,
 *      then A happens-before C
 *
 * If there is NO happens-before relationship between two actions,
 * the JMM allows ANY possible outcome — including wrong ones.
 *
 * This is why every non-synchronized concurrent program is technically
 * undefined behavior at the JMM level — even if it usually "works."
 *
 */
public class HardwareMemoryArchitecture {

    // This class is documentation only — run Visualization.java to see diagrams
    public static void main(String[] args) {
        System.out.println("This file is documentation — run Visualization.java to see diagrams");
    }
}
