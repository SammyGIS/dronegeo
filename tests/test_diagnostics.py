"""
tests.test_diagnostics
~~~~~~~~~~~~~~~~~~~~~~
Unit tests for flight strip vertical alignment (ΔZ) and DEM terrain anomaly detection.
"""

import pytest
import numpy as np
from dronegeo.diagnostics.strip_alignment import check_strip_alignment, StripAlignmentReport
from dronegeo.diagnostics.terrain_anomaly import detect_terrain_anomalies, TerrainAnomalyReport


def test_check_strip_alignment_with_shift(synthetic_overlapping_strips):
    """Verify strip alignment accurately recovers the calibrated vertical shift (~ -0.15m or +0.15m)."""
    strip1, strip2 = synthetic_overlapping_strips
    report = check_strip_alignment(strip1, strip2, sample_resolution=1.0)

    assert isinstance(report, StripAlignmentReport)
    assert report.has_overlap is True
    assert report.sampled_cells_count > 0
    # Difference should be close to -0.15m (ref - target = z1 - (z1 + 0.15))
    assert abs(report.median_offset - (-0.15)) < 0.08
    assert report.std_dev < 0.10

    report_dict = report.to_dict()
    assert "median_offset_m" in report_dict or "median_offset" in report_dict


def test_detect_terrain_anomalies_clean_dem(synthetic_dem_tif):
    """Verify clean synthetic DEM produces zero or minimal anomaly alerts."""
    report = detect_terrain_anomalies(synthetic_dem_tif, spike_threshold=300.0, slope_gradient_threshold_deg=60.0)
    assert isinstance(report, TerrainAnomalyReport)
    assert report.spike_count == 0
    assert report.anomaly_pixel_count >= 0
    assert report.z_min_valid > 150.0
    assert report.z_max_valid < 300.0
