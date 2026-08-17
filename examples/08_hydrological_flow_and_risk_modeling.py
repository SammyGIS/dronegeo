#!/usr/bin/env python3
"""
Example 08: Hydrological Flow Routing & Terrain Risk Modeling
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Demonstrates terrain hydrology algorithms and risk modeling tools with
peer-reviewed scientific literature references:

1. Flow Direction Routing:
   * D8 Steepest Descent: O'Callaghan & Mark (1984)
   * D-Infinity Continuous Flow Angle: Tarboton (1997)

2. Catchment Drainage:
   * Flow Accumulation (Upslope contributing area): Jenson & Domingue (1988)
   * Stream Channel Network Extraction: Tarboton, Bras & Rodriguez-Iturbe (1991)

3. Environmental Risk Indices:
   * Topographic Wetness Index (TWI / CTI): Beven & Kirkby (1979) - Flood pooling & soil saturation
   * Stream Power Index (SPI): Moore et al. (1991) - Channel scouring & erosion risk
   * Sediment Transport Index (STI / USLE LS factor): Moore & Burch (1986) - Hillslope soil loss
   * Multi-Criteria Landslide Hazard Susceptibility: Montgomery & Dietrich (1994)
"""

import sys
import os

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from pathlib import Path
import subprocess
import dronegeo as dg

OUTPUT_DIR = Path(__file__).parent / "outputs" / "08_hydrology_risk"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
SAMPLE_LAS = Path(__file__).parent / "data" / "flight_survey_master.las"
DEM_TIF = OUTPUT_DIR / "hydrology_dtm.tif"


def ensure_base_dem():
    if not DEM_TIF.exists():
        if not SAMPLE_LAS.exists():
            gen_script = Path(__file__).parent / "00_generate_sample_datasets.py"
            subprocess.run([sys.executable, str(gen_script)], check=True)
        print("Generating baseline DTM for hydrology and risk modeling...")
        dg.dem.create_dtm(str(SAMPLE_LAS), str(DEM_TIF), resolution=0.50)


def main():
    print("=" * 75)
    print("DroneGeo Example 08: Hydrological Flow & Terrain Risk Modeling")
    print("=" * 75)

    ensure_base_dem()

    d8_tif = OUTPUT_DIR / "flow_direction_d8.tif"
    dinf_tif = OUTPUT_DIR / "flow_direction_dinfinity.tif"
    accum_tif = OUTPUT_DIR / "flow_accumulation.tif"
    streams_tif = OUTPUT_DIR / "extracted_stream_channels.tif"
    twi_tif = OUTPUT_DIR / "topographic_wetness_index_twi.tif"
    spi_tif = OUTPUT_DIR / "stream_power_index_spi.tif"
    sti_tif = OUTPUT_DIR / "sediment_transport_index_sti.tif"
    hazard_tif = OUTPUT_DIR / "landslide_susceptibility_hazard.tif"

    # 1. Flow Direction Routing
    print("\n[1/4] Computing Hydrological Flow Routing Algorithms...")
    print("  * D8 Algorithm (O'Callaghan & Mark, 1984)...")
    dg.hydrology.compute_d8_flow_direction(str(DEM_TIF), str(d8_tif))

    print("  * D-Infinity Algorithm (Tarboton, 1997)...")
    dg.hydrology.compute_dinfinity_flow_direction(str(DEM_TIF), str(dinf_tif))

    # 2. Flow Accumulation & Channel Network
    print("\n[2/4] Computing Contributing Catchment Area & Channels...")
    print("  * Topological Flow Accumulation (Jenson & Domingue, 1988)...")
    dg.hydrology.compute_flow_accumulation(str(DEM_TIF), str(accum_tif), units="cells")

    print("  * Channel Head Extraction (Tarboton et al., 1991)...")
    dg.hydrology.extract_stream_network(str(accum_tif), str(streams_tif), threshold_cells=200)

    # 3. Environmental Erosion & Saturation Risk Indices
    print("\n[3/4] Modeling Topographic Risk & Wetness Indices...")
    print("  * Topographic Wetness Index (TWI - Beven & Kirkby, 1979)...")
    dg.hydrology.compute_topographic_wetness_index(str(DEM_TIF), str(twi_tif))

    print("  * Stream Power Index (SPI - Moore et al., 1991)...")
    dg.hydrology.compute_stream_power_index(str(DEM_TIF), str(spi_tif))

    print("  * Sediment Transport Index (STI / USLE LS - Moore & Burch, 1986)...")
    dg.hydrology.compute_sediment_transport_index(str(DEM_TIF), str(sti_tif))

    # 4. Multi-Criteria Slope Failure / Landslide Hazard Score
    print("\n[4/4] Generating Multi-Criteria Landslide Hazard Score...")
    print("  * Slope Instability Model (Montgomery & Dietrich, 1994)...")
    dg.hydrology.compute_landslide_susceptibility_index(
        dem_path=str(DEM_TIF),
        output_tif=str(hazard_tif),
        slope_weight=0.50,
        twi_weight=0.35,
        curvature_weight=0.15,
    )

    twi_meta = dg.utils.get_raster_metadata_summary(str(twi_tif))
    print("\n--- Hydrology & Risk Summary ---")
    print(f"Grid GSD Resolution : {twi_meta['resolution_x_m']} m")
    print(f"TWI Value Range     : [{twi_meta['z_min_m']:.2f}, {twi_meta['z_max_m']:.2f}]")
    print(f"\n[OK] All hydrological and risk models saved in: {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    main()
