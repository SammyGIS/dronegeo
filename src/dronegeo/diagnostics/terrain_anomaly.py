"""
dronegeo.diagnostics.terrain_anomaly
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Detects terrain elevation spikes, pits, unnatural slope cliffs, and step tears in DEM surfaces.
"""

from __future__ import annotations
from pathlib import Path
from dataclasses import dataclass
from typing import Union, Optional, Dict, Any

import numpy as np
import scipy.ndimage as ndi
import rasterio

from ..config.compute import ComputeConfig, get_compute_config, collect_garbage_if_needed
from ..core.base import BaseDiagnostic
from ..core.exceptions import SurfaceInterpolationError, RasterIOError


@dataclass
class TerrainAnomalyReport:
    """
    Diagnostic report of detected elevation spikes, pits, and slope discontinuities.

    Attributes:
        dem_path: Source DEM GeoTIFF path.
        has_anomalies: True if any anomaly regions exceeded thresholds.
        anomaly_pixel_count: Total number of pixels identified as anomalous.
        anomaly_area_pct: Percentage of valid DEM area affected by anomalies.
        spike_count: Number of high elevation spike pixels detected.
        step_cliff_count: Number of steep artificial slope/cliff pixels detected.
        z_min_valid: Minimum valid elevation in meters.
        z_max_valid: Maximum valid elevation in meters.
        anomaly_mask: 2D boolean mask of anomaly locations.
        downsample_factor: Downsample factor used during analysis.

    Example:
        >>> report = detect_terrain_anomalies("raw_dtm.tif", spike_threshold=1035.0)
        >>> print(f"Has anomalies: {report.has_anomalies}")
        >>> print(f"Affected area: {report.anomaly_area_pct:.2f}% ({report.anomaly_pixel_count:,} pixels)")
    """
    dem_path: str
    has_anomalies: bool
    anomaly_pixel_count: int
    anomaly_area_pct: float
    spike_count: int
    step_cliff_count: int
    z_min_valid: float
    z_max_valid: float
    anomaly_mask: Optional[np.ndarray] = None
    downsample_factor: int = 1

    def to_dict(self) -> Dict[str, Any]:
        """Serializes report metrics into a dictionary."""
        return {
            "dem_path": self.dem_path,
            "has_anomalies": self.has_anomalies,
            "anomaly_pixels": self.anomaly_pixel_count,
            "anomaly_area_pct": round(self.anomaly_area_pct, 3),
            "spike_pixels": self.spike_count,
            "step_cliff_pixels": self.step_cliff_count,
            "z_min_valid_m": round(self.z_min_valid, 2),
            "z_max_valid_m": round(self.z_max_valid, 2),
            "downsample_factor": self.downsample_factor,
        }


class TerrainAnomalyDetector(BaseDiagnostic):
    """
    Diagnostic analyzer for detecting elevation anomalies, sensor jumps, and unnatural cliffs.

    Example:
        >>> from dronegeo.diagnostics import TerrainAnomalyDetector
        >>> detector = TerrainAnomalyDetector()
        >>> report = detector.run_check("raw_dtm.tif", spike_threshold=1035.0)
    """

    def run_check(
        self,
        dem_path: Union[str, Path],
        spike_threshold: Optional[float] = None,
        pit_threshold: Optional[float] = None,
        slope_gradient_threshold_deg: float = 45.0,
        downsample_factor: int = 4,
        dilation_iterations: int = 6,
        **kwargs
    ) -> TerrainAnomalyReport:
        return detect_terrain_anomalies(
            dem_path=dem_path,
            spike_threshold=spike_threshold,
            pit_threshold=pit_threshold,
            slope_gradient_threshold_deg=slope_gradient_threshold_deg,
            downsample_factor=downsample_factor,
            dilation_iterations=dilation_iterations,
            config=self.config,
        )


