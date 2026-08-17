"""
tests.test_end_to_end
~~~~~~~~~~~~~~~~~~~~~
Integration test running full end-to-end drone survey processing workflow:
Raw LAS -> Point Cloud Audit -> DTM/DSM/CHM -> Orthomosaic -> Morphology -> Volumetrics.
"""

import os
import dronegeo as dg


def test_full_survey_processing_pipeline(synthetic_las_file, temp_workspace):
    """
    Executes an end-to-end survey pipeline on synthetic flight data:
    1. Audits point cloud
    2. Generates continuous DTM (0.5m)
    3. Generates DSM (0.5m)
    4. Computes Canopy Height Model (CHM)
    5. Computes True-Color Orthomosaic
    6. Computes VARI vegetation index
    7. Computes Hillshade and Topographic Slope
    8. Exports Vector Contours
    """
    # 1. Point Cloud Audit
    profile = dg.lidar.profile_point_cloud(synthetic_las_file)
    assert profile.total_points == 5000

    # 2. DTM & DSM Generation
    dtm_tif = temp_workspace / "e2e_dtm.tif"
    dsm_tif = temp_workspace / "e2e_dsm.tif"
    chm_tif = temp_workspace / "e2e_chm.tif"

    dg.dem.create_dtm(synthetic_las_file, str(dtm_tif), resolution=0.5)
    dg.dem.create_dsm(synthetic_las_file, str(dsm_tif), resolution=0.5)
    dg.dem.create_chm(str(dsm_tif), str(dtm_tif), str(chm_tif), clamp_min=0.0)

    assert os.path.exists(str(dtm_tif))
    assert os.path.exists(str(dsm_tif))
    assert os.path.exists(str(chm_tif))

    # 3. Orthomosaic & Vegetation Index
    ortho_tif = temp_workspace / "e2e_ortho.tif"
    vari_tif = temp_workspace / "e2e_vari.tif"

    dg.imagery.create_true_color_orthomosaic(synthetic_las_file, str(ortho_tif), resolution=0.5)
    dg.imagery.compute_vari(str(ortho_tif), str(vari_tif))

    assert os.path.exists(str(ortho_tif))
    assert os.path.exists(str(vari_tif))

    # 4. Morphology: Hillshade & Slope
    hs_tif = temp_workspace / "e2e_hillshade.tif"
    slope_tif = temp_workspace / "e2e_slope.tif"

    dg.analysis.generate_hillshade(str(dtm_tif), str(hs_tif))
    dg.analysis.generate_slope_map(str(dtm_tif), str(slope_tif))

    assert os.path.exists(str(hs_tif))
    assert os.path.exists(str(slope_tif))

    # 5. Vector Contours
    contours_shp = temp_workspace / "e2e_contours.geojson"
    gdf = dg.analysis.generate_contour_lines(str(dtm_tif), str(contours_shp), interval_m=1.0)
    assert len(gdf) > 0
    assert os.path.exists(str(contours_shp))
