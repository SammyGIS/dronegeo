#!/usr/bin/env python3
"""
Example 03: Survey-Grade Surface Models (DTM, DSM, CHM & Intensity)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Demonstrates:
- Continuous Digital Terrain Model (DTM) with multi-threaded k-NN IDW.
- Digital Surface Model (DSM) with maximum surface return filtering.
- Canopy Height Model (CHM = DSM - DTM) for vegetation canopy audit.
- LiDAR Intensity rasterization.
"""

import sys
import os

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from pathlib import Path
import subprocess
import dronegeo as dg

OUTPUT_DIR = Path(__file__).parent / "outputs" / "03_surfaces"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
SAMPLE_LAS = Path(__file__).parent / "data" / "flight_survey_master.las"


def ensure_sample_data():
    if not SAMPLE_LAS.exists():
        gen_script = Path(__file__).parent / "00_generate_sample_datasets.py"
        subprocess.run([sys.executable, str(gen_script)], check=True)


def main():
    print("=" * 70)
    print("DroneGeo Example 03: DTM, DSM, CHM & Intensity Generation")
    print("=" * 70)

    ensure_sample_data()

    dtm_tif = OUTPUT_DIR / "survey_dtm.tif"
    dsm_tif = OUTPUT_DIR / "survey_dsm.tif"
    chm_tif = OUTPUT_DIR / "canopy_height_model.tif"
    intensity_tif = OUTPUT_DIR / "lidar_intensity.tif"

    # 1. Generate Continuous DTM (0.25m)
    print(f"\n[1/4] Generating Continuous Ground DTM: {dtm_tif.name}...")
    dg.dem.create_dtm(
        las_path=str(SAMPLE_LAS),
        output_tif=str(dtm_tif),
        resolution=0.25,
        k_neighbors=8,
        ground_class=2,
    )

    # 2. Generate Continuous DSM (0.25m)
    print(f"\n[2/4] Generating Maximum Return DSM: {dsm_tif.name}...")
    dg.dem.create_dsm(
        las_path=str(SAMPLE_LAS),
        output_tif=str(dsm_tif),
        resolution=0.25,
    )

    # 3. Compute Canopy Height Model (CHM = DSM - DTM)
    print(f"\n[3/4] Computing Canopy Height Model: {chm_tif.name}...")
    dg.dem.create_chm(
        dsm_path=str(dsm_tif),
        dtm_path=str(dtm_tif),
        output_tif=str(chm_tif),
        clamp_min=0.0,
        clamp_max=40.0,
    )

    # 4. Generate LiDAR Intensity Raster
    print(f"\n[4/4] Generating Intensity Raster: {intensity_tif.name}...")
    dg.dem.create_intensity_raster(
        las_path=str(SAMPLE_LAS),
        output_tif=str(intensity_tif),
        resolution=0.25,
    )

    # Summary
    meta = dg.utils.get_raster_metadata_summary(str(dtm_tif))
    print("\n--- Output Deliverables Summary ---")
    print(f"GSD Resolution : {meta['resolution_x_m']} m")
    print(f"Dimensions     : {meta['width_px']} x {meta['height_px']} px")
    print(f"CRS            : {meta['crs']}")
    print(f"DTM Elevation  : [{meta['z_min_m']:.2f}m - {meta['z_max_m']:.2f}m]")
    print(f"\n[OK] All surface models generated in: {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    main()
