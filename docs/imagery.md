# 🎨 True-Color Orthomosaics & Crop Health Indices

Transform point cloud RGB colors into 4-band RGBA GeoTIFF orthomosaics and compute visible photogrammetric vegetation indices.

---

## 🌿 Supported Vegetation Indices

- **VARI** (Visible Atmospherically Resistant Index): $(G - R) / (G + R - B)$ - Crop canopy greenness.
- **GLI** (Green Leaf Index): $(2G - R - B) / (2G + R + B)$ - Leaf chlorophyll vitality.
- **TGI** (Triangular Greenness Index): Nitrogen and chlorophyll monitoring.
- **ExG** (Excess Green Index): $2G - R - B$ - Weed & vegetation segmentation.
- **NGRDI** (Normalized Green-Red Difference Index): $(G - R) / (G + R)$.

---

## 💻 Python Example

```python
import dronegeo as dg

# 1. 4-Band RGBA Orthomosaic
ortho = dg.imagery.create_true_color_orthomosaic(
    las_path="survey.las",
    output_tif="orthomosaic.tif",
    resolution=0.20,
    alpha_channel=True,
    auto_contrast=True
)

# 2. Photometric Crop Indices
vari = dg.imagery.compute_vari(ortho, "crop_vari.tif")
gli = dg.imagery.compute_gli(ortho, "leaf_gli.tif")
```
