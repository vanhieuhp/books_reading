# Chapter 6, Section 1: Partitioning of Key-Value Data
## Complete Learning Module

### 📁 Files Overview

```
chapter6/1_key_value_partitioning/
├── 01_key_range_partitioning.py    (18 KB) — Exercise 1
├── 02_hash_partitioning.py         (15 KB) — Exercise 2
├── 03_compound_keys.py             (21 KB) — Exercise 3
├── 04_hot_spot_solutions.py        (17 KB) — Exercise 4
├── README.md                        (8.6 KB) — Complete guide
├── QUICKSTART.md                    (7.9 KB) — 5-minute start
├── TEACHING_GUIDE.md                (8.1 KB) — Teaching notes
└── INDEX.md                         (this file)
```

**Total:** ~95 KB of code + documentation

---

## 🚀 Quick Start (Choose One)

### Option 1: Run All Exercises (2 hours)
```bash
python3 01_key_range_partitioning.py
python3 02_hash_partitioning.py
python3 03_compound_keys.py
python3 04_hot_spot_solutions.py
```

### Option 2: Quick Overview (15 minutes)
```bash
# Read QUICKSTART.md first
cat QUICKSTART.md

# Then run just Exercise 1
python3 01_key_range_partitioning.py
```

### Option 3: Deep Dive (3 hours)
```bash
# Read the complete guide
cat README.md

# Run all exercises
python3 01_key_range_partitioning.py
python3 02_hash_partitioning.py
python3 03_compound_keys.py
python3 04_hot_spot_solutions.py

# Read teaching notes
cat TEACHING_GUIDE.md
```

---

## 📚 What Each File Teaches

### 01_key_range_partitioning.py
**Duration:** 30 minutes | **Lines:** 450+

**Concepts:**
- Range-based key assignment (like encyclopedia volumes)
- Efficient range queries
- The hot spot problem with time-series data
- Fixing hot spots with key prefixing

**Demos:**
1. Basic range partitioning
2. Efficient range queries
3. The hot spot problem
4. Fixing hot spots with prefixes
5. Partition rebalancing

---

### 02_hash_partitioning.py
**Duration:** 30 minutes | **Lines:** 400+

