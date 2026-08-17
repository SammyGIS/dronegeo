"""
dronegeo.spatial
~~~~~~~~~~~~~~~~
Spatial coordinate reference systems, PROJ bindings, and projection resolution.
"""

from .crs_manager import (
    resolve_crs,
    bind_proj_environment,
    get_spatial_bounds_from_las,
    get_spatial_bounds_from_raster,
)

__all__ = [
    "resolve_crs",
    "bind_proj_environment",
    "get_spatial_bounds_from_las",
    "get_spatial_bounds_from_raster",
]
