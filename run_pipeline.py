#!/usr/bin/env python3
"""
Complete EIT Stroke Analysis Pipeline Runner
============================================

This script runs the complete analysis pipeline in the correct order:

1. Classification experiment (stroke vs healthy)
2. Electrode importance analysis (generates CSV)
3. Clinical visualization (generates HTML report)

Usage:
    python run_pipeline.py

Make sure all dependencies are installed first:
    pip install -r requirements.txt
    cd visualization_pipeline && pip install -r requirements.txt
"""

import subprocess
import sys
from pathlib import Path
import shutil
import glob

def run_command(cmd, description, cwd=None):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    print(f"RUNNING: {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, shell=True, check=True, cwd=cwd, 
                              capture_output=False, text=True)
        print(f"✓ SUCCESS: {description}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ FAILED: {description}")
        print(f"Error: {e}")
        return False

def main():
    print("EIT Stroke Analysis Pipeline")
    print("=" * 60)
    
    base_dir = Path(__file__).parent
    
    # Step 1: Run classification experiment
    print("\nStep 1: Running stroke classification experiment...")
    if not run_command("python experiments/stroke_detection.py", 
                      "Stroke vs Healthy Classification", cwd=base_dir):
        print("Classification experiment failed. Stopping.")
        return False
    
    # Step 2: Run electrode analysis
    print("\nStep 2: Generating electrode importance analysis...")
    if not run_command("python electrode_analysis/detailed_electrode_contributions.py", 
                      "Electrode Contribution Analysis", cwd=base_dir):
        print("Electrode analysis failed. Stopping.")
        return False
    
    # Step 3: Copy CSV to visualization pipeline
    print("\nStep 3: Preparing data for visualization...")
    
    # Find the most recent electrode contributions CSV
    csv_pattern = "plots/detailed_electrode_contributions_*.csv"
    csv_files = glob.glob(str(base_dir / csv_pattern))
    
    if not csv_files:
        print("No electrode contributions CSV found. Make sure step 2 completed successfully.")
        return False
    
    # Get the most recent file
    latest_csv = max(csv_files, key=lambda f: Path(f).stat().st_mtime)
    dest_csv = base_dir / "visualization_pipeline" / "data" / "contribution.csv"
    
    # Create destination directory
    dest_csv.parent.mkdir(parents=True, exist_ok=True)
    
    # Copy the CSV
    shutil.copy2(latest_csv, dest_csv)
    print(f"✓ Copied {Path(latest_csv).name} to visualization pipeline")
    
    # Step 4: Run visualization pipeline
    print("\nStep 4: Generating clinical visualizations...")
    vis_dir = base_dir / "visualization_pipeline"
    if not run_command("python run_analysis.py", 
                      "Clinical Visualization Pipeline", cwd=vis_dir):
        print("Visualization pipeline failed. Stopping.")
        return False
    
    # Summary
    print("\n" + "=" * 60)
    print("PIPELINE COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    
    output_dir = vis_dir / "output"
    print(f"\nResults available in:")
    print(f"  Classification plots: {base_dir / 'plots'}")
    print(f"  Electrode CSV files: {base_dir / 'plots'}")
    print(f"  Clinical report: {output_dir / 'report.html'}")
    print(f"  Visualization PNGs: {output_dir / 'figures'}")
    
    print(f"\n📊 Open the main report:")
    print(f"  {output_dir / 'report.html'}")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)