from __future__ import annotations

from dataclasses import dataclass, field
from bisect import bisect_left
from typing import List, Tuple

@dataclass
class SparseIndex:
    # list of (key, offset) pairs, sorted by key
    entries: List[Tuple[str, int]] = field(default_factory=list)

    def find_start_offset(self, key: str) -> int:
        """
        Find the offset of the block where 'key' would live.
        We return the offset for the greatest indexed key <= target key.
        """
        if not self.entries:
            return 0
        keys = [k for k, _ in self.entries]
        i = bisect_left(keys, key)
        if i == 0:
            return 0
        return self.entries[i - 1][1]

    def to_json(self) -> list:
        return [[k, off] for k, off in self.entries]

    @staticmethod
    def from_json(data: list) -> "SparseIndex":
        idx = SparseIndex()
        idx.entries = [(k, int(off)) for k, off in data]
        return idx
