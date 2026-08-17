r"""
dronegeo.hydrology.risk_indices
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Terrain risk modeling: Topographic Wetness Index (TWI), Stream Power Index (SPI),
Sediment Transport Index (STI), and Slope Failure / Landslide Hazard Risk Index.

Scientific References & Literature:
1. **Topographic Wetness Index (TWI / CTI)**:
   - Beven, K. J., & Kirkby, M. J. (1979). A physically based, variable contributing area model of
     basin hydrology. *Hydrological Sciences Bulletin*, 24(1), 43-69.
     https://doi.org/10.1080/02626667909491834
   - Sørensen, R., Zinko, U., & Seibert, J. (2006). On the calculation of the topographic wetness index:
     evaluation of different methods based on field observations. *Hydrology and Earth System Sciences*,
     10(1), 101-112. https://doi.org/10.5194/hess-10-101-2006
   - Formula: $\text{TWI} = \ln\left(\frac{a}{\tan(\beta) + \epsilon}\right)$
     where $a$ is specific catchment area per unit contour width ($A / \text{cell\_size}$) and $\beta$ is slope (radians).

2. **Stream Power Index (SPI)**:
   - Moore, I. D., Grayson, R. B., & Ladson, A. R. (1991). Digital terrain modelling: A review of
     hydrological, geomorphological, and biological applications. *Hydrological Processes*, 5(1), 3-30.
     https://doi.org/10.1002/hyp.3360050103
   - Formula: $\text{SPI} = a \cdot \tan(\beta)$
     Measures potential stream erosion and channel scouring force.

3. **Sediment Transport Index (STI / LS Factor)**:
   - Moore, I. D., & Burch, G. J. (1986). Physical basis of the length-slope factor in the Universal Soil
     Loss Equation. *Soil Science Society of America Journal*, 50(5), 1294-1298.
   - Moore, I. D., & Wilson, J. P. (1992). Length-slope factors for the Revised Universal Soil Loss
     Equation: Simplified method of estimation. *Journal of Soil and Water Conservation*, 47(5), 423-428.
   - Formula: $\text{STI} = \left(\frac{a}{22.13}\right)^{0.6} \cdot \left(\frac{\sin(\beta)}{0.0896}\right)^{1.3}$

4. **Multi-Criteria Landslide / Slope Instability Hazard Index**:
   - Montgomery, D. R., & Dietrich, W. E. (1994). A physically based model for the topographic control on
     shallow landsliding. *Water Resources Research*, 30(4), 1153-1171.
   - Combines slope gradient ($\beta$), soil saturation propensity ($\text{TWI}$), and surface planform curvature.
"""

from __future__ import annotations
from pathlib import Path
from dataclasses import dataclass
from typing import Union, Optional, Tuple, Dict, Any
import numpy as np
import rasterio

from ..core.exceptions import ComputationError, RasterIOError
from ..utils.file_utils import ensure_output_directory
from .flow_accumulation import compute_flow_accumulation


def compute_topographic_wetness_index(
    dem_path: Union[str, Path],
    output_tif: Union[str, Path],
    accumulation_path: Optional[Union[str, Path]] = None,
    epsilon: float = 0.001,
) -> str:
    """
    Computes Topographic Wetness Index (TWI) / Compound Topographic Index (CTI).

    Scientific Reference:
        Beven, K. J., & Kirkby, M. J. (1979). "A physically based, variable contributing area model
        of basin hydrology." Hydrological Sciences Bulletin, 24(1), 43-69.

    Formula:
        TWI = ln( a / (tan(beta) + epsilon) )
        where a = Specific Catchment Area = (Accumulation * cell_width) / contour_width

    Args:
        dem_path: Input DEM GeoTIFF path.
        output_tif: Destination TWI GeoTIFF path (float32).
        accumulation_path: Optional pre-computed flow accumulation raster path.
        epsilon: Small positive smoothing factor to prevent division by zero on perfectly flat cells.

    Returns:
        String path to the output TWI GeoTIFF.
    """
    ensure_output_directory(output_tif)
    p_dem = Path(dem_path)
    if not p_dem.exists():
        raise FileNotFoundError(f"DEM not found: {p_dem}")

    try:
        with rasterio.open(str(p_dem)) as src:
            dem = src.read(1).astype(np.float64)
            profile = src.profile.copy()
            dx = float(src.res[0])
            dy = float(src.res[1])
            nodata = src.nodata if src.nodata is not None else -9999.0

        valid = (dem != nodata) & (~np.isnan(dem))

        # Compute slope in radians
        gy, gx = np.gradient(dem, dy, dx)
        slope_rad = np.arctan(np.sqrt(gx**2 + gy**2))

        # Compute or load flow accumulation
        if accumulation_path is not None and Path(accumulation_path).exists():
            with rasterio.open(str(accumulation_path)) as asrc:
                accum = asrc.read(1).astype(np.float64)
        else:
            temp_accum = Path(output_tif).with_suffix(".accum_temp.tif")
            compute_flow_accumulation(dem_path, temp_accum, units="cells")
            with rasterio.open(str(temp_accum)) as asrc:
                accum = asrc.read(1).astype(np.float64)
            if temp_accum.exists():
                temp_accum.unlink()

        # Specific catchment area per unit contour width (a = Accumulation * cell_area / contour_length)
        specific_catchment_area = np.maximum(1.0, accum) * dx

        # TWI calculation: ln(a / (tan(slope) + epsilon))
        tan_slope = np.tan(slope_rad)
        twi = np.log(specific_catchment_area / (tan_slope + epsilon))
        twi[~valid] = -9999.0

        profile.update(dtype="float32", count=1, nodata=-9999.0)
        with rasterio.open(str(output_tif), "w", **profile) as dst:
            dst.write(twi.astype(np.float32), 1)

        return str(Path(output_tif).resolve())

    except Exception as e:
        raise ComputationError(f"Failed to compute Topographic Wetness Index (TWI): {e}")


