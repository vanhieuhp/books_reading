"""
Exercise 4: Fencing Tokens — The Solution to Zombie Writes

DDIA Reference: Chapter 8, "Fencing Tokens" (pp. 180-197)

This exercise demonstrates how fencing tokens prevent zombie writes.
A fencing token is a monotonically increasing number issued with each lease.
The storage service rejects writes with stale tokens.

Key concepts:
  - Lock service issues a monotonically increasing token with each lease
  - Client must include the token with every write
  - Storage service rejects writes with stale tokens
  - Prevents zombie writes even if a process pauses and resumes

Run: python 04_fencing_tokens.py
"""

import sys
import time
from typing import Dict, Optional, Tuple
from dataclasses import dataclass

# Fix Windows terminal encoding for Unicode output
sys.stdout.reconfigure(encoding='utf-8')


# =============================================================================
# CORE COMPONENTS: Fencing Token, Lease, Storage
# =============================================================================

@dataclass
class Lease:
    """A lease with a fencing token."""
    holder_id: str
    token: int  # Monotonically increasing fencing token
    issued_at: float
    duration_seconds: float

    def is_expired(self, current_time: float) -> bool:
        """Check if this lease has expired."""
        return current_time > (self.issued_at + self.duration_seconds)


class LockService:
    """
    A lock service that issues leases with fencing tokens.

    DDIA insight: "The lock service issues a lease with a FENCING TOKEN
    (monotonically increasing number). This token is used to prevent
    zombie writes."
    """

    def __init__(self):
        self.leases: Dict[str, Lease] = {}
        self.next_token = 1  # Monotonically increasing

    def acquire_lease(self, resource_id: str, holder_id: str, duration_seconds: float) -> Optional[Lease]:
        """
        Try to acquire a lease for a resource.

        Returns the lease (with fencing token) if successful, None otherwise.
        """
        current_time = time.time()

        # Check if resource is already leased
        if resource_id in self.leases:
            existing_lease = self.leases[resource_id]
            if not existing_lease.is_expired(current_time):
                return None  # Lease still held

        # Issue new lease with fencing token
        token = self.next_token
        self.next_token += 1

        lease = Lease(
            holder_id=holder_id,
            token=token,
            issued_at=current_time,
            duration_seconds=duration_seconds
        )
        self.leases[resource_id] = lease
        return lease

    def renew_lease(self, resource_id: str, holder_id: str, duration_seconds: float) -> Optional[Lease]:
        """
        Try to renew a lease.

        Returns the renewed lease (with new token) if successful, None otherwise.
        """
        current_time = time.time()

        if resource_id not in self.leases:
            return None

        lease = self.leases[resource_id]

        # Check if lease is held by this holder
        if lease.holder_id != holder_id:
            return None

        # Issue new lease with new token
        token = self.next_token
        self.next_token += 1

        new_lease = Lease(
            holder_id=holder_id,
            token=token,
            issued_at=current_time,
            duration_seconds=duration_seconds
        )
        self.leases[resource_id] = new_lease
        return new_lease


class StorageWithoutFencing:
    """
    Storage service WITHOUT fencing tokens (vulnerable to zombie writes).
    """

    def __init__(self, lock_service: LockService):
        self.lock_service = lock_service
        self.data: Dict[str, str] = {}
        self.write_log: list = []

    def write(self, resource_id: str, holder_id: str, value: str) -> Tuple[bool, str]:
        """
        Try to write a value (without fencing token check).

        This is vulnerable to zombie writes!
        """
        # Only check if lease exists (not if it's valid)
        if resource_id not in self.lock_service.leases:
            return False, "No lease held"

        # Write the value (VULNERABLE!)
        self.data[resource_id] = value
        self.write_log.append({
            'time': time.time(),
            'holder': holder_id,
            'resource': resource_id,
            'value': value,
            'token': None
        })
        return True, "Write successful (no fencing check!)"


