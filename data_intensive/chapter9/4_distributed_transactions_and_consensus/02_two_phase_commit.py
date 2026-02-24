#!/usr/bin/env python3
"""
Exercise 2: Two-Phase Commit (2PC)

This exercise demonstrates the Two-Phase Commit protocol and its fatal flaw:
the blocking problem when the coordinator crashes.

Key concepts:
- Phase 1 (Prepare): Coordinator asks participants if they can commit
- Phase 2 (Commit/Abort): Coordinator tells participants the final decision
- The Fatal Flaw: If coordinator crashes after Phase 1, participants are stuck
- Blocking Protocol: Participants hold locks while waiting for coordinator
- Not True Consensus: Doesn't satisfy the Termination property
"""

from enum import Enum
from typing import List, Optional
import time


class ParticipantState(Enum):
    IDLE = "IDLE"
    PREPARED = "PREPARED"
    COMMITTED = "COMMITTED"
    ABORTED = "ABORTED"
    BLOCKED = "BLOCKED"  # Waiting for coordinator decision


class Participant:
    """A participant in a 2PC transaction."""

    def __init__(self, participant_id: int):
        self.participant_id = participant_id
        self.state = ParticipantState.IDLE
        self.transaction_data = None
        self.locks_held = []

    def prepare(self, transaction_data) -> bool:
        """
        Phase 1: Prepare to commit.

        Returns True if ready to commit, False if cannot commit.
        """
        print(f"  {self}: Preparing transaction...")
        self.transaction_data = transaction_data

        # Simulate checking if we can commit
        # In real systems, this would check constraints, acquire locks, etc.
        can_commit = True

        if can_commit:
            print(f"  {self}: ✅ Ready to commit (wrote to WAL)")
            self.state = ParticipantState.PREPARED
            self.locks_held.append(f"lock_{self.participant_id}")
            return True
        else:
            print(f"  {self}: ❌ Cannot commit")
            return False

    def commit(self):
        """Phase 2: Commit the transaction."""
        print(f"  {self}: Committing...")
        self.state = ParticipantState.COMMITTED
        self.locks_held.clear()
        print(f"  {self}: ✅ Committed")

    def abort(self):
        """Phase 2: Abort the transaction."""
        print(f"  {self}: Aborting...")
        self.state = ParticipantState.ABORTED
        self.transaction_data = None
        self.locks_held.clear()
        print(f"  {self}: ✅ Aborted")

    def block(self):
        """Participant is blocked waiting for coordinator decision."""
        print(f"  {self}: ⏳ BLOCKED (waiting for coordinator decision)")
        self.state = ParticipantState.BLOCKED

    def __repr__(self):
        return f"Participant({self.participant_id})"


class Coordinator:
    """The coordinator in a 2PC transaction."""

    def __init__(self, coordinator_id: int):
        self.coordinator_id = coordinator_id
        self.participants: List[Participant] = []
        self.crashed = False

    def add_participant(self, participant: Participant):
        self.participants.append(participant)

    def execute_transaction(self, transaction_data, crash_after_phase1=False):
        """Execute a 2PC transaction."""
        print(f"\n{self}: Starting 2PC transaction")
        print(f"Transaction data: {transaction_data}")

        # Phase 1: Prepare
        print(f"\n{self}: PHASE 1 - PREPARE")
        print(f"{self}: Asking participants if they can commit...")

        votes = []
        for participant in self.participants:
            vote = participant.prepare(transaction_data)
            votes.append(vote)

        # Check if all participants voted "Yes"
        if not all(votes):
            print(f"\n{self}: ❌ At least one participant voted 'No'")
            print(f"{self}: PHASE 2 - ABORT")
            for participant in self.participants:
                if participant.state == ParticipantState.PREPARED:
                    participant.abort()
            return

        print(f"\n{self}: ✅ All participants voted 'Yes'")

        # Simulate coordinator crash after Phase 1
        if crash_after_phase1:
            print(f"\n{self}: --- COORDINATOR CRASHES ---")
            self.crashed = True
            print(f"\n{self}: Participants are now BLOCKED")
            for participant in self.participants:
                participant.block()
            return

        # Phase 2: Commit
        print(f"\n{self}: PHASE 2 - COMMIT")
        print(f"{self}: Telling participants to commit...")

        for participant in self.participants:
            participant.commit()

        print(f"\n{self}: ✅ Transaction committed successfully")

    def __repr__(self):
        return f"Coordinator({self.coordinator_id})"


def demo_successful_2pc():
    """Demonstrate a successful 2PC transaction."""
    print("\n" + "=" * 80)
    print("DEMO 1: SUCCESSFUL 2PC TRANSACTION")
    print("=" * 80)

    coordinator = Coordinator(0)
    participants = [Participant(i) for i in range(3)]
    for p in participants:
        coordinator.add_participant(p)

    coordinator.execute_transaction("UPDATE account SET balance = balance - 100")

    print(f"\nFinal states:")
    for p in participants:
        print(f"  {p}: {p.state.value}")


