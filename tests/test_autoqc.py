"""
tests.test_autoqc
~~~~~~~~~~~~~~~~~
Unit and integration tests for the DroneGeo AutoQC inspection, diagnostic,
and auto-remediation engine.
"""

from pathlib import Path
import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin
import laspy
import pyproj

from dronegeo.diagnostics.autoqc import (
    inspect_point_cloud,
    inspect_elevation_model,
    correct_point_cloud,
    correct_point_clouud,
    remediate_point_cloud,
    remediate_elevation_model,
    inspect,
    correct,
    remediate,
    IssueSeverity,
)


@pytest.fixture
def noisy_synthetic_las(tmp_path):
    """Creates a synthetic LAS file with injected defects (missing CRS and multipath floaters)."""
    las_path = tmp_path / "defective_survey.las"
    n = 5000
    # 50m x 50m area = 2.0 pts/m2
    x = 500000.0 + np.random.uniform(0, 50, n)
    y = 5200000.0 + np.random.uniform(0, 50, n)
    z = 250.0 + 0.05 * (x - 500000.0) + np.random.normal(0, 0.05, n)

    # Inject 20 severe multipath floaters
    z[:20] += 150.0

    classification = np.full(n, 2, dtype=np.uint8)

    header = laspy.LasHeader(point_format=2, version="1.4")
    header.offsets = [500000.0, 5200000.0, 200.0]
    header.scales = [0.001, 0.001, 0.001]
    # Intentionally do NOT add CRS

    las = laspy.LasData(header)
    las.x, las.y, las.z = x, y, z
    las.raw_classification = classification
    las.write(str(las_path))
    return str(las_path)


@pytest.fixture
def defective_dem_geotiff(tmp_path):
    """Creates a synthetic DEM with NoData holes and sharp vertical spike tears."""
    dem_path = tmp_path / "defective_dem.tif"
    rows, cols = 60, 60
    y, x = np.mgrid[0:rows, 0:cols]
    data = (300.0 + 0.05 * x + 0.03 * y).astype(np.float32)

    # Inject NoData void hole in center (10x10)
    data[25:35, 25:35] = -9999.0

    # Inject vertical spike
    data[10, 10] += 50.0

    transform = from_origin(500000.0, 5200060.0, 1.0, 1.0)
    crs = rasterio.crs.CRS.from_epsg(32632)

    with rasterio.open(
        str(dem_path), "w", driver="GTiff", height=rows, width=cols, count=1,
        dtype="float32", crs=crs, transform=transform, nodata=-9999.0
    ) as dst:
        dst.write(data, 1)

    return str(dem_path)


def test_inspect_and_remediate_point_cloud(noisy_synthetic_las, tmp_path):
    """Verify LAS inspection identifies missing CRS & floaters, and auto-remediate repairs them."""
    # 1. Inspect
    report = inspect_point_cloud(noisy_synthetic_las, expected_crs=32632)
    assert report.quality_score < 100
    assert report.has_critical_issues
    assert any(i.code == "LAS_CRS_MISSING" for i in report.issues)
    assert any(i.code == "LAS_MULTIPATH_NOISE" for i in report.issues)

    # Verify report formatting
    md = report.to_markdown()
    assert "AutoQC: Diagnostic & Survey Health Report" in md
    assert "LAS_MULTIPATH_NOISE" in md

    js = report.to_json()
    assert "quality_score" in js

    # 2. Correct / Remediate
    clean_las = tmp_path / "repaired_survey.las"
    correct_point_cloud(noisy_synthetic_las, str(clean_las), report=report, assign_crs=32632)
    assert clean_las.exists()

    # Verify alias parity
    assert correct_point_clouud is correct_point_cloud
    assert remediate_point_cloud is correct_point_cloud

    # 3. Re-inspect repaired LAS
    recheck = inspect_point_cloud(str(clean_las), expected_crs=32632)
    assert recheck.quality_score == 100
    assert not any(i.code == "LAS_CRS_MISSING" for i in recheck.issues)
    assert not any(i.code == "LAS_MULTIPATH_NOISE" for i in recheck.issues)


def test_inspect_and_remediate_elevation_model(defective_dem_geotiff, tmp_path):
    """Verify DEM inspection detects void holes & spikes, and auto-remediation heals them."""
    # 1. Inspect
    report = inspect_elevation_model(defective_dem_geotiff)
    assert report.quality_score < 100
    assert any(i.code == "DEM_VOID_POCKETS" for i in report.issues)
    assert any(i.code == "DEM_ELEVATION_SPIKES" for i in report.issues)

    # 2. Remediate
    healed_dem = tmp_path / "healed_dem.tif"
    remediate_elevation_model(defective_dem_geotiff, str(healed_dem), report=report)
    assert healed_dem.exists()

    # 3. Verify healed DEM has zero NoData in survey area and suppressed spikes
    with rasterio.open(str(healed_dem)) as src:
        data = src.read(1)
        assert not np.any(np.isclose(data, -9999.0))
        assert np.max(data) < 320.0  # Spike of +50m (350m+) smoothed out

    # Re-inspect
    recheck = inspect_elevation_model(str(healed_dem))
    assert recheck.quality_score >= 95


def test_generic_dispatcher(noisy_synthetic_las, defective_dem_geotiff, tmp_path):
    """Verify dg.autoqc.inspect and dg.autoqc.remediate dispatch correctly by extension."""
    rep_las = inspect(noisy_synthetic_las)
    assert rep_las.dataset_type == "point_cloud"

    rep_dem = inspect(defective_dem_geotiff)
    assert rep_dem.dataset_type == "elevation_model"

    out_las = tmp_path / "auto_disp_las.las"
    correct(noisy_synthetic_las, str(out_las))
    assert out_las.exists()

    out_dem = tmp_path / "auto_disp_dem.tif"
    remediate(defective_dem_geotiff, str(out_dem))
    assert out_dem.exists()
    assert correct is remediate
