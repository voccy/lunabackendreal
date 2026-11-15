"""LUNA scientific assessment API: LOLA terrain + NAIF SPICE geometry.
This is a screening tool, not a certified landing safety or RF link analysis.
"""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from pathlib import Path
from functools import lru_cache
import math, os, threading
import numpy as np
import rasterio
from rasterio.transform import rowcol
from pyproj import CRS, Transformer
try:
    import spiceypy as spice
except ImportError:  # Terrain-only API remains usable without SPICE dependencies.
    spice = None
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from science_enhancements import surface_diagnostics, finite_rows, screening_score, sampled_shadow_mask

ROOT = Path(__file__).resolve().parent
DATA = Path(os.getenv("LUNA_DATA_DIR", ROOT / "data"))
KERNEL_DIR = Path(os.getenv("LUNA_KERNEL_DIR", ROOT / "kernels"))
MOON_RADIUS_M = 1_737_400.0
FRAME = os.getenv("LUNA_MOON_FRAME", "MOON_ME")
app = FastAPI(title="LUNA Scientific API", version="1.0.0")
SPICE_LOCK = threading.RLock()  # CSPICE kernel-pool calls are serialized across concurrent API requests.

class AssessmentRequest(BaseModel):
    name: str = "Candidate site"
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    date: str
    time: str
    window_days: int = Field(default=3, ge=1, le=14)
    step_minutes: int = Field(default=10, ge=5, le=60)
    observer_height_m: float = Field(default=1.0, ge=0, le=20)
    max_slope_deg: float = Field(default=12, ge=0, le=45)
    min_sun_hours: float = Field(default=4, ge=0, le=336)
    min_earth_hours: float = Field(default=2, ge=0, le=336)
    solar_panel_area_m2: float = Field(default=1.0, gt=0, le=10000)
    solar_panel_efficiency: float = Field(default=0.25, gt=0, le=1)

@lru_cache(maxsize=1)
def load_kernels():
    if spice is None:
        raise RuntimeError("SpiceyPy is not installed. Install science_api/requirements.txt before SPICE assessments.")
    # This DE421 lunar geometry workflow requires the four kernels below.
    # The generic text planetary PCK is optional because the lunar frame uses
    # the provided DE421 binary lunar PCK + frame definition. Do not prevent
    # real SPICE geometry solely because pck00011.tpc is not installed.
    required = ["naif0012.tls", "de421.bsp", "moon_pa_de421_1900-2050.bpc", "moon_080317.tf"]
    missing = [n for n in required if not (KERNEL_DIR / n).exists()]
    if missing:
        raise RuntimeError("Missing SPICE kernels: " + ", ".join(missing) + ". Run scripts/download_science_data.py")
    with SPICE_LOCK:
        spice.kclear()
        for name in required: spice.furnsh(str(KERNEL_DIR / name))
        if (KERNEL_DIR / "pck00011.tpc").exists():
            spice.furnsh(str(KERNEL_DIR / "pck00011.tpc"))
    # The LOLA 5 m polar products use the DE421 Mean Earth frame.
    return {"kernels": required, "frame": FRAME, "ephemeris": "DE421 ephemeris + DE421 ME lunar orientation"}

def raster_pixel_spacing_m(ds, latitude_deg=0.0):
    """Estimate raster pixel spacing in metres for projected or geographic lunar grids."""
    dx, dy = abs(ds.transform.a), abs(ds.transform.e)
    if ds.crs and ds.crs.is_geographic:
        dy = math.radians(dy) * MOON_RADIUS_M
        dx = math.radians(dx) * MOON_RADIUS_M * max(0.0, math.cos(math.radians(latitude_deg)))
    return max(dx, dy)


def dem_paths():
    """Discover installed LOLA elevation products, preferring finest pixel spacing.

    Supports PGDA regional 5 m tiles, the 87S 5 m mosaic, and product-90
    multi-resolution South Pole COG/GeoTIFF products.
    """
    root = DATA / "lola"
    candidates = []
    if not root.exists():
        return {}
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() != ".tif":
            continue
        name = path.name.lower()
        is_regional = name.endswith("_surf.tif")
        is_mosaic = name == "ldem_87s_5mpp.tif"
        is_large_area = name.startswith("ldem_") and "_adj" in name and not any(
            token in name for token in ("_err", "_hill", "_effres"))
        is_global = name == "lunar_lro_lola_global_ldem_118m_mar2014.tif"
        if not (is_regional or is_mosaic or is_large_area or is_global):
            continue
        try:
            with rasterio.open(path) as ds:
                resolution = raster_pixel_spacing_m(ds, 0.0)
        except Exception:
            continue
        if is_regional:
            label = str(path.parent.relative_to(root)) + " regional 5 m"
        elif is_mosaic:
            label = "South Pole 87S mosaic 5 m"
        elif is_global:
            label = "Whole-Moon LOLA global DEM 118 m"
        else:
            label = path.stem.replace("_", " ")
        candidates.append((resolution, label, path))
    candidates.sort(key=lambda item: item[0])
    return {label: path for _, label, path in candidates}


