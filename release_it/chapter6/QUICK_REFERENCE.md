# Chapter 6: Foundations - Quick Reference

## 📊 Latency Numbers Every Developer Should Know

| Operation | Time | Relative to RAM |
|-----------|------|-----------------|
| L1 cache reference | 0.5 ns | 1x (baseline) |
| L2 cache reference | 7 ns | 14x |
| Main memory access | 100 ns | 200x |
| SSD random read | 150 μs | 3,000x |
| Disk seek | 10 ms | 200,000x |
| Network RTT (same DC) | 500 μs | 10,000x |
| Network RTT (cross-country) | 150 ms | 3,000,000x |

## 🌍 OSI Model Layers

| Layer | Name | Protocol Examples |
|-------|------|-------------------|
| 7 | Application | HTTP, DNS, SMTP |
| 6 | Presentation | TLS, compression |
| 5 | Session | RPC, NetBIOS |
| 4 | Transport | TCP, UDP |
| 3 | Network | IP, routing |
| 2 | Data Link | Ethernet, WiFi |
| 1 | Physical | Cables, switches |

## 🔄 TCP Three-Way Handshake

```
Client                    Server
   |                         |
   |-------- SYN ----------->|
   |                         |
   |<----- SYN-ACK ---------|
   |                         |
   |-------- ACK ----------->|
   |                         |
   |------ DATA ------------| (Connection established)
```

**Total overhead**: ~1.5 RTT before data transfer

## 🔌 Connection Pool Configuration

### HTTP Client (Go)
```go
&http.Transport{
    MaxIdleConns:        100,        // Total idle connections
    MaxIdleConnsPerHost: 50,         // Per-destination limit
    IdleConnTimeout:      90 * time.Second,
    ResponseHeaderTimeout: 5 * time.Second,
}
```

### Database Pool (PostgreSQL/pgx)
```go
config.MinConns = 10       // Minimum pool size
config.MaxConns = 50       // Maximum pool size
config.MaxConnLifetime = time.Hour
config.MaxConnWaitTime = 5 * time.Second
```

## 💾 Storage Comparison

| Type | Random Access | Sequential | Use Case |
|------|---------------|------------|----------|
| HDD | ~10 ms | ~100 MB/s | Cold storage, large files |
| SSD | ~150 μs | ~500 MB/s | Primary storage |
| NVMe | ~30 μs | ~3 GB/s | High-performance |

## 🏗️ Design Principles

### 1. Network is Not Free
- [ ] Minimize round trips
- [ ] Batch operations
- [ ] Use connection pooling
- [ ] Consider gRPC for internal services

### 2. Storage Is Slow
- [ ] Cache aggressively
- [ ] Batch writes
- [ ] Consider access patterns
- [ ] Use appropriate storage type

### 3. Memory Is Finite
- [ ] Don't load everything
- [ ] Stream large data
- [ ] Monitor usage
- [ ] Set appropriate limits

### 4. Failure Is Possible
- [ ] Handle network failures
- [ ] Handle storage failures
- [ ] Plan for hardware failures
- [ ] Implement circuit breakers

## 🛠️ Common Mistakes to Avoid

| Mistake | Consequence | Solution |
|---------|-------------|----------|
| No connection pooling | Connection exhaustion | Configure pool limits |
| Loading large files | OOM kill | Stream processing |
| No timeouts | Resource exhaustion | Set timeouts |
| Ignoring network latency | Slow user experience | Cache, batch, prefetch |
| Single point of failure | System-wide outage | Redundancy, failover |

## 🔍 Debugging Checklist

When investigating performance issues:

1. [ ] **Network**: Check RTT, packet loss, bandwidth
2. [ ] **Database**: Check connection pool, query performance, I/O wait
3. [ ] **Memory**: Check usage, GC pressure, allocation rate
4. [ ] **CPU**: Check utilization, context switching
5. [ ] **Storage**: Check I/O wait, queue depth, capacity

## 📈 Monitoring Metrics

| Category | Key Metrics |
|----------|-------------|
| Network | RTT, bandwidth, packet loss, connection errors |
| Memory | RSS, heap alloc, GC pause time |
| Storage | I/O wait, queue depth, capacity |
| TCP | Connection setup time, connection errors, timeouts |

---

*Quick Reference Card - Release It! Chapter 6*
