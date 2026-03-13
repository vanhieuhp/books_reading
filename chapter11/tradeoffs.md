# 📘 Chapter 11: Transparency — Trade-offs & When NOT to Use This

One hallmark of a staff engineer is knowing when **not** to apply a pattern. This section covers the trade-offs Chapter 11 doesn't explicitly discuss.

---

## Structured Logging Trade-offs

### Use This When:
- You have multiple services that need to be correlated
- Log volume exceeds 10GB/day (text search becomes impractical)
- You need to alert on log patterns (e.g., error rate from logs)
- Compliance requires structured audit trails

### Avoid This When:
- Single monolithic application with simple debugging needs
- Log volume is low (< 1GB/day) and grep suffices
- You're in early exploration phase and moving fast
- Team doesn't have tooling to parse JSON logs

### Hidden Costs:
| Cost | Impact |
|------|--------|
| **Parsing overhead** | JSON parsing ~5-10% CPU overhead vs text |
| **Tooling investment** | Need Kibana/Datadog to make JSON useful |
| **Schema evolution** | Adding fields requires coordination |
| **Storage** | JSON is more verbose than text (~30% larger) |

### Staff-Level Insight:
> At small scale, text logs with grep work fine. The break-even point is typically around 10 services or 10GB/day. Before that, structured logging adds complexity without much benefit.

---

## Distributed Tracing Trade-offs

### Use This When:
- Request flows through 5+ services
- You have chronic "slow requests" that you can't reproduce
- Cross-service latency is a user complaint
- You need to identify which dependency is slow

### Avoid This When:
- Simple request-response (2-3 services)
- You're already doing well with correlation IDs in logs
- Adding tracing would delay shipping the feature
- Your team is < 3 people and moving fast

### Hidden Costs:
| Cost | Impact |
|------|--------|
| **Performance overhead** | 2-5% latency increase from tracing |
| **Storage** | Traces are large (KB per trace) |
| **Instrumentation effort** | Every service needs updates |
| **Tooling** | Jaeger/Zipkin UI, training |

### Staff-Level Insight:
> Don't implement distributed tracing just because "everyone does it." If you can debug issues with correlation IDs and logs, tracing is premature optimization. The complexity multiplies with service count.

---

## RED Method Trade-offs

### Use This When:
- You have multiple services with different SLAs
- You need to identify which service is causing issues
- Capacity planning is important
- You want to set meaningful SLOs

### Avoid This When:
- Single service, simple application
- You're in rapid prototyping phase
- You don't have Prometheus/Datadog set up yet
- Your team is small and can debug via logs

### Hidden Costs:
| Cost | Impact |
|------|--------|
| **Metric cardinality** | Too many labels = Prometheus memory explosion |
| **Query complexity** | PromQL is powerful but has learning curve |
| **Dashboard maintenance** | Dashboards rot; need ongoing care |
| **Alert tuning** | Thresholds require ongoing adjustment |

### Staff-Level Insight:
> Start with 3-5 key metrics, not 50. You can always add more granularity, but removing metrics is harder. Focus on what you'd alert on today, not what might be useful someday.

---

## USE Method Trade-offs

### Use This When:
- Resource exhaustion is a common failure mode
- You need to justify infrastructure costs
- You're running on fixed-capacity infrastructure
- You want to predict when you'll hit limits

### Avoid This When:
- Cloud environment with auto-scaling
- Resources are effectively infinite (e.g., managed DB with auto-scale)
- You're not seeing resource-related incidents

### Hidden Costs:
| Cost | Impact |
|------|--------|
| **Metric collection** | Need node_exporter, cloudwatch exporter |
| **Interpretation** | "High CPU" doesn't always mean "problem" |
| **False confidence** | Low utilization doesn't mean performance is good |

### Staff-Level Insight:
> USE is most valuable for infrastructure you control. In cloud environments with auto-scaling, USE metrics tell you about cost, not just capacity. The real question: "Are we wasting money?"

---

## Health Check Trade-offs

### Use This When:
- Running on Kubernetes (required)
- You want zero-downtime deployments
- Dependencies can fail independently
- You need graceful degradation

### Avoid This When:
- Single instance deployment
- Health check would essentially duplicate other monitoring
- External dependencies are not critical

### Hidden Costs:
| Cost | Impact |
|------|--------|
| **Check complexity** | Too many checks = slow probes = timeouts |
| **Death spirals** | Liveness checks dependencies = cascade restarts |
| **Kubernetes coupling** | Hard to run outside K8s |

### Staff-Level Insight:
> The most common mistake: making liveness checks too complex. Liveness should be: "is my process running?" That's it. Everything else is readiness.

---

## Actionable Alerting Trade-offs

### Use This When:
- You have 24/7 on-call (or want to protect it)
- Alert noise is causing fatigue
- You have SLOs to protect
- Incidents are too frequent

### Avoid This When:
- Early stage, low traffic
- Team is small and can tolerate noise
- You're still learning what "normal" looks like

### Hidden Costs:
| Cost | Impact |
|------|--------|
| **Initial silence** | Fewer alerts feels like "nothing is happening" |
| **Tuning effort** | Thresholds need continuous refinement |
| **Runbook maintenance** | Runbooks must stay current with code |

### Staff-Level Insight:
> The goal isn't zero alerts—it's zero *unactionable* alerts. A well-tuned alert system might actually have *more* alerts during an incident because each alert triggers immediate action.

---

## Summary: Decision Matrix

| Scenario | What to Implement | What to Skip |
|----------|------------------|---------------|
| 2-3 services, low traffic | Structured logging | Tracing, complex metrics |
| 5-10 services | RED metrics, correlation IDs | Full tracing initially |
| 10+ services, 24/7 ops | Full observability stack | None—it's essential |
| Kubernetes deployment | Health checks | Skipping health checks |
| On-call team burning out | Alerting overhaul | None—critical |

---

## The Bottom Line

**Start simple, add complexity as needed:**

1. **Phase 1**: Structured logging + correlation IDs (minimum viable)
2. **Phase 2**: RED metrics per service (when you have multiple services)
3. **Phase 3**: Distributed tracing (when debugging is painful)
4. **Phase 4**: Fine-tuned alerting (when you have SLOs)

Don't build Phase 3 infrastructure when Phase 1 solves your problems. But when you need it, invest fully—partial observability is worse than none.
