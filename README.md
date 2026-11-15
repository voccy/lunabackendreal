# LUNA — Lunar Landing Site Navigator (Site01 integrated)

This package is rebuilt as a **Cloudflare Pages-compatible static site + Pages Functions API**. **Site01 is integrated with five actual uploaded GeoTIFF rasters.** See **[SITE01_INTEGRATION.md](SITE01_INTEGRATION.md)** for Windows setup, offline Site01 viewer, API, tests and caveats. It also includes an optional separate scheduled Worker for periodic source-manifest checks.

## 1. Preview locally

The front end works as a static preview without Python:

1. Extract this ZIP.
2. Open `index.html` in a browser.
3. The planner, schematic coordinate map, 3D globe illustration, demo assessment, and scenario comparison work locally.

The stylesheet and script use relative paths (`./style.css`, `./app.js`), so opening `index.html` directly will no longer break the styling.

For API-backed local testing, first start the science service (see Section 3), then use Wrangler Pages dev:
```bash
npm install -D wrangler
cp .dev.vars.example .dev.vars
node scripts/build_pages.mjs
npx wrangler pages dev public
```
The `.dev.vars` file points the Pages Function at `http://127.0.0.1:8000`. It is git-ignored. Opening `index.html` directly is still a static demo and will not call the Python science service.

## 2. Deploy to Cloudflare Pages

1. Push the extracted project to a GitHub repository.
2. In Cloudflare, create a Pages project and connect that repository.
3. Framework preset: **None**.
4. Build command: `node scripts/build_pages.mjs`.
5. Build output directory: `public`. Raw GeoTIFF rasters live only in the Python science service; do **not** deploy them as Pages assets.
6. Deploy.

Pages Functions in `/functions/api/` provide:
- `GET /api/locations`
- `POST /api/assess` (proxies to the Python science service)
- `POST /api/compare`
- `GET /api/data-status`
- `POST /api/data-refresh`

The browser preview falls back to clearly labelled illustrative demo values if the science API is unavailable. It does not silently present those values as NASA calculations.

## 3. LOLA science data + SPICE service

The Python science API uses actual NASA/USGS LOLA elevation rasters and NAIF SPICE kernels. It discovers installed elevation products at startup/request time and selects the finest-resolution DEM covering the requested coordinate.

### Download profiles

Run these commands from the project root:

```bash
# Small development pack: Site04 + Site23 5 m products and SPICE kernels
python scripts/download_science_data.py --profile starter

# Whole-Moon baseline DEM (about 8 GB)
python scripts/download_science_data.py --profile global

# All listed South Pole 5 m regional sites + 87S 5 m mosaic
python scripts/download_science_data.py --profile south-pole-5m

# Catalogue every downloadable asset linked by PGDA products 78, 81 and 90
# without downloading anything:
python scripts/download_science_data.py --profile all --catalogue-only

# Review the full download plan:
python scripts/download_science_data.py --profile all --dry-run

# Download all linked PGDA assets plus the whole-Moon 118 m global LOLA DEM.
# This can require hundreds of GB; only run after reviewing the catalogue/plan.
python scripts/download_science_data.py --profile all --yes
```

Profiles:

- `starter`: Site04 and Site23 5 m/pixel regional layers (elevation, slope, height uncertainty, LOLA return count, slope uncertainty) plus NAIF kernels.
- `global`: the USGS-hosted whole-Moon LOLA 118.45 m/pixel GeoTIFF (approximately 8 GB). This gives broad global elevation coverage, not high-resolution landing-site terrain.
- `south-pole-5m`: the 27 regional sites listed by NASA PGDA product 78 and the 87S 5 m mosaic. This downloads the core terrain layers, not every clone/point-cloud/ROI asset.
- `all`: dynamically scrapes every downloadable asset linked from NASA PGDA products 78, 81 and 90 (including published regional clones, XYZI point clouds, ROI assets, large-area DEM/roughness/PSR products) and adds the whole-Moon 118 m global DEM. It is intentionally opt-in because the total volume is very large.

