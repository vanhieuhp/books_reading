"""
Demo script to visualize how buf = lines[0] works when reading backwards in chunks.
This shows why we need to keep the first part of the buffer.
"""

# Simulate a log file with 3 lines
file_content = b"1000\tuser:1\t{name:Alice}\n2000\tuser:2\t{name:Bob}\n3000\tuser:3\t{name:Charlie}\n"

print("=" * 70)
print("ORIGINAL FILE CONTENT:")
print("=" * 70)
print(file_content.decode('utf-8'))
print(f"File size: {len(file_content)} bytes\n")

# Simulate reading backwards in chunks
chunk_size = 30  # Read 30 bytes at a time
file_size = len(file_content)
offset = 0
buf = b""

print("=" * 70)
print("SIMULATING BACKWARDS READING (like _reverse_scan_latest does):")
print("=" * 70)

iteration = 1
while offset < file_size:
    print(f"\n--- ITERATION {iteration} ---")
    
    # Calculate where to read from
    offset = min(file_size, offset + chunk_size)
    read_from = file_size - offset
    read_to = min(file_size, read_from + chunk_size)
    
    print(f"Reading from position {read_from} to {read_to} (backwards from end)")
    
    # Read chunk
    chunk = file_content[read_from:read_to]
    print(f"Chunk read: {chunk!r}")
    print(f"Chunk (decoded): {chunk.decode('utf-8', errors='replace')}")
    
    # Prepend to buffer (because we're reading backwards)
    old_buf = buf
    buf = chunk + buf
    print(f"\nBuffer BEFORE prepending: {old_buf!r}")
    print(f"Buffer AFTER prepending:   {buf!r}")
    
    # Split by newlines
    lines = buf.split(b"\n")
    print(f"\nAfter split(b'\\n'): {len(lines)} parts")
    for i, line in enumerate(lines):
        marker = " ← lines[0] (KEEP IN BUFFER)" if i == 0 else " ← complete line" if line else " ← empty"
        print(f"  lines[{i}] = {line!r}{marker}")
    
    # Keep first part in buffer
    old_buf_value = buf
    buf = lines[0]
    complete_lines = lines[1:]
    
    print(f"\n✅ buf = lines[0] = {buf!r}")
    print(f"✅ complete_lines = lines[1:] = {complete_lines}")
    
    # Process complete lines
    if complete_lines:
        print(f"\n📝 Processing {len(complete_lines)} complete line(s):")
        for line in reversed(complete_lines):  # Process in reverse (newest first)
            if line:  # Skip empty
                parts = line.split(b"\t", 2)
                if len(parts) == 3:
                    print(f"   Found: timestamp={parts[0].decode()}, key={parts[1].decode()}, value={parts[2].decode()}")
    
    iteration += 1
    if iteration > 10:  # Safety limit
        break

print("\n" + "=" * 70)
print("FINAL BUFFER CHECK:")
print("=" * 70)
if buf:
    print(f"Remaining buffer: {buf!r}")
    print("This would be checked at the end (line 86-92 in logdb.py)")
else:
    print("Buffer is empty - all lines processed!")

print("\n" + "=" * 70)
print("KEY INSIGHT:")
print("=" * 70)
print("""
When reading backwards in chunks:
1. lines[0] = First part of buffer (might be INCOMPLETE - missing data from previous chunk)
2. lines[1:] = Complete lines (guaranteed to have \\n before them, so they're complete)

Example scenario where line is split:
  Chunk 1 (read first): "def\\nghi\\n" 
    → lines = [b"def", b"ghi", b""]
    → buf = b"def" (keep - might continue in next chunk)
    → Process: b"ghi" (complete)
  
  Chunk 2 (read next): "abc\\n"
    → buf = b"abc\\n" + b"def" = b"abc\\ndef"
    → lines = [b"abc", b"def"]
    → buf = b"abc" (keep)
    → Process: b"def" (now complete!)
""")
