"""
Exercise 3: Error Handling and Retries

DDIA Reference: Chapter 7, "Transactions" (pp. 235-240)

This exercise demonstrates ERROR HANDLING and RETRIES in transactions.

Key concepts:
  - Transactions enable safe retries (atomicity means no partial state)
  - But retrying is not as simple as it looks
  - Idempotency: retrying must be safe (no duplicate effects)
  - Exponential backoff: avoid overwhelming the system
  - Transient vs permanent errors: only retry transient errors

Real-world scenarios:
  1. Network failure: retry is safe (transaction was atomic)
  2. Duplicate write: retry causes duplicate effect (need idempotency)
  3. Overload: retry makes it worse (need exponential backoff)
  4. Constraint violation: retry is pointless (permanent error)

Run: python 03_error_handling_retries.py
"""

import sys
import time
import random
from typing import Dict, Optional, Any, Callable
from enum import Enum
from dataclasses import dataclass

sys.stdout.reconfigure(encoding='utf-8')


# =============================================================================
# CORE COMPONENTS: ErrorType, Transaction, RetryPolicy
# =============================================================================

class ErrorType(Enum):
    """Type of error that can occur."""
    TRANSIENT = "transient"  # Retry is safe
    PERMANENT = "permanent"  # Retry is pointless
    DUPLICATE = "duplicate"  # Retry causes duplicate effect


class TransactionResult(Enum):
    """Result of a transaction."""
    SUCCESS = "success"
    TRANSIENT_ERROR = "transient_error"
    PERMANENT_ERROR = "permanent_error"
    DUPLICATE_ERROR = "duplicate_error"


@dataclass
class TransactionOutcome:
    """Outcome of a transaction attempt."""
    result: TransactionResult
    error_message: str = ""
    attempt: int = 1

    def __repr__(self):
        return f"Outcome({self.result.value}, attempt={self.attempt})"


class RetryPolicy:
    """
    Policy for retrying failed transactions.

    DDIA: "Retrying is not as simple as it looks. You need to handle:
      1. Idempotency: retrying must be safe
      2. Exponential backoff: avoid overwhelming the system
      3. Transient vs permanent errors: only retry transient errors"
    """

    def __init__(self, max_retries: int = 3, initial_backoff_ms: float = 10):
        self.max_retries = max_retries
        self.initial_backoff_ms = initial_backoff_ms

    def should_retry(self, error_type: ErrorType, attempt: int) -> bool:
        """Determine if we should retry based on error type and attempt count."""
        if error_type == ErrorType.PERMANENT:
            return False  # Never retry permanent errors

        if error_type == ErrorType.DUPLICATE:
            return False  # Never retry duplicate errors

        if attempt >= self.max_retries:
            return False  # Max retries exceeded

        return True

    def get_backoff_ms(self, attempt: int) -> float:
        """
        Calculate backoff time using exponential backoff with jitter.

        DDIA: "If the error is due to overload, retrying makes the problem
        worse. You need exponential backoff."

        Formula: backoff = initial_backoff * (2 ^ attempt) + random_jitter
        """
        exponential_backoff = self.initial_backoff_ms * (2 ** (attempt - 1))
        jitter = random.uniform(0, exponential_backoff * 0.1)
        return exponential_backoff + jitter


class IdempotencyKey:
    """
    An idempotency key ensures that retrying a transaction is safe.

    DDIA: "If the transaction actually succeeded, but the network failed
    while sending the acknowledgment back to the client, the client may
    retry and execute it twice (e.g., sending an email twice or charging
    a credit card twice). You need idempotency."

    Solution: Use an idempotency key to detect duplicate requests.
    """

    def __init__(self):
        self.completed_requests: Dict[str, Any] = {}  # key -> result

    def is_duplicate(self, key: str) -> bool:
        """Check if this request has already been processed."""
        return key in self.completed_requests

    def get_result(self, key: str) -> Optional[Any]:
        """Get the result of a previously processed request."""
        return self.completed_requests.get(key)

    def record_result(self, key: str, result: Any):
        """Record the result of a processed request."""
        self.completed_requests[key] = result


