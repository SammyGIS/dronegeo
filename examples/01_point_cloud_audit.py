#!/usr/bin/env python3
"""
Example 01: Pre-Processing Point Cloud Audit & Quality Dashboard
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Demonstrates how to audit raw UAV LiDAR point clouds:
- Calculates point density (pts/m2)
- Returns breakdown (single vs multiple pulse returns)
- Classification percentages (Ground vs Vegetation vs Unclassified)
- Elevation distribution (min, max, percentiles)
- Generates a multi-panel pre-flight QC dashboard PNG
"""

import sys
import os

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from pathlib import Path
import subprocess
import dronegeo as dg

OUTPUT_DIR = Path(__file__).parent / "outputs" / "01_audit"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
SAMPLE_LAS = Path(__file__).parent / "data" / "flight_survey_master.las"


def ensure_sample_data():
    """Generates canonical sample datasets if not already present."""
    if not SAMPLE_LAS.exists():
        print("Canonical sample data not found. Running 00_generate_sample_datasets.py...")
        gen_script = Path(__file__).parent / "00_generate_sample_datasets.py"
        subprocess.run([sys.executable, str(gen_script)], check=True)


def main():
    print("=" * 70)
    print("DroneGeo Example 01: Pre-Processing Point Cloud Audit")
    print("=" * 70)

    ensure_sample_data()

    # 1. Profile point cloud
    print(f"\n[1/2] Auditing point cloud: {SAMPLE_LAS.name}...")
    report = dg.lidar.profile_point_cloud(str(SAMPLE_LAS))

    print("\n--- Summary Audit Report ---")
    print(f"Total Points        : {report.total_points:,}")
    print(f"Mean Density        : {report.mean_point_density:.2f} pts/m2")
    z_min, z_max = report.spatial_bounds_xyz["Z"]
    print(f"Elevation Range (Z) : [{z_min:.2f} m, {z_max:.2f} m]")
    print(f"Has RGB Channels    : {report.has_rgb}")
    print(f"Has Intensity       : {report.has_intensity}")
    print("Classifications     :")
    for cls_name, pct in report.classification_percentages.items():
        print(f"  * {cls_name:22s}: {pct:5.2f}%")

    # 2. Generate visual QC dashboard
    qc_png = OUTPUT_DIR / "point_cloud_qc_dashboard.png"
    print(f"\n[2/2] Generating pre-flight QC dashboard: {qc_png.name}...")
    dg.lidar.plot_point_cloud_profile(report, output_png=str(qc_png))

    print(f"\n[OK] Audit complete! Dashboard saved to: {qc_png.resolve()}")


if __name__ == "__main__":
    main()
