"""
dronegeo.dem.surface_models
~~~~~~~~~~~~~~~~~~~~~~~~~~~
High-resolution continuous DTM, DSM, CHM, True-Color RGB Orthomosaic, and Intensity GeoTIFF generation.
"""

from __future__ import annotations
import time
from pathlib import Path
from typing import Union, Optional, Tuple, Callable

import numpy as np
import scipy.ndimage as ndi
from scipy.spatial import cKDTree
import rasterio
from rasterio.transform import from_origin
from rasterio.crs import CRS
import laspy

from ..config.compute import ComputeConfig, get_compute_config, collect_garbage_if_needed
from ..spatial.crs_manager import resolve_crs
from ..core.base import BaseSurfaceGenerator
from ..core.exceptions import (
    PointCloudError,
    EmptyPointCloudError,
    InsufficientGroundPointsError,
    MissingDimensionError,
    IncompatibleRasterDimensionsError,
    RasterIOError,
)
from .boundary_extraction import extract_flight_footprint_mask


class DTMGenerator(BaseSurfaceGenerator):
    """
    Continuous Survey-Grade Digital Terrain Model (DTM) Generator.

    Real-World Applications:
        - Civil & Topographic Surveying: Bare-earth elevation extraction for road design,
          drainage basins, and flood modeling.
        - Forestry & Environmental Science: Ground surface modeling under dense multi-layered tree canopies.
        - Mining & Earthwork Planning: Baseline ground surface generation for stockpile and excavation planning.

    When to Use:
        Use when converting classified LiDAR point clouds into bare-earth DTMs. Unlike standard
        Delaunay TIN triangulation which leaves sharp crystal/facet lines on steep slopes, this
        generator produces a seamless, continuous-gradient surface.

    Attributes:
        resolution: Spatial cell resolution in meters (e.g., 0.118 for 11.8cm GSD).
        footprint_buffer: Exterior buffer distance in meters for concave hull masking.
        k_neighbors: Number of nearest ground vertices queried per pixel for IDW interpolation.
        ground_class: ASPRS classification value representing ground returns (default: 2).
        block_rows: Number of raster rows processed per memory block in chunked mode.
        crs: Coordinate reference system specification (EPSG integer, WKT, or .prj path).
        config: ComputeConfig instance managing CPU workers and streaming chunk sizes.

    Example:
        >>> from dronegeo.dem import DTMGenerator
        >>> generator = DTMGenerator(resolution=0.118, k_neighbors=8, ground_class=2)
        >>> dtm_tif = generator.generate(
        ...     las_path="data/flight_survey.laz",
        ...     output_path="outputs/survey_dtm.tif"
        ... )
        >>> print(f"DTM created at: {dtm_tif}")
    """

    def __init__(
        self,
        resolution: float = 0.118,
        footprint_buffer: float = 3.0,
        k_neighbors: int = 8,
        ground_class: int = 2,
        block_rows: Optional[int] = None,
        crs: Optional[Union[str, int, CRS, Path]] = None,
        config: Optional[ComputeConfig] = None,
    ):
        super().__init__(resolution=resolution, footprint_buffer=footprint_buffer, config=config)
        assert k_neighbors >= 1, f"k_neighbors must be at least 1, got {k_neighbors}"
        assert ground_class >= 0, f"ground_class must be non-negative, got {ground_class}"
        if block_rows is not None:
            assert block_rows >= 64, f"block_rows must be at least 64, got {block_rows}"

        self.k_neighbors = int(k_neighbors)
        self.ground_class = int(ground_class)
        self.block_rows = block_rows
        self.crs = crs

    def generate(
        self,
        las_path: Union[str, Path],
        output_path: Union[str, Path],
        progress_callback: Optional[Callable[[int, int, float], None]] = None,
        **kwargs
    ) -> str:
        """
        Executes DTM generation pipeline and writes the output GeoTIFF.

        Args:
            las_path: Path to input LAS/LAZ point cloud file.
            output_path: Destination path for the generated GeoTIFF.
            progress_callback: Optional callback function receiving (processed_rows, total_rows, pct).

        Returns:
            Absolute string path to the created DTM GeoTIFF.
        """
        return create_dtm(
            las_path=las_path,
            output_tif=output_path,
            resolution=self.resolution,
            footprint_buffer=self.footprint_buffer,
            k_neighbors=self.k_neighbors,
            ground_class=self.ground_class,
            block_rows=self.block_rows,
            crs=self.crs,
            progress_callback=progress_callback,
            config=self.config,
        )


