"""
Exercise 1: Network Failures — The Ambiguity Problem

DDIA Reference: Chapter 8, "What Can Go Wrong with a Network Request" (pp. 280-282)

This exercise demonstrates the fundamental problem with distributed systems:
when you send a request and don't receive a response, you CANNOT distinguish
between multiple failure scenarios. All four look identical from the client's
perspective.

Key concepts:
  - Request lost in network
  - Server processing slowly
  - Response lost in network
  - Server crashed mid-processing
  - All four scenarios produce the same observable outcome: no response

Run: python 01_network_failures.py
"""

import sys
import time
import random
import threading
from enum import Enum
from typing import Optional, Callable
from dataclasses import dataclass

# Fix Windows terminal encoding for Unicode output
sys.stdout.reconfigure(encoding='utf-8')


# =============================================================================
# CORE COMPONENTS: Network, Server, Client
# =============================================================================

class NetworkFailureType(Enum):
    """Types of network failures that can occur."""
    REQUEST_LOST = "request_lost"
    SERVER_SLOW = "server_slow"
    RESPONSE_LOST = "response_lost"
    SERVER_CRASHED = "server_crashed"


@dataclass
class Request:
    """A network request."""
    request_id: int
    data: str
    timestamp: float


@dataclass
class Response:
    """A network response."""
    request_id: int
    result: str
    timestamp: float


class NetworkSimulator:
    """
    Simulates a network with various failure modes.

    DDIA insight: "When you send a request over the network and don't receive
    a response, you cannot distinguish between these scenarios..."
    """

    def __init__(self, failure_type: NetworkFailureType, failure_probability: float = 0.5):
        self.failure_type = failure_type
        self.failure_probability = failure_probability
        self.requests_sent = 0
        self.responses_received = 0
        self.failures_triggered = 0

    def send_request(self, request: Request, server_handler: Callable) -> Optional[Response]:
        """
        Send a request through the network.

        Returns the response if successful, None if network failure occurs.
        """
        self.requests_sent += 1

        # Simulate network delay
        network_delay = random.uniform(0.01, 0.05)  # 10-50ms
        time.sleep(network_delay)

        # Determine if failure occurs
        if random.random() < self.failure_probability:
            self.failures_triggered += 1

            if self.failure_type == NetworkFailureType.REQUEST_LOST:
                # Request never reaches server
                return None

            elif self.failure_type == NetworkFailureType.SERVER_SLOW:
                # Request reaches server, but server is slow
                # Simulate server processing for a long time
                time.sleep(2.0)  # Simulate slow processing
                # But we'll timeout before getting response
                return None

            elif self.failure_type == NetworkFailureType.RESPONSE_LOST:
                # Server processes request successfully, but response is lost
                response = server_handler(request)
                # Response is lost in network
                return None

            elif self.failure_type == NetworkFailureType.SERVER_CRASHED:
                # Server crashes while processing
                # Simulate crash by not returning anything
                return None

        # Success case: request reaches server, server processes, response returns
        response = server_handler(request)
        self.responses_received += 1
        return response


class SimpleServer:
    """A simple server that processes requests."""

    def __init__(self, name: str = "SERVER"):
        self.name = name
        self.requests_processed = 0
        self.storage = {}

    def handle_request(self, request: Request) -> Response:
        """Process a request and return a response."""
        self.requests_processed += 1

        # Simulate processing
        time.sleep(random.uniform(0.01, 0.05))

        # Store the data
        self.storage[request.request_id] = request.data

        return Response(
            request_id=request.request_id,
            result=f"Processed: {request.data}",
            timestamp=time.time()
        )


class Client:
    """A client that sends requests and handles responses."""

    def __init__(self, name: str = "CLIENT", timeout: float = 1.0):
        self.name = name
        self.timeout = timeout
        self.requests_sent = 0
        self.responses_received = 0
        self.timeouts = 0

    def send_request_with_timeout(self, network: NetworkSimulator, server: SimpleServer,
                                   request_data: str) -> Optional[Response]:
        """
        Send a request with a timeout.

        If no response within timeout, assume failure.
        """
        self.requests_sent += 1
        request = Request(
            request_id=self.requests_sent,
            data=request_data,
            timestamp=time.time()
        )

        # Send request through network
        start_time = time.time()
        response = network.send_request(request, server.handle_request)

        elapsed = time.time() - start_time

        if response is None:
            self.timeouts += 1
            return None
        else:
            self.responses_received += 1
            return response


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


