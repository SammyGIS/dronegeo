# Profiling & Visualizations API (`dronegeo.profiling`)

Cross-sectional terrain transects, statistical error residual histograms, and spatial grid chip maps.

---

### `dronegeo.profiling.extract_elevation_transect`
???+ func "<span class='swagger-badge badge-func'>FUNCTION</span> `dg.profiling.extract_elevation_transect(dem_path, start_xy, end_xy, num_samples=200) -> TransectProfile`"

    **Overview & Real-World Use Case:**  
    Extracts a 2D cross-sectional slice along an arbitrary straight-line path across a digital elevation model (e.g. road cross-sections, pipeline routes, or riverbank slopes).

---

### `dronegeo.profiling.plot_elevation_transects`
??? func "<span class='swagger-badge badge-func'>FUNCTION</span> `dg.profiling.plot_elevation_transects(profiles, output_image, title=None) -> str`"

    **Overview & Real-World Use Case:**  
    Renders high-resolution comparative cross-sectional profile charts (e.g. comparing Pre-Construction vs Post-Construction terrain surfaces).

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
