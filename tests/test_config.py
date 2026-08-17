"""
tests.test_config
~~~~~~~~~~~~~~~~~
Unit tests for dronegeo compute engine configuration and scoped context managers.
"""

import pytest
from dronegeo.config.compute import (
    ComputeConfig,
    get_compute_config,
    set_compute_config,
    set_compute_profile,
    compute_context,
)


def test_default_compute_config():
    """Verify default compute configuration defaults to safe system parameters."""
    cfg = get_compute_config()
    assert isinstance(cfg, ComputeConfig)
    assert cfg.n_jobs >= 1
    assert cfg.chunk_size > 0
    assert cfg.block_rows > 0


def test_set_compute_config():
    """Verify global compute configuration updates correctly."""
    original = get_compute_config()
    try:
        new_cfg = ComputeConfig(n_jobs=2, chunk_size=500_000, low_memory_mode=True)
        set_compute_config(new_cfg)
        active = get_compute_config()
        assert active.n_jobs == 2
        assert active.chunk_size == 500_000
        assert active.low_memory_mode is True
    finally:
        set_compute_config(original)


def test_compute_profiles():
    """Verify built-in profile presets (maximum, balanced, low_memory)."""
    original = get_compute_config()
    try:
        cfg_max = set_compute_profile("maximum")
        assert cfg_max.low_memory_mode is False
        assert cfg_max.chunk_size >= 1_000_000

        cfg_low = set_compute_profile("low_memory")
        assert cfg_low.low_memory_mode is True
        assert cfg_low.n_jobs <= 4

        with pytest.raises(ValueError):
            set_compute_profile("invalid_profile_name")
    finally:
        set_compute_config(original)


def test_scoped_compute_context():
    """Verify compute_context temporarily alters config and restores on exit."""
    original = get_compute_config()
    initial_n_jobs = original.n_jobs

    with compute_context(n_jobs=1, chunk_size=100_000, low_memory_mode=True):
        scoped = get_compute_config()
        assert scoped.n_jobs == 1
        assert scoped.chunk_size == 100_000
        assert scoped.low_memory_mode is True

    # Check restored state
    restored = get_compute_config()
    assert restored.n_jobs == initial_n_jobs
