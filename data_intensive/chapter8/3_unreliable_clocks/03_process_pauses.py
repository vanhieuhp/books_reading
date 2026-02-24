"""
Exercise 3: Process Pauses — The Zombie Write Problem

DDIA Reference: Chapter 8, "Process Pauses" (pp. 155-178)

This exercise demonstrates how process pauses (GC, VM suspension) can cause
a process to act on stale state after resuming, leading to data corruption.

Key concepts:
  - Java/Go processes can freeze for hundreds of milliseconds during GC
  - VMs can be suspended for live migration
  - A paused process doesn't know it was paused
  - Leases can expire while a process is paused
  - A resumed process may act on stale state (zombie writes)

Run: python 03_process_pauses.py
"""

import sys
import time
import threading
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# Fix Windows terminal encoding for Unicode output
sys.stdout.reconfigure(encoding='utf-8')


# =============================================================================
# CORE COMPONENTS: Lease, Storage, Client
# =============================================================================

@dataclass
class Lease:
    """A lease (lock) with an expiration time."""
    holder_id: str
    issued_at: float
    duration_seconds: float

    def is_expired(self, current_time: float) -> bool:
        """Check if this lease has expired."""
        return current_time > (self.issued_at + self.duration_seconds)

    def time_remaining(self, current_time: float) -> float:
        """Get time remaining on this lease."""
        return max(0, (self.issued_at + self.duration_seconds) - current_time)


class LockService:
    """
    A centralized lock service that issues leases.

    DDIA insight: "A lock service issues a lease with a duration.
    The client must renew the lease before it expires."
    """

    def __init__(self):
        self.leases: Dict[str, Lease] = {}

    def acquire_lease(self, resource_id: str, holder_id: str, duration_seconds: float) -> Optional[Lease]:
        """
        Try to acquire a lease for a resource.

        Returns the lease if successful, None if already held.
        """
        current_time = time.time()

        # Check if resource is already leased
        if resource_id in self.leases:
            existing_lease = self.leases[resource_id]
            if not existing_lease.is_expired(current_time):
                return None  # Lease still held

        # Issue new lease
        lease = Lease(holder_id=holder_id, issued_at=current_time, duration_seconds=duration_seconds)
        self.leases[resource_id] = lease
        return lease

    def renew_lease(self, resource_id: str, holder_id: str, duration_seconds: float) -> bool:
        """
        Try to renew a lease.

        Returns True if successful, False if lease is held by someone else.
        """
        current_time = time.time()

        if resource_id not in self.leases:
            return False

        lease = self.leases[resource_id]

        # Check if lease is held by this holder
        if lease.holder_id != holder_id:
            return False

        # Renew the lease
        lease.issued_at = current_time
        return True

    def check_lease(self, resource_id: str, holder_id: str) -> bool:
        """
        Check if a holder still has a valid lease.

        Returns True if lease is valid, False otherwise.
        """
        current_time = time.time()

        if resource_id not in self.leases:
            return False

        lease = self.leases[resource_id]

        # Check if lease is held by this holder and not expired
        return lease.holder_id == holder_id and not lease.is_expired(current_time)


class Storage:
    """
    A storage service that checks leases before allowing writes.

    DDIA insight: "The storage service must check the lease before
    accepting a write. This prevents zombie writes."
    """

    def __init__(self, lock_service: LockService):
        self.lock_service = lock_service
        self.data: Dict[str, str] = {}
        self.write_log: list = []

    def write(self, resource_id: str, holder_id: str, value: str) -> Tuple[bool, str]:
        """
        Try to write a value.

        Returns (success, message).
        """
        # Check if holder has a valid lease
        if not self.lock_service.check_lease(resource_id, holder_id):
            return False, f"Lease expired or not held by {holder_id}"

        # Write the value
        self.data[resource_id] = value
        self.write_log.append({
            'time': time.time(),
            'holder': holder_id,
            'resource': resource_id,
            'value': value
        })
        return True, "Write successful"

    def read(self, resource_id: str) -> Optional[str]:
        """Read a value."""
        return self.data.get(resource_id)