def companion_paths(dem_path: Path):
    """Return available LOLA ancillary layers matched to the DEM's product family."""
    name = dem_path.name
    parent = dem_path.parent
    if name.endswith("_surf.tif"):
        stem = name[:-len("surf.tif")]
        return {
            "slope": parent / f"{stem}slp.tif",
            "uncertainty": parent / f"{stem}toterr.tif",
            "count": parent / f"{stem}ldec.tif",
            "slope_uncertainty": parent / f"{stem}slperr.tif",
        }
    if name.lower() == "ldem_87s_5mpp.tif":
        return {"slope": parent / "ldsm_87s_5mpp.tif",
                "count": parent / "ldec_87s_5mpp.tif"}
    if name.upper().startswith("LDEM_") and "_ADJ" in name.upper():
        stem = name.upper().replace("LDEM_", "", 1)
        return {
            "slope": parent / f"LDSM_{stem}",
            "uncertainty": parent / f"LDEM_{stem.replace('_ADJ.TIF', '_ADJ_ERR.TIF')}",
            "count": parent / f"LDEC_{stem}",
            "effective_resolution": parent / f"LDEM_{stem.replace('_ADJ.TIF', '_ADJ_EFFRES.TIF')}",
        }
    return {}


def open_dem(lat, lon):
    # Geographic coordinates are planetocentric, east-positive, on the LOLA reference sphere.
    geo = CRS.from_proj4(f"+proj=longlat +a={MOON_RADIUS_M} +b={MOON_RADIUS_M} +no_defs")
    for label, path in dem_paths().items():
        ds = rasterio.open(path)
        try:
            if ds.crs and ds.crs.is_geographic:
                x, y = lon, lat
            else:
                x, y = Transformer.from_crs(geo, ds.crs, always_xy=True).transform(lon, lat)
            r, c = rowcol(ds.transform, x, y)
            if 0 <= r < ds.height and 0 <= c < ds.width:
                return label, ds, x, y, int(r), int(c)
        except Exception:
            ds.close(); raise
        ds.close()
    raise HTTPException(422, "No downloaded LOLA elevation product covers this coordinate. Download an applicable regional tile or South Pole coverage product using scripts/download_science_data.py.")

def sample_band(path, row, col, reference=None):
    if not path.exists(): return None
    with rasterio.open(path) as ds:
        if reference is not None and (ds.crs != reference.crs or ds.transform != reference.transform or ds.width != reference.width or ds.height != reference.height):
            raise HTTPException(500, f"LOLA ancillary raster grid mismatch: {path.name}")
        v = ds.read(1, window=((row,row+1),(col,col+1)), masked=True)[0,0]
        return None if np.ma.is_masked(v) or not np.isfinite(v) else float(v)

def ingestion_manifest():
    path = DATA / "ingestion_manifest.json"
    if not path.exists(): return None
    try:
        import json
        return json.loads(path.read_text())
    except Exception: return None

def local_basis(lat_deg, lon_deg):
    lat, lon = math.radians(lat_deg), math.radians(lon_deg)
    up = np.array([math.cos(lat)*math.cos(lon), math.cos(lat)*math.sin(lon), math.sin(lat)])
    east = np.array([-math.sin(lon), math.cos(lon), 0.0])
    north = np.cross(up, east)
    return east, north, up

def az_el(vec, lat, lon):
    east, north, up = local_basis(lat, lon)
    e, n, u = float(np.dot(vec,east)), float(np.dot(vec,north)), float(np.dot(vec,up))
    return math.degrees(math.atan2(e,n)) % 360, math.degrees(math.atan2(u, math.hypot(e,n)))

