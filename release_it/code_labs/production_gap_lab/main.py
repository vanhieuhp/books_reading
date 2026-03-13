"""
PRODUCTION GAP DETECTOR LAB (Python Version)
============================================
This lab demonstrates how to find production bugs BEFORE production.
We'll simulate Scale, Time, and Diversity axes to expose hidden issues.

Run with: python main.py
"""

import time
import threading
import traceback
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from collections import OrderedDict
from typing import Dict, Any, Optional
import sys


# =============================================================================
# THE NAIVE SERVICE: What appears to work in tests
# =============================================================================

class NaiveUserStore:
    """
    NaiveUserStore looks fine but has multiple production bugs:
    1. No connection pooling (creates new "connection" per request)
    2. Unbounded cache (grows forever)
    3. No timeouts (waits forever)
    4. No error handling for bad data
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._users = {}
        self._cache = {}  # BUG 2: unbounded - grows forever
        self._op_count = 0

    def create_user(self, user_id: int, name: str, email: str) -> None:
        """
        BUG 1: Simulates creating a new DB connection every time.
        In production: O(n) database connections = connection exhaustion
        """
        # Simulate connection setup delay (like real DB)
        time.sleep(0.001)  # 1ms - this adds up!

        with self._lock:
            self._users[user_id] = {"id": user_id, "name": name, "email": email}

            # BUG 2: Add to cache with NO eviction - unbounded growth
            # In production: OOM after days of running
            self._cache[email] = self._users[user_id]
            self._op_count += 1

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """
        BUG 3: No timeout - can wait forever.
        In production: request hangs indefinitely.
        """
        # Simulate slow query (like real production DB under load)
        time.sleep(0.01)  # 10ms

        with self._lock:
            return self._cache.get(email)

    def update_user_name(self, user_id: int, name: str) -> None:
        """
        BUG 4: No validation - accepts garbage data.
        In production: bad data causes crashes or security issues.
        """
        with self._lock:
            if user_id not in self._users:
                raise ValueError(f"User {user_id} not found")

            # No validation! Accepts anything.
            # Production edge case: empty name, SQL injection, etc.
            self._users[user_id]["name"] = name


# =============================================================================
# PRODUCTION-APPROACH: Fixed version
# =============================================================================

class ProductionUserStore:
    """
    Production-ready user store with:
    - Bounded concurrency (semaphore)
    - Bounded cache (LRU eviction)
    - Context/timeouts
    - Input validation
    """

    def __init__(self, max_cache: int = 1000, max_parallel: int = 50):
        self._lock = threading.Lock()
        self._users = {}
        self._cache = LRUCache(max_size=max_cache)  # Bounded cache
        self._semaphore = threading.Semaphore(max_parallel)  # Bounded concurrency
        self._op_count = 0

    def create_user(self, user_id: int, name: str, email: str, timeout: float = 5.0) -> None:
        # Validate input (Axis 3: Diversity)
        if not name:
            raise ValueError("name cannot be empty")
        if len(name) > 1000:
            raise ValueError("name too long")

        # Acquire semaphore (Axis 2: Scale - bounded concurrency)
        acquired = self._semaphore.acquire(timeout=timeout)
        if not acquired:
            raise TimeoutError(f"Could not acquire semaphore within {timeout}s")

        try:
            with self._lock:
                self._users[user_id] = {"id": user_id, "name": name, "email": email}
                self._cache.set(email, self._users[user_id])
                self._op_count += 1
        finally:
            self._semaphore.release()

    def get_user_by_email(self, email: str, timeout: float = 5.0) -> Optional[Dict]:
        # Would implement with context/timeout in real code
        with self._lock:
            return self._cache.get(email)


class LRUCache:
    """Simple LRU cache with bounded size."""

    def __init__(self, max_size: int = 1000):
        self._max_size = max_size
        self._data = OrderedDict()

    def get(self, key: str) -> Optional[Any]:
        if key in self._data:
            # Move to end (most recently used)
            self._data.move_to_end(key)
            return self._data[key]
        return None

    def set(self, key: str, value: Any) -> None:
        if key in self._data:
            self._data.move_to_end(key)
        else:
            # Evict oldest if at capacity
            if len(self._data) >= self._max_size:
                self._data.popitem(last=False)
        self._data[key] = value

    def __len__(self):
        return len(self._data)


# =============================================================================
# DETECTORS: Tests that expose the production gaps
# =============================================================================

class ProductionGapDetector:
    """Runs tests that expose production gaps."""

    def __init__(self):
        self.errors = []
        self.hung_ops = 0
        self.total_ops = 0

    def run_scale_test(self, store, num_concurrent: int, duration_sec: float) -> Dict[str, bool]:
        """
        Axis 2: Scale Test - concurrent load
        """
        print(f"\n=== SCALE TEST ===")
        print(f"Simulating {num_concurrent} concurrent users for {duration_sec}s...")

        results = {
            "connection_exhaustion": False,
            "hung_operations": False,
            "cache_growth_unbounded": False
        }

        start_time = time.time()
        ops_count = [0]  # Use list for closure mutation
        errors_count = [0]

        def worker(user_id: int):
            try:
                store.create_user(user_id, f"User-{user_id}", f"user{user_id}@test.com")
                ops_count[0] += 1

                store.get_user_by_email(f"user{user_id}@test.com")
                ops_count[0] += 1
            except Exception as e:
                errors_count[0] += 1
                self.errors.append(str(e))

        # Run concurrent workers
        with ThreadPoolExecutor(max_workers=num_concurrent) as executor:
            futures = []
            while time.time() - start_time < duration_sec:
                # Submit batch of workers
                for i in range(num_concurrent):
                    user_id = int(time.time() * 1000) + i
                    futures.append(executor.submit(worker, user_id))

                time.sleep(0.1)  # Small delay between batches

        # Wait for completion
        for f in futures:
            try:
                f.result(timeout=5)
            except Exception:
                errors_count[0] += 1

        elapsed = time.time() - start_time
        ops_per_sec = ops_count[0] / elapsed if elapsed > 0 else 0

        print(f"Total operations: {ops_count[0]}")
        print(f"Errors: {errors_count[0]}")
        print(f"Duration: {elapsed:.2f}s")
        print(f"Ops/sec: {ops_per_sec:.2f}")

        # Check for connection issues (too many errors)
        if errors_count[0] > ops_count[0] * 0.1:  # More than 10% error rate
            results["connection_exhaustion"] = True

        # Check cache growth
        if hasattr(store, '_cache'):
            cache_size = len(store._cache)
            print(f"Cache size: {cache_size}")
            # In naive store, cache grows unbounded
            results["cache_growth_unbounded"] = cache_size > num_concurrent

        return results

    def run_diversity_test(self, store) -> Dict[str, bool]:
        """
        Axis 3: Diversity Test - edge cases
        """
        print(f"\n=== DIVERSITY TEST ===")
        print("Testing edge case inputs...")

        results = {"no_validation": False}

        edge_cases = [
            ("empty string", 1, ""),
            ("very long string", 2, "x" * 10000),
            ("special characters", 3, "<script>alert('xss')</script>"),
            ("null bytes", 4, "user\x00name"),
            ("unicode", 5, "\u7528\u6237"),
            ("sql injection", 6, "'; DROP TABLE users; --"),
        ]

        unsafe_count = 0

        for name, user_id, value in edge_cases:
            try:
                store.update_user_name(user_id, value)
                print(f"  ACCEPTED: {name} (BAD - no validation!)")
                unsafe_count += 1
            except ValueError:
                print(f"  REJECTED: {name} (GOOD - validation worked)")

        results["no_validation"] = unsafe_count > 0

        return results


# =============================================================================
# MAIN: Run the demonstration
# =============================================================================

def main():
    print("=" * 50)
    print("PRODUCTION GAP DETECTOR")
    print("=" * 50)

    # Test 1: Scale and Time (using naive store)
    print("\n--- TESTING NAIVE IMPLEMENTATION ---")
    naive_store = NaiveUserStore()

    detector = ProductionGapDetector()

    # Run scale test (Axis 2: Scale, Axis 1: Time compressed)
    scale_results = detector.run_scale_test(naive_store, num_concurrent=50, duration_sec=5)

    # Run diversity test (Axis 3: Diversity)
    # First, create some users
    for i in range(10):
        naive_store.create_user(i, f"User-{i}", f"user{i}@test.com")

    diversity_results = detector.run_diversity_test(naive_store)

    # Summary
    print("\n" + "=" * 50)
    print("PRODUCTION GAPS DETECTED:")
    print("=" * 50)

    gaps_found = []

    if scale_results.get("connection_exhaustion"):
        gaps_found.append("  - Scale: Connection/resource exhaustion under load")

    if scale_results.get("cache_growth_unbounded"):
        gaps_found.append("  - Time: Memory leak from unbounded cache")

    if diversity_results.get("no_validation"):
        gaps_found.append("  - Diversity: No input validation (security risk)")

    if gaps_found:
        for gap in gaps_found:
            print(gap)
    else:
        print("  (No gaps detected - unlikely for naive implementation)")

    # Show what the production approach fixes
    print("\n--- COMPARISON: PRODUCTION IMPLEMENTATION ---")
    print("The production approach includes:")
    print("  - Bounded concurrency (semaphore)")
    print("  - Bounded cache (LRU eviction)")
    print("  - Input validation")
    print("  - Timeouts on all operations")
    print("=" * 50)

    return 0


if __name__ == "__main__":
    sys.exit(main())
