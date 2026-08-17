# 🚀 Quickstart Guide

Get started with `dronegeo` in 3 simple steps:

---

### 1. Pre-Processing AutoQC Inspection

```python
import dronegeo as dg

# Inspect raw LiDAR survey point cloud
report = dg.autoqc.inspect_point_cloud("survey.las", expected_crs=32632)
report.print_summary()

# If issues were detected, auto-heal with 1 line
if report.has_critical_issues:
    clean_las = dg.autoqc.remediate_point_cloud("survey.las", "cleaned_survey.las", report=report)
```

---

### 2. Generate Survey-Grade Surface Models (DTM, DSM, CHM)

```python
import dronegeo as dg

# Continuous Ground DTM via multi-threaded k-NN IDW
dtm = dg.dem.create_dtm("cleaned_survey.las", "dtm.tif", resolution=0.25)

# Maximum Surface DSM
dsm = dg.dem.create_dsm("cleaned_survey.las", "dsm.tif", resolution=0.25)

# Canopy Height Model (CHM = DSM - DTM)
chm = dg.dem.create_chm(dsm, dtm, "canopy_height.tif")
```

---

### 3. Hydrology & Terrain Risk Modeling

```python
import dronegeo as dg

# Flow accumulation and stream network extraction
accum = dg.hydrology.compute_flow_accumulation("dtm.tif", "flow_accum.tif")
streams = dg.hydrology.extract_stream_network("flow_accum.tif", "streams.tif", threshold_cells=200)

# Topographic Wetness Index (Flood & soil saturation risk)
twi = dg.hydrology.compute_topographic_wetness_index("dtm.tif", "twi.tif")

# Landslide susceptibility hazard score [0-100]
hazard = dg.hydrology.compute_landslide_susceptibility_index("dtm.tif", "landslide_hazard.tif")
```
