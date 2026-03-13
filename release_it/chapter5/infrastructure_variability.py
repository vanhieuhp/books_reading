"""
Infrastructure Variability Visualization
=========================================
Chapter 5: The Un-virtualized Ground - Release It!

This script generates visualizations that demonstrate how infrastructure layers
add latency variability at each level of the stack.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch


def create_infrastructure_stack_diagram():
    """Create the infrastructure stack diagram showing layers and their costs."""
    fig, ax = plt.subplots(1, 1, figsize=(12, 10))

    # Define layers
    layers = [
        ("Application Layer", "#2ecc71", "Your code:\n• Business logic\n• Request handling\n• Response generation"),
        ("Runtime Layer", "#f1c40f", "Language Runtime:\n• Thread scheduling\n• Garbage collection\n• Event loop"),
        ("Virtualization Layer", "#e67e22", "Hypervisor:\n• vCPU scheduling\n• Virtual networks\n• Virtual storage"),
        ("Physical Layer", "#e74c3c", "Hardware:\n• CPU cores\n• Network cards\n• Storage devices"),
    ]

    # Draw layers
    y_positions = [0.75, 0.55, 0.35, 0.15]
    heights = [0.18, 0.18, 0.18, 0.18]

    for i, (name, color, detail) in enumerate(layers):
        rect = FancyBboxPatch(
            (0.1, y_positions[i]), 0.8, heights[i],
            boxstyle="round,pad=0.02,rounding_size=0.02",
            facecolor=color, edgecolor='black', linewidth=2, alpha=0.8
        )
        ax.add_patch(rect)
        ax.text(0.5, y_positions[i] + heights[i]/2, name,
                ha='center', va='center', fontsize=14, fontweight='bold', color='white')
        ax.text(0.5, y_positions[i] - 0.02, detail,
                ha='center', va='top', fontsize=9, style='italic')

    # Add arrows showing "leaky abstraction"
    ax.annotate('', xy=(0.95, 0.65), xytext=(0.95, 0.75),
                arrowprops=dict(arrowstyle='->', color='red', lw=2))
    ax.text(0.82, 0.70, 'Variability\nadded here', fontsize=9, color='red')

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    ax.set_title('Infrastructure Stack: Where Variability Comes From',
                 fontsize=16, fontweight='bold', pad=20)

    plt.tight_layout()
    plt.savefig('infrastructure_stack.png', dpi=150, bbox_inches='tight')
    plt.show()


def create_latency_variability_chart():
    """Create histogram showing latency variability amplification."""
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    # Layer 1: Application
    np.random.seed(42)
    app_latency = np.random.normal(50, 5, 10000)
    axes[0].hist(app_latency, bins=60, alpha=0.7, color='#2ecc71', edgecolor='black')
    axes[0].axvline(50, color='red', linestyle='--', lw=2, label='Mean')
    axes[0].axvline(np.percentile(app_latency, 99), color='orange', linestyle='--', lw=2, label='p99')
    axes[0].set_title('Application Layer\n(σ = 5ms)', fontsize=12, fontweight='bold')
    axes[0].set_xlabel('Latency (ms)')
    axes[0].set_ylabel('Frequency')
    axes[0].legend()

    # Layer 2: Virtualization
    vm_latency = np.random.normal(65, 15, 10000)
    axes[1].hist(vm_latency, bins=60, alpha=0.7, color='#f1c40f', edgecolor='black')
    axes[1].axvline(65, color='red', linestyle='--', lw=2, label='Mean')
    axes[1].axvline(np.percentile(vm_latency, 99), color='orange', linestyle='--', lw=2, label='p99')
    axes[1].set_title('Virtualization Layer\n(σ = 15ms)', fontsize=12, fontweight='bold')
    axes[1].set_xlabel('Latency (ms)')
    axes[1].set_ylabel('Frequency')
    axes[1].legend()

    # Layer 3: Physical Hardware
    hw_latency = np.random.normal(80, 35, 10000)
    hw_latency = np.clip(hw_latency, 20, 200)
    axes[2].hist(hw_latency, bins=60, alpha=0.7, color='#e74c3c', edgecolor='black')
    axes[2].axvline(80, color='red', linestyle='--', lw=2, label='Mean')
    axes[2].axvline(np.percentile(hw_latency, 99), color='orange', linestyle='--', lw=2, label='p99')
    axes[2].set_title('Physical Layer\n(σ = 35ms)', fontsize=12, fontweight='bold')
    axes[2].set_xlabel('Latency (ms)')
    axes[2].set_ylabel('Frequency')
    axes[2].legend()

    plt.suptitle('Latency Variability Amplification Across Infrastructure Layers',
                 fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig('latency_variability.png', dpi=150, bbox_inches='tight')
    plt.show()


def create_variability_factors_chart():
    """Create a chart showing different virtualization factors."""
    fig, ax = plt.subplots(figsize=(10, 6))

    factors = [
        'CPU Contention',
        'Memory Pressure',
        'Network Overhead',
        'Storage I/O',
        'VM Migration',
        'Host Maintenance',
    ]

    # Impact in milliseconds (approximate)
    impact = [15, 20, 10, 25, 100, 50]
    colors = ['#e74c3c', '#e67e22', '#f1c40f', '#e74c3c', '#e74c3c', '#e67e22']

    bars = ax.barh(factors, impact, color=colors, edgecolor='black')
    ax.set_xlabel('Typical Latency Impact (ms)', fontsize=12)
    ax.set_title('Infrastructure Variability Factors', fontsize=14, fontweight='bold')

    # Add value labels
    for bar, val in zip(bars, impact):
        ax.text(bar.get_width() + 2, bar.get_y() + bar.get_height()/2,
                f'+{val}ms', va='center', fontsize=10)

    ax.set_xlim(0, 120)
    plt.tight_layout()
    plt.savefig('variability_factors.png', dpi=150, bbox_inches='tight')
    plt.show()


def create_comparison_table():
    """Create a comparison table of different infrastructure approaches."""
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.axis('off')

    # Data
    data = [
        ['Approach', 'Variability', 'Cost', 'Control', 'Use Case'],
        ['Bare Metal', 'Low', 'High', 'Full', 'HPC, Databases'],
        ['Single-Tenant VM', 'Medium', 'Medium', 'High', 'Enterprise Apps'],
        ['Multi-Tenant VM', 'High', 'Low', 'Low', 'General Purpose'],
        ['Container (K8s)', 'High', 'Low-Med', 'Medium', 'Microservices'],
        ['Serverless', 'Very High', 'Pay-per-use', 'Minimal', 'Event-driven'],
    ]

    table = ax.table(cellText=data[1:], colLabels=data[0],
                     cellLoc='center', loc='center',
                     colColours=['#3498db']*5)

    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1.2, 2)

    # Style header
    for i in range(5):
        table[(0, i)].set_text_props(fontweight='bold', color='white')

    ax.set_title('Infrastructure Options: Variability vs Control Trade-off',
                 fontsize=14, fontweight='bold', pad=20)

    plt.tight_layout()
    plt.savefig('infrastructure_comparison.png', dpi=150, bbox_inches='tight')
    plt.show()


def create_resilience_patterns_diagram():
    """Create diagram showing resilience patterns for infrastructure variability."""
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.axis('off')

    patterns = [
        ('Circuit Breaker', 'Fail fast when downstream is overwhelmed'),
        ('Timeout', 'Never wait forever for infrastructure'),
        ('Retry with Backoff', 'Give infrastructure time to recover'),
        ('Bulkhead', 'Isolate failures to single component'),
        ('Graceful Degradation', 'Reduce functionality, stay available'),
    ]

    y_positions = np.linspace(0.8, 0.2, len(patterns))

    for i, (pattern, desc) in enumerate(patterns):
        # Draw box
        rect = FancyBboxPatch(
            (0.1, y_positions[i] - 0.08), 0.8, 0.12,
            boxstyle="round,pad=0.01,rounding_size=0.01",
            facecolor='#3498db', edgecolor='black', linewidth=2, alpha=0.8
        )
        ax.add_patch(rect)
        ax.text(0.5, y_positions[i], pattern,
                ha='center', va='center', fontsize=12, fontweight='bold', color='white')
        ax.text(0.5, y_positions[i] - 0.15, desc,
                ha='center', va='top', fontsize=10, style='italic')

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_title('Resilience Patterns for Infrastructure Variability',
                 fontsize=14, fontweight='bold', pad=20)

    plt.tight_layout()
    plt.savefig('resilience_patterns.png', dpi=150, bbox_inches='tight')
    plt.show()


if __name__ == "__main__":
    print("Generating visualizations for Chapter 5: The Un-virtualized Ground")
    print("=" * 60)

    print("\n1. Creating infrastructure stack diagram...")
    create_infrastructure_stack_diagram()

    print("2. Creating latency variability chart...")
    create_latency_variability_chart()

    print("3. Creating variability factors chart...")
    create_variability_factors_chart()

    print("4. Creating infrastructure comparison table...")
    create_comparison_table()

    print("5. Creating resilience patterns diagram...")
    create_resilience_patterns_diagram()

    print("\n" + "=" * 60)
    print("All visualizations saved as PNG files in current directory!")
    print("=" * 60)
