# Interactive API Reference & Function Specifications

<p align="center">
  <b>FastAPI / Swagger-Style Interactive Documentation with Full Parameter Specs, Types, Outputs & Examples</b>
</p>

Click on any function dropdown below to inspect its required inputs, parameters, return types, physical algorithms, and copy-paste code snippets.

---

## 1. Diagnostics & AutoQC Subsystem

### `dronegeo.autoqc.inspect_point_cloud`
???+ func "<span class='swagger-badge badge-func'>FUNCTION</span> `dg.autoqc.inspect_point_cloud(las_path, expected_crs=None) -> AutoQCReport`"

    **Overview & Real-World Use Case:**  
    Performs comprehensive pre-processing diagnostic inspection on raw LAS/LAZ point clouds. Scans for missing CRS projections, atmospheric sensor multipath noise floaters, low ground penetration density, and unclassified returns.

    #### Parameters & Inputs
    | Parameter | Type | Required / Default | Description |
    | :--- | :--- | :--- | :--- |
    | `las_path` | `str \| Path` | **Required** | Absolute or relative path to the input ASPRS LAS or LAZ point cloud file on disk. |
    | `expected_crs` | `int \| str` | Optional (`None`) | Expected EPSG code (e.g. `32632`) to check against if projection header is missing. |

    #### Returns & Outputs
    - **Return Type**: `AutoQCReport`
    - **Attributes**:
      - `quality_score` (`int`): Survey health score from 0 to 100 (100 = survey grade).
      - `overall_status` (`IssueSeverity`): `HEALTHY`, `INFO`, `WARNING`, or `CRITICAL`.
      - `issues` (`List[DiagnosticIssue]`): Detailed list of detected defects with root cause, impact, and prescribed fixes.
      - `summary_metrics` (`dict`): Total points, density ($pts/m^2$), ground percentage, min/max elevation.

    #### Code Example
    ```python
    import dronegeo as dg

    # Inspect raw point cloud
    report = dg.autoqc.inspect_point_cloud("survey.las", expected_crs=32632)
    print(f"Health Score: {report.quality_score}/100 [{report.overall_status.value}]")
    report.print_summary()
    ```

---

### `dronegeo.autoqc.remediate_point_cloud`
??? func "<span class='swagger-badge badge-func'>FUNCTION</span> `dg.autoqc.remediate_point_cloud(las_path, output_las, report=None, assign_crs=None, clean_outliers=True, ...) -> str`"

    **Overview & Real-World Use Case:**  
    1-line automated healing pipeline for defective LAS point clouds. Filters out laser noise floaters (using Statistical Outlier Removal cutoffs), injects missing projected EPSG headers, and preserves all RGB and intensity dimensions.

    #### Parameters & Inputs
    | Parameter | Type | Required / Default | Description |
    | :--- | :--- | :--- | :--- |
    | `las_path` | `str \| Path` | **Required** | Defective input LAS/LAZ point cloud file path. |
    | `output_las` | `str \| Path` | **Required** | Destination cleaned LAS point cloud file path. |
    | `report` | `AutoQCReport` | Optional (`None`) | Pre-computed AutoQC diagnostic report (if omitted, diagnoses automatically). |
    | `assign_crs` | `int` | Optional (`None`) | Target EPSG code (e.g. `32632`) to embed into the point cloud header. |
    | `clean_outliers` | `bool` | Optional (`True`) | Whether to filter statistical elevation floaters and pits. |
    | `z_min_cutoff` | `float` | Optional (`None`) | Minimum allowable elevation in meters. |
    | `z_max_cutoff` | `float` | Optional (`None`) | Maximum allowable elevation in meters. |

    #### Returns & Outputs
    - **Return Type**: `str` (Absolute file path to the cleaned, survey-grade output LAS file).

    #### Code Example
    ```python
    import dronegeo as dg

    clean_las = dg.autoqc.remediate_point_cloud("flight_raw.las", "flight_clean.las", assign_crs=32632)
    print(f"Repaired LAS written to: {clean_las}")
    ```

---

