---
title: 'PyFlowTerrain: High-Resolution Hydrological Flow Routing and Topographic Wetness Index Modeling in Python'
tags:
  - Python
  - hydrology
  - digital elevation models
  - terrain analysis
  - flood modeling
authors:
  - name: Computational Hydrologist
    orcid: 0000-0000-0000-0000
    affiliation: 1
affiliations:
  - name: Department of Water Resources and Hydroinformatics
    index: 1
date: 20 June 2025
bibliography: paper.bib
---

# Summary

Digital Elevation Models (DEMs) derived from drone photogrammetry and airborne LiDAR provide ultra-high spatial resolution terrain grids. Calculating hydrologic flow routing, catchment boundaries, and saturation indices on these fine-scale grids is critical for flood risk assessment and agricultural nutrient runoff modeling. `PyFlowTerrain` is a high-performance Python package implementing single-flow direction (D8) and multi-flow direction (D-infinity) accumulation algorithms directly integrated with standard raster formats.

# Statement of Need

Hydro-geomorphic analyses often rely on legacy FORTRAN or C++ libraries (such as TauDEM or SAGA GIS) that are difficult to embed into continuous automated pipelines or cloud Jupyter environments. `PyFlowTerrain` delivers vectorized NumPy and SciPy implementations of critical terrain indices—including Topographic Wetness Index (TWI), Stream Power Index (SPI), and Sediment Transport Index (STI)—with memory-efficient tile streaming.

# Comparison with Existing Ecosystem

| Feature | `PyFlowTerrain` | `RichDEM` | `WhiteboxTools` |
| :--- | :---: | :---: | :---: |
| **D8 / D-infinity Routing** | ✅ | ✅ | ✅ |
| **Topographic Wetness (TWI)** | ✅ | ❌ | ✅ |
| **Stream Power Index (SPI)** | ✅ | ❌ | ✅ |
| **Native NumPy Array API** | ✅ | ❌ | ❌ |

# Example Usage

```python
import pyflowterrain as pft
import rasterio

# Load high-resolution DTM
with rasterio.open("high_res_dem.tif") as src:
    dem = src.read(1)
    transform = src.transform

# Calculate D-infinity flow accumulation and TWI
flow_acc = pft.accumulate_d_infinity(dem, transform=transform)
twi = pft.compute_twi(dem, flow_acc, transform=transform)
```

# Acknowledgements

The authors acknowledge the foundational work by Tarboton (1997) and Moore et al. (1991) in digital elevation hydrological modeling.

# References
