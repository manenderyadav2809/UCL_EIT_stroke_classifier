"""
Detailed Electrode Contributions for Each Stroke Patient

This module provides a complete breakdown of all 32 electrode contributions
for each individual stroke patient, helping to understand the full pattern
of electrode involvement in stroke detection decisions.
"""

import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from datetime import datetime
import pandas as pd
from scipy.spatial.distance import cdist

# Set matplotlib to use Agg backend for headless operation
mpl.use('Agg')

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.data_loader import load_eit_data, get_27_subject_cohort
from src.features.gsa import build_electrode_graph, BEST_ALPHA, BAND_LO, BAND_HI
from src.utils import electrode_spectrum_matrix

# Electrode coordinate table with names
ELECTRODE_COORD_TABLE = [
    ("FP2",    0.101412, 0.042578, 0.131065),
    ("FP1",    0.151292, 0.041441, 0.130196),
    ("F8",     0.072204, 0.070328, 0.131346),
    ("F4",     0.092561, 0.062527, 0.156750),
    ("Fz",     0.127605, 0.053614, 0.166368),
    ("F3",     0.167149, 0.067805, 0.154810),
    ("F7",     0.184628, 0.070138, 0.129700),
    ("FC6",    0.070805, 0.090619, 0.151198),
    ("FC2",    0.102617, 0.088382, 0.179815),
    ("FC1",    0.153259, 0.090816, 0.177953),
    ("FC5",    0.184426, 0.091658, 0.149607),
    ("T8",     0.048835, 0.125922, 0.122920),
    ("C4",     0.074019, 0.125950, 0.169412),
    ("CZ",     0.125712, 0.126015, 0.190618),
    ("C3",     0.178643, 0.126343, 0.169205),
    ("T7",     0.202036, 0.127006, 0.132310),
    ("TP10",   0.051562, 0.161578, 0.093972),
    ("CP6",    0.061816, 0.155658, 0.152531),
    ("CP2",    0.092385, 0.163433, 0.181028),
    ("CP1",    0.164329, 0.165419, 0.177857),
    ("CP5",    0.191738, 0.157512, 0.150624),
    ("TP9",    0.199505, 0.162722, 0.093679),
    ("P4",     0.077253, 0.185251, 0.156537),
    ("Pz",     0.126285, 0.198345, 0.166404),
    ("P3",     0.179480, 0.184037, 0.155066),
    ("P8",     0.056988, 0.169492, 0.131095),
    ("PO4",    0.098454, 0.213609, 0.131306),
    ("PO3",    0.153472, 0.213956, 0.131209),
    ("P7",     0.198140, 0.163776, 0.129244),
    ("I2/O10", 0.098454, 0.218000, 0.093539),
    ("I1/O9",  0.153472, 0.218000, 0.093554),
    ("Oz",     0.126000, 0.223000, 0.112000),
    ("NFpz",   0.126352, 0.042010, 0.120000),
]

def get_electrode_names(xyz):
    """
    Map electrode positions to their standard EEG names.
    
    Args:
        xyz: Array of electrode positions (n x 3)
        
    Returns:
        list: Electrode names corresponding to positions
    """
    table_names = np.array([r[0] for r in ELECTRODE_COORD_TABLE])
    table_xyz = np.array([[r[1], r[2], r[3]] for r in ELECTRODE_COORD_TABLE])
    
    names_out = []
    tol = 1e-4
    D = cdist(xyz, table_xyz)
    
    for i in range(xyz.shape[0]):
        j = int(np.argmin(D[i]))
        if D[i, j] <= tol:
            names_out.append(str(table_names[j]))
        else:
            names_out.append(f"REF_{i}")  # Reference electrode or unknown
    
    return names_out


