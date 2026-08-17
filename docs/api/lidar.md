# LiDAR & Strip Alignment API (`dronegeo.lidar`)

Multi-strip flightline vertical co-registration ($\Delta Z$), LiDAR statistical point cloud profiling, and terrain datum rectification.

---

### `dronegeo.lidar.profile_point_cloud`
???+ func "<span class='swagger-badge badge-func'>FUNCTION</span> `dg.lidar.profile_point_cloud(las_path, grid_resolution=5.0) -> PointCloudProfile`"

    **Overview & Real-World Use Case:**  
    Pre-flight audit tool that scans LiDAR flight data for spatial bounding box extent, point density ($pts/m^2$), pulse return distribution (first, intermediate, last returns), RGB channels, and unclassified returns.

    #### Parameters & Inputs
    | Parameter | Type | Required / Default | Description |
    | :--- | :--- | :--- | :--- |
    | `las_path` | `str \| Path` | **Required** | Source LAS/LAZ point cloud file path. |
    | `grid_resolution` | `float` | Optional (`5.0`) | Spatial cell size in meters for local density estimation. |

    #### Returns & Outputs
    - **Return Type**: `PointCloudProfile` data class with density, class distributions, and bounding box metrics.

---

### `dronegeo.lidar.align_and_merge_strips`
??? func "<span class='swagger-badge badge-func'>FUNCTION</span> `dg.lidar.align_and_merge_strips(las_files, output_las, z_shifts=None) -> str`"

    **Overview & Real-World Use Case:**  
    Co-registers multiple overlapping flight passes by applying calibrated vertical shift vectors ($\Delta Z$) to eliminate flightline seam steps before unifying into a single master point cloud.

---

## Full Module Docstrings

::: dronegeo.lidar.strip_alignment
    options:
      members:
        - align_and_merge_strips
        - rectify_point_cloud_elevation

::: dronegeo.lidar.point_metrics
    options:
      members:
        - profile_point_cloud
        - PointCloudProfile
