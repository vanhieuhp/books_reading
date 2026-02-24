"""
Demonstration: Why binary mode and why lines[0] can be incomplete
This shows the difference between reading line-by-line vs reading in chunks.
"""

import io

# Create sample file content
file_content = """1000\tuser:1\t{"name":"Alice"}\n2000\tuser:2\t{"name":"Bob"}\n3000\tuser:3\t{"name":"Charlie"}\n"""

print("=" * 80)
print("ORIGINAL FILE CONTENT:")
print("=" * 80)
print(repr(file_content))
print(f"\nFile as bytes: {len(file_content.encode('utf-8'))} bytes")
print()

# Show the file as bytes with positions
file_bytes = file_content.encode('utf-8')
print("File bytes with positions:")
for i in range(0, len(file_bytes), 20):
    chunk = file_bytes[i:i+20]
    print(f"Position {i:3d}: {chunk!r}")

print("\n" + "=" * 80)
print("PROBLEM: Reading in CHUNKS (not line-by-line)")
print("=" * 80)
print("""
When we read in CHUNKS (fixed byte sizes), chunk boundaries don't care about lines!
A chunk can cut through the middle of a line.
""")

# Simulate reading in 30-byte chunks
chunk_size = 30
print(f"\nReading in {chunk_size}-byte chunks:\n")

for i in range(0, len(file_bytes), chunk_size):
    chunk = file_bytes[i:i+chunk_size]
    print(f"Chunk starting at byte {i}:")
    print(f"  Bytes: {chunk!r}")
    print(f"  Decoded: {chunk.decode('utf-8', errors='replace')}")
    print(f"  Split by \\n: {chunk.split(b'\\n')}")
    print()

print("=" * 80)
print("KEY INSIGHT: Chunk boundaries can split lines!")
print("=" * 80)
print("""
Notice how chunks don't align with line boundaries!
- Chunk 1 might end in the middle of a line
- Chunk 2 starts with the rest of that line

This is why lines[0] can be incomplete!
""")

print("\n" + "=" * 80)
print("WHY BINARY MODE?")
print("=" * 80)
print("""
Text mode ("r") reads FORWARD line-by-line. You can't:
- Seek to exact byte positions
- Read exact number of bytes
- Read backwards efficiently

Binary mode ("rb") lets us:
- f.seek(file_size - offset)  ← Jump to exact byte position
- f.read(chunk_size)          ← Read exact number of bytes
- Read backwards chunk by chunk
""")

# Demonstrate the actual problem
print("\n" + "=" * 80)
print("DEMONSTRATION: Reading backwards in chunks")
print("=" * 80)

file_size = len(file_bytes)
chunk_size = 30
offset = 0
buf = b""

iteration = 1
while offset < file_size:
    print(f"\n--- ITERATION {iteration} ---")
    
    # Calculate read position (backwards from end)
    offset = min(file_size, offset + chunk_size)
    read_from = file_size - offset
    read_to = min(file_size, read_from + chunk_size)
    
    # Read chunk
    chunk = file_bytes[read_from:read_to]
    print(f"Reading bytes {read_from} to {read_to} (backwards)")
    print(f"Chunk: {chunk!r}")
    
    # Prepend to buffer
    buf = chunk + buf
    print(f"Buffer: {buf!r}")
    
    # Split by newlines
    lines = buf.split(b'\n')
    print(f"After split(b'\\n'): {len(lines)} parts")
    
    for i, line in enumerate(lines[:3]):  # Show first 3
        if i == 0:
            print(f"  lines[0] = {line!r} ← INCOMPLETE? (might continue in next chunk)")
        else:
            print(f"  lines[{i}] = {line!r} ← Complete line")
    
    # Keep first, process rest
    buf = lines[0]
    complete_lines = lines[1:]
    
    print(f"\n✅ Keeping lines[0] = {buf!r} in buffer")
    print(f"✅ Processing {len([l for l in complete_lines if l])} complete line(s)")
    
    iteration += 1
    if iteration > 5:
        break

print("\n" + "=" * 80)
print("WHY CAN'T WE USE TEXT MODE?")
print("=" * 80)

# Show what happens with text mode
print("\nTrying to read backwards with text mode:")
print("""
# Text mode reads FORWARD only:
with open(file, "r") as f:
    f.seek(100)  # Can't seek backwards precisely!
    line = f.readline()  # Reads forward, not backwards
    # Can't read exact byte positions
    # Can't read in fixed-size chunks
    # Can't efficiently read backwards
""")

print("\n" + "=" * 80)
print("THE ANSWER TO YOUR QUESTION:")
print("=" * 80)
print("""
Q: "In decode mode, the line still stay in one line, why encode binary 
    the content of line[0] can be part of previous buffer?"

A: The issue is NOT about encoding/decoding!
   
   The issue is about READING IN CHUNKS vs READING LINE-BY-LINE:
   
   1. If we read LINE-BY-LINE (text mode):
      - Each line is complete ✅
      - But we can't read BACKWARDS efficiently ❌
      - We can't seek to exact byte positions ❌
   
   2. If we read in CHUNKS (binary mode):
      - We can read backwards ✅
      - We can seek to exact positions ✅
      - But chunks can CUT THROUGH LINES ❌
      - That's why lines[0] might be incomplete!
   
   Example:
   File: "line1\\nline2\\nline3\\n"
   
   Reading in 10-byte chunks:
   Chunk 1: "line2\\nline"  ← "line" is incomplete!
   Chunk 2: "3\\nline1\\n"   ← Now we have complete "line3" and "line1"
   
   That's why we keep lines[0] in buffer - it might be the tail end
   of a line that started in the previous chunk!
""")
