#!/usr/bin/env python3
"""
run_analysis.py
---------------
End-to-end entry point. Reads the contribution CSV and PDF reports
(or annotated lesion data), renders all figures, and builds the
combined HTML report.

Usage:
    python run_analysis.py

All paths and options are in config.py.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

# Make sure the package is importable when this is run directly
sys.path.insert(0, str(Path(__file__).parent))

import config
from src.load_data import load_contributions, list_patients
from src.render_lesion_atlas import render_all as render_lesion_atlas_all
from src.render_eit import render_all as render_eit_all
from src.build_html_report import build_report


def main():
    t0 = time.time()
    print(f"Stroke EIT Analysis Pipeline")
    print(f"{'=' * 60}")
    print(f"Input CSV:    {config.INPUT_CSV}")
    print(f"PDF dir:      {config.PDF_DIR}")
    print(f"Output dir:   {config.OUTPUT_DIR}")
    print(f"Top-K:        {config.TOP_K}")
    print()

    # 1. Load contribution data
    print("[1/4] Loading contribution data ...")
    df = load_contributions(config.INPUT_CSV)
    patients = list_patients(df)
    print(f"      → Loaded {len(patients)} patients, "
          f"{len(df)} electrode entries")

    # 2. Render lesion atlas figures
    print("[2/4] Rendering lesion atlas figures ...")
    print("      (one per scan; both schematic and anatomical variants)")
    atlas_paths = render_lesion_atlas_all(config.LESION_ATLAS_DIR,
                                           dpi=config.DPI)
    print(f"      → {len(atlas_paths)} files in {config.LESION_ATLAS_DIR}")

    # 3. Render EIT electrode visualizations
    print("[3/4] Rendering EIT electrode visualizations ...")
    print(f"      (top-{config.TOP_K} electrodes per patient based on clinical context)")
    eit_paths = render_eit_all(df, config.EIT_MAPS_DIR,
                                top_k=config.TOP_K,
                                cmap=config.CMAP,
                                dpi=config.DPI)
    print(f"      → {len(eit_paths)} files in {config.EIT_MAPS_DIR}")

    # 4. Build HTML report
    print("[4/4] Building combined HTML report ...")
    report_path = build_report(df,
                                config.LESION_ATLAS_DIR,
                                config.EIT_MAPS_DIR,
                                config.REPORT_HTML,
                                top_k=config.TOP_K)
    size_kb = report_path.stat().st_size // 1024
    print(f"      → {report_path} ({size_kb} KB)")

    elapsed = time.time() - t0
    print()
    print(f"Done in {elapsed:.1f}s")
    print()
    print(f"Open in browser:")
    print(f"  {report_path}")
    print()
    print(f"Per-patient PNGs (for direct embedding elsewhere):")
    print(f"  Lesion atlas: {config.LESION_ATLAS_DIR}")
    print(f"  EIT figures:  {config.EIT_MAPS_DIR}")


if __name__ == "__main__":
    main()
