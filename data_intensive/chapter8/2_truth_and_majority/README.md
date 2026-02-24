# Section 2: The Truth is Defined by the Majority

This section covers quorum-based consensus and distributed locks.

## 📚 Contents

- **[QUICKSTART.md](./QUICKSTART.md)** - Get started in 3 steps
- **[01_quorum_basics.py](./01_quorum_basics.py)** - Quorum fundamentals and leader election
- **[02_quorum_locks.py](./02_quorum_locks.py)** - Distributed locks with fencing tokens

## 🎯 Learning Objectives

After this section, you should understand:

1. **Quorum Basics**
   - What is a quorum and how to calculate it
   - How quorums prevent split-brain
   - Fault tolerance with quorums

2. **Leader Election**
   - How nodes vote for a leader
   - Why a single node can't declare itself leader
   - How quorums ensure only one leader

3. **Network Partitions**
   - What happens when the network splits
   - Why only one partition can have a quorum
   - How quorums prevent split-brain

4. **Distributed Locks**
   - How quorums are used for locks
   - The zombie process problem
   - How fencing tokens prevent data corruption

## 🔑 Key Concepts

### Quorum

A **quorum** is a majority of nodes.

For n nodes: `quorum_size = floor(n/2) + 1`

Examples:
- 3 nodes: quorum = 2
- 5 nodes: quorum = 3
- 7 nodes: quorum = 4

### Fault Tolerance

A system can tolerate f failures if it has at least 2f+1 nodes.

Examples:
- 3 nodes: can tolerate 1 failure
- 5 nodes: can tolerate 2 failures
- 7 nodes: can tolerate 3 failures

### Split-Brain Prevention

With a network partition, only ONE partition can have a quorum.

Example: 5 nodes partitioned into 3 and 2
- Partition A (3 nodes): Has quorum (3 >= 3) → can elect leader
- Partition B (2 nodes): No quorum (2 < 3) → cannot elect leader
- Result: No split-brain!

### Fencing Tokens

A monotonically increasing number issued with each lease.

Prevents a zombie process (one that resumed after a pause) from doing damage:

```
1. Lock service issues lease with token = 33
   Thread 1 gets token 33

2. Thread 1 pauses for 15 seconds (GC pause)

3. Lock service issues new lease with token = 34
   Thread 2 gets token 34

4. Thread 1 resumes, tries to write with token 33
   Storage layer: "I've already seen token 34"
   Storage layer REJECTS write (token 33 is stale)

5. Thread 2 writes with token 34
   Storage layer ACCEPTS write
```

## 📖 Code Examples

### Example 1: Quorum Calculation

```python
from chapter8_2_truth_and_majority.quorum_basics import QuorumVoter

nodes = [Node(i) for i in range(5)]
voter = QuorumVoter(nodes)

print(f"Quorum size: {voter.get_quorum_size()}")  # 3
print(f"Can tolerate: {voter.can_tolerate_failures()} failures")  # 2
```

### Example 2: Leader Election

```python
voter.simulate_election(candidate_id=0, term=1)
# Output:
# --- Leader Election ---
# Candidate 0 requesting votes for term 1
# Quorum size needed: 3 out of 5 nodes
# Votes received: {0: True, 1: True, 2: True, 3: False, 4: False}
# Vote count: 3/5
# ✓ Candidate 0 becomes LEADER
```

### Example 3: Network Partition

```python
sim = NetworkPartitionSimulation(total_nodes=5)
sim.simulate_partition(partition_a_size=3)
# Output:
# --- Network Partition Simulation ---
# Total nodes: 5
# Partition A: 3 nodes
# Partition B: 2 nodes
# Quorum size needed: 3
#
# Partition A can elect leader: True
# Partition B can elect leader: False
# ✓ SAFE: Only one partition can elect a leader
```

### Example 4: Distributed Locks