class StorageWithFencing:
    """
    Storage service WITH fencing tokens (protected against zombie writes).

    DDIA insight: "The storage service checks the fencing token on every write.
    If the token is stale, the write is rejected."
    """

    def __init__(self, lock_service: LockService):
        self.lock_service = lock_service
        self.data: Dict[str, str] = {}
        self.write_log: list = []
        self.max_token_seen: Dict[str, int] = {}  # Track highest token per resource

    def write(self, resource_id: str, holder_id: str, token: int, value: str) -> Tuple[bool, str]:
        """
        Try to write a value with a fencing token.

        Returns (success, message).
        """
        # Check if token is valid
        if resource_id not in self.max_token_seen:
            self.max_token_seen[resource_id] = 0

        if token <= self.max_token_seen[resource_id]:
            return False, f"Stale token {token} (max seen: {self.max_token_seen[resource_id]})"

        # Update max token seen
        self.max_token_seen[resource_id] = token

        # Write the value
        self.data[resource_id] = value
        self.write_log.append({
            'time': time.time(),
            'holder': holder_id,
            'resource': resource_id,
            'value': value,
            'token': token
        })
        return True, f"Write successful (token {token})"

    def read(self, resource_id: str) -> Optional[str]:
        """Read a value."""
        return self.data.get(resource_id)


class Client:
    """
    A client that holds a lease with a fencing token.
    """

    def __init__(self, client_id: str, lock_service: LockService):
        self.client_id = client_id
        self.lock_service = lock_service
        self.current_lease: Optional[Lease] = None

    def acquire_lease(self, resource_id: str, duration_seconds: float) -> bool:
        """Acquire a lease for a resource."""
        lease = self.lock_service.acquire_lease(resource_id, self.client_id, duration_seconds)
        if lease:
            self.current_lease = lease
            return True
        return False

    def renew_lease(self, resource_id: str, duration_seconds: float) -> bool:
        """Renew the current lease."""
        new_lease = self.lock_service.renew_lease(resource_id, self.client_id, duration_seconds)
        if new_lease:
            self.current_lease = new_lease
            return True
        return False

    def simulate_pause(self, duration_seconds: float):
        """Simulate a process pause (GC, VM suspension, etc.)."""
        time.sleep(duration_seconds)

    def get_token(self) -> Optional[int]:
        """Get the current fencing token."""
        return self.current_lease.token if self.current_lease else None


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


def demo_1_without_fencing():
    """
    Demo 1: Zombie write WITHOUT fencing tokens.

    DDIA concept: "Without fencing tokens, zombie writes can occur."
    """
    print_header("DEMO 1: Zombie Write WITHOUT Fencing Tokens")
    print("""
    Without fencing tokens, the storage service cannot detect zombie writes.
    """)

    lock_service = LockService()
    storage = StorageWithoutFencing(lock_service)
    client1 = Client("Client-1", lock_service)
    client2 = Client("Client-2", lock_service)

    print("  📍 Scenario: GC pause causes zombie write (no fencing)")
    print()

    # Client 1 acquires lease
    print("  Step 1: Client 1 acquires lease (5 second duration)")
    client1.acquire_lease("resource:1", duration_seconds=5)
    print(f"    ✅ Lease acquired (token={client1.get_token()})")

    # Client 1 tries to write
    print("\n  Step 2: Client 1 writes")
    success, msg = storage.write("resource:1", "Client-1", "value_from_client1")
    print(f"    {'✅' if success else '❌'} {msg}")

    # GC pause
    print("\n  Step 3: ⏸️  GC PAUSE FOR 6 SECONDS")
    client1.simulate_pause(6)

    # Client 2 acquires lease
    print("\n  Step 4: Client 2 acquires lease (while Client 1 was paused)")
    client2.acquire_lease("resource:1", duration_seconds=10)
    print(f"    ✅ Lease acquired (token={client2.get_token()})")

    # Client 2 writes
    print("\n  Step 5: Client 2 writes")
    success, msg = storage.write("resource:1", "Client-2", "value_from_client2")
    print(f"    {'✅' if success else '❌'} {msg}")

    # Client 1 resumes and tries to write (ZOMBIE WRITE!)
    print("\n  Step 6: Client 1 resumes and tries to write (ZOMBIE WRITE!)")
    success, msg = storage.write("resource:1", "Client-1", "zombie_write_from_client1")
    print(f"    {'✅' if success else '❌'} {msg}")

    print(f"\n  📊 Final value in storage: {storage.read('resource:1')}")

    print("""
  💥 PROBLEM:
     Client 1's zombie write was ACCEPTED!
     The storage service has no way to detect that the lease expired.
     Data corruption occurred! ❌

     DDIA: "Without fencing tokens, a zombie process can write stale data."
    """)


