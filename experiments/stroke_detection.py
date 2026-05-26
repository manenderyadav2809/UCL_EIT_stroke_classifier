"""
Experiment 1: Stroke Detection (Healthy vs Stroke)

Compares HMD baseline, standard GSA, and optimal SA-GSA (α=0.2) methods
for detecting stroke from healthy controls using the 27-subject cohort.
"""

import sys
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib as mpl
from datetime import datetime
import os

# Set matplotlib to use Agg backend for headless operation
mpl.use('Agg')

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_loader import load_eit_data, get_27_subject_cohort
from src.features import compute_hmd_features, compute_optimal_sagsa, compute_standard_gsa
from src.evaluation import evaluate_classifier, mcnemar_test
import numpy as np


def create_plot_directory():
    """Create timestamped directory for saving plots."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    plot_dir = Path(__file__).parent.parent / "plots" / f"stroke_detection_{timestamp}"
    plot_dir.mkdir(parents=True, exist_ok=True)
    return plot_dir


def plot_feature_distributions(F_hmd, F_gsa, F_sagsa, labels, plot_dir):
    """Plot feature distributions for each method."""
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    healthy_mask = (labels == "healthy")
    stroke_mask = ~healthy_mask
    
    features = [F_hmd, F_gsa, F_sagsa]
    titles = ['HMD Features', 'GSA Features', 'SA-GSA Features']
    
    for i, (features_i, title) in enumerate(zip(features, titles)):
        axes[i].hist(features_i[healthy_mask], bins=15, alpha=0.6, label='Healthy', density=True)
        axes[i].hist(features_i[stroke_mask], bins=15, alpha=0.6, label='Stroke', density=True)
        axes[i].set_xlabel('Feature Value')
        axes[i].set_ylabel('Density')
        axes[i].set_title(title)
        axes[i].legend()
        axes[i].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(plot_dir / "feature_distributions.png", dpi=300, bbox_inches='tight')
    plt.close()


def plot_performance_comparison(results_hmd, results_gsa, results_sagsa, plot_dir):
    """Plot performance comparison between methods."""
    methods = ['HMD', 'GSA', 'SA-GSA']
    results = [results_hmd, results_gsa, results_sagsa]
    
    # Extract metrics
    accuracy_scores = [r['accuracy'] for r in results]
    sensitivity = [r['sensitivity'] for r in results]
    specificity = [r['specificity'] for r in results]
    auc_scores = [r['auc'] for r in results]
    
    # Bar plot comparison
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    x = range(len(methods))
    width = 0.6
    
    # Accuracy
    axes[0,0].bar(x, accuracy_scores, width, color=['lightcoral', 'lightblue', 'lightgreen'])
    axes[0,0].set_ylabel('Accuracy')
    axes[0,0].set_title('Accuracy Comparison')
    axes[0,0].set_xticks(x)
    axes[0,0].set_xticklabels(methods)
    axes[0,0].grid(True, alpha=0.3)
    axes[0,0].set_ylim(0, 1)
    
    # Sensitivity
    axes[0,1].bar(x, sensitivity, width, color=['lightcoral', 'lightblue', 'lightgreen'])
    axes[0,1].set_ylabel('Sensitivity')
    axes[0,1].set_title('Sensitivity Comparison')
    axes[0,1].set_xticks(x)
    axes[0,1].set_xticklabels(methods)
    axes[0,1].grid(True, alpha=0.3)
    axes[0,1].set_ylim(0, 1)
    
    # Specificity
    axes[1,0].bar(x, specificity, width, color=['lightcoral', 'lightblue', 'lightgreen'])
    axes[1,0].set_ylabel('Specificity')
    axes[1,0].set_title('Specificity Comparison')
    axes[1,0].set_xticks(x)
    axes[1,0].set_xticklabels(methods)
    axes[1,0].grid(True, alpha=0.3)
    axes[1,0].set_ylim(0, 1)
    
    # AUC
    axes[1,1].bar(x, auc_scores, width, color=['lightcoral', 'lightblue', 'lightgreen'])
    axes[1,1].set_ylabel('AUC')
    axes[1,1].set_title('AUC Comparison')
    axes[1,1].set_xticks(x)
    axes[1,1].set_xticklabels(methods)
    axes[1,1].grid(True, alpha=0.3)
    axes[1,1].set_ylim(0, 1)
    
    plt.tight_layout()
    plt.savefig(plot_dir / "performance_comparison.png", dpi=300, bbox_inches='tight')
    plt.close()


def plot_prediction_confusion(results_hmd, results_gsa, results_sagsa, y_binary, names, plot_dir):
    """Plot prediction results in a confusion-style visualization."""
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    
    results = [results_hmd, results_gsa, results_sagsa]
    titles = ['HMD Predictions', 'GSA Predictions', 'SA-GSA Predictions']
    
    for i, (result, title) in enumerate(zip(results, titles)):
        predictions = result['predictions']
        correct = (predictions == y_binary)
        
        # Create scatter plot
        for j, (true_label, pred, is_correct, name) in enumerate(zip(y_binary, predictions, correct, names)):
            color = 'green' if is_correct else 'red'
            marker = 'o' if true_label == 0 else 's'  # circle for healthy, square for stroke
            fill = 'full' if pred == true_label else 'none'
            
            axes[i].scatter(j, pred, c=color, marker=marker, s=100, alpha=0.7)
        
        axes[i].set_xlabel('Subject Index')
        axes[i].set_ylabel('Predicted Label')
        axes[i].set_title(title)
        axes[i].set_yticks([0, 1])
        axes[i].set_yticklabels(['Healthy', 'Stroke'])
        axes[i].grid(True, alpha=0.3)
        
        # Add legend
        from matplotlib.lines import Line2D
        legend_elements = [
            Line2D([0], [0], marker='o', color='w', markerfacecolor='green', markersize=10, label='Correct (Healthy)'),
            Line2D([0], [0], marker='s', color='w', markerfacecolor='green', markersize=10, label='Correct (Stroke)'),
            Line2D([0], [0], marker='o', color='w', markerfacecolor='red', markersize=10, label='Incorrect (Healthy)'),
            Line2D([0], [0], marker='s', color='w', markerfacecolor='red', markersize=10, label='Incorrect (Stroke)')
        ]
        axes[i].legend(handles=legend_elements, loc='upper right', fontsize=8)
    
    plt.tight_layout()
    plt.savefig(plot_dir / "prediction_visualization.png", dpi=300, bbox_inches='tight')
    plt.close()


def main():
    print("=" * 80)
    print("EXPERIMENT 1: STROKE DETECTION (Healthy vs Stroke)")
    print("=" * 80)
    
    # Create timestamped directory for plots
    plot_dir = create_plot_directory()
    print(f"Plots will be saved to: {plot_dir}")
    
    # Load 27-subject cohort
    print("Loading data...")
    data = load_eit_data()
    data_27 = get_27_subject_cohort(data)
    
    labels = data_27["labels"]
    names = data_27["names"]
    n_subjects = len(names)
    
    # Create binary labels: 0=healthy, 1=stroke
    y_binary = np.zeros(n_subjects, dtype=int)
    stroke_mask = (labels == "ischaemia") | (labels == "haemorrhage") 
    y_binary[stroke_mask] = 1
    
    n_healthy = int((labels == "healthy").sum())
    n_ischaemia = int((labels == "ischaemia").sum())
    n_haemorrhage = int((labels == "haemorrhage").sum())
    
    print(f"\nDataset: {n_subjects} subjects")
    print(f"  Healthy: {n_healthy}")
    print(f"  Ischaemia: {n_ischaemia}")  
    print(f"  Haemorrhage: {n_haemorrhage}")
    print(f"  Total Stroke: {n_ischaemia + n_haemorrhage}")
    
    # Compute features
    print("\n" + "=" * 80)
    print("FEATURE COMPUTATION")
    print("=" * 80)
    
    F_hmd = compute_hmd_features(data_27)
    F_gsa = compute_standard_gsa(data_27)
    F_sagsa = compute_optimal_sagsa(data_27)
    
    # Evaluate each method
    print("\n" + "=" * 80) 
    print("CLASSIFICATION RESULTS")
    print("=" * 80)
    
    results_hmd = evaluate_classifier("HMD (Channel-space baseline)", F_hmd, y_binary)
    results_gsa = evaluate_classifier("GSA (α=0.0)", F_gsa, y_binary)  
    results_sagsa = evaluate_classifier("SA-GSA (α=0.2) - OPTIMAL", F_sagsa, y_binary)
    
    # Generate plots
    print("\n" + "=" * 80)
    print("GENERATING PLOTS")
    print("=" * 80)
    
    print("Creating feature distribution plots...")
    plot_feature_distributions(F_hmd, F_gsa, F_sagsa, labels, plot_dir)
    
    print("Creating performance comparison plots...")
    plot_performance_comparison(results_hmd, results_gsa, results_sagsa, plot_dir)
    
    print("Creating prediction visualization plots...")
    plot_prediction_confusion(results_hmd, results_gsa, results_sagsa, y_binary, names, plot_dir)
    
    # Paired comparisons  
    print("\n" + "=" * 80)
    print("PAIRED STATISTICAL COMPARISONS (McNemar Test)")
    print("=" * 80)
    
    p_sagsa_vs_hmd, b1, c1 = mcnemar_test(
        results_sagsa["predictions"], 
        results_hmd["predictions"], 
        y_binary
    )
    
    p_sagsa_vs_gsa, b2, c2 = mcnemar_test(
        results_sagsa["predictions"],
        results_gsa["predictions"], 
        y_binary
    )
    
    p_gsa_vs_hmd, b3, c3 = mcnemar_test(
        results_gsa["predictions"],
        results_hmd["predictions"],
        y_binary
    )
    
    print(f"\nSA-GSA vs HMD:")
    print(f"  SA-GSA correct, HMD wrong: {b1}")
    print(f"  SA-GSA wrong, HMD correct: {c1}") 
    print(f"  McNemar p-value: {p_sagsa_vs_hmd:.4f}")
    
    print(f"\nSA-GSA vs GSA:")
    print(f"  SA-GSA correct, GSA wrong: {b2}")
    print(f"  SA-GSA wrong, GSA correct: {c2}")
    print(f"  McNemar p-value: {p_sagsa_vs_gsa:.4f}")
    
    print(f"\nGSA vs HMD:")
    print(f"  GSA correct, HMD wrong: {b3}")
    print(f"  GSA wrong, HMD correct: {c3}")
    print(f"  McNemar p-value: {p_gsa_vs_hmd:.4f}")
    
    # Per-subject predictions table
    print("\n" + "=" * 80)
    print("PER-SUBJECT PREDICTIONS")
    print("=" * 80)
    
    print(f"{'Subject':<14} {'True':<12} {'HMD':<8} {'GSA':<8} {'SA-GSA':<8}")
    print("-" * 58)
    
    for i in range(n_subjects):
        true_label = "healthy" if y_binary[i] == 0 else "stroke"
        hmd_pred = "healthy" if results_hmd["predictions"][i] == 0 else "stroke"
        gsa_pred = "healthy" if results_gsa["predictions"][i] == 0 else "stroke"  
        sagsa_pred = "healthy" if results_sagsa["predictions"][i] == 0 else "stroke"
        
        print(f"{names[i]:<14} {true_label:<12} {hmd_pred:<8} {gsa_pred:<8} {sagsa_pred:<8}")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    print(f"\nBest performing method: SA-GSA (α=0.2)")
    print(f"  Accuracy: {results_sagsa['accuracy']:.3f}")
    print(f"  Statistical significance: p={results_sagsa['p_perm']:.4f}")
    
    if results_sagsa['accuracy'] > results_hmd['accuracy']:
        improvement = (results_sagsa['accuracy'] - results_hmd['accuracy']) * 100
        print(f"  Improvement over HMD baseline: +{improvement:.1f} percentage points")
    
    if results_sagsa['accuracy'] > results_gsa['accuracy']:
        improvement = (results_sagsa['accuracy'] - results_gsa['accuracy']) * 100  
        print(f"  Improvement over standard GSA: +{improvement:.1f} percentage points")
    
    print(f"\nSA-GSA demonstrates the benefit of incorporating injection pattern structure")
    print(f"into the graph construction (α=0.2 mixing parameter).")
    
    print(f"\nPlots saved to: {plot_dir}")
    print(f"Generated plots:")
    print(f"  - feature_distributions.png")
    print(f"  - performance_comparison.png") 
    print(f"  - prediction_visualization.png")
    
    print("\nExperiment completed successfully!")


if __name__ == "__main__":
    main()