def compute_stream_power_index(
    dem_path: Union[str, Path],
    output_tif: Union[str, Path],
    accumulation_path: Optional[Union[str, Path]] = None,
) -> str:
    """
    Computes Stream Power Index (SPI) quantifying potential water flow erosive energy.

    Scientific Reference:
        Moore, I. D., Grayson, R. B., & Ladson, A. R. (1991). "Digital terrain modelling: A review of
        hydrological, geomorphological, and biological applications." Hydrological Processes, 5(1), 3-30.

    Formula:
        SPI = a * tan(beta)
        where a = Specific Catchment Area, beta = Topographic Slope (radians).

    Args:
        dem_path: Input DEM GeoTIFF path.
        output_tif: Output SPI GeoTIFF path.
        accumulation_path: Optional pre-computed flow accumulation raster path.

    Returns:
        String path to the output SPI GeoTIFF.
    """
    ensure_output_directory(output_tif)
    p_dem = Path(dem_path)
    if not p_dem.exists():
        raise FileNotFoundError(f"DEM not found: {p_dem}")

    try:
        with rasterio.open(str(p_dem)) as src:
            dem = src.read(1).astype(np.float64)
            profile = src.profile.copy()
            dx = float(src.res[0])
            dy = float(src.res[1])
            nodata = src.nodata if src.nodata is not None else -9999.0

        valid = (dem != nodata) & (~np.isnan(dem))

        # Slope
        gy, gx = np.gradient(dem, dy, dx)
        slope_rad = np.arctan(np.sqrt(gx**2 + gy**2))

        # Flow accumulation
        if accumulation_path is not None and Path(accumulation_path).exists():
            with rasterio.open(str(accumulation_path)) as asrc:
                accum = asrc.read(1).astype(np.float64)
        else:
            temp_accum = Path(output_tif).with_suffix(".spi_accum_temp.tif")
            compute_flow_accumulation(dem_path, temp_accum, units="cells")
            with rasterio.open(str(temp_accum)) as asrc:
                accum = asrc.read(1).astype(np.float64)
            if temp_accum.exists():
                temp_accum.unlink()

        specific_catchment_area = np.maximum(1.0, accum) * dx
        spi = specific_catchment_area * np.tan(slope_rad)
        spi[~valid] = -9999.0

        profile.update(dtype="float32", count=1, nodata=-9999.0)
        with rasterio.open(str(output_tif), "w", **profile) as dst:
            dst.write(spi.astype(np.float32), 1)

        return str(Path(output_tif).resolve())

    except Exception as e:
        raise ComputationError(f"Failed to compute Stream Power Index (SPI): {e}")


