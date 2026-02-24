# Hash Index Explained

## What is a Hash Index?

A **hash index** is a data structure that maps **keys** to **byte offsets** in a file. Instead of scanning the entire file to find a key, you can:
1. Look up the key in the index (O(1) - instant!)
2. Jump directly to that byte offset in the file
3. Read just that one line

Think of it like a **table of contents** in a book - instead of reading every page to find "Chapter 5", you look it up in the index and jump directly to page 47!

---

## Visual Comparison

### Without Index (Reverse Scan):
```
File: [line1][line2][line3]...[line99998][line99999][line100000]
                                                              ↑
                                                      Start here, scan backwards
                                                      until you find the key
                                                      (might read 50,000 lines!)
```

**Time:** O(n) - worst case, read entire file

### With Hash Index:
```
Index (in memory):
  "user:1"    → offset 0
  "user:2"    → offset 45
  "user:3"    → offset 90
  ...
  "user:50000" → offset 2,250,000
  "user:100000" → offset 4,500,000

File: [line1][line2][line3]...[line50000]...[line100000]
       ↑      ↑      ↑              ↑              ↑
       |      |      |              |              |
       Jump directly to offset - read ONE line!
```

**Time:** O(1) - constant time, always read just 1 line!

---

## How It Works in Our Code

### 1. The Index Structure

```python
@dataclass
class LogDBIndexed:
    path: str
    index: Dict[str, int] = field(default_factory=dict)  # key -> byte offset
```

**The index is a Python dictionary:**
- **Key:** The database key (e.g., `"user:1"`)
- **Value:** The byte offset where that key's record starts in the file

**Example index:**
```python
{
    "user:1": 0,           # user:1's record starts at byte 0
    "user:2": 45,          # user:2's record starts at byte 45
    "user:3": 90,          # user:3's record starts at byte 90
    "user:50000": 2250000, # user:50000's record starts at byte 2,250,000
}
```

---

### 2. Building the Index (`build_index()`)

```python
def build_index(self) -> None:
    """
    One-time scan: rebuild key->offset map from the whole log.
    Last occurrence wins (because later writes overwrite earlier ones).
    """
    self.index.clear()  # Start fresh
    if not os.path.exists(self.path):
        return

    with open(self.path, "rb") as f:  # Binary mode for exact byte positions
        offset = 0  # Track current position in file
        while True:
            line = f.readline()  # Read one line
            if not line:
                break  # End of file
            
            # Parse the line: timestamp \t key \t value \n
            parts = raw.split(b"\t", 2)
            if len(parts) == 3:
                _, key_b, _ = parts
                key = key_b.decode("utf-8")
                self.index[key] = offset  # Store: key → offset
                # NOTE: If key appears again, this overwrites (latest wins!)
            
            offset = f.tell()  # Get new offset after reading line
```

**What happens:**
1. Read file from start to end (one time)
2. For each line, extract the key
3. Store `key → current_offset` in the index
4. If a key appears multiple times, **last one wins** (overwrites previous)

**Example:**
```
File content:
  Offset 0:    "1000\tuser:1\t{age:24}\n"
  Offset 45:   "2000\tuser:2\t{age:21}\n"
  Offset 90:   "3000\tuser:1\t{age:25}\n"  ← user:1 appears again!

After building index:
  index = {
    "user:1": 90,   ← Latest offset (age 25)
    "user:2": 45
  }
```

---

### 3. Writing Data (`put()`)

```python
def put(self, key: str, value: dict) -> None:
    # ... create line ...
    
    with open(self.path, "ab") as f:  # Append mode (binary)
        offset = f.tell()  # Get current position BEFORE writing
        f.write(line)      # Write the line
        f.flush()
        os.fsync(f.fileno())
    
    # Update index: store offset of this new record
    self.index[key] = offset  # Latest write wins!
```

**Key insight:** We update the index **immediately** when writing, so we don't need to rebuild it every time!

**Example:**
```python
db.put("user:1", {"age": 24})
# File: "1000\tuser:1\t{age:24}\n" at offset 0
# Index: {"user:1": 0}

db.put("user:2", {"age": 21})
# File: "2000\tuser:2\t{age:21}\n" at offset 45
# Index: {"user:1": 0, "user:2": 45}

db.put("user:1", {"age": 25})  # Overwrite!
# File: "3000\tuser:1\t{age:25}\n" at offset 90
# Index: {"user:1": 90, "user:2": 45}  ← user:1 now points to offset 90!
```

---

### 4. Reading Data (`get()`)

```python
def get(self, key: str) -> Optional[dict]:
    # Step 1: Look up key in index (O(1) - instant!)
    offset = self.index.get(key)
    if offset is None:
        return None  # Key not found
    
    # Step 2: Jump directly to that offset (O(1) - instant!)
    with open(self.path, "rb") as f:
        f.seek(offset)  # Jump to exact byte position
        line = f.readline()  # Read just ONE line
    
    # Step 3: Parse and return
    parts = line.split(b"\t", 2)
    return json.loads(parts[2].decode("utf-8"))
```

