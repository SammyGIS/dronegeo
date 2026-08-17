"""
dronegeo.profiling.diagnostic_plots
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Quality control visualizations: Overlap residual histograms, anomaly heatmaps, and before/after verification.
"""

from __future__ import annotations
from pathlib import Path
from typing import Union, Optional

import numpy as np
import rasterio
import matplotlib.pyplot as plt

from ..diagnostics.strip_alignment import StripAlignmentReport
from ..diagnostics.terrain_anomaly import TerrainAnomalyReport
from ..core.exceptions import AlignmentError, RasterIOError


def plot_strip_overlap_residuals(
    report: StripAlignmentReport,
    output_png: Union[str, Path],
    title: Optional[str] = None,
) -> str:
    """
    Plots the statistical vertical error histogram and residual distribution for overlapping flight strips.

    Args:
        report: StripAlignmentReport from check_strip_alignment().
        output_png: Destination path for the saved image.
        title: Optional custom plot title.

    Returns:
        Absolute string path to the saved PNG plot.

    Raises:
        AlignmentError: If the report contains no raw residuals or no spatial overlap.

    Example:
        >>> import dronegeo as dg
        >>> report = dg.diagnostics.check_strip_alignment("strip1.laz", "strip2.laz")
        >>> dg.profiling.plot_strip_overlap_residuals(report, "outputs/overlap_error_hist.png")
    """
    out_path = Path(output_png)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if report.raw_residuals is None or len(report.raw_residuals) == 0:
        raise AlignmentError("StripAlignmentReport does not contain raw residuals. Run check_strip_alignment with store_residuals=True.")

    res = report.raw_residuals
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6), dpi=150)
    fig.suptitle(title or "Flightline Overlap Vertical Datum Discrepancy (ΔZ)", fontsize=14, fontweight="bold")

    # 1. Error Histogram
    ax1.hist(res, bins=60, color="#2E86AB", edgecolor="black", alpha=0.8, density=True)
    ax1.axvline(report.median_offset, color="red", linestyle="--", linewidth=2.0, label=f"Median Shift: {report.median_offset:+.3f}m")
    ax1.axvline(report.mean_offset, color="orange", linestyle=":", linewidth=2.0, label=f"Mean Shift: {report.mean_offset:+.3f}m")
    ax1.set_title("Overlap Elevation Difference Histogram", fontsize=12, fontweight="bold")
    ax1.set_xlabel("Elevation Difference (Reference - Target) in meters", fontsize=11)
    ax1.set_ylabel("Probability Density", fontsize=11)
    ax1.grid(True, linestyle=":", alpha=0.6)
    ax1.legend(loc="upper right", framealpha=0.9)

    # 2. Cumulative Distribution & Stats Box
    sorted_res = np.sort(res)
    cdf = np.linspace(0, 1, len(sorted_res))
    ax2.plot(sorted_res, cdf, color="#A23B72", linewidth=2.5)
    ax2.axhline(0.5, color="gray", linestyle=":", alpha=0.7)
    ax2.axvline(report.median_offset, color="red", linestyle="--", linewidth=1.5)

    stats_text = (
        f"OVERLAP STATS\n"
        f"{'-'*20}\n"
        f"• Sampled Cells: {report.sampled_cells_count:,}\n"
        f"• Median ΔZ: {report.median_offset:+.4f} m\n"
        f"• Mean ΔZ: {report.mean_offset:+.4f} m\n"
        f"• Std Dev (σ): {report.std_dev:.4f} m\n"
        f"• 5th %: {report.p5:+.4f} m\n"
        f"• 95th %: {report.p95:+.4f} m\n"
    )
    ax2.text(
        0.05, 0.65, stats_text, transform=ax2.transAxes,
        fontsize=10, fontfamily="monospace",
        bbox=dict(boxstyle="round,pad=0.6", facecolor="#F8F9FA", edgecolor="#CED4DA")
    )
    ax2.set_title("Cumulative Error Distribution (CDF)", fontsize=12, fontweight="bold")
    ax2.set_xlabel("Elevation Difference (meters)", fontsize=11)
    ax2.set_ylabel("Cumulative Probability", fontsize=11)
    ax2.grid(True, linestyle=":", alpha=0.6)

    plt.tight_layout()
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    assert out_path.exists() and out_path.stat().st_size > 0, f"Failed to save residual plot: {out_path}"
    return str(out_path)


