"""
Leader Election with ZooKeeper

This module demonstrates how to implement leader election using ZooKeeper.

Key concepts:
- Ephemeral nodes for automatic failure detection
- Watches for reactive updates
- Linearizable writes for consistency

Pattern:
1. All candidates try to create /election/leader (ephemeral)
2. Only one succeeds (linearizable write)
3. That node is the leader
4. Other nodes watch /election/leader
5. If leader crashes → node is deleted → watch fires → new election
"""

from kazoo.client import KazooClient
from kazoo.exceptions import NodeExistsError, NoNodeError
import time
import threading
import json


class LeaderElection:
    """Implement leader election using ZooKeeper."""

    def __init__(self, node_id, hosts="127.0.0.1:2181"):
        """
        Initialize leader election.

        Args:
            node_id: Unique identifier for this node
            hosts: ZooKeeper hosts
        """
        self.node_id = node_id
        self.zk = KazooClient(hosts=hosts)
        self.zk.start()
        self.is_leader = False
        self.leader_id = None
        self.election_path = "/election/leader"

    def become_leader(self):
        """
        Try to become the leader.

        Returns:
            True if successful, False otherwise
        """
        leader_data = json.dumps({
            "node_id": self.node_id,
            "timestamp": time.time()
        }).encode()

        try:
            # Try to create the leader node (ephemeral)
            self.zk.create(self.election_path, leader_data, ephemeral=True)
            self.is_leader = True
            self.leader_id = self.node_id
            print(f"✓ [{self.node_id}] Became leader!")
            return True
        except NodeExistsError:
            # Someone else is the leader
            print(f"✗ [{self.node_id}] Someone else is the leader")
            self.is_leader = False
            return False

    def watch_leader(self):
        """
        Watch for leader changes.

        When the leader node is deleted (leader crashed), this fires.
        """
        def on_leader_change(event):
            print(f"\n! [{self.node_id}] Leader changed! Event: {event}")
            self.is_leader = False
            self.leader_id = None

            # Try to become the new leader
            time.sleep(0.1)  # Small delay to avoid thundering herd
            self.become_leader()

            # Re-register the watch
            self.watch_leader()

        try:
            self.zk.exists(self.election_path, watch=on_leader_change)
            print(f"  [{self.node_id}] Watching for leader changes...")
        except NoNodeError:
            print(f"  [{self.node_id}] Leader node doesn't exist yet")

    def get_leader(self):
        """
        Get the current leader.

        Returns:
            Leader node ID or None
        """
        try:
            data, _ = self.zk.get(self.election_path)
            leader_info = json.loads(data.decode())
            return leader_info["node_id"]
        except NoNodeError:
            return None

    def run_election(self):
        """
        Run the leader election process.

        This is the main election loop:
        1. Try to become leader
        2. If successful, do leader work
        3. If not, watch for leader changes
        """
        print(f"\n[{self.node_id}] Starting election...")

        if self.become_leader():
            # I'm the leader, watch for my own deletion
            self.watch_leader()
        else:
            # I'm not the leader, watch for leader changes
            self.watch_leader()

    def do_leader_work(self, duration=5):
        """
        Simulate leader doing work.

        Args:
            duration: How long to do work (seconds)
        """
        if not self.is_leader:
            print(f"✗ [{self.node_id}] Not the leader, cannot do leader work")
            return

        print(f"\n[{self.node_id}] Doing leader work for {duration} seconds...")
        start = time.time()
        while time.time() - start < duration and self.is_leader:
            print(f"  [{self.node_id}] Leader work... (still leader: {self.is_leader})")
            time.sleep(1)

        if self.is_leader:
            print(f"  [{self.node_id}] Finished leader work")
        else:
            print(f"  [{self.node_id}] Lost leadership during work!")

    def close(self):
        """Close the ZooKeeper connection."""
        self.zk.stop()
        print(f"✓ [{self.node_id}] Closed ZooKeeper connection")


