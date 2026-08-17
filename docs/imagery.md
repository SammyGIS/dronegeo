# True-Color Orthomosaics & Crop Vitality Indices

Create seamless 4-band RGBA photographic orthomosaics from LiDAR RGB colors and compute visible photogrammetric vegetation indices for precision agriculture and forestry.

---

## Photogrammetric Vegetation Indices

When standard drones carry RGB cameras (without expensive multispectral NIR sensors), visible-spectrum vegetation indices can measure crop health and chlorophyll:

| Index | Formula | What It Measures | Real-World Use Case |
| :--- | :--- | :--- | :--- |
| **VARI** | $\frac{G - R}{G + R - B}$ | Atmospherically resistant canopy greenness | Crop vigor, yield forecasting |
| **GLI** | $\frac{2G - R - B}{2G + R + B}$ | Leaf chlorophyll and photosynthesis activity | Nitrogen deficiency, plant stress |
| **TGI** | $G - 0.39R - 0.61B$ | Triangular greenness index | Chlorophyll content in green leaves |
| **ExG** | $2G - R - B$ | Excess Green vegetation segmentation | Weed detection & crop masking |
| **NGRDI** | $\frac{G - R}{G + R}$ | Normalized green-red difference index | Canopy biomass estimation |

---

## Python Code Example

```python
import dronegeo as dg

# 1. Generate 4-Band RGBA Orthomosaic (0.10m resolution)
ortho = dg.imagery.create_true_color_orthomosaic(
    las_path="flight_survey.las",
    output_tif="true_color_ortho.tif",
    resolution=0.10,
    alpha_channel=True,
    auto_contrast=True
)

# 2. Compute Crop Health Indices
vari = dg.imagery.compute_vari(ortho, "crop_health_vari.tif")
gli = dg.imagery.compute_gli(ortho, "chlorophyll_gli.tif")
```
