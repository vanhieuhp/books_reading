#!/usr/bin/env python3
"""
Exercise 5: Consensus with Fencing Tokens

This exercise demonstrates how to combine consensus (for agreement) with
fencing tokens (for enforcement) to build truly safe distributed systems.

Key concepts:
- Use Raft to elect a leader
- Leader issues fencing tokens
- Storage layer checks tokens on every write
- Prevents zombie writes (old leader writing with stale token)
- Combines agreement (consensus) with enforcement (fencing)
"""

from enum import Enum
from typing import Optional, Dict


class NodeState(Enum):
    FOLLOWER = "Follower"
    CANDIDATE = "Candidate"
    LEADER = "Leader"


class RaftLeaderElection:
    """Simplified Raft leader election."""

    def __init__(self, num_nodes: int):
        self.num_nodes = num_nodes
        self.current_term = 0
        self.leader_id: Optional[int] = None
        self.leader_token = 0

    def elect_leader(self, leader_id: int) -> int:
        """
        Elect a new leader and issue a fencing token.

        Returns the fencing token for the new leader.
        """
        self.current_term += 1
        self.leader_id = leader_id
        self.leader_token += 1

        print(f"  Raft: Elected Node {leader_id} as leader (term {self.current_term})")
        print(f"  Raft: Issued fencing token {self.leader_token}")

        return self.leader_token


class StorageWithFencing:
    """Storage layer that enforces fencing tokens."""

    def __init__(self):
        self.data: Dict[str, str] = {}
        self.max_token_seen: Dict[str, int] = {}

    def write(self, resource_id: str, token: int, value: str) -> bool:
        """
        Write data with a fencing token.

        Returns True if write succeeded, False if token is stale.
        """
        if token <= self.max_token_seen.get(resource_id, 0):
            print(f"    Storage: ❌ REJECTED (stale token {token})")
            return False

        self.max_token_seen[resource_id] = token
        self.data[resource_id] = value
        print(f"    Storage: ✅ ACCEPTED (token {token})")
        return True

    def read(self, resource_id: str) -> Optional[str]:
        """Read data."""
        return self.data.get(resource_id)


class LeaderWithFencing:
    """A leader that uses fencing tokens."""

    def __init__(self, leader_id: int, fencing_token: int):
        self.leader_id = leader_id
        self.fencing_token = fencing_token
        self.is_leader = True

    def write(self, storage: StorageWithFencing, resource_id: str, value: str) -> bool:
        """Write data using fencing token."""
        print(f"  Leader {self.leader_id}: Writing '{value}' with token {self.fencing_token}")
        return storage.write(resource_id, self.fencing_token, value)

    def lose_leadership(self):
        """Simulate losing leadership (e.g., network partition)."""
        self.is_leader = False
        print(f"  Leader {self.leader_id}: Lost leadership (network partition)")


def demo_successful_write():
    """Demonstrate a successful write with fencing tokens."""
    print("\n" + "=" * 80)
    print("DEMO 1: SUCCESSFUL WRITE WITH FENCING TOKENS")
    print("=" * 80)

    # Initialize Raft and storage
    raft = RaftLeaderElection(num_nodes=3)
    storage = StorageWithFencing()

    # Elect leader
    print(f"\nStep 1: Elect leader")
    token1 = raft.elect_leader(leader_id=0)

    # Create leader with token
    leader1 = LeaderWithFencing(leader_id=0, fencing_token=token1)

    # Leader writes data
    print(f"\nStep 2: Leader writes data")
    leader1.write(storage, "account_balance", "1000")

    # Verify data was written
    print(f"\nStep 3: Verify data")
    value = storage.read("account_balance")
    print(f"  Storage: account_balance = {value}")


def demo_zombie_write_prevented():
    """Demonstrate how fencing tokens prevent zombie writes."""
    print("\n" + "=" * 80)
    print("DEMO 2: ZOMBIE WRITE PREVENTED BY FENCING TOKENS")
    print("=" * 80)

    # Initialize Raft and storage
    raft = RaftLeaderElection(num_nodes=3)
    storage = StorageWithFencing()

    # Elect first leader
    print(f"\nStep 1: Elect first leader")
    token1 = raft.elect_leader(leader_id=0)
    leader1 = LeaderWithFencing(leader_id=0, fencing_token=token1)

    # First leader writes data
    print(f"\nStep 2: First leader writes data")
    leader1.write(storage, "account_balance", "1000")

    # Network partition: first leader loses leadership
    print(f"\nStep 3: Network partition (first leader loses leadership)")
    leader1.lose_leadership()

    # Elect new leader
    print(f"\nStep 4: Elect new leader")
    token2 = raft.elect_leader(leader_id=1)
    leader2 = LeaderWithFencing(leader_id=1, fencing_token=token2)

    # New leader writes data
    print(f"\nStep 5: New leader writes data")
    leader2.write(storage, "account_balance", "2000")

    # Old leader (still thinks it's leader) tries to write
    print(f"\nStep 6: Old leader tries to write (zombie write)")
    print(f"  Leader 0: Still thinks it's the leader")
    print(f"  Leader 0: Tries to write with token {token1}")
    leader1.write(storage, "account_balance", "1500")

    # Verify final state
    print(f"\nStep 7: Verify final state")
    value = storage.read("account_balance")
    print(f"  Storage: account_balance = {value}")
    print(f"  ✅ Zombie write was prevented!")
    print(f"     Old leader's write was rejected (stale token)")
    print(f"     New leader's write was accepted (current token)")


