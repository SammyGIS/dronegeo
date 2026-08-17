# Continuous Surface Models (DTM, DSM, CHM)

Generate continuous, survey-grade Digital Terrain Models (DTM), Digital Surface Models (DSM), and Canopy Height Models (CHM).

---

## The $k$-NN IDW Engine vs Traditional TINs

Traditional photogrammetry software often uses naive Delaunay Triangulation (TIN) to create elevation models:
- **The Problem with TINs**: In areas where point spacing varies, TINs create flat, angular triangles ("facet stepping") and artificial elevation cliffs.
- **The `dronegeo` Solution**: `dronegeo.dem` uses a multi-threaded spatial Kd-Tree $k$-Nearest Neighbors ($k$-NN) **Inverse Distance Weighting (IDW)** algorithm:
  $$Z(x, y) = \frac{\sum_{i=1}^k \frac{z_i}{d_i^p}}{\sum_{i=1}^k \frac{1}{d_i^p}}$$
  where $d_i$ is Euclidean distance and $p=2.0$ is the distance power weight. This produces continuous, smooth-gradient terrain models suitable for engineering and hydrology.

---

## 1. Digital Terrain Model (DTM / Bare-Earth)

Strips vegetation, crops, vehicles, and buildings by querying only **Ground Classified Points (Class 2)**:

```python
import dronegeo as dg

dtm_tif = dg.dem.create_dtm(
    las_path="survey.las",
    output_tif="bare_earth_dtm.tif",
    resolution=0.25,        # 0.25m per pixel
    k_neighbors=8,          # 8 nearest neighbors
    ground_class=2          # ASPRS Standard Ground Class
)
```

---

## 2. Digital Surface Model (DSM / Top-of-Canopy)

Captures highest surface elevations (tree canopies, building roofs, transmission towers):

```python
import dronegeo as dg

dsm_tif = dg.dem.create_dsm(
    las_path="survey.las",
    output_tif="surface_dsm.tif",
    resolution=0.25
)
```

---

## 3. Canopy Height Model (CHM)

Calculates the true height of vegetation and structures above the bare earth:
$$\text{CHM} = \max(\text{DSM} - \text{DTM}, 0)$$

```python
import dronegeo as dg

chm_tif = dg.dem.create_chm(
    dsm_path=dsm_tif,
    dtm_path=dtm_tif,
    output_tif="canopy_heights.tif",
    clamp_min=0.0           # Disallow negative heights
)
```
