"""
dronegeo.imagery.vegetation_indices
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Photogrammetric and visible spectral vegetation indices (VARI, GLI, TGI, ExG, NGRDI) from RGB orthomosaics.
"""

from __future__ import annotations
from pathlib import Path
from typing import Union, Optional, Literal

import numpy as np
import rasterio

from ..core.exceptions import RasterIOError


def compute_visible_vegetation_index(
    ortho_path: Union[str, Path],
    output_tif: Union[str, Path],
    index: Literal["VARI", "GLI", "TGI", "EXG", "NGRDI"] = "VARI",
) -> str:
    """
    Computes a photogrammetric visible vegetation index map from an RGB orthomosaic GeoTIFF.

    Real-World Applications:
        - Precision Agriculture: Detecting crop nitrogen stress, crop vigor, and irrigation anomalies
          using standard consumer drone RGB cameras (e.g. DJI Mavic 3 Enterprise, Phantom 4 Pro)
          without requiring expensive multispectral NIR cameras.
        - Forestry & Canopy Monitoring: Identifying tree crown dieback, invasive weed patches,
          and vegetation regrowth stages.
        - Environmental GIS: Assessing riparian green buffer zones and urban green space coverage.

    When to Use:
        - Use VARI: Best overall general crop health index that resists atmospheric haze and lighting shifts.
        - Use GLI: Best for detecting chlorophyll concentration in dense green canopies.
        - Use ExG: Best for binary plant vs. soil segmentation (e.g. counting seedling emergence).

    Supported Indices:
        - "VARI" (Visible Atmospherically Resistant Index): (G - R) / (G + R - B)
        - "GLI" (Green Leaf Index): (2G - R - B) / (2G + R + B)
        - "TGI" (Triangular Greenness Index): G - 0.39*R - 0.61*B
        - "EXG" (Excess Green Index): 2G - R - B
        - "NGRDI" (Normalized Green-Red Difference Index): (G - R) / (G + R)

    Args:
        ortho_path: Path to input 3-band (RGB) or 4-band (RGBA) Orthomosaic GeoTIFF.
        output_tif: Target float32 GeoTIFF destination path.
        index: Index formula name (one of 'VARI', 'GLI', 'TGI', 'EXG', 'NGRDI').

    Returns:
        Absolute string path to the created index GeoTIFF.

    Raises:
        FileNotFoundError: If input orthomosaic file does not exist on disk.
        ValueError: If input orthomosaic has fewer than 3 bands.

    Example:
        >>> import dronegeo as dg
        >>> vari_path = dg.imagery.compute_visible_vegetation_index(
        ...     ortho_path="survey_ortho.tif",
        ...     output_tif="survey_vari.tif",
        ...     index="VARI"
        ... )
        >>> print(f"VARI vegetation map created: {vari_path}")
    """
    idx_upper = str(index).upper()
    valid_indices = ("VARI", "GLI", "TGI", "EXG", "NGRDI")
    if idx_upper not in valid_indices:
        raise ValueError(f"Unknown index '{index}'. Choose from {valid_indices}.")

    p_in = Path(ortho_path)
    p_out = Path(output_tif)

    assert p_in.exists(), f"Input orthomosaic not found: {p_in}"
    p_out.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.open(str(p_in)) as src:
        if src.count < 3:
            raise ValueError(f"Input orthomosaic has {src.count} bands. At least 3 bands (RGB) required.")

        r = src.read(1).astype(np.float32)
        g = src.read(2).astype(np.float32)
        b = src.read(3).astype(np.float32)
        meta = src.meta.copy()

    valid = (r > 0) | (g > 0) | (b > 0)
    index_grid = np.full_like(r, -10000.0, dtype=np.float32)

    max_val = max(float(np.nanmax(r)), float(np.nanmax(g)), float(np.nanmax(b)))
    if max_val > 1.0:
        r_n = r / 255.0
        g_n = g / 255.0
        b_n = b / 255.0
    else:
        r_n, g_n, b_n = r, g, b

    if idx_upper == "VARI":
        denom = g_n + r_n - b_n
        denom = np.where(np.abs(denom) < 1e-4, 1e-4, denom)
        res = (g_n - r_n) / denom
        index_grid[valid] = np.clip(res[valid], -1.0, 1.0)

    elif idx_upper == "GLI":
        denom = 2.0 * g_n + r_n + b_n
        denom = np.where(np.abs(denom) < 1e-4, 1e-4, denom)
        res = (2.0 * g_n - r_n - b_n) / denom
        index_grid[valid] = np.clip(res[valid], -1.0, 1.0)

    elif idx_upper == "TGI":
        res = g_n - (0.39 * r_n) - (0.61 * b_n)
        index_grid[valid] = res[valid]

    elif idx_upper == "EXG":
        total = r_n + g_n + b_n
        total = np.where(total < 1e-4, 1e-4, total)
        r_chrom = r_n / total
        g_chrom = g_n / total
        b_chrom = b_n / total
        res = 2.0 * g_chrom - r_chrom - b_chrom
        index_grid[valid] = res[valid]

    elif idx_upper == "NGRDI":
        denom = g_n + r_n
        denom = np.where(np.abs(denom) < 1e-4, 1e-4, denom)
        res = (g_n - r_n) / denom
        index_grid[valid] = np.clip(res[valid], -1.0, 1.0)

    del r, g, b, r_n, g_n, b_n

    meta.update({
        'count': 1,
        'dtype': 'float32',
        'nodata': -10000.0,
        'compress': 'lzw',
    })

    with rasterio.open(str(p_out), "w", **meta) as dst:
        dst.write(index_grid, 1)

    del index_grid
    assert p_out.exists() and p_out.stat().st_size > 0, f"Failed to write vegetation index: {p_out}"
    return str(p_out)


def compute_vari(ortho_path: Union[str, Path], output_tif: Union[str, Path]) -> str:
    """Convenience wrapper for Visible Atmospherically Resistant Index (VARI)."""
    return compute_visible_vegetation_index(ortho_path, output_tif, index="VARI")


def compute_gli(ortho_path: Union[str, Path], output_tif: Union[str, Path]) -> str:
    """Convenience wrapper for Green Leaf Index (GLI)."""
    return compute_visible_vegetation_index(ortho_path, output_tif, index="GLI")


def compute_tgi(ortho_path: Union[str, Path], output_tif: Union[str, Path]) -> str:
    """Convenience wrapper for Triangular Greenness Index (TGI)."""
    return compute_visible_vegetation_index(ortho_path, output_tif, index="TGI")


def compute_exg(ortho_path: Union[str, Path], output_tif: Union[str, Path]) -> str:
    """Convenience wrapper for Excess Green Index (ExG)."""
    return compute_visible_vegetation_index(ortho_path, output_tif, index="EXG")


def compute_ngrdi(ortho_path: Union[str, Path], output_tif: Union[str, Path]) -> str:
    """Convenience wrapper for Normalized Green-Red Difference Index (NGRDI)."""
    return compute_visible_vegetation_index(ortho_path, output_tif, index="NGRDI")
