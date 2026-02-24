from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass, field
from bisect import insort
from typing import Optional, Any, Dict, List, Tuple

from utils import fsync_file, now_ms
from sparse_index import SparseIndex
from sstable import SSTable

@dataclass
class LSMKV:
    dir_path: str = "lsm_data"
    wal_path: str = field(init=False)
    manifest_path: str = field(init=False)

    # memtable
    mem: Dict[str, dict] = field(default_factory=dict)
    mem_keys_sorted: List[str] = field(default_factory=list)

    # sstables newest->oldest (paths)
    sst_ids: List[str] = field(default_factory=list)

    # tuning
    flush_threshold: int = 5000          # flush when memtable has this many keys
    sparse_step: int = 50               # index every N keys in SSTable

    def __post_init__(self):
        os.makedirs(self.dir_path, exist_ok=True)
        self.wal_path = os.path.join(self.dir_path, "wal.log")
        self.manifest_path = os.path.join(self.dir_path, "manifest.json")
        self._load_manifest()
        self.recover()

    # ------------------- Public API -------------------

    def put(self, key: str, value: Any, durable: bool = True) -> None:
        self._append_wal({"op": "PUT", "ts": now_ms(), "k": key, "v": value}, durable=durable)
        self._mem_put(key, {"t": 0, "v": value})
        if len(self.mem) >= self.flush_threshold:
            self.flush()

    def delete(self, key: str, durable: bool = True) -> None:
        self._append_wal({"op": "DEL", "ts": now_ms(), "k": key}, durable=durable)
        self._mem_put(key, {"t": 1, "v": None})  # tombstone
        if len(self.mem) >= self.flush_threshold:
            self.flush()

    def get(self, key: str) -> Optional[Any]:
        # 1) check memtable
        v = self.mem.get(key)
        if v is not None:
            return None if v["t"] == 1 else v["v"]

        # 2) check SSTables newest->oldest (newest wins)
        for sst_id in self.sst_ids:
            sst = self._load_sstable(sst_id)
            rec, _ = sst.get(key)  # Unpack tuple (record, bytes_read) - ignore bytes_read
            if rec is None:
                continue
            return None if rec["t"] == 1 else rec["v"]
        return None

    def flush(self) -> None:
        """
        Write memtable to a new SSTable (sorted by key), then clear memtable.
        """
        if not self.mem:
            return

        sst_id = f"{now_ms()}_{uuid.uuid4().hex[:8]}"
        dat_path, idx_path = self._sst_paths(sst_id)

        # write sorted records
        idx = SparseIndex()
        count = 0

        with open(dat_path, "wb") as df:
            for k in self.mem_keys_sorted:
                entry = self.mem[k]
                rec = {"k": k, "t": entry["t"], "v": entry["v"]}
                off = df.tell()
                df.write((json.dumps(rec, separators=(",", ":")) + "\n").encode("utf-8"))

                if count % self.sparse_step == 0:
                    idx.entries.append((k, off))
                count += 1
            fsync_file(df)

        with open(idx_path, "w", encoding="utf-8") as inf:
            json.dump(idx.to_json(), inf)
            fsync_file(inf)

        # update manifest: newest first
        self.sst_ids.insert(0, sst_id)
        self._save_manifest()

        # clear memtable + truncate wal (simple strategy for learning)
        self.mem.clear()
        self.mem_keys_sorted.clear()
        self._truncate_wal()

    def compact_two_oldest(self) -> None:
        """
        Merge two OLDEST SSTables into one. (You can also merge newest+next.)
        Newer records win when keys overlap.
        """
        if len(self.sst_ids) < 2:
            return

        # pick the two oldest (end of list)
        older_id = self.sst_ids[-1]
        newer_id = self.sst_ids[-2]

        older = self._load_sstable(older_id)
        newer = self._load_sstable(newer_id)

        merged_id = f"compact_{now_ms()}_{uuid.uuid4().hex[:6]}"
        dat_path, idx_path = self._sst_paths(merged_id)

        it_new = self._iter_sstable_records(newer.dat_path)
        it_old = self._iter_sstable_records(older.dat_path)

        rec_new = next(it_new, None)
        rec_old = next(it_old, None)

        idx = SparseIndex()
        count = 0

        with open(dat_path, "wb") as out:
            while rec_new is not None or rec_old is not None:
                if rec_old is None:
                    chosen = rec_new
                    rec_new = next(it_new, None)
                elif rec_new is None:
                    chosen = rec_old
                    rec_old = next(it_old, None)
                else:
                    # merge by key (both streams are sorted)
                    if rec_new["k"] < rec_old["k"]:
                        chosen = rec_new
                        rec_new = next(it_new, None)
                    elif rec_new["k"] > rec_old["k"]:
                        chosen = rec_old
                        rec_old = next(it_old, None)
                    else:
                        # same key: NEWER wins
                        chosen = rec_new
                        rec_new = next(it_new, None)
                        rec_old = next(it_old, None)

                # drop overwritten keys already handled by merge ordering
                # keep tombstones (could drop them if you know all older levels compacted)
                off = out.tell()
                out.write((json.dumps(chosen, separators=(",", ":")) + "\n").encode("utf-8"))
                if count % self.sparse_step == 0:
                    idx.entries.append((chosen["k"], off))
                count += 1

            fsync_file(out)
        with open(idx_path, "w", encoding="utf-8") as inf:
            json.dump(idx.to_json(), inf)
            fsync_file(inf)

        # replace: remove two old SSTables, insert merged (as oldest position)
        self._delete_sstable_files(older_id)
        self._delete_sstable_files(newer_id)

        self.sst_ids = self.sst_ids[:-2] + [merged_id]
        self._save_manifest()

    # ------------------- Recovery & Manifest -------------------

    def recover(self) -> None:
        """
        Replay WAL into memtable (like crash recovery).
        """
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
        if not os.path.exists(self.manifest_path):
            self.sst_ids = []
            return
        with open(self.manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.sst_ids = list(data.get("sst_ids", []))

    def _save_manifest(self) -> None:
        tmp = self.manifest_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({"sst_ids": self.sst_ids}, f)
            fsync_file(f)
        os.replace(tmp, self.manifest_path)

    # ------------------- Internals -------------------

    def _append_wal(self, rec: dict, durable: bool) -> None:
        payload = (json.dumps(rec, separators=(",", ":")) + "\n").encode("utf-8")
        with open(self.wal_path, "ab") as f:
            f.write(payload)
            if durable:
                fsync_file(f)

    def _truncate_wal(self) -> None:
        # simplest: truncate to empty after flush
        with open(self.wal_path, "wb") as f:
            fsync_file(f)

    def _mem_put(self, key: str, entry: dict) -> None:
        if key not in self.mem:
            insort(self.mem_keys_sorted, key)
        self.mem[key] = entry

    def _sst_paths(self, sst_id: str) -> Tuple[str, str]:
        dat_path = os.path.join(self.dir_path, f"sst_{sst_id}.dat")
        idx_path = os.path.join(self.dir_path, f"sst_{sst_id}.idx")
        return dat_path, idx_path

    def _load_sstable(self, sst_id: str) -> SSTable:
        dat_path, idx_path = self._sst_paths(sst_id)
        return SSTable.load(dat_path, idx_path)

    def _iter_sstable_records(self, dat_path: str):
        with open(dat_path, "rb") as f:
            for line in f:
                yield json.loads(line)

    def _delete_sstable_files(self, sst_id: str) -> None:
        dat_path, idx_path = self._sst_paths(sst_id)
        for p in (dat_path, idx_path):
            if os.path.exists(p):
                os.remove(p)

if __name__ == "__main__":
    db = LSMKV(flush_threshold=5, sparse_step=2)  # small numbers so you can see flush/compaction fast

    db.put("user:1", {"name": "Hieu"})
    db.put("user:2", {"name": "An"})
    db.put("user:3", {"name": "Binh"})
    db.put("user:2", {"name": "An v2"})  # overwrite
    db.delete("user:3")                  # tombstone

    # triggers flush because threshold=5 keys in mem
    print("get user:2:", db.get("user:2"))
    print("get user:3:", db.get("user:3"))

    # add more to create another SSTable
    db.put("user:4", {"x": 1})
    db.put("user:5", {"x": 2})
    db.put("user:6", {"x": 3})
    db.put("user:7", {"x": 4})
    db.put("user:8", {"x": 5})  # flush again

    print("SSTables newest->oldest:", db.sst_ids)
    print("Compacting two oldest...")
    db.compact_two_oldest()
    print("SSTables newest->oldest:", db.sst_ids)