**The magic:**
1. **Lookup in index:** `index.get("user:50000")` → returns `2250000` (instant!)
2. **Seek to offset:** `f.seek(2250000)` → jump directly to that byte (instant!)
3. **Read one line:** `f.readline()` → read just that line (fast!)

**Total time:** O(1) - constant time, regardless of file size!

---

## Visual Example: Finding `user:50000`

### Without Index (Reverse Scan):
```
File (100,000 lines, ~4.5 MB):
[line1][line2]...[line49999][line50000][line50001]...[line100000]
                                                              ↑
                                                      Start here
                                                      Read line 100000 (not it)
                                                      Read line 99999 (not it)
                                                      ...
                                                      Read line 50001 (not it)
                                                      Read line 50000 (found!)
                                                      
Time: ~50,000 line reads = SLOW!
```

### With Hash Index:
```
Step 1: Look up in index (in memory):
  index["user:50000"] → 2250000  (instant!)

Step 2: Jump to file:
  f.seek(2250000)  (instant!)

Step 3: Read one line:
  f.readline()  → "3000\tuser:50000\t{age:45}\n"  (fast!)

Time: 1 lookup + 1 seek + 1 read = FAST!
```

---

## Performance Comparison

| Operation | Without Index | With Hash Index | Speedup |
|-----------|--------------|-----------------|---------|
| **Lookup first key** | O(n) - scan entire file | O(1) - direct jump | ~100,000x |
| **Lookup middle key** | O(n/2) - scan half file | O(1) - direct jump | ~50,000x |
| **Lookup last key** | O(1) - found immediately | O(1) - direct jump | ~1x |
| **Write** | O(1) - append | O(1) - append + update index | ~same |
| **Range query** | O(n) - scan | O(n) - scan index + sort | ~same |

---

## Advantages of Hash Index

✅ **Fast lookups:** O(1) - constant time, regardless of file size
✅ **Simple:** Just a dictionary mapping keys to offsets
✅ **Efficient writes:** Still append-only (fast writes)
✅ **Latest value:** Automatically handles overwrites (last write wins)

---

## Disadvantages of Hash Index

❌ **Memory usage:** Index must fit in RAM (for 100k keys, ~few MB)
❌ **No range queries:** Can't efficiently find "all keys between user:100 and user:200"
❌ **No prefix queries:** Finding "all keys starting with 'user:'" requires scanning entire index
❌ **Must rebuild:** If index is lost, must scan entire file to rebuild

---

## Code Walkthrough

### Example: Complete Flow

```python
# 1. Create database
db = LogDBIndexed("data.log")

# 2. Write some data
db.put("user:1", {"age": 24})  # Index: {"user:1": 0}
db.put("user:2", {"age": 21})  # Index: {"user:1": 0, "user:2": 45}
db.put("user:1", {"age": 25})  # Index: {"user:1": 90, "user:2": 45}

# 3. Read data (fast!)
result = db.get("user:1")
# Step 1: index.get("user:1") → 90
# Step 2: f.seek(90)
# Step 3: f.readline() → "3000\tuser:1\t{age:25}\n"
# Result: {"age": 25} ✅

# 4. What if file already exists?
db.build_index()  # Rebuild index from file (one-time scan)
```

---

## Key Concepts

### 1. Byte Offset
- **Offset** = position in file (in bytes)
- Byte 0 = start of file
- Byte 100 = 100 bytes from start
- `f.seek(offset)` = jump to that exact position

### 2. Latest Write Wins
- If same key written multiple times, index stores **latest offset**
- When reading, you get the **most recent value**
- Old values still in file (append-only), but index points to latest

### 3. In-Memory vs On-Disk
- **Index:** Stored in RAM (Python dict) - fast lookups
- **Data:** Stored on disk (log file) - persistent storage
- Trade-off: Speed (RAM) vs Persistence (disk)

### 4. O(1) Lookup
- **O(1)** = constant time
- Whether file has 100 or 100 million records, lookup takes same time!
- Hash table lookup is O(1) on average

---

## Real-World Analogy

**Hash Index = GPS Navigation**

- **Without index:** Drive around randomly until you find the address (slow!)
- **With index:** GPS tells you exact coordinates, you drive directly there (fast!)

The index is like a GPS that knows where everything is stored!

---

## Summary

**Hash Index = Dictionary mapping keys to file positions**

1. **Write:** Append to file + update index
2. **Read:** Look up key in index → jump to offset → read one line
3. **Result:** O(1) lookups instead of O(n) scans!

**Trade-offs:**
- ✅ Fast lookups
- ❌ Uses memory
- ❌ Can't do range queries efficiently

This is why databases use indexes - they make lookups **thousands of times faster**!
