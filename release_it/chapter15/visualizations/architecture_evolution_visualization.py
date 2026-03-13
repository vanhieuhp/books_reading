"""
Architecture Evolution Concept Map
Visualizing the decision space for evolution strategies

Run this to generate: architecture_evolution_concept.png
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

def create_evolution_visualization():
    fig, axes = plt.subplots(1, 2, figsize=(16, 8))

    # LEFT: Evolution Strategy Decision Tree
    ax1 = axes[0]
    ax1.set_xlim(0, 10)
    ax1.set_ylim(0, 10)
    ax1.set_title("Evolution Strategy Selection", fontsize=14, fontweight='bold', pad=20)

    # Root node
    root = mpatches.FancyBboxPatch((4, 8.5), 2, 0.8, boxstyle="round,pad=0.05",
        facecolor='#2C5F8A', edgecolor='#1a3a5c', linewidth=2)
    ax1.add_patch(root)
    ax1.text(5, 8.9, "Need to Adapt?", ha='center', va='center', color='white', fontweight='bold', fontsize=10)

    # Branch 1: Small Team
    ax1.annotate('', xy=(2, 6.5), xytext=(4.5, 8.3),
        arrowprops=dict(arrowstyle='->', color='#666', lw=1.5))
    ax1.text(3.2, 7.5, "Small Team\n(<10 devs)", ha='center', va='center', fontsize=9)

    modular = mpatches.FancyBboxPatch((0.5, 5.5), 3, 0.8, boxstyle="round,pad=0.05",
        facecolor='#27AE60', edgecolor='#1e7a3e', linewidth=2)
    ax1.add_patch(modular)
    ax1.text(2, 5.9, "Modular Monolith", ha='center', va='center', color='white', fontweight='bold', fontsize=10)

    # Branch 2: Team Growing
    ax1.annotate('', xy=(5, 6.5), xytext=(5.5, 8.3),
        arrowprops=dict(arrowstyle='->', color='#666', lw=1.5))
    ax1.text(5.8, 7.5, "Team Growing", ha='center', va='center', fontsize=9)

    extraction = mpatches.FancyBboxPatch((4, 5.5), 3, 0.8, boxstyle="round,pad=0.05",
        facecolor='#3498DB', edgecolor='#2471a3', linewidth=2)
    ax1.add_patch(extraction)
    ax1.text(5.5, 5.9, "Service Extraction", ha='center', va='center', color='white', fontweight='bold', fontsize=10)

    # Branch 3: Rewrite Needed
    ax1.annotate('', xy=(8, 6.5), xytext=(6.5, 8.3),
        arrowprops=dict(arrowstyle='->', color='#666', lw=1.5))
    ax1.text(7, 7.5, "Rewrite\nRequired", ha='center', va='center', fontsize=9)

    strangler = mpatches.FancyBboxPatch((7, 5.5), 2.5, 0.8, boxstyle="round,pad=0.05",
        facecolor='#9B59B6', edgecolor='#7d3c98', linewidth=2)
    ax1.add_patch(strangler)
    ax1.text(8.25, 5.9, "Strangler", ha='center', va='center', color='white', fontweight='bold', fontsize=10)

    # Branch 4: Tech Change
    ax1.annotate('', xy=(5, 3.5), xytext=(5.5, 5.3),
        arrowprops=dict(arrowstyle='->', color='#666', lw=1.5))
    ax1.text(6.2, 4.5, "Technology\nChange", ha='center', va='center', fontsize=9)

    branch_abs = mpatches.FancyBboxPatch((3.5, 2.5), 3, 0.8, boxstyle="round,pad=0.05",
        facecolor='#E67E22', edgecolor='#b96a1d', linewidth=2)
    ax1.add_patch(branch_abs)
    ax1.text(5, 2.9, "Branch by Abstraction", ha='center', va='center', color='white', fontweight='bold', fontsize=10)

    # Scale indicators
    ax1.text(0.5, 1.5, "Scaling Patterns:", fontsize=10, fontweight='bold')
    ax1.text(0.5, 1.0, "- Horizontal: Add instances + load balancer", fontsize=8)
    ax1.text(0.5, 0.6, "- Vertical: Bigger machines", fontsize=8)
    ax1.text(0.5, 0.2, "- DB: Read replicas, CQRS, Sharding", fontsize=8)

    ax1.axis('off')

    # RIGHT: Team Size vs Complexity Trade-off
    ax2 = axes[1]
    team_sizes = np.array([5, 10, 20, 50, 100, 200])
    monolith_cost = np.array([1, 2, 5, 15, 40, 100])  # Complexity increases faster
    microservices_cost = np.array([3, 4, 6, 10, 18, 35])  # Higher base but slower growth

    ax2.plot(team_sizes, monolith_cost, 'o-', linewidth=2, markersize=8, label='Monolith', color='#E74C3C')
    ax2.plot(team_sizes, microservices_cost, 's--', linewidth=2, markersize=8, label='Microservices', color='#3498DB')

    # Crossover point annotation
    ax2.axvline(x=15, color='#666', linestyle=':', alpha=0.5)
    ax2.text(15, 90, 'Crossover Point\n~15 developers', ha='center', fontsize=9, style='italic')

    ax2.set_xlabel('Team Size (developers)', fontsize=11)
    ax2.set_ylabel('Organizational Complexity', fontsize=11)
    ax2.set_title('Monolith vs Microservices Trade-off', fontsize=14, fontweight='bold', pad=20)
    ax2.legend(loc='upper left')
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim(0, 210)
    ax2.set_ylim(0, 110)

    # Add region labels
    ax2.fill_between(team_sizes[:2], 0, monolith_cost[:2], alpha=0.2, color='#E74C3C')
    ax2.fill_between(team_sizes[3:], 0, microservices_cost[3:], alpha=0.2, color='#3498DB')
    ax2.text(8, 50, 'Monolith\nPreferred', ha='center', fontsize=10, color='#E74C3C', fontweight='bold')
    ax2.text(120, 50, 'Microservices\nMay Help', ha='center', fontsize=10, color='#3498DB', fontweight='bold')

    plt.tight_layout()
    plt.savefig('architecture_evolution_concept.png', dpi=150, bbox_inches='tight')
    plt.show()
    print("Visualization saved to: architecture_evolution_concept.png")


if __name__ == "__main__":
    create_evolution_visualization()
