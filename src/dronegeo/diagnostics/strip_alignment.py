"""
dronegeo.diagnostics.strip_alignment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Spatial vertical offset detection (ΔZ) and overlap residual analysis between flightlines.
"""

from __future__ import annotations
from pathlib import Path
from dataclasses import dataclass
from typing import Union, Tuple, Optional, Dict, Any

import numpy as np
import laspy

from ..config.compute import ComputeConfig, get_compute_config, collect_garbage_if_needed
from ..core.base import BaseDiagnostic
from ..core.exceptions import PointCloudError, EmptyPointCloudError, NoSpatialOverlapError, InsufficientOverlapDataError


@dataclass
class StripAlignmentReport:
    """
    Summary report of the vertical datum discrepancy between two overlapping flight strips.

    Attributes:
        las_path1: Reference LAS/LAZ file path.
        las_path2: Target LAS/LAZ file path to be shifted.
        overlap_bounds: Tuple of (left, right, bottom, top) in spatial coordinates.
        has_overlap: True if valid spatial overlap exists between the two clouds.
        mean_offset: Mean vertical difference in overlap (reference - target) in meters.
        median_offset: Median vertical difference in overlap (recommended shift) in meters.
        std_dev: Standard deviation of vertical differences in meters.
        p5: 5th percentile of vertical differences in meters.
        p95: 95th percentile of vertical differences in meters.
        sampled_cells_count: Number of valid rasterized comparison cells in overlap.
        raw_residuals: 1D array of sampled elevation difference residuals.

    Example:
        >>> report = check_strip_alignment("strip1.laz", "strip2.laz")
        >>> print(f"Median offset: {report.median_offset:+.3f}m (Std: {report.std_dev:.3f}m)")
        >>> print(f"Sampled comparison cells: {report.sampled_cells_count:,}")
    """
    las_path1: str
    las_path2: str
    overlap_bounds: Tuple[float, float, float, float]
    has_overlap: bool
    mean_offset: float
    median_offset: float
    std_dev: float
    p5: float
    p95: float
    sampled_cells_count: int
    raw_residuals: Optional[np.ndarray] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serializes report metrics into a dictionary."""
        return {
            "las_path1": self.las_path1,
            "las_path2": self.las_path2,
            "overlap_bounds": self.overlap_bounds,
            "has_overlap": self.has_overlap,
            "mean_offset_m": round(self.mean_offset, 4),
            "median_offset_m": round(self.median_offset, 4),
            "std_dev_m": round(self.std_dev, 4),
            "p5_m": round(self.p5, 4),
            "p95_m": round(self.p95, 4),
            "sampled_cells": self.sampled_cells_count,
        }


class StripAlignmentChecker(BaseDiagnostic):
    """
    Diagnostic tool to inspect vertical datum offsets between overlapping flight strips.

    Example:
        >>> from dronegeo.diagnostics import StripAlignmentChecker
        >>> checker = StripAlignmentChecker()
        >>> report = checker.run_check("flight_strip1.laz", "flight_strip2.laz", sample_resolution=0.5)
        >>> print(f"Detected Shift: {report.median_offset:+.4f} m")
    """

    def run_check(
        self,
        las_path1: Union[str, Path],
        las_path2: Union[str, Path],
        sample_resolution: float = 0.5,
        outlier_percentiles: Tuple[float, float] = (5.0, 95.0),
        store_residuals: bool = True,
        raise_on_no_overlap: bool = False,
        **kwargs
    ) -> StripAlignmentReport:
        return check_strip_alignment(
            las_path1=las_path1,
            las_path2=las_path2,
            sample_resolution=sample_resolution,
            outlier_percentiles=outlier_percentiles,
            store_residuals=store_residuals,
            raise_on_no_overlap=raise_on_no_overlap,
            config=self.config,
        )


def check_strip_alignment(
    las_path1: Union[str, Path],
    las_path2: Union[str, Path],
    sample_resolution: float = 0.5,
    outlier_percentiles: Tuple[float, float] = (5.0, 95.0),
    store_residuals: bool = True,
    raise_on_no_overlap: bool = False,
    config: Optional[ComputeConfig] = None,
) -> StripAlignmentReport:
    """
    Analyzes the vertical datum offset (ΔZ) between two overlapping point clouds.

    Streams points across the intersection bounding box into a 2D minimum-elevation
    ground comparison surface and computes robust median shift and variance.

    Args:
        las_path1: Reference LAS/LAZ file path.
        las_path2: Secondary LAS/LAZ file path (to align).
        sample_resolution: Spatial grid resolution in meters for overlap sampling (default: 0.5m).
        outlier_percentiles: (low, high) percentile bounds to filter out vegetation/noise outliers.
        store_residuals: If True, stores 1D residual array in report for plotting.
        raise_on_no_overlap: If True, raises NoSpatialOverlapError when clouds do not intersect.
        config: Optional ComputeConfig for chunk sizing.

    Returns:
        StripAlignmentReport instance with exact offset metrics.

    Raises:
        FileNotFoundError: If either input LAS file does not exist on disk.
        EmptyPointCloudError: If either input LAS point cloud contains zero points.
        NoSpatialOverlapError: If clouds do not overlap horizontally and raise_on_no_overlap is True.

    Example:
        >>> import dronegeo as dg
        >>> report = dg.diagnostics.check_strip_alignment(
        ...     las_path1="strip_01.laz",
        ...     las_path2="strip_02.laz",
        ...     sample_resolution=0.5
        ... )
        >>> print(f"Detected Shift: {report.median_offset:+.4f} m (Std: {report.std_dev:.4f} m)")
    """
    cfg = config or get_compute_config()
    p1 = Path(las_path1)
    p2 = Path(las_path2)

    assert p1.exists(), f"Reference LAS file not found: {p1}"
    assert p2.exists(), f"Secondary LAS file not found: {p2}"
    assert sample_resolution > 0, f"sample_resolution must be positive, got {sample_resolution}"

    with laspy.open(str(p1)) as f1, laspy.open(str(p2)) as f2:
        h1, h2 = f1.header, f2.header

        if h1.point_count == 0:
            raise EmptyPointCloudError(f"Reference point cloud is empty: {p1}")
        if h2.point_count == 0:
            raise EmptyPointCloudError(f"Secondary point cloud is empty: {p2}")

        left = max(float(h1.mins[0]), float(h2.mins[0]))
        right = min(float(h1.maxs[0]), float(h2.maxs[0]))
        bottom = max(float(h1.mins[1]), float(h2.mins[1]))
        top = min(float(h1.maxs[1]), float(h2.maxs[1]))

        overlap_box = (left, right, bottom, top)

        if left >= right or bottom >= top:
            if raise_on_no_overlap:
                raise NoSpatialOverlapError(
                    f"No spatial horizontal overlap exists between {p1.name} and {p2.name}",
                    details={"bounds1": (h1.mins[:2], h1.maxs[:2]), "bounds2": (h2.mins[:2], h2.maxs[:2])}
                )
            return StripAlignmentReport(
                las_path1=str(p1),
                las_path2=str(p2),
                overlap_bounds=overlap_box,
                has_overlap=False,
                mean_offset=0.0,
                median_offset=0.0,
                std_dev=0.0,
                p5=0.0,
                p95=0.0,
                sampled_cells_count=0,
            )

        res = float(sample_resolution)
        w = max(1, int(np.ceil((right - left) / res)))
        h = max(1, int(np.ceil((top - bottom) / res)))

        grid1 = np.full((h, w), np.nan, dtype=np.float32)
        grid2 = np.full((h, w), np.nan, dtype=np.float32)

        # 1. Sample Reference Cloud (f1)
        for chunk in f1.chunk_iterator(cfg.chunk_size):
            cx = np.array(chunk.x, dtype=np.float64)
            cy = np.array(chunk.y, dtype=np.float64)
            cz = np.array(chunk.z, dtype=np.float32)

            mask = (cx >= left) & (cx <= right) & (cy >= bottom) & (cy <= top)
            if not np.any(mask):
                continue

            mx, my, mz = cx[mask], cy[mask], cz[mask]
            c_cols = np.clip(((mx - left) / res).astype(int), 0, w - 1)
            c_rows = np.clip(((top - my) / res).astype(int), 0, h - 1)

            for r, c, z in zip(c_rows, c_cols, mz):
                if np.isnan(grid1[r, c]) or z < grid1[r, c]:
                    grid1[r, c] = z

        # 2. Sample Secondary Cloud (f2)
        for chunk in f2.chunk_iterator(cfg.chunk_size):
            cx = np.array(chunk.x, dtype=np.float64)
            cy = np.array(chunk.y, dtype=np.float64)
            cz = np.array(chunk.z, dtype=np.float32)

            mask = (cx >= left) & (cx <= right) & (cy >= bottom) & (cy <= top)
            if not np.any(mask):
                continue

            mx, my, mz = cx[mask], cy[mask], cz[mask]
            c_cols = np.clip(((mx - left) / res).astype(int), 0, w - 1)
            c_rows = np.clip(((top - my) / res).astype(int), 0, h - 1)

            for r, c, z in zip(c_rows, c_cols, mz):
                if np.isnan(grid2[r, c]) or z < grid2[r, c]:
                    grid2[r, c] = z

    valid = (~np.isnan(grid1)) & (~np.isnan(grid2))
    cell_count = int(np.sum(valid))

    if cell_count == 0:
        return StripAlignmentReport(
            las_path1=str(p1),
            las_path2=str(p2),
            overlap_bounds=overlap_box,
            has_overlap=True,
            mean_offset=0.0,
            median_offset=0.0,
            std_dev=0.0,
            p5=0.0,
            p95=0.0,
            sampled_cells_count=0,
        )

    diff = (grid1[valid] - grid2[valid]).astype(np.float64)
    p_low, p_high = outlier_percentiles
    assert p_low < p_high, f"outlier_percentiles low ({p_low}) must be < high ({p_high})"
    val_low = float(np.percentile(diff, p_low))
    val_high = float(np.percentile(diff, p_high))

    diff_filtered = diff[(diff >= val_low) & (diff <= val_high)]
    if len(diff_filtered) == 0:
        diff_filtered = diff

    report = StripAlignmentReport(
        las_path1=str(p1),
        las_path2=str(p2),
        overlap_bounds=overlap_box,
        has_overlap=True,
        mean_offset=float(np.mean(diff_filtered)),
        median_offset=float(np.median(diff_filtered)),
        std_dev=float(np.std(diff_filtered)),
        p5=val_low,
        p95=val_high,
        sampled_cells_count=cell_count,
        raw_residuals=diff_filtered if store_residuals else None,
    )

    del grid1, grid2, valid, diff
    collect_garbage_if_needed(cfg)
    return report
