"""
dronegeo.lidar.point_metrics
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Comprehensive pre-processing point cloud profiling, metadata auditing, density, and QC visualization.
"""

from __future__ import annotations
from pathlib import Path
from dataclasses import dataclass
from typing import Union, Optional, Dict, Any, List, Tuple

import numpy as np
import laspy
import matplotlib.pyplot as plt

from ..config.compute import ComputeConfig, get_compute_config, collect_garbage_if_needed
from ..core.exceptions import PointCloudError, EmptyPointCloudError

ASPRS_CLASS_MAP = {
    0: "Created / Never Classified",
    1: "Unassigned",
    2: "Ground",
    3: "Low Vegetation",
    4: "Medium Vegetation",
    5: "High Vegetation",
    6: "Building",
    7: "Low Point / Noise",
    8: "Model Key-point",
    9: "Water",
    12: "Overlap Points",
}


@dataclass
class PointCloudProfileReport:
    """
    Comprehensive pre-processing audit and quality profile of a LAS/LAZ point cloud.

    Attributes:
        las_path: File path of the point cloud.
        total_points: Total point count in header.
        spatial_bounds_xyz: ((min_x, max_x), (min_y, max_y), (min_z, max_z)).
        footprint_area_sq_m: Approximate horizontal bounding box area in m².
        mean_point_density: Estimated point density in points/m².
        has_rgb: True if Red/Green/Blue color channels are populated.
        has_intensity: True if intensity values are non-zero.
        has_gps_time: True if GPS timestamps are present.
        dimensions_list: List of all stored point format dimension names.
        classification_counts: Dict mapping ASPRS class IDs to point totals.
        classification_percentages: Dict mapping class names to percentage of total cloud.
        elevation_percentiles: Dict of Z elevation quantiles (p1, p5, p25, p50, p75, p95, p99).
        returns_breakdown: Dict mapping return numbers to point counts.

    Example:
        >>> report = profile_point_cloud("flight_survey.laz")
        >>> print(f"Total points: {report.total_points:,}")
        >>> print(f"Point density: {report.mean_point_density:.2f} pts/m²")
        >>> print(f"Class percentages: {report.classification_percentages}")
    """
    las_path: str
    total_points: int
    spatial_bounds_xyz: Dict[str, List[float]]
    footprint_area_sq_m: float
    mean_point_density: float
    has_rgb: bool
    has_intensity: bool
    has_gps_time: bool
    dimensions_list: List[str]
    classification_counts: Dict[int, int]
    classification_percentages: Dict[str, float]
    elevation_percentiles: Dict[str, float]
    returns_breakdown: Dict[int, int]

    def to_dict(self) -> Dict[str, Any]:
        """Serializes report metrics into a dictionary."""
        return {
            "las_path": self.las_path,
            "total_points": self.total_points,
            "spatial_bounds_xyz": self.spatial_bounds_xyz,
            "footprint_area_m2": round(self.footprint_area_sq_m, 1),
            "point_density_pts_m2": round(self.mean_point_density, 2),
            "has_rgb": self.has_rgb,
            "has_intensity": self.has_intensity,
            "has_gps_time": self.has_gps_time,
            "dimensions": self.dimensions_list,
            "classifications": self.classification_percentages,
            "elevation_percentiles_m": self.elevation_percentiles,
            "returns": self.returns_breakdown,
        }


