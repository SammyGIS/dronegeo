"""
tests.test_profiling
~~~~~~~~~~~~~~~~~~~~
Unit tests for elevation transects, diagnostic QC plots, and grid chip tiling.
"""

import os
import pytest
import geopandas as gpd
from shapely.geometry import box
from dronegeo.profiling.elevation_transects import extract_orthogonal_transects, plot_elevation_transects
from dronegeo.profiling.diagnostic_plots import plot_strip_overlap_residuals, plot_anomaly_heatmap
from dronegeo.profiling.grid_tiling import map_grid_chips
from dronegeo.diagnostics.strip_alignment import check_strip_alignment
from dronegeo.diagnostics.terrain_anomaly import detect_terrain_anomalies


def test_elevation_transects(synthetic_dem_tif, temp_workspace):
    """Verify transect extraction and plotting."""
    data = extract_orthogonal_transects(synthetic_dem_tif, count=3)
    assert len(data) == 3

    out_png = temp_workspace / "transects.png"
    res_png = plot_elevation_transects(synthetic_dem_tif, output_png=str(out_png), count=3)
    assert os.path.exists(res_png)
    assert os.path.getsize(res_png) > 0


def test_plot_strip_overlap_residuals(synthetic_overlapping_strips, temp_workspace):
    """Verify residual distribution plot for overlapping strips."""
    strip1, strip2 = synthetic_overlapping_strips
    report = check_strip_alignment(strip1, strip2, sample_resolution=1.0)

    out_png = temp_workspace / "residuals.png"
    res = plot_strip_overlap_residuals(report, str(out_png))
    assert os.path.exists(res)


def test_plot_anomaly_heatmap(synthetic_dem_tif, temp_workspace):
    """Verify anomaly heatmap generation."""
    report = detect_terrain_anomalies(synthetic_dem_tif)
    out_png = temp_workspace / "anomalies.png"
    res = plot_anomaly_heatmap(synthetic_dem_tif, report, str(out_png))
    assert os.path.exists(res)


def test_map_grid_chips(synthetic_dem_tif, temp_workspace, sample_crs_epsg):
    """Verify survey grid chip map generation with vector grid polygons."""
    # Create simple 2x2 grid GeoJSON
    poly1 = box(500000.0, 5200000.0, 500050.0, 5200050.0)
    poly2 = box(500050.0, 5200000.0, 500100.0, 5200050.0)
    poly3 = box(500000.0, 5200050.0, 500050.0, 5200100.0)
    poly4 = box(500050.0, 5200050.0, 500100.0, 5200100.0)

    gdf = gpd.GeoDataFrame({
        "id": ["CHIP_01", "CHIP_02", "CHIP_03", "CHIP_04"],
        "geometry": [poly1, poly2, poly3, poly4]
    }, crs=f"EPSG:{sample_crs_epsg}")

    grid_file = temp_workspace / "survey_grid.geojson"
    gdf.to_file(str(grid_file), driver="GeoJSON")

    out_png = temp_workspace / "grid_chips.png"
    res = map_grid_chips(synthetic_dem_tif, str(grid_file), str(out_png), label_column="id")
    assert os.path.exists(res)
