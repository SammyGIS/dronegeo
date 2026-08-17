"""
dronegeo.analysis.contours
~~~~~~~~~~~~~~~~~~~~~~~~~~
Topographic contour line vector extraction (Shapefile / GeoJSON / GeoPackage) from DEM rasters.
"""

from __future__ import annotations
from pathlib import Path
from typing import Union, Optional

import numpy as np
import geopandas as gpd
from shapely.geometry import LineString
import rasterio
import matplotlib.pyplot as plt

from ..core.exceptions import RasterIOError


def generate_contour_lines(
    dem_path: Union[str, Path],
    output_vector_path: Optional[Union[str, Path]] = None,
    interval_m: float = 1.0,
    base_elevation: float = 0.0,
    min_elevation: Optional[float] = None,
    max_elevation: Optional[float] = None,
    downsample_factor: int = 1,
) -> gpd.GeoDataFrame:
    """
    Extracts survey-grade vector contour lines from an input DEM raster.

    Real-World Applications:
        - Civil Engineering & Surveying: Generating 0.5m, 1.0m, or 5.0m interval contour maps for
          direct CAD integration (AutoCAD Civil 3D, Bentley MicroStation).
        - Architectural Planning: Site slope visualization on zoning drawings.
        - Outdoor Recreation & GIS: Topographic hiking, trail, and municipal mapping.

    When to Use:
        Use whenever vector elevation contours are required from raster digital elevation models.

    Args:
        dem_path: Path to input DEM GeoTIFF.
        output_vector_path: Optional destination path to save vector file (.shp, .geojson, .gpkg).
        interval_m: Contour interval step in meters (e.g. 0.5m, 1.0m, 5.0m). Default is 1.0m.
        base_elevation: Reference base elevation from which interval steps are calculated (default: 0.0m).
        min_elevation: Optional lower elevation bound for contour extraction.
        max_elevation: Optional upper elevation bound for contour extraction.
        downsample_factor: Downsample factor for rapid contouring on massive grids (default: 1).

    Returns:
        GeoPandas GeoDataFrame containing contour LineString geometries and 'elevation' columns.

    Raises:
        FileNotFoundError: If input DEM raster does not exist on disk.
        ValueError: If interval_m <= 0.

    Example:
        >>> import dronegeo as dg
        >>> contours_gdf = dg.analysis.generate_contour_lines(
        ...     dem_path="outputs/survey_dtm.tif",
        ...     output_vector_path="outputs/contours_1m.shp",
        ...     interval_m=1.0
        ... )
        >>> print(f"Generated {len(contours_gdf):,} contour line segments.")
    """
    assert interval_m > 0, f"interval_m must be positive, got {interval_m}"
    p_in = Path(dem_path)
    assert p_in.exists(), f"Input DEM not found: {p_in}"

    ds = max(1, int(downsample_factor))

    with rasterio.open(str(p_in)) as src:
        dtm = src.read(1)[::ds, ::ds].astype(np.float32)
        nodata = float(src.nodata) if src.nodata is not None else -10000.0
        transform = src.transform
        raster_crs = src.crs
        res_x = src.res[0] * ds
        res_y = src.res[1] * ds

    valid_mask = (dtm != nodata) & (~np.isnan(dtm)) & (dtm > -500.0)
    valid_z = dtm[valid_mask]

    if len(valid_z) == 0:
        return gpd.GeoDataFrame(columns=["elevation", "geometry"], crs=raster_crs)

    z_min = float(np.min(valid_z)) if min_elevation is None else float(min_elevation)
    z_max = float(np.max(valid_z)) if max_elevation is None else float(max_elevation)

    start_level = np.ceil((z_min - base_elevation) / interval_m) * interval_m + base_elevation
    levels = np.arange(start_level, z_max + (interval_m * 0.1), interval_m)

    if len(levels) == 0:
        return gpd.GeoDataFrame(columns=["elevation", "geometry"], crs=raster_crs)

    height, width = dtm.shape
    x_coords = transform.c + (np.arange(width) + 0.5) * res_x
    y_coords = transform.f - (np.arange(height) + 0.5) * res_y

    dtm_masked = np.where(valid_mask, dtm, np.nan)

    fig, ax = plt.subplots()
    cs = ax.contour(x_coords, y_coords, dtm_masked, levels=levels)
    plt.close(fig)

    records = []
    if hasattr(cs, "allsegs"):
        for level, segs in zip(cs.levels, cs.allsegs):
            for seg in segs:
                if len(seg) >= 2:
                    records.append({
                        "elevation": float(level),
                        "geometry": LineString(seg)
                    })
    elif hasattr(cs, "collections"):
        for level, collection in zip(cs.levels, cs.collections):
            for path in collection.get_paths():
                v = path.vertices
                if len(v) >= 2:
                    records.append({
                        "elevation": float(level),
                        "geometry": LineString(v)
                    })

    gdf = gpd.GeoDataFrame(records, columns=["elevation", "geometry"], crs=raster_crs)

    if output_vector_path is not None:
        p_out = Path(output_vector_path)
        p_out.parent.mkdir(parents=True, exist_ok=True)
        driver = "GeoJSON" if p_out.suffix.lower() == ".geojson" else ("GPKG" if p_out.suffix.lower() == ".gpkg" else "ESRI Shapefile")
        gdf.to_file(str(p_out), driver=driver)

    return gdf
