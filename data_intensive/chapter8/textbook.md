# Chapter 8: The Trouble with Distributed Systems

This is a comprehensive summary of **Chapter 8: The Trouble with Distributed Systems** from *Designing Data-Intensive Applications* by Martin Kleppmann.

---

## Introduction: Why This Chapter Matters

Chapters 5-7 described the algorithms that distributed databases use (replication, partitioning, transactions). This chapter takes a step back and asks: **What can actually go wrong?**

The answer is: everything. Networks lose packets. Clocks drift. Processes freeze for seconds at a time. This chapter is a systematic catalog of all the ways a distributed system can fail, and why these failures are fundamentally different from failures on a single computer.

**The key mental shift:** On a single computer, things either work or they don't. In a distributed system, you may have **partial failures** — some parts work while others fail, and you may not even be able to *tell* which parts have failed. This **nondeterminism** and **partial failure** is what makes distributed systems fundamentally harder than single-machine programming.

---

# 1. Faults and Partial Failures

## Single Machine vs. Distributed System

On a single computer, an operation either:
* Produces a correct result, or
* The entire computer crashes (kernel panic, hardware failure)

There is no "in-between." The software is designed to be *deterministic*: the same operation on the same data always gives the same result.

In a distributed system, the "in-between" is the norm:
* A message you sent might have been delivered, or not.
* A remote node might have processed your request, or it might have crashed.
* You might receive a response, or the network might have dropped it.
* The response you received might be from before or after a restart.

**You simply cannot tell.** The only way to know the status of a remote node is to send it a message and wait for a response. But if no response comes, you have no way of knowing *why*.

## Cloud Computing vs. High-Performance Computing (HPC)

There is a spectrum of approaches:
* **HPC (Supercomputers):** If any component fails, abort the entire computation, fix the hardware, restart from a checkpoint. This works because all nodes are in the same building with fast, reliable networking.
* **Cloud Computing:** Failures are constant and expected. You can't stop the world to fix one machine. The system must **tolerate faults** and keep running despite continuous partial failures.

DDIA focuses on the cloud computing worldview: **build reliability from unreliable components.**

---

# 2. Unreliable Networks

Most distributed systems use **shared-nothing architectures**: the only way nodes communicate is by sending messages over the network. And the network is unreliable.

## What Can Go Wrong with a Network Request

When you send a request over the network and don't receive a response, you **cannot distinguish** between these scenarios:

```
Scenario 1: Request was lost in the network
  Client ──── X ────► Server
  (Server never received the request)

Scenario 2: Server received request but is too slow
  Client ────────────► Server (processing for 30 seconds...)
  (Response hasn't come back yet)

Scenario 3: Server processed request, but response was lost
  Client ◄──── X ──── Server
  (Server did the work, but you'll never know!)

Scenario 4: Server received request, crashed while processing
  Client ────────────► Server 💥
  (May or may not have completed. Impossible to tell.)
```

From the client's perspective, all four scenarios look identical: **no response**. The client has no way to distinguish them.

## Network Partitions

A **network partition** (or **netsplit**) is when the network link between some nodes is broken, isolating them into separate groups that can communicate within a group but not across groups.

```
Normal:                    After Network Partition:
  A ◄──► B ◄──► C           A ◄──► B     C (isolated)
```

Network partitions are surprisingly common even in well-managed datacenters. Switches fail, cables are accidentally unplugged, firmware bugs cause packet loss, misconfigured firewalls block traffic, etc.

## Timeouts and Unbounded Delays

Since you can't tell if a remote node is dead or just slow, the practical approach is to use a **timeout**: if no response within X seconds, assume the node is dead.

But how long should the timeout be?
* **Too short:** You'll falsely declare healthy nodes as dead. This triggers unnecessary failovers, which cause even more load, which causes more timeouts — a cascading failure.
* **Too long:** Users wait forever for an error message. Dead nodes aren't detected quickly enough.

**Why there is no "right" timeout:** Network delays are **unbounded**. Unlike a telephone circuit (which guarantees constant bandwidth), the Internet uses **packet switching** with no guaranteed delivery time. Reasons for delay:
1. **Queueing:** Network switches buffer packets. If a switch's buffer is full, it drops packets (TCP retransmits them later, adding delay).
2. **CPU scheduling:** The OS may not run your process for several milliseconds while it handles other processes, interrupts, etc.
3. **TCP flow control:** If the receiver is slow, TCP throttles the sender, adding latency.
4. **TCP retransmits:** If a packet is lost, TCP automatically retransmits it, adding round-trip-time delays. The sender doesn't know about this.
5. **Virtualization:** In cloud environments, a VM can be paused for live migration or overcommitted CPU scheduling.

