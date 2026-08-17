# 🔍 AutoQC: Dynamic Diagnostics & Auto-Healing

The **AutoQC** module (`dronegeo.autoqc` or `dronegeo.diagnostics.autoqc`) automatically inspects raw drone surveys for defects, explains the physical root cause, and provides a 1-line auto-healing pipeline.

---

## 🛠️ Defect Detection Heuristics

| Defect Code | Name | Physical Root Cause | Actionable AutoQC Fix |
| :--- | :--- | :--- | :--- |
| `LAS_CRS_MISSING` | Missing EPSG Header | Flight controller exported local Cartesian coordinates | Embeds target EPSG CRS projection |
| `LAS_MULTIPATH_NOISE` | Outlier Elevation Floaters | Dust, birds, glass/water multipath reflections | Filters statistical elevation outliers ($3\sigma$) |
| `LAS_LOW_GROUND_DENSITY` | Low Ground Penetration | Dense forest canopy or NIR pulse absorption | Increases $k$-NN search radius |
| `DEM_VOID_POCKETS` | NoData Holes / Gaps | Sensor occlusions, shadows, or small search radius | Distance-transform nearest-neighbor infill |
| `DEM_ELEVATION_SPIKES` | Sharp Cliff Tears ($>15\text{m}$) | Aerial obstacle strikes (cranes, powerlines, birds) | Local adaptive median despike filter |

---

## 💻 Python Example

```python
import dronegeo as dg

# 1. Run AutoQC on raw LAS
report = dg.autoqc.inspect_point_cloud("flight.las", expected_crs=32632)
report.print_summary()

# 2. Export detailed Markdown & JSON reports
report_md = report.to_markdown()
report_json = report.to_json()

# 3. Automatically remediate / heal
clean_las = dg.autoqc.remediate_point_cloud("flight.las", "flight_clean.las", report=report)
```