def demo_1_request_lost():
    """
    Demo 1: Request is lost in the network.

    DDIA: "Scenario 1: Request was lost in the network
           Client ──── X ────► Server
           (Server never received the request)"
    """
    print_header("SCENARIO 1: Request Lost in Network")
    print("""
    The client sends a request, but it never reaches the server.
    The network drops the packet.

    From the client's perspective: No response (timeout)
    """)

    server = SimpleServer("SERVER")
    network = NetworkSimulator(NetworkFailureType.REQUEST_LOST, failure_probability=1.0)
    client = Client("CLIENT", timeout=1.0)

    print("  📤 Client sends request: 'INSERT user (id=1, name=Alice)'")
    print("  ⏳ Waiting for response...")

    response = client.send_request_with_timeout(network, server, "INSERT user (id=1, name=Alice)")

    if response is None:
        print("  ❌ TIMEOUT: No response received after 1.0s")
        print(f"  📊 Server processed: {server.requests_processed} requests")
        print(f"  💾 Server storage: {server.storage}")
    else:
        print(f"  ✅ Response: {response.result}")

    print("""
  💡 KEY INSIGHT:
     The client has NO WAY to know that the request was lost.
     It just sees: no response = timeout.
    """)


def demo_2_server_slow():
    """
    Demo 2: Server is processing slowly.

    DDIA: "Scenario 2: Server received request but is too slow
           Client ────────────► Server (processing for 30 seconds...)
           (Response hasn't come back yet)"
    """
    print_header("SCENARIO 2: Server Processing Slowly")
    print("""
    The client sends a request, the server receives it and starts processing,
    but the server is slow. The response doesn't come back within the timeout.

    From the client's perspective: No response (timeout)
    """)

    server = SimpleServer("SERVER")
    network = NetworkSimulator(NetworkFailureType.SERVER_SLOW, failure_probability=1.0)
    client = Client("CLIENT", timeout=1.0)

    print("  📤 Client sends request: 'SELECT * FROM users'")
    print("  ⏳ Waiting for response (timeout=1.0s)...")

    response = client.send_request_with_timeout(network, server, "SELECT * FROM users")

    if response is None:
        print("  ❌ TIMEOUT: No response received after 1.0s")
        print(f"  📊 Server processed: {server.requests_processed} requests")
        print(f"     (Server was still processing when we gave up!)")
    else:
        print(f"  ✅ Response: {response.result}")

    print("""
  💡 KEY INSIGHT:
     The client cannot tell if the server is slow or if the request was lost.
     Both produce the same observable outcome: timeout.
    """)


def demo_3_response_lost():
    """
    Demo 3: Response is lost in the network.

    DDIA: "Scenario 3: Server processed request, but response was lost
           Client ◄──── X ──── Server
           (Server did the work, but you'll never know!)"
    """
    print_header("SCENARIO 3: Response Lost in Network")
    print("""
    The client sends a request, the server receives it, processes it successfully,
    but the response is lost in the network on the way back.

    From the client's perspective: No response (timeout)

    ⚠️  DANGER: The server DID the work, but the client doesn't know!
    """)

    server = SimpleServer("SERVER")
    network = NetworkSimulator(NetworkFailureType.RESPONSE_LOST, failure_probability=1.0)
    client = Client("CLIENT", timeout=1.0)

    print("  📤 Client sends request: 'UPDATE user SET age=26 WHERE id=1'")
    print("  ⏳ Waiting for response (timeout=1.0s)...")

    response = client.send_request_with_timeout(network, server, "UPDATE user SET age=26 WHERE id=1")

    if response is None:
        print("  ❌ TIMEOUT: No response received after 1.0s")
        print(f"  📊 Server processed: {server.requests_processed} requests")
        print(f"  💾 Server storage: {server.storage}")
        print(f"     ⚠️  THE SERVER DID THE WORK! But we don't know it!")
    else:
        print(f"  ✅ Response: {response.result}")

    print("""
  💡 KEY INSIGHT:
     This is the most dangerous scenario!
     The server successfully processed the request, but the client doesn't know.
     If the client retries, the operation might be executed twice!
    """)


def demo_4_server_crashed():
    """
    Demo 4: Server crashed while processing.

    DDIA: "Scenario 4: Server received request, crashed while processing
           Client ────────────► Server 💥
           (May or may not have completed. Impossible to tell.)"
    """
    print_header("SCENARIO 4: Server Crashed Mid-Processing")
    print("""
    The client sends a request, the server receives it and starts processing,
    but the server crashes before completing the request.

    From the client's perspective: No response (timeout)

    ⚠️  DANGER: We don't know if the operation was partially completed!
    """)

    server = SimpleServer("SERVER")
    network = NetworkSimulator(NetworkFailureType.SERVER_CRASHED, failure_probability=1.0)
    client = Client("CLIENT", timeout=1.0)

    print("  📤 Client sends request: 'TRANSFER $100 from account A to B'")
    print("  ⏳ Waiting for response (timeout=1.0s)...")

    response = client.send_request_with_timeout(network, server, "TRANSFER $100 from account A to B")

    if response is None:
        print("  ❌ TIMEOUT: No response received after 1.0s")
        print(f"  💥 Server crashed! (or is unreachable)")
        print(f"  ❓ Did the transfer complete? We don't know!")
        print(f"  ❓ Is the money deducted from A? We don't know!")
        print(f"  ❓ Is the money added to B? We don't know!")
    else:
        print(f"  ✅ Response: {response.result}")

    print("""
  💡 KEY INSIGHT:
     This is the most dangerous scenario for financial systems!
     We don't know if the operation was partially completed.

     Solutions:
       1. Idempotent operations (safe to retry)
       2. Distributed transactions (2-phase commit)
       3. Event sourcing (replay to recover state)
    """)