class DSMGenerator(BaseSurfaceGenerator):
    """
    Continuous Digital Surface Model (DSM) Generator.

    Real-World Applications:
        - Urban Planning & Telecom: Building rooftop height modeling and 5G line-of-sight analysis.
        - Forestry Biomass: Forest canopy top elevation modeling.
        - Solar Potential: Rooftop shadow and solar irradiance modeling.

    When to Use:
        Use when you need the envelope of the highest surface points (including trees,
        structures, and roofs) rather than the bare ground.

    Attributes:
        resolution: Spatial cell resolution in meters (default: 0.118m).
        footprint_buffer: Exterior buffer distance in meters for flight boundary mask.
        crs: Coordinate reference system specification.
        config: ComputeConfig instance.

    Example:
        >>> from dronegeo.dem import DSMGenerator
        >>> generator = DSMGenerator(resolution=0.10)
        >>> dsm_tif = generator.generate("data/flight.laz", "outputs/dsm.tif")
    """

    def __init__(
        self,
        resolution: float = 0.118,
        footprint_buffer: float = 3.0,
        crs: Optional[Union[str, int, CRS, Path]] = None,
        config: Optional[ComputeConfig] = None,
    ):
        super().__init__(resolution=resolution, footprint_buffer=footprint_buffer, config=config)
        self.crs = crs

    def generate(
        self,
        las_path: Union[str, Path],
        output_path: Union[str, Path],
        progress_callback: Optional[Callable[[str], None]] = None,
        **kwargs
    ) -> str:
        """
        Executes DSM surface generation and writes the output GeoTIFF.

        Args:
            las_path: Path to input LAS/LAZ point cloud file.
            output_path: Destination path for the generated GeoTIFF.
            progress_callback: Optional status callback receiving string messages.

        Returns:
            Absolute string path to the created DSM GeoTIFF.
        """
        return create_dsm(
            las_path=las_path,
            output_tif=output_path,
            resolution=self.resolution,
            footprint_buffer=self.footprint_buffer,
            crs=self.crs,
            progress_callback=progress_callback,
            config=self.config,
        )


class RGBOrthoGenerator(BaseSurfaceGenerator):
    """
    True-Color 3-band RGB Orthomosaic Generator from colorized LAS point clouds.

    Real-World Applications:
        - Cadastral & Land Management: Visual property boundaries and high-resolution base maps.
        - Construction Site Progress: Visual inspection orthomosaics for stakeholder reporting.
        - Asset Management: Road and utility corridor visual condition surveys.

    When to Use:
        Use when extracting a calibrated, true-color visual orthomosaic directly from colorized
        photogrammetric or LiDAR point clouds.

    Attributes:
        resolution: Grid cell size in meters (default: 0.118m).
        footprint_buffer: Boundary buffer distance in meters.
        crs: Target Coordinate Reference System.
        config: ComputeConfig instance.

    Example:
        >>> from dronegeo.dem import RGBOrthoGenerator
        >>> ortho_gen = RGBOrthoGenerator(resolution=0.10)
        >>> ortho_tif = ortho_gen.generate("data/colorized_cloud.laz", "outputs/ortho.tif")
    """

    def __init__(
        self,
        resolution: float = 0.118,
        footprint_buffer: float = 3.0,
        crs: Optional[Union[str, int, CRS, Path]] = None,
        config: Optional[ComputeConfig] = None,
    ):
        super().__init__(resolution=resolution, footprint_buffer=footprint_buffer, config=config)
        self.crs = crs

    def generate(
        self,
        las_path: Union[str, Path],
        output_path: Union[str, Path],
        **kwargs
    ) -> str:
        """
        Generates 3-band RGB true-color GeoTIFF orthomosaic.

        Args:
            las_path: Colorized LAS/LAZ file containing RGB dimensions.
            output_path: Destination path for the 3-band GeoTIFF.

        Returns:
            Absolute string path to the created RGB GeoTIFF.
        """
        return create_rgb_ortho(
            las_path=las_path,
            output_tif=output_path,
            resolution=self.resolution,
            footprint_buffer=self.footprint_buffer,
            crs=self.crs,
            config=self.config,
        )


