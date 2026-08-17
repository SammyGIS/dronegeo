# Utilities & Helpers API (`dronegeo.utils`)

File validation, bounding box geometric helpers, color ramps, and benchmarking timers.

---

### `dronegeo.utils.benchmark_timer`
???+ func "<span class='swagger-badge badge-context'>CONTEXT MANAGER</span> `dg.utils.benchmark_timer(label='Task')`"

    **Overview & Real-World Use Case:**  
    Measures and logs exact high-precision execution runtime in seconds or milliseconds for performance auditing.

---

## Full Module Docstrings

::: dronegeo.utils.geo_utils
    options:
      members:
        - compute_bounding_box_area
        - compute_bounding_box_intersection
        - compute_bounding_box_union

::: dronegeo.utils.file_utils
    options:
      members:
        - verify_las_file
        - verify_raster_file
        - ensure_output_directory
