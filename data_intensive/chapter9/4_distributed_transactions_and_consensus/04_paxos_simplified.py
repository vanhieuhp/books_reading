#!/usr/bin/env python3
"""
Exercise 4: Paxos Consensus Algorithm (Simplified)

This exercise demonstrates the Paxos consensus algorithm, which is the
foundational consensus algorithm. Paxos is notoriously difficult to understand,
so this is a simplified version that captures the key ideas.

Key concepts:
- Proposers: Propose values
- Acceptors: Accept proposals and remember them
- Learners: Learn the final decision
- Two phases: Prepare phase and Accept phase
- Quorum: Majority of acceptors must agree
- Any two quorums overlap (prevents split-brain)
"""

from typing import List, Optional, Dict, Tuple
from enum import Enum


class ProposalNumber:
    """A proposal number (used for ordering proposals)."""

    def __init__(self, number: int, proposer_id: int):
        self.number = number
        self.proposer_id = proposer_id

    def __lt__(self, other):
        if self.number != other.number:
            return self.number < other.number
        return self.proposer_id < other.proposer_id

    def __le__(self, other):
        return self < other or (self.number == other.number and self.proposer_id == other.proposer_id)

    def __gt__(self, other):
        return not self <= other

    def __ge__(self, other):
        return not self < other

    def __eq__(self, other):
        return self.number == other.number and self.proposer_id == other.proposer_id

    def __repr__(self):
        return f"Proposal({self.number}.{self.proposer_id})"


class Acceptor:
    """An acceptor in Paxos."""

    def __init__(self, acceptor_id: int):
        self.acceptor_id = acceptor_id
        self.promised_proposal: Optional[ProposalNumber] = None
        self.accepted_proposal: Optional[ProposalNumber] = None
        self.accepted_value: Optional[str] = None

    def prepare(self, proposal_number: ProposalNumber) -> Tuple[bool, Optional[ProposalNumber], Optional[str]]:
        """
        Phase 1: Prepare.

        Acceptor promises not to accept any proposal with a lower number.
        Returns (success, accepted_proposal, accepted_value).
        """
        if self.promised_proposal is None or proposal_number > self.promised_proposal:
            self.promised_proposal = proposal_number
            return (True, self.accepted_proposal, self.accepted_value)
        else:
            return (False, None, None)

    def accept(self, proposal_number: ProposalNumber, value: str) -> bool:
        """
        Phase 2: Accept.

        Acceptor accepts the proposal if it hasn't promised a higher proposal.
        Returns True if accepted, False otherwise.
        """
        if self.promised_proposal is None or proposal_number >= self.promised_proposal:
            self.accepted_proposal = proposal_number
            self.accepted_value = value
            return True
        else:
            return False

    def __repr__(self):
        return f"Acceptor({self.acceptor_id})"


