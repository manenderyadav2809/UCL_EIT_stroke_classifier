"""
Graph Spectral Anomaly (GSA) and Structure-Aware GSA (SA-GSA) features.
Includes the optimal SA-GSA implementation with alpha=0.2.
"""

import numpy as np
from scipy.spatial.distance import cdist
from scipy.linalg import eigh
from ..utils import electrode_spectrum_matrix


# Optimal parameters from research
BEST_ALPHA = 0.1  # SA-GSA mixing parameter with best results
BAND_LO = 700.0   # Hz
BAND_HI = 1700.0  # Hz  
KNN_K = 5


def build_electrode_graph(xyz, protocol, alpha=0.0):
    """
    Build electrode graph combining spatial and injection patterns.
    
    Args:
        xyz: Electrode positions (32 x 3)
        protocol: Protocol matrix (measurements x 3)
        alpha: Mixing parameter (0=spatial only, 1=injection only)
        
    Returns:
        tuple: (eigenvalues, eigenvectors) of normalized Laplacian
    """
    
    # Spatial distance matrix
    D_geo = cdist(xyz, xyz)
    D_geo_norm = D_geo / D_geo.max()
    
    if alpha > 0:
        # Injection pattern signatures
        P = protocol.astype(int)
        inj_pair_id = np.array([f"{a}-{b}" for a, b in P[:, :2]])
        unique_inj = np.unique(inj_pair_id)
        inj_to_col = {u: j for j, u in enumerate(unique_inj)}
        
        inj_signature = np.zeros((32, len(unique_inj)))
        for r in range(P.shape[0]):
            e = P[r, 2] - 1
            if 0 <= e < 32:
                inj_signature[e, inj_to_col[inj_pair_id[r]]] += 1
        
        # Normalize injection signatures
        row_sums = inj_signature.sum(axis=1, keepdims=True)
        inj_signature_norm = inj_signature / np.clip(row_sums, 1e-9, None)
        
        # Cosine distance between injection patterns
        def cosine_dist(A, B):
            A_n = A / np.clip(np.linalg.norm(A, axis=1, keepdims=True), 1e-9, None)
            B_n = B / np.clip(np.linalg.norm(B, axis=1, keepdims=True), 1e-9, None)
            return 1.0 - A_n @ B_n.T
        
        D_inj = cosine_dist(inj_signature_norm, inj_signature_norm)
        D_inj_norm = D_inj / D_inj.max()
        
        # Combined distance
        D_combined = (1 - alpha) * D_geo_norm + alpha * D_inj_norm
    else:
        D_combined = D_geo_norm
    
    # Build k-NN graph
    sigma = np.median(np.sort(D_combined, axis=1)[:, 1:KNN_K + 1])
    W = np.zeros((32, 32))
    
    for i in range(32):
        nbrs = np.argsort(D_combined[i])[1:KNN_K + 1]
        for j in nbrs:
            w = np.exp(-(D_combined[i, j] ** 2) / (2 * sigma ** 2))
            W[i, j] = w
            W[j, i] = w
    
    # Normalized Laplacian
    deg = W.sum(axis=1)
    d_inv_sqrt = 1.0 / np.sqrt(np.clip(deg, 1e-6, None))
    L_norm = np.eye(32) - (d_inv_sqrt[:, None] * W * d_inv_sqrt[None, :])
    
    eigvals, eigvecs = eigh(L_norm)
    return eigvals, eigvecs


def compute_gsa_features(voltages, freq, protocol, xyz, alpha=0.0):
    """
    Compute GSA or SA-GSA features for all subjects.
    
    Args:
        voltages: Voltage data (subjects x measurements x frequencies)
        freq: Frequency array
        protocol: Protocol matrix
        xyz: Electrode positions
        alpha: SA-GSA mixing parameter (0.0=GSA, 0.1=optimal SA-GSA)
        
    Returns:
        numpy array: GSA features per subject
    """
    
    n_subjects = voltages.shape[0]
    
    # Build graph
    eigvals, eigvecs = build_electrode_graph(xyz, protocol, alpha)
    
    # Get electrode spectrum matrices
    X_all = np.full((n_subjects, 32, len(freq)), np.nan)
    for k in range(n_subjects):
        M = electrode_spectrum_matrix(voltages[k], protocol)
        # Fill NaNs with row means, then zeros
        row_mean = np.nanmean(M, axis=1, keepdims=True)
        M = np.where(np.isfinite(M), M, row_mean)
        M = np.where(np.isfinite(M), M, 0.0)
        X_all[k] = M
    
    # Graph Fourier transform
    C_all = np.stack([eigvecs.T @ X_all[k] for k in range(n_subjects)])
    
    # Identify healthy subjects for template
    healthy_mask = np.array([True] * n_subjects)  # Will be set by caller
    
    return _compute_gsa_from_coeffs(C_all, freq, healthy_mask)


