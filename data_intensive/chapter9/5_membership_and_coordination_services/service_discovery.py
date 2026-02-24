"""
Service Discovery with ZooKeeper

This module demonstrates how to implement service discovery using ZooKeeper.

Key concepts:
- Services register themselves with ephemeral nodes
- Clients watch for service changes
- Automatic cleanup when services crash

Pattern:
1. Service registers: create /services/database/node1 (ephemeral)
2. Service stores its address in the node data
3. Clients watch /services/database
4. When a service joins → watch fires → clients update routing
5. When a service crashes → node deleted → watch fires → clients update routing
"""

from kazoo.client import KazooClient
from kazoo.exceptions import NodeExistsError, NoNodeError
import time
import json
import threading


class ServiceRegistry:
    """Service registry using ZooKeeper."""

    def __init__(self, hosts="127.0.0.1:2181"):
        """Initialize service registry."""
        self.zk = KazooClient(hosts=hosts)
        self.zk.start()
        self.services_path = "/services"
        self.zk.ensure_path(self.services_path)

    def register_service(self, service_name, node_id, address, port):
        """
        Register a service instance.

        Args:
            service_name: Name of the service (e.g., "database")
            node_id: Unique identifier for this instance
            address: Host address (e.g., "localhost")
            port: Port number

        Returns:
            Path of registered node
        """
        service_path = f"{self.services_path}/{service_name}"
        self.zk.ensure_path(service_path)

        node_path = f"{service_path}/{node_id}"
        node_data = json.dumps({
            "node_id": node_id,
            "address": address,
            "port": port,
            "registered_at": time.time()
        }).encode()

        try:
            created_path = self.zk.create(node_path, node_data, ephemeral=True)
            print(f"✓ Registered {service_name}/{node_id} at {address}:{port}")
            return created_path
        except NodeExistsError:
            print(f"✗ Service already registered: {node_path}")
            return None

    def deregister_service(self, service_name, node_id):
        """
        Deregister a service instance.

        Args:
            service_name: Name of the service
            node_id: Unique identifier for this instance

        Returns:
            True if deregistered, False otherwise
        """
        node_path = f"{self.services_path}/{service_name}/{node_id}"
        try:
            self.zk.delete(node_path)
            print(f"✓ Deregistered {service_name}/{node_id}")
            return True
        except NoNodeError:
            print(f"✗ Service not found: {node_path}")
            return False

    def discover_services(self, service_name):
        """
        Discover all instances of a service.

        Args:
            service_name: Name of the service

        Returns:
            List of service instances
        """
        service_path = f"{self.services_path}/{service_name}"
        try:
            node_ids = self.zk.get_children(service_path)
            services = []
            for node_id in node_ids:
                node_path = f"{service_path}/{node_id}"
                data, _ = self.zk.get(node_path)
                service_info = json.loads(data.decode())
                services.append(service_info)
            return services
        except NoNodeError:
            print(f"✗ Service not found: {service_path}")
            return []

    def watch_services(self, service_name, callback):
        """
        Watch for changes in service instances.

        Args:
            service_name: Name of the service
            callback: Function to call when services change

        Note: Watches are one-time only. Re-register after firing.
        """
        service_path = f"{self.services_path}/{service_name}"

        def on_change(event):
            print(f"\n! Service change detected: {event}")
            services = self.discover_services(service_name)
            callback(services)
            # Re-register the watch
            self.watch_services(service_name, callback)

        try:
            self.zk.get_children(service_path, watch=on_change)
            print(f"✓ Watching service: {service_name}")
        except NoNodeError:
            print(f"✗ Service not found: {service_path}")

    def close(self):
        """Close the ZooKeeper connection."""
        self.zk.stop()
        print("✓ Closed ZooKeeper connection")


class ServiceClient:
    """Client that discovers and uses services."""

    def __init__(self, service_name, hosts="127.0.0.1:2181"):
        """Initialize service client."""
        self.service_name = service_name
        self.registry = ServiceRegistry(hosts)
        self.available_services = []
        self.current_index = 0

    def discover(self):
        """Discover available services."""
        self.available_services = self.registry.discover_services(self.service_name)
        print(f"\n✓ Discovered {len(self.available_services)} instances of {self.service_name}:")
        for service in self.available_services:
            print(f"  - {service['node_id']}: {service['address']}:{service['port']}")

    def watch(self):
        """Watch for service changes."""
        def on_services_change(services):
            self.available_services = services
            print(f"✓ Updated service list: {len(services)} instances available")

        self.registry.watch_services(self.service_name, on_services_change)

    def get_service(self):
        """
        Get a service instance (round-robin).

        Returns:
            Service instance or None
        """
        if not self.available_services:
            print(f"✗ No services available: {self.service_name}")
            return None

        service = self.available_services[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.available_services)
        return service

    def call_service(self):
        """Simulate calling a service."""
        service = self.get_service()
        if service:
            print(f"  → Calling {service['node_id']} at {service['address']}:{service['port']}")
            return service
        return None

    def close(self):
        """Close the client."""
        self.registry.close()


