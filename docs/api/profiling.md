# Profiling & Visualizations API (`dronegeo.profiling`)

High-performance 2D cross-sectional terrain transects, multi-epoch profile comparisons, LiDAR vertical point slices, statistical error residual histograms, and spatial grid chip maps.

---

### `dronegeo.profiling.extract_elevation_transect`
???+ func "<span class='swagger-badge badge-func'>FUNCTION</span> `dg.profiling.extract_elevation_transect(dem_path, start_xy, end_xy, num_samples=200, label='Transect') -> TransectProfile`"

    **Overview & Real-World Use Case:**  
    Extracts a high-precision 2D cross-sectional elevation slice along an arbitrary straight-line path across a digital elevation model (GeoTIFF). Essential for civil engineering road cross-sections, trench profiles, riverbed bathymetry, and slope gradient auditing.

    **Parameters:**
    - `dem_path` (*Union[str, Path]*): Path to input raster elevation model GeoTIFF.
    - `start_xy` (*Tuple[float, float]*): Projected $(X, Y)$ coordinate of starting point.
    - `end_xy` (*Tuple[float, float]*): Projected $(X, Y)$ coordinate of ending point.
    - `num_samples` (*int*, default=200): Number of equidistant sampling points along the transect line.
    - `label` (*str*, default="Transect"): Descriptive label for plotting legends.

    **Returns:**
    - `TransectProfile`: Dataclass containing `distances_m`, `elevations_m`, `start_xy`, `end_xy`, `min_elev_m`, `max_elev_m`, and `elev_range_m`.

---

### `dronegeo.profiling.plot_elevation_transects`
??? func "<span class='swagger-badge badge-func'>FUNCTION</span> `dg.profiling.plot_elevation_transects(profiles, output_image, title=None, show_fill=True) -> str`"

    **Overview & Real-World Use Case:**  
    Renders high-resolution comparative cross-sectional profile charts (e.g. comparing Pre-Excavation vs Post-Excavation terrain surfaces or design grade lines).

    **Parameters:**
    - `profiles` (*Union[TransectProfile, List[TransectProfile]]*): One or more extracted transect profile objects.
    - `output_image` (*Union[str, Path]*): Destination path for rendered PNG/JPEG chart.
    - `title` (*Optional[str]*): Custom chart title.
    - `show_fill` (*bool*, default=True): Whether to render a semi-transparent elevation gradient fill under profile curves.

    **Returns:**
    - `str`: Absolute path to saved image file.

---

### `dronegeo.lidar.plot_point_cloud_profile`
??? func "<span class='swagger-badge badge-func'>FUNCTION</span> `dg.lidar.plot_point_cloud_profile(las_path, start_xy, end_xy, width=2.0, color_by='elevation', output_image=None) -> str`"

    **Overview & Real-World Use Case:**  
    Extracts a 2D vertical profile corridor (buffer width $W$) through raw 3D LiDAR point clouds, coloring points by elevation ($Z$) or ASPRS classification (Ground, Vegetation, Building).

---

## Full Module Docstrings

::: dronegeo.profiling.elevation_transects
    options:
      members:
        - extract_elevation_transect
        - plot_elevation_transects
        - TransectProfile

::: dronegeo.profiling.diagnostic_plots
    options:
      members:
        - plot_strip_overlap_residuals
        - map_grid_chips
        - plot_anomaly_heatmap
