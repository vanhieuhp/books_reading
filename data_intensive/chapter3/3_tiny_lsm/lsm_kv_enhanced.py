"""
Enhanced LSM KV Store with:
- Bloom filters for faster reads
- Range queries
- Leveled compaction
- Metrics tracking
"""

from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass, field
from bisect import insort
from typing import Optional, Any, Dict, List, Tuple, Iterator

from utils import fsync_file, now_ms
from sparse_index import SparseIndex
from sstable import SSTable
from bloom_filter import BloomFilter
from metrics import Metrics

@dataclass
class LSMKV:
    dir_path: str = "lsm_data"
    wal_path: str = field(init=False)
    manifest_path: str = field(init=False)

    # memtable
    mem: Dict[str, dict] = field(default_factory=dict)
    mem_keys_sorted: List[str] = field(default_factory=list)

    # sstables: organized by level
    # levels[0] = newest (memtable flushes here)
    # levels[1] = older, levels[2] = even older, etc.
    levels: List[List[str]] = field(default_factory=lambda: [[]])  # List of SSTable IDs per level
    
    # Legacy: flat list for backward compatibility
    sst_ids: List[str] = field(init=False)

    # tuning
    flush_threshold: int = 5000          # flush when memtable has this many keys
    sparse_step: int = 50               # index every N keys in SSTable
    enable_bloom_filter: bool = True    # Use bloom filters
    bloom_capacity: int = 10000          # Expected keys per SSTable
    bloom_error_rate: float = 0.01      # 1% false positive rate
    
    # Leveled compaction settings
    use_leveled_compaction: bool = True
    level_size_multiplier: int = 10    # Level N can be 10x size of level N-1
    max_sstables_per_level: int = 4     # Compact when this many SSTables in level
    
    # Metrics
    metrics: Metrics = field(default_factory=Metrics)
    
    # SSTable cache (in-memory to avoid reloading index/bloom filter)
    _sstable_cache: Dict[str, SSTable] = field(default_factory=dict, init=False)
    _cache_size_limit: int = 100  # Max cached SSTables

    def __post_init__(self):
        os.makedirs(self.dir_path, exist_ok=True)
        self.wal_path = os.path.join(self.dir_path, "wal.log")
        self.manifest_path = os.path.join(self.dir_path, "manifest.json")
        self._load_manifest()
        self.recover()
        # Initialize sst_ids for backward compatibility
        self._update_sst_ids()

    # ------------------- Public API -------------------

    def put(self, key: str, value: Any, durable: bool = True) -> None:
        """Put a key-value pair."""
        start_time = time.time()
        
        self._append_wal({"op": "PUT", "ts": now_ms(), "k": key, "v": value}, durable=durable)
        self._mem_put(key, {"t": 0, "v": value})
        
        latency_ms = (time.time() - start_time) * 1000
        self.metrics.record_write(latency_ms)
        
        if len(self.mem) >= self.flush_threshold:
            self.flush()

    def delete(self, key: str, durable: bool = True) -> None:
        """Delete a key."""
        start_time = time.time()
        
        self._append_wal({"op": "DEL", "ts": now_ms(), "k": key}, durable=durable)
        self._mem_put(key, {"t": 1, "v": None})  # tombstone
        
        latency_ms = (time.time() - start_time) * 1000
        self.metrics.record_delete()
        self.metrics.record_write(latency_ms)
        
        if len(self.mem) >= self.flush_threshold:
            self.flush()

    def get(self, key: str) -> Optional[Any]:
        """Get a value by key."""
        start_time = time.time()
        total_bytes_read = 0
        
        # 1) check memtable
        v = self.mem.get(key)
        if v is not None:
            result = None if v["t"] == 1 else v["v"]
            latency_ms = (time.time() - start_time) * 1000
            # Memtable read: no disk I/O, but we still count as 0 bytes
            self.metrics.record_read(latency_ms, bytes_read=0)
            return result

        # 2) check SSTables level by level (newest first)
        for level in self.levels:
            for sst_id in level:  # Within level, check in order
                sst, was_cached = self._load_sstable(sst_id)
                rec, bytes_read = sst.get(key)
                
                # Count bytes read from data file
                total_bytes_read += bytes_read
                
                # Only count index/bloom filter bytes if NOT cached (first load)
                if not was_cached:
                    dat_path, idx_path, bloom_path = self._sst_paths(sst_id)
                    if os.path.exists(idx_path):
                        total_bytes_read += os.path.getsize(idx_path)
                    if os.path.exists(bloom_path):
                        total_bytes_read += os.path.getsize(bloom_path)
                
                if rec is None:
                    continue  # Key not found in this SSTable, try next
                
                # Found the key!
                result = None if rec["t"] == 1 else rec["v"]
                latency_ms = (time.time() - start_time) * 1000
                self.metrics.record_read(latency_ms, bytes_read=total_bytes_read)
                return result
        
        latency_ms = (time.time() - start_time) * 1000
        self.metrics.record_read(latency_ms, bytes_read=total_bytes_read)
        return None

    def scan(self, start_key: str, end_key: Optional[str] = None) -> Iterator[Tuple[str, Any]]:
        """
        Range query: scan keys from start_key to end_key (inclusive).
        If end_key is None, scan to the end.
        
        Returns iterator of (key, value) tuples.
        """
        # Collect all records from memtable and SSTables
        seen_keys = set()
        results = []
        
        # Check memtable
        for key in self.mem_keys_sorted:
            if key < start_key:
                continue
            if end_key is not None and key > end_key:
                break
            entry = self.mem[key]
            if entry["t"] != 1:  # Not a tombstone
                results.append((key, entry["v"]))
            seen_keys.add(key)
        
        # Check SSTables (newest to oldest)
        for level in self.levels:
            for sst_id in level:
                sst, _ = self._load_sstable(sst_id)  # Unpack tuple, ignore was_cached
                for rec in sst.scan(start_key, end_key):
                    key = rec["k"]
                    # Skip if we've already seen a newer value
                    if key in seen_keys:
                        continue
                    if rec["t"] != 1:  # Not a tombstone
                        results.append((key, rec["v"]))
                    seen_keys.add(key)
        
        # Sort by key and yield
        results.sort(key=lambda x: x[0])
        for key, value in results:
            yield key, value

    def flush(self) -> None:
        """
        Write memtable to a new SSTable (sorted by key), then clear memtable.
        """
        if not self.mem:
            return

        start_time = time.time()
        sst_id = f"{now_ms()}_{uuid.uuid4().hex[:8]}"
        dat_path, idx_path, bloom_path = self._sst_paths(sst_id)

        # Create bloom filter if enabled
        bloom_filter = None
        if self.enable_bloom_filter:
            bloom_filter = BloomFilter(capacity=self.bloom_capacity, error_rate=self.bloom_error_rate)

        # write sorted records
        idx = SparseIndex()
        count = 0
        bytes_written = 0

        with open(dat_path, "wb") as df:
            for k in self.mem_keys_sorted:
                entry = self.mem[k]
                rec = {"k": k, "t": entry["t"], "v": entry["v"]}
                off = df.tell()
                line = (json.dumps(rec, separators=(",", ":")) + "\n").encode("utf-8")
                df.write(line)
                bytes_written += len(line)

                # Add to bloom filter
                if bloom_filter is not None:
                    bloom_filter.add(k)

                if count % self.sparse_step == 0:
                    idx.entries.append((k, off))
                count += 1
            fsync_file(df)

        with open(idx_path, "w", encoding="utf-8") as inf:
            json.dump(idx.to_json(), inf)
            fsync_file(inf)
            bytes_written += os.path.getsize(idx_path)

        # Save bloom filter
        if bloom_filter is not None:
            with open(bloom_path, "w", encoding="utf-8") as bf:
                json.dump(bloom_filter.to_json(), bf)
                fsync_file(bf)
            bytes_written += os.path.getsize(bloom_path)

        # Add to level 0 (newest)
        if not self.levels:
            self.levels = [[]]
        self.levels[0].insert(0, sst_id)
        self._update_sst_ids()
        self._save_manifest()

        # Check if level 0 needs compaction
        if self.use_leveled_compaction and len(self.levels[0]) > self.max_sstables_per_level:
            self._compact_level(0)

        # clear memtable + truncate wal
        self.mem.clear()
        self.mem_keys_sorted.clear()
        self._truncate_wal()

        latency_ms = (time.time() - start_time) * 1000
        self.metrics.record_flush(latency_ms, bytes_written)

    def compact_two_oldest(self) -> None:
        """
        Legacy compaction: Merge two OLDEST SSTables into one.
        For leveled compaction, use compact_level() instead.
        """
        if not self.use_leveled_compaction:
            # Use old compaction strategy
            all_ssts = [sst_id for level in self.levels for sst_id in level]
            if len(all_ssts) < 2:
                return
            
            older_id = all_ssts[-1]
            newer_id = all_ssts[-2]
            self._merge_two_sstables(newer_id, older_id)

    def compact_level(self, level: int) -> None:
        """Manually trigger compaction for a specific level."""
        if level < len(self.levels):
            self._compact_level(level)

    # ------------------- Leveled Compaction -------------------

    def _compact_level(self, level: int) -> None:
        """
        Compact a level: merge SSTables in this level with next level.
        Leveled compaction strategy.
        """
        if level >= len(self.levels):
            return
        
        if len(self.levels[level]) <= self.max_sstables_per_level:
            return  # No compaction needed
        
        start_time = time.time()
        
        # Get SSTables to compact from this level
        sstables_to_compact = self.levels[level][:self.max_sstables_per_level]
        
        # Get overlapping SSTables from next level
        next_level = level + 1
        if next_level >= len(self.levels):
            self.levels.append([])
        
        # Find overlapping SSTables in next level
        overlapping = []
        for sst_id in self.levels[next_level]:
            # Simple overlap check: if any key range overlaps
            # For simplicity, we'll merge with all SSTables in next level
            # In production, you'd check key ranges
            overlapping.append(sst_id)
        
        # Merge all SSTables
        all_sstables = sstables_to_compact + overlapping
        if len(all_sstables) < 2:
            return
        
        # Merge into new SSTable
        merged_id = self._merge_multiple_sstables(all_sstables, next_level)
        
        # Remove old SSTables
        for sst_id in sstables_to_compact:
            if sst_id in self.levels[level]:
                self.levels[level].remove(sst_id)
            self._delete_sstable_files(sst_id)
        
        for sst_id in overlapping:
            if sst_id in self.levels[next_level]:
                self.levels[next_level].remove(sst_id)
            self._delete_sstable_files(sst_id)
        
        # Add merged SSTable to next level
        self.levels[next_level].append(merged_id)
        self._update_sst_ids()
        self._save_manifest()
        
        # Check if next level needs compaction
        if len(self.levels[next_level]) > self.max_sstables_per_level:
            self._compact_level(next_level)
        
        latency_ms = (time.time() - start_time) * 1000
        # Estimate bytes (simplified)
        self.metrics.record_compaction(latency_ms, 0, 0)

    def _merge_multiple_sstables(self, sst_ids: List[str], target_level: int) -> str:
        """Merge multiple SSTables into one."""
        merged_id = f"compact_{now_ms()}_{uuid.uuid4().hex[:6]}"
        dat_path, idx_path, bloom_path = self._sst_paths(merged_id)
        
        # Create iterators for all SSTables
        iterators = []
        for sst_id in sst_ids:
            sst, _ = self._load_sstable(sst_id)  # Unpack tuple, ignore was_cached
            iterators.append((sst_id, self._iter_sstable_records(sst.dat_path)))
        
        # Initialize current records
        current_recs = {}
        for sst_id, it in iterators:
            rec = next(it, None)
            if rec is not None:
                current_recs[sst_id] = rec
        
        # Create bloom filter
        bloom_filter = None
        if self.enable_bloom_filter:
            bloom_filter = BloomFilter(capacity=self.bloom_capacity, error_rate=self.bloom_error_rate)
        
        idx = SparseIndex()
        count = 0
        
        with open(dat_path, "wb") as out:
            while current_recs:
                # Find smallest key
                min_key = None
                chosen_sst = None
                for sst_id, rec in current_recs.items():
                    if min_key is None or rec["k"] < min_key:
                        min_key = rec["k"]
                        chosen_sst = sst_id
                
                # Get record with smallest key
                chosen = current_recs[chosen_sst]
                
                # Advance iterator for chosen SSTable
                it = iterators[[sst_id for sst_id, _ in iterators].index(chosen_sst)][1]
                next_rec = next(it, None)
                if next_rec is not None:
                    current_recs[chosen_sst] = next_rec
                else:
                    del current_recs[chosen_sst]
                
                # Skip if we've seen this key from a newer SSTable
                # (In leveled compaction, newer SSTables come first in sst_ids)
                # For simplicity, we keep the first occurrence
                
                # Write record
                off = out.tell()
                out.write((json.dumps(chosen, separators=(",", ":")) + "\n").encode("utf-8"))
                
                if bloom_filter is not None:
                    bloom_filter.add(chosen["k"])
                
                if count % self.sparse_step == 0:
                    idx.entries.append((chosen["k"], off))
                count += 1
            
            fsync_file(out)
        
        # Write index
        with open(idx_path, "w", encoding="utf-8") as inf:
            json.dump(idx.to_json(), inf)
            fsync_file(inf)
        
        # Write bloom filter
        if bloom_filter is not None:
            with open(bloom_path, "w", encoding="utf-8") as bf:
                json.dump(bloom_filter.to_json(), bf)
                fsync_file(bf)
        
        return merged_id

    def _merge_two_sstables(self, newer_id: str, older_id: str) -> None:
        """Legacy: Merge two SSTables (for backward compatibility)."""
        merged_id = self._merge_multiple_sstables([newer_id, older_id], 1)
        
        # Remove old SSTables
        for level in self.levels:
            if newer_id in level:
                level.remove(newer_id)
            if older_id in level:
                level.remove(older_id)
        
        self._delete_sstable_files(newer_id)
        self._delete_sstable_files(older_id)
        
        # Add to level 1
        if len(self.levels) < 2:
            self.levels.append([])
        self.levels[1].append(merged_id)
        self._update_sst_ids()
        self._save_manifest()

    # ------------------- Recovery & Manifest -------------------

    def recover(self) -> None:
        """Replay WAL into memtable (like crash recovery)."""
        if not os.path.exists(self.wal_path):
            return
        with open(self.wal_path, "rb") as f:
            for line in f:
                rec = json.loads(line)
                op = rec.get("op")
                k = rec.get("k")
                if not isinstance(k, str):
                    continue
                if op == "PUT":
                    self._mem_put(k, {"t": 0, "v": rec.get("v")})
                elif op == "DEL":
                    self._mem_put(k, {"t": 1, "v": None})

    def _load_manifest(self) -> None:
        """Load manifest with support for both old and new formats."""
        if not os.path.exists(self.manifest_path):
            self.levels = [[]]
            return
        
        with open(self.manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Support both old format (flat list) and new format (levels)
        if "levels" in data:
            self.levels = data["levels"]
        elif "sst_ids" in data:
            # Convert old format to new format
            self.levels = [data["sst_ids"]]
        else:
            self.levels = [[]]

    def _save_manifest(self) -> None:
        """Save manifest with levels structure."""
        tmp = self.manifest_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({"levels": self.levels}, f)
            fsync_file(f)
        os.replace(tmp, self.manifest_path)

    def _update_sst_ids(self) -> None:
        """Update flat sst_ids list from levels (for backward compatibility)."""
        self.sst_ids = [sst_id for level in self.levels for sst_id in level]

    # ------------------- Internals -------------------

    def _append_wal(self, rec: dict, durable: bool) -> None:
        payload = (json.dumps(rec, separators=(",", ":")) + "\n").encode("utf-8")
        with open(self.wal_path, "ab") as f:
            f.write(payload)
            if durable:
                fsync_file(f)

    def _truncate_wal(self) -> None:
        with open(self.wal_path, "wb") as f:
            fsync_file(f)

    def _mem_put(self, key: str, entry: dict) -> None:
        if key not in self.mem:
            insort(self.mem_keys_sorted, key)
        self.mem[key] = entry

    def _sst_paths(self, sst_id: str) -> Tuple[str, str, str]:
        """Return (dat_path, idx_path, bloom_path)."""
        dat_path = os.path.join(self.dir_path, f"sst_{sst_id}.dat")
        idx_path = os.path.join(self.dir_path, f"sst_{sst_id}.idx")
        bloom_path = os.path.join(self.dir_path, f"sst_{sst_id}.bloom")
        return dat_path, idx_path, bloom_path

    def _load_sstable(self, sst_id: str) -> tuple[SSTable, bool]:
        """
        Load SSTable, using cache if available.
        
        Returns:
            (SSTable, was_cached): Tuple of SSTable and whether it was cached
        """
        # Check cache first
        if sst_id in self._sstable_cache:
            return self._sstable_cache[sst_id], True
        
        # Load from disk
        dat_path, idx_path, bloom_path = self._sst_paths(sst_id)
        bloom_path_to_load = bloom_path if self.enable_bloom_filter else None
        sst = SSTable.load(dat_path, idx_path, bloom_path_to_load)
        
        # Add to cache (simple LRU: evict oldest if cache full)
        if len(self._sstable_cache) >= self._cache_size_limit:
            # Evict oldest SSTable (first in cache)
            oldest = next(iter(self._sstable_cache))
            del self._sstable_cache[oldest]
        
        self._sstable_cache[sst_id] = sst
        return sst, False

    def _iter_sstable_records(self, dat_path: str):
        with open(dat_path, "rb") as f:
            for line in f:
                yield json.loads(line)

    def _delete_sstable_files(self, sst_id: str) -> None:
        """Delete SSTable files and remove from cache."""
        dat_path, idx_path, bloom_path = self._sst_paths(sst_id)
        for p in (dat_path, idx_path, bloom_path):
            if os.path.exists(p):
                os.remove(p)
        # Remove from cache if present
        if sst_id in self._sstable_cache:
            del self._sstable_cache[sst_id]

    def get_metrics(self) -> Metrics:
        """Get metrics object."""
        return self.metrics

    def print_stats(self) -> None:
        """Print statistics."""
        self.metrics.print_stats()

if __name__ == "__main__":
    # Example usage
    db = LSMKV(
        flush_threshold=5,
        sparse_step=2,
        enable_bloom_filter=True,
        use_leveled_compaction=True
    )

    db.put("user:1", {"name": "Hieu"})
    db.put("user:2", {"name": "An"})
    db.put("user:3", {"name": "Binh"})
    db.put("user:2", {"name": "An v2"})
    db.delete("user:3")

    print("get user:2:", db.get("user:2"))
    print("get user:3:", db.get("user:3"))

    # Range query
    print("\nRange query user:1 to user:5:")
    for key, value in db.scan("user:1", "user:5"):
        print(f"  {key}: {value}")

    db.print_stats()
