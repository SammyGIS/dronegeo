# AutoQC: Survey Diagnostics & Auto-Healing

The **AutoQC** engine (`dronegeo.autoqc` or `dronegeo.diagnostics.autoqc`) acts as an automated quality inspector for raw UAV surveys. It detects defects, explains why they occurred in plain language, quantifies the downstream GIS impact, suggests optimal processing parameters, and auto-heals the files.

---

## Why AutoQC Matters

When drones capture LiDAR and photogrammetry data, common field issues arise:
1. **Sensor Multipath Noise**: Optical reflections off water ponds, glass solar panels, or dust in the air create "floating" laser points 100m above the ground.
2. **Missing Spatial Projection (CRS)**: Flight control software often exports raw Cartesian $X, Y, Z$ coordinates without appending the EPSG coordinate system header (e.g. UTM Zone 32N / EPSG 32632).
3. **NoData Voids**: Water bodies or deep tree shadows produce holes in elevation rasters that break drainage and volume calculations.
4. **Sharp Sensor Tears**: High-speed drone banking can cause vertical cliff tears across adjacent pixels.

---

## Comprehensive Defect Matrix

| Issue Code | Defect Title | Severity | Physical Root Cause | Downstream GIS Risk | Prescribed Fix |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `LAS_CRS_MISSING` | Missing EPSG Header | **CRITICAL** | Drone exported local Cartesian coordinates | Fails spatial overlay with other project layers | Injects target EPSG CRS projection header |
| `LAS_MULTIPATH_NOISE` | Outlier Elevation Floaters | **CRITICAL / WARNING** | Laser pulse scattering off dust, birds, water | Creates giant artificial spikes in DSMs | Statistical Outlier Removal (SOR) filtering |
| `LAS_UNCLASSIFIED` | Zero Ground Points | **CRITICAL** | Raw photogrammetric cloud without classification | DTM will mistakenly include trees & buildings | Morphological ground segmentation |
| `LAS_LOW_GROUND_DENSITY` | Sparse Ground Returns | **WARNING** | Dense jungle canopy absorbing laser pulses | Creates jagged interpolation voids | Increases $k$-NN search radius ($k=14$) |
| `DEM_VOID_POCKETS` | NoData Hole Clusters | **CRITICAL / WARNING** | Occlusions, shadows, or water absorption | Breaks hydrological flow paths | Smooth distance-transform nearest-neighbor infill |
| `DEM_ELEVATION_SPIKES` | Vertical Cliff Tears ($>15\text{m}$) | **WARNING** | Propeller wash, crane jibs, or bird strikes | Distorts hillshade visual relief | Adaptive local median despike filter |

---

## Python Usage Example

```python
import dronegeo as dg

# 1. Inspect any survey file (LAS, LAZ, GeoTIFF)
report = dg.autoqc.inspect("raw_flight_survey.las", expected_crs=32632)

# 2. View human-readable terminal summary
report.print_summary()

# 3. Export detailed audit reports (Markdown & JSON)
md_text = report.to_markdown()
json_text = report.to_json()

# 4. 1-Line Automated Remediation
clean_file = dg.autoqc.remediate(
    input_path="raw_flight_survey.las",
    output_path="survey_remediated.las",
    report=report
)
print(f"AutoQC Quality Score: {report.quality_score}/100 -> Repaired deliverable saved!")
```
