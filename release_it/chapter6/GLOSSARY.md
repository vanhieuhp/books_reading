# Chapter 6: Foundations - Glossary of Key Terms

## Networking

### DNS (Domain Name System)
- **What**: Hierarchical naming system that translates domain names to IP addresses
- **Why it matters**: DNS failures are catastrophic; cache invalidation is slow
- **Key concept**: TTL (Time To Live) controls cache duration

### TCP (Transmission Control Protocol)
- **What**: Connection-oriented transport protocol providing reliable, ordered delivery
- **Key concept**: Three-way handshake (SYN → SYN-ACK → ACK) establishes connection
- **Why it matters**: Connection setup takes time; understanding this helps with pooling

### UDP (User Datagram Protocol)
- **What**: Connectionless protocol without delivery guarantees
- **Why it matters**: Lower latency than TCP; used for DNS, streaming, gaming

### Load Balancer
- **What**: Distributes traffic across multiple servers
- **Types**:
  - Layer 4 (transport): Routes based on IP/port
  - Layer 7 (application): Routes based on HTTP content
- **Why it matters**: Critical for scalability and reliability

### OSI Model
- **What**: 7-layer network model (Physical → Application)
- **Why it matters**: Problems at different layers need different solutions

## Hardware

### NUMA (Non-Uniform Memory Access)
- **What**: Memory architecture where access time depends on memory location
- **Why it matters**: Affects performance in multi-socket systems

### SSD vs HDD
- **SSD**: Solid-state; no moving parts; fast random access (~150 μs)
- **HDD**: Mechanical; seek time (~10 ms)
- **Why it matters**: Storage choice affects application performance

### CPU Cache (L1, L2, L3)
- **What**: On-CPU memory with different sizes and speeds
- **L1**: Fastest (~0.5 ns), smallest (~32 KB)
- **L2**: Slower (~7 ns), larger (~256 KB)
- **L3**: Slowest (~30 ns), largest (~8 MB)
- **Why it matters**: Cache misses are expensive

## Performance

### Latency vs Throughput
- **Latency**: Time for single operation (ms)
- **Throughput**: Operations per time (ops/sec)
- **Why it matters**: Optimizing one may hurt the other

### Connection Pooling
- **What**: Reusing connections instead of creating new ones
- **Why it matters**: Avoids TCP handshake overhead
- **Key metrics**: Max connections, idle timeout, wait time

### Circuit Breaker
- **What**: Pattern that "trips" when failures exceed threshold
- **Why it matters**: Prevents cascade failures

---

## Quick Reference

| Term | One-Line Definition |
|------|---------------------|
| DNS | Translates names to IPs |
| TCP | Reliable connection protocol |
| OSI Model | 7-layer network model |
| Load Balancer | Distributes traffic |
| SSD | Fast solid-state storage |
| HDD | Slow mechanical storage |
| L1/L2/L3 Cache | CPU on-chip memory |
| NUMA | Non-uniform memory access |
| Latency | Time per operation |
| Throughput | Operations per second |
| Connection Pool | Reuses connections |
| Circuit Breaker | Fails fast on errors |

---

*Glossary - Release It! Chapter 6: Foundations*
