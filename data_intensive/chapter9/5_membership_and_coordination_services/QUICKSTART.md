# Quick Start: Membership and Coordination Services

## Prerequisites

1. **Install ZooKeeper**
   ```bash
   # macOS
   brew install zookeeper

   # Ubuntu/Debian
   sudo apt-get install zookeeper

   # Or download from: https://zookeeper.apache.org/releases.html
   ```

2. **Install Python ZooKeeper client**
   ```bash
   pip install kazoo
   ```

3. **Start ZooKeeper**
   ```bash
   zkServer.sh start
   # Or on macOS with Homebrew:
   zkServer start
   ```

4. **Verify ZooKeeper is running**
   ```bash
   echo ruok | nc localhost 2181
   # Should respond with: imok
   ```

## Running the Examples

### Example 1: Basic Operations

```bash
python zookeeper_basics.py
```

**What it demonstrates:**
- Creating nodes
- Reading nodes
- Updating nodes
- Deleting nodes
- Listing children
- Watching nodes
- Storing JSON data

**Key concepts:**
- ZNodes are like files in a filesystem
- Ephemeral nodes are auto-deleted on disconnect
- Watches notify you of changes

### Example 2: Leader Election

```bash
python leader_election.py
```

**What it demonstrates:**
- Multiple nodes trying to become leader
- Only one succeeds (linearizable write)
- Other nodes watch for leader changes
- When leader crashes, new election is triggered
- Concurrent election with multiple nodes

**Key concepts:**
- Ephemeral nodes prevent zombie leaders
- Watches enable reactive re-election
- Majority prevents split-brain

### Example 3: Service Discovery

```bash
python service_discovery.py
```

**What it demonstrates:**
- Services registering themselves
- Clients discovering services
- Automatic cleanup when services crash
- Dynamic service discovery with watches
- Load balancing (round-robin)

**Key concepts:**
- Ephemeral nodes for automatic cleanup
- Watches for reactive updates
- Service registry pattern

### Example 4: Distributed Locks

```bash
python distributed_locks.py
```

**What it demonstrates:**
- Acquiring and releasing locks
- Multiple nodes contending for a lock
- Lock holder failure and automatic release
- Sequential access to shared resource
- Fencing tokens to prevent zombie writes

**Key concepts:**
- Ephemeral nodes for automatic lock release
- Watches for reactive lock acquisition
- Fencing tokens prevent data corruption

## Understanding the Output

### Successful Operations
```
✓ Created node: /config/database_url
✓ Read node: /config/database_url
✓ Updated node: /config/database_url
✓ Deleted node: /config/database_url
```

### Errors
```
✗ Node already exists: /config/database_url
✗ Node not found: /config/database_url
```

### Events
```
! Service change detected: WatchedEvent(type='CHANGED', state='CONNECTED', path='/services/database')
! Leader changed! Event: WatchedEvent(type='DELETED', state='CONNECTED', path='/election/leader')
```

## Common Issues

### Issue: "Connection refused"
**Solution:** Make sure ZooKeeper is running
```bash
zkServer.sh start
```

### Issue: "No module named 'kazoo'"
**Solution:** Install the Python client
```bash
pip install kazoo
```

### Issue: "Node already exists"
**Solution:** Clean up previous runs
```bash
# Connect to ZooKeeper CLI
zkCli.sh

# Delete nodes
deleteall /election
deleteall /services
deleteall /locks
deleteall /config
```

## Exploring ZooKeeper Manually

### Connect to ZooKeeper CLI
```bash
zkCli.sh
```

### Common Commands
```
# List children
ls /
ls /services

# Get node data
get /election/leader

# Create node
create /test "hello"

# Delete node
delete /test

# Watch for changes
stat /election/leader watch
```

## Next Steps

1. **Understand the concepts**
   - Read TEACHING_GUIDE.md for deep explanations
   - Understand ephemeral nodes, watches, and linearizability

2. **Run the examples**
   - Start with zookeeper_basics.py
   - Then try leader_election.py
   - Then service_discovery.py
   - Finally distributed_locks.py

3. **Modify the examples**
   - Add more nodes
   - Change timeouts
   - Add error handling
   - Implement your own patterns

4. **Real-world applications**
   - Kafka uses ZooKeeper for broker coordination
   - HBase uses ZooKeeper for region server tracking
   - Hadoop uses ZooKeeper for NameNode HA

## Key Takeaways

1. **Ephemeral nodes** enable automatic failure detection
2. **Watches** enable reactive updates (no polling)
3. **Linearizable writes** ensure consistency
4. **Serializable reads** are fast (but might be stale)
5. **ZooKeeper is not a database** — it's a coordination service

## Further Reading

- DDIA Chapter 9: "Consistency and Consensus"
- ZooKeeper documentation: https://zookeeper.apache.org/
- Kazoo documentation: https://kazoo.readthedocs.io/