def demo_2_with_fencing():
    """
    Demo 2: Zombie write WITH fencing tokens (prevented!).

    DDIA concept: "Fencing tokens prevent zombie writes."
    """
    print_header("DEMO 2: Zombie Write WITH Fencing Tokens (Prevented!)")
    print("""
    With fencing tokens, the storage service can detect and reject zombie writes.
    """)

    lock_service = LockService()
    storage = StorageWithFencing(lock_service)
    client1 = Client("Client-1", lock_service)
    client2 = Client("Client-2", lock_service)

    print("  📍 Scenario: GC pause causes zombie write (WITH fencing)")
    print()

    # Client 1 acquires lease
    print("  Step 1: Client 1 acquires lease (5 second duration)")
    client1.acquire_lease("resource:1", duration_seconds=5)
    token1 = client1.get_token()
    print(f"    ✅ Lease acquired (token={token1})")

    # Client 1 tries to write
    print("\n  Step 2: Client 1 writes with token")
    success, msg = storage.write("resource:1", "Client-1", token1, "value_from_client1")
    print(f"    {'✅' if success else '❌'} {msg}")

    # GC pause
    print("\n  Step 3: ⏸️  GC PAUSE FOR 6 SECONDS")
    client1.simulate_pause(6)

    # Client 2 acquires lease
    print("\n  Step 4: Client 2 acquires lease (while Client 1 was paused)")
    client2.acquire_lease("resource:1", duration_seconds=10)
    token2 = client2.get_token()
    print(f"    ✅ Lease acquired (token={token2})")

    # Client 2 writes
    print("\n  Step 5: Client 2 writes with token")
    success, msg = storage.write("resource:1", "Client-2", token2, "value_from_client2")
    print(f"    {'✅' if success else '❌'} {msg}")

    # Client 1 resumes and tries to write (ZOMBIE WRITE!)
    print("\n  Step 6: Client 1 resumes and tries to write (ZOMBIE WRITE!)")
    print(f"    Client 1 still has token={token1} (stale!)")
    success, msg = storage.write("resource:1", "Client-1", token1, "zombie_write_from_client1")
    print(f"    {'✅' if success else '❌'} {msg}")

    print(f"\n  📊 Final value in storage: {storage.read('resource:1')}")

    print("""
  ✅ SOLUTION WORKS:
     Client 1's zombie write was REJECTED!
     The storage service detected the stale token and prevented corruption.

     DDIA: "The fencing token ensures that even if a client doesn't realize
     its lease has expired, the storage system acts as the final safeguard."
    """)


def demo_3_token_sequence():
    """
    Demo 3: Show how tokens are monotonically increasing.

    DDIA concept: "Tokens are monotonically increasing."
    """
    print_header("DEMO 3: Monotonically Increasing Tokens")
    print("""
    Each time a lease is issued or renewed, a new token is generated.
    Tokens are always increasing, never reused.
    """)

    lock_service = LockService()
    client = Client("Client-1", lock_service)

    print("  📍 Scenario: Client acquires and renews leases")
    print()

    tokens = []

    # Acquire lease 1
    print("  Step 1: Client acquires lease")
    client.acquire_lease("resource:1", duration_seconds=1)
    token1 = client.get_token()
    tokens.append(token1)
    print(f"    Token: {token1}")

    # Wait for lease to expire
    time.sleep(1.1)

    # Acquire lease 2
    print("\n  Step 2: Client acquires lease again (after expiry)")
    client.acquire_lease("resource:1", duration_seconds=1)
    token2 = client.get_token()
    tokens.append(token2)
    print(f"    Token: {token2}")

    # Renew lease
    print("\n  Step 3: Client renews lease")
    client.renew_lease("resource:1", duration_seconds=1)
    token3 = client.get_token()
    tokens.append(token3)
    print(f"    Token: {token3}")

    print(f"\n  📊 Token sequence: {tokens}")
    print(f"  ✅ Tokens are monotonically increasing: {tokens == sorted(tokens)}")

    print("""
  💡 KEY INSIGHT:
     Tokens are never reused. Each new lease gets a higher token.
     This ensures that stale tokens can always be detected.
    """)


