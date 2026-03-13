#!/usr/bin/env python3
"""
Visualization: Eight-Minute Hour Timeline
==========================================
This script generates a timeline showing what happens during an 8-minute spike,
comparing reactive autoscaling vs. ideal protection mechanisms.

Book: Release It! - Chapter 10
Author: Michael Nygard

Run: python eight_minute_timeline.py
Output: eight_minute_timeline.png
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# Set up the figure
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), height_ratios=[1.2, 1])

# Colors
colors = {
    'traffic': '#F44336',
    'capacity': '#4CAF50',
    'queue': '#FF9800',
    'autoscale': '#2196F3',
    'protection': '#00BCD4',
    'fail': '#9C27B0'
}

time_points = np.array([0, 1, 2, 3, 4, 5, 6, 7, 8])

# === TOP CHART: Traffic vs Capacity ===
ax1.set_xlim(-0.5, 8.5)
ax1.set_ylim(0, 12)

# Traffic curve (ramp up quickly in first 2 minutes, stay high)
traffic = [1, 5, 7.5, 7.5, 7.5, 7.5, 7.5, 7.5, 7.5]  # 7.5x normal

# Base capacity (constant until autoscale kicks in)
capacity = [1, 1, 1, 2, 3, 4, 5, 6, 7]  # Reacts at minute 3

# Fill area where traffic > capacity (the gap)
ax1.fill_between(time_points, traffic, capacity, where=[t > c for t, c in zip(traffic, capacity)],
                  alpha=0.3, color=colors['fail'], label='Unmet demand')

# Plot traffic line
ax1.plot(time_points, traffic, color=colors['traffic'], linewidth=3, marker='o', markersize=8, label='Traffic (7.5x normal)')

# Plot capacity line
ax1.plot(time_points, capacity, color=colors['capacity'], linewidth=3, marker='s', markersize=8, label='Capacity (autoscale)')

# Add annotations for key events
ax1.annotate('Traffic spike\nbegins', xy=(0, 1), xytext=(0.3, 2),
            fontsize=9, arrowprops=dict(arrowstyle='->', color=colors['traffic']))

ax1.annotate('Autoscaler\ntriggers', xy=(1, 1), xytext=(1.5, 3.5),
            fontsize=9, arrowprops=dict(arrowstyle='->', color=colors['autoscale']))

ax1.annotate('New instances\ncome online', xy=(3, 2), xytext=(3.5, 4),
            fontsize=9, arrowprops=dict(arrowstyle='->', color=colors['autoscale']))

ax1.annotate('Original\ncapacity\nexhausted', xy=(5, 4), xytext=(5.5, 6),
            fontsize=9, arrowprops=dict(arrowstyle='->', color=colors['fail']))

ax1.annotate('System at\nbreaking\npoint', xy=(8, 7), xytext=(7, 9),
            fontsize=9, arrowprops=dict(arrowstyle='->', color=colors['fail']))

ax1.set_xlabel('Time (minutes)', fontsize=11)
ax1.set_ylabel('Load (relative to normal = 1)', fontsize=11)
ax1.set_title('The Problem: Autoscaling Cannot Keep Up', fontsize=14, fontweight='bold', pad=20)
ax1.legend(loc='upper right', fontsize=9)
ax1.set_xticks(time_points)
ax1.grid(True, alpha=0.3)
ax1.axhline(y=1, color='gray', linestyle='--', alpha=0.5, label='Normal capacity')

# Add text box explaining the gap
gap_text = "Gap: 0.5x - 5.5x\nunmet demand"
ax1.text(4, 1, gap_text, fontsize=10, bbox=dict(boxstyle='round', facecolor='#FFEBEE', alpha=0.8))

# === BOTTOM CHART: What Should Happen (Load Shedding) ===
ax2.set_xlim(-0.5, 8.5)
ax2.set_ylim(0, 12)

# With load shedding: capacity stays constant, but we shed excess
traffic_protected = [1, 5, 7.5, 7.5, 7.5, 7.5, 7.5, 7.5, 7.5]
capacity_protected = [1, 1.2, 1.2, 1.2, 1.2, 1.2, 1.2, 1.2, 1.2]  # Pre-warmed + small buffer
served = [1, 1.2, 1.2, 1.2, 1.2, 1.2, 1.2, 1.2, 1.2]  # Capped at capacity
shed = [0, 3.8, 6.3, 6.3, 6.3, 6.3, 6.3, 6.3, 6.3]  # Traffic - served

# Plot total traffic
ax2.plot(time_points, traffic_protected, color=colors['traffic'], linewidth=3,
         marker='o', markersize=8, label='Incoming traffic')

# Plot served traffic (capped)
ax2.plot(time_points, served, color=colors['capacity'], linewidth=3,
         marker='s', markersize=8, label='Traffic served (capped)')

# Fill shed traffic
ax2.fill_between(time_points, traffic_protected, served, where=[t > s for t, s in zip(traffic_protected, served)],
                  alpha=0.3, color=colors['protection'], label='Load shed (rejected)')

# Annotations
ax2.annotate('Load shedding\nbegins', xy=(1, 5), xytext=(1.5, 7),
            fontsize=9, arrowprops=dict(arrowstyle='->', color=colors['protection']))

ax2.annotate('Return 503\nwith Retry-After', xy=(3, 7.5), xytext=(4, 9),
            fontsize=9, arrowprops=dict(arrowstyle='->', color=colors['protection']))

ax2.annotate('Core functions\nprotected', xy=(6, 1.2), xytext=(6.5, 3),
            fontsize=9, arrowprops=dict(arrowstyle='->', color=colors['capacity']))

ax2.set_xlabel('Time (minutes)', fontsize=11)
ax2.set_ylabel('Load (relative to normal = 1)', fontsize=11)
ax2.set_title('The Solution: Load Shedding Protects Core Functionality', fontsize=14, fontweight='bold', pad=20)
ax2.legend(loc='upper right', fontsize=9)
ax2.set_xticks(time_points)
ax2.grid(True, alpha=0.3)

# Add explanation box
explanation_text = "With load shedding:\n• Core requests served\n• Excess rejected fast (503)\n• System stays healthy\n• Recovery is fast"
ax2.text(4.5, 0.5, explanation_text, fontsize=10,
        bbox=dict(boxstyle='round', facecolor='#E0F7FA', alpha=0.9))

plt.tight_layout()
plt.savefig('eight_minute_timeline.png', dpi=150, bbox_inches='tight',
            facecolor='white', edgecolor='none')
plt.show()

print("Timeline visualization saved to eight_minute_timeline.png")
