"""Independent geometry cases and actual raster/API smoke tests.
These do NOT validate NAIF ephemeris or certify landing safety.
"""
import math
from pathlib import Path
import numpy as np
import rasterio
from fastapi.testclient import TestClient
import main

client = TestClient(main.app)
SITE = Path(__file__).resolve().parents[1] / 'data/lola/site01'


def test_spherical_site_basis_and_cardinal_sun_directions():
    latitude, longitude = -89.463162834, -137.489552922
    east, north, up = main.local_basis(latitude, longitude)
    for vec, expected_az, expected_elevation in (
        (north, 0, 0), (east, 90, 0), (-north, 180, 0),
        (-east, 270, 0), (up, 0, 90), (-up, 0, -90),
        ((north + up) / math.sqrt(2), 0, 45),
    ):
        az, elevation = main.az_el(vec, latitude, longitude)
        if abs(expected_elevation) != 90:  # azimuth is undefined at the zenith/nadir
            assert math.isclose(az, expected_az, abs_tol=1e-7)
        assert math.isclose(elevation, expected_elevation, abs_tol=1e-7)


def test_site01_original_rasters_have_matching_georeferencing():
    names = ('surf', 'slp', 'ldec', 'toterr', 'slperr')
    rasters = [SITE / f'Site01_final_adj_5mpp_{n}.tif' for n in names]
    assert all(x.is_file() for x in rasters)
    with rasterio.open(rasters[0]) as dem:
        assert dem.width == dem.height == 3200
        assert math.isclose(abs(dem.transform.a), 5, abs_tol=1e-8)
        assert math.isclose(abs(dem.transform.e), 5, abs_tol=1e-8)
        transform, crs = dem.transform, dem.crs
    for path in rasters[1:]:
        with rasterio.open(path) as ds:
            assert ds.transform == transform
            assert ds.crs == crs
            assert ds.width == ds.height == 3200


def test_site01_point_and_grid_are_real_dataset_samples():
    lat, lon = -89.463162834, -137.489552922
    r = client.get('/lola/site01-point',params={'latitude':lat,'longitude':lon})
    assert r.status_code == 200, r.text
    payload = r.json()
    for key in ('elevation_m','slope_deg','elevation_uncertainty_m','slope_uncertainty_deg','lola_count'):
        assert payload[key] is not None and math.isfinite(payload[key])
    response = client.get('/lola/terrain-grid',params={'latitude':lat,'longitude':lon,'radius_m':1000,'size':17})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data['size'] == 17 and len(data['elevations_m']) == 17
    assert math.isfinite(data['elevations_m'][8][8])
    assert math.isclose(data['elevations_m'][8][8], payload['elevation_m'], abs_tol=0.02)


def test_spice_unavailable_returns_explicit_setup_error():
    status = client.get('/health').json()
    assert 'spice_missing' in status and 'spiceypy_installed' in status
    if not status['spiceypy_installed'] or status['spice_missing']:
        request={'latitude':-89.463162834,'longitude':-137.489552922,'date':'2026-11-14','time':'12:00'}
        result = client.post('/assess',json=request)
        assert result.status_code == 503
        assert 'SPICE' in result.text or 'SpiceyPy' in result.text
