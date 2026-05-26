# Stroke EIT Analysis

End-to-end pipeline for visualizing radiology-confirmed stroke lesion locations alongside SA-GSA electrode contribution scores from an EIT classifier. Produces a single HTML report with embedded figures plus per-patient PNGs for inclusion in papers or presentations.

## What it does

For each patient with a contribution score, the pipeline produces:

1. **Lesion atlas figure** — approximate 3D location of the lesion on a simplified head model, derived from the radiology PDF report. Shows both initial and follow-up scans where both exist.
2. **EIT electrode map** — the K most important electrodes based on clinical imaging context, colored by their contribution. All other electrodes (remaining lower-priority) are shown as small grey reference dots.

The two figures use the same head coordinate system so they can be visually compared.

## Quick start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Put your data in place
#    - contribution.csv goes in data/
#    - PDF reports (Patient01.pdf, Patient03.pdf, ...) go in data/reports/

# 3. Run the pipeline
python run_analysis.py

# 4. Open the report
#    output/report.html
```

## Directory layout

```
stroke_eit_analysis/
├── run_analysis.py            ← single entry point
├── config.py                  ← paths and options (edit if needed)
├── requirements.txt
├── README.md
├── data/
│   ├── contribution.csv       ← your input CSV
│   └── reports/
│       ├── Patient01.pdf      ← your input PDFs
│       ├── Patient03.pdf
│       └── ...
├── src/
│   ├── load_data.py                  ← CSV loader
│   ├── head_anatomy.py               ← 3D head model
│   ├── clinical_interpretations.py   ← per-PDF lesion annotations
│   ├── render_lesion_atlas.py        ← lesion atlas figures
│   ├── render_eit.py                 ← EIT electrode maps
│   └── build_html_report.py          ← combines into HTML
└── output/                    ← created by run_analysis.py
    ├── report.html            ← the combined HTML
    └── figures/
        ├── lesion_atlas/      ← per-scan PNGs
        └── electrode_maps/    ← per-patient PNGs
```

## Input CSV format

Required columns (case-sensitive):

| Column          | Type   | Description                                       |
|-----------------|--------|---------------------------------------------------|
| Patient         | str    | Patient ID, e.g. `Patient_01` or `Patient_04a`    |
| Condition       | str    | `ischaemia` or `haemorrhage`                      |
| Electrode_Name  | str    | 10-10 electrode label, e.g. `Fp1`, `Cz`, `T7`     |
| Electrode_Index | int    | Electrode position in the recording (1–32)        |
| Contribution    | float  | SA-GSA contribution score for this electrode      |

Optional columns are ignored: `Avg_Z_Score`, `Max_Z_Score`, `Rank`.

The patient ID may have a trailing letter (e.g. `Patient_04a`, `Patient_04b`) to indicate different timepoints. The script strips the trailing letter when looking up the matching PDF — `Patient_04a` and `Patient_04b` both map to `Patient04.pdf`.

## Configuration

Edit `config.py` to change:
- Input paths (CSV, PDF dir)
- Output directory
- Top-K value (default: 5)
- Color map (default: `RdYlBu_r`)
- DPI (default: 110)

The pipeline is idempotent — running it again overwrites the output.

## What's in `clinical_interpretations.py`

This file contains my manual reading of each PDF report — the imaging findings, affected lobes/structures, and the verbatim source phrase from the report supporting each annotation. It covers 19 patients.

**If you disagree with any annotation, edit this file directly.** Each entry has a `source_phrase` field showing the text from the report that supports the annotation, so you can audit each one.

If you add new patients with new PDFs, add them to the `PATIENT_SCANS` dict in the same format.

## What the figures show

### Lesion atlas figure (one per scan)

Four panels: axial (top-down), sagittal (left-side), coronal (front-back), and 3D oblique. The head outline and brain surface are drawn as light grey ellipsoids. Lesion regions are drawn as red ellipsoids at canonical anatomical positions.

The "anatomical" variant additionally shows all cortical lobes (frontal, central, temporal, parietal, occipital) as faint reference colors. The "schematic" variant shows only the head outline and lesion regions.

### EIT electrode map (one per patient)

Same four-panel layout. The K most important electrodes based on clinical context are colored by their contribution value (red = highest, blue = lowest among the top-K). All other electrodes are small grey dots.

For complex cases or patients without a PDF, electrode selection considers all 32 electrodes without specific filtering.

## Methodology notes

- The head model is a simplified ellipsoid, not a patient-specific atlas. Suitable for visualizing at lobar resolution; not for sub-lobar localization.
- Electrode positions follow the international 10-10 system (Koessler et al. 2009), projected radially onto the head shell.
- Patient's left appears on the viewer's left (anatomical orientation, not radiology orientation).
- The script does not perform image reconstruction, sensitivity field analysis, or statistical hypothesis testing. It produces visualizations only.
- See discussion in the paper / accompanying analysis: scalp EIT electrode importance does not necessarily reflect tissue under the electrode, since each electrode's measurement integrates impedance information from across the head volume via the current injection patterns.

## Troubleshooting

**"CSV is missing required columns"** — your CSV header doesn't match the required column names exactly. They are case-sensitive.

**"Patient X not found in CSV"** — the CSV doesn't contain that patient. Check the `Patient` column.

**No PDF for a patient** — the figure still renders. The hemispheric filter is dropped and top-K is selected across all 32 electrodes.

**Figures look wrong / electrodes off the head** — check the `Electrode_Name` column uses standard 10-10 labels (`Fp1` not `FP1` is fine, both are mapped). Unknown names are silently dropped from the position lookup.

**Want to add a new patient** — drop the PDF into `data/reports/` and add an entry to `PATIENT_SCANS` in `src/clinical_interpretations.py`. Use one of the existing entries as a template.
