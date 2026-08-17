"""
dronegeo.spatial.crs_manager
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
CRS resolution, projection validation, and PROJ library environment bindings.
"""

from __future__ import annotations
import os
from pathlib import Path
from typing import Union, Optional, Tuple, Dict, Any

import rasterio
from rasterio.crs import CRS
import laspy

from ..core.exceptions import SpatialReferenceError


def bind_proj_environment() -> Optional[str]:
    """
    Safely binds PROJ environment variables to pyproj / rasterio internal proj_data directory.

    Real-World Applications:
        - Windows / Conda / PostgreSQL / PostGIS Systems: Prevents classic GDAL/PROJ DLL path lookup failures
          where system PROJ_LIB points to external incompatible PROJ database versions.

    When to Use:
        Executed automatically upon package import. Can also be called manually in custom scripts.

    Returns:
        The bound PROJ data directory path as a string, or None if not found.
    """
    # 1. First priority: Python's active pyproj bundled database
    try:
        import pyproj.datadir
        p_dir = pyproj.datadir.get_data_dir()
        if p_dir and os.path.exists(p_dir):
            os.environ["PROJ_DATA"] = p_dir
            os.environ["PROJ_LIB"] = p_dir
            return p_dir
    except Exception:
        pass

    # 2. Second priority: rasterio proj_data
    try:
        proj_dir = str(Path(rasterio.__file__).parent / "proj_data")
        if os.path.exists(proj_dir):
            os.environ["PROJ_DATA"] = proj_dir
            os.environ["PROJ_LIB"] = proj_dir
            return proj_dir
    except Exception:
        pass

    return None


# Execute PROJ environment binding automatically upon module import
bind_proj_environment()


def resolve_crs(
    crs_input: Optional[Union[str, int, CRS, Path]] = None,
    prj_file: Optional[Union[str, Path]] = None,
    default_epsg: int = 32632,
) -> CRS:
    """
    Resolves a coordinate reference system into a valid Rasterio CRS object from various inputs:
    - EPSG integer code (e.g. 32632 for WGS84 / UTM Zone 32N)
    - EPSG string (e.g. "EPSG:32632")
    - Path to an ESRI/WKT .prj file (e.g. "data/survey.prj")
    - Existing rasterio.crs.CRS object

    Real-World Applications:
        - Survey Data Ingestion: Standardizing coordinate reference systems from drone RTK base stations,
          CAD project files (.prj), or global EPSG codes.

    When to Use:
        Use whenever setting or validating target coordinate systems for GeoTIFF rasters or vector contours.

    Args:
        crs_input: Optional CRS specification (integer EPSG, string, Path, or CRS).
        prj_file: Optional path to a .prj file.
        default_epsg: Fallback EPSG code if no CRS is specified (default: 32632 for UTM 32N).

    Returns:
        A rasterio.crs.CRS instance.

    Raises:
        SpatialReferenceError: If a specified CRS string or WKT file cannot be parsed.

    Example:
        >>> import dronegeo as dg
        >>> crs = dg.spatial.resolve_crs(32632)
        >>> print(f"Resolved CRS: {crs.to_string()}")
    """
    bind_proj_environment()

    if prj_file is not None:
        prj_path = Path(prj_file)
        if prj_path.exists():
            wkt_text = prj_path.read_text().strip()
            if wkt_text:
                try:
                    return CRS.from_wkt(wkt_text)
                except Exception as e:
                    raise SpatialReferenceError(f"Failed to parse .prj file: {prj_path}", details=str(e))

    if crs_input is None:
        return CRS.from_epsg(default_epsg)

    if isinstance(crs_input, CRS):
        return crs_input

    if isinstance(crs_input, int):
        try:
            return CRS.from_epsg(crs_input)
        except Exception as e:
            raise SpatialReferenceError(f"Invalid EPSG code: {crs_input}", details=str(e))

    if isinstance(crs_input, (str, Path)):
        p = Path(crs_input)
        if p.exists() and p.suffix.lower() == ".prj":
            wkt_text = p.read_text().strip()
            try:
                return CRS.from_wkt(wkt_text)
            except Exception as e:
                raise SpatialReferenceError(f"Failed to parse .prj file: {p}", details=str(e))

        str_val = str(crs_input).strip()
        if str_val.upper().startswith("EPSG:"):
            try:
                code = int(str_val.split(":")[1])
                return CRS.from_epsg(code)
            except Exception as e:
                raise SpatialReferenceError(f"Invalid EPSG string: {str_val}", details=str(e))
        elif str_val.isdigit():
            try:
                return CRS.from_epsg(int(str_val))
            except Exception as e:
                raise SpatialReferenceError(f"Invalid EPSG code: {str_val}", details=str(e))
        else:
            try:
                return CRS.from_user_input(str_val)
            except Exception:
                return CRS.from_epsg(default_epsg)

    return CRS.from_epsg(default_epsg)


def get_spatial_bounds_from_las(las_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Reads header spatial extents from a LAS/LAZ point cloud without loading full point arrays.

    Real-World Applications:
        - Fast Pre-Flight Check: Inspecting bounding coordinates and point totals in milliseconds
          without loading multi-gigabyte point arrays into RAM.

    Args:
        las_path: Path to the LAS/LAZ file.

    Returns:
        Dictionary containing point count, min/max for X, Y, Z, scales, offsets, and version.

    Raises:
        FileNotFoundError: If input LAS file does not exist.

    Example:
        >>> import dronegeo as dg
        >>> bounds = dg.spatial.get_spatial_bounds_from_las("survey.laz")
        >>> print(f"Point count: {bounds['point_count']:,}, X bounds: [{bounds['min_x']}, {bounds['max_x']}]")
    """
    path = Path(las_path)
    assert path.exists(), f"LAS file not found: {path}"

    with laspy.open(str(path)) as reader:
        h = reader.header
        return {
            "point_count": int(h.point_count),
            "min_x": float(h.mins[0]),
            "max_x": float(h.maxs[0]),
            "min_y": float(h.mins[1]),
            "max_y": float(h.maxs[1]),
            "min_z": float(h.mins[2]),
            "max_z": float(h.maxs[2]),
            "scale": [float(s) for s in h.scales],
            "offset": [float(o) for o in h.offsets],
            "version": f"{h.version.major}.{h.version.minor}",
            "point_format_id": int(h.point_format.id),
        }


def get_spatial_bounds_from_raster(raster_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Reads spatial bounds, resolution, and CRS metadata from a GeoTIFF raster.

    Args:
        raster_path: Path to the GeoTIFF raster file.

    Returns:
        Dictionary containing bounds, resolution, width, height, and CRS.

    Raises:
        FileNotFoundError: If input raster file does not exist.

    Example:
        >>> import dronegeo as dg
        >>> info = dg.spatial.get_spatial_bounds_from_raster("survey_dtm.tif")
        >>> print(f"Resolution: {info['res_x']}m, Dimensions: {info['width']}x{info['height']}")
    """
    path = Path(raster_path)
    assert path.exists(), f"Raster file not found: {path}"

    with rasterio.open(str(path)) as src:
        b = src.bounds
        return {
            "min_x": float(b.left),
            "max_x": float(b.right),
            "min_y": float(b.bottom),
            "max_y": float(b.top),
            "res_x": float(src.res[0]),
            "res_y": float(src.res[1]),
            "width": int(src.width),
            "height": int(src.height),
            "crs": src.crs.to_string() if src.crs else None,
            "nodata": float(src.nodata) if src.nodata is not None else None,
        }
