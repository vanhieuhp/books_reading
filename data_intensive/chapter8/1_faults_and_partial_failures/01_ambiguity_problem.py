"""
Exercise 1: The Ambiguity Problem — Why You Can't Retry Safely

DDIA Reference: Chapter 8, "Faults and Partial Failures" (pp. 280-283)

This exercise demonstrates the fundamental problem of distributed systems:
when you don't get a response, you cannot tell WHY.

Scenarios:
  1. Request lost in network
  2. Server is processing (slow)
  3. Server processed it, response lost
  4. Server crashed mid-processing

From the client's perspective, all four look identical: NO RESPONSE.

The consequence: Retrying is dangerous. If you retry and the first request
actually succeeded, you might execute the operation twice.

Run: python 01_ambiguity_problem.py
"""

import sys
import time
import random
from enum import Enum
from typing import Optional, Tuple

sys.stdout.reconfigure(encoding='utf-8')


# =============================================================================
# FAILURE MODES
# =============================================================================

class FailureMode(Enum):
    """The four indistinguishable failure scenarios."""
    REQUEST_LOST = "Request lost in network"
    SERVER_SLOW = "Server is processing (slow)"
    RESPONSE_LOST = "Server processed it, response lost"
    SERVER_CRASHED = "Server crashed mid-processing"


# =============================================================================
# SERVER SIMULATION
# =============================================================================

class SimpleServer:
    """A server that can fail in different ways."""

    def __init__(self, failure_mode: FailureMode, processing_time: float = 0.1):
        self.failure_mode = failure_mode
        self.processing_time = processing_time
        self.processed_requests = []  # Track what we actually processed
        self.crashed = False

    def handle_request(self, request_id: int, amount: float) -> Optional[str]:
        """
        Process a payment request.

        Returns:
          - "success" if request was processed and response sent
          - None if request was lost, response was lost, or server crashed
        """

        if self.failure_mode == FailureMode.REQUEST_LOST:
            # Request never reaches server
            return None

        if self.failure_mode == FailureMode.SERVER_SLOW:
            # Server receives request but takes too long
            time.sleep(self.processing_time + 2.0)  # Simulate slow processing
            # Response will be sent, but client will timeout
            self.processed_requests.append((request_id, amount))
            return "success"

        if self.failure_mode == FailureMode.RESPONSE_LOST:
            # Server processes request but response is lost
            time.sleep(self.processing_time)
            self.processed_requests.append((request_id, amount))
            return None  # Response lost

        if self.failure_mode == FailureMode.SERVER_CRASHED:
            # Server crashes mid-processing
            time.sleep(self.processing_time / 2)
            # Randomly decide if we actually processed it before crashing
            if random.random() < 0.5:
                self.processed_requests.append((request_id, amount))
            self.crashed = True
            return None

        return "success"


# =============================================================================
# CLIENT SIMULATION
# =============================================================================

class Client:
    """A client that sends requests and handles timeouts."""

    def __init__(self, server: SimpleServer, timeout: float = 1.0):
        self.server = server
        self.timeout = timeout
        self.sent_requests = []  # Track what we sent
        self.successful_responses = []  # Track what we got responses for

    def send_payment(self, request_id: int, amount: float) -> Tuple[bool, str]:
        """
        Send a payment request to the server.

        Returns:
          (success: bool, reason: str)
          - (True, "Response received") if we got a response
          - (False, "Timeout") if we didn't get a response within timeout
        """
        self.sent_requests.append((request_id, amount))

        start_time = time.time()
        response = self.server.handle_request(request_id, amount)
        elapsed = time.time() - start_time

        if elapsed > self.timeout:
            # Timeout: we didn't get a response in time
            return False, "Timeout"

        if response is None:
            # No response (could be any of 4 reasons)
            return False, "No response"

        # Got a response
        self.successful_responses.append((request_id, amount))
        return True, "Response received"


# =============================================================================
# DEMONSTRATION
# =============================================================================

def demonstrate_ambiguity():
    """Show that all four failure modes look identical from the client's perspective."""

    print("=" * 80)
    print("EXERCISE 1: THE AMBIGUITY PROBLEM")
    print("=" * 80)
    print()

    print("📋 SCENARIO: Client sends a payment request to a server")
    print("   Client timeout: 1 second")
    print()

    # Test each failure mode
    for failure_mode in FailureMode:
        print("-" * 80)
        print(f"🔴 FAILURE MODE: {failure_mode.value}")
        print("-" * 80)

        server = SimpleServer(failure_mode)
        client = Client(server, timeout=1.0)

        # Send a payment request
        request_id = 1
        amount = 100.0

        print(f"💳 Client sends: Payment request #{request_id} for ${amount}")
        print(f"   (Client will wait up to 1 second for response)")
        print()

        success, reason = client.send_payment(request_id, amount)

        print(f"⏱️  Result: {reason}")
        print()

        # Show what actually happened on the server
        print(f"🖥️  Server state:")
        print(f"   - Crashed: {server.crashed}")
        print(f"   - Processed requests: {server.processed_requests}")
        print()

        # The key insight
        if not success:
            print("❓ CLIENT'S PERSPECTIVE:")
            print("   'I didn't get a response. Why?'")
            print()
            print("   Possible reasons:")
            print("   1. Request was lost in the network")
            print("   2. Server is processing (slow)")
            print("   3. Server processed it, but response was lost")
            print("   4. Server crashed mid-processing")
            print()
            print("   ⚠️  I CANNOT TELL WHICH ONE!")
            print()

            # Show the actual reason
            print(f"✅ ACTUAL REASON: {failure_mode.value}")
            print()

            # Show the danger of retrying
            if server.processed_requests:
                print("⚠️  DANGER: If I retry, the operation might execute TWICE!")
                print(f"   Server already processed: {server.processed_requests}")
                print()
        else:
            print("✅ Got response successfully")
            print()

        print()


