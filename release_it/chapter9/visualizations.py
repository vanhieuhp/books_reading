"""
Control Plane Architecture Visualization
Run this script to generate architecture diagrams for Chapter 9
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# Set up the figure with dark background for modern look
plt.style.use('default')
fig, axes = plt.subplots(2, 2, figsize=(16, 14))
fig.suptitle('Control Plane Architecture - Release It! Chapter 9', fontsize=18, fontweight='bold', y=0.98)

# Color scheme
control_plane_color = '#4A90D9'
data_plane_color = '#50C878'
traffic_color = '#FF6B6B'
config_color = '#9B59B6'
discovery_color = '#F39C12'
deploy_color = '#1ABC9C'

# ============================================================
# Plot 1: High-Level Architecture
# ============================================================
ax1 = axes[0, 0]
ax1.set_facecolor('#f8f9fa')

# Control Plane box
cp_box = mpatches.FancyBboxPatch((0.1, 0.4), 0.8, 0.5, boxstyle="round,pad=0.02",
                                   facecolor=control_plane_color, edgecolor='#2c3e50', linewidth=2, alpha=0.85)
ax1.add_patch(cp_box)
ax1.text(0.5, 0.7, 'CONTROL PLANE', ha='center', va='center', fontsize=14, fontweight='bold', color='white')
ax1.text(0.5, 0.55, 'Service Discovery', ha='center', va='center', fontsize=10, color='white')
ax1.text(0.5, 0.47, 'Configuration Management', ha='center', va='center', fontsize=10, color='white')
ax1.text(0.5, 0.39, 'Deployment Orchestration', ha='center', va='center', fontsize=10, color='white')
ax1.text(0.5, 0.31, 'Traffic Management', ha='center', va='center', fontsize=10, color='white')

# Data Plane box
dp_box = mpatches.FancyBboxPatch((0.1, 0.08), 0.8, 0.22, boxstyle="round,pad=0.02",
                                   facecolor=data_plane_color, edgecolor='#2c3e50', linewidth=2, alpha=0.85)
ax1.add_patch(dp_box)
ax1.text(0.5, 0.22, 'DATA PLANE', ha='center', va='center', fontsize=12, fontweight='bold', color='white')
ax1.text(0.5, 0.13, 'User Traffic / Business Logic', ha='center', va='center', fontsize=10, color='white')

# Arrow
ax1.annotate('', xy=(0.5, 0.35), xytext=(0.5, 0.42),
             arrowprops=dict(arrowstyle='->', color='#2c3e50', lw=3))

ax1.set_xlim(0, 1)
ax1.set_ylim(0, 1)
ax1.axis('off')
ax1.set_title('Control Plane vs Data Plane', fontsize=13, fontweight='bold', pad=10)

# ============================================================
# Plot 2: Service Discovery Flow
# ============================================================
ax2 = axes[0, 1]
ax2.set_facecolor('#f8f9fa')

# Components - using rounded rectangles
components = [
    (0.08, 0.72, 'Client\nApp', '#E74C3C'),
    (0.38, 0.72, 'Service\nRegistry', discovery_color),
    (0.68, 0.72, 'Load\nBalancer', traffic_color),
    (0.88, 0.42, 'Service\nInstance\nB', data_plane_color),
    (0.58, 0.42, 'Service\nInstance\nA', data_plane_color),
    (0.28, 0.42, 'Service\nInstance\nC', data_plane_color),
]

for x, y, label, color in components:
    circle = plt.Circle((x, y), 0.09, color=color, ec='#2c3e50', linewidth=2, alpha=0.85)
    ax2.add_patch(circle)
    # Handle multiline text
    lines = label.split('\n')
    for i, line in enumerate(lines):
        ax2.text(x, y + 0.03 - (i * 0.06), line, ha='center', va='center', fontsize=8, color='white', fontweight='bold')

# Arrows with labels
ax2.annotate('', xy=(0.30, 0.72), xytext=(0.17, 0.72), arrowprops=dict(arrowstyle='->', color='#2c3e50', lw=2))
ax2.annotate('', xy=(0.60, 0.72), xytext=(0.47, 0.72), arrowprops=dict(arrowstyle='->', color='#2c3e50', lw=2))
ax2.annotate('', xy=(0.80, 0.52), xytext=(0.80, 0.62), arrowprops=dict(arrowstyle='->', color='#2c3e50', lw=2))
ax2.annotate('', xy=(0.64, 0.52), xytext=(0.64, 0.62), arrowprops=dict(arrowstyle='->', color='#2c3e50', lw=2))
ax2.annotate('', xy=(0.48, 0.52), xytext=(0.48, 0.62), arrowprops=dict(arrowstyle='->', color='#2c3e50', lw=2))

# Labels
ax2.text(0.12, 0.85, '1. Query', fontsize=9, fontweight='bold', color='#2c3e50')
ax2.text(0.42, 0.85, '2. Route', fontsize=9, fontweight='bold', color='#2c3e50')
ax2.text(0.85, 0.28, '3. Forward\nto healthy', fontsize=8, fontweight='bold', color='#2c3e50')

ax2.set_xlim(0, 1)
ax2.set_ylim(0.15, 1)
ax2.axis('off')
ax2.set_title('Service Discovery Flow', fontsize=13, fontweight='bold', pad=10)

# ============================================================
# Plot 3: Deployment Strategies Comparison
# ============================================================
ax3 = axes[1, 0]
ax3.set_facecolor('#f8f9fa')

strategies = ['Blue-Green', 'Rolling', 'Canary']
colors = [control_plane_color, deploy_color, traffic_color]
descriptions = [
    'Zero downtime\nInstant rollback\nDouble resource cost',
    'Incremental update\nNo extra resources\nSlower rollback',
    'Gradual exposure\nReal traffic testing\nRequires good metrics'
]

y_positions = [0.75, 0.42, 0.09]
for i, (strategy, y, color, desc) in enumerate(zip(strategies, y_positions, colors, descriptions)):
    rect = mpatches.FancyBboxPatch((0.05, y-0.12), 0.9, 0.22, boxstyle="round,pad=0.02",
                                     facecolor=color, edgecolor='#2c3e50', linewidth=2, alpha=0.85)
    ax3.add_patch(rect)
    ax3.text(0.5, y+0.04, strategy, ha='center', va='center', fontsize=12, fontweight='bold', color='white')
    ax3.text(0.5, y-0.07, desc, ha='center', va='center', fontsize=8, color='white')

# Add visual representation of strategies
# Blue-Green visual
ax3.text(0.5, -0.08, 'v1 (Blue) ← traffic → v2 (Green)', ha='center', fontsize=8, style='italic', color='#7f8c8d')

ax3.set_xlim(0, 1)
ax3.set_ylim(-0.25, 1)
ax3.axis('off')
ax3.set_title('Deployment Strategies Comparison', fontsize=13, fontweight='bold', pad=10)

# ============================================================
# Plot 4: Circuit Breaker States
# ============================================================
ax4 = axes[1, 1]
ax4.set_facecolor('#f8f9fa')

# States
states = ['CLOSED\n(Normal)', 'OPEN\n(Blocking)', 'HALF-OPEN\n(Test)']
x_positions = [0.15, 0.5, 0.85]
state_colors = ['#27AE60', '#E74C3C', '#F39C12']

for x, state, color in zip(x_positions, states, state_colors):
    circle = plt.Circle((x, 0.5), 0.13, color=color, ec='#2c3e50', linewidth=2, alpha=0.85)
    ax4.add_patch(circle)
    lines = state.split('\n')
    for i, line in enumerate(lines):
        ax4.text(x, 0.52 - (i * 0.06), line, ha='center', va='center', fontsize=9, fontweight='bold', color='white')

# Transitions - solid for normal, dashed for recovery
ax4.annotate('', xy=(0.36, 0.5), xytext=(0.28, 0.5),
             arrowprops=dict(arrowstyle='->', color='#2c3e50', lw=2))
ax4.annotate('', xy=(0.64, 0.5), xytext=(0.72, 0.5),
             arrowprops=dict(arrowstyle='->', color='#2c3e50', lw=2))
ax4.annotate('', xy=(0.28, 0.30), xytext=(0.36, 0.40),
             arrowprops=dict(arrowstyle='->', color='#2c3e50', lw=1.5, linestyle='--', alpha=0.7))
ax4.annotate('', xy=(0.72, 0.30), xytext=(0.64, 0.40),
             arrowprops=dict(arrowstyle='->', color='#2c3e50', lw=1.5, linestyle='--', alpha=0.7))

# Transition labels
ax4.text(0.32, 0.68, 'Failure threshold\nreached', ha='center', va='bottom', fontsize=7, color='#2c3e50')
ax4.text(0.68, 0.68, 'Timeout expires', ha='center', va='bottom', fontsize=7, color='#2c3e50')
ax4.text(0.20, 0.20, 'Reset', ha='center', va='top', fontsize=7, color='#2c3e50')
ax4.text(0.80, 0.20, 'Test request', ha='center', va='top', fontsize=7, color='#2c3e50')

ax4.set_xlim(0, 1)
ax4.set_ylim(0, 1)
ax4.axis('off')
ax4.set_title('Circuit Breaker State Machine', fontsize=13, fontweight='bold', pad=10)

plt.tight_layout(rect=[0, 0, 1, 0.96])
plt.savefig('chapter9_control_plane_architecture.png', dpi=150, bbox_inches='tight', facecolor='white', edgecolor='none')
plt.show()
print("Visualization saved to: chapter9_control_plane_architecture.png")

# ============================================================
# Additional: Service Discovery Sequence Diagram
# ============================================================
fig2, ax = plt.subplots(figsize=(12, 8))
ax.set_facecolor('#f8f9fa')

# Title
ax.text(0.5, 0.95, 'Service Discovery Sequence', ha='center', va='top', fontsize=14, fontweight='bold', transform=ax.transAxes)

# Timeline elements
participants = ['Service A', 'Registry', 'Database', 'Service B']
y_pos = [0.75, 0.5, 0.35, 0.2]

# Draw participant boxes
for y, name in zip(y_pos, participants):
    rect = mpatches.FancyBboxPatch((0.05, y-0.05), 0.15, 0.1, boxstyle="round,pad=0.01",
                                     facecolor=control_plane_color if name != 'Service A' and name != 'Service B' else data_plane_color,
                                     edgecolor='#2c3e50', linewidth=2, alpha=0.85)
    ax.add_patch(rect)
    ax.text(0.125, y, name, ha='center', va='center', fontsize=9, fontweight='bold', color='white')

# Draw timeline
for y in y_pos:
    ax.plot([0.2, 0.9], [y, y], color='#bdc3c7', linewidth=1, linestyle='-')

# Arrows for sequence
sequence = [
    (0.125, 0.75, 0.125, 0.5, '1. Register', 'up'),
    (0.125, 0.5, 0.35, 0.35, '2. Store', 'up'),
    (0.35, 0.35, 0.125, 0.5, '3. Confirm', 'down'),
    (0.125, 0.75, 0.125, 0.5, '4. Heartbeat', 'up'),
    (0.125, 0.75, 0.4, 0.2, '5. Query: where is B?', 'right'),
    (0.4, 0.2, 0.125, 0.5, '6. Lookup B', 'right'),
    (0.125, 0.5, 0.4, 0.2, '7. Return: B@10.0.0.5', 'left'),
    (0.125, 0.75, 0.4, 0.2, '8. Direct call', 'right'),
]

for x1, y1, x2, y2, label, direction in sequence:
    if direction == 'up':
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle='->', color='#3498db', lw=1.5))
    elif direction == 'down':
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle='->', color='#3498db', lw=1.5))
    elif direction == 'right':
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle='->', color='#e74c3c', lw=1.5))
    else:
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle='->', color='#27ae60', lw=1.5))

    ax.text((x1+x2)/2, (y1+y2)/2 + 0.03, label, ha='center', va='bottom', fontsize=7, color='#2c3e50')

ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis('off')

plt.tight_layout()
plt.savefig('chapter9_service_discovery_sequence.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.show()
print("Sequence diagram saved to: chapter9_service_discovery_sequence.png")

print("\n✅ All visualizations generated successfully!")
