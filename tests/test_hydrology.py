"""
tests.test_hydrology
~~~~~~~~~~~~~~~~~~~~
Unit tests for hydrological flow routing (D8, D-inf), accumulation,
Topographic Wetness Index (TWI), Stream Power (SPI), Sediment Transport (STI),
and Landslide Susceptibility Hazard modeling.
"""

import os
import pytest
import numpy as np
import rasterio
from dronegeo.hydrology.flow_direction import (
    compute_d8_flow_direction,
    compute_dinfinity_flow_direction,
)
from dronegeo.hydrology.flow_accumulation import (
    compute_flow_accumulation,
    extract_stream_network,
)
from dronegeo.hydrology.risk_indices import (
    compute_topographic_wetness_index,
    compute_stream_power_index,
    compute_sediment_transport_index,
    compute_landslide_susceptibility_index,
)


def test_d8_and_dinfinity_flow_direction(synthetic_dem_tif, temp_workspace):
    """Verify D8 and D-Infinity flow direction calculation."""
    d8_tif = temp_workspace / "flow_d8.tif"
    dinf_tif = temp_workspace / "flow_dinf.tif"

    res_d8 = compute_d8_flow_direction(synthetic_dem_tif, str(d8_tif))
    res_dinf = compute_dinfinity_flow_direction(synthetic_dem_tif, str(dinf_tif))

    assert os.path.exists(res_d8)
    assert os.path.exists(res_dinf)

    with rasterio.open(res_d8) as src:
        assert src.dtypes[0] == "uint8"
        data = src.read(1)
        # Valid D8 codes: 0, 1, 2, 4, 8, 16, 32, 64, 128
        valid_codes = {0, 1, 2, 4, 8, 16, 32, 64, 128}
        assert set(np.unique(data)).issubset(valid_codes)


def test_flow_accumulation_and_stream_extraction(synthetic_dem_tif, temp_workspace):
    """Verify flow accumulation and channel extraction."""
    accum_tif = temp_workspace / "accum.tif"
    stream_tif = temp_workspace / "streams.tif"

    res_accum = compute_flow_accumulation(synthetic_dem_tif, str(accum_tif), units="cells")
    assert os.path.exists(res_accum)

    with rasterio.open(res_accum) as src:
        data = src.read(1)
        valid = data[data != src.nodata]
        assert len(valid) > 0
        assert valid.min() >= 1.0  # Each cell has at least itself

    res_stream = extract_stream_network(str(accum_tif), str(stream_tif), threshold_cells=50)
    assert os.path.exists(res_stream)


def test_hydrological_risk_indices(synthetic_dem_tif, temp_workspace):
    """Verify TWI, SPI, STI, and Landslide Susceptibility calculations."""
    twi_tif = temp_workspace / "twi.tif"
    spi_tif = temp_workspace / "spi.tif"
    sti_tif = temp_workspace / "sti.tif"
    hazard_tif = temp_workspace / "landslide_hazard.tif"

    assert os.path.exists(compute_topographic_wetness_index(synthetic_dem_tif, str(twi_tif)))
    assert os.path.exists(compute_stream_power_index(synthetic_dem_tif, str(spi_tif)))
    assert os.path.exists(compute_sediment_transport_index(synthetic_dem_tif, str(sti_tif)))
    assert os.path.exists(compute_landslide_susceptibility_index(synthetic_dem_tif, str(hazard_tif)))

    with rasterio.open(str(twi_tif)) as src:
        data = src.read(1)
        valid = data[data != src.nodata]
        assert len(valid) > 0

    with rasterio.open(str(hazard_tif)) as src:
        data = src.read(1)
        valid = data[data != 255]
        assert len(valid) > 0
        assert valid.min() >= 0
        assert valid.max() <= 100
