"""
Bloom Filter implementation for LSM Tree.
A probabilistic data structure that can tell you if a key is definitely NOT in a set.
"""

import hashlib
import json
import math
from typing import List


class BloomFilter:
    """
    Simple Bloom Filter implementation.
    
    Uses multiple hash functions to set bits in a bit array.
    Can have false positives (says key might be there when it's not)
    Never has false negatives (if it says "not there", it's definitely not)
    """
    
    def __init__(self, capacity: int = 10000, error_rate: float = 0.01):
        """
        Initialize bloom filter.
        
        Args:
            capacity: Expected number of elements
            error_rate: Desired false positive rate (0.01 = 1%)
        """
        self.capacity = capacity
        self.error_rate = error_rate
        
        # Calculate optimal size and hash count
        # m = -n * ln(p) / (ln(2)^2)  where n=capacity, p=error_rate
        self.size = int(-capacity * math.log(error_rate) / (math.log(2) ** 2))
        self.hash_count = int((self.size / capacity) * math.log(2))
        
        # Ensure minimum values
        self.size = max(self.size, 64)  # At least 64 bits
        self.hash_count = max(self.hash_count, 1)  # At least 1 hash function
        
        # Bit array (using bytearray for efficiency)
        self.bit_array = bytearray((self.size + 7) // 8)  # Round up to bytes
    
    def _hash(self, key: str, seed: int) -> int:
        """Generate hash for key with given seed."""
        # Use MD5 hash with seed to create different hash functions
        h = hashlib.md5(f"{key}:{seed}".encode()).hexdigest()
        return int(h, 16) % self.size
    
    def add(self, key: str) -> None:
        """Add key to bloom filter."""
        for i in range(self.hash_count):
            pos = self._hash(key, i)
            byte_pos = pos // 8
            bit_pos = pos % 8
            self.bit_array[byte_pos] |= (1 << bit_pos)
    
    def might_contain(self, key: str) -> bool:
        """
        Check if key might be in the filter.
        
        Returns:
            False: Key is definitely NOT in the filter
            True: Key MIGHT be in the filter (could be false positive)
        """
        for i in range(self.hash_count):
            pos = self._hash(key, i)
            byte_pos = pos // 8
            bit_pos = pos % 8
            if not (self.bit_array[byte_pos] & (1 << bit_pos)):
                return False  # Definitely not there
        return True  # Might be there
    
    def to_json(self) -> dict:
        """Serialize bloom filter to JSON."""
        return {
            "capacity": self.capacity,
            "error_rate": self.error_rate,
            "size": self.size,
            "hash_count": self.hash_count,
            "bit_array": self.bit_array.hex()  # Convert to hex string
        }
    
    @staticmethod
    def from_json(data: dict) -> "BloomFilter":
        """Deserialize bloom filter from JSON."""
        bf = BloomFilter(capacity=data["capacity"], error_rate=data["error_rate"])
        bf.size = data["size"]
        bf.hash_count = data["hash_count"]
        bf.bit_array = bytearray.fromhex(data["bit_array"])
        return bf
