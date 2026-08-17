"""
dronegeo.profiling.grid_tiling
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Spatial vector grid overlay, tile chip mapping, and centroid ID annotation.
"""

from __future__ import annotations
from pathlib import Path
from typing import Union, Optional

import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
import matplotlib.pyplot as plt
import matplotlib.patheffects as PathEffects

from ..core.exceptions import RasterIOError


def map_grid_chips(
    dem_path: Union[str, Path],
    grid_vector_path: Union[str, Path],
    output_png: Union[str, Path],
    label_column: str = "id",
    downsample_factor: int = 4,
    title: Optional[str] = None,
    colormap: str = "terrain",
) -> str:
    """
    Renders a spatial indexing map overlaying survey tile grid polygons on a DEM raster.

    Automatically aligns CRS between vector and raster layers and annotates each grid
    tile's centroid with its ID.

    Args:
        dem_path: Path to input DEM GeoTIFF.
        grid_vector_path: Path to Shapefile (.shp) or GeoJSON survey grid polygons.
        output_png: Destination path for saved PNG map.
        label_column: Name of the attribute column for chip IDs (default: 'id').
        downsample_factor: Downsample factor for fast high-resolution rendering (default: 4).
        title: Optional custom plot title.
        colormap: Matplotlib colormap for raster elevation (default: 'terrain').

    Returns:
        Absolute string path to the saved PNG map.

    Raises:
        FileNotFoundError: If input DEM or vector file does not exist.

    Example:
        >>> import dronegeo as dg
        >>> map_file = dg.profiling.map_grid_chips(
        ...     dem_path="outputs/survey_dtm.tif",
        ...     grid_vector_path="data/survey_grid.shp",
        ...     output_png="outputs/grid_chips_overview.png",
        ...     label_column="id"
        ... )
    """
    dem_p = Path(dem_path)
    grid_p = Path(grid_vector_path)
    out_p = Path(output_png)

    assert dem_p.exists(), f"DEM raster not found: {dem_p}"
    assert grid_p.exists(), f"Grid vector file not found: {grid_p}"

    out_p.parent.mkdir(parents=True, exist_ok=True)

    try:
        grid_gdf = gpd.read_file(str(grid_p))
    except Exception as e:
        raise RasterIOError(f"Failed to read grid vector file: {grid_p}", details=str(e))

    try:
        with rasterio.open(str(dem_p)) as src:
            ds = max(1, int(downsample_factor))
            data = src.read(
                1,
                out_shape=(
                    src.count,
                    int(src.height // ds),
                    int(src.width // ds)
                )
            )
            nodata = float(src.nodata) if src.nodata is not None else -10000.0
            extent = [src.bounds.left, src.bounds.right, src.bounds.bottom, src.bounds.top]
            raster_crs = src.crs
    except Exception as e:
        raise RasterIOError(f"Failed to read DEM raster: {dem_p}", details=str(e))

    if grid_gdf.crs != raster_crs and raster_crs is not None:
        grid_gdf = grid_gdf.to_crs(raster_crs)

    if nodata is not None:
        data = np.ma.masked_equal(data, nodata)

    fig, ax = plt.subplots(figsize=(14, 12), dpi=200)

    im = ax.imshow(data, cmap=colormap, extent=extent, origin="upper")
    cbar = plt.colorbar(im, ax=ax, shrink=0.75, pad=0.03)
    cbar.set_label("Elevation (meters)", fontsize=12, fontweight="bold")

    grid_gdf.boundary.plot(ax=ax, color="#E63946", linewidth=1.8, linestyle="-", label="Grid Tile Boundary")

    txt_effects = [PathEffects.withStroke(linewidth=3, foreground="white")]
    tile_count = 0

    for idx, row in grid_gdf.iterrows():
        if label_column in row and not pd.isnull(row[label_column]):
            try:
                tile_id = f"{int(row[label_column])}"
            except Exception:
                tile_id = str(row[label_column])
        else:
            tile_id = str(idx + 1)

        centroid = row["geometry"].centroid
        ax.text(
            centroid.x, centroid.y, tile_id,
            color="#1D3557",
            fontsize=11,
            fontweight="bold",
            ha="center",
            va="center",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="#F1FAEE", edgecolor="#E63946", alpha=0.9),
            path_effects=txt_effects
        )
        tile_count += 1

    ax.set_title(
        title or f"Raster Grid Chips Location Map - {dem_p.stem} ({tile_count} Chips)",
        fontsize=15, fontweight="bold", pad=12
    )
    ax.set_xlabel("UTM Easting (X - meters)", fontsize=11)
    ax.set_ylabel("UTM Northing (Y - meters)", fontsize=11)
    ax.grid(True, linestyle=":", alpha=0.4, color="gray")

    plt.tight_layout()
    fig.savefig(out_p, dpi=200, bbox_inches="tight")
    plt.close(fig)

    assert out_p.exists() and out_p.stat().st_size > 0, f"Failed to save grid chips map: {out_p}"
    return str(out_p)
