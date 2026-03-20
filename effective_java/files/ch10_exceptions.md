# Chapter 10: Exceptions

## Overview
Exceptions are Java's mechanism for communicating abnormal conditions from a method to its caller. Used correctly, they improve readability, correctness, and maintainability. Used incorrectly — for control flow, silently swallowed, or improperly chosen — they become a source of dangerous, hard-to-diagnose bugs.

**Core Theme:** Exceptions are for exceptional conditions. Choose the right type (checked vs unchecked). Include all relevant failure information. Never hide exceptions. Ensure failure leaves the object in a valid state.

**Why This Matters:** Swallowed exceptions and poorly designed exception hierarchies are among the most dangerous patterns in production Java code. An empty `catch` block is a ticking time bomb.

---

## Items

### Item 69 — Use exceptions only for exceptional conditions
- **Rule:** Never use exceptions for ordinary control flow; they are for truly exceptional conditions
- **The array loop antipattern:** Using `ArrayIndexOutOfBoundsException` to terminate a loop — hard to understand, slower, hides real bugs
- **Well-designed APIs:** Should not force clients to use exceptions for control flow; provide state-testing methods (`hasNext()` before `next()`) or return optionals
- **State-testing vs Optional:** If there's a concurrent modification risk between test and act, use Optional or a special return value; otherwise state-testing (`hasNext()`) is fine
- **Performance note:** Exceptions are designed for exceptional cases; JVM does not optimize exception-path code

### Item 70 — Use checked exceptions for recoverable conditions, runtime exceptions for programming errors
- **Rule:** Three categories of throwables — each with a purpose:
  1. **Checked exceptions:** Conditions from which the caller can reasonably recover (`IOException`, `SQLException`); caller is forced to handle
  2. **Runtime exceptions (`RuntimeException`):** Programming errors — precondition violations, bugs (`NullPointerException`, `IllegalArgumentException`, `ArrayIndexOutOfBoundsException`)
  3. **Errors:** Reserved for JVM-level conditions (`OutOfMemoryError`, `StackOverflowError`); never throw or catch `Error` in application code
- **Decision rule:** "Can the caller reasonably recover from this?" → Yes: checked. No: unchecked.
- **Trend:** Modern Java libraries (and many senior developers) prefer unchecked exceptions because checked exceptions create API coupling and are often swallowed

### Item 71 — Avoid unnecessary use of checked exceptions
- **Rule:** Use checked exceptions only when both conditions are met: (1) the exception cannot be prevented by proper API use, and (2) the programmer can take useful action when it occurs
- **The burden of checked exceptions:** Every checked exception is another `throws` clause, another catch block, forces streams/lambdas to wrap it
- **Alternatives to checked exceptions:**
  1. Return `Optional<T>` instead of throwing
  2. Provide a state-testing method: `actionPermitted()` + `action()` instead of one `action()` that throws
- **When checked is justified:** `IOException` for I/O operations — callers genuinely need to handle file-not-found, permission-denied, etc.

### Item 72 — Favor the use of standard exceptions
- **Rule:** Reuse standard Java exceptions rather than creating new ones for common cases
- **Most important standard exceptions:**
  - `IllegalArgumentException` — wrong parameter value
  - `IllegalStateException` — object state is invalid for the operation
  - `NullPointerException` — null where non-null required
  - `IndexOutOfBoundsException` — index out of range
  - `ConcurrentModificationException` — concurrent modification detected
  - `UnsupportedOperationException` — operation not supported
- **Choosing between `IllegalArgumentException` and `IllegalStateException`:** If the call would be valid for some other object state, prefer `IllegalStateException`; otherwise `IllegalArgumentException`
- **Don't reuse:** `Exception`, `RuntimeException`, `Throwable`, `Error` directly — too broad, uninformative

### Item 73 — Throw exceptions appropriate to the abstraction
- **Rule:** Higher-level layers should catch lower-level exceptions and translate them to exceptions meaningful at the higher abstraction level
- **Exception translation:** Catch low-level exception, throw high-level exception
- **Exception chaining:** Pass the original exception as the cause: `throw new HighLevelException(e)` — preserves full stack trace
- **Use sparingly:** Exception translation adds complexity; the best solution is to prevent the lower-level exception entirely
- **Don't overuse:** Indiscriminate exception translation can hide programming errors that should propagate

### Item 74 — Document all exceptions thrown by each method
- **Rule:** Always declare checked exceptions with `@throws` tag in Javadoc; always document unchecked exceptions too
- **For each exception document:** The condition under which it is thrown
- **Javadoc `@throws`:** Use for both checked (also in `throws` clause) and unchecked (Javadoc only — no `throws` clause for unchecked)
- **Class-level invariants:** Document if the class throws an exception on any method when in a certain state
- **Never:** `@throws Exception` or `@throws RuntimeException` — too vague, uninformative

