"""
dronegeo.lidar
~~~~~~~~~~~~~~
Point cloud (LAS/LAZ) processing, strip alignment, terrain rectification, and pre-flight profiling.
"""

from .point_metrics import (
    PointCloudProfileReport,
    profile_point_cloud,
    plot_point_cloud_profile,
    compute_point_density,
)
from .strip_alignment import (
    align_and_merge_strips,
)
from .terrain_rectification import (
    compute_rectification_surface,
    rectify_point_cloud_elevation,
)

__all__ = [
    "PointCloudProfileReport",
    "profile_point_cloud",
    "plot_point_cloud_profile",
    "compute_point_density",
    "align_and_merge_strips",
    "compute_rectification_surface",
    "rectify_point_cloud_elevation",
]
