"""
dronegeo.lidar.strip_alignment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Multi-strip flightline co-registration, datum offset adjustments, and master LAS/LAZ merging.
"""

from __future__ import annotations
import time
from pathlib import Path
from typing import Union, List, Optional, Callable

import numpy as np
import laspy

from ..config.compute import ComputeConfig, get_compute_config, collect_garbage_if_needed
from ..core.exceptions import PointCloudError, EmptyPointCloudError


def align_and_merge_strips(
    las_files: List[Union[str, Path]],
    output_las: Union[str, Path],
    z_shifts: Optional[List[float]] = None,
    progress_callback: Optional[Callable[[int, int, float], None]] = None,
    config: Optional[ComputeConfig] = None,
) -> str:
    """
    Applies vertical datum adjustment offsets to multiple flight strips and merges them
    into a single unified master LAS/LAZ point cloud using chunked memory streaming.

    Args:
        las_files: List of input LAS/LAZ file paths to merge.
        output_las: Target output path for the unified master LAS/LAZ.
        z_shifts: Optional list of float vertical offsets in meters corresponding to each input file.
                  If None, 0.0 shift is applied across all files.
        progress_callback: Optional callback fn(written_pts, total_pts, pct).
        config: Optional ComputeConfig instance.

    Returns:
        Absolute string path to the created master LAS/LAZ file.

    Raises:
        ValueError: If `las_files` is empty or `z_shifts` length does not match `las_files`.
        FileNotFoundError: If any input file does not exist on disk.
        EmptyPointCloudError: If total point count across all files is 0.

    Example:
        >>> import dronegeo as dg
        >>> master_laz = dg.lidar.align_and_merge_strips(
        ...     las_files=["flight_pass1.laz", "flight_pass2.laz"],
        ...     output_las="outputs/master_cloud.laz",
        ...     z_shifts=[0.0, +3.095]
        ... )
        >>> print(f"Unified cloud saved to: {master_laz}")
    """
    cfg = config or get_compute_config()

    if not las_files or len(las_files) == 0:
        raise ValueError("las_files list must contain at least one point cloud path.")

    file_paths = [Path(f) for f in las_files]

    for p in file_paths:
        if not p.exists():
            raise FileNotFoundError(f"Input LAS file not found: {p}")

    out_path = Path(output_las)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if z_shifts is None:
        shifts = [0.0] * len(file_paths)
    else:
        if len(z_shifts) != len(file_paths):
            raise ValueError(f"Length of z_shifts ({len(z_shifts)}) must match las_files ({len(file_paths)}).")
        shifts = list(z_shifts)

    # 1. Inspect all headers to determine unified bounding extents and total point counts
    min_x = float("inf")
    max_x = float("-inf")
    min_y = float("inf")
    max_y = float("-inf")
    min_z = float("inf")
    max_z = float("-inf")
    total_pts = 0

    first_header = None
    for p, dz in zip(file_paths, shifts):
        with laspy.open(str(p)) as reader:
            h = reader.header
            if first_header is None:
                first_header = h
            min_x = min(min_x, float(h.mins[0]))
            max_x = max(max_x, float(h.maxs[0]))
            min_y = min(min_y, float(h.mins[1]))
            max_y = max(max_y, float(h.maxs[1]))
            min_z = min(min_z, float(h.mins[2]) + dz)
            max_z = max(max_z, float(h.maxs[2]) + dz)
            total_pts += int(h.point_count)

    if total_pts == 0:
        raise EmptyPointCloudError("Total point count across all input LAS files is 0.")

    # Create Master Output Header
    out_header = laspy.LasHeader(
        point_format=first_header.point_format.id,
        version=first_header.version
    )
    out_header.offsets = [min_x, min_y, 0.0]
    out_header.scales = [0.001, 0.001, 0.001]
    out_header.mins = [min_x, min_y, min_z]
    out_header.maxs = [max_x, max_y, max_z]

    written_count = 0

    # 2. Stream and write each strip sequentially
    with laspy.open(str(out_path), mode="w", header=out_header) as writer:
        for idx, (p, dz) in enumerate(zip(file_paths, shifts)):
            with laspy.open(str(p)) as reader:
                for chunk in reader.chunk_iterator(cfg.chunk_size):
                    if abs(dz) > 1e-5:
                        chunk.z = np.array(chunk.z, dtype=np.float64) + dz
                    writer.write_points(chunk)
                    written_count += len(chunk)

                    pct = (written_count / total_pts) * 100.0 if total_pts > 0 else 100.0
                    if progress_callback is not None:
                        progress_callback(written_count, total_pts, pct)

    collect_garbage_if_needed(cfg)
    assert out_path.exists() and out_path.stat().st_size > 0, f"Failed to write merged master LAS: {out_path}"
    return str(out_path)
