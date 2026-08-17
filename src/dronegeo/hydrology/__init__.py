"""
dronegeo.hydrology
~~~~~~~~~~~~~~~~~~
Hydrological flow routing, stream extraction, erosion risk indices (SPI, STI),
Topographic Wetness Index (TWI), and landslide hazard susceptibility modeling.

Scientific Citations:
- Beven & Kirkby (1979) - Topographic Wetness Index (TWI/CTI)
- O'Callaghan & Mark (1984) - D8 Flow Direction & Drainage Extraction
- Tarboton (1997) - D-Infinity Continuous Flow Algorithm
- Moore et al. (1991) - Stream Power Index (SPI)
- Moore & Burch (1986) - Sediment Transport Index (STI / LS factor)
- Montgomery & Dietrich (1994) - Topographic Landslide & Slope Failure Model
"""

from .flow_direction import (
    compute_d8_flow_direction,
    compute_dinfinity_flow_direction,
)
from .flow_accumulation import (
    compute_flow_accumulation,
    extract_stream_network,
)
from .risk_indices import (
    compute_topographic_wetness_index,
    compute_stream_power_index,
    compute_sediment_transport_index,
    compute_landslide_susceptibility_index,
)

__all__ = [
    "compute_d8_flow_direction",
    "compute_dinfinity_flow_direction",
    "compute_flow_accumulation",
    "extract_stream_network",
    "compute_topographic_wetness_index",
    "compute_stream_power_index",
    "compute_sediment_transport_index",
    "compute_landslide_susceptibility_index",
]
