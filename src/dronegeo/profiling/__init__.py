"""
dronegeo.profiling
~~~~~~~~~~~~~~~~~~
Elevation transects, diagnostic QC visualizations, difference maps, and survey grid chip tiling.
"""

from .elevation_transects import (
    extract_orthogonal_transects,
    plot_elevation_transects,
)
from .diagnostic_plots import (
    plot_strip_overlap_residuals,
    plot_anomaly_heatmap,
    plot_before_after_comparison,
)
from .grid_tiling import (
    map_grid_chips,
)

__all__ = [
    "extract_orthogonal_transects",
    "plot_elevation_transects",
    "plot_strip_overlap_residuals",
    "plot_anomaly_heatmap",
    "plot_before_after_comparison",
    "map_grid_chips",
]
