# Visualization Patterns by Topic Type

## Systems / Architecture Topics
Use `matplotlib` + `patches` for box-and-arrow diagrams
```python
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch

fig, ax = plt.subplots(1, 1, figsize=(12, 8))
ax.set_xlim(0, 10); ax.set_ylim(0, 10)

# Draw components as rectangles
box = mpatches.FancyBboxPatch((1, 4), 2, 1.5, boxstyle="round,pad=0.1",
    facecolor='#4A90D9', edgecolor='#2C5F8A', linewidth=2)
ax.add_patch(box)
ax.text(2, 4.75, "Component A", ha='center', va='center', color='white', fontweight='bold')

# Draw arrows
ax.annotate('', xy=(5, 4.75), xytext=(3, 4.75),
    arrowprops=dict(arrowstyle='->', color='#333', lw=2))

ax.axis('off')
plt.title("System Architecture: <Topic>", fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig("architecture.png", dpi=150, bbox_inches='tight')
```

## Graph / DAG Concepts (databases, dependency graphs)
```python
import networkx as nx
import matplotlib.pyplot as plt

G = nx.DiGraph()
G.add_edges_from([('A', 'B'), ('A', 'C'), ('B', 'D'), ('C', 'D')])

pos = nx.spring_layout(G, seed=42)
nx.draw(G, pos, with_labels=True, node_color='#4A90D9',
        node_size=2000, font_color='white', font_size=12,
        arrows=True, arrowsize=20, edge_color='#555')
plt.title("Dependency Graph")
plt.savefig("dag.png", dpi=150, bbox_inches='tight')
```

## Performance / Trade-off Comparisons
```python
import matplotlib.pyplot as plt
import numpy as np

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Left: Latency comparison
approaches = ['Naive', 'Optimized', 'Production']
latencies = [450, 120, 35]  # ms
colors = ['#E74C3C', '#F39C12', '#27AE60']
axes[0].bar(approaches, latencies, color=colors, edgecolor='black', linewidth=0.5)
axes[0].set_title('Latency Comparison (ms)', fontweight='bold')
axes[0].set_ylabel('Latency (ms)')
for i, v in enumerate(latencies):
    axes[0].text(i, v + 5, f'{v}ms', ha='center', fontweight='bold')

# Right: Trade-off radar (consistency vs availability vs partition)
# Use a radar/spider chart for CAP-style trade-offs
plt.tight_layout()
plt.savefig("tradeoffs.png", dpi=150, bbox_inches='tight')
```

## State Machines / Transitions
```python
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch

# Draw states as circles, transitions as labeled arrows
states = {'INIT': (1, 5), 'RUNNING': (4, 7), 'WAITING': (4, 3), 'DONE': (7, 5)}
transitions = [
    ('INIT', 'RUNNING', 'start()'),
    ('RUNNING', 'WAITING', 'block()'),
    ('WAITING', 'RUNNING', 'signal()'),
    ('RUNNING', 'DONE', 'finish()'),
]
# ... draw logic
```

## Timeline / Sequence Diagrams
```python
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

fig, ax = plt.subplots(figsize=(14, 8))
actors = ['Client', 'Load Balancer', 'Service A', 'Database']
# Draw vertical lifelines, horizontal message arrows
# ... draw logic
```

## Choosing the Right Visualization
| Topic Type | Best Library | Chart Type |
|---|---|---|
| System components | matplotlib patches | Box-and-arrow |
| Data flow | networkx | DAG / directed graph |
| Performance | matplotlib bar/line | Bar chart, log scale |
| State machines | matplotlib | Node-arc diagram |
| Sequence/protocol | matplotlib | Swimlane / sequence |
| Distribution | seaborn | Histogram, violin plot |
| CAP / trade-off space | matplotlib radar | Spider chart |
| Time-series | matplotlib line | Line chart with annotations |