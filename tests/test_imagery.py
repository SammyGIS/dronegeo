"""
tests.test_imagery
~~~~~~~~~~~~~~~~~~
Unit tests for True-Color Orthomosaics and visible vegetation indices (VARI, GLI, TGI, ExG, NGRDI).
"""

import os
import pytest
import numpy as np
import rasterio
from dronegeo.imagery.orthomosaic import (
    create_true_color_orthomosaic,
    enhance_orthomosaic_contrast,
)
from dronegeo.imagery.vegetation_indices import (
    compute_vari,
    compute_gli,
    compute_tgi,
    compute_exg,
    compute_ngrdi,
    compute_visible_vegetation_index,
)


def test_create_true_color_orthomosaic(synthetic_las_file, temp_workspace):
    """Verify true color orthomosaic generation from point cloud RGB."""
    out_ortho = temp_workspace / "ortho_test.tif"
    ortho_path = create_true_color_orthomosaic(
        las_path=synthetic_las_file,
        output_tif=str(out_ortho),
        resolution=1.0,
        alpha_channel=True,
    )
    assert os.path.exists(ortho_path)
    with rasterio.open(ortho_path) as src:
        assert src.count == 4  # RGBA


def test_enhance_orthomosaic_contrast():
    """Verify contrast enhancement array stretching function."""
    arr = np.linspace(10, 200, 100).reshape((10, 10))
    enhanced = enhance_orthomosaic_contrast(arr, p_low=2.0, p_high=98.0)
    assert enhanced.shape == (10, 10)
    assert enhanced.min() >= 0.0
    assert enhanced.max() <= 255.0


def test_vegetation_indices(synthetic_ortho_tif, temp_workspace):
    """Verify calculation of VARI, GLI, TGI, ExG, and NGRDI vegetation indices."""
    indices = ["VARI", "GLI", "TGI", "ExG", "NGRDI"]
    funcs = [compute_vari, compute_gli, compute_tgi, compute_exg, compute_ngrdi]

    for name, func in zip(indices, funcs):
        out_tif = temp_workspace / f"index_{name}.tif"
        res_path = func(synthetic_ortho_tif, str(out_tif))
        assert os.path.exists(res_path)
        with rasterio.open(res_path) as src:
            assert src.count == 1
            data = src.read(1)
            valid = data[data != src.nodata]
            assert len(valid) > 0


def test_compute_visible_vegetation_index_generic(synthetic_ortho_tif, temp_workspace):
    """Verify generic index dispatcher."""
    out_tif = temp_workspace / "generic_vari.tif"
    res = compute_visible_vegetation_index(synthetic_ortho_tif, str(out_tif), index="VARI")
    assert os.path.exists(res)
