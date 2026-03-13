"""
Chaos Engineering Visualizations
================================
Generate architecture and process diagrams for Chapter 13: Chaos Engineering
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np


def create_chaos_loop_diagram():
    """Create the Chaos Engineering Experiment Loop diagram"""
    fig, ax = plt.subplots(1, 1, figsize=(14, 10))

    # Define boxes and arrows for chaos engineering loop
    boxes = {
        'Define Steady State': (0.5, 0.85, 0.18, 0.08),
        'Hypothesize': (0.5, 0.68, 0.18, 0.08),
        'Design Experiment': (0.5, 0.51, 0.18, 0.08),
        'Run Experiment': (0.5, 0.34, 0.18, 0.08),
        'Analyze Results': (0.5, 0.17, 0.18, 0.08),
        'Improve System': (0.85, 0.34, 0.18, 0.08),
    }

    colors = {
        'Define Steady State': '#4CAF50',
        'Hypothesize': '#2196F3',
        'Design Experiment': '#FF9800',
        'Run Experiment': '#F44336',
        'Analyze Results': '#9C27B0',
        'Improve System': '#00BCD4',
    }

    # Draw boxes
    for name, (x, y, w, h) in boxes.items():
        rect = mpatches.FancyBboxPatch(
            (x - w/2, y - h/2), w, h,
            boxstyle="round,pad=0.02,rounding_size=0.02",
            facecolor=colors[name], edgecolor='black', linewidth=2
        )
        ax.add_patch(rect)
        ax.text(x, y, name, ha='center', va='center', fontsize=9, fontweight='bold', color='white', wrap=True)

    # Draw arrows
    arrow_props = dict(arrowstyle='->', connectionstyle='arc3,rad=0.1', lw=2)

    # Main loop arrows
    ax.annotate('', xytext=(0.5, 0.77), xy=(0.5, 0.73), arrowprops=arrow_props)
    ax.annotate('', xytext=(0.5, 0.60), xy=(0.5, 0.56), arrowprops=arrow_props)
    ax.annotate('', xytext=(0.5, 0.43), xy=(0.5, 0.39), arrowprops=arrow_props)
    ax.annotate('', xytext=(0.5, 0.26), xy=(0.5, 0.22), arrowprops=arrow_props)

    # Feedback loop to "Improve System"
    ax.annotate('', xytext=(0.5, 0.13), xy=(0.65, 0.13), arrowprops=dict(arrowstyle='->', lw=2))
    ax.annotate('', xytext=(0.85, 0.38), xy=(0.75, 0.46), arrowprops=dict(arrowstyle='->', lw=2))

    # Add "Continuous" label
    ax.text(0.72, 0.52, 'Continuous\nImprovement', fontsize=8, ha='center', style='italic')

    # Add title and annotations
    ax.set_title('Chaos Engineering Experiment Loop\n(The Steady-State Hypothesis Framework)', fontsize=14, fontweight='bold', pad=20)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')

    # Add legend for chaos types
    chaos_types = [
        ('Infrastructure', '#F44336', 'Hardware, network, servers'),
        ('Application', '#FF9800', 'Processes, exceptions, latency'),
        ('Dependency', '#9C27B0', 'APIs, databases, caches'),
        ('Load', '#2196F3', 'Traffic spikes, connection exhaustion'),
    ]

    legend_y = 0.95
    ax.text(0.02, legend_y, 'Types of Chaos:', fontsize=10, fontweight='bold')
    for i, (name, color, desc) in enumerate(chaos_types):
        rect = mpatches.Rectangle((0.02, legend_y - 0.05 - i*0.045), 0.02, 0.035, facecolor=color)
        ax.add_patch(rect)
        ax.text(0.05, legend_y - 0.032 - i*0.045, f'{name}: {desc}', fontsize=8)

    plt.tight_layout()
    plt.savefig('chaos_engineering_loop.png', dpi=150, bbox_inches='tight', facecolor='white')
    plt.show()
    print("Created: chaos_engineering_loop.png")


def create_chaos_architecture_diagram():
    """Create the Chaos Engineering Architecture diagram"""
    from matplotlib.patches import FancyBboxPatch

    fig, ax = plt.subplots(1, 1, figsize=(16, 11))

    # User-facing layer
    user_box = FancyBboxPatch((0.45, 0.92), 0.10, 0.04, boxstyle="round,pad=0.01", facecolor='#2196F3', edgecolor='black')
    ax.add_patch(user_box)
    ax.text(0.5, 0.94, 'Users', ha='center', va='center', fontsize=10, fontweight='bold', color='white')

    # API Gateway
    gateway_box = FancyBboxPatch((0.40, 0.85), 0.20, 0.05, boxstyle="round,pad=0.01", facecolor='#4CAF50', edgecolor='black')
    ax.add_patch(gateway_box)
    ax.text(0.5, 0.875, 'API Gateway', ha='center', va='center', fontsize=9, fontweight='bold', color='white')

    # Service mesh
    services = [
        ('Order\nService', 0.15, 0.72, '#FF9800'),
        ('Payment\nService', 0.38, 0.72, '#FF9800'),
        ('Inventory\nService', 0.62, 0.72, '#FF9800'),
        ('User\nService', 0.85, 0.72, '#FF9800'),
    ]

    for name, x, y, color in services:
        box = FancyBboxPatch((x-0.08, y-0.04), 0.16, 0.08, boxstyle="round,pad=0.01", facecolor=color, edgecolor='black', linewidth=2)
        ax.add_patch(box)
        ax.text(x, y, name, ha='center', va='center', fontsize=8, fontweight='bold', color='white')

    # Data layer
    databases = [
        ('PostgreSQL', 0.20, 0.55, '#9C27B0'),
        ('Redis Cache', 0.45, 0.55, '#9C27B0'),
        ('Kafka', 0.70, 0.55, '#9C27B0'),
    ]

    for name, x, y, color in databases:
        box = FancyBboxPatch((x-0.08, y-0.04), 0.16, 0.08, boxstyle="round,pad=0.01", facecolor=color, edgecolor='black', linewidth=2)
        ax.add_patch(box)
        ax.text(x, y, name, ha='center', va='center', fontsize=8, fontweight='bold', color='white')

    # Chaos injection points (stars)
    chaos_points = [
        ('⚡ Network\nPartition', 0.08, 0.50),
        ('⚡ Kill\nService', 0.50, 0.35),
        ('⚡ Latency\nInjection', 0.85, 0.50),
        ('⚡ DB\nFailure', 0.50, 0.78),
    ]

    for label, x, y in chaos_points:
        ax.text(x, y, label, ha='center', va='center', fontsize=7, color='#F44336', fontweight='bold')

    # Monitoring/Observability
    monitor_box = FancyBboxPatch((0.42, 0.18), 0.16, 0.10, boxstyle="round,pad=0.01", facecolor='#607D8B', edgecolor='black', linewidth=2)
    ax.add_patch(monitor_box)
    ax.text(0.5, 0.23, 'Observability', ha='center', va='center', fontsize=9, fontweight='bold', color='white')
    ax.text(0.5, 0.20, 'Prometheus + Grafana', ha='center', va='center', fontsize=7, color='white')
    ax.text(0.5, 0.17, '+ Jaeger', ha='center', va='center', fontsize=7, color='white')

    # Chaos Control Plane
    chaos_box = FancyBboxPatch((0.80, 0.18), 0.14, 0.10, boxstyle="round,pad=0.01", facecolor='#F44336', edgecolor='black', linewidth=2)
    ax.add_patch(chaos_box)
    ax.text(0.87, 0.23, 'Chaos Control', ha='center', va='center', fontsize=8, fontweight='bold', color='white')
    ax.text(0.87, 0.20, 'Litmus/ChaosMesh', ha='center', va='center', fontsize=7, color='white')

    # Draw connection lines
    # User to gateway
    ax.annotate('', xy=(0.5, 0.88), xytext=(0.5, 0.94), arrowprops=dict(arrowstyle='->', lw=2, color='gray'))
    # Gateway to services
    for _, x, y, _ in services:
        ax.annotate('', xy=(x, y+0.05), xytext=(x, 0.82), arrowprops=dict(arrowstyle='->', lw=1.5, color='gray'))
    # Services to databases
    for _, x, y, _ in services:
        for dx, dy, _ in databases:
            if abs(x - dx) < 0.3:
                ax.annotate('', xy=(dx, y-0.04), xytext=(x, y-0.08), arrowprops=dict(arrowstyle='->', lw=1, color='gray', linestyle='dashed'))

    # Labels
    ax.text(0.5, 0.05, 'Chaos Engineering Architecture: Injecting Failures to Discover System Weaknesses',
            ha='center', va='center', fontsize=12, fontweight='bold')
    ax.text(0.5, 0.02, 'Steady State = Normal Behavior | Hypothesis = What We Expect | Experiment = What We Break',
            ha='center', va='center', fontsize=9, style='italic')

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')

    plt.tight_layout()
    plt.savefig('chaos_architecture.png', dpi=150, bbox_inches='tight', facecolor='white')
    plt.show()
    print("Created: chaos_architecture.png")


def create_mttr_comparison():
    """Create a comparison chart showing MTTR vs MTBF trade-offs"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Left: MTTR vs MTBF
    mtbf_values = np.array([100, 500, 1000, 5000, 10000])  # Hours between failures
    mttr_values = np.array([5, 15, 30, 60, 120])  # Minutes to recover
    cost_prevent = mtbf_values * 0.1  # Cost to prevent: proportional to MTBF
    cost_recover = mttr_values / 60 * 10  # Cost to recover: proportional to MTTR

    x = np.arange(len(mtbf_values))
    width = 0.35

    bars1 = ax1.bar(x - width/2, cost_prevent, width, label='Cost to Prevent (arbitrary)', color='#2196F3', alpha=0.7)
    bars2 = ax1.bar(x + width/2, cost_recover, width, label='Cost to Recover (arbitrary)', color='#F44336', alpha=0.7)

    ax1.set_xlabel('MTBF (Hours between failures)')
    ax1.set_ylabel('Relative Cost')
    ax1.set_title('MTBF vs MTTR: The Cost Trade-off')
    ax1.set_xticks(x)
    ax1.set_xticklabels(['100h', '500h', '1000h', '5000h', '10000h'])
    ax1.legend()
    ax1.grid(axis='y', alpha=0.3)

    # Right: Availability vs Cost (the 9s curve)
    nines = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9])
    availability = [90, 99, 99.9, 99.99, 99.999, 99.9999, 99.99999, 99.999999, 99.9999999]
    # Exponential cost curve
    cost = np.exp(nines * 0.8)

    ax2.plot(nines, cost, 'o-', color='#4CAF50', linewidth=2, markersize=8)
    ax2.set_xlabel('Number of 9s in Availability')
    ax2.set_ylabel('Relative Cost (log scale)')
    ax2.set_title('The Exponential Cost of Availability')
    ax2.set_yscale('log')
    ax2.grid(True, alpha=0.3)
    ax2.set_xticks(nines)

    # Annotate key points
    ax2.annotate('99.9% = 8.7h\ndowntime/year', xy=(3, 8), xytext=(4, 20),
                arrowprops=dict(arrowstyle='->', color='gray'),
                fontsize=9, color='gray')
    ax2.annotate('99.999% = 5min\ndowntime/year', xy=(5, 54), xytext=(6, 150),
                arrowprops=dict(arrowstyle='->', color='gray'),
                fontsize=9, color='gray')

    plt.tight_layout()
    plt.savefig('mttr_mtbf_comparison.png', dpi=150, bbox_inches='tight', facecolor='white')
    plt.show()
    print("Created: mttr_mtbf_comparison.png")


if __name__ == "__main__":
    print("Generating Chaos Engineering visualizations...")
    print("=" * 50)

    print("\n1. Creating Chaos Loop diagram...")
    create_chaos_loop_diagram()

    print("\n2. Creating Chaos Architecture diagram...")
    create_chaos_architecture_diagram()

    print("\n3. Creating MTTR vs MTBF comparison...")
    create_mttr_comparison()

    print("\n" + "=" * 50)
    print("All visualizations created successfully!")
