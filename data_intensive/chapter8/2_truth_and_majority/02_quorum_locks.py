"""
Chapter 8: Quorum-Based Distributed Locks

This module demonstrates how quorums are used to implement reliable distributed locks.

Key Concepts:
- A lock is only valid if a MAJORITY of lock service nodes has confirmed it
- Prevents zombie processes from holding stale locks
- Works even with network partitions (one partition can't hold locks)
"""

from typing import Dict, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import time


class LockStatus(Enum):
    """Status of a lock request."""
    ACQUIRED = "acquired"
    DENIED = "denied"
    EXPIRED = "expired"


@dataclass
class Lock:
    """Represents a lock held by a client."""
    lock_id: str
    client_id: str
    acquired_at: float
    ttl: float  # Time to live in seconds
    fencing_token: int  # Monotonically increasing token

    def is_expired(self, current_time: float) -> bool:
        """Check if the lock has expired."""
        return current_time - self.acquired_at > self.ttl

    def __repr__(self) -> str:
        return f"Lock(id={self.lock_id}, client={self.client_id}, token={self.fencing_token})"


@dataclass
class LockServiceNode:
    """A single node in the distributed lock service."""
    node_id: int
    locks: Dict[str, Lock] = field(default_factory=dict)
    next_fencing_token: int = 1

    def acquire_lock(self, lock_id: str, client_id: str, ttl: float, current_time: float) -> Optional[Lock]:
        """
        Try to acquire a lock on this node.

        Returns: Lock object if successful, None if lock is held by another client.
        """
        if lock_id in self.locks:
            existing_lock = self.locks[lock_id]
            if not existing_lock.is_expired(current_time):
                # Lock is still held by another client
                return None
            # Lock expired, remove it
            del self.locks[lock_id]

        # Create new lock with fencing token
        lock = Lock(
            lock_id=lock_id,
            client_id=client_id,
            acquired_at=current_time,
            ttl=ttl,
            fencing_token=self.next_fencing_token
        )
        self.next_fencing_token += 1
        self.locks[lock_id] = lock
        return lock

    def release_lock(self, lock_id: str, client_id: str) -> bool:
        """Release a lock if held by the client."""
        if lock_id in self.locks and self.locks[lock_id].client_id == client_id:
            del self.locks[lock_id]
            return True
        return False


