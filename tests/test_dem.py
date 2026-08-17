"""
tests.test_dem
~~~~~~~~~~~~~~
Unit tests for continuous DTM, DSM, CHM, and concave footprint extraction.
"""

import os
import pytest
import numpy as np
import rasterio
from dronegeo.dem.surface_models import (
    create_dtm,
    create_dsm,
    create_chm,
    create_intensity_raster,
)
from dronegeo.dem.boundary_extraction import extract_flight_footprint_mask


def test_create_dtm(synthetic_las_file, temp_workspace):
    """Verify DTM continuous surface generation."""
    out_dtm = temp_workspace / "dtm_test.tif"
    dtm_path = create_dtm(
        las_path=synthetic_las_file,
        output_tif=str(out_dtm),
        resolution=1.0,
        k_neighbors=4,
    )
    assert os.path.exists(dtm_path)
    with rasterio.open(dtm_path) as src:
        assert src.count == 1
        data = src.read(1)
        valid = data[data != src.nodata]
        assert len(valid) > 0
        assert valid.min() >= 240.0
        assert valid.max() <= 280.0


def test_create_dsm(synthetic_las_file, temp_workspace):
    """Verify DSM surface generation."""
    out_dsm = temp_workspace / "dsm_test.tif"
    dsm_path = create_dsm(
        las_path=synthetic_las_file,
        output_tif=str(out_dsm),
        resolution=1.0,
    )
    assert os.path.exists(dsm_path)
    with rasterio.open(dsm_path) as src:
        assert src.count == 1
        data = src.read(1)
        valid = data[data != src.nodata]
        assert len(valid) > 0


def test_create_chm(synthetic_las_file, temp_workspace):
    """Verify Canopy Height Model (CHM = DSM - DTM) calculation."""
    out_dtm = temp_workspace / "dtm_for_chm.tif"
    out_dsm = temp_workspace / "dsm_for_chm.tif"
    out_chm = temp_workspace / "chm_test.tif"

    create_dtm(synthetic_las_file, str(out_dtm), resolution=1.0)
    create_dsm(synthetic_las_file, str(out_dsm), resolution=1.0)

    chm_path = create_chm(
        dsm_path=str(out_dsm),
        dtm_path=str(out_dtm),
        output_tif=str(out_chm),
        clamp_min=0.0,
        clamp_max=50.0,
    )
    assert os.path.exists(chm_path)
    with rasterio.open(chm_path) as src:
        data = src.read(1)
        valid = data[data != src.nodata]
        assert len(valid) > 0
        assert valid.min() >= 0.0


def test_create_intensity_raster(synthetic_las_file, temp_workspace):
    """Verify LiDAR intensity raster generation."""
    out_int = temp_workspace / "intensity.tif"
    int_path = create_intensity_raster(synthetic_las_file, str(out_int), resolution=1.0)
    assert os.path.exists(int_path)


def test_extract_flight_footprint_mask(synthetic_las_file):
    """Verify footprint mask extraction."""
    mask, (h, w), bounds = extract_flight_footprint_mask(synthetic_las_file, pixel_res=1.0)
    assert mask is not None
    assert h > 0 and w > 0
    assert np.sum(mask) > 0