The `all` profile is all assets linked by those selected PGDA products, **not a mirror of every raw LOLA EDR/RDR/GDR observation in the PDS mission archive**. The PDS archive contains additional raw and gridded products and needs a separate PDS-aware ingestion catalogue. The downloader records the URL, local path, byte count and SHA-256 for each successfully downloaded file. Downloads are resumable: existing non-empty files are retained and hashed.

### Start locally with Docker

```bash
docker compose -f docker-compose.science.yml up --build
```

The Docker image no longer assumes that only Site04 and Site23 exist. It downloads the `starter` pack on first start if files are absent, and the API discovers other installed DEMs under `science_api/data/lola/`. For a large profile, run the downloader on a machine with adequate disk space before starting the service. Persist `science_api/data/` and `science_api/kernels/` as volumes.

API endpoints:
- `GET http://localhost:8000/health` — installed DEMs, total DEM bytes, missing kernels.
- `GET http://localhost:8000/lola/catalog` — installed DEM metadata, bounds, resolution and companion layers.
- `GET http://localhost:8000/lola/terrain-grid?latitude=...&longitude=...` — downsampled LOLA elevation grid for the interactive local 3D terrain mesh.
- `GET /api/lola-catalog` and `GET /api/lola-terrain?...` — Cloudflare Pages proxies to the science service.
- `POST http://localhost:8000/assess` — data-backed site assessment.

### Automated checks

Install development dependencies and run the current regression checks:

```bash
python -m pip install -r science_api/requirements-dev.txt
cd science_api
pytest -q tests
```

The included tests cover LOLA DEM discovery, regional companion-layer matching, resolution ordering, global DEM registration, local coordinate-basis orthogonality and visibility-interval duration arithmetic. They are software regression tests, not an independent validation of SPICE ephemerides or published lunar illumination results.

### Coverage and resolution behaviour

The API scans installed GeoTIFFs and prefers the finest pixel spacing that covers the requested point. Supported families include the regional `*_surf.tif` products, the `ldem_87s_5mpp.tif` South Pole mosaic, PGDA product-90 `LDEM_*_ADJ.TIF` products, and the whole-Moon USGS global 118 m LOLA DEM. Companion slope, uncertainty, effective-resolution and count layers are sampled only when present and grid-aligned. If a layer is unavailable, the API returns `null` rather than inventing a value.

The 5 m grid spacing is not the same as independent measurement resolution: NASA notes that many pixels in the regional polar DEMs are interpolated between LOLA tracks. Use the return-count, uncertainty and effective-resolution products when available. A global 118 m DEM is appropriate for global context and coarse terrain screening, not precision landing-site assessment.

The terrain horizon is currently a sampled screening profile (5-degree azimuth bins, 20 m radial samples, up to 3 km). It is not a full-resolution ray-traced mesh. The global 118 m raster is therefore oversampled by this horizon routine; treat its horizon as coarse and use high-resolution local products for detailed assessment.

### SPICE kernels

The LOLA regional products use the `MOON_ME` frame associated with DE421. The downloader obtains the LSK, DE421 SPK, lunar orientation binary PCK, lunar frame kernel and text PCK from NAIF. The exact kernel set is recorded in the science API provenance. Do not silently mix a DEM tied to one lunar frame with kernels defining another frame. NAIF documents that lunar ME/PA frame definitions are ephemeris-specific; the current DE421 setup is retained to match the PGDA regional LOLA products.

### Cloud-hosted science service

The geospatial science API is separate from Cloudflare Pages because large rasters and repeated terrain sampling are not suitable for a Pages Function runtime. Deploy the Python service to a container host with persistent storage, then set `LUNA_SCIENCE_API_URL` in Pages to its HTTPS URL. Use object storage/CDN (for example, Cloudflare R2) for distribution of large static DEMs if you later move beyond a persistent science-service volume.

## 4. Enable Cloudflare KV cache

