# Hydrology & Flood Risk API (`dronegeo.hydrology`)

Hydrological flow routing, drainage accumulation, stream channels, Topographic Wetness Index (TWI), and Landslide hazard scoring.

---

### `dronegeo.hydrology.compute_d8_flow_direction`
???+ func "<span class='swagger-badge badge-func'>FUNCTION</span> `dg.hydrology.compute_d8_flow_direction(dem_path, output_tif) -> str`"

    **Overview & Real-World Use Case:**  
    Calculates deterministic steepest descent flow direction across 8 neighbor pixels using the O'Callaghan & Mark (1984) D8 routing algorithm. Encodes direction as ESRI power-of-two bits (1, 2, 4, 8, 16, 32, 64, 128).

    #### Parameters & Inputs
    | Parameter | Type | Required / Default | Description |
    | :--- | :--- | :--- | :--- |
    | `dem_path` | `str \| Path` | **Required** | Input bare-earth DTM GeoTIFF file path. |
    | `output_tif` | `str \| Path` | **Required** | Destination uint8 GeoTIFF file path for D8 directions. |

    #### Returns & Outputs
    - **Return Type**: `str` (Path to created D8 flow direction GeoTIFF).

---

### `dronegeo.hydrology.compute_flow_accumulation`
??? func "<span class='swagger-badge badge-func'>FUNCTION</span> `dg.hydrology.compute_flow_accumulation(dem_path, output_tif, units='cells') -> str`"

    **Overview & Real-World Use Case:**  
    Calculates cumulative upslope contributing catchment area for every pixel on the landscape. Identifies stream valleys, natural swales, and drainage paths.

---

### `dronegeo.hydrology.compute_topographic_wetness_index`
??? func "<span class='swagger-badge badge-func'>FUNCTION</span> `dg.hydrology.compute_topographic_wetness_index(dem_path, output_tif) -> str`"

    **Overview & Real-World Use Case:**  
    Computes the Beven & Kirkby (1979) Topographic Wetness Index: $\text{TWI} = \ln\left(\frac{a}{\tan \beta}\right)$. Identifies soil saturation and flood pooling zones.

---

### `dronegeo.hydrology.compute_landslide_susceptibility_index`
??? func "<span class='swagger-badge badge-func'>FUNCTION</span> `dg.hydrology.compute_landslide_susceptibility_index(dem_path, output_tif) -> str`"

    **Overview & Real-World Use Case:**  
    Evaluates multi-criteria slope stability hazard score (0 to 100) based on Montgomery & Dietrich (1994) shallow landslide physics.

---

## Full Module Docstrings

::: dronegeo.hydrology.flow_direction
    options:
      members:
        - compute_d8_flow_direction
        - compute_dinfinity_flow_direction

::: dronegeo.hydrology.flow_accumulation
    options:
      members:
        - compute_flow_accumulation
        - extract_stream_network

::: dronegeo.hydrology.risk_indices
    options:
      members:
        - compute_topographic_wetness_index
        - compute_stream_power_index
        - compute_sediment_transport_index
        - compute_landslide_susceptibility_index