class TransactionExecutor:
    """
    Executes transactions with error handling and retries.

    DDIA: "A key safety feature of transactions is the ability to retry
    on failure (because Atomicity means the failed transaction left no
    partial state). However, retrying is not as simple as it looks."
    """

    def __init__(self, retry_policy: RetryPolicy = None):
        self.retry_policy = retry_policy or RetryPolicy()
        self.idempotency_keys = IdempotencyKey()

    def execute_with_retries(
        self,
        txn_func: Callable,
        idempotency_key: str = None,
        description: str = ""
    ) -> TransactionOutcome:
        """
        Execute a transaction with automatic retries.

        DDIA: "The application can safely retry on transient errors
        because Atomicity means the failed transaction left no partial state."

        Steps:
          1. Check idempotency key (avoid duplicate effects)
          2. Execute transaction
          3. On transient error: retry with exponential backoff
          4. On permanent error: fail immediately
        """
        attempt = 0

        while attempt < self.retry_policy.max_retries:
            attempt += 1

            # Step 1: Check idempotency key
            if idempotency_key and self.idempotency_keys.is_duplicate(idempotency_key):
                result = self.idempotency_keys.get_result(idempotency_key)
                return TransactionOutcome(
                    result=TransactionResult.SUCCESS,
                    error_message=f"Duplicate request (idempotency key: {idempotency_key})",
                    attempt=attempt
                )

            # Step 2: Execute transaction
            try:
                outcome = txn_func()

                # Success
                if outcome["success"]:
                    if idempotency_key:
                        self.idempotency_keys.record_result(idempotency_key, outcome)

                    return TransactionOutcome(
                        result=TransactionResult.SUCCESS,
                        error_message="",
                        attempt=attempt
                    )

                # Transient error
                if outcome.get("error_type") == ErrorType.TRANSIENT:
                    if not self.retry_policy.should_retry(ErrorType.TRANSIENT, attempt):
                        return TransactionOutcome(
                            result=TransactionResult.TRANSIENT_ERROR,
                            error_message=outcome.get("error_message", "Transient error"),
                            attempt=attempt
                        )

                    # Backoff and retry
                    backoff_ms = self.retry_policy.get_backoff_ms(attempt)
                    time.sleep(backoff_ms / 1000)
                    continue

                # Permanent error
                if outcome.get("error_type") == ErrorType.PERMANENT:
                    return TransactionOutcome(
                        result=TransactionResult.PERMANENT_ERROR,
                        error_message=outcome.get("error_message", "Permanent error"),
                        attempt=attempt
                    )

                # Duplicate error
                if outcome.get("error_type") == ErrorType.DUPLICATE:
                    return TransactionOutcome(
                        result=TransactionResult.DUPLICATE_ERROR,
                        error_message=outcome.get("error_message", "Duplicate error"),
                        attempt=attempt
                    )

            except Exception as e:
                # Unexpected error
                return TransactionOutcome(
                    result=TransactionResult.PERMANENT_ERROR,
                    error_message=str(e),
                    attempt=attempt
                )

        # Max retries exceeded
        return TransactionOutcome(
            result=TransactionResult.TRANSIENT_ERROR,
            error_message="Max retries exceeded",
            attempt=attempt
        )


# =============================================================================
# DEMONSTRATION SCENARIOS
# =============================================================================

def print_header(title: str):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_section(title: str):
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}")


