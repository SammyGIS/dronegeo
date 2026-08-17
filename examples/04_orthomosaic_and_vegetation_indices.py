#!/usr/bin/env python3
"""
Example 04: True-Color Orthomosaic & Visible Vegetation Indices
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Demonstrates:
- True-Color 4-band RGBA Orthomosaic generation from point cloud RGB color.
- Contrast histogram stretching (2%-98%).
- Photogrammetric Vegetation Indices:
  * VARI  (Visible Atmospherically Resistant Index) - Crop canopy greenness
  * GLI   (Green Leaf Index) - Leaf chlorophyll density
  * TGI   (Triangular Greenness Index) - Precision agricultural nitrogen/chlorophyll
  * ExG   (Excess Green Index) - Crop/weed segmentation
  * NGRDI (Normalized Green-Red Difference Index)
"""

import sys
import os

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from pathlib import Path
import subprocess
import dronegeo as dg

OUTPUT_DIR = Path(__file__).parent / "outputs" / "04_imagery"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
SAMPLE_LAS = Path(__file__).parent / "data" / "flight_survey_master.las"


def ensure_sample_data():
    if not SAMPLE_LAS.exists():
        gen_script = Path(__file__).parent / "00_generate_sample_datasets.py"
        subprocess.run([sys.executable, str(gen_script)], check=True)


def main():
    print("=" * 70)
    print("DroneGeo Example 04: True-Color Orthomosaic & Vegetation Indices")
    print("=" * 70)

    ensure_sample_data()

    # 1. Generate 4-band RGBA Orthomosaic (0.20m GSD)
    ortho_tif = OUTPUT_DIR / "true_color_orthomosaic.tif"
    print(f"\n[1/3] Rasterizing point cloud RGB into RGBA Orthomosaic: {ortho_tif.name}...")
    dg.imagery.create_true_color_orthomosaic(
        las_path=str(SAMPLE_LAS),
        output_tif=str(ortho_tif),
        resolution=0.20,
        alpha_channel=True,
        auto_contrast=True,
    )

    # 2. Compute Crop Vegetation Indices
    print("\n[2/3] Computing Photogrammetric Visible Vegetation Indices...")
    vari_tif = OUTPUT_DIR / "vegetation_vari.tif"
    gli_tif = OUTPUT_DIR / "vegetation_gli.tif"
    tgi_tif = OUTPUT_DIR / "vegetation_tgi.tif"
    exg_tif = OUTPUT_DIR / "vegetation_exg.tif"

    dg.imagery.compute_vari(str(ortho_tif), str(vari_tif))
    print(f"  * VARI Index  : {vari_tif.name}")

    dg.imagery.compute_gli(str(ortho_tif), str(gli_tif))
    print(f"  * GLI Index   : {gli_tif.name}")

    dg.imagery.compute_tgi(str(ortho_tif), str(tgi_tif))
    print(f"  * TGI Index   : {tgi_tif.name}")

    dg.imagery.compute_exg(str(ortho_tif), str(exg_tif))
    print(f"  * ExG Index   : {exg_tif.name}")

    meta = dg.utils.get_raster_metadata_summary(str(vari_tif))
    print("\n--- Output Summary ---")
    print(f"Ortho Resolution : {meta['resolution_x_m']} m GSD")
    print(f"VARI Value Range : [{meta['z_min_m']:.3f}, {meta['z_max_m']:.3f}]")
    print(f"\n[OK] All orthos and vegetation maps saved in: {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    main()
