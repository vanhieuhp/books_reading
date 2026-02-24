#!/usr/bin/env python3
"""
Exercise 3: Raft Consensus Algorithm

This exercise demonstrates the Raft consensus algorithm, which breaks consensus
into three sub-problems:

1. Leader Election: Elect a leader
2. Log Replication: Replicate log entries to followers
3. Safety: Ensure the new leader has all committed entries

Key concepts:
- Followers, Candidates, Leaders
- Terms (epoch numbers)
- Election timeout
- Heartbeats
- Log replication
- Quorum-based commitment
"""

from enum import Enum
from typing import List, Optional, Dict
import random


class NodeState(Enum):
    FOLLOWER = "Follower"
    CANDIDATE = "Candidate"
    LEADER = "Leader"


class LogEntry:
    """A log entry in the Raft log."""

    def __init__(self, term: int, value: str):
        self.term = term
        self.value = value

    def __repr__(self):
        return f"Entry(term={self.term}, value='{self.value}')"


class RaftNode:
    """A node in the Raft consensus algorithm."""

    def __init__(self, node_id: int, num_nodes: int):
        self.node_id = node_id
        self.num_nodes = num_nodes

        # Persistent state
        self.current_term = 0
        self.voted_for: Optional[int] = None
        self.log: List[LogEntry] = []

        # Volatile state
        self.state = NodeState.FOLLOWER
        self.commit_index = 0
        self.last_applied = 0

        # Leader state
        self.next_index: Dict[int, int] = {}
        self.match_index: Dict[int, int] = {}

        # Election state
        self.election_timeout = random.randint(150, 300)  # milliseconds
        self.time_since_last_heartbeat = 0

    def become_candidate(self):
        """Transition to candidate state."""
        self.current_term += 1
        self.state = NodeState.CANDIDATE
        self.voted_for = self.node_id
        print(f"  {self}: Becomes CANDIDATE (term {self.current_term})")

    def become_leader(self):
        """Transition to leader state."""
        self.state = NodeState.LEADER
        print(f"  {self}: Becomes LEADER (term {self.current_term})")

        # Initialize leader state
        for i in range(self.num_nodes):
            if i != self.node_id:
                self.next_index[i] = len(self.log)
                self.match_index[i] = 0

    def become_follower(self, term: int):
        """Transition to follower state."""
        if term > self.current_term:
            self.current_term = term
            self.voted_for = None
        self.state = NodeState.FOLLOWER
        print(f"  {self}: Becomes FOLLOWER (term {self.current_term})")

    def request_vote(self, candidate_id: int, candidate_term: int, candidate_log_length: int) -> bool:
        """
        Handle a vote request from a candidate.

        Returns True if we vote for the candidate, False otherwise.
        """
        # If candidate's term is older, reject
        if candidate_term < self.current_term:
            return False

        # If candidate's term is newer, update our term
        if candidate_term > self.current_term:
            self.current_term = candidate_term
            self.voted_for = None

        # If we haven't voted in this term, and candidate's log is up-to-date, vote
        if self.voted_for is None or self.voted_for == candidate_id:
            if candidate_log_length >= len(self.log):
                self.voted_for = candidate_id
                return True

        return False

    def append_entry(self, leader_id: int, leader_term: int, entries: List[LogEntry]) -> bool:
        """
        Handle an append_entries RPC from the leader.

        Returns True if entries were appended, False otherwise.
        """
        # If leader's term is older, reject
        if leader_term < self.current_term:
            return False

        # If leader's term is newer, update our term
        if leader_term > self.current_term:
            self.current_term = leader_term
            self.voted_for = None

        # Become follower if we're not already
        if self.state != NodeState.FOLLOWER:
            self.become_follower(leader_term)

        # Append entries to log
        for entry in entries:
            self.log.append(entry)

        return True

    def __repr__(self):
        return f"Node({self.node_id})"


