# Hydrology & Flood Risk Modeling

Simulate watershed drainage paths, stream channel formation, soil moisture saturation, and landslide susceptibility from high-resolution drone elevation models.

---

## The Hydrological Risk Indices Explained

| Index | Formula | What It Means in Plain English | Primary Application |
| :--- | :--- | :--- | :--- |
| **D8 Flow Direction** | Steepest descent to 8 neighbors | Determines which adjacent pixel water flows to. | Watershed delineation & drainage paths |
| **D-Infinity Flow ($D_\infty$)** | Continuous triangular facets ($0-2\pi$) | Allows water to disperse across two downward slope facets. | Diffuse runoff & soil erosion modeling |
| **Flow Accumulation** | Cumulative upslope pixel count | Measures total drainage area feeding into each pixel. | Stream channel & valley extraction |
| **Topographic Wetness Index (TWI)** | $\ln(a / \tan \beta)$ | High TWI indicates flat valley depressions where water ponds. | Flood risk & wetland mapping |
| **Stream Power Index (SPI)** | $a \cdot \tan \beta$ | Measures erosive power of flowing surface runoff. | Culvert placement & gully erosion risk |
| **Sediment Transport Index (STI)** | $(a / 22.13)^{0.6} \cdot (\sin \beta / 0.0896)^{1.3}$ | Evaluates hillslope soil carrying capacity (USLE LS 3D factor). | Agricultural soil conservation & silt fencing |
| **Landslide Hazard Score** | Multi-criteria normalized [0-100] | Flags steep slopes with high wetness and convergent curvature. | Slope failure & landslide hazard zonation |

---

## Python Code Examples

```python
import dronegeo as dg

# 1. Flow Directions (D8 and D-Infinity)
dg.hydrology.compute_d8_flow_direction("dtm.tif", "flow_direction_d8.tif")
dg.hydrology.compute_dinfinity_flow_direction("dtm.tif", "flow_direction_dinf.tif")

# 2. Flow Accumulation & Stream Network
accum = dg.hydrology.compute_flow_accumulation("dtm.tif", "accum.tif")
streams = dg.hydrology.extract_stream_network(accum, "streams.tif", threshold_cells=200)

# 3. Environmental Risk Indices (TWI, SPI, STI, Landslide)
twi = dg.hydrology.compute_topographic_wetness_index("dtm.tif", "twi.tif")
spi = dg.hydrology.compute_stream_power_index("dtm.tif", "spi.tif")
sti = dg.hydrology.compute_sediment_transport_index("dtm.tif", "sti.tif")
hazard = dg.hydrology.compute_landslide_susceptibility_index("dtm.tif", "landslide_hazard.tif")
```