def compute_detailed_electrode_contributions(data):
    """
    Compute detailed electrode contributions for all subjects.
    
    Returns:
        dict: Complete electrode contribution data
    """
    
    voltages = data["voltages"]
    freq = data["freq"]
    protocol = data["protocol"]
    xyz = data["nominal_pos"][:32]
    labels = data["labels"]
    names = data["names"]
    
    # Get electrode names from coordinates
    electrode_names = get_electrode_names(xyz)
    
    n_subjects = voltages.shape[0]
    band_mask = (freq >= BAND_LO) & (freq <= BAND_HI)
    
    # Build SA-GSA graph
    eigvals, eigvecs = build_electrode_graph(xyz, protocol, BEST_ALPHA)
    
    print(f"Computing detailed electrode contributions using SA-GSA (α={BEST_ALPHA})")
    print(f"Frequency band: {BAND_LO}-{BAND_HI} Hz")
    
    # Get electrode spectrum matrices
    X_all = np.full((n_subjects, 32, len(freq)), np.nan)
    for k in range(n_subjects):
        M = electrode_spectrum_matrix(voltages[k], protocol)
        row_mean = np.nanmean(M, axis=1, keepdims=True)
        M = np.where(np.isfinite(M), M, row_mean)
        M = np.where(np.isfinite(M), M, 0.0)
        X_all[k] = M
    
    # Graph Fourier transform
    C_all = np.stack([eigvecs.T @ X_all[k] for k in range(n_subjects)])
    
    # Healthy subject mask
    healthy_mask = (labels == "healthy")
    stroke_mask = ~healthy_mask
    
    # Compute healthy reference
    C_healthy = C_all[healthy_mask]
    mu_healthy_full = np.nanmean(C_healthy, axis=0)
    sd_healthy_full = np.nanstd(C_healthy, axis=0, ddof=1)
    
    # Store detailed results
    electrode_contributions = np.zeros((n_subjects, 32))
    z_scores_band_avg = np.zeros((n_subjects, 32))  # Average z-score in band
    z_scores_max = np.zeros((n_subjects, 32))       # Max z-score in band
    
    for k in range(n_subjects):
        if healthy_mask[k]:
            # Leave-one-out for healthy subjects
            k_in_healthy = np.where(healthy_mask)[0]
            kp = int(np.where(k_in_healthy == k)[0][0])
            other = np.delete(C_healthy, kp, axis=0)
            mu = np.nanmean(other, axis=0)
            sd = np.nanstd(other, axis=0, ddof=1)
        else:
            # Full healthy pool for stroke patients
            mu = mu_healthy_full
            sd = sd_healthy_full
        
        # Compute z-scores for each electrode and frequency
        Z = (C_all[k] - mu) / np.clip(sd, 1e-3, None)
        Z_band = Z[:, band_mask]
        
        # Compute various electrode metrics
        for electrode in range(32):
            z_electrode = Z_band[electrode, :]
            z_valid = z_electrode[np.isfinite(z_electrode)]
            
            if z_valid.size > 0:
                # Mean squared z-score (main contribution metric)
                electrode_contributions[k, electrode] = np.mean(z_valid ** 2)
                # Average z-score magnitude
                z_scores_band_avg[k, electrode] = np.mean(np.abs(z_valid))
                # Maximum z-score magnitude
                z_scores_max[k, electrode] = np.max(np.abs(z_valid))
            else:
                electrode_contributions[k, electrode] = np.nan
                z_scores_band_avg[k, electrode] = np.nan
                z_scores_max[k, electrode] = np.nan
    
    return {
        'contributions': electrode_contributions,
        'z_scores_avg': z_scores_band_avg,
        'z_scores_max': z_scores_max,
        'labels': labels,
        'names': names,
        'healthy_mask': healthy_mask,
        'stroke_mask': stroke_mask,
        'electrode_names': electrode_names
    }