def demo_5_all_scenarios_look_identical():
    """
    Demo 5: Show that all four scenarios produce the same observable outcome.

    DDIA: "From the client's perspective, all four scenarios look identical:
           no response. The client has no way to distinguish them."
    """
    print_header("ALL SCENARIOS LOOK IDENTICAL")
    print("""
    This is the fundamental problem with distributed systems.
    When you don't receive a response, you cannot tell which of the four
    scenarios occurred. All you know is: no response.
    """)

    scenarios = [
        (NetworkFailureType.REQUEST_LOST, "Request Lost"),
        (NetworkFailureType.SERVER_SLOW, "Server Slow"),
        (NetworkFailureType.RESPONSE_LOST, "Response Lost"),
        (NetworkFailureType.SERVER_CRASHED, "Server Crashed"),
    ]

    print(f"\n  {'Scenario':<20} {'Client Observes':<30} {'Server State':<30}")
    print(f"  {'─'*70}")

    for failure_type, scenario_name in scenarios:
        server = SimpleServer("SERVER")
        network = NetworkSimulator(failure_type, failure_probability=1.0)
        client = Client("CLIENT", timeout=1.0)

        response = client.send_request_with_timeout(network, server, "INSERT data")

        client_observes = "❌ TIMEOUT (no response)" if response is None else "✅ Response received"
        server_state = f"Processed: {server.requests_processed} requests"

        print(f"  {scenario_name:<20} {client_observes:<30} {server_state:<30}")

    print("""
  💡 KEY INSIGHT:
     The client's observable outcome is the same for all four scenarios:
     TIMEOUT (no response).

     This is why distributed systems are fundamentally harder than
     single-machine systems. You must design for this ambiguity!
    """)


def demo_6_retry_problem():
    """
    Demo 6: Show why retrying is dangerous.

    If you retry after a timeout, you might execute the operation twice!
    """
    print_header("THE RETRY PROBLEM")
    print("""
    When you get a timeout, your first instinct is to retry.
    But if the response was lost (Scenario 3), retrying causes the
    operation to execute twice!
    """)

    print("\n  Scenario: Response Lost (but we don't know it)")
    print("  ─" * 60)

    server = SimpleServer("SERVER")
    network = NetworkSimulator(NetworkFailureType.RESPONSE_LOST, failure_probability=1.0)
    client = Client("CLIENT", timeout=1.0)

    print("\n  Attempt 1:")
    print("    📤 Client sends: 'DEBIT $50 from account'")
    response1 = client.send_request_with_timeout(network, server, "DEBIT $50 from account")
    print(f"    ❌ TIMEOUT (response was lost, but we don't know it)")
    print(f"    💾 Server storage: {server.storage}")

    print("\n  Attempt 2 (retry):")
    print("    📤 Client sends: 'DEBIT $50 from account' (RETRY)")
    response2 = client.send_request_with_timeout(network, server, "DEBIT $50 from account")
    print(f"    ❌ TIMEOUT again")
    print(f"    💾 Server storage: {server.storage}")

    print(f"\n  ⚠️  PROBLEM:")
    print(f"     Server processed: {server.requests_processed} requests")
    print(f"     But we only intended to debit once!")
    print(f"     The account was debited TWICE!")

    print("""
  💡 SOLUTION: Idempotent Operations

     Make operations idempotent so retrying is safe:
       • Include a unique request ID
       • Server checks if request was already processed
       • If yes, return cached response without re-executing

     Example:
       Request: {id: "req-12345", operation: "DEBIT $50"}
       Server: "I've already processed req-12345, returning cached response"
    """)


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 80)
    print("  EXERCISE 1: NETWORK FAILURES — THE AMBIGUITY PROBLEM")
    print("  DDIA Chapter 8: 'What Can Go Wrong with a Network Request'")
    print("=" * 80)
    print("""
  When you send a request and don't receive a response, you cannot distinguish
  between multiple failure scenarios. This exercise demonstrates all four
  scenarios and shows why they're indistinguishable from the client's perspective.
    """)

    demo_1_request_lost()
    demo_2_server_slow()
    demo_3_response_lost()
    demo_4_server_crashed()
    demo_5_all_scenarios_look_identical()
    demo_6_retry_problem()

    print("\n" + "=" * 80)
    print("  EXERCISE 1 COMPLETE ✅")
    print("=" * 80)
    print("""
  Key Takeaways:

  1. 🔴 You CANNOT distinguish between 4 different failure scenarios
  2. 🔴 All four produce the same observable outcome: TIMEOUT
  3. 🔴 Retrying is dangerous (might execute operation twice)
  4. ✅ Solution: Make operations idempotent with request IDs
  5. ✅ Solution: Use distributed transactions or event sourcing

  Next: Run 02_network_partitions.py to learn about network partitions
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
