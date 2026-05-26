"""
Harmonic Mean Distance (HMD) features for EIT stroke classification.
Channel-space anomaly detection baseline method.
"""

import numpy as np
from ..utils import log_abs_mask

# Constants
FREQ_BAND = (100.0, 2000.0)  # Full frequency band for HMD


def compute_hmd_features(data):
    """
    Compute HMD (Harmonic Mean Distance) features for all subjects.
    
    Args:
        data: Dict from data_loader with keys: voltages, freq, labels
        
    Returns:
        numpy array: HMD features per subject
    """
    
    voltages = data["voltages"]
    freq = data["freq"]
    labels = data["labels"]
    
    print(f"Computing HMD features (band {FREQ_BAND[0]}-{FREQ_BAND[1]} Hz)")
    
    n_subjects = voltages.shape[0]
    healthy_mask = (labels == "healthy")
    healthy_idx = np.where(healthy_mask)[0]
    
    # Frequency mask
    freq_mask = (freq >= FREQ_BAND[0]) & (freq <= FREQ_BAND[1])
    
    # Compute log|V| for all healthy subjects
    healthy_L_stack = np.stack([log_abs_mask(voltages[k]) for k in healthy_idx])
    mu_healthy_full = np.nanmean(healthy_L_stack, axis=0)
    sd_healthy_full = np.nanstd(healthy_L_stack, axis=0, ddof=1)
    
    hmd_features = np.zeros(n_subjects)
    
    for k in range(n_subjects):
        # Get healthy template (LOO for healthy, full pool for patients)
        if healthy_mask[k]:
            # Leave-one-out for healthy subjects
            k_in_healthy = int(np.where(healthy_idx == k)[0][0])
            other = np.delete(healthy_L_stack, k_in_healthy, axis=0)
            mu_template = np.nanmean(other, axis=0)
            sd_template = np.nanstd(other, axis=0, ddof=1)
        else:
            # Full healthy pool for patients
            mu_template = mu_healthy_full
            sd_template = sd_healthy_full
        
        # Compute Z-scores
        L_subj = log_abs_mask(voltages[k])
        Z2 = ((L_subj - mu_template) / np.clip(sd_template, 1e-3, None)) ** 2
        
        # Apply frequency mask and compute HMD
        Z2_band = Z2[:, freq_mask]
        z2_valid = Z2_band[np.isfinite(Z2_band)]
        
        if z2_valid.size >= 20:
            hmd_features[k] = float(np.mean(z2_valid))
        else:
            hmd_features[k] = np.nan
    
    print(f"HMD features computed for {n_subjects} subjects")
    print(f"Healthy subjects: {healthy_mask.sum()}")
    print(f"HMD range: [{np.nanmin(hmd_features):.3f}, {np.nanmax(hmd_features):.3f}]")
    
    return hmd_features


def compute_hmd_deep_features(data):
    """
    Compute HMD-deep features using only deep measurement channels.
    
    Args:
        data: Dict from data_loader
        
    Returns:
        numpy array: HMD-deep features per subject
    """
    
    voltages = data["voltages"]
    freq = data["freq"] 
    protocol = data["protocol"]
    labels = data["labels"]
    nominal_pos = data["nominal_pos"]
    
    print("Computing HMD-deep features")
    
    # Identify deep channels (80th percentile of electrode separation)
    P = protocol.astype(int)
    xyz = nominal_pos[:32]
    
    d_cs = np.zeros(protocol.shape[0])
    for i in range(protocol.shape[0]):
        a, b = P[i, 0] - 1, P[i, 1] - 1
        if 0 <= a < 32 and 0 <= b < 32:
            d_cs[i] = np.linalg.norm(xyz[a] - xyz[b])
        else:
            d_cs[i] = np.nan
    
    deep_threshold = np.nanpercentile(d_cs, 80)
    deep_rows = np.where(d_cs >= deep_threshold)[0]
    
    print(f"Using {len(deep_rows)} deep channels (≥{deep_threshold:.3f} spatial separation)")
    
    n_subjects = voltages.shape[0]
    healthy_mask = (labels == "healthy")
    healthy_idx = np.where(healthy_mask)[0]
    
    # Frequency mask
    freq_mask = (freq >= FREQ_BAND[0]) & (freq <= FREQ_BAND[1])
    
    # Compute log|V| for healthy subjects
    healthy_L_stack = np.stack([log_abs_mask(voltages[k]) for k in healthy_idx])
    mu_healthy_full = np.nanmean(healthy_L_stack, axis=0)
    sd_healthy_full = np.nanstd(healthy_L_stack, axis=0, ddof=1)
    
    hmd_deep_features = np.zeros(n_subjects)
    
    for k in range(n_subjects):
        # Get healthy template
        if healthy_mask[k]:
            k_in_healthy = int(np.where(healthy_idx == k)[0][0])
            other = np.delete(healthy_L_stack, k_in_healthy, axis=0)
            mu_template = np.nanmean(other, axis=0)
            sd_template = np.nanstd(other, axis=0, ddof=1)
        else:
            mu_template = mu_healthy_full
            sd_template = sd_healthy_full
        
        # Compute Z-scores for deep channels only
        L_subj = log_abs_mask(voltages[k])
        Z2 = ((L_subj - mu_template) / np.clip(sd_template, 1e-3, None)) ** 2
        
        # Apply deep channel and frequency masks
        Z2_deep_band = Z2[deep_rows][:, freq_mask]
        z2_valid = Z2_deep_band[np.isfinite(Z2_deep_band)]
        
        if z2_valid.size >= 20:
            hmd_deep_features[k] = float(np.mean(z2_valid))
        else:
            hmd_deep_features[k] = np.nan
    
    print(f"HMD-deep features computed for {n_subjects} subjects")
    print(f"HMD-deep range: [{np.nanmin(hmd_deep_features):.3f}, {np.nanmax(hmd_deep_features):.3f}]")
    
    return hmd_deep_features