### Item 75 — Include failure-capture information in detail messages
- **Rule:** Exception messages must contain all parameter and field values that contributed to the exception
- **Why:** When debugging from a stack trace in production, the message is often all you have
- **`IndexOutOfBoundsException` example:** "Index: 10, Size: 5" — not just "array index out of bounds"
- **What to include:** All illegal argument values, all relevant state values at the time of failure
- **What NOT to include:** User-readable prose, sensitive information (passwords, PII) — logs are often less secure
- **Modern approach:** Add a constructor that takes typed parameters and formats the message: `new IndexOutOfBoundsException(index, size)`

### Item 76 — Strive for failure atomicity
- **Rule:** A failed method invocation should leave the object in the state it was in prior to the invocation
- **Why:** Violated atomicity creates partially mutated objects that are difficult or impossible to use safely
- **Four techniques:**
  1. Use immutable objects (failure atomicity is free — no state to corrupt)
  2. Check parameters before mutating state (validate upfront, mutate only if valid)
  3. Perform operations on a temporary copy, then swap atomically
  4. Recovery code (rare) — write rollback code to undo partial changes on failure
- **When it's hard:** Some operations (two-thread exceptions, network) can't be made atomic without major complexity; document that failure may leave the object in an inconsistent state

### Item 77 — Don't ignore exceptions
- **Rule:** Never write an empty catch block; at minimum log the exception; ideally handle it or propagate it
- **The empty catch antipattern:** `catch (Exception e) {}` — silently swallows the error, makes debugging impossible
- **If you truly must ignore it:** Add a comment explaining why it's safe to ignore, name the exception variable `ignored`
- **Logging minimum:** `logger.log(Level.WARNING, "Unexpected exception", e)` — at least you know it happened
- **When catching broadly:** `catch (Exception e)` — acceptable in top-level handlers and framework boundaries, but always log with the full stack trace

---

## Key Concepts

| Exception Type | Use Case | Example |
|---|---|---|
| Checked | Recoverable external failure | `IOException`, `SQLException` |
| RuntimeException | Programming error / precondition | `IllegalArgumentException`, `NPE` |
| Error | JVM/system failure | `OutOfMemoryError` |
| Custom exception | Domain-specific recoverable failure | `InsufficientFundsException` |

| Technique | Item | Pattern |
|---|---|---|
| Fail fast | 69, 49 | Check upfront, throw early |
| Exception translation | 73 | Catch low, throw high |
| Failure atomicity | 76 | Validate before mutate |
| Never swallow | 77 | Always log at minimum |

---

## Relationships to Other Chapters
- Item 49 (Ch 8): Parameter validation (fail fast) directly prevents the need for some exceptions
- Item 17 (Ch 4): Immutability makes failure atomicity (Item 76) essentially free
- Item 45 (Ch 7): Checked exceptions in lambdas/streams force wrapping — strongly incentivizes unchecked exceptions (Item 71)
- Item 9 (Ch 2): `try-with-resources` is the correct implementation of `AutoCloseable`

---

## Agent Prompt

When generating content for this chapter:

1. **Item 70 — Checked vs Unchecked Decision Flowchart** — Generate a flowchart: "Should I throw a checked exception?" Start with: "Is this a programming error?" → Yes → RuntimeException. "Can the caller realistically recover?" → No → RuntimeException. "Is recovery requiring meaningful action?" → No → consider Optional. → Yes → checked.

2. **Item 77 — The Swallowed Exception Crime Scene** — Create a realistic scenario: a file-based configuration loader swallows an `IOException` in a catch block. Show how this manifests 10 lines later as a `NullPointerException` with no trace back to the root cause. Show the fix.

3. **Item 75 — Exception Message Template** — Provide a template for good exception messages and 5 before/after examples: "Error" → "Cannot transfer $500.00 from Account#12345 (balance: $200.00)".

4. **For exercises:**
   - Exercise 1 [Beginner]: Find and fix 3 antipatterns: exception used for control flow, empty catch block, exception with useless message
   - Exercise 2 [Intermediate]: Implement `StackUnderflowException` correctly: custom exception class, chaining constructor, good message format, `@throws` documentation
   - Exercise 3 [Intermediate]: Make a `BankAccount.transfer()` method failure-atomic using the "check then mutate" and "copy and swap" techniques
   - Exercise 4 [Advanced]: Wrap a third-party library that throws checked exceptions in a service layer that throws appropriate domain unchecked exceptions (exception translation)

5. **For use cases:**
   - Spring's `DataAccessException` hierarchy — exception translation from JDBC checked exceptions to unchecked domain exceptions
   - REST API error handling: translating domain exceptions to HTTP status codes with `@ExceptionHandler`
   - Circuit breaker patterns (Resilience4j) — catching and translating exceptions in distributed systems

6. **For interview questions:** "When would you choose a checked exception over an unchecked exception?" (tests philosophy, not just knowledge). "What is exception chaining and why is it important?" (many don't know). The gotcha: "What is the problem with `catch (Exception e)` at the top level of a thread?"

7. **Advice:** Give a strong recommendation for the "fail fast" principle. A method that validates its preconditions and fails immediately with a clear message is 10× easier to debug than one that silently corrupts state and fails later. Include a code review checklist for exception usage.