def profile_point_cloud(
    las_path: Union[str, Path],
    sample_limit: Optional[int] = 2_000_000,
    config: Optional[ComputeConfig] = None,
) -> PointCloudProfileReport:
    """
    Executes a complete pre-processing audit on a raw LAS/LAZ point cloud.

    Analyzes header dimensions, point classification breakdown, elevation percentiles,
    pulse return counts, and true-color RGB availability.

    Args:
        las_path: Path to the LAS/LAZ point cloud file.
        sample_limit: Maximum points to stream for statistical percentiles (default: 2,000,000).
        config: Optional ComputeConfig instance.

    Returns:
        PointCloudProfileReport instance.

    Raises:
        FileNotFoundError: If input LAS/LAZ file does not exist on disk.
        EmptyPointCloudError: If point cloud header indicates 0 points.

    Example:
        >>> import dronegeo as dg
        >>> report = dg.lidar.profile_point_cloud("survey.laz")
        >>> print(f"Density: {report.mean_point_density:.1f} pts/m²")
    """
    cfg = config or get_compute_config()
    p = Path(las_path)
    assert p.exists(), f"LAS point cloud not found: {p}"

    with laspy.open(str(p)) as reader:
        h = reader.header
        total_pts = int(h.point_count)
        if total_pts == 0:
            raise EmptyPointCloudError(f"Point cloud contains zero points: {p}")

        min_x, max_x = float(h.mins[0]), float(h.maxs[0])
        min_y, max_y = float(h.mins[1]), float(h.maxs[1])
        min_z, max_z = float(h.mins[2]), float(h.maxs[2])

        area_sq_m = max(1.0, (max_x - min_x) * (max_y - min_y))
        density = total_pts / area_sq_m if area_sq_m > 0 else 0.0

        dim_names = [d.name for d in h.point_format.dimensions]
        has_rgb = "red" in dim_names and "green" in dim_names and "blue" in dim_names
        has_intensity = "intensity" in dim_names
        has_gps_time = "gps_time" in dim_names

        class_counts: Dict[int, int] = {}
        returns_counts: Dict[int, int] = {}
        z_samples: List[float] = []

        pts_collected = 0
        for chunk in reader.chunk_iterator(cfg.chunk_size):
            classes, counts = np.unique(chunk.classification, return_counts=True)
            for c, cnt in zip(classes, counts):
                class_counts[int(c)] = class_counts.get(int(c), 0) + int(cnt)

            ret_nums, ret_counts = np.unique(chunk.return_number, return_counts=True)
            for r, cnt in zip(ret_nums, ret_counts):
                returns_counts[int(r)] = returns_counts.get(int(r), 0) + int(cnt)

            if sample_limit is None or pts_collected < sample_limit:
                sub_z = np.array(chunk.z, dtype=np.float32)
                if sample_limit and (pts_collected + len(sub_z)) > sample_limit:
                    take = sample_limit - pts_collected
                    sub_z = sub_z[:take]
                z_samples.extend(sub_z.tolist())
                pts_collected += len(sub_z)

    class_pcts: Dict[str, float] = {}
    for c_id, cnt in sorted(class_counts.items()):
        name = ASPRS_CLASS_MAP.get(c_id, f"Class {c_id}")
        pct = (cnt / total_pts) * 100.0 if total_pts > 0 else 0.0
        class_pcts[f"{name} ({c_id})"] = round(pct, 2)

    if len(z_samples) > 0:
        z_arr = np.array(z_samples, dtype=np.float64)
        pcts = {
            "p1": round(float(np.percentile(z_arr, 1)), 2),
            "p5": round(float(np.percentile(z_arr, 5)), 2),
            "p25": round(float(np.percentile(z_arr, 25)), 2),
            "p50_median": round(float(np.percentile(z_arr, 50)), 2),
            "p75": round(float(np.percentile(z_arr, 75)), 2),
            "p95": round(float(np.percentile(z_arr, 95)), 2),
            "p99": round(float(np.percentile(z_arr, 99)), 2),
            "min": round(min_z, 2),
            "max": round(max_z, 2),
        }
        del z_arr
    else:
        pcts = {"min": min_z, "max": max_z, "median": (min_z + max_z) / 2.0}

    del z_samples
    collect_garbage_if_needed(cfg)

    return PointCloudProfileReport(
        las_path=str(p),
        total_points=total_pts,
        spatial_bounds_xyz={
            "X": [min_x, max_x],
            "Y": [min_y, max_y],
            "Z": [min_z, max_z],
        },
        footprint_area_sq_m=area_sq_m,
        mean_point_density=density,
        has_rgb=has_rgb,
        has_intensity=has_intensity,
        has_gps_time=has_gps_time,
        dimensions_list=dim_names,
        classification_counts=class_counts,
        classification_percentages=class_pcts,
        elevation_percentiles=pcts,
        returns_breakdown=returns_counts,
    )


