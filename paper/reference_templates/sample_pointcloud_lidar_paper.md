---
title: 'LiGuard: A Python Framework for LiDAR Quality Assurance and Sensor Noise Rectification'
tags:
  - Python
  - LiDAR
  - point cloud
  - remote sensing
  - quality control
authors:
  - name: Research Contributor
    orcid: 0000-0000-0000-0000
    affiliation: 1
affiliations:
  - name: Institute for Airborne Remote Sensing, Earth Observation Center
    index: 1
date: 15 March 2024
bibliography: paper.bib
---

# Summary

Light Detection and Ranging (LiDAR) provides millimeter-to-centimeter precision 3D structural measurements across terrestrial, airborne, and drone observation platforms. However, raw point clouds frequently suffer from atmospheric multipath reflections, laser sensor blooming, and uncalibrated flight strip datum offsets. `LiGuard` is a lightweight Python framework designed to automate the detection, filtering, and statistical healing of defective point clouds in high-throughput data pipelines.

# Statement of Need

Geoscientists and forestry researchers frequently process multi-gigabyte point clouds collected across complex terrain. Existing open-source point cloud processing suites (such as PDAL or CloudCompare) require extensive C++ build steps or manual graphical user interaction. `LiGuard` addresses this limitation by offering pure Python bindings built directly on NumPy and Laspy, allowing researchers to embed automated statistical outlier removal, strip co-registration, and ground surface classification into cloud-native automated analysis pipelines.

# State of the Field

| Feature | `LiGuard` | `PDAL Filters` | `CloudCompare` |
| :--- | :---: | :---: | :---: |
| **Interface** | Pure Python | C++ JSON Pipeline | Desktop GUI |
| **Automated Strip QA** | ✅ Native | ⚠️ Custom Scripting | ❌ Manual |
| **Statistical Outlier Filter** | ✅ Dynamic | ✅ Static | ✅ Manual |
| **Zero-C Setup** | ✅ | ❌ | ❌ |

# Key Features

- **Automated Multipath Noise Filtering:** Statistical IQR and local density thresholding.
- **Flightline Co-registration:** Computes elevation offsets ($\Delta Z$) between overlapping flight lines.
- **Header Metadata Resolution:** Injects missing EPSG coordinate reference systems into raw point cloud headers.

# Example Usage

```python
import liguard as lg

# Clean and co-register raw flight lines
clean_las = lg.clean_point_cloud("flight_01_raw.las", output_path="flight_01_clean.las")
report = lg.audit_strip_alignment("flight_01_clean.las", "flight_02_clean.las")
print(f"Mean flightline vertical offset: {report.mean_delta_z:.3f} m")
```

# Acknowledgements

We thank the developers of Laspy and SciPy for the foundational libraries supporting this work.

# References
