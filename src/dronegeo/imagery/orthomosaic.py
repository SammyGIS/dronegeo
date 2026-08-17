"""
dronegeo.imagery.orthomosaic
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
True-Color RGB/RGBA Orthomosaic rasterization, gap infilling, and photometric contrast enhancement.
"""

from __future__ import annotations
from pathlib import Path
from typing import Union, Optional, Tuple, Callable

import numpy as np
import scipy.ndimage as ndi
import rasterio
from rasterio.transform import from_origin
from rasterio.crs import CRS
import laspy

from ..config.compute import ComputeConfig, get_compute_config, collect_garbage_if_needed
from ..spatial.crs_manager import resolve_crs
from ..core.base import BaseSurfaceGenerator
from ..core.exceptions import MissingDimensionError, EmptyPointCloudError, RasterIOError
from ..dem.boundary_extraction import extract_flight_footprint_mask


class RGBOrthomosaicGenerator(BaseSurfaceGenerator):
    """
    Pix4D-grade True-Color Orthomosaic Generator from aerial point clouds.

    Real-World Applications:
        - Cadastral & Land Titling: Survey-grade photographic basemaps with accurate spatial coordinates.
        - Construction Quality Control: High-resolution visual inspection orthomosaics for milestone tracking.
        - Infrastructure & Utility Surveys: Corridor inspection maps for pipelines and power transmission lines.

    When to Use:
        Use when generating photographic true-color visual orthomosaics from colorized drone point clouds.

    Attributes:
        resolution: Ground Sampling Distance (GSD) / pixel resolution in meters (default: 0.10m).
        footprint_buffer: Boundary buffer distance in meters for flight footprint clipping.
        alpha_channel: If True, writes 4-band RGBA GeoTIFF where Band 4 is binary alpha transparency.
        auto_contrast: If True, applies 2%-98% cumulative histogram stretch to brighten natural shadows.
        crs: Target Coordinate Reference System.
        config: ComputeConfig instance.

    Example:
        >>> from dronegeo.imagery import RGBOrthomosaicGenerator
        >>> generator = RGBOrthomosaicGenerator(resolution=0.08, alpha_channel=True, auto_contrast=True)
        >>> ortho_tif = generator.generate("data/colorized_cloud.laz", "outputs/orthomosaic.tif")
    """

    def __init__(
        self,
        resolution: float = 0.10,
        footprint_buffer: float = 3.0,
        alpha_channel: bool = True,
        auto_contrast: bool = False,
        crs: Optional[Union[str, int, CRS, Path]] = None,
        config: Optional[ComputeConfig] = None,
    ):
        super().__init__(resolution=resolution, footprint_buffer=footprint_buffer, config=config)
        self.alpha_channel = alpha_channel
        self.auto_contrast = auto_contrast
        self.crs = crs

    def generate(
        self,
        las_path: Union[str, Path],
        output_path: Union[str, Path],
        progress_callback: Optional[Callable[[str], None]] = None,
        **kwargs
    ) -> str:
        return create_true_color_orthomosaic(
            las_path=las_path,
            output_tif=output_path,
            resolution=self.resolution,
            footprint_buffer=self.footprint_buffer,
            alpha_channel=self.alpha_channel,
            auto_contrast=self.auto_contrast,
            crs=self.crs,
            progress_callback=progress_callback,
            config=self.config,
        )


