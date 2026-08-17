"""
dronegeo
~~~~~~~~
A high-performance, modular Python library for drone remote sensing, UAV LiDAR point cloud
processing, true-color orthomosaics, photogrammetric vegetation indices, terrain morphology,
hydrological flow routing, erosion risk modeling, and continuous DEM generation.

Submodules:
- `dronegeo.core`: Abstract Base Classes (ABCs), interfaces, and domain exception hierarchy.
- `dronegeo.config`: Hardware/compute engine, worker allocation, and execution context managers.
- `dronegeo.spatial`: Projection resolution, UTM coordinates, and PROJ environment bindings.
- `dronegeo.diagnostics`: Pre-processing inspection for strip datum offsets (ΔZ) and terrain anomalies.
- `dronegeo.lidar`: Point cloud profiling, multi-pass strip alignment, and terrain rectification.
- `dronegeo.dem`: High-resolution continuous DTM, DSM, CHM, and intensity rasters.
- `dronegeo.imagery`: True-Color Orthomosaics (RGB/RGBA) and Visible Vegetation Indices (VARI, GLI, TGI, ExG).
- `dronegeo.analysis`: Analytical Hillshade, Slope, Aspect, Vector Contours, and 3D Cut/Fill Volumetrics.
- `dronegeo.hydrology`: Hydrological flow routing (D8, D-inf), TWI, Stream Power (SPI), and Sediment Transport (STI).
- `dronegeo.profiling`: Elevation transects, diagnostic QC visualizations, and spatial grid chip mapping.
- `dronegeo.utils`: Spatial bounding box arithmetic, file validation, color ramps, and benchmarking timers.
"""

from __future__ import annotations
import os

# Safe initialization of PROJ environment variables before importing geospatial dependencies
try:
    import pyproj.datadir
    _proj_dir = pyproj.datadir.get_data_dir()
    if _proj_dir and os.path.exists(_proj_dir):
        os.environ["PROJ_DATA"] = _proj_dir
        os.environ["PROJ_LIB"] = _proj_dir
except Exception:
    pass

try:
    import matplotlib
    matplotlib.use("Agg")
except Exception:
    pass

__version__ = "0.1.0"
__author__ = "STROM Drone Remote Sensing Team"

from . import core
from . import config
from . import spatial
from . import diagnostics
from . import lidar
from . import dem
from . import imagery
from . import analysis
from . import hydrology
from . import profiling
from . import utils

# Convenient alias
risk = hydrology

from .config.compute import (
    ComputeConfig,
    set_compute_config,
    get_compute_config,
    set_compute_profile,
    reset_compute_config,
    compute_context,
)

from .core.exceptions import (
    DroneGeoError,
    PointCloudError,
    EmptyPointCloudError,
    MissingDimensionError,
    InvalidPointCloudFormatError,
    InsufficientGroundPointsError,
    SpatialReferenceError,
    AlignmentError,
    NoSpatialOverlapError,
    InsufficientOverlapDataError,
    SurfaceInterpolationError,
    IncompatibleRasterDimensionsError,
    RasterIOError,
    ComputationError,
)

__all__ = [
    "__version__",
    "__author__",
    "core",
    "config",
    "spatial",
    "diagnostics",
    "lidar",
    "dem",
    "imagery",
    "analysis",
    "hydrology",
    "risk",
    "profiling",
    "utils",
    "ComputeConfig",
    "set_compute_config",
    "get_compute_config",
    "set_compute_profile",
    "reset_compute_config",
    "compute_context",
    "DroneGeoError",
    "PointCloudError",
    "EmptyPointCloudError",
    "MissingDimensionError",
    "InvalidPointCloudFormatError",
    "InsufficientGroundPointsError",
    "SpatialReferenceError",
    "AlignmentError",
    "NoSpatialOverlapError",
    "InsufficientOverlapDataError",
    "SurfaceInterpolationError",
    "IncompatibleRasterDimensionsError",
    "RasterIOError",
    "ComputationError",
]