def plot_anomaly_heatmap(
    dem_path: Union[str, Path],
    anomaly_report: TerrainAnomalyReport,
    output_png: Union[str, Path],
    title: Optional[str] = None,
) -> str:
    """
    Renders a spatial 2D map highlighting detected terrain anomaly regions overlaid on the DEM.

    Args:
        dem_path: Path to the input DEM GeoTIFF.
        anomaly_report: TerrainAnomalyReport from detect_terrain_anomalies().
        output_png: Destination path for the saved image.
        title: Optional custom plot title.

    Returns:
        Absolute string path to the saved PNG plot.

    Example:
        >>> import dronegeo as dg
        >>> anomaly_rep = dg.diagnostics.detect_terrain_anomalies("raw_dtm.tif", spike_threshold=1035.0)
        >>> dg.profiling.plot_anomaly_heatmap("raw_dtm.tif", anomaly_rep, "outputs/anomaly_heatmap.png")
    """
    out_path = Path(output_png)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.open(str(dem_path)) as src:
        dtm = src.read(1)
        nodata = float(src.nodata) if src.nodata is not None else -10000.0

    valid_mask = (dtm != nodata) & (~np.isnan(dtm)) & (dtm > -500.0)
    ds = anomaly_report.downsample_factor
    dtm_ds = np.where(valid_mask[::ds, ::ds], dtm[::ds, ::ds], np.nan)

    fig, ax = plt.subplots(figsize=(12, 10), dpi=150)
    im = ax.imshow(dtm_ds, cmap="terrain")
    cbar = plt.colorbar(im, ax=ax, fraction=0.035, pad=0.04)
    cbar.set_label("Elevation (m)", fontsize=11)

    if anomaly_report.anomaly_mask is not None and np.any(anomaly_report.anomaly_mask):
        mask_overlay = np.zeros((*anomaly_report.anomaly_mask.shape, 4), dtype=np.float32)
        mask_overlay[anomaly_report.anomaly_mask] = [1.0, 0.0, 0.0, 0.55]
        ax.imshow(mask_overlay)

    ax.set_title(
        title or f"Terrain Anomaly Diagnostic Map - {Path(dem_path).name}\n"
        f"({anomaly_report.anomaly_pixel_count:,} anomaly px | {anomaly_report.anomaly_area_pct:.2f}% of survey area)",
        fontsize=13, fontweight="bold"
    )
    ax.axis("off")

    plt.tight_layout()
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    assert out_path.exists() and out_path.stat().st_size > 0, f"Failed to save anomaly heatmap: {out_path}"
    return str(out_path)


def plot_before_after_comparison(
    before_dem: Union[str, Path],
    after_dem: Union[str, Path],
    output_png: Union[str, Path],
    downsample_factor: int = 4,
    title: Optional[str] = None,
) -> str:
    """
    Renders a 3-panel quality control verification map:
    - Panel 1: Original Unrectified DEM.
    - Panel 2: Rectified Clean DEM.
    - Panel 3: Elevation Difference Surface (ΔZ = After - Before).

    Args:
        before_dem: Path to raw / unrectified DEM GeoTIFF.
        after_dem: Path to rectified clean DEM GeoTIFF.
        output_png: Path to save the PNG visualization.
        downsample_factor: Downsample factor for fast rendering (default: 4).
        title: Optional custom title.

    Returns:
        Absolute string path to the saved PNG plot.

    Example:
        >>> import dronegeo as dg
        >>> dg.profiling.plot_before_after_comparison(
        ...     before_dem="raw_dtm.tif",
        ...     after_dem="rectified_dtm.tif",
        ...     output_png="outputs/rectification_verification.png"
        ... )
    """
    out_path = Path(output_png)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.open(str(before_dem)) as src1, rasterio.open(str(after_dem)) as src2:
        d1 = src1.read(1)[::downsample_factor, ::downsample_factor]
        d2 = src2.read(1)[::downsample_factor, ::downsample_factor]
        nodata1 = float(src1.nodata) if src1.nodata is not None else -10000.0
        nodata2 = float(src2.nodata) if src2.nodata is not None else -10000.0

    valid1 = (d1 != nodata1) & (~np.isnan(d1)) & (d1 > -500.0)
    valid2 = (d2 != nodata2) & (~np.isnan(d2)) & (d2 > -500.0)
    common_valid = valid1 & valid2

    d1_vis = np.where(valid1, d1, np.nan)
    d2_vis = np.where(valid2, d2, np.nan)

    diff = np.zeros_like(d1, dtype=np.float32)
    diff[common_valid] = (d2[common_valid] - d1[common_valid])
    diff_vis = np.where(common_valid, diff, np.nan)

    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(22, 8), dpi=150)
    fig.suptitle(title or "Terrain Rectification Verification (Before vs. After)", fontsize=16, fontweight="bold", y=0.98)

    vmin = min(float(np.nanmin(d1_vis)), float(np.nanmin(d2_vis)))
    vmax = max(float(np.nanmax(d1_vis)), float(np.nanmax(d2_vis)))

    im1 = ax1.imshow(d1_vis, cmap="terrain", vmin=vmin, vmax=vmax)
    ax1.set_title("1. Original Baseline DEM", fontsize=12, fontweight="bold")
    ax1.axis("off")
    plt.colorbar(im1, ax=ax1, fraction=0.035, pad=0.04, label="Elevation (m)")

    im2 = ax2.imshow(d2_vis, cmap="terrain", vmin=vmin, vmax=vmax)
    ax2.set_title("2. Rectified Seamless DEM", fontsize=12, fontweight="bold")
    ax2.axis("off")
    plt.colorbar(im2, ax=ax2, fraction=0.035, pad=0.04, label="Elevation (m)")

    diff_max = float(np.nanmax(np.abs(diff_vis))) if np.any(common_valid) else 1.0
    im3 = ax3.imshow(diff_vis, cmap="coolwarm", vmin=-diff_max, vmax=diff_max)
    ax3.set_title("3. Delta Correction Surface (ΔZ)", fontsize=12, fontweight="bold")
    ax3.axis("off")
    plt.colorbar(im3, ax=ax3, fraction=0.035, pad=0.04, label="Correction Delta (m)")

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    assert out_path.exists() and out_path.stat().st_size > 0, f"Failed to save comparison plot: {out_path}"
    return str(out_path)
