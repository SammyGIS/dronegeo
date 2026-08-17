"""
dronegeo.analysis.morphology
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Analytical Hillshade, Slope gradient (degrees/percent), Aspect, and Terrain Ruggedness Index (TRI).
"""

from __future__ import annotations
from pathlib import Path
from typing import Union, Optional, Literal

import numpy as np
import scipy.ndimage as ndi
import rasterio

from ..core.exceptions import RasterIOError


def generate_hillshade(
    dem_path: Union[str, Path],
    output_tif: Union[str, Path],
    azimuth_deg: float = 315.0,
    altitude_deg: float = 45.0,
    z_factor: float = 1.0,
) -> str:
    """
    Generates a survey-grade analytical 8-bit Hillshade GeoTIFF from an input DEM.

    Real-World Applications:
        - Geomorphology & Geology: Revealing fault lines, geologic bedding planes, and drainage channels.
        - High-Impact Mapping: Creating 3D relief background basemaps for drone survey deliverables.
        - Hazard Mapping: Identifying rockfall corridors and steep slope scarps.

    When to Use:
        Use to visually enhance subtle terrain features by simulating sun illumination across the landscape.

    Math Formulation:
        - Horn's gradient method with photometric shading:
          Shaded = sin(altitude) * cos(slope) + cos(altitude) * sin(slope) * cos(azimuth - aspect)

    Args:
        dem_path: Path to input DEM GeoTIFF.
        output_tif: Target 8-bit uint8 Hillshade GeoTIFF destination path.
        azimuth_deg: Sun azimuth illumination angle in degrees (0° = North, 90° = East, default: 315° NW).
        altitude_deg: Sun elevation/altitude angle above the horizon in degrees (default: 45°).
        z_factor: Vertical exaggeration factor (default: 1.0).

    Returns:
        Absolute string path to the created Hillshade GeoTIFF.

    Raises:
        FileNotFoundError: If input DEM does not exist on disk.

    Example:
        >>> import dronegeo as dg
        >>> hillshade_path = dg.analysis.generate_hillshade(
        ...     dem_path="dtm.tif",
        ...     output_tif="hillshade.tif",
        ...     azimuth_deg=315.0,
        ...     altitude_deg=45.0
        ... )
    """
    p_in = Path(dem_path)
    p_out = Path(output_tif)
    assert p_in.exists(), f"Input DEM not found: {p_in}"
    assert 0.0 <= azimuth_deg <= 360.0, f"azimuth_deg must be in [0, 360], got {azimuth_deg}"
    assert 0.0 < altitude_deg <= 90.0, f"altitude_deg must be in (0, 90], got {altitude_deg}"

    p_out.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.open(str(p_in)) as src:
        dtm = src.read(1).astype(np.float32)
        nodata = float(src.nodata) if src.nodata is not None else -10000.0
        res_x, res_y = src.res
        meta = src.meta.copy()

    valid_mask = (dtm != nodata) & (~np.isnan(dtm)) & (dtm > -500.0)

    gy, gx = np.gradient(dtm)
    gx = (gx * z_factor) / res_x
    gy = (gy * z_factor) / res_y

    slope_rad = np.arctan(np.sqrt(gx**2 + gy**2))
    aspect_rad = np.arctan2(-gx, gy)

    azimuth_rad = np.radians(360.0 - azimuth_deg + 90.0)
    altitude_rad = np.radians(altitude_deg)

    shaded = (
        np.sin(altitude_rad) * np.cos(slope_rad) +
        np.cos(altitude_rad) * np.sin(slope_rad) * np.cos(azimuth_rad - aspect_rad)
    )

    hillshade_255 = np.where(valid_mask, np.clip(254.0 * shaded, 1.0, 255.0), 0).astype(np.uint8)
    del dtm, gx, gy, slope_rad, aspect_rad, shaded

    meta.update({
        'count': 1,
        'dtype': 'uint8',
        'nodata': 0,
        'compress': 'lzw',
    })

    with rasterio.open(str(p_out), "w", **meta) as dst:
        dst.write(hillshade_255, 1)

    del hillshade_255
    assert p_out.exists() and p_out.stat().st_size > 0, f"Failed to write Hillshade: {p_out}"
    return str(p_out)


def generate_slope_map(
    dem_path: Union[str, Path],
    output_tif: Union[str, Path],
    units: Literal["degrees", "percent"] = "degrees",
) -> str:
    """
    Computes a continuous topographic Slope map GeoTIFF.

    Real-World Applications:
        - Civil Infrastructure: Identifying steep road grades exceeding engineering limits (>12%).
        - Solar Farm Engineering: Selecting terrain slopes suitable for solar tracking arrays (<5°).
        - Landslide Hazard: Delineating steep slope thresholds (>35°) prone to slope failure.

    When to Use:
        Use when assessing terrain steepness for construction, drainage, or slope stability.

    Args:
        dem_path: Path to input DEM GeoTIFF.
        output_tif: Target float32 Slope GeoTIFF destination path.
        units: "degrees" (0° to 90°) or "percent" (rise over run * 100). Default is 'degrees'.

    Returns:
        Absolute string path to the created Slope GeoTIFF.

    Example:
        >>> import dronegeo as dg
        >>> slope_path = dg.analysis.generate_slope_map("dtm.tif", "slope_degrees.tif", units="degrees")
    """
    p_in = Path(dem_path)
    p_out = Path(output_tif)
    assert p_in.exists(), f"Input DEM not found: {p_in}"

    p_out.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.open(str(p_in)) as src:
        dtm = src.read(1).astype(np.float32)
        nodata = float(src.nodata) if src.nodata is not None else -10000.0
        res_x, res_y = src.res
        meta = src.meta.copy()

    valid_mask = (dtm != nodata) & (~np.isnan(dtm)) & (dtm > -500.0)

    gy, gx = np.gradient(dtm)
    gx = gx / res_x
    gy = gy / res_y
    slope_rad = np.arctan(np.sqrt(gx**2 + gy**2))

    if units == "percent":
        slope_val = np.tan(slope_rad) * 100.0
    else:
        slope_val = np.degrees(slope_rad)

    slope_out = np.where(valid_mask, slope_val, -10000.0).astype(np.float32)
    del dtm, gx, gy, slope_rad, slope_val

    meta.update({
        'count': 1,
        'dtype': 'float32',
        'nodata': -10000.0,
        'compress': 'lzw',
    })

    with rasterio.open(str(p_out), "w", **meta) as dst:
        dst.write(slope_out, 1)

    del slope_out
    assert p_out.exists() and p_out.stat().st_size > 0, f"Failed to write Slope map: {p_out}"
    return str(p_out)


