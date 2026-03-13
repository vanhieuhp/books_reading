# Chapter 6: Foundations

## Chapter Overview

Chapter 6 dives deep into the foundational infrastructure that software runs on: networking, physical hardware, and system interconnect. Michael Nygard emphasizes that understanding these foundations is crucial for building reliable production systems. Even if you don't manage this infrastructure directly, knowing how it works helps you design better software.

## The Physical Reality

### Computers Are Physical

**The Implications**
- Heat must be dissipated
- Power must be supplied
- Components wear out
- Distance affects latency

**Design Implications**
- Data centers are engineered environments
- Hardware redundancy is essential
- Network topology matters
- Storage performance varies

### The Components

**Compute**
- CPUs have limits
- Memory is finite
- Storage has throughput limits
- Network bandwidth is constrained

**Network**
- Latency is not zero
- Bandwidth has limits
- Packets can be lost
- Network equipment fails

**Storage**
- Disk I/O is the bottleneck
- SSDs have different characteristics than HDDs
- Network-attached storage has variable latency
- Backups take time

## Networking Fundamentals

### The OSI Model

Understanding networking layers helps diagnose issues:

| Layer | Name | Examples |
|-------|------|----------|
| 7 | Application | HTTP, DNS, SMTP |
| 6 | Presentation | TLS, compression |
| 5 | Session | RPC, NetBIOS |
| 4 | Transport | TCP, UDP |
| 3 | Network | IP, routing |
| 2 | Data Link | Ethernet, WiFi |
| 1 | Physical | Cables, switches |

**Why It Matters**
- Problems at different layers need different solutions
- Understanding the layer helps debug issues
- Network issues often manifest as application problems

### TCP Deep Dive

**Connection Lifecycle**
1. SYN (synchronize)
2. SYN-ACK (synchronize-acknowledge)
3. ACK (acknowledge)
4. Data transfer
5. FIN (finish)
6. ACK
7. FIN
8. ACK

**Key Concepts**
- Three-way handshake
- Flow control
- Congestion control
- Retransmission

**Application Implications**
- Connection setup takes time
- Latency affects throughput
- Packet loss reduces efficiency
- Connection limits matter

### DNS

**How DNS Works**
- Hierarchical lookup
- Caching at multiple levels
- TTL (Time To Live) affects changes
- Multiple record types

**Stability Considerations**
- DNS failures are catastrophic
- Cache invalidation is slow
- TTLs must be balanced
- Multiple DNS servers needed

### Load Balancing

**Types**
- Layer 4 (transport layer)
- Layer 7 (application layer)
- DNS-based
- Client-side

**Considerations**
- Session affinity
- Health checks
- Backend capacity
- SSL termination

## Hardware Fundamentals

### Memory

**Types of Memory**
- RAM (volatile)
- CPU caches (L1, L2, L3)
- Storage (non-volatile)

**Performance Characteristics**
- CPU cache: nanoseconds
- RAM: nanoseconds to microseconds
- SSD: microseconds to milliseconds
- HDD: milliseconds

**Implications for Software**
- Memory access patterns matter
- Caching improves performance
- Memory leaks are serious
- Out-of-memory kills processes

### Storage

**HDD vs SSD**
- HDD: mechanical, seek time
- SSD: electronic, random access
- Both have sequential vs random performance differences
- SSD wear leveling

**Network-Attached Storage**
- NFS, CIFS, cloud storage
- Latency varies
- Throughput limits
- Concurrent access considerations

### CPU

**Key Concepts**
- Clock speed
- Cores and threads
- Cache hierarchy
- Thermal throttling

**Multi-Core Implications**
- Parallelism requires explicit design
- Synchronization overhead
- NUMA (Non-Uniform Memory Access)
- Context switching costs

## The Interconnect

### How Components Connect

**Network Topologies**
- Star
- Mesh
- Tree
- Ring

**Path Components**
- Network interface cards (NICs)
- Switches
- Routers
- Firewalls
- Load balancers

### Latency Numbers Every Developer Should Know

| Operation | Time |
|-----------|------|
| L1 cache reference | 0.5 ns |
| L2 cache reference | 7 ns |
| Main memory access | 100 ns |
| SSD random read | 150 μs |
| Disk seek | 10 ms |
| Network round-trip (same datacenter) | 500 μs |
| Network round-trip (cross-country) | 150 ms |

### Bandwidth Considerations

**Typical Limits**
- 1 Gbps NIC common
- 10 Gbps for high performance
- Storage throughput varies
- Network is often the bottleneck

**Implications**
- Data transfer costs time
- Compression can help
- Batching improves efficiency
- Proximity matters

## Designing for the Foundations

### What Application Developers Should Know

1. **Network is Not Free**
   - Every call has latency
   - Connections have overhead
   - Data size matters

2. **Storage Is Slow**
   - Cache aggressively
   - Batch operations
   - Consider access patterns

3. **Memory Is Finite**
   - Don't load everything
   - Stream large data
   - Monitor usage

4. **Failure Is Possible**
   - Network can fail
   - Storage can fail
   - Hardware can fail

### Common Mistakes

**Ignoring Network**
- Too many round trips
- Unnecessary data transfer
- No connection pooling

**Ignoring Storage**
- Unnecessary disk writes
- No caching
- Poor query patterns

**Ignoring Memory**
- Memory leaks
- Unbounded collections
- Loading too much data

## Actionable Takeaways

1. **Understand Your Stack** - Know what your code runs on
2. **Design for Network Latency** - Minimize round trips, batch operations
3. **Cache Aggressively** - Memory and cache are faster than network/storage
4. **Monitor Infrastructure** - Track CPU, memory, network, storage metrics
5. **Plan for Failure** - Every component can fail

---

*Next: Chapter 7 - Instance Room*
