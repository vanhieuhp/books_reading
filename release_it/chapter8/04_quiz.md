# Chapter 8: Interconnect — Quiz

## Quiz 1: DNS Fundamentals

**Question 1**: What is the primary risk of using a single DNS provider?
- A) Slower resolution times
- B) Complete service outage when provider fails
- C) Security vulnerabilities
- D) Higher costs

**Question 2**: A 30-day TTL on DNS records means:
- A) Records change every 30 days
- B) Resolvers cache records for 30 days
- C) DNS provider updates every 30 days
- D) Certificate validity period

**Question 3**: Which is NOT a DNS best practice?
- A) Use multiple DNS providers
- B) Set appropriate TTLs
- C) Use highest possible TTL for stability
- D) Monitor DNS resolution time

---

## Quiz 2: Load Balancers

**Question 4**: Layer 7 load balancing operates at which OSI layer?
- A) Network layer
- B) Transport layer
- C) Application layer
- D) Data link layer

**Question 5**: Which load balancing algorithm is best for ensuring a user always reaches the same server?
- A) Round Robin
- B) Least Connections
- C) IP Hash
- D) Weighted

**Question 6**: Why can health checks be dangerous?
- A) They consume too much bandwidth
- B) Poorly designed checks can cause flapping or miss real failures
- C) They require HTTPS
- D) They slow down the load balancer

---

## Quiz 3: Circuit Breakers

**Question 7**: In a circuit breaker, what happens when the circuit is "OPEN"?
- A) Requests are routed to all servers
- B) Requests fail immediately without calling the service
- C) Requests are queued for later
- D) Health checks are disabled

**Question 8**: What is the purpose of the "HALF-OPEN" state?
- A) Complete failure of the service
- B) Testing if the service has recovered
- C) Normal operation with monitoring
- D) Maintenance mode

**Question 9**: A circuit breaker should have:
- A) Only a failure threshold
- B) Only a timeout
- C) Both failure threshold AND timeout
- D) Neither

---

## Quiz 4: Connection Management

**Question 10**: Connection pool exhaustion typically causes:
- A) Faster response times
- B) Requests to hang or fail
- C) Reduced memory usage
- D) Lower CPU usage

**Question 11**: Which is NOT a critical timeout for network calls?
- A) Connection timeout
- B) Read timeout
- C) DNS timeout
- D) Total timeout

**Question 12**: What's the relationship between pool size and throughput?
- A) Larger pool always means higher throughput
- B) Smaller pool always means higher throughput
- C) There's an optimal size based on backend capacity
- D) Pool size doesn't affect throughput

---

## Quiz 5: Firewalls & Segmentation

**Question 13**: A "fail-open" firewall:
- A) Blocks all traffic on error
- B) Allows all traffic on error
- C) Logs all traffic on error
- D) Encrypts all traffic on error

**Question 14**: Network segmentation primarily helps with:
- A) Increasing bandwidth
- B) Limiting blast radius of failures
- C) Reducing DNS lookups
- D) Improving search rankings

---

## Quiz 6: Modern Patterns

**Question 15**: A service mesh provides:
- A) DNS resolution
- B) Automatic mTLS between services
- C) Load balancing only
- D) Single sign-on

**Question 16**: When should you use CDN?
- A) For real-time data
- B) For dynamic content that changes constantly
- C) For static assets with global users
- D) For database queries

---

## Quiz 7: Staff-Level Synthesis

**Question 17**: At a large scale (millions of users), why does DNS become even more critical?
- A) DNS lookups are free
- B) Single failures affect millions instantly
- C) DNS providers give discounts
- D) DNS is faster than load balancers

**Question 18**: Why should circuit breakers be placed at every network boundary?
- A) They're required by compliance
- B) Every boundary can fail independently
- C) They're easy to implement
- D) Management requires them

---

## Answer Key

| Question | Answer | Explanation |
|----------|--------|-------------|
| 1 | B | Single provider = single point of failure |
| 2 | B | TTL = Time To Live = cache duration |
| 3 | C | High TTL prevents quick changes; appropriate TTL matters |
| 4 | C | L7 = Application layer |
| 5 | C | IP Hash provides consistent hashing for session affinity |
| 6 | B | Bad health checks cause false positives or miss failures |
| 7 | B | Open = fail fast, don't call service |
| 8 | B | Half-open = testing recovery |
| 9 | C | Both threshold AND timeout needed |
| 10 | B | No available connections = requests hang/fail |
| 11 | C | DNS timeout is important but not one of the 4 critical ones |
| 12 | C | Optimal size based on backend capacity |
| 13 | B | Fail-open = allow on error (security risk) |
| 14 | B | Segmentation limits blast radius |
| 15 | B | Service mesh provides automatic mTLS |
| 16 | C | CDN for static assets |
| 17 | B | At scale, DNS failure = mass outage |
| 18 | B | Every boundary can fail independently |

---

*Quiz generated for Release It! Chapter 8 - Interconnect*