**Concepts:**
- Hash functions for uniform distribution
- Eliminating hot spots
- Why range queries become slow
- Deterministic hash functions (MD5, not Python's hash())

**Demos:**
1. Hash distribution
2. Eliminating hot spots
3. Inefficient range queries
4. Hash function importance
5. The problem with hash(key) % N

---

### 03_compound_keys.py
**Duration:** 30 minutes | **Lines:** 500+

**Concepts:**
- Compound primary keys (Cassandra-style)
- First column hashed, remaining columns sorted
- Efficient range queries within a partition
- Real-world use cases

**Demos:**
1. Compound key structure
2. Efficient within-partition range queries
3. Inefficient cross-partition range queries
4. Real-world example (social media feed)
5. Comparison with other approaches

---

### 04_hot_spot_solutions.py
**Duration:** 30 minutes | **Lines:** 450+

**Concepts:**
- The "celebrity problem" (viral posts)
- Hot spot detection
- Key splitting as a solution
- Read/write trade-offs

**Demos:**
1. The celebrity problem
2. Key splitting solution
3. Read/write trade-off
4. Selective key splitting
5. Real-world example (social media platform)

---

### README.md
**Duration:** 10 minutes to read

**Contains:**
- Learning objectives
- Exercise file overview
- Mapping to DDIA Chapter 6
- Output previews
- Key concepts per exercise
- Comparison table
- Completion checklist
- Next steps

---

### QUICKSTART.md
**Duration:** 5 minutes to read

**Contains:**
- 4-step quick start guide
- The big picture diagram
- Key insights from DDIA
- Discussion questions
- Real-world systems
- Troubleshooting

---

### TEACHING_GUIDE.md
**Duration:** 15 minutes to read

**Contains:**
- Complete overview of what was created
- Learning path explanation
- Core concepts summary
- Comparison table
- Key quotes from DDIA
- Real-world systems
- How to use this material
- Code quality notes
- Next steps

---

## 🎯 Learning Outcomes

After completing this module, you will understand:

1. ✅ **Range Partitioning**
   - How keys are assigned based on ranges
   - Why range queries are efficient
   - Why hot spots occur with time-series data
   - How to fix hot spots with key prefixing

2. ✅ **Hash Partitioning**
   - How hash functions distribute keys uniformly
   - Why hot spots are eliminated
   - Why range queries become slow
   - Why deterministic hash functions are required

3. ✅ **Compound Keys**
   - How to combine hashing and sorting
   - Efficient range queries within a partition
   - Real-world use cases (social media, IoT, time-series)
   - Trade-offs with cross-partition queries

4. ✅ **Hot Spot Solutions**
   - How to detect hot keys
   - Key splitting as a solution
   - Read/write trade-offs
   - When to apply splitting

---

## 📊 Code Statistics

| File | Lines | Classes | Functions | Demos |
|------|-------|---------|-----------|-------|
| 01_key_range_partitioning.py | 450+ | 2 | 8 | 5 |
| 02_hash_partitioning.py | 400+ | 2 | 7 | 5 |
| 03_compound_keys.py | 500+ | 3 | 7 | 5 |
| 04_hot_spot_solutions.py | 450+ | 2 | 7 | 5 |
| **Total** | **1800+** | **9** | **29** | **20** |

---

## 🔗 Mapping to DDIA

| Exercise | DDIA Section | Pages | Concepts |
|----------|-------------|-------|----------|
| 01 | Partitioning by Key Range | 200-203 | Range assignment, hot spots, prefixing |
| 02 | Partitioning by Hash of Key | 203-206 | Hash functions, load balancing, range queries |
| 03 | Compound Primary Keys | 206-207 | Hybrid approach, Cassandra-style |
| 04 | Handling Skewed Workloads | 207-209 | Celebrity problem, key splitting |

---

## 💡 Key Insights

### The Fundamental Trade-off
```
Range Partitioning:
  ✅ Fast range queries
  ❌ Hot spots

Hash Partitioning:
  ✅ No hot spots
  ❌ Slow range queries

Compound Keys:
  ✅ No hot spots + fast range queries (within partition)
  ❌ Slow cross-partition range queries

Hot Spot Splitting:
  ✅ Spreads load
  ❌ Slow reads (must query all split keys)
```

### The Core Principle
> "Every partitioning strategy has trade-offs. Choose based on your workload."

---

## 🎓 How to Use This Material

### For Self-Study
1. Read QUICKSTART.md (5 min)
2. Run Exercise 1 (5 min)
3. Read README.md (10 min)
4. Run Exercises 2-4 (15 min each)
5. Read TEACHING_GUIDE.md (15 min)
6. Modify code and experiment (30 min)

**Total time:** ~2 hours

### For Teaching
1. Show QUICKSTART.md to students
2. Run Exercise 1 together
3. Have students run Exercises 2-4
4. Discuss trade-offs using comparison table
5. Have students modify code

### For Interviews
1. Use these exercises to explain partitioning
2. Discuss trade-offs between approaches
3. Explain real-world systems
4. Discuss how to detect and handle hot spots

---

## ✅ Verification Checklist

- [x] All 4 exercises created
- [x] All exercises run without errors
- [x] All exercises produce clear output
- [x] README.md created with complete guide
- [x] QUICKSTART.md created with 5-minute start
- [x] TEACHING_GUIDE.md created with teaching notes
- [x] Code is well-commented
- [x] Code uses clear formatting (emojis, sections)
- [x] All concepts from DDIA Chapter 6, Section 1 covered
- [x] Real-world systems explained

---

## 🚀 Next Steps

### Immediate
1. Run all 4 exercises
2. Read the documentation
3. Modify code to experiment

### Short-term
1. Complete Section 2: Partitioning and Secondary Indexes
2. Complete Section 3: Rebalancing Partitions
3. Complete Section 4: Request Routing

### Long-term
1. Study other chapters of DDIA
2. Implement partitioning in a real system
3. Design a distributed database

---

## 📞 Support

If you have questions:
1. Check QUICKSTART.md for common issues
2. Read the inline comments in the code
3. Review TEACHING_GUIDE.md for concepts
4. Modify the code and experiment

---

## 📄 License

This material is created for educational purposes based on *Designing Data-Intensive Applications* by Martin Kleppmann.

---

**Ready to start?** Run: `python3 01_key_range_partitioning.py` 🚀
