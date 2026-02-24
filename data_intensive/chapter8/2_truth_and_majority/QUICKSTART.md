# Quick Start: Truth is Defined by the Majority

Get started with quorum-based consensus in 3 steps.

## Step 1: Understand the Problem

In distributed systems, a single node cannot trust its own judgment:

- A node thinks it's the leader, but the network has partitioned
- The other nodes have elected a new leader
- Now there are TWO leaders (split-brain) → data corruption!

**Solution: Quorums**

A node can only believe something if a **majority** (quorum) of nodes agrees.

## Step 2: Run the Basic Example

```bash
python 01_quorum_basics.py
```

This demonstrates:
- How quorum size is calculated
- How many failures a system can tolerate
- Leader election with quorum voting
- Network partitions and split-brain prevention

**Key insight:** Only the partition with a quorum can elect a leader.

## Step 3: Run the Distributed Locks Example

```bash
python 02_quorum_locks.py
```

This demonstrates:
- How quorums are used for distributed locks
- The zombie process problem
- How fencing tokens prevent data corruption

**Key insight:** Even if a process doesn't know its lease expired, the storage layer can reject stale writes using fencing tokens.

## 🎯 What You'll Learn

### Quorum Basics

For n nodes:
- **Quorum size** = floor(n/2) + 1
- **Fault tolerance** = n - quorum_size

Examples:
- 3 nodes: quorum = 2, can tolerate 1 failure
- 5 nodes: quorum = 3, can tolerate 2 failures
- 7 nodes: quorum = 4, can tolerate 3 failures

### Network Partitions

With a 5-node system partitioned into 3 and 2:
- Partition A (3 nodes): Has quorum → can elect leader
- Partition B (2 nodes): No quorum → cannot elect leader
- Result: No split-brain!

### Distributed Locks

A lock is only valid if a **quorum** of lock service nodes confirms it:

```
Client A: Requests lock from 5 nodes
          Gets confirmation from 3 nodes (quorum)
          Lock is acquired

Network partition: 3 nodes in Partition A, 2 in Partition B

Client B in Partition B: Requests lock from 2 nodes
                         Gets confirmation from 2 nodes
                         But 2 < 3 (quorum), so lock is NOT acquired
                         No data corruption!
```

### Fencing Tokens

Prevents zombie processes from corrupting data:

```
1. Thread 1 acquires lock with token 33
2. Thread 1 pauses (GC pause)
3. Thread 2 acquires lock with token 34
4. Thread 1 resumes, tries to write with token 33
5. Storage layer: "Token 33 < 34, REJECT"
6. Thread 2 writes with token 34: ACCEPT
```

## 💡 Experiments to Try

### Experiment 1: Change Quorum Size

Edit `01_quorum_basics.py` and change the number of nodes:

```python
nodes = [Node(i) for i in range(7)]  # Try 7 nodes instead of 5
```

See how quorum size and fault tolerance change.

### Experiment 2: Simulate Different Partitions

Edit `01_quorum_basics.py` and try different partition sizes:

```python
sim.simulate_partition(partition_a_size=4)  # 4-1 partition
sim.simulate_partition(partition_a_size=2)  # 2-3 partition
```

See which partitions can elect leaders.

### Experiment 3: Zombie Process Scenarios

Edit `02_quorum_locks.py` and modify the pause duration:

```python
lock_service.advance_time(20.0)  # Longer pause
```

See how fencing tokens prevent data corruption.

## 🔑 Key Takeaways

1. **Quorums prevent split-brain** - Only one partition can have a majority
2. **Quorums enable fault tolerance** - System can tolerate f failures with 2f+1 nodes
3. **Fencing tokens prevent zombie writes** - Storage layer is the final safeguard
4. **Truth is defined by majority** - Single node's judgment is unreliable

## 📚 Next Steps

1. Read the detailed explanations in the code comments
2. Try the experiments above
3. Answer the interview questions in `5_interview_questions/`
4. Design your own leader election algorithm using quorums

## ❓ Common Questions

**Q: Why do we need a quorum? Can't we just use a timeout?**

A: Timeouts are imperfect. With a network partition, both partitions might think the other is dead. Quorums ensure only one partition can make decisions.

**Q: What if we have an even number of nodes?**

A: Quorum = floor(n/2) + 1, so:
- 4 nodes: quorum = 3
- 6 nodes: quorum = 4

With an even number, you can't split evenly. One partition will always have the quorum.

**Q: What if a node in the quorum is Byzantine (lying)?**

A: That's Byzantine fault tolerance, which requires 3f+1 nodes to tolerate f Byzantine nodes. See `4_byzantine_faults/` for details.

**Q: How do you detect a network partition?**

A: You can't directly detect it. You use timeouts: if a node doesn't respond within X seconds, assume it's dead. But this is imperfect (can't distinguish dead from slow).

---

**Ready to dive deeper? Check out the detailed code examples and interview questions!**
