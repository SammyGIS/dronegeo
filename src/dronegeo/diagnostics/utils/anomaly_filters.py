"""
dronegeo.diagnostics.utils.anomaly_filters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Filtering algorithms for statistical point cloud noise and DEM surface spikes.
"""

from __future__ import annotations
import numpy as np
from scipy.ndimage import distance_transform_edt, median_filter


def filter_elevation_outliers(
    z_coords: np.ndarray,
    z_min_cutoff: float | None = None,
    z_max_cutoff: float | None = None,
) -> np.ndarray:
    """Returns a boolean mask of valid point elevations within the cutoff envelope."""
    mask = np.ones(len(z_coords), dtype=bool)
    if z_min_cutoff is not None:
        mask &= (z_coords >= z_min_cutoff)
    if z_max_cutoff is not None:
        mask &= (z_coords <= z_max_cutoff)
    return mask


def smooth_terrain_spikes(
    elevation_grid: np.ndarray,
    invalid_mask: np.ndarray,
    spike_threshold_m: float = 10.0,
    kernel_size: int = 3,
) -> np.ndarray:
    """Applies adaptive median filtering to remove sharp spike artifacts while preserving valid relief."""
    output_grid = elevation_grid.copy()
    valid_mask = ~invalid_mask

    if np.any(valid_mask):
        med = median_filter(output_grid, size=kernel_size)
        diff = np.abs(output_grid - med)
        spike_mask = (diff > spike_threshold_m) & valid_mask
        output_grid[spike_mask] = med[spike_mask]

    return output_grid


def infill_nodata_holes(
    elevation_grid: np.ndarray,
    invalid_mask: np.ndarray,
) -> np.ndarray:
    """Infills NoData holes using smooth nearest-neighbor distance transform propagation."""
    output_grid = elevation_grid.copy()
    if np.any(invalid_mask) and not np.all(invalid_mask):
        indices = distance_transform_edt(invalid_mask, return_distances=False, return_indices=True)
        output_grid[invalid_mask] = elevation_grid[tuple(indices)][invalid_mask]
    return output_grid
