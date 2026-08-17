"""
dronegeo.hydrology.flow_accumulation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Flow accumulation calculation and drainage stream network extraction.

Scientific References:
- O'Callaghan, J. F., & Mark, D. M. (1984). The extraction of drainage networks from digital elevation data.
  Computer Vision, Graphics, and Image Processing, 28(3), 323-344.
- Jenson, S. K., & Domingue, J. O. (1988). Extracting topographic structure from digital elevation data for
  geographic information system analysis. Photogrammetric Engineering and Remote Sensing, 54(11), 1593-1600.
- Tarboton, D. G., Bras, R. L., & Rodriguez-Iturbe, I. (1991). On the extraction of channel networks from
  digital elevation data. Hydrological Processes, 5(1), 81-100.
"""

from __future__ import annotations
from pathlib import Path
from typing import Union, Optional, Tuple, Dict, Any
import numpy as np
import rasterio

from ..core.exceptions import RasterIOError, ComputationError
from ..utils.file_utils import ensure_output_directory
from .flow_direction import D8_OFFSETS, compute_d8_flow_direction


def compute_flow_accumulation(
    dem_path: Union[str, Path],
    output_tif: Union[str, Path],
    flow_dir_path: Optional[Union[str, Path]] = None,
    units: str = "cells",
) -> str:
    """
    Calculates accumulated upslope contributing area for each cell in the DEM.

    Scientific References:
        - O'Callaghan & Mark (1984) / Jenson & Domingue (1988).

    Args:
        dem_path: Input elevation GeoTIFF path.
        output_tif: Output flow accumulation GeoTIFF path.
        flow_dir_path: Optional pre-computed D8 flow direction raster path.
        units: 'cells' (integer cell counts) or 'm2' (area in square meters).

    Returns:
        String path to the output accumulation GeoTIFF.
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
            cell_area = dx * dy
            nodata = src.nodata if src.nodata is not None else -9999.0

        rows, cols = dem.shape
        valid = (dem != nodata) & (~np.isnan(dem))

        # Generate or read flow direction
        if flow_dir_path is not None and Path(flow_dir_path).exists():
            with rasterio.open(str(flow_dir_path)) as fsrc:
                fdir = fsrc.read(1).astype(np.uint8)
        else:
            temp_fdir = Path(output_tif).with_suffix(".fdir_temp.tif")
            compute_d8_flow_direction(dem_path, temp_fdir)
            with rasterio.open(str(temp_fdir)) as fsrc:
                fdir = fsrc.read(1).astype(np.uint8)
            if temp_fdir.exists():
                temp_fdir.unlink()

        # Topological sorting by descending elevation
        indices = np.argsort(-dem.ravel())
        accum = np.ones((rows, cols), dtype=np.float64)

        for idx in indices:
            r, c = divmod(idx, cols)
            if not valid[r, c]:
                accum[r, c] = 0
                continue
            code = fdir[r, c]
            if code in D8_OFFSETS:
                dr, dc = D8_OFFSETS[code]
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols and valid[nr, nc]:
                    accum[nr, nc] += accum[r, c]

        accum[~valid] = -9999.0
        if units.lower() == "m2":
            accum_out = np.where(valid, accum * cell_area, -9999.0)
        else:
            accum_out = accum

        profile.update(dtype="float32", count=1, nodata=-9999.0)
        with rasterio.open(str(output_tif), "w", **profile) as dst:
            dst.write(accum_out.astype(np.float32), 1)

        return str(Path(output_tif).resolve())

    except Exception as e:
        raise ComputationError(f"Failed to compute flow accumulation: {e}")


def extract_stream_network(
    accumulation_path: Union[str, Path],
    output_tif: Union[str, Path],
    threshold_cells: int = 500,
) -> str:
    """
    Extracts binary stream channel network raster by applying an accumulation threshold.

    Scientific Reference:
        Tarboton, D. G., Bras, R. L., & Rodriguez-Iturbe, I. (1991). "On the extraction of channel networks
        from digital elevation data." Hydrological Processes, 5(1), 81-100.

    Args:
        accumulation_path: Path to flow accumulation GeoTIFF.
        output_tif: Output binary stream raster GeoTIFF path (1 = stream channel, 0 = non-channel).
        threshold_cells: Minimum number of contributing cells to initiate a channel head.

    Returns:
        String path to the output stream network raster.
    """
    ensure_output_directory(output_tif)
    with rasterio.open(str(accumulation_path)) as src:
        accum = src.read(1)
        profile = src.profile.copy()
        nodata = src.nodata if src.nodata is not None else -9999.0

    valid = (accum != nodata) & (accum >= 0)
    streams = np.zeros(accum.shape, dtype=np.uint8)
    streams[valid & (accum >= threshold_cells)] = 1

    profile.update(dtype="uint8", count=1, nodata=0)
    with rasterio.open(str(output_tif), "w", **profile) as dst:
        dst.write(streams, 1)

    return str(Path(output_tif).resolve())
