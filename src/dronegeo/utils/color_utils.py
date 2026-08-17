"""
dronegeo.utils.color_utils
~~~~~~~~~~~~~~~~~~~~~~~~~~
Pre-configured color ramps and custom colormaps for elevation, slope, and vegetation visualization.
"""

from __future__ import annotations
from typing import List, Tuple, Union

import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, ListedColormap


def get_elevation_colormap(name: str = "terrain") -> LinearSegmentedColormap:
    """
    Returns a standardized Matplotlib colormap for digital elevation models.

    Options: 'terrain', 'gist_earth', 'viridis', 'magma', 'turbo'.

    Example:
        >>> from dronegeo.utils import get_elevation_colormap
        >>> cmap = get_elevation_colormap("terrain")
    """
    return plt.get_cmap(name)


def get_vegetation_colormap() -> LinearSegmentedColormap:
    """
    Returns a custom Green-Yellow-Brown colormap optimized for photogrammetric vegetation index maps (VARI, GLI).

    Example:
        >>> from dronegeo.utils import get_vegetation_colormap
        >>> veg_cmap = get_vegetation_colormap()
    """
    colors = ["#7F4F24", "#DDA15E", "#E9D8A6", "#94D2BD", "#0A9396", "#005F73", "#1B4332"]
    return LinearSegmentedColormap.from_list("dronegeo_vegetation", colors, N=256)


def create_custom_diverging_colormap(
    neg_color: str = "#2B5C8F",
    mid_color: str = "#F7F7F7",
    pos_color: str = "#C23B22",
    name: str = "custom_diverging",
) -> LinearSegmentedColormap:
    """
    Creates a 3-stop diverging colormap for Cut/Fill and elevation change (ΔZ) residual plots.

    Example:
        >>> from dronegeo.utils import create_custom_diverging_colormap
        >>> cut_fill_cmap = create_custom_diverging_colormap(neg_color="blue", mid_color="white", pos_color="red")
    """
    return LinearSegmentedColormap.from_list(name, [neg_color, mid_color, pos_color], N=256)
