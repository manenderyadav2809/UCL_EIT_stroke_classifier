"""
UCL Stroke EIT Dataset loader and preprocessing pipeline.
Handles MATLAB v7.3 HDF5 format with robust preprocessing.
"""

import h5py
import numpy as np
from pathlib import Path
from scipy.spatial.distance import cdist

# Configuration
MAT_PATH = Path("data/UCL_Stroke_EIT_Dataset.mat")
CACHE_PATH = Path("data/eit_cache.npz")
NAN_THRESHOLD = 647
KNN_K = 5
IMPUTE_LAMBDA = 1.0
SNR_DB = 47.5


def decode_uint16_string(arr):
    """Decode MATLAB uint16 string arrays."""
    return "".join(chr(int(c)) for c in arr.ravel())


def is_ascii(arr):
    """Check if array contains ASCII characters."""
    return np.all((arr >= 32) & (arr <= 126))


def deref(obj, f):
    """Recursively resolve HDF5 references safely."""
    while isinstance(obj, h5py.Reference):
        if not obj:
            return None
        obj = f[obj]

    data = obj[()]

    # Handle uint16: distinguish string vs numeric
    if isinstance(data, np.ndarray) and data.dtype.kind in ("u", "i"):
        if data.ndim >= 1 and is_ascii(data):
            return decode_uint16_string(data)
        else:
            return data  # keep numeric

    # Resolve nested references
    if isinstance(data, np.ndarray) and data.dtype == object:
        return np.array([deref(x, f) for x in data.ravel()])

    return data


def safe_int_array(val):
    """Convert to int array safely, ignoring non-numeric garbage."""
    arr = np.array(val).ravel()

    clean = []
    for x in arr:
        if isinstance(x, (int, float, np.integer, np.floating)):
            clean.append(int(x))

    return np.array(clean, dtype=int) if clean else np.array([], dtype=int)


def impute_missing_values(vc, protocol):
    """Graph-based imputation for missing voltage values."""
    out = vc.copy()
    inj_ids = np.array([f"{a}-{b}" for a,b in protocol[:,:2]])
    unique_inj = np.unique(inj_ids)

    # Build electrode graph
    nom_xyz = load_electrode_positions()
    D = cdist(nom_xyz, nom_xyz)
    sigma = np.median(np.sort(D, axis=1)[:, 1:KNN_K+1])
    W = np.zeros_like(D)

    for i in range(32):
        neighbors = np.argsort(D[i])[1:KNN_K+1]
        for j in neighbors:
            w = np.exp(-(D[i,j]**2)/(2*sigma**2))
            W[i,j] = w
            W[j,i] = w

    L_mat = np.diag(W.sum(axis=1)) - W

    # Impute per injection pattern
    for inj in unique_inj:
        rows = np.where(inj_ids == inj)[0]
        vplus = protocol[rows,2]-1

        for fi in range(vc.shape[1]):
            vals = vc[rows,fi]

            if np.all(~np.isnan(vals)):
                continue

            elec = np.full(32, np.nan)

            for r,v,vp in zip(rows, vals, vplus):
                if not np.isnan(v):
                    vp_int = int(vp)
                    if 0 <= vp_int < 32:
                        elec[vp_int] = v if np.isnan(elec[vp_int]) else 0.5*(elec[vp_int]+v)

            obs = ~np.isnan(elec)
            if obs.sum() < 5:
                continue

            M = np.diag(obs.astype(float))
            b = M @ np.nan_to_num(elec)
            A = M + IMPUTE_LAMBDA * L_mat

            v_filled = np.linalg.solve(A, b)

            for r,v,vp in zip(rows, vals, vplus):
                if np.isnan(v):
                    vp_int = int(vp)
                    if 0 <= vp_int < 32:
                        out[r,fi] = v_filled[vp_int]

    return out


def load_electrode_positions():
    """Load nominal electrode positions from cache or file."""
    if CACHE_PATH.exists():
        cache = np.load(CACHE_PATH, allow_pickle=True)
        return cache["nominal_pos"][:32]
    
    with h5py.File(MAT_PATH, "r") as f:
        settings = f["EITSETTINGS"]
        return np.array(settings["ElectrodePosition"][()]).T[:32]