class Client:
    """
    A client that holds a lease and performs work.

    DDIA insight: "A client acquires a lease, does work, and must
    renew the lease before it expires. If the client pauses (GC),
    the lease may expire without the client knowing."
    """

    def __init__(self, client_id: str, lock_service: LockService, storage: Storage):
        self.client_id = client_id
        self.lock_service = lock_service
        self.storage = storage
        self.current_lease: Optional[Lease] = None
        self.is_paused = False
        self.pause_duration = 0

    def acquire_lease(self, resource_id: str, duration_seconds: float) -> bool:
        """Acquire a lease for a resource."""
        lease = self.lock_service.acquire_lease(resource_id, self.client_id, duration_seconds)
        if lease:
            self.current_lease = lease
            return True
        return False

    def renew_lease(self, resource_id: str, duration_seconds: float) -> bool:
        """Renew the current lease."""
        return self.lock_service.renew_lease(resource_id, self.client_id, duration_seconds)

    def simulate_pause(self, duration_seconds: float):
        """Simulate a process pause (GC, VM suspension, etc.)."""
        self.is_paused = True
        self.pause_duration = duration_seconds
        time.sleep(duration_seconds)
        self.is_paused = False

    def do_work(self, resource_id: str, value: str) -> Tuple[bool, str]:
        """
        Do work that requires the lease.

        DDIA: "A client acquires a lease, does work, and must ensure
        the lease hasn't expired before writing."
        """
        # Check if lease is still valid
        if not self.lock_service.check_lease(resource_id, self.client_id):
            return False, "Lease expired!"

        # Do the work (write)
        success, message = self.storage.write(resource_id, self.client_id, value)
        return success, message


# =============================================================================
# DEMONSTRATION SCENARIOS
# =============================================================================

def print_header(title: str):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_section(title: str):
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}")


def demo_1_normal_operation():
    """
    Demo 1: Normal operation without pauses.

    DDIA concept: "When everything works normally, leases prevent conflicts."
    """
    print_header("DEMO 1: Normal Operation (No Pauses)")
    print("""
    When a client holds a lease and completes work before the lease expires,
    everything works correctly.
    """)

    lock_service = LockService()
    storage = Storage(lock_service)
    client1 = Client("Client-1", lock_service, storage)
    client2 = Client("Client-2", lock_service, storage)

    print("  📍 Scenario: Two clients, exclusive access via leases")
    print()

    # Client 1 acquires lease
    print("  Step 1: Client 1 acquires lease (10 second duration)")
    client1.acquire_lease("resource:1", duration_seconds=10)
    print(f"    ✅ Lease acquired")

    # Client 1 does work
    print("\n  Step 2: Client 1 does work")
    success, msg = client1.do_work("resource:1", "value_from_client1")
    print(f"    {'✅' if success else '❌'} {msg}")

    # Client 2 tries to acquire lease (should fail)
    print("\n  Step 3: Client 2 tries to acquire lease (should fail)")
    acquired = client2.acquire_lease("resource:1", duration_seconds=10)
    print(f"    {'✅' if acquired else '❌'} Lease acquired: {acquired}")

    print("""
  💡 KEY INSIGHT:
     Leases provide mutual exclusion. Only one client can hold the lease
     at a time, preventing concurrent writes.
    """)