def demo_4_multiple_resources():
    """
    Demo 4: Fencing tokens work independently per resource.

    DDIA concept: "Tokens are per-resource, not global."
    """
    print_header("DEMO 4: Fencing Tokens Per Resource")
    print("""
    Each resource has its own token sequence.
    Tokens for different resources are independent.
    """)

    lock_service = LockService()
    storage = StorageWithFencing(lock_service)
    client = Client("Client-1", lock_service)

    print("  📍 Scenario: Client holds leases for multiple resources")
    print()

    # Acquire leases for two resources
    print("  Step 1: Client acquires leases for two resources")
    client.acquire_lease("resource:1", duration_seconds=10)
    token1 = client.get_token()
    print(f"    Resource 1: token={token1}")

    client.acquire_lease("resource:2", duration_seconds=10)
    token2 = client.get_token()
    print(f"    Resource 2: token={token2}")

    # Write to both resources
    print("\n  Step 2: Client writes to both resources")
    success1, msg1 = storage.write("resource:1", "Client-1", token1, "value1")
    print(f"    Resource 1: {'✅' if success1 else '❌'} {msg1}")

    success2, msg2 = storage.write("resource:2", "Client-1", token2, "value2")
    print(f"    Resource 2: {'✅' if success2 else '❌'} {msg2}")

    print("""
  💡 KEY INSIGHT:
     Each resource maintains its own token sequence.
     A stale token for resource 1 doesn't affect writes to resource 2.
    """)


def demo_5_comparison_table():
    """
    Demo 5: Comparison of approaches.

    DDIA concept: "Fencing tokens are the practical solution."
    """
    print_header("DEMO 5: Comparison of Approaches")
    print("""
    How do different approaches handle zombie writes?
    """)

    print("""
  ┌─────────────────────────┬──────────────┬──────────────┬──────────────┐
  │ Approach                │ Zombie Write │ Complexity   │ Cost         │
  │                         │ Prevention   │              │              │
  ├─────────────────────────┼──────────────┼──────────────┼──────────────┤
  │ No safeguard            │ ❌ NO        │ Low          │ Free         │
  │ (vulnerable)            │              │              │              │
  ├─────────────────────────┼──────────────┼──────────────┼──────────────┤
  │ Lease checks only       │ ⚠️  PARTIAL  │ Medium       │ Low          │
  │ (can be bypassed)       │              │              │              │
  ├─────────────────────────┼──────────────┼──────────────┼──────────────┤
  │ Fencing tokens          │ ✅ YES       │ Medium       │ Low          │
  │ (practical solution)    │              │              │              │
  ├─────────────────────────┼──────────────┼──────────────┼──────────────┤
  │ Google Spanner TrueTime │ ✅ YES       │ High         │ VERY HIGH    │
  │ (overkill for most)     │              │              │              │
  └─────────────────────────┴──────────────┴──────────────┴──────────────┘

  💡 RECOMMENDATION:
     Use fencing tokens for most distributed systems.
     They provide strong guarantees with reasonable complexity.
    """)


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 80)
    print("  EXERCISE 4: FENCING TOKENS — THE SOLUTION TO ZOMBIE WRITES")
    print("  DDIA Chapter 8: 'Fencing Tokens'")
    print("=" * 80)
    print("""
  This exercise demonstrates how fencing tokens prevent zombie writes.
  A fencing token is a monotonically increasing number issued with each lease.
  The storage service rejects writes with stale tokens.

  Key insight: Fencing tokens are the practical solution to process pause problems.
    """)

    demo_1_without_fencing()
    demo_2_with_fencing()
    demo_3_token_sequence()
    demo_4_multiple_resources()
    demo_5_comparison_table()

    print("\n" + "=" * 80)
    print("  EXERCISE 4 COMPLETE ✅")
    print("=" * 80)
    print("""
  Key Takeaways:

  1. 🔐 Fencing tokens are monotonically increasing numbers
  2. 🛡️  Storage service rejects writes with stale tokens
  3. 🧟 Prevents zombie writes even if a process pauses and resumes
  4. 📊 Tokens are per-resource, not global
  5. ⚖️  Practical solution: good guarantees, reasonable complexity

  You've completed Section 3: Unreliable Clocks! 🎉
  Next: Section 4 - Knowledge, Truth, and Lies (Quorums & Byzantine Faults)
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
