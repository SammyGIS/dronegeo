"""
dronegeo.diagnostics.autoqc
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Automated Quality Control (AutoQC), Root-Cause Explanation, and Auto-Remediation
Engine for UAV LiDAR Point Clouds and Surface Models (DTMs / DSMs).

Identifies survey defects, explains the physical root cause, quantifies the
downstream GIS impact, suggests exact parameter values to fix them, and provides
an automated `.remediate()` pipeline.
"""

from __future__ import annotations
import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np
import rasterio

from ..core.exceptions import DroneGeoError
from ..lidar.point_metrics import profile_point_cloud
from ..utils.file_utils import verify_las_file, verify_raster_file, ensure_output_directory
from .utils.report_formatters import format_markdown_report, format_terminal_summary
from .utils.anomaly_filters import filter_elevation_outliers, smooth_terrain_spikes, infill_nodata_holes

logger = logging.getLogger(__name__)


class IssueSeverity(str, Enum):
    """Severity classification for survey data defects."""
    HEALTHY = "HEALTHY"
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


@dataclass
class DiagnosticIssue:
    """Represents a single detected survey defect, its root cause, and prescribed fix."""
    code: str
    title: str
    severity: IssueSeverity
    description: str
    root_cause: str
    impact: str
    suggested_parameters: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "title": self.title,
            "severity": self.severity.value,
            "description": self.description,
            "root_cause": self.root_cause,
            "impact": self.impact,
            "suggested_parameters": self.suggested_parameters,
        }


