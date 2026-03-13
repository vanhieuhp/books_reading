#!/usr/bin/env python3
"""
Section 2: Visual Architecture — Infrastructure Stack Visualization

This script generates multiple visualizations for understanding the
virtualization abstraction gap discussed in Chapter 5 of Release It.

Run with: python section2_visual_architecture.py
Output: PNG files showing infrastructure layers and performance variability
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# Set style for professional diagrams
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 11


def create_infrastructure_stack_diagram():
    """
    Create a layered diagram showing the infrastructure stack
    from application to physical hardware.
    """
    fig, ax = plt.subplots(figsize=(14, 10))

    # Define layers with colors
    layers = [
        {"name": "APPLICATION LAYER", "color": "#3498db", "y": 0.9,
         "items": ["Your Code", "Business Logic", "HTTP Servers"]},
        {"name": "RUNTIME LAYER", "color": "#9b59b6", "y": 0.72,
         "items": ["JVM/Node/Python", "Thread Pools", "Connections"]},
        {"name": "VIRTUALIZATION LAYER", "color": "#e67e22", "y": 0.54,
         "items": ["vCPU", "vMemory", "vNetwork", "vDisk"]},
        {"name": "PHYSICAL LAYER", "color": "#e74c3c", "y": 0.36,
         "items": ["CPU Cores", "RAM", "NIC", "Disk Controller"]},
        {"name": "SHARED INFRASTRUCTURE", "color": "#95a5a6", "y": 0.18,
         "items": ["Noisy Neighbors", "Hypervisor", "Network Fabric"]},
    ]

    # Draw layers
    for layer in layers:
        # Main layer box
        rect = mpatches.FancyBboxPatch(
            (0.05, layer["y"] - 0.12), 0.9, 0.14,
            boxstyle="round,pad=0.02",
            facecolor=layer["color"],
            alpha=0.3,
            edgecolor=layer["color"],
            linewidth=2
        )
        ax.add_patch(rect)

        # Layer title
        ax.text(0.5, layer["y"], layer["name"],
                ha='center', va='center',
                fontsize=14, fontweight='bold',
                color=layer["color"])

        # Layer items (smaller text)
        items_text = " | ".join(layer["items"])
        ax.text(0.5, layer["y"] - 0.06, items_text,
                ha='center', va='center',
                fontsize=9, style='italic', color='#555')

    # Add arrows showing "hidden" problems
    problems = [
        (0.5, 0.5, "CPU Steal\n(vCPU contention)", "#e74c3c"),
        (0.25, 0.4, "I/O Wait\n(storage contention)", "#e74c3c"),
        (0.75, 0.4, "Network Latency\n(virtual switch)", "#e74c3c"),
        (0.5, 0.15, "Noisy Neighbors\n(unknowable)", "#7f8c8d"),
    ]

    for x, y, text, color in problems:
        ax.annotate(text, xy=(x, y), xytext=(x, y - 0.05),
                   fontsize=9, ha='center', color=color,
                   arrowprops=dict(arrowstyle='->', color=color, lw=1.5))

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    ax.set_title('The Infrastructure Stack: Where Problems Hide',
                fontsize=16, fontweight='bold', pad=20)

    plt.tight_layout()
    plt.savefig('infrastructure_stack.png', dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print("✓ Created: infrastructure_stack.png")


def create_performance_variability_chart():
    """
    Visualize performance variability - the key insight of this chapter.
    Shows how the same operation can have wildly different latencies.
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # Plot 1: CPU Steal Time Distribution
    ax1 = axes[0, 0]
    np.random.seed(42)

    # Simulate "good" vs "bad" host performance
    good_host = np.random.normal(0.5, 0.2, 1000)
    bad_host = np.random.exponential(3.0, 1000)

    ax1.hist(good_host, bins=50, alpha=0.6, label='Dedicated Host', color='#2ecc71')
    ax1.hist(bad_host, bins=50, alpha=0.6, label='Shared Host (noisy neighbor)', color='#e74c3c')
    ax1.set_xlabel('CPU Steal Time (%)')
    ax1.set_ylabel('Frequency')
    ax1.set_title('CPU Steal Time: Dedicated vs Shared', fontweight='bold')
    ax1.legend()
    ax1.axvline(x=10, color='#e74c3c', linestyle='--', label='Alert threshold')

    # Plot 2: I/O Wait Variability Over Time
    ax2 = axes[0, 1]
    time = np.arange(0, 60, 1)  # 60 seconds
    # Normal operation with occasional spikes
    io_wait = np.random.gamma(2, 2, 60)
    io_wait[45:50] = io_wait[45:50] * 5  # Simulate noisy neighbor spike

    ax2.plot(time, io_wait, color='#3498db', linewidth=1.5)
    ax2.fill_between(time, io_wait, alpha=0.3, color='#3498db')
    ax2.axhline(y=20, color='#e74c3c', linestyle='--', label='Warning threshold')
    ax2.set_xlabel('Time (seconds)')
    ax2.set_ylabel('I/O Wait (%)')
    ax2.set_title('I/O Wait Variability Over Time', fontweight='bold')
    ax2.legend()

    # Plot 3: Latency Distribution Comparison
    ax3 = axes[1, 0]
    # Normal application latency
    normal_latency = np.random.lognormal(2, 0.3, 1000)  # P50 ~7ms, P99 ~20ms
    # With infrastructure contention
    degraded_latency = np.random.lognormal(3, 0.8, 1000)  # Much longer tail

    ax3.hist(normal_latency, bins=50, alpha=0.6, label='Normal', color='#2ecc71', range=(0, 100))
    ax3.hist(degraded_latency, bins=50, alpha=0.6, label='With infra issues', color='#e74c3c', range=(0, 100))
    ax3.set_xlabel('Request Latency (ms)')
    ax3.set_ylabel('Frequency')
    ax3.set_title('Application Latency: Clean vs Contended', fontweight='bold')
    ax3.legend()

    # Plot 4: The "Bad Day" Pattern
    ax4 = axes[1, 1]
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    # Simulate: some days are worse than others (noisy neighbor patterns)
    base_errors = [2, 3, 15, 4, 2, 1, 2]  # Wednesday was bad
    error_rate = np.array(base_errors) + np.random.normal(0, 1, 7)

    colors = ['#2ecc71' if e < 5 else '#e74c3c' for e in base_errors]
    bars = ax4.bar(days, error_rate, color=colors, edgecolor='#333')
    ax4.set_xlabel('Day of Week')
    ax4.set_ylabel('Error Rate (%)')
    ax4.set_title('The "Bad Day" Pattern', fontweight='bold')
    ax4.axhline(y=10, color='#e74c3c', linestyle='--', alpha=0.7)

    # Add annotation
    ax4.annotate('Host migration\nor noisy neighbor', xy=(2, 15), xytext=(2, 18),
                fontsize=10, ha='center', arrowprops=dict(arrowstyle='->', color='#e74c3c'))

    plt.suptitle('Performance Variability: The Hidden Instability',
                 fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig('performance_variability.png', dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print("✓ Created: performance_variability.png")


def create_failure_mode_diagram():
    """
    Show how hardware/virtualization failures manifest as application errors.
    """
    fig, ax = plt.subplots(figsize=(14, 8))

    # Create a flow diagram showing failure propagation
    failure_modes = [
        ("Hardware Layer", [
            "Memory ECC error",
            "Disk sector failure",
            "Network card flapping",
            "CPU thermal throttling"
        ], "#e74c3c"),
        ("Virtualization Layer", [
            "CPU steal > 20%",
            "I/O wait spike",
            "VM migration",
            "Memory overcommit"
        ], "#e67e22"),
        ("Application Layer", [
            "Random crashes",
            "Timeout errors",
            "Connection failures",
            "Corrupted data"
        ], "#3498db"),
    ]

    y_positions = [0.85, 0.55, 0.25]
    x_start = 0.05

    for i, (layer, problems, color) in enumerate(failure_modes):
        y = y_positions[i]

        # Draw layer box
        rect = mpatches.FancyBboxPatch(
            (x_start, y - 0.12), 0.9, 0.2,
            boxstyle="round,pad=0.02",
            facecolor=color,
            alpha=0.2,
            edgecolor=color,
            linewidth=3
        )
        ax.add_patch(rect)

        # Layer name
        ax.text(0.5, y + 0.02, layer,
                ha='center', va='center',
                fontsize=14, fontweight='bold', color=color)

        # Problems list
        for j, problem in enumerate(problems):
            ax.text(0.1 + j * 0.22, y - 0.05, f"• {problem}",
                    ha='center', va='center',
                    fontsize=9, color='#333')

        # Arrow to next layer (if not last)
        if i < len(failure_modes) - 1:
            ax.annotate('', xy=(0.5, y_positions[i+1] + 0.12),
                       xytext=(0.5, y - 0.12),
                       arrowprops=dict(arrowstyle='->', color='#7f8c8d', lw=2))

    # Add "manifests as" labels
    ax.text(0.55, 0.7, "manifests as",
            fontsize=10, style='italic', color='#7f8c8d', ha='center')
    ax.text(0.55, 0.4, "manifests as",
            fontsize=10, style='italic', color='#7f8c8d', ha='center')

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    ax.set_title('How Infrastructure Failures Propagate to Applications',
                fontsize=16, fontweight='bold', pad=20)

    # Add key insight box
    insight_box = mpatches.FancyBboxPatch(
        (0.05, 0.02), 0.9, 0.08,
        boxstyle="round,pad=0.01",
        facecolor='#fff3cd',
        edgecolor='#ffc107',
        linewidth=2
    )
    ax.add_patch(insight_box)
    ax.text(0.5, 0.06,
            "💡 Key Insight: Hardware failures often appear as software problems",
            ha='center', va='center', fontsize=11, fontweight='bold')

    plt.tight_layout()
    plt.savefig('failure_propagation.png', dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print("✓ Created: failure_propagation.png")


if __name__ == "__main__":
    print("Generating visualizations for Chapter 5: The Un-virtualized Ground\n")

    create_infrastructure_stack_diagram()
    create_performance_variability_chart()
    create_failure_mode_diagram()

    print("\n✅ All visualizations created successfully!")
    print("Output files:")
    print("  • infrastructure_stack.png - The layers between app and hardware")
    print("  • performance_variability.png - Performance variation patterns")
    print("  • failure_propagation.png - How failures propagate")
