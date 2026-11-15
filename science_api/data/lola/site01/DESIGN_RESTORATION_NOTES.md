# ORIGINAL HOMEPAGE DESIGN RESTORED

This package uses **LUNA_Cloudflare_Ready(6).zip** as the source of truth for the original homepage design.

- `index.html`: Original homepage/hero markup retained unchanged, with only a Site01 navigation entry and separate Site01 section added, plus the new CSS/JS includes.
- `style.css`: Exact byte-for-byte original Cloudflare Ready stylesheet.
- `site01.css`: A separate stylesheet for the Site01 readout; the homepage style is not overridden.
- `app.js`, `terrain-webgl.js`, `science_api/`, `functions/`, `scripts/`, five GeoTIFF rasters and SPICE setup scripts: from the provided Site01 SPICE package.
- `public/`: Browser assets, kept consistent with project root. `node scripts/build_pages.mjs` regenerates this.

## View locally (Windows)
Extract the ZIP fully to a normal folder (do NOT open `index.html` directly from inside WinRAR's Temp directory).
Open Command Prompt in `LUNA_Cloudflare` and run `py -m http.server 8080`; then visit `http://localhost:8080`.
Select Site01 in the planner and use **Open Site01 in 3D**. The bundled preview is a downsample of the included elevation raster.
For scientific API functionality and full instructions, consult `README.md`, `SCIENTIFIC_UPGRADE_STATUS.md`, and `SPICE_KERNEL_SETUP.md`. Actual SPICE kernels are not bundled.

## Limitations
No live Cloudflare deployment has been performed. Browser appearance and 3D controls require on-device verification. Full ephemeris calculations require the NASA/NAIF kernels and SpiceyPy.
