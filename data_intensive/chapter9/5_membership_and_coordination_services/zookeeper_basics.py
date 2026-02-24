"""
ZooKeeper Basics: Fundamental Operations

This module demonstrates basic ZooKeeper operations:
- Creating nodes
- Reading nodes
- Deleting nodes
- Ephemeral nodes
- Watches

Note: This uses the Kazoo library (Python ZooKeeper client).
Install with: pip install kazoo
"""

from kazoo.client import KazooClient
from kazoo.exceptions import NodeExistsError, NoNodeError
import time
import json


class ZooKeeperBasics:
    """Basic ZooKeeper operations."""

    def __init__(self, hosts="127.0.0.1:2181"):
        """Initialize ZooKeeper client."""
        self.zk = KazooClient(hosts=hosts)
        self.zk.start()

    def create_node(self, path, data=None, ephemeral=False):
        """
        Create a ZNode.

        Args:
            path: Path to the node (e.g., "/config/database_url")
            data: Data to store (bytes or string)
            ephemeral: If True, node is deleted when client disconnects

        Returns:
            Path of created node
        """
        if isinstance(data, str):
            data = data.encode()

        try:
            created_path = self.zk.create(path, data, ephemeral=ephemeral)
            print(f"✓ Created node: {created_path}")
            return created_path
        except NodeExistsError:
            print(f"✗ Node already exists: {path}")
            return None

    def read_node(self, path):
        """
        Read data from a ZNode.

        Args:
            path: Path to the node

        Returns:
            Tuple of (data, stat) where stat contains metadata
        """
        try:
            data, stat = self.zk.get(path)
            print(f"✓ Read node: {path}")
            print(f"  Data: {data.decode()}")
            print(f"  Version: {stat.version}")
            print(f"  Created: {stat.ctime}")
            print(f"  Modified: {stat.mtime}")
            return data, stat
        except NoNodeError:
            print(f"✗ Node not found: {path}")
            return None, None

    def update_node(self, path, data):
        """
        Update data in a ZNode.

        Args:
            path: Path to the node
            data: New data (bytes or string)

        Returns:
            New stat
        """
        if isinstance(data, str):
            data = data.encode()

        try:
            stat = self.zk.set(path, data)
            print(f"✓ Updated node: {path}")
            print(f"  New version: {stat.version}")
            return stat
        except NoNodeError:
            print(f"✗ Node not found: {path}")
            return None

    def delete_node(self, path):
        """
        Delete a ZNode.

        Args:
            path: Path to the node

        Returns:
            True if deleted, False otherwise
        """
        try:
            self.zk.delete(path)
            print(f"✓ Deleted node: {path}")
            return True
        except NoNodeError:
            print(f"✗ Node not found: {path}")
            return False

    def list_children(self, path):
        """
        List children of a ZNode.

        Args:
            path: Path to the parent node

        Returns:
            List of child node names
        """
        try:
            children = self.zk.get_children(path)
            print(f"✓ Children of {path}:")
            for child in children:
                print(f"  - {child}")
            return children
        except NoNodeError:
            print(f"✗ Node not found: {path}")
            return []

    def watch_node(self, path, callback):
        """
        Watch a ZNode for changes.

        Args:
            path: Path to the node
            callback: Function to call when node changes

        Note: Watches are one-time only. Re-register after firing.
        """
        def on_change(event):
            print(f"✓ Watch fired for {path}: {event}")
            callback(event)

        try:
            self.zk.exists(path, watch=on_change)
            print(f"✓ Watching node: {path}")
        except NoNodeError:
            print(f"✗ Node not found: {path}")

    def ensure_path(self, path):
        """
        Ensure a path exists, creating parent nodes if needed.

        Args:
            path: Path to ensure exists
        """
        self.zk.ensure_path(path)
        print(f"✓ Ensured path: {path}")

    def close(self):
        """Close the ZooKeeper connection."""
        self.zk.stop()
        print("✓ Closed ZooKeeper connection")


