from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Optional, Iterator

from sparse_index import SparseIndex
from bloom_filter import BloomFilter

@dataclass
class SSTable:
    dat_path: str
    idx_path: str
    sparse_index: SparseIndex
    bloom_filter: Optional[BloomFilter] = None

    def get(self, key: str) -> tuple[Optional[dict], int]:
        """
        Use sparse index to seek near the key, then scan forward until:
        - key found -> return record
        - key passed -> stop
        
        Uses bloom filter to skip SSTable if key definitely not present.
        
        Returns:
            (record, bytes_read): Tuple of record (or None) and bytes read from disk
        """
        bytes_read = 0
        
        if not os.path.exists(self.dat_path):
            return None, 0

        # Check bloom filter first (if available)
        if self.bloom_filter is not None:
            if not self.bloom_filter.might_contain(key):
                return None, 0  # Definitely not in this SSTable

        # Track bytes read for index file (approximate - we load it once)
        # For accuracy, we'd need to track this separately, but for simplicity
        # we'll estimate based on file size if we read the SSTable
        start_off = self.sparse_index.find_start_offset(key)
        with open(self.dat_path, "rb") as f:
            f.seek(start_off)
            initial_pos = f.tell()
            while True:
                line = f.readline()
                if not line:
                    bytes_read = f.tell() - initial_pos
                    return None, bytes_read
                bytes_read += len(line)
                rec = json.loads(line)
                k = rec["k"]
                if k == key:
                    return rec, bytes_read
                if k > key:
                    return None, bytes_read

    def scan(self, start_key: str, end_key: Optional[str] = None) -> Iterator[dict]:
        """
        Scan records from start_key to end_key (inclusive).
        If end_key is None, scan to end of file.
        """
        if not os.path.exists(self.dat_path):
            return

        start_off = self.sparse_index.find_start_offset(start_key)
        with open(self.dat_path, "rb") as f:
            f.seek(start_off)
            for line in f:
                rec = json.loads(line)
                k = rec["k"]
                
                # Skip until we reach start_key
                if k < start_key:
                    continue
                
                # Stop if we've passed end_key
                if end_key is not None and k > end_key:
                    break
                
                yield rec

    @staticmethod
    def load(dat_path: str, idx_path: str, bloom_path: Optional[str] = None) -> "SSTable":
        with open(idx_path, "r", encoding="utf-8") as f:
            idx_data = json.load(f)
        
        bloom_filter = None
        if bloom_path and os.path.exists(bloom_path):
            with open(bloom_path, "r", encoding="utf-8") as f:
                bloom_data = json.load(f)
                bloom_filter = BloomFilter.from_json(bloom_data)
        
        return SSTable(
            dat_path=dat_path,
            idx_path=idx_path,
            sparse_index=SparseIndex.from_json(idx_data),
            bloom_filter=bloom_filter
        )
