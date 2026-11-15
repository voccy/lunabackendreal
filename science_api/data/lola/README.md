# LUNA LOLA terrain data

The five uploaded Site01 5 m rasters are included under `site01/`. Other large NASA/USGS LOLA products are not bundled. Download them with `scripts/download_science_data.py` from the project root.

## Download profiles

```bash
# Development subset
python scripts/download_science_data.py --profile starter

# Whole-Moon global LOLA DEM (about 8 GB)
python scripts/download_science_data.py --profile global

# All listed regional South Pole 5 m products + 87S mosaic
python scripts/download_science_data.py --profile south-pole-5m

# Catalogue every linked file from PGDA products 78, 81 and 90 without downloading
python scripts/download_science_data.py --profile all --catalogue-only

# Full PGDA linked-asset collection + global DEM (very large)
python scripts/download_science_data.py --profile all --yes
```

## Product families

- Regional South Pole 5 m products: NASA PGDA product 78, including elevation (`*_surf.tif`), slope (`*_slp.tif`), height uncertainty (`*_toterr.tif`), LOLA return count (`*_ldec.tif`), slope uncertainty (`*_slperr.tif`), point clouds, ROI archives and published clones.
- South Pole 87S 5 m mosaic: NASA PGDA product 81.
- Multi-resolution South Pole elevation, slope, count, uncertainty, effective-resolution, hillshade, roughness and permanently-shadowed-region products: NASA PGDA product 90.
- Whole-Moon LOLA global 118.45 m/pixel DEM: USGS Astrogeology distribution of the LRO LOLA global DEM.

The `all` profile scrapes the downloadable assets linked from PGDA products 78, 81 and 90 and adds the global 118 m DEM. This is not a mirror of every raw LOLA EDR/RDR/GDR file in the PDS mission archive. Full raw PDS coverage and all tiled 512/1024 px-per-degree GDR products remain a separate ingestion task.

## Coordinate and resolution notes

The high-resolution PGDA polar products use south-polar stereographic coordinates in the `MOON_ME` frame associated with DE421. The whole-Moon global product uses a simple cylindrical projection, planetocentric latitude and east-positive longitude. Pixel spacing is not equivalent to independent measurement resolution; many DEM cells are interpolated between LOLA tracks. Interpret elevation together with count, uncertainty and effective-resolution layers where available.

Sources:
- https://pgda.gsfc.nasa.gov/products/78
- https://pgda.gsfc.nasa.gov/products/81
- https://pgda.gsfc.nasa.gov/products/90
- https://astrogeology.usgs.gov/search/map/moon_lro_lola_dem_118m
- https://pds-geosciences.wustl.edu/missions/lro/lola_faq.htm