def example_basic_operations():
    """Example: Basic CRUD operations."""
    print("\n" + "="*60)
    print("Example 1: Basic CRUD Operations")
    print("="*60)

    zk = ZooKeeperBasics()

    # Ensure path exists
    zk.ensure_path("/examples")

    # Create a node
    zk.create_node("/examples/config", "database_url=localhost:5432")

    # Read the node
    zk.read_node("/examples/config")

    # Update the node
    zk.update_node("/examples/config", "database_url=localhost:5433")

    # Read again
    zk.read_node("/examples/config")

    # Delete the node
    zk.delete_node("/examples/config")

    zk.close()


def example_ephemeral_nodes():
    """Example: Ephemeral nodes for failure detection."""
    print("\n" + "="*60)
    print("Example 2: Ephemeral Nodes")
    print("="*60)

    zk = ZooKeeperBasics()
    zk.ensure_path("/services")

    # Create an ephemeral node
    print("\nCreating ephemeral node...")
    zk.create_node("/services/database", "localhost:5432", ephemeral=True)

    # Verify it exists
    zk.read_node("/services/database")

    # Simulate process running
    print("\nProcess is running (ephemeral node exists)...")
    time.sleep(2)

    # When we close the connection, the ephemeral node is deleted
    print("\nClosing connection (simulating process crash)...")
    zk.close()

    # Reconnect and verify node is gone
    print("\nReconnecting to verify node was deleted...")
    zk = ZooKeeperBasics()
    data, stat = zk.read_node("/services/database")
    if data is None:
        print("✓ Ephemeral node was automatically deleted!")

    zk.close()


def example_watches():
    """Example: Watching nodes for changes."""
    print("\n" + "="*60)
    print("Example 3: Watches")
    print("="*60)

    zk = ZooKeeperBasics()
    zk.ensure_path("/config")

    # Create a node
    zk.create_node("/config/setting", "value1")

    # Watch for changes
    def on_change(event):
        print(f"  → Callback: Node changed! Event: {event}")
        # Re-read the data
        data, _ = zk.read_node("/config/setting")

    zk.watch_node("/config/setting", on_change)

    # Update the node (should trigger the watch)
    print("\nUpdating node (should trigger watch)...")
    zk.update_node("/config/setting", "value2")

    # Wait for watch to fire
    time.sleep(1)

    # Clean up
    zk.delete_node("/config/setting")
    zk.close()


def example_list_children():
    """Example: Listing children of a node."""
    print("\n" + "="*60)
    print("Example 4: Listing Children")
    print("="*60)

    zk = ZooKeeperBasics()
    zk.ensure_path("/services/database")

    # Create multiple child nodes
    zk.create_node("/services/database/node1", "localhost:5432")
    zk.create_node("/services/database/node2", "localhost:5433")
    zk.create_node("/services/database/node3", "localhost:5434")

    # List children
    zk.list_children("/services/database")

    # Clean up
    zk.delete_node("/services/database/node1")
    zk.delete_node("/services/database/node2")
    zk.delete_node("/services/database/node3")
    zk.close()


def example_json_data():
    """Example: Storing JSON data in nodes."""
    print("\n" + "="*60)
    print("Example 5: JSON Data")
    print("="*60)

    zk = ZooKeeperBasics()
    zk.ensure_path("/config")

    # Store JSON data
    config = {
        "database": "localhost:5432",
        "cache": "localhost:6379",
        "timeout": 30
    }
    config_json = json.dumps(config)
    zk.create_node("/config/app", config_json)

    # Read and parse JSON
    data, _ = zk.read_node("/config/app")
    if data:
        parsed = json.loads(data.decode())
        print(f"  Parsed config: {parsed}")

    zk.delete_node("/config/app")
    zk.close()


if __name__ == "__main__":
    print("\n" + "="*60)
    print("ZooKeeper Basics Examples")
    print("="*60)
    print("\nNote: These examples assume ZooKeeper is running on localhost:2181")
    print("Start ZooKeeper with: zkServer.sh start")

    try:
        example_basic_operations()
        example_ephemeral_nodes()
        example_watches()
        example_list_children()
        example_json_data()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("Make sure ZooKeeper is running on localhost:2181")
