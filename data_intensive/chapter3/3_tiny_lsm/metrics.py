"""
Metrics tracking for LSM Tree performance monitoring.
"""

import time
from dataclasses import dataclass, field
from typing import Dict, List
from collections import deque


@dataclass
class Metrics:
    """Track performance metrics for LSM Tree."""
    
    # Counters
    write_count: int = 0
    read_count: int = 0
    delete_count: int = 0
    flush_count: int = 0
    compaction_count: int = 0
    
    # Latencies (in milliseconds)
    write_latencies: deque = field(default_factory=lambda: deque(maxlen=1000))
    read_latencies: deque = field(default_factory=lambda: deque(maxlen=1000))
    flush_latencies: deque = field(default_factory=lambda: deque(maxlen=100))
    compaction_latencies: deque = field(default_factory=lambda: deque(maxlen=100))
    
    # Amplification metrics
    bytes_written: int = 0  # Total bytes written to disk
    bytes_read: int = 0     # Total bytes read from disk
    logical_writes: int = 0 # Logical write operations
    
    def record_write(self, latency_ms: float, bytes_written: int = 0) -> None:
        """Record a write operation."""
        self.write_count += 1
        self.logical_writes += 1
        self.write_latencies.append(latency_ms)
        self.bytes_written += bytes_written
    
    def record_read(self, latency_ms: float, bytes_read: int = 0) -> None:
        """Record a read operation."""
        self.read_count += 1
        self.read_latencies.append(latency_ms)
        self.bytes_read += bytes_read
    
    def record_delete(self) -> None:
        """Record a delete operation."""
        self.delete_count += 1
    
    def record_flush(self, latency_ms: float, bytes_written: int = 0) -> None:
        """Record a flush operation."""
        self.flush_count += 1
        self.flush_latencies.append(latency_ms)
        self.bytes_written += bytes_written
    
    def record_compaction(self, latency_ms: float, bytes_written: int = 0, bytes_read: int = 0) -> None:
        """Record a compaction operation."""
        self.compaction_count += 1
        self.compaction_latencies.append(latency_ms)
        self.bytes_written += bytes_written
        self.bytes_read += bytes_read
    
    def get_write_amplification(self) -> float:
        """Calculate write amplification (physical writes / logical writes)."""
        if self.logical_writes == 0:
            return 0.0
        return self.bytes_written / max(self.logical_writes, 1)
    
    def get_read_amplification(self) -> float:
        """Calculate read amplification (bytes read / bytes requested)."""
        if self.read_count == 0:
            return 0.0
        return self.bytes_read / max(self.read_count, 1)
    
    def get_avg_write_latency(self) -> float:
        """Get average write latency in milliseconds."""
        if not self.write_latencies:
            return 0.0
        return sum(self.write_latencies) / len(self.write_latencies)
    
    def get_avg_read_latency(self) -> float:
        """Get average read latency in milliseconds."""
        if not self.read_latencies:
            return 0.0
        return sum(self.read_latencies) / len(self.read_latencies)
    
    def get_p95_write_latency(self) -> float:
        """Get 95th percentile write latency."""
        if not self.write_latencies:
            return 0.0
        sorted_latencies = sorted(self.write_latencies)
        idx = int(len(sorted_latencies) * 0.95)
        return sorted_latencies[min(idx, len(sorted_latencies) - 1)]
    
    def get_p95_read_latency(self) -> float:
        """Get 95th percentile read latency."""
        if not self.read_latencies:
            return 0.0
        sorted_latencies = sorted(self.read_latencies)
        idx = int(len(sorted_latencies) * 0.95)
        return sorted_latencies[min(idx, len(sorted_latencies) - 1)]
    
    def get_stats(self) -> Dict[str, any]:
        """Get all statistics as a dictionary."""
        return {
            "operations": {
                "writes": self.write_count,
                "reads": self.read_count,
                "deletes": self.delete_count,
                "flushes": self.flush_count,
                "compactions": self.compaction_count,
            },
            "latencies_ms": {
                "write_avg": self.get_avg_write_latency(),
                "write_p95": self.get_p95_write_latency(),
                "read_avg": self.get_avg_read_latency(),
                "read_p95": self.get_p95_read_latency(),
            },
            "amplification": {
                "write": self.get_write_amplification(),
                "read": self.get_read_amplification(),
            },
            "io": {
                "bytes_written": self.bytes_written,
                "bytes_read": self.bytes_read,
            }
        }
    
    def print_stats(self) -> None:
        """Print statistics in a readable format."""
        stats = self.get_stats()
        print("\n" + "=" * 60)
        print("LSM Tree Metrics")
        print("=" * 60)
        print(f"\nOperations:")
        print(f"  Writes:    {stats['operations']['writes']:,}")
        print(f"  Reads:     {stats['operations']['reads']:,}")
        print(f"  Deletes:   {stats['operations']['deletes']:,}")
        print(f"  Flushes:   {stats['operations']['flushes']:,}")
        print(f"  Compactions: {stats['operations']['compactions']:,}")
        print(f"\nLatencies (ms):")
        print(f"  Write avg: {stats['latencies_ms']['write_avg']:.2f}")
        print(f"  Write p95: {stats['latencies_ms']['write_p95']:.2f}")
        print(f"  Read avg:  {stats['latencies_ms']['read_avg']:.2f}")
        print(f"  Read p95:  {stats['latencies_ms']['read_p95']:.2f}")
        print(f"\nAmplification:")
        print(f"  Write: {stats['amplification']['write']:.2f}x")
        print(f"  Read:  {stats['amplification']['read']:.2f}x")
        print(f"\nI/O:")
        print(f"  Bytes written: {stats['io']['bytes_written']:,}")
        print(f"  Bytes read:    {stats['io']['bytes_read']:,}")
        print("=" * 60)
