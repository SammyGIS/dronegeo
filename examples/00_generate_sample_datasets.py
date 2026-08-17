#!/usr/bin/env python3
"""
Example 00: Generate Standard Sample Datasets
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Generates all canonical sample UAV LiDAR point clouds, multi-strip flightlines,
and survey datasets into `examples/data/` for downstream examples and tutorials.
"""

import sys
import os

# Ensure UTF-8 output encoding for cross-platform terminals
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import dronegeo as dg
from pathlib import Path
import numpy as np
import laspy
import pyproj
import rasterio
from rasterio.transform import from_origin
import geopandas as gpd
from shapely.geometry import box

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
CRS_EPSG = 32632  # WGS84 / UTM Zone 32N


def generate_master_las(path: Path) -> None:
    """Generates a rich 50,000 pt survey with topography, tree canopy, RGB, and intensity."""
    if path.exists():
        print(f"  [OK] {path.name} already exists.")
        return

    print(f"  [+] Generating {path.name} (50,000 points)...")
    np.random.seed(42)
    n = 50_000

    # 250m x 250m survey bounding box
    x = 500000.0 + np.random.uniform(0, 250, n)
    y = 5200000.0 + np.random.uniform(0, 250, n)

    # Complex undulating terrain surface with ridge, valley, and drainage gully
    terrain_z = (
        250.0
        + 0.06 * (x - 500000.0)
        + 0.04 * (y - 5200000.0)
        + 8.0 * np.sin((x - 500000.0) / 35.0) * np.cos((y - 5200000.0) / 35.0)
    )

    # 65% Ground points (class 2), 35% Vegetation (class 4/5)
    is_ground = np.random.rand(n) > 0.35
    classification = np.where(is_ground, 2, np.random.choice([4, 5], size=n))
    z = np.where(is_ground, terrain_z + np.random.normal(0, 0.04, n), terrain_z + np.random.uniform(2.5, 18.0, n))

    # Multi-return pulses
    return_num = np.random.choice([1, 2], size=n, p=[0.80, 0.20]).astype(np.uint8)
    num_returns = np.where(return_num == 2, 2, 1).astype(np.uint8)

    # Photometric RGB and NIR-like Intensity
    intensity = np.where(is_ground, np.random.randint(1200, 3500, n), np.random.randint(4500, 18000, n)).astype(np.uint16)
    red = np.where(is_ground, np.random.randint(22000, 38000, n), np.random.randint(8000, 18000, n)).astype(np.uint16)
    green = np.where(is_ground, np.random.randint(19000, 32000, n), np.random.randint(38000, 58000, n)).astype(np.uint16)
    blue = np.where(is_ground, np.random.randint(14000, 26000, n), np.random.randint(6000, 16000, n)).astype(np.uint16)

    header = laspy.LasHeader(point_format=3, version="1.4")
    header.offsets = [500000.0, 5200000.0, 200.0]
    header.scales = [0.001, 0.001, 0.001]
    header.add_crs(pyproj.CRS.from_epsg(CRS_EPSG))

    las = laspy.LasData(header)
    las.x, las.y, las.z = x, y, z
    las.intensity = intensity
    las.raw_classification = classification.astype(np.uint8)
    las.return_number = return_num
    las.number_of_returns = num_returns
    las.red, las.green, las.blue = red, green, blue

    las.write(str(path))
    print(f"      Saved: {path.name} ({path.stat().st_size / (1024*1024):.2f} MB)")


def generate_flight_strips(s1_path: Path, s2_path: Path) -> None:
    """Generates two overlapping flight passes with +0.12m vertical shift in overlap zone."""
    if s1_path.exists() and s2_path.exists():
        print(f"  [OK] {s1_path.name} & {s2_path.name} already exist.")
        return

    print("  [+] Generating overlapping flight strips (Strip 1 & Strip 2 with +0.12m dZ)...")
    np.random.seed(101)

    # Strip 1: X in [500000, 500140], Y in [5200000, 5200200]
    n1 = 20_000
    x1 = 500000.0 + np.random.uniform(0, 140, n1)
    y1 = 5200000.0 + np.random.uniform(0, 200, n1)
    z1 = 250.0 + 0.05 * (x1 - 500000.0) + 0.03 * (y1 - 5200000.0) + np.random.normal(0, 0.03, n1)

    h1 = laspy.LasHeader(point_format=2, version="1.4")
    h1.offsets = [500000.0, 5200000.0, 200.0]
    h1.scales = [0.001, 0.001, 0.001]
    h1.add_crs(pyproj.CRS.from_epsg(CRS_EPSG))
    las1 = laspy.LasData(h1)
    las1.x, las1.y, las1.z = x1, y1, z1
    las1.raw_classification = np.full(n1, 2, dtype=np.uint8)
    las1.write(str(s1_path))

    # Strip 2: X in [500070, 500210] (Overlap from 500070 to 500140 = 70m) with +0.12m datum shift
    n2 = 20_000
    x2 = 500070.0 + np.random.uniform(0, 140, n2)
    y2 = 5200000.0 + np.random.uniform(0, 200, n2)
    z2 = 250.0 + 0.05 * (x2 - 500000.0) + 0.03 * (y2 - 5200000.0) + 0.12 + np.random.normal(0, 0.03, n2)

    h2 = laspy.LasHeader(point_format=2, version="1.4")
    h2.offsets = [500000.0, 5200000.0, 200.0]
    h2.scales = [0.001, 0.001, 0.001]
    h2.add_crs(pyproj.CRS.from_epsg(CRS_EPSG))
    las2 = laspy.LasData(h2)
    las2.x, las2.y, las2.z = x2, y2, z2
    las2.raw_classification = np.full(n2, 2, dtype=np.uint8)
    las2.write(str(s2_path))

    print(f"      Saved: {s1_path.name}, {s2_path.name}")