# Keep site coordinates in the request scope for projection construction.
def terrain_horizon(ds, lat, lon, elev0, observer_h):
    geo = CRS.from_proj4(f"+proj=longlat +a={MOON_RADIUS_M} +b={MOON_RADIUS_M} +no_defs")
    local = CRS.from_proj4(f"+proj=aeqd +lat_0={lat} +lon_0={lon} +a={MOON_RADIUS_M} +b={MOON_RADIUS_M} +units=m +no_defs")
    if ds.crs and ds.crs.is_geographic:
        to_geo = Transformer.from_crs(local, geo, always_xy=True)
        transform_local = to_geo.transform
    else:
        to_dem = Transformer.from_crs(local, ds.crs, always_xy=True)
        transform_local = to_dem.transform
    azimuths = np.arange(0.0, 360.0, 5.0)
    distances = np.arange(20.0, 3_000.1, 20.0)  # 3 km: inside the 16-km Site01 footprint near its center
    out = np.full(azimuths.size, np.nan)
    coverage = np.zeros(azimuths.size)
    with rasterio.open(ds.name) as src:
        for i, az in enumerate(azimuths):
            a = math.radians(az)
            east = distances * math.sin(a)
            north = distances * math.cos(a)
            xx, yy = transform_local(east, north)
            coords = list(zip(xx, yy))
            masked = list(src.sample(coords, masked=True))
            vals = np.array([float(v[0]) if not np.ma.is_masked(v[0]) else np.nan for v in masked])
            valid = np.isfinite(vals) & (vals > -1e20)
            coverage[i] = float(valid.mean())
            if valid.any():
                surface_radius = MOON_RADIUS_M + elev0 + observer_h
                curvature_drop = surface_radius * (1.0 - np.cos(distances[valid] / surface_radius))
                relative_height = vals[valid] - (elev0 + observer_h) - curvature_drop
                elev = np.degrees(np.arctan2(relative_height, distances[valid]))
                out[i] = max(-90.0, float(np.max(elev)))
    if np.any(coverage < 0.8):
        raise HTTPException(422, "The selected point is too close to the edge of available LOLA coverage for a complete 3 km terrain horizon. Choose a point farther inside the selected LOLA DEM coverage or use a broader-resolution DEM.")
    return azimuths, out, coverage

def horizon_at(az, bins, profile):
    idx = int(round((az % 360.0) / 5.0)) % len(profile)
    return float(profile[idx])

def body_vector(target, et):
    # Apparent target position from Moon centre in the same DE421 ME body-fixed frame as LOLA.
    with SPICE_LOCK:
        pos, _ = spice.spkezr(target, et, FRAME, "LT+S", "MOON")
    return np.asarray(pos, dtype=float) * 1000.0

def geometry_at(dt, req, site_xyz):
    utc = dt.strftime("%Y-%m-%dT%H:%M:%S")
    with SPICE_LOCK:
        et = spice.str2et(utc + " UTC")
    lat, lon = req.latitude, req.longitude
    site = site_xyz
    sun_from_moon = body_vector("SUN", et)
    earth_from_moon = body_vector("EARTH", et)
    sun_vec = sun_from_moon - site
    earth_vec = earth_from_moon - site
    saz, selv = az_el(sun_vec, lat, lon)
    eaz, eelv = az_el(earth_vec, lat, lon)
    sun_range = float(np.linalg.norm(sun_from_moon))
    earth_range = float(np.linalg.norm(earth_from_moon))
    return {"datetime_utc": dt.isoformat().replace("+00:00","Z"), "sun_azimuth_deg": saz, "sun_elevation_deg": selv,
            "earth_azimuth_deg": eaz, "earth_elevation_deg": eelv,
            "sun_range_m":sun_range,"earth_range_m":earth_range,
            "sun_semidiameter_deg":math.degrees(math.asin(695700000.0/sun_range)),
            "earth_semidiameter_deg":math.degrees(math.asin(6378.1366e3/earth_range))}

def intervals(samples, key):
    out=[]; start=None; prev=None
    for s in samples:
        visible=s[key]
        t=datetime.fromisoformat(s["datetime_utc"].replace("Z","+00:00"))
        if visible and start is None: start=t
        if not visible and start is not None:
            out.append({"start_utc":start.isoformat().replace("+00:00","Z"),"end_utc":prev.isoformat().replace("+00:00","Z"),"duration_hours":round((prev-start).total_seconds()/3600,2)})
            start=None
        prev=t
    if start is not None and prev is not None:
        out.append({"start_utc":start.isoformat().replace("+00:00","Z"),"end_utc":None,"duration_hours":round((prev-start).total_seconds()/3600,2),"open_at_analysis_end":True})
    return out

