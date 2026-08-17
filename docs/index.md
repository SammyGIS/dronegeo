# Welcome to `dronegeo` 🛸

<div align="center">
  <img src="images/dronegeo.png" width="280" alt="dronegeo logo" />
  <p><b>High-Performance Python Remote Sensing, UAV LiDAR, Hydrological Flow & Photogrammetry Processing Toolkit</b></p>
</div>

---

## 📖 Overview

`dronegeo` is a modern, modular Python library built for drone survey teams, remote sensing researchers, GIS engineers, and photogrammetry specialists. It bridges raw aerial sensor data (LAS/LAZ point clouds, multiband imagery) and survey-grade deliverables:

- **🔍 AutoQC & Diagnostics**: Automated defect inspection, physical root-cause explanations, and 1-line auto-healing.
- **⛰️ Survey-Grade Surface Models**: Smooth bare-earth DTMs ($k$-NN IDW with zero facet steps), surface DSMs, and Canopy Height Models (CHM).
- **🌊 Hydrological Flow & Flood Risk**: D8 and D-Infinity flow routing, stream channel extraction, Topographic Wetness Index (TWI), and Landslide hazard scoring.
- **🎨 RGB Orthomosaics & Crop Health**: 4-band RGBA orthos and photogrammetric vegetation indices (VARI, GLI, TGI, ExG).
- **📐 Terrain Morphology & 3D Volumetrics**: Analytical hillshades, slope/aspect, vector contours, and excavation cut/fill volume reports.

---

## ⚡ Quick Installation

```bash
pip install dronegeo
```

Or install with development extras:

```bash
pip install "dronegeo[docs,test,dev]"
```
