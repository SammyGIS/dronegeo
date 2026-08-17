# Analysis & Volumetrics API (`dronegeo.analysis`)

3D Cut & Fill earthwork volumes, stockpile volume audits, analytical hillshades, slope/aspect, and CAD/GIS contour line generation.

---

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

### `dronegeo.analysis.compute_stockpile_volume`
??? func "<span class='swagger-badge badge-func'>FUNCTION</span> `dg.analysis.compute_stockpile_volume(dem_path, base_elevation=None) -> StockpileVolumeReport`"

    **Overview & Real-World Use Case:**  
    Measures aggregate stockpile material volume ($m^3$) and surface footprint area ($m^2$) above a base elevation datum plane.

---

### `dronegeo.analysis.generate_contour_lines`
??? func "<span class='swagger-badge badge-func'>FUNCTION</span> `dg.analysis.generate_contour_lines(dem_path, output_vector_path, interval_m=1.0) -> GeoDataFrame`"

    **Overview & Real-World Use Case:**  
    Extracts smooth vector elevation contour lines and exports them directly to GeoJSON, Shapefile (`.shp`), or GeoPackage for CAD and GIS layout maps.

---

## Full Module Docstrings

::: dronegeo.analysis.volumetrics
    options:
      members:
        - compute_cut_fill_volume
        - compute_stockpile_volume
        - VolumetricCutFillReport
        - StockpileVolumeReport

::: dronegeo.analysis.contours
    options:
      members:
        - generate_contour_lines

::: dronegeo.analysis.morphology
    options:
      members:
        - generate_hillshade
        - generate_slope_map
        - generate_aspect_map
        - compute_surface_derivatives