def demo_leader_election():
    """Demonstrate Raft leader election."""
    print("\n" + "=" * 80)
    print("DEMO 1: RAFT LEADER ELECTION")
    print("=" * 80)

    num_nodes = 5
    nodes = [RaftNode(i, num_nodes) for i in range(num_nodes)]

    print(f"\nInitial state: All nodes are followers")
    for node in nodes:
        print(f"  {node}: {node.state.value} (term {node.current_term})")

    # Simulate election timeout on Node 1
    print(f"\nElection timeout triggered on Node 1")
    nodes[1].become_candidate()

    # Node 1 requests votes from other nodes
    print(f"\nNode 1 requests votes from peers")
    votes = 1  # Node 1 votes for itself
    for i, node in enumerate(nodes):
        if i != 1:
            if node.request_vote(1, nodes[1].current_term, len(nodes[1].log)):
                votes += 1
                print(f"  {node}: Votes for Node 1 ✅")
            else:
                print(f"  {node}: Rejects Node 1 ❌")

    # Check if Node 1 got majority
    quorum = num_nodes // 2 + 1
    print(f"\nVotes for Node 1: {votes}/{num_nodes}")
    print(f"Quorum needed: {quorum}")

    if votes >= quorum:
        print(f"✅ Node 1 becomes LEADER")
        nodes[1].become_leader()
    else:
        print(f"❌ Node 1 does not have majority")

    # Update other nodes' state
    for i, node in enumerate(nodes):
        if i != 1 and node.state == NodeState.FOLLOWER:
            node.current_term = nodes[1].current_term

    print(f"\nFinal state:")
    for node in nodes:
        print(f"  {node}: {node.state.value} (term {node.current_term})")


def demo_log_replication():
    """Demonstrate Raft log replication."""
    print("\n" + "=" * 80)
    print("DEMO 2: RAFT LOG REPLICATION")
    print("=" * 80)

    num_nodes = 5
    nodes = [RaftNode(i, num_nodes) for i in range(num_nodes)]

    # Make Node 0 the leader
    nodes[0].become_leader()
    nodes[0].current_term = 1
    for i in range(1, num_nodes):
        nodes[i].current_term = 1
        nodes[i].state = NodeState.FOLLOWER

    print(f"\nInitial state:")
    print(f"  Node 0: LEADER (term 1)")
    for i in range(1, num_nodes):
        print(f"  {nodes[i]}: FOLLOWER (term 1)")

    # Leader receives a write from client
    print(f"\nClient writes: 'set x = 5'")
    entry = LogEntry(term=1, value="set x = 5")
    nodes[0].log.append(entry)
    print(f"  Node 0: Appends entry to log: {entry}")

    # Leader replicates entry to followers
    print(f"\nLeader replicates entry to followers")
    for i in range(1, num_nodes):
        if nodes[i].append_entry(0, 1, [entry]):
            print(f"  {nodes[i]}: Appends entry to log ✅")
        else:
            print(f"  {nodes[i]}: Rejects entry ❌")

    # Leader commits entry when majority has it
    print(f"\nLeader checks if entry is replicated on majority")
    replicated_count = 1  # Leader has it
    for i in range(1, num_nodes):
        if len(nodes[i].log) > 0:
            replicated_count += 1

    quorum = num_nodes // 2 + 1
    print(f"Replicated on {replicated_count}/{num_nodes} nodes")
    print(f"Quorum needed: {quorum}")

    if replicated_count >= quorum:
        print(f"✅ Entry is replicated on majority")
        nodes[0].commit_index = len(nodes[0].log) - 1
        print(f"  Leader commits entry")

        # Leader notifies followers to commit
        print(f"\nLeader notifies followers to commit")
        for i in range(1, num_nodes):
            nodes[i].commit_index = len(nodes[i].log) - 1
            print(f"  {nodes[i]}: Commits entry")

    print(f"\nFinal state:")
    for node in nodes:
        print(f"  {node}: log = {node.log}, committed = {node.commit_index}")


def demo_safety():
    """Demonstrate Raft safety: new leader has all committed entries."""
    print("\n" + "=" * 80)
    print("DEMO 3: RAFT SAFETY")
    print("=" * 80)

    print("""
Raft Safety Property:
- A candidate can only be elected leader if its log is at least as up-to-date
  as a majority of nodes.
- This ensures that the new leader never loses committed entries.

Example:
  Node A: log = [entry(term=1), entry(term=2)]
  Node B: log = [entry(term=1)]

  Node A's log is more up-to-date (higher term)
  Node A can be elected leader
  Node B cannot be elected leader (would lose entry(term=2))
    """)

    num_nodes = 3
    nodes = [RaftNode(i, num_nodes) for i in range(num_nodes)]

    # Simulate different log states
    nodes[0].log = [LogEntry(1, "set x = 1"), LogEntry(2, "set x = 2")]
    nodes[1].log = [LogEntry(1, "set x = 1")]
    nodes[2].log = [LogEntry(1, "set x = 1"), LogEntry(2, "set x = 2")]

    print(f"\nLog states:")
    for node in nodes:
        print(f"  {node}: {node.log}")

    # Node 1 becomes candidate
    print(f"\nNode 1 becomes candidate and requests votes")
    nodes[1].become_candidate()

    # Check if Node 1 can be elected
    print(f"\nNode 0 checks if Node 1's log is up-to-date:")
    print(f"  Node 0 log length: {len(nodes[0].log)}")
    print(f"  Node 1 log length: {len(nodes[1].log)}")
    print(f"  Node 1's log is NOT up-to-date (shorter)")
    print(f"  Node 0: Rejects Node 1 ❌")

    print(f"\nNode 2 checks if Node 1's log is up-to-date:")
    print(f"  Node 2 log length: {len(nodes[2].log)}")
    print(f"  Node 1 log length: {len(nodes[1].log)}")
    print(f"  Node 1's log is NOT up-to-date (shorter)")
    print(f"  Node 2: Rejects Node 1 ❌")

    print(f"\n✅ Node 1 cannot be elected (doesn't have majority)")
    print(f"   This prevents Node 1 from losing committed entries")


