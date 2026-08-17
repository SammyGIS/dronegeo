# Surface Models API (`dronegeo.dem`)

High-resolution bare-earth DTMs, maximum surface DSMs, and Canopy Height Models (CHM) via spatial Kd-Tree $k$-NN Inverse Distance Weighting (IDW).

---

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

---

### `dronegeo.dem.create_dsm`
??? func "<span class='swagger-badge badge-func'>FUNCTION</span> `dg.dem.create_dsm(las_path, output_tif, resolution=0.25, ...) -> str`"

    **Overview & Real-World Use Case:**  
    Generates a continuous Digital Surface Model (DSM) capturing the top of vegetation canopies, building rooftops, and powerlines from maximum LiDAR pulse returns.

---

### `dronegeo.dem.create_chm`
??? func "<span class='swagger-badge badge-func'>FUNCTION</span> `dg.dem.create_chm(dsm_path, dtm_path, output_tif, clamp_min=0.0) -> str`"

    **Overview & Real-World Use Case:**  
    Computes a Canopy Height Model (CHM) representing actual tree heights and crop canopy growth in meters: $\text{CHM} = \max(\text{DSM} - \text{DTM}, 0)$.

---

## Full Module Docstrings

::: dronegeo.dem.surface_models
    options:
      members:
        - create_dtm
        - create_dsm
        - create_chm
        - create_intensity_raster
        - extract_flight_footprint_mask

::: dronegeo.dem.boundary_extraction
    options:
      members:
        - extract_boundary_polygon
        - extract_alpha_shape_boundary
        - extract_bounding_box_polygon