1. Create a KV namespace in Cloudflare.
2. Bind it to your Pages project as `LUNA_CACHE` in the dashboard (Settings → Functions → KV namespace bindings). The default `wrangler.toml` intentionally has no fake KV ID.
4. Redeploy.

The KV binding is used by the optional source-manifest updater in this package. The current science assessment proxy does not cache time-series results; add a deliberately versioned cache only after the dataset/kernel version is included in the cache key.

## 5. Automatic source-manifest checks

A source manifest is a JSON file you control. Example:
```json
{
  "products": [
    {
      "name": "Example dataset",
      "source": "official source landing page",
      "version": "your version label",
      "download_url": "official downloadable product URL",
      "checksum": "SHA-256 checksum"
    }
  ]
}
```

Set `LUNA_MANIFEST_URL` in Cloudflare environment variables. The Pages `Check source manifest` button checks the manifest on demand.

For a scheduled daily check, deploy the optional Worker in `worker/` as a separate Worker, bind the same KV namespace, set `LUNA_MANIFEST_URL`, and enable its cron trigger. Cloudflare Pages Functions do not themselves run scheduled cron events; that is why the scheduled Worker is separate.

**Important:** the updater currently checks manifest metadata only. It does not download NASA products, validate checksums, reproject data, or replace datasets. Those steps need a product-specific ingestion and validation pipeline.

## 6. What is implemented vs. what still needs scientific integration

### Implemented in this prototype
- Historical reference entries: Apollo 11, Apollo 17, Luna 16, Chang'e 4.
- Candidate regions: Shackleton Crater region and Malapert Massif region.
- Custom latitude/longitude input and click-to-place coordinate map.
- Date and UTC time selection.
- Schematic 2D coordinate map and an interactive local 3D terrain mesh when an actual LOLA DEM is installed and the science API is connected; otherwise the 3D panel remains explicitly schematic.
- Assessment panel and side-by-side comparison of up to 8 scenarios.
- Cloudflare Pages Functions API and optional KV response cache.
- Optional scheduled source-manifest metadata check.

### Implemented in the South Pole science service
- Resumable LOLA ingestion profiles, SHA-256 manifest records, multi-product DEM discovery, and companion-layer sampling where available.
- NAIF SPICE apparent Sun/Earth geometry using the LOLA-compatible lunar Mean Earth frame.
- DEM-derived local horizon obstruction, Sun/Earth geometric visibility windows, and a downsampled 3D terrain grid endpoint.
- Time-series sampling and explicit, editable mission screening criteria.
- Data provenance in each science assessment.

### Still not implemented / not validated
- Full PDS raw LOLA mission archive mirroring and complete tiled 512/1024 px-per-degree GDR coverage.
- Independent numerical validation against JPL Horizons and published illumination studies.
- Image-derived boulder-scale terrain, global textured 3D globe and full-resolution mesh ray tracing.
- Actual solar-array/battery energy and thermal model.
- RF communication link budget and antenna/relay model.
- Operational landing safety certification or autonomous navigation.

If the Python science service is not running or the selected coordinate is outside the loaded LOLA tiles, the browser uses explicitly labelled illustrative demo values instead.

## 7. Data updates and validation still required

LOLA is an archived terrain/topography dataset, not a live sensor feed. The new local downloader records source URLs, retrieval time, byte counts and SHA-256 hashes, but the scheduled Cloudflare manifest Worker still checks metadata only. It does not automatically download, validate and activate new NASA datasets.

Before calling a new data release validated, the ingestion process still needs to check file format, coordinate reference system, units, coverage, no-data values and product-specific quality layers. Keep the previous validated dataset active until a new product passes those checks. Record product ID, version, retrieval time, checksum and processing steps.

The science API's terrain calculations now use installed raster products and available companion layers, but the solar/Earth geometry and illumination windows have not yet been independently benchmarked against JPL Horizons and published reference cases. Do not describe the current outputs as scientifically validated until that regression suite is complete.