def demo_2_gc_pause_disaster():
    """
    Demo 2: GC pause causes lease to expire, leading to zombie write.

    DDIA concept: "Process Pauses: The Zombie Write Problem"
    """
    print_header("DEMO 2: GC Pause Causes Zombie Write")
    print("""
    A GC pause can cause a process to miss lease renewal.
    When the process resumes, it may act on stale state.
    """)

    lock_service = LockService()
    storage = Storage(lock_service)
    client1 = Client("Client-1", lock_service, storage)
    client2 = Client("Client-2", lock_service, storage)

    print("  📍 Scenario: GC pause causes lease expiry")
    print()

    # Client 1 acquires lease
    print("  Step 1: Client 1 acquires lease (5 second duration)")
    client1.acquire_lease("resource:1", duration_seconds=5)
    print(f"    ✅ Lease acquired")

    # Client 1 starts work
    print("\n  Step 2: Client 1 starts work")
    print(f"    Lease valid: {lock_service.check_lease('resource:1', 'Client-1')}")

    # GC pause happens
    print("\n  Step 3: ⏸️  GC PAUSE FOR 6 SECONDS")
    print(f"    (Lease duration was only 5 seconds!)")
    client1.simulate_pause(6)

    # Client 1 resumes
    print("\n  Step 4: Client 1 resumes after GC pause")
    print(f"    Lease valid: {lock_service.check_lease('resource:1', 'Client-1')}")

    # Client 2 acquires lease during Client 1's pause
    print("\n  Step 5: Client 2 acquires lease (while Client 1 was paused)")
    client2.acquire_lease("resource:1", duration_seconds=10)
    print(f"    ✅ Lease acquired by Client 2")

    # Client 1 tries to write (zombie write!)
    print("\n  Step 6: Client 1 tries to write (ZOMBIE WRITE!)")
    success, msg = client1.do_work("resource:1", "value_from_client1")
    print(f"    {'✅' if success else '❌'} {msg}")

    # Client 2 writes
    print("\n  Step 7: Client 2 writes (legitimate)")
    success, msg = client2.do_work("resource:1", "value_from_client2")
    print(f"    {'✅' if success else '❌'} {msg}")

    print(f"\n  📊 Final value in storage: {storage.read('resource:1')}")

    print("""
  💥 PROBLEM:
     Client 1 tried to write after its lease expired!
     The storage service rejected the write (good).
     But in a system without proper safeguards, this could cause corruption.

     DDIA: "A process can be paused at any time for unpredictable durations.
     During this pause, the process cannot do anything — it can't even
     respond to heartbeats."
    """)


def demo_3_lease_renewal():
    """
    Demo 3: Proper lease renewal to prevent expiry.

    DDIA concept: "Clients must renew leases before they expire."
    """
    print_header("DEMO 3: Proper Lease Renewal")
    print("""
    To prevent lease expiry, clients must renew leases periodically.
    """)

    lock_service = LockService()
    storage = Storage(lock_service)
    client = Client("Client-1", lock_service, storage)

    print("  📍 Scenario: Client renews lease before expiry")
    print()

    # Acquire lease
    print("  Step 1: Client acquires lease (3 second duration)")
    client.acquire_lease("resource:1", duration_seconds=3)
    print(f"    ✅ Lease acquired")

    # Do work
    print("\n  Step 2: Client does work")
    success, msg = client.do_work("resource:1", "value_1")
    print(f"    {'✅' if success else '❌'} {msg}")

    # Wait 2 seconds (lease still valid)
    print("\n  Step 3: Wait 2 seconds (lease still valid)")
    time.sleep(2)
    print(f"    Lease valid: {lock_service.check_lease('resource:1', 'Client-1')}")

    # Renew lease
    print("\n  Step 4: Client renews lease (before expiry)")
    client.renew_lease("resource:1", duration_seconds=3)
    print(f"    ✅ Lease renewed")

    # Do more work
    print("\n  Step 5: Client does more work")
    success, msg = client.do_work("resource:1", "value_2")
    print(f"    {'✅' if success else '❌'} {msg}")

    print("""
  💡 KEY INSIGHT:
     By renewing the lease before it expires, the client maintains
     exclusive access to the resource.

     In real systems, this renewal happens automatically in a background thread.
    """)


