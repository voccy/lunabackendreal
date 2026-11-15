# LUNA LOLA upgrade notes

## Added in this update

- Multi-profile NASA/USGS LOLA downloader (`starter`, `global`, `south-pole-5m`, `all`).
- Dynamic catalogue discovery from PGDA product pages 78, 81 and 90 for the `all` profile, including published regional assets, clones, point clouds, ROI archives, large-area topography, roughness and PSR layers.
- Whole-Moon 118.45 m/pixel LOLA global DEM download option.
- Resumable downloads and SHA-256 ingestion manifest records.
- Science API discovery of installed regional, mosaic, large-area and global DEMs; finest covering grid is selected.
- Companion slope, height uncertainty, slope uncertainty, effective resolution and LOLA return-count sampling when the corresponding layers exist.
- `GET /lola/catalog` and `GET /lola/terrain-grid` endpoints.
- Cloudflare Pages proxy endpoints `/api/lola-catalog` and `/api/lola-terrain`.
- Interactive downsampled 3D local terrain mesh from actual LOLA samples, with drag rotation and scroll zoom. The schematic globe remains only as a no-data fallback.
- Five software regression tests for catalogue discovery and helper calculations.

## Important limitations

- No multi-gigabyte NASA/USGS raster binaries are included in this ZIP. Run the downloader on a machine with sufficient storage.
- `all` means all downloadable assets linked by PGDA products 78, 81 and 90 plus the global 118 m DEM. It is not a complete mirror of all raw LOLA mission data in the PDS archive.
- The current 3D mesh is a downsampled local terrain patch (65 x 65 by default), not a full-resolution global Moon mesh or a certified engineering terrain model.
- SPICE geometry and illumination calculations still need independent numerical validation against JPL Horizons and published reference cases.
- Cloudflare Pages, R2, KV and the remote science API are not deployed/configured by this ZIP. The project still needs the user's Cloudflare resources and science-service hosting URL.