### `dronegeo.autoqc.inspect_elevation_model`
??? func "<span class='swagger-badge badge-func'>FUNCTION</span> `dg.autoqc.inspect_elevation_model(dem_path) -> AutoQCReport`"

    **Overview & Real-World Use Case:**  
    Inspects DTM and DSM GeoTIFF elevation models for NoData void holes, sharp vertical sensor cliff tears ($|dZ| > 15\text{m}$), and spatial resolution consistency.

    #### Parameters & Inputs
    | Parameter | Type | Required / Default | Description |
    | :--- | :--- | :--- | :--- |
    | `dem_path` | `str \| Path` | **Required** | Path to the GeoTIFF elevation model to diagnose. |

    #### Returns & Outputs
    - **Return Type**: `AutoQCReport` with void percentage, elevation spike counts, and recommended repair parameters.

---

### `dronegeo.autoqc.remediate_elevation_model`
??? func "<span class='swagger-badge badge-func'>FUNCTION</span> `dg.autoqc.remediate_elevation_model(dem_path, output_dem, report=None, fill_voids=True, despike_filter=True, assign_crs=None) -> str`"

    **Overview & Real-World Use Case:**  
    Heals defective DTM/DSM GeoTIFF elevation models. Infills terrain NoData holes using smooth nearest-neighbor distance transforms and suppresses sensor spike tears with adaptive local median filtering.

    #### Parameters & Inputs
    | Parameter | Type | Required / Default | Description |
    | :--- | :--- | :--- | :--- |
    | `dem_path` | `str \| Path` | **Required** | Defective input GeoTIFF elevation model path. |
    | `output_dem` | `str \| Path` | **Required** | Target healed GeoTIFF destination path. |
    | `fill_voids` | `bool` | Optional (`True`) | Whether to infill NoData void holes. |
    | `despike_filter`| `bool` | Optional (`True`) | Whether to smooth extreme vertical sensor spikes. |
    | `assign_crs` | `int` | Optional (`None`) | Target EPSG code to embed if CRS is missing. |

    #### Returns & Outputs
    - **Return Type**: `str` (File path to repaired GeoTIFF elevation model).

---

## 2. High-Resolution Surface Models (`dronegeo.dem`)

### `dronegeo.dem.create_dtm`
???+ func "<span class='swagger-badge badge-func'>FUNCTION</span> `dg.dem.create_dtm(las_path, output_tif, resolution=0.25, k_neighbors=8, ground_class=2, ...) -> str`"

    **Overview & Real-World Use Case:**  
    Generates a continuous, survey-grade Bare-Earth Digital Terrain Model (DTM) from classified point clouds using multi-threaded spatial Kd-Tree $k$-NN Inverse Distance Weighting (IDW). Filters out trees, crops, and buildings with zero facet stepping.

    #### Parameters & Inputs
    | Parameter | Type | Required / Default | Description |
    | :--- | :--- | :--- | :--- |
    | `las_path` | `str \| Path` | **Required** | Source LAS/LAZ point cloud file. |
    | `output_tif` | `str \| Path` | **Required** | Destination 32-bit Float GeoTIFF file path. |
    | `resolution` | `float` | Optional (`0.25`) | Ground Sampling Distance (GSD) in meters per pixel (e.g. `0.10`, `0.25`, `1.0`). |
    | `k_neighbors` | `int` | Optional (`8`) | Number of nearest ground neighbors used in IDW interpolation. |
    | `ground_class`| `int` | Optional (`2`) | ASPRS Standard classification code for ground returns (default Class 2). |
    | `power` | `float` | Optional (`2.0`) | IDW distance weighting exponent. |
    | `nodata_val` | `float` | Optional (`-9999.0`) | Sentinel value assigned to unpopulated pixels outside survey boundary. |

    #### Returns & Outputs
    - **Return Type**: `str` (Path to the generated GeoTIFF DTM).

    #### Code Example
    ```python
    import dronegeo as dg

    dtm = dg.dem.create_dtm(
        las_path="flight.las",
        output_tif="outputs/bare_earth_dtm.tif",
        resolution=0.20,
        k_neighbors=8
    )
    ```

---