def visibility_events(samples, key, rise_label, set_label):
    """Sample-resolution boundary events; not exact horizon-crossing roots.

    The instant reported is the timestamp of the first sample in the new
    state. The true crossing lies between adjacent samples.
    """
    events = []
    for previous, current in zip(samples, samples[1:]):
        before, after = bool(previous[key]), bool(current[key])
        if before != after:
            events.append({"type": rise_label if after else set_label,
                           "datetime_utc": current["datetime_utc"],
                           "bounded_by_utc": [previous["datetime_utc"], current["datetime_utc"]],
                           "accuracy": "sample-resolution crossing bound, not exact event time"})
    return events


@app.get("/health")
def health():
    missing=[n for n in ["naif0012.tls","de421.bsp","moon_pa_de421_1900-2050.bpc","moon_080317.tf"] if not (KERNEL_DIR/n).exists()]
    dems={k: p.exists() for k,p in dem_paths().items()}
    total_bytes=sum(p.stat().st_size for p in dem_paths().values() if p.exists())
    return {"status":"ready" if spice is not None and not missing and any(dems.values()) else "setup_required",
            "spiceypy_installed": spice is not None,"spice_missing":missing,"optional_text_pck_installed":(KERNEL_DIR/"pck00011.tpc").exists(),"spice_geometry_verified":False,"lola_dems":dems,"lola_dem_count":len(dems),
            "lola_bytes":total_bytes,"frame":FRAME}

@app.get("/lola/catalog")
def lola_catalog():
    """Return installed DEM coverage and available companion products."""
    products=[]
    for label, path in dem_paths().items():
        with rasterio.open(path) as ds:
            companions=companion_paths(path)
            products.append({"label":label,"file":str(path.relative_to(DATA)),
                "resolution_m":round(raster_pixel_spacing_m(ds, 0.0),3),
                "width":ds.width,"height":ds.height,"crs":str(ds.crs),
                "bounds":[ds.bounds.left,ds.bounds.bottom,ds.bounds.right,ds.bounds.top],
                "bytes":path.stat().st_size,
                "layers":{key: value.exists() for key,value in companions.items()}})
    return {"count":len(products),"products":products,
            "scope_note":"Installed PGDA derived products only; not a complete mirror of raw LOLA/PDS observations."}

@app.get("/lola/terrain-grid")
def lola_terrain_grid(latitude: float = Query(ge=-90, le=90),
                      longitude: float = Query(ge=-180, le=180),
                      radius_m: float = Query(default=5000, ge=250, le=20000),
                      size: int = Query(default=65, ge=16, le=129)):
    """Return a bounded, downsampled real LOLA height grid for local 3D rendering."""
    label, ds, _, _, _, _ = open_dem(latitude, longitude)
    try:
        geo = CRS.from_proj4(f"+proj=longlat +a={MOON_RADIUS_M} +b={MOON_RADIUS_M} +no_defs")
        local = CRS.from_proj4(
            f"+proj=aeqd +lat_0={latitude} +lon_0={longitude} "
            f"+a={MOON_RADIUS_M} +b={MOON_RADIUS_M} +units=m +no_defs")
        if ds.crs and ds.crs.is_geographic:
            to_geo = Transformer.from_crs(local, geo, always_xy=True)
            transform_local = to_geo.transform
        else:
            to_dem = Transformer.from_crs(local, ds.crs, always_xy=True)
            transform_local = to_dem.transform
        axis = np.linspace(-radius_m, radius_m, size)
        xx, yy = np.meshgrid(axis, axis)
        dx, dy = transform_local(xx.ravel(), yy.ravel())
        coords = list(zip(dx.tolist(), dy.tolist()))
        raw = np.fromiter((float(v[0]) for v in ds.sample(coords)), dtype=float, count=len(coords))
        nodata = ds.nodata
        valid = np.isfinite(raw)
        if nodata is not None:
            valid &= raw != nodata
        raw[~valid] = np.nan
        grid = raw.reshape((size, size))
        if int(np.isfinite(grid).sum()) < size * size * 0.5:
            raise HTTPException(422, "The selected LOLA product does not cover enough of this terrain window. Try a smaller terrain radius or another coordinate.")
        resolution = raster_pixel_spacing_m(ds, latitude)
        return {"dataset":label,"product":Path(ds.name).name,"resolution_m":round(resolution,3),
                "latitude":latitude,"longitude":longitude,"radius_m":radius_m,"size":size,
                "elevations_m":[[None if not np.isfinite(v) else round(float(v),2) for v in row] for row in grid],
                "note":"Actual sampled LOLA elevation grid. Grid is downsampled for interactive display; it is not a full-resolution engineering mesh."}
    finally:
        ds.close()


