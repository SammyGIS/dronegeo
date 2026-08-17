"""
Script to generate Figure 1 for the JOSS manuscript.
Visualizes DroneGeo's end-to-end scientific pipeline:
Raw UAV Sensors -> AutoQC Diagnostics & Healing -> Terrain Morphology -> Hydrology & Risk Analytics.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pathlib import Path

fig, ax = plt.subplots(figsize=(12, 6.5), dpi=300)
ax.set_facecolor("#f8fafc")
fig.patch.set_facecolor("#ffffff")

# Box styling helper
def draw_stage(x, y, w, h, title, items, color, border_color):
    box = patches.FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.03,rounding_size=0.04",
        edgecolor=border_color,
        facecolor=color,
        linewidth=1.8,
        zorder=2
    )
    ax.add_patch(box)
    
    # Title
    ax.text(x + w / 2, y + h - 0.05, title, ha="center", va="top",
            fontsize=11.5, fontweight="bold", color="#0f172a")
    
    # Divider line
    ax.plot([x + 0.02, x + w - 0.02], [y + h - 0.08, y + h - 0.08],
            color=border_color, lw=1.0, alpha=0.5)
    
    # Content items
    for i, item in enumerate(items):
        ax.text(x + 0.025, y + h - 0.12 - i * 0.052, f"• {item}",
                ha="left", va="top", fontsize=9.5, color="#334155")

# Draw 4 Stages
stages = [
    (
        0.03, 0.15, 0.21, 0.72,
        "1. Raw Ingestion",
        [
            "LiDAR Point Clouds (.las/.laz)",
            "RGB Sensor Imagery",
            "Survey GCP Benchmarks",
            "Flight Navigation Trajectories",
            "Coordinate Reference (UTM/EPSG)"
        ],
        "#e0f2fe", "#0284c7"
    ),
    (
        0.27, 0.15, 0.21, 0.72,
        "2. AutoQC Diagnostics",
        [
            "Strip Offset Audit (ΔZ)",
            "GCP 3D RMSE Validation",
            "Point Cloud Noise Trimming",
            "Missing CRS Header Embed",
            "DEM Hole & Spike Healing"
        ],
        "#fef3c7", "#d97706"
    ),
    (
        0.51, 0.15, 0.21, 0.72,
        "3. Surface Morphology",
        [
            "Continuous DTM / DSM / CHM",
            "Multithreaded IDW / TIN",
            "True-Color Orthomosaics",
            "Vegetation Indices (VARI, GLI)",
            "Vector Contour Generation"
        ],
        "#dcfce7", "#16a34a"
    ),
    (
        0.75, 0.15, 0.22, 0.72,
        "4. Risk & Hydrology",
        [
            "D8 & D-inf Flow Accumulation",
            "Topographic Wetness (TWI)",
            "Stream Power Index (SPI)",
            "Sediment Transport (STI)",
            "3D Cut / Fill Volumetrics"
        ],
        "#ede9fe", "#7c3aed"
    )
]

for x, y, w, h, title, items, col, border in stages:
    draw_stage(x, y, w, h, title, items, col, border)

# Draw connecting arrows between stages
arrow_props = dict(facecolor="#475569", edgecolor="#334155", width=2.5, headwidth=8, headlength=8)
for i in range(3):
    x_start = stages[i][0] + stages[i][2] + 0.005
    x_end = stages[i+1][0] - 0.005
    y_mid = 0.51
    ax.annotate(
        "", xy=(x_end, y_mid), xytext=(x_start, y_mid),
        arrowprops=dict(arrowstyle="-|>", lw=2.2, color="#475569", mutation_scale=16)
    )

# Header Title and Subtitle
ax.text(0.5, 0.96, "DroneGeo Modular Processing Architecture", ha="center", va="top",
        fontsize=14, fontweight="bold", color="#0f172a")
ax.text(0.5, 0.91, "End-to-End UAV Remote Sensing, LiDAR AutoQC Healing, Morphological Surface Generation & Hydrological Modeling",
        ha="center", va="top", fontsize=9.5, color="#64748b", style="italic")

ax.set_xlim(0, 1.0)
ax.set_ylim(0, 1.0)
ax.axis("off")
plt.tight_layout()

out_path = Path(__file__).parent / "figure1_pipeline.png"
plt.savefig(out_path, dpi=300, bbox_inches="tight")
print(f"Generated: {out_path}")
