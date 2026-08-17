"""
tests.conftest
~~~~~~~~~~~~~~
Shared pytest fixtures and synthetic data generators for dronegeo unit and integration tests.
Generates realistic UAV LiDAR point clouds and GeoTIFF surface models without external network downloads.
"""

import os
import sys
import tempfile
from pathlib import Path
import pytest
import numpy as np

import matplotlib
matplotlib.use("Agg")

# Ensure clean PROJ bindings before rasterio initialization
try:
    import pyproj.datadir
    _proj_dir = pyproj.datadir.get_data_dir()
    if _proj_dir and os.path.exists(_proj_dir):
        os.environ["PROJ_DATA"] = _proj_dir
        os.environ["PROJ_LIB"] = _proj_dir
except Exception:
    pass

import laspy
import rasterio
from rasterio.transform import from_origin
from rasterio.crs import CRS


@pytest.fixture(scope="session")
def sample_crs_epsg():
    """Default Projected Coordinate Reference System (UTM Zone 32N / WGS84)."""
    return 32632


@pytest.fixture(scope="session")
def sample_bounds():
    """Geographic bounding box for synthetic test surveys (minx, miny, maxx, maxy)."""
    return (500000.0, 5200000.0, 500100.0, 5200100.0)


@pytest.fixture
def temp_workspace():
    """Provides an isolated temporary directory for test output generation."""
    with tempfile.TemporaryDirectory(prefix="dronegeo_test_") as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def synthetic_las_file(temp_workspace, sample_crs_epsg):
    """
    Creates a synthetic LAS 1.4 point cloud file with:
    - 5,000 points
    - Ground (class 2) and Vegetation (class 4, 5) classifications
    - Multi-returns (1 of 1, 1 of 2, 2 of 2)
    - RGB color channels
    - Realistic undulating elevation surface
    """
    las_path = temp_workspace / "synthetic_survey.las"

    n_points = 5000
    np.random.seed(42)

    # 100m x 100m bounding box
    x = 500000.0 + np.random.uniform(0, 100, n_points)
    y = 5200000.0 + np.random.uniform(0, 100, n_points)

    # Undulating terrain z = base + slope + sinusoidal ripples
    base_z = 250.0 + 0.05 * (x - 500000.0) + 0.03 * (y - 5200000.0) + 2.5 * np.sin((x - 500000.0) / 15.0)
    
    # 70% Ground points (class 2), 30% Canopy/Vegetation (class 4/5)
    is_ground = np.random.rand(n_points) > 0.30
    classification = np.where(is_ground, 2, np.random.choice([4, 5], size=n_points))
    
    # Add canopy height for non-ground points
    z = np.where(is_ground, base_z + np.random.normal(0, 0.05, n_points), base_z + np.random.uniform(2.0, 12.0, n_points))

    # Intensity & RGB
    intensity = np.where(is_ground, np.random.randint(1000, 3000, n_points), np.random.randint(4000, 15000, n_points)).astype(np.uint16)
    red = np.where(is_ground, np.random.randint(20000, 35000, n_points), np.random.randint(10000, 20000, n_points)).astype(np.uint16)
    green = np.where(is_ground, np.random.randint(18000, 30000, n_points), np.random.randint(35000, 55000, n_points)).astype(np.uint16)
    blue = np.where(is_ground, np.random.randint(15000, 25000, n_points), np.random.randint(8000, 18000, n_points)).astype(np.uint16)

    # Returns
    return_number = np.random.choice([1, 2], size=n_points, p=[0.8, 0.2]).astype(np.uint8)
    number_of_returns = np.where(return_number == 2, 2, 1).astype(np.uint8)

    import pyproj
    pyproj_crs = pyproj.CRS.from_epsg(sample_crs_epsg)

    # Build LAS header
    header = laspy.LasHeader(point_format=3, version="1.4")
    header.offsets = [500000.0, 5200000.0, 200.0]
    header.scales = [0.001, 0.001, 0.001]
    header.add_crs(pyproj_crs)

    las = laspy.LasData(header)
    las.x = x
    las.y = y
    las.z = z
    las.intensity = intensity
    las.raw_classification = classification.astype(np.uint8)
    las.return_number = return_number
    las.number_of_returns = number_of_returns
    las.red = red
    las.green = green
    las.blue = blue

    las.write(str(las_path))
    return str(las_path)