### Choosing Timeouts in Practice
Rather than using a fixed timeout:
* Systems like **Akka** and **Cassandra** use an adaptive approach: measure observed response times and their variability (jitter), and automatically adjust the timeout based on the distribution.
* **Phi Accrual Failure Detector** (used by Akka and Cassandra): Instead of a binary "dead or alive," it outputs a suspicion level (phi φ) that increases over time without a heartbeat. The application chooses its own threshold for declaring a node dead.

---

# 3. Unreliable Clocks

Every machine has its own clock, and **no two clocks agree perfectly**. Even with NTP (Network Time Protocol) synchronization, clocks drift by milliseconds, and NTP can occasionally jump backward.

This is disastrous for distributed systems because many algorithms rely on a notion of "when" an event happened.

## Two Types of Clocks

### Time-of-Day Clocks
* Returns the current date and time (e.g., `gettimeofday()`, `System.currentTimeMillis()`).
* Synchronized to NTP (but may jump forward or backward after an NTP reset).
* **Not suitable for measuring elapsed time** because it can jump.

### Monotonic Clocks
* Always moves forward (never jumps backward).
* Returns elapsed time since some arbitrary point (e.g., system boot).
* **Good for measuring durations** (e.g., "this request took 150ms").
* **Not meaningful across machines** — you can't compare monotonic clock values from two different servers.

## Clock Skew: The Silent Killer

Because NTP synchronization is imperfect, different machines can have clocks that differ by milliseconds or even seconds.

**Why this is dangerous for databases:**

### The LWW (Last-Write-Wins) Disaster with Clock Skew

```
Node A's clock: 10:00:00.100   (slightly fast)
Node B's clock: 10:00:00.000   (correct)

Write 1: Client writes to Node B at Node B's time = 10:00:00.000
Write 2: Client writes to Node A at Node A's time = 10:00:00.100

With Last-Write-Wins: Write 2 (timestamp 10:00:00.100) "wins"
                      Write 1 (timestamp 10:00:00.000) is silently deleted

But Write 1 may have actually happened AFTER Write 2 in real time!
Node A's clock was simply ahead.
```

An increment of 1ms in clock skew can cause data loss. This is why LWW with physical timestamps is fundamentally broken as a conflict resolution strategy.

### Relying on Clock for Ordering Events

**Google Spanner's approach (TrueTime):** Google uses GPS receivers and atomic clocks in every datacenter to keep clocks synchronized to within ~7ms. Spanner's API returns a time interval `[earliest, latest]` rather than a single point in time, acknowledging the inherent uncertainty. Transactions are ordered based on these intervals, waiting if intervals overlap.

This is the most expensive way to solve the problem. No open-source database replicates this approach.

## Process Pauses

Even if clocks were perfect, a process can be **paused** at any time for unpredictable durations:

1. **Garbage Collection (GC):** A Java/Go process can freeze for hundreds of milliseconds (sometimes seconds) during a full GC pause. During this pause, the process cannot do anything — it can't even respond to heartbeats.
2. **Virtual Machine suspension:** A hypervisor can suspend a VM at any time for live migration, preemption, or snapshotting.
3. **Disk I/O:** A synchronous disk access (especially to a network-attached disk) can block for seconds.
4. **Swapping (thrashing):** If the OS starts paging memory to disk, the process slows to a crawl.
5. **SIGSTOP signal:** An administrator (or a bug) can send `SIGSTOP` to pause a process indefinitely.

**Why this is dangerous:**

```
Thread 1: Acquires a lease (lock) that expires in 10 seconds.
Thread 1: Begins critical work.
Thread 1: --- GC PAUSE FOR 15 SECONDS ---
Thread 1: Resumes, believes it still holds the lease.
Thread 1: Writes data (BUT THE LEASE EXPIRED 5 SECONDS AGO!).
Thread 2: Acquired the lease during Thread 1's pause.
Thread 2: Also writes data.

Result: Both threads wrote during the "exclusive" lease period.
        Data corruption.
```

### Fencing Tokens (The Solution)

To prevent a paused process from doing damage after its lease has expired:

```
1. Lock service issues a lease with a FENCING TOKEN (monotonically increasing number).
   Thread 1 gets lease with token = 33.
   Thread 2 gets lease with token = 34 (after Thread 1's lease expired).

2. The storage service checks the fencing token on every write.
   Thread 1 (paused, wakes up): tries to write with token = 33.
   Storage service: "I've already seen token 34. Token 33 is stale. REJECTED."

3. Thread 2: writes with token = 34. ACCEPTED.
```

The fencing token ensures that even if a client doesn't realize its lease has expired, the storage system acts as the final safeguard.

---

# 4. Knowledge, Truth, and Lies

## The Truth is Defined by the Majority