def plot_point_cloud_profile(
    report: PointCloudProfileReport,
    output_png: Union[str, Path],
    title: Optional[str] = None,
) -> str:
    """
    Renders a multi-panel pre-processing Quality Control (QC) dashboard from a PointCloudProfileReport.

    Args:
        report: PointCloudProfileReport instance.
        output_png: Destination path for the saved image.
        title: Optional custom dashboard title.

    Returns:
        Absolute string path to the saved PNG plot.

    Example:
        >>> import dronegeo as dg
        >>> report = dg.lidar.profile_point_cloud("flight.laz")
        >>> dg.lidar.plot_point_cloud_profile(report, "preflight_audit.png")
    """
    out_path = Path(output_png)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    fig = plt.figure(figsize=(16, 10), dpi=200)
    fig.suptitle(title or f"Point Cloud Pre-Processing Audit: {Path(report.las_path).name}", fontsize=15, fontweight="bold", y=0.98)

    # 1. Classification Pie Chart
    ax1 = fig.add_subplot(2, 2, 1)
    labels = list(report.classification_percentages.keys())
    values = list(report.classification_percentages.values())
    if len(values) > 0 and sum(values) > 0:
        ax1.pie(values, labels=labels, autopct="%1.1f%%", startangle=140, textprops={'fontsize': 9})
    ax1.set_title("ASPRS Classification Breakdown", fontsize=12, fontweight="bold")

    # 2. Elevation Percentiles
    ax2 = fig.add_subplot(2, 2, 2)
    p_names = ["p1", "p5", "p25", "p50_median", "p75", "p95", "p99"]
    p_vals = [report.elevation_percentiles.get(k, 0.0) for k in p_names]
    ax2.plot(p_names, p_vals, marker='o', color='#2B5B84', linewidth=2.2, markersize=7)
    ax2.set_title("Elevation (Z) Quantile Profile", fontsize=12, fontweight="bold")
    ax2.set_ylabel("Elevation (m)", fontsize=11)
    ax2.grid(True, linestyle=":", alpha=0.6)

    # 3. Return Number Breakdown
    ax3 = fig.add_subplot(2, 2, 3)
    rets = sorted(report.returns_breakdown.keys())
    r_counts = [report.returns_breakdown[r] for r in rets]
    ax3.bar([f"Return {r}" for r in rets], r_counts, color="#3A86C8", edgecolor="black", alpha=0.85)
    ax3.set_title("LiDAR Pulse Return Distribution", fontsize=12, fontweight="bold")
    ax3.set_ylabel("Points Count", fontsize=11)
    ax3.grid(True, axis='y', linestyle=":", alpha=0.6)

    # 4. Text Summary Card
    ax4 = fig.add_subplot(2, 2, 4)
    ax4.axis("off")
    summary_text = (
        f"POINT CLOUD AUDIT SUMMARY\n"
        f"{'='*38}\n"
        f"• Total Points: {report.total_points:,}\n"
        f"• Point Density: {report.mean_point_density:.2f} pts/m²\n"
        f"• Bounding Footprint: {report.footprint_area_sq_m / 10000:.2f} ha\n"
        f"• X Range: [{report.spatial_bounds_xyz['X'][0]:.2f}, {report.spatial_bounds_xyz['X'][1]:.2f}]\n"
        f"• Y Range: [{report.spatial_bounds_xyz['Y'][0]:.2f}, {report.spatial_bounds_xyz['Y'][1]:.2f}]\n"
        f"• Z Range: [{report.spatial_bounds_xyz['Z'][0]:.2f}m, {report.spatial_bounds_xyz['Z'][1]:.2f}m]\n"
        f"• RGB Color: {'Available' if report.has_rgb else 'Not Present'}\n"
        f"• Intensity: {'Available' if report.has_intensity else 'Not Present'}\n"
        f"• GPS Time: {'Available' if report.has_gps_time else 'Not Present'}\n"
    )
    ax4.text(
        0.05, 0.5, summary_text,
        fontsize=11, fontfamily="monospace", va="center",
        bbox=dict(boxstyle="round,pad=0.8", facecolor="#F8F9FA", edgecolor="#CED4DA")
    )

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    return str(out_path)


def compute_point_density(
    las_path: Union[str, Path],
    grid_resolution: float = 1.0,
    config: Optional[ComputeConfig] = None,
) -> Tuple[np.ndarray, Tuple[float, float, float, float]]:
    """
    Computes a 2D spatial point density grid (points per square meter).

    Args:
        las_path: Path to LAS/LAZ point cloud file.
        grid_resolution: Grid pixel size in meters (default: 1.0m).
        config: Optional ComputeConfig instance.

    Returns:
        Tuple of (density_grid_array, (min_x, max_x, min_y, max_y)).

    Example:
        >>> import dronegeo as dg
        >>> density_grid, bounds = dg.lidar.compute_point_density("survey.laz", grid_resolution=1.0)
    """
    cfg = config or get_compute_config()
    p = Path(las_path)
    assert p.exists(), f"LAS point cloud not found: {p}"
    assert grid_resolution > 0, f"grid_resolution must be positive, got {grid_resolution}"

    with laspy.open(str(p)) as reader:
        h = reader.header
        min_x, max_x = float(h.mins[0]), float(h.maxs[0])
        min_y, max_y = float(h.mins[1]), float(h.maxs[1])

        res = float(grid_resolution)
        width = max(1, int(np.ceil((max_x - min_x) / res)))
        height = max(1, int(np.ceil((max_y - min_y) / res)))

        density = np.zeros((height, width), dtype=np.uint32)

        for chunk in reader.chunk_iterator(cfg.chunk_size):
            cx = np.array(chunk.x, dtype=np.float64)
            cy = np.array(chunk.y, dtype=np.float64)

            cols = np.clip(((cx - min_x) / res).astype(int), 0, width - 1)
            rows = np.clip(((max_y - cy) / res).astype(int), 0, height - 1)

            indices = rows * width + cols
            u_idx, u_cnt = np.unique(indices, return_counts=True)
            density.flat[u_idx] += u_cnt.astype(np.uint32)

    cell_area = res * res
    density_per_sqm = density.astype(np.float32) / cell_area
    del density
    collect_garbage_if_needed(cfg)

    return density_per_sqm, (min_x, max_x, min_y, max_y)