@app.get("/lola/site01-point")
def site01_point(latitude: float = Query(ge=-90, le=90), longitude: float = Query(ge=-180, le=180)):
    """Sample the actual uploaded Site01 GeoTIFF layers, independent of SPICE setup."""
    site = DATA / "lola" / "site01" / "Site01_final_adj_5mpp_surf.tif"
    if not site.exists():
        raise HTTPException(503, "Site01 GeoTIFF files are not installed")
    geo = CRS.from_proj4(f"+proj=longlat +a={MOON_RADIUS_M} +b={MOON_RADIUS_M} +no_defs")
    with rasterio.open(site) as dem:
        to_dem = Transformer.from_crs(geo, dem.crs, always_xy=True)
        x, y = to_dem.transform(longitude, latitude)
        row, col = rowcol(dem.transform, x, y)
        if not (0 <= row < dem.height and 0 <= col < dem.width):
            raise HTTPException(422, "Coordinates are outside the installed Site01 raster")
        companions = companion_paths(site)
        return {"dataset": "site01 regional 5 m", "latitude": latitude,
                "longitude": longitude, "pixel_size_m": round(raster_pixel_spacing_m(dem, latitude), 3),
                "elevation_m": sample_band(site, row, col, dem),
                "slope_deg": sample_band(companions["slope"], row, col, dem),
                "elevation_uncertainty_m": sample_band(companions["uncertainty"], row, col, dem),
                "slope_uncertainty_deg": sample_band(companions["slope_uncertainty"], row, col, dem),
                "lola_count": sample_band(companions["count"], row, col, dem)}

