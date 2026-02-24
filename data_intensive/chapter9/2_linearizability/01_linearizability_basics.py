"""
Chapter 9: Linearizability Basics

This module demonstrates the fundamental principle of linearizability:
"The system behaves as if there is only one copy of the data, and every
operation takes effect atomically at some point between its start and end."

Key Concepts:
- Linearizability is the strongest single-object consistency model
- Once a write completes, ALL subsequent reads must see the new value
- There is a single, global "point in time" where each operation takes effect
- Linearizability implies a total order of all operations
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import time


class OperationType(Enum):
    """Types of operations in the system."""
    READ = "read"
    WRITE = "write"


@dataclass
class Operation:
    """Represents a single operation (read or write)."""
    op_type: OperationType
    client_id: str
    key: str
    value: Optional[int] = None  # For writes
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    result: Optional[int] = None  # For reads

    def duration(self) -> float:
        """Return operation duration in milliseconds."""
        if self.end_time is None:
            return 0
        return (self.end_time - self.start_time) * 1000

    def __repr__(self) -> str:
        if self.op_type == OperationType.WRITE:
            return f"Write({self.client_id}, {self.key}={self.value})"
        else:
            return f"Read({self.client_id}, {self.key}) → {self.result}"


class LinearizableStore:
    """
    A linearizable key-value store.

    This is a SINGLE-THREADED, SINGLE-MACHINE store that serves as the
    reference implementation. In a real distributed system, you'd need
    consensus algorithms (Raft, Paxos) to achieve linearizability.
    """

    def __init__(self):
        self.data: Dict[str, int] = {}
        self.operations: List[Operation] = []
        self.operation_order: List[Tuple[str, str, int]] = []  # (client, key, value)

    def write(self, client_id: str, key: str, value: int) -> Operation:
        """
        Write a value. This operation is atomic and takes effect immediately.
        """
        op = Operation(
            op_type=OperationType.WRITE,
            client_id=client_id,
            key=key,
            value=value,
            start_time=time.time()
        )

        # The write takes effect atomically
        self.data[key] = value
        self.operation_order.append((client_id, key, value))

        op.end_time = time.time()
        self.operations.append(op)
        return op

    def read(self, client_id: str, key: str) -> Operation:
        """
        Read a value. Returns the current value (or None if key doesn't exist).
        """
        op = Operation(
            op_type=OperationType.READ,
            client_id=client_id,
            key=key,
            start_time=time.time()
        )

        # The read returns the current value
        op.result = self.data.get(key)

        op.end_time = time.time()
        self.operations.append(op)
        return op

    def get_state(self) -> Dict[str, int]:
        """Return current state of the store."""
        return self.data.copy()


class NonLinearizableStore:
    """
    A NON-linearizable store that allows stale reads.

    This simulates a system with eventual consistency where replicas
    are not immediately synchronized.
    """

    def __init__(self, num_replicas: int = 3):
        self.replicas: List[Dict[str, int]] = [{} for _ in range(num_replicas)]
        self.operations: List[Operation] = []
        self.sync_delay = 0.1  # Simulated replication delay in seconds

    def write(self, client_id: str, key: str, value: int) -> Operation:
        """
        Write to primary replica. Other replicas sync asynchronously.
        """
        op = Operation(
            op_type=OperationType.WRITE,
            client_id=client_id,
            key=key,
            value=value,
            start_time=time.time()
        )

        # Write to primary (replica 0)
        self.replicas[0][key] = value

        # Other replicas will eventually get the update (simulated)
        # For now, they don't have it yet

        op.end_time = time.time()
        self.operations.append(op)
        return op

    def read(self, client_id: str, key: str, replica_id: int = 0) -> Operation:
        """
        Read from any replica. May return stale data.
        """
        op = Operation(
            op_type=OperationType.READ,
            client_id=client_id,
            key=key,
            start_time=time.time()
        )

        # Read from specified replica (may be stale)
        op.result = self.replicas[replica_id].get(key)

        op.end_time = time.time()
        self.operations.append(op)
        return op

    def sync_replicas(self):
        """Simulate replication delay - sync all replicas."""
        # Copy primary to all replicas
        for i in range(1, len(self.replicas)):
            self.replicas[i].update(self.replicas[0])


def demonstrate_linearizability():
    """
    Demonstrate linearizability with a simple example.

    Timeline:
        0ms          50ms         100ms        150ms
    Client A: ──write(x=1)────────────────|
    Client B:          ──read(x)────|
    Client C:                   ──read(x)──────|

    Linearizable: B reads 1, C reads 1
    Non-linearizable: B reads 0, C reads 1 (violates monotonicity)
    """
    print("=" * 70)
    print("DEMONSTRATION 1: Linearizability vs Non-Linearizability")
    print("=" * 70)

    # Linearizable store
    print("\n--- Linearizable Store ---")
    linear_store = LinearizableStore()

    # Client A writes x=1
    print("Client A: write(x=1)")
    linear_store.write("client_a", "x", 1)

    # Client B reads x (after write completes)
    print("Client B: read(x)")
    read_b = linear_store.read("client_b", "x")
    print(f"  Result: {read_b.result} (expected: 1)")

    # Client C reads x
    print("Client C: read(x)")
    read_c = linear_store.read("client_c", "x")
    print(f"  Result: {read_c.result} (expected: 1)")

    print("\n[OK] Linearizable: Both clients see the new value")

    # Non-linearizable store
    print("\n--- Non-Linearizable Store (Eventual Consistency) ---")
    non_linear_store = NonLinearizableStore(num_replicas=3)

    # Client A writes x=1 to primary
    print("Client A: write(x=1) to primary")
    non_linear_store.write("client_a", "x", 1)

    # Client B reads from replica 1 (hasn't synced yet)
    print("Client B: read(x) from replica 1 (before sync)")
    read_b = non_linear_store.read("client_b", "x", replica_id=1)
    print(f"  Result: {read_b.result} (stale! expected: 1)")

    # Now sync replicas
    non_linear_store.sync_replicas()

    # Client C reads from replica 1 (now synced)
    print("Client C: read(x) from replica 1 (after sync)")
    read_c = non_linear_store.read("client_c", "x", replica_id=1)
    print(f"  Result: {read_c.result} (now up-to-date)")

    print("\n[WARNING] Non-Linearizable: Client B saw stale data")


def demonstrate_total_order():
    """
    Demonstrate that linearizability implies a total order of operations.

    In a linearizable system, there is a single, global order of all operations
    that is consistent with real-time.
    """
    print("\n" + "=" * 70)
    print("DEMONSTRATION 2: Linearizability Implies Total Order")
    print("=" * 70)

    store = LinearizableStore()

    # Simulate concurrent operations
    print("\nOperations:")
    print("1. Client A: write(x=1)")
    store.write("client_a", "x", 1)

    print("2. Client B: write(x=2)")
    store.write("client_b", "x", 2)

    print("3. Client C: read(x)")
    read_c = store.read("client_c", "x")
    print(f"   Result: {read_c.result}")

    print("4. Client D: write(x=3)")
    store.write("client_d", "x", 3)

    print("5. Client E: read(x)")
    read_e = store.read("client_e", "x")
    print(f"   Result: {read_e.result}")

    print("\n--- Total Order of Operations ---")
    for i, (client, key, value) in enumerate(store.operation_order, 1):
        print(f"{i}. {client}: write({key}={value})")

    print("\n[OK] There is a single, global order of all operations")
    print("[OK] This order is consistent with real-time")
    print("[OK] All clients see operations in this same order")


def demonstrate_cap_theorem():
    """
    Demonstrate the CAP theorem trade-off.

    CAP Theorem: In the presence of a network partition, you must choose
    between Consistency (linearizability) and Availability.
    """
    print("\n" + "=" * 70)
    print("DEMONSTRATION 3: CAP Theorem Trade-off")
    print("=" * 70)

    print("\nScenario: Network partition between two datacenters")
    print("  Datacenter A: 2 nodes")
    print("  Datacenter B: 2 nodes")
    print("  Quorum size: 3 (need majority of 4 nodes)")

    print("\n--- CP System (Consistent + Partition-tolerant) ---")
    print("During partition:")
    print("  Datacenter A (2 nodes): Cannot reach quorum -> REJECTS writes")
    print("  Datacenter B (2 nodes): Cannot reach quorum -> REJECTS writes")
    print("  Result: System is consistent but unavailable")
    print("  Examples: ZooKeeper, etcd, HBase")

    print("\n--- AP System (Available + Partition-tolerant) ---")
    print("During partition:")
    print("  Datacenter A (2 nodes): Accepts writes -> may be stale")
    print("  Datacenter B (2 nodes): Accepts writes -> may be stale")
    print("  Result: System is available but not linearizable")
    print("  Examples: Cassandra, DynamoDB")

    print("\n[WARNING] You cannot have all three: C, A, and P")
    print("    Network partitions WILL happen, so you must choose C or A")


def demonstrate_linearizability_cost():
    """
    Demonstrate the performance cost of linearizability.

    To guarantee linearizability, every write must wait for a round-trip
    to a quorum of replicas. This adds latency.
    """
    print("\n" + "=" * 70)
    print("DEMONSTRATION 4: Performance Cost of Linearizability")
    print("=" * 70)

    print("\nLinearizable Write (requires quorum confirmation):")
    print("  1. Client sends write to leader")
    print("  2. Leader sends to all replicas")
    print("  3. Wait for majority (quorum) to acknowledge")
    print("  4. Leader confirms to client")
    print("  Latency: ~2 * network_round_trip_time")

    print("\nNon-Linearizable Write (async replication):")
    print("  1. Client sends write to primary")
    print("  2. Primary acknowledges immediately")
    print("  3. Primary sends to replicas asynchronously")
    print("  Latency: ~1 * network_round_trip_time")

    print("\nExample with 3 replicas across 3 datacenters:")
    print("  Network latency between datacenters: 50ms")
    print("  Linearizable write: ~100ms (2 round-trips)")
    print("  Non-linearizable write: ~50ms (1 round-trip)")
    print("\n[WARNING] Linearizability has 2x latency cost in this scenario")


def demonstrate_compare_and_set():
    """
    Demonstrate compare-and-set (CAS) operation, which requires linearizability.

    CAS is used for unique constraints: "Set this value only if it's currently X"
    """
    print("\n" + "=" * 70)
    print("DEMONSTRATION 5: Compare-and-Set (CAS) Requires Linearizability")
    print("=" * 70)

    print("\nUse case: Registering a unique username")
    print("  Two users try to register 'alice' concurrently")
    print("  Exactly one must succeed")

    print("\n--- With Linearizability (CAS) ---")
    store = LinearizableStore()

    print("Client A: CAS(username, '', 'alice')")
    print("  -> Checks if username is empty")
    print("  -> Sets to 'alice'")
    print("  -> Returns: SUCCESS")

    print("Client B: CAS(username, '', 'alice')")
    print("  -> Checks if username is empty")
    print("  -> It's 'alice' (not empty)")
    print("  -> Returns: FAILED (already taken)")

    print("\n[OK] Exactly one client succeeded")
    print("[OK] No race condition")

    print("\n--- Without Linearizability (Eventual Consistency) ---")
    print("Client A: write(username='alice')")
    print("Client B: write(username='alice')")
    print("  Both writes succeed (no check)")
    print("  Replicas eventually converge to one value")
    print("  But which one? Undefined!")
    print("\n[WARNING] Cannot guarantee exactly one succeeds")


if __name__ == "__main__":
    demonstrate_linearizability()
    demonstrate_total_order()
    demonstrate_cap_theorem()
    demonstrate_linearizability_cost()
    demonstrate_compare_and_set()

    print("\n" + "=" * 70)
    print("KEY TAKEAWAYS")
    print("=" * 70)
    print("""
1. Linearizability = "behave as if one copy of data"
2. Once a write completes, ALL subsequent reads see the new value
3. Linearizability implies a total order of all operations
4. CAP Theorem: Choose Consistency or Availability during partitions
5. Linearizability has performance cost (requires quorum confirmation)
6. Used for: leader election, unique constraints, cross-channel dependencies
7. Implemented via: consensus algorithms (Raft, Paxos), single-leader replication
    """)
