<p align="center">
  <img src="https://raw.githubusercontent.com/SammyGIS/dronegeo/main/docs/images/dronegeo.png" width="240" alt="dronegeo logo" />
</p>

<h1 align="center">dronegeo</h1>

<p align="center">
  <b>High-Performance Python Remote Sensing, UAV LiDAR, Hydrological Flow & Photogrammetry Processing Toolkit</b>
</p>

<p align="center">
  <a href="https://pypi.org/project/dronegeo/"><img src="https://img.shields.io/pypi/v/dronegeo?style=for-the-badge&logo=pypi&color=007ec6" alt="PyPI Version" /></a>
  <a href="https://python.org"><img src="https://img.shields.io/pypi/pyversions/dronegeo?style=for-the-badge&logo=python&color=3776AB" alt="Python Version" /></a>
  <a href="https://sammygis.github.io/dronegeo/"><img src="https://img.shields.io/badge/Live%20Docs-GitHub%20Pages-teal?style=for-the-badge&logo=materialformkdocs" alt="GitHub Pages" /></a>
  <a href="https://github.com/SammyGIS/dronegeo/actions"><img src="https://img.shields.io/badge/Tests-54%20Passed%20(100%25)-brightgreen?style=for-the-badge&logo=pytest" alt="Tests" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge" alt="License" /></a>
  <a href="#"><img src="https://img.shields.io/badge/Engine-Multi--Threaded%20k--NN-orange?style=for-the-badge" alt="Engine" /></a>
</p>

<p align="center">
  <a href="https://sammygis.github.io/dronegeo/autoqc/"><img src="https://img.shields.io/badge/AutoQC-Diagnostic%20%26%20Healing-00c853?style=flat-square" alt="AutoQC" /></a>
  <a href="https://sammygis.github.io/dronegeo/autoqc/"><img src="https://img.shields.io/badge/GCP%20Audit-ASPRS%20%7C%20NSSDA%2095%25-00e676?style=flat-square" alt="GCP Audit" /></a>
  <a href="https://sammygis.github.io/dronegeo/surfaces/"><img src="https://img.shields.io/badge/DTM%20%26%20DSM-Survey%20Grade%200.10m-2979ff?style=flat-square" alt="DTM" /></a>
  <a href="https://sammygis.github.io/dronegeo/api/profiling/"><img src="https://img.shields.io/badge/Elevation%20Profiles-Cross--Sections-ff4081?style=flat-square" alt="Elevation Profiles" /></a>
  <a href="https://sammygis.github.io/dronegeo/hydrology/"><img src="https://img.shields.io/badge/Hydrology-D8%20%7C%20D--Infinity%20%7C%20TWI-00b0ff?style=flat-square" alt="Hydrology" /></a>
  <a href="https://sammygis.github.io/dronegeo/imagery/"><img src="https://img.shields.io/badge/Orthomosaic-4--Band%20RGBA-aa00ff?style=flat-square" alt="Orthomosaic" /></a>
  <a href="https://sammygis.github.io/dronegeo/volumetrics/"><img src="https://img.shields.io/badge/Volumetrics-3D%20Cut%20%26%20Fill-ff9100?style=flat-square" alt="Volumetrics" /></a>
</p>

---

## 🌐 Live Interactive Documentation

Explore the complete interactive documentation, guides, and Swagger-style API specifications:

👉 **[https://sammygis.github.io/dronegeo/](https://sammygis.github.io/dronegeo/)**

| Guide & Topic | Direct Live Link | Description |
| :--- | :--- | :--- |
| 🚀 **Beginner Quickstart** | [sammygis.github.io/dronegeo/quickstart](https://sammygis.github.io/dronegeo/quickstart/) | 5-minute step-by-step tutorial from raw LAS to finished deliverables |
| 🔍 **AutoQC & GCP Diagnostics** | [sammygis.github.io/dronegeo/autoqc](https://sammygis.github.io/dronegeo/autoqc/) | Pre-flight audit, ASPRS GCP/Checkpoint validation, blunder detection & auto-healing |
| ⛰️ **Surface Models (DEM)** | [sammygis.github.io/dronegeo/surfaces](https://sammygis.github.io/dronegeo/surfaces/) | Smooth $k$-NN IDW Bare-Earth DTMs, DSMs & Canopy Height Models |
| 📈 **Elevation Profiles & Transects** | [sammygis.github.io/dronegeo/api/profiling](https://sammygis.github.io/dronegeo/api/profiling/) | Cross-sectional slices, point cloud profiles & multi-epoch surface comparisons |
| 🌊 **Hydrology & Flood Risk** | [sammygis.github.io/dronegeo/hydrology](https://sammygis.github.io/dronegeo/hydrology/) | D8/D-Inf flow routing, TWI flood pooling & Landslide hazard scoring |
| 🎨 **Orthos & Crop Vitality** | [sammygis.github.io/dronegeo/imagery](https://sammygis.github.io/dronegeo/imagery/) | 4-band RGBA orthomosaics & VARI / GLI / TGI agricultural indices |
| 📐 **3D Volumetrics & Contours** | [sammygis.github.io/dronegeo/volumetrics](https://sammygis.github.io/dronegeo/volumetrics/) | Excavation Cut & Fill ($m^3$), stockpiles & CAD vector contours |
| 💻 **Interactive Notebooks** | [sammygis.github.io/dronegeo/examples](https://sammygis.github.io/dronegeo/examples/) | Standalone Python scripts & Jupyter notebook walkthroughs |
| 📚 **Full API Reference** | [sammygis.github.io/dronegeo/api](https://sammygis.github.io/dronegeo/api/) | Collapsible parameter dropdowns, types, returns & docstrings |

---

## Overview

`dronegeo` is a modular, high-performance Python library built for remote sensing scientists, drone survey teams, GIS engineers, and photogrammetry specialists. It bridges the gap between raw aerial sensor data (LAS/LAZ point clouds, multiband imagery) and survey-grade GIS deliverables (DTMs, DSMs, CHMs, Orthomosaics, Hillshades, Vector Contours, Hydrological Flow Risk Models, Cross-Sectional Transects, and 3D Earthwork Volumetrics).

---

## Capabilities and Real-World Examples

| Subsystem | Function | Real-World Application & Problem Solved |
| :--- | :--- | :--- |
| **GCP & Checkpoint Validation** | `validate_gcp_accuracy` | **Geodetic Accuracy Audit**: Compares LAS point clouds and DEMs against surveyed field targets (Shapefile, GeoJSON, CSV). Computes ASPRS/NSSDA $\text{RMSE}_z$, mean datum shift $\bar{\Delta Z}$, 95% confidence accuracy, and isolates surveyor blunders via Median Absolute Deviation (MAD). |
| **Diagnostics & AutoQC** | `autoqc.inspect` | **Find & Explain Errors**: Automatically detects missing CRS, multipath noise floaters, vertical datum shifts, or DEM hole voids with physical root-cause explanation. |
| | `autoqc.remediate` | **Auto-Heal Survey Files**: 1-line automated repair pipeline that filters out noise floaters, assigns missing CRS, rectifies vertical datum shifts, and infills terrain holes. |
| | `check_strip_alignment` | **Fix vertical flightline seams**: Auto-detects if pass #2 is 12cm higher than pass #1 and computes the exact correction ($\Delta Z$). |
| | `detect_terrain_anomalies` | **Find sensor glitches**: Scans elevation models for false vertical spikes, bird strikes, or subterranean pits. |
| | `profile_point_cloud` | **Pre-flight data audit**: Checks point density (e.g. $55 \text{ pts/m}^2$), vegetation penetration, and pulse returns. |
| **Elevation Profiles & Transects** | `extract_elevation_transect` | **Cross-Section Analysis**: Samples arbitrary 2D straight-line slices across elevation models for road cross-sections, trenches, and riverbeds. |
| | `plot_elevation_transects` | **Multi-Epoch Profile Plots**: Generates publication-ready comparative cross-sectional charts (e.g. Pre-Excavation vs Post-Excavation vs As-Built design). |
| | `plot_point_cloud_profile` | **LiDAR Profile Slices**: Renders 2D vertical slices of point clouds colored by elevation or classification. |
| **Surface Models** | `create_dtm` | **Bare-Earth Model**: Filters out trees, crops, and buildings to create a smooth, continuous terrain ground surface without facet stepping. |
| | `create_dsm` | **Full Surface Model**: Captures top-of-canopy, building rooftops, and powerlines from maximum LiDAR pulse returns. |
| | `create_chm` | **Forest & Crop Height**: Subtracts DTM from DSM to measure true tree heights and crop canopy growth in meters. |
| **Hydrology & Flood Risk** | `compute_d8_flow_direction` | **Water Flow Direction**: Simulates which direction rainwater will flow across every pixel on the landscape. |
| | `compute_flow_accumulation` | **Stream Extraction**: Finds natural drainage valleys, gullies, and stream network headwaters. |
| | `compute_topographic_wetness_index` | **Flood & Soil Saturation Risk**: Highlights low-lying depression zones prone to waterlogging and pooling. |
| | `compute_stream_power_index` | **Channel Erosion Risk**: Identifies steep gullies and runoff channels subject to aggressive soil scouring. |
| | `compute_sediment_transport_index` | **Soil Loss Model (USLE LS)**: Estimates hillslope sediment transport for agricultural conservation. |
| | `compute_landslide_susceptibility_index` | **Slope Failure Risk**: Multi-criteria hazard score (0-100) combining steep slope, wetness, and curvature. |
| **RGB Orthomosaics** | `create_true_color_orthomosaic` | **Photo-Realistic Maps**: Generates seamless 4-band RGBA true-color aerial maps from point cloud colors. |
| | `compute_visible_vegetation_index` | **Crop & Biomass Health**: Computes VARI, GLI, and TGI greenness maps to monitor agricultural crop vitality. |
| **Terrain Analysis** | `generate_hillshade` | **3D Visual Relief**: Generates shaded relief maps for presentations, site plans, and GIS map layouts. |
| | `generate_slope_map` / `generate_aspect_map` | **Slope & Compass Facing**: Calculates hillside gradient (degrees) and solar aspect heading (0°-360°). |
| | `generate_contour_lines` | **CAD & GIS Vector Contours**: Generates smooth 0.5m, 1m, or 5m elevation contour lines (GeoJSON/Shapefile). |
| | `compute_cut_fill_volume` | **3D Earthwork Volumes**: Measures excavated cut ($m^3$) and fill balance between two drone survey flights (e.g. monthly quarry audits). |
| **Hardware Scaling** | `compute_context` | **Multi-Core Speed**: Dynamically scales CPU workers and memory chunks to process massive surveys efficiently. |

---

## Installation

Install via pip from PyPI:

```bash
pip install dronegeo
```

Or install with development, test, and documentation extras:

```bash
pip install "dronegeo[docs,test,dev]"
```

---

## Running Tests

`dronegeo` includes a comprehensive automated test suite with synthetic point clouds and surface models:

```bash
# Run all 54 test suites
pytest -v

# Run with test coverage
pytest --cov=dronegeo tests/
```

---

## Quick Start Guides and Workflows

All examples are standalone and runnable out-of-the-box in the `examples/` directory:

```bash
# 1. Generate canonical sample datasets once
python examples/00_generate_sample_datasets.py

# 2. Run any workflow
python examples/01_point_cloud_audit.py
python examples/02_strip_alignment_and_merging.py
python examples/03_surface_models_dtm_dsm_chm.py
python examples/04_orthomosaic_and_vegetation_indices.py
python examples/05_terrain_morphology_and_contours.py
python examples/06_earthwork_cut_fill_volumetrics.py
python examples/07_elevation_transects_and_qc.py
python examples/08_hydrological_flow_and_risk_modeling.py
python examples/09_autoqc_survey_diagnostics_and_healing.py
python examples/10_gcp_accuracy_validation.py
```

Or open the interactive Jupyter Notebook:
```bash
jupyter notebook examples/notebooks/dronegeo_interactive_tutorial.ipynb
```

---

### 1. Ground Control Point (GCP) Accuracy Validation & Auto-Rectification

Validate raw LAS/LAZ point clouds or DEM GeoTIFFs against surveyed field targets (**ESRI Shapefile, GeoJSON, or CSV**) before starting heavy processing:

```python
import dronegeo as dg

# 1. Direct ASPRS / NSSDA geodetic accuracy validation
gcp_report = dg.validate_gcp_accuracy(
    dataset_path="flight_raw.las",
    gcp_data="survey_gcps.shp",      # Or "survey_gcps.geojson" / "gcps.csv"
    search_radius=2.5,               # Search radius for ground returns (m)
    target_tolerance_m=0.05          # 5 cm engineering specification
)

# 2. Print rich geodetic accuracy table to console
gcp_report.print_summary()

print(f"ASPRS RMSEz             : {gcp_report.rmse_z * 100:.2f} cm")
print(f"Systematic Datum Bias   : {gcp_report.mean_bias_z * 100:+.2f} cm")
print(f"NSSDA 95% Vertical Error: {gcp_report.accuracy_95_nssda * 100:.2f} cm")

# 3. Check for surveyor blunders (e.g. pole height entry typos)
if gcp_report.suspect_outliers:
    for blunder in gcp_report.suspect_outliers:
        print(f"Blunder detected at {blunder.point_id}: dZ = {blunder.delta_z * 100:+.1f} cm")
```

---

### 2. AutoQC Survey Diagnostics and 1-Line Auto-Healing

Run full automated pre-flight diagnostics and heal survey defects:

```python
import dronegeo as dg

# 1. Inspect raw survey point cloud with embedded GCP verification
report = dg.autoqc.inspect_point_cloud(
    las_path="raw_flight.las",
    expected_crs=32632,
    gcp_data="survey_gcps.geojson",
    target_tolerance_m=0.05
)
report.print_summary()

# 2. Automatically heal survey defects (removes floaters, sets CRS, rectifies datum shift)
if report.has_critical_issues:
    clean_las = dg.autoqc.remediate_point_cloud(
        las_path="raw_flight.las",
        output_las="cleaned_survey.las",
        report=report,
        assign_crs=32632
    )
```

---

### 3. Elevation Profiles and Cross-Section Transects

Extract high-resolution terrain cross-sections along arbitrary straight-line paths (e.g. road centerline, pipeline right-of-way, or quarry benches) and compare multi-epoch surfaces:

```python
import dronegeo as dg

# 1. Define survey transect line (Start [X, Y] to End [X, Y])
p_start = (500020.0, 5200020.0)
p_end   = (500180.0, 5200180.0)

# 2. Extract 2D elevation profiles across multiple survey epochs
profile_before = dg.profiling.extract_elevation_transect(
    dem_path="quarry_pre_excavation.tif",
    start_xy=p_start,
    end_xy=p_end,
    num_samples=250,
    label="Pre-Excavation Terrain"
)

profile_after = dg.profiling.extract_elevation_transect(
    dem_path="quarry_post_excavation.tif",
    start_xy=p_start,
    end_xy=p_end,
    num_samples=250,
    label="Post-Excavation Terrain"
)

# 3. Render publication-ready comparative cross-section plot
dg.profiling.plot_elevation_transects(
    profiles=[profile_before, profile_after],
    output_image="outputs/elevation_cross_section.png",
    title="Quarry Bench Cut Cross-Section (Transect A-A')"
)
```

---

### 4. Multi-Strip Flightline Alignment and Co-Registration ($\Delta Z$)

```python
import dronegeo as dg

# 1. Detect overlap vertical offset
overlap_report = dg.diagnostics.check_strip_alignment(
    las_path1="flight_strip1.las",
    las_path2="flight_strip2.las",
    sample_resolution=0.5
)
print(f"Detected Datum Shift: {overlap_report.median_offset:+.4f} m (Std: {overlap_report.std_dev:.4f} m)")

# 2. Plot statistical error histogram
dg.profiling.plot_strip_overlap_residuals(overlap_report, "outputs/overlap_residuals.png")

# 3. Merge strips with vertical shift applied
master_las = dg.lidar.align_and_merge_strips(
    las_files=["flight_strip1.las", "flight_strip2.las"],
    output_las="outputs/unified_master.las",
    z_shifts=[0.0, overlap_report.median_offset]
)
```

---

### 5. Continuous DTM, DSM, and Canopy Height Models (CHM)

```python
import dronegeo as dg

# Continuous Ground DTM (0.10m)
dtm_path = dg.dem.create_dtm(
    las_path="outputs/unified_master.las",
    output_tif="outputs/survey_dtm.tif",
    resolution=0.10,
    k_neighbors=8,
    ground_class=2
)

# Continuous DSM (0.10m)
dsm_path = dg.dem.create_dsm(
    las_path="outputs/unified_master.las",
    output_tif="outputs/survey_dsm.tif",
    resolution=0.10
)

# Canopy Height Model (CHM = DSM - DTM)
chm_path = dg.dem.create_chm(
    dsm_path=dsm_path,
    dtm_path=dtm_path,
    output_tif="outputs/canopy_height.tif",
    clamp_min=0.0
)
```

---

### 6. Hydrological Flow Routing and Terrain Risk Modeling

```python
import dronegeo as dg

# 1. D8 and D-Infinity Flow Routing
dg.hydrology.compute_d8_flow_direction("outputs/survey_dtm.tif", "outputs/flow_d8.tif")
dg.hydrology.compute_dinfinity_flow_direction("outputs/survey_dtm.tif", "outputs/flow_dinf.tif")

# 2. Flow Accumulation and Drainage Network
dg.hydrology.compute_flow_accumulation("outputs/survey_dtm.tif", "outputs/flow_accum.tif", units="cells")
dg.hydrology.extract_stream_network("outputs/flow_accum.tif", "outputs/stream_channels.tif", threshold_cells=200)

# 3. Topographic Wetness Index (TWI - Soil Saturation / Flood Risk)
dg.hydrology.compute_topographic_wetness_index("outputs/survey_dtm.tif", "outputs/twi.tif")

# 4. Stream Power Index (SPI - Channel Scouring Erosion) & Sediment Transport (STI)
dg.hydrology.compute_stream_power_index("outputs/survey_dtm.tif", "outputs/spi.tif")
dg.hydrology.compute_sediment_transport_index("outputs/survey_dtm.tif", "outputs/sti.tif")

# 5. Multi-Criteria Landslide Hazard Susceptibility Score [0-100]
dg.hydrology.compute_landslide_susceptibility_index("outputs/survey_dtm.tif", "outputs/landslide_hazard.tif")
```

---

### 7. True-Color RGB Orthomosaics and Photometric Vegetation Indices

```python
import dronegeo as dg

# 1. Generate 4-band RGBA True-Color Orthomosaic
ortho_path = dg.imagery.create_true_color_orthomosaic(
    las_path="outputs/unified_master.las",
    output_tif="outputs/true_color_ortho.tif",
    resolution=0.10,
    alpha_channel=True,
    auto_contrast=True
)

# 2. Compute Visible Atmospherically Resistant Index (VARI)
vari_tif = dg.imagery.compute_vari(ortho_path=ortho_path, output_tif="outputs/crop_health_vari.tif")

# 3. Compute Green Leaf Index (GLI)
gli_tif = dg.imagery.compute_gli(ortho_path=ortho_path, output_tif="outputs/leaf_chlorophyll_gli.tif")
```

---

### 8. Terrain Morphology: Hillshade, Slope, Aspect, and Vector Contours

```python
import dronegeo as dg

# 1. Analytical Photometric Hillshade (Azimuth 315° NW, Altitude 45°)
dg.analysis.generate_hillshade("outputs/survey_dtm.tif", "outputs/hillshade.tif")

# 2. Topographic Slope Map (in degrees)
dg.analysis.generate_slope_map("outputs/survey_dtm.tif", "outputs/slope_degrees.tif", units="degrees")

# 3. Compass Aspect Map (0° to 360°)
dg.analysis.generate_aspect_map("outputs/survey_dtm.tif", "outputs/aspect_compass.tif")

# 4. Generate 1.0m Vector Contour Lines (Shapefile / GeoJSON)
contours_gdf = dg.analysis.generate_contour_lines(
    dem_path="outputs/survey_dtm.tif",
    output_vector_path="outputs/contours_1m.geojson",
    interval_m=1.0
)
print(f"Generated {len(contours_gdf):,} vector contour segments.")
```

---

### 9. 3D Cut and Fill Volumetrics and Stockpile Calculations

```python
import dronegeo as dg

# 1. 3D Cut & Fill Volume between Two Survey Epochs
vol_report = dg.analysis.compute_cut_fill_volume(
    before_dem="quarry_january.tif",
    after_dem="quarry_february.tif",
    output_diff_tif="quarry_elevation_diff.tif"
)

print(f"Excavated Cut Volume: {vol_report.cut_volume_m3:,.1f} m³")
print(f"Deposited Fill Volume: {vol_report.fill_volume_m3:,.1f} m³")
print(f"Net Volume Change: {vol_report.net_volume_m3:,.1f} m³")

# 2. Stockpile Volume against Reference Base Datum
stockpile = dg.analysis.compute_stockpile_volume("stockpile_dtm.tif", base_elevation=540.0)
print(f"Stockpile Volume: {stockpile.cut_volume_m3:,.2f} m³ across {stockpile.surface_area_m2:,.1f} m²")
```

---

### 10. Hardware Resource Management and Scoped Contexts

```python
import dronegeo as dg

# Global Preset
dg.set_compute_profile("maximum")  # Or "balanced", "low_memory"

# Scoped Context Manager (Automatically restores prior settings on exit)
with dg.compute_context(n_jobs=4, chunk_size=1_000_000, low_memory_mode=True):
    dtm = dg.dem.create_dtm("survey.las", "dtm.tif")
```

---

## Documentation and Live Preview

`dronegeo` official interactive documentation is hosted on GitHub Pages:

- **Official Documentation Portal**: [https://sammygis.github.io/dronegeo/](https://sammygis.github.io/dronegeo/)

To launch the documentation locally with instant hot-reloading:

```bash
pip install -e ".[docs]"
mkdocs serve
```

---

## Scientific Literature and References

1. **ASPRS Positional Accuracy Standards for Geospatial Data**:
   - American Society for Photogrammetry and Remote Sensing (ASPRS). (2014). *ASPRS Positional Accuracy Standards for Digital Geospatial Data*. Photogrammetric Engineering & Remote Sensing, 81(3), A1-A26.
2. **Topographic Wetness Index ($\text{TWI}$)**:
   - Beven, K. J., & Kirkby, M. J. (1979). *A physically based, variable contributing area model of basin hydrology*. Hydrological Sciences Bulletin, 24(1), 43-69.
3. **D8 Drainage Flow Routing**:
   - O'Callaghan, J. F., & Mark, D. M. (1984). *The extraction of drainage networks from digital elevation data*. Computer Vision, Graphics, and Image Processing, 28(3), 323-344.
4. **D-Infinity Continuous Flow Algorithm**:
   - Tarboton, D. G. (1997). *A new method for the determination of flow directions and upslope areas in grid digital elevation models*. Water Resources Research, 33(2), 309-319.
5. **Stream Power Index ($\text{SPI}$)**:
   - Moore, I. D., Grayson, R. B., & Ladson, A. R. (1991). *Digital terrain modelling: A review of hydrological, geomorphological, and biological applications*. Hydrological Processes, 5(1), 3-30.
6. **Sediment Transport Index ($\text{STI}$ / USLE LS 3D Factor)**:
   - Moore, I. D., & Burch, G. J. (1986). *Physical basis of the length-slope factor in the Universal Soil Loss Equation*. Soil Science Society of America Journal, 50(5), 1294-1298.
7. **Topographic Landslide Susceptibility Hazard Model**:
   - Montgomery, D. R., & Dietrich, W. E. (1994). *A physically based model for the topographic control on shallow landsliding*. Water Resources Research, 30(4), 1153-1171.

---

## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.