class Proposer:
    """A proposer in Paxos."""

    def __init__(self, proposer_id: int, num_acceptors: int):
        self.proposer_id = proposer_id
        self.num_acceptors = num_acceptors
        self.proposal_number = 0

    def propose(self, value: str, acceptors: List[Acceptor]) -> Tuple[bool, Optional[str]]:
        """
        Propose a value using Paxos.

        Returns (success, final_value).
        """
        # Phase 1: Prepare
        self.proposal_number += 1
        proposal = ProposalNumber(self.proposal_number, self.proposer_id)

        print(f"\n  {self}: Phase 1 - Prepare (proposal {proposal})")

        promises = []
        highest_accepted_proposal = None
        highest_accepted_value = None

        for acceptor in acceptors:
            success, accepted_proposal, accepted_value = acceptor.prepare(proposal)
            if success:
                promises.append(acceptor)
                print(f"    {acceptor}: Promises not to accept lower proposals ✅")

                # Track the highest accepted proposal
                if accepted_proposal is not None:
                    if highest_accepted_proposal is None or accepted_proposal > highest_accepted_proposal:
                        highest_accepted_proposal = accepted_proposal
                        highest_accepted_value = accepted_value
            else:
                print(f"    {acceptor}: Rejects (already promised higher) ❌")

        # Check if we got a quorum
        quorum = self.num_acceptors // 2 + 1
        if len(promises) < quorum:
            print(f"  {self}: ❌ Did not get quorum ({len(promises)}/{quorum})")
            return (False, None)

        print(f"  {self}: ✅ Got quorum ({len(promises)}/{quorum})")

        # Phase 2: Accept
        # If any acceptor has accepted a proposal, use that value
        # Otherwise, use our proposed value
        if highest_accepted_value is not None:
            value_to_accept = highest_accepted_value
            print(f"  {self}: Using previously accepted value: {value_to_accept}")
        else:
            value_to_accept = value
            print(f"  {self}: Using proposed value: {value_to_accept}")

        print(f"\n  {self}: Phase 2 - Accept (proposal {proposal}, value {value_to_accept})")

        accepts = []
        for acceptor in promises:
            if acceptor.accept(proposal, value_to_accept):
                accepts.append(acceptor)
                print(f"    {acceptor}: Accepts proposal ✅")
            else:
                print(f"    {acceptor}: Rejects proposal ❌")

        # Check if we got a quorum
        if len(accepts) < quorum:
            print(f"  {self}: ❌ Did not get quorum ({len(accepts)}/{quorum})")
            return (False, None)

        print(f"  {self}: ✅ Got quorum ({len(accepts)}/{quorum})")
        print(f"  {self}: ✅ CONSENSUS REACHED: {value_to_accept}")

        return (True, value_to_accept)

    def __repr__(self):
        return f"Proposer({self.proposer_id})"


def demo_successful_paxos():
    """Demonstrate a successful Paxos consensus."""
    print("\n" + "=" * 80)
    print("DEMO 1: SUCCESSFUL PAXOS CONSENSUS")
    print("=" * 80)

    num_acceptors = 5
    acceptors = [Acceptor(i) for i in range(num_acceptors)]
    proposer = Proposer(0, num_acceptors)

    print(f"\nScenario: Proposer 0 proposes value 'Leader is Node 1'")
    success, value = proposer.propose("Leader is Node 1", acceptors)

    if success:
        print(f"\n✅ Consensus reached: {value}")
    else:
        print(f"\n❌ Consensus failed")


def demo_competing_proposers():
    """Demonstrate competing proposers in Paxos."""
    print("\n" + "=" * 80)
    print("DEMO 2: COMPETING PROPOSERS")
    print("=" * 80)

    num_acceptors = 5
    acceptors = [Acceptor(i) for i in range(num_acceptors)]

    proposer1 = Proposer(1, num_acceptors)
    proposer2 = Proposer(2, num_acceptors)

    print(f"\nScenario: Two proposers competing")
    print(f"  Proposer 1 proposes: 'Leader is Node 1'")
    print(f"  Proposer 2 proposes: 'Leader is Node 2'")

    # Proposer 1 starts
    print(f"\n--- Proposer 1 starts ---")
    success1, value1 = proposer1.propose("Leader is Node 1", acceptors)

    # Proposer 2 starts (with higher proposal number)
    print(f"\n--- Proposer 2 starts ---")
    success2, value2 = proposer2.propose("Leader is Node 2", acceptors)

    print(f"\n--- Results ---")
    if success1:
        print(f"Proposer 1: ✅ {value1}")
    else:
        print(f"Proposer 1: ❌ Failed")

    if success2:
        print(f"Proposer 2: ✅ {value2}")
    else:
        print(f"Proposer 2: ❌ Failed")

    if success1 and success2:
        if value1 == value2:
            print(f"\n✅ Both proposers agreed on the same value: {value1}")
        else:
            print(f"\n❌ Proposers agreed on different values!")


