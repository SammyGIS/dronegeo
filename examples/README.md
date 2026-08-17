# 🛸 DroneGeo Examples & Tutorials

This directory contains standalone, fully runnable example scripts and an interactive Jupyter Notebook showcasing `dronegeo` workflows from raw drone point clouds to survey-grade deliverables.

---

## 📂 Quick Start & Execution

First, generate the canonical sample datasets once using script `00`:

```bash
# 1. Generate all canonical sample LiDAR & raster datasets
python examples/00_generate_sample_datasets.py
```

All sample datasets will be stored in `examples/data/`. Downstream example scripts automatically consume these files and write output GeoTIFFs, PNG plots, and GeoJSON files to `examples/outputs/`.

---

## 🚀 Examples Catalog

| Script | Title | Description | Key Outputs |
| :--- | :--- | :--- | :--- |
| **`00_generate_sample_datasets.py`** | *Sample Dataset Generator* | Creates canonical 50k pt LAS clouds, multi-strip passes ($\\Delta Z$), and multi-epoch quarry DEMs. | `examples/data/*.las`, `*.tif`, `*.geojson` |
| **`01_point_cloud_audit.py`** | *Point Cloud QC Audit* | Audits point density ($pts/m^2$), pulse returns, classifications, and generates multi-panel QC dashboard. | `point_cloud_qc_dashboard.png` |
| **`02_strip_alignment_and_merging.py`** | *Flightline Co-Registration* | Detects median vertical offset ($\\Delta Z$) across overlapping flight passes and merges into unified master cloud. | `master_unified_cloud.las`, `overlap_residuals_histogram.png` |
| **`03_surface_models_dtm_dsm_chm.py`** | *Survey-Grade Surface Models* | Multi-threaded $k$-NN IDW continuous DTM, Maximum Surface DSM, and Canopy Height Models (CHM). | `survey_dtm.tif`, `survey_dsm.tif`, `canopy_height_model.tif` |
| **`04_orthomosaic_and_vegetation_indices.py`** | *True-Color Orthos & Indices* | 4-band RGBA True-Color Orthomosaic with auto-contrast, VARI, GLI, TGI, and ExG crop health maps. | `true_color_orthomosaic.tif`, `vegetation_vari.tif`, `vegetation_gli.tif` |
| **`05_terrain_morphology_and_contours.py`** | *Morphology & Contours* | 8-bit analytical hillshade (Horn 315°), slope (deg), aspect compass heading, TRI, and 1m vector contours. | `hillshade_315_45.tif`, `slope_degrees.tif`, `contour_lines_1m.geojson` |
| **`06_earthwork_cut_fill_volumetrics.py`** | *3D Earthwork Volumetrics* | Differential 3D Cut & Fill earthwork volumes ($m^3$) between survey epochs and stockpile volume audits. | `quarry_elevation_difference.tif` |
| **`07_elevation_transects_and_qc.py`** | *Transect Profiles & Chip Maps* | 1D/2D cross-sectional topographic profiles and survey vector tile grid chip indexing maps. | `elevation_transect_profiles.png`, `survey_grid_chips_map.png` |
| **`08_hydrological_flow_and_risk_modeling.py`** | *Hydrology & Risk Modeling* | D8, $D_\\infty$, flow accumulation, TWI, Stream Power Index (SPI), Sediment Transport (STI), and landslide hazard index. | `flow_direction_d8.tif`, `topographic_wetness_index_twi.tif`, `landslide_susceptibility_hazard.tif` |

---

## 📓 Interactive Jupyter Tutorial

Launch the end-to-end interactive notebook:

```bash
jupyter notebook examples/dronegeo_interactive_tutorial.ipynb
```

---

## 🔬 Scientific Literature References for Risk & Hydrology

- **D8 Algorithm**: O'Callaghan, J. F., & Mark, D. M. (1984). *The extraction of drainage networks from digital elevation data*. Computer Vision, Graphics, and Image Processing, 28(3), 323-344.
- **D-Infinity Algorithm**: Tarboton, D. G. (1997). *A new method for the determination of flow directions and upslope areas in grid digital elevation models*. Water Resources Research, 33(2), 309-319.
- **Topographic Wetness Index (TWI / CTI)**: Beven, K. J., & Kirkby, M. J. (1979). *A physically based, variable contributing area model of basin hydrology*. Hydrological Sciences Bulletin, 24(1), 43-69.
- **Stream Power Index (SPI)**: Moore, I. D., Grayson, R. B., & Ladson, A. R. (1991). *Digital terrain modelling: A review of hydrological, geomorphological, and biological applications*. Hydrological Processes, 5(1), 3-30.
- **Sediment Transport Index (STI / USLE LS)**: Moore, I. D., & Burch, G. J. (1986). *Physical basis of the length-slope factor in the Universal Soil Loss Equation*. Soil Science Society of America Journal, 50(5), 1294-1298.
- **Landslide Susceptibility Hazard Model**: Montgomery, D. R., & Dietrich, W. E. (1994). *A physically based model for the topographic control on shallow landsliding*. Water Resources Research, 30(4), 1153-1171.
