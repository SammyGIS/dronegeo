"""
dronegeo.diagnostics.gcp_validation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Ground Control Point (GCP) and Survey Checkpoint Accuracy Diagnostics Engine.

Evaluates absolute 3D vertical and horizontal accuracy of raw LiDAR point clouds (LAS/LAZ)
and digital elevation models (GeoTIFF) against surveyed field control targets according to
ASPRS and NSSDA geospatial accuracy standards.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import rasterio
from scipy.spatial import cKDTree

from ..core.exceptions import SpatialReferenceError, DatasetValidationError


class PointType(str, Enum):
    """Classification of survey control points."""
    GCP = "GCP"
    CHECK = "CHECK"
    UNKNOWN = "UNKNOWN"


class ResidualStatus(str, Enum):
    """Quality status of individual GCP elevation residual."""
    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"


@dataclass
class GCPResidualPoint:
    """Individual survey control point residual record."""
    point_id: str
    x: float
    y: float
    z_survey: float
    z_drone: float
    delta_z: float  # z_drone - z_survey
    horizontal_dist: float = 0.0
    point_type: PointType = PointType.GCP
    status: ResidualStatus = ResidualStatus.PASS
    neighbors_used: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "point_id": self.point_id,
            "x": round(self.x, 3),
            "y": round(self.y, 3),
            "z_survey": round(self.z_survey, 3),
            "z_drone": round(self.z_drone, 3),
            "delta_z": round(self.delta_z, 4),
            "point_type": self.point_type.value,
            "status": self.status.value,
            "neighbors_used": self.neighbors_used,
        }


@dataclass
class GCPValidationReport:
    """
    Comprehensive statistical accuracy evaluation report against Ground Control Points.
    Compliant with ASPRS Positional Accuracy Standards for Digital Geospatial Data.
    """
    dataset_path: str
    dataset_type: str  # 'point_cloud' or 'elevation_model'
    total_points: int
    num_gcps: int
    num_checkpoints: int
    rmse_z: float
    mean_bias_z: float
    std_dev_z: float
    accuracy_95_nssda: float  # 1.96 * RMSEz
    min_delta_z: float
    max_delta_z: float
    target_tolerance_m: float
    passed_tolerance: bool
    residuals: List[GCPResidualPoint] = field(default_factory=list)
    suspect_outliers: List[GCPResidualPoint] = field(default_factory=list)
    recommended_z_shift: float = 0.0

    def print_summary(self) -> None:
        """Prints a rich, formatted survey accuracy report to the console."""
        sep = "=" * 78
        subsep = "-" * 78
        print(f"\n{sep}")
        print("  DRONEGEO GCP & CHECKPOINT ACCURACY EVALUATION REPORT")
        print(f"{sep}")
        print(f"  Dataset        : {Path(self.dataset_path).name} ({self.dataset_type})")
        print(f"  Control Points : {self.total_points} Total ({self.num_gcps} GCPs, {self.num_checkpoints} Checkpoints)")
        print(f"  Target Spec    : <= {self.target_tolerance_m * 100:.1f} cm vertical tolerance")
        print(f"  Overall Status : {'[PASSED]' if self.passed_tolerance else '[FAILED TOLERANCE]'}")
        print(f"{subsep}")
        print(f"  ASPRS / NSSDA Vertical Accuracy Metrics:")
        print(f"    * Root Mean Square Error (RMSEz) : {self.rmse_z * 100:6.2f} cm ({self.rmse_z:.4f} m)")
        print(f"    * Mean Error (Systematic Bias dZ): {self.mean_bias_z * 100:+6.2f} cm ({self.mean_bias_z:+.4f} m)")
        print(f"    * Standard Deviation (sigma_z)   : {self.std_dev_z * 100:6.2f} cm ({self.std_dev_z:.4f} m)")
        print(f"    * NSSDA 95% Confidence Accuracy  : {self.accuracy_95_nssda * 100:6.2f} cm ({self.accuracy_95_nssda:.4f} m)")
        print(f"    * Error Extents [Min / Max]      : {self.min_delta_z * 100:+6.2f} cm / {self.max_delta_z * 100:+6.2f} cm")
        print(f"{subsep}")
        
        if self.suspect_outliers:
            print(f"  [!] SUSPECT OUTLIER CONTROL POINTS ({len(self.suspect_outliers)} detected):")
            for out in self.suspect_outliers:
                print(f"    - ID '{out.point_id}' ({out.point_type.value}): dZ = {out.delta_z * 100:+.1f} cm (Check for pole height or field note typos)")
            print(f"{subsep}")

        if abs(self.mean_bias_z) > self.target_tolerance_m:
            print(f"  [>] RECOMMENDED DATUM RECTIFICATION:")
            print(f"    Apply vertical shift of dZ = {self.recommended_z_shift:+.4f} m to eliminate survey datum bias.")
            print(f"{subsep}")

        print("  PER-POINT RESIDUAL DETAILS:")
        print(f"    {'ID':<12} {'Type':<8} {'X (Easting)':<12} {'Y (Northing)':<13} {'Z_GCP (m)':<10} {'Z_Drone':<10} {'dZ (cm)':<10} {'Status'}")
        for r in self.residuals:
            print(f"    {r.point_id:<12} {r.point_type.value:<8} {r.x:<12.2f} {r.y:<13.2f} {r.z_survey:<10.3f} {r.z_drone:<10.3f} {r.delta_z * 100:+8.2f}  {r.status.value}")
        print(f"{sep}\n")

    def to_dict(self) -> Dict[str, Any]:
        """Serializes report to dictionary."""
        return {
            "dataset_path": str(self.dataset_path),
            "dataset_type": self.dataset_type,
            "total_points": self.total_points,
            "num_gcps": self.num_gcps,
            "num_checkpoints": self.num_checkpoints,
            "rmse_z_m": round(self.rmse_z, 4),
            "mean_bias_z_m": round(self.mean_bias_z, 4),
            "std_dev_z_m": round(self.std_dev_z, 4),
            "accuracy_95_nssda_m": round(self.accuracy_95_nssda, 4),
            "min_delta_z_m": round(self.min_delta_z, 4),
            "max_delta_z_m": round(self.max_delta_z, 4),
            "target_tolerance_m": self.target_tolerance_m,
            "passed_tolerance": self.passed_tolerance,
            "recommended_z_shift_m": round(self.recommended_z_shift, 4),
            "suspect_outliers": [p.to_dict() for p in self.suspect_outliers],
            "residuals": [p.to_dict() for p in self.residuals],
        }

    def to_markdown(self) -> str:
        """Exports accuracy audit report in GitHub-flavored Markdown."""
        lines = [
            f"# GCP & Checkpoint Accuracy Report: `{Path(self.dataset_path).name}`",
            "",
            f"- **Dataset Type**: `{self.dataset_type}`",
            f"- **Control Points**: {self.total_points} total ({self.num_gcps} GCPs, {self.num_checkpoints} Checkpoints)",
            f"- **Overall Status**: {'**PASSED**' if self.passed_tolerance else '**FAILED TOLERANCE**'}",
            f"- **Target Tolerance**: $\\le {self.target_tolerance_m * 100:.1f}\\text{ cm}$",
            "",
            "## ASPRS / NSSDA Statistical Summary",
            "",
            "| Metric | Value (m) | Value (cm) | Status |",
            "| :--- | :--- | :--- | :--- |",
            f"| **Root Mean Square Error (RMSEz)** | `{self.rmse_z:.4f} m` | `{self.rmse_z * 100:.2f} cm` | {'✅ Pass' if self.rmse_z <= self.target_tolerance_m else '❌ Exceeds'} |",
            f"| **Mean Vertical Bias (ΔZ)** | `{self.mean_bias_z:+.4f} m` | `{self.mean_bias_z * 100:+.2f} cm` | {'Systematic Shift' if abs(self.mean_bias_z) > 0.05 else 'Calibrated'} |",
            f"| **Standard Deviation (σz)** | `{self.std_dev_z:.4f} m` | `{self.std_dev_z * 100:.2f} cm` | - |",
            f"| **NSSDA 95% Confidence Accuracy** | `{self.accuracy_95_nssda:.4f} m` | `{self.accuracy_95_nssda * 100:.2f} cm` | - |",
            "",
            "## Control Point Residuals",
            "",
            "| Point ID | Type | Easting (X) | Northing (Y) | Z Survey (m) | Z Drone (m) | Residual ΔZ (cm) | Status |",
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
        ]
        for r in self.residuals:
            status_icon = "🟢" if r.status == ResidualStatus.PASS else ("🟡" if r.status == ResidualStatus.WARNING else "🔴")
            lines.append(
                f"| `{r.point_id}` | `{r.point_type.value}` | `{r.x:.2f}` | `{r.y:.2f}` | `{r.z_survey:.3f}` | `{r.z_drone:.3f}` | `{r.delta_z * 100:+.2f} cm` | {status_icon} `{r.status.value}` |"
            )
        return "\n".join(lines)


def load_gcp_dataset(
    gcp_input: Union[str, Path, Any]
) -> List[Tuple[str, float, float, float, PointType]]:
    """
    Ingests Ground Control Points from Shapefiles, GeoJSON, GeoPackage, CSV, DataFrame, or dicts.

    Returns:
        List of tuples: `(point_id, x, y, z, point_type)`
    """
    points: List[Tuple[str, float, float, float, PointType]] = []

    # 1. Path input (Shapefile, GeoJSON, GeoPackage, CSV, TXT)
    if isinstance(gcp_input, (str, Path)):
        p = Path(gcp_input)
        if not p.exists():
            raise FileNotFoundError(f"GCP control file not found: {p}")

        suffix = p.suffix.lower()

        # A. Vector Geometries (Shapefile, GeoJSON, GPKG)
        if suffix in (".shp", ".geojson", ".json", ".gpkg"):
            try:
                import geopandas as gpd
            except ImportError:
                raise ImportError("geopandas is required to read Shapefile and GeoJSON GCP files.")

            gdf = gpd.read_file(str(p))
            for idx, row in gdf.iterrows():
                geom = row.geometry
                if geom is None or geom.is_empty:
                    continue

                x, y = geom.x, geom.y
                # Check for 3D Z coordinate in geometry first
                if geom.has_z:
                    z = float(geom.z)
                else:
                    # Look for elevation column
                    z_col = _find_matching_column(row.keys(), ["z", "elev", "elevation", "height", "altitude", "ortho_ht"])
                    if z_col:
                        z = float(row[z_col])
                    else:
                        raise ValueError(f"No Z elevation coordinate found in vector record #{idx} in {p.name}")

                # Find ID and Type
                id_col = _find_matching_column(row.keys(), ["id", "name", "point_id", "pt_id", "code", "target"])
                pt_id = str(row[id_col]) if id_col else f"GCP_{idx + 1}"

                type_col = _find_matching_column(row.keys(), ["type", "class", "point_type", "role"])
                pt_type = _parse_point_type(str(row[type_col])) if type_col else PointType.GCP

                points.append((pt_id, float(x), float(y), float(z), pt_type))
            return points

        # B. Delimited Text (CSV, TXT, TSV)
        elif suffix in (".csv", ".txt", ".tsv", ".dat"):
            import csv
            with open(str(p), "r", encoding="utf-8-sig") as f:
                # Detect delimiter
                sample = f.read(2048)
                f.seek(0)
                sniffer = csv.Sniffer()
                try:
                    dialect = sniffer.sniff(sample)
                    delimiter = dialect.delimiter
                except Exception:
                    delimiter = "," if "," in sample else "\t"

                reader = csv.reader(f, delimiter=delimiter)
                rows = [r for r in reader if r and not r[0].startswith("#")]

            if not rows:
                raise ValueError(f"GCP file {p.name} contains no valid data rows.")

            # Check if first row is a header
            first_row = [c.strip().lower() for c in rows[0]]
            has_header = any(term in first_row for term in ["x", "y", "z", "easting", "northing", "elevation", "id"])

            if has_header:
                header = first_row
                data_rows = rows[1:]
                x_idx = _find_col_idx(header, ["x", "easting", "east", "lon", "longitude"])
                y_idx = _find_col_idx(header, ["y", "northing", "north", "lat", "latitude"])
                z_idx = _find_col_idx(header, ["z", "elevation", "elev", "height", "ortho_ht", "altitude"])
                id_idx = _find_col_idx(header, ["id", "point_id", "pt_id", "name", "target", "code"])
                type_idx = _find_col_idx(header, ["type", "point_type", "class", "role"])
            else:
                # Fallback format: ID, X, Y, Z or X, Y, Z
                data_rows = rows
                if len(rows[0]) >= 4:
                    id_idx, x_idx, y_idx, z_idx, type_idx = 0, 1, 2, 3, (4 if len(rows[0]) > 4 else None)
                else:
                    id_idx, x_idx, y_idx, z_idx, type_idx = None, 0, 1, 2, None

            for i, r in enumerate(data_rows):
                try:
                    x = float(r[x_idx].strip())
                    y = float(r[y_idx].strip())
                    z = float(r[z_idx].strip())
                    pt_id = r[id_idx].strip() if (id_idx is not None and id_idx < len(r)) else f"GCP_{i + 1}"
                    pt_type = _parse_point_type(r[type_idx].strip()) if (type_idx is not None and type_idx < len(r)) else PointType.GCP
                    points.append((pt_id, x, y, z, pt_type))
                except (ValueError, IndexError):
                    continue
            return points

    # 2. In-Memory GeoDataFrame / DataFrame
    elif hasattr(gcp_input, "iterrows") and hasattr(gcp_input, "columns"):
        for idx, row in gcp_input.iterrows():
            if hasattr(row, "geometry") and row.geometry is not None:
                x, y = row.geometry.x, row.geometry.y
                z = float(row.geometry.z) if row.geometry.has_z else float(row.get("z", row.get("elevation", 0.0)))
            else:
                x_col = _find_matching_column(row.keys(), ["x", "easting", "east"])
                y_col = _find_matching_column(row.keys(), ["y", "northing", "north"])
                z_col = _find_matching_column(row.keys(), ["z", "elevation", "elev"])
                x, y, z = float(row[x_col]), float(row[y_col]), float(row[z_col])

            id_col = _find_matching_column(row.keys(), ["id", "name", "point_id", "pt_id"])
            pt_id = str(row[id_col]) if id_col else f"GCP_{idx + 1}"

            type_col = _find_matching_column(row.keys(), ["type", "point_type"])
            pt_type = _parse_point_type(str(row[type_col])) if type_col else PointType.GCP

            points.append((pt_id, x, y, z, pt_type))
        return points

    # 3. List of dicts or objects
    elif isinstance(gcp_input, (list, tuple)):
        for i, item in enumerate(gcp_input):
            if isinstance(item, dict):
                x = float(item.get("x", item.get("easting", 0.0)))
                y = float(item.get("y", item.get("northing", 0.0)))
                z = float(item.get("z", item.get("elevation", 0.0)))
                pt_id = str(item.get("id", item.get("name", f"GCP_{i+1}")))
                pt_type = _parse_point_type(str(item.get("type", "GCP")))
                points.append((pt_id, x, y, z, pt_type))
            elif isinstance(item, (list, tuple)) and len(item) >= 3:
                if len(item) >= 4 and isinstance(item[0], str):
                    pt_id, x, y, z = str(item[0]), float(item[1]), float(item[2]), float(item[3])
                else:
                    pt_id, x, y, z = f"GCP_{i+1}", float(item[0]), float(item[1]), float(item[2])
                points.append((pt_id, x, y, z, PointType.GCP))
        return points

    raise ValueError(f"Unsupported GCP input format: {type(gcp_input)}")


def validate_gcp_accuracy(
    dataset_path: Union[str, Path],
    gcp_data: Union[str, Path, Any],
    search_radius: float = 2.5,
    target_tolerance_m: float = 0.05,
    ground_only: bool = True,
    k_neighbors: int = 6,
) -> GCPValidationReport:
    """
    Evaluates survey accuracy of a LAS/LAZ point cloud or DEM GeoTIFF against Ground Control Points.

    Real-World Use Cases:
        - Survey QC Sign-Off: Confirms if a drone flight meets ASPRS 5cm / 10cm vertical accuracy specs.
        - Datum Rectification: Detects vertical datum shifts (e.g. Geoid vs Ellipsoid height offsets).
        - Blunder Detection: Identifies surveyor pole-height errors or swapped GCP coordinates.

    Args:
        dataset_path: Path to LAS/LAZ point cloud or GeoTIFF DEM.
        gcp_data: Path to GCP file (.shp, .geojson, .gpkg, .csv) or DataFrame / array.
        search_radius: Maximum planar search radius (meters) around each GCP in point cloud.
        target_tolerance_m: Allowable vertical RMSE error threshold (default 0.05m = 5cm).
        ground_only: If True, uses only ASPRS Class 2 (Ground) returns for point clouds.
        k_neighbors: Number of nearest ground points queried for local IDW elevation interpolation.

    Returns:
        GCPValidationReport dataclass with ASPRS statistics, per-point residuals, and remediation advice.
    """
    p_ds = Path(dataset_path)
    if not p_ds.exists():
        raise FileNotFoundError(f"Input survey dataset not found: {p_ds}")

    control_points = load_gcp_dataset(gcp_data)
    if not control_points:
        raise ValueError("No valid Ground Control Points found in provided GCP dataset.")

    suffix = p_ds.suffix.lower()
    residuals: List[GCPResidualPoint] = []

    # -------------------------------------------------------------
    # Scenario A: Validate Raw LAS/LAZ Point Cloud
    # -------------------------------------------------------------
    if suffix in (".las", ".laz"):
        import laspy

        with laspy.open(str(p_ds)) as reader:
            las = reader.read()

        x_pts = np.asarray(las.x, dtype=np.float64)
        y_pts = np.asarray(las.y, dtype=np.float64)
        z_pts = np.asarray(las.z, dtype=np.float64)

        if ground_only and hasattr(las, "classification"):
            classes = np.asarray(las.classification)
            ground_mask = (classes == 2)
            if np.any(ground_mask):
                x_pts, y_pts, z_pts = x_pts[ground_mask], y_pts[ground_mask], z_pts[ground_mask]

        if len(x_pts) == 0:
            raise ValueError("No ground points found in point cloud to evaluate against GCPs.")

        # Build 2D Spatial Kd-Tree for fast neighbor lookup
        xy_coords = np.column_stack([x_pts, y_pts])
        tree = cKDTree(xy_coords)

        for pt_id, gx, gy, gz_survey, pt_type in control_points:
            # Query k nearest neighbors within search radius
            distances, indices = tree.query([gx, gy], k=min(k_neighbors, len(x_pts)), distance_upper_bound=search_radius)

            valid_mask = distances < np.inf
            if not np.any(valid_mask):
                # Out of flight boundary
                continue

            valid_d = distances[valid_mask]
            valid_idx = indices[valid_mask]

            if np.any(valid_d < 1e-4):
                # Direct hit
                z_drone = float(z_pts[valid_idx[np.argmin(valid_d)]])
            else:
                # 2D Inverse Distance Weighting (IDW)
                weights = 1.0 / (valid_d ** 2)
                z_drone = float(np.sum(weights * z_pts[valid_idx]) / np.sum(weights))

            delta_z = z_drone - gz_survey
            abs_dz = abs(delta_z)

            if abs_dz <= target_tolerance_m:
                status = ResidualStatus.PASS
            elif abs_dz <= target_tolerance_m * 1.5:
                status = ResidualStatus.WARNING
            else:
                status = ResidualStatus.FAIL

            residuals.append(
                GCPResidualPoint(
                    point_id=pt_id,
                    x=gx,
                    y=gy,
                    z_survey=gz_survey,
                    z_drone=z_drone,
                    delta_z=delta_z,
                    point_type=pt_type,
                    status=status,
                    neighbors_used=int(np.sum(valid_mask)),
                )
            )

        dataset_type = "point_cloud"

    # -------------------------------------------------------------
    # Scenario B: Validate GeoTIFF Elevation Model (DTM / DSM)
    # -------------------------------------------------------------
    elif suffix in (".tif", ".tiff", ".vrt"):
        with rasterio.open(str(p_ds)) as src:
            dem_data = src.read(1)
            nodata = src.nodata if src.nodata is not None else -9999.0
            transform = src.transform

            for pt_id, gx, gy, gz_survey, pt_type in control_points:
                try:
                    row, col = src.index(gx, gy)
                    if 0 <= row < src.height and 0 <= col < src.width:
                        z_val = float(dem_data[row, col])
                        if z_val != nodata and not np.isnan(z_val):
                            z_drone = z_val
                            delta_z = z_drone - gz_survey
                            abs_dz = abs(delta_z)

                            if abs_dz <= target_tolerance_m:
                                status = ResidualStatus.PASS
                            elif abs_dz <= target_tolerance_m * 1.5:
                                status = ResidualStatus.WARNING
                            else:
                                status = ResidualStatus.FAIL

                            residuals.append(
                                GCPResidualPoint(
                                    point_id=pt_id,
                                    x=gx,
                                    y=gy,
                                    z_survey=gz_survey,
                                    z_drone=z_drone,
                                    delta_z=delta_z,
                                    point_type=pt_type,
                                    status=status,
                                    neighbors_used=1,
                                )
                            )
                except Exception:
                    continue

        dataset_type = "elevation_model"
    else:
        raise DatasetValidationError(f"Unsupported dataset format '{suffix}'. Must be LAS, LAZ, or GeoTIFF.")

    if not residuals:
        raise ValueError(f"No control points overlapped spatially with dataset '{p_ds.name}'. Check coordinate systems.")

    # -------------------------------------------------------------
    # Calculate Statistical Accuracy Metrics (ASPRS / NSSDA)
    # -------------------------------------------------------------
    deltas = np.array([r.delta_z for r in residuals], dtype=np.float64)
    rmse_z = float(np.sqrt(np.mean(deltas ** 2)))
    mean_bias_z = float(np.mean(deltas))
    std_dev_z = float(np.std(deltas, ddof=1)) if len(deltas) > 1 else 0.0
    accuracy_95 = float(1.96 * rmse_z)

    # Detect statistical outliers and surveyor blunders using Median Absolute Deviation (MAD)
    suspect_outliers: List[GCPResidualPoint] = []
    if len(residuals) >= 3:
        median_delta = float(np.median(deltas))
        abs_diffs = np.abs(deltas - median_delta)
        mad = float(np.median(abs_diffs))
        robust_sigma = float(1.4826 * mad) if mad > 1e-4 else (std_dev_z if std_dev_z > 1e-4 else 0.05)
        outlier_bound = max(2.5 * robust_sigma, 1.5 * target_tolerance_m)

        for r in residuals:
            is_mad_outlier = abs(r.delta_z - median_delta) > outlier_bound
            is_gross_blunder = abs(r.delta_z) > (3.0 * target_tolerance_m) and abs(r.delta_z - median_delta) > (2.0 * target_tolerance_m)
            if (is_mad_outlier or is_gross_blunder) and abs(r.delta_z) > target_tolerance_m:
                suspect_outliers.append(r)

    num_gcps = sum(1 for r in residuals if r.point_type == PointType.GCP)
    num_checks = sum(1 for r in residuals if r.point_type == PointType.CHECK)

    passed_tolerance = bool(rmse_z <= target_tolerance_m and len(suspect_outliers) == 0)

    # Compute robust recommended Z shift (excluding gross blunders)
    clean_deltas = [r.delta_z for r in residuals if r not in suspect_outliers]
    if clean_deltas:
        recommended_z_shift = float(-np.mean(clean_deltas))
    else:
        recommended_z_shift = float(-mean_bias_z)

    return GCPValidationReport(
        dataset_path=str(p_ds.resolve()),
        dataset_type=dataset_type,
        total_points=len(residuals),
        num_gcps=num_gcps,
        num_checkpoints=num_checks,
        rmse_z=rmse_z,
        mean_bias_z=mean_bias_z,
        std_dev_z=std_dev_z,
        accuracy_95_nssda=accuracy_95,
        min_delta_z=float(np.min(deltas)),
        max_delta_z=float(np.max(deltas)),
        target_tolerance_m=target_tolerance_m,
        passed_tolerance=passed_tolerance,
        residuals=residuals,
        suspect_outliers=suspect_outliers,
        recommended_z_shift=recommended_z_shift,
    )


# -------------------------------------------------------------
# Internal Helpers
# -------------------------------------------------------------
def _find_matching_column(keys: Any, targets: List[str]) -> Optional[str]:
    keys_clean = {str(k).strip().lower(): str(k) for k in keys}
    for t in targets:
        if t in keys_clean:
            return keys_clean[t]
    return None


def _find_col_idx(header: List[str], targets: List[str]) -> int:
    for t in targets:
        if t in header:
            return header.index(t)
    return 0


def _parse_point_type(val: str) -> PointType:
    v = str(val).strip().upper()
    if "CHECK" in v or "CHK" in v:
        return PointType.CHECK
    return PointType.GCP
