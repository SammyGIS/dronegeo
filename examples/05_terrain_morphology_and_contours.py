#!/usr/bin/env python3
"""
Example 05: Terrain Morphology & Vector Contours
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Demonstrates:
- 8-bit Photometric Analytical Hillshade (Horn's algorithm, Azimuth 315 NW, Altitude 45).
- Topographic Slope gradient map (in degrees / percent).
- Compass Aspect heading map (0 - 360 deg).
- Terrain Ruggedness Index (TRI / Riley et al., 1999).
- Smooth Vector Elevation Contour Lines (GeoJSON / Shapefile export).
"""

import sys
import os

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from pathlib import Path
import subprocess
import dronegeo as dg

OUTPUT_DIR = Path(__file__).parent / "outputs" / "05_morphology"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
SAMPLE_LAS = Path(__file__).parent / "data" / "flight_survey_master.las"
DEM_TIF = OUTPUT_DIR / "base_dtm.tif"


def ensure_base_dem():
    if not DEM_TIF.exists():
        if not SAMPLE_LAS.exists():
            gen_script = Path(__file__).parent / "00_generate_sample_datasets.py"
            subprocess.run([sys.executable, str(gen_script)], check=True)
        print("Generating baseline DTM for terrain morphology...")
        dg.dem.create_dtm(str(SAMPLE_LAS), str(DEM_TIF), resolution=0.50)


def main():
    print("=" * 70)
    print("DroneGeo Example 05: Terrain Morphology & Contours")
    print("=" * 70)

    ensure_base_dem()

    hillshade_tif = OUTPUT_DIR / "hillshade_315_45.tif"
    slope_tif = OUTPUT_DIR / "slope_degrees.tif"
    aspect_tif = OUTPUT_DIR / "aspect_compass.tif"
    tri_tif = OUTPUT_DIR / "terrain_ruggedness_index.tif"
    contours_geojson = OUTPUT_DIR / "contour_lines_1m.geojson"

    # 1. Analytical Photometric Hillshade
    print(f"\n[1/5] Generating 8-bit Hillshade: {hillshade_tif.name}...")
    dg.analysis.generate_hillshade(
        dem_path=str(DEM_TIF),
        output_tif=str(hillshade_tif),
        azimuth_deg=315.0,
        altitude_deg=45.0,
        z_factor=1.0,
    )

    # 2. Slope Map
    print(f"\n[2/5] Generating Slope Map: {slope_tif.name}...")
    dg.analysis.generate_slope_map(
        dem_path=str(DEM_TIF),
        output_tif=str(slope_tif),
        units="degrees",
    )

    # 3. Compass Aspect Map
    print(f"\n[3/5] Generating Aspect Map: {aspect_tif.name}...")
    dg.analysis.generate_aspect_map(
        dem_path=str(DEM_TIF),
        output_tif=str(aspect_tif),
    )

    # 4. Terrain Ruggedness Index (TRI)
    print(f"\n[4/5] Computing Terrain Ruggedness Index: {tri_tif.name}...")
    dg.analysis.generate_terrain_ruggedness_index(
        dem_path=str(DEM_TIF),
        output_tif=str(tri_tif),
    )

    # 5. Vector Contour Lines
    print(f"\n[5/5] Extracting 1.0m Vector Contour Lines: {contours_geojson.name}...")
    gdf = dg.analysis.generate_contour_lines(
        dem_path=str(DEM_TIF),
        output_vector_path=str(contours_geojson),
        interval_m=1.0,
    )

    print("\n--- Morphology Deliverables Summary ---")
    print(f"Extracted Contours : {len(gdf):,} polyline segments")
    print(f"Elevation Range    : [{gdf['elevation'].min():.1f}m - {gdf['elevation'].max():.1f}m]")
    print(f"\n[OK] All morphology deliverables saved in: {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    main()
