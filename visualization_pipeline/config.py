"""
config.py
---------
All user-editable settings for the stroke EIT analysis pipeline.
Edit paths to match your system if the defaults don't fit.
"""

from pathlib import Path

# Repo root (this file's directory)
ROOT = Path(__file__).parent.resolve()

# ---------------------------------------------------------------------------
# INPUT PATHS
# ---------------------------------------------------------------------------
# Path to your contribution CSV. Expected columns:
#   Patient, Condition, Electrode_Name, Electrode_Index, Contribution
# (plus optional: Avg_Z_Score, Max_Z_Score, Rank — ignored by this script)
INPUT_CSV = ROOT / "data" / "contribution.csv"

# Directory containing the radiology PDFs. File naming: Patient01.pdf,
# Patient03.pdf, etc. Patients without PDFs are still rendered (EIT only).
PDF_DIR = ROOT / "data" / "reports"

# ---------------------------------------------------------------------------
# OUTPUT PATHS
# ---------------------------------------------------------------------------
# Single output folder. Created if it doesn't exist.
OUTPUT_DIR = ROOT / "output"

# Subdirectories inside the output dir for the per-patient PNGs.
LESION_ATLAS_DIR = OUTPUT_DIR / "figures" / "lesion_atlas"
EIT_MAPS_DIR     = OUTPUT_DIR / "figures" / "electrode_maps"

# Combined HTML report.
REPORT_HTML = OUTPUT_DIR / "report.html"

# ---------------------------------------------------------------------------
# ANALYSIS OPTIONS
# ---------------------------------------------------------------------------
# Number of top electrodes to highlight in the EIT electrode maps.
# Everything else (remaining lower-priority electrodes) is shown in grey.
TOP_K = 5

# Smoothing not used in this version — kept here as a placeholder if
# you want to add it back. Set TOP_K_SMOOTHING_SIGMA_MM = None to disable.
TOP_K_SMOOTHING_SIGMA_MM = None

# Color map for contribution heatmaps (matplotlib colormap name).
CMAP = "RdYlBu_r"

# Rendering DPI for PNG output.
DPI = 110

# ---------------------------------------------------------------------------
# WHAT'S IN PATIENT IDS
# ---------------------------------------------------------------------------
# CSV patient IDs may have a trailing letter (e.g. "Patient_04a" for the
# first timepoint, "Patient_04b" for the second). The PDF reports don't use
# this suffix — Patient04.pdf covers all timepoints. The script strips the
# trailing letter when mapping a CSV patient ID to its PDF.
