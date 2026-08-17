"""
tests.test_core
~~~~~~~~~~~~~~~
Unit tests for dronegeo core exception hierarchy and abstract base classes.
"""

import pytest
from dronegeo.core.exceptions import (
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
from dronegeo.core.base import (
    BaseDiagnostic,
    BaseSurfaceGenerator,
    BasePointCloudFilter,
    BaseProfiler,
)


def test_exception_inheritance():
    """Verify all custom exceptions derive from DroneGeoError and standard built-ins."""
    assert issubclass(PointCloudError, DroneGeoError)
    assert issubclass(EmptyPointCloudError, PointCloudError)
    assert issubclass(MissingDimensionError, PointCloudError)
    assert issubclass(InvalidPointCloudFormatError, PointCloudError)
    assert issubclass(InsufficientGroundPointsError, PointCloudError)
    
    assert issubclass(SpatialReferenceError, DroneGeoError)
    assert issubclass(AlignmentError, DroneGeoError)
    assert issubclass(NoSpatialOverlapError, AlignmentError)
    assert issubclass(InsufficientOverlapDataError, AlignmentError)
    
    assert issubclass(SurfaceInterpolationError, DroneGeoError)
    assert issubclass(IncompatibleRasterDimensionsError, DroneGeoError)
    assert issubclass(RasterIOError, DroneGeoError)
    assert issubclass(ComputationError, DroneGeoError)


def test_exception_raising_and_messages():
    """Verify exceptions format custom error messages properly."""
    with pytest.raises(EmptyPointCloudError) as exc_info:
        raise EmptyPointCloudError("Point cloud file 'survey.las' has 0 points.")
    assert "0 points" in str(exc_info.value)

    with pytest.raises(NoSpatialOverlapError) as exc_info:
        raise NoSpatialOverlapError("Strips strip1.las and strip2.las share 0% overlap.")
    assert "0% overlap" in str(exc_info.value)


def test_base_abstract_classes():
    """Verify abstract base classes cannot be instantiated directly without implementing abstract methods."""
    with pytest.raises(TypeError):
        BaseDiagnostic()

    with pytest.raises(TypeError):
        BaseSurfaceGenerator()

    with pytest.raises(TypeError):
        BasePointCloudFilter()

    with pytest.raises(TypeError):
        BaseProfiler()
