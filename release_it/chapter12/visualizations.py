#!/usr/bin/env python3
"""
Chapter 12: Adaptation - Visualizations
Deployment Strategies, Versioning, and CD Pipeline Visualizations

Run: python visualizations.py
Output: PNG files showing deployment concepts
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['figure.facecolor'] = 'white'
plt.rcParams['font.size'] = 10


def draw_deployment_comparison():
    """Deployment Strategy Comparison Chart"""
    fig, ax = plt.subplots(figsize=(14, 8))

    strategies = ['Big Bang', 'Rolling', 'Blue-Green', 'Canary', 'Feature Flags']
    risk_scores = [9, 6, 4, 2, 1]  # Lower is better
    speed_scores = [9, 4, 8, 5, 7]  # Higher is faster
    rollback_difficulty = [9, 7, 2, 3, 1]  # Lower is easier

    x = np.arange(len(strategies))
    width = 0.25

    bars1 = ax.bar(x - width, risk_scores, width, label='Risk (lower=better)', color='#E74C3C', alpha=0.8)
    bars2 = ax.bar(x, speed_scores, width, label='Speed (higher=better)', color='#3498DB', alpha=0.8)
    bars3 = ax.bar(x + width, rollback_difficulty, width, label='Rollback Ease (lower=easier)', color='#27AE60', alpha=0.8)

    ax.set_xlabel('Deployment Strategy', fontweight='bold', fontsize=12)
    ax.set_ylabel('Score (1-10)', fontweight='bold', fontsize=12)
    ax.set_title('Deployment Strategy Trade-offs\n(Book: Release It! - Chapter 12)', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(strategies, fontsize=11)
    ax.legend(loc='upper right')
    ax.set_ylim(0, 10)

    # Add annotations
    annotations = [
        ('High risk,\nno canary', 'Big Bang'),
        ('Gradual,\nbut slow', 'Rolling'),
        ('Fast switch,\ndb complexity', 'Blue-Green'),
        ('Data-driven,\ncomplex setup', 'Canary'),
        ('Decoupled deploy\nfrom release', 'Feature Flags'),
    ]

    for i, (annot, strat) in enumerate(annotations):
        if strat == 'Feature Flags':
            ax.annotate(annot, xy=(i, risk_scores[i] - 0.8), ha='center', fontsize=8,
                       color='#2C3E50', style='italic')
        else:
            ax.annotate(annot, xy=(i, risk_scores[i] + 0.3), ha='center', fontsize=8,
                       color='#2C3E50', style='italic')

    plt.tight_layout()
    plt.savefig('deployment_comparison.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("[OK] Created deployment_comparison.png")


def draw_versioning_strategies():
    """API Versioning Strategy Comparison"""
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    # Strategy data
    strategies = ['URL Path', 'Header', 'Query Param']
    visibility = [10, 7, 8]  # How visible is version to clients
    url_cleanliness = [3, 10, 6]
    caching = [9, 8, 4]
    routing_complexity = [5, 7, 6]

    metrics = ['Visibility', 'URL Cleanliness', 'Caching', 'Routing Simplicity']
    data = np.array([
        [10, 3, 9, 5],   # URL Path
        [7, 10, 8, 7],   # Header
        [8, 6, 4, 6],    # Query Param
    ])

    colors = ['#3498DB', '#E74C3C', '#27AE60']

    x = np.arange(len(metrics))
    width = 0.25

    for idx, (strategy, color) in enumerate(zip(strategies, colors)):
        axes[0].bar(idx + (np.arange(len(metrics)) - 1) * width,
                   data[idx], width, label=strategy, color=color, alpha=0.8)

    axes[0].set_xlabel('Metric', fontweight='bold')
    axes[0].set_ylabel('Score (1-10)', fontweight='bold')
    axes[0].set_title('Versioning Strategy Comparison', fontweight='bold', fontsize=12)
    axes[0].set_xticks(range(len(metrics)))
    axes[0].set_xticklabels(metrics, rotation=15, ha='right')
    axes[0].legend(loc='upper right')
    axes[0].set_ylim(0, 12)

    # Example URLs
    axes[1].text(0.5, 0.8, 'URL Path', fontsize=12, fontweight='bold', ha='center')
    axes[1].text(0.5, 0.6, '/api/v1/users\n/api/v2/users', fontsize=10, ha='center',
                 family='monospace', bbox=dict(boxstyle='round', facecolor='#ECF0F1'))
    axes[1].text(0.5, 0.35, 'Header', fontsize=12, fontweight='bold', ha='center')
    axes[1].text(0.5, 0.15, 'Accept: vnd.api.v1+json', fontsize=9, ha='center',
                 family='monospace', bbox=dict(boxstyle='round', facecolor='#ECF0F1'))
    axes[1].axis('off')

    axes[2].text(0.5, 0.8, 'Query Parameter', fontsize=12, fontweight='bold', ha='center')
    axes[2].text(0.5, 0.6, '/api/users?version=1', fontsize=10, ha='center',
                 family='monospace', bbox=dict(boxstyle='round', facecolor='#ECF0F1'))
    axes[2].text(0.5, 0.35, 'Pros & Cons', fontsize=12, fontweight='bold', ha='center')
    pros = '[OK] Explicit\n[OK] Easy to test\n[X] URL pollution\n[X] Caching issues'
    axes[2].text(0.5, 0.1, pros, fontsize=9, ha='center', va='top')
    axes[2].axis('off')

    plt.tight_layout()
    plt.savefig('versioning_strategies.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("[OK] Created versioning_strategies.png")


def draw_cd_pipeline():
    """Continuous Delivery Pipeline Flow"""
    fig, ax = plt.subplots(figsize=(16, 8))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 10)
    ax.axis('off')

    # Pipeline stages
    stages = [
        (1, 'Commit', '#3498DB'),
        (3.5, 'Build', '#9B59B6'),
        (6, 'Test', '#E67E22'),
        (8.5, 'Stage', '#1ABC9C'),
        (11, 'Prod', '#E74C3C'),
        (13.5, 'Monitor', '#27AE60'),
    ]

    # Draw stages as boxes
    for x, name, color in stages:
        box = FancyBboxPatch((x - 0.8, 4), 1.6, 2,
                             boxstyle="round,pad=0.05,rounding_size=0.2",
                             facecolor=color, edgecolor='#2C3E50', linewidth=2, alpha=0.9)
        ax.add_patch(box)
        ax.text(x, 5, name, ha='center', va='center',
               fontweight='bold', color='white', fontsize=11)

    # Draw arrows between stages
    for i in range(len(stages) - 1):
        start = stages[i][0] + 0.8
        end = stages[i + 1][0] - 0.8
        ax.annotate('', xy=(end, 5), xytext=(start, 5),
                   arrowprops=dict(arrowstyle='->', color='#2C3E50', lw=2))

    # Add details below each stage
    details = [
        ('Code push\nUnit tests', 'Compile\nPackage', 'Integration\nE2E tests', 'Deploy to\nstaging', 'Deploy to\nproduction', 'Metrics\nAlerts'),
        ('git push', 'docker build', 'pytest\nlint', 'Blue-green\nor canary', 'Traffic\nswitch', 'Error rate\nLatency'),
    ]

    for idx, (detail1, detail2) in enumerate(zip(details[0], details[1])):
        x_pos = stages[idx][0]
        ax.text(x_pos, 2.5, detail1, ha='center', va='top', fontsize=8, color='#2C3E50')
        ax.text(x_pos, 1.5, detail2, ha='center', va='top', fontsize=7,
               color='#7F8C8D', style='italic')

    # Add rollback arrow
    ax.annotate('', xy=(11, 7.5), xytext=(8.5, 7.5),
                arrowprops=dict(arrowstyle='->', color='#E74C3C', lw=2, ls='--'))
    ax.text(9.75, 7.8, 'Auto-Rollback\n(on failure)', ha='center', fontsize=8,
           color='#E74C3C', fontweight='bold')

    # Title
    ax.text(8, 9.2, 'Continuous Delivery Pipeline', ha='center',
           fontsize=14, fontweight='bold')
    ax.text(8, 8.7, '(Book: Release It! - Chapter 12)', ha='center',
           fontsize=10, color='#7F8C8D')

    # Feature flag annotation
    ax.text(13.5, 7.5, 'Feature Flags\ndecouple deploy\nfrom release',
           ha='center', fontsize=8, color='#27AE60',
           bbox=dict(boxstyle='round', facecolor='#E8F8F5', edgecolor='#27AE60'))

    plt.tight_layout()
    plt.savefig('cd_pipeline.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("[OK] Created cd_pipeline.png")


def draw_canary_deployment():
    """Canary Deployment Visualization"""
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 8)
    ax.axis('off')

    # Draw infrastructure layers
    # Load Balancer
    lb = FancyBboxPatch((0.5, 6), 2, 1.2,
                        boxstyle="round,pad=0.05", facecolor='#3498DB',
                        edgecolor='#2C3E50', linewidth=2)
    ax.add_patch(lb)
    ax.text(1.5, 6.6, 'Load\nBalancer', ha='center', va='center',
           color='white', fontweight='bold', fontsize=9)

    # Versions and their traffic percentages
    versions = [
        (4, 'v1.0\n(Stable)', '#27AE60', 90),
        (7.5, 'v1.1\n(Canary)', '#E74C3C', 9),
        (11, 'v1.2\n(Experimental)', '#9B59B6', 1),
    ]

    for x, label, color, pct in versions:
        box = FancyBboxPatch((x - 0.8, 5.5), 1.6, 1.8,
                            boxstyle="round,pad=0.05", facecolor=color,
                            edgecolor='#2C3E50', linewidth=2)
        ax.add_patch(box)
        ax.text(x, 6.4, label, ha='center', va='center',
               color='white', fontweight='bold', fontsize=8)
        ax.text(x, 5.9, f'{pct}% traffic', ha='center', va='center',
               color='white', fontsize=7)

    # Arrows from LB to versions
    for x, _, _, _ in versions:
        ax.annotate('', xy=(x, 5.5), xytext=(1.5, 6),
                   arrowprops=dict(arrowstyle='->', color='#2C3E50', lw=1.5))

    # Monitoring box
    monitor = FancyBboxPatch((4, 2), 4, 2),
    ax.add_patch(FancyBboxPatch((4, 2), 4, 1.8,
                               boxstyle="round,pad=0.05", facecolor='#F39C12',
                               edgecolor='#2C3E50', linewidth=2))
    ax.text(6, 3.2, 'Canary Analysis', ha='center', va='center',
           fontweight='bold', fontsize=11)
    ax.text(6, 2.5, 'Error rate: 0.1%\nLatency: 45ms\nHealth: PASS', ha='center',
           va='center', fontsize=9, family='monospace')

    # Feedback loop
    ax.annotate('', xy=(8, 4), xytext=(8, 3.8),
               arrowprops=dict(arrowstyle='->', color='#27AE60', lw=2))
    ax.text(8.5, 3.5, 'If metrics bad:\nauto-rollback',
           fontsize=8, color='#27AE60', va='top')

    # Title
    ax.text(6, 7.5, 'Canary Deployment Flow', ha='center',
           fontsize=14, fontweight='bold')
    ax.text(6, 7, '(Gradual rollout with automated health checking)', ha='center',
           fontsize=10, color='#7F8C8D')

    plt.tight_layout()
    plt.savefig('canary_deployment.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("[OK] Created canary_deployment.png")


def draw_feature_flags_flow():
    """Feature Flags Architecture"""
    fig, ax = plt.subplots(figsize=(14, 7))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 8)
    ax.axis('off')

    # Main components
    components = [
        (1, 'Developer', '#3498DB'),
        (4, 'Feature Flag\nService', '#E74C3C'),
        (9, 'Application\nService', '#27AE60'),
        (13, 'Users', '#9B59B6'),
    ]

    for x, label, color in components:
        circle = plt.Circle((x, 5), 0.8, color=color, alpha=0.8, ec='#2C3E50', lw=2)
        ax.add_patch(circle)
        ax.text(x, 5, label, ha='center', va='center',
               color='white', fontweight='bold', fontsize=8)

    # Arrows
    arrows = [((2, 4), (4, 5)), ((4, 5), (9, 5)), ((9, 5), (11, 5)), ((11, 5), (13, 5))]
    for start, end in arrows:
        ax.annotate('', xy=end, xytext=start,
                   arrowprops=dict(arrowstyle='->', color='#2C3E50', lw=1.5))

    # Annotations
    ax.text(2.5, 4.3, '1. Create flag', fontsize=8, color='#7F8C8D')
    ax.text(6.5, 4.3, '2. Evaluate flag\n(at runtime)', fontsize=8, color='#7F8C8D')
    ax.text(11, 4.3, '3. Serve content\nbased on flag', fontsize=8, color='#7F8C8D')

    # Feature flag states
    states = [
        (1, 'OFF', '#95A5A6'),
        (4, 'ROLLING\nOUT', '#F39C12'),
        (7, 'A/B TEST', '#3498DB'),
        (10, '100%', '#27AE60'),
    ]

    for x, state, color in states:
        box = FancyBboxPatch((x - 0.4, 1.5), 0.8, 0.8,
                            boxstyle="round,pad=0.02", facecolor=color,
                            edgecolor='#2C3E50', linewidth=1)
        ax.add_patch(box)
        ax.text(x, 1.9, state, ha='center', va='bottom', fontsize=7, fontweight='bold')

    # Title
    ax.text(7, 7.5, 'Feature Flags: Decouple Deploy from Release', ha='center',
           fontsize=14, fontweight='bold')
    ax.text(7, 7, '(Code ships with flags OFF, toggled at runtime)', ha='center',
           fontsize=10, color='#7F8C8D')

    # Legend
    ax.text(12, 2.5, 'Flag States:', fontsize=9, fontweight='bold')
    ax.text(12, 2, 'OFF: Old code path', fontsize=7, color='#7F8C8D')
    ax.text(12, 1.6, 'ROLLING: Gradual %', fontsize=7, color='#7F8C8D')
    ax.text(12, 1.2, 'A/B: User segments', fontsize=7, color='#7F8C8D')
    ax.text(12, 0.8, '100%: Full rollout', fontsize=7, color='#7F8C8D')

    plt.tight_layout()
    plt.savefig('feature_flags.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("[OK] Created feature_flags.png")


def main():
    print("=" * 60)
    print("Chapter 12: Adaptation - Generating Visualizations")
    print("=" * 60)

    draw_deployment_comparison()
    draw_versioning_strategies()
    draw_cd_pipeline()
    draw_canary_deployment()
    draw_feature_flags_flow()

    print("=" * 60)
    print("All visualizations generated successfully!")
    print("Output files:")
    print("  - deployment_comparison.png")
    print("  - versioning_strategies.png")
    print("  - cd_pipeline.png")
    print("  - canary_deployment.png")
    print("  - feature_flags.png")
    print("=" * 60)


if __name__ == '__main__':
    main()
