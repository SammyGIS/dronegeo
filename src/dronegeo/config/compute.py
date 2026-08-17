"""
dronegeo.config.compute
~~~~~~~~~~~~~~~~~~~~~~~
CPU thread pool allocation, RAM chunking sizes, hardware profiles, and execution context managers.
"""

from __future__ import annotations
import os
import gc
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Optional, Literal, Generator, Union


@dataclass
class ComputeConfig:
    """
    Hardware and memory execution settings for dronegeo operations.

    Real-World Applications:
        - Workstation Acceleration: Unlocking all CPU cores on 16/32/64-thread workstations for rapid k-NN queries.
        - Field Laptop Execution: Throttling RAM chunks and thread allocations to prevent out-of-memory
          crashes when processing large surveys on 8GB/16GB laptops.

    When to Use:
        Configure globally via `set_compute_profile()` or locally inside a `compute_context()` block.

    Attributes:
        n_jobs: Number of CPU worker threads to use for parallel tasks (e.g. k-NN searches).
                -1 uses all available CPU cores. Default is auto-detected.
        chunk_size: Number of LAS/LAZ points processed per memory chunk during streaming.
                    Default is 2,500,000 points.
        block_rows: Number of raster rows processed per memory block in DEM generation.
                    Default is 2048 rows.
        low_memory_mode: If True, triggers immediate garbage collection and avoids large
                         intermediate array allocations. Default is False.

    Example:
        >>> from dronegeo.config import ComputeConfig
        >>> cfg = ComputeConfig(n_jobs=8, chunk_size=3_000_000, low_memory_mode=False)
    """
    n_jobs: int = -1
    chunk_size: int = 2_500_000
    block_rows: int = 2048
    low_memory_mode: bool = False

    def __post_init__(self):
        total_cores = os.cpu_count() or 4
        if isinstance(self.n_jobs, int):
            if self.n_jobs == -1 or self.n_jobs <= 0:
                self.n_jobs = total_cores
            elif self.n_jobs > total_cores:
                self.n_jobs = total_cores
        else:
            self.n_jobs = total_cores

        assert self.chunk_size >= 100_000, f"chunk_size must be >= 100,000, got {self.chunk_size}"
        assert self.block_rows >= 64, f"block_rows must be >= 64, got {self.block_rows}"


_ACTIVE_CONFIG = ComputeConfig()


def get_compute_config() -> ComputeConfig:
    """
    Returns a copy of the active global compute configuration.

    Example:
        >>> import dronegeo as dg
        >>> cfg = dg.get_compute_config()
        >>> print(f"Active CPU workers: {cfg.n_jobs}, Chunk size: {cfg.chunk_size:,}")
    """
    return ComputeConfig(
        n_jobs=_ACTIVE_CONFIG.n_jobs,
        chunk_size=_ACTIVE_CONFIG.chunk_size,
        block_rows=_ACTIVE_CONFIG.block_rows,
        low_memory_mode=_ACTIVE_CONFIG.low_memory_mode,
    )


def set_compute_config(
    n_jobs: Optional[Union[int, ComputeConfig]] = None,
    chunk_size: Optional[int] = None,
    block_rows: Optional[int] = None,
    low_memory_mode: Optional[bool] = None,
) -> ComputeConfig:
    """
    Sets global compute and hardware parameters for dronegeo.

    Supports passing either individual parameters or a ComputeConfig instance as the first argument.

    Real-World Applications:
        - Custom Hardware Tuning: Allocating specific CPU threads and RAM batch sizes.

    Args:
        n_jobs: Number of CPU cores to allocate (-1 for all cores) or a ComputeConfig instance.
        chunk_size: Point cloud stream chunk size (e.g. 2_500_000).
        block_rows: Raster block height in rows (e.g. 2048).
        low_memory_mode: Enable aggressive memory saving.

    Returns:
        The updated ComputeConfig.

    Example:
        >>> import dronegeo as dg
        >>> dg.set_compute_config(n_jobs=8, chunk_size=3_000_000)
    """
    global _ACTIVE_CONFIG
    if isinstance(n_jobs, ComputeConfig):
        _ACTIVE_CONFIG.n_jobs = n_jobs.n_jobs
        _ACTIVE_CONFIG.chunk_size = n_jobs.chunk_size
        _ACTIVE_CONFIG.block_rows = n_jobs.block_rows
        _ACTIVE_CONFIG.low_memory_mode = n_jobs.low_memory_mode
    else:
        if n_jobs is not None:
            _ACTIVE_CONFIG.n_jobs = n_jobs
        if chunk_size is not None:
            _ACTIVE_CONFIG.chunk_size = chunk_size
        if block_rows is not None:
            _ACTIVE_CONFIG.block_rows = block_rows
        if low_memory_mode is not None:
            _ACTIVE_CONFIG.low_memory_mode = low_memory_mode

    _ACTIVE_CONFIG.__post_init__()
    return get_compute_config()


