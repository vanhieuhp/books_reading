"""
Chapter 9: Consistency Models and Consensus — Code Examples

This module provides practical code examples for understanding consistency models,
ordering guarantees, and consensus algorithms.
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import time
from collections import defaultdict


# ============================================================================
# 1. CONSISTENCY MODELS
# ============================================================================

class ConsistencyModel(Enum):
    """Enum for different consistency models."""
    EVENTUAL = "eventual"
    CAUSAL = "causal"
    LINEARIZABLE = "linearizable"


@dataclass
class WriteOperation:
    """Represents a write operation."""
    key: str
    value: any
    timestamp: float
    client_id: str


@dataclass
class ReadOperation:
    """Represents a read operation."""
    key: str
    timestamp: float
    client_id: str


class EventualConsistencyStore:
    """
    Eventual Consistency: After all writes stop, replicas eventually converge.

    Characteristics:
    - Very weak guarantee
    - Very available
    - Might read stale data for unbounded time
    - Used by: Cassandra, DynamoDB
    """

    def __init__(self, num_replicas: int = 3):
        self.replicas = [{} for _ in range(num_replicas)]
        self.num_replicas = num_replicas
        self.replication_queue = defaultdict(list)

    def write(self, key: str, value: any) -> bool:
        """Write to one replica (returns immediately)."""
        # Write to first replica
        self.replicas[0][key] = value

        # Queue replication to other replicas (happens asynchronously)
        for i in range(1, self.num_replicas):
            self.replication_queue[i].append((key, value))

        return True

    def read(self, replica_id: int = 0) -> Dict:
        """Read from a specific replica (might be stale)."""
        return self.replicas[replica_id].copy()

    def replicate(self, replica_id: int) -> int:
        """
        Process pending replications for a replica.
        Returns number of items replicated.
        """
        count = 0
        while self.replication_queue[replica_id]:
            key, value = self.replication_queue[replica_id].pop(0)
            self.replicas[replica_id][key] = value
            count += 1
        return count

    def replicate_all(self):
        """Replicate to all replicas (simulating eventual consistency)."""
        for i in range(1, self.num_replicas):
            self.replicate(i)


class LinearizableStore:
    """
    Linearizability: System behaves as if there's only one copy of data.

    Characteristics:
    - Strongest single-object consistency
    - Once a write completes, ALL subsequent reads see new value
    - Real-time ordering: if A finishes before B starts, A's effects visible to B
    - Equivalent to single-threaded database

    Implementation: Single leader with synchronous replication
    """

    def __init__(self, num_replicas: int = 3):
        self.leader_data = {}
        self.replicas = [{} for _ in range(num_replicas)]
        self.num_replicas = num_replicas
        self.write_log = []

    def write(self, key: str, value: any) -> bool:
        """
        Write to leader, wait for quorum confirmation.
        Returns only after majority of replicas have acknowledged.
        """
        # Write to leader
        self.leader_data[key] = value
        self.write_log.append((key, value))

        # Synchronously replicate to all followers
        # (In real system, wait for quorum, not all)
        for replica in self.replicas:
            replica[key] = value

        return True

    def read(self, replica_id: int = 0) -> Dict:
        """
        Read from any replica (all have same data due to sync replication).
        """
        if replica_id == 0:
            return self.leader_data.copy()
        return self.replicas[replica_id - 1].copy()

    def get_write_order(self) -> List[Tuple[str, any]]:
        """Get the total order of all writes."""
        return self.write_log.copy()


class CausalConsistencyStore:
    """
    Causal Consistency: Preserves cause-and-effect ordering.

    Characteristics:
    - If event A causally caused event B, every node sees A before B
    - Concurrent events can be in any order
    - Stronger than eventual, weaker than linearizable
    - Uses vector clocks to track causality
    """

    def __init__(self, num_replicas: int = 3):
        self.replicas = [{} for _ in range(num_replicas)]
        self.vector_clocks = [defaultdict(int) for _ in range(num_replicas)]
        self.num_replicas = num_replicas
        self.replication_queue = defaultdict(list)

    def write(self, key: str, value: any, client_id: str) -> Tuple[str, Dict]:
        """
        Write to a replica and return vector clock.
        Vector clock tracks causality.
        """
        replica_id = 0

        # Increment this replica's clock
        self.vector_clocks[replica_id][replica_id] += 1

        # Write with vector clock
        vc = dict(self.vector_clocks[replica_id])
        self.replicas[replica_id][key] = (value, vc)

        # Queue for replication with vector clock
        for i in range(1, self.num_replicas):
            self.replication_queue[i].append((key, value, vc))

        return key, vc

    def read(self, replica_id: int = 0) -> Dict:
        """Read from a replica (respects causal ordering)."""
        result = {}
        for key, (value, vc) in self.replicas[replica_id].items():
            result[key] = value
        return result

    def replicate(self, replica_id: int) -> int:
        """
        Replicate to a replica, respecting causal ordering.
        Only replicate if dependencies are satisfied.
        """
        count = 0
        pending = list(self.replication_queue[replica_id])
        self.replication_queue[replica_id] = []

        for key, value, vc in pending:
            # Check if dependencies are satisfied
            # (simplified: just replicate in order)
            self.replicas[replica_id][key] = (value, vc)
            self.vector_clocks[replica_id][replica_id] = max(
                self.vector_clocks[replica_id][replica_id],
                vc.get(replica_id, 0)
            )
            count += 1

        return count


# ============================================================================
# 2. ORDERING GUARANTEES
# ============================================================================

class TotalOrderBroadcast:
    """
    Total Order Broadcast: All nodes deliver messages in the same order.

    Guarantees:
    1. Reliable delivery: If delivered to one node, delivered to all
    2. Total ordering: All nodes deliver in same order

    This is what a replication log in single-leader database provides.
    """

    def __init__(self, num_nodes: int = 3):
        self.num_nodes = num_nodes
        self.logs = [[] for _ in range(num_nodes)]
        self.sequence_number = 0

    def broadcast(self, message: str, sender_id: int) -> int:
        """
        Broadcast a message from a sender.
        Returns the sequence number assigned to this message.
        """
        seq_num = self.sequence_number
        self.sequence_number += 1

        # Deliver to all nodes in the same order
        for i in range(self.num_nodes):
            self.logs[i].append((seq_num, message, sender_id))

        return seq_num

    def get_log(self, node_id: int) -> List[Tuple[int, str, int]]:
        """Get the log for a node (all nodes have same log)."""
        return self.logs[node_id].copy()

    def verify_total_order(self) -> bool:
        """Verify that all nodes have the same log in the same order."""
        first_log = self.logs[0]
        for i in range(1, self.num_nodes):
            if self.logs[i] != first_log:
                return False
        return True


class PartialOrderTracker:
    """
    Partial Order: Some events are ordered, some are concurrent.

    Uses vector clocks to track causality.
    """

    def __init__(self):
        self.events = []
        self.vector_clocks = {}

    def record_event(self, event_id: str, client_id: int,
                    dependencies: List[str] = None) -> Dict[int, int]:
        """
        Record an event with its dependencies.
        Returns the vector clock for this event.
        """
        if dependencies is None:
            dependencies = []

        # Initialize vector clock
        vc = defaultdict(int)

        # Increment this client's clock
        vc[client_id] += 1

        # Merge dependencies
        for dep_id in dependencies:
            if dep_id in self.vector_clocks:
                dep_vc = self.vector_clocks[dep_id]
                for client, count in dep_vc.items():
                    vc[client] = max(vc[client], count)

        self.vector_clocks[event_id] = dict(vc)
        self.events.append((event_id, dependencies))

        return dict(vc)

    def happens_before(self, event_a: str, event_b: str) -> bool:
        """Check if event A happens before event B."""
        if event_a not in self.vector_clocks or event_b not in self.vector_clocks:
            return False

        vc_a = self.vector_clocks[event_a]
        vc_b = self.vector_clocks[event_b]

        # A < B if A's clock is <= B's clock in all dimensions
        # and strictly less in at least one
        less_or_equal = all(vc_a.get(c, 0) <= vc_b.get(c, 0)
                           for c in set(vc_a.keys()) | set(vc_b.keys()))
        strictly_less = any(vc_a.get(c, 0) < vc_b.get(c, 0)
                           for c in set(vc_a.keys()) | set(vc_b.keys()))

        return less_or_equal and strictly_less

    def concurrent(self, event_a: str, event_b: str) -> bool:
        """Check if events are concurrent (neither happens before the other)."""
        return (not self.happens_before(event_a, event_b) and
                not self.happens_before(event_b, event_a))


# ============================================================================
# 3. CONSENSUS BASICS
# ============================================================================

class RaftNode:
    """
    Simplified Raft consensus algorithm.

    Three sub-problems:
    1. Leader Election
    2. Log Replication
    3. Safety
    """

    def __init__(self, node_id: int, num_nodes: int):
        self.node_id = node_id
        self.num_nodes = num_nodes

        # Persistent state
        self.current_term = 0
        self.voted_for = None
        self.log = []

        # Volatile state
        self.state = "follower"  # follower, candidate, leader
        self.commit_index = 0
        self.last_applied = 0

        # Leader state
        self.next_index = {}
        self.match_index = {}

        # Heartbeat tracking
        self.last_heartbeat = time.time()

    def request_vote(self, term: int, candidate_id: int,
                    last_log_index: int, last_log_term: int) -> bool:
        """
        Handle vote request from a candidate.
        Returns True if vote is granted.
        """
        # If term is newer, update current term
        if term > self.current_term:
            self.current_term = term
            self.voted_for = None

        # Vote if:
        # 1. Term matches current term
        # 2. Haven't voted yet or voted for this candidate
        # 3. Candidate's log is at least as up-to-date as ours
        if (term == self.current_term and
            (self.voted_for is None or self.voted_for == candidate_id)):

            # Check if candidate's log is up-to-date
            if last_log_index >= len(self.log) - 1:
                self.voted_for = candidate_id
                return True

        return False

    def append_entries(self, term: int, leader_id: int,
                      prev_log_index: int, prev_log_term: int,
                      entries: List[str], leader_commit: int) -> bool:
        """
        Handle append entries (heartbeat or log replication) from leader.
        Returns True if entries are appended.
        """
        # If term is newer, update current term
        if term > self.current_term:
            self.current_term = term
            self.state = "follower"

        # Reject if term is stale
        if term < self.current_term:
            return False

        # Update heartbeat
        self.last_heartbeat = time.time()

        # Append entries
        if entries:
            self.log.extend(entries)

        # Update commit index
        if leader_commit > self.commit_index:
            self.commit_index = min(leader_commit, len(self.log) - 1)

        return True

    def start_election(self) -> int:
        """
        Start a leader election.
        Returns the term number for this election.
        """
        self.current_term += 1
        self.state = "candidate"
        self.voted_for = self.node_id

        return self.current_term

    def become_leader(self):
        """Become the leader."""
        self.state = "leader"
        self.next_index = {i: len(self.log) for i in range(self.num_nodes)}
        self.match_index = {i: 0 for i in range(self.num_nodes)}

    def get_state(self) -> Dict:
        """Get the current state of this node."""
        return {
            "node_id": self.node_id,
            "state": self.state,
            "term": self.current_term,
            "voted_for": self.voted_for,
            "log_length": len(self.log),
            "commit_index": self.commit_index,
        }


class TwoPhaseCommit:
    """
    Two-Phase Commit (2PC): Distributed transaction protocol.

    PROBLEM: If coordinator crashes after Phase 1, participants get stuck.
    This is why 2PC is NOT a consensus algorithm.
    """

    def __init__(self, num_participants: int = 3):
        self.num_participants = num_participants
        self.participants = [{"state": "initial"} for _ in range(num_participants)]
        self.coordinator_state = "initial"

    def phase_1_prepare(self) -> bool:
        """
        Phase 1: Ask all participants if they can commit.
        Returns True if all participants vote Yes.
        """
        self.coordinator_state = "preparing"

        votes = []
        for i in range(self.num_participants):
            # Participant writes to WAL but doesn't commit
            self.participants[i]["state"] = "prepared"
            votes.append(True)  # Simplified: all vote Yes

        return all(votes)

    def phase_2_commit(self) -> bool:
        """
        Phase 2: Tell all participants to commit.
        Returns True if all participants commit successfully.
        """
        self.coordinator_state = "committing"

        for i in range(self.num_participants):
            self.participants[i]["state"] = "committed"

        self.coordinator_state = "committed"
        return True

    def phase_2_abort(self) -> bool:
        """
        Phase 2: Tell all participants to abort.
        Returns True if all participants abort successfully.
        """
        self.coordinator_state = "aborting"

        for i in range(self.num_participants):
            self.participants[i]["state"] = "aborted"

        self.coordinator_state = "aborted"
        return True

    def coordinator_crashes_after_phase_1(self):
        """
        Simulate coordinator crash after Phase 1.
        Participants are now stuck!
        """
        self.coordinator_state = "crashed"
        # Participants are in "prepared" state, don't know what to do

    def get_state(self) -> Dict:
        """Get the current state of the system."""
        return {
            "coordinator": self.coordinator_state,
            "participants": [p["state"] for p in self.participants],
        }


# ============================================================================
# 4. CAP THEOREM DEMONSTRATION
# ============================================================================

class CAPTheorem:
    """
    CAP Theorem: During a network partition, choose Consistency or Availability.

    You cannot have all three:
    - Consistency (linearizability)
    - Availability (every request gets response)
    - Partition Tolerance (system works despite partitions)
    """

    @staticmethod
    def cp_system_example():
        """
        CP System: Consistent + Partition-tolerant

        During partition: Some requests return errors (sacrifices availability)
        Examples: ZooKeeper, etcd, HBase, Spanner
        """
        return {
            "name": "CP System (e.g., ZooKeeper)",
            "consistency": "Linearizable",
            "availability": "No (rejects requests in minority partition)",
            "partition_tolerance": "Yes",
            "example_behavior": {
                "normal": "All requests succeed",
                "partition": "Majority partition: requests succeed",
                "partition": "Minority partition: requests rejected",
            }
        }

    @staticmethod
    def ap_system_example():
        """
        AP System: Available + Partition-tolerant

        During partition: All requests get responses, but might be stale
        Examples: Cassandra, DynamoDB, CouchDB
        """
        return {
            "name": "AP System (e.g., Cassandra)",
            "consistency": "Eventual (not linearizable)",
            "availability": "Yes (all requests get responses)",
            "partition_tolerance": "Yes",
            "example_behavior": {
                "normal": "All requests succeed",
                "partition": "Both partitions: requests succeed",
                "partition": "But data might be inconsistent",
            }
        }


# ============================================================================
# DEMONSTRATION
# ============================================================================

def demonstrate_consistency_models():
    """Demonstrate different consistency models."""
    print("\n" + "=" * 70)
    print("CONSISTENCY MODELS DEMONSTRATION")
    print("=" * 70)

    # Eventual Consistency
    print("\n1. EVENTUAL CONSISTENCY")
    print("-" * 70)
    eventual_store = EventualConsistencyStore(num_replicas=3)
    eventual_store.write("x", 1)
    print(f"After write, replica 0: {eventual_store.read(0)}")
    print(f"After write, replica 1 (stale): {eventual_store.read(1)}")
    eventual_store.replicate_all()
    print(f"After replication, replica 1: {eventual_store.read(1)}")

    # Linearizable
    print("\n2. LINEARIZABLE CONSISTENCY")
    print("-" * 70)
    linear_store = LinearizableStore(num_replicas=3)
    linear_store.write("x", 1)
    print(f"After write, all replicas have same data: {linear_store.read(0)}")
    print(f"Replica 1: {linear_store.read(1)}")
    print(f"Write order: {linear_store.get_write_order()}")

    # Causal Consistency
    print("\n3. CAUSAL CONSISTENCY")
    print("-" * 70)
    causal_store = CausalConsistencyStore(num_replicas=3)
    key, vc = causal_store.write("x", 1, "client_1")
    print(f"Write with vector clock: {vc}")
    print(f"Replica 0: {causal_store.read(0)}")
    causal_store.replicate(1)
    print(f"After replication, replica 1: {causal_store.read(1)}")


def demonstrate_ordering():
    """Demonstrate ordering guarantees."""
    print("\n" + "=" * 70)
    print("ORDERING GUARANTEES DEMONSTRATION")
    print("=" * 70)

    # Total Order Broadcast
    print("\n1. TOTAL ORDER BROADCAST")
    print("-" * 70)
    tob = TotalOrderBroadcast(num_nodes=3)
    tob.broadcast("write(x=1)", 0)
    tob.broadcast("write(y=2)", 1)
    tob.broadcast("write(z=3)", 0)

    print("Node 0 log:", tob.get_log(0))
    print("Node 1 log:", tob.get_log(1))
    print("Node 2 log:", tob.get_log(2))
    print(f"All nodes have same log: {tob.verify_total_order()}")

    # Partial Order
    print("\n2. PARTIAL ORDER (Vector Clocks)")
    print("-" * 70)
    po = PartialOrderTracker()

    # Event A: Question posted
    vc_a = po.record_event("question", 0)
    print(f"Event A (question): {vc_a}")

    # Event B: Answer posted (depends on A)
    vc_b = po.record_event("answer", 1, dependencies=["question"])
    print(f"Event B (answer): {vc_b}")

    # Event C: Another answer (concurrent with B)
    vc_c = po.record_event("answer2", 2)
    print(f"Event C (answer2): {vc_c}")

    print(f"\nA happens before B: {po.happens_before('question', 'answer')}")
    print(f"B and C are concurrent: {po.concurrent('answer', 'answer2')}")


def demonstrate_consensus():
    """Demonstrate consensus algorithms."""
    print("\n" + "=" * 70)
    print("CONSENSUS ALGORITHMS DEMONSTRATION")
    print("=" * 70)

    # Raft
    print("\n1. RAFT CONSENSUS")
    print("-" * 70)
    nodes = [RaftNode(i, 3) for i in range(3)]

    # Node 0 starts election
    term = nodes[0].start_election()
    print(f"Node 0 starts election for term {term}")
    print(f"Node 0 state: {nodes[0].get_state()}")

    # Other nodes vote for node 0
    vote_0 = nodes[1].request_vote(term, 0, 0, 0)
    vote_1 = nodes[2].request_vote(term, 0, 0, 0)
    print(f"Node 1 votes for node 0: {vote_0}")
    print(f"Node 2 votes for node 0: {vote_1}")

    # Node 0 becomes leader
    if vote_0 and vote_1:
        nodes[0].become_leader()
        print(f"Node 0 becomes leader")
        print(f"Node 0 state: {nodes[0].get_state()}")

    # 2PC
    print("\n2. TWO-PHASE COMMIT")
    print("-" * 70)
    tpc = TwoPhaseCommit(num_participants=3)

    print("Phase 1: Prepare")
    if tpc.phase_1_prepare():
        print(f"All participants ready: {tpc.get_state()}")

        print("\nPhase 2: Commit")
        tpc.phase_2_commit()
        print(f"Transaction committed: {tpc.get_state()}")

    # 2PC with coordinator crash
    print("\n2PC with Coordinator Crash:")
    tpc2 = TwoPhaseCommit(num_participants=3)
    tpc2.phase_1_prepare()
    print(f"After Phase 1: {tpc2.get_state()}")

    tpc2.coordinator_crashes_after_phase_1()
    print(f"Coordinator crashes: {tpc2.get_state()}")
    print("Participants are stuck! They don't know whether to commit or abort.")


def demonstrate_cap():
    """Demonstrate CAP theorem."""
    print("\n" + "=" * 70)
    print("CAP THEOREM DEMONSTRATION")
    print("=" * 70)

    print("\nCP System (e.g., ZooKeeper):")
    cp = CAPTheorem.cp_system_example()
    for key, value in cp.items():
        print(f"  {key}: {value}")

    print("\nAP System (e.g., Cassandra):")
    ap = CAPTheorem.ap_system_example()
    for key, value in ap.items():
        print(f"  {key}: {value}")


def main():
    """Run all demonstrations."""
    print("=" * 70)
    print("CHAPTER 9: CONSISTENCY AND CONSENSUS — CODE EXAMPLES")
    print("=" * 70)

    demonstrate_consistency_models()
    demonstrate_ordering()
    demonstrate_consensus()
    demonstrate_cap()

    print("\n" + "=" * 70)
    print("DEMONSTRATIONS COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
