# 🌊 Hydrology & Flood Risk Modeling

Terrain hydrology and environmental risk algorithms based on peer-reviewed scientific literature.

---

## 🔬 Supported Algorithms & Literature References

1. **D8 Flow Direction**: O'Callaghan & Mark (1984) - *Deterministic 8-neighbor steepest descent*.
2. **D-Infinity Flow Direction**: Tarboton (1997) - *Continuous flow angle ($0 - 2\pi$ rad)*.
3. **Flow Accumulation**: Jenson & Domingue (1988) - *Upslope contributing catchment drainage area*.
4. **Topographic Wetness Index (TWI)**: Beven & Kirkby (1979) - *Soil saturation and flood pooling potential*.
5. **Stream Power Index (SPI)**: Moore et al. (1991) - *Channel scouring and runoff erosion power*.
6. **Sediment Transport Index (STI / USLE LS)**: Moore & Burch (1986) - *Hillslope soil loss risk*.
7. **Landslide Susceptibility Hazard Model**: Montgomery & Dietrich (1994) - *Multi-criteria slope failure hazard score*.

---

## 💻 Python Example

```python
import dronegeo as dg

# D8 and D-Infinity Flow Directions
dg.hydrology.compute_d8_flow_direction("dtm.tif", "flow_d8.tif")
dg.hydrology.compute_dinfinity_flow_direction("dtm.tif", "flow_dinf.tif")

# Flow Accumulation & Stream Network
dg.hydrology.compute_flow_accumulation("dtm.tif", "accum.tif")
dg.hydrology.extract_stream_network("accum.tif", "streams.tif", threshold_cells=200)

# Topographic Wetness Index (TWI) & Landslide Hazard
dg.hydrology.compute_topographic_wetness_index("dtm.tif", "twi.tif")
dg.hydrology.compute_landslide_susceptibility_index("dtm.tif", "landslide_hazard.tif")
```
