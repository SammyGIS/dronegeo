"""
dronegeo.utils.file_utils
~~~~~~~~~~~~~~~~~~~~~~~~~
File validation, output directory management, and byte size formatting utilities.
"""

from __future__ import annotations
from pathlib import Path
from typing import Union, Optional

import laspy
import rasterio

from ..core.exceptions import InvalidPointCloudFormatError, RasterIOError


def verify_las_file(las_path: Union[str, Path]) -> bool:
    """
    Validates that a file exists, is readable, and contains a valid ASPRS LAS/LAZ point cloud header.

    Real-World Applications:
        - Input Validation: Pre-flight checks before launching long computational pipelines.

    Args:
        las_path: Path to check.

    Returns:
        True if valid.

    Raises:
        FileNotFoundError: If the file does not exist on disk.
        InvalidPointCloudFormatError: If the file is not a valid LAS/LAZ point cloud.

    Example:
        >>> from dronegeo.utils import verify_las_file
        >>> is_valid = verify_las_file("data/survey.laz")
    """
    p = Path(las_path)
    if not p.exists():
        raise FileNotFoundError(f"LAS file does not exist: {p}")
    if p.stat().st_size == 0:
        raise InvalidPointCloudFormatError(f"LAS file is empty (0 bytes): {p}")

    try:
        with laspy.open(str(p)) as reader:
            _ = reader.header.point_count
        return True
    except Exception as e:
        raise InvalidPointCloudFormatError(f"Failed to open LAS file header: {p}", details=str(e))


def verify_raster_file(raster_path: Union[str, Path]) -> bool:
    """
    Validates that a raster file exists, is readable, and is a valid GeoTIFF format.

    Args:
        raster_path: Path to GeoTIFF file.

    Returns:
        True if valid.

    Raises:
        FileNotFoundError: If raster does not exist.
        RasterIOError: If raster cannot be opened.

    Example:
        >>> from dronegeo.utils import verify_raster_file
        >>> is_valid = verify_raster_file("outputs/dtm.tif")
    """
    p = Path(raster_path)
    if not p.exists():
        raise FileNotFoundError(f"Raster file does not exist: {p}")

    try:
        with rasterio.open(str(p)) as src:
            _ = src.shape
        return True
    except Exception as e:
        raise RasterIOError(f"Failed to open raster file: {p}", details=str(e))


def format_file_size(num_bytes: int) -> str:
    """
    Formats an integer byte count into a human-readable string (KB, MB, GB).

    Example:
        >>> from dronegeo.utils import format_file_size
        >>> print(format_file_size(524288000))
        '500.00 MB'
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if abs(num_bytes) < 1024.0:
            return f"{num_bytes:3.2f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.2f} PB"


def ensure_output_directory(file_path: Union[str, Path]) -> Path:
    """
    Ensures that the parent directory for a destination file path exists on disk.

    Args:
        file_path: Target destination file path.

    Returns:
        Path object of the file.

    Example:
        >>> from dronegeo.utils import ensure_output_directory
        >>> path = ensure_output_directory("outputs/nested/subfolder/file.tif")
    """
    p = Path(file_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p
