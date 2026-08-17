"""
dronegeo.core
~~~~~~~~~~~~~
Core interfaces, Abstract Base Classes (ABCs), and domain-specific exception hierarchy.
"""

from .base import (
    BaseDiagnostic,
    BaseSurfaceGenerator,
    BasePointCloudFilter,
    BaseProfiler,
)
from .exceptions import (
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
    DatasetValidationError,
)

__all__ = [
    "BaseDiagnostic",
    "BaseSurfaceGenerator",
    "BasePointCloudFilter",
    "BaseProfiler",
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
    "DatasetValidationError",
]
