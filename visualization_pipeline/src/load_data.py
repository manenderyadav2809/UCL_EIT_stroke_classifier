"""
load_data.py
------------
Load electrode contribution data from a CSV file.

Expected CSV columns (case-sensitive):
  Patient          : str  — patient identifier (e.g. "Patient_01", "Patient_04a")
  Condition        : str  — "ischaemia" or "haemorrhage"
  Electrode_Name   : str  — 10-10 electrode label (e.g. "Fp1", "Cz", "T7")
  Electrode_Index  : int  — electrode position in the recording (1..32)
  Contribution     : float — SA-GSA contribution score for this electrode

Optional columns (ignored by this script): Avg_Z_Score, Max_Z_Score, Rank.
"""

from pathlib import Path

import pandas as pd


REQUIRED_COLS = ["Patient", "Condition", "Electrode_Name",
                 "Electrode_Index", "Contribution"]


def load_contributions(csv_path: Path) -> pd.DataFrame:
    """
    Read the contribution CSV. Validates required columns are present
    and returns a DataFrame sorted by (Patient, Electrode_Index).

    Raises:
        FileNotFoundError if csv_path doesn't exist
        ValueError if any required column is missing
    """
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(
            f"Contribution CSV not found at: {csv_path}\n"
            f"Edit config.py INPUT_CSV to point to your file."
        )

    df = pd.read_csv(csv_path)

    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(
            f"CSV is missing required columns: {missing}\n"
            f"Found columns: {list(df.columns)}\n"
            f"Required: {REQUIRED_COLS}"
        )

    # Normalize whitespace in string columns
    for col in ["Patient", "Condition", "Electrode_Name"]:
        df[col] = df[col].astype(str).str.strip()

    df = df.sort_values(["Patient", "Electrode_Index"]).reset_index(drop=True)
    return df


def get_patient_data(df: pd.DataFrame, patient_id: str) -> pd.DataFrame:
    """Return the subset of the DataFrame for one patient."""
    sub = df[df["Patient"] == patient_id]
    if sub.empty:
        raise KeyError(f"Patient {patient_id!r} not found in CSV")
    return sub


def list_patients(df: pd.DataFrame) -> list[str]:
    """Return sorted list of patient IDs in the CSV."""
    return sorted(df["Patient"].unique())
