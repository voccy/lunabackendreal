import numpy as np
from science_enhancements import surface_diagnostics, sampled_shadow_mask, screening_score
from fastapi.testclient import TestClient
import main


def test_flat_surface_has_zero_slope_and_no_curvature():
    a=[[100.]*9 for _ in range(9)]
    d=surface_diagnostics(a,5)
    assert abs(d['slope_deg'][4,4])<1e-8
    assert abs(d['curvature_proxy_per_m'][4,4])<1e-8
    assert np.isfinite(d['hillshade'][4,4])


def test_known_plane_slope_and_data_gaps():
    a=[[10+2*i for i in range(9)] for j in range(9)]
    d=surface_diagnostics(a,2)
    assert abs(d['slope_deg'][4,4]-45)<1e-8
    a[4][3]=None
    d=surface_diagnostics(a,2)
    assert np.isnan(d['slope_deg'][4,4])


def test_shadow_direction_and_no_fabricated_missing_pixels():
    a=[[0.]*7 for _ in range(7)]
    a[3][4]=200  # ridge immediately east of center
    mask=sampled_shadow_mask(a,5,90,10)
    assert mask[3][3] is True
    assert mask[3][5] is False
    assert sampled_shadow_mask(a,5,90,-1)[3][3] is None
    a[3][4]=None
    assert sampled_shadow_mask(a,5,90,10)[3][3] is None


def test_transparent_scoring_not_certified():
    d=screening_score(0,12,4,4,2,2,72)
    assert d['score_0_100']==100
    assert 'not' in d['interpretation'].lower()
    assert screening_score(None,12,4,4,2,2,72) is None
    assert screening_score(12,12,0,4,0,2,72)['score_0_100']==0


def test_real_site01_analysis_endpoint():
    client=TestClient(main.app)
    params={'latitude':-89.463162834,'longitude':-137.489552922,'size':33,'radius_m':900}
    r=client.get('/lola/terrain-analysis',params=params)
    assert r.status_code==200,r.text
    d=r.json()
    assert d['size']==33 and d['slope_summary']['valid_cell_count']>400
    assert d['sample_spacing_m']==56.25
    assert d['product']=='Site01_final_adj_5mpp_surf.tif'
    assert any(v is not None for row in d['elevations_m'] for v in row)
    r=client.get('/lola/terrain-analysis',params={**params,'sun_azimuth_deg':90,'sun_elevation_deg':5})
    assert r.status_code==200,r.text
    assert len(r.json()['shadow_screening']['shadow_mask'])==33
    assert client.get('/lola/terrain-analysis',params={**params,'sun_azimuth_deg':90}).status_code==422
