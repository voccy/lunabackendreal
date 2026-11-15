# Site01 integration — LUNA Cloudflare

This is **the original Cloudflare LUNA application**, extended with Site01 data from LunaSight. It is not a standalone Streamlit application.

## Windows setup — quick offline Site01 viewing

1. Unzip the package into a short folder path, e.g. `C:\LUNA_Cloudflare`.
2. Open Command Prompt in that folder.
3. With Python installed, run:

   ```bat
   py -m http.server 8080
   ```

4. Visit `http://localhost:8080/` in your browser.
5. Select **Site01 > Open Site01 in 3D**. The interactive viewer loads a **bundled 65 × 65 sampled snapshot of the actual uploaded elevation raster** and supports mouse drag and wheel zoom. Select **Inspect current coordinates** for the bundled *center-point* sample.

**Important:** Static mode only offers the *Site01 central coordinate* and its sampled terrain snapshot. It is not a substitute for the original raster or the full Python science service. Other coordinates, detailed raster layer sampling, illumination, and SPICE assessment need the backend.

## Full scientific raster API on Windows

Install Python 3.11–3.13 and Node.js (LTS). In the unzipped root folder:

```bat
py -m venv .venv
.venv\Scripts\activate
python -m pip install -r science_api\requirements.txt
python -m uvicorn science_api.main:app --host 127.0.0.1 --port 8000
```

In **another** Command Prompt opened in the same root folder:

```bat
npm install -D wrangler
copy .dev.vars.example .dev.vars
node scripts\build_pages.mjs
npx wrangler pages dev public
```

Open the URL Wrangler prints, then use Site01 from the main interface. `.dev.vars.example` should point `LUNA_SCIENCE_API_URL` to `http://127.0.0.1:8000`. With the backend connected, the Site01 3D grid is sampled live, and its five GeoTIFF layers can be inspected at arbitrary coordinates *within* their coverage.

`/health` can indicate `setup_required` until SPICE kernels are downloaded. **Terrain endpoints do not need SPICE kernels**, but `POST /assess` does. Consult the main README for official kernel download instructions and Docker options. The scientific API must run separately from Cloudflare Pages; don't upload the ~200 MB raster collection into Pages static assets.

## Cloudflare hosting

Deploy the existing Cloudflare static app and Pages Functions as described in README.md. **Use `node scripts/build_pages.mjs` as the build command and `public` as the output directory.** This is necessary to keep the large GeoTIFF files out of Cloudflare Pages static uploads. The compact `data/site01-preview-grid.json` and `data/site01-center-point.json` can be deployed with Pages to enable the Site01 **center** 3D demonstration even if `LUNA_SCIENCE_API_URL` is not configured. To inspect arbitrary Site01 points from all five original rasters, host `science_api/` on a Python-capable service with `science_api/data/lola/site01/` available and configure the Pages `LUNA_SCIENCE_API_URL` environment variable to that service's HTTPS origin. Cloudflare Pages alone cannot execute rasterio or SpiceyPy.

## Source raster files and meaning

The supplied source files were copied byte-for-byte (not resampled or changed) into `science_api/data/lola/site01/`:

- `Site01_final_adj_5mpp_surf.tif` — surface elevation (meters, LOLA reference sphere convention)
- `Site01_final_adj_5mpp_slp.tif` — slope (degrees)
- `Site01_final_adj_5mpp_ldec.tif` — LOLA measurement/return-count layer
- `Site01_final_adj_5mpp_toterr.tif` — elevation uncertainty layer (meters)
- `Site01_final_adj_5mpp_slperr.tif` — slope uncertainty layer (degrees)

Each raster is 3200 × 3200 float32 pixels, south-polar stereographic, 5 meters per pixel. The Site01 center selected by LUNA is derived from the elevation raster transform: approximately **lat −89.463162834°, lon −137.489552922°** (planetocentric, east-positive). It is **the raster center, not a certified landing coordinate**. The data comes from the uploaded files; its asserted NASA provenance has not been independently verified in this session. The sampled 3D view preserves raw elevation values in the JSON; the viewer applies **2.2× vertical exaggeration** only for visual display. Pixel spacing does not establish true independent LOLA measurement resolution.

The older LunaSight source was a separate Streamlit frontend. Its useful Site01 five-layer data and point inspection capability have been **integrated into the existing LUNA frontend + Python backend**, rather than shipping a disconnected Streamlit process. Existing Cloudflare planner, comparison, 2D map, 3D globe/terrain mode, assessment, source status, and Cloudflare Functions remain.

## New routes

- `GET /lola/site01-point?latitude=-89.463162834&longitude=-137.489552922` — returns the five raster values (Python FastAPI).
- `GET /api/site01-point?latitude=...&longitude=...` — Cloudflare Pages proxy to that Python endpoint.
- Existing `GET /lola/catalog` and `GET /lola/terrain-grid` automatically discover Site01 and return its sampled elevation mesh.

## Tests actually run (this build)

- Python syntax compilation: **passed**.
- JavaScript syntax: `node --check app.js` and all Pages Function files: **passed**.
- Byte-for-byte SHA-256 comparison of all five copies against uploaded files: **passed**.
- FastAPI TestClient `/lola/catalog`: **passed**, Site01 and all four companions discovered.
- FastAPI TestClient `/lola/site01-point` at raster center: **passed** (five numeric band values).
- FastAPI TestClient `/lola/site01-point` outside coverage: **passed** (HTTP 422).
- FastAPI TestClient `/lola/terrain-grid` at raster center (33 × 33): **passed**.
- These raster API tests used an **import-only dummy SpiceyPy module** because `spiceypy` is not installed in this runtime. **No SPICE ephemeris or full assessment is claimed tested.**

## Known limitations

- Network access to install SpiceyPy was unavailable (DNS/name resolution), so full Python runtime import with real SPICE and the existing scientific regression suite could not be verified here.
- Actual SPICE kernels are **not bundled**. Follow the existing README script to obtain them for a working `POST /assess`.
- No Cloudflare deployment was performed, and no live Pages browser test was possible here. The viewer UI was syntax-checked but not browser-automated.
- Cloudflare requires an external Python service for dynamic raster sampling; offline snapshot is limited to one exact coordinate and is deliberately labelled as such.
- Five raster files are large (~205 MB uncompressed total); static Pages deployment must exclude raw raster files (deploy code/static assets separately), while retaining rasters in the Python service.
- This is not a certified landing-site hazard analysis, and the scientific interpretation of the uploaded rasters was not externally audited.
