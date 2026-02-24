"""
Chapter 8: Interview-Level Questions and Teaching Guide

This module provides interview questions and detailed explanations for Chapter 8 concepts.
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


class Chapter8InterviewGuide:
    """Comprehensive interview guide for Chapter 8."""

    @staticmethod
    def get_questions() -> List[InterviewQuestion]:
        """Return all interview questions for Chapter 8."""
        return [
            InterviewQuestion(
                question="A client sends a request and receives no response. What are the possible causes?",
                answer="""
There are four indistinguishable scenarios from the client's perspective:

1. REQUEST LOST: The request never reached the server
   Client ──── X ────► Server

2. SERVER SLOW: The server received the request but is processing it slowly
   Client ────────────► Server (processing for 30 seconds...)

3. RESPONSE LOST: The server processed the request but the response was lost
   Client ◄──── X ──── Server

4. SERVER CRASHED: The server received the request but crashed while processing
   Client ────────────► Server 💥

The client has NO WAY to distinguish between these scenarios. This is the fundamental
problem of distributed systems: you cannot tell if a remote node is dead or just slow.

SOLUTION: Use timeouts, but understand the trade-offs:
- Too short: False positives, cascading failures
- Too long: Users wait forever for error messages
- Adaptive timeouts: Measure response times and adjust dynamically
                """,
                key_points=[
                    "Four indistinguishable scenarios",
                    "Client cannot determine root cause",
                    "Timeouts are imperfect solution",
                    "Network delays are unbounded",
                    "This is why distributed systems are hard"
                ],
                follow_up="How would you implement an adaptive timeout mechanism?",
                difficulty="easy"
            ),

            InterviewQuestion(
                question="Why can't you use wall-clock timestamps to reliably order events in a distributed system?",
                answer="""
Wall-clock timestamps are unreliable for ordering because:

1. CLOCK SKEW: Different machines' clocks disagree
   Node A's clock: 10:00:00.100 (slightly fast)
   Node B's clock: 10:00:00.000 (correct)

   Write 1: Happens on Node B at 10:00:00.000
   Write 2: Happens on Node A at 10:00:00.100

   With Last-Write-Wins: Write 2 "wins" (higher timestamp)
   But Write 1 may have actually happened AFTER Write 2 in real time!
   Result: Data loss!

2. NTP JUMPS: Network Time Protocol can jump backward
   - NTP periodically adjusts the clock
   - A clock can jump backward by seconds
   - Timestamps can go backward in time
   - Leases and timeouts become unreliable

3. UNBOUNDED DRIFT: Clocks drift at different rates
   - Even with NTP, clocks can differ by milliseconds
   - An increment of 1ms in clock skew can cause data loss

SOLUTION: Use logical clocks or vector clocks
- Lamport timestamps: Simple, but don't capture causality
- Vector clocks: More complex, but capture causality
- Google Spanner's TrueTime: Use GPS + atomic clocks (expensive!)
                """,
                key_points=[
                    "Clock skew causes wrong ordering",
                    "NTP can jump backward",
                    "LWW with physical timestamps is broken",
                    "Even 1ms of skew can cause data loss",
                    "Logical clocks are more reliable"
                ],
                follow_up="How do Lamport timestamps solve this problem? What are their limitations?",
                difficulty="medium"
            ),

            InterviewQuestion(
                question="What is a fencing token and why is it needed?",
                answer="""
FENCING TOKEN: A monotonically increasing number issued with each lease/lock.

THE PROBLEM (Zombie Process):
1. Thread 1 acquires a lease that expires in 10 seconds
2. Thread 1 begins critical work
3. Thread 1 pauses for 15 seconds (GC pause, VM suspension)
4. Thread 1 resumes, still thinks it holds the lease
5. Thread 1 writes data (BUT THE LEASE EXPIRED 5 SECONDS AGO!)
6. Thread 2 acquired the lease during Thread 1's pause
7. Thread 2 also writes data
Result: DATA CORRUPTION (both threads wrote during "exclusive" period)

THE SOLUTION (Fencing Tokens):
1. Lock service issues lease with FENCING TOKEN = 33
   Thread 1 gets token 33

2. Thread 1 pauses for 15 seconds

3. Lock service issues new lease with FENCING TOKEN = 34
   Thread 2 gets token 34

4. Thread 1 resumes, tries to write with token 33
   Storage service checks: "I've already seen token 34"
   Storage service REJECTS write (token 33 is stale)

