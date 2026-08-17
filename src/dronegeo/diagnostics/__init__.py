"""
dronegeo.diagnostics
~~~~~~~~~~~~~~~~~~~~
Pre-processing diagnostic audits for strip misalignment, terrain anomalies,
and the automated "AutoQC" inspection & healing subsystem.
"""

from .strip_alignment import (
    StripAlignmentReport,
    StripAlignmentChecker,
    check_strip_alignment,
)
from .terrain_anomaly import (
    TerrainAnomalyReport,
    TerrainAnomalyDetector,
    detect_terrain_anomalies,
)
from .autoqc import (
    IssueSeverity,
    DiagnosticIssue,
    AutoQCReport,
    inspect_point_cloud,
    inspect_elevation_model,
    remediate_point_cloud,
    remediate_elevation_model,
    inspect,
    remediate,
)
from . import utils

__all__ = [
    "StripAlignmentReport",
    "StripAlignmentChecker",
    "check_strip_alignment",
    "TerrainAnomalyReport",
    "TerrainAnomalyDetector",
    "detect_terrain_anomalies",
    "IssueSeverity",
    "DiagnosticIssue",
    "AutoQCReport",
    "inspect_point_cloud",
    "inspect_elevation_model",
    "remediate_point_cloud",
    "remediate_elevation_model",
    "inspect",
    "remediate",
    "utils",
]