def demo_4_multiple_clients_contention():
    """
    Demo 4: Multiple clients competing for leases.

    DDIA concept: "Leases provide mutual exclusion in distributed systems."
    """
    print_header("DEMO 4: Multiple Clients Competing for Leases")
    print("""
    When multiple clients compete for the same resource, leases ensure
    only one can hold it at a time.
    """)

    lock_service = LockService()
    storage = Storage(lock_service)
    clients = [Client(f"Client-{i+1}", lock_service, storage) for i in range(3)]

    print("  📍 Scenario: Three clients competing for one resource")
    print()

    # Client 1 acquires lease
    print("  Step 1: Client 1 acquires lease")
    clients[0].acquire_lease("resource:1", duration_seconds=2)
    print(f"    ✅ Lease acquired by Client 1")

    # Clients 2 and 3 try to acquire (should fail)
    print("\n  Step 2: Clients 2 and 3 try to acquire (should fail)")
    for i in range(1, 3):
        acquired = clients[i].acquire_lease("resource:1", duration_seconds=2)
        print(f"    {'✅' if acquired else '❌'} Client {i+1}: {acquired}")

    # Wait for Client 1's lease to expire
    print("\n  Step 3: Wait 2 seconds for Client 1's lease to expire")
    time.sleep(2)

    # Client 2 acquires lease
    print("\n  Step 4: Client 2 acquires lease (after Client 1's expired)")
    acquired = clients[1].acquire_lease("resource:1", duration_seconds=2)
    print(f"    {'✅' if acquired else '❌'} Lease acquired by Client 2")

    print("""
  💡 KEY INSIGHT:
     Leases provide a simple but effective way to ensure mutual exclusion
     in distributed systems. When one lease expires, another client can
     acquire it.
    """)


def demo_5_without_lease_checks():
    """
    Demo 5: What happens without lease checks (data corruption).

    DDIA concept: "Without fencing tokens or lease checks, zombie writes occur."
    """
    print_header("DEMO 5: Data Corruption Without Lease Checks")
    print("""
    If the storage service doesn't check leases, zombie writes can occur.
    """)

    print("""
  📍 Scenario: Storage service doesn't check leases

  Thread 1: Acquires lease (expires in 10 seconds)
  Thread 1: Begins critical work
  Thread 1: --- GC PAUSE FOR 15 SECONDS ---
  Thread 1: Resumes, believes it still holds the lease
  Thread 1: Writes data (BUT THE LEASE EXPIRED 5 SECONDS AGO!)

  Thread 2: Acquired the lease during Thread 1's pause
  Thread 2: Also writes data

  Result: Both threads wrote during the "exclusive" lease period.
          Data corruption! ❌

  💡 SOLUTION:
     The storage service must check the lease on every write.
     If the lease is invalid, reject the write.

     Even better: Use fencing tokens (see Exercise 4).
    """)


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 80)
    print("  EXERCISE 3: PROCESS PAUSES — THE ZOMBIE WRITE PROBLEM")
    print("  DDIA Chapter 8: 'Process Pauses'")
    print("=" * 80)
    print("""
  This exercise demonstrates how process pauses (GC, VM suspension) can cause
  a process to act on stale state after resuming, leading to data corruption.

  Key insight: Leases can expire while a process is paused. The process
  doesn't know it was paused and may act on stale state (zombie writes).
    """)

    demo_1_normal_operation()
    demo_2_gc_pause_disaster()
    demo_3_lease_renewal()
    demo_4_multiple_clients_contention()
    demo_5_without_lease_checks()

    print("\n" + "=" * 80)
    print("  EXERCISE 3 COMPLETE ✅")
    print("=" * 80)
    print("""
  Key Takeaways:

  1. 🔒 Leases provide mutual exclusion in distributed systems
  2. ⏸️  Process pauses (GC, VM suspension) can cause lease expiry
  3. 🧟 A paused process may resume and act on stale state (zombie writes)
  4. 🔍 Storage services must check leases before accepting writes
  5. 🔄 Clients must renew leases before they expire

  Next: Run 04_fencing_tokens.py to learn the complete solution
    """)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting...")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