### `dronegeo.dem.create_dsm`
??? func "<span class='swagger-badge badge-func'>FUNCTION</span> `dg.dem.create_dsm(las_path, output_tif, resolution=0.25, ...) -> str`"

    **Overview & Real-World Use Case:**  
    Generates a continuous Digital Surface Model (DSM) capturing the top of vegetation canopies, building rooftops, and powerlines from maximum LiDAR pulse returns.

    #### Parameters & Inputs
    | Parameter | Type | Required / Default | Description |
    | :--- | :--- | :--- | :--- |
    | `las_path` | `str \| Path` | **Required** | Input LAS/LAZ point cloud file path. |
    | `output_tif` | `str \| Path` | **Required** | Destination GeoTIFF file path. |
    | `resolution` | `float` | Optional (`0.25`) | Pixel resolution in meters. |

    #### Returns & Outputs
    - **Return Type**: `str` (Path to the generated GeoTIFF DSM).

---

### `dronegeo.dem.create_chm`
??? func "<span class='swagger-badge badge-func'>FUNCTION</span> `dg.dem.create_chm(dsm_path, dtm_path, output_tif, clamp_min=0.0) -> str`"

    **Overview & Real-World Use Case:**  
    Computes a Canopy Height Model (CHM) representing actual tree heights and crop canopy growth in meters: $\text{CHM} = \max(\text{DSM} - \text{DTM}, 0)$.

    #### Parameters & Inputs
    | Parameter | Type | Required / Default | Description |
    | :--- | :--- | :--- | :--- |
    | `dsm_path` | `str \| Path` | **Required** | Path to the Digital Surface Model GeoTIFF. |
    | `dtm_path` | `str \| Path` | **Required** | Path to the Digital Terrain Model GeoTIFF. |
    | `output_tif` | `str \| Path` | **Required** | Destination Canopy Height Model GeoTIFF. |
    | `clamp_min` | `float` | Optional (`0.0`) | Minimum cutoff to prevent negative heights from sensor noise. |

    #### Returns & Outputs
    - **Return Type**: `str` (Path to the generated GeoTIFF CHM).

---

## 3. Hydrology & Flood Risk Modeling (`dronegeo.hydrology`)

### `dronegeo.hydrology.compute_flow_accumulation`
???+ func "<span class='swagger-badge badge-func'>FUNCTION</span> `dg.hydrology.compute_flow_accumulation(dem_path, output_tif, units='cells') -> str`"

    **Overview & Real-World Use Case:**  
    Calculates cumulative upslope contributing catchment area for every pixel on the landscape based on D8 steepest descent flow routing. Identifies stream headwaters, natural valleys, and drainage basins.

    #### Parameters & Inputs
    | Parameter | Type | Required / Default | Description |
    | :--- | :--- | :--- | :--- |
    | `dem_path` | `str \| Path` | **Required** | Input bare-earth DTM GeoTIFF path. |
    | `output_tif` | `str \| Path` | **Required** | Destination flow accumulation GeoTIFF path. |
    | `units` | `str` | Optional (`'cells'`) | Accumulation units: `'cells'` (pixel count) or `'area_m2'` (square meters). |

    #### Returns & Outputs
    - **Return Type**: `str` (Path to the generated Flow Accumulation raster).

---

### `dronegeo.hydrology.compute_topographic_wetness_index`
??? func "<span class='swagger-badge badge-func'>FUNCTION</span> `dg.hydrology.compute_topographic_wetness_index(dem_path, output_tif) -> str`"

    **Overview & Real-World Use Case:**  
    Computes the Beven & Kirkby (1979) Topographic Wetness Index:
    $$\text{TWI} = \ln\left(\frac{a}{\tan \beta}\right)$$
    where $a$ is specific catchment area and $\beta$ is slope angle in radians. Highlights flat valley depressions prone to flash flooding and waterlogging.

    #### Parameters & Inputs
    | Parameter | Type | Required / Default | Description |
    | :--- | :--- | :--- | :--- |
    | `dem_path` | `str \| Path` | **Required** | Input bare-earth DTM GeoTIFF. |
    | `output_tif` | `str \| Path` | **Required** | Destination TWI GeoTIFF path. |

    #### Returns & Outputs
    - **Return Type**: `str` (Path to the generated TWI GeoTIFF).

