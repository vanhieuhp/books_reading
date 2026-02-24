# Day 1 Quick Start Guide

## 🚀 Get Started in 3 Steps

### Step 1: Install Dependencies

```bash
# Option A: Use the setup script
./setup.sh

# Option B: Manual installation
pip3 install msgpack
```

### Step 2: Run the Demo

```bash
python3 encoding_demo.py
```

### Step 3: Review the Results

The script will show you:
- Size comparison (bytes)
- Performance comparison (speed)
- Human readability examples
- Key insights and takeaways

## 📊 What to Expect

The script tests with different data sizes:
- 1 record (quick test)
- 100 records
- 1,000 records  
- 10,000 records (may take a moment)

You'll see output like:

```
ENCODING COMPARISON RESULTS (1,000 records)
================================================================================
Format          Size           Size vs JSON    Encode Time    Decode Time   
--------------------------------------------------------------------------------
JSON            245.23 KB     baseline        12.34 ms       8.90 ms       
MessagePack     189.45 KB     -22.8%          5.67 ms        4.23 ms       
Pickle          156.78 KB     -36.1%          3.45 ms        2.12 ms       
```

## 💡 Key Questions to Answer

As you run the demo, think about:

1. **Why are binary formats smaller?**
   - JSON includes field names in every record
   - Binary formats use more efficient encoding

2. **Why are binary formats faster?**
   - No string parsing needed
   - Direct binary operations
   - Better CPU cache usage

3. **What's the trade-off?**
   - Binary formats are not human-readable
   - Harder to debug
   - Need special tools to inspect

4. **When would you use each?**
   - JSON: Web APIs, config files, debugging
   - MessagePack: Internal services, performance
   - Pickle: Python-only, trusted data (never for APIs!)

## 🎯 Learning Goals

By the end of this exercise, you should understand:

- ✅ What encoding means (object → bytes)
- ✅ Why binary formats exist (size & speed)
- ✅ Trade-offs between formats
- ✅ When to use each format

## 🐛 Troubleshooting

### "ModuleNotFoundError: No module named 'msgpack'"

```bash
pip3 install msgpack
```

The script will still work with just JSON and Pickle, but you'll miss the MessagePack comparison.

### Script runs slowly

This is normal! The script tests with up to 10,000 records to show real differences.
You can modify the `test_sizes` list in `main()` to test fewer records.

### Want to see just a quick test?

Edit `encoding_demo.py` and change:
```python
test_sizes = [1, 100, 1000, 10000]  # Full test
```
to:
```python
test_sizes = [1, 100]  # Quick test
```

## ✅ Completion Checklist

- [ ] Installed dependencies (msgpack)
- [ ] Ran the script successfully
- [ ] Reviewed the comparison tables
- [ ] Understood the size differences
- [ ] Understood the performance differences
- [ ] Read the key insights section
- [ ] Can explain when to use each format

## 📚 Next Steps

Once you've completed Day 1:

1. ✅ You understand encoding fundamentals
2. ✅ You've seen text vs binary trade-offs
3. ✅ Ready for Day 2: JSON Deep Dive

**Ready?** Move on to Day 2 where you'll build a REST API with JSON!
