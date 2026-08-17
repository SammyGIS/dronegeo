"""
09_gcp_accuracy_validation.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
High-Performance GCP & Checkpoint Accuracy Validation and AutoQC Remediation.

Demonstrates:
1. Creating/loading surveyed Ground Control Points (GCPs & Checkpoints) from CSV, Shapefiles, or GeoJSON.
2. Running pre-flight AutoQC on raw LAS/LAZ point clouds against surveyed field targets.
3. Calculating ASPRS / NSSDA standard positional accuracy metrics (RMSEz, Mean Bias, 95% Confidence).
4. Detecting gross surveyor blunders (e.g. pole height entry typos or mislabeled markers).
5. Automatically remediating vertical datum bias (e.g. Ellipsoid vs Geoid undulation offset).
"""

from pathlib import Path
import json
import numpy as np
import laspy

import dronegeo as dg

OUTPUT_DIR = Path("./output_gcp_validation")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def main():
    print("=" * 80)
    print("  DRONEGEO - GROUND CONTROL POINT (GCP) ACCURACY AUDIT & AUTOQC")
    print("=" * 80)

    # -------------------------------------------------------------------------
    # STEP 1: Generate Synthetic Drone Flight LAS & Field GCP Dataset
    # -------------------------------------------------------------------------
    print("\n[Step 1] Generating raw drone survey point cloud with a systematic -18cm datum bias...")
    las_path = OUTPUT_DIR / "flight_block_uncalibrated.las"
    gcp_csv = OUTPUT_DIR / "field_survey_gcps.csv"
    gcp_geojson = OUTPUT_DIR / "field_survey_gcps.geojson"

    n_points = 25000
    np.random.seed(42)
    xs = np.random.uniform(500000.0, 500200.0, n_points)
    ys = np.random.uniform(5200000.0, 5200200.0, n_points)
    # Ground truth elevation: 120.0m + slope + slight undulation
    z_true = 120.0 + 0.04 * (xs - 500000.0) + 0.03 * (ys - 5200000.0)
    # Introduce deliberate -0.18m systematic vertical datum shift + 2cm random flight noise
    z_drone = z_true - 0.18 + np.random.normal(0, 0.02, n_points)

    header = laspy.LasHeader(point_format=3, version="1.4")
    header.offsets = [500000.0, 5200000.0, 100.0]
    header.scales = [0.001, 0.001, 0.001]
    las = laspy.LasData(header)
    las.x, las.y, las.z = xs, ys, z_drone
    las.classification = np.full(n_points, 2, dtype=np.uint8)  # Class 2: Ground
    las.write(str(las_path))

    # Field Survey Ground Control Points (RTK Surveyed Ground Truth)
    # 5 GCPs, 2 Independent Checkpoints, 1 deliberate blunder (rod height typo: -0.65m)
    survey_points = [
        ("GCP_01", 500030.0, 5200030.0, 120.0 + 0.04 * 30.0 + 0.03 * 30.0, "GCP"),
        ("GCP_02", 500090.0, 5200040.0, 120.0 + 0.04 * 90.0 + 0.03 * 40.0, "GCP"),
        ("GCP_03", 500150.0, 5200080.0, 120.0 + 0.04 * 150.0 + 0.03 * 80.0, "GCP"),
        ("GCP_04", 500050.0, 5200160.0, 120.0 + 0.04 * 50.0 + 0.03 * 160.0, "GCP"),
        ("GCP_05", 500170.0, 5200170.0, 120.0 + 0.04 * 170.0 + 0.03 * 170.0, "GCP"),
        ("CHK_01", 500100.0, 5200100.0, 120.0 + 0.04 * 100.0 + 0.03 * 100.0, "CHECK"),
        ("CHK_02", 500120.0, 5200140.0, 120.0 + 0.04 * 120.0 + 0.03 * 140.0, "CHECK"),
        ("GCP_BLUNDER", 500080.0, 5200090.0, (120.0 + 0.04 * 80.0 + 0.03 * 90.0) - 0.65, "GCP"),
    ]

    # Save to CSV
    with open(gcp_csv, "w", encoding="utf-8") as f:
        f.write("id,easting,northing,elevation,type\n")
        for gid, gx, gy, gz, gtype in survey_points:
            f.write(f"{gid},{gx},{gy},{gz:.3f},{gtype}\n")

    # Save to GeoJSON
    features = [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [gx, gy, gz]},
            "properties": {"id": gid, "type": gtype, "elevation": gz}
        }
        for gid, gx, gy, gz, gtype in survey_points
    ]
    with open(gcp_geojson, "w", encoding="utf-8") as f:
        json.dump({"type": "FeatureCollection", "features": features}, f, indent=2)

    print(f"  [OK] Raw LAS point cloud written : {las_path} ({n_points:,} points)")
    print(f"  [OK] Survey GCPs exported to CSV : {gcp_csv}")
    print(f"  [OK] Survey GCPs exported to JSON: {gcp_geojson}")

    # -------------------------------------------------------------------------
    # STEP 2: Direct GCP Accuracy Validation (ASPRS Standards Engine)
    # -------------------------------------------------------------------------
    print("\n[Step 2] Executing standalone ASPRS GCP accuracy validation...")
    gcp_report = dg.validate_gcp_accuracy(
        dataset_path=las_path,
        gcp_data=gcp_csv,
        search_radius=2.5,
        target_tolerance_m=0.05,  # 5 cm engineering specification
    )

    gcp_report.print_summary()

    # -------------------------------------------------------------------------
    # STEP 3: Full AutoQC Pipeline with Integrated GCP Verification
    # -------------------------------------------------------------------------
    print("\n[Step 3] Running full AutoQC pre-flight inspection with GCPs...")
    qc_report = dg.autoqc.inspect_point_cloud(
        las_path=las_path,
        expected_crs=32632,
        gcp_data=gcp_geojson,
        target_tolerance_m=0.05,
    )
    qc_report.print_summary()

    # -------------------------------------------------------------------------
    # STEP 4: Automated Point Cloud Remediation (Auto-Datum Rectification)
    # -------------------------------------------------------------------------
    print("\n[Step 4] Auto-Remediating point cloud with calibrated vertical datum shift...")
    calibrated_las = OUTPUT_DIR / "flight_block_calibrated.las"
    dg.autoqc.remediate_point_cloud(
        las_path=las_path,
        output_las=calibrated_las,
        report=qc_report,
        assign_crs=32632,
    )

    # -------------------------------------------------------------------------
    # STEP 5: Post-Remediation Verification Audit
    # -------------------------------------------------------------------------
    print("\n[Step 5] Auditing accuracy of calibrated point cloud against GCPs...")
    # Exclude blunder point for final clean verification
    clean_gcps = [p for p in survey_points if p[0] != "GCP_BLUNDER"]
    post_report = dg.validate_gcp_accuracy(
        dataset_path=calibrated_las,
        gcp_data=clean_gcps,
        target_tolerance_m=0.05,
    )
    post_report.print_summary()

    print("\n" + "=" * 80)
    print("  GCP ACCURACY VALIDATION & AUTO-RECTIFICATION WORKFLOW COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
