# Spatial & CRS Management API (`dronegeo.spatial`)

Coordinate Reference System (CRS) resolution, EPSG projection validation, and spatial bounding box arithmetic.

---

### `dronegeo.spatial.resolve_crs`
???+ func "<span class='swagger-badge badge-func'>FUNCTION</span> `dg.spatial.resolve_crs(crs_input) -> pyproj.CRS`"

    **Overview & Real-World Use Case:**  
    Parses any CRS representation (EPSG integer, EPSG string `"EPSG:32632"`, WKT string, PROJ JSON, or `pyproj.CRS` object) into a standardized `pyproj.CRS` instance.

---

## Full Module Docstrings

::: dronegeo.spatial.crs_manager
    options:
      members:
        - resolve_crs
        - is_projected_crs
        - get_utm_epsg_from_lon_lat
        - validate_dataset_crs
