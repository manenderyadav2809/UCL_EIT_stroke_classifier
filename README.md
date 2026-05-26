# EIT Stroke Classification Pipeline - Final Code Package

This package contains the complete pipeline for EIT-based stroke classification analysis, including feature extraction, classification evaluation, electrode contribution analysis, and clinical visualization.

## Package Structure

```
final_code_25may/
├── README.md                           ← This file
├── requirements.txt                    ← Python dependencies
├── data/                              ← Dataset and cached data
│   ├── UCL_Stroke_EIT_Dataset.mat     ← Original dataset
│   ├── eit_cache.npz                  ← Preprocessed EIT data
│   └── report_files/                  ← Clinical PDF reports
├── src/                               ← Core library modules
│   ├── data_loader.py                 ← Data loading utilities
│   ├── evaluation.py                  ← Classification evaluation
│   ├── utils.py                       ← General utilities
│   └── features/                      ← Feature extraction
│       ├── hmd.py                     ← HMD features
│       └── gsa.py                     ← GSA/SA-GSA features
├── experiments/                       ← Main classification experiments
│   └── stroke_detection.py            ← Stroke vs healthy classification
├── electrode_analysis/                ← Electrode importance analysis
│   └── detailed_electrode_contributions.py  ← Generate electrode CSV
└── visualization_pipeline/            ← Clinical visualization system
    ├── run_analysis.py                ← Main visualization entry point
    ├── config.py                      ← Configuration settings
    ├── load_data.py                   ← CSV data loader
    ├── clinical_interpretations.py    ← Clinical annotations
    ├── head_anatomy.py                ← 3D head model
    ├── render_lesion_atlas.py         ← Lesion visualization
    ├── render_eit.py                  ← Electrode visualization
    ├── build_html_report.py           ← HTML report generation
    └── requirements.txt               ← Visualization dependencies
```

## Quick Start

### 1. Install Dependencies

For the main analysis:
```bash
pip install numpy scipy matplotlib scikit-learn pandas h5py
```

For the visualization pipeline:
```bash
cd visualization_pipeline
pip install -r requirements.txt
```

### 2. Run Classification Experiment

```bash
# Run stroke vs healthy classification
python experiments/stroke_detection.py
```

This will:
- Load the 27-subject cohort
- Compute HMD, GSA, and SA-GSA features
- Evaluate classification performance
- Generate performance comparison plots

### 3. Generate Electrode Importance Data

```bash
# Generate detailed electrode contributions CSV
python electrode_analysis/detailed_electrode_contributions.py
```

This creates CSV files with columns:
- Patient, Condition, Electrode_Name, Electrode_Index, Contribution, Avg_Z_Score, Max_Z_Score, Rank

### 4. Create Clinical Visualizations

```bash
# Copy generated CSV to visualization pipeline
cp plots/detailed_electrode_contributions_*.csv visualization_pipeline/data/contribution.csv

# Run visualization pipeline
cd visualization_pipeline
python run_analysis.py
```

This generates:
- Individual electrode importance maps
- Lesion atlas visualizations  
- Combined HTML report

## Key Components

### 1. Classification Pipeline (`experiments/stroke_detection.py`)
- Compares HMD baseline vs GSA vs SA-GSA methods
- Uses leave-one-patient-out cross-validation
- Statistical significance testing with permutations

### 2. Electrode Analysis (`electrode_analysis/detailed_electrode_contributions.py`)
- Computes SA-GSA contributions for each electrode
- Generates detailed per-patient electrode rankings
- **Creates the CSV file used by the visualization pipeline**

### 3. Visualization System (`visualization_pipeline/`)
- Maps electrode contributions to 3D head positions
- Integrates with clinical radiology reports
- **De-emphasized clinical terminology for general use**
- Generates publication-ready figures

## Data Flow

1. **Raw Data** → `UCL_Stroke_EIT_Dataset.mat` (Original UCL dataset)
2. **Preprocessing** → `eit_cache.npz` (Cached processed data)
3. **Classification** → `stroke_detection.py` (Performance evaluation)
4. **Electrode Analysis** → `detailed_electrode_contributions.py` (CSV generation)
5. **Visualization** → `visualization_pipeline/` (Clinical reports)

## Configuration

### Stroke Detection
- Edit `stroke_detection.py` to modify feature parameters
- Classification uses optimal SA-GSA (α=0.2) by default

### Electrode Analysis
- Electrode importance based on SA-GSA z-scores in 20-50 Hz band
- Results ranked by mean-squared z-score contribution

### Visualization Pipeline
- Edit `visualization_pipeline/config.py` for paths and options
- Default: Top-5 electrodes highlighted based on clinical context
- Clinical interpretations in `clinical_interpretations.py`

## Key Features

### Scientific Rigor
- Leave-one-patient-out cross-validation
- Permutation testing for significance
- McNemar's test for paired comparisons
- Wilson confidence intervals

### Clinical Integration
- 19 patients with manual radiology annotations
- Electrode positioning via standard 10-10 system
- 3D anatomical visualization
- HTML reports for clinical review

### Methodological Transparency
- Clear separation of feature types (HMD, GSA, SA-GSA)
- Detailed electrode contribution analysis
- Reproducible experimental pipeline

## Output Files

### Classification Results
- Feature distribution plots
- Performance comparison charts
- Per-subject prediction tables
- Statistical test results

### Electrode Analysis
- `detailed_electrode_contributions_*.csv` - Complete electrode data
- `patient_summary_*.csv` - Per-patient summaries
- Comprehensive visualization plots

### Clinical Visualization
- `output/report.html` - Combined clinical report
- `output/figures/electrode_maps/` - Per-patient electrode maps
- `output/figures/lesion_atlas/` - Anatomical lesion locations

## Notes

- The pipeline uses a simplified ellipsoid head model suitable for lobar-level analysis
- Electrode importance reflects graph-domain contributions, not direct tissue correspondence
- All statistical tests account for small sample size (n=27)
- **Clinical focus minimized in visualization for general applicability**

## Citation

If you use this pipeline, please cite the original UCL stroke EIT dataset and SA-GSA methodology.