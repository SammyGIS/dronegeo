"""
dronegeo.dem.boundary_extraction
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Concave hull flight footprint boundary extraction to eliminate outer extrapolation flares.
"""

from __future__ import annotations
from pathlib import Path
from typing import Union, Tuple, Optional

import numpy as np
import scipy.ndimage as ndi
import laspy

from ..config.compute import ComputeConfig, get_compute_config, collect_garbage_if_needed
from ..core.exceptions import PointCloudError, EmptyPointCloudError


def extract_flight_footprint_mask(
    las_path: Union[str, Path],
    pixel_res: float = 0.118,
    buffer_distance: float = 3.0,
    downsample_factor: int = 2,
    config: Optional[ComputeConfig] = None,
) -> Tuple[np.ndarray, Tuple[int, int], Tuple[float, float, float, float]]:
    """
    Extracts a crisp binary boolean concave hull footprint mask matching the exact flight path.

    Real-World Applications:
        - Aerial Survey QC: Trimming artificial interpolation "skirts" and cliff edges at the
          boundary of the drone flight area.
        - Orthomosaic Boundaries: Creating clean, non-rectangular survey area boundaries.

    When to Use:
        Always called automatically during DTM/DSM/Orthomosaic generation to prevent spatial
        extrapolation beyond areas where true drone points exist.

    Args:
        las_path: Path to input LAS/LAZ point cloud file.
        pixel_res: Resolution of the target raster grid in meters (default: 0.118m).
        buffer_distance: Outer buffer padding distance in meters around valid returns (default: 3.0m).
        downsample_factor: Downsample factor for rapid morphological dilation (default: 2).
        config: Optional ComputeConfig instance.

    Returns:
        Tuple of (footprint_mask_2d, (height, width), (min_x, max_x, min_y, max_y)).

    Raises:
        FileNotFoundError: If input LAS file does not exist.
        EmptyPointCloudError: If point cloud has 0 points.

    Example:
        >>> import dronegeo as dg
        >>> mask, (h, w), bounds = dg.dem.extract_flight_footprint_mask(
        ...     las_path="survey.laz",
        ...     pixel_res=0.10,
        ...     buffer_distance=3.0
        ... )
        >>> print(f"Footprint valid pixels: {np.sum(mask):,} out of {h*w:,}")
    """
    cfg = config or get_compute_config()
    p = Path(las_path)
    assert p.exists(), f"LAS file not found: {p}"
    assert pixel_res > 0, f"pixel_res must be positive, got {pixel_res}"
    assert buffer_distance >= 0, f"buffer_distance must be >= 0, got {buffer_distance}"

    with laspy.open(str(p)) as reader:
        h = reader.header
        if h.point_count == 0:
            raise EmptyPointCloudError(f"Point cloud is empty: {p}")
        min_x, max_x = float(h.mins[0]), float(h.maxs[0])
        min_y, max_y = float(h.mins[1]), float(h.maxs[1])

    width = max(1, int(np.ceil((max_x - min_x) / pixel_res)))
    height = max(1, int(np.ceil((max_y - min_y) / pixel_res)))

    ds = max(1, int(downsample_factor))
    h_ds = height // ds + 1
    w_ds = width // ds + 1

    point_present_ds = np.zeros((h_ds, w_ds), dtype=bool)

    with laspy.open(str(p)) as reader:
        for chunk in reader.chunk_iterator(cfg.chunk_size):
            cx = np.array(chunk.x, dtype=np.float64)
            cy = np.array(chunk.y, dtype=np.float64)

            cols = np.clip(((cx - min_x) / pixel_res).astype(int), 0, width - 1)
            rows = np.clip(((max_y - cy) / pixel_res).astype(int), 0, height - 1)

            point_present_ds[rows // ds, cols // ds] = True

    buf_iter = max(1, int(np.ceil(buffer_distance / (pixel_res * ds))))
    struct = ndi.generate_binary_structure(2, 2)
    fp_ds = ndi.binary_dilation(point_present_ds, structure=struct, iterations=buf_iter)
    fp_ds = ndi.binary_fill_holes(fp_ds)
    del point_present_ds

    r_idx = np.clip(np.arange(height) // ds, 0, fp_ds.shape[0] - 1)
    c_idx = np.clip(np.arange(width) // ds, 0, fp_ds.shape[1] - 1)
    footprint_mask = fp_ds[r_idx[:, None], c_idx[None, :]]
    del fp_ds
    collect_garbage_if_needed(cfg)

    return footprint_mask, (height, width), (min_x, max_x, min_y, max_y)
