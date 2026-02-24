# Quick Start: Chapter 8, Section 3 — Unreliable Clocks

## 🚀 Get Started in 5 Minutes

### What You'll Learn

This section teaches you why clocks are unreliable in distributed systems and how to handle them:

1. **Clock Skew** — Different machines' clocks disagree, breaking Last-Write-Wins
2. **Clock Types** — Wall-clock vs monotonic clocks and when to use each
3. **Process Pauses** — GC and VM suspension cause zombie writes
4. **Fencing Tokens** — The solution to prevent zombie writes

### Run the Exercises

```bash
# Exercise 1: See how clock skew breaks Last-Write-Wins
python 01_clock_skew.py

# Exercise 2: Understand monotonic vs wall-clock time
python 02_monotonic_vs_wall_clock.py

# Exercise 3: Experience the zombie write problem
python 03_process_pauses.py

# Exercise 4: Learn how fencing tokens prevent zombie writes
python 04_fencing_tokens.py
```

### Key Insights

**Exercise 1 — Clock Skew:**
- Even 1ms of clock skew can cause silent data loss
- Last-Write-Wins with physical timestamps is fundamentally broken
- Google Spanner's TrueTime is the only reliable solution (and very expensive)

**Exercise 2 — Clock Types:**
- Use **monotonic clocks** for measuring durations (they never jump backward)
- Use **wall-clock time** for logging timestamps (but not for ordering events)
- Never compare monotonic clock values across machines

**Exercise 3 — Process Pauses:**
- Java/Go processes can freeze for hundreds of milliseconds during GC
- VMs can be suspended for live migration
- A paused process doesn't know it was paused and may act on stale state

**Exercise 4 — Fencing Tokens:**
- Fencing tokens are monotonically increasing numbers issued with each lease
- Storage service rejects writes with stale tokens
- Prevents zombie writes even if a process pauses and resumes

### Common Mistakes to Avoid

❌ **Don't:** Use wall-clock timestamps to order events across machines
✅ **Do:** Use logical clocks, fencing tokens, or consensus algorithms

❌ **Don't:** Measure durations using wall-clock time
✅ **Do:** Use monotonic clocks for measuring durations

❌ **Don't:** Assume leases are always valid
✅ **Do:** Check fencing tokens before writing

❌ **Don't:** Rely on timeouts to detect dead processes
✅ **Do:** Use heartbeats with fencing tokens or quorum-based approaches

### Next Steps

1. Run all 4 exercises to understand the concepts
2. Read the TEACHING_GUIDE.md for deep explanations
3. Try modifying the code to experiment with different scenarios
4. Move on to Section 4: Knowledge, Truth, and Lies (Quorums & Byzantine Faults)

### Files in This Section

| File | Purpose |
|------|---------|
| `README.md` | Overview and learning objectives |
| `QUICKSTART.md` | This file — quick start guide |
| `TEACHING_GUIDE.md` | Deep explanations and best practices |
| `01_clock_skew.py` | Demonstrates clock skew and LWW issues |
| `02_monotonic_vs_wall_clock.py` | Compares clock types |
| `03_process_pauses.py` | Simulates GC pauses and lease expiry |
| `04_fencing_tokens.py` | Demonstrates fencing token solution |

---

**Ready to start?** Run `python 01_clock_skew.py` now! 🚀