def demo_multiple_leader_transitions():
    """Demonstrate multiple leader transitions with fencing tokens."""
    print("\n" + "=" * 80)
    print("DEMO 3: MULTIPLE LEADER TRANSITIONS")
    print("=" * 80)

    raft = RaftLeaderElection(num_nodes=5)
    storage = StorageWithFencing()

    leaders = []

    # Simulate multiple leader transitions
    for i in range(3):
        print(f"\n--- Leader Transition {i + 1} ---")

        # Elect new leader
        print(f"Step 1: Elect new leader")
        token = raft.elect_leader(leader_id=i)
        leader = LeaderWithFencing(leader_id=i, fencing_token=token)
        leaders.append(leader)

        # New leader writes data
        print(f"Step 2: New leader writes data")
        leader.write(storage, "counter", str(i + 1))

        # Old leaders try to write (zombie writes)
        if i > 0:
            print(f"Step 3: Old leaders try to write (zombie writes)")
            for j in range(i):
                print(f"  Leader {j}: Tries to write with token {leaders[j].fencing_token}")
                leaders[j].write(storage, "counter", str(j + 100))

    # Verify final state
    print(f"\nFinal state:")
    value = storage.read("counter")
    print(f"  Storage: counter = {value}")
    print(f"  ✅ All zombie writes were prevented!")


def demo_why_fencing_is_necessary():
    """Explain why fencing tokens are necessary even with consensus."""
    print("\n" + "=" * 80)
    print("DEMO 4: WHY FENCING TOKENS ARE NECESSARY")
    print("=" * 80)

    print("""
Consensus ensures AGREEMENT:
  - All nodes agree on who the leader is
  - Raft ensures only one leader per term

But consensus alone is NOT enough!

Problem: A node might think it's the leader but actually isn't.

Scenario:
  1. Node A is elected leader (term 1)
  2. Node A writes data
  3. Network partition: Node A is isolated
  4. Nodes B, C, D elect Node B as new leader (term 2)
  5. Node B writes data
  6. Network partition heals
  7. Node A still thinks it's the leader (term 1)
  8. Node A tries to write data

Result: TWO LEADERS WRITING! ❌

Why this happens:
  - Node A doesn't know about the new leader (was isolated)
  - Node A thinks it's still the leader
  - Node A tries to write data

Solution: FENCING TOKENS

Fencing tokens ensure ENFORCEMENT:
  - Each leader gets a unique, monotonically increasing token
  - Storage layer checks the token on every write
  - Stale tokens are rejected

With fencing tokens:
  - Node A tries to write with token 1
  - Storage: "I've already seen token 2. Token 1 is stale. REJECTED."
  - Node B writes with token 2
  - Storage: "Token 2 is valid. ACCEPTED."

Result: Only the current leader can write! ✅

Key insight:
  Consensus (Raft) + Fencing Tokens = True Safety
  - Consensus ensures agreement on who the leader is
  - Fencing tokens ensure only the current leader can write
    """)


def demo_without_fencing():
    """Demonstrate what happens without fencing tokens."""
    print("\n" + "=" * 80)
    print("DEMO 5: WITHOUT FENCING TOKENS (DANGEROUS!)")
    print("=" * 80)

    print("""
Without fencing tokens, the system is vulnerable to zombie writes.

Scenario:
  1. Node A is leader, writes data
  2. Network partition: Node A is isolated
  3. Node B becomes new leader, writes data
  4. Network partition heals
  5. Node A tries to write data (thinks it's still leader)

Without fencing tokens:
  - Storage accepts writes from both Node A and Node B
  - Data corruption! ❌

With fencing tokens:
  - Storage rejects Node A's write (stale token)
  - Storage accepts Node B's write (current token)
  - Data is safe! ✅

Conclusion:
  Always use fencing tokens with consensus!
  Consensus alone is not enough for safety.
    """)


def main():
    print("\n" + "=" * 80)
    print("EXERCISE 5: CONSENSUS WITH FENCING TOKENS")
    print("=" * 80)

    demo_successful_write()
    demo_zombie_write_prevented()
    demo_multiple_leader_transitions()
    demo_why_fencing_is_necessary()
    demo_without_fencing()

    print("\n" + "=" * 80)
    print("KEY TAKEAWAYS")
    print("=" * 80)
    print("""
1. Consensus (Raft) ensures AGREEMENT:
   - All nodes agree on who the leader is
   - Only one leader per term

2. Fencing tokens ensure ENFORCEMENT:
   - Each leader gets a unique, monotonically increasing token
   - Storage layer checks the token on every write
   - Stale tokens are rejected

3. Consensus + Fencing Tokens = True Safety:
   - Prevents zombie writes (old leader writing with stale token)
   - Prevents data corruption from multiple leaders
   - Ensures only the current leader can write

4. Why both are necessary:
   - Consensus alone: Nodes agree on leader, but leader might not know it lost leadership
   - Fencing tokens alone: Storage enforces tokens, but no agreement on who should have token
   - Together: Agreement (consensus) + Enforcement (fencing) = Safety

5. Real-world systems use this pattern:
   - etcd: Raft + fencing tokens
   - CockroachDB: Raft + fencing tokens
   - Google Spanner: Paxos + TrueTime

6. Best practices:
   - Always use fencing tokens with consensus
   - Don't rely on consensus alone for safety
   - Use a coordination service (ZooKeeper, etcd, Consul)
   - Let them handle consensus and fencing for you
    """)


if __name__ == "__main__":
    main()
