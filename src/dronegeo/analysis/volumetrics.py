"""
dronegeo.analysis.volumetrics
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Pix4D-grade 3D Stockpile and Cut & Fill volume calculations between survey epochs and base planes.
"""

from __future__ import annotations
from pathlib import Path
from dataclasses import dataclass
from typing import Union, Optional, Dict, Any

import numpy as np
import rasterio

from ..core.exceptions import IncompatibleRasterDimensionsError, RasterIOError


@dataclass
class VolumetricReport:
    """
    Detailed 3D volumetric computation report (Cut, Fill, and Net volume).

    Attributes:
        cut_volume_m3: Volume of earth excavated/removed (m³).
        fill_volume_m3: Volume of earth added/deposited (m³).
        net_volume_m3: Net volume difference in m³ (Cut - Fill).
        total_volume_m3: Absolute sum of cut and fill in m³.
        surface_area_m2: Planimetric horizontal survey area in m².
        mean_height_diff_m: Average vertical displacement across valid area in meters.
        max_cut_depth_m: Maximum excavation depth in meters.
        max_fill_height_m: Maximum stockpile height in meters.
    """
    cut_volume_m3: float
    fill_volume_m3: float
    net_volume_m3: float
    total_volume_m3: float
    surface_area_m2: float
    mean_height_diff_m: float
    max_cut_depth_m: float
    max_fill_height_m: float

    def to_dict(self) -> Dict[str, Any]:
        """Serializes volumetric metrics to a dictionary."""
        return {
            "cut_volume_m3": round(self.cut_volume_m3, 3),
            "fill_volume_m3": round(self.fill_volume_m3, 3),
            "net_volume_m3": round(self.net_volume_m3, 3),
            "total_volume_m3": round(self.total_volume_m3, 3),
            "surface_area_m2": round(self.surface_area_m2, 2),
            "mean_height_diff_m": round(self.mean_height_diff_m, 4),
            "max_cut_depth_m": round(self.max_cut_depth_m, 3),
            "max_fill_height_m": round(self.max_fill_height_m, 3),
        }


def compute_cut_fill_volume(
    before_dem: Union[str, Path],
    after_dem: Union[str, Path],
    output_diff_tif: Optional[Union[str, Path]] = None,
) -> VolumetricReport:
    """
    Computes 3D Cut & Fill earthwork volumes between two survey DEM epochs.

    Real-World Applications:
        - Mining & Quarries: Calculating monthly extraction volumes for inventory accounting.
        - Construction & Civil Engineering: Verifying subcontractor earthwork invoices
          (m³ of soil excavated vs. backfilled).
        - Natural Hazard Assessment: Measuring landslide debris displacement or coastal erosion.

    When to Use:
        Use when you have two digital elevation models of the same geographic site flown
        at different dates (e.g. Before excavation and After excavation).

    Math Formulation:
        - Cut Volume (m³) = sum(Before - After) * cell_area  (where Before > After)
        - Fill Volume (m³) = sum(After - Before) * cell_area (where After > Before)

    Args:
        before_dem: Path to initial / baseline DEM GeoTIFF.
        after_dem: Path to subsequent / post-construction DEM GeoTIFF.
        output_diff_tif: Optional path to save the 32-bit float elevation difference GeoTIFF.

    Returns:
        VolumetricReport dataclass with complete cut, fill, and net volumes.

    Raises:
        FileNotFoundError: If either input DEM does not exist on disk.
        IncompatibleRasterDimensionsError: If the two DEMs have different grid dimensions.

    Example:
        >>> import dronegeo as dg
        >>> report = dg.analysis.compute_cut_fill_volume(
        ...     before_dem="quarry_january.tif",
        ...     after_dem="quarry_february.tif",
        ...     output_diff_tif="quarry_difference.tif"
        ... )
        >>> print(f"Excavated Cut: {report.cut_volume_m3:,.1f} m³")
        >>> print(f"Deposited Fill: {report.fill_volume_m3:,.1f} m³")
    """
    p1 = Path(before_dem)
    p2 = Path(after_dem)

    assert p1.exists(), f"Baseline DEM not found: {p1}"
    assert p2.exists(), f"Comparison DEM not found: {p2}"

    with rasterio.open(str(p1)) as src1, rasterio.open(str(p2)) as src2:
        if src1.shape != src2.shape:
            raise IncompatibleRasterDimensionsError(
                f"DEM shape mismatch: {src1.shape} != {src2.shape}",
                details={"before_shape": src1.shape, "after_shape": src2.shape}
            )

        d1 = src1.read(1).astype(np.float32)
        d2 = src2.read(1).astype(np.float32)
        nodata1 = float(src1.nodata) if src1.nodata is not None else -10000.0
        nodata2 = float(src2.nodata) if src2.nodata is not None else -10000.0
        res_x, res_y = src1.res
        meta = src1.meta.copy()

    valid1 = (d1 != nodata1) & (~np.isnan(d1)) & (d1 > -500.0)
    valid2 = (d2 != nodata2) & (~np.isnan(d2)) & (d2 > -500.0)
    common_valid = valid1 & valid2

    cell_area = float(res_x * res_y)
    valid_count = int(np.sum(common_valid))

    if valid_count == 0:
        return VolumetricReport(
            cut_volume_m3=0.0,
            fill_volume_m3=0.0,
            net_volume_m3=0.0,
            total_volume_m3=0.0,
            surface_area_m2=0.0,
            mean_height_diff_m=0.0,
            max_cut_depth_m=0.0,
            max_fill_height_m=0.0,
        )

    diff = np.zeros_like(d1, dtype=np.float32)
    diff[common_valid] = (d1[common_valid] - d2[common_valid])

    cut_mask = common_valid & (diff > 0)
    fill_mask = common_valid & (diff < 0)

    cut_vol = float(np.sum(diff[cut_mask]) * cell_area)
    fill_vol = float(np.sum(-diff[fill_mask]) * cell_area)
    net_vol = cut_vol - fill_vol
    tot_vol = cut_vol + fill_vol
    area = valid_count * cell_area

    max_cut = float(np.max(diff[cut_mask])) if np.any(cut_mask) else 0.0
    max_fill = float(np.max(-diff[fill_mask])) if np.any(fill_mask) else 0.0
    mean_diff = float(np.mean(diff[common_valid]))

    if output_diff_tif is not None:
        p_out = Path(output_diff_tif)
        p_out.parent.mkdir(parents=True, exist_ok=True)
        diff_out = np.where(common_valid, diff, -10000.0).astype(np.float32)
        meta.update({'count': 1, 'dtype': 'float32', 'nodata': -10000.0, 'compress': 'lzw'})
        with rasterio.open(str(p_out), "w", **meta) as dst:
            dst.write(diff_out, 1)
        del diff_out

    del d1, d2, diff, valid1, valid2, common_valid

    return VolumetricReport(
        cut_volume_m3=cut_vol,
        fill_volume_m3=fill_vol,
        net_volume_m3=net_vol,
        total_volume_m3=tot_vol,
        surface_area_m2=area,
        mean_height_diff_m=mean_diff,
        max_cut_depth_m=max_cut,
        max_fill_height_m=max_fill,
    )


