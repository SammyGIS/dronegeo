# AutoQC & Diagnostics API (`dronegeo.autoqc`)

Dynamic survey defect inspection, physical root-cause explanation, and 1-line auto-healing engine.

---

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

    report = dg.autoqc.inspect_point_cloud("raw_survey.las", expected_crs=32632)
    report.print_summary()
    ```

---

### `dronegeo.autoqc.remediate_point_cloud`
??? func "<span class='swagger-badge badge-func'>FUNCTION</span> `dg.autoqc.remediate_point_cloud(las_path, output_las, report=None, assign_crs=None, clean_outliers=True, ...) -> str`"

    **Overview & Real-World Use Case:**  
    1-line automated healing pipeline for defective LAS point clouds. Filters out laser noise floaters, injects missing projected EPSG headers, and preserves all RGB and intensity dimensions.

    #### Parameters & Inputs
    | Parameter | Type | Required / Default | Description |
    | :--- | :--- | :--- | :--- |
    | `las_path` | `str \| Path` | **Required** | Defective input LAS/LAZ point cloud file path. |
    | `output_las` | `str \| Path` | **Required** | Destination cleaned LAS point cloud file path. |
    | `report` | `AutoQCReport` | Optional (`None`) | Pre-computed AutoQC diagnostic report. |
    | `assign_crs` | `int` | Optional (`None`) | Target EPSG code (e.g. `32632`) to embed into the point cloud header. |
    | `clean_outliers` | `bool` | Optional (`True`) | Whether to filter statistical elevation floaters and pits. |

    #### Returns & Outputs
    - **Return Type**: `str` (Path to cleaned output LAS file).

---

### `dronegeo.autoqc.inspect_elevation_model`
??? func "<span class='swagger-badge badge-func'>FUNCTION</span> `dg.autoqc.inspect_elevation_model(dem_path) -> AutoQCReport`"

    **Overview & Real-World Use Case:**  
    Inspects DTM and DSM GeoTIFF elevation models for NoData void holes, sharp vertical sensor cliff tears ($|dZ| > 15\text{m}$), and spatial resolution consistency.

    #### Parameters & Inputs
    | Parameter | Type | Required / Default | Description |
    | :--- | :--- | :--- | :--- |
    | `dem_path` | `str \| Path` | **Required** | Path to the GeoTIFF elevation model to diagnose. |

---

### `dronegeo.autoqc.remediate_elevation_model`
??? func "<span class='swagger-badge badge-func'>FUNCTION</span> `dg.autoqc.remediate_elevation_model(dem_path, output_dem, report=None, fill_voids=True, despike_filter=True, assign_crs=None) -> str`"

    **Overview & Real-World Use Case:**  
    Heals defective DTM/DSM GeoTIFF elevation models. Infills terrain NoData holes using smooth nearest-neighbor distance transforms and suppresses sensor spike tears with adaptive local median filtering.

---

## Full Module Docstrings

::: dronegeo.diagnostics.autoqc
    options:
      members:
        - inspect_point_cloud
        - inspect_elevation_model
        - remediate_point_cloud
        - remediate_elevation_model
        - inspect
        - remediate
        - AutoQCReport
        - DiagnosticIssue
        - IssueSeverity