5. Thread 2 writes with token 34
   Storage service checks: "Token 34 >= 34"
   Storage service ACCEPTS write

KEY INSIGHT: The storage layer acts as the final safeguard.
Even if a client doesn't realize its lease expired, the storage system
prevents it from doing damage.

IMPLEMENTATION:
- Lock service: Increment token on each lease grant
- Client: Include token with every write
- Storage: Reject writes with stale tokens
                """,
                key_points=[
                    "Fencing token is monotonically increasing number",
                    "Prevents zombie processes from corrupting data",
                    "Storage layer is the final safeguard",
                    "Works even if client doesn't know lease expired",
                    "Essential for systems with process pauses"
                ],
                follow_up="How would you implement fencing tokens in a distributed database?",
                difficulty="hard"
            ),

            InterviewQuestion(
                question="How does Google Spanner solve the clock synchronization problem?",
                answer="""
GOOGLE SPANNER'S APPROACH: TrueTime API

THE PROBLEM:
- Distributed systems need to order events
- Wall-clock timestamps are unreliable (clock skew, NTP jumps)
- Logical clocks don't capture real-world time

SPANNER'S SOLUTION:
1. HARDWARE: GPS receivers and atomic clocks in every datacenter
   - Atomic clocks are extremely accurate (drift < 1 microsecond/second)
   - GPS provides external time reference
   - Multiple receivers for redundancy