@app.post("/assess")
def assess(req: AssessmentRequest):
    try:
        kernels=load_kernels()
    except Exception as exc:
        raise HTTPException(503, str(exc))
    try:
        start=datetime.fromisoformat(f"{req.date}T{req.time}:00+00:00")
    except ValueError: raise HTTPException(400,"Use date YYYY-MM-DD and time HH:MM UTC.")
    label, ds, x, y, row, col = open_dem(req.latitude, req.longitude)
    try:
        # DEMs can differ in sampling resolution; never discard an otherwise
        # valid installed product just because it is not 5 m/pixel.
        elev=sample_band(Path(ds.name),row,col,ds)
        if elev is None: raise HTTPException(422,"No valid LOLA elevation at this coordinate.")
        ancillary=companion_paths(Path(ds.name))
        slope=sample_band(ancillary["slope"],row,col,ds) if ancillary.get("slope") else None
        zerr=sample_band(ancillary["uncertainty"],row,col,ds) if ancillary.get("uncertainty") else None
        count=sample_band(ancillary["count"],row,col,ds) if ancillary.get("count") else None
        slope_uncertainty=sample_band(ancillary["slope_uncertainty"],row,col,ds) if ancillary.get("slope_uncertainty") else None
        effective_resolution=sample_band(ancillary["effective_resolution"],row,col,ds) if ancillary.get("effective_resolution") else None
        bins, horizons, horizon_coverage=terrain_horizon(ds,req.latitude,req.longitude,elev,req.observer_height_m)
        product_resolution=raster_pixel_spacing_m(ds, req.latitude)
        product_name=Path(ds.name).name
    finally: ds.close()
    lat,lon=math.radians(req.latitude),math.radians(req.longitude)
    radius=MOON_RADIUS_M+elev+req.observer_height_m
    site_xyz=radius*np.array([math.cos(lat)*math.cos(lon),math.cos(lat)*math.sin(lon),math.sin(lat)])
    step=timedelta(minutes=req.step_minutes)
    samples=[]; n=int(req.window_days*24*60/req.step_minutes)+1
    for i in range(n):
        dt=start+i*step
        g=geometry_at(dt,req,site_xyz)
        sh=horizon_at(g["sun_azimuth_deg"],bins,horizons)
        eh=horizon_at(g["earth_azimuth_deg"],bins,horizons)
        sun_range=g["sun_range_m"]
        g.update({"terrain_horizon_sun_deg":sh,"terrain_horizon_earth_deg":eh,
                  "sun_visible":g["sun_elevation_deg"]+g["sun_semidiameter_deg"]>sh,
                  "earth_visible":g["earth_elevation_deg"]+g["earth_semidiameter_deg"]>eh})
        # Flat horizontal receiver plane; no panel pointing or RF link budget is assumed.
        g["horizontal_irradiance_w_m2"] = round(1361.0*(149597870700.0/sun_range)**2*max(0.0,math.sin(math.radians(max(0.0,g["sun_elevation_deg"])))) if g["sun_visible"] else 0.0,1)
        samples.append(g)
    sun_windows=intervals(samples,"sun_visible"); earth_windows=intervals(samples,"earth_visible")
    sun_hours=round(sum(x["duration_hours"] for x in sun_windows),2)
    earth_hours=round(sum(x["duration_hours"] for x in earth_windows),2)
    sun_events=visibility_events(samples,"sun_visible","sunrise","sunset")
    earth_events=visibility_events(samples,"earth_visible","earthrise","earthset")
    # Each sample except the final endpoint represents a fixed-duration time bin.
    # This discretization is explicit: no claim of exact rise/set event times.
    sun_hours=round(sum(bool(v["sun_visible"]) for v in samples[:-1])*req.step_minutes/60,2)
    earth_hours=round(sum(bool(v["earth_visible"]) for v in samples[:-1])*req.step_minutes/60,2)
    sun_percent=round(100.0*sum(bool(v["sun_visible"]) for v in samples[:-1])/max(len(samples)-1,1),2)
    earth_percent=round(100.0*sum(bool(v["earth_visible"]) for v in samples[:-1])/max(len(samples)-1,1),2)
    peak_irradiance=max((v["horizontal_irradiance_w_m2"] for v in samples),default=0.0)
    mean_irradiance=round(sum(v["horizontal_irradiance_w_m2"] for v in samples)/len(samples),1)
    # Flat upward-facing panel only. NO temperature, dust, charge-controller,
    # thermal, storage, degradation or shadow-subpixel losses are modeled.
    energy_wh_m2 = sum(v['horizontal_irradiance_w_m2'] for v in samples[:-1]) * req.step_minutes / 60
    panel_electric_wh = energy_wh_m2 * req.solar_panel_area_m2 * req.solar_panel_efficiency
    max_horizon=float(np.max(horizons)); mean_horizon=float(np.mean(horizons))
    terrain_ok=slope is not None and slope<=req.max_slope_deg
    sun_ok=sun_hours>=req.min_sun_hours
    earth_ok=earth_hours>=req.min_earth_hours
    criteria={"slope": {"value_deg":slope,"limit_deg":req.max_slope_deg,"status":"MEETS" if terrain_ok else "DOES_NOT_MEET" if slope is not None else "UNKNOWN"},
              "sunlight": {"visible_hours":sun_hours,"minimum_hours":req.min_sun_hours,"status":"MEETS" if sun_ok else "DOES_NOT_MEET"},
              "earth_line_of_sight": {"visible_hours":earth_hours,"minimum_hours":req.min_earth_hours,"status":"MEETS" if earth_ok else "DOES_NOT_MEET"}}
    status="MEETS_ALL_SCREENING_TARGETS" if all(v["status"]=="MEETS" for v in criteria.values()) else "ONE_OR_MORE_TARGETS_NOT_MET" if all(v["status"]!="UNKNOWN" for v in criteria.values()) else "INCOMPLETE_DATA"
    score=screening_score(slope,req.max_slope_deg,sun_hours,req.min_sun_hours,earth_hours,req.min_earth_hours,req.window_days*24)
    return {"screening_score":score,"name":req.name,"latitude":req.latitude,"longitude":req.longitude,"datetime_utc":start.isoformat().replace("+00:00","Z"),
      "solar_azimuth_deg":round(samples[0]["sun_azimuth_deg"],2),"solar_elevation_deg":round(samples[0]["sun_elevation_deg"],2),
      "earth_azimuth_deg":round(samples[0]["earth_azimuth_deg"],2),"earth_elevation_deg":round(samples[0]["earth_elevation_deg"],2),
      "sun_visible_demo":samples[0]["sun_visible"],"earth_visible_demo":samples[0]["earth_visible"],
      "calculation_mode":"NAIF SPICE LT+S + installed LOLA terrain horizon","scientific_status":"DATA-BACKED SCREENING. Geometry uses NAIF SPICE; visibility includes the sampled LOLA terrain horizon. Not a certified landing safety assessment or RF link budget.",
      "terrain":{"available":True,"dataset":label,"product":product_name,"resolution_m":round(product_resolution,3),"elevation_m":round(elev,2),"slope_deg":round(slope,2) if slope is not None else None,"slope_uncertainty_rms_deg":round(slope_uncertainty,2) if slope_uncertainty is not None else None,"height_uncertainty_rms_m":round(zerr,2) if zerr is not None else None,"effective_resolution_m":round(effective_resolution,2) if effective_resolution is not None else None,"lola_return_count":round(count,2) if count is not None else None,"horizon_max_deg":round(max_horizon,2),"horizon_mean_deg":round(mean_horizon,2),"horizon_profile":[[round(float(a),1),round(float(h),2)] for a,h in zip(bins,horizons)],"note":f"LOLA grid spacing is {product_resolution:.3f} m/pixel; this is not necessarily independent measurement resolution. Use supplied uncertainty, effective-resolution and return-count layers when available."},
      "sun_visible":samples[0]["sun_visible"],"earth_visible":samples[0]["earth_visible"],
      "sun_windows":sun_windows,"earth_windows":earth_windows,
      "sun_events":sun_events,"earth_events":earth_events,
      "sunrise_events_utc":[x["datetime_utc"] for x in sun_events if x["type"]=="sunrise"],
      "sunset_events_utc":[x["datetime_utc"] for x in sun_events if x["type"]=="sunset"],
      "earthrise_events_utc":[x["datetime_utc"] for x in earth_events if x["type"]=="earthrise"],
      "earthset_events_utc":[x["datetime_utc"] for x in earth_events if x["type"]=="earthset"],
      "sun_visible_percent_of_window":sun_percent,"earth_visible_percent_of_window":earth_percent,
      "visibility_temporal_resolution_minutes":req.step_minutes,
      "sunlight_hours":sun_hours,"earth_los_hours":earth_hours,"analysis_window_hours":req.window_days*24,
      "time_to_sunset_hours":next((round((datetime.fromisoformat(w["end_utc"].replace("Z","+00:00"))-start).total_seconds()/3600,2) for w in sun_windows if w.get("end_utc") and w["start_utc"]<=start.isoformat().replace("+00:00","Z")<=w["end_utc"]),None),
      "time_to_earthset_hours":next((round((datetime.fromisoformat(w["end_utc"].replace("Z","+00:00"))-start).total_seconds()/3600,2) for w in earth_windows if w.get("end_utc") and w["start_utc"]<=start.isoformat().replace("+00:00","Z")<=w["end_utc"]),None),
      "sun_visible_beyond_window":any(w.get("open_at_analysis_end") and w["start_utc"]<=start.isoformat().replace("+00:00","Z") for w in sun_windows),
      "earth_visible_beyond_window":any(w.get("open_at_analysis_end") and w["start_utc"]<=start.isoformat().replace("+00:00","Z") for w in earth_windows),
      "solar_energy_estimate":{"incident_irradiation_wh_m2":round(energy_wh_m2,1),
        "estimated_electric_wh":round(panel_electric_wh,1),
        "panel_area_m2":req.solar_panel_area_m2,"panel_efficiency":req.solar_panel_efficiency,
        "model":"Illustrative flat horizontal panel; no thermal, dust, pointing, wiring, storage or conversion losses; not an engineering power system estimate."},
      "peak_horizontal_irradiance_w_m2":round(peak_irradiance,1),"mean_horizontal_irradiance_w_m2":mean_irradiance,
      "communication":"Geometric direct-to-Earth line of sight only; RF link budget requires antenna, frequency, transmitter, receiver and relay assumptions.",
      "mission_assessment":{"status":status,"criteria":criteria,"interpretation":"Screening against the explicit default thresholds in the request. These are editable example targets, not universal lunar landing standards."},
      "time_series":samples,"timeline": [{"datetime_utc":v["datetime_utc"],"sun_visible":v["sun_visible"],"earth_visible":v["earth_visible"],"horizontal_irradiance_w_m2":v["horizontal_irradiance_w_m2"]} for v in samples],"data_provenance":{"terrain_source":"NASA GSFC PGDA LOLA derived topography products","terrain_product":product_name,"terrain_frame":"MOON_ME / DE421","ephemeris":"JPL DE421 SPK + NAIF lunar DE421 orientation kernels","spice_frame":FRAME,"time_scale":"UTC input converted to SPICE ET/TDB","observer_height_m":req.observer_height_m,"terrain_horizon":{"azimuth_step_deg":5,"radial_step_m":20,"maximum_range_km":3,"azimuth_bins_with_80pct_coverage":int(np.sum(horizon_coverage>=0.8)),"total_azimuth_bins":int(len(horizon_coverage))},"spice_kernels":kernels["kernels"],"ingestion_manifest":ingestion_manifest()}}


