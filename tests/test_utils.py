"""
tests.test_utils
~~~~~~~~~~~~~~~~
Unit tests for dronegeo spatial math, file validation, color ramps, and benchmarking utilities.
"""

import time
import numpy as np
import pytest
from dronegeo.utils.geo_utils import (
    calculate_bounding_box_intersection,
    format_spatial_extent,
    get_raster_metadata_summary,
    downsample_array_2d,
)
from dronegeo.utils.file_utils import (
    verify_las_file,
    verify_raster_file,
    format_file_size,
    ensure_output_directory,
)
from dronegeo.utils.color_utils import (
    get_elevation_colormap,
    get_vegetation_colormap,
    create_custom_diverging_colormap,
)
from dronegeo.utils.benchmarking import ExecutionTimer


def test_bounding_box_intersection():
    """Verify bounding box intersection calculations."""
    bbox1 = (100.0, 200.0, 100.0, 200.0)
    bbox2 = (150.0, 250.0, 150.0, 250.0)
    inter = calculate_bounding_box_intersection(bbox1, bbox2)
    assert inter == (150.0, 200.0, 150.0, 200.0)

    # Disjoint boxes
    bbox3 = (300.0, 400.0, 300.0, 400.0)
    assert calculate_bounding_box_intersection(bbox1, bbox3) is None


def test_format_spatial_extent():
    """Verify extent formatting string."""
    text = format_spatial_extent(100.0, 200.0, 300.0, 400.0)
    assert "Area:" in text
    assert "X:" in text
    assert "Y:" in text


def test_downsample_array_2d():
    """Verify 2D array downsampling decimation."""
    arr = np.zeros((100, 100))
    ds = downsample_array_2d(arr, factor=4)
    assert ds.shape == (25, 25)


def test_raster_metadata_summary(synthetic_dem_tif):
    """Verify GeoTIFF metadata extraction helper."""
    meta = get_raster_metadata_summary(synthetic_dem_tif)
    assert meta["width_px"] == 100
    assert meta["height_px"] == 100
    assert meta["band_count"] == 1
    assert "EPSG:32632" in meta["crs"]
    assert meta["z_min_m"] is not None
    assert meta["z_max_m"] is not None


def test_file_utils_validation(synthetic_las_file, synthetic_dem_tif):
    """Verify LAS and Raster validation helpers."""
    assert verify_las_file(synthetic_las_file) is True
    assert verify_raster_file(synthetic_dem_tif) is True
    assert format_file_size(1024 * 1024 * 5) == "5.00 MB"


def test_color_utils():
    """Verify colormap retrieval and custom colormap generation."""
    elev_cmap = get_elevation_colormap("terrain")
    assert elev_cmap is not None
    veg_cmap = get_vegetation_colormap()
    assert veg_cmap is not None
    div_cmap = create_custom_diverging_colormap()
    assert div_cmap is not None


def test_execution_timer():
    """Verify ExecutionTimer records elapsed runtime accurately."""
    with ExecutionTimer("Test Operation") as timer:
        time.sleep(0.05)
    assert timer.elapsed_seconds >= 0.04