```python
lock_service = QuorumLockService(num_nodes=5)
lock = lock_service.acquire_lock("resource_1", "client_a", ttl=10.0)
# Output:
# ✓ Lock acquired: Lock(id=resource_1, client=client_a, token=1)
```

### Example 5: Zombie Process Prevention

```python
sim = ZombieProcessSimulation()
sim.simulate_zombie_without_fencing()
# Output:
# ⚠️  DATA CORRUPTION: Both clients wrote during 'exclusive' period!

sim.simulate_zombie_with_fencing()
# Output:
# ✓ DATA SAFE: Storage layer acted as final safeguard!
```

## 🚀 Running the Examples

### Run all examples:

```bash
python 01_quorum_basics.py
python 02_quorum_locks.py
```

### Run specific examples:

```bash
# Just quorum basics
python 01_quorum_basics.py

# Just distributed locks
python 02_quorum_locks.py
```

## 💡 Experiments

### Experiment 1: Change System Size

Edit `01_quorum_basics.py`:

```python
# Try different system sizes
for n in [3, 5, 7, 9, 11]:
    quorum = (n // 2) + 1
    tolerance = n - quorum
    print(f"{n} nodes: quorum={quorum}, can tolerate {tolerance} failures")
```

### Experiment 2: Simulate Different Partitions

Edit `01_quorum_basics.py`:

```python
sim = NetworkPartitionSimulation(total_nodes=7)

# Try different partition sizes
for partition_a_size in range(1, 7):
    sim.simulate_partition(partition_a_size)
```

### Experiment 3: Lock Expiration

Edit `02_quorum_locks.py`:

```python
lock_service = QuorumLockService(num_nodes=5)
lock = lock_service.acquire_lock("resource", "client_a", ttl=5.0)

# Advance time past expiration
lock_service.advance_time(6.0)

# Try to acquire same lock
lock2 = lock_service.acquire_lock("resource", "client_b", ttl=5.0)
# Should succeed because first lock expired
```

## 🎓 Interview Questions

1. **What is a quorum and why is it important?**
   - Quorum = majority of nodes
   - Prevents split-brain
   - Enables fault tolerance

2. **How does a quorum prevent split-brain?**
   - Only one partition can have a majority
   - Other partition cannot make decisions
   - No conflicting decisions

3. **What is a fencing token and why is it needed?**
   - Monotonically increasing number with each lease
   - Prevents zombie processes from corrupting data
   - Storage layer rejects stale tokens

4. **How would you implement quorum-based leader election?**
   - Candidate requests votes from all nodes
   - Candidate becomes leader if it gets quorum votes
   - Prevents zombie leaders

5. **What happens if a node in the quorum is Byzantine (lying)?**
   - That's Byzantine fault tolerance
   - Requires 3f+1 nodes to tolerate f Byzantine nodes
   - See `4_byzantine_faults/` for details

## 📚 Key Terminology

| Term | Definition |
|------|-----------|
| **Quorum** | Majority of nodes (more than half) |
| **Split-Brain** | Two nodes both think they're the leader |
| **Zombie Leader** | Node that thinks it's the leader but network has partitioned |
| **Network Partition** | Network link failure isolating groups of nodes |
| **Fencing Token** | Monotonically increasing token to prevent stale writes |
| **Zombie Process** | Process that resumed after pause and thinks it holds expired lease |

## 🔗 Related Concepts

- **Raft Consensus Algorithm** - Uses quorums for leader election
- **Paxos Algorithm** - Classic consensus algorithm
- **Byzantine Generals Problem** - Classic problem in distributed systems
- **CAP Theorem** - Consistency, Availability, Partition tolerance trade-offs

## 📖 Further Reading

- Chapter 8 of "Designing Data-Intensive Applications"
- Raft consensus algorithm: https://raft.github.io/
- Paxos algorithm: Leslie Lamport's papers
- Byzantine Generals Problem: Lamport, Shostak, Pease

---

**Start with [QUICKSTART.md](./QUICKSTART.md) to begin!**
