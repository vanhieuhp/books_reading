# Chapter 12: Serialization

## Overview
Java's built-in serialization mechanism (`ObjectOutputStream`/`ObjectInputStream`) was a controversial feature from the start. This chapter explains why it carries enormous hidden costs — in security, correctness, performance, and maintainability — and what to do instead.

**Core Theme:** Avoid Java serialization in new code. Use cross-platform structured data formats (JSON, Protocol Buffers, Avro) instead. If you must use serialization, understand its hazards deeply and defend against them.

**Why This Matters:** Java deserialization is one of the most exploited attack surfaces in enterprise Java. The 2015–2020 wave of critical vulnerabilities in Apache Commons, Spring, and many other widely-used libraries were all deserialization exploits. This is not theoretical — it is actively exploited in production systems.

---

## Items

### Item 85 — Prefer alternatives to Java serialization
- **Rule:** Do not use Java serialization in new systems; use JSON, Protocol Buffers, or another cross-platform format
- **The fundamental problem:** Deserialization is effectively a remote code execution vector. The `readObject()` method of any class in the classpath can be called with attacker-crafted byte streams
- **Gadget chains:** Sequences of `readObject()` calls that chain through legitimate classes to achieve arbitrary code execution without a custom exploit class
- **Libraries affected:** Apache Commons Collections, Spring Framework, JBoss, WebLogic — all had critical RCE vulnerabilities from deserialization
- **Better alternatives:**
  - **JSON:** Jackson, Gson, JSON-B — human-readable, cross-platform, language-agnostic
  - **Protocol Buffers:** Google's binary format — compact, fast, schema-enforced
  - **Avro:** Apache's schema-based format — excellent for data pipelines
  - **Thrift:** Facebook's cross-language RPC and serialization
- **If you can't avoid it:** Never deserialize untrusted data. Use a deserialization filter (`ObjectInputFilter` — Java 9+) to whitelist allowed classes
- **`ObjectInputFilter`:** Allows you to reject classes that should never appear in a stream; `jdk.serialFilter` system property for JVM-wide filtering

### Item 86 — Implement Serializable with great caution
- **Rule:** Implementing `Serializable` is a major long-term commitment; do it only after careful consideration
- **Three major costs:**
  1. **Decreases flexibility:** The serialized form is part of the API — changing the class can break serialization compatibility
  2. **Increases bug likelihood:** Serialization is a hidden constructor that bypasses all validation logic; invariants can be violated
  3. **Increases security vulnerabilities:** Every serializable class is an attack surface for deserialization exploits
- **High-risk classes:** Classes designed for inheritance should not implement `Serializable` unless the subclasses also need it — but then subclasses are forced to handle serialization
- **Inner classes:** Should not implement `Serializable` — the serialized form depends on the compiler-generated synthetic fields, which are implementation details
- **`serialVersionUID`:** Declare explicitly to avoid `InvalidClassException` on minor class changes; even if you never change the class

### Item 87 — Consider using a custom serialized form
- **Rule:** Before accepting the default serialized form, ask whether it is the best serialized form for your class
- **Default form is appropriate:** Only when the physical representation matches the logical content (simple data classes)
- **Default form is inappropriate when:** Physical representation differs from logical content; private implementation details leak into the serialized form; too much data is serialized
- **The `StringList` example:** A linked list serializes its internal node structure; a custom form should serialize just the number of elements and their strings
- **Custom form advantages:** Smaller serialized size, better performance, ability to refactor internals without breaking the serialized form
- **`writeObject`/`readObject`:** Override to implement custom serialization; always call `defaultWriteObject()` or `defaultReadObject()` first for forward/backward compatibility
- **`transient` keyword:** Mark fields that should not be serialized (derived fields, caches, non-serializable fields); document in Javadoc why each transient field is excluded

### Item 88 — Write readObject methods defensively
- **Rule:** `readObject` is a public constructor that takes a byte stream; it must validate arguments and make defensive copies just like a real constructor
- **The attack:** An attacker crafts a byte stream that provides a `Period` with `end` before `start`; without defensive `readObject`, the invariant is violated
- **Defensive readObject steps:**
  1. `s.defaultReadObject()` — deserialize all fields
  2. Make defensive copies of all mutable fields (before validation!)
  3. Validate all invariants; throw `InvalidObjectException` if violated
- **The mutable component attack:** Even a `final` private mutable field can be compromised if the attacker holds a reference to the object it points to from a different part of the object graph
- **Private constructor + static factory:** If you can design the class this way, serialization via a serialization proxy (Item 90) is safer
- **`InvalidObjectException`:** Throw this from `readObject` when invariants fail — it's the correct exception for deserialization failures

