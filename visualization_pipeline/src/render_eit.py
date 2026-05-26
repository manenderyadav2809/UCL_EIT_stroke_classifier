"""
render_eit.py
-------------------------
Per-patient 3D EIT views showing the top-K electrodes of the head as colored spheres.

For patients without specific clinical guidance, electrode selection considers 
all available data.
"""

from __future__ import annotations

import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
from matplotlib.patches import Ellipse
import mne
import numpy as np
import pandas as pd

from .head_anatomy import HEAD_SHELL, BRAIN_SURFACE, ellipsoid_mesh
from .clinical_interpretations import PATIENT_SCANS


HEAD_CENTER = np.array(HEAD_SHELL["center"], dtype=float)
HEAD_SEMI   = np.array(HEAD_SHELL["semi_axes"], dtype=float)

GREY_DOT_COLOR = "#a0a0a0"
GREY_DOT_SIZE  = 18
GREY_DOT_ALPHA = 0.55


# ---------------------------------------------------------------------------
# Electrode positioning
# ---------------------------------------------------------------------------

def _csv_to_mne_name(name: str) -> str:
    fix = {"FP1": "Fp1", "FP2": "Fp2",
           "CZ": "Cz", "FZ": "Fz", "PZ": "Pz", "OZ": "Oz",
           "I1/O9": "I1", "I2/O10": "I2"}
    return fix.get(name.strip(), name.strip())


def get_electrode_positions(csv_names: list[str]) -> tuple[np.ndarray, list[str]]:
    """
    Map CSV electrode names to 3D positions on the head shell of our
    anatomical model.

    Returns:
        (N, 3) positions in mm, and the list of CSV names successfully mapped.
    """
    montage = mne.channels.make_standard_montage("standard_1005")
    ch_pos = montage.get_positions()["ch_pos"]
    lookup = {n.lower(): n for n in ch_pos}

    positions, kept = [], []
    for csv_name in csv_names:
        mne_name = _csv_to_mne_name(csv_name)
        actual = lookup.get(mne_name.lower())
        if actual is None:
            continue
        p = np.array(ch_pos[actual]) * 1000.0
        offset = p - HEAD_CENTER
        norm = np.sqrt(np.sum((offset / HEAD_SEMI) ** 2))
        p_proj = HEAD_CENTER + offset / norm if norm > 1e-9 else p
        positions.append(p_proj)
        kept.append(csv_name)
    return np.array(positions), kept


def _electrode_side(name: str) -> str:
    digits = re.findall(r"\d+", name.strip())
    if not digits:
        return "mid"
    return "left" if int(digits[-1]) % 2 == 1 else "right"


# ---------------------------------------------------------------------------
# Clinical context from medical reports
# ---------------------------------------------------------------------------

def get_clinical_context(patient_id: str) -> tuple[str, str]:
    pdf_pid = re.sub(r"[a-z]$", "", patient_id)
    if pdf_pid not in PATIENT_SCANS:
        return "unknown", f"No radiology report for {patient_id} — all electrodes considered."
    data = PATIENT_SCANS[pdf_pid]

    sides = []
    deep_flags = []
    for key in ("report_B", "report_A"):
        if key in data:
            scan = data[key]
            if scan["side"] not in ("none", None):
                sides.append(scan["side"])
            has_cortical = any(
                not r.startswith(("thalamus", "basal_ganglia", "internal_capsule",
                                  "brainstem", "cerebellum"))
                for r in scan.get("regions", [])
            )
            deep_flags.append(bool(scan.get("regions")) and not has_cortical)

    if not sides:
        return "unknown", " "
    if "bilateral" in sides:
        return "bilateral", " "

    side = max(set(sides), key=sides.count)
    if any(deep_flags):
        summary = data.get("summary", "").split(".")[0].lower()
        note = (f"DEEP LESION ({side} {summary}). Scalp EIT cannot directly "
                f"localize this; corresponding electrodes shown for completeness.")
    else:
        note = f"Cortical/mixed lesion on the {side}."
    return side, note


# ---------------------------------------------------------------------------
# View helpers
# ---------------------------------------------------------------------------

def _proj_ellipse(center, semi_axes, view: str):
    cx, cy, cz = center
    a, b, c = semi_axes
    if view == "axial":     return cx, cy, a, b
    if view == "sagittal":  return cy, cz, b, c
    if view == "coronal":   return cx, cz, a, c
    raise ValueError(view)


def _project_2d(pts, view: str):
    if view == "axial":     return pts[:, 0], pts[:, 1]
    if view == "sagittal":  return pts[:, 1], pts[:, 2]
    if view == "coronal":   return pts[:, 0], pts[:, 2]


def _normalize_minmax(values: np.ndarray) -> np.ndarray:
    vmin, vmax = values.min(), values.max()
    if vmax - vmin < 1e-12:
        return np.zeros_like(values)
    return (values - vmin) / (vmax - vmin)