def demo_1_why_retries_are_needed():
    """
    Demo 1: Show why retries are needed.

    DDIA concept: "A key safety feature of transactions is the ability
    to retry on failure."
    """
    print_header("DEMO 1: Why Retries Are Needed")
    print("""
    Scenario: Network failure during transaction commit.

    Without retries:
      • Transaction succeeds on server
      • Network fails before acknowledgment
      • Client thinks transaction failed
      • User retries manually
      • Result: duplicate transaction!

    With retries:
      • Transaction succeeds on server
      • Network fails before acknowledgment
      • Client automatically retries
      • Server detects duplicate (idempotency key)
      • Client gets correct result
      • Result: no duplicate!
    """)

    print("  Timeline:\n")

    print("  1. Client sends: Transfer $100 from A to B")
    print("     Server receives and processes")
    print("     ✅ Transaction succeeds on server")

    print("\n  2. Server sends acknowledgment")
    print("     💥 Network fails!")
    print("     Client never receives acknowledgment")

    print("\n  3. Client timeout:")
    print("     ❌ Without retries:")
    print("        Client thinks transaction failed")
    print("        User manually retries")
    print("        Result: $200 transferred (duplicate!)")

    print("\n     ✅ With retries:")
    print("        Client automatically retries")
    print("        Server detects duplicate (idempotency key)")
    print("        Server returns cached result")
    print("        Result: $100 transferred (correct!)")

    print("""
  💡 KEY INSIGHT (DDIA):
     Retries are safe because:
       • Atomicity means failed transaction left no partial state
       • Idempotency keys prevent duplicate effects
       • Client can safely retry without manual intervention
    """)


def demo_2_transient_vs_permanent_errors():
    """
    Demo 2: Show the difference between transient and permanent errors.

    DDIA concept: "It is only worth retrying on transient errors.
    Retrying on a permanent error is pointless."
    """
    print_header("DEMO 2: Transient vs Permanent Errors")
    print("""
    Transient errors (retry is safe):
      • Network timeout
      • Temporary overload
      • Deadlock
      • Temporary database unavailability

    Permanent errors (retry is pointless):
      • Constraint violation (e.g., duplicate key)
      • Invalid input
      • Permission denied
      • Schema mismatch
    """)

    executor = TransactionExecutor()

    print("  Scenario 1: Transient error (network timeout)\n")

    attempt_count = [0]

    def transient_error_txn():
        attempt_count[0] += 1
        if attempt_count[0] < 3:
            return {
                "success": False,
                "error_type": ErrorType.TRANSIENT,
                "error_message": "Network timeout"
            }
        return {"success": True}

    print("  Executing transaction with transient errors...")
    outcome = executor.execute_with_retries(transient_error_txn, description="Transfer")
    print(f"  Result: {outcome.result.value}")
    print(f"  Attempts: {outcome.attempt}")
    print(f"  ✅ Succeeded after retries!")

    print(f"\n  Scenario 2: Permanent error (constraint violation)\n")

    def permanent_error_txn():
        return {
            "success": False,
            "error_type": ErrorType.PERMANENT,
            "error_message": "Duplicate key: account already exists"
        }

    print("  Executing transaction with permanent error...")
    outcome = executor.execute_with_retries(permanent_error_txn, description="Create account")
    print(f"  Result: {outcome.result.value}")
    print(f"  Attempts: {outcome.attempt}")
    print(f"  ❌ Failed immediately (no retries)")

    print("""
  💡 KEY INSIGHT (DDIA):
     Retry strategy:
       • Transient errors: retry with exponential backoff
       • Permanent errors: fail immediately
       • Duplicate errors: return cached result
    """)