### Item 89 — For instance control, prefer enum types to readResolve
- **Rule:** If you rely on `readResolve` for singleton enforcement, declare ALL fields as `transient`; better yet, use an enum singleton
- **The problem:** A serializable singleton with non-transient fields can be "attacked" through deserialization — the attacker creates a second instance via the stream and `readResolve` doesn't prevent field access
- **`readResolve` mechanics:** Called after deserialization; can return a different object (the cached singleton); the deserialized object is then garbage-collected
- **The `readResolve` attack:** If any field is non-transient, an attacker can hold a reference to it before `readResolve` drops the deserialized instance
- **Enum singleton:** Completely immune to this attack — enum constant deserialization is handled specially by the JVM and never creates a new instance
- **Other instance-controlled classes** (e.g. type-safe enums before Java 5): All must have all fields `transient` if using `readResolve`

### Item 90 — Consider serialization proxies instead of serialized instances
- **Rule:** Use the serialization proxy pattern to serialize and deserialize complex objects safely and with less risk
- **The pattern:**
  1. Inner static class `SerializationProxy` contains all the logical state
  2. `writeReplace()` on the outer class returns a `SerializationProxy` instance instead of itself
  3. `readResolve()` on the proxy reconstructs the original object via the normal constructor
  4. `readObject()` on the outer class throws `InvalidObjectException` (proxy is always used)
- **Benefits:**
  - Uses the normal constructor for deserialization → all validation happens automatically
  - Immune to the mutable component attack (Item 88)
  - Allows the deserialized instance to be of a different class than the serialized one
- **Cost:** ~14% performance overhead per serialization; not suitable for classes that are extendable by clients
- **Best candidate:** Immutable classes that must support serialization

---

## Key Concepts

| Item | Threat Mitigated | Technique |
|---|---|---|
| 85 | RCE via deserialization gadget chains | Use JSON/Protobuf; whitelist with ObjectInputFilter |
| 86 | API coupling, security surface | Implement Serializable only when necessary |
| 87 | Leaked internals, large payloads | Custom writeObject/readObject |
| 88 | Invariant violation via crafted stream | Defensive copies + validation in readObject |
| 89 | Extra singleton instances | Enum singleton |
| 90 | All of the above | Serialization proxy pattern |

---

## Relationships to Other Chapters
- Item 3 (Ch 2): Enum singleton (Item 89) is the same recommendation as Item 3, but now from a serialization-safety perspective
- Item 17 (Ch 4): Immutable objects (Item 17) are the best candidates for serialization proxies (Item 90)
- Item 50 (Ch 8): Defensive copies in `readObject` (Item 88) follow the same principle as Item 50
- Item 70 (Ch 10): `InvalidObjectException` is the correct checked exception for deserialization failures

---

## Agent Prompt

When generating content for this chapter:

1. **Item 85 — The Deserialization Attack Demo** — Create a simplified demonstration of a "gadget chain" attack using only JDK classes. Show how a crafted byte stream could trigger `Runtime.exec()` via a chain of legitimate class `readObject()` methods. Then show how `ObjectInputFilter` blocks it.

2. **Item 88 — Defensive readObject Step-by-Step** — Implement the full `Period` class from the book: first the broken version (no defensive readObject), then the attack byte stream that corrupts it, then the correct defensive implementation that resists the attack.

3. **Item 90 — Complete Serialization Proxy Implementation** — Implement the `Period` class with a full serialization proxy: `writeReplace()`, `SerializationProxy.readResolve()`, and the defensive `readObject()` that throws. Show a before/after with the proxy making the class resilient to all deserialization attacks.

4. **For exercises:**
   - Exercise 1 [Beginner]: Add `serialVersionUID` to an existing class; deliberately break serialization by changing a field and show the error; fix it with a custom form
   - Exercise 2 [Intermediate]: Refactor a class that implements `Serializable` with an `ArrayList` field to use a custom serialized form
   - Exercise 3 [Advanced]: Implement the full serialization proxy pattern for an immutable `Money` class
   - Exercise 4 [Advanced]: Configure `ObjectInputFilter` to whitelist only your application's classes and measure its effectiveness against a crafted stream

5. **For use cases:**
   - Java EE / Jakarta EE: HTTP Session serialization — classes stored in session must be serializable; this is a major attack surface in clustered applications
   - Spring Cache: Serialization for distributed caches (Redis, Hazelcast) — use Jackson instead of Java serialization
   - Kafka: Message serialization — always use Avro or JSON with a schema registry, never Java serialization
   - RMI/Java EE: Deprecated patterns where serialization was required; modern replacements (gRPC, REST) avoid it

6. **For interview questions:** "What security vulnerabilities are associated with Java deserialization?" (security awareness). "What is the serialization proxy pattern and what problem does it solve?" (deep knowledge). The gotcha: "Why is it dangerous to use Java serialization to store user sessions in a distributed application?"

7. **Advice:** Give a direct, strong recommendation: for any new project in 2024+, Java serialization should not be used. Provide a migration checklist for legacy projects: (1) audit all `Serializable` classes, (2) identify deserialization entry points, (3) add `ObjectInputFilter` as an emergency measure, (4) plan migration to JSON/Protobuf. Recommend tools: ysoserial for testing your deserialization defenses, Serial Killer (IntelliJ plugin) for auditing.