# ---------------------------------------------------------------------------
# Drawing
# ---------------------------------------------------------------------------

def _draw_2d(ax, view, positions_all, side_mask, values_for_top,
             vmin, vmax, cmap, clinical_context):
    if view == "axial":
        ax.set_xlabel("Left ← X (mm) → Right")
        ax.set_ylabel("Posterior ← Y (mm) → Anterior")
        ax.set_xlim(-100, 100); ax.set_ylim(-120, 120)
    elif view == "sagittal":
        ax.set_xlabel("Posterior ← Y (mm) → Anterior")
        ax.set_ylabel("Inferior ← Z (mm) → Superior")
        ax.set_xlim(-120, 120); ax.set_ylim(-60, 100)
    elif view == "coronal":
        ax.set_xlabel("Left ← X (mm) → Right")
        ax.set_ylabel("Inferior ← Z (mm) → Superior")
        ax.set_xlim(-100, 100); ax.set_ylim(-60, 100)
    ax.set_aspect("equal")
    ax.grid(alpha=0.2)

    ex_all, ey_all = _project_2d(positions_all, view)
    hcx, hcy, ha, hb = _proj_ellipse(HEAD_SHELL["center"], HEAD_SHELL["semi_axes"], view)

    ax.add_patch(Ellipse((hcx, hcy), 2 * ha, 2 * hb, fill=False,
                         edgecolor="black", linewidth=1.5, zorder=10))

    if clinical_context in ("left", "right") and view in ("axial", "coronal"):
        ax.axvline(0, color="#666", linestyle="--", linewidth=0.8,
                   alpha=0.5, zorder=11)

    # Non-top electrodes as grey dots
    ax.scatter(ex_all[~side_mask], ey_all[~side_mask],
               color=GREY_DOT_COLOR, s=GREY_DOT_SIZE, alpha=GREY_DOT_ALPHA,
               edgecolors="none", zorder=7)

    # Top-K colored
    sizes = 30 + 200 * _normalize_minmax(np.abs(values_for_top[side_mask]))
    ax.scatter(ex_all[side_mask], ey_all[side_mask],
               c=values_for_top[side_mask], cmap=cmap, vmin=vmin, vmax=vmax,
               s=sizes, alpha=0.95, zorder=8,
               edgecolors="black", linewidths=0.5)

    if view == "axial":
        anterior_y = HEAD_SHELL["center"][1] + HEAD_SHELL["semi_axes"][1]
        ax.plot([-7, 0, 7], [anterior_y, anterior_y + 8, anterior_y],
                color="black", linewidth=1.5, zorder=11)

    if view in ("axial", "coronal"):
        ax.text(-92, ax.get_ylim()[1] * 0.85, "L",
                fontsize=11, fontweight="bold", color="#555")
        ax.text( 88, ax.get_ylim()[1] * 0.85, "R",
                fontsize=11, fontweight="bold", color="#555")

    ax.set_title(view.upper(), fontsize=10, fontweight="bold")


def _draw_3d(ax, positions_all, side_mask, values_for_top,
             vmin, vmax, cmap, clinical_context):
    hx, hy, hz = ellipsoid_mesh(HEAD_SHELL["center"], HEAD_SHELL["semi_axes"], n=20)
    ax.plot_wireframe(hx, hy, hz, color="#ccc", linewidth=0.25, alpha=0.35)

    bx, by, bz = ellipsoid_mesh(BRAIN_SURFACE["center"], BRAIN_SURFACE["semi_axes"], n=20)
    ax.plot_wireframe(bx, by, bz, color="#aaa", linewidth=0.3, alpha=0.4)

    ax.scatter(positions_all[~side_mask, 0],
               positions_all[~side_mask, 1],
               positions_all[~side_mask, 2],
               color=GREY_DOT_COLOR, s=30, alpha=GREY_DOT_ALPHA,
               edgecolors="none", depthshade=False, zorder=9)

    sizes = 40 + 200 * _normalize_minmax(np.abs(values_for_top[side_mask]))
    ax.scatter(positions_all[side_mask, 0],
               positions_all[side_mask, 1],
               positions_all[side_mask, 2],
               c=values_for_top[side_mask], cmap=cmap, vmin=vmin, vmax=vmax,
               s=sizes, edgecolors="black", linewidths=0.5,
               depthshade=False, zorder=10)

    ax.set_xlim(-100, 100); ax.set_ylim(-120, 120); ax.set_zlim(-60, 100)
    ax.set_box_aspect((1.0, 1.2, 0.8))
    if clinical_context == "right":
        ax.view_init(elev=20, azim=50)
    else:
        ax.view_init(elev=20, azim=-50)
    ax.set_xlabel("L / R"); ax.set_ylabel("P / A"); ax.set_zlabel("I / S")
    ax.set_title("3D OBLIQUE", fontsize=10, fontweight="bold")


