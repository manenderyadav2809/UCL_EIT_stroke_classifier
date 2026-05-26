"""
head_anatomy.py
---------------
Defines anatomical brain regions as 3D ellipsoids in head coordinates.

Coordinate system:
    origin = approximate brain center
    +x = right (in patient space; same as RAS+)
    -x = left
    +y = anterior
    -y = posterior
    +z = superior
    -z = inferior
    units = mm

Head outer shell: roughly 85mm half-width, 100mm half-AP, 80mm half-SI.

Each region is defined as an ellipsoid:
    center    = (x, y, z) in mm
    semi_axes = (a, b, c) for the ellipsoid radii in mm

These are approximations adequate for visual localization at lobar
resolution. They are NOT MNI atlas labels — they are simplified
anatomical placements that capture "where in the head" each region
sits. Reviewers should be told this in the caption.

For bilateral regions we define separate _left and _right entries
where appropriate. Midline structures share one entry.
"""

import numpy as np

# Head outer shell (a fairly realistic adult skull)
HEAD_SHELL = {
    "semi_axes": (85.0, 105.0, 82.0),   # LR, AP, SI
    "center":    (0.0, 5.0, 0.0),        # head extends slightly more anterior
}

# Brain surface (slightly inside the skull)
BRAIN_SURFACE = {
    "semi_axes": (72.0, 92.0, 65.0),
    "center":    (0.0, 5.0, -3.0),
}


# ---------------------------------------------------------------------------
# Cortical lobes (paired left/right)
# ---------------------------------------------------------------------------
# These are the regions a radiology report calls out by name:
#   "left frontal lobe", "right occipital", "left parietal", etc.
#
# Each lobe is placed at the canonical position of that lobe in the head,
# with semi-axes scaled to make them visually distinct without overlapping
# too aggressively in the rendering. They DO overlap somewhat at lobar
# boundaries — that's anatomically correct.

LOBES = {
    # FRONTAL: anterior, takes up roughly the front third of the brain
    "frontal_left":  {"center": (-35, 55, 15),  "semi_axes": (28, 32, 30)},
    "frontal_right": {"center": ( 35, 55, 15),  "semi_axes": (28, 32, 30)},

    # CENTRAL (peri-Rolandic strip): a band across the top middle
    # Narrow in AP, wide in LR, tall in SI. Sits at the central sulcus.
    "central_left":  {"center": (-35, 5, 35),   "semi_axes": (25, 18, 28)},
    "central_right": {"center": ( 35, 5, 35),   "semi_axes": (25, 18, 28)},

    # TEMPORAL: lateral, inferior. Tucked under the sylvian fissure.
    "temporal_left":  {"center": (-55, 0, -15), "semi_axes": (18, 35, 22)},
    "temporal_right": {"center": ( 55, 0, -15), "semi_axes": (18, 35, 22)},

    # PARIETAL: posterior to central, superior
    "parietal_left":  {"center": (-35, -35, 30), "semi_axes": (28, 30, 28)},
    "parietal_right": {"center": ( 35, -35, 30), "semi_axes": (28, 30, 28)},

    # OCCIPITAL: posterior pole
    "occipital_left":  {"center": (-25, -70, 5), "semi_axes": (22, 22, 25)},
    "occipital_right": {"center": ( 25, -70, 5), "semi_axes": (22, 22, 25)},
}


# ---------------------------------------------------------------------------
# Deep / subcortical structures
# ---------------------------------------------------------------------------
# Smaller, more central. These are what reports call out for:
#   "left thalamic haemorrhage"
#   "right striatocapsular bleed"
#   "lacunar infarct"
#   "internal capsule"
#   "brainstem"
#   "cerebellum"

DEEP_STRUCTURES = {
    # THALAMUS: paired, deep, central
    "thalamus_left":  {"center": (-12, -10, 5),  "semi_axes": (10, 13, 10)},
    "thalamus_right": {"center": ( 12, -10, 5),  "semi_axes": (10, 13, 10)},

    # BASAL GANGLIA / striatocapsular: anterior and lateral to thalamus
    "basal_ganglia_left":  {"center": (-18, 5, 5),  "semi_axes": (12, 18, 12)},
    "basal_ganglia_right": {"center": ( 18, 5, 5),  "semi_axes": (12, 18, 12)},

    # INTERNAL CAPSULE: between basal ganglia and thalamus, sort of a slab
    "internal_capsule_left":  {"center": (-22, -2, 5),  "semi_axes": (4, 18, 12)},
    "internal_capsule_right": {"center": ( 22, -2, 5),  "semi_axes": (4, 18, 12)},

    # BRAINSTEM: midline, inferior (pons + midbrain)
    "brainstem": {"center": (0, -18, -25), "semi_axes": (10, 15, 22)},

    # CEREBELLUM: posterior, inferior, paired
    "cerebellum_left":  {"center": (-25, -55, -30), "semi_axes": (22, 25, 18)},
    "cerebellum_right": {"center": ( 25, -55, -30), "semi_axes": (22, 25, 18)},
}


# ---------------------------------------------------------------------------
# Sub-cortical specifics (used when reports name a specific gyrus / area)
# ---------------------------------------------------------------------------
SPECIFIC_REGIONS = {
    # Insula sits at the lateral fronto-temporal border, deep to the operculum
    "insula_left":  {"center": (-45, 0, 5),   "semi_axes": (10, 18, 12)},
    "insula_right": {"center": ( 45, 0, 5),   "semi_axes": (10, 18, 12)},

    # Paracentral lobule: medial central, near midline
    "paracentral_left":  {"center": (-8, 0, 50),  "semi_axes": (10, 18, 15)},
    "paracentral_right": {"center": ( 8, 0, 50),  "semi_axes": (10, 18, 15)},

    # Premotor: anterior to precentral gyrus
    "premotor_left":  {"center": (-35, 20, 40),  "semi_axes": (18, 12, 18)},
    "premotor_right": {"center": ( 35, 20, 40),  "semi_axes": (18, 12, 18)},
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def all_regions() -> dict:
    """Merge all region dicts into one for lookup."""
    out = {}
    out.update(LOBES)
    out.update(DEEP_STRUCTURES)
    out.update(SPECIFIC_REGIONS)
    return out


def ellipsoid_mesh(center, semi_axes, n=30):
    """Return (X, Y, Z) meshgrid for an ellipsoid surface."""
    u = np.linspace(0, 2*np.pi, n)
    v = np.linspace(0, np.pi, n)
    x = center[0] + semi_axes[0] * np.outer(np.cos(u), np.sin(v))
    y = center[1] + semi_axes[1] * np.outer(np.sin(u), np.sin(v))
    z = center[2] + semi_axes[2] * np.outer(np.ones_like(u), np.cos(v))
    return x, y, z


def is_inside_ellipsoid(points, center, semi_axes):
    """Boolean mask: which points are inside an ellipsoid?"""
    cx, cy, cz = center
    a, b, c = semi_axes
    x, y, z = points[:, 0], points[:, 1], points[:, 2]
    return ((x - cx) / a) ** 2 + ((y - cy) / b) ** 2 + ((z - cz) / c) ** 2 <= 1.0
