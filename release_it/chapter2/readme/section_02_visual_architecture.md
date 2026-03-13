# Section 2: Visual Architecture / Concept Map

## Visualization 1: Cascade Failure Timeline

This visualization shows how a single exception propagates through shared resources over time.

```python
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

fig, axes = plt.subplots(2, 2, figsize=(16, 12))
fig.suptitle('Chapter 2: Cascading Failure — Visual Deep Dive', fontsize=16, fontweight='bold')

# ──────────────────────────────────────────
# Plot 1: Resource Utilization Over Time
# ──────────────────────────────────────────
ax1 = axes[0, 0]
time = np.arange(0, 65, 1)

# Simulate resource utilization curves
thread_util = np.clip(20 + 80 * (1 / (1 + np.exp(-0.3 * (time - 10)))), 0, 100)
conn_util = np.clip(15 + 85 * (1 / (1 + np.exp(-0.4 * (time - 15)))), 0, 100)
queue_depth = np.clip(0 + 500 * (1 / (1 + np.exp(-0.2 * (time - 20)))), 0, 500)
throughput = np.clip(100 - 100 * (1 / (1 + np.exp(-0.3 * (time - 12)))), 0, 100)

ax1.plot(time, thread_util, 'r-', linewidth=2, label='Thread Pool %')
ax1.plot(time, conn_util, 'b-', linewidth=2, label='Connection Pool %')
ax1.plot(time, throughput, 'g-', linewidth=2, label='Throughput (req/s)')
ax1.axvline(x=0, color='orange', linestyle='--', alpha=0.7, label='Exception Thrown')
ax1.axvline(x=10, color='red', linestyle='--', alpha=0.5)
ax1.axvline(x=30, color='darkred', linestyle='--', alpha=0.5)
ax1.axvspan(10, 30, alpha=0.1, color='red')
ax1.axvspan(30, 65, alpha=0.2, color='red')

ax1.set_xlabel('Time (seconds)')
ax1.set_ylabel('Utilization %')
ax1.set_title('Resource Utilization During Cascade')
ax1.legend(loc='center right', fontsize=8)
ax1.set_ylim(0, 110)
ax1.annotate('Thread pool\nexhausted', xy=(10, 100), fontsize=8,
            xytext=(15, 85), arrowprops=dict(arrowstyle='->', color='red'))
ax1.annotate('Total\noutage', xy=(30, 0), fontsize=8,
            xytext=(35, 30), arrowprops=dict(arrowstyle='->', color='darkred'))

# ──────────────────────────────────────────
# Plot 2: Cascade Dependency Graph
# ──────────────────────────────────────────
ax2 = axes[0, 1]
ax2.set_xlim(0, 10)
ax2.set_ylim(0, 10)
ax2.set_aspect('equal')
ax2.set_title('Cascade Dependency Graph')
ax2.axis('off')

# Draw nodes
nodes = {
    'Exception': (5, 9),
    'Thread\nBlocked': (5, 7.2),
    'Thread Pool\nExhausted': (5, 5.4),
    'Connection\nPool Starved': (3, 3.5),
    'Request\nQueue Full': (7, 3.5),
    'Health Check\nFails': (3, 1.5),
    'Load Balancer\nRemoves': (7, 1.5),
    'TOTAL\nOUTAGE': (5, 0),
}

colors = {
    'Exception': '#FFA500',
    'Thread\nBlocked': '#FF8C00',
    'Thread Pool\nExhausted': '#FF4500',
    'Connection\nPool Starved': '#DC143C',
    'Request\nQueue Full': '#DC143C',
    'Health Check\nFails': '#8B0000',
    'Load Balancer\nRemoves': '#8B0000',
    'TOTAL\nOUTAGE': '#000000',
}

for label, (x, y) in nodes.items():
    color = colors[label]
    fontcolor = 'white' if color in ['#8B0000', '#000000'] else 'black'
    bbox = dict(boxstyle='round,pad=0.5', facecolor=color, alpha=0.8)
    ax2.text(x, y, label, ha='center', va='center', fontsize=7,
            fontweight='bold', color=fontcolor, bbox=bbox)

# Draw edges
edges = [
    ('Exception', 'Thread\nBlocked'),
    ('Thread\nBlocked', 'Thread Pool\nExhausted'),
    ('Thread Pool\nExhausted', 'Connection\nPool Starved'),
    ('Thread Pool\nExhausted', 'Request\nQueue Full'),
    ('Connection\nPool Starved', 'Health Check\nFails'),
    ('Request\nQueue Full', 'Load Balancer\nRemoves'),
    ('Health Check\nFails', 'TOTAL\nOUTAGE'),
    ('Load Balancer\nRemoves', 'TOTAL\nOUTAGE'),
]

for start_label, end_label in edges:
    sx, sy = nodes[start_label]
    ex, ey = nodes[end_label]
    ax2.annotate('', xy=(ex, ey + 0.5), xytext=(sx, sy - 0.5),
                arrowprops=dict(arrowstyle='->', color='red', lw=1.5))

# ──────────────────────────────────────────
# Plot 3: Thread States Over Time (Stacked)
# ──────────────────────────────────────────
ax3 = axes[1, 0]
total_threads = 50

active = np.clip(25 - 25 * (1 / (1 + np.exp(-0.5 * (time - 8)))), 0, 50)
blocked = np.clip(0 + 50 * (1 / (1 + np.exp(-0.3 * (time - 10)))), 0, 50)
idle = total_threads - active - blocked
idle = np.clip(idle, 0, 50)

ax3.stackplot(time, active, blocked, idle,
             labels=['Active (working)', 'Blocked (waiting)', 'Idle'],
             colors=['#2ecc71', '#e74c3c', '#95a5a6'], alpha=0.8)
ax3.set_xlabel('Time (seconds)')
ax3.set_ylabel('Thread Count')
ax3.set_title('Thread Pool State Transition')
ax3.legend(loc='upper right', fontsize=8)
ax3.set_ylim(0, total_threads + 5)
ax3.axvline(x=0, color='orange', linestyle='--', alpha=0.7)

# ──────────────────────────────────────────
# Plot 4: Latency Distribution Before/After
# ──────────────────────────────────────────
ax4 = axes[1, 1]

# Normal latency: mostly fast with a small tail
np.random.seed(42)
normal_latency = np.random.exponential(50, 1000)  # ms
normal_latency = np.clip(normal_latency, 5, 500)

# Cascade latency: bimodal — some fast, most timeout
cascade_fast = np.random.exponential(50, 200)
cascade_timeout = np.random.normal(30000, 2000, 800)  # 30s timeout
cascade_latency = np.concatenate([cascade_fast, cascade_timeout])

ax4.hist(normal_latency, bins=50, alpha=0.6, color='#2ecc71', label='Normal (p99=250ms)', density=True)
ax4.hist(cascade_latency / 1000, bins=50, alpha=0.6, color='#e74c3c', label='Cascade (p99=30s)', density=True)
ax4.set_xlabel('Latency (seconds)')
ax4.set_ylabel('Density')
ax4.set_title('Latency Distribution: Normal vs Cascade')
ax4.legend(fontsize=8)
ax4.set_xlim(0, 35)

plt.tight_layout()
plt.savefig('cascade_failure_visualization.png', dpi=150, bbox_inches='tight')
plt.show()
print("✅ Saved: cascade_failure_visualization.png")
```

