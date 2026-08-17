#!/usr/bin/env python3
"""
Example 09: AutoQC Survey Diagnostics, Root-Cause Analysis & Auto-Healing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Demonstrates:
- Dynamic detection of survey defects (missing CRS, sensor multipath noise, void holes).
- Physical root-cause explanation & impact assessment.
- Automatic parameter estimation to heal defects.
- One-line automated `.remediate()` pipeline to generate clean survey-grade deliverables.
"""

import sys
import os

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import dronegeo as dg
from pathlib import Path
import numpy as np
import rasterio
from rasterio.transform import from_origin
import laspy

OUTPUT_DIR = Path(__file__).parent / "outputs" / "09_autoqc"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def create_defective_datasets(las_out: Path, dem_out: Path) -> None:
    """Generates synthetic survey files with intentional defects to showcase diagnostic tools."""
    # 1. Defective LAS (Missing CRS + 25 Multipath Floaters)
    n = 20_000
    x = 500000.0 + np.random.uniform(0, 150, n)
    y = 5200000.0 + np.random.uniform(0, 150, n)
    z = 250.0 + 0.05 * (x - 500000.0) + np.random.normal(0, 0.04, n)
    z[:25] += 120.0  # Atmospheric noise floaters

    header = laspy.LasHeader(point_format=2, version="1.4")
    header.offsets = [500000.0, 5200000.0, 200.0]
    header.scales = [0.001, 0.001, 0.001]
    las = laspy.LasData(header)
    las.x, las.y, las.z = x, y, z
    las.raw_classification = np.full(n, 2, dtype=np.uint8)
    las.write(str(las_out))

    # 2. Defective DEM (NoData Void Hole + Cliff Tear Spike)
    rows, cols = 80, 80
    y_g, x_g = np.mgrid[0:rows, 0:cols]
    dem_data = (300.0 + 0.06 * x_g + 0.04 * y_g).astype(np.float32)
    dem_data[30:45, 30:45] = -9999.0  # Water hole void
    dem_data[15, 15] += 45.0          # Severe elevation spike

    transform = from_origin(500000.0, 5200080.0, 1.0, 1.0)
    crs = rasterio.crs.CRS.from_epsg(32632)
    with rasterio.open(
        str(dem_out), "w", driver="GTiff", height=rows, width=cols, count=1,
        dtype="float32", crs=crs, transform=transform, nodata=-9999.0
    ) as dst:
        dst.write(dem_data, 1)


def main():
    print("=" * 75)
    print("DroneGeo Example 09: AutoQC Survey Diagnostics & Auto-Healing")
    print("=" * 75)

    raw_las = OUTPUT_DIR / "defective_raw_cloud.las"
    raw_dem = OUTPUT_DIR / "defective_raw_dem.tif"
    clean_las = OUTPUT_DIR / "remediated_clean_cloud.las"
    clean_dem = OUTPUT_DIR / "remediated_clean_dem.tif"
    report_md = OUTPUT_DIR / "autoqc_diagnostic_report.md"

    print("\n[1/4] Preparing defective sample dataset (injected multipath & void gaps)...")
    create_defective_datasets(raw_las, raw_dem)

    # 1. Run Dynamic AutoQC Diagnostics on Point Cloud
    print("\n[2/4] Running AutoQC on Point Cloud...")
    las_report = dg.autoqc.inspect_point_cloud(str(raw_las), expected_crs=32632)
    las_report.print_summary()

    # 2. Run Dynamic AutoQC Diagnostics on Elevation Model
    print("\n[3/4] Running AutoQC on Elevation Model...")
    dem_report = dg.autoqc.inspect_elevation_model(str(raw_dem))
    dem_report.print_summary()

    # Save Markdown Diagnostic Report
    report_md.write_text(las_report.to_markdown() + "\n\n" + dem_report.to_markdown(), encoding="utf-8")
    print(f"\n[+] Detailed Markdown Report saved to: {report_md.name}")

    # 3. Automatically Remediate / Auto-Heal
    print("\n[4/4] Executing Automated Remediation Pipeline...")
    dg.autoqc.remediate_point_cloud(str(raw_las), str(clean_las), report=las_report, assign_crs=32632)
    print(f"  * Cleaned LAS written: {clean_las.name}")

    dg.autoqc.remediate_elevation_model(str(raw_dem), str(clean_dem), report=dem_report)
    print(f"  * Healed DEM written : {clean_dem.name}")

    # 4. Verify Healed Results
    healed_check = dg.autoqc.inspect_elevation_model(str(clean_dem))
    print(f"\n[OK] Healed DEM Quality Score: {healed_check.quality_score}/100 [{healed_check.overall_status.value}]")
    print(f"     Outputs saved to: {OUTPUT_DIR.resolve()}\n")


if __name__ == "__main__":
    main()