def create_true_color_orthomosaic(
    las_path: Union[str, Path],
    output_tif: Union[str, Path],
    resolution: float = 0.10,
    footprint_buffer: float = 3.0,
    alpha_channel: bool = False,
    auto_contrast: bool = False,
    crs: Optional[Union[str, int, CRS, Path]] = None,
    progress_callback: Optional[Callable[[str], None]] = None,
    config: Optional[ComputeConfig] = None,
) -> str:
    """
    Rasterizes point cloud Red/Green/Blue color attributes into a survey-grade true-color orthomosaic GeoTIFF.

    Real-World Applications:
        - Urban Planning & Engineering: Orthorectified basemaps for municipal GIS databases.
        - Precision Agriculture: Visual crop canopy basemaps for index overlay.
        - Environmental Assessment: Coastal zone monitoring and vegetation mapping.

    When to Use:
        Use when creating 3-band RGB or 4-band RGBA (with alpha transparency) GeoTIFF orthomosaics
        from aerial drone point clouds.

    Args:
        las_path: Path to colorized LAS/LAZ point cloud.
        output_tif: Target GeoTIFF destination path.
        resolution: Ground Sampling Distance (GSD) / pixel resolution in meters (default: 0.10m).
        footprint_buffer: Outer boundary buffer in meters (default: 3.0m).
        alpha_channel: If True, writes a 4-band RGBA GeoTIFF where Band 4 is the alpha transparency mask.
        auto_contrast: If True, performs 2%-98% cumulative histogram stretching for enhanced dynamic range.
        crs: Coordinate Reference System specification.
        progress_callback: Optional status message callback fn(msg).
        config: Optional ComputeConfig instance.

    Returns:
        Absolute string path to the created orthomosaic GeoTIFF.

    Raises:
        FileNotFoundError: If input LAS file does not exist on disk.
        EmptyPointCloudError: If point cloud contains 0 points.
        MissingDimensionError: If point cloud does not contain Red/Green/Blue color attributes.

    Example:
        >>> import dronegeo as dg
        >>> ortho_path = dg.imagery.create_true_color_orthomosaic(
        ...     las_path="survey_flight.laz",
        ...     output_tif="survey_ortho.tif",
        ...     resolution=0.08,
        ...     alpha_channel=True,
        ...     auto_contrast=True
        ... )
    """
    assert resolution > 0, f"resolution must be positive, got {resolution}"
    assert footprint_buffer >= 0, f"footprint_buffer must be >= 0, got {footprint_buffer}"

    cfg = config or get_compute_config()
    p_in = Path(las_path)
    p_out = Path(output_tif)

    assert p_in.exists(), f"LAS file not found: {p_in}"
    p_out.parent.mkdir(parents=True, exist_ok=True)
    target_crs = resolve_crs(crs)

    if progress_callback:
        progress_callback("Extracting concave hull footprint boundary...")

    fp, (height, width), (min_x, max_x, min_y, max_y) = extract_flight_footprint_mask(
        p_in, pixel_res=resolution, buffer_distance=footprint_buffer, config=cfg
    )
    assert height > 0 and width > 0, f"Invalid raster dimensions: {height}x{width}"
    transform = from_origin(min_x, max_y, resolution, resolution)

    r_grid = np.zeros((height, width), dtype=np.float32)
    g_grid = np.zeros((height, width), dtype=np.float32)
    b_grid = np.zeros((height, width), dtype=np.float32)
    count_grid = np.zeros((height, width), dtype=np.uint32)

    if progress_callback:
        progress_callback("Streaming point cloud color channels...")

    with laspy.open(str(p_in)) as reader:
        total_pts = int(reader.header.point_count)
        if total_pts == 0:
            raise EmptyPointCloudError(f"Point cloud contains zero points: {p_in}")

        dim_names = [d.name for d in reader.header.point_format.dimensions]
        if not ("red" in dim_names and "green" in dim_names and "blue" in dim_names):
            raise MissingDimensionError(
                f"Point cloud {p_in.name} missing Red/Green/Blue color dimensions. Available: {dim_names}",
                details={"available_dimensions": dim_names}
            )

        for chunk in reader.chunk_iterator(cfg.chunk_size):
            cx = np.array(chunk.x, dtype=np.float64)
            cy = np.array(chunk.y, dtype=np.float64)
            cr = np.array(chunk.red, dtype=np.float32)
            cg = np.array(chunk.green, dtype=np.float32)
            cb = np.array(chunk.blue, dtype=np.float32)

            if np.max(cr) > 255.0 or np.max(cg) > 255.0 or np.max(cb) > 255.0:
                cr = cr / 256.0
                cg = cg / 256.0
                cb = cb / 256.0

            cols = np.clip(((cx - min_x) / resolution).astype(int), 0, width - 1)
            rows = np.clip(((max_y - cy) / resolution).astype(int), 0, height - 1)
            idx = rows * width + cols

            np.add.at(r_grid.ravel(), idx, cr)
            np.add.at(g_grid.ravel(), idx, cg)
            np.add.at(b_grid.ravel(), idx, cb)
            np.add.at(count_grid.ravel(), idx, 1)

    valid_cells = count_grid > 0
    r_grid[valid_cells] /= count_grid[valid_cells]
    g_grid[valid_cells] /= count_grid[valid_cells]
    b_grid[valid_cells] /= count_grid[valid_cells]
    del count_grid

    missing_interior = fp & (~valid_cells)
    if np.any(missing_interior):
        ind = ndi.distance_transform_edt(~valid_cells, return_distances=False, return_indices=True)
        r_grid[missing_interior] = r_grid[tuple(ind)][missing_interior]
        g_grid[missing_interior] = g_grid[tuple(ind)][missing_interior]
        b_grid[missing_interior] = b_grid[tuple(ind)][missing_interior]

    if auto_contrast:
        r_grid = enhance_orthomosaic_contrast(r_grid, mask=fp)
        g_grid = enhance_orthomosaic_contrast(g_grid, mask=fp)
        b_grid = enhance_orthomosaic_contrast(b_grid, mask=fp)

    r_out = np.where(fp, np.clip(r_grid, 0, 255), 0).astype(np.uint8)
    g_out = np.where(fp, np.clip(g_grid, 0, 255), 0).astype(np.uint8)
    b_out = np.where(fp, np.clip(b_grid, 0, 255), 0).astype(np.uint8)
    del r_grid, g_grid, b_grid

    band_count = 4 if alpha_channel else 3

    meta = {
        'driver': 'GTiff',
        'height': height,
        'width': width,
        'count': band_count,
        'dtype': 'uint8',
        'crs': target_crs,
        'transform': transform,
        'nodata': 0 if not alpha_channel else None,
        'compress': 'lzw',
    }

    with rasterio.open(str(p_out), "w", **meta) as dst:
        dst.write(r_out, 1)
        dst.write(g_out, 2)
        dst.write(b_out, 3)
        if alpha_channel:
            alpha_band = np.where(fp, 255, 0).astype(np.uint8)
            dst.write(alpha_band, 4)
            del alpha_band

    del r_out, g_out, b_out, fp
    collect_garbage_if_needed(cfg)

    assert p_out.exists() and p_out.stat().st_size > 0, f"Failed to write orthomosaic: {p_out}"
    return str(p_out)


def enhance_orthomosaic_contrast(
    band_array: np.ndarray,
    mask: Optional[np.ndarray] = None,
    p_low: float = 2.0,
    p_high: float = 98.0,
) -> np.ndarray:
    """
    Applies cumulative percentile histogram stretching (2%-98%) to an RGB color band.

    Args:
        band_array: 2D float array containing color values.
        mask: Optional boolean mask of valid pixels.
        p_low: Lower percentile cutoff (default: 2.0).
        p_high: Upper percentile cutoff (default: 98.0).

    Returns:
        Contrast-enhanced 2D float array in range [0.0, 255.0].
    """
    valid = (mask & (band_array > 0)) if mask is not None else (band_array > 0)
    if not np.any(valid):
        return band_array

    vals = band_array[valid]
    v_min = float(np.percentile(vals, p_low))
    v_max = float(np.percentile(vals, p_high))

    if v_max <= v_min:
        return band_array

    stretched = np.clip((band_array - v_min) / (v_max - v_min) * 255.0, 0.0, 255.0)
    return stretched