def example_service_registration():
    """Example: Service registration and discovery."""
    print("\n" + "="*60)
    print("Example 1: Service Registration and Discovery")
    print("="*60)

    registry = ServiceRegistry()

    # Register multiple database instances
    print("\nRegistering database services...")
    registry.register_service("database", "db1", "localhost", 5432)
    registry.register_service("database", "db2", "localhost", 5433)
    registry.register_service("database", "db3", "localhost", 5434)

    # Discover services
    print("\nDiscovering database services...")
    services = registry.discover_services("database")
    for service in services:
        print(f"  - {service['node_id']}: {service['address']}:{service['port']}")

    registry.close()


def example_service_failure():
    """Example: Service failure and automatic cleanup."""
    print("\n" + "="*60)
    print("Example 2: Service Failure and Automatic Cleanup")
    print("="*60)

    registry = ServiceRegistry()

    # Register a service
    print("\nRegistering service...")
    registry.register_service("cache", "cache1", "localhost", 6379)

    # Verify it's registered
    print("\nVerifying registration...")
    services = registry.discover_services("cache")
    print(f"  Found {len(services)} service(s)")

    # Simulate service failure (deregister)
    print("\nSimulating service failure...")
    registry.deregister_service("cache", "cache1")

    # Verify it's gone
    print("\nVerifying cleanup...")
    services = registry.discover_services("cache")
    print(f"  Found {len(services)} service(s)")

    registry.close()


def example_client_discovery():
    """Example: Client discovering and using services."""
    print("\n" + "="*60)
    print("Example 3: Client Discovery and Load Balancing")
    print("="*60)

    # Register services
    registry = ServiceRegistry()
    print("\nRegistering services...")
    registry.register_service("api", "api1", "localhost", 8001)
    registry.register_service("api", "api2", "localhost", 8002)
    registry.register_service("api", "api3", "localhost", 8003)

    # Client discovers and uses services
    client = ServiceClient("api")
    print("\nClient discovering services...")
    client.discover()

    # Simulate load balancing (round-robin)
    print("\nSimulating load balancing (round-robin)...")
    for i in range(6):
        print(f"Request {i+1}:")
        client.call_service()

    registry.close()
    client.close()


def example_dynamic_service_discovery():
    """Example: Dynamic service discovery with watches."""
    print("\n" + "="*60)
    print("Example 4: Dynamic Service Discovery")
    print("="*60)

    registry = ServiceRegistry()

    # Register initial services
    print("\nRegistering initial services...")
    registry.register_service("worker", "worker1", "localhost", 9001)
    registry.register_service("worker", "worker2", "localhost", 9002)

    # Client watches for changes
    client = ServiceClient("worker")
    print("\nClient watching for service changes...")
    client.discover()
    client.watch()

    # Simulate service changes
    print("\nSimulating service changes...")

    print("\n1. Adding new service...")
    registry.register_service("worker", "worker3", "localhost", 9003)
    time.sleep(1)

    print("\n2. Removing a service...")
    registry.deregister_service("worker", "worker1")
    time.sleep(1)

    print("\n3. Adding another service...")
    registry.register_service("worker", "worker4", "localhost", 9004)
    time.sleep(1)

    registry.close()
    client.close()


def example_multiple_service_types():
    """Example: Multiple service types."""
    print("\n" + "="*60)
    print("Example 5: Multiple Service Types")
    print("="*60)

    registry = ServiceRegistry()

    # Register different service types
    print("\nRegistering services...")
    registry.register_service("database", "db1", "localhost", 5432)
    registry.register_service("database", "db2", "localhost", 5433)
    registry.register_service("cache", "cache1", "localhost", 6379)
    registry.register_service("cache", "cache2", "localhost", 6380)
    registry.register_service("api", "api1", "localhost", 8001)

    # Discover each service type
    print("\nDiscovering services by type...")
    for service_type in ["database", "cache", "api"]:
        services = registry.discover_services(service_type)
        print(f"\n{service_type}:")
        for service in services:
            print(f"  - {service['node_id']}: {service['address']}:{service['port']}")

    registry.close()


if __name__ == "__main__":
    print("\n" + "="*60)
    print("Service Discovery Examples")
    print("="*60)
    print("\nNote: These examples assume ZooKeeper is running on localhost:2181")
    print("Start ZooKeeper with: zkServer.sh start")

    try:
        example_service_registration()
        example_service_failure()
        example_client_discovery()
        example_dynamic_service_discovery()
        example_multiple_service_types()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("Make sure ZooKeeper is running on localhost:2181")
