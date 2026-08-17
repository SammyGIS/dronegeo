"""
dronegeo.config
~~~~~~~~~~~~~~~
Hardware resource management, compute configuration, and scoped context managers.
"""

from .compute import (
    ComputeConfig,
    set_compute_config,
    get_compute_config,
    set_compute_profile,
    reset_compute_config,
    compute_context,
)

__all__ = [
    "ComputeConfig",
    "set_compute_config",
    "get_compute_config",
    "set_compute_profile",
    "reset_compute_config",
    "compute_context",
]