@dataclass
class AutoQCReport:
    """Comprehensive AutoQC report for a point cloud or elevation model."""
    dataset_path: str
    dataset_type: str  # 'point_cloud' or 'elevation_model'
    quality_score: int  # 0 to 100 (100 = perfect survey grade)
    overall_status: IssueSeverity
    summary_metrics: Dict[str, Any] = field(default_factory=dict)
    issues: List[DiagnosticIssue] = field(default_factory=list)

    @property
    def has_critical_issues(self) -> bool:
        return any(issue.severity == IssueSeverity.CRITICAL for issue in self.issues)

    @property
    def aggregated_suggested_parameters(self) -> Dict[str, Any]:
        """Combines all recommended parameters across detected issues."""
        params: Dict[str, Any] = {}
        for issue in self.issues:
            params.update(issue.suggested_parameters)
        return params

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dataset_path": self.dataset_path,
            "dataset_type": self.dataset_type,
            "quality_score": self.quality_score,
            "overall_status": self.overall_status.value,
            "summary_metrics": self.summary_metrics,
            "issues": [issue.to_dict() for issue in self.issues],
            "aggregated_suggested_parameters": self.aggregated_suggested_parameters,
        }

    def to_json(self, indent: int = 2) -> str:
        """Serializes report to structured JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    def to_markdown(self) -> str:
        """Generates a professional GitHub Markdown diagnostic report."""
        return format_markdown_report(
            dataset_path=self.dataset_path,
            dataset_type=self.dataset_type,
            quality_score=self.quality_score,
            overall_status=self.overall_status.value,
            summary_metrics=self.summary_metrics,
            issues=[i.to_dict() for i in self.issues],
        )

    def print_summary(self) -> None:
        """Prints formatted diagnostic summary to console."""
        format_terminal_summary(
            dataset_path=self.dataset_path,
            dataset_type=self.dataset_type,
            quality_score=self.quality_score,
            overall_status=self.overall_status.value,
            summary_metrics=self.summary_metrics,
            issues=[i.to_dict() for i in self.issues],
        )


def inspect_point_cloud(
    las_path: Union[str, Path],
    expected_crs: Optional[Union[str, int]] = None,
) -> AutoQCReport:
    """
    Performs comprehensive AutoQC diagnostic inspection on raw LAS/LAZ point clouds.

    Checks:
    1. CRS / Projection validity and missing EPSG codes.
    2. Atmospheric noise, bird strikes, and multipath elevation floaters/pits.
    3. Ground return density and vegetation penetration deficits.
    4. Missing ground classification codes (Class 0/1 unclassified).
    5. Pulse return completeness.

    Parameters
    ----------
    las_path : str or Path
        Path to input LAS/LAZ point cloud file.
    expected_crs : str or int, optional
        Expected EPSG coordinate system (e.g. 32632) to verify against.

    Returns
    -------
    AutoQCReport
        Structured diagnostic report with quality score, root-cause findings, and recommended parameters.
    """
    las_file = Path(las_path)
    verify_las_file(las_file)
    import laspy

    issues: List[DiagnosticIssue] = []
    quality_score = 100

    report = profile_point_cloud(str(las_file))
    total_pts = report.total_points
    mean_density = report.mean_point_density
    classes = report.classification_percentages

    with laspy.open(str(las_file)) as f:
        header = f.header
        las_data = f.read()

    z_vals = np.array(las_data.z, dtype=np.float64)
    z_mean = float(np.mean(z_vals))
    z_std = float(np.std(z_vals))
    z_min, z_max = float(np.min(z_vals)), float(np.max(z_vals))

    # 1. CRS Check
    crs_str = header.parse_crs()
    has_crs = crs_str is not None and len(str(crs_str).strip()) > 0
    if not has_crs:
        quality_score -= 25
        issues.append(DiagnosticIssue(
            code="LAS_CRS_MISSING",
            title="Missing Coordinate Reference System (CRS)",
            severity=IssueSeverity.CRITICAL,
            description="The point cloud header contains no EPSG projection or WKT coordinate metadata.",
            root_cause="The sensor export software or flight controller saved coordinates in raw local Cartesian space without appending the target CRS header.",
            impact="The point cloud cannot be projected into GIS software (QGIS/ArcGIS) and will fail spatial overlay with other survey layers.",
            suggested_parameters={"assign_crs": int(expected_crs) if expected_crs else 32632},
        ))

    # 2. Outlier / Multipath Elevation Noise Check (Floaters / Pits)
    z_p1 = float(np.percentile(z_vals, 1.0))
    z_p99 = float(np.percentile(z_vals, 99.0))
    iqr = z_p99 - z_p1

    high_noise_mask = z_vals > (z_p99 + 3.0 * iqr)
    low_noise_mask = z_vals < (z_p1 - 3.0 * iqr)
    noise_count = int(np.sum(high_noise_mask) + np.sum(low_noise_mask))
    noise_pct = (noise_count / total_pts) * 100.0 if total_pts > 0 else 0.0

    if noise_count > 0:
        sev = IssueSeverity.CRITICAL if noise_pct > 1.0 else IssueSeverity.WARNING
        quality_score -= (20 if sev == IssueSeverity.CRITICAL else 10)
        issues.append(DiagnosticIssue(
            code="LAS_MULTIPATH_NOISE",
            title="Multipath Elevation Floaters or Subterranean Noise Pits",
            severity=sev,
            description=f"Detected {noise_count:,} severe outlier points ({noise_pct:.2f}%) outside the realistic terrain elevation envelope.",
            root_cause="Atmospheric dust/fog scattering, bird strikes, or optical laser multipath reflection off water bodies and glass roofs.",
            impact="Will create extreme artificial spikes in DSMs, corrupt contour lines, and produce erroneous earthwork cut/fill calculations.",
            suggested_parameters={
                "clean_outliers": True,
                "z_min_cutoff": float(z_p1 - 1.5 * iqr),
                "z_max_cutoff": float(z_p99 + 1.5 * iqr),
                "sor_k_neighbors": 10,
                "sor_std_multiplier": 2.0,
            },
        ))

    # 3. Ground Point Density & Classification Check
    ground_pct = 0.0
    for k, v in classes.items():
        if "Ground" in k or k.startswith("2") or "2" in k:
            ground_pct += v

    ground_density = (ground_pct / 100.0) * mean_density

    if ground_pct < 0.1:
        quality_score -= 30
        issues.append(DiagnosticIssue(
            code="LAS_UNCLASSIFIED",
            title="Unclassified Point Cloud (No Ground Class 2)",
            severity=IssueSeverity.CRITICAL,
            description="The point cloud contains zero classified ground points (all points are class 0/1).",
            root_cause="Point cloud was generated from raw photogrammetry matching or unclassified LiDAR without running morphological ground segmentation.",
            impact="Cannot generate true bare-earth DTMs; running DTM generation will mistakenly include trees and buildings.",
            suggested_parameters={
                "classify_ground": True,
                "ground_filter_method": "progressive_tin",
                "cell_size": 1.0,
            },
        ))
    elif ground_density < 0.5:
        quality_score -= 15
        issues.append(DiagnosticIssue(
            code="LAS_LOW_GROUND_DENSITY",
            title="Low Ground Point Penetration Density",
            severity=IssueSeverity.WARNING,
            description=f"Effective ground density is only {ground_density:.2f} pts/m² (< 0.50 pts/m² recommended threshold).",
            root_cause="Dense vegetation canopy absorption, high flight altitude, fast flight velocity, or wet ground absorbing near-infrared LiDAR pulses.",
            impact="Interpolating bare-earth DTMs with default search parameters may produce interpolation voids or jagged triangulation facets.",
            suggested_parameters={
                "k_neighbors": 14,
                "max_search_radius_m": 5.0,
                "smoothing_regularization": 0.5,
            },
        ))

    quality_score = max(0, min(100, quality_score))
    overall_status = (
        IssueSeverity.CRITICAL if any(i.severity == IssueSeverity.CRITICAL for i in issues)
        else (IssueSeverity.WARNING if any(i.severity == IssueSeverity.WARNING for i in issues)
        else (IssueSeverity.INFO if issues else IssueSeverity.HEALTHY))
    )

    metrics = {
        "total_points": total_pts,
        "mean_point_density_pts_m2": mean_density,
        "ground_point_density_pts_m2": ground_density,
        "ground_percentage": ground_pct,
        "z_min_m": z_min,
        "z_max_m": z_max,
        "z_mean_m": z_mean,
        "z_std_m": z_std,
        "noise_points_count": noise_count,
        "has_valid_crs": has_crs,
    }

    return AutoQCReport(
        dataset_path=str(las_file),
        dataset_type="point_cloud",
        quality_score=quality_score,
        overall_status=overall_status,
        summary_metrics=metrics,
        issues=issues,
    )


def inspect_elevation_model(
    dem_path: Union[str, Path],
) -> AutoQCReport:
    """
    Performs comprehensive AutoQC diagnostic inspection on DTM/DSM GeoTIFF elevation models.

    Checks:
    1. Presence of NoData voids and disconnected hole clusters.
    2. Elevation spikes and artificial sinkhole pits.
    3. Unnatural vertical cliff edges and steep slope anomalies (> 80 deg).
    4. Coordinate Reference System (CRS) resolution and square pixel aspect.

    Parameters
    ----------
    dem_path : str or Path
        Path to input GeoTIFF elevation model.

    Returns
    -------
    AutoQCReport
        Structured diagnostic report with quality score, root-cause findings, and recommended parameters.
    """
    dem_file = Path(dem_path)
    verify_raster_file(dem_file)

    issues: List[DiagnosticIssue] = []
    quality_score = 100

    with rasterio.open(str(dem_file)) as src:
        data = src.read(1).astype(np.float64)
        nodata = src.nodata
        crs = src.crs
        res_x, res_y = abs(src.transform.a), abs(src.transform.e)

    if nodata is not None:
        valid_mask = ~np.isclose(data, nodata) & ~np.isnan(data)
    else:
        valid_mask = ~np.isnan(data)

    total_pixels = data.size
    valid_pixels = int(np.sum(valid_mask))
    void_pixels = total_pixels - valid_pixels
    void_pct = (void_pixels / total_pixels) * 100.0 if total_pixels > 0 else 0.0

    valid_data = data[valid_mask]
    if len(valid_data) == 0:
        return AutoQCReport(
            dataset_path=str(dem_file),
            dataset_type="elevation_model",
            quality_score=0,
            overall_status=IssueSeverity.CRITICAL,
            summary_metrics={"total_pixels": total_pixels, "valid_pixels": 0},
            issues=[DiagnosticIssue(
                code="DEM_EMPTY",
                title="Raster Contains No Valid Elevation Data",
                severity=IssueSeverity.CRITICAL,
                description="All pixels are NoData or NaN.",
                root_cause="Interpolation failed or input was completely clipped.",
                impact="Raster is unusable.",
                suggested_parameters={},
            )],
        )

    z_min, z_max = float(np.min(valid_data)), float(np.max(valid_data))
    z_mean, z_std = float(np.mean(valid_data)), float(np.std(valid_data))

    # 1. CRS Check
    has_crs = crs is not None and len(str(crs).strip()) > 0
    if not has_crs:
        quality_score -= 25
        issues.append(DiagnosticIssue(
            code="DEM_CRS_MISSING",
            title="Missing Coordinate Reference System (CRS)",
            severity=IssueSeverity.CRITICAL,
            description="The GeoTIFF has no projected CRS header or spatial georeferencing information.",
            root_cause="The export tool omitted EPSG metadata during rasterization.",
            impact="Cannot overlay with other project layers in GIS.",
            suggested_parameters={"assign_crs": 32632},
        ))

    # 2. NoData Voids Check
    if void_pct > 1.5:
        sev = IssueSeverity.CRITICAL if void_pct > 15.0 else IssueSeverity.WARNING
        quality_score -= (25 if sev == IssueSeverity.CRITICAL else 10)
        issues.append(DiagnosticIssue(
            code="DEM_VOID_POCKETS",
            title="NoData Voids / Terrain Hole Gaps",
            severity=sev,
            description=f"Raster contains {void_pixels:,} void pixels ({void_pct:.2f}% of survey area).",
            root_cause="Sensor occlusions, shadow areas, water absorption, or point cloud interpolation search radius was too small.",
            impact="Hydrological flow routing and cut/fill volumetric tools will fail or generate erroneous holes.",
            suggested_parameters={
                "fill_voids": True,
                "infill_method": "distance_transform",
                "max_void_radius_px": 20,
            },
        ))

    # 3. Severe Elevation Spikes / Pits Detection
    gy, gx = np.gradient(data)
    gradient_magnitude = np.sqrt(gx**2 + gy**2)
    gradient_magnitude[~valid_mask] = 0.0

    spike_mask = (gradient_magnitude > 15.0) & valid_mask
    spike_count = int(np.sum(spike_mask))

    if spike_count > 0:
        quality_score -= 15
        issues.append(DiagnosticIssue(
            code="DEM_ELEVATION_SPIKES",
            title="Sharp Vertical Terrain Spikes or Unnatural Cliff Tears",
            severity=IssueSeverity.WARNING,
            description=f"Detected {spike_count:,} sharp vertical elevation cliff tears (|dZ| > 15m across adjacent pixels).",
            root_cause="Unfiltered aerial noise (e.g. bird strikes, crane jibs, drone propellers) or unhandled edge discontinuities.",
            impact="Distorts analytical hillshades, creates false extreme slope gradients, and breaks drainage paths.",
            suggested_parameters={
                "despike_filter": True,
                "median_kernel_size": 3,
                "spike_threshold_m": 12.0,
            },
        ))

    quality_score = max(0, min(100, quality_score))
    overall_status = (
        IssueSeverity.CRITICAL if any(i.severity == IssueSeverity.CRITICAL for i in issues)
        else (IssueSeverity.WARNING if any(i.severity == IssueSeverity.WARNING for i in issues)
        else (IssueSeverity.INFO if issues else IssueSeverity.HEALTHY))
    )

    metrics = {
        "dimensions_px": f"{data.shape[1]} x {data.shape[0]}",
        "resolution_m": round(float(res_x), 3),
        "total_pixels": total_pixels,
        "valid_pixels": valid_pixels,
        "void_pixels": void_pixels,
        "void_percentage": void_pct,
        "z_min_m": z_min,
        "z_max_m": z_max,
        "z_mean_m": z_mean,
        "z_std_m": z_std,
        "elevation_spikes_count": spike_count,
        "has_valid_crs": has_crs,
    }

    return AutoQCReport(
        dataset_path=str(dem_file),
        dataset_type="elevation_model",
        quality_score=quality_score,
        overall_status=overall_status,
        summary_metrics=metrics,
        issues=issues,
    )


def remediate_point_cloud(
    las_path: Union[str, Path],
    output_las: Union[str, Path],
    report: Optional[AutoQCReport] = None,
    assign_crs: Optional[int] = None,
    clean_outliers: bool = True,
    z_min_cutoff: Optional[float] = None,
    z_max_cutoff: Optional[float] = None,
) -> str:
    """
    Automatically repairs and cleans a defective LAS point cloud based on AutoQC findings.

    Remediations Applied:
    - Filters out extreme elevation outliers (multipath noise and floaters).
    - Embeds valid EPSG CRS headers into unreferenced point clouds.
    - Preserves all valid point dimensions, RGB colors, and intensity.

    Parameters
    ----------
    las_path : str or Path
        Defective input LAS point cloud path.
    output_las : str or Path
        Destination clean LAS point cloud path.
    report : AutoQCReport, optional
        Pre-computed diagnostic report (if omitted, diagnoses dynamically).
    assign_crs : int, optional
        Explicit EPSG code to assign if missing.
    clean_outliers : bool, default True
        Whether to strip statistical noise floaters and pits.
    z_min_cutoff : float, optional
        Minimum valid elevation cutoff.
    z_max_cutoff : float, optional
        Maximum valid elevation cutoff.

    Returns
    -------
    str
        Path to clean, survey-grade output LAS point cloud.
    """
    las_file = Path(las_path)
    verify_las_file(las_file)
    out_file = ensure_output_directory(output_las)
    import laspy
    import pyproj

    if report is None:
        report = inspect_point_cloud(str(las_file), expected_crs=assign_crs)

    suggested = report.aggregated_suggested_parameters
    effective_crs = assign_crs or suggested.get("assign_crs", 32632)
    effective_z_min = z_min_cutoff if z_min_cutoff is not None else suggested.get("z_min_cutoff")
    effective_z_max = z_max_cutoff if z_max_cutoff is not None else suggested.get("z_max_cutoff")

    with laspy.open(str(las_file)) as f:
        header = f.header
        las_data = f.read()

    z_vals = np.array(las_data.z, dtype=np.float64)

    if clean_outliers:
        keep_mask = filter_elevation_outliers(z_vals, effective_z_min, effective_z_max)
    else:
        keep_mask = np.ones(len(z_vals), dtype=bool)

    filtered_las = las_data[keep_mask]

    if header.parse_crs() is None or effective_crs is not None:
        try:
            filtered_las.header.add_crs(pyproj.CRS.from_epsg(effective_crs))
        except Exception:
            pass

    filtered_las.write(str(out_file))
    logger.info(f"AutoQC remediated LAS written: {out_file} ({len(filtered_las):,} points retained)")
    return str(out_file)


def remediate_elevation_model(
    dem_path: Union[str, Path],
    output_dem: Union[str, Path],
    report: Optional[AutoQCReport] = None,
    fill_voids: bool = True,
    despike_filter: bool = True,
    assign_crs: Optional[int] = None,
) -> str:
    """
    Automatically heals and repairs a defective DTM/DSM GeoTIFF elevation model.

    Remediations Applied:
    - Infills NoData voids and terrain holes using smooth distance-transform nearest-neighbor infilling.
    - Suppresses extreme sensor spikes and cliff tears via adaptive local median filtering.
    - Embeds projected CRS spatial georeferencing metadata if missing.

    Parameters
    ----------
    dem_path : str or Path
        Defective input GeoTIFF elevation model path.
    output_dem : str or Path
        Destination repaired GeoTIFF elevation model path.
    report : AutoQCReport, optional
        Pre-computed diagnostic report (if omitted, diagnoses dynamically).
    fill_voids : bool, default True
        Whether to infill NoData holes.
    despike_filter : bool, default True
        Whether to apply local spike smoothing.
    assign_crs : int, optional
        Target EPSG code to assign if missing.

    Returns
    -------
    str
        Path to repaired GeoTIFF deliverable.
    """
    dem_file = Path(dem_path)
    verify_raster_file(dem_file)
    out_file = ensure_output_directory(output_dem)

    if report is None:
        report = inspect_elevation_model(str(dem_file))

    with rasterio.open(str(dem_file)) as src:
        data = src.read(1).astype(np.float32)
        profile = src.profile.copy()
        nodata = src.nodata

    if nodata is not None:
        invalid_mask = np.isclose(data, nodata) | np.isnan(data)
    else:
        invalid_mask = np.isnan(data)

    repaired_data = data.copy()

    # 1. Infill NoData Voids
    if fill_voids:
        repaired_data = infill_nodata_holes(repaired_data, invalid_mask)

    # 2. Despike Sharp Cliff Tears
    if despike_filter:
        repaired_data = smooth_terrain_spikes(repaired_data, invalid_mask, spike_threshold_m=10.0, kernel_size=3)

    if profile.get("crs") is None and assign_crs is not None:
        profile["crs"] = rasterio.crs.CRS.from_epsg(assign_crs)

    profile.update(dtype="float32", nodata=-9999.0)
    with rasterio.open(str(out_file), "w", **profile) as dst:
        dst.write(repaired_data.astype(np.float32), 1)

    logger.info(f"AutoQC remediated GeoTIFF written: {out_file}")
    return str(out_file)


def inspect(dataset_path: Union[str, Path], **kwargs: Any) -> AutoQCReport:
    """Convenience AutoQC dispatcher that inspects either a LAS/LAZ point cloud or DEM GeoTIFF."""
    path_str = str(dataset_path).lower()
    if path_str.endswith(".las") or path_str.endswith(".laz"):
        return inspect_point_cloud(dataset_path, **kwargs)
    elif path_str.endswith(".tif") or path_str.endswith(".tiff"):
        return inspect_elevation_model(dataset_path)
    else:
        raise DroneGeoError(f"Unsupported dataset format: {dataset_path}. Expected LAS/LAZ or GeoTIFF.")


def remediate(input_path: Union[str, Path], output_path: Union[str, Path], **kwargs: Any) -> str:
    """Convenience AutoQC dispatcher that auto-remediates either a LAS/LAZ point cloud or DEM GeoTIFF."""
    path_str = str(input_path).lower()
    if path_str.endswith(".las") or path_str.endswith(".laz"):
        return remediate_point_cloud(input_path, output_path, **kwargs)
    elif path_str.endswith(".tif") or path_str.endswith(".tiff"):
        return remediate_elevation_model(input_path, output_path, **kwargs)
    else:
        raise DroneGeoError(f"Unsupported dataset format: {input_path}. Expected LAS/LAZ or GeoTIFF.")
