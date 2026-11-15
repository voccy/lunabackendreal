"""Reproducible Site01 raster diagnostics and transparent mission screening.
No inferred geological classification or uncertified mission safety ranking.
"""
from __future__ import annotations
import numpy as np


def surface_diagnostics(elevations_m, spacing_m):
    """Finite-difference slope, local Laplacian, and topographic hillshade.

    Spacing refers to the *sampled grid*, not the native LOLA pixel spacing.
    Missing samples stay missing. All arrays use row 0=north and east to right.
    """
    a = np.array([[np.nan if v is None else float(v) for v in row] for row in elevations_m], dtype=float)
    if a.ndim != 2 or min(a.shape) < 3 or not np.isfinite(spacing_m) or spacing_m <= 0:
        raise ValueError('A 3x3 or larger elevation grid and positive metric sample spacing are required')
    # Central differences only where all required neighbors are present.
    east = np.full_like(a, np.nan)
    north = np.full_like(a, np.nan)
    east[:, 1:-1] = (a[:, 2:] - a[:, :-2])/(2*spacing_m)
    north[1:-1, :] = (a[:-2, :] - a[2:, :])/(2*spacing_m)
    slope = np.degrees(np.arctan(np.hypot(east, north)))
    # 315 deg sun-from-north, elevation 45 deg for diagnostic hillshade ONLY.
    # This is not time-dependent SPICE illumination.
    az, altitude = np.deg2rad(315.), np.deg2rad(45.)
    nx, ny, nz = -east, -north, np.ones_like(a)
    norm = np.sqrt(nx*nx + ny*ny + nz*nz)
    sun_e, sun_n, sun_u = np.sin(az)*np.cos(altitude), np.cos(az)*np.cos(altitude), np.sin(altitude)
    hillshade = np.clip((nx*sun_e + ny*sun_n + nz*sun_u)/norm, 0, 1)
    lap = np.full_like(a, np.nan)
    lap[1:-1, 1:-1] = (a[:-2,1:-1] + a[2:,1:-1] + a[1:-1,:-2] + a[1:-1,2:] - 4*a[1:-1,1:-1]) / spacing_m**2
    return {'slope_deg':slope,'curvature_proxy_per_m':lap,'hillshade':hillshade}


def finite_rows(values, digits=3):
    return [[None if not np.isfinite(v) else round(float(v),digits) for v in row] for row in values]


def screening_score(slope_deg, slope_limit_deg, sunlight_hours, sun_target_hours,
                    earth_hours, earth_target_hours, analysis_hours):
    """Explicit illustrative weighted score (not a certified NASA safety metric).
    None when any required observation is unavailable. The score is not a
    lander safety determination, and must not outrank site hazard review.
    """
    vals=(slope_deg,slope_limit_deg,sunlight_hours,sun_target_hours,earth_hours,earth_target_hours,analysis_hours)
    if any(v is None or not np.isfinite(v) for v in vals) or slope_limit_deg<=0 or analysis_hours<=0:
        return None
    slope_score = max(0.,1. - max(0.,slope_deg)/slope_limit_deg)
    solar_score = min(1.,max(0.,sunlight_hours)/max(sun_target_hours,1e-6)) if sun_target_hours else 1.
    earth_score = min(1.,max(0.,earth_hours)/max(earth_target_hours,1e-6)) if earth_target_hours else 1.
    total=round(100*(.4*slope_score+.35*solar_score+.25*earth_score),1)
    return {'score_0_100':total,'components':{'slope':round(slope_score*100,1),
             'sunlight':round(solar_score*100,1),'earth_visibility':round(earth_score*100,1)},
            'weights':{'slope':0.4,'sunlight':0.35,'earth_visibility':0.25},
            'interpretation':'User-configurable exploratory screening only; not a probability of landing success.'}


def sampled_shadow_mask(elevations_m, spacing_m, solar_azimuth_deg, solar_elevation_deg):
    """Approximate finite-grid line-of-sight shadow screening.

    Discrete 2D rays, finite terrain coverage, no penumbra, no self-shading
    subpixel facets and no uncertainty propagation. Non-covered points remain
    unknown (None), and a low-altitude / below-horizon Sun is not automatically
    proof of a permanently shadowed region.
    """
    a = np.array([[np.nan if v is None else float(v) for v in row] for row in elevations_m], dtype=float)
    h,w=a.shape
    if not (-90 <= solar_elevation_deg <= 90) or spacing_m<=0:
        raise ValueError('Invalid solar elevation or spacing')
    if solar_elevation_deg <= 0:
        # An apparent negative solar elevation at the CENTER is not proof that
        # every elevated grid cell is shaded. Do not assert a shadow mask.
        return [[None for _ in row] for row in a]
    elev = np.deg2rad(solar_elevation_deg)
    az=np.deg2rad(solar_azimuth_deg)
    # Rays go toward Sun; 0deg=N, 90deg=E. Row increases southward.
    ux=np.sin(az); uy=-np.cos(az)
    result=[]
    for row in range(h):
        out=[]
        for col in range(w):
            base=a[row,col]
            if not np.isfinite(base):out.append(None);continue
            obscured=False; unknown=False
            max_steps=int(max(h,w)*1.4143)
            for step in range(1,max_steps):
                x=int(round(col+step*ux)); y=int(round(row+step*uy))
                if x<0 or y<0 or x>=w or y>=h:break
                height=a[y,x]
                if not np.isfinite(height):unknown=True;break
                if height>base+step*spacing_m*np.tan(elev):obscured=True;break
            out.append(None if unknown else obscured)
        result.append(out)
    return result
