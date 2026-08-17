"""
dronegeo.utils.geo_utils
~~~~~~~~~~~~~~~~~~~~~~~~
Spatial bounding box arithmetic, coordinate formatting, raster summary inspectors, and 2D array downsamplers.
"""

from __future__ import annotations
from pathlib import Path
from typing import Union, Tuple, Optional, Dict, Any

import numpy as np
import rasterio

from ..core.exceptions import RasterIOError


def calculate_bounding_box_intersection(
    bbox1: Tuple[float, float, float, float],
    bbox2: Tuple[float, float, float, float],
) -> Optional[Tuple[float, float, float, float]]:
    """
    Computes the spatial intersection rectangle of two bounding boxes (left, right, bottom, top).

    Real-World Applications:
        - Overlap Validation: Checking if two separate drone flight lines overlap geographically
          before running alignment or merging.

    When to Use:
        Use when finding the common bounding box between two survey flight passes or raster datasets.

    Args:
        bbox1: (left, right, bottom, top) of the first extent.
        bbox2: (left, right, bottom, top) of the second extent.

    Returns:
        Tuple of (left, right, bottom, top) representing the intersection, or None if no overlap.

    Example:
        >>> from dronegeo.utils import calculate_bounding_box_intersection
        >>> overlap = calculate_bounding_box_intersection(
        ...     (500.0, 1000.0, 100.0, 600.0),
        ...     (800.0, 1200.0, 400.0, 800.0)
        ... )
        >>> print(f"Intersection box: {overlap}")
    """
    left = max(bbox1[0], bbox2[0])
    right = min(bbox1[1], bbox2[1])
    bottom = max(bbox1[2], bbox2[2])
    top = min(bbox1[3], bbox2[3])

    if left >= right or bottom >= top:
        return None

    return (left, right, bottom, top)


def format_spatial_extent(
    left: float, right: float, bottom: float, top: float, unit: str = "m"
) -> str:
    """
    Formats bounding box coordinates into a clean human-readable string.

    Real-World Applications:
        - Survey Reporting: Generating formatted spatial extent strings for survey QC logs.

    Args:
        left: Minimum X coordinate (Easting).
        right: Maximum X coordinate (Easting).
        bottom: Minimum Y coordinate (Northing).
        top: Maximum Y coordinate (Northing).
        unit: Measurement unit symbol (default: 'm').

    Returns:
        Formatted spatial extent string.

    Example:
        >>> from dronegeo.utils import format_spatial_extent
        >>> text = format_spatial_extent(345200.5, 346100.8, 4820100.2, 4821000.9)
        >>> print(text)
    """
    width = right - left
    height = top - bottom
    area_ha = (width * height) / 10000.0
    return (
        f"X: [{left:,.2f}{unit}, {right:,.2f}{unit}] (Width: {width:,.2f}{unit}) | "
        f"Y: [{bottom:,.2f}{unit}, {top:,.2f}{unit}] (Height: {height:,.2f}{unit}) | "
        f"Area: {area_ha:,.2f} ha"
    )


def get_raster_metadata_summary(raster_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Reads and formats comprehensive metadata from a GeoTIFF raster into an inspection dictionary.

    Real-World Applications:
        - Data Ingestion QC: Verifying resolution, band counts, CRS, and valid elevation ranges.

    Args:
        raster_path: Path to input GeoTIFF file.

    Returns:
        Dictionary containing spatial bounds, resolution, width, height, CRS, dtype, and elevation stats.

    Raises:
        FileNotFoundError: If the raster file does not exist on disk.
        RasterIOError: If reading the raster file fails.

    Example:
        >>> from dronegeo.utils import get_raster_metadata_summary
        >>> summary = get_raster_metadata_summary("dtm.tif")
        >>> print(f"GSD: {summary['resolution_x_m']}m, CRS: {summary['crs']}")
    """
    p = Path(raster_path)
    assert p.exists(), f"Raster file not found: {p}"

    try:
        with rasterio.open(str(p)) as src:
            b = src.bounds
            data = src.read(1)
            nodata = float(src.nodata) if src.nodata is not None else -10000.0
            valid = (data != nodata) & (~np.isnan(data)) & (data > -500.0)

            z_min = float(np.min(data[valid])) if np.any(valid) else None
            z_max = float(np.max(data[valid])) if np.any(valid) else None
            z_mean = float(np.mean(data[valid])) if np.any(valid) else None

            return {
                "file_name": p.name,
                "file_size_mb": round(p.stat().st_size / (1024 * 1024), 2),
                "width_px": int(src.width),
                "height_px": int(src.height),
                "band_count": int(src.count),
                "resolution_x_m": round(float(src.res[0]), 4),
                "resolution_y_m": round(float(src.res[1]), 4),
                "crs": src.crs.to_string() if src.crs else "Undefined",
                "nodata_value": nodata,
                "z_min_m": round(z_min, 3) if z_min is not None else None,
                "z_max_m": round(z_max, 3) if z_max is not None else None,
                "z_mean_m": round(z_mean, 3) if z_mean is not None else None,
                "bounds_extent": (float(b.left), float(b.right), float(b.bottom), float(b.top)),
            }
    except Exception as e:
        raise RasterIOError(f"Failed to inspect raster: {p}", details=str(e))


def downsample_array_2d(array: np.ndarray, factor: int = 4) -> np.ndarray:
    """
    Downsamples a 2D NumPy array by an integer step factor.

    Real-World Applications:
        - Fast Rendering: Decimating massive 20,000x20,000 raster arrays for quick preview plotting.

    Args:
        array: Input 2D NumPy array.
        factor: Decimation step factor (default: 4).

    Returns:
        Downsampled 2D NumPy array.

    Example:
        >>> from dronegeo.utils import downsample_array_2d
        >>> small_arr = downsample_array_2d(large_grid, factor=5)
    """
    assert factor >= 1, f"factor must be >= 1, got {factor}"
    ds = int(factor)
    return array[::ds, ::ds].copy()