# =============================================================================
# RETRY STRATEGY DEMONSTRATION
# =============================================================================

def demonstrate_retry_danger():
    """Show why naive retry strategies are dangerous."""

    print("=" * 80)
    print("THE DANGER OF RETRYING")
    print("=" * 80)
    print()

    print("Scenario: Client sends payment request, gets no response")
    print("Strategy: Retry 3 times")
    print()

    # Simulate the RESPONSE_LOST scenario
    server = SimpleServer(FailureMode.RESPONSE_LOST)
    client = Client(server, timeout=1.0)

    print("Attempt 1:")
    success, reason = client.send_payment(1, 100.0)
    print(f"  Result: {reason}")
    print(f"  Server processed: {server.processed_requests}")
    print()

    if not success:
        print("Attempt 2 (retry):")
        success, reason = client.send_payment(2, 100.0)
        print(f"  Result: {reason}")
        print(f"  Server processed: {server.processed_requests}")
        print()

    if not success:
        print("Attempt 3 (retry again):")
        success, reason = client.send_payment(3, 100.0)
        print(f"  Result: {reason}")
        print(f"  Server processed: {server.processed_requests}")
        print()

    print("💥 DISASTER:")
    print(f"   Client sent 3 requests (IDs: 1, 2, 3)")
    print(f"   Server processed: {server.processed_requests}")
    print()
    print("   The first request WAS processed (response was just lost).")
    print("   But the client didn't know, so it retried.")
    print("   Now the payment was charged 3 times!")
    print()


# =============================================================================
# IDEMPOTENCY SOLUTION
# =============================================================================

class IdempotentServer:
    """A server that deduplicates requests using request IDs."""

    def __init__(self, failure_mode: FailureMode, processing_time: float = 0.1):
        self.failure_mode = failure_mode
        self.processing_time = processing_time
        self.processed_requests = {}  # request_id -> (amount, timestamp)
        self.crashed = False

    def handle_request(self, request_id: int, amount: float) -> Optional[str]:
        """
        Process a payment request idempotently.

        If we've already processed this request_id, return the same result
        without processing it again.
        """

        # Check if we've already processed this request
        if request_id in self.processed_requests:
            # Return the same result as before (without processing again)
            return "success"

        if self.failure_mode == FailureMode.REQUEST_LOST:
            return None

        if self.failure_mode == FailureMode.SERVER_SLOW:
            time.sleep(self.processing_time + 2.0)
            self.processed_requests[request_id] = (amount, time.time())
            return "success"

        if self.failure_mode == FailureMode.RESPONSE_LOST:
            time.sleep(self.processing_time)
            self.processed_requests[request_id] = (amount, time.time())
            return None

        if self.failure_mode == FailureMode.SERVER_CRASHED:
            time.sleep(self.processing_time / 2)
            if random.random() < 0.5:
                self.processed_requests[request_id] = (amount, time.time())
            self.crashed = True
            return None

        self.processed_requests[request_id] = (amount, time.time())
        return "success"


class IdempotentClient:
    """A client that uses the same request ID for retries."""

    def __init__(self, server: IdempotentServer, timeout: float = 1.0):
        self.server = server
        self.timeout = timeout
        self.attempts = 0

    def send_payment_with_retries(self, request_id: int, amount: float, max_retries: int = 3) -> bool:
        """Send a payment request with retries using the same request ID."""

        for attempt in range(max_retries):
            self.attempts += 1
            start_time = time.time()
            response = self.server.handle_request(request_id, amount)
            elapsed = time.time() - start_time

            if elapsed <= self.timeout and response is not None:
                return True

        return False


def demonstrate_idempotency_solution():
    """Show how idempotency solves the retry problem."""

    print("=" * 80)
    print("SOLUTION: IDEMPOTENT OPERATIONS")
    print("=" * 80)
    print()

    print("Strategy: Use the same request ID for all retries")
    print("Server deduplicates based on request ID")
    print()

    server = IdempotentServer(FailureMode.RESPONSE_LOST)
    client = IdempotentClient(server, timeout=1.0)

    request_id = 1  # Same request ID for all attempts
    amount = 100.0

    print(f"Sending payment request #{request_id} for ${amount}")
    print("(Will retry up to 3 times with the same request ID)")
    print()

    success = client.send_payment_with_retries(request_id, amount, max_retries=3)

    print(f"Result: {'Success' if success else 'Failed'}")
    print(f"Attempts made: {client.attempts}")
    print(f"Server processed: {server.processed_requests}")
    print()

    print("✅ SOLUTION WORKS:")
    print(f"   Client retried 3 times")
    print(f"   But server only processed the payment ONCE")
    print(f"   Because all retries had the same request ID")
    print()


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    demonstrate_ambiguity()
    print()
    print()
    demonstrate_retry_danger()
    print()
    print()
    demonstrate_idempotency_solution()

    print()
    print("=" * 80)
    print("KEY TAKEAWAYS")
    print("=" * 80)
    print()
    print("1. When you don't get a response, you cannot tell WHY")
    print("   - Request lost?")
    print("   - Server slow?")
    print("   - Response lost?")
    print("   - Server crashed?")
    print()
    print("2. Naive retries are dangerous")
    print("   - If the first request actually succeeded, retrying executes it twice")
    print()
    print("3. Solution: Idempotent operations")
    print("   - Use a unique request ID")
    print("   - Server deduplicates based on request ID")
    print("   - Retries are safe because they produce the same result")
    print()
