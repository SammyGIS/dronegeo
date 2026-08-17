# ⛰️ High-Resolution Surface Models

Generate continuous, survey-grade Digital Terrain Models (DTM), Digital Surface Models (DSM), and Canopy Height Models (CHM).

---

## 🏗️ Surface Interpolation Engine

`dronegeo.dem` uses a multi-threaded $k$-NN Inverse Distance Weighted (IDW) interpolation engine with spatial Kd-Trees:
- **Zero Facet Stepping**: Unlike naive Delaunay Triangulation (TIN), $k$-NN IDW produces smooth, continuous-gradient bare-earth surfaces.
- **Concave Hull Boundary Clamping**: Eliminates artificial interpolation extrapolation beyond true drone flight boundary perimeters.

---

## 💻 Python Example

```python
import dronegeo as dg

# 1. Bare-Earth DTM (Ground Class 2)
dtm_path = dg.dem.create_dtm(
    las_path="survey.las",
    output_tif="dtm_025m.tif",
    resolution=0.25,
    k_neighbors=8,
    ground_class=2
)

# 2. Maximum Surface DSM
dsm_path = dg.dem.create_dsm(
    las_path="survey.las",
    output_tif="dsm_025m.tif",
    resolution=0.25
)

# 3. Canopy Height Model (CHM = DSM - DTM)
chm_path = dg.dem.create_chm(
    dsm_path=dsm_path,
    dtm_path=dtm_path,
    output_tif="canopy_height.tif",
    clamp_min=0.0
)
```
