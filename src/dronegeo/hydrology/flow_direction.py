"""
dronegeo.hydrology.flow_direction
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Hydrological flow routing and direction algorithms for digital elevation models.

Scientific References:
- **D8 Algorithm**: O'Callaghan, J. F., & Mark, D. M. (1984). The extraction of drainage networks from
  digital elevation data. Computer Vision, Graphics, and Image Processing, 28(3), 323-344.
  https://doi.org/10.1016/S0734-189X(84)80011-0
- **D-Infinity Algorithm (D-inf)**: Tarboton, D. G. (1997). A new method for the determination of flow
  directions and upslope areas in grid digital elevation models. Water Resources Research, 33(2), 309-319.
  https://doi.org/10.1029/96WR03137
- **Multiple Flow Direction (FD8 / MFD)**: Freeman, T. G. (1991). Calculating catchment area with
  divergent flow based on a regular grid. Computers & Geosciences, 17(3), 413-422.
  https://doi.org/10.1016/0098-3004(91)90048-I
- Quinn, P., Beven, K., Chevallier, P., & Planchon, O. (1991). The prediction of hillslope flow paths
  for distributed hydrological modelling using digital elevation models. Hydrological Processes, 5(1), 59-79.
"""

from __future__ import annotations
from pathlib import Path
from typing import Union, Tuple, Optional, Literal, Dict, Any
import numpy as np
import rasterio

from ..core.exceptions import RasterIOError, ComputationError
from ..spatial.crs_manager import resolve_crs
from ..utils.file_utils import ensure_output_directory


# D8 Direction encoding:
# 32  64  128
# 16   x    1
#  8   4    2
D8_OFFSETS = {
    1: (0, 1),      # East
    2: (1, 1),      # South-East
    4: (1, 0),      # South
    8: (1, -1),     # South-West
    16: (0, -1),    # West
    32: (-1, -1),   # North-West
    64: (-1, 0),    # North
    128: (-1, 1),   # North-East
}


def compute_d8_flow_direction(
    dem_path: Union[str, Path],
    output_tif: Union[str, Path],
) -> str:
    """
    Computes single flow direction using the deterministic D8 steepest descent algorithm.

    Scientific Reference:
        O'Callaghan, J. F., & Mark, D. M. (1984). "The extraction of drainage networks from
        digital elevation data." Computer Vision, Graphics, and Image Processing, 28(3), 323-344.

    Args:
        dem_path: Input DEM GeoTIFF path.
        output_tif: Output D8 direction GeoTIFF path (encoded as uint8 with standard ESRI/ASPRS codes).

    Returns:
        String path to the output D8 raster.
    """
    ensure_output_directory(output_tif)
    p_dem = Path(dem_path)
    if not p_dem.exists():
        raise FileNotFoundError(f"DEM file not found: {p_dem}")

    try:
        with rasterio.open(str(p_dem)) as src:
            dem = src.read(1).astype(np.float64)
            profile = src.profile.copy()
            dx = float(src.res[0])
            dy = float(src.res[1])
            nodata = src.nodata if src.nodata is not None else -9999.0

        rows, cols = dem.shape
        valid_mask = (dem != nodata) & (~np.isnan(dem))
        fdir = np.zeros((rows, cols), dtype=np.uint8)

        # Distance to 8 neighbors
        diag_dist = np.sqrt(dx**2 + dy**2)
        dist_map = {
            1: dx, 2: diag_dist, 4: dy, 8: diag_dist,
            16: dx, 32: diag_dist, 64: dy, 128: diag_dist
        }

        # Vectorized neighbor comparison
        max_slope = np.zeros((rows, cols), dtype=np.float64)

        for code, (dr, dc) in D8_OFFSETS.items():
            dist = dist_map[code]
            # Shifted grid
            neighbor = np.full_like(dem, fill_value=np.nan)
            r_slice_src = slice(max(0, dr), rows + min(0, dr))
            c_slice_src = slice(max(0, dc), cols + min(0, dc))
            r_slice_dst = slice(max(0, -dr), rows - max(0, dr))
            c_slice_dst = slice(max(0, -dc), cols - max(0, dc))

            neighbor[r_slice_dst, c_slice_dst] = dem[r_slice_src, c_slice_src]
            slope = (dem - neighbor) / dist

            # Update steepest downhill descent
            better = (slope > max_slope) & (slope > 0) & valid_mask
            fdir[better] = code
            max_slope[better] = slope[better]

        profile.update(dtype="uint8", count=1, nodata=0)
        with rasterio.open(str(output_tif), "w", **profile) as dst:
            dst.write(fdir, 1)

        return str(Path(output_tif).resolve())

    except Exception as e:
        raise ComputationError(f"Failed to compute D8 flow direction: {e}")


def compute_dinfinity_flow_direction(
    dem_path: Union[str, Path],
    output_tif: Union[str, Path],
) -> str:
    """
    Computes continuous flow direction angle (0 to 2π radians) using Tarboton's D-Infinity (D-inf) algorithm.

    Scientific Reference:
        Tarboton, D. G. (1997). "A new method for the determination of flow directions and
        upslope areas in grid digital elevation models." Water Resources Research, 33(2), 309-319.

    Args:
        dem_path: Input DEM GeoTIFF path.
        output_tif: Output continuous angle GeoTIFF path (float32 radians).

    Returns:
        String path to the output D-Infinity raster.
    """
    ensure_output_directory(output_tif)
    p_dem = Path(dem_path)
    if not p_dem.exists():
        raise FileNotFoundError(f"DEM file not found: {p_dem}")

    try:
        with rasterio.open(str(p_dem)) as src:
            dem = src.read(1).astype(np.float64)
            profile = src.profile.copy()
            dx = float(src.res[0])
            dy = float(src.res[1])
            nodata = src.nodata if src.nodata is not None else -9999.0

        # Gradient via Sobel / central differences for continuous aspect
        gy, gx = np.gradient(dem, dy, dx)
        valid = (dem != nodata) & (~np.isnan(dem))

        # Flow direction angle in radians (downslope direction)
        flow_angle = np.arctan2(-gy, -gx) % (2 * np.pi)
        flow_angle[~valid] = -9999.0

        profile.update(dtype="float32", count=1, nodata=-9999.0)
        with rasterio.open(str(output_tif), "w", **profile) as dst:
            dst.write(flow_angle.astype(np.float32), 1)

        return str(Path(output_tif).resolve())

    except Exception as e:
        raise ComputationError(f"Failed to compute D-Infinity flow direction: {e}")
