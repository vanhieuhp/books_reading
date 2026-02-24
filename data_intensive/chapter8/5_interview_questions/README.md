# Section 5: Interview-Level Questions

This section contains 8 interview-level questions with detailed answers and teaching notes.

## 📚 Contents

- **[interview_guide.py](./interview_guide.py)** - 8 interview questions with detailed answers

## 🎯 Learning Objectives

After this section, you should be able to:

1. Answer all 8 interview questions confidently
2. Explain the key concepts behind each answer
3. Discuss trade-offs and design decisions
4. Apply these concepts to real-world scenarios

## 📖 Interview Questions

### Easy Questions (2)

1. **A client sends a request and receives no response. What are the possible causes?**
   - Request lost
   - Server slow
   - Response lost
   - Server crashed
   - All look identical from client's perspective

2. **What is a quorum and why is it important?**
   - Quorum = majority of nodes
   - Prevents split-brain
   - Enables fault tolerance

### Medium Questions (4)

3. **Why can't you use wall-clock timestamps to reliably order events in a distributed system?**
   - Clock skew: different machines' clocks disagree
   - NTP jumps: clocks can jump backward
   - Even 1ms of skew can cause data loss

4. **What is the difference between a crash fault and a Byzantine fault?**
   - Crash fault: node stops responding (honest failure)
   - Byzantine fault: node sends arbitrary messages (dishonest failure)
   - CFT needs f+1 nodes, BFT needs 3f+1 nodes

5. **Why are GC pauses dangerous for distributed systems?**
   - Missed heartbeats (false failure detection)
   - Expired leases (zombie writes)
   - Process pause can cause split-brain

6. **What is a network partition and how does it affect distributed systems?**
   - Network link failure isolating groups of nodes
   - Risk of split-brain without quorums
   - CAP theorem: can't have all 3 properties

### Hard Questions (2)

7. **What is a fencing token and why is it needed?**
   - Monotonically increasing number with each lease
   - Prevents zombie processes from corrupting data
   - Storage layer rejects stale tokens

8. **How does Google Spanner solve the clock synchronization problem?**
   - Uses GPS and atomic clocks
   - TrueTime returns uncertainty interval
   - Transactions wait for intervals to pass
   - Extremely expensive, not practical for most systems

## 🚀 Running the Interview Guide

```bash
python interview_guide.py
```

This will print:
1. Study guide with key concepts
2. All 8 interview questions with detailed answers
3. Questions organized by difficulty level

## 💡 How to Use This Guide

### For Learning

1. Read the study guide to understand key concepts
2. Read each question and try to answer it yourself
3. Compare your answer with the provided answer
4. Review the key points and follow-up questions

### For Interview Preparation

1. Print out the questions (without answers)
2. Practice answering each question
3. Time yourself (aim for 2-3 minutes per question)
4. Review your answers against the provided answers
5. Practice follow-up questions

### For Teaching

1. Use the questions to assess understanding
2. Use the key points to guide discussions
3. Use the follow-up questions to deepen understanding
4. Use the study guide to provide context

## 📚 Study Guide Topics

The study guide covers:

1. **Partial Failures**
   - Single machine vs distributed system
   - Nondeterminism and partial failure

2. **Unreliable Networks**
   - Packet loss and delays
   - Network partitions
   - Timeouts and unbounded delays

3. **Unreliable Clocks**
   - Clock skew and NTP jumps
   - Process pauses
   - Fencing tokens

4. **Truth is Defined by Majority**
   - Quorums and consensus
   - Preventing split-brain
   - Zombie leaders

5. **Byzantine Faults**
   - Crash faults vs Byzantine faults
   - Fault tolerance requirements
   - When Byzantine tolerance is needed

## 🎓 Interview Preparation Strategy

### Week 1: Learn the Concepts

- Read Chapter 8 of "Designing Data-Intensive Applications"
- Run the code examples in `2_truth_and_majority/` and `4_byzantine_faults/`
- Read the study guide

### Week 2: Answer the Questions

- Try to answer each question without looking at the answer
- Compare your answer with the provided answer
- Identify gaps in your understanding

### Week 3: Practice and Refine

- Practice answering questions out loud
- Time yourself (aim for 2-3 minutes per question)
- Practice follow-up questions
- Discuss with others

### Week 4: Mock Interviews

- Have someone ask you the questions
- Practice explaining concepts clearly
- Practice handling follow-up questions
- Get feedback on your explanations

## 💡 Tips for Answering Interview Questions

1. **Start with the big picture**
   - Explain the problem first
   - Then explain the solution
   - Then explain the trade-offs

2. **Use examples**
   - Concrete examples are easier to understand
   - Use numbers and specific scenarios
   - Draw diagrams if possible

3. **Explain the trade-offs**
   - Every solution has trade-offs
   - Explain what you're trading off
   - Explain when each approach is appropriate

4. **Show your thinking**
   - Explain your reasoning
   - Show how you arrived at the answer
   - Discuss alternative approaches

5. **Be honest about what you don't know**
   - It's okay to say "I don't know"
   - Explain how you would find the answer
   - Show your problem-solving approach

## 🔗 Related Resources

- Chapter 8 of "Designing Data-Intensive Applications"
- Raft consensus algorithm: https://raft.github.io/
- Paxos algorithm: Leslie Lamport's papers
- Google Spanner paper: https://research.google/pubs/spanner-googles-globally-distributed-database/
- Byzantine Generals Problem: Lamport, Shostak, Pease

## 📖 Key Terminology

| Term | Definition |
|------|-----------|
| **Partial Failure** | Some components work, some fail, in unpredictable combinations |
| **Network Partition** | Network link failure isolating groups of nodes |
| **Quorum** | Majority of nodes (more than half) |
| **Split-Brain** | Two nodes both think they're the leader |
| **Fencing Token** | Monotonically increasing token to prevent stale writes |
| **Byzantine Fault** | Node that behaves arbitrarily (lies, sends contradictory messages) |
| **Clock Skew** | Different machines' clocks disagree on current time |
| **Process Pause** | Process frozen by GC, VM suspension, or OS scheduling |

## 🎯 Success Criteria

You should be able to:

- [ ] Answer all 8 questions confidently
- [ ] Explain the key concepts behind each answer
- [ ] Discuss trade-offs and design decisions
- [ ] Answer follow-up questions
- [ ] Apply these concepts to real-world scenarios
- [ ] Explain why distributed systems are hard
- [ ] Design systems that handle partial failures
- [ ] Explain when Byzantine tolerance is needed

---

**Start with `python interview_guide.py` to begin!**
