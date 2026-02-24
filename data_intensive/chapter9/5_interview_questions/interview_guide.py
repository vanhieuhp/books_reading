"""
Chapter 9: Interview-Level Questions and Teaching Guide

This module provides interview questions and detailed explanations for Chapter 9 concepts.
"""

from typing import List, Dict
from dataclasses import dataclass


@dataclass
class InterviewQuestion:
    """Represents an interview question with answer and teaching notes."""
    question: str
    answer: str
    key_points: List[str]
    follow_up: str
    difficulty: str  # "easy", "medium", "hard"


class Chapter9InterviewGuide:
    """Comprehensive interview guide for Chapter 9."""

    @staticmethod
    def get_questions() -> List[InterviewQuestion]:
        """Return all interview questions for Chapter 9."""
        return [
            InterviewQuestion(
                question="What is linearizability and how does it differ from serializability?",
                answer="""
LINEARIZABILITY (Single-Object Consistency):
- Behaves as if there is only one copy of the data
- Operations are atomic and take effect at some point between start and end
- Real-time ordering: if operation A finishes before B starts, A's effects are visible to B
- Applies to SINGLE objects only
- Example: A write to x=1 completes, then ALL subsequent reads see x=1

SERIALIZABILITY (Multi-Object Consistency):
- Transactions appear to execute sequentially (one after another)
- Provides isolation between transactions
- Does NOT guarantee real-time ordering
- Applies to MULTIPLE objects in a transaction
- Example: Transaction A and B can interleave, but result looks sequential

STRICT SERIALIZABILITY (Strongest):
- Both linearizable AND serializable
- Combines real-time ordering with transaction isolation
- Hardest to achieve, most expensive

KEY DIFFERENCE:
Linearizability: "One copy of data, atomic operations"
Serializability: "Transactions don't interfere with each other"

EXAMPLE:
Transaction A: read(x), write(y)
Transaction B: read(y), write(x)

Serializable: Result looks like A then B (or B then A)
Linearizable: Real-time ordering is respected

If A finishes before B starts:
- Serializable: ✓ (result is A then B)
- Linearizable: ✓ (A's effects visible to B)

If A and B overlap:
- Serializable: ✓ (can interleave, but result is sequential)
- Linearizable: ✗ (violates real-time ordering)
                """,
                key_points=[
                    "Linearizability: single-object, real-time ordering",
                    "Serializability: multi-object, transaction isolation",
                    "Strict Serializability = Linearizable + Serializable",
                    "Linearizability is about real-time, serializability is about isolation",
                    "Most databases provide serializability, not linearizability"
                ],
                follow_up="Can you give an example of a system that is serializable but not linearizable?",
                difficulty="hard"
            ),

            InterviewQuestion(
                question="Explain the CAP theorem. What does a CP system sacrifice?",
                answer="""
CAP THEOREM:
During a network partition, a distributed system must choose between:
- Consistency (linearizability)
- Availability (every request gets a response)
- Partition Tolerance (system works despite partitions)

You cannot have all three. Since network partitions WILL happen, you must choose C or A.

CP SYSTEM (Consistent + Partition-tolerant):
- During partition: Some requests return errors
- Sacrifices: Availability
- Examples: ZooKeeper, etcd, HBase, Spanner

How it works:
1. Network partition splits nodes into two groups
2. Only the group with a quorum (majority) can make decisions
3. The minority group rejects requests
4. Result: Consistent but unavailable in minority partition

Example with 5 nodes:
- Partition A: 3 nodes (has quorum)
  - Can elect leader
  - Can process writes
  - Available and consistent

- Partition B: 2 nodes (no quorum)
  - Cannot elect leader
  - Cannot process writes
  - Unavailable but consistent (no conflicting writes)

TRADE-OFF:
CP systems sacrifice availability to maintain consistency.
During a partition, the minority partition becomes unavailable.

WHY CHOOSE CP?
- Banking systems (consistency is critical)
- Distributed locks (must prevent split-brain)
- Coordination services (must have single source of truth)

IMPORTANT NUANCE:
- "Consistency" in CAP means specifically linearizability
- Not the generic word "consistency"
- Many systems are "eventually consistent" but not linearizable
- CAP is often misunderstood because of this terminology
                """,
                key_points=[
                    "CAP: choose Consistency or Availability during partition",
                    "CP system: rejects requests in minority partition",
                    "Sacrifices availability to maintain consistency",
                    "Only partition with quorum can make decisions",
                    "Examples: ZooKeeper, etcd, HBase"
                ],
                follow_up="What does an AP system sacrifice? Give an example.",
                difficulty="medium"
            ),

            InterviewQuestion(
                question="What is the fundamental flaw of Two-Phase Commit?",
                answer="""
TWO-PHASE COMMIT (2PC):
A protocol for distributed transactions across multiple database nodes.

PHASE 1 — PREPARE:
Coordinator: "Can you commit this transaction?"
Node A: "Yes, I'm ready." (writes to WAL, doesn't commit)
Node B: "Yes, I'm ready." (writes to WAL, doesn't commit)

PHASE 2 — COMMIT:
Coordinator: "OK, commit!"
Node A: Commits
Node B: Commits

THE FATAL FLAW:
If the coordinator crashes after Phase 1 but before Phase 2:

1. Participants have voted "Yes" (promised to commit)
2. Participants don't know the final decision
3. Participants CANNOT ABORT:
   - Coordinator might come back and say "Commit"
   - If they abort, they violate the coordinator's decision
4. Participants CANNOT COMMIT:
   - Coordinator might come back and say "Abort"
   - If they commit, they violate the coordinator's decision
5. Participants are STUCK:
   - Holding locks on data
   - Blocking all other transactions
   - Must wait for coordinator to recover

EXAMPLE:
1. Coordinator sends "Prepare" to Node A and Node B
2. Node A: "Yes, ready" (locks data, writes to WAL)
3. Node B: "Yes, ready" (locks data, writes to WAL)
4. Coordinator crashes before sending "Commit" or "Abort"
5. Node A and B are stuck:
   - Data is locked
   - Other transactions cannot proceed
   - If coordinator's disk is destroyed, they're stuck forever

WHY THIS IS BLOCKING:
- 2PC violates the Termination property of consensus
- Consensus requires: every non-crashed node eventually decides
- 2PC: participants can be stuck indefinitely

SOLUTIONS:
1. Three-Phase Commit (3PC): Adds extra round, but doesn't work well with partitions
2. Sagas: Break transaction into compensating transactions
3. Event Sourcing: Use eventual consistency instead
4. Raft/Paxos: Use consensus for distributed transactions

KEY INSIGHT:
2PC is NOT a consensus algorithm. It's a blocking protocol.
Never use 2PC for critical systems. Use consensus algorithms instead.
                """,
                key_points=[
                    "2PC can get stuck if coordinator crashes",
                    "Participants hold locks, blocking other transactions",
                    "Violates Termination property of consensus",
                    "NOT a consensus algorithm",
                    "Better alternatives: Sagas, Event Sourcing, Consensus"
                ],
                follow_up="How would you implement distributed transactions without 2PC?",
                difficulty="hard"
            ),

            InterviewQuestion(
                question="How does Raft elect a leader?",
                answer="""
RAFT LEADER ELECTION:

INITIAL STATE:
- All nodes start as followers
- Each node has a current term (starts at 0)
- Each node has a voted_for field (initially null)

TIMEOUT TRIGGERS ELECTION:
- Followers expect heartbeats from leader every heartbeat_interval
- If no heartbeat for election_timeout period:
  - Follower becomes a candidate
  - Increments current term
  - Votes for itself
  - Sends RequestVote RPC to all other nodes

VOTING PROCESS:
Other nodes receive RequestVote:
- If candidate's term is newer: update current term
- If candidate's log is at least as up-to-date as ours:
  - Grant vote (if haven't voted yet or voted for this candidate)
- Otherwise: deny vote

CANDIDATE BECOMES LEADER:
- If candidate gets votes from majority of nodes:
  - Becomes leader
  - Sends heartbeats to all followers
  - Heartbeats reset election timeout on followers

TERM NUMBERS PREVENT STALE LEADERS:
- Each leadership period has a unique term number
- Term numbers are monotonically increasing
- If a node receives a message from a stale term:
  - Ignores it
  - Prevents old leaders from overriding new ones

EXAMPLE WITH 5 NODES:
1. All nodes are followers, term = 0
2. Node 0 times out, becomes candidate, term = 1
3. Node 0 votes for itself, requests votes from nodes 1-4
4. Nodes 1 and 2 grant votes (majority = 3)
5. Node 0 becomes leader with term = 1
6. Node 0 sends heartbeats to all followers
7. Followers reset their election timeout

WHAT IF TWO CANDIDATES?
1. Node 0 becomes candidate, term = 1
2. Node 1 becomes candidate, term = 1
3. Both request votes
4. Nodes split their votes (no majority)
5. Both candidates timeout and increment term
6. Eventually one gets majority

SAFETY GUARANTEES:
- At most one leader per term (because majority is unique)
- Leader has most up-to-date log (because candidates check log)
- Committed entries are never lost (because leader checks log)

KEY INSIGHT:
Raft uses term numbers and majority voting to ensure:
1. Only one leader at a time
2. Leader has most up-to-date data
3. Stale leaders cannot override new leaders
                """,
                key_points=[
                    "Followers timeout and become candidates",
                    "Candidates request votes from all nodes",
                    "Candidate becomes leader if it gets majority votes",
                    "Term numbers prevent stale leaders",
                    "At most one leader per term (majority is unique)"
                ],
                follow_up="What happens if the leader crashes? How long does it take to elect a new leader?",
                difficulty="medium"
            ),

            InterviewQuestion(
                question="Why are ephemeral nodes in ZooKeeper useful for leader election?",
                answer="""
EPHEMERAL NODES:
A ZooKeeper node that is automatically deleted when its creator disconnects.

THE PROBLEM (Without Ephemeral Nodes):
1. Node A becomes leader, creates /leader node
2. Node A crashes
3. /leader node still exists (nobody deleted it)
4. Other nodes think Node A is still leader
5. No new election happens
6. System is stuck with no leader

THE SOLUTION (With Ephemeral Nodes):
1. Node A becomes leader, creates ephemeral /leader node
2. Node A crashes
3. ZooKeeper detects disconnection
4. /leader node is automatically deleted
5. Other nodes watch /leader and get notified
6. New election is triggered immediately
7. New leader creates /leader node

HOW IT WORKS:
1. Candidate nodes try to create /leader (ephemeral)
2. Only one succeeds (ZooKeeper is atomic)
3. That node becomes leader
4. Other nodes watch /leader
5. If leader crashes:
   - Connection is lost
   - /leader is auto-deleted
   - Watchers are notified
   - New election starts

ADVANTAGES:
1. Automatic cleanup: No need to manually delete /leader
2. Immediate detection: Watchers are notified immediately
3. No false positives: If node is truly dead, /leader disappears
4. Simple implementation: Just create/watch a node

EXAMPLE:
```
Node A: create /leader (ephemeral)
        → Becomes leader
        → Sends heartbeats

Node B: watches /leader
        → Sees /leader exists
        → Knows Node A is leader

Node A crashes:
        → Connection lost
        → /leader auto-deleted
        → Node B notified immediately
        → Node B starts new election
        → Node B creates /leader
        → Node B becomes leader
```

WHY THIS IS ELEGANT:
- No need for timeouts (immediate detection)
- No need for heartbeats (automatic cleanup)
- No false positives (node must be connected to hold /leader)
- Simple and reliable

COMPARISON WITH HEARTBEATS:
Heartbeat approach:
- Leader sends heartbeats every 1 second
- Followers timeout after 3 seconds
- 3-second delay to detect failure

Ephemeral node approach:
- Leader holds /leader
- Followers watch /leader
- Immediate detection when leader crashes

KEY INSIGHT:
Ephemeral nodes solve the zombie leader problem automatically.
They're one of ZooKeeper's most elegant features.
                """,
                key_points=[
                    "Ephemeral nodes auto-delete when creator disconnects",
                    "Solves zombie leader problem automatically",
                    "Immediate detection of leader failure",
                    "No need for timeouts or heartbeats",
                    "Simple and reliable"
                ],
                follow_up="How would you implement leader election without ephemeral nodes?",
                difficulty="easy"
            ),

            InterviewQuestion(
                question="What is Total Order Broadcast and why is it equivalent to consensus?",
                answer="""
TOTAL ORDER BROADCAST (Atomic Broadcast):
A protocol that guarantees:
1. Reliable delivery: If a message is delivered to one node, it's delivered to ALL nodes
2. Total ordering: All nodes deliver messages in the SAME order

EXAMPLE:
Replication log in a single-leader database:

Leader's log:
  [write(x=1), write(y=2), write(z=3)]

Follower 1 receives:
  [write(x=1), write(y=2), write(z=3)]

Follower 2 receives:
  [write(x=1), write(y=2), write(z=3)]

All nodes process in the same order!

WHY IT'S EQUIVALENT TO CONSENSUS:

TOTAL ORDER BROADCAST → LINEARIZABLE STORAGE:
You can build a linearizable key-value store on top of total order broadcast.

To do a linearizable write:
1. Broadcast message "set x = v"
2. Wait for it to come back to you in the delivery order
3. When it arrives, it has been ordered relative to all other writes
4. Result: Linearizable storage

LINEARIZABLE STORAGE → TOTAL ORDER BROADCAST:
You can use a linearizable register as a counter to assign sequence numbers.

To broadcast a message:
1. Atomically increment a counter (linearizable operation)
2. Assign the counter value as sequence number
3. Deliver messages in sequence number order
4. Result: Total order broadcast

THEY'RE EQUIVALENT IN POWER:
- Both provide a total order of events
- Both can be used to implement the other
- Both require consensus (majority agreement)

REAL-WORLD EXAMPLES:

Single-Leader Replication:
- Leader assigns sequence numbers to writes
- Followers apply writes in order
- This is total order broadcast

Raft Consensus:
- Leader appends entries to log
- Followers replicate log in order
- This is total order broadcast

Paxos Consensus:
- Proposers propose values
- Acceptors accept in order
- This is total order broadcast

KEY INSIGHT:
Total order broadcast is the essence of consensus.
If you can order all events consistently, you can solve any distributed problem.
                """,
                key_points=[
                    "Total order broadcast: reliable delivery + total ordering",
                    "Equivalent to consensus",
                    "Can build linearizable storage on top of it",
                    "Can use linearizable storage to implement it",
                    "Single-leader replication is total order broadcast"
                ],
                follow_up="How would you implement total order broadcast using a linearizable register?",
                difficulty="hard"
            ),

            InterviewQuestion(
                question="Why is the FLP impossibility result important?",
                answer="""
FLP IMPOSSIBILITY RESULT:
Fischer, Lynch, and Paterson (1985) proved that in an asynchronous system,
there is NO algorithm that always reaches consensus if even one node can crash.

WHAT IT MEANS:
In a purely asynchronous system (no timing guarantees):
- You cannot guarantee consensus
- Even if only one node crashes
- Even if you have unlimited time
- Even if you have unlimited messages

ASYNCHRONOUS SYSTEM:
- No bounds on message delivery time
- No bounds on process execution time
- You cannot distinguish between dead nodes and slow nodes
- You cannot use timeouts

WHY THIS MATTERS:
It proves that consensus is fundamentally hard.
You cannot solve it with pure logic alone.

HOW REAL SYSTEMS WORK AROUND IT:
Real systems use PARTIAL SYNCHRONY:
- Assume timeouts eventually work (but not always)
- Use timeouts as a heuristic for failure detection
- Ensure safety even if timeouts are wrong
- Sacrifice liveness (progress) if timeouts fail

EXAMPLE:
Raft uses timeouts for leader election:
- If no heartbeat for election_timeout: assume leader is dead
- But timeout might be wrong (leader is just slow)
- If timeout is wrong: no progress (liveness fails)
- But safety is maintained (no split-brain)

PRACTICAL IMPLICATIONS:
1. Consensus algorithms must use timeouts
2. Timeouts are imperfect (can cause false positives)
3. Systems must handle false positives gracefully
4. Safety is more important than liveness

COMPARISON:
Asynchronous system (FLP):
- Consensus is impossible
- No timeouts allowed
- Theoretical model

Partially synchronous system (Real world):
- Consensus is possible
- Timeouts are allowed
- Practical model

EXAMPLE OF FALSE POSITIVE:
1. Leader is slow (GC pause, network congestion)
2. Followers timeout and elect new leader
3. Now there are two leaders (split-brain)
4. But Raft prevents this with term numbers
5. Old leader's messages are ignored (stale term)

KEY INSIGHT:
FLP proves consensus is impossible in theory.
But practical systems work around it using timeouts.
The trade-off: sacrifice liveness to maintain safety.
                """,
                key_points=[
                    "FLP: consensus impossible in asynchronous systems",
                    "Even with one crash, no algorithm always works",
                    "Real systems use partial synchrony (timeouts)",
                    "Timeouts are imperfect but necessary",
                    "Safety is maintained, liveness may fail"
                ],
                follow_up="How do Raft and Paxos work around the FLP impossibility?",
                difficulty="hard"
            ),

            InterviewQuestion(
                question="What is the relationship between consistency models and consensus?",
                answer="""
CONSISTENCY MODELS:
- Eventual Consistency: Weakest, no ordering guarantee
- Causal Consistency: Respects cause-and-effect
- Linearizability: Strongest, single-object consistency

CONSENSUS:
- Getting multiple nodes to agree on something
- Foundation of all reliable distributed systems

THE RELATIONSHIP:

LINEARIZABILITY REQUIRES CONSENSUS:
- Linearizability requires a total order of operations
- Total order requires all nodes to agree on the order
- This is consensus

Example:
- Write x=1 on Node A
- Read x on Node B
- For linearizability: B must see x=1
- This requires consensus on the order of operations

CONSENSUS PROVIDES LINEARIZABILITY:
- Consensus algorithms (Raft, Paxos) provide total order
- Total order broadcast is equivalent to consensus
- You can build linearizable storage on top of consensus

EVENTUAL CONSISTENCY DOESN'T NEED CONSENSUS:
- Eventual consistency allows any order
- Nodes can converge independently
- No need for agreement on order

CAUSAL CONSISTENCY NEEDS PARTIAL CONSENSUS:
- Causal consistency respects cause-and-effect
- Uses vector clocks to track causality
- Doesn't need full consensus, just causal ordering

HIERARCHY:

Strongest (requires most consensus):
  Linearizability
  ↓ (requires total order)
  Total Order Broadcast
  ↓ (equivalent to)
  Consensus (Raft, Paxos)

Middle (requires partial consensus):
  Causal Consistency
  ↓ (requires causal ordering)
  Vector Clocks

Weakest (no consensus needed):
  Eventual Consistency
  ↓ (just wait long enough)
  Convergence

PRACTICAL IMPLICATIONS:

If you want linearizability:
- You need consensus
- You need to wait for quorum confirmation
- You sacrifice latency for consistency

If you want eventual consistency:
- You don't need consensus
- You can return immediately
- You sacrifice consistency for latency

If you want causal consistency:
- You need partial consensus
- You need vector clocks
- You get middle ground

KEY INSIGHT:
Stronger consistency models require more consensus.
Consensus is expensive (latency, availability).
Choose the weakest consistency model that works for your use case.
                """,
                key_points=[
                    "Linearizability requires consensus",
                    "Consensus provides total order",
                    "Eventual consistency doesn't need consensus",
                    "Causal consistency needs partial consensus",
                    "Stronger consistency = more consensus = more cost"
                ],
                follow_up="Can you design a system that uses eventual consistency for reads and consensus for writes?",
                difficulty="hard"
            ),

            InterviewQuestion(
                question="How would you design a distributed lock service?",
                answer="""
REQUIREMENTS:
1. Only one client can hold a lock at a time
2. Locks must be safe (prevent split-brain)
3. Locks must be reliable (survive node failures)
4. Locks must be fair (no starvation)

NAIVE APPROACH (DOESN'T WORK):
```
Lock service on single node:
- Client A: "Can I have lock?"
- Lock service: "Yes"
- Client A crashes
- Lock is never released
- System is stuck
```

BETTER APPROACH (Using Consensus):
```
Lock service with consensus (Raft/Paxos):
1. Client A: "Can I have lock?"
2. Lock service: Consensus with all nodes
3. If consensus reached: "Yes, lock granted"
4. Client A: Holds lock
5. Client A: "Release lock"
6. Lock service: Consensus to release
7. Lock is released
```

EVEN BETTER (Using Leases):
```
Lock service with leases:
1. Client A: "Can I have lock?"
2. Lock service: "Yes, lease expires in 10 seconds"
3. Client A: Holds lock for 10 seconds
4. If Client A crashes: lease expires, lock is released
5. Other clients can acquire lock
```

BEST APPROACH (Using Fencing Tokens):
```
Lock service with fencing tokens:
1. Client A: "Can I have lock?"
2. Lock service: "Yes, token = 33"
3. Client A: Writes data with token 33
4. Storage: Checks token, accepts write
5. Client A crashes, lease expires
6. Client B: "Can I have lock?"
7. Lock service: "Yes, token = 34"
8. Client B: Writes data with token 34
9. Storage: Checks token, accepts write
10. If Client A resumes and tries to write with token 33:
    Storage: "Token 33 < 34, rejected"
```

IMPLEMENTATION DETAILS:

Lock Service (using Raft):
```python
class LockService:
    def __init__(self):
        self.locks = {}  # lock_name -> (holder, token, expiry)
        self.token_counter = 0

    def acquire_lock(self, lock_name, client_id, lease_duration):
        if lock_name in self.locks:
            holder, token, expiry = self.locks[lock_name]
            if expiry > now():
                return None  # Lock held

        # Grant lock
        self.token_counter += 1
        token = self.token_counter
        expiry = now() + lease_duration
        self.locks[lock_name] = (client_id, token, expiry)
        return token

    def release_lock(self, lock_name, client_id, token):
        if lock_name in self.locks:
            holder, t, expiry = self.locks[lock_name]
            if holder == client_id and t == token:
                del self.locks[lock_name]
                return True
        return False
```

Storage Layer (with fencing):
```python
class Storage:
    def __init__(self):
        self.data = {}
        self.max_token = {}  # key -> max_token_seen

    def write(self, key, value, token):
        if key not in self.max_token:
            self.max_token[key] = 0

        if token < self.max_token[key]:
            return False  # Stale token, reject

        self.max_token[key] = token
        self.data[key] = value
        return True
```

KEY FEATURES:
1. Consensus: Ensures only one lock holder
2. Leases: Automatically release locks on crash
3. Fencing tokens: Prevent zombie writes
4. Monotonic tokens: Ensure ordering

REAL-WORLD EXAMPLES:
- ZooKeeper: Ephemeral nodes + watches
- etcd: Leases + consensus
- Consul: Leases + consensus
- Google Chubby: Leases + fencing tokens

KEY INSIGHT:
A good distributed lock service needs:
1. Consensus (to prevent split-brain)
2. Leases (to handle crashes)
3. Fencing tokens (to prevent zombie writes)
                """,
                key_points=[
                    "Need consensus to prevent split-brain",
                    "Need leases to handle crashes",
                    "Need fencing tokens to prevent zombie writes",
                    "Token must be monotonically increasing",
                    "Storage layer is the final safeguard"
                ],
                follow_up="How would you handle a client that holds a lock but becomes slow (GC pause)?",
                difficulty="hard"
            ),
        ]

    @staticmethod
    def print_all_questions():
        """Print all interview questions with answers."""
        questions = Chapter9InterviewGuide.get_questions()

        for i, q in enumerate(questions, 1):
            print(f"\n{'=' * 70}")
            print(f"QUESTION {i} [{q.difficulty.upper()}]")
            print(f"{'=' * 70}")
            print(f"\n{q.question}\n")
            print(f"ANSWER:")
            print(q.answer)
            print(f"\nKEY POINTS:")
            for point in q.key_points:
                print(f"  • {point}")
            print(f"\nFOLLOW-UP QUESTION:")
            print(f"  {q.follow_up}")

    @staticmethod
    def print_by_difficulty(difficulty: str):
        """Print questions filtered by difficulty."""
        questions = Chapter9InterviewGuide.get_questions()
        filtered = [q for q in questions if q.difficulty == difficulty]

        print(f"\n{'=' * 70}")
        print(f"CHAPTER 9 INTERVIEW QUESTIONS - {difficulty.upper()}")
        print(f"{'=' * 70}")

        for i, q in enumerate(filtered, 1):
            print(f"\n{i}. {q.question}")

    @staticmethod
    def get_study_guide() -> str:
        """Return a comprehensive study guide."""
        return """
CHAPTER 9 STUDY GUIDE: Consistency and Consensus

KEY CONCEPTS TO MASTER:

1. CONSISTENCY MODELS
   - Eventual Consistency: Weakest, no ordering guarantee
   - Causal Consistency: Respects cause-and-effect
   - Linearizability: Strongest, single-object consistency
   - Serializability: Multi-object transaction isolation

2. ORDERING GUARANTEES
   - Partial Order: Some events ordered, some concurrent
   - Total Order: Every pair of events is ordered
   - Total Order Broadcast: All nodes deliver in same order
   - Equivalent to consensus

3. CONSENSUS ALGORITHMS
   - Raft: Understandable, leader-based
   - Paxos: Original, harder to understand
   - FLP Impossibility: Consensus impossible in async systems
   - Practical systems use partial synchrony (timeouts)

4. DISTRIBUTED TRANSACTIONS
   - 2PC: Blocking protocol, can get stuck
   - Sagas: Break into compensating transactions
   - Event Sourcing: Use eventual consistency
   - Consensus: Use Raft/Paxos for atomic transactions

5. CAP THEOREM
   - Choose Consistency or Availability during partition
   - CP systems: Consistent but unavailable (ZooKeeper, etcd)
   - AP systems: Available but inconsistent (Cassandra, DynamoDB)
   - Partition tolerance is mandatory

6. COORDINATION SERVICES
   - ZooKeeper: Ephemeral nodes, watches, consensus
   - etcd: Raft-based, key-value store
   - Consul: Service mesh, service discovery
   - Used for leader election, distributed locks, config management

STUDY STRATEGY:

1. Read the textbook.md for conceptual understanding
2. Run the code examples to see concepts in action
3. Modify the code to experiment with different scenarios
4. Answer the interview questions without looking at answers
5. Review the key points and follow-up questions

COMMON INTERVIEW PATTERNS:

Pattern 1: "What's the difference between X and Y?"
- Linearizability vs Serializability
- Eventual vs Causal vs Linearizable
- Raft vs Paxos
- CP vs AP systems

Pattern 2: "How would you design X?"
- Distributed lock service
- Leader election
- Distributed transactions
- Consensus algorithm

Pattern 3: "What are the trade-offs?"
- Consistency vs Availability (CAP)
- Latency vs Safety (timeouts)
- Cost vs Fault Tolerance (quorum size)
- Complexity vs Correctness

PRACTICE EXERCISES:

1. Explain linearizability to a non-technical person
2. Design a distributed lock service with fencing tokens
3. Simulate Raft leader election with network partition
4. Explain why 2PC is problematic
5. Compare CP and AP systems for different use cases

RESOURCES:

- Chapter 9 of "Designing Data-Intensive Applications"
- Raft consensus algorithm (https://raft.github.io/)
- Paxos algorithm (Leslie Lamport's papers)
- Google Spanner paper (TrueTime)
- CAP theorem (Eric Brewer's papers)
"""


def main():
    """Run the interview guide."""
    print("=" * 70)
    print("CHAPTER 9: INTERVIEW-LEVEL QUESTIONS AND TEACHING GUIDE")
    print("=" * 70)

    # Print study guide
    print(Chapter9InterviewGuide.get_study_guide())

    # Print by difficulty
    print("\n" + "=" * 70)
    print("QUESTIONS BY DIFFICULTY")
    print("=" * 70)
    for difficulty in ["easy", "medium", "hard"]:
        Chapter9InterviewGuide.print_by_difficulty(difficulty)

    print("\n" + "=" * 70)
    print("To see detailed answers, run:")
    print("  python -c \"from interview_guide import Chapter9InterviewGuide; Chapter9InterviewGuide.print_all_questions()\"")
    print("=" * 70)


if __name__ == "__main__":
    main()