def generate_quarry_epochs(e1_path: Path, e2_path: Path) -> None:
    """Generates two DEM epochs representing quarry earthwork excavation and stockpile deposition."""
    if e1_path.exists() and e2_path.exists():
        print(f"  [OK] {e1_path.name} & {e2_path.name} already exist.")
        return

    print("  [+] Generating multi-epoch DEMs for earthwork volumetrics...")
    rows, cols = 150, 150
    res = 1.0
    y, x = np.mgrid[0:rows, 0:cols]

    # Epoch 1: Natural terrain with pre-excavation hillside
    base = 300.0 + 0.08 * x + 0.05 * y + 3.0 * np.sin(x / 15.0)
    e1 = base.astype(np.float32)

    # Epoch 2: Excavated pit (cut) in center-left, and newly built aggregate stockpile (fill) in top-right
    e2 = e1.copy()
    pit_mask = ((x - 50)**2 + (y - 75)**2) < 25**2
    e2[pit_mask] -= 6.0 * (1.0 - np.sqrt((x[pit_mask] - 50)**2 + (y[pit_mask] - 75)**2) / 25.0).astype(np.float32)

    stockpile_mask = ((x - 110)**2 + (y - 110)**2) < 20**2
    e2[stockpile_mask] += 5.0 * (1.0 - np.sqrt((x[stockpile_mask] - 110)**2 + (y[stockpile_mask] - 110)**2) / 20.0).astype(np.float32)

    transform = from_origin(500000.0, 5200150.0, res, res)
    crs = rasterio.crs.CRS.from_epsg(CRS_EPSG)

    for path, data in [(e1_path, e1), (e2_path, e2)]:
        with rasterio.open(
            str(path), "w", driver="GTiff", height=rows, width=cols, count=1,
            dtype="float32", crs=crs, transform=transform, nodata=-9999.0
        ) as dst:
            dst.write(data, 1)

    print(f"      Saved: {e1_path.name}, {e2_path.name}")


def generate_survey_grid_vector(path: Path) -> None:
    """Generates vector survey tile grid polygons (4x4 tiles)."""
    if path.exists():
        print(f"  [OK] {path.name} already exists.")
        return

    print(f"  [+] Generating vector survey tile grid: {path.name}...")
    tile_size = 62.5
    chips = []
    chip_ids = []

    for r in range(4):
        for c in range(4):
            x_min = 500000.0 + c * tile_size
            x_max = x_min + tile_size
            y_min = 5200000.0 + r * tile_size
            y_max = y_min + tile_size
            chips.append(box(x_min, y_min, x_max, y_max))
            chip_ids.append(f"BLOCK_{r+1}{chr(65+c)}")

    gdf = gpd.GeoDataFrame({"id": chip_ids, "geometry": chips}, crs=f"EPSG:{CRS_EPSG}")
    gdf.to_file(str(path), driver="GeoJSON")
    print(f"      Saved: {path.name}")


def main():
    print("=" * 75)
    print("DroneGeo: Generating Canonical Sample Datasets in examples/data/")
    print("=" * 75)

    generate_master_las(DATA_DIR / "flight_survey_master.las")
    generate_flight_strips(DATA_DIR / "flight_strip_01.las", DATA_DIR / "flight_strip_02.las")
    generate_quarry_epochs(DATA_DIR / "quarry_epoch1.tif", DATA_DIR / "quarry_epoch2.tif")
    generate_survey_grid_vector(DATA_DIR / "survey_grid.geojson")

    print("\n[OK] All sample datasets are ready in:")
    print(f"     {DATA_DIR.resolve()}\n")


if __name__ == "__main__":
    main()
