# API Reference Overview

Welcome to the **DroneGeo API Reference**. Every module contains interactive, collapsible function specifications with input parameters, types, return values, and copy-paste code snippets.

---

## API Subsystem Modules

| Subsystem | Module | Key Functions & Capabilities |
| :--- | :--- | :--- |
| **🔍 [AutoQC & Diagnostics](autoqc.md)** | `dronegeo.autoqc` | `inspect_point_cloud`, `remediate_point_cloud`, `inspect_elevation_model`, `remediate_elevation_model` |
| **⛰️ [Surface Models (DEM)](dem.md)** | `dronegeo.dem` | `create_dtm`, `create_dsm`, `create_chm`, `create_intensity_raster`, `extract_flight_footprint_mask` |
| **🌊 [Hydrology & Flood Risk](hydrology.md)** | `dronegeo.hydrology` | `compute_d8_flow_direction`, `compute_flow_accumulation`, `compute_topographic_wetness_index`, `compute_landslide_susceptibility_index` |
| **🎨 [Imagery & Orthomosaics](imagery.md)** | `dronegeo.imagery` | `create_true_color_orthomosaic`, `compute_vari`, `compute_gli`, `compute_tgi`, `compute_exg` |
| **📐 [Analysis & Volumetrics](analysis.md)** | `dronegeo.analysis` | `compute_cut_fill_volume`, `compute_stockpile_volume`, `generate_hillshade`, `generate_contour_lines` |
| **🛸 [LiDAR & Strip Alignment](lidar.md)** | `dronegeo.lidar` | `profile_point_cloud`, `align_and_merge_strips`, `rectify_point_cloud_elevation` |
| **📈 [Profiling & Visualizations](profiling.md)** | `dronegeo.profiling` | `extract_elevation_transect`, `plot_elevation_transects`, `plot_strip_overlap_residuals`, `map_grid_chips` |
| **⚡ [Compute & Hardware Scaling](config.md)** | `dronegeo.config` | `set_compute_profile`, `compute_context`, `get_compute_config` |
| **🌐 [Spatial & CRS Management](spatial.md)** | `dronegeo.spatial` | `resolve_crs`, `get_spatial_bounds_from_raster`, `get_spatial_bounds_from_las` |
| **🛠️ [Utils & Helpers](utils.md)** | `dronegeo.utils` | `verify_las_file`, `verify_raster_file`, `ensure_output_directory`, `format_file_size` |