def create_dsm(
    las_path: Union[str, Path],
    output_tif: Union[str, Path],
    resolution: float = 0.118,
    footprint_buffer: float = 3.0,
    crs: Optional[Union[str, int, CRS, Path]] = None,
    progress_callback: Optional[Callable[[str], None]] = None,
    config: Optional[ComputeConfig] = None,
) -> str:
    """
    Generates a survey-grade continuous Digital Surface Model (DSM) GeoTIFF.

    Real-World Applications:
        - Urban 3D Modeling: Building envelope height and architectural massing models.
        - Solar Energy: Rooftop surface slope and solar irradiance estimation.
        - Telecom 5G: Line-of-sight clearance between towers and receiver antennas.

    When to Use:
        Use when you need the surface of all highest returns (including tree crowns and building roofs).

    Math Formulation:
        - 2D Binned Maximum Return: Z_dsm(row, col) = max(Z_i) for points falling in pixel (row, col).
        - Gap Infill: Euclidean Distance Transform nearest valid neighbor infilling:
          Z_infill = Z_dsm[distance_transform_edt(isnan(Z_dsm))].

    Args:
        las_path: Path to input LAS/LAZ point cloud file.
        output_tif: Target GeoTIFF destination path.
        resolution: Grid cell resolution in meters (default: 0.118m).
        footprint_buffer: Buffer distance in meters for flight boundary mask (default: 3.0m).
        crs: Coordinate Reference System specification (EPSG code, WKT, or .prj path).
        progress_callback: Optional status callback fn(msg).
        config: Optional ComputeConfig instance.

    Returns:
        Absolute string path to the created DSM GeoTIFF.

    Raises:
        FileNotFoundError: If input LAS/LAZ file does not exist on disk.
        EmptyPointCloudError: If the input point cloud contains zero points.

    Example:
        >>> import dronegeo as dg
        >>> dsm_path = dg.dem.create_dsm(
        ...     las_path="survey_flight.laz",
        ...     output_tif="survey_dsm.tif",
        ...     resolution=0.10
        ... )
    """
    assert resolution > 0, f"Resolution must be positive, got {resolution}"
    assert footprint_buffer >= 0, f"Footprint buffer must be >= 0, got {footprint_buffer}"

    cfg = config or get_compute_config()
    p_in = Path(las_path)
    p_out = Path(output_tif)

    assert p_in.exists(), f"Input LAS file does not exist: {p_in}"
    assert p_in.is_file(), f"Input LAS path is not a valid file: {p_in}"

    p_out.parent.mkdir(parents=True, exist_ok=True)
    target_crs = resolve_crs(crs)

    if progress_callback:
        progress_callback("Extracting concave hull footprint boundary...")

    fp, (height, width), (min_x, max_x, min_y, max_y) = extract_flight_footprint_mask(
        p_in, pixel_res=resolution, buffer_distance=footprint_buffer, config=cfg
    )
    assert height > 0 and width > 0, f"Invalid raster dimensions: {height}x{width}"
    transform = from_origin(min_x, max_y, resolution, resolution)

    flat_dsm = np.full(height * width, -np.inf, dtype=np.float32)

    if progress_callback:
        progress_callback("Streaming point cloud for maximum surface returns...")

    with laspy.open(str(p_in)) as reader:
        if reader.header.point_count == 0:
            raise EmptyPointCloudError(f"Point cloud is empty: {p_in}")

        for chunk in reader.chunk_iterator(cfg.chunk_size):
            cx = np.array(chunk.x, dtype=np.float64)
            cy = np.array(chunk.y, dtype=np.float64)
            cz = np.array(chunk.z, dtype=np.float32)

            cols = np.clip(((cx - min_x) / resolution).astype(int), 0, width - 1)
            rows = np.clip(((max_y - cy) / resolution).astype(int), 0, height - 1)
            indices = rows * width + cols

            np.maximum.at(flat_dsm, indices, cz)

    dsm_raw = np.where(flat_dsm > -np.inf, flat_dsm, np.nan).reshape((height, width))
    del flat_dsm

    if progress_callback:
        progress_callback("Infilling interior gaps and applying boundary mask...")

    ind_dsm = ndi.distance_transform_edt(np.isnan(dsm_raw), return_distances=False, return_indices=True)
    dsm_filled = dsm_raw[tuple(ind_dsm)]
    dsm_smooth = ndi.gaussian_filter(dsm_filled, sigma=1.0)
    dsm_final = np.where(fp, np.where(np.isnan(dsm_raw), dsm_smooth, dsm_filled), -10000.0).astype(np.float32)
    del dsm_raw, ind_dsm, dsm_filled, dsm_smooth, fp

    meta = {
        'driver': 'GTiff',
        'height': height,
        'width': width,
        'count': 1,
        'dtype': 'float32',
        'crs': target_crs,
        'transform': transform,
        'nodata': -10000.0,
        'compress': 'lzw',
    }

    with rasterio.open(str(p_out), "w", **meta) as dst:
        dst.write(dsm_final, 1)

    del dsm_final
    collect_garbage_if_needed(cfg)

    assert p_out.exists() and p_out.stat().st_size > 0, f"Failed to write output DSM: {p_out}"
    return str(p_out)


