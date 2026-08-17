"""
tests.test_lidar
~~~~~~~~~~~~~~~~
Unit tests for point cloud profiling, strip merging, and terrain rectification.
"""

import os
import pytest
from dronegeo.lidar.point_metrics import (
    profile_point_cloud,
    PointCloudProfileReport,
    compute_point_density,
    plot_point_cloud_profile,
)
from dronegeo.lidar.strip_alignment import align_and_merge_strips
from dronegeo.lidar.terrain_rectification import (
    compute_rectification_surface,
    rectify_point_cloud_elevation,
)
from dronegeo.dem.surface_models import create_dtm


def test_profile_point_cloud(synthetic_las_file):
    """Verify point cloud profiling metrics."""
    report = profile_point_cloud(synthetic_las_file)
    assert isinstance(report, PointCloudProfileReport)
    assert report.total_points == 5000
    assert report.mean_point_density > 0.0
    assert report.has_rgb is True
    assert 2 in report.classification_counts
    z_min, z_max = report.spatial_bounds_xyz["Z"]
    assert z_min < z_max


def test_compute_point_density(synthetic_las_file):
    """Verify point cloud density grid calculation."""
    density_grid, bounds = compute_point_density(synthetic_las_file, grid_resolution=1.0)
    assert density_grid.shape[0] > 0
    assert density_grid.shape[1] > 0
    assert len(bounds) == 4
    assert bounds[0] < bounds[1]


def test_plot_point_cloud_profile(synthetic_las_file, temp_workspace):
    """Verify pre-flight QC dashboard PNG generation."""
    report = profile_point_cloud(synthetic_las_file)
    out_png = temp_workspace / "qc_profile.png"
    result = plot_point_cloud_profile(report, output_png=str(out_png))
    assert os.path.exists(result)
    assert os.path.getsize(result) > 0


def test_align_and_merge_strips(synthetic_overlapping_strips, temp_workspace):
    """Verify merging multiple flight strips with shift offsets."""
    strip1, strip2 = synthetic_overlapping_strips
    out_merged = temp_workspace / "merged_strips.las"

    merged_path = align_and_merge_strips(
        las_files=[strip1, strip2],
        output_las=str(out_merged),
        z_shifts=[0.0, -0.15],
    )
    assert os.path.exists(merged_path)

    report = profile_point_cloud(merged_path)
    assert report.total_points == 6000  # 3000 + 3000


def test_rectify_point_cloud_elevation(synthetic_las_file, temp_workspace):
    """Verify point cloud elevation rectification."""
    dtm_tif = temp_workspace / "rect_dtm.tif"
    create_dtm(synthetic_las_file, str(dtm_tif), resolution=1.0)

    surface = compute_rectification_surface(str(dtm_tif))
    out_rect = temp_workspace / "rectified.las"

    result = rectify_point_cloud_elevation(
        las_in=synthetic_las_file,
        las_out=str(out_rect),
        rectification_surface=surface,
    )
    assert os.path.exists(result)