def print_detailed_patient_contributions(data, save_to_file=True):
    """
    Print detailed electrode contributions for each stroke patient.
    """
    
    contributions = data['contributions']
    labels = data['labels']
    names = data['names']
    stroke_mask = data['stroke_mask']
    z_scores_avg = data['z_scores_avg']
    z_scores_max = data['z_scores_max']
    electrode_names = data['electrode_names']
    
    stroke_indices = np.where(stroke_mask)[0]
    stroke_names = np.array(names)[stroke_mask]
    stroke_labels = np.array(labels)[stroke_mask]
    stroke_contributions = contributions[stroke_mask]
    
    print("\n" + "=" * 100)
    print("DETAILED ELECTRODE CONTRIBUTIONS FOR EACH STROKE PATIENT")
    print("=" * 100)
    
    # Prepare data for saving
    detailed_data = []
    
    for i, (patient_idx, name, label) in enumerate(zip(stroke_indices, stroke_names, stroke_labels)):
        print(f"\n{name} ({label.upper()}):")
        print("-" * 80)
        
        patient_contribs = contributions[patient_idx]
        patient_z_avg = z_scores_avg[patient_idx]
        patient_z_max = z_scores_max[patient_idx]
        
        # Sort electrodes by contribution
        electrode_order = np.argsort(patient_contribs)[::-1]
        
        print("Electrode Name | Contribution | Avg |Z| | Max |Z| | Rank")
        print("-" * 60)
        
        for rank, electrode_idx in enumerate(electrode_order, 1):
            contrib = patient_contribs[electrode_idx]
            z_avg = patient_z_avg[electrode_idx]
            z_max = patient_z_max[electrode_idx]
            electrode_name = electrode_names[electrode_idx]
            
            if np.isfinite(contrib):
                print(f"{electrode_name:>13s} | {contrib:11.4f} | {z_avg:7.3f} | {z_max:7.3f} | {rank:4d}")
                
                # Store for CSV
                detailed_data.append({
                    'Patient': name,
                    'Condition': label,
                    'Electrode_Name': electrode_name,
                    'Electrode_Index': electrode_idx,
                    'Contribution': contrib,
                    'Avg_Z_Score': z_avg,
                    'Max_Z_Score': z_max,
                    'Rank': rank
                })
            else:
                print(f"{electrode_name:>13s} |         NaN |     NaN |     NaN | {rank:4d}")
        
        # Summary for this patient
        valid_contribs = patient_contribs[np.isfinite(patient_contribs)]
        if len(valid_contribs) > 0:
            total_contrib = np.sum(valid_contribs)
            top_5_contrib = np.sum(np.sort(valid_contribs)[-5:])
            top_10_contrib = np.sum(np.sort(valid_contribs)[-10:])
            
            print(f"\nSummary for {name}:")
            print(f"  Total contribution: {total_contrib:.3f}")
            print(f"  Top 5 electrodes contribute: {top_5_contrib:.3f} ({100*top_5_contrib/total_contrib:.1f}%)")
            print(f"  Top 10 electrodes contribute: {top_10_contrib:.3f} ({100*top_10_contrib/total_contrib:.1f}%)")
            print(f"  Number of active electrodes: {len(valid_contribs)}")
    
    # Save to CSV file
    if save_to_file and detailed_data:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_file = Path(__file__).parent / "plots" / f"detailed_electrode_contributions_{timestamp}.csv"
        
        df = pd.DataFrame(detailed_data)
        df.to_csv(csv_file, index=False)
        print(f"\nDetailed data saved to: {csv_file}")
        
        # Also create a summary CSV
        summary_data = []
        for name in stroke_names:
            patient_data = df[df['Patient'] == name]
            if not patient_data.empty:
                summary_data.append({
                    'Patient': name,
                    'Condition': patient_data.iloc[0]['Condition'],
                    'Total_Contribution': patient_data['Contribution'].sum(),
                    'Top_5_Contribution': patient_data.nlargest(5, 'Contribution')['Contribution'].sum(),
                    'Top_10_Contribution': patient_data.nlargest(10, 'Contribution')['Contribution'].sum(),
                    'Most_Important_Electrode': patient_data.iloc[0]['Electrode_Name'],
                    'Highest_Contribution': patient_data['Contribution'].max()
                })
        
        summary_df = pd.DataFrame(summary_data)
        summary_csv_file = Path(__file__).parent / "plots" / f"patient_summary_{timestamp}.csv"
        summary_df.to_csv(summary_csv_file, index=False)
        print(f"Patient summary saved to: {summary_csv_file}")
    
    return detailed_data