def demo_quorum_overlap():
    """Demonstrate why quorums prevent split-brain."""
    print("\n" + "=" * 80)
    print("DEMO 3: QUORUM OVERLAP (PREVENTS SPLIT-BRAIN)")
    print("=" * 80)

    print("""
Key insight: Any two quorums overlap.

Example with 5 acceptors:
  Quorum 1: {Acceptor 0, Acceptor 1, Acceptor 2}
  Quorum 2: {Acceptor 2, Acceptor 3, Acceptor 4}
  Overlap: {Acceptor 2}

Why this prevents split-brain:
  If Quorum 1 accepts value v, then Acceptor 2 knows about it.
  If Quorum 2 tries to accept value w (w ≠ v), Acceptor 2 will reject it
  (because it already accepted v with a higher proposal number).

This ensures that all quorums will eventually agree on the same value.
    """)

    num_acceptors = 5
    quorum_size = num_acceptors // 2 + 1

    print(f"\nWith {num_acceptors} acceptors:")
    print(f"  Quorum size: {quorum_size}")

    print(f"\nExample quorums:")
    print(f"  Quorum 1: {{Acceptor 0, Acceptor 1, Acceptor 2}}")
    print(f"  Quorum 2: {{Acceptor 2, Acceptor 3, Acceptor 4}}")
    print(f"  Overlap: {{Acceptor 2}}")

    print(f"\nWhy any two quorums overlap:")
    print(f"  Total acceptors: {num_acceptors}")
    print(f"  Quorum size: {quorum_size}")
    print(f"  Minimum overlap: {2 * quorum_size - num_acceptors}")
    print(f"  {2 * quorum_size - num_acceptors} > 0, so overlap is guaranteed ✅")


def demo_paxos_vs_raft():
    """Compare Paxos and Raft."""
    print("\n" + "=" * 80)
    print("DEMO 4: PAXOS VS RAFT")
    print("=" * 80)

    print("""
Paxos:
  - Invented by Leslie Lamport (1989)
  - The foundational consensus algorithm
  - Notoriously difficult to understand and implement
  - Used by Google Chubby
  - Guarantees safety and liveness (with partial synchrony)

Raft:
  - Invented by Diego Ongaro and John Ousterhout (2014)
  - Designed to be more understandable than Paxos
  - Breaks consensus into three sub-problems
  - Used by etcd, CockroachDB, TiKV, Consul
  - Easier to implement and reason about

Key differences:
  Paxos:
    - Proposers, Acceptors, Learners (separate roles)
    - Two phases: Prepare and Accept
    - Can have multiple leaders (liveness issue)
    - Requires leader election on top

  Raft:
    - Followers, Candidates, Leaders (state machine)
    - Three sub-problems: Leader Election, Log Replication, Safety
    - Strong leader (only one leader at a time)
    - Leader election built-in

Correctness:
  - Both Paxos and Raft are correct
  - Both guarantee safety and liveness (with partial synchrony)
  - Both use quorums to prevent split-brain

Practical recommendation:
  - Use Raft if you need to understand the algorithm
  - Use Paxos if you need the original algorithm
  - Use a coordination service (ZooKeeper, etcd, Consul) instead of implementing yourself
    """)


def main():
    print("\n" + "=" * 80)
    print("EXERCISE 4: PAXOS CONSENSUS ALGORITHM (SIMPLIFIED)")
    print("=" * 80)

    demo_successful_paxos()
    demo_competing_proposers()
    demo_quorum_overlap()
    demo_paxos_vs_raft()

    print("\n" + "=" * 80)
    print("KEY TAKEAWAYS")
    print("=" * 80)
    print("""
1. Paxos has three roles:
   - Proposers: Propose values
   - Acceptors: Accept proposals
   - Learners: Learn the final decision

2. Paxos has two phases:
   - Phase 1 (Prepare): Proposer asks acceptors for promises
   - Phase 2 (Accept): Proposer asks acceptors to accept a value

3. Quorums prevent split-brain:
   - Any two quorums overlap
   - If one quorum accepts value v, any other quorum must know about it

4. Paxos is correct but hard to understand:
   - Guarantees safety and liveness (with partial synchrony)
   - Notoriously difficult to implement correctly

5. Raft is easier to understand:
   - Breaks consensus into three sub-problems
   - Strong leader (only one leader at a time)
   - Used by etcd, CockroachDB, TiKV, Consul

6. Both Paxos and Raft use quorums:
   - Majority of nodes must agree
   - Prevents split-brain during network partitions

7. Practical recommendation:
   - Use a coordination service (ZooKeeper, etcd, Consul)
   - Don't implement consensus yourself
    """)


if __name__ == "__main__":
    main()