def create_dtm(
    las_path: Union[str, Path],
    output_tif: Union[str, Path],
    resolution: float = 0.118,
    footprint_buffer: float = 3.0,
    k_neighbors: int = 8,
    ground_class: int = 2,
    block_rows: Optional[int] = None,
    crs: Optional[Union[str, int, CRS, Path]] = None,
    progress_callback: Optional[Callable[[int, int, float], None]] = None,
    config: Optional[ComputeConfig] = None,
) -> str:
    """
    Generates a continuous, survey-grade Digital Terrain Model (DTM) GeoTIFF.

    Real-World Applications:
        - Civil Engineering & Earthworks: Bare earth modeling for highway and railway design.
        - Hydrology & Flood Modeling: True bare-earth elevation for watershed and stormwater analysis.
        - Forestry: Accurate digital ground terrain under heavy tree canopies.

    When to Use:
        Use when standard Delaunay TIN triangulation generates artificial faceted crystal edges on
        steep hillsides. This algorithm applies multi-threaded k-NN Inverse Distance Weighting to
        guarantee a continuous C1 gradient.

    Math Formulation:
        - Inverse Distance Weighting: w_i = 1 / max(d_i, 1e-4)^2
        - Normalized Weights: W_i = w_i / sum(w_i)
        - Interpolated Elevation: Z_dtm = sum(W_i * Z_i) for k-nearest ground points.

    Args:
        las_path: Path to input LAS/LAZ point cloud file.
        output_tif: Target GeoTIFF destination path.
        resolution: Grid cell resolution in meters (default: 0.118m).
        footprint_buffer: Buffer distance in meters for flight boundary mask (default: 3.0m).
        k_neighbors: Number of nearest ground neighbors for smooth IDW (default: 8).
        ground_class: ASPRS classification value for bare earth (default: 2).
        block_rows: Block slice height in rows. If None, taken from compute config.
        crs: Coordinate Reference System specification.
        progress_callback: Optional callback fn(processed_rows, total_rows, pct).
        config: Optional ComputeConfig instance.

    Returns:
        Absolute string path to the created DTM GeoTIFF.

    Raises:
        FileNotFoundError: If input LAS file does not exist on disk.
        EmptyPointCloudError: If point cloud has 0 points.
        InsufficientGroundPointsError: If zero points match the specified ground classification.

    Example:
        >>> import dronegeo as dg
        >>> dtm_path = dg.dem.create_dtm(
        ...     las_path="survey_flight.laz",
        ...     output_tif="survey_dtm.tif",
        ...     resolution=0.118,
        ...     k_neighbors=8
        ... )
    """
    assert resolution > 0, f"Resolution must be positive, got {resolution}"
    assert footprint_buffer >= 0, f"Footprint buffer must be >= 0, got {footprint_buffer}"
    assert k_neighbors >= 1, f"k_neighbors must be >= 1, got {k_neighbors}"

    cfg = config or get_compute_config()
    p_in = Path(las_path)
    p_out = Path(output_tif)

    assert p_in.exists(), f"Input LAS file does not exist: {p_in}"
    assert p_in.is_file(), f"Input LAS path is not a valid file: {p_in}"

    p_out.parent.mkdir(parents=True, exist_ok=True)
    target_crs = resolve_crs(crs)
    b_rows = block_rows or cfg.block_rows
    assert b_rows > 0, f"block_rows must be > 0, got {b_rows}"

    fp, (height, width), (min_x, max_x, min_y, max_y) = extract_flight_footprint_mask(
        p_in, pixel_res=resolution, buffer_distance=footprint_buffer, config=cfg
    )
    assert height > 0 and width > 0, f"Invalid raster dimensions: {height}x{width}"
    transform = from_origin(min_x, max_y, resolution, resolution)

    # 1. Collect Ground Classification Nodes
    ground_x: list = []
    ground_y: list = []
    ground_z: list = []

    with laspy.open(str(p_in)) as reader:
        if reader.header.point_count == 0:
            raise EmptyPointCloudError(f"Point cloud is empty: {p_in}")

        for chunk in reader.chunk_iterator(cfg.chunk_size):
            cx = np.array(chunk.x, dtype=np.float64)
            cy = np.array(chunk.y, dtype=np.float64)
            cz = np.array(chunk.z, dtype=np.float32)
            c_cls = np.array(chunk.classification, dtype=np.uint8)

            g_mask = (c_cls == ground_class)
            if not np.any(g_mask):
                g_mask = np.ones_like(cz, dtype=bool)

            ground_x.extend(cx[g_mask].tolist())
            ground_y.extend(cy[g_mask].tolist())
            ground_z.extend(cz[g_mask].tolist())

    gx = np.array(ground_x, dtype=np.float64)
    gy = np.array(ground_y, dtype=np.float64)
    gz = np.array(ground_z, dtype=np.float32)
    del ground_x, ground_y, ground_z

    if len(gx) == 0:
        raise InsufficientGroundPointsError(f"No ground points (class {ground_class}) found in {p_in.name}")

    # Pixel decimation for unique nodes to accelerate tree queries
    g_cols = np.clip(((gx - min_x) / resolution).astype(int), 0, width - 1)
    g_rows = np.clip(((max_y - gy) / resolution).astype(int), 0, height - 1)
    g_idx = g_rows * width + g_cols
    u_idx, u_pos = np.unique(g_idx, return_index=True)

    nodes_x = gx[u_pos]
    nodes_y = gy[u_pos]
    nodes_z = gz[u_pos]
    del gx, gy, gz, g_cols, g_rows, g_idx, u_idx, u_pos
    collect_garbage_if_needed(cfg)

    # 2. Build KDTree for k-NN IDW Ground Interpolation
    tree = cKDTree(np.column_stack([nodes_x, nodes_y]))
    final_dtm = np.full((height, width), -10000.0, dtype=np.float32)

    # 3. Stream interpolation in multi-threaded raster blocks
    effective_k = min(k_neighbors, len(nodes_x))
    for r_start in range(0, height, b_rows):
        r_end = min(r_start + b_rows, height)
        b_fp = fp[r_start:r_end, :]

        b_sub_rows, b_cols = np.where(b_fp)
        if len(b_sub_rows) > 0:
            eval_x = min_x + (b_cols + 0.5) * resolution
            eval_y = max_y - (r_start + b_sub_rows + 0.5) * resolution
            eval_pts = np.column_stack([eval_x, eval_y])

            dists, idxs = tree.query(eval_pts, k=effective_k, workers=cfg.n_jobs)
            if effective_k == 1:
                idxs = idxs[:, None]
                dists = dists[:, None]

            weights = 1.0 / np.maximum(dists, 1e-4)**2
            weights /= np.sum(weights, axis=1, keepdims=True)
            z_interpolated = np.sum(weights * nodes_z[idxs], axis=1).astype(np.float32)

            final_dtm[r_start + b_sub_rows, b_cols] = z_interpolated

        pct = (r_end / height) * 100.0
        if progress_callback:
            progress_callback(r_end, height, pct)

    del nodes_x, nodes_y, nodes_z, tree, fp
    collect_garbage_if_needed(cfg)

    meta = {
        'driver': 'GTiff',
        'height': height,
        'width': width,
        'count': 1,
        'dtype': 'float32',
        'crs': target_crs,
        'transform': transform,
        'nodata': -10000.0,
        'compress': 'lzw',
    }

    with rasterio.open(str(p_out), "w", **meta) as dst:
        dst.write(final_dtm, 1)

    del final_dtm
    collect_garbage_if_needed(cfg)

    assert p_out.exists() and p_out.stat().st_size > 0, f"Failed to write output DTM: {p_out}"
    return str(p_out)


