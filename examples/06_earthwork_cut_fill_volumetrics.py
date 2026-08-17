#!/usr/bin/env python3
"""
Example 06: 3D Earthwork Cut & Fill Volumetrics & Stockpile Audits
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Demonstrates:
- 3D Cut & Fill earthwork differential volume between multi-temporal survey epochs.
- Spatial elevation delta map (dZ GeoTIFF).
- Stockpile volume and surface footprint area calculation above reference base plane.
"""

import sys
import os

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from pathlib import Path
import subprocess
import dronegeo as dg

OUTPUT_DIR = Path(__file__).parent / "outputs" / "06_volumetrics"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
EPOCH1 = Path(__file__).parent / "data" / "quarry_epoch1.tif"
EPOCH2 = Path(__file__).parent / "data" / "quarry_epoch2.tif"


def ensure_sample_data():
    if not EPOCH1.exists() or not EPOCH2.exists():
        gen_script = Path(__file__).parent / "00_generate_sample_datasets.py"
        subprocess.run([sys.executable, str(gen_script)], check=True)


def main():
    print("=" * 70)
    print("DroneGeo Example 06: 3D Earthwork Volumetrics & Stockpiles")
    print("=" * 70)

    ensure_sample_data()

    diff_tif = OUTPUT_DIR / "quarry_elevation_difference.tif"

    # 1. Compute 3D Cut/Fill Volume between Epoch 1 and Epoch 2
    print(f"\n[1/2] Computing 3D Cut/Fill between Epoch 1 & Epoch 2...")
    vol_report = dg.analysis.compute_cut_fill_volume(
        before_dem=str(EPOCH1),
        after_dem=str(EPOCH2),
        output_diff_tif=str(diff_tif),
    )

    print("\n--- Earthwork Volumetric Report ---")
    print(f"Excavated Cut Volume : {vol_report.cut_volume_m3:,.2f} m3")
    print(f"Deposited Fill Volume: {vol_report.fill_volume_m3:,.2f} m3")
    print(f"Net Volume Balance   : {vol_report.net_volume_m3:+,.2f} m3")
    print(f"Active Surface Area  : {vol_report.surface_area_m2:,.1f} m2")
    print(f"Max Cut Depth (dZ)   : {vol_report.max_cut_depth_m:.2f} m")
    print(f"Max Fill Height (dZ) : {vol_report.max_fill_height_m:.2f} m")

    # 2. Compute Stockpile Volume against Reference Plane (e.g. 305.0m datum)
    print(f"\n[2/2] Computing Stockpile Volume against 305.0m base plane...")
    stockpile_report = dg.analysis.compute_stockpile_volume(
        dem_path=str(EPOCH2),
        base_elevation=305.0,
    )

    print("\n--- Stockpile Report ---")
    print(f"Stockpile Volume     : {stockpile_report.cut_volume_m3:,.2f} m3")
    print(f"Stockpile Footprint  : {stockpile_report.surface_area_m2:,.1f} m2")

    print(f"\n[OK] Volumetrics complete! Output difference GeoTIFF: {diff_tif.resolve()}")


if __name__ == "__main__":
    main()
