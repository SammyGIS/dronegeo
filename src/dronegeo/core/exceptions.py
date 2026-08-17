"""
dronegeo.core.exceptions
~~~~~~~~~~~~~~~~~~~~~~~~
Comprehensive domain-specific exception hierarchy for dronegeo.
All exceptions provide structured error context and descriptive diagnostic messages.
"""

from typing import Optional, Any


class DroneGeoError(Exception):
    """Base exception for all dronegeo runtime and processing errors."""

    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(message)
        self.message = message
        self.details = details

    def __str__(self) -> str:
        if self.details is not None:
            return f"[DroneGeoError] {self.message} | Details: {self.details}"
        return f"[DroneGeoError] {self.message}"


class PointCloudError(DroneGeoError):
    """Raised when point cloud reading, header parsing, or dimension validation fails."""
    pass


class EmptyPointCloudError(PointCloudError):
    """Raised when an input LAS/LAZ point cloud file contains zero points."""
    pass


class MissingDimensionError(PointCloudError):
    """Raised when a required point attribute (e.g. Red/Green/Blue, Intensity) is absent."""
    pass


class InvalidPointCloudFormatError(PointCloudError):
    """Raised when a LAS/LAZ point format or version is corrupt or unsupported."""
    pass


class InsufficientGroundPointsError(PointCloudError):
    """Raised when zero ground return points (Class 2) are found in the point cloud."""
    pass


class SpatialReferenceError(DroneGeoError):
    """Raised when CRS resolution, EPSG lookup, or coordinate projection fails."""
    pass


class AlignmentError(DroneGeoError):
    """Base exception for flightline overlap analysis and strip co-registration errors."""
    pass


class NoSpatialOverlapError(AlignmentError):
    """Raised when two flight strips do not intersect in horizontal coordinate space."""
    pass


class InsufficientOverlapDataError(AlignmentError):
    """Raised when overlapping area contains zero valid ground comparison cells."""
    pass


class SurfaceInterpolationError(DroneGeoError):
    """Raised when raster surface generation, k-NN IDW, or grid interpolation fails."""
    pass


class IncompatibleRasterDimensionsError(SurfaceInterpolationError):
    """Raised when two rasters (e.g. DSM and DTM) have mismatched dimensions or CRS for CHM calculation."""
    pass


class RasterIOError(DroneGeoError):
    """Raised when GeoTIFF raster reading, writing, or GeoTransform assignment fails."""
    pass


class ComputationError(DroneGeoError):
    """Raised when a numerical calculation (e.g. least-squares trend surface) fails to converge."""
    pass


class DatasetValidationError(DroneGeoError):
    """Raised when an input dataset or control file fails structural format validation."""
    pass