def demo_participant_rejects():
    """Demonstrate 2PC when a participant rejects."""
    print("\n" + "=" * 80)
    print("DEMO 2: PARTICIPANT REJECTS (ABORT)")
    print("=" * 80)

    coordinator = Coordinator(0)
    participants = [Participant(i) for i in range(3)]
    for p in participants:
        coordinator.add_participant(p)

    # Simulate one participant rejecting
    original_prepare = participants[1].prepare

    def prepare_reject(transaction_data):
        print(f"  {participants[1]}: ❌ Cannot commit (constraint violation)")
        participants[1].state = ParticipantState.ABORTED
        return False

    participants[1].prepare = prepare_reject

    coordinator.execute_transaction("UPDATE account SET balance = balance - 100")

    print(f"\nFinal states:")
    for p in participants:
        print(f"  {p}: {p.state.value}")


def demo_coordinator_crash():
    """Demonstrate the fatal flaw: coordinator crash after Phase 1."""
    print("\n" + "=" * 80)
    print("DEMO 3: COORDINATOR CRASH (THE FATAL FLAW)")
    print("=" * 80)

    coordinator = Coordinator(0)
    participants = [Participant(i) for i in range(3)]
    for p in participants:
        coordinator.add_participant(p)

    coordinator.execute_transaction(
        "UPDATE account SET balance = balance - 100", crash_after_phase1=True
    )

    print(f"\nFinal states:")
    for p in participants:
        print(f"  {p}: {p.state.value}")
        if p.locks_held:
            print(f"       Locks held: {p.locks_held}")

    print(f"""
⚠️  PROBLEM: PARTICIPANTS ARE BLOCKED

Participants have voted "Yes" and are holding locks.
They are waiting for the coordinator to tell them to commit or abort.

But the coordinator has crashed!

What happens now?
1. Participants cannot commit (coordinator might say "Abort")
2. Participants cannot abort (coordinator might say "Commit")
3. Participants are stuck, holding locks
4. Other transactions cannot access the locked data
5. If coordinator's disk is destroyed, participants may be stuck FOREVER

This is the BLOCKING PROBLEM of 2PC.
    """)


def demo_blocking_cascade():
    """Demonstrate how blocking cascades through the system."""
    print("\n" + "=" * 80)
    print("DEMO 4: BLOCKING CASCADE")
    print("=" * 80)

    print("""
Scenario: Multiple transactions using 2PC

Transaction 1:
  Coordinator 1 crashes after Phase 1
  Participants 1, 2, 3 are BLOCKED (holding locks)

Transaction 2:
  Tries to access data locked by Transaction 1
  Coordinator 2 waits for Participants 1, 2, 3 to respond
  But they are BLOCKED waiting for Coordinator 1
  Coordinator 2 also gets stuck

Transaction 3:
  Tries to access data locked by Transaction 2
  Also gets stuck

Result: CASCADING FAILURES ❌
  The entire system is blocked waiting for Coordinator 1 to recover
    """)


def demo_why_2pc_is_not_consensus():
    """Explain why 2PC is not true consensus."""
    print("\n" + "=" * 80)
    print("WHY 2PC IS NOT TRUE CONSENSUS")
    print("=" * 80)

    print("""
Consensus requires four properties:

1. Uniform Agreement: No two nodes decide differently ✅
   2PC ensures this (all participants commit or all abort)

2. Integrity: No node decides twice ✅
   2PC ensures this (each participant decides once)

3. Validity: If a node decides value v, then v was proposed ✅
   2PC ensures this (only proposed values are committed)

4. Termination: Every non-crashed node eventually decides ❌
   2PC FAILS this property!

Why 2PC fails Termination:
- If the coordinator crashes after Phase 1, participants are stuck
- They cannot decide (cannot commit or abort)
- They wait indefinitely for the coordinator to recover
- If the coordinator's disk is destroyed, they wait FOREVER

Therefore, 2PC is NOT a true consensus algorithm.

Real consensus algorithms (Paxos, Raft) satisfy all four properties.
They are NON-BLOCKING: even if the leader crashes, the system can still decide.
    """)


def main():
    print("\n" + "=" * 80)
    print("EXERCISE 2: TWO-PHASE COMMIT (2PC)")
    print("=" * 80)

    demo_successful_2pc()
    demo_participant_rejects()
    demo_coordinator_crash()
    demo_blocking_cascade()
    demo_why_2pc_is_not_consensus()

    print("\n" + "=" * 80)
    print("KEY TAKEAWAYS")
    print("=" * 80)
    print("""
1. 2PC has two phases: Prepare and Commit
2. Phase 1: Coordinator asks participants if they can commit
3. Phase 2: Coordinator tells participants the final decision
4. The Fatal Flaw: If coordinator crashes after Phase 1, participants are stuck
5. Participants hold locks while waiting for coordinator
6. If coordinator's disk is destroyed, participants may be stuck forever
7. 2PC is a BLOCKING protocol (violates Termination property)
8. 2PC is NOT true consensus
9. Real consensus algorithms (Paxos, Raft) are non-blocking
10. Avoid 2PC for critical systems; use consensus-based transactions instead
    """)


if __name__ == "__main__":
    main()
