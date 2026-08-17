#!/usr/bin/env python3
"""
Example 07: Elevation Transects & Spatial QC Chip Mapping
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Demonstrates:
- Extracting 1D topographic cross-sectional transects across a DEM.
- Generating multi-panel transect profile QC visualizations.
- Overlaying vector survey grid polygon chips with centroid label annotations.
"""

import sys
import os

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from pathlib import Path
import subprocess
import dronegeo as dg

OUTPUT_DIR = Path(__file__).parent / "outputs" / "07_profiling"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
SAMPLE_LAS = Path(__file__).parent / "data" / "flight_survey_master.las"
GRID_GEOJSON = Path(__file__).parent / "data" / "survey_grid.geojson"
DEM_TIF = OUTPUT_DIR / "sample_dtm.tif"


def ensure_sample_data():
    if not DEM_TIF.exists():
        if not SAMPLE_LAS.exists() or not GRID_GEOJSON.exists():
            gen_script = Path(__file__).parent / "00_generate_sample_datasets.py"
            subprocess.run([sys.executable, str(gen_script)], check=True)
        print("Generating baseline DTM for transect profiling...")
        dg.dem.create_dtm(str(SAMPLE_LAS), str(DEM_TIF), resolution=0.50)


def main():
    print("=" * 70)
    print("DroneGeo Example 07: Elevation Transects & QC Chip Mapping")
    print("=" * 70)

    ensure_sample_data()

    transect_png = OUTPUT_DIR / "elevation_transect_profiles.png"
    grid_map_png = OUTPUT_DIR / "survey_grid_chips_map.png"

    # 1. Extract and Plot 3 Cross-Sectional Transects
    print(f"\n[1/2] Generating cross-sectional elevation transects: {transect_png.name}...")
    dg.profiling.plot_elevation_transects(
        dem_path=str(DEM_TIF),
        output_png=str(transect_png),
        count=3,
        direction="vertical",
        title="Topographic Elevation Transect Cross-Sections",
    )

    # 2. Map Survey Vector Grid Chips on DEM
    print(f"\n[2/2] Overlaying survey grid vector chips: {grid_map_png.name}...")
    dg.profiling.map_grid_chips(
        dem_path=str(DEM_TIF),
        grid_vector_path=str(GRID_GEOJSON),
        output_png=str(grid_map_png),
        label_column="id",
        title="UAV Survey Vector Tile Grid Index",
    )

    print(f"\n[OK] QC plots generated in: {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    main()
