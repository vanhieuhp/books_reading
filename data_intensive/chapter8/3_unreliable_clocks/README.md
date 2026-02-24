# Section 3: Unreliable Clocks — Hands-On Exercises

## 🎯 Learning Objectives

By completing these 4 exercises, you will:

1. ✅ **Understand clock skew** and how it breaks Last-Write-Wins (LWW)
2. ✅ **Distinguish between monotonic and wall-clock time** and their use cases
3. ✅ **Experience process pauses** (GC, VM suspension) and their impact on leases
4. ✅ **Implement fencing tokens** — the solution to prevent zombie writes

## 📁 Exercise Files

| # | File | DDIA Concept | Time |
|---|------|-------------|------|
| 1 | `01_clock_skew.py` | Clock skew, LWW data loss | 30 min |
| 2 | `02_monotonic_vs_wall_clock.py` | Time-of-day vs monotonic clocks | 30 min |
| 3 | `03_process_pauses.py` | GC pauses, lease expiry, zombie writes | 40 min |
| 4 | `04_fencing_tokens.py` | Fencing tokens as safeguard | 40 min |

**Total time**: ~2.5 hours

## 🚀 How to Run

```bash
# No dependencies needed! Just run with Python 3.8+

# Exercise 1: Clock skew and LWW disaster
python 01_clock_skew.py

# Exercise 2: Monotonic vs wall-clock time
python 02_monotonic_vs_wall_clock.py

# Exercise 3: Process pauses and lease expiry
python 03_process_pauses.py

# Exercise 4: Fencing tokens solution
python 04_fencing_tokens.py
```

## 🗺️ Mapping to DDIA Chapter 8

```
Exercise 1  →  "Unreliable Clocks" (pp. 106-125)
              "Clock Skew: The Silent Killer" (pp. 125-130)
              "LWW (Last-Write-Wins) Disaster" (pp. 130-145)

Exercise 2  →  "Two Types of Clocks" (pp. 112-124)
              "Time-of-Day Clocks" (pp. 114-117)
              "Monotonic Clocks" (pp. 119-124)

Exercise 3  →  "Process Pauses" (pp. 155-178)
              "Garbage Collection" (pp. 159-160)
              "VM Suspension" (pp. 160-161)
              "Lease Expiry Problem" (pp. 167-178)

Exercise 4  →  "Fencing Tokens" (pp. 180-197)
              "The Solution: Fencing Tokens" (pp. 184-197)
```

## 📊 What You'll See

### Exercise 1 Output Preview:
```
================================================================================
CLOCK SKEW: The Silent Killer
================================================================================

Scenario: Two nodes with clock skew, using Last-Write-Wins

Node A's clock: 10:00:00.100  (5ms FAST)
Node B's clock: 10:00:00.000  (correct)

Write 1: Client writes to Node B at 10:00:00.000
Write 2: Client writes to Node A at 10:00:00.100

With Last-Write-Wins:
  ✅ Write 2 (timestamp 10:00:00.100) WINS
  ❌ Write 1 (timestamp 10:00:00.000) is SILENTLY DELETED

⚠️  DATA LOSS: Write 1 may have actually happened AFTER Write 2 in real time!
    Node A's clock was simply ahead.
```

### Exercise 3 Output Preview:
```
================================================================================
PROCESS PAUSES: The Zombie Write Problem
================================================================================

Thread 1: Acquires lease (expires in 10 seconds)
Thread 1: Begins critical work
Thread 1: --- GC PAUSE FOR 15 SECONDS ---
Thread 1: Resumes, believes it still holds the lease
Thread 1: Attempts to write data

⚠️  PROBLEM: The lease expired 5 seconds ago!
    Thread 2 acquired the lease during Thread 1's pause.
    Both threads think they have exclusive access.

Result: DATA CORRUPTION ❌
```

## 🎓 Key Concepts per Exercise

### Exercise 1: Clock Skew
- Different machines' clocks can differ by milliseconds or more
- NTP synchronization is imperfect
- Last-Write-Wins with physical timestamps is fundamentally broken
- An increment of 1ms in clock skew can cause silent data loss

### Exercise 2: Monotonic vs Wall-Clock Time
- **Wall-clock (time-of-day)**: Returns current date/time, can jump backward
- **Monotonic**: Always moves forward, good for measuring durations
- **Key insight**: Never use wall-clock for ordering events across machines
- **Monotonic clocks are not comparable across machines**

### Exercise 3: Process Pauses
- Java/Go processes can freeze for hundreds of milliseconds during GC
- VMs can be suspended for live migration
- A paused process doesn't know it was paused
- Leases can expire while a process is paused
- A resumed process may act on stale state (zombie writes)

### Exercise 4: Fencing Tokens
- Lock service issues a monotonically increasing token with each lease
- Storage layer checks the token on every write
- Stale tokens are rejected, preventing zombie writes
- Fencing tokens are the practical solution to process pause problems

## 💡 Exercises to Try After Running

1. **Increase clock skew** — change `CLOCK_SKEW_MS` to see how much data loss occurs
2. **Vary GC pause duration** — see how long pauses need to be to cause problems
3. **Add more concurrent writers** — observe how conflicts multiply
4. **Disable fencing tokens** — see what happens without the safeguard

## ✅ Completion Checklist

- [ ] Exercise 1: Understand why LWW with physical timestamps fails
- [ ] Exercise 2: Can explain the difference between monotonic and wall-clock time
- [ ] Exercise 3: Can identify the zombie write problem and its causes
- [ ] Exercise 4: Can explain how fencing tokens prevent zombie writes

## 📚 Next Steps

After completing Section 3:
1. ✅ You understand why clocks are unreliable in distributed systems
2. ✅ You know the dangers of clock-based ordering
3. ✅ You understand process pauses and their impact
4. ✅ Ready for Section 4: Knowledge, Truth, and Lies (Quorums & Byzantine Faults)

---

**Start with `01_clock_skew.py`!** 🚀
