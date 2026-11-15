from pathlib import Path
import numpy as np
import rasterio
from rasterio.transform import from_origin

import main


def write_raster(path: Path, resolution: float = 5.0):
    path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(
        path, "w", driver="GTiff", width=8, height=8, count=1,
        dtype="float32", crs="EPSG:3857",
        transform=from_origin(0, 1000, resolution, resolution),
        nodata=-9999,
    ) as ds:
        ds.write(np.ones((8, 8), dtype="float32"), 1)


def test_regional_dem_discovery_and_companions(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "DATA", tmp_path)
    root = tmp_path / "lola" / "site04"
    dem = root / "Site04_final_adj_5mpp_surf.tif"
    write_raster(dem)
    for suffix in ("slp", "toterr", "ldec", "slperr"):
        write_raster(root / f"Site04_final_adj_5mpp_{suffix}.tif")

    products = main.dem_paths()
    assert len(products) == 1
    assert next(iter(products.values())) == dem
    companions = main.companion_paths(dem)
    assert all(path.exists() for path in companions.values())


def test_global_dem_is_discovered(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "DATA", tmp_path)
    dem = tmp_path / "lola" / "global" / "Lunar_LRO_LOLA_Global_LDEM_118m_Mar2014.tif"
    dem.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(dem, "w", driver="GTiff", width=8, height=8, count=1,
        dtype="float32", crs="EPSG:4326",
        transform=from_origin(-180, 90, 360/92160, 180/46080), nodata=-9999) as ds:
        ds.write(np.ones((8, 8), dtype="float32"), 1)
    products = main.dem_paths()
    assert "Whole-Moon LOLA global DEM 118 m" in products
    assert products["Whole-Moon LOLA global DEM 118 m"] == dem
    with rasterio.open(dem) as ds:
        assert 118 < main.raster_pixel_spacing_m(ds, 0) < 119


def test_finest_resolution_is_first(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "DATA", tmp_path)
    root = tmp_path / "lola"
    fine = root / "site04" / "Site04_final_adj_5mpp_surf.tif"
    coarse = root / "large_area" / "LDEM_80S_80MPP_ADJ.TIF"
    write_raster(fine, 5.0)
    write_raster(coarse, 80.0)
    values = list(main.dem_paths().values())
    assert values[0] == fine