## Visualization 2: The Monitoring Blindspot

```python
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

fig, axes = plt.subplots(1, 2, figsize=(14, 6))
fig.suptitle('The Monitoring Blindspot: What You See vs Reality', fontsize=14, fontweight='bold')

# ──────────────────────────────────────────
# Left: What Monitoring Shows
# ──────────────────────────────────────────
ax1 = axes[0]
metrics = ['CPU', 'Memory', 'Disk I/O', 'Network', 'Process\nAlive']
values = [5, 70, 10, 15, 100]
bar_colors = ['#2ecc71', '#f1c40f', '#2ecc71', '#2ecc71', '#2ecc71']

bars = ax1.barh(metrics, values, color=bar_colors, edgecolor='white', height=0.6)
ax1.set_xlim(0, 110)
ax1.set_title('📊 What Monitoring Shows\n(Everything looks GREEN)', color='green', fontsize=12)
ax1.set_xlabel('Utilization %')

for bar, val in zip(bars, values):
    ax1.text(val + 2, bar.get_y() + bar.get_height()/2, f'{val}%',
            va='center', fontweight='bold', fontsize=10)

# Add a big green checkmark
ax1.text(80, 2, '✅', fontsize=40, ha='center', va='center', alpha=0.3)

# ──────────────────────────────────────────
# Right: What's Actually Happening
# ──────────────────────────────────────────
ax2 = axes[1]
real_metrics = ['Throughput', 'Queue\nDepth', 'Thread Pool\nAvailable', 'Connection\nPool Free', 'User Error\nRate']
real_values = [0, 95, 0, 0, 100]
real_colors = ['#e74c3c', '#e74c3c', '#e74c3c', '#e74c3c', '#e74c3c']

bars2 = ax2.barh(real_metrics, real_values, color=real_colors, edgecolor='white', height=0.6)
ax2.set_xlim(0, 110)
ax2.set_title('🔥 What\'s Actually Happening\n(System is DEAD)', color='red', fontsize=12)
ax2.set_xlabel('Value (normalized)')

labels2 = ['0 req/s', '500+', '0 free', '0 free', '100%']
for bar, val, label in zip(bars2, real_values, labels2):
    ax2.text(max(val, 5) + 2, bar.get_y() + bar.get_height()/2, label,
            va='center', fontweight='bold', fontsize=10, color='red')

# Add a big red X
ax2.text(80, 2, '❌', fontsize=40, ha='center', va='center', alpha=0.3)

plt.tight_layout()
plt.savefig('monitoring_blindspot.png', dpi=150, bbox_inches='tight')
plt.show()
print("✅ Saved: monitoring_blindspot.png")
```

