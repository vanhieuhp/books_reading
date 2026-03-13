#!/usr/bin/env python3
"""
Visualization: Eight-Minute Hour Concept Map
=============================================
This script generates a conceptual diagram showing the cascade failure
pattern and the relationship between load spike and system response.

Book: Release It! - Chapter 10
Author: Michael Nygard

Run: python concept_map.py
Output: concept_map.png
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# Set up the figure with a dark theme for better contrast
plt.style.use('default')
fig, ax = plt.subplots(1, 1, figsize=(14, 10))

# Define colors
colors = {
    'normal': '#4CAF50',      # Green
    'spike': '#F44336',       # Red
    'autoscale': '#2196F3',   # Blue
    'exhaust': '#FF9800',     # Orange
    'failure': '#9C27B0',     # Purple
    'protection': '#00BCD4',  # Cyan
    'arrow': '#333333'
}

# Draw the timeline axis
ax.set_xlim(0, 10)
ax.set_ylim(0, 10)

# Title
ax.text(5, 9.5, 'The Eight-Minute Hour: Cascade Failure Pattern',
        ha='center', fontsize=16, fontweight='bold')
ax.text(5, 9.0, '60 minutes of traffic arrives in 8 minutes → 7.5x normal load',
        ha='center', fontsize=11, style='italic', color='#666')

# === Phase 1: Traffic Spike ===
ax.add_patch(mpatches.FancyBboxPatch((0.5, 7), 3, 1.2,
                                       boxstyle="round,pad=0.05",
                                       facecolor=colors['spike'], alpha=0.7))
ax.text(2, 7.6, 'TRAFFIC SPIKE', ha='center', fontsize=11, fontweight='bold', color='white')
ax.text(2, 7.2, '7.5x load in 8 min', ha='center', fontsize=9, color='white')

# === Phase 2: Autoscaling (Fails) ===
ax.add_patch(mpatches.FancyBboxPatch((4, 7), 3, 1.2,
                                       boxstyle="round,pad=0.05",
                                       facecolor=colors['autoscale'], alpha=0.7))
ax.text(5.5, 7.6, 'AUTOSCALING', ha='center', fontsize=11, fontweight='bold', color='white')
ax.text(5.5, 7.2, 'Reactive - too slow', ha='center', fontsize=9, color='white')

# Arrow from spike to autoscale
ax.annotate('', xy=(4, 7.6), xytext=(3.5, 7.6),
            arrowprops=dict(arrowstyle='->', color=colors['arrow'], lw=2))

# === Phase 3: Resource Exhaustion ===
ax.add_patch(mpatches.FancyBboxPatch((0.5, 5), 3, 1.5,
                                       boxstyle="round,pad=0.05",
                                       facecolor=colors['exhaust'], alpha=0.7))
ax.text(2, 6.1, 'RESOURCE EXHAUSTION', ha='center', fontsize=10, fontweight='bold', color='white')
ax.text(2, 5.6, '• Connection pools', ha='left', fontsize=9, color='white')
ax.text(2, 5.3, '• Thread pools', ha='left', fontsize=9, color='white')
ax.text(2, 5.0, '• Memory / GC', ha='left', fontsize=9, color='white')

# Arrow from autoscale to exhaustion
ax.annotate('', xy=(0.8, 5.75), xytext=(3.2, 7),
            arrowprops=dict(arrowstyle='->', color=colors['arrow'], lw=2,
                          connectionstyle='arc3,rad=-0.3'))

# === Phase 4: Cascade Failure ===
ax.add_patch(mpatches.FancyBboxPatch((4, 4.5), 3, 2,
                                       boxstyle="round,pad=0.05",
                                       facecolor=colors['failure'], alpha=0.7))
ax.text(5.5, 6.1, 'CASCADE FAILURE', ha='center', fontsize=10, fontweight='bold', color='white')
ax.text(5.5, 5.6, 'Phase 1: Queue buildup', ha='center', fontsize=9, color='white')
ax.text(5.5, 5.3, 'Phase 2: Timeouts', ha='center', fontsize=9, color='white')
ax.text(5.5, 5.0, 'Phase 3: Complete failure', ha='center', fontsize=9, color='white')

# Arrow from exhaustion to cascade
ax.annotate('', xy=(4, 5.5), xytext=(3.5, 5),
            arrowprops=dict(arrowstyle='->', color=colors['arrow'], lw=2))

# === Solution Box (Bottom) ===
ax.add_patch(mpatches.FancyBboxPatch((0.5, 1.5), 9, 2.5,
                                       boxstyle="round,pad=0.1",
                                       facecolor=colors['protection'], alpha=0.3,
                                       edgecolor=colors['protection'], linewidth=3))
ax.text(5, 3.6, 'PROTECTION MECHANISMS', ha='center', fontsize=12, fontweight='bold', color='#333')

# Protection strategies - left column
ax.text(1.5, 3.0, 'Load Shedding', ha='left', fontsize=10, fontweight='bold')
ax.text(1.5, 2.6, '• Reject excess early', ha='left', fontsize=9)
ax.text(1.5, 2.3, '• Return 503 with Retry-After', ha='left', fontsize=9)
ax.text(1.5, 2.0, '• Protect core functionality', ha='left', fontsize=9)

# Protection strategies - right column
ax.text(5.5, 3.0, 'Resilience Patterns', ha='left', fontsize=10, fontweight='bold')
ax.text(5.5, 2.6, '• Circuit breakers', ha='left', fontsize=9)
ax.text(5.5, 2.3, '• Exponential backoff + jitter', ha='left', fontsize=9)
ax.text(5.5, 2.0, '• Bulkheads for isolation', ha='left', fontsize=9)

# Arrow from cascade to protection
ax.annotate('', xy=(5, 4.5), xytext=(5, 4),
            arrowprops=dict(arrowstyle='->', color=colors['protection'], lw=3))

# === Timeline annotations ===
ax.text(8, 8.5, 'Timeline:', fontsize=9, fontweight='bold')
ax.text(8, 8.0, '0 min: Spike starts', fontsize=8)
ax.text(8, 7.5, '1 min: Autoscaler triggers', fontsize=8)
ax.text(8, 7.0, '3 min: New instances start', fontsize=8)
ax.text(8, 6.5, '5 min: Original exhausted', fontsize=8)
ax.text(8, 6.0, '8 min: Breaking point', fontsize=8)

# Key insight box
insight_box = mpatches.FancyBboxPatch((0.3, 0.2), 9.4, 0.9,
                                        boxstyle="round,pad=0.05",
                                        facecolor='#FFF9C4',
                                        edgecolor='#F9A825', linewidth=2)
ax.add_patch(insight_box)
ax.text(5, 0.65, 'KEY INSIGHT: Autoscaling is reactive -- design for peak +20%, not average',
        ha='center', fontsize=10, fontweight='bold', color='#333')

# Remove axes
ax.set_axis_off()

# Save
plt.tight_layout()
plt.savefig('concept_map.png', dpi=150, bbox_inches='tight',
            facecolor='white', edgecolor='none')
plt.show()

print("Concept map saved to concept_map.png")
