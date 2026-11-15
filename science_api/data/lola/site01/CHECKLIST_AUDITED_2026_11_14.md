# LUNA — Audited Technical Checklist (14 November 2026)

**Audit basis:** actual merged ZIP source, uploaded files, automated tests. This replaces *status labels*, not the original scope. “Implemented” means present in code, not validated science or Cloudflare deployment.

**Critical:** Four genuine-format kernels were added. `pck00011.tpc` was not supplied; it is optional for the current DE421/MOON_ME geometry. SpiceyPy is unavailable in this environment, so SPICE numerical execution remains unverified.

**LUNA — Technical Development Checklist**
*Lunar Landing Site Navigator | Prototype status inventory | 14 November 2026*
**Status key:&#x20;**&#x49;mplemented = present in the prototype; Partially implemented = interface/framework exists but needs completion or validation; Missing / not integrated = not currently implemented as a working capability; Planned = discussed but not verified as built.
| Component / task | Audited status | Evidence / limitation |
| --- | --- | --- |
| NASA LOLA (Lunar Orbiter Laser Altimeter) | Implemented for Site01 | Five actual user-supplied LOLA-derived Site01 GeoTIFF layers are bundled |
| LOLA Digital Elevation Model (DEM) | Implemented for Site01 | 5 m grid, not necessarily 5 m measurement accuracy |
| JPL SPICE kernels | Partially implemented | Four required DE421 kernel files bundled; optional pck00011.tpc missing; runtime unverified |
| JPL ephemeris data | Partially implemented | DE421 SPK bundled; SpiceyPy execution not yet checked |
| NASA JPL Horizons | Missing  / not integrated (not revalidated) | No verified change in this integration |
| LROC imagery | Missing  / not integrated (not revalidated) | No verified change in this integration |
| NASA PDS data | Planned (not revalidated) | No verified change in this integration |
| Historical landing-site coordinates | Implemented (not revalidated) | No verified change in this integration |
| Predefined south-pole locations | Implemented (not revalidated) | No verified change in this integration |
| Custom coordinates | Implemented (not revalidated) | No verified change in this integration |
| Component / task | Audited status | Evidence / limitation |
| --- | --- | --- |
| Lunar elevation data processing | Implemented for Site01 | GeoTIFF discovery, projection, point/grid sampling |
| LOLA DEM integration | Implemented for Site01 | Raster-backed API and preview grid |
| Terrain slope calculations | Partially implemented | Samples precomputed LOLA slope raster; no independent DEM slope validation |
| Crater identification | Missing (not revalidated) | No verified change in this integration |
| Mountain/ridge identification | Missing (not revalidated) | No verified change in this integration |
| Local terrain horizon calculations | Implemented, screening only | 10 km sampled horizon at 5 degree azimuth increments; coverage-dependent |
| Terrain obstruction detection | Partially implemented | Horizon compared with Sun/Earth angles; only within sampled 10 km |
| Landing-site elevation information | Implemented for Site01 | Actual raster sampling within DEM coverage |
| Realistic 3D terrain rendering | Partially implemented | WebGL terrain mesh from real elevation samples; browser GPU test outstanding |
| Component / task | Audited status | Evidence / limitation |
| --- | --- | --- |
| Sun position dashboard | Partially  implemented / placeholder (not revalidated) | No verified change in this integration |
| Sun azimuth calculations | Implemented, unvalidated | SPICE geometry code present; execution needs SpiceyPy |
| Sun elevation calculations | Implemented, unvalidated | SPICE geometry code present; execution needs SpiceyPy |
| Sunrise calculations | Partially implemented | Sample-bounded visibility transition event available from science API; true event time not independently validated |
| Sunset calculations | Partially implemented | Sample-bounded visibility transition event available from science API; true event time not independently validated |
| Sunlight duration | Partially implemented | Sampled visibility windows in backend; SPICE runtime unverified |
| Illumination percentage | Partially implemented | Fraction of selected analysis window with visible Sun, using sampled terrain horizon; not permanent illumination probability |
| Permanently shadowed region detection | Missing (not revalidated) | No verified change in this integration |
| Terrain-based shadow calculations | Partially implemented | Horizon occultation at sampled azimuths, not full shadow maps |
| Solar power potential estimation | Partially implemented | Horizontal irradiance screening; panel model not defined |
| Date/time selection interface | Implemented (not revalidated) | No verified change in this integration |
| Component / task | Audited status | Evidence / limitation |
| --- | --- | --- |
| Earth position dashboard | Partially  implemented / placeholder (not revalidated) | No verified change in this integration |
| Earth azimuth calculations | Implemented, unvalidated | SPICE geometry code; runtime not checked |
| Earth elevation calculations | Implemented, unvalidated | SPICE geometry code; runtime not checked |
| Earthrise calculations | Partially implemented | Sample-bounded visibility transition event available from science API; true event time not independently validated |
| Earthset calculations | Partially implemented | Sample-bounded visibility transition event available from science API; true event time not independently validated |
| Direct-to-Earth visibility | Partially implemented | Geometric visibility, no RF link budget |
| Communication window calculations | Partially implemented | Backend samples Earth visibility for chosen time period |
| Terrain-blocked communication detection | Partially implemented | Terrain horizon comparison within 10 km |
| Total communication hours | Partially implemented | Backend sums sampled LOS windows; numerical validation pending |
| Component / task | Audited status | Evidence / limitation |
| --- | --- | --- |
| Main dashboard | Implemented (not revalidated) | No verified change in this integration |
| 2D lunar map interface | Implemented (not revalidated) | No verified change in this integration |
| 2D map with real LOLA terrain | Missing | Existing 2D map remains schematic |
| Zoom and coordinate selection | Implemented (not revalidated) | No verified change in this integration |
| Historical landing-site markers | Implemented (not revalidated) | No verified change in this integration |
| Custom location markers | Implemented (not revalidated) | No verified change in this integration |
| 3D map interface | Partially implemented | Actual WebGL terrain mesh code; browser not tested |
| Real 3D lunar terrain | Partially implemented | Site01 real DEM mesh; no end-to-end browser verification |
| Sun/Earth visualization | Partially  implemented / placeholder (not revalidated) | No verified change in this integration |
| Terrain shadow visualization | Missing (not revalidated) | No verified change in this integration |
| Landing-site comparison visualization | Partially  implemented (not revalidated) | No verified change in this integration |
| Component / task | Audited status | Evidence / limitation |
| --- | --- | --- |
| Python backend | Implemented (not revalidated) | No verified change in this integration |
| FastAPI | Implemented (not revalidated) | No verified change in this integration |
| SQLite database | Implemented (not revalidated) | No verified change in this integration |
| Redis caching support | Partially  implemented / optional framework (not revalidated) | No verified change in this integration |
| API architecture | Implemented (not revalidated) | No verified change in this integration |
| Location API | Implemented (not revalidated) | No verified change in this integration |
| Assessment API | Implemented (not revalidated) | No verified change in this integration |
| Comparison API | Implemented (not revalidated) | No verified change in this integration |
| Data refresh API | Framework implemented (not revalidated) | No verified change in this integration |
| Data status API | Framework implemented (not revalidated) | No verified change in this integration |
| Real NASA data API integration | Partially implemented | Locally bundled NASA-derived products accessible via raster API; no live NASA ingest API |
| Python science engine | Implemented, requires validation | Geometry, terrain, horizon and analysis endpoints are in Python |
| Validated scientific calculation engine | Missing | Need SpiceyPy runtime and independent reference comparison |
| Cloudflare Worker integration | Partially implemented | Pages Functions proxy and optional Worker code; deployment not verified |
| Cloudflare deployment | Not verified | No live Pages deployment performed |
| Docker / Docker Compose | Implemented as configuration | Dockerfiles and compose supplied, not executed |
| Component / task | Audited status | Evidence / limitation |
| --- | --- | --- |
| Location database | Implemented (not revalidated) | No verified change in this integration |
| SQLite storage | Implemented (not revalidated) | No verified change in this integration |
| Redis caching framework | Partially  implemented (not revalidated) | No verified change in this integration |
| Browser-side caching | Planned (not revalidated) | No verified change in this integration |
| IndexedDB | Planned (not revalidated) | No verified change in this integration |
| PostgreSQL/PostGIS | Planned (not revalidated) | No verified change in this integration |
| Object storage for terrain datasets | Planned (not revalidated) | No verified change in this integration |
| Scheduled data-manifest checking | Framework implemented (not revalidated) | No verified change in this integration |
| Automatic NASA dataset downloading | Partially implemented | Download scripts present, remote download not tested |
| Dataset version tracking | Framework implemented (not revalidated) | No verified change in this integration |
| Data provenance documentation | Implemented (not revalidated) | No verified change in this integration |
| Data freshness/status page | Implemented (not revalidated) | No verified change in this integration |
| Component / task | Audited status | Evidence / limitation |
| --- | --- | --- |
| Multiple landing-site selection | Implemented (not revalidated) | No verified change in this integration |
| Date and time selection | Implemented (not revalidated) | No verified change in this integration |
| Scenario system | Implemented (not revalidated) | No verified change in this integration |
| Compare different locations | Partially  implemented (not revalidated) | No verified change in this integration |
| Compare different dates | Partially  implemented (not revalidated) | No verified change in this integration |
| Sunlight-based site ranking | Missing | Screening thresholds exist; no ranking engine |
| Communication-based site ranking | Missing | Screening thresholds exist; no ranking engine |
| Combined landing-site suitability score | Partially implemented | Pass/fail screening thresholds; no calibrated score |
| Mission constraint configuration | Planned  / partial (not revalidated) | No verified change in this integration |
| Automatic alternative-site recommendations | Missing (not revalidated) | No verified change in this integration |
| Mission timeline visualization | Planned (not revalidated) | No verified change in this integration |
| Component / task | Audited status | Evidence / limitation |
| --- | --- | --- |
| Download and integrate NASA LOLA elevation  datasets | Priority (not revalidated) | No verified change in this integration |
| Build the LOLA DEM processing pipeline | Priority (not revalidated) | No verified change in this integration |
| Integrate JPL SPICE kernels | Priority (not revalidated) | No verified change in this integration |
| Implement validated Sun position  calculations | Priority (not revalidated) | No verified change in this integration |
| Implement validated Earth position  calculations | Priority (not revalidated) | No verified change in this integration |
| Build terrain horizon calculations | Priority (not revalidated) | No verified change in this integration |
| Calculate terrain-based sunlight and shadows | Priority (not revalidated) | No verified change in this integration |
| Calculate sunrise and sunset | Priority (not revalidated) | No verified change in this integration |
| Calculate Earthrise and Earthset | Priority (not revalidated) | No verified change in this integration |
| Calculate direct-to-Earth communication  windows | Priority (not revalidated) | No verified change in this integration |
| Implement terrain-based communication  obstruction | Priority (not revalidated) | No verified change in this integration |
| Build realistic 3D lunar terrain | Priority (not revalidated) | No verified change in this integration |
| Integrate LROC imagery | Later (not revalidated) | No verified change in this integration |
| Estimate solar power generation potential | Priority (not revalidated) | No verified change in this integration |
| Build a landing-site suitability scoring  system | Priority (not revalidated) | No verified change in this integration |
| Build automatic landing-site comparisons | Priority (not revalidated) | No verified change in this integration |
| Implement NASA dataset downloading and  updates | Later (not revalidated) | No verified change in this integration |
| Connect the frontend to the scientific  calculation engine | Priority (not revalidated) | No verified change in this integration |
| Verify Cloudflare and Python backend  integration | Later (not revalidated) | No verified change in this integration |
| Test calculations against independent  NASA/JPL reference data | Priority (not revalidated) | No verified change in this integration |

## Reproduce checks (Windows or Linux)

```bash
python -m pip install -r science_api/requirements-dev.txt
cd science_api
python -m pytest -q tests
cd ..
python scripts/verify_spice.py
node --check app.js
node scripts/build_pages.mjs
```

The site is not deployed to Cloudflare. Browser-based 3D validation, independent ephemeris verification, full-horizon shadow validation, and optional text PCK remain unfinished.
