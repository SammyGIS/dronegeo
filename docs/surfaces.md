# Continuous Surface Models (DTM, DSM, CHM)

Generate continuous, survey-grade Digital Terrain Models (DTM), Digital Surface Models (DSM), and Canopy Height Models (CHM) from drone point clouds.

---

## 1. What It Does

When surveying land with a drone or LiDAR scanner, you need continuous raster grids for CAD, GIS, and engineering:
- **Bare-Earth DTM**: Strips away trees, crops, vehicles, and buildings to model the true bare soil and rock surface. Essential for civil engineering, flood risk modeling, and grading plans.
- **Full-Surface DSM**: Captures the top surface of all objects (tree canopies, building rooftops, powerlines). Essential for solar roof potential and line-of-sight analysis.
- **Canopy Height Model (CHM)**: Measures the exact vertical height of trees, forestry timber stands, and agricultural crops above ground level.

---

## 2. How It Works

Traditional photogrammetry software often creates flat, angular triangles ("facet stepping") when generating terrain surfaces using Delaunay Triangulation (TIN).

`dronegeo` solves this using a multi-threaded spatial **Kd-Tree $k$-Nearest Neighbors ($k$-NN) Inverse Distance Weighting (IDW)** algorithm:

$$Z(x, y) = \frac{\sum_{i=1}^k \frac{z_i}{d_i^p}}{\sum_{i=1}^k \frac{1}{d_i^p}}$$

- $d_i$: Euclidean planar distance from pixel center to the $i$-th nearest LiDAR ground point.
- $p = 2.0$: Distance power exponent.
- $k = 8$: Number of spatial neighbors queried via multi-threaded Kd-Tree.

This mathematical interpolation produces mathematically continuous, ultra-smooth terrain gradients without facet tears or jagged stepping.

---

## 3. The Code

```python
import dronegeo as dg

# ---------------------------------------------------------
# 1. Bare-Earth Digital Terrain Model (DTM)
# ---------------------------------------------------------
dtm_tif = dg.dem.create_dtm(
    las_path="survey_flight.las",
    output_tif="bare_earth_dtm.tif",
    resolution=0.25,        # 25cm Ground Sampling Distance (GSD)
    k_neighbors=8,          # 8 nearest ground neighbors
    ground_class=2          # ASPRS Standard Ground Class
)
print(f"Bare-earth DTM created: {dtm_tif}")

# ---------------------------------------------------------
# 2. Digital Surface Model (DSM)
# ---------------------------------------------------------
dsm_tif = dg.dem.create_dsm(
    las_path="survey_flight.las",
    output_tif="surface_dsm.tif",
    resolution=0.25
)
print(f"Full surface DSM created: {dsm_tif}")

# ---------------------------------------------------------
# 3. Canopy Height Model (CHM = DSM - DTM)
# ---------------------------------------------------------
chm_tif = dg.dem.create_chm(
    dsm_path=dsm_tif,
    dtm_path=dtm_tif,
    output_tif="canopy_heights.tif",
    clamp_min=0.0           # Prevents negative heights from minor sensor noise
)
print(f"Canopy height model created: {chm_tif}")

# ---------------------------------------------------------
# 4. Intensity Reflectivity Raster
# ---------------------------------------------------------
intensity_tif = dg.dem.create_intensity_raster(
    las_path="survey_flight.las",
    output_tif="lidar_intensity.tif",
    resolution=0.25
)
print(f"LiDAR reflectivity intensity map created: {intensity_tif}")
```
