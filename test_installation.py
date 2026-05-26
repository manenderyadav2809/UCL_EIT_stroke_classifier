#!/usr/bin/env python3
"""
Test script to verify the EIT analysis pipeline is correctly installed.

Usage:
    python test_installation.py
"""

import sys
from pathlib import Path

def test_imports():
    """Test if all required modules can be imported."""
    print("Testing imports...")
    
    # Test basic scientific libraries
    try:
        import numpy as np
        import scipy
        import matplotlib.pyplot as plt
        import pandas as pd
        import sklearn
        print("✓ Core scientific libraries OK")
    except ImportError as e:
        print(f"✗ Core libraries failed: {e}")
        return False
    
    # Test local src modules
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from src.data_loader import load_eit_data
        from src.evaluation import evaluate_classifier
        from src.features import compute_hmd_features, compute_optimal_sagsa
        print("✓ Local src modules OK")
    except ImportError as e:
        print(f"✗ Local modules failed: {e}")
        return False
    
    return True

def test_data_files():
    """Test if required data files exist."""
    print("\nTesting data files...")
    
    base_dir = Path(__file__).parent
    required_files = [
        "data/eit_cache.npz",
        "data/UCL_Stroke_EIT_Dataset.mat",
    ]
    
    missing_files = []
    for file_path in required_files:
        full_path = base_dir / file_path
        if full_path.exists():
            size_mb = full_path.stat().st_size / (1024 * 1024)
            print(f"✓ {file_path} ({size_mb:.1f} MB)")
        else:
            print(f"✗ {file_path} - NOT FOUND")
            missing_files.append(file_path)
    
    return len(missing_files) == 0

def test_data_loading():
    """Test if data can be loaded successfully."""
    print("\nTesting data loading...")
    
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from src.data_loader import load_eit_data, get_27_subject_cohort
        
        print("  Loading EIT data...")
        data = load_eit_data()
        print(f"  ✓ Loaded {len(data['names'])} total subjects")
        
        print("  Getting 27-subject cohort...")
        data_27 = get_27_subject_cohort(data)
        print(f"  ✓ 27-subject cohort: {len(data_27['names'])} subjects")
        
        # Check data structure
        labels = data_27['labels']
        n_healthy = int((labels == "healthy").sum())
        n_stroke = len(labels) - n_healthy
        print(f"  ✓ {n_healthy} healthy, {n_stroke} stroke patients")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Data loading failed: {e}")
        return False

def test_visualization_dependencies():
    """Test visualization pipeline dependencies."""
    print("\nTesting visualization dependencies...")
    
    try:
        import mne
        print("✓ MNE-Python available")
    except ImportError:
        print("✗ MNE-Python not available (needed for visualization)")
        print("  Install with: pip install mne")
        return False
    
    # Check visualization pipeline structure
    vis_dir = Path(__file__).parent / "visualization_pipeline"
    required_vis_files = [
        "config.py",
        "run_analysis.py", 
        "src/load_data.py",
        "src/clinical_interpretations.py",
        "requirements.txt"
    ]
    
    missing_vis = []
    for file_path in required_vis_files:
        if (vis_dir / file_path).exists():
            print(f"✓ visualization_pipeline/{file_path}")
        else:
            print(f"✗ visualization_pipeline/{file_path} - NOT FOUND")
            missing_vis.append(file_path)
    
    return len(missing_vis) == 0

def main():
    print("EIT Stroke Analysis Pipeline - Installation Test")
    print("=" * 60)
    
    all_tests = [
        ("Import Test", test_imports),
        ("Data Files Test", test_data_files),
        ("Data Loading Test", test_data_loading),
        ("Visualization Test", test_visualization_dependencies)
    ]
    
    results = []
    for test_name, test_func in all_tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name:25s}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 All tests passed! The pipeline is ready to use.")
        print("\nNext steps:")
        print("  1. Run full pipeline: python run_pipeline.py")
        print("  2. Or run components individually:")
        print("     - Classification: python experiments/stroke_detection.py")
        print("     - Electrode analysis: python electrode_analysis/detailed_electrode_contributions.py")
        print("     - Visualization: cd visualization_pipeline && python run_analysis.py")
    else:
        print(f"\n❌ {len(results) - passed} test(s) failed. Please fix issues before running the pipeline.")
    
    return passed == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)