## 8. Cloudflare services: what belongs where

- **Pages**: website files and Pages Functions API.
- **Workers**: scheduled updater or heavier server-side tasks.
- **KV**: optional manifest metadata storage; science time-series responses are not cached by default.
- **D1**: optional relational catalogue, user projects, scenario history, and audit log. Not required for this prototype.
- **R2**: optional storage for large DEM tiles, imagery, and downloaded data products. Not required until real datasets are integrated.

They can live in one GitHub repository, but Pages, the scheduled Worker, and their bindings are configured/deployed as separate Cloudflare resources.

## 9. Fair comparison with NASA Moon Trek / QuickMap

Do not claim LUNA has features those platforms lack without testing and documenting it. The proposed differentiator is a guided mission-replanning workflow: save multiple site/date alternatives, compare the outputs in one view, and explain the effect of schedule or location changes. Build a benchmark table against the current versions of the NASA tools before making competition claims.


## November 2026 uploaded-kernel and checklist update

The four user-uploaded DE421 SPICE kernels are now bundled at `science_api/kernels/` under canonical filenames. The optional `pck00011.tpc` file was **not uploaded**. It is not required for the app's explicitly named `MOON_ME` DE421 Sun/Earth geometry calls; some other planetary SPICE workflows may require the text PCK. Download it with `py scripts\download_spice_kernels.py` when desired.

**Important:** The presence of kernels does not imply that the numerical SPICE backend was executed in this packaging environment. Run `py -m pip install -r science_api\requirements.txt`, then `py scripts\verify_spice.py` on Windows to check actual kernel loading, 2026 Sun/Earth vectors and the 2008 NAIF reference example.

`CHECKLIST_AUDITED_2026_11_14.md` gives a line-by-line status against your website's technical development checklist. The backend now also exposes **sample-resolution** sunrise, sunset, Earthrise and Earthset transition brackets, visible-fraction percentages and stated temporal resolution; those are not exact independently validated crossing times.

The original Cloudflare Ready homepage CSS and design remain untouched. The five Site01 LOLA GeoTIFFs are unchanged. Neither the Python service nor the Cloudflare Pages site is deployed by this bundle.


## 14 November 2026 — Additional science enhancements

- `/lola/terrain-analysis` returns real installed-DEM samples, derived finite-difference slopes, curvature proxies, and **diagnostic** hillshade. An optional caller-supplied solar direction produces a small-grid approximate terrain shadow mask. The response explicitly describes limitations.
- The homepage retains the original `style.css` exactly. A new section below Site01 offers 2D grayscale relief derived from original Site01 elevation raster, derived slope visualizations, optional approximate shadows after a **real** science assessment, and time-series timeline. The static relief is *not LROC imagery*.
- Data-backed assessments report a transparent illustrative screening score and optional electrical yield from a flat horizontal solar panel; these are assumption-based screening indicators, not engineering mission safety results.
- Saved scenarios persist locally in browser `localStorage`; this is not server backup or synchronized storage. Assessments export as JSON.
- The terrain horizon now samples **3 km**, rather than 10 km, since a 10 km ray exceeds local coverage near the center of the 16 km Site01 tile. It still returns an explicit error when coverage falls short; 3 km cannot establish the true distant lunar skyline.
- Recreate offline relief if desired: `py -m pip install pillow` then `py scripts/build_site01_relief.py` and `node scripts/build_pages.mjs`.
- Test the science API: `cd science_api` then `py -m pytest -q` with `requirements-dev.txt` installed. Run `py scripts/verify_spice.py` from project root for a real kernel/NAIF numeric regression check; this was **not executable here** without SpiceyPy.
- Cloudflare Pages still requires a separately hosted HTTPS FastAPI service and environment variable `LUNA_SCIENCE_API_URL`. Runtime hosting and live deployment are not included. Configured Pages/Workers functions cannot directly run Python.
- See `FULL_PASS_CHECKLIST_2026_11_14.md` for the verified status inventory and blockers.