def detect_terrain_anomalies(
    dem_path: Union[str, Path],
    spike_threshold: Optional[float] = None,
    pit_threshold: Optional[float] = None,
    slope_gradient_threshold_deg: float = 45.0,
    downsample_factor: int = 4,
    dilation_iterations: int = 6,
    config: Optional[ComputeConfig] = None,
) -> TerrainAnomalyReport:
    """
    Inspects a DEM GeoTIFF for elevation spikes, pits, and unnatural vertical tears/cliffs.

    Args:
        dem_path: Path to the input DEM GeoTIFF.
        spike_threshold: Optional absolute elevation upper bound (e.g. 1035.0m). If None, auto-calculated from P99.5.
        pit_threshold: Optional absolute elevation lower bound. If None, auto-calculated from P0.5.
        slope_gradient_threshold_deg: Maximum natural slope angle in degrees before flagging as cliff step (default: 45.0).
        downsample_factor: Downsample factor for rapid spatial analysis (default: 4).
        dilation_iterations: Morphological dilation iterations to expand boundary buffer around anomalies.
        config: Optional ComputeConfig instance.

    Returns:
        TerrainAnomalyReport with full spatial statistics and boolean mask.

    Raises:
        FileNotFoundError: If input DEM GeoTIFF does not exist on disk.
        RasterIOError: If reading GeoTIFF raster arrays fails.

    Example:
        >>> import dronegeo as dg
        >>> anomaly_report = dg.diagnostics.detect_terrain_anomalies(
        ...     dem_path="flight_dtm.tif",
        ...     spike_threshold=1035.0,
        ...     slope_gradient_threshold_deg=45.0
        ... )
        >>> print(f"Detected {anomaly_report.anomaly_pixel_count:,} anomalous pixels")
    """
    cfg = config or get_compute_config()
    p = Path(dem_path)

    assert p.exists(), f"DEM raster not found: {p}"
    assert slope_gradient_threshold_deg > 0, f"slope_gradient_threshold_deg must be positive, got {slope_gradient_threshold_deg}"
    assert downsample_factor >= 1, f"downsample_factor must be >= 1, got {downsample_factor}"

    try:
        with rasterio.open(str(p)) as src:
            dtm_full = src.read(1)
            nodata = float(src.nodata) if src.nodata is not None else -10000.0
            res_x, res_y = src.res
    except Exception as e:
        raise RasterIOError(f"Failed to read DEM raster: {p}", details=str(e))

    ds = max(1, int(downsample_factor))
    dtm = dtm_full[::ds, ::ds].copy()
    del dtm_full
    collect_garbage_if_needed(cfg)

    valid_mask = (dtm != nodata) & (~np.isnan(dtm)) & (dtm > -500.0) & (dtm < 9000.0)
    valid_count = int(np.sum(valid_mask))

    if valid_count == 0:
        return TerrainAnomalyReport(
            dem_path=str(p),
            has_anomalies=False,
            anomaly_pixel_count=0,
            anomaly_area_pct=0.0,
            spike_count=0,
            step_cliff_count=0,
            z_min_valid=0.0,
            z_max_valid=0.0,
            anomaly_mask=np.zeros_like(dtm, dtype=bool),
            downsample_factor=ds,
        )

    valid_z = dtm[valid_mask]
    z_min = float(np.min(valid_z))
    z_max = float(np.max(valid_z))

    if spike_threshold is None:
        p99_7 = float(np.percentile(valid_z, 99.7))
        spike_threshold = p99_7 if (z_max - p99_7) > 15.0 else (z_max + 1.0)

    if pit_threshold is None:
        p0_3 = float(np.percentile(valid_z, 0.3))
        pit_threshold = p0_3 if (p0_3 - z_min) > 15.0 else (z_min - 1.0)

    # 1. Direct Spike and Pit detection
    spike_mask = valid_mask & (dtm >= spike_threshold)
    pit_mask = valid_mask & (dtm <= pit_threshold)

    # 2. Gradient / Slope Discontinuity Detection
    eff_res_x = res_x * ds
    eff_res_y = res_y * ds

    gy, gx = np.gradient(np.where(valid_mask, dtm, np.nan))
    gy = gy / eff_res_y
    gx = gx / eff_res_x
    slope_rad = np.arctan(np.sqrt(gx**2 + gy**2))
    slope_deg = np.degrees(slope_rad)
    cliff_mask = valid_mask & (slope_deg > slope_gradient_threshold_deg) & (~np.isnan(slope_deg))

    anomaly_raw = (spike_mask | pit_mask | cliff_mask) & valid_mask

    if np.any(anomaly_raw) and dilation_iterations > 0:
        anomaly_expanded = ndi.binary_dilation(anomaly_raw, iterations=dilation_iterations) & valid_mask
    else:
        anomaly_expanded = anomaly_raw

    anomaly_px = int(np.sum(anomaly_expanded))
    pct = (anomaly_px / valid_count) * 100.0 if valid_count > 0 else 0.0

    report = TerrainAnomalyReport(
        dem_path=str(p),
        has_anomalies=anomaly_px > 0,
        anomaly_pixel_count=anomaly_px,
        anomaly_area_pct=pct,
        spike_count=int(np.sum(spike_mask)),
        step_cliff_count=int(np.sum(cliff_mask)),
        z_min_valid=z_min,
        z_max_valid=z_max,
        anomaly_mask=anomaly_expanded,
        downsample_factor=ds,
    )

    del dtm, valid_mask, spike_mask, pit_mask, cliff_mask
    collect_garbage_if_needed(cfg)
    return report
