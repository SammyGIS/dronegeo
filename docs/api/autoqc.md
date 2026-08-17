# AutoQC & Diagnostics API (`dronegeo.autoqc`)

Dynamic survey defect inspection, ASPRS Ground Control Point (GCP) and Checkpoint geodetic accuracy auditing, physical root-cause explanation, and 1-line auto-healing engine.

---

### `dronegeo.validate_gcp_accuracy`
???+ func "<span class='swagger-badge badge-func'>FUNCTION</span> `dg.validate_gcp_accuracy(dataset_path, gcp_data, search_radius=2.5, target_tolerance_m=0.05, ground_only=True, k_neighbors=6) -> GCPValidationReport`"

    **Overview & Real-World Use Case:**  
    Performs rigorous geodetic accuracy validation on raw LAS/LAZ point clouds or DEM GeoTIFFs against surveyed Ground Control Points (GCPs) and independent Checkpoints. Supports **Shapefiles (`.shp`)**, **GeoJSON (`.geojson`)**, and **CSV/TXT** tables. Computes ASPRS / NSSDA standard accuracy statistics ($\text{RMSE}_z$, mean bias $\bar{\Delta Z}$, $\sigma_z$, 95% confidence accuracy), isolates rogue surveyor blunders via Median Absolute Deviation (MAD), and prescribes exact vertical datum offsets ($\Delta Z$).

    #### Parameters & Inputs
    | Parameter | Type | Required / Default | Description |
    | :--- | :--- | :--- | :--- |
    | `dataset_path` | `str \| Path` | **Required** | Path to LAS/LAZ point cloud or DEM GeoTIFF. |
    | `gcp_data` | `str \| Path \| Any` | **Required** | Path to `.shp`, `.geojson`, `.gpkg`, `.csv`, `.txt`, or Pandas/GeoPandas DataFrame. |
    | `search_radius` | `float` | Optional (`2.5`) | Horizontal search radius (m) for LiDAR ground returns or raster sampling. |
    | `target_tolerance_m` | `float` | Optional (`0.05`) | Maximum allowable vertical tolerance (m) for engineering compliance. |
    | `ground_only` | `bool` | Optional (`True`) | In LAS point clouds, restrict evaluation to Class 2 (Ground) returns. |
    | `k_neighbors` | `int` | Optional (`6`) | Number of nearest neighbors used for IDW elevation interpolation. |

    #### Returns & Outputs
    - **Return Type**: `GCPValidationReport`
    - **Attributes**:
      - `rmse_z` (`float`): Root Mean Square Error in vertical dimension (m).
      - `mean_bias_z` (`float`): Mean systematic datum shift $\bar{\Delta Z}$ (m).
      - `accuracy_95_nssda` (`float`): 95% confidence vertical accuracy ($1.96 \times \text{RMSE}_z$).
      - `passed_tolerance` (`bool`): Whether $\text{RMSE}_z \le \text{target\_tolerance\_m}$ and no blunder outliers exist.
      - `recommended_z_shift` (`float`): Recommended vertical shift to eliminate survey datum bias.
      - `suspect_outliers` (`List[GCPResidualPoint]`): Control points flagged as surveyor blunders.
      - `residuals` (`List[GCPResidualPoint]`): Per-point error table with drone elevation, survey elevation, and $\Delta Z$.

---

### `dronegeo.autoqc.inspect_point_cloud`
???+ func "<span class='swagger-badge badge-func'>FUNCTION</span> `dg.autoqc.inspect_point_cloud(las_path, expected_crs=None, gcp_data=None, target_tolerance_m=0.05) -> AutoQCReport`"

    **Overview & Real-World Use Case:**  
    Performs comprehensive pre-processing diagnostic inspection on raw LAS/LAZ point clouds. Scans for missing CRS projections, atmospheric sensor multipath noise floaters, low ground penetration density, unclassified returns, and evaluates ground control target accuracy if `gcp_data` is supplied.

    #### Parameters & Inputs
    | Parameter | Type | Required / Default | Description |
    | :--- | :--- | :--- | :--- |
    | `las_path` | `str \| Path` | **Required** | Absolute or relative path to the input ASPRS LAS or LAZ point cloud file on disk. |
    | `expected_crs` | `int \| str` | Optional (`None`) | Expected EPSG code (e.g. `32632`) to check against if projection header is missing. |
    | `gcp_data` | `str \| Path \| Any` | Optional (`None`) | Optional ground control targets (Shapefile, GeoJSON, or CSV). |
    | `target_tolerance_m` | `float` | Optional (`0.05`) | Allowable vertical error threshold (m). |

---

### `dronegeo.autoqc.remediate_point_cloud`
??? func "<span class='swagger-badge badge-func'>FUNCTION</span> `dg.autoqc.remediate_point_cloud(las_path, output_las, report=None, assign_crs=None, clean_outliers=True, z_shift=None) -> str`"

    **Overview & Real-World Use Case:**  
    1-line automated healing pipeline for defective LAS point clouds. Filters out laser noise floaters, injects missing projected EPSG headers, rectifies systematic vertical datum bias ($z\_shift$), and preserves all RGB and intensity dimensions.

---

### `dronegeo.autoqc.inspect_elevation_model`
??? func "<span class='swagger-badge badge-func'>FUNCTION</span> `dg.autoqc.inspect_elevation_model(dem_path, gcp_data=None, target_tolerance_m=0.05) -> AutoQCReport`"

    **Overview & Real-World Use Case:**  
    Inspects DTM and DSM GeoTIFF elevation models for NoData void holes, sharp vertical sensor cliff tears ($|dZ| > 15\text{m}$), spatial resolution consistency, and ground control accuracy.

---

### `dronegeo.autoqc.remediate_elevation_model`
??? func "<span class='swagger-badge badge-func'>FUNCTION</span> `dg.autoqc.remediate_elevation_model(dem_path, output_dem, report=None, fill_voids=True, despike_filter=True, assign_crs=None, z_shift=None) -> str`"

    **Overview & Real-World Use Case:**  
    Heals defective DTM/DSM GeoTIFF elevation models. Infills terrain NoData holes using smooth nearest-neighbor distance transforms, suppresses sensor spike tears with adaptive local median filtering, and rectifies vertical elevation bias.

---

## Full Module Docstrings

::: dronegeo.diagnostics.gcp_validation
    options:
      members:
        - validate_gcp_accuracy
        - load_gcp_dataset
        - GCPValidationReport
        - GCPResidualPoint
        - PointType
        - ResidualStatus

::: dronegeo.diagnostics.autoqc
    options:
      members:
        - inspect_point_cloud
        - inspect_elevation_model
        - correct_point_cloud
        - remediate_point_cloud
        - correct_elevation_model
        - remediate_elevation_model
        - inspect
        - correct
        - remediate
        - AutoQCReport
        - DiagnosticIssue
        - IssueSeverity
