# LUNA Site01: verified features, setup and limits (2026-11-14)

## Actual NASA Site01 LOLA-derived rasters

The ZIP includes all five uploaded originals, unmodified, as `science_api/data/lola/site01/Site01_final_adj_5mpp_{surf,slp,ldec,toterr,slperr}.tif` (~195 MiB total uncompressed). Their exact filenames are listed on NASA GSFC PGDA product 78: https://pgda.gsfc.nasa.gov/products/78 . This establishes an authoritative product-name match, **not a byte-for-byte integrity comparison against NASA's online copies**. The raster values were not synthesized. See `DATA_CHECKSUMS_SHA256.txt` for hashes of the files actually shipped.

`surf` = elevation; `slp` = surface slope; `ldec` = return/density count layer; `toterr` = total vertical uncertainty; `slperr` = slope uncertainty. GeoTIFF pixel spacing is 5 m and must not be confused with independent measurement resolution.

## Actual 3D terrain

An integrated native WebGL triangular surface renderer (`terrain-webgl.js`) uses the same Site01 DEM height samples returned by `/lola/terrain-grid` or bundled Site01 preview. Drag to orbit and use the mouse wheel to zoom. The added **Vertical scale** control defaults to **1× true vertical scale**; 2.2× is a visibly labeled optional exaggeration. If WebGL is unavailable, the existing software 3D canvas renderer remains as fallback and uses 2.2× vertical exaggeration. No heights are fabricated, but the **preview and live terrain mesh are downsampled** for browser performance; they are not full 5 m engineering models. Camera/WebGL rendering has not been browser-tested in this environment (Chromium navigation is blocked by administrator policy).

## SPICE kernels: NOT bundled

The science engine contains real NAIF SPICE call paths but **no SPICE kernel files could be downloaded** because this execution environment cannot resolve external hostnames. SpiceyPy also could not be installed from offline package sources. Run this in a network-connected Windows terminal from the project root:

```bat
py -m pip install -r science_api\requirements.txt
py scripts\download_spice_kernels.py
```

Official kernel source URLs (recorded and downloaded only on your machine):

- https://naif.jpl.nasa.gov/pub/naif/generic_kernels/lsk/naif0012.tls
- https://naif.jpl.nasa.gov/pub/naif/JUNO/kernels/spk/de421.bsp
- https://naif.jpl.nasa.gov/pub/naif/generic_kernels/pck/moon_pa_de421_1900-2050.bpc
- https://naif.jpl.nasa.gov/pub/naif/generic_kernels/fk/satellites/moon_080317.tf
- https://naif.jpl.nasa.gov/pub/naif/generic_kernels/pck/pck00011.tpc

The download helper saves SHA-256 hashes of installed files. Check `/health` for missing kernel names and whether SpiceyPy is installed. A complete SPICE validation still requires evaluating at known reference epochs and comparing against independently authoritative ephemeris values.

## Windows run

Open a Command Prompt in the unzipped `LUNA_Cloudflare` project:

```bat
py -m venv .venv
.venv\Scripts\activate
python -m pip install -r science_api\requirements.txt
py scripts\download_spice_kernels.py
python -m uvicorn science_api.main:app --host 127.0.0.1 --port 8000
```

In a second Command Prompt, still in `LUNA_Cloudflare`:

```bat
copy .dev.vars.example .dev.vars
npm install -D wrangler
node scripts\build_pages.mjs
npx wrangler pages dev public
```

Open the local Pages URL from Wrangler. For static preview without a backend use `py -m http.server 8080 -d public` (offline Site01 center only).

## Cloudflare production setup

- Build: `node scripts/build_pages.mjs`; output: `public`. The build excludes the five large rasters.
- Deploy to a new Cloudflare Pages project, connecting your own repository or running `npx wrangler pages deploy public --project-name luna-lunar-navigator` after authentication. **No deployment credentials or Cloudflare account were accessible here, and no deployment was attempted.**
- Deploy `science_api/` separately to a Python/Docker-capable HTTPS host, with the original Site01 GeoTIFFs mounted on persistent storage and installed SPICE kernels.
- Configure Pages `LUNA_SCIENCE_API_URL` = the Python service's HTTPS origin; set `LUNA_MANIFEST_URL` only if using the optional manifest checker.
- If you want metadata caching, create and bind a KV namespace as `LUNA_CACHE` in Pages settings. It is optional; this package no longer ships an invalid placeholder namespace ID.
- Verify live `GET /api/data-status`, `GET /api/site01-point?...`, `GET /api/lola-terrain?...`, and `POST /api/assess`, alongside authentication, browser behavior and CORS. No production endpoints were tested here.

## Test results actually observed

- Python tests: **9 passed**, including independent ENU/azimuth/elevation vector cases, five-raster coordinate/transform checks, actual Site01 point and DEM grid sampling, missing-SPICE error behavior, product discovery and interval calculations.
- Python compileall: passed.
- JavaScript syntax: `node --check` on application, WebGL module and Cloudflare Pages Functions: passed.
- Cloudflare Pages static build (`node scripts/build_pages.mjs`): passed.
- Browser/WebGL smoke test: **BLOCKED** — Chromium returned `net::ERR_BLOCKED_BY_ADMINISTRATOR` for localhost and file URLs.
- NASA/NAIF downloading: **BLOCKED** — network host resolution failed. No SPICE kernels bundled.
- Real SPICE numerical validation: **NOT RUN**, needs SpiceyPy + genuine kernel files.
- Cloudflare production deployment: **NOT RUN**, needs account access, service URL and live verification.

This package is a science-backed research prototype, not an operational landing-safety assessment. SPICE illuminations, DEM horizon sampling and slope screening require independent mission-grade verification before real mission use.