# ---------------------------------------------------------------------------
# Per-patient render
# ---------------------------------------------------------------------------

def render_patient(patient_id: str, csv_names: list[str],
                   raw_values: np.ndarray, out_dir: Path,
                   top_k: int = 5, cmap: str = "RdYlBu_r",
                   dpi: int = 110) -> Path:
    """
    Render the top-K EIT electrode figure for one patient.

    The K colored electrodes use min-max normalization over themselves; everything else
    is shown as a small grey dot.
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    clinical_context, note = get_clinical_context(patient_id)

    positions, kept_names = get_electrode_positions(csv_names)
    name_to_val = dict(zip(csv_names, raw_values))
    raw_aligned = np.array([name_to_val[n] for n in kept_names])

    # Candidate side mask
    if clinical_context in ("bilateral", "unknown"):
        candidate_mask = np.ones(len(kept_names), dtype=bool)
    elif clinical_context == "left":
        candidate_mask = np.array([
            _electrode_side(n) in ("left", "mid") for n in kept_names
        ])
    elif clinical_context == "right":
        candidate_mask = np.array([
            _electrode_side(n) in ("right", "mid") for n in kept_names
        ])

    candidate_indices = np.where(candidate_mask)[0]
    candidate_raws = raw_aligned[candidate_mask]
    K = min(top_k, len(candidate_indices))
    top_local = np.argsort(-candidate_raws)[:K]
    top_global = candidate_indices[top_local]

    side_mask = np.zeros(len(kept_names), dtype=bool)
    side_mask[top_global] = True

    # Normalize among the top-K
    subset_vals = raw_aligned[side_mask]
    if len(subset_vals) > 0 and subset_vals.max() - subset_vals.min() > 1e-12:
        vmin_raw = subset_vals.min(); vmax_raw = subset_vals.max()
        values = (raw_aligned - vmin_raw) / (vmax_raw - vmin_raw)
        values = np.clip(values, 0.0, 1.0)
    else:
        values = np.zeros_like(raw_aligned)

    vmin, vmax = 0.0, 1.0

    # Figure
    fig = plt.figure(figsize=(17, 4.8), dpi=dpi)
    gs = fig.add_gridspec(1, 4, width_ratios=[1, 1, 1, 1.2], wspace=0.25)
    ax_axial    = fig.add_subplot(gs[0, 0])
    ax_sagittal = fig.add_subplot(gs[0, 1])
    ax_coronal  = fig.add_subplot(gs[0, 2])
    ax_3d       = fig.add_subplot(gs[0, 3], projection="3d")

    _draw_2d(ax_axial,    "axial",    positions, side_mask, values,
             vmin, vmax, cmap, clinical_context)
    _draw_2d(ax_sagittal, "sagittal", positions, side_mask, values,
             vmin, vmax, cmap, clinical_context)
    _draw_2d(ax_coronal,  "coronal",  positions, side_mask, values,
             vmin, vmax, cmap, clinical_context)
    _draw_3d(ax_3d, positions, side_mask, values, vmin, vmax, cmap, clinical_context)

    sm = ScalarMappable(norm=Normalize(vmin=vmin, vmax=vmax), cmap=cmap)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=[ax_axial, ax_sagittal, ax_coronal],
                        orientation="horizontal",
                        fraction=0.04, pad=0.15, shrink=0.8)
    cbar.set_label(f"Contribution (min-max over top {K} electrodes)", fontsize=9)

    colored_indices = np.where(side_mask)[0]
    colored_names = [kept_names[i] for i in colored_indices]
    colored_raws = raw_aligned[colored_indices]
    order = np.argsort(-colored_raws)
    top_str = ", ".join([colored_names[i] for i in order])

    suptitle = (f"{patient_id}  |  Clinical context: {clinical_context.upper()}  "
                f"|  Top-{K}: {top_str}")
    fig.suptitle(suptitle, fontsize=12, fontweight="bold", y=1.10)
    fig.text(0.5, 1.03, note, ha="center", fontsize=9.5,
             color="#555", style="italic", wrap=True)

    out_path = out_dir / f"{patient_id}_electrode_map.png"
    fig.savefig(out_path, bbox_inches="tight", dpi=dpi)
    plt.close(fig)
    return out_path


def render_all(df: pd.DataFrame, out_dir: Path, top_k: int = 5,
               cmap: str = "RdYlBu_r", dpi: int = 110) -> list[Path]:
    """Render the EIT figure for every patient in the CSV."""
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for pid in sorted(df["Patient"].unique()):
        sub = df[df["Patient"] == pid].sort_values("Electrode_Index")
        names = sub["Electrode_Name"].tolist()
        raw = sub["Contribution"].to_numpy(dtype=float)
        p = render_patient(pid, names, raw, out_dir,
                           top_k=top_k, cmap=cmap, dpi=dpi)
        paths.append(p)
    return paths