---

### `dronegeo.hydrology.compute_landslide_susceptibility_index`
??? func "<span class='swagger-badge badge-func'>FUNCTION</span> `dg.hydrology.compute_landslide_susceptibility_index(dem_path, output_tif) -> str`"

    **Overview & Real-World Use Case:**  
    Evaluates multi-criteria slope stability hazard score (0 to 100) based on Montgomery & Dietrich (1994) shallow landslide physics, integrating steep slope gradients, high moisture accumulation, and convergent profile curvature.

    #### Parameters & Inputs
    | Parameter | Type | Required / Default | Description |
    | :--- | :--- | :--- | :--- |
    | `dem_path` | `str \| Path` | **Required** | Input bare-earth DTM GeoTIFF. |
    | `output_tif` | `str \| Path` | **Required** | Destination hazard score GeoTIFF (0-100). |

    #### Returns & Outputs
    - **Return Type**: `str` (Path to the landslide susceptibility GeoTIFF deliverable).

---

## 4. RGB Orthomosaics & Crop Health Indices (`dronegeo.imagery`)

### `dronegeo.imagery.create_true_color_orthomosaic`
???+ func "<span class='swagger-badge badge-func'>FUNCTION</span> `dg.imagery.create_true_color_orthomosaic(las_path, output_tif, resolution=0.10, alpha_channel=True, ...) -> str`"

    **Overview & Real-World Use Case:**  
    Renders a seamless 4-band (RGBA) photographic orthomosaic GeoTIFF from colored point clouds ($R, G, B$) with transparent Alpha nodata boundaries and optional dynamic contrast enhancement.

    #### Parameters & Inputs
    | Parameter | Type | Required / Default | Description |
    | :--- | :--- | :--- | :--- |
    | `las_path` | `str \| Path` | **Required** | Input LAS file with RGB color channels. |
    | `output_tif` | `str \| Path` | **Required** | Target 4-band RGBA GeoTIFF destination. |
    | `resolution` | `float` | Optional (`0.10`) | Ground resolution in meters per pixel. |
    | `alpha_channel`| `bool` | Optional (`True`) | Whether to add transparent 4th band for nodata boundary masking. |
    | `auto_contrast`| `bool` | Optional (`True`) | Applies 2%-98% cumulative histogram percentile contrast stretch. |

    #### Returns & Outputs
    - **Return Type**: `str` (Path to created Orthomosaic GeoTIFF).

---

### `dronegeo.imagery.compute_visible_vegetation_index`
??? func "<span class='swagger-badge badge-func'>FUNCTION</span> `dg.imagery.compute_visible_vegetation_index(ortho_path, output_tif, index='VARI') -> str`"

    **Overview & Real-World Use Case:**  
    Computes visible-spectrum photogrammetric vegetation health index maps for precision agriculture and crop monitoring.

    #### Scientifically Correct Formulas
    - **VARI** (Visible Atmospherically Resistant Index):
      $$\text{VARI} = \frac{G - R}{G + R - B}$$
    - **GLI** (Green Leaf Index):
      $$\text{GLI} = \frac{2G - R - B}{2G + R + B}$$
    - **TGI** (Triangular Greenness Index):
      $$\text{TGI} = G - 0.39R - 0.61B$$
    - **ExG** (Excess Green Index):
      $$\text{ExG} = 2G - R - B$$
    - **NGRDI** (Normalized Green-Red Difference Index):
      $$\text{NGRDI} = \frac{G - R}{G + R}$$

    #### Parameters & Inputs
    | Parameter | Type | Required / Default | Description |
    | :--- | :--- | :--- | :--- |
    | `ortho_path` | `str \| Path` | **Required** | Path to 3-band RGB or 4-band RGBA Orthomosaic GeoTIFF. |
    | `output_tif` | `str \| Path` | **Required** | Destination float32 vegetation map path. |
    | `index` | `str` | Optional (`'VARI'`) | One of `'VARI'`, `'GLI'`, `'TGI'`, `'EXG'`, `'NGRDI'`. |

    #### Returns & Outputs
    - **Return Type**: `str` (Path to created crop index GeoTIFF).

