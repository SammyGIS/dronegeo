"""
dronegeo.profiling.elevation_transects
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
1D/2D cross-sectional elevation profiling and multi-transect quality control plotting.
"""

from __future__ import annotations
from pathlib import Path
from typing import Union, List, Optional, Dict, Any

import numpy as np
import rasterio
import matplotlib.pyplot as plt

from ..core.base import BaseProfiler
from ..core.exceptions import RasterIOError, SurfaceInterpolationError


class ElevationTransectProfiler(BaseProfiler):
    """
    Topographic cross-section profiler for 1D/2D DEM transect extraction and QC visualization.

    Example:
        >>> from dronegeo.profiling import ElevationTransectProfiler
        >>> profiler = ElevationTransectProfiler()
        >>> transects = profiler.extract_profile("dtm.tif", direction="vertical", count=3)
        >>> plot_png = profiler.plot_profile("dtm.tif", "transect_qc.png", direction="vertical")
    """

    def extract_profile(
        self,
        dem_path: Union[str, Path],
        direction: str = "vertical",
        indices: Optional[List[int]] = None,
        count: int = 3,
        **kwargs
    ) -> List[Dict[str, Any]]:
        return extract_orthogonal_transects(
            dem_path=dem_path,
            direction=direction,
            indices=indices,
            count=count,
        )

    def plot_profile(
        self,
        dem_path: Union[str, Path],
        output_png: Union[str, Path],
        direction: str = "vertical",
        indices: Optional[List[int]] = None,
        count: int = 3,
        anomaly_threshold: Optional[float] = None,
        colormap: str = "gist_earth",
        downsample_preview: int = 5,
        title: Optional[str] = None,
        **kwargs
    ) -> str:
        return plot_elevation_transects(
            dem_path=dem_path,
            output_png=output_png,
            direction=direction,
            indices=indices,
            count=count,
            anomaly_threshold=anomaly_threshold,
            colormap=colormap,
            downsample_preview=downsample_preview,
            title=title,
        )


def extract_orthogonal_transects(
    dem_path: Union[str, Path],
    direction: str = "vertical",
    indices: Optional[List[int]] = None,
    count: int = 3,
) -> List[Dict[str, Any]]:
    """
    Extracts 1D distance vs elevation profile curves along orthogonal grid columns or rows.

    Args:
        dem_path: Path to DEM GeoTIFF.
        direction: "vertical" (South to North) or "horizontal" (West to East).
        indices: Optional list of specific column/row pixel indices. If None, auto-selected across valid data.
        count: Number of transects to auto-select if indices is None (default: 3).

    Returns:
        List of dictionaries containing name, index, distance_m, and elevation_m arrays.

    Raises:
        FileNotFoundError: If input DEM raster file does not exist on disk.
        RasterIOError: If reading the raster file fails.

    Example:
        >>> import dronegeo as dg
        >>> profiles = dg.profiling.extract_orthogonal_transects("dtm.tif", direction="vertical", count=3)
        >>> for p in profiles:
        ...     print(f"{p['name']}: {len(p['elevation_m'])} samples, max elev: {np.max(p['elevation_m']):.2f}m")
    """
    p = Path(dem_path)
    assert p.exists(), f"DEM file not found: {p}"
    assert count >= 1, f"count must be at least 1, got {count}"

    try:
        with rasterio.open(str(p)) as src:
            dtm = src.read(1)
            nodata = float(src.nodata) if src.nodata is not None else -10000.0
            res_x, res_y = src.res
    except Exception as e:
        raise RasterIOError(f"Failed to read raster: {p}", details=str(e))

    valid_mask = (dtm != nodata) & (~np.isnan(dtm)) & (dtm > -500.0)
    rows, cols = dtm.shape

    transects = []

    if direction.lower().startswith("v"):
        valid_cols = np.where(np.any(valid_mask, axis=0))[0]
        if len(valid_cols) == 0:
            return []

        if indices is None:
            chosen_cols = np.linspace(valid_cols[0] + 50, valid_cols[-1] - 50, count, dtype=int).tolist()
        else:
            chosen_cols = indices

        for c in chosen_cols:
            c = int(np.clip(c, 0, cols - 1))
            v_rows = np.where(valid_mask[:, c])[0]
            if len(v_rows) == 0:
                continue

            rows_s_to_n = np.sort(v_rows)[::-1]
            elev = dtm[rows_s_to_n, c]
            dist = np.arange(len(rows_s_to_n)) * res_y

            transects.append({
                "name": f"Transect (Col {c})",
                "index": c,
                "direction": "vertical",
                "start_rc": (int(rows_s_to_n[0]), c),
                "end_rc": (int(rows_s_to_n[-1]), c),
                "distance_m": dist,
                "elevation_m": elev,
            })
    else:
        valid_rows = np.where(np.any(valid_mask, axis=1))[0]
        if len(valid_rows) == 0:
            return []

        if indices is None:
            chosen_rows = np.linspace(valid_rows[0] + 50, valid_rows[-1] - 50, count, dtype=int).tolist()
        else:
            chosen_rows = indices

        for r in chosen_rows:
            r = int(np.clip(r, 0, rows - 1))
            v_cols = np.where(valid_mask[r, :])[0]
            if len(v_cols) == 0:
                continue

            cols_w_to_e = np.sort(v_cols)
            elev = dtm[r, cols_w_to_e]
            dist = (cols_w_to_e - cols_w_to_e[0]) * res_x

            transects.append({
                "name": f"Transect (Row {r})",
                "index": r,
                "direction": "horizontal",
                "start_rc": (r, int(cols_w_to_e[0])),
                "end_rc": (r, int(cols_w_to_e[-1])),
                "distance_m": dist,
                "elevation_m": elev,
            })

    return transects