def compute_stockpile_volume(
    dem_path: Union[str, Path],
    base_elevation: Optional[float] = None,
) -> VolumetricReport:
    """
    Computes the 3D volume of a stockpile or excavation pit against a flat horizontal base plane.

    Real-World Applications:
        - Construction & Aggregates: Auditing stock of gravel, asphalt, sand, or mineral piles.
        - Landfill & Waste Management: Measuring residual capacity in landfill cells.
        - Bulk Material Supply: Calculating bulk material tonnage (volume * bulk density).

    When to Use:
        Use when measuring a pile resting on a known flat yard floor or reference elevation.

    Args:
        dem_path: Path to stockpile DEM GeoTIFF.
        base_elevation: Horizontal reference datum in meters. If None, auto-detected from minimum valid elevation.

    Returns:
        VolumetricReport with stockpile volume and area statistics.

    Example:
        >>> import dronegeo as dg
        >>> stockpile = dg.analysis.compute_stockpile_volume("stockpile_dtm.tif", base_elevation=540.0)
        >>> print(f"Stockpile Volume: {stockpile.cut_volume_m3:,.2f} m³")
    """
    p = Path(dem_path)
    assert p.exists(), f"DEM raster not found: {p}"

    with rasterio.open(str(p)) as src:
        dtm = src.read(1).astype(np.float32)
        nodata = float(src.nodata) if src.nodata is not None else -10000.0
        res_x, res_y = src.res

    valid_mask = (dtm != nodata) & (~np.isnan(dtm)) & (dtm > -500.0)
    valid_count = int(np.sum(valid_mask))
    cell_area = float(res_x * res_y)

    if valid_count == 0:
        return VolumetricReport(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

    if base_elevation is None:
        base_elevation = float(np.min(dtm[valid_mask]))

    height_above_base = np.zeros_like(dtm, dtype=np.float32)
    height_above_base[valid_mask] = dtm[valid_mask] - base_elevation

    pos_mask = valid_mask & (height_above_base > 0)
    neg_mask = valid_mask & (height_above_base < 0)

    pos_vol = float(np.sum(height_above_base[pos_mask]) * cell_area)
    neg_vol = float(np.sum(-height_above_base[neg_mask]) * cell_area)
    area = valid_count * cell_area

    max_h = float(np.max(height_above_base[pos_mask])) if np.any(pos_mask) else 0.0
    min_d = float(np.max(-height_above_base[neg_mask])) if np.any(neg_mask) else 0.0
    mean_h = float(np.mean(height_above_base[valid_mask]))

    del dtm, height_above_base

    return VolumetricReport(
        cut_volume_m3=pos_vol,
        fill_volume_m3=neg_vol,
        net_volume_m3=pos_vol - neg_vol,
        total_volume_m3=pos_vol + neg_vol,
        surface_area_m2=area,
        mean_height_diff_m=mean_h,
        max_cut_depth_m=max_h,
        max_fill_height_m=min_d,
    )
