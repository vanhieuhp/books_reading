"""
Distributed Locks with ZooKeeper

This module demonstrates how to implement distributed locks using ZooKeeper.

Key concepts:
- Ephemeral nodes for automatic lock release
- Watches for reactive lock acquisition
- Fencing tokens to prevent zombie writes

Pattern:
1. Process tries to create /locks/resource (ephemeral)
2. If successful → process holds the lock
3. Other processes wait for the lock to be deleted
4. If lock holder crashes → lock auto-deleted → next process acquires lock
"""

from kazoo.client import KazooClient
from kazoo.exceptions import NodeExistsError, NoNodeError
import time
import json
import threading


class DistributedLock:
    """Distributed lock using ZooKeeper."""

    def __init__(self, resource_name, node_id, hosts="127.0.0.1:2181"):
        """
        Initialize distributed lock.

        Args:
            resource_name: Name of the resource to lock
            node_id: Unique identifier for this node
            hosts: ZooKeeper hosts
        """
        self.resource_name = resource_name
        self.node_id = node_id
        self.zk = KazooClient(hosts=hosts)
        self.zk.start()
        self.lock_path = f"/locks/{resource_name}"
        self.zk.ensure_path("/locks")
        self.is_locked = False
        self.lock_token = None

    def acquire(self, timeout=None):
        """
        Acquire the lock.

        Args:
            timeout: Maximum time to wait for lock (seconds)

        Returns:
            True if lock acquired, False if timeout
        """
        lock_data = json.dumps({
            "node_id": self.node_id,
            "acquired_at": time.time()
        }).encode()

        start_time = time.time()

        while True:
            try:
                # Try to create the lock node (ephemeral)
                self.zk.create(self.lock_path, lock_data, ephemeral=True)
                self.is_locked = True
                self.lock_token = self.node_id
                print(f"✓ [{self.node_id}] Acquired lock on {self.resource_name}")
                return True
            except NodeExistsError:
                # Lock is held by someone else
                print(f"✗ [{self.node_id}] Lock held by someone else, waiting...")

                # Check timeout
                if timeout and (time.time() - start_time) > timeout:
                    print(f"✗ [{self.node_id}] Lock acquisition timeout")
                    return False

                # Wait for lock to be released
                self._wait_for_lock_release()

    def _wait_for_lock_release(self):
        """Wait for the lock to be released."""
        def on_lock_released(event):
            print(f"  [{self.node_id}] Lock released! Event: {event}")

        try:
            self.zk.exists(self.lock_path, watch=on_lock_released)
            # Wait for watch to fire
            time.sleep(0.1)
        except NoNodeError:
            # Lock already released
            pass

    def release(self):
        """
        Release the lock.

        Returns:
            True if released, False otherwise
        """
        if not self.is_locked:
            print(f"✗ [{self.node_id}] Lock not held")
            return False

        try:
            self.zk.delete(self.lock_path)
            self.is_locked = False
            self.lock_token = None
            print(f"✓ [{self.node_id}] Released lock on {self.resource_name}")
            return True
        except NoNodeError:
            print(f"✗ [{self.node_id}] Lock not found")
            return False

    def is_locked_by_me(self):
        """Check if lock is held by this node."""
        return self.is_locked

    def get_lock_holder(self):
        """Get the node ID of the lock holder."""
        try:
            data, _ = self.zk.get(self.lock_path)
            lock_info = json.loads(data.decode())
            return lock_info["node_id"]
        except NoNodeError:
            return None

    def close(self):
        """Close the ZooKeeper connection."""
        if self.is_locked:
            self.release()
        self.zk.stop()
        print(f"✓ [{self.node_id}] Closed ZooKeeper connection")


