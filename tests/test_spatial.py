"""
tests.test_spatial
~~~~~~~~~~~~~~~~~~
Unit tests for CRS resolver, EPSG/WKT coordinate system extraction, and PROJ bindings.
"""

import pytest
from rasterio.crs import CRS
from dronegeo.spatial.crs_manager import (
    resolve_crs,
    get_spatial_bounds_from_las,
    get_spatial_bounds_from_raster,
    bind_proj_environment,
)


def test_resolve_crs_numeric_and_string():
    """Verify resolve_crs handles numeric and string EPSG identifiers."""
    crs1 = resolve_crs(32632)
    assert crs1.to_epsg() == 32632

    crs2 = resolve_crs("EPSG:4326")
    assert crs2.to_epsg() == 4326


def test_get_spatial_bounds_from_raster(synthetic_dem_tif):
    """Verify spatial bounds and metadata extraction from GeoTIFF."""
    info = get_spatial_bounds_from_raster(synthetic_dem_tif)
    assert info["width"] == 100
    assert info["height"] == 100
    assert "EPSG:32632" in info["crs"]
    assert info["min_x"] < info["max_x"]
    assert info["min_y"] < info["max_y"]


def test_get_spatial_bounds_from_las(synthetic_las_file):
    """Verify spatial bounds extraction from LAS header without full point array load."""
    bounds = get_spatial_bounds_from_las(synthetic_las_file)
    assert bounds["point_count"] == 5000
    assert bounds["min_x"] < bounds["max_x"]
    assert bounds["min_y"] < bounds["max_y"]


def test_bind_proj_environment():
    """Verify safe binding of PROJ data directory."""
    result = bind_proj_environment()
    # Should either return a string path or None if not applicable
    assert result is None or isinstance(result, str)
