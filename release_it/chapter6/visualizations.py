#!/usr/bin/env python3
"""
Visualization: Latency Hierarchy
Chapter 6: Foundations - Release It!

This script generates a visualization of the latency hierarchy,
showing how different operations compare in speed.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

def create_latency_hierarchy():
    """Create latency hierarchy visualization"""
    # Latency data (approximate values in nanoseconds)
    operations = [
        'L1 Cache Reference',
        'L2 Cache Reference',
        'Main Memory Access',
        'SSD Random Read',
        'Disk Seek',
        'Network RTT (Same DC)',
        'Network RTT (Cross-Country)'
    ]
    latencies_ns = [0.5, 7, 100, 150000, 10000000, 500000, 150000000]
    latencies_label = ['0.5 ns', '7 ns', '100 ns', '150 μs', '10 ms', '500 μs', '150 ms']

    fig, ax = plt.subplots(figsize=(14, 8))

    # Color gradient from fast (green) to slow (red)
    colors = plt.cm.RdYlGn_r(np.linspace(0.1, 0.9, len(operations)))

    y_pos = np.arange(len(operations))
    bars = ax.barh(y_pos, latencies_ns, color=colors, edgecolor='black', linewidth=1.2)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(operations, fontsize=12)
    ax.set_xlabel('Latency (nanoseconds, log scale)', fontsize=12)
    ax.set_xscale('log')
    ax.set_title('Latency Hierarchy: How Operations Compare\n(Every step ~10-100x slower)', fontsize=14, fontweight='bold')

    # Add value annotations
    for i, (bar, label) in enumerate(zip(bars, latencies_label)):
        ax.text(bar.get_width() * 1.1, bar.get_y() + bar.get_height()/2,
                label, va='center', fontsize=11, fontweight='bold')

    # Add reference line for RAM
    ax.axvline(x=100, color='gray', linestyle='--', alpha=0.5)
    ax.text(100, -0.7, 'RAM reference = 100 ns baseline', fontsize=9, ha='center', color='gray')

    # Add annotations showing relative speeds
    ax.annotate('In CPU', xy=(1, 0), xytext=(0.3, -0.5),
                fontsize=9, color='green', fontweight='bold',
                arrowprops=dict(arrowstyle='->', color='green'))
    ax.annotate('Cross-network', xy=(500000000, 6), xytext=(10000000, 6.5),
                fontsize=9, color='red', fontweight='bold',
                arrowprops=dict(arrowstyle='->', color='red'))

    plt.tight_layout()
    plt.savefig('latency_hierarchy.png', dpi=150, bbox_inches='tight')
    plt.show()
    print("Created: latency_hierarchy.png")

def create_memory_hierarchy():
    """Create memory hierarchy visualization"""
    fig, ax = plt.subplots(figsize=(12, 6))

    # Memory types and their characteristics
    memory_types = ['L1 Cache', 'L2 Cache', 'L3 Cache', 'RAM', 'SSD', 'HDD']
    access_times = [0.5, 7, 30, 100, 150000, 10000000]  # nanoseconds
    sizes = ['32 KB', '256 KB', '8 MB', 'GBs', 'TBs', 'TBs']
    colors = ['#2E7D32', '#388E3C', '#4CAF50', '#FFC107', '#FF9800', '#F44336']

    x = np.arange(len(memory_types))
    width = 0.6

    bars = ax.bar(x, access_times, width, color=colors, edgecolor='black')

    # Add size labels
    for bar, size in zip(bars, sizes):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height * 1.1,
                f'{size}', ha='center', va='bottom', fontsize=10)

    ax.set_ylabel('Access Time (nanoseconds, log scale)', fontsize=12)
    ax.set_yscale('log')
    ax.set_title('Memory Hierarchy: Size vs Speed Trade-off', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(memory_types, fontsize=11)

    # Add annotations
    ax.annotate('Fastest\nSmallest', xy=(0, 0.3), fontsize=9, ha='center', color='green')
    ax.annotate('Slowest\nLargest', xy=(5, 50000000), fontsize=9, ha='center', color='red')

    plt.tight_layout()
    plt.savefig('memory_hierarchy.png', dpi=150, bbox_inches='tight')
    plt.show()
    print("Created: memory_hierarchy.png")

def create_network_comparison():
    """Compare network vs local operations"""
    fig, ax = plt.subplots(figsize=(10, 6))

    operations = ['Local RAM', 'Local SSD', 'Local HDD', 'Same DC Network', 'Cross-Country']
    latencies = [100, 150000, 10000000, 500000, 150000000]
    colors = ['#2E7D32', '#4CAF50', '#FFC107', '#FF5722', '#F44336']

    bars = ax.bar(operations, latencies, color=colors, edgecolor='black')

    # Add value labels
    for bar, lat in zip(bars, latencies):
        height = bar.get_height()
        if lat < 1000:
            label = f'{lat} ns'
        elif lat < 1000000:
            label = f'{lat/1000:.0f} μs'
        else:
            label = f'{lat/1000000:.0f} ms'
        ax.text(bar.get_x() + bar.get_width()/2., height * 1.05,
                label, ha='center', va='bottom', fontsize=10, fontweight='bold')

    ax.set_ylabel('Latency (nanoseconds, log scale)', fontsize=12)
    ax.set_yscale('log')
    ax.set_title('Local vs Network Operations\nNetwork is ~5000x slower than RAM', fontsize=14, fontweight='bold')

    # Add divider
    ax.axhline(y=1000000, color='gray', linestyle='--', alpha=0.5)
    ax.text(4.5, 2000000, 'ms boundary', fontsize=9, color='gray')

    plt.tight_layout()
    plt.savefig('network_comparison.png', dpi=150, bbox_inches='tight')
    plt.show()
    print("Created: network_comparison.png")

if __name__ == '__main__':
    create_latency_hierarchy()
    create_memory_hierarchy()
    create_network_comparison()
    print("\nAll visualizations created successfully!")
