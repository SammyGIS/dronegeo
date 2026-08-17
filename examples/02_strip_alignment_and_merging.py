#!/usr/bin/env python3
"""
Example 02: Multi-Strip Flightline Co-Registration & Alignment (dZ)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Demonstrates:
- Detecting vertical datum offsets (dZ) across overlapping flight strips.
- Statistical residual inspection (median shift, standard deviation).
- Plotting the error distribution histogram.
- Applying vertical correction and merging strips into a unified master cloud.
"""

import sys
import os

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from pathlib import Path
import subprocess
import dronegeo as dg

OUTPUT_DIR = Path(__file__).parent / "outputs" / "02_alignment"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
STRIP1 = Path(__file__).parent / "data" / "flight_strip_01.las"
STRIP2 = Path(__file__).parent / "data" / "flight_strip_02.las"


def ensure_sample_data():
    """Generates canonical sample datasets if not already present."""
    if not STRIP1.exists() or not STRIP2.exists():
        print("Canonical sample data not found. Running 00_generate_sample_datasets.py...")
        gen_script = Path(__file__).parent / "00_generate_sample_datasets.py"
        subprocess.run([sys.executable, str(gen_script)], check=True)


def main():
    print("=" * 70)
    print("DroneGeo Example 02: Multi-Strip Flightline Alignment (dZ)")
    print("=" * 70)

    ensure_sample_data()

    # 1. Detect vertical discrepancy in overlap zone
    print("\n[1/3] Measuring vertical datum offset in strip overlap zone...")
    report = dg.diagnostics.check_strip_alignment(
        las_path1=str(STRIP1),
        las_path2=str(STRIP2),
        sample_resolution=0.5,
    )

    print("\n--- Overlap Alignment Analysis ---")
    print(f"Overlap Detected       : {report.has_overlap}")
    print(f"Comparison Grid Cells  : {report.sampled_cells_count:,}")
    print(f"Median Vertical Offset : {report.median_offset:+.4f} m (Shift to align Strip 2)")
    print(f"Standard Deviation     : {report.std_dev:.4f} m")
    print(f"90% CI Range (p5 - p95): [{report.p5:+.4f} m, {report.p95:+.4f} m]")

    # 2. Plot residual distribution
    hist_png = OUTPUT_DIR / "overlap_residuals_histogram.png"
    print(f"\n[2/3] Plotting residual distribution histogram: {hist_png.name}...")
    dg.profiling.plot_strip_overlap_residuals(report, output_png=str(hist_png))

    # 3. Merge strips with correction applied
    master_las = OUTPUT_DIR / "master_unified_cloud.las"
    print(f"\n[3/3] Merging strips into unified master cloud: {master_las.name}...")
    dg.lidar.align_and_merge_strips(
        las_files=[str(STRIP1), str(STRIP2)],
        output_las=str(master_las),
        z_shifts=[0.0, report.median_offset],
    )

    print(f"\n[OK] Multi-strip co-registration complete! Outputs saved in: {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    main()
