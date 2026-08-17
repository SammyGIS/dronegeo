"""
tests.test_analysis
~~~~~~~~~~~~~~~~~~~
Unit tests for morphology (Hillshade, Slope, Aspect, TRI), 3D Cut/Fill Volumetrics, and Contour generation.
"""

import os
import pytest
import rasterio
from dronegeo.analysis.morphology import (
    generate_hillshade,
    generate_slope_map,
    generate_aspect_map,
    generate_terrain_ruggedness_index,
)
from dronegeo.analysis.volumetrics import (
    compute_cut_fill_volume,
    compute_stockpile_volume,
    VolumetricReport,
)
from dronegeo.analysis.contours import generate_contour_lines


def test_morphology_surface_derivatives(synthetic_dem_tif, temp_workspace):
    """Verify Hillshade, Slope, Aspect, and TRI raster generation."""
    hs_path = temp_workspace / "hillshade.tif"
    slope_path = temp_workspace / "slope.tif"
    aspect_path = temp_workspace / "aspect.tif"
    tri_path = temp_workspace / "tri.tif"

    assert os.path.exists(generate_hillshade(synthetic_dem_tif, str(hs_path)))
    assert os.path.exists(generate_slope_map(synthetic_dem_tif, str(slope_path)))
    assert os.path.exists(generate_aspect_map(synthetic_dem_tif, str(aspect_path)))
    assert os.path.exists(generate_terrain_ruggedness_index(synthetic_dem_tif, str(tri_path)))

    with rasterio.open(str(hs_path)) as src:
        assert src.dtypes[0] == "uint8"


def test_cut_fill_volumetrics(synthetic_dem_tif, temp_workspace):
    """Verify 3D Cut & Fill volume computation between epochs."""
    out_diff = temp_workspace / "diff.tif"
    # Compare synthetic_dem_tif with itself -> Net volume should be ~0.0
    report = compute_cut_fill_volume(
        before_dem=synthetic_dem_tif,
        after_dem=synthetic_dem_tif,
        output_diff_tif=str(out_diff),
    )
    assert isinstance(report, VolumetricReport)
    assert abs(report.cut_volume_m3) < 1e-4
    assert abs(report.fill_volume_m3) < 1e-4
    assert abs(report.net_volume_m3) < 1e-4
    assert os.path.exists(str(out_diff))


def test_stockpile_volumetrics(synthetic_dem_tif):
    """Verify stockpile volume computation above reference plane."""
    # Synthetic DEM is between 200m and ~210m. Reference datum at 190m.
    report = compute_stockpile_volume(synthetic_dem_tif, base_elevation=190.0)
    assert isinstance(report, VolumetricReport)
    assert report.cut_volume_m3 > 0.0
    assert report.surface_area_m2 > 0.0


def test_generate_contour_lines(synthetic_dem_tif, temp_workspace):
    """Verify vector contour lines extraction."""
    out_geojson = temp_workspace / "contours.geojson"
    gdf = generate_contour_lines(
        dem_path=synthetic_dem_tif,
        output_vector_path=str(out_geojson),
        interval_m=2.0,
    )
    assert len(gdf) > 0
    assert "elevation" in gdf.columns
    assert os.path.exists(str(out_geojson))