## Visualization 3: Cascade Propagation in Microservices

```python
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

fig, ax = plt.subplots(figsize=(14, 8))
ax.set_xlim(0, 14)
ax.set_ylim(0, 10)
ax.set_aspect('equal')
ax.axis('off')
ax.set_title('Cascade Propagation in a Microservices Architecture',
            fontsize=14, fontweight='bold')

# Service chain: A → B → C → D (database)
services = {
    'API\nGateway': (2, 7),
    'Service A\n(Orders)': (5, 8.5),
    'Service B\n(Inventory)': (8, 8.5),
    'Service C\n(Payments)': (11, 8.5),
    'Service D\n(Users)': (5, 5.5),
    'Service E\n(Shipping)': (8, 5.5),
    'Database': (11, 5.5),
    'Cache\n(Redis)': (11, 2.5),
}

# State: healthy, degraded, dead
states = {
    'API\nGateway': 'dead',
    'Service A\n(Orders)': 'dead',
    'Service B\n(Inventory)': 'degraded',
    'Service C\n(Payments)': 'dead',
    'Service D\n(Users)': 'degraded',
    'Service E\n(Shipping)': 'healthy',
    'Database': 'dead',
    'Cache\n(Redis)': 'healthy',
}

state_colors = {
    'healthy': '#2ecc71',
    'degraded': '#f39c12',
    'dead': '#e74c3c',
}

for label, (x, y) in services.items():
    color = state_colors[states[label]]
    bbox = dict(boxstyle='round,pad=0.6', facecolor=color, alpha=0.85, edgecolor='white', linewidth=2)
    fontcolor = 'white' if states[label] == 'dead' else 'black'
    ax.text(x, y, label, ha='center', va='center', fontsize=9,
           fontweight='bold', color=fontcolor, bbox=bbox)

# Draw connections with failure indicators
connections = [
    ('API\nGateway', 'Service A\n(Orders)', 'dead'),
    ('API\nGateway', 'Service D\n(Users)', 'degraded'),
    ('Service A\n(Orders)', 'Service B\n(Inventory)', 'degraded'),
    ('Service A\n(Orders)', 'Service C\n(Payments)', 'dead'),
    ('Service B\n(Inventory)', 'Database', 'dead'),
    ('Service C\n(Payments)', 'Database', 'dead'),
    ('Service D\n(Users)', 'Service E\n(Shipping)', 'healthy'),
    ('Service D\n(Users)', 'Cache\n(Redis)', 'healthy'),
    ('Service E\n(Shipping)', 'Database', 'dead'),
]

line_colors = {'healthy': '#2ecc71', 'degraded': '#f39c12', 'dead': '#e74c3c'}

for start, end, state in connections:
    sx, sy = services[start]
    ex, ey = services[end]
    ax.annotate('', xy=(ex, ey + 0.5), xytext=(sx, sy - 0.5),
               arrowprops=dict(arrowstyle='->', color=line_colors[state], lw=2, alpha=0.7))

# Legend
legend_elements = [
    mpatches.Patch(facecolor='#2ecc71', label='Healthy'),
    mpatches.Patch(facecolor='#f39c12', label='Degraded'),
    mpatches.Patch(facecolor='#e74c3c', label='Dead'),
]
ax.legend(handles=legend_elements, loc='lower left', fontsize=10)

# Annotation: root cause
ax.annotate('⚡ ROOT CAUSE:\nDatabase connection\npool exhausted',
           xy=(11, 5.5), xytext=(11, 3.8),
           fontsize=9, color='red', fontweight='bold', ha='center',
           arrowprops=dict(arrowstyle='->', color='red', lw=2))

# Timeline annotation
ax.text(7, 1, '⏱ T+0: DB slow → T+10s: Connection pool exhausted → T+30s: Service C dead → T+45s: Full cascade',
       fontsize=9, ha='center', style='italic',
       bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.9))

plt.tight_layout()
plt.savefig('microservices_cascade.png', dpi=150, bbox_inches='tight')
plt.show()
print("✅ Saved: microservices_cascade.png")
```

---

## Key Visual Takeaways

| Visualization | What It Shows | Staff-Level Insight |
|---|---|---|
| Resource Utilization | How fast resources exhaust during cascade | The sigmoid curve — you have **seconds**, not minutes, once the cascade starts |
| Thread Pool States | Active → Blocked transition is invisible to CPU metrics | Monitor **thread states**, not just thread counts |
| Monitoring Blindspot | Green dashboards during dead systems | Your health check must verify **useful work**, not just liveness |
| Microservices Cascade | One dead database kills everything upstream | **Bulkheads** and **circuit breakers** are the only defense |

---

[← Previous: Section 1](./section_01_core_concepts.md) | [Next: Section 3 — Code Examples →](./section_03_code_examples.md)