@app.get("/lola/terrain-analysis")
def lola_terrain_analysis(latitude: float = Query(ge=-90, le=90),
                          longitude: float = Query(ge=-180, le=180),
                          radius_m: float = Query(default=900, ge=250, le=3000),
                          size: int = Query(default=65, ge=17, le=129),
                          sun_azimuth_deg: float | None = Query(default=None, ge=0, le=360),
                          sun_elevation_deg: float | None = Query(default=None, ge=-90, le=90)):
    """Actual elevation data; derived finite-difference terrain diagnostics.

    Optional sunlight direction is caller-supplied, NOT inferred ephemeris.
    """
    grid = lola_terrain_grid(latitude, longitude, radius_m, size)
    spacing = 2*radius_m/(size-1)
    derived = surface_diagnostics(grid['elevations_m'], spacing)
    slope = derived['slope_deg']
    valid = slope[np.isfinite(slope)]
    payload = {"dataset":grid['dataset'],"product":grid['product'],"center": [latitude,longitude],
        "radius_m":radius_m,"size":size,"sample_spacing_m":spacing,
        "elevations_m":grid['elevations_m'],
        "slope_deg": finite_rows(slope,2),
        "curvature_proxy_per_m":finite_rows(derived['curvature_proxy_per_m'],7),
        "diagnostic_hillshade":finite_rows(derived['hillshade'],3),
        "slope_summary":{"valid_cell_count":int(valid.size),"mean_deg":round(float(valid.mean()),2) if valid.size else None,
          "max_deg":round(float(valid.max()),2) if valid.size else None},
        "limitations":"Slopes are derived from a downsampled grid (not the full native 5 m product). Curvature is a geometric proxy, not automated confirmed crater/ridge identification. Hillshade uses arbitrary 315° azimuth, 45° elevation for visualization."}
    if (sun_azimuth_deg is None) != (sun_elevation_deg is None):
        raise HTTPException(422,'Provide both solar azimuth and solar elevation, or neither.')
    if sun_azimuth_deg is not None:
        if size > 65:raise HTTPException(422,'Shadow grid size must be 65 or smaller to limit expensive ray tracing.')
        mask=sampled_shadow_mask(grid['elevations_m'], spacing,sun_azimuth_deg,sun_elevation_deg)
        cells=[value for row in mask for value in row if value is not None]
        payload['shadow_screening']={"solar_azimuth_deg":sun_azimuth_deg,
            "solar_elevation_deg":sun_elevation_deg,
            "shadow_mask":mask,"shadowed_fraction_of_evaluable_cells":round(sum(cells)/len(cells),4) if cells else None,
            "valid_cell_count":len(cells),"method":"Finite-grid approximate ray casting; not a validated full-resolution lunar shadow solution."}
    return payload

