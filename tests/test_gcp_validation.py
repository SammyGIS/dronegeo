"""
tests/test_gcp_validation.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Comprehensive unit and integration test suite for Ground Control Point (GCP)
and survey checkpoint accuracy diagnostics, format loaders, and AutoQC auto-remediation.
"""

import json
import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin
import laspy
from pathlib import Path

import dronegeo as dg
from dronegeo.diagnostics.gcp_validation import (
    PointType,
    ResidualStatus,
    GCPResidualPoint,
    GCPValidationReport,
    load_gcp_dataset,
    validate_gcp_accuracy,
)


@pytest.fixture
def sample_las_and_gcps(tmp_path):
    """Creates a synthetic LAS point cloud and corresponding GCP dataset."""
    las_path = tmp_path / "survey_flight.las"
    csv_path = tmp_path / "survey_gcps.csv"
    geojson_path = tmp_path / "survey_gcps.geojson"

    # 1. Create LAS terrain surface with base elevation = 100.0m + slope
    n_pts = 5000
    xs = np.random.uniform(500000.0, 500100.0, n_pts)
    ys = np.random.uniform(5200000.0, 5200100.0, n_pts)
    zs = 100.0 + 0.05 * (xs - 500000.0) + 0.02 * (ys - 5200000.0)

    header = laspy.LasHeader(point_format=3, version="1.4")
    header.offsets = [500000.0, 5200000.0, 100.0]
    header.scales = [0.001, 0.001, 0.001]

    las = laspy.LasData(header)
    las.x = xs
    las.y = ys
    las.z = zs
    las.raw_classification = np.full(n_pts, 2, dtype=np.uint8)  # Ground class
    las.write(str(las_path))

    # 2. Create 5 GCPs: 4 accurate, 1 outlier blunder
    gcps = [
        ("GCP_01", 500020.0, 5200020.0, 100.0 + 0.05 * 20.0 + 0.02 * 20.0, "GCP"),
        ("GCP_02", 500040.0, 5200040.0, 100.0 + 0.05 * 40.0 + 0.02 * 40.0, "GCP"),
        ("GCP_03", 500060.0, 5200060.0, 100.0 + 0.05 * 60.0 + 0.02 * 60.0, "GCP"),
        ("CHK_01", 500080.0, 5200080.0, 100.0 + 0.05 * 80.0 + 0.02 * 80.0, "CHECK"),
        ("GCP_OUTLIER", 500050.0, 5200050.0, (100.0 + 0.05 * 50.0 + 0.02 * 50.0) - 0.75, "GCP"),  # 75cm blunder
    ]

    # Write CSV
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("id,easting,northing,elevation,type\n")
        for gid, gx, gy, gz, gtype in gcps:
            f.write(f"{gid},{gx},{gy},{gz:.3f},{gtype}\n")

    # Write GeoJSON
    features = []
    for gid, gx, gy, gz, gtype in gcps:
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [gx, gy, gz]},
            "properties": {"id": gid, "type": gtype, "elevation": gz}
        })
    geojson_data = {"type": "FeatureCollection", "features": features}
    with open(geojson_path, "w", encoding="utf-8") as f:
        json.dump(geojson_data, f)

    return las_path, csv_path, geojson_path, gcps


@pytest.fixture
def sample_dem(tmp_path):
    """Creates a synthetic DTM GeoTIFF raster."""
    dem_path = tmp_path / "terrain_dem.tif"
    transform = from_origin(500000.0, 5200100.0, 1.0, 1.0)
    data = np.full((100, 100), 100.0, dtype=np.float32)

    with rasterio.open(
        str(dem_path),
        "w",
        driver="GTiff",
        height=100,
        width=100,
        count=1,
        dtype="float32",
        crs="EPSG:32632",
        transform=transform,
        nodata=-9999.0,
    ) as dst:
        dst.write(data, 1)

    return dem_path


def test_load_gcp_csv(sample_las_and_gcps):
    _, csv_path, _, _ = sample_las_and_gcps
    points = load_gcp_dataset(csv_path)
    assert len(points) == 5
    assert points[0][0] == "GCP_01"
    assert points[0][4] == PointType.GCP
    assert points[3][4] == PointType.CHECK


def test_load_gcp_geojson(sample_las_and_gcps):
    _, _, geojson_path, _ = sample_las_and_gcps
    points = load_gcp_dataset(geojson_path)
    assert len(points) == 5
    assert points[0][0] == "GCP_01"
    assert points[3][4] == PointType.CHECK


def test_validate_las_point_cloud_accuracy(sample_las_and_gcps):
    las_path, csv_path, _, _ = sample_las_and_gcps
    report = validate_gcp_accuracy(
        dataset_path=las_path,
        gcp_data=csv_path,
        search_radius=5.0,
        target_tolerance_m=0.05,
    )

    assert isinstance(report, GCPValidationReport)
    assert report.total_points == 5
    assert report.num_gcps == 4
    assert report.num_checkpoints == 1
    assert len(report.suspect_outliers) == 1
    assert report.suspect_outliers[0].point_id == "GCP_OUTLIER"
    assert not report.passed_tolerance  # Outlier caused failure


def test_validate_dem_accuracy(sample_dem):
    dem_path = sample_dem
    gcps = [
        {"id": "GCP_1", "x": 500010.0, "y": 5200090.0, "z": 100.0, "type": "GCP"},
        {"id": "GCP_2", "x": 500020.0, "y": 5200080.0, "z": 100.02, "type": "GCP"},
        {"id": "CHK_1", "x": 500030.0, "y": 5200070.0, "z": 99.98, "type": "CHECK"},
    ]

    report = validate_gcp_accuracy(
        dataset_path=dem_path,
        gcp_data=gcps,
        target_tolerance_m=0.05,
    )

    assert report.dataset_type == "elevation_model"
    assert report.total_points == 3
    assert report.rmse_z < 0.03
    assert report.passed_tolerance


def test_autoqc_inspection_with_gcps(sample_las_and_gcps, tmp_path):
    las_path, csv_path, _, _ = sample_las_and_gcps

    # AutoQC inspection with GCPs
    qc_report = dg.autoqc.inspect_point_cloud(
        las_path=las_path,
        gcp_data=csv_path,
        target_tolerance_m=0.05,
    )

    assert "gcp_accuracy" in qc_report.summary_metrics
    assert any("GCP" in issue.code for issue in qc_report.issues)

    # Test remediation with datum shift
    remediated_las = tmp_path / "remediated.las"
    out_path = dg.autoqc.remediate_point_cloud(
        las_path=las_path,
        output_las=remediated_las,
        report=qc_report,
        z_shift=0.10,
    )
    assert Path(out_path).exists()