2. TRUETIME API: Returns uncertainty interval, not a point in time
   TrueTime.now() returns [earliest, latest]
   - earliest: Lower bound on current time
   - latest: Upper bound on current time
   - Interval width: ~7ms (Google's typical uncertainty)

   Example:
   TrueTime.now() = [10:00:00.100, 10:00:00.107]
   "The current time is somewhere in this 7ms window"

3. TRANSACTION ORDERING:
   - Each transaction gets a timestamp from TrueTime
   - Transactions are ordered by their timestamp intervals
   - If intervals overlap, Spanner waits for the interval to pass
   - This ensures a total order of transactions

EXAMPLE:
Transaction A: timestamp = [10:00:00.100, 10:00:00.107]
Transaction B: timestamp = [10:00:00.105, 10:00:00.112]

Intervals overlap! Spanner waits until 10:00:00.112 before committing
to ensure A happens-before B.

WHY THIS WORKS:
- Eliminates clock skew as a source of ordering problems
- Provides external time reference (GPS)
- Acknowledges inherent uncertainty in time measurement

COST:
- Extremely expensive (GPS receivers, atomic clocks in every datacenter)
- Only Google can afford this
- No open-source database replicates this approach
                """,
                key_points=[
                    "Uses GPS and atomic clocks",
                    "TrueTime returns uncertainty interval",
                    "Transactions wait for intervals to pass",
                    "Provides total order of transactions",
                    "Extremely expensive, not practical for most systems"
                ],
                follow_up="What are the trade-offs of Spanner's approach? Why don't other databases use it?",
                difficulty="hard"
            ),

            InterviewQuestion(
                question="What is the difference between a crash fault and a Byzantine fault?",
                answer="""
CRASH FAULT (Honest Failure):
- Node stops responding
- Node may have crashed, lost power, or network connection failed
- Node is not sending any messages (or sending nothing)
- Assumption: Node is honest but faulty

Example:
- Server crashes and stops responding to requests
- Network link is cut, node is isolated
- Process is killed

BYZANTINE FAULT (Dishonest Failure):
- Node sends arbitrary or malicious messages
- Node may lie, send contradictory messages to different peers
- Node may send corrupted data
- Node may collude with other faulty nodes
- Assumption: Node is dishonest

Example:
- Compromised server sends wrong data to some clients
- Attacker sends contradictory messages to different nodes
- Node sends different values to different peers

TOLERANCE REQUIREMENTS:
Crash Fault Tolerance (CFT):
- Need f+1 nodes to tolerate f failures
- Example: 3 nodes can tolerate 1 crash
- Used in: Raft, Paxos, most databases

Byzantine Fault Tolerance (BFT):
- Need 3f+1 nodes to tolerate f Byzantine nodes
- Example: 4 nodes can tolerate 1 Byzantine node
- Used in: Blockchains, aerospace, adversarial systems

COST COMPARISON:
For 1 fault:
- CFT: 2 nodes
- BFT: 4 nodes (2x overhead)

For 2 faults:
- CFT: 3 nodes
- BFT: 7 nodes (2.3x overhead)

WHY MOST DATABASES DON'T NEED BFT:
- All nodes run by same organization (trusted)
- All nodes in same datacenter (trusted network)
- No adversarial participants
- Nodes fail by crashing, not by lying
- BFT is dramatically more expensive

WHERE BFT IS NECESSARY:
- Blockchains (untrusted participants)
- Aerospace systems (cosmic rays can flip bits)
- Systems with adversarial participants
- Distributed systems across untrusted organizations
                """,
                key_points=[
                    "Crash fault: node stops responding",
                    "Byzantine fault: node sends arbitrary messages",
                    "CFT needs f+1 nodes, BFT needs 3f+1 nodes",
                    "BFT is 3x more expensive than CFT",
                    "Most databases only need CFT"
                ],
                follow_up="Can you give an example of a system that needs Byzantine fault tolerance?",
                difficulty="medium"
            ),

            InterviewQuestion(
                question="Why are GC pauses dangerous for distributed systems?",
                answer="""
GC PAUSE: A garbage collection pause can freeze a Java/Go process for
hundreds of milliseconds (sometimes seconds). During this pause, the process
cannot do anything - it can't respond to heartbeats, renew leases, or process messages.

THE DANGERS:

1. MISSED HEARTBEATS:
   - Node A sends heartbeats to Node B every 1 second
   - Node A has a 5-second GC pause
   - Node B doesn't receive 5 heartbeats
   - Node B thinks Node A is dead
   - Node B elects a new leader
   - Node A resumes and is now a "zombie leader"
   Result: Split-brain, data corruption

2. EXPIRED LEASES:
   - Node A acquires a lease that expires in 10 seconds
   - Node A has a 15-second GC pause
   - Lease expires while Node A is paused
   - Node A resumes and still thinks it holds the lease
   - Node A writes data with expired lease
   Result: Data corruption (see fencing tokens)

3. ZOMBIE WRITES:
   - Node A acquires a lock
   - Node A has a GC pause
   - Lock expires, Node B acquires it
   - Node A resumes and writes with expired lock
   - Both Node A and Node B write during "exclusive" period
   Result: Data corruption

SOLUTIONS:

1. FENCING TOKENS:
   - Storage layer rejects writes with stale tokens
   - Prevents zombie writes even if client doesn't know lease expired

2. SHORT GC PAUSES:
   - Use low-latency GC algorithms (G1, ZGC)
   - Tune GC to minimize pause times
   - But can't eliminate pauses completely

3. DESIGN FOR PAUSES:
   - Assume processes can pause at any time
   - Use timeouts and heartbeats
   - Use fencing tokens
   - Don't rely on timing assumptions

4. PROCESS PAUSE DETECTION:
   - Detect when a process resumes after a pause
   - Invalidate leases/locks after pause
   - Refresh state from authoritative source

KEY INSIGHT:
In distributed systems, you must assume that any process can pause
at any time for an unpredictable duration. Design your system accordingly.
                """,
                key_points=[
                    "GC pause can freeze process for seconds",
                    "Causes missed heartbeats (false failure detection)",
                    "Causes expired leases (zombie writes)",
                    "Fencing tokens prevent data corruption",
                    "Must design system to tolerate pauses"
                ],
                follow_up="How would you detect that a process has resumed after a pause?",
                difficulty="medium"
            ),

            InterviewQuestion(
                question="What is a quorum and why is it important?",
                answer="""
QUORUM: A majority of nodes (more than half).

For n nodes: quorum_size = floor(n/2) + 1

Examples:
- 3 nodes: quorum = 2
- 5 nodes: quorum = 3
- 7 nodes: quorum = 4

WHY QUORUMS ARE IMPORTANT:

1. PREVENTS SPLIT-BRAIN:
   With network partition, only ONE partition can have a quorum.

   Example: 5 nodes, partition into 3 and 2
   - Partition A (3 nodes): Has quorum (3 >= 3)
   - Partition B (2 nodes): No quorum (2 < 3)
   - Only Partition A can elect a leader
   - No split-brain!

2. ENSURES CONSENSUS:
   A decision is only valid if a MAJORITY agrees.

   Example: Leader election
   - Candidate needs votes from quorum (3 out of 5)
   - Even if 2 nodes are down, candidate can still become leader
   - Ensures only one leader at a time

3. FAULT TOLERANCE:
   System can tolerate f failures if n >= 2f + 1

   Examples:
   - 3 nodes: can tolerate 1 failure
   - 5 nodes: can tolerate 2 failures
   - 7 nodes: can tolerate 3 failures

QUORUM-BASED DECISIONS:

Leader Election:
- Candidate requests votes from all nodes
- Candidate becomes leader if it gets quorum votes
- Prevents zombie leaders (isolated node can't get quorum)

Distributed Locks:
- Lock is only valid if quorum of lock service nodes confirms it
- Prevents zombie processes from holding stale locks

Consensus:
- Value is only "decided" if quorum of nodes agree
- Ensures consistency even with network partitions

EXAMPLE: Quorum-Based Lock Service
5 nodes, quorum = 3

Client A tries to acquire lock:
- Requests lock from all 5 nodes
- Gets confirmation from 3 nodes (quorum)
- Lock is acquired

Network partition: 3 nodes in Partition A, 2 in Partition B

Client B in Partition B tries to acquire lock:
- Requests lock from 2 nodes in Partition B
- Gets confirmation from 2 nodes
- But 2 < 3 (quorum), so lock is NOT acquired
- Client B cannot hold lock in minority partition
- No data corruption!

KEY INSIGHT:
Quorums ensure that only one partition can make decisions.
This prevents split-brain and data corruption.
                """,
                key_points=[
                    "Quorum = majority of nodes",
                    "Only one partition can have quorum",
                    "Prevents split-brain",
                    "Ensures consensus",
                    "Enables fault tolerance"
                ],
                follow_up="How would you implement quorum-based leader election?",
                difficulty="easy"
            ),

            InterviewQuestion(
                question="What is a network partition and how does it affect distributed systems?",
                answer="""
NETWORK PARTITION (Netsplit): A network link failure that isolates groups of nodes.

EXAMPLE:
Normal:                    After Network Partition:
  A ◄──► B ◄──► C           A ◄──► B     C (isolated)

Nodes A and B can communicate with each other.
Node C is isolated and cannot communicate with A or B.

HOW PARTITIONS HAPPEN:
- Switch failure
- Cable unplugged
- Firmware bug causing packet loss
- Misconfigured firewall
- Overloaded network link
- Surprisingly common even in well-managed datacenters

EFFECTS ON DISTRIBUTED SYSTEMS:

1. NODES CANNOT COMMUNICATE:
   - Nodes in different partitions cannot send messages
   - Nodes think other nodes are dead
   - But nodes are actually alive (just isolated)

2. SPLIT-BRAIN RISK:
   Without quorums:
   - Partition A elects a leader
   - Partition B elects a different leader
   - Two leaders, data corruption!

   With quorums:
   - Only partition with quorum can elect leader
   - Other partition cannot make decisions
   - No split-brain

3. CONSISTENCY VS AVAILABILITY TRADE-OFF:
   - Partition A (has quorum): Can continue operating (available)
   - Partition B (no quorum): Must stop (unavailable but consistent)

   This is the CAP theorem:
   - Consistency: All nodes see same data
   - Availability: System continues operating
   - Partition tolerance: System works despite network partitions

   You can have at most 2 of 3 in a network partition.

EXAMPLE: 5-node system with 3-2 partition

Partition A (3 nodes):
- Has quorum (3 >= 3)
- Can elect leader
- Can process writes
- System is available

Partition B (2 nodes):
- No quorum (2 < 3)
- Cannot elect leader
- Cannot process writes
- System is unavailable
- But data is consistent (no conflicting writes)

When partition heals:
- Partition B nodes rejoin Partition A
- Partition B nodes catch up on missed writes
- System is consistent again

SOLUTIONS:

1. QUORUM-BASED DECISIONS:
   - Only partition with quorum can make decisions
   - Prevents split-brain
   - Ensures consistency

2. TIMEOUT-BASED FAILURE DETECTION:
   - Detect when nodes are unreachable
   - Assume they're dead after timeout
   - But timeout is imperfect (can't distinguish dead from slow)

3. MONITORING AND ALERTING:
   - Monitor network health
   - Alert when partitions occur
   - Manual intervention if needed

KEY INSIGHT:
Network partitions are inevitable. Design your system to handle them.
Use quorums to prevent split-brain and ensure consistency.
                """,
                key_points=[
                    "Network partition isolates groups of nodes",
                    "Nodes think other nodes are dead",
                    "Risk of split-brain without quorums",
                    "CAP theorem: can't have all 3 properties",
                    "Quorums prevent split-brain"
                ],
                follow_up="How would you detect a network partition? How long should the timeout be?",
                difficulty="medium"
            ),
        ]

    @staticmethod
    def print_all_questions():
        """Print all interview questions with answers."""
        questions = Chapter8InterviewGuide.get_questions()

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
        questions = Chapter8InterviewGuide.get_questions()
        filtered = [q for q in questions if q.difficulty == difficulty]

        print(f"\n{'=' * 70}")
        print(f"CHAPTER 8 INTERVIEW QUESTIONS - {difficulty.upper()}")
        print(f"{'=' * 70}")

        for i, q in enumerate(filtered, 1):
            print(f"\n{i}. {q.question}")

    @staticmethod
    def get_study_guide() -> str:
        """Return a comprehensive study guide."""
        return """
CHAPTER 8 STUDY GUIDE: The Trouble with Distributed Systems

KEY CONCEPTS TO MASTER:

1. PARTIAL FAILURES
   - Single machine: Either works or crashes (deterministic)
   - Distributed system: Some parts work, some fail (nondeterministic)
   - You may not even know which parts have failed

2. UNRELIABLE NETWORKS
   - Packets can be lost
   - Delays are unbounded
   - Network partitions can isolate groups of nodes
   - You cannot distinguish between dead nodes and slow nodes

3. UNRELIABLE CLOCKS
   - Clock skew: Different machines' clocks disagree
   - NTP jumps: Clocks can jump backward
   - Process pauses: Processes can freeze for unpredictable durations
   - Solutions: Logical clocks, fencing tokens, TrueTime

4. TRUTH IS DEFINED BY MAJORITY
   - Single node's judgment is unreliable
   - Quorum (majority) provides consensus
   - Prevents split-brain and zombie leaders
   - Enables fault tolerance

5. BYZANTINE FAULTS
   - Nodes can lie or send contradictory messages
   - Most databases don't need Byzantine tolerance
   - Byzantine tolerance is 3x more expensive than crash tolerance
   - Needed for blockchains and adversarial systems

STUDY STRATEGY:

1. Read the textbook.md for conceptual understanding
2. Run the code examples to see concepts in action
3. Modify the code to experiment with different scenarios
4. Answer the interview questions without looking at answers
5. Review the key points and follow-up questions

COMMON INTERVIEW PATTERNS:

Pattern 1: "What can go wrong?"
- Network packet loss
- Network delay
- Network partition
- Clock skew
- Process pause
- Node crash
- Byzantine node

Pattern 2: "How do you solve it?"
- Timeouts (imperfect)
- Quorums (prevents split-brain)
- Fencing tokens (prevents zombie writes)
- Logical clocks (reliable ordering)
- Monitoring and alerting

Pattern 3: "What are the trade-offs?"
- Consistency vs Availability (CAP theorem)
- Latency vs Reliability (timeouts)
- Cost vs Fault Tolerance (quorum size)
- Complexity vs Safety (Byzantine tolerance)

PRACTICE EXERCISES:

1. Design a leader election algorithm using quorums
2. Implement a distributed lock service with fencing tokens
3. Simulate a network partition and show how quorums prevent split-brain
4. Explain why LWW with physical timestamps is broken
5. Design a system that tolerates Byzantine nodes

RESOURCES:

- Chapter 8 of "Designing Data-Intensive Applications"
- Raft consensus algorithm (https://raft.github.io/)
- Paxos algorithm (Leslie Lamport's papers)
- Google Spanner paper (TrueTime)
- Byzantine Generals Problem (Lamport, Shostak, Pease)
"""


def main():
    """Run the interview guide."""
    print("=" * 70)
    print("CHAPTER 8: INTERVIEW-LEVEL QUESTIONS AND TEACHING GUIDE")
    print("=" * 70)

    # Print study guide
    print(Chapter8InterviewGuide.get_study_guide())

    # Print by difficulty
    print("\n" + "=" * 70)
    print("QUESTIONS BY DIFFICULTY")
    print("=" * 70)
    for difficulty in ["easy", "medium", "hard"]:
        Chapter8InterviewGuide.print_by_difficulty(difficulty)

    print("\n" + "=" * 70)
    print("To see detailed answers, run:")
    print("  python -c \"from interview_guide import Chapter8InterviewGuide; Chapter8InterviewGuide.print_all_questions()\"")
    print("=" * 70)


if __name__ == "__main__":
    main()
