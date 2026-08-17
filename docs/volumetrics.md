# 3D Earthwork Volumetrics & Terrain Morphology

Compute 3D excavation cut/fill volume differences, audit stockpile materials, and generate CAD/GIS vector contour lines.

---

## Earthwork Cut & Fill Volumetrics Explained

When monitoring quarries, mining pits, or civil construction sites, drone surveys are flown periodically (e.g. Month 1 vs Month 2):
- **Cut Volume ($m^3$)**: Material excavated / removed where the new elevation is lower than the previous elevation ($\Delta Z < 0$).
- **Fill Volume ($m^3$)**: Material deposited / added where the new elevation is higher than the previous elevation ($\Delta Z > 0$).
- **Net Volume ($m^3$)**: $\text{Fill Volume} - \text{Cut Volume}$.

---

## Stockpile Volume Auditing

Calculates the total material volume ($m^3$) of aggregate gravel, sand, or mineral stockpiles sitting above a reference base datum plane or toe boundary.

---

## Python Code Example

```python
import dronegeo as dg

# 1. 3D Cut & Fill Volumetric Report between Two Survey Epochs
vol = dg.analysis.compute_cut_fill_volume(
    before_dem="quarry_january.tif",
    after_dem="quarry_february.tif",
    output_diff_tif="elevation_diff.tif"
)

print(f"Excavated Cut Volume : {vol.cut_volume_m3:,.1f} m³")
print(f"Deposited Fill Volume: {vol.fill_volume_m3:,.1f} m³")
print(f"Net Balance          : {vol.net_volume_m3:+,.1f} m³")

# 2. Stockpile Volume Audit above Reference Datum (e.g. 540m)
stockpile = dg.analysis.compute_stockpile_volume("stockpile_dtm.tif", base_elevation=540.0)
print(f"Stockpile Volume: {stockpile.cut_volume_m3:,.2f} m³ across {stockpile.surface_area_m2:,.1f} m²")

# 3. Generate 1.0m Vector Contour Lines
contours = dg.analysis.generate_contour_lines("quarry_february.tif", "contours_1m.geojson", interval_m=1.0)
```