# Connect the website buttons to the existing Python science API.
app.add_api_route("/api/assess", assess, methods=["POST"])
app.add_api_route("/api/lola-terrain", lola_terrain_grid, methods=["GET"])
app.add_api_route("/api/site01-point", site01_point, methods=["GET"])
app.add_api_route("/api/lola-terrain-analysis", lola_terrain_analysis, methods=["GET"])
app.add_api_route("/api/lola-catalog", lola_catalog, methods=["GET"])


@app.post("/api/compare")
def api_compare(payload: dict):
    scenarios = payload.get("scenarios")
    if not isinstance(scenarios, list) or not 1 <= len(scenarios) <= 8:
        raise HTTPException(400, "Compare 1 to 8 scenarios.")
    results = []
    for scenario in scenarios:
        try:
            request = AssessmentRequest.model_validate(scenario)
        except ValueError as exc:
            raise HTTPException(422, str(exc))
        results.append(assess(request))
    return {"results": results}


@app.get("/api/data-status")
def api_data_status():
    h = health()
    return {
        "terrain": {
            "status": f"{h['lola_dem_count']} LOLA DEM products detected",
            "count": h["lola_dem_count"],
            "bytes": h["lola_bytes"]
        },
        "ephemeris": {
            "status": "Connected" if not h["spice_missing"] and h["spiceypy_installed"] else "Setup required"
        },
        "imagery": {"status": "Not configured"},
        "science_api": {"status": h["status"], "health": h},
        "cache": {"status": "Not configured"},
        "updater": {"message": "Cloudflare updater is not available on Back4app."}
    }


@app.post("/api/data-refresh")
def api_data_refresh():
    return {"message": "Automatic data refresh is not configured on Back4app."}

                              
from fastapi.staticfiles import StaticFiles

app.mount(
    "/",
    StaticFiles(directory=ROOT.parent / "public", html=True),
    name="frontend"
)
                              