---

## 5. 3D Volumetrics & Terrain Morphology (`dronegeo.analysis`)

### `dronegeo.analysis.compute_cut_fill_volume`
???+ func "<span class='swagger-badge badge-func'>FUNCTION</span> `dg.analysis.compute_cut_fill_volume(before_dem, after_dem, output_diff_tif=None) -> VolumetricCutFillReport`"

    **Overview & Real-World Use Case:**  
    Calculates differential 3D excavation cut volume ($m^3$) and fill volume ($m^3$) between two drone survey flights (e.g. monthly quarry audits or construction earthwork progress).

    #### Parameters & Inputs
    | Parameter | Type | Required / Default | Description |
    | :--- | :--- | :--- | :--- |
    | `before_dem` | `str \| Path` | **Required** | Earlier epoch DEM GeoTIFF (e.g. Month 1). |
    | `after_dem` | `str \| Path` | **Required** | Later epoch DEM GeoTIFF (e.g. Month 2). |
    | `output_diff_tif` | `str \| Path` | Optional (`None`) | Optional destination path to save elevation difference GeoTIFF ($\Delta Z$). |

    #### Returns & Outputs
    - **Return Type**: `VolumetricCutFillReport`
    - **Attributes**:
      - `cut_volume_m3` (`float`): Excavated volume in cubic meters ($m^3$).
      - `fill_volume_m3` (`float`): Deposited fill volume in cubic meters ($m^3$).
      - `net_volume_m3` (`float`): Net volume mass balance ($\text{Fill} - \text{Cut}$).
      - `mean_elevation_change_m` (`float`): Average vertical shift ($\Delta Z$).

---

### `dronegeo.analysis.generate_contour_lines`
??? func "<span class='swagger-badge badge-func'>FUNCTION</span> `dg.analysis.generate_contour_lines(dem_path, output_vector_path, interval_m=1.0) -> GeoDataFrame`"

    **Overview & Real-World Use Case:**  
    Extracts smooth vector elevation contour lines and exports them directly to GeoJSON, Shapefile (`.shp`), or GeoPackage for CAD and GIS layout maps.

    #### Parameters & Inputs
    | Parameter | Type | Required / Default | Description |
    | :--- | :--- | :--- | :--- |
    | `dem_path` | `str \| Path` | **Required** | Source DTM/DSM GeoTIFF file path. |
    | `output_vector_path` | `str \| Path` | **Required** | Target vector file path (`.geojson`, `.shp`, `.gpkg`). |
    | `interval_m` | `float` | Optional (`1.0`) | Vertical contour elevation interval in meters (e.g. `0.5`, `1.0`, `5.0`). |

    #### Returns & Outputs
    - **Return Type**: `geopandas.GeoDataFrame` with geometry and `elevation` attribute column.

---

## 6. Hardware Scaling & Compute Profiles (`dronegeo.config`)

### `dronegeo.config.compute_context`
???+ func "<span class='swagger-badge badge-context'>CONTEXT MANAGER</span> `dg.compute_context(n_jobs=None, chunk_size=None, low_memory_mode=None)`"

    **Overview & Real-World Use Case:**  
    Scoped context manager that temporarily applies custom CPU worker counts and RAM chunking configurations to a code block, automatically restoring previous global settings upon exit.

    #### Parameters & Inputs
    | Parameter | Type | Required / Default | Description |
    | :--- | :--- | :--- | :--- |
    | `n_jobs` | `int` | Optional (`-1`) | Number of parallel CPU worker threads (`-1` = all CPU cores). |
    | `chunk_size` | `int` | Optional (`500_000`) | Point batch buffer size for chunked spatial processing. |
    | `low_memory_mode`| `bool` | Optional (`False`) | Enforces streaming execution on RAM-constrained machines. |

    #### Code Example
    ```python
    import dronegeo as dg

    # Process massive survey using 8 threads and 1M point chunks
    with dg.compute_context(n_jobs=8, chunk_size=1_000_000):
        dtm = dg.dem.create_dtm("huge_survey.las", "dtm.tif")
    ```