def demo_3_idempotency_prevents_duplicates():
    """
    Demo 3: Show how idempotency keys prevent duplicate effects.

    DDIA concept: "If the transaction actually succeeded, but the network
    failed while sending the acknowledgment back to the client, the client
    may retry and execute it twice. You need idempotency."
    """
    print_header("DEMO 3: Idempotency Prevents Duplicates")
    print("""
    Scenario: Client retries after network failure.

    Without idempotency:
      • First attempt: Transfer $100 (succeeds)
      • Network fails
      • Retry: Transfer $100 again (succeeds)
      • Result: $200 transferred (duplicate!)

    With idempotency:
      • First attempt: Transfer $100 (succeeds, recorded with key)
      • Network fails
      • Retry: Server detects duplicate key
      • Server returns cached result
      • Result: $100 transferred (correct!)
    """)

    executor = TransactionExecutor()
    account_balance = {"balance": 1000}

    def transfer_txn():
        account_balance["balance"] -= 100
        return {"success": True}

    print("  Initial balance: $1000\n")

    print("  Attempt 1: Transfer $100 with idempotency key 'txn_123'")
    outcome1 = executor.execute_with_retries(
        transfer_txn,
        idempotency_key="txn_123",
        description="Transfer"
    )
    print(f"  Result: {outcome1.result.value}")
    print(f"  Balance: ${account_balance['balance']}")

    print(f"\n  Attempt 2: Retry with same idempotency key 'txn_123'")
    outcome2 = executor.execute_with_retries(
        transfer_txn,
        idempotency_key="txn_123",
        description="Transfer"
    )
    print(f"  Result: {outcome2.result.value}")
    print(f"  Balance: ${account_balance['balance']}")
    print(f"  ✅ Balance unchanged (duplicate detected)!")

    print("""
  💡 KEY INSIGHT (DDIA):
     Idempotency keys ensure:
       • Retries don't cause duplicate effects
       • Server returns cached result for duplicate requests
       • Client can safely retry without manual intervention
    """)


def demo_4_exponential_backoff():
    """
    Demo 4: Show exponential backoff to avoid overwhelming the system.

    DDIA concept: "If the error is due to overload, retrying makes the
    problem worse. You need exponential backoff."
    """
    print_header("DEMO 4: Exponential Backoff")
    print("""
    Scenario: System is overloaded, many clients are retrying.

    Without exponential backoff:
      • All clients retry immediately
      • System is even more overloaded
      • More clients fail
      • Cascading failure!

    With exponential backoff:
      • Clients wait before retrying
      • Wait time increases with each retry
      • System has time to recover
      • Fewer cascading failures
    """)

    policy = RetryPolicy(max_retries=5, initial_backoff_ms=10)

    print("  Backoff schedule:\n")
    print("  Attempt | Backoff (ms) | Wait time")
    print("  ────────┼──────────────┼──────────")

    for attempt in range(1, 6):
        backoff = policy.get_backoff_ms(attempt)
        print(f"  {attempt:7d} | {backoff:12.1f} | {backoff/1000:6.3f}s")

    print("""
  Formula: backoff = initial_backoff * (2 ^ (attempt - 1)) + jitter

  Example:
    Attempt 1: 10ms (immediate retry)
    Attempt 2: 20ms (double)
    Attempt 3: 40ms (double)
    Attempt 4: 80ms (double)
    Attempt 5: 160ms (double)

  Benefits:
    • Reduces load on overloaded system
    • Gives system time to recover
    • Prevents cascading failures
    • Jitter prevents thundering herd
    """)

    print("""
  💡 KEY INSIGHT (DDIA):
     Exponential backoff is essential for:
       • Handling overload gracefully
       • Preventing cascading failures
       • Allowing system to recover
    """)


def demo_5_retry_strategy():
    """
    Demo 5: Show a complete retry strategy.

    DDIA concept: "Retrying is not as simple as it looks. You need to
    handle idempotency, exponential backoff, and error types."
    """
    print_header("DEMO 5: Complete Retry Strategy")
    print("""
    A robust retry strategy handles:
      1. Idempotency: prevent duplicate effects
      2. Exponential backoff: avoid overwhelming system
      3. Error classification: only retry transient errors
      4. Max retries: give up after too many attempts
    """)

    executor = TransactionExecutor(
        retry_policy=RetryPolicy(max_retries=4, initial_backoff_ms=10)
    )

    print("  Scenario: Transfer with transient errors\n")

    attempt_count = [0]

    def transfer_with_errors():
        attempt_count[0] += 1
        print(f"    Attempt {attempt_count[0]}: ", end="")

        if attempt_count[0] == 1:
            print("Network timeout (transient)")
            return {
                "success": False,
                "error_type": ErrorType.TRANSIENT,
                "error_message": "Network timeout"
            }
        elif attempt_count[0] == 2:
            print("Database overload (transient)")
            return {
                "success": False,
                "error_type": ErrorType.TRANSIENT,
                "error_message": "Database overload"
            }
        else:
            print("Success!")
            return {"success": True}

    print("  Executing transfer with automatic retries:")
    outcome = executor.execute_with_retries(
        transfer_with_errors,
        idempotency_key="transfer_123",
        description="Transfer"
    )

    print(f"\n  Final result: {outcome.result.value}")
    print(f"  Total attempts: {outcome.attempt}")
    print(f"  ✅ Transaction succeeded after retries!")

    print("""
  💡 KEY INSIGHT (DDIA):
     A complete retry strategy:
       1. Assigns idempotency key to each request
       2. Classifies errors (transient vs permanent)
       3. Retries only transient errors
       4. Uses exponential backoff
       5. Gives up after max retries
       6. Returns cached result for duplicates
    """)


