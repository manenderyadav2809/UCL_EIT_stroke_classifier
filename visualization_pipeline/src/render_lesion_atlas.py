"""
render_lesion_atlas.py
----------------------
Generate per-scan 4-view PNG figures showing the lesion's approximate 3D
location on a simplified head model.

Each PNG has four panels: axial / sagittal / coronal / 3D oblique.
The schematic view shows the head outline plus the lesion regions.
The anatomical view additionally shows all cortical lobes as faint
reference colors.
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse
import numpy as np

from .head_anatomy import (
    HEAD_SHELL, BRAIN_SURFACE, LOBES, all_regions, ellipsoid_mesh,
)
from .clinical_interpretations import PATIENT_SCANS


LESION_COLOR = "#d62728"
LESION_EDGE  = "#7a0000"

LOBE_REF_COLOR = {
    "frontal":   "#e8c4a8",
    "central":   "#c4d8e8",
    "temporal":  "#e8d4c4",
    "parietal":  "#d4e8c4",
    "occipital": "#d8c4e8",
}


def _project_ellipse(center, semi_axes, view: str):
    cx, cy, cz = center
    ax, ay, az = semi_axes
    if view == "axial":     return (cx, cy, 2 * ax, 2 * ay)
    if view == "sagittal":  return (cy, cz, 2 * ay, 2 * az)
    if view == "coronal":   return (cx, cz, 2 * ax, 2 * az)
    raise ValueError(view)


def _draw_2d_view(ax, view: str, lesion_region_keys: list, anatomical: bool):
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

    cx, cy, w, h = _project_ellipse(HEAD_SHELL["center"], HEAD_SHELL["semi_axes"], view)
    ax.add_patch(Ellipse((cx, cy), w, h, fill=False, edgecolor="black",
                         linewidth=1.5, zorder=2))
    cx, cy, w, h = _project_ellipse(BRAIN_SURFACE["center"], BRAIN_SURFACE["semi_axes"], view)
    ax.add_patch(Ellipse((cx, cy), w, h, fill=True, facecolor="#f5f5f5",
                         edgecolor="#888", linewidth=0.5, alpha=0.7, zorder=1))

    if view == "axial":
        anterior_y = HEAD_SHELL["center"][1] + HEAD_SHELL["semi_axes"][1]
        ax.plot([-7, 0, 7], [anterior_y, anterior_y + 8, anterior_y],
                color="black", linewidth=1.5, zorder=3)

    if anatomical:
        for region_key in LOBES:
            lobe_type = region_key.split("_")[0]
            color = LOBE_REF_COLOR.get(lobe_type, "#dddddd")
            cx, cy, w, h = _project_ellipse(
                LOBES[region_key]["center"], LOBES[region_key]["semi_axes"], view)
            ax.add_patch(Ellipse((cx, cy), w, h, fill=True,
                                 facecolor=color, edgecolor="none",
                                 alpha=0.35, zorder=3))

    regions_lookup = all_regions()
    for region_key in lesion_region_keys:
        if region_key not in regions_lookup:
            continue
        r = regions_lookup[region_key]
        cx, cy, w, h = _project_ellipse(r["center"], r["semi_axes"], view)
        ax.add_patch(Ellipse((cx, cy), w, h, fill=True,
                             facecolor=LESION_COLOR, edgecolor=LESION_EDGE,
                             linewidth=1.5, alpha=0.55, zorder=5))

    if view in ("axial", "coronal"):
        ax.text(-92, ax.get_ylim()[1] * 0.85, "L",
                fontsize=11, fontweight="bold", color="#555")
        ax.text( 88, ax.get_ylim()[1] * 0.85, "R",
                fontsize=11, fontweight="bold", color="#555")

    ax.set_title(view.upper(), fontsize=10, fontweight="bold")


def _draw_3d_view(ax, lesion_region_keys: list, anatomical: bool,
                  azim: int = -50, elev: int = 20):
    bx, by, bz = ellipsoid_mesh(
        BRAIN_SURFACE["center"], BRAIN_SURFACE["semi_axes"], n=24)
    ax.plot_wireframe(bx, by, bz, color="#aaa", linewidth=0.3, alpha=0.4)

    hx, hy, hz = ellipsoid_mesh(
        HEAD_SHELL["center"], HEAD_SHELL["semi_axes"], n=20)
    ax.plot_wireframe(hx, hy, hz, color="#ccc", linewidth=0.2, alpha=0.2)

    if anatomical:
        for region_key in LOBES:
            lobe_type = region_key.split("_")[0]
            color = LOBE_REF_COLOR.get(lobe_type, "#dddddd")
            lx, ly, lz = ellipsoid_mesh(
                LOBES[region_key]["center"], LOBES[region_key]["semi_axes"], n=18)
            ax.plot_surface(lx, ly, lz, color=color, alpha=0.18,
                            edgecolor="none", antialiased=True)

    regions_lookup = all_regions()
    for region_key in lesion_region_keys:
        if region_key not in regions_lookup:
            continue
        r = regions_lookup[region_key]
        lx, ly, lz = ellipsoid_mesh(r["center"], r["semi_axes"], n=24)
        ax.plot_surface(lx, ly, lz, color=LESION_COLOR, alpha=0.7,
                        edgecolor=LESION_EDGE, linewidth=0.5,
                        antialiased=True)

    ax.set_xlim(-100, 100); ax.set_ylim(-120, 120); ax.set_zlim(-60, 100)
    ax.set_box_aspect((1.0, 1.2, 0.8))
    ax.view_init(elev=elev, azim=azim)
    ax.set_xlabel("L / R"); ax.set_ylabel("P / A"); ax.set_zlabel("I / S")
    ax.set_title("3D OBLIQUE", fontsize=10, fontweight="bold")


def render_scan(patient_id: str, scan_label: str, scan: dict,
                out_dir: Path, anatomical: bool, dpi: int = 110) -> Path:
    fig = plt.figure(figsize=(14, 4.5), dpi=dpi)
    ax_axial    = fig.add_subplot(1, 4, 1)
    ax_sagittal = fig.add_subplot(1, 4, 2)
    ax_coronal  = fig.add_subplot(1, 4, 3)
    ax_3d       = fig.add_subplot(1, 4, 4, projection="3d")

    regions = scan.get("regions", [])
    _draw_2d_view(ax_axial,    "axial",    regions, anatomical)
    _draw_2d_view(ax_sagittal, "sagittal", regions, anatomical)
    _draw_2d_view(ax_coronal,  "coronal",  regions, anatomical)
    _draw_3d_view(ax_3d, regions, anatomical)

    suffix = "anatomical" if anatomical else "schematic"
    side = scan.get("side", "?")
    region_str = ", ".join(regions) if regions else "no acute lesion"
    suptitle = (
        f"{patient_id} — {scan_label} ({scan.get('modality','?')}, "
        f"{scan.get('timing','?')})  |  side: {side}  |  {region_str}"
    )
    fig.suptitle(suptitle, fontsize=11, fontweight="bold", y=1.02)
    fig.tight_layout()

    safe = scan_label.replace(" ", "")
    out_path = out_dir / f"{patient_id}_{safe}_{suffix}.png"
    fig.savefig(out_path, bbox_inches="tight", dpi=dpi)
    plt.close(fig)
    return out_path


def render_all(out_dir: Path, dpi: int = 110) -> list[Path]:
    """Render every scan in PATIENT_SCANS, both schematic and anatomical variants."""
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for patient_id, data in sorted(PATIENT_SCANS.items()):
        for scan_key in ("report_A", "report_B"):
            if scan_key not in data:
                continue
            scan = data[scan_key]
            for anatomical in (False, True):
                p = render_scan(patient_id, scan["scan_label"], scan,
                                out_dir, anatomical=anatomical, dpi=dpi)
                paths.append(p)
    return paths