class QuorumLockService:
    """
    Distributed lock service using quorum-based consensus.

    A lock is only considered held if a MAJORITY of nodes confirm it.
    """

    def __init__(self, num_nodes: int):
        self.nodes = [LockServiceNode(i) for i in range(num_nodes)]
        self.quorum_size = (num_nodes // 2) + 1
        self.current_time = time.time()

    def acquire_lock(self, lock_id: str, client_id: str, ttl: float = 10.0) -> Optional[Lock]:
        """
        Acquire a lock by requesting it from all nodes.

        Returns: Lock object if quorum confirms, None otherwise.
        """
        locks_acquired = []

        for node in self.nodes:
            lock = node.acquire_lock(lock_id, client_id, ttl, self.current_time)
            if lock:
                locks_acquired.append(lock)

        # Check if we got a quorum
        if len(locks_acquired) >= self.quorum_size:
            # Return the lock with the highest fencing token
            # (in case of concurrent attempts, the one with higher token wins)
            return max(locks_acquired, key=lambda l: l.fencing_token)
        else:
            # Didn't get quorum, release locks from nodes that granted them
            for node in self.nodes:
                node.release_lock(lock_id, client_id)
            return None

    def release_lock(self, lock_id: str, client_id: str) -> bool:
        """Release a lock from all nodes."""
        released_count = 0
        for node in self.nodes:
            if node.release_lock(lock_id, client_id):
                released_count += 1
        return released_count >= self.quorum_size

    def advance_time(self, seconds: float):
        """Advance the simulated time."""
        self.current_time += seconds

    def check_lock_status(self, lock_id: str) -> Dict:
        """Check the status of a lock across all nodes."""
        status = {
            "lock_id": lock_id,
            "nodes_holding_lock": [],
            "nodes_without_lock": []
        }

        for node in self.nodes:
            if lock_id in node.locks:
                lock = node.locks[lock_id]
                if not lock.is_expired(self.current_time):
                    status["nodes_holding_lock"].append({
                        "node_id": node.node_id,
                        "client_id": lock.client_id,
                        "token": lock.fencing_token
                    })
                else:
                    status["nodes_without_lock"].append(node.node_id)
            else:
                status["nodes_without_lock"].append(node.node_id)

        return status


class ZombieProcessSimulation:
    """
    Demonstrates the zombie process problem and how fencing tokens solve it.

    Zombie: A process that resumed after a pause (GC, VM suspension) and
    still thinks it holds a lease, but the lease has actually expired.
    """

    def __init__(self):
        self.lock_service = QuorumLockService(num_nodes=5)

    def simulate_zombie_without_fencing(self):
        """
        Scenario: Without fencing tokens, a zombie can cause data corruption.
        """
        print("\n### Scenario 1: Zombie WITHOUT Fencing Tokens ###")
        print("(This is BAD - data corruption!)\n")

        # Client A acquires lock
        lock_a = self.lock_service.acquire_lock("resource", "client_a", ttl=5.0)
        print(f"1. Client A acquires lock: {lock_a}")

        # Client A starts critical work
        print("2. Client A begins critical work...")

        # Client A pauses (GC, VM suspension) for 6 seconds
        print("3. Client A pauses for 6 seconds (GC pause)")
        self.lock_service.advance_time(6.0)

        # Lock has expired, Client B acquires it
        lock_b = self.lock_service.acquire_lock("resource", "client_b", ttl=5.0)
        print(f"4. Client B acquires lock: {lock_b}")
        print("5. Client B begins critical work...")

        # Client A resumes
        print("6. Client A resumes from pause")
        print("   Client A still thinks it holds the lock!")
        print("   Client A writes to resource (WRONG!)")
        print("   Client B also writes to resource (WRONG!)")
        print("\n[WARN] DATA CORRUPTION: Both clients wrote during 'exclusive' period!")

    def simulate_zombie_with_fencing(self):
        """
        Scenario: With fencing tokens, the storage layer rejects stale writes.
        """
        print("\n### Scenario 2: Zombie WITH Fencing Tokens ###")
        print("(This is GOOD - data is safe!)\n")

        # Client A acquires lock with token 1
        lock_a = self.lock_service.acquire_lock("resource", "client_a", ttl=5.0)
        print(f"1. Client A acquires lock: {lock_a}")
        token_a = lock_a.fencing_token

        # Client A starts critical work
        print("2. Client A begins critical work...")

        # Client A pauses for 6 seconds
        print("3. Client A pauses for 6 seconds (GC pause)")
        self.lock_service.advance_time(6.0)

        # Lock has expired, Client B acquires it with token 2
        lock_b = self.lock_service.acquire_lock("resource", "client_b", ttl=5.0)
        print(f"4. Client B acquires lock: {lock_b}")
        token_b = lock_b.fencing_token
        print("5. Client B begins critical work...")

        # Client A resumes
        print("6. Client A resumes from pause")
        print(f"   Client A tries to write with token {token_a}")
        print(f"   Storage layer checks: token {token_a} < {token_b}")
        print(f"   Storage layer REJECTS write (stale token!)")
        print(f"\n   Client B writes with token {token_b}")
        print(f"   Storage layer checks: token {token_b} >= {token_b}")
        print(f"   Storage layer ACCEPTS write")
        print("\n[OK] DATA SAFE: Storage layer acted as final safeguard!")


def main():
    """Demonstrate quorum-based distributed locks."""

    print("=" * 60)
    print("QUORUM-BASED DISTRIBUTED LOCKS")
    print("=" * 60)

    # Example 1: Basic lock acquisition
    print("\n### Example 1: Lock Acquisition with Quorum ###")
    lock_service = QuorumLockService(num_nodes=5)

    lock = lock_service.acquire_lock("resource_1", "client_a", ttl=10.0)
    if lock:
        print(f"[OK] Lock acquired: {lock}")
        print(f"  Quorum size: {lock_service.quorum_size}")
    else:
        print("[FAIL] Failed to acquire lock")

    # Example 2: Lock status across nodes
    print("\n### Example 2: Lock Status Across Nodes ###")
    status = lock_service.check_lock_status("resource_1")
    print(f"Lock status for 'resource_1':")
    print(f"  Nodes holding lock: {status['nodes_holding_lock']}")
    print(f"  Nodes without lock: {status['nodes_without_lock']}")

    # Example 3: Lock expiration
    print("\n### Example 3: Lock Expiration ###")
    print("Advancing time by 11 seconds (lock TTL is 10 seconds)...")
    lock_service.advance_time(11.0)
    status = lock_service.check_lock_status("resource_1")
    print(f"Lock status after expiration:")
    print(f"  Nodes holding lock: {status['nodes_holding_lock']}")
    print(f"  Nodes without lock: {status['nodes_without_lock']}")

    # Example 4: Zombie process scenarios
    print("\n" + "=" * 60)
    print("ZOMBIE PROCESS SCENARIOS")
    print("=" * 60)

    sim = ZombieProcessSimulation()
    sim.simulate_zombie_without_fencing()
    sim.simulate_zombie_with_fencing()


if __name__ == "__main__":
    main()
