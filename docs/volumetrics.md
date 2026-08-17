# 3D Earthwork Volumetrics & Terrain Morphology

Compute 3D excavation cut/fill volume differences, audit stockpile materials, and generate CAD/GIS vector contour lines.

---

## 1. What It Does

In civil construction, quarry mining, and landfill management, project managers need accurate volumetric quantities for billing and progress monitoring:
- **3D Cut & Fill Volumetrics**: Measures exact earthmoving quantities excavated (cut) or deposited (fill) between two drone flight surveys (e.g. Month 1 vs Month 2).
- **Stockpile Auditing**: Computes the volume ($m^3$) and footprint surface area ($m^2$) of gravel, sand, or mineral stockpiles above a reference datum.
- **Topographic Terrain Morphology**: Generates analytical hillshades, slope gradients (degrees), compass aspect directions (0°-360°), and CAD vector contour lines.

---

## 2. How It Works

### Volumetric Integration Mathematics
For every cell $(x, y)$ in the aligned DEM grid:
$$\Delta Z(x, y) = Z_{\text{after}}(x, y) - Z_{\text{before}}(x, y)$$

$$\text{Cell Area} = \Delta x \times \Delta y = \text{resolution}^2$$

- **Excavated Cut Volume ($m^3$)**:
  $$V_{\text{cut}} = \sum_{\Delta Z < 0} |\Delta Z(x, y)| \times \text{Cell Area}$$
- **Deposited Fill Volume ($m^3$)**:
  $$V_{\text{fill}} = \sum_{\Delta Z > 0} \Delta Z(x, y) \times \text{Cell Area}$$
- **Net Mass Balance ($m^3$)**:
  $$V_{\text{net}} = V_{\text{fill}} - V_{\text{cut}}$$

---

## 3. The Code

```python
import dronegeo as dg

# ---------------------------------------------------------
# Step 1: 3D Cut & Fill Volume between Survey Epochs
# ---------------------------------------------------------
vol_report = dg.analysis.compute_cut_fill_volume(
    before_dem="quarry_month1_dtm.tif",
    after_dem="quarry_month2_dtm.tif",
    output_diff_tif="elevation_difference_map.tif"
)

print(f"Excavated Cut Volume : {vol_report.cut_volume_m3:,.2f} m³")
print(f"Deposited Fill Volume: {vol_report.fill_volume_m3:,.2f} m³")
print(f"Net Mass Balance     : {vol_report.net_volume_m3:+,.2f} m³")
print(f"Mean Elevation Shift : {vol_report.mean_elevation_change_m:+.3f} m")

# ---------------------------------------------------------
# Step 2: Stockpile Material Volume Audit
# ---------------------------------------------------------
stockpile = dg.analysis.compute_stockpile_volume(
    dem_path="stockpile_dtm.tif",
    base_elevation=540.0    # Reference toe base elevation in meters
)

print(f"Stockpile Volume: {stockpile.cut_volume_m3:,.2f} m³")
print(f"Surface Footprint: {stockpile.surface_area_m2:,.1f} m²")

# ---------------------------------------------------------
# Step 3: Topographic Morphology & Vector Contours
# ---------------------------------------------------------
# Analytical Shaded Relief Hillshade
dg.analysis.generate_hillshade("quarry_month2_dtm.tif", "hillshade.tif", azimuth=315.0, altitude=45.0)

# Topographic Slope Gradient (degrees)
dg.analysis.generate_slope_map("quarry_month2_dtm.tif", "slope_degrees.tif", units="degrees")

# Compass Aspect Direction (0° - 360°)
dg.analysis.generate_aspect_map("quarry_month2_dtm.tif", "aspect_compass.tif")

# 1.0m CAD/GIS Vector Contour Lines (GeoJSON / Shapefile)
contours_gdf = dg.analysis.generate_contour_lines(
    dem_path="quarry_month2_dtm.tif",
    output_vector_path="contours_1m.geojson",
    interval_m=1.0
)
print(f"Exported {len(contours_gdf):,} vector contour line segments.")
```
