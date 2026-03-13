## Part I: Stability

This section focuses on the "physics" of failure—how one small crack becomes a total collapse.

* **Chapter 1: Living in Production** – The reality check. Why code that passes QA still fails in the real world.
* **Chapter 2: Case Study: The Exception That Chain-Reacted** – A post-mortem of a real-world disaster involving a single blocked thread.
* **Chapter 3: Stability Anti-Patterns** – The "villains" of software.
* *Examples:* Impatience, Resource Exhaustion, Cascading Failures.


* **Chapter 4: Stability Patterns** – The "heroes" of software.
* *Examples:* Circuit Breakers, Bulkheads, Timeouts, Handshaking.



---

## Part II: Design for Production

Here, the focus shifts to the architectural decisions made during the "Create" phase of a project.

* **Chapter 5: Case Study: The Un-virtualized Ground** – Exploring how physical hardware and virtualization layers impact software stability.
* **Chapter 6: Foundations** – Networking, physical hardware, and the "Interconnect."
* **Chapter 7: Instance Room** – How to handle your application's lifecycle, from startup to shutdown.
* **Chapter 8: Interconnect** – Managing the messy reality of DNS, Load Balancers, and Firewalls.
* **Chapter 9: Control Plane** – How to manage your fleet of services at scale.

---

## Part III: Operations

This section treats "Operations" not as a separate department, but as a core requirement of the code itself.

* **Chapter 10: Case Study: The Eight-Minute Hour** – A look at how a system's performance profile changes under sudden, massive stress.
* **Chapter 11: Transparency** – Logging, monitoring, and metrics. If you can't see it, you can't fix it.
* **Chapter 12: Adaptation** – How systems change over time and how to handle versioning and deployments.
* **Chapter 13: Chaos Engineering** – Proactively breaking your own system to find weaknesses before the users do.

---

## Part IV: The Systemic Perspective

The final chapters look at the bigger picture: the organization and the future.

* **Chapter 14: Case Study: The Trampled Product Launch** – Analysis of a high-profile failure and the organizational pressure that caused it.
* **Chapter 15: Adaptation** – How to evolve the architecture as the business grows.
* **Chapter 16: The Systemic View** – Recognizing that the software, the hardware, and the humans are all one giant, interconnected system.

