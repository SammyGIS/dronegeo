"""
dronegeo.core.base
~~~~~~~~~~~~~~~~~~
Abstract Base Classes (ABCs) and core interfaces for dronegeo processors,
surface generators, point cloud filters, and diagnostic analyzers.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Union, Optional, Dict, Any, Tuple
import numpy as np

from ..config.compute import ComputeConfig, get_compute_config


class BaseDiagnostic(ABC):
    """
    Abstract Base Class for all pre-processing quality control and anomaly detectors.
    """

    def __init__(self, config: Optional[ComputeConfig] = None):
        self.config = config or get_compute_config()

    @abstractmethod
    def run_check(self, *args, **kwargs) -> Any:
        """
        Executes the diagnostic inspection and returns a structured report dataclass.
        """
        pass


class BaseSurfaceGenerator(ABC):
    """
    Abstract Base Class for all DEM, DSM, DTM, CHM, and Orthomosaic surface interpolators.
    """

    def __init__(
        self,
        resolution: float = 0.118,
        footprint_buffer: float = 3.0,
        config: Optional[ComputeConfig] = None,
    ):
        assert resolution > 0, f"Resolution must be positive, got {resolution}"
        assert footprint_buffer >= 0, f"Footprint buffer must be non-negative, got {footprint_buffer}"

        self.resolution = float(resolution)
        self.footprint_buffer = float(footprint_buffer)
        self.config = config or get_compute_config()

    @abstractmethod
    def generate(
        self,
        las_path: Union[str, Path],
        output_path: Union[str, Path],
        **kwargs
    ) -> str:
        """
        Generates a surface raster from an input LAS/LAZ point cloud.

        Args:
            las_path: Source LAS/LAZ point cloud file path.
            output_path: Target GeoTIFF destination path.

        Returns:
            Absolute string path to the created raster GeoTIFF.
        """
        pass


class BasePointCloudFilter(ABC):
    """
    Abstract Base Class for point cloud filters, datum transformers, and rectifiers.
    """

    def __init__(self, config: Optional[ComputeConfig] = None):
        self.config = config or get_compute_config()

    @abstractmethod
    def apply(
        self,
        input_path: Union[str, Path],
        output_path: Union[str, Path],
        **kwargs
    ) -> str:
        """
        Applies point transformation or filtering and writes output point cloud.
        """
        pass


class BaseProfiler(ABC):
    """
    Abstract Base Class for 1D/2D topographic profilers and cross-section extractors.
    """

    @abstractmethod
    def extract_profile(
        self,
        dem_path: Union[str, Path],
        **kwargs
    ) -> Any:
        """
        Extracts 1D/2D cross-sectional elevation data from a raster.
        """
        pass

    @abstractmethod
    def plot_profile(
        self,
        dem_path: Union[str, Path],
        output_png: Union[str, Path],
        **kwargs
    ) -> str:
        """
        Generates and saves a visual profile plot.
        """
        pass