@pytest.fixture
def synthetic_overlapping_strips(temp_workspace, sample_crs_epsg):
    """
    Creates two overlapping flight strips with a calibrated +0.15m vertical shift (ΔZ)
    in the 40m overlap corridor.
    """
    import pyproj
    pyproj_crs = pyproj.CRS.from_epsg(sample_crs_epsg)

    strip1_path = temp_workspace / "flight_strip_01.las"
    strip2_path = temp_workspace / "flight_strip_02.las"

    np.random.seed(101)
    
    # Strip 1: X in [500000, 500080], Y in [5200000, 5200100]
    n1 = 3000
    x1 = 500000.0 + np.random.uniform(0, 80, n1)
    y1 = 5200000.0 + np.random.uniform(0, 100, n1)
    z1 = 250.0 + 0.04 * (x1 - 500000.0) + 0.02 * (y1 - 5200000.0) + np.random.normal(0, 0.03, n1)

    h1 = laspy.LasHeader(point_format=2, version="1.4")
    h1.offsets = [500000.0, 5200000.0, 200.0]
    h1.scales = [0.001, 0.001, 0.001]
    h1.add_crs(pyproj_crs)
    las1 = laspy.LasData(h1)
    las1.x = x1
    las1.y = y1
    las1.z = z1
    las1.raw_classification = np.full(n1, 2, dtype=np.uint8)
    las1.write(str(strip1_path))

    # Strip 2: X in [500040, 500120] (Overlap from 500040 to 500080), with +0.15m vertical offset
    n2 = 3000
    x2 = 500040.0 + np.random.uniform(0, 80, n2)
    y2 = 5200000.0 + np.random.uniform(0, 100, n2)
    z2 = 250.0 + 0.04 * (x2 - 500000.0) + 0.02 * (y2 - 5200000.0) + 0.15 + np.random.normal(0, 0.03, n2)

    h2 = laspy.LasHeader(point_format=2, version="1.4")
    h2.offsets = [500000.0, 5200000.0, 200.0]
    h2.scales = [0.001, 0.001, 0.001]
    h2.add_crs(pyproj_crs)
    las2 = laspy.LasData(h2)
    las2.x = x2
    las2.y = y2
    las2.z = z2
    las2.raw_classification = np.full(n2, 2, dtype=np.uint8)
    las2.write(str(strip2_path))

    return str(strip1_path), str(strip2_path)


@pytest.fixture
def synthetic_dem_tif(temp_workspace, sample_crs_epsg):
    """
    Creates a synthetic 100x100 float32 DEM GeoTIFF (resolution=1.0m)
    with smooth parabolic terrain and known elevation bounds.
    """
    dem_path = temp_workspace / "synthetic_dem.tif"
    rows, cols = 100, 100
    res = 1.0

    y, x = np.mgrid[0:rows, 0:cols]
    elevation = 200.0 + 0.05 * x + 0.08 * y + 5.0 * np.sin(x / 10.0) * np.cos(y / 10.0)
    elevation = elevation.astype(np.float32)

    transform = from_origin(500000.0, 5200100.0, res, res)
    crs = CRS.from_epsg(sample_crs_epsg)

    with rasterio.open(
        str(dem_path),
        "w",
        driver="GTiff",
        height=rows,
        width=cols,
        count=1,
        dtype="float32",
        crs=crs,
        transform=transform,
        nodata=-9999.0,
    ) as dst:
        dst.write(elevation, 1)

    return str(dem_path)


@pytest.fixture
def synthetic_ortho_tif(temp_workspace, sample_crs_epsg):
    """
    Creates a synthetic 4-band RGBA uint8 Orthomosaic GeoTIFF (100x100 pixels, resolution=1.0m).
    """
    ortho_path = temp_workspace / "synthetic_ortho.tif"
    rows, cols = 100, 100
    res = 1.0

    r = np.random.randint(50, 180, (rows, cols), dtype=np.uint8)
    g = np.random.randint(120, 240, (rows, cols), dtype=np.uint8)
    b = np.random.randint(30, 100, (rows, cols), dtype=np.uint8)
    a = np.full((rows, cols), 255, dtype=np.uint8)

    transform = from_origin(500000.0, 5200100.0, res, res)
    crs = CRS.from_epsg(sample_crs_epsg)

    with rasterio.open(
        str(ortho_path),
        "w",
        driver="GTiff",
        height=rows,
        width=cols,
        count=4,
        dtype="uint8",
        crs=crs,
        transform=transform,
    ) as dst:
        dst.write(r, 1)
        dst.write(g, 2)
        dst.write(b, 3)
        dst.write(a, 4)

    return str(ortho_path)
