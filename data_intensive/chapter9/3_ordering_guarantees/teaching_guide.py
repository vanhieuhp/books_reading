"""
Teaching Guide: Chapter 9, Section 3 - Ordering Guarantees

This guide contains interview-level questions and detailed answers to help you
master the concepts of ordering guarantees in distributed systems.

Key concepts:
- Causal ordering (partial order)
- Total order
- Total order broadcast
- Relationship to linearizability and consensus
"""


class TeachingGuide:
    """Interactive teaching guide with interview questions"""

    @staticmethod
    def question_1():
        """
        Q1: What is the difference between causal ordering and total ordering?
        Difficulty: Medium
        """
        return {
            "question": "What is the difference between causal ordering and total ordering?",
            "difficulty": "Medium",
            "answer": """
CAUSAL ORDERING (Partial Order):
- Preserves the "happened-before" relationship
- If event A causally caused event B, all nodes must see A before B
- Events that are NOT causally related (concurrent) can be seen in any order
- Example: Question → Answer → Comment (causal chain)
           Two independent questions (concurrent, any order)

TOTAL ORDERING (Total Order):
- Every pair of events is ordered
- All nodes see events in the SAME order
- No concurrent events (or rather, concurrent events have a defined order)
- Example: All events in a single-leader replication log

KEY DIFFERENCE:
- Causal: Some events are ordered, some are not (partial order)
- Total: All events are ordered (total order)

ANALOGY:
- Causal: "If A caused B, B must come after A" (but A and C can be in any order)
- Total: "There's a single global order for all events"

TRADE-OFF:
- Causal: Weaker guarantee, easier to implement, lower latency
- Total: Stronger guarantee, harder to implement, higher latency
            """,
            "key_points": [
                "Causal = partial order (some events ordered, some not)",
                "Total = total order (all events ordered)",
                "Causal allows concurrent events in any order",
                "Total requires a single order for all events",
                "Causal is weaker but more efficient",
            ],
            "follow_up": [
                "Can you give an example where causal ordering is sufficient?",
                "Why would you want total ordering if causal is weaker?",
                "How does total ordering relate to linearizability?",
            ]
        }

    @staticmethod
    def question_2():
        """
        Q2: What is total order broadcast and why is it equivalent to consensus?
        Difficulty: Hard
        """
        return {
            "question": "What is total order broadcast and why is it equivalent to consensus?",
            "difficulty": "Hard",
            "answer": """
TOTAL ORDER BROADCAST (Atomic Broadcast):
A protocol that guarantees:
1. Reliable delivery: If one node receives a message, ALL nodes receive it
2. Total ordering: All nodes deliver messages in the SAME order

IMPLEMENTATION:
- Single-leader approach: Leader assigns sequence numbers
- All followers apply messages in order
- This is exactly what replication logs do

EQUIVALENCE TO CONSENSUS:
Total Order Broadcast ↔ Consensus (they're equivalent in power)

Direction 1: Total Order Broadcast → Consensus
- Use total order broadcast to order all proposals
- All nodes see the same first proposal
- That proposal is the consensus value
- Example: Leader election via total order broadcast

Direction 2: Consensus → Total Order Broadcast
- Use a linearizable register as a counter
- Each message gets the next sequence number atomically
- This provides a total order

WHY THEY'RE EQUIVALENT:
- Both require all nodes to agree on something
- Total order broadcast: agree on the order of messages
- Consensus: agree on a single value
- You can implement one using the other

PRACTICAL IMPLICATION:
- Any system that implements consensus can provide total order broadcast
- Any system that implements total order broadcast can solve consensus
- Examples: Raft, Paxos, ZooKeeper all do both
            """,
            "key_points": [
                "Total order broadcast = reliable delivery + total ordering",
                "Equivalent to consensus in power",
                "Can implement consensus using total order broadcast",
                "Can implement total order broadcast using consensus",
                "Single-leader replication implements total order broadcast",
            ],
            "follow_up": [
                "How would you implement leader election using total order broadcast?",
                "Why is total order broadcast equivalent to consensus?",
                "What's the relationship between total order broadcast and linearizability?",
            ]
        }

    @staticmethod
    def question_3():
        """
        Q3: How does total order broadcast relate to linearizability?
        Difficulty: Hard
        """
        return {
            "question": "How does total order broadcast relate to linearizability?",
            "difficulty": "Hard",
            "answer": """
RELATIONSHIP:
Total Order Broadcast → Linearizable Storage (one direction)
Linearizable Storage → Total Order Broadcast (other direction)

DIRECTION 1: Total Order Broadcast → Linearizable Storage
- Use total order broadcast to order all writes
- To do a linearizable write: broadcast "set x = v"
- Wait for the message to come back in delivery order
- When it arrives, it has been ordered relative to all other writes
- Result: Linearizable key-value store

DIRECTION 2: Linearizable Storage → Total Order Broadcast
- Use a linearizable register as a counter
- Each message gets the next sequence number atomically
- This provides a total order
- Result: Total order broadcast

KEY INSIGHT:
- Total order broadcast is the "ordering" part of linearizability
- Linearizability = total order + real-time consistency
- Total order broadcast = total order (but not necessarily real-time)

EXAMPLE:
Single-leader replication:
- Provides total order broadcast (all followers see same order)
- With synchronous replication: provides linearizability
- With asynchronous replication: provides total order only

PRACTICAL IMPLICATION:
- If you have total order broadcast, you can build linearizable storage
- If you have linearizable storage, you can implement total order broadcast
- They're equivalent in power
            """,
            "key_points": [
                "Total order broadcast can implement linearizable storage",
                "Linearizable storage can implement total order broadcast",
                "They're equivalent in power",
                "Linearizability = total order + real-time consistency",
                "Single-leader replication provides total order broadcast",
            ],
            "follow_up": [
                "Why is total order broadcast weaker than linearizability?",
                "How would you add real-time consistency to total order broadcast?",
                "What's the performance difference between total order and linearizability?",
            ]
        }

    @staticmethod
    def question_4():
        """
        Q4: Explain the concept of vector clocks and how they track causality.
        Difficulty: Hard
        """
        return {
            "question": "Explain the concept of vector clocks and how they track causality.",
            "difficulty": "Hard",
            "answer": """
VECTOR CLOCKS:
A mechanism for tracking causal relationships in distributed systems.

HOW THEY WORK:
1. Each node maintains a vector of logical timestamps
   - Vector has one entry per node
   - Initially all zeros: [0, 0, 0] for 3 nodes

2. On local event:
   - Increment your own entry
   - Example: Node A increments: [1, 0, 0]

3. On sending message:
   - Increment your own entry
   - Send the vector with the message
   - Example: Node A sends with [2, 0, 0]

4. On receiving message:
   - Merge vectors: take max of each component
   - Then increment your own entry
   - Example: Node B receives [2, 0, 0], merges to [2, 1, 0], then increments to [2, 2, 0]

CAUSALITY DETECTION:
- Event A happened before Event B if A's vector < B's vector (component-wise)
- Events are concurrent if neither vector is less than the other

EXAMPLE:
Node A: [1, 0, 0] → sends message → [2, 0, 0]
Node B: receives [2, 0, 0] → [2, 1, 0] → local event → [2, 2, 0]
Node C: receives [2, 2, 0] → [2, 2, 1]

Causality:
- A's event [1, 0, 0] happened before B's event [2, 1, 0] [OK]
- B's event [2, 2, 0] happened before C's event [2, 2, 1] [OK]
- A's event [1, 0, 0] happened before C's event [2, 2, 1] [OK]

ADVANTAGES:
- Precisely tracks causal relationships
- Can detect concurrent events
- No need for synchronized clocks

DISADVANTAGES:
- Vector size grows with number of nodes
- Overhead for every message
- Not practical for very large systems

PRACTICAL USE:
- Git uses similar concepts (DAG of commits)
- Riak uses vector clocks for conflict detection
- Dynamo uses vector clocks for versioning
            """,
            "key_points": [
                "Vector clocks track causal relationships",
                "Each node maintains a vector of logical timestamps",
                "Increment own entry on local event",
                "Merge vectors on message receipt",
                "Can detect concurrent events",
                "Overhead grows with number of nodes",
            ],
            "follow_up": [
                "How would you detect concurrent events using vector clocks?",
                "What's the overhead of vector clocks in a large system?",
                "How does Git use similar concepts?",
            ]
        }

    @staticmethod
    def question_5():
        """
        Q5: In a single-leader replication system, what ordering guarantee does the
            replication log provide?
        Difficulty: Medium
        """
        return {
            "question": """In a single-leader replication system, what ordering guarantee does the
            replication log provide?""",
            "difficulty": "Medium",
            "answer": """
SINGLE-LEADER REPLICATION:
- All writes go to the leader
- Leader writes to its WAL (Write-Ahead Log)
- Leader sends log entries to followers
- Followers apply entries in the same order

ORDERING GUARANTEE:
The replication log provides TOTAL ORDER BROADCAST:
1. Reliable delivery: All followers eventually get all entries
2. Total ordering: All followers apply entries in the same order

WHAT IT PROVIDES:
- Total order: All nodes see writes in the same order
- Causal consistency: If write A depends on write B, B comes before A
- NOT linearizability: Order might not match real-time

EXAMPLE:
Leader receives writes: W1, W2, W3
- Writes to WAL: [W1, W2, W3]
- Sends to followers
- All followers apply: W1, then W2, then W3

SYNCHRONOUS vs ASYNCHRONOUS:
- Synchronous replication: Provides linearizability
  (leader waits for quorum to acknowledge before responding to client)
- Asynchronous replication: Provides total order only
  (leader responds immediately, followers catch up later)

PRACTICAL SYSTEMS:
- PostgreSQL: Streaming replication (total order)
- MySQL: Binlog replication (total order)
- MongoDB: Oplog replication (total order)
- All provide total order broadcast via replication log
            """,
            "key_points": [
                "Replication log provides total order broadcast",
                "All followers see writes in the same order",
                "Provides causal consistency",
                "NOT linearizability (unless synchronous)",
                "Synchronous replication adds linearizability",
            ],
            "follow_up": [
                "What's the difference between synchronous and asynchronous replication?",
                "Why doesn't asynchronous replication provide linearizability?",
                "How would you add linearizability to asynchronous replication?",
            ]
        }

    @staticmethod
    def question_6():
        """
        Q6: Why is total order broadcast equivalent to consensus?
        Difficulty: Hard
        """
        return {
            "question": "Why is total order broadcast equivalent to consensus?",
            "difficulty": "Hard",
            "answer": """
CONSENSUS PROBLEM:
Get all nodes to agree on a single value.

TOTAL ORDER BROADCAST PROBLEM:
Get all nodes to deliver messages in the same order.

WHY THEY'RE EQUIVALENT:

DIRECTION 1: Total Order Broadcast → Consensus
Problem: Multiple nodes propose different values. Reach consensus.

Solution using total order broadcast:
1. Each node broadcasts its proposed value
2. Use total order broadcast to order all proposals
3. All nodes see the same first proposal
4. That proposal is the consensus value
5. All nodes agree!

Example: Leader election
- Node A proposes itself as leader
- Node B proposes itself as leader
- Node C proposes itself as leader
- Total order broadcast orders proposals: A, B, C
- All nodes see A first
- A is elected leader (consensus!)

DIRECTION 2: Consensus → Total Order Broadcast
Problem: Order messages so all nodes see them in the same order.

Solution using consensus:
1. Use a linearizable register as a counter
2. For each message, use consensus to assign the next sequence number
3. All nodes agree on the sequence number
4. Messages are ordered by sequence number
5. All nodes deliver in the same order

Example:
- Message M1: consensus assigns sequence 1
- Message M2: consensus assigns sequence 2
- Message M3: consensus assigns sequence 3
- All nodes deliver: M1, M2, M3

WHY THEY'RE EQUIVALENT:
- Both require all nodes to agree on something
- Total order broadcast: agree on the order
- Consensus: agree on a value
- You can implement one using the other
- They have the same fundamental difficulty

PRACTICAL IMPLICATION:
- Raft implements both consensus and total order broadcast
- Paxos implements both consensus and total order broadcast
- ZooKeeper implements both
- If you solve one, you've solved the other
            """,
            "key_points": [
                "Total order broadcast can implement consensus",
                "Consensus can implement total order broadcast",
                "They're equivalent in power",
                "Both require all nodes to agree",
                "Raft, Paxos, ZooKeeper implement both",
            ],
            "follow_up": [
                "How would you implement leader election using total order broadcast?",
                "How would you implement total order broadcast using consensus?",
                "Why are they equivalent?",
            ]
        }

    @staticmethod
    def question_7():
        """
        Q7: What are the trade-offs between causal consistency and total order?
        Difficulty: Medium
        """
        return {
            "question": "What are the trade-offs between causal consistency and total order?",
            "difficulty": "Medium",
            "answer": """
CAUSAL CONSISTENCY:
- Preserves cause-and-effect relationships
- Concurrent events can be in any order
- Weaker guarantee
- Lower latency
- Higher availability

TOTAL ORDER:
- All nodes see events in the same order
- No concurrent events (or defined order)
- Stronger guarantee
- Higher latency
- Lower availability

TRADE-OFFS:

1. CONSISTENCY vs PERFORMANCE
   Causal: Weaker consistency, better performance
   Total: Stronger consistency, worse performance

2. IMPLEMENTATION COMPLEXITY
   Causal: Easier to implement (vector clocks)
   Total: Harder to implement (need leader or consensus)

3. AVAILABILITY
   Causal: More available (can work with partitions)
   Total: Less available (need quorum)

4. LATENCY
   Causal: Lower latency (local operations possible)
   Total: Higher latency (need coordination)

5. USE CASES
   Causal: Q&A forums, social media, collaborative editing
   Total: Financial transactions, inventory management

WHEN TO USE CAUSAL:
- Concurrent events don't conflict
- Availability is important
- Latency is critical
- Example: Social media (posts and comments)

WHEN TO USE TOTAL:
- Concurrent events might conflict
- Consistency is important
- Latency is acceptable
- Example: Bank transfers, inventory

PRACTICAL SYSTEMS:
- Cassandra: Eventual consistency (weak)
- Riak: Causal consistency (with vector clocks)
- PostgreSQL: Total order (single-leader)
- ZooKeeper: Linearizability (total order + real-time)
            """,
            "key_points": [
                "Causal: weaker, faster, more available",
                "Total: stronger, slower, less available",
                "Causal allows concurrent events in any order",
                "Total requires a single order",
                "Choose based on application needs",
            ],
            "follow_up": [
                "Can you give an example where causal is sufficient?",
                "Can you give an example where total order is needed?",
                "What's the performance difference?",
            ]
        }

    @staticmethod
    def question_8():
        """
        Q8: How would you implement a distributed counter using total order broadcast?
        Difficulty: Hard
        """
        return {
            "question": "How would you implement a distributed counter using total order broadcast?",
            "difficulty": "Hard",
            "answer": """
PROBLEM:
Implement a counter that can be incremented from multiple nodes, with all nodes
seeing the same value.

SOLUTION USING TOTAL ORDER BROADCAST:

1. BROADCAST INCREMENTS
   - Each node broadcasts "increment" messages
   - Total order broadcast ensures all nodes see increments in the same order

2. APPLY IN ORDER
   - Each node maintains a local counter
   - Applies increments in the order received from total order broadcast
   - All nodes end up with the same value

IMPLEMENTATION:

class DistributedCounter:
    def __init__(self, node_id, nodes):
        self.node_id = node_id
        self.counter = 0
        self.log = []  # Total order broadcast log
        self.applied = 0  # How many log entries applied

    def increment(self):
        # Broadcast increment message
        msg = Message(f"INC_{self.node_id}_{time.time()}", "increment")
        broadcast(msg)  # Uses total order broadcast

    def apply_log(self):
        # Apply all unapplied log entries in order
        while self.applied < len(self.log):
            msg = self.log[self.applied]
            self.counter += 1
            self.applied += 1

    def get_value(self):
        self.apply_log()
        return self.counter

EXAMPLE:
Node A: increment() → broadcasts INC_A_1
Node B: increment() → broadcasts INC_B_1
Node C: increment() → broadcasts INC_C_1

Total order broadcast orders: INC_A_1, INC_B_1, INC_C_1

All nodes apply in order:
- Apply INC_A_1: counter = 1
- Apply INC_B_1: counter = 2
- Apply INC_C_1: counter = 3

All nodes have counter = 3 [OK]

WHY THIS WORKS:
- Total order broadcast ensures all nodes see increments in the same order
- Each node applies in the same order
- All nodes end up with the same value

ADVANTAGES:
- Simple to understand
- Guaranteed consistency
- Works across network partitions (eventually)

DISADVANTAGES:
- Latency: Must wait for total order broadcast
- Throughput: Limited by broadcast latency
- Not suitable for high-frequency updates

REAL-WORLD EXAMPLE:
- Kafka: Each partition has a log with sequence numbers
- Consumers read in order
- All consumers see the same order
- Can implement distributed counters on top
            """,
            "key_points": [
                "Broadcast increment messages",
                "Use total order broadcast to order increments",
                "Each node applies in the same order",
                "All nodes end up with the same value",
                "Simple but has latency overhead",
            ],
            "follow_up": [
                "What's the latency of this approach?",
                "How would you optimize for high-frequency updates?",
                "How does this compare to a single-leader counter?",
            ]
        }

    @staticmethod
    def run_interactive_guide():
        """Run the interactive teaching guide"""
        questions = [
            TeachingGuide.question_1(),
            TeachingGuide.question_2(),
            TeachingGuide.question_3(),
            TeachingGuide.question_4(),
            TeachingGuide.question_5(),
            TeachingGuide.question_6(),
            TeachingGuide.question_7(),
            TeachingGuide.question_8(),
        ]

        print("=" * 80)
        print("TEACHING GUIDE: Chapter 9, Section 3 - Ordering Guarantees")
        print("=" * 80)
        print("\nThis guide contains 8 interview-level questions on ordering guarantees.")
        print("Try to answer each question before looking at the answer!\n")

        for i, q in enumerate(questions, 1):
            print(f"\n{'=' * 80}")
            print(f"QUESTION {i} ({q['difficulty']}): {q['question']}")
            print(f"{'=' * 80}")

            # Show question
            input("Press Enter to see the answer...")

            # Show answer
            print(f"\nANSWER:\n{q['answer']}")

            # Show key points
            print("\nKEY POINTS:")
            for point in q['key_points']:
                print(f"  • {point}")

            # Show follow-up questions
            print("\nFOLLOW-UP QUESTIONS:")
            for follow_up in q['follow_up']:
                print(f"  • {follow_up}")

            # Ask if user wants to continue
            response = input("\nContinue to next question? (y/n): ").strip().lower()
            if response != 'y':
                break

        print("\n" + "=" * 80)
        print("END OF TEACHING GUIDE")
        print("=" * 80)


if __name__ == "__main__":
    # Run the interactive guide
    TeachingGuide.run_interactive_guide()

    # Or print all questions at once
    print("\n\nTo see all questions at once, use:")
    print("  python teaching_guide.py --all")
