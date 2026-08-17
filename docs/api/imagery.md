# Imagery & Orthomosaics API (`dronegeo.imagery`)

True-color 4-band (RGBA) photographic orthomosaics and visible vegetation indices (VARI, GLI, TGI, ExG, NGRDI).

---

### `dronegeo.imagery.create_true_color_orthomosaic`
???+ func "<span class='swagger-badge badge-func'>FUNCTION</span> `dg.imagery.create_true_color_orthomosaic(las_path, output_tif, resolution=0.10, alpha_channel=True, ...) -> str`"

    **Overview & Real-World Use Case:**  
    Renders a seamless 4-band (RGBA) photographic orthomosaic GeoTIFF from colored point clouds ($R, G, B$) with transparent Alpha nodata boundaries and optional dynamic contrast enhancement.

    #### Parameters & Inputs
    | Parameter | Type | Required / Default | Description |
    | :--- | :--- | :--- | :--- |
    | `las_path` | `str \| Path` | **Required** | Input LAS file with RGB color channels. |
    | `output_tif` | `str \| Path` | **Required** | Target 4-band RGBA GeoTIFF destination. |
    | `resolution` | `float` | Optional (`0.10`) | Ground resolution in meters per pixel. |
    | `alpha_channel`| `bool` | Optional (`True`) | Whether to add transparent 4th band for nodata boundary masking. |
    | `auto_contrast`| `bool` | Optional (`True`) | Applies 2%-98% cumulative histogram percentile contrast stretch. |

    #### Returns & Outputs
    - **Return Type**: `str` (Path to created Orthomosaic GeoTIFF).

---

### `dronegeo.imagery.compute_visible_vegetation_index`
??? func "<span class='swagger-badge badge-func'>FUNCTION</span> `dg.imagery.compute_visible_vegetation_index(ortho_path, output_tif, index='VARI') -> str`"

    **Overview & Real-World Use Case:**  
    Computes visible-spectrum photogrammetric vegetation health index maps for precision agriculture and crop monitoring.

    #### Supported Mathematical Formulas
    - **VARI**: $\frac{G - R}{G + R - B}$
    - **GLI**: $\frac{2G - R - B}{2G + R + B}$
    - **TGI**: $G - 0.39R - 0.61B$
    - **ExG**: $2G - R - B$
    - **NGRDI**: $\frac{G - R}{G + R}$

---

## Full Module Docstrings

::: dronegeo.imagery.orthomosaic
    options:
      members:
        - create_true_color_orthomosaic
        - enhance_orthomosaic_contrast

::: dronegeo.imagery.vegetation_indices
    options:
      members:
        - compute_vari
        - compute_gli
        - compute_tgi
        - compute_exg
        - compute_ngrdi
        - compute_visible_vegetation_index
