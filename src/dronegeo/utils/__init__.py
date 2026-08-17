"""
dronegeo.utils
~~~~~~~~~~~~~~
Convenience utilities for spatial calculations, file validation, color ramps, and execution benchmarking.
"""

from .geo_utils import (
    calculate_bounding_box_intersection,
    format_spatial_extent,
    get_raster_metadata_summary,
    downsample_array_2d,
)
from .file_utils import (
    verify_las_file,
    verify_raster_file,
    format_file_size,
    ensure_output_directory,
)
from .color_utils import (
    get_elevation_colormap,
    get_vegetation_colormap,
    create_custom_diverging_colormap,
)
from .benchmarking import (
    ExecutionTimer,
    time_operation,
)

__all__ = [
    "calculate_bounding_box_intersection",
    "format_spatial_extent",
    "get_raster_metadata_summary",
    "downsample_array_2d",
    "verify_las_file",
    "verify_raster_file",
    "format_file_size",
    "ensure_output_directory",
    "get_elevation_colormap",
    "get_vegetation_colormap",
    "create_custom_diverging_colormap",
    "ExecutionTimer",
    "time_operation",
]
