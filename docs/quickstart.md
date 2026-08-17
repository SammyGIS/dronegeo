# Beginner Quickstart Guide

This step-by-step guide walks you through processing a drone survey from raw point cloud to finished survey deliverables in under 5 minutes.

---

## Step 1: Pre-Processing AutoQC (Inspect & Heal)

Before launching heavy computation, check your raw survey data for defects (e.g. missing projection headers or atmospheric laser dust):

```python
import dronegeo as dg

# 1. Audit raw LAS file
report = dg.autoqc.inspect_point_cloud("flight_raw.las", expected_crs=32632)

# Print friendly console report
report.print_summary()

# 2. If errors were found (e.g. laser noise floaters), auto-heal in 1 line:
if report.has_critical_issues:
    clean_las = dg.autoqc.remediate_point_cloud(
        las_path="flight_raw.las",
        output_las="flight_cleaned.las",
        report=report,
        assign_crs=32632
    )
    print(f"Clean survey saved to: {clean_las}")
```

---

## Step 2: Create Bare-Earth DTM, DSM & Canopy Heights

Convert the 3D laser points into continuous 2D GeoTIFF raster maps:

```python
import dronegeo as dg

# 1. Bare-Earth Digital Terrain Model (DTM)
# Strips trees and buildings using ground classification (Class 2)
dtm_tif = dg.dem.create_dtm(
    las_path="flight_cleaned.las",
    output_tif="terrain_dtm.tif",
    resolution=0.25,      # 25cm pixel resolution
    k_neighbors=8         # Smooth multi-threaded k-NN interpolation
)

# 2. Digital Surface Model (DSM)
# Captures top of tree canopies and building rooftops
dsm_tif = dg.dem.create_dsm(
    las_path="flight_cleaned.las",
    output_tif="surface_dsm.tif",
    resolution=0.25
)

# 3. Canopy Height Model (CHM)
# Measures actual tree and crop heights above the ground (CHM = DSM - DTM)
chm_tif = dg.dem.create_chm(
    dsm_path=dsm_tif,
    dtm_path=dtm_tif,
    output_tif="canopy_height.tif",
    clamp_min=0.0         # Clamps any sub-zero values to 0 meters
)
```

---

## Step 3: Simulate Water Drainage & Flood Risks

Understand how water flows across the site during heavy storms:

```python
import dronegeo as dg

# 1. Flow Accumulation (Finds natural streams and drainage channels)
accum_tif = dg.hydrology.compute_flow_accumulation("terrain_dtm.tif", "flow_accumulation.tif")

# 2. Extract Vector Streams where water concentrates (> 200 contributing cells)
streams_tif = dg.hydrology.extract_stream_network(accum_tif, "streams.tif", threshold_cells=200)

# 3. Topographic Wetness Index (TWI - Flood pooling & waterlogging zones)
twi_tif = dg.hydrology.compute_topographic_wetness_index("terrain_dtm.tif", "flood_pooling_twi.tif")

# 4. Landslide Hazard Score [0-100]
hazard_tif = dg.hydrology.compute_landslide_susceptibility_index("terrain_dtm.tif", "landslide_hazard.tif")
```

---

## Step 4: Measure 3D Excavation Cut & Fill Volumes

Compare two drone flights to measure exact earthwork volumes:

```python
import dronegeo as dg

# Compare site topography before vs after construction
vol = dg.analysis.compute_cut_fill_volume(
    before_dem="quarry_january.tif",
    after_dem="quarry_february.tif",
    output_diff_tif="elevation_difference.tif"
)

print(f"Excavated Dirt (Cut) : {vol.cut_volume_m3:,.1f} m³")
print(f"Deposited Dirt (Fill): {vol.fill_volume_m3:,.1f} m³")
print(f"Net Mass Balance     : {vol.net_volume_m3:+,.1f} m³")
```

---

## Step 5: Export CAD & GIS Vector Contour Lines

Generate smooth elevation contour lines ready for CAD drawings and GIS map layouts:

```python
import dronegeo as dg

# Generate 1.0-meter vector contour lines saved as GeoJSON or Shapefile
contours = dg.analysis.generate_contour_lines(
    dem_path="terrain_dtm.tif",
    output_vector_path="contours_1m.geojson",
    interval_m=1.0
)

print(f"Exported {len(contours):,} contour polylines.")
```