def _compute_gsa_from_coeffs(C_all, freq, healthy_mask):
    """
    Compute GSA features from graph Fourier coefficients.
    
    Args:
        C_all: Graph Fourier coefficients (subjects x nodes x frequencies)
        freq: Frequency array
        healthy_mask: Boolean mask for healthy subjects
        
    Returns:
        numpy array: GSA features per subject
    """
    
    n_subjects = C_all.shape[0]
    band_mask = (freq >= BAND_LO) & (freq <= BAND_HI)
    
    # Healthy reference (for patients) or LOO (for healthy subjects)
    C_healthy = C_all[healthy_mask]
    mu_healthy_full = np.nanmean(C_healthy, axis=0)
    sd_healthy_full = np.nanstd(C_healthy, axis=0, ddof=1)
    
    gsa_features = np.zeros(n_subjects)
    
    for k in range(n_subjects):
        if healthy_mask[k]:
            # Leave-one-out for healthy subjects
            k_in_healthy = np.where(healthy_mask)[0]
            kp = int(np.where(k_in_healthy == k)[0][0])
            other = np.delete(C_healthy, kp, axis=0)
            mu = np.nanmean(other, axis=0)
            sd = np.nanstd(other, axis=0, ddof=1)
        else:
            # Full healthy pool for patients
            mu = mu_healthy_full
            sd = sd_healthy_full
        
        # Z-score and integrate over frequency band
        Z = (C_all[k] - mu) / np.clip(sd, 1e-3, None)
        Z2 = Z[:, band_mask] ** 2
        z2_valid = Z2[np.isfinite(Z2)]
        
        if z2_valid.size >= 20:
            gsa_features[k] = float(np.mean(z2_valid))
        else:
            gsa_features[k] = np.nan
    
    return gsa_features


def compute_optimal_sagsa(data):
    """
    Compute optimal SA-GSA features (alpha=0.2) for the dataset.
    
    Args:
        data: Dict from data_loader with keys: voltages, freq, protocol, nominal_pos, labels
        
    Returns:
        numpy array: SA-GSA features per subject
    """
    
    voltages = data["voltages"] 
    freq = data["freq"]
    protocol = data["protocol"]
    xyz = data["nominal_pos"][:32]
    labels = data["labels"]
    
    # print(f"Computing SA-GSA features (α={BEST_ALPHA}, band={BAND_LO}-{BAND_HI} Hz)")
    
    # Build SA-GSA graph
    eigvals, eigvecs = build_electrode_graph(xyz, protocol, BEST_ALPHA)
    
    # Get electrode spectrum matrices
    n_subjects = voltages.shape[0]
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
    
    # Compute SA-GSA features
    sagsa_features = _compute_gsa_from_coeffs(C_all, freq, healthy_mask)
    
    print(f"SA-GSA features computed for {n_subjects} subjects")
    print(f"Healthy subjects: {healthy_mask.sum()}")
    print(f"SA-GSA range: [{np.nanmin(sagsa_features):.3f}, {np.nanmax(sagsa_features):.3f}]")
    
    return sagsa_features


def compute_standard_gsa(data):
    """
    Compute standard GSA features (alpha=0.0) for comparison.
    
    Args:
        data: Dict from data_loader
        
    Returns:
        numpy array: GSA features per subject
    """
    
    voltages = data["voltages"]
    freq = data["freq"] 
    protocol = data["protocol"]
    xyz = data["nominal_pos"][:32]
    labels = data["labels"]
    
    print(f"Computing GSA features (α=0.0, band={BAND_LO}-{BAND_HI} Hz)")
    
    # Build spatial-only graph
    eigvals, eigvecs = build_electrode_graph(xyz, protocol, alpha=0.0)
    
    # Get electrode spectrum matrices
    n_subjects = voltages.shape[0]
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
    
    # Compute GSA features
    gsa_features = _compute_gsa_from_coeffs(C_all, freq, healthy_mask)
    
    print(f"GSA features computed for {n_subjects} subjects")
    
    return gsa_features