def generate_aspect_map(
    dem_path: Union[str, Path],
    output_tif: Union[str, Path],
) -> str:
    """
    Computes a continuous Aspect map GeoTIFF representing the compass direction of maximum slope (0° to 360°).

    Real-World Applications:
        - Solar Energy: Orienting solar panels toward optimal solar azimuth (South-facing in Northern hemisphere).
        - Agriculture & Viticulture: Analyzing vineyard hillside aspect and micro-climates.
        - Snowpack & Hydrology: Modeling snowmelt rates on North vs. South-facing mountain slopes.

    When to Use:
        Use when terrain orientation with respect to compass directions is needed.

    Args:
        dem_path: Path to input DEM GeoTIFF.
        output_tif: Target float32 Aspect GeoTIFF destination path.

    Returns:
        Absolute string path to the created Aspect GeoTIFF.

    Example:
        >>> import dronegeo as dg
        >>> aspect_path = dg.analysis.generate_aspect_map("dtm.tif", "aspect.tif")
    """
    p_in = Path(dem_path)
    p_out = Path(output_tif)
    assert p_in.exists(), f"Input DEM not found: {p_in}"

    p_out.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.open(str(p_in)) as src:
        dtm = src.read(1).astype(np.float32)
        nodata = float(src.nodata) if src.nodata is not None else -10000.0
        res_x, res_y = src.res
        meta = src.meta.copy()

    valid_mask = (dtm != nodata) & (~np.isnan(dtm)) & (dtm > -500.0)

    gy, gx = np.gradient(dtm)
    gx = gx / res_x
    gy = gy / res_y

    aspect_rad = np.arctan2(-gx, gy)
    aspect_deg = np.degrees(aspect_rad)
    aspect_compass = np.where(aspect_deg < 0, aspect_deg + 360.0, aspect_deg)

    aspect_out = np.where(valid_mask, aspect_compass, -10000.0).astype(np.float32)
    del dtm, gx, gy, aspect_rad, aspect_deg, aspect_compass

    meta.update({
        'count': 1,
        'dtype': 'float32',
        'nodata': -10000.0,
        'compress': 'lzw',
    })

    with rasterio.open(str(p_out), "w", **meta) as dst:
        dst.write(aspect_out, 1)

    del aspect_out
    assert p_out.exists() and p_out.stat().st_size > 0, f"Failed to write Aspect map: {p_out}"
    return str(p_out)


def generate_terrain_ruggedness_index(
    dem_path: Union[str, Path],
    output_tif: Union[str, Path],
) -> str:
    """
    Computes the Riley Terrain Ruggedness Index (TRI) representing local topographic roughness.

    Real-World Applications:
        - Ecological Wildlife Modeling: Habitat suitability modeling based on surface ruggedness.
        - Off-Road Mobility: Vehicle trafficability and ground obstacle navigation.

    When to Use:
        Use when quantifying surface heterogeneity and micro-topographic roughness.

    Args:
        dem_path: Path to input DEM GeoTIFF.
        output_tif: Target float32 TRI GeoTIFF destination path.

    Returns:
        Absolute string path to the created TRI GeoTIFF.

    Example:
        >>> import dronegeo as dg
        >>> tri_path = dg.analysis.generate_terrain_ruggedness_index("dtm.tif", "ruggedness_tri.tif")
    """
    p_in = Path(dem_path)
    p_out = Path(output_tif)
    assert p_in.exists(), f"Input DEM not found: {p_in}"

    p_out.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.open(str(p_in)) as src:
        dtm = src.read(1).astype(np.float32)
        nodata = float(src.nodata) if src.nodata is not None else -10000.0
        meta = src.meta.copy()

    valid_mask = (dtm != nodata) & (~np.isnan(dtm)) & (dtm > -500.0)

    mean_dtm = ndi.uniform_filter(dtm, size=3, mode='reflect')
    diff_sq = (dtm - mean_dtm)**2
    tri = np.sqrt(ndi.uniform_filter(diff_sq, size=3, mode='reflect'))

    tri_out = np.where(valid_mask, tri, -10000.0).astype(np.float32)
    del dtm, mean_dtm, diff_sq, tri

    meta.update({
        'count': 1,
        'dtype': 'float32',
        'nodata': -10000.0,
        'compress': 'lzw',
    })

    with rasterio.open(str(p_out), "w", **meta) as dst:
        dst.write(tri_out, 1)

    del tri_out
    assert p_out.exists() and p_out.stat().st_size > 0, f"Failed to write TRI map: {p_out}"
    return str(p_out)
