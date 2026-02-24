import os
import time

TOMBSTONE = {"__tombstone__": True}

def fsync_file(f) -> None:
    f.flush()
    os.fsync(f.fileno())

def now_ms() -> int:
    return int(time.time() * 1000)