def compute_sediment_transport_index(
    dem_path: Union[str, Path],
    output_tif: Union[str, Path],
    accumulation_path: Optional[Union[str, Path]] = None,
) -> str:
    """
    Computes Sediment Transport Index (STI / USLE LS 3D Factor) for soil erosion modeling.

    Scientific References:
        - Moore, I. D., & Burch, G. J. (1986). Soil Science Society of America Journal, 50(5), 1294-1298.
        - Moore, I. D., & Wilson, J. P. (1992). Journal of Soil and Water Conservation, 47(5), 423-428.

    Formula:
        STI = (a / 22.13)^0.6 * (sin(beta) / 0.0896)^1.3

    Args:
        dem_path: Input DEM GeoTIFF path.
        output_tif: Destination STI GeoTIFF path.
        accumulation_path: Optional pre-computed accumulation raster path.

    Returns:
        String path to the output STI GeoTIFF.
    """
    ensure_output_directory(output_tif)
    p_dem = Path(dem_path)
    if not p_dem.exists():
        raise FileNotFoundError(f"DEM not found: {p_dem}")

    try:
        with rasterio.open(str(p_dem)) as src:
            dem = src.read(1).astype(np.float64)
            profile = src.profile.copy()
            dx = float(src.res[0])
            dy = float(src.res[1])
            nodata = src.nodata if src.nodata is not None else -9999.0

        valid = (dem != nodata) & (~np.isnan(dem))

        # Slope
        gy, gx = np.gradient(dem, dy, dx)
        slope_rad = np.arctan(np.sqrt(gx**2 + gy**2))

        # Flow accumulation
        if accumulation_path is not None and Path(accumulation_path).exists():
            with rasterio.open(str(accumulation_path)) as asrc:
                accum = asrc.read(1).astype(np.float64)
        else:
            temp_accum = Path(output_tif).with_suffix(".sti_accum_temp.tif")
            compute_flow_accumulation(dem_path, temp_accum, units="cells")
            with rasterio.open(str(temp_accum)) as asrc:
                accum = asrc.read(1).astype(np.float64)
            if temp_accum.exists():
                temp_accum.unlink()

        specific_catchment_area = np.maximum(1.0, accum) * dx
        
        # STI = (a / 22.13)^0.6 * (sin(slope) / 0.0896)^1.3
        sti = (specific_catchment_area / 22.13) ** 0.6 * (np.maximum(1e-5, np.sin(slope_rad)) / 0.0896) ** 1.3
        sti[~valid] = -9999.0

        profile.update(dtype="float32", count=1, nodata=-9999.0)
        with rasterio.open(str(output_tif), "w", **profile) as dst:
            dst.write(sti.astype(np.float32), 1)

        return str(Path(output_tif).resolve())

    except Exception as e:
        raise ComputationError(f"Failed to compute Sediment Transport Index (STI): {e}")


def compute_landslide_susceptibility_index(
    dem_path: Union[str, Path],
    output_tif: Union[str, Path],
    slope_weight: float = 0.50,
    twi_weight: float = 0.35,
    curvature_weight: float = 0.15,
) -> str:
    """
    Computes a multi-criteria Landslide & Slope Failure Susceptibility Index (0 to 100).

    Scientific Reference:
        Montgomery, D. R., & Dietrich, W. E. (1994). "A physically based model for the topographic
        control on shallow landsliding." Water Resources Research, 30(4), 1153-1171.

    Args:
        dem_path: Input DEM GeoTIFF path.
        output_tif: Destination Landslide Susceptibility raster path (uint8 [0, 100]).
        slope_weight: Weight contribution for topographic steepness (default: 0.50).
        twi_weight: Weight contribution for moisture saturation / TWI (default: 0.35).
        curvature_weight: Weight contribution for planform convergence / hollows (default: 0.15).

    Returns:
        String path to output hazard raster.
    """
    ensure_output_directory(output_tif)
    p_dem = Path(dem_path)
    if not p_dem.exists():
        raise FileNotFoundError(f"DEM not found: {p_dem}")

    try:
        with rasterio.open(str(p_dem)) as src:
            dem = src.read(1).astype(np.float64)
            profile = src.profile.copy()
            dx = float(src.res[0])
            dy = float(src.res[1])
            nodata = src.nodata if src.nodata is not None else -9999.0

        valid = (dem != nodata) & (~np.isnan(dem))

        # 1. Slope Score (Normalized 0 to 100, peaks around 30°-45°)
        gy, gx = np.gradient(dem, dy, dx)
        slope_deg = np.rad2deg(np.arctan(np.sqrt(gx**2 + gy**2)))
        slope_score = np.clip((slope_deg / 45.0) * 100.0, 0.0, 100.0)

        # 2. TWI Score (Normalized)
        temp_twi = Path(output_tif).with_suffix(".twi_haz_temp.tif")
        compute_topographic_wetness_index(dem_path, temp_twi)
        with rasterio.open(str(temp_twi)) as tsrc:
            twi = tsrc.read(1).astype(np.float64)
        if temp_twi.exists():
            temp_twi.unlink()

        twi_valid = twi[valid & (twi > -100.0)]
        twi_min, twi_max = (np.percentile(twi_valid, 5), np.percentile(twi_valid, 95)) if len(twi_valid) > 0 else (0, 1)
        twi_norm = np.clip((twi - twi_min) / max(1e-5, twi_max - twi_min) * 100.0, 0.0, 100.0)

        # 3. Curvature Score (Laplacian / profile concavity)
        laplacian = - (np.gradient(gx, axis=1) + np.gradient(gy, axis=0))
        curv_score = np.clip((laplacian + 0.5) * 100.0, 0.0, 100.0)

        # Weighted composite score
        total_weight = slope_weight + twi_weight + curvature_weight
        composite_score = (
            (slope_weight * slope_score) +
            (twi_weight * twi_norm) +
            (curvature_weight * curv_score)
        ) / total_weight

        hazard_map = np.where(valid, np.clip(composite_score, 0.0, 100.0), 255).astype(np.uint8)

        profile.update(dtype="uint8", count=1, nodata=255)
        with rasterio.open(str(output_tif), "w", **profile) as dst:
            dst.write(hazard_map, 1)

        return str(Path(output_tif).resolve())

    except Exception as e:
        raise ComputationError(f"Failed to compute Landslide Susceptibility Index: {e}")
