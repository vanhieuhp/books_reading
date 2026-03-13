# Chapter 9: Control Plane — Quick Reference

## 📌 Key Concepts

### Control Plane vs Data Plane

| Aspect | Control Plane | Data Plane |
|--------|---------------|------------|
| Purpose | Manage how work gets handled | Handle actual user traffic |
| Examples | Service discovery, config, deployment | API servers, databases |
| Scale | Few instances, high reliability | Many instances, scales horizontally |
| Failure impact | System-wide | Single service |

---

## Service Discovery

### Client-Side Discovery
```
Client → Service Registry → Get Address → Call Service
```
- Client queries registry directly
- Client chooses instance (load balancing)
- Examples: Eureka, Consul (client SDK)

### Server-Side Discovery
```
Client → Load Balancer → Registry → Service
```
- Client contacts load balancer
- Balancer queries registry
- Balancer routes request
- Examples: AWS ELB, Kubernetes Ingress

### Health Check Types

| Type | Purpose | Examples |
|------|---------|----------|
| Liveness | Is process alive? | Ping, /health |
| Readiness | Ready for traffic? | Dependencies available |
| Business | Functioning correctly | Custom checks |

---

## Configuration Management

### Patterns Comparison

| Pattern | Pros | Cons |
|---------|------|------|
| Environment Variables | Simple, built-in | Limited structure, secrets risk |
| Configuration Files | Structured, versionable | Manual distribution |
| External Services | Centralized, dynamic | Additional dependency |

### Best Practices

1. **Separate config from code** — Same code, different configs
2. **Never commit secrets** — Use secrets management
3. **Validate at startup** — Schema validation, required fields
4. **Version configuration** — Rollback capability, audit trail

---

## Deployment Strategies

### Blue-Green

```
Blue: v1 (active) → Switch traffic → Blue: v1 (standby)
Green: v2 (standby)                  Green: v2 (active)
```

- ✅ Zero downtime
- ✅ Instant rollback
- ❌ Double resource cost

### Rolling

```
v1 → v1,v2 → v2,v3 → v3
```

- ✅ No extra resources
- ❌ Slower rollback
- ❌ Partial downtime during update

### Canary

```
99% v1 → 50% v1/50% v2 → 1% v1/99% v2 → 100% v2
```

- ✅ Gradual exposure
- ✅ Real traffic testing
- ✅ Fast rollback
- ❌ Requires good metrics

---

## Feature Flags

### Use Cases

- Kill switches (instant disable)
- A/B testing
- Gradual rollout
- Beta testing

### Flag States

- **OFF** — Feature disabled
- **ON** — Feature enabled for all
- **CONDITIONAL** — Based on user attributes
- **ROLLOUT** — Percentage-based

---

## Traffic Management

### Circuit Breaker States

```
CLOSED → (failure threshold) → OPEN → (timeout) → HALF-OPEN → (success) → CLOSED
         ↑_______________________________________|
```

| State | Behavior |
|-------|----------|
| Closed | Normal operation, requests allowed |
| Open | Requests blocked, fail fast |
| Half-Open | Test requests allowed |

---

## Control Plane Patterns

### Leader Election
- Database-based
- ZooKeeper, etcd, Consul

### Distributed Locking
- Prevent concurrent modifications
- Use cases: migrations, deployment coordination

### Event-Driven
- Services emit events
- Control plane subscribes
- Reactive updates

---

## Tools by Category

### Service Discovery
- etcd
- Consul
- Eureka
- ZooKeeper

### Configuration
- Spring Cloud Config
- Consul
- etcd
- AWS Parameter Store

### Deployment
- Spinnaker
- Argo CD
- Jenkins X
- GitOps tools

### Traffic
- Envoy
- Istio
- Linkerd
- Nginx

---

## Common Pitfalls

### Service Discovery
1. Single point of failure
2. No health checks
3. Caching too aggressively
4. Not handling churn

### Configuration
1. Secrets in code
2. No validation
3. No versioning
4. Configuration drift

### Deployment
1. No rollback
2. Long deployments
3. No canarying
4. Manual steps

### Traffic Management
1. No circuit breaking
2. No rate limiting
3. Poor health checks
4. Single point

---

## Actionable Takeaways

1. **Invest in Service Discovery** — Make it reliable and fast
2. **Externalize Configuration** — Separate from code
3. **Automate Deployments** — Remove manual steps
4. **Implement Feature Flags** — Enable gradual rollout
5. **Design for Failure** — Control plane can fail
6. **Monitor Everything** — You can't fix what you can't see

---

*Quick reference generated from Book Deep Learner - Release It! Chapter 9*
