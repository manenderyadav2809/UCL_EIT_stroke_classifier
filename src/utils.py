"""
Common utilities for EIT stroke classification.
"""

import numpy as np

# Constants
SNR_DB = 47.5


def channel_noise_floor(V, snr_db=SNR_DB):
    """Compute channel noise floor based on peak signal."""
    peak = np.nanmax(np.abs(V), axis=1)
    return peak * (10 ** (-snr_db / 20))


def log_abs_mask(V, floor_mult=3):
    """
    Compute log|V| with noise floor masking.
    
    Args:
        V: Voltage matrix (measurements x frequencies)
        floor_mult: Multiplier for noise floor threshold
        
    Returns:
        Log magnitude with noise-masked values as NaN
    """
    absV = np.abs(V)
    floor = channel_noise_floor(V)[:, None]
    good = absV > (floor_mult * floor)
    
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.log(np.where(good, absV, np.nan))


def electrode_spectrum_matrix(V, protocol):
    """
    Compute per-electrode spectrum matrix.
    
    Args:
        V: Voltage matrix (measurements x frequencies)  
        protocol: Protocol matrix (measurements x 3)
        
    Returns:
        Spectrum matrix (32 electrodes x frequencies)
    """
    P = protocol.astype(int)
    out = np.full((32, V.shape[1]), np.nan)
    L = log_abs_mask(V)
    
    for e in range(32):
        rows = np.where(P[:, 2] == e + 1)[0]
        if rows.size == 0:
            continue
        out[e] = np.nanmean(L[rows], axis=0)
    
    return out


def safe_standardize(X_train, X_test):
    """Safely standardize features, handling NaN and constant features."""
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        mu = np.nanmean(X_train, axis=0)
        sd = np.nanstd(X_train, axis=0, ddof=1)
    
    sd = np.where((sd < 1e-8) | ~np.isfinite(sd), 1.0, sd)
    mu = np.where(np.isfinite(mu), mu, 0.0)
    
    X_train_std = np.where(np.isfinite(X_train), (X_train - mu) / sd, 0.0)
    X_test_std = np.where(np.isfinite(X_test), (X_test - mu) / sd, 0.0)
    
    return X_train_std, X_test_std


def base_subject_id(name):
    """Extract base subject ID (remove 'a'/'b' suffixes)."""
    name = str(name)
    return name[:-1] if name[-1] in ("a", "b") else name