def reset_compute_config() -> ComputeConfig:
    """
    Resets the global compute configuration to system default values.
    """
    global _ACTIVE_CONFIG
    _ACTIVE_CONFIG = ComputeConfig()
    return get_compute_config()


def set_compute_profile(profile: Literal["maximum", "balanced", "low_memory"]) -> ComputeConfig:
    """
    Applies a pre-configured hardware profile.

    Real-World Applications:
        - "maximum": For dedicated desktop workstations with 32GB+ RAM to minimize processing time.
        - "balanced": Standard production mode using 75% of available CPU cores.
        - "low_memory": For field laptops with 8GB/16GB RAM to prevent memory saturation and system lag.

    Args:
        profile: One of "maximum", "balanced", or "low_memory".

    Returns:
        The newly configured ComputeConfig.

    Example:
        >>> import dronegeo as dg
        >>> dg.set_compute_profile("maximum")
    """
    total_cores = os.cpu_count() or 4
    if profile == "maximum":
        return set_compute_config(
            n_jobs=total_cores,
            chunk_size=5_000_000,
            block_rows=4096,
            low_memory_mode=False,
        )
    elif profile == "balanced":
        balanced_cores = max(1, int(total_cores * 0.75))
        return set_compute_config(
            n_jobs=balanced_cores,
            chunk_size=2_500_000,
            block_rows=2048,
            low_memory_mode=False,
        )
    elif profile == "low_memory":
        return set_compute_config(
            n_jobs=min(4, max(1, total_cores // 2)),
            chunk_size=1_000_000,
            block_rows=1024,
            low_memory_mode=True,
        )
    else:
        raise ValueError(f"Unknown profile: {profile}. Must be 'maximum', 'balanced', or 'low_memory'.")


@contextmanager
def compute_context(
    n_jobs: Optional[int] = None,
    chunk_size: Optional[int] = None,
    block_rows: Optional[int] = None,
    low_memory_mode: Optional[bool] = None,
) -> Generator[ComputeConfig, None, None]:
    """
    Scoped context manager that temporarily adjusts compute settings and safely restores previous settings on exit.

    Real-World Applications:
        - Fine-Grained Memory Budgeting: Running memory-heavy steps (e.g. k-NN IDW DTM) in low-memory mode
          without permanently modifying global settings for downstream lightweight steps.

    Example:
        >>> import dronegeo as dg
        >>> with dg.compute_context(n_jobs=4, low_memory_mode=True):
        ...     dtm = dg.dem.create_dtm("survey.laz", "dtm.tif")
    """
    previous_config = get_compute_config()
    try:
        yield set_compute_config(
            n_jobs=n_jobs,
            chunk_size=chunk_size,
            block_rows=block_rows,
            low_memory_mode=low_memory_mode,
        )
    finally:
        set_compute_config(previous_config)


def collect_garbage_if_needed(config: Optional[ComputeConfig] = None) -> None:
    """
    Triggers explicit garbage collection if low_memory_mode is active.
    """
    active = config or get_compute_config()
    if active.low_memory_mode:
        gc.collect()