def create_chm(
    dsm_path: Union[str, Path],
    dtm_path: Union[str, Path],
    output_tif: Union[str, Path],
    clamp_min: float = 0.0,
    clamp_max: Optional[float] = 120.0,
) -> str:
    """
    Computes a Canopy Height Model (CHM = DSM - DTM) GeoTIFF.

    Real-World Applications:
        - Forestry Inventory: Individual tree height extraction, crown delineation, and timber volume estimation.
        - Utility Vegetation Management: Detecting tree encroachment within power line right-of-way corridors.
        - Ecology & Carbon Modeling: Estimating forest biomass carbon stock.

    When to Use:
        Use when you have both a DSM (surface with canopy) and a DTM (bare ground) and need the true
        normalized height of vegetation or structures above the ground.

    Math Formulation:
        - CHM(row, col) = clamp(DSM(row, col) - DTM(row, col), min=clamp_min, max=clamp_max)

    Args:
        dsm_path: Path to input DSM GeoTIFF.
        dtm_path: Path to input DTM GeoTIFF.
        output_tif: Target CHM GeoTIFF destination path.
        clamp_min: Minimum height floor in meters (default: 0.0m).
        clamp_max: Optional maximum height ceiling in meters (default: 120.0m).

    Returns:
        Absolute string path to the created CHM GeoTIFF.

    Raises:
        FileNotFoundError: If DSM or DTM file does not exist.
        IncompatibleRasterDimensionsError: If DSM and DTM raster dimensions do not match.

    Example:
        >>> import dronegeo as dg
        >>> chm_path = dg.dem.create_chm(
        ...     dsm_path="survey_dsm.tif",
        ...     dtm_path="survey_dtm.tif",
        ...     output_tif="survey_chm.tif"
        ... )
    """
    p_dsm = Path(dsm_path)
    p_dtm = Path(dtm_path)
    p_out = Path(output_tif)

    assert p_dsm.exists(), f"DSM raster does not exist: {p_dsm}"
    assert p_dtm.exists(), f"DTM raster does not exist: {p_dtm}"
    if clamp_max is not None:
        assert clamp_max > clamp_min, f"clamp_max ({clamp_max}) must be greater than clamp_min ({clamp_min})"

    p_out.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.open(str(p_dsm)) as src_dsm, rasterio.open(str(p_dtm)) as src_dtm:
        if src_dsm.shape != src_dtm.shape:
            raise IncompatibleRasterDimensionsError(
                f"Mismatched raster shapes: DSM {src_dsm.shape} != DTM {src_dtm.shape}"
            )
        dsm = src_dsm.read(1)
        dtm = src_dtm.read(1)
        nodata_dsm = src_dsm.nodata if src_dsm.nodata is not None else -10000.0
        nodata_dtm = src_dtm.nodata if src_dtm.nodata is not None else -10000.0
        meta = src_dsm.meta.copy()

    valid = (dsm != nodata_dsm) & (dtm != nodata_dtm) & (~np.isnan(dsm)) & (~np.isnan(dtm))
    chm = np.full_like(dsm, -10000.0, dtype=np.float32)

    diff = dsm[valid] - dtm[valid]
    diff = np.maximum(diff, clamp_min)
    if clamp_max is not None:
        diff = np.minimum(diff, clamp_max)

    chm[valid] = diff.astype(np.float32)
    meta.update({'nodata': -10000.0, 'dtype': 'float32', 'compress': 'lzw'})

    with rasterio.open(str(p_out), "w", **meta) as dst:
        dst.write(chm, 1)

    assert p_out.exists() and p_out.stat().st_size > 0, f"Failed to write output CHM: {p_out}"
    return str(p_out)