def create_comprehensive_visualization(data):
    """
    Create comprehensive visualization of all electrode contributions.
    """
    
    contributions = data['contributions']
    labels = data['labels']
    names = data['names']
    stroke_mask = data['stroke_mask']
    electrode_names = data['electrode_names']
    
    stroke_names = np.array(names)[stroke_mask]
    stroke_labels = np.array(labels)[stroke_mask]
    stroke_contributions = contributions[stroke_mask]
    
    # Create timestamp for file naming
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    plot_dir = Path(__file__).parent / "plots"
    plot_dir.mkdir(exist_ok=True)
    
    # 1. Comprehensive heatmap - all electrodes, all stroke patients
    fig, ax = plt.subplots(figsize=(16, 12))
    
    # Sort patients by total contribution for better visualization
    total_contribs = np.nansum(stroke_contributions, axis=1)
    patient_order = np.argsort(total_contribs)[::-1]
    
    ordered_contribs = stroke_contributions[patient_order]
    ordered_names = stroke_names[patient_order]
    ordered_labels = stroke_labels[patient_order]
    
    im = ax.imshow(ordered_contribs, aspect='auto', cmap='hot', interpolation='nearest')
    
    # Set labels
    ax.set_xlabel('Electrode Name', fontsize=12)
    ax.set_ylabel('Stroke Patients (ordered by total contribution)', fontsize=12)
    ax.set_title('Complete Electrode Contribution Matrix - All Stroke Patients', fontsize=14)
    
    # Set ticks
    ax.set_xticks(range(0, 32, 2))
    ax.set_xticklabels([electrode_names[i] for i in range(0, 32, 2)], rotation=45, ha='right')
    ax.set_yticks(range(len(ordered_names)))
    ax.set_yticklabels([f"{name} ({label})" for name, label in zip(ordered_names, ordered_labels)], 
                       fontsize=8)
    
    # Add colorbar
    cbar = plt.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label('Electrode Contribution Score', fontsize=12)
    
    plt.tight_layout()
    plt.savefig(plot_dir / f"complete_electrode_matrix_{timestamp}.png", 
                dpi=300, bbox_inches='tight')
    plt.close()
    
    # 2. Individual patient detailed plots (6 per figure)
    n_patients = len(stroke_names)
    n_figures = (n_patients + 5) // 6  # Ceiling division
    
    for fig_idx in range(n_figures):
        fig, axes = plt.subplots(2, 3, figsize=(20, 12))
        axes = axes.flatten()
        
        start_idx = fig_idx * 6
        end_idx = min(start_idx + 6, n_patients)
        
        for i, patient_idx in enumerate(range(start_idx, end_idx)):
            ax = axes[i]
            
            name = stroke_names[patient_idx]
            label = stroke_labels[patient_idx]
            contribs = stroke_contributions[patient_idx]
            
            # Bar plot for this patient
            x_patient = np.arange(len(electrode_names))
            bars = ax.bar(x_patient, contribs, alpha=0.7, 
                         color='red' if label == 'ischaemia' else 'darkred')
            
            ax.set_xlabel('Electrode Name')
            ax.set_ylabel('Contribution Score')
            ax.set_title(f'{name} ({label.upper()})')
            ax.set_xticks(x_patient[::4])  # Show every 4th electrode name
            ax.set_xticklabels([electrode_names[j] for j in range(0, len(electrode_names), 4)], 
                              rotation=45, ha='right')
            ax.grid(True, alpha=0.3)
            
            # Highlight top 3 electrodes
            top_3_indices = np.argsort(contribs)[::-1][:3]
            for electrode_idx in top_3_indices:
                if np.isfinite(contribs[electrode_idx]):
                    ax.axvline(x=electrode_idx, color='green', linestyle='--', alpha=0.8, linewidth=2)
                    # Add text annotation
                    ax.text(electrode_idx, contribs[electrode_idx], 
                           electrode_names[electrode_idx], ha='center', va='bottom', 
                           fontweight='bold', color='green', fontsize=8)
        
        # Hide unused subplots
        for i in range(end_idx - start_idx, 6):
            axes[i].set_visible(False)
        
        plt.tight_layout()
        plt.savefig(plot_dir / f"individual_patients_detailed_{fig_idx+1}_{timestamp}.png", 
                    dpi=300, bbox_inches='tight')
        plt.close()
    
    print(f"\nVisualization files created:")
    print(f"  - complete_electrode_matrix_{timestamp}.png")
    for fig_idx in range(n_figures):
        print(f"  - individual_patients_detailed_{fig_idx+1}_{timestamp}.png")


def main():
    print("=" * 100)
    print("DETAILED ELECTRODE CONTRIBUTIONS FOR EACH STROKE PATIENT")
    print("=" * 100)
    
    # Load data
    print("Loading data...")
    data = load_eit_data()
    data_27 = get_27_subject_cohort(data)
    
    labels = data_27["labels"]
    names = data_27["names"]
    
    stroke_mask = (labels != "healthy")
    n_stroke = stroke_mask.sum()
    
    print(f"Found {n_stroke} stroke patients in the dataset")
    
    # Compute detailed contributions
    print("\nComputing detailed electrode contributions...")
    contribution_data = compute_detailed_electrode_contributions(data_27)
    
    # Print detailed results for each patient
    detailed_data = print_detailed_patient_contributions(contribution_data, save_to_file=True)
    
    # Create comprehensive visualizations
    print("\nCreating comprehensive visualizations...")
    create_comprehensive_visualization(contribution_data)
    
    print(f"\nAnalysis completed! Check the plots/ directory for detailed visualizations and CSV files.")
    
    return contribution_data, detailed_data


if __name__ == "__main__":
    contribution_data, detailed_data = main()