def plot_elevation_transects(
    dem_path: Union[str, Path],
    output_png: Union[str, Path],
    direction: str = "vertical",
    indices: Optional[List[int]] = None,
    count: int = 3,
    anomaly_threshold: Optional[float] = None,
    colormap: str = "gist_earth",
    downsample_preview: int = 5,
    title: Optional[str] = None,
) -> str:
    """
    Renders a dual-panel topographic transect analysis plot:
    - Left Panel: 2D DEM Overview with transect line paths and start/end direction arrows.
    - Right Panel: 1D continuous distance vs. elevation profile curves.

    Args:
        dem_path: Path to input DEM GeoTIFF.
        output_png: Path where the output image should be saved.
        direction: "vertical" or "horizontal".
        indices: Optional explicit column or row indices.
        count: Number of transects to auto-place if indices is None (default: 3).
        anomaly_threshold: Optional elevation threshold (in meters) to highlight as a reference line.
        colormap: Matplotlib colormap for the 2D surface overview (default: 'gist_earth').
        downsample_preview: Downsample factor for fast overview map rendering (default: 5).
        title: Optional custom plot title.

    Returns:
        Absolute string path to the saved PNG plot.

    Raises:
        ValueError: If no valid transects could be extracted from the DEM.

    Example:
        >>> import dronegeo as dg
        >>> plot_file = dg.profiling.plot_elevation_transects(
        ...     dem_path="outputs/survey_dtm.tif",
        ...     output_png="outputs/transect_profiles.png",
        ...     direction="vertical",
        ...     count=3
        ... )
    """
    p = Path(dem_path)
    out_path = Path(output_png)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.open(str(p)) as src:
        dtm = src.read(1)
        nodata = float(src.nodata) if src.nodata is not None else -10000.0

    valid_mask = (dtm != nodata) & (~np.isnan(dtm)) & (dtm > -500.0)
    transects = extract_orthogonal_transects(p, direction=direction, indices=indices, count=count)

    if len(transects) == 0:
        raise ValueError(f"No valid transects could be extracted from {p.name}")

    fig = plt.figure(figsize=(18, 10), dpi=150)
    fig.suptitle(title or f"Elevation Transect Analysis - {p.name}", fontsize=15, fontweight="bold", y=0.98)

    # 1. 2D Map Overview (Left)
    ax1 = fig.add_subplot(1, 2, 1)
    ds = max(1, int(downsample_preview))
    dtm_vis = np.where(valid_mask[::ds, ::ds], dtm[::ds, ::ds], np.nan)
    im = ax1.imshow(dtm_vis, cmap=colormap)

    palette = ['#00E5FF', '#FFD600', '#FF4081', '#76FF03', '#FF6D00']

    for idx, t in enumerate(transects):
        c = palette[idx % len(palette)]
        r1, c1 = t["start_rc"]
        r2, c2 = t["end_rc"]

        ax1.plot([c1 / ds, c2 / ds], [r1 / ds, r2 / ds], color=c, linewidth=2.5, label=t["name"])
        ax1.scatter([c1 / ds], [r1 / ds], color=c, marker='v' if t["direction"] == "vertical" else '>', s=90, edgecolors='black')
        ax1.scatter([c2 / ds], [r2 / ds], color=c, marker='^' if t["direction"] == "vertical" else '<', s=90, edgecolors='black')

    ax1.set_title("2D DEM Surface with Transect Lines", fontsize=12, fontweight="bold")
    ax1.legend(loc='lower left', framealpha=0.9, fontsize=10)
    ax1.axis('off')
    cbar = plt.colorbar(im, ax=ax1, fraction=0.035, pad=0.04)
    cbar.set_label("Elevation (m)", fontsize=11)

    # 2. 1D Profile Curves (Right)
    ax2 = fig.add_subplot(1, 2, 2)
    for idx, t in enumerate(transects):
        c = palette[idx % len(palette)]
        ax2.plot(t["distance_m"], t["elevation_m"], color=c, linewidth=2.2, label=t["name"])

    if anomaly_threshold is not None:
        ax2.axhline(anomaly_threshold, color='red', linestyle='--', linewidth=1.5, label=f'Threshold ({anomaly_threshold:.1f}m)')

    ax2.set_title(f"Elevation Profiles ({'South to North' if direction.lower().startswith('v') else 'West to East'})", fontsize=12, fontweight="bold")
    ax2.set_xlabel("Distance along Transect (meters)", fontsize=11)
    ax2.set_ylabel("Elevation (meters)", fontsize=11)
    ax2.grid(True, linestyle="--", alpha=0.6)
    ax2.legend(loc='upper left', framealpha=0.9, fontsize=10)

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(out_path, bbox_inches='tight')
    plt.close(fig)

    del dtm, valid_mask
    assert out_path.exists() and out_path.stat().st_size > 0, f"Failed to save transect plot: {out_path}"
    return str(out_path)
