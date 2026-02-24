# Chapter 8, Section 3: Unreliable Clocks — Complete Index

## 📑 Documentation

| File | Purpose | Read Time |
|------|---------|-----------|
| [QUICKSTART.md](QUICKSTART.md) | 5-minute quick start guide | 5 min |
| [README.md](README.md) | Overview and learning objectives | 10 min |
| [TEACHING_GUIDE.md](TEACHING_GUIDE.md) | Deep explanations and best practices | 30 min |
| [PACKAGE_SUMMARY.md](PACKAGE_SUMMARY.md) | Complete package overview | 10 min |

## 💻 Code Exercises

| # | File | Topic | Time | Difficulty |
|---|------|-------|------|------------|
| 1 | [01_clock_skew.py](01_clock_skew.py) | Clock skew & LWW | 30 min | ⭐ Easy |
| 2 | [02_monotonic_vs_wall_clock.py](02_monotonic_vs_wall_clock.py) | Clock types | 30 min | ⭐ Easy |
| 3 | [03_process_pauses.py](03_process_pauses.py) | Zombie writes | 40 min | ⭐⭐ Medium |
| 4 | [04_fencing_tokens.py](04_fencing_tokens.py) | Fencing tokens | 40 min | ⭐⭐ Medium |

**Total Time:** ~2.5 hours

## 🎯 Quick Navigation

### I want to...

**...understand the concepts quickly**
→ Read [QUICKSTART.md](QUICKSTART.md) (5 min)

**...see the problems in action**
→ Run `python 01_clock_skew.py` and `python 03_process_pauses.py`

**...learn deeply**
→ Read [TEACHING_GUIDE.md](TEACHING_GUIDE.md) (30 min)

**...prepare for interviews**
→ Read [TEACHING_GUIDE.md](TEACHING_GUIDE.md) section 8 (Interview Questions)

**...teach others**
→ Use [PACKAGE_SUMMARY.md](PACKAGE_SUMMARY.md) section "Teaching Tips"

**...modify and experiment**
→ Start with any exercise and modify the code

## 📊 Content Overview

### Exercise 1: Clock Skew
- **Problem**: Different machines' clocks disagree
- **Impact**: Silent data loss with Last-Write-Wins
- **Solution**: Google Spanner's TrueTime (expensive)
- **Key Insight**: Even 1ms of clock skew can cause data loss

### Exercise 2: Clock Types
- **Wall-Clock Time**: Can jump backward, comparable across machines
- **Monotonic Clocks**: Always move forward, not comparable
- **Key Insight**: Use the right clock for the right job

### Exercise 3: Process Pauses
- **Problem**: Processes can pause (GC, VM suspension)
- **Impact**: Zombie writes with expired leases
- **Solution**: Lease checks and fencing tokens
- **Key Insight**: A paused process doesn't know it was paused

### Exercise 4: Fencing Tokens
- **Solution**: Monotonically increasing tokens with each lease
- **How It Works**: Storage rejects writes with stale tokens
- **Impact**: Prevents zombie writes completely
- **Key Insight**: Practical solution with reasonable complexity

## 🔑 Key Concepts

```
Clock Skew
  ↓
Last-Write-Wins Breaks
  ↓
Need Reliable Ordering
  ↓
Monotonic Clocks (per-machine)
  ↓
Process Pauses
  ↓
Zombie Writes
  ↓
Fencing Tokens (solution)
```

## ✅ Learning Checklist

- [ ] Understand clock skew and its impact
- [ ] Know the difference between wall-clock and monotonic time
- [ ] Understand process pauses and zombie writes
- [ ] Know how fencing tokens prevent zombie writes
- [ ] Can explain these concepts to others
- [ ] Can answer interview questions
- [ ] Can apply these concepts to your own systems

## 🚀 Getting Started

### Option 1: Quick Start (15 minutes)
```bash
cat QUICKSTART.md
python 01_clock_skew.py
```

### Option 2: Full Learning (3 hours)
```bash
cat README.md
python 01_clock_skew.py
python 02_monotonic_vs_wall_clock.py
python 03_process_pauses.py
python 04_fencing_tokens.py
cat TEACHING_GUIDE.md
```

### Option 3: Deep Dive (4 hours)
```bash
cat PACKAGE_SUMMARY.md
# Run all exercises
python 01_clock_skew.py
python 02_monotonic_vs_wall_clock.py
python 03_process_pauses.py
python 04_fencing_tokens.py
# Read all documentation
cat README.md
cat TEACHING_GUIDE.md
# Modify and experiment with the code
```

## 📚 Related Sections

- **Section 1**: Faults and Partial Failures
- **Section 2**: Unreliable Networks
- **Section 3**: Unreliable Clocks ← **You are here**
- **Section 4**: Knowledge, Truth, and Lies

## 🎓 Learning Outcomes

After completing this section, you will:

1. ✅ Understand why clocks are unreliable in distributed systems
2. ✅ Know the dangers of clock-based ordering
3. ✅ Understand process pauses and their impact
4. ✅ Know how to prevent zombie writes
5. ✅ Be able to apply these concepts to real systems

## 📖 Further Reading

- DDIA Chapter 8: "The Trouble with Distributed Systems"
- Google Spanner paper
- Lamport's "Time, Clocks, and the Ordering of Events"
- Vector Clocks paper

---

**Start with [QUICKSTART.md](QUICKSTART.md) or run `python 01_clock_skew.py`!** 🚀