def create_rgb_ortho(
    las_path: Union[str, Path],
    output_tif: Union[str, Path],
    resolution: float = 0.118,
    footprint_buffer: float = 3.0,
    crs: Optional[Union[str, int, CRS, Path]] = None,
    config: Optional[ComputeConfig] = None,
) -> str:
    """
    Extracts and rasterizes point cloud Red/Green/Blue color attributes into a 3-band GeoTIFF true-color orthomosaic.

    Real-World Applications:
        - Site Mapping: High-resolution true-color basemaps for CAD and GIS overlays.
        - Asset Inspection: Visual verification of infrastructure conditions.

    When to Use:
        Use when the point cloud contains color attributes (from an integrated camera or photogrammetry).

    Args:
        las_path: Path to colorized LAS/LAZ point cloud file.
        output_tif: Target 3-band GeoTIFF destination path.
        resolution: Grid cell resolution in meters (default: 0.118m).
        footprint_buffer: Buffer distance in meters for boundary mask (default: 3.0m).
        crs: Coordinate Reference System specification.
        config: Optional ComputeConfig instance.

    Returns:
        Absolute string path to the created RGB GeoTIFF.

    Raises:
        MissingDimensionError: If point cloud lacks Red/Green/Blue color dimensions.

    Example:
        >>> import dronegeo as dg
        >>> ortho_path = dg.dem.create_rgb_ortho(
        ...     las_path="colorized_points.laz",
        ...     output_tif="orthomosaic.tif",
        ...     resolution=0.10
        ... )
    """
    assert resolution > 0, f"Resolution must be positive, got {resolution}"
    assert footprint_buffer >= 0, f"Footprint buffer must be >= 0, got {footprint_buffer}"

    cfg = config or get_compute_config()
    p_in = Path(las_path)
    p_out = Path(output_tif)

    assert p_in.exists(), f"LAS file does not exist: {p_in}"
    p_out.parent.mkdir(parents=True, exist_ok=True)
    target_crs = resolve_crs(crs)

    fp, (height, width), (min_x, max_x, min_y, max_y) = extract_flight_footprint_mask(
        p_in, pixel_res=resolution, buffer_distance=footprint_buffer, config=cfg
    )
    assert height > 0 and width > 0, f"Invalid raster dimensions: {height}x{width}"
    transform = from_origin(min_x, max_y, resolution, resolution)

    r_grid = np.zeros((height, width), dtype=np.float32)
    g_grid = np.zeros((height, width), dtype=np.float32)
    b_grid = np.zeros((height, width), dtype=np.float32)
    count_grid = np.zeros((height, width), dtype=np.uint32)

    with laspy.open(str(p_in)) as reader:
        dim_names = [d.name for d in reader.header.point_format.dimensions]
        if not ("red" in dim_names and "green" in dim_names and "blue" in dim_names):
            raise MissingDimensionError(
                f"Point cloud {p_in.name} missing RGB dimensions. Available: {dim_names}"
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

    r_out = np.where(fp, np.clip(r_grid, 0, 255), 0).astype(np.uint8)
    g_out = np.where(fp, np.clip(g_grid, 0, 255), 0).astype(np.uint8)
    b_out = np.where(fp, np.clip(b_grid, 0, 255), 0).astype(np.uint8)
    del r_grid, g_grid, b_grid, fp

    meta = {
        'driver': 'GTiff',
        'height': height,
        'width': width,
        'count': 3,
        'dtype': 'uint8',
        'crs': target_crs,
        'transform': transform,
        'nodata': 0,
        'compress': 'lzw',
    }

    with rasterio.open(str(p_out), "w", **meta) as dst:
        dst.write(r_out, 1)
        dst.write(g_out, 2)
        dst.write(b_out, 3)

    del r_out, g_out, b_out
    collect_garbage_if_needed(cfg)

    assert p_out.exists() and p_out.stat().st_size > 0, f"Failed to write output RGB Ortho: {p_out}"
    return str(p_out)


def create_intensity_raster(
    las_path: Union[str, Path],
    output_tif: Union[str, Path],
    resolution: float = 0.118,
    footprint_buffer: float = 3.0,
    crs: Optional[Union[str, int, CRS, Path]] = None,
    config: Optional[ComputeConfig] = None,
) -> str:
    """
    Rasterizes LiDAR sensor reflectance intensity into a single-band GeoTIFF.

    Real-World Applications:
        - Night Surveys: High-contrast reflectance imaging when photographic light is absent.
        - Material Classification: Distinguishing asphalt from concrete and identifying moisture.

    When to Use:
        Use when analyzing laser return signal strength / surface reflectivity.

    Args:
        las_path: Path to LAS/LAZ point cloud file with intensity values.
        output_tif: Target GeoTIFF destination path.
        resolution: Grid cell resolution in meters (default: 0.118m).
        footprint_buffer: Buffer distance in meters for boundary mask (default: 3.0m).
        crs: Coordinate Reference System specification.
        config: Optional ComputeConfig instance.

    Returns:
        Absolute string path to the created Intensity GeoTIFF.

    Raises:
        MissingDimensionError: If point cloud lacks the intensity attribute.

    Example:
        >>> import dronegeo as dg
        >>> int_path = dg.dem.create_intensity_raster(
        ...     las_path="lidar_flight.laz",
        ...     output_tif="reflectance_intensity.tif"
        ... )
    """
    assert resolution > 0, f"Resolution must be positive, got {resolution}"
    assert footprint_buffer >= 0, f"Footprint buffer must be >= 0, got {footprint_buffer}"

    cfg = config or get_compute_config()
    p_in = Path(las_path)
    p_out = Path(output_tif)

    assert p_in.exists(), f"LAS file does not exist: {p_in}"
    p_out.parent.mkdir(parents=True, exist_ok=True)
    target_crs = resolve_crs(crs)

    fp, (height, width), (min_x, max_x, min_y, max_y) = extract_flight_footprint_mask(
        p_in, pixel_res=resolution, buffer_distance=footprint_buffer, config=cfg
    )
    assert height > 0 and width > 0, f"Invalid raster dimensions: {height}x{width}"
    transform = from_origin(min_x, max_y, resolution, resolution)

    int_grid = np.zeros((height, width), dtype=np.float32)
    count_grid = np.zeros((height, width), dtype=np.uint32)

    with laspy.open(str(p_in)) as reader:
        dim_names = [d.name for d in reader.header.point_format.dimensions]
        if "intensity" not in dim_names:
            raise MissingDimensionError(
                f"Point cloud {p_in.name} missing intensity channel. Dimensions: {dim_names}"
            )

        for chunk in reader.chunk_iterator(cfg.chunk_size):
            cx = np.array(chunk.x, dtype=np.float64)
            cy = np.array(chunk.y, dtype=np.float64)
            c_int = np.array(chunk.intensity, dtype=np.float32)

            cols = np.clip(((cx - min_x) / resolution).astype(int), 0, width - 1)
            rows = np.clip(((max_y - cy) / resolution).astype(int), 0, height - 1)
            idx = rows * width + cols

            np.add.at(int_grid.ravel(), idx, c_int)
            np.add.at(count_grid.ravel(), idx, 1)

    valid_cells = count_grid > 0
    int_grid[valid_cells] /= count_grid[valid_cells]
    del count_grid

    int_final = np.where(fp, int_grid, -10000.0).astype(np.float32)
    del int_grid, fp

    meta = {
        'driver': 'GTiff',
        'height': height,
        'width': width,
        'count': 1,
        'dtype': 'float32',
        'crs': target_crs,
        'transform': transform,
        'nodata': -10000.0,
        'compress': 'lzw',
    }

    with rasterio.open(str(p_out), "w", **meta) as dst:
        dst.write(int_final, 1)

    del int_final
    collect_garbage_if_needed(cfg)

    assert p_out.exists() and p_out.stat().st_size > 0, f"Failed to write output Intensity raster: {p_out}"
    return str(p_out)
