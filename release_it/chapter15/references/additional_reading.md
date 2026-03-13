# Additional Reading: Architecture Evolution

## Release It! by Michael Nygard

---

## Primary References

### Martin Fowler's Patterns

1. **Strangler Fig Application**
   - URL: https://martinfowler.com/bliki/StranglerFigApplication.html
   - Summary: Detailed explanation of the Strangler pattern

2. **Branch by Abstraction**
   - URL: https://martinfowler.com/bliki/BranchByAbstraction.html
   - Summary: Pattern for making large-scale changes without branching

3. **Microservice Premium**
   - URL: https://martinfowler.com/bliki/MicroservicePremium.html
   - Summary: When microservices are worth the additional complexity

### Conway's Law

1. **Original Paper**
   - URL: https://www.martinpower.com/wp-content/uploads/2020/03/Conway-ConwaysLaw1967.pdf
   - Summary: Melvin Conway's original 1967 paper

2. **Conway's Law in Practice**
   - URL: https://www.martinfowler.com/articles/branching-patterns.html
   - Summary: How team structure affects code structure

---

## Case Studies

### Netflix

1. **Evolution of Netflix API**
   - URL: https://netflixtechblog.com/evolution-of-the-netflix-api-bb9ae9cf292c
   - Summary: From monolith to API gateway

2. **Microservices at Netflix**
   - URL: https://netflixtechblog.com/finding-microservices-at-netflix-scale-71e5ef32c1e2
   - Summary: Scaling challenges and solutions

### Amazon

1. **Working Backwards**
   - URL: https://www.allthingsdistributed.com/2022/06/working-backwards.html
   - Summary: Amazon's approach to building and shipping

### Uber

1. **Uber's Migration to Microservices**
   - URL: https://eng.uber.com/microservices-legacy-refactor/
   - Summary: Practical lessons from a real migration

---

## Books

1. **Building Microservices** by Sam Newman
   - ISBN: 978-1492034018
   - Summary: Comprehensive guide to microservices

2. **Fundamentals of Software Architecture** by Mark Richards
   - ISBN: 978-1492043454
   - Summary: Architecture patterns and decision frameworks

3. **Team Topologies** by Matthew Skelton
   - ISBN: 978-1942788817
   - Summary: Team structure and Conway's Law

4. **Site Reliability Engineering**
   - URL: https://sre.google/sre-book/table-of-contents/
   - Summary: Google's approach to production systems

---

## Tools & Platforms

### Service Discovery

1. **Eureka** (Netflix)
   - URL: https://github.com/Netflix/eureka
   - Summary: Service registry for AWS

2. **Consul** (HashiCorp)
   - URL: https://www.consul.io/
   - Summary: Service networking

### Resilience

1. **Hystrix** (Netflix)
   - URL: https://github.com/Netflix/Hystrix
   - Summary: Circuit breaker pattern

2. **Resilience4j**
   - URL: https://resilience4j.readme.io/
   - Summary: Java resilience patterns

### Observability

1. **Jaeger**
   - URL: https://www.jaegertracing.io/
   - Summary: Distributed tracing

2. **Prometheus**
   - URL: https://prometheus.io/
   - Summary: Monitoring and alerting

---

## Videos & Talks

1. **Simon Brown: Software Architecture for Developers**
   - URL: https://www.youtube.com/watch?v=G1L2pQ9lM5Y
   - Summary: Architecture as code

2. **Building Evolutionary Architectures**
   - URL: https://www.youtube.com/watch?v=0G3Ew\nh2O5c
   - Summary:Neal Ford's talks on evolutionary architecture

---

## Key Concepts Summary

### When to Use Microservices
- Team size > 15-20
- Clear independent modules
- Different scaling requirements
- Different deployment cadences

### When NOT to Use Microservices
- Small team (< 10)
- Domain still evolving
- Tightly coupled modules
- Limited operational experience

### Migration Strategies
1. **Strangler**: New system beside old, migrate feature by feature
2. **Branch by Abstraction**: Abstract, implement new, switch
3. **Parallel Run**: Both systems, verify, switch
4. **Feature Flags**: Toggle between implementations

---

*References generated for Release It! Chapter 15: Adaptation (Architecture Evolution)*
