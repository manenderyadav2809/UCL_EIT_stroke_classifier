"""
build_html_report.py
--------------------
Combine the lesion atlas and EIT figures into a single
self-contained HTML report. Images are embedded as base64 so the HTML
file is portable (one file = whole report).
"""

import base64
import re
from pathlib import Path

import pandas as pd

from .clinical_interpretations import PATIENT_SCANS


def _b64(path: Path) -> str:
    if not path.exists():
        return ""
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode()


def _patient_to_pdf_stem(p: str) -> str:
    return re.sub(r"[a-z]$", "", p)


def build_report(df: pd.DataFrame,
                 lesion_atlas_dir: Path,
                 eit_maps_dir: Path,
                 out_html: Path,
                 top_k: int = 5) -> Path:
    """
    Build the combined HTML report.

    Args:
        df:                 DataFrame from load_contributions()
        lesion_atlas_dir:   directory of per-scan lesion atlas PNGs
        eit_maps_dir:       directory of per-patient EIT PNGs
        out_html:           output HTML file path
        top_k:              top-K value used (just for display in methods)
    """
    csv_patients = sorted(df["Patient"].unique())

    html = ["""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>Stroke EIT Analysis — Lesion Atlas + EIT Contributions</title>
<style>
  body { font-family: -apple-system, system-ui, sans-serif; max-width: 1400px;
         margin: 20px auto; padding: 0 24px; color: #1a1a1a; line-height: 1.55; }
  h1 { border-bottom: 3px solid #222; padding-bottom: 8px; }
  h2 { margin-top: 28px; border-bottom: 1px solid #ccc; padding-bottom: 4px; }
  .nav { background: #f5f5f5; padding: 10px 16px; border-radius: 5px;
         margin: 12px 0; font-size: 13px; }
  .nav a { margin: 0 5px; color: #2c5aa0; text-decoration: none; }
  .nav a:hover { text-decoration: underline; }
  .methods { background: #f5f8fb; padding: 14px 22px;
             border-left: 4px solid #2c7fb8; margin: 14px 0; font-size: 13.5px; }
  .patient-block {
    margin-top: 32px; padding: 14px 20px;
    background: #fbfbfb; border: 1px solid #ddd; border-radius: 6px;
  }
  .patient-header { font-size: 17px; font-weight: 700; margin-bottom: 8px; }
  .summary { color: #555; font-size: 14px; font-style: italic; margin-bottom: 12px; }
  .section-label {
    font-size: 12px; font-weight: 700; color: #555;
    text-transform: uppercase; letter-spacing: 1px;
    margin: 14px 0 6px 0; padding-bottom: 3px;
    border-bottom: 1px dashed #ccc;
  }
  .figure-container {
    margin: 8px 0; padding: 10px;
    background: white; border: 1px solid #e0e0e0; border-radius: 4px;
  }
  .figure-container img { width: 100%; max-width: 1280px;
                           border: 1px solid #ddd; border-radius: 3px;
                           display: block; }
  .source-phrase {
    font-style: italic; color: #333;
    background: #fffaf0; padding: 6px 10px;
    border-left: 3px solid #d4a017; margin: 6px 0;
    border-radius: 0 3px 3px 0; font-size: 12.5px;
  }
  .scan-meta { font-size: 12px; color: #666; margin-bottom: 4px; }
  .no-pdf-note {
    padding: 8px 14px; background: #fff3cd;
    border-left: 3px solid #d4a017; border-radius: 0 4px 4px 0;
    font-size: 13px; color: #644;
  }
</style></head><body>
"""]

    html.append(f"""
<h1>Stroke EIT Analysis — Lesion Atlas + EIT Contributions</h1>
<p>For each patient: the radiologically-confirmed lesion location is shown
on a simplified head model (where a PDF report is available), and the
top-{top_k} EIT contribution electrodes guided by clinical imaging
are highlighted, with everything else shown as small grey reference dots.</p>
""")

    html.append(f"""
<h2>Methods</h2>
<div class="methods">
<p><b>Lesion annotation.</b> Each radiology report was read manually and the
lesion location recorded at the lobar / specific-structure level. Where
both an initial and follow-up scan exist, both are shown. The verbatim
phrase from the report supporting each annotation is reproduced below the
figure.</p>


<p><b>Normalization.</b> The top-{top_k} colored electrodes are min-max
normalized over themselves. All other electrodes are shown as small grey
reference dots regardless of their value.</p>

<p><b>Deep lesions.</b> For patients with purely deep lesions (e.g.
thalamic or striatocapsular bleeds), no cortical scalp projection
exists; the figure is shown for completeness but scalp EIT cannot
directly localize these lesions.</p>

<p><b>Anatomical model.</b> A simplified ellipsoidal head model with five
cortical lobes (frontal, central, temporal, parietal, occipital) and deep
structures (thalamus, basal ganglia, internal capsule, brainstem,
cerebellum). This is not a patient-specific atlas — it is a reference
geometry adequate for visualizing lesion location at lobar resolution.
Coordinate convention is RAS+ (right-anterior-superior), with patient's
left appearing on the viewer's left.</p>
</div>
""")

    # Navigation
    html.append('<div class="nav"><b>Jump to patient:</b>')
    for pid in csv_patients:
        anchor = pid.replace("_", "")
        html.append(f'<a href="#{anchor}">{pid}</a>')
    html.append('</div>')

    # Per-patient blocks
    for pid in csv_patients:
        anchor = pid.replace("_", "")
        condition = df[df["Patient"] == pid]["Condition"].iloc[0]

        html.append(f'<div class="patient-block" id="{anchor}">')
        html.append(f'<div class="patient-header">{pid} '
                    f'<span style="color: #888; font-weight: 400;">'
                    f'({condition})</span></div>')

        pdf_pid = _patient_to_pdf_stem(pid)
        scan_data = PATIENT_SCANS.get(pdf_pid)

        if scan_data:
            html.append(f'<div class="summary">{scan_data["summary"]}</div>')
            html.append('<div class="section-label">Lesion atlas (from radiology report)</div>')
            for scan_key in ("report_A", "report_B"):
                if scan_key not in scan_data:
                    continue
                scan = scan_data[scan_key]
                safe = scan["scan_label"].replace(" ", "")
                anat_path = lesion_atlas_dir / f"{pdf_pid}_{safe}_anatomical.png"

                html.append('<div class="figure-container">')
                html.append(
                    f'<div class="scan-meta">'
                    f'<b>{scan["scan_label"]}</b> — {scan["modality"]}, '
                    f'{scan["timing"]} ({scan["date"]})  •  '
                    f'side: <b>{scan["side"]}</b>  •  '
                    f'regions: {", ".join(scan["regions"]) or "—"}'
                    f'</div>')
                html.append(f'<div class="source-phrase">"{scan["source_phrase"]}"</div>')
                if anat_path.exists():
                    html.append(f'<img src="{_b64(anat_path)}" alt="lesion atlas"/>')
                html.append('</div>')
        else:
            html.append('<div class="no-pdf-note">'
                        'No radiology report available for this patient. '
                        'EIT contributions are shown below with no hemispheric filter.'
                        '</div>')

        # EIT
        html.append(f'<div class="section-label">EIT contributions — top-{top_k} electrodes</div>')
        eit_path = eit_maps_dir / f"{pid}_electrode_map.png"
        if eit_path.exists():
            html.append('<div class="figure-container">')
            html.append('<span class="scan-meta">'
                        f'Top-{top_k} electrodes guided by clinical context colored by '
                        f'min-max normalized contribution. All other electrodes shown as '
                        f'small grey reference dots.'
                        '</span>')
            html.append(f'<img src="{_b64(eit_path)}" alt="EIT top-K electrode contribution"/>')
            html.append('</div>')

        html.append('</div>')

    html.append("</body></html>")

    out_html.parent.mkdir(parents=True, exist_ok=True)
    out_html.write_text("".join(html))
    return out_html