In a distributed system, a node cannot trust its own judgment. Consider:
* A node thinks it's the leader, but the network has partitioned and the other nodes have elected a new leader. The old node is now a **zombie leader** — it thinks it's in charge, but nobody else agrees.
* A node thinks another node is dead (no heartbeat response), but the "dead" node is actually fine; there's just a network problem.

**The solution: quorums.** A node cannot unilaterally declare something as true. It can only believe something if a **majority** of nodes (a quorum) agrees.

This applies to:
* **Leader election:** A leader is only the leader if a majority of nodes says so.
* **Distributed locks:** A lock is only held if a majority of lock service nodes has confirmed it.
* **Consensus:** A value is only "decided" if a majority of participants agreed.

## Byzantine Faults

Everything discussed so far assumes nodes are **honest but potentially faulty** — they might crash, be slow, or lose messages, but they don't intentionally lie. A node that sends incorrect or malicious messages is called a **Byzantine fault**.

**Byzantine fault tolerance (BFT)** means: the system operates correctly even if some nodes are lying, compromised, or sending contradictory messages to different peers.

* **Most database systems do NOT need BFT** because all nodes are in the same datacenter, run by the same organization, and are trusted.
* **Where BFT matters:** Blockchain (Bitcoin, Ethereum), aerospace systems (where cosmic rays can flip bits in RAM), systems where participants may be adversarial.

BFT algorithms (like PBFT) are dramatically more complex and expensive than non-Byzantine algorithms. Kleppmann notes that it's rarely worth the cost for typical data systems.

---

# Summary Cheat Sheet

```
┌─────────────────────────┬─────────────────────────────────────────────┐
│ Problem                 │ Impact                                      │
├─────────────────────────┼─────────────────────────────────────────────┤
│ Network packet loss     │ Request or response silently disappears     │
│ Network delay           │ Can't tell if node is dead or just slow     │
│ Network partition       │ Cluster splits into isolated groups         │
│ Clock skew              │ LWW drops the "wrong" write; ordering broken│
│ Clock jump (NTP)        │ Timeouts and leases expire at wrong times   │
│ GC pause                │ Process freezes; misses heartbeats; zombies │
│ VM suspension           │ Process frozen indefinitely without warning │
│ Partial failure         │ Some nodes work, some don't; can't tell     │
└─────────────────────────┴─────────────────────────────────────────────┘
```

---

# Key Terminology

* **Partial Failure:** Some components work, some fail, in unpredictable combinations.
* **Network Partition (Netsplit):** Network link failure isolating groups of nodes.
* **Unbounded Delay:** Network delays have no upper bound (unlike telephone circuits).
* **Clock Skew:** Different machines' clocks disagree on the current time.
* **Monotonic Clock:** A clock that always moves forward (good for measuring durations).
* **Time-of-Day Clock:** Returns wall-clock time (can jump backward after NTP sync).
* **Process Pause:** A process frozen by GC, VM suspension, or OS scheduling.
* **Fencing Token:** A monotonically increasing token attached to leases/locks to prevent stale writes.
* **Byzantine Fault:** A node that behaves arbitrarily (lies, sends contradictory messages).
* **Quorum:** A majority of nodes must agree for a decision to be considered valid.

---

# Interview-Level Questions

1. **A client sends a request and receives no response. What are the possible causes?**
   → (a) Request lost, (b) Server slow, (c) Server processed it but response lost, (d) Server crashed mid-processing. All look identical from the client's perspective.

2. **Why can't you use wall-clock timestamps to reliably order events in a distributed system?**
   → Clock skew. Different machines' clocks can differ by milliseconds or more. NTP can jump backward. A "later" timestamp on one machine may actually represent an earlier real-world event.

3. **What is a fencing token and why is it needed?**
   → A monotonically increasing number issued with each lease. Prevents a "zombie" process (one that resumed after a GC pause) from performing writes with an expired lease. The storage layer rejects writes with stale tokens.

4. **How does Google Spanner solve the clock synchronization problem?**
   → GPS receivers and atomic clocks in every datacenter. The TrueTime API returns an uncertainty interval `[earliest, latest]` and transactions wait for the interval to pass before committing, ensuring a total order.

5. **What is the difference between a crash fault and a Byzantine fault?**
   → Crash fault: node stops responding (honest failure). Byzantine fault: node sends arbitrary or malicious messages (dishonest failure). Most databases only handle crash faults; Byzantine tolerance is needed for blockchains and adversarial environments.

6. **Why are GC pauses dangerous for distributed systems?**
   → A GC pause can cause a node to miss heartbeats (falsely declared dead), miss lease renewals (lease expires while paused), or resume and act on stale state (zombie writes). Solutions: fencing tokens, short GC pauses (G1/ZGC), or designing the system to tolerate pauses.
