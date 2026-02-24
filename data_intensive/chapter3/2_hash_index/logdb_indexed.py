
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Optional, Dict


@dataclass
class LogDBIndexed:
    path: str
    index: Dict[str, int] = field(default_factory=dict)  # Hash index: key -> byte offset in file
    # Example: {"user:1": 0, "user:2": 45, "user:3": 90}
    # This is stored in RAM for fast O(1) lookups

    def build_index(self) -> None:
        """
        One-time scan: rebuild key->offset map from the whole log.
        Last occurrence wins (because later writes overwrite earlier ones).
        
        This is called when:
        - Database is opened and file already exists
        - Index was lost/corrupted and needs rebuilding
        """
        self.index.clear()  # Start with empty index
        if not os.path.exists(self.path):
            return  # No file = no index needed

        with open(self.path, "rb") as f:  # Binary mode for exact byte positions
            offset = 0  # Track current byte position in file
            while True:
                line = f.readline()  # Read one line (includes \n)
                if not line:
                    break  # End of file reached
                
                # Remove trailing newline if present
                if line.endswith(b"\n"):
                    raw = line[:-1]  # Remove \n
                else:
                    raw = line  # Last line might not have \n

                # Parse line: format is "timestamp \t key \t value"
                parts = raw.split(b"\t", 2)  # Split into max 3 parts
                if len(parts) == 3:
                    _, key_b, _ = parts  # Extract key (middle part)
                    try:
                        key = key_b.decode("utf-8")  # Convert bytes to string
                        self.index[key] = offset  # Store: key → offset
                        # NOTE: If key appears multiple times, this overwrites!
                        # Last occurrence wins (latest value)
                    except UnicodeDecodeError:
                        pass  # Skip invalid keys

                offset = f.tell()  # Get new offset after reading this line
                # f.tell() returns current file position (in bytes)

    def put(self, key: str, value: dict) -> None:
        """
        Append record and update index with the offset of this new record.
        
        Steps:
        1. Create line: timestamp \t key \t value \n
        2. Get current file offset (where we'll write)
        3. Append line to file
        4. Update index: key → offset (latest write wins!)
        """
        if "\t" in key or "\n" in key:
            raise ValueError("key must not contain tab or newline")

        ts = int(time.time() * 1000)  # Timestamp in milliseconds
        value_json = json.dumps(value, separators=(",", ":"))  # Compact JSON
        line = f"{ts}\t{key}\t{value_json}\n".encode("utf-8")  # Convert to bytes

        # Use binary append so offsets are byte-accurate.
        with open(self.path, "ab") as f:  # "ab" = append binary mode
            offset = f.tell()  # Get current file position BEFORE writing
            # This is where our new record will start
            f.write(line)  # Append line to end of file
            f.flush()  # Force Python to write to OS buffer
            os.fsync(f.fileno())  # Force OS to write to disk (durability)

        # Update hash index: latest write wins
        # If key already exists, this overwrites the old offset
        self.index[key] = offset  # Store: key → offset of this record

    def get(self, key: str) -> Optional[dict]:
        """
        O(1) point lookup (after index built): seek to offset and read one line.
        
        This is FAST because:
        1. Lookup in index (Python dict) = O(1) - instant!
        2. f.seek(offset) = O(1) - jump directly to byte position
        3. f.readline() = O(1) - read just one line
        
        Total: O(1) - constant time, regardless of file size!
        """
        # Step 1: Look up key in index (O(1) - instant!)
        offset = self.index.get(key)  # Returns None if key not found
        if offset is None:
            return None  # Key doesn't exist
        if not os.path.exists(self.path):
            return None  # File doesn't exist

        # Step 2: Jump directly to that offset (O(1) - instant!)
        with open(self.path, "rb") as f:  # Binary mode for exact positioning
            f.seek(offset)  # Jump to exact byte position
            line = f.readline()  # Read just ONE line (fast!)
            if not line:
                return None  # File was truncated or index is stale
            
            # Remove trailing newline if present
            if line.endswith(b"\n"):
                line = line[:-1]

            # Step 3: Parse the line
            parts = line.split(b"\t", 2)  # Split: [timestamp, key, value]
            if len(parts) != 3:
                return None  # Malformed line

            _, key_b, value_b = parts
            # Sanity check: verify key matches (index might be stale/corrupt)
            if key_b.decode("utf-8", errors="ignore") != key:
                return None  # Index points to wrong record

            # Step 4: Parse JSON and return
            try:
                return json.loads(value_b.decode("utf-8"))  # Convert bytes → string → dict
            except json.JSONDecodeError:
                return None  # Invalid JSON

    def scan_range_prefix(self, prefix: str) -> list[str]:
        """
        Demonstrate why hash indexes are bad for ranges:
        To find keys by prefix, we must scan the whole index and sort.
        
        This is SLOW because:
        - Hash index is unordered (keys are in random order)
        - Must check EVERY key in index (O(n))
        - Must sort results (O(n log n))
        
        Better indexes for ranges: B-tree, LSM-tree
        """
        matches = [k for k in self.index.keys() if k.startswith(prefix)]  # Scan all keys
        matches.sort()  # Sort results (hash index doesn't preserve order)
        return matches


if __name__ == "__main__":
    db = LogDBIndexed("data_indexed.log")
    db.build_index()

    db.put("user:1", {"name": "Hieu", "age": 24})
    db.put("user:2", {"name": "An", "age": 21})
    db.put("user:1", {"name": "Hieu", "age": 25})

    print("get user:1 =", db.get("user:1"))
    print("get user:2 =", db.get("user:2"))
    print("get user:999 =", db.get("user:999"))

    # Show the weakness: prefix/range needs scanning + sorting
    print("prefix user: keys =", db.scan_range_prefix("user:"))
