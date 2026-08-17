# True-Color Orthomosaics & Crop Vitality Indices

Create seamless 4-band RGBA photographic orthomosaics from drone surveys and compute visible photogrammetric vegetation indices for precision agriculture and forestry.

---

## 1. What It Does

- **4-Band RGBA True-Color Orthomosaics**: Produces high-resolution photographic aerial maps with transparent nodata boundaries (Alpha channel) that overlay seamlessly in GIS software and project drawings.
- **Precision Agriculture Crop Health**: Evaluates crop nitrogen stress, chlorophyll density, and vegetative biomass using standard RGB cameras (e.g. DJI Mavic 3 Enterprise, Phantom 4 Pro) without needing expensive multispectral NIR hardware.

---

## 2. How It Works

### Orthomosaic Rendering Engine
1. **Point Color Sampling**: Extracts calibrated 8-bit or 16-bit RGB values from laser points.
2. **Dynamic Histogram Contrast Enhancement**: Applies 2%-98% cumulative percentile histogram stretch to correct for atmospheric haze or low-light cloud shadows.
3. **Alpha Channel Masking**: Adds a transparent 4th band covering unpopulated flight boundary pixels.

### Photogrammetric Vegetation Indices

| Index | Mathematical Formula | What It Measures | Real-World Agricultural Use Case |
| :--- | :---: | :--- | :--- |
| **VARI** | $$\frac{G - R}{G + R - B}$$ | Atmospherically resistant canopy greenness | Crop vigor, yield forecasting, drought stress |
| **GLI** | $$\frac{2G - R - B}{2G + R + B}$$ | Leaf chlorophyll & photosynthetic activity | Nitrogen deficiency, plant health monitoring |
| **TGI** | $$G - 0.39R - 0.61B$$ | Triangular greenness index | Chlorophyll content in green leaves |
| **ExG** | $$2G - R - B$$ | Excess Green vegetation segmentation | Weed detection & crop vs soil masking |
| **NGRDI** | $$\frac{G - R}{G + R}$$ | Normalized green-red difference index | Canopy biomass & crop emergence counts |

---

## 3. The Code

```python
import dronegeo as dg

# ---------------------------------------------------------
# Step 1: Generate 4-Band RGBA True-Color Orthomosaic
# ---------------------------------------------------------
ortho_path = dg.imagery.create_true_color_orthomosaic(
    las_path="flight_survey.las",
    output_tif="true_color_orthomosaic.tif",
    resolution=0.10,        # 10cm Ground Sampling Distance
    alpha_channel=True,     # Transparent background
    auto_contrast=True      # 2%-98% histogram contrast stretch
)
print(f"Orthomosaic created: {ortho_path}")

# ---------------------------------------------------------
# Step 2: Compute Agricultural Crop Health Indices
# ---------------------------------------------------------
# 1. Visible Atmospherically Resistant Index (VARI)
vari_tif = dg.imagery.compute_vari(
    ortho_path=ortho_path,
    output_tif="crop_health_vari.tif"
)

# 2. Green Leaf Index (GLI - Chlorophyll)
gli_tif = dg.imagery.compute_gli(
    ortho_path=ortho_path,
    output_tif="leaf_chlorophyll_gli.tif"
)

# 3. Triangular Greenness Index (TGI)
tgi_tif = dg.imagery.compute_tgi(
    ortho_path=ortho_path,
    output_tif="triangular_greenness_tgi.tif"
)

# 4. Excess Green Index (ExG - Weed/Crop Segmentation)
exg_tif = dg.imagery.compute_exg(
    ortho_path=ortho_path,
    output_tif="excess_green_exg.tif"
)

print("All vegetation health maps computed!")
```