def example_simple_election():
    """Example: Simple leader election with 3 nodes."""
    print("\n" + "="*60)
    print("Example 1: Simple Leader Election")
    print("="*60)

    # Create 3 nodes
    nodes = [
        LeaderElection("node1"),
        LeaderElection("node2"),
        LeaderElection("node3")
    ]

    # All nodes try to become leader
    print("\nAll nodes trying to become leader...")
    for node in nodes:
        node.run_election()

    # Check who is the leader
    time.sleep(1)
    print("\nCurrent leader:")
    for node in nodes:
        leader = node.get_leader()
        print(f"  [{node.node_id}] sees leader: {leader}")

    # Clean up
    for node in nodes:
        node.close()


def example_leader_failure():
    """Example: Leader failure and re-election."""
    print("\n" + "="*60)
    print("Example 2: Leader Failure and Re-election")
    print("="*60)

    # Create 3 nodes
    nodes = [
        LeaderElection("node1"),
        LeaderElection("node2"),
        LeaderElection("node3")
    ]

    # All nodes try to become leader
    print("\nAll nodes trying to become leader...")
    for node in nodes:
        node.run_election()

    time.sleep(1)

    # Find the leader
    leader_node = None
    for node in nodes:
        if node.is_leader:
            leader_node = node
            break

    if leader_node:
        print(f"\n✓ Current leader: {leader_node.node_id}")

        # Simulate leader failure
        print(f"\n! Simulating leader failure (closing {leader_node.node_id})...")
        leader_node.close()

        # Wait for re-election
        print("\nWaiting for re-election...")
        time.sleep(2)

        # Check new leader
        print("\nNew leader:")
        for node in nodes:
            if node.is_leader:
                print(f"  ✓ {node.node_id} is the new leader!")

    # Clean up
    for node in nodes:
        if node.zk.connected:
            node.close()


def example_leader_work():
    """Example: Leader doing work."""
    print("\n" + "="*60)
    print("Example 3: Leader Doing Work")
    print("="*60)

    # Create 2 nodes
    nodes = [
        LeaderElection("node1"),
        LeaderElection("node2")
    ]

    # Run election
    print("\nRunning election...")
    for node in nodes:
        node.run_election()

    time.sleep(1)

    # Leader does work
    print("\nLeader doing work...")
    for node in nodes:
        if node.is_leader:
            node.do_leader_work(duration=3)

    # Clean up
    for node in nodes:
        node.close()


def example_concurrent_election():
    """Example: Concurrent election with multiple nodes."""
    print("\n" + "="*60)
    print("Example 4: Concurrent Election")
    print("="*60)

    # Create 5 nodes
    nodes = [LeaderElection(f"node{i}") for i in range(1, 6)]

    # Run election concurrently
    print("\nRunning concurrent election...")
    threads = []
    for node in nodes:
        thread = threading.Thread(target=node.run_election)
        threads.append(thread)
        thread.start()

    # Wait for all threads
    for thread in threads:
        thread.join()

    time.sleep(1)

    # Check results
    print("\nElection results:")
    leader_count = 0
    for node in nodes:
        if node.is_leader:
            print(f"  ✓ {node.node_id} is the leader")
            leader_count += 1
        else:
            print(f"  - {node.node_id} is a follower")

    if leader_count == 1:
        print(f"\n✓ Exactly one leader elected!")
    else:
        print(f"\n✗ ERROR: {leader_count} leaders elected (should be 1)!")

    # Clean up
    for node in nodes:
        node.close()


if __name__ == "__main__":
    print("\n" + "="*60)
    print("Leader Election Examples")
    print("="*60)
    print("\nNote: These examples assume ZooKeeper is running on localhost:2181")
    print("Start ZooKeeper with: zkServer.sh start")

    try:
        example_simple_election()
        example_leader_failure()
        example_leader_work()
        example_concurrent_election()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("Make sure ZooKeeper is running on localhost:2181")