def demo_term_numbers():
    """Demonstrate why term numbers prevent old leaders from overriding new ones."""
    print("\n" + "=" * 80)
    print("DEMO 4: TERM NUMBERS (EPOCH NUMBERS)")
    print("=" * 80)

    print("""
Term Numbers:
- Each term represents a leadership period
- Terms are monotonically increasing
- If a node receives a message from a leader with a stale term, it ignores it

Why this matters:
- Prevents old leaders from overriding new ones
- Ensures safety during leader transitions

Example:
  Term 0: No leader
  Term 1: Node 0 is leader
  Term 2: Node 1 is leader (after Node 0 crashes)
  Term 3: Node 2 is leader (after Node 1 crashes)

If Node 0 (old leader from Term 1) tries to send a message:
  Node 1: Receives message with term=1
  Node 1: Current term is 2
  Node 1: Ignores message (term is stale)
  Node 1: Sends back message with term=2
  Node 0: Updates its term to 2
  Node 0: Becomes follower
    """)

    num_nodes = 3
    nodes = [RaftNode(i, num_nodes) for i in range(num_nodes)]

    # Simulate term progression
    print(f"\nTerm progression:")

    # Term 1: Node 0 is leader
    nodes[0].current_term = 1
    nodes[0].state = NodeState.LEADER
    nodes[1].current_term = 1
    nodes[2].current_term = 1
    print(f"  Term 1: Node 0 is LEADER")

    # Term 2: Node 1 is leader
    nodes[1].current_term = 2
    nodes[1].state = NodeState.LEADER
    nodes[0].current_term = 2
    nodes[2].current_term = 2
    print(f"  Term 2: Node 1 is LEADER")

    # Node 0 (old leader) tries to send a message
    print(f"\nNode 0 (old leader from Term 1) tries to send a message")
    print(f"  Node 0 term: {nodes[0].current_term}")
    print(f"  Message term: 1 (stale)")

    print(f"\nNode 1 receives message from Node 0:")
    print(f"  Node 1 term: {nodes[1].current_term}")
    print(f"  Message term: 1")
    print(f"  Message term < Node 1 term: {1 < nodes[1].current_term}")
    print(f"  Node 1: Ignores message (term is stale) ✅")


def main():
    print("\n" + "=" * 80)
    print("EXERCISE 3: RAFT CONSENSUS ALGORITHM")
    print("=" * 80)

    demo_leader_election()
    demo_log_replication()
    demo_safety()
    demo_term_numbers()

    print("\n" + "=" * 80)
    print("KEY TAKEAWAYS")
    print("=" * 80)
    print("""
1. Raft breaks consensus into three sub-problems:
   - Leader Election
   - Log Replication
   - Safety

2. Raft has three node states:
   - Follower: Receives messages from leader
   - Candidate: Requests votes in election
   - Leader: Sends heartbeats and replicates log entries

3. Leader election:
   - Followers become candidates if election timeout expires
   - Candidates request votes from peers
   - Candidate with majority votes becomes leader

4. Log replication:
   - Leader receives writes from clients
   - Leader replicates entries to followers
   - Entry is committed when replicated on majority

5. Safety:
   - New leader must have all committed entries
   - Candidate can only be elected if log is up-to-date

6. Term numbers:
   - Prevent old leaders from overriding new ones
   - Ensure safety during leader transitions

7. Raft is used by:
   - etcd (Kubernetes)
   - CockroachDB
   - TiKV (TiDB)
   - Consul
    """)


if __name__ == "__main__":
    main()
