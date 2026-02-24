from __future__ import annotations  # Enable forward references in type hints
import json                          # Convert Python dicts to/from JSON strings
import os                            # File system operations (check if file exists, etc.)
import time                          # Get current timestamp
from dataclasses import dataclass    # Decorator to auto-generate __init__ and other methods
from typing import Optional          # Type hint: means "this type or None"


@dataclass(frozen=True)              # frozen=True makes class immutable (can't change after creation)
class LogDB:
    path: str                        # File path where we store the log data

    def put(self, key: str, value: dict) -> None:  # Write a key-value pair to the log
        """
        Append-only write: one line per record.
        """
        if "\t" in key or "\n" in key:  # Check if key contains tab or newline (we use these as separators)
            raise ValueError("key must not contain tab or newline")  # Throw error if invalid
        ts = int(time.time() * 1000)  # Get current time in milliseconds (timestamp)
        line = f"{ts}\t{key}\t{json.dumps(value, separators=(',', ':'))}\n"  # Format: timestamp TAB key TAB json_value NEWLINE

        # Append is sequential -> fast
        with open(self.path, "a", encoding="utf-8") as f:  # Open file in append mode (adds to end, doesn't overwrite)
            f.write(line)            # Write the formatted line to file
            f.flush()                # Force Python to write buffer to OS (but not yet to disk)
            os.fsync(f.fileno())     # Force OS to write to disk immediately (ensures durability)

    def get_latest(self, key: str) -> Optional[dict]:  # Get the most recent value for a key, returns None if not found
        """
        Slow read (no index): search from the end to find latest key.
        This demonstrates why indexes/memtables exist.
        """
        if not os.path.exists(self.path):  # Check if the log file exists
            return None                     # Return None if file doesn't exist yet

        # Reverse-scan lines from the end. We do a chunked approach to avoid reading whole file.
        with open(self.path, "rb") as f:  # Open file in binary read mode ("rb" = read bytes)
            return self._reverse_scan_latest(f, key)  # Call helper method to scan backwards

    def tail(self, n: int = 10) -> list[str]:  # Get last n lines from the log (default 10)
        if not os.path.exists(self.path):      # Check if file exists
            return []                           # Return empty list if no file
        with open(self.path, "rb") as f:       # Open file in binary read mode
            lines = f.read().splitlines()[-n:] # Read entire file, split into lines, take last n lines
        return [ln.decode("utf-8", errors="replace") for ln in lines]  # Convert each byte line to string, return list

    def _reverse_scan_latest(self, f, key: str) -> Optional[dict]:  # Private helper: scan file backwards to find key
        """
        Read file backwards in chunks, splitting into lines, returning the latest matching key.
        """
        key_bytes = key.encode("utf-8")  # Convert key string to bytes for comparison
        buf = b""                        # Buffer to hold partial lines (bytes type: b"")
        pos = f.seek(0, os.SEEK_END)     # Move file pointer to end of file (returns position)
        file_size = f.tell()             # Get current position (which is file size since we're at end)

        chunk_size = 8192                # Read 8KB chunks at a time (8192 bytes)
        offset = 0                       # Track how far from end we've read

        while offset < file_size:       # Keep reading until we've covered entire file
            offset = min(file_size, offset + chunk_size)  # Calculate next offset (don't go past file start)
            f.seek(file_size - offset)   # Move file pointer backwards from end
            chunk = f.read(min(chunk_size, offset - (offset - chunk_size)))  # Read chunk (handles edge case at start)
            buf = chunk + buf            # Prepend chunk to buffer (we're reading backwards, so prepend)

            lines = buf.split(b"\n")     # Split buffer into lines (b"\n" is newline in bytes)
            # Example: if buf = b"abc\ndef\nghi", then lines = [b"abc", b"def", b"ghi", b""]
            # 
            # WHY CAN lines[0] BE INCOMPLETE?
            # We read in CHUNKS (fixed byte sizes like 8192), not line-by-line.
            # Chunk boundaries don't care about line boundaries - they can cut through the middle of a line!
            # 
            # Example file: "line1\nline2\nline3\n"
            # Reading in 10-byte chunks backwards:
            #   Chunk 1: "line2\nline"  → lines[0] = b"line" (INCOMPLETE - missing "3\n" from next chunk)
            #   Chunk 2: "3\nline1\n"    → Prepend to buffer: "3\nline1\n" + "line" = "3\nline1\nline"
            #                             → Now lines[0] = b"3" and lines[1] = b"line1" (complete!)
            # 
            # Key insight: lines[0] is the FIRST part of buffer - it might be the TAIL END of a line
            # that started in the previous chunk. We keep it to combine with the next chunk!
            buf = lines[0]               # Keep first element (might be incomplete - tail end of line from previous chunk)
            complete_lines = lines[1:]   # Rest are complete lines we can process (guaranteed to have \n before them)

            # scan complete lines from end to start
            for ln in reversed(complete_lines):  # Loop through lines in reverse order (newest first)
                if not ln:               # Skip empty lines
                    continue
                # format: ts \t key \t json
                parts = ln.split(b"\t", 2)  # Split line by tab into max 3 parts: [timestamp, key, value]
                if len(parts) != 3:      # Skip if line doesn't have exactly 3 parts (malformed)
                    continue
                _, k, v = parts          # Unpack: ignore timestamp (_), get key (k) and value (v)
                if k == key_bytes:       # Check if this key matches what we're looking for
                    try:
                        return json.loads(v.decode("utf-8"))  # Convert bytes to string, parse JSON, return dict
                    except json.JSONDecodeError:  # If JSON is invalid, return None
                        return None

        # check remaining buffer (the first line)
        if buf:                          # After reading all chunks, check if buffer has remaining data
            parts = buf.split(b"\t", 2)  # Split remaining buffer by tab
            if len(parts) == 3 and parts[1] == key_bytes:  # Check if valid format and key matches
                try:
                    return json.loads(parts[2].decode("utf-8"))  # Parse and return JSON value
                except json.JSONDecodeError:  # Handle invalid JSON
                    return None
        return None                     # Key not found in entire file

if __name__ == "__main__":             # Only run this code if script is executed directly (not imported)
    db = LogDB("data.log")             # Create a LogDB instance with file "data.log"

    db.put("user:1", {"name": "Hieu", "age": 24})  # Write first record for user:1
    db.put("user:2", {"name": "An", "age": 21})    # Write record for user:2
    db.put("user:1", {"name": "Hieu", "age": 25})  # Overwrite user:1 by appending new record (old one still in file)

    print("tail:", db.tail(5))                      # Print last 5 lines from log
    print("user:1 latest:", db.get_latest("user:1"))  # Get and print latest value for user:1 (should be age 25)
    print("user:2 latest:", db.get_latest("user:2"))  # Get and print latest value for user:2
    print("user:3 latest:", db.get_latest("user:3"))  # Get and print latest value for user:3 (should be None, doesn't exist)