class CriticalSection:
    """Context manager for critical sections protected by a lock."""

    def __init__(self, lock):
        """Initialize critical section."""
        self.lock = lock

    def __enter__(self):
        """Acquire lock on entry."""
        self.lock.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Release lock on exit."""
        self.lock.release()


def example_simple_lock():
    """Example: Simple lock acquisition and release."""
    print("\n" + "="*60)
    print("Example 1: Simple Lock Acquisition")
    print("="*60)

    lock = DistributedLock("database", "node1")

    # Acquire lock
    print("\nAcquiring lock...")
    if lock.acquire():
        print("✓ Lock acquired")

        # Do critical work
        print("\nDoing critical work...")
        time.sleep(2)

        # Release lock
        print("\nReleasing lock...")
        lock.release()

    lock.close()


def example_lock_contention():
    """Example: Multiple nodes contending for a lock."""
    print("\n" + "="*60)
    print("Example 2: Lock Contention")
    print("="*60)

    # Create 3 nodes
    locks = [
        DistributedLock("resource", "node1"),
        DistributedLock("resource", "node2"),
        DistributedLock("resource", "node3")
    ]

    # All nodes try to acquire lock
    print("\nAll nodes trying to acquire lock...")

    def try_lock(lock):
        if lock.acquire(timeout=5):
            print(f"  [{lock.node_id}] Doing critical work...")
            time.sleep(2)
            lock.release()
        else:
            print(f"  [{lock.node_id}] Failed to acquire lock")

    threads = []
    for lock in locks:
        thread = threading.Thread(target=try_lock, args=(lock,))
        threads.append(thread)
        thread.start()

    # Wait for all threads
    for thread in threads:
        thread.join()

    # Clean up
    for lock in locks:
        lock.close()


def example_lock_holder_failure():
    """Example: Lock holder failure and automatic release."""
    print("\n" + "="*60)
    print("Example 3: Lock Holder Failure")
    print("="*60)

    # Create 2 nodes
    lock1 = DistributedLock("resource", "node1")
    lock2 = DistributedLock("resource", "node2")

    # Node 1 acquires lock
    print("\nNode 1 acquiring lock...")
    lock1.acquire()

    # Node 2 tries to acquire lock (will wait)
    print("\nNode 2 trying to acquire lock (will wait)...")

    def try_lock2():
        if lock2.acquire(timeout=10):
            print(f"  [node2] Acquired lock!")
            lock2.release()

    thread = threading.Thread(target=try_lock2)
    thread.start()

    # Wait a bit
    time.sleep(1)

    # Simulate node 1 failure (close connection)
    print("\nSimulating node 1 failure (closing connection)...")
    lock1.close()

    # Wait for node 2 to acquire lock
    thread.join()

    # Clean up
    lock2.close()


def example_context_manager():
    """Example: Using lock as context manager."""
    print("\n" + "="*60)
    print("Example 4: Lock as Context Manager")
    print("="*60)

    lock = DistributedLock("resource", "node1")

    print("\nUsing lock as context manager...")
    with CriticalSection(lock):
        print("  Inside critical section")
        print("  Doing critical work...")
        time.sleep(1)

    print("✓ Exited critical section (lock released)")

    lock.close()


def example_sequential_access():
    """Example: Sequential access to resource."""
    print("\n" + "="*60)
    print("Example 5: Sequential Access")
    print("="*60)

    # Create 4 nodes
    locks = [
        DistributedLock("resource", f"node{i}")
        for i in range(1, 5)
    ]

    print("\nAll nodes accessing resource sequentially...")

    def access_resource(lock):
        if lock.acquire(timeout=10):
            print(f"  [{lock.node_id}] Accessing resource...")
            time.sleep(1)
            lock.release()
        else:
            print(f"  [{lock.node_id}] Failed to acquire lock")

    threads = []
    for lock in locks:
        thread = threading.Thread(target=access_resource, args=(lock,))
        threads.append(thread)
        thread.start()

    # Wait for all threads
    for thread in threads:
        thread.join()

    # Clean up
    for lock in locks:
        lock.close()


def example_lock_with_fencing():
    """Example: Lock with fencing token."""
    print("\n" + "="*60)
    print("Example 6: Lock with Fencing Token")
    print("="*60)

    print("\nNote: This example shows the concept of fencing tokens.")
    print("In practice, the storage layer would check the token.")

    lock = DistributedLock("resource", "node1")

    # Acquire lock
    print("\nAcquiring lock...")
    lock.acquire()

    # Get fencing token
    token = lock.lock_token
    print(f"✓ Fencing token: {token}")

    # Simulate write with token
    print(f"\nWriting data with token {token}...")
    print("  Storage layer checks: Is token valid?")
    print(f"  → Yes, token {token} is valid")
    print("  → Write accepted")

    # Release lock
    lock.release()

    # Try to write with old token (should be rejected)
    print(f"\nTrying to write with old token {token}...")
    print("  Storage layer checks: Is token valid?")
    print(f"  → No, token {token} is stale")
    print("  → Write rejected (zombie write prevented!)")

    lock.close()


if __name__ == "__main__":
    print("\n" + "="*60)
    print("Distributed Lock Examples")
    print("="*60)
    print("\nNote: These examples assume ZooKeeper is running on localhost:2181")
    print("Start ZooKeeper with: zkServer.sh start")

    try:
        example_simple_lock()
        example_lock_contention()
        example_lock_holder_failure()
        example_context_manager()
        example_sequential_access()
        example_lock_with_fencing()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("Make sure ZooKeeper is running on localhost:2181")
