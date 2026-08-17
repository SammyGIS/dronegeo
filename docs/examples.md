# 📦 Examples Catalog & Interactive Notebooks

All examples are standalone and runnable in the repository's `examples/` directory.

---

## 🚀 Standalone Script Workflows

```bash
# 1. Generate canonical sample datasets once
python examples/00_generate_sample_datasets.py

# 2. Run any workflow
python examples/01_point_cloud_audit.py
python examples/02_strip_alignment_and_merging.py
python examples/03_surface_models_dtm_dsm_chm.py
python examples/04_orthomosaic_and_vegetation_indices.py
python examples/05_terrain_morphology_and_contours.py
python examples/06_earthwork_cut_fill_volumetrics.py
python examples/07_elevation_transects_and_qc.py
python examples/08_hydrological_flow_and_risk_modeling.py
python examples/09_autoqc_survey_diagnostics_and_healing.py
python examples/10_gcp_accuracy_validation.py
```

| Script | Workflow Name | What It Demonstrates |
| :--- | :--- | :--- |
| `01_point_cloud_audit.py` | LiDAR Inspection | Point density, bounding bounds, ground return ratio, classification summary. |
| `02_strip_alignment_and_merging.py` | Strip Co-Registration | Detects inter-strip vertical shift $\Delta Z$, plots error histogram, merges strips. |
| `03_surface_models_dtm_dsm_chm.py` | Surface Rasterization | 0.10m Bare-Earth DTM, DSM, and Canopy Height Model (CHM) generation. |
| `04_orthomosaic_and_vegetation_indices.py` | Orthophotos & Crops | 4-band RGBA orthomosaics and VARI / GLI / TGI crop vitality indices. |
| `05_terrain_morphology_and_contours.py` | Morphology & Vectors | Hillshade, slope, aspect, and smooth vector contour lines (Shapefile/GeoJSON). |
| `06_earthwork_cut_fill_volumetrics.py` | 3D Volumetrics | Cut/Fill excavation volumes between epochs and stockpile volume calculations. |
| `07_elevation_transects_and_qc.py` | Cross-Section Profiles | Extracts 2D elevation transects and renders comparative multi-epoch charts. |
| `08_hydrological_flow_and_risk_modeling.py` | Watershed Hydrology | D8/D-Inf flow routing, accumulation streams, TWI flood pooling, SPI, and landslides. |
| `09_autoqc_survey_diagnostics_and_healing.py` | AutoQC Auto-Healing | Pre-flight audit, floater noise filtering, missing CRS injection, and void filling. |
| `10_gcp_accuracy_validation.py` | GCP Accuracy Audit | Ingests Shapefile/GeoJSON/CSV, evaluates ASPRS $\text{RMSE}_z$, and auto-rectifies $\Delta Z$. |

---

## 📓 Interactive Jupyter Tutorial

Launch the end-to-end tutorial notebook:

```bash
jupyter notebook examples/notebooks/dronegeo_interactive_tutorial.ipynb
```
