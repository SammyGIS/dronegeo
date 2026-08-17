# 📐 3D Earthwork Volumetrics & Terrain Morphology

Compute 3D cut/fill earthwork volumes, stockpile volume audits, and extract vector elevation contour lines.

---

## 🏗️ Volumetrics Engine

- **Multi-Temporal Cut & Fill**: Computes exact excavated cut volume ($m^3$), deposited fill volume ($m^3$), and net mass balance ($\Delta Z$) between two survey epochs.
- **Stockpile Volume**: Computes above-datum pile volume ($m^3$) and footprint surface area ($m^2$).
- **Vector Contours**: Extracts smooth contour polylines exported to Shapefile (.shp), GeoJSON, or GeoPackage.

---

## 💻 Python Example

```python
import dronegeo as dg

# 1. 3D Cut & Fill Volume between Epoch 1 and Epoch 2
report = dg.analysis.compute_cut_fill_volume(
    before_dem="quarry_epoch1.tif",
    after_dem="quarry_epoch2.tif",
    output_diff_tif="elevation_diff.tif"
)
print(f"Excavated Cut : {report.cut_volume_m3:,.1f} m³")
print(f"Deposited Fill: {report.fill_volume_m3:,.1f} m³")
print(f"Net Balance   : {report.net_volume_m3:+,.1f} m³")

# 2. Extract 1.0m Vector Contour Lines
contours = dg.analysis.generate_contour_lines("dtm.tif", "contours_1m.geojson", interval_m=1.0)
```