def load_eit_data():
    """
    Load and preprocess UCL Stroke EIT Dataset.
    
    Returns:
        dict: Processed data with keys:
            - freq: frequency array
            - protocol: measurement protocol  
            - nominal_pos: electrode positions
            - voltages: voltage measurements (subjects x measurements x frequencies)
            - labels: subject classifications
            - names: subject IDs
    """
    
    if CACHE_PATH.exists():
        print(f"Loading cached data from {CACHE_PATH}")
        cache = np.load(CACHE_PATH, allow_pickle=True)
        return {
            "freq": cache["freq"],
            "protocol": cache["protocol"], 
            "nominal_pos": cache["nominal_pos"],
            "voltages": cache["voltages"],
            "labels": cache["labels"],
            "names": cache["names"]
        }
    
    print("Processing UCL EIT Dataset...")
    assert MAT_PATH.exists(), f"Dataset not found: {MAT_PATH}"

    with h5py.File(MAT_PATH, "r") as f:
        # Load settings
        settings = f["EITSETTINGS"]
        freq = np.array(settings["Freq"][()]).ravel()
        protocol = np.array(settings["Protocol"][()]).T
        nominal_pos = np.array(settings["ElectrodePosition"][()]).T

        print(f"Frequencies: {len(freq)} points ({freq.min():.1f}-{freq.max():.1f} Hz)")
        print(f"Protocol shape: {protocol.shape}")
        print(f"Electrode positions: {nominal_pos.shape}")

        # Load subject data
        eitdata = f["EITDATA"]
        fields = ["NameTag", "Classification", "SubClassification",
                  "VoltagesCleaned", "VoltagesFull", "RemovedChannels", "Diagnosis"]

        n_entries = eitdata["NameTag"].shape[0]
        print(f"Processing {n_entries} recordings...")

        subjects = []
        for i in range(n_entries):
            rec = {}
            for fld in fields:
                ref_arr = np.asarray(eitdata[fld][()]).ravel()
                val = deref(ref_arr[i], f)

                if val is None:
                    rec[fld] = None
                elif fld in ("VoltagesCleaned", "VoltagesFull"):
                    rec[fld] = np.array(val).T  # (930, 17)
                elif fld == "RemovedChannels":
                    rec[fld] = safe_int_array(val)
                else:
                    rec[fld] = str(val)

            subjects.append(rec)

    # Filter by NaN threshold
    print(f"\nFiltering subjects (NaN threshold: {NAN_THRESHOLD})")
    keep_mask = []
    for s in subjects:
        vc = s["VoltagesCleaned"]
        n_nan = int(np.isnan(vc).sum())
        s["n_nan"] = n_nan
        keep_mask.append(n_nan <= NAN_THRESHOLD)

    kept = [s for s, k in zip(subjects, keep_mask) if k]
    print(f"Kept {len(kept)}/{len(subjects)} recordings")

    # Impute missing values
    print("Imputing missing values...")
    for s in kept:
        vc = s["VoltagesCleaned"]
        if s["n_nan"] == 0:
            s["VoltagesImputed"] = vc
        else:
            s["VoltagesImputed"] = impute_missing_values(vc, protocol)

    # Create final data structure
    voltages = np.stack([s["VoltagesImputed"] for s in kept])
    labels = np.array([s["Classification"] for s in kept])
    names = np.array([s["NameTag"] for s in kept])

    # Summary
    n_healthy = sum(s["Classification"] == "healthy" for s in kept)
    n_isch = sum(s["Classification"] == "ischaemia" for s in kept)  
    n_haem = sum(s["Classification"] == "haemorrhage" for s in kept)
    print(f"\nFinal cohort: {n_healthy} healthy, {n_isch} ischaemia, {n_haem} haemorrhage")

    # Cache results
    cache_data = {
        "freq": freq,
        "protocol": protocol,
        "nominal_pos": nominal_pos,
        "voltages": voltages,
        "labels": labels,
        "names": names
    }
    
    CACHE_PATH.parent.mkdir(exist_ok=True)
    np.savez_compressed(CACHE_PATH, **cache_data)
    print(f"Cached data to {CACHE_PATH}")

    return cache_data


def get_27_subject_cohort(data):
    """
    Filter to canonical 27-subject cohort used in final analysis.
    
    Args:
        data: Dict from load_eit_data()
        
    Returns:
        dict: Filtered data for 27 subjects
    """
    
    COHORT_27 = {
        "healthy": [
            "Subject_01b", "Subject_02a", "Subject_03b", "Subject_04a", "Subject_05a",
            "Subject_06a", "Subject_07a", "Subject_08a", "Subject_09a", "Subject_10a",
        ],
        "ischaemia": [
            "Patient_01", "Patient_04a", "Patient_09", "Patient_12a", "Patient_15",
            "Patient_16", "Patient_18", "Patient_19b", "Patient_25b", "Patient_26",
        ],
        "haemorrhage": [
            "Patient_03", "Patient_05", "Patient_06a", "Patient_17", "Patient_20",
            "Patient_23b", "Patient_24",
        ],
    }
    
    allowed = sum(COHORT_27.values(), [])
    names_str = [str(nm) for nm in data["names"]]
    keep_mask = np.array([nm in allowed for nm in names_str])
    
    if keep_mask.sum() != 27:
        found = set(np.array(names_str)[keep_mask])
        missing = set(allowed) - found
        extra = found - set(allowed)
        if missing:
            print(f"WARNING: Missing subjects: {missing}")
        if extra:
            print(f"WARNING: Extra subjects: {extra}")
    
    filtered_data = {
        "freq": data["freq"],
        "protocol": data["protocol"],
        "nominal_pos": data["nominal_pos"],
        "voltages": data["voltages"][keep_mask],
        "labels": data["labels"][keep_mask], 
        "names": data["names"][keep_mask]
    }
    
    print(f"Filtered to 27-subject cohort: {keep_mask.sum()} subjects")
    return filtered_data


if __name__ == "__main__":
    data = load_eit_data()
    data_27 = get_27_subject_cohort(data)
    
    print("\nDataset Summary:")
    print(f"Total subjects: {len(data_27['names'])}")
    print(f"Frequencies: {len(data_27['freq'])}")
    print(f"Voltage shape: {data_27['voltages'].shape}")
    
    unique, counts = np.unique(data_27['labels'], return_counts=True)
    for label, count in zip(unique, counts):
        print(f"{label}: {count}")