def demo_6_when_not_to_retry():
    """
    Demo 6: Show when NOT to retry.

    DDIA concept: "It is only worth retrying on transient errors.
    Retrying on a permanent error is pointless."
    """
    print_header("DEMO 6: When NOT to Retry")
    print("""
    Permanent errors that should NOT be retried:
      • Constraint violations (duplicate key, foreign key)
      • Invalid input (malformed request)
      • Permission denied (authentication/authorization)
      • Schema mismatch (incompatible data)
      • Business logic violations (insufficient funds)

    Retrying these errors wastes resources and delays failure.
    Better to fail fast and let the application handle it.
    """)

    executor = TransactionExecutor()

    print("  Scenario 1: Duplicate key (permanent error)\n")

    def duplicate_key_txn():
        return {
            "success": False,
            "error_type": ErrorType.PERMANENT,
            "error_message": "Duplicate key: user_id already exists"
        }

    outcome = executor.execute_with_retries(duplicate_key_txn)
    print(f"  Result: {outcome.result.value}")
    print(f"  Attempts: {outcome.attempt}")
    print(f"  ✅ Failed immediately (no retries)")

    print(f"\n  Scenario 2: Insufficient funds (permanent error)\n")

    def insufficient_funds_txn():
        return {
            "success": False,
            "error_type": ErrorType.PERMANENT,
            "error_message": "Insufficient funds: need $100, have $50"
        }

    outcome = executor.execute_with_retries(insufficient_funds_txn)
    print(f"  Result: {outcome.result.value}")
    print(f"  Attempts: {outcome.attempt}")
    print(f"  ✅ Failed immediately (no retries)")

    print("""
  💡 KEY INSIGHT (DDIA):
     Fail fast on permanent errors:
       • Retrying won't help
       • Wastes resources
       • Delays error handling
       • Better to fail immediately and let application handle it
    """)


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 80)
    print("  EXERCISE 3: ERROR HANDLING AND RETRIES")
    print("  DDIA Chapter 7: 'Transactions'")
    print("=" * 80)
    print("""
  This exercise demonstrates ERROR HANDLING and RETRIES in transactions.

  Key concepts:
    • Transactions enable safe retries (atomicity)
    • Idempotency prevents duplicate effects
    • Exponential backoff avoids overwhelming system
    • Only retry transient errors
    • Fail fast on permanent errors
    """)

    demo_1_why_retries_are_needed()
    demo_2_transient_vs_permanent_errors()
    demo_3_idempotency_prevents_duplicates()
    demo_4_exponential_backoff()
    demo_5_retry_strategy()
    demo_6_when_not_to_retry()

    print("\n" + "=" * 80)
    print("  EXERCISE 3 COMPLETE ✅")
    print("=" * 80)
    print("""
  Key Takeaways:

  1. 🔄 Retries are safe because of atomicity
  2. 🔑 Idempotency keys prevent duplicate effects
  3. ⏱️  Exponential backoff avoids overwhelming system
  4. 🎯 Only retry transient errors
  5. ⚡ Fail fast on permanent errors
  6. 📊 Monitor retry rates to detect issues

  Summary:
    • Transient errors: retry with exponential backoff
    • Permanent errors: fail immediately
    • Duplicate requests: return cached result
    • Max retries: give up and fail
    """)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting...")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
