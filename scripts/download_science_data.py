#!/usr/bin/env python3
"""Ingest official NASA PGDA LOLA products and NAIF kernels.

Profiles:
  starter       Original Site04 + Site23 5 m products (smallest useful setup)
  south-pole-5m All 27 regional 5 m sites plus the 87S 5 m mosaic
  global        Whole-Moon LOLA 118 m/pixel global DEM (about 8 GB).
  all           Global DEM plus every downloadable asset linked by PGDA products
                78, 81 and 90 (potentially hundreds of GB; review first).

This is a curated PGDA product ingestion pipeline, not a mirror of every raw
LOLA/PDS laser observation ever acquired by LRO.
"""
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urljoin, urlparse
from html.parser import HTMLParser
from datetime import datetime, timezone
import hashlib, json, sys, argparse, time, re

ROOT = Path(__file__).resolve().parents[1]
REGIONAL_BASE = "https://pgda.gsfc.nasa.gov/data/LOLA_5mpp"
LARGE_BASE = "https://pgda.gsfc.nasa.gov/data/LOLA_20mpp"

# Names and products published by NASA GSFC PGDA product 78.
SITES = ["Site01", "Site04", "Site06", "Site07", "Site11", "Site20", "Site20v2",
         "Site23", "Site42", "Haworth", "Shoemaker", "DM1", "DM2", "SL2", "SL3",
         "NPA", "NPB", "NPC", "NPD", "LM1", "LM2", "LM3", "LM4", "LM5", "LM6", "LM7", "LM8"]
REGIONAL_SUFFIXES = ["surf.tif", "slp.tif", "toterr.tif", "ldec.tif", "slperr.tif"]

# Exact large-area file naming convention and products documented on PGDA product 90.
LARGE_AREA = {
    "60S": {"240MPP": ["LDEC", "LDEM", "LDEM_EFFRES", "LDEM_ERR", "LDEM_HILL", "LDSM", "LDSM_ERR"],
            "120MPP": ["LDEC", "LDEM", "LDEM_EFFRES", "LDEM_ERR", "LDEM_HILL", "LDSM", "LDSM_ERR"],
            "60MPP": ["LDEC", "LDEM", "LDEM_EFFRES", "LDEM_ERR", "LDEM_HILL", "LDSM", "LDSM_ERR"]},
    "75S": {"30MPP": ["LDEC", "LDEM", "LDEM_EFFRES", "LDEM_ERR", "LDEM_HILL", "LDSM", "LDSM_ERR"]},
    "80S": {"80MPP": ["LDEC", "LDEM", "LDEM_EFFRES", "LDEM_ERR", "LDEM_HILL", "LDSM", "LDSM_ERR"],
            "40MPP": ["LDEC", "LDEM", "LDEM_EFFRES", "LDEM_ERR", "LDEM_HILL", "LDSM", "LDSM_ERR"],
            "20MPP": ["LDEC", "LDEM", "LDEM_EFFRES", "LDEM_ERR", "LDEM_HILL", "LDSM", "LDSM_ERR"]},
    "83S": {"10MPP": ["LDEC", "LDEM", "LDEM_EFFRES", "LDEM_ERR", "LDEM_HILL", "LDSM", "LDSM_ERR"]},
}

KERNELS = {
    "naif0012.tls": "https://naif.jpl.nasa.gov/pub/naif/generic_kernels/lsk/naif0012.tls",
    "de421.bsp": "https://naif.jpl.nasa.gov/pub/naif/JUNO/kernels/spk/de421.bsp",
    "moon_pa_de421_1900-2050.bpc": "https://naif.jpl.nasa.gov/pub/naif/generic_kernels/pck/moon_pa_de421_1900-2050.bpc",
    "moon_080317.tf": "https://naif.jpl.nasa.gov/pub/naif/generic_kernels/fk/satellites/moon_080317.tf",
    "pck00011.tpc": "https://naif.jpl.nasa.gov/pub/naif/generic_kernels/pck/pck00011.tpc",
}

class LinkCollector(HTMLParser):
    def __init__(self):
        super().__init__(); self.links = []
    def handle_starttag(self, tag, attrs):
        if tag.lower() == "a":
            href = dict(attrs).get("href")
            if href: self.links.append(href)

def discover_all_published_assets():
    """Scrape official PGDA product pages so clones/point clouds/ROIs are not guessed."""
    pages = [
        "https://pgda.gsfc.nasa.gov/products/78",
        "https://pgda.gsfc.nasa.gov/products/81",
        "https://pgda.gsfc.nasa.gov/products/90",
    ]
    found = {}
    for page in pages:
        req = Request(page, headers={"User-Agent": "LUNA-research-data-ingestor/1.0"})
        with urlopen(req, timeout=60) as response:
            html = response.read().decode("utf-8", errors="replace")
        parser = LinkCollector(); parser.feed(html)
        for href in parser.links:
            url = urljoin(page, href)
            path = urlparse(url).path
            if "/data/LOLA_5mpp/" not in path and "/data/LOLA_20mpp/" not in path:
                continue
            rel = path.split("/data/", 1)[1]
            # Exclude directory links and HTML pages; preserve every published data asset.
            if rel.endswith("/") or Path(rel).suffix.lower() in (".html", ".htm"):
                continue
            found[url] = {"name": Path(rel).name, "url": url,
                          "path": f"science_api/data/lola/archive/{rel}",
                          "kind": "official-pgda-archive-asset", "source_page": page}
    return list(found.values())

def build_catalog(profile: str):
    items = []
    if profile == "global":
        return [{"name":"Lunar_LRO_LOLA_Global_LDEM_118m_Mar2014.tif",
                 "url":"https://planetarymaps.usgs.gov/mosaic/Lunar_LRO_LOLA_Global_LDEM_118m_Mar2014.tif",
                 "path":"science_api/data/lola/global/Lunar_LRO_LOLA_Global_LDEM_118m_Mar2014.tif",
                 "kind":"global-lola-dem","resolution_m":118.45,"coverage":"global"}]
    selected_sites = ["Site04", "Site23"] if profile == "starter" else SITES
    for site in selected_sites:
        folder = site
        for suffix in REGIONAL_SUFFIXES:
            filename = f"{site}_final_adj_5mpp_{suffix}"
            items.append({"name": filename, "url": f"{REGIONAL_BASE}/{folder}/{filename}",
                          "path": f"science_api/data/lola/{site.lower()}/{filename}",
                          "kind": "regional-5m", "site": site})
    if profile != "starter":
        # The official product uses this lowercase filename and 87S path.
        for filename in ["ldem_87s_5mpp.tif", "ldsm_87s_5mpp.tif", "ldec_87s_5mpp.tif", "ldem_87s_5mpp_hillshade.tif"]:
            items.append({"name": filename, "url": f"https://pgda.gsfc.nasa.gov/data/LOLA_5mpp/87S/{filename}",
                          "path": f"science_api/data/lola/mosaic/{filename}", "kind": "south-pole-mosaic"})
    if profile == "all":
        # Dynamically retrieve every linked asset from the three official PGDA
        # product pages, including regional clones, XYZI point clouds, ROI archives,
        # roughness/PSR products and all listed large-area DEM resolutions.
        assets = discover_all_published_assets()
        assets.append({"name":"Lunar_LRO_LOLA_Global_LDEM_118m_Mar2014.tif",
                       "url":"https://planetarymaps.usgs.gov/mosaic/Lunar_LRO_LOLA_Global_LDEM_118m_Mar2014.tif",
                       "path":"science_api/data/lola/global/Lunar_LRO_LOLA_Global_LDEM_118m_Mar2014.tif",
                       "kind":"global-lola-dem","resolution_m":118.45,"coverage":"global"})
        return assets
    return items

def sha256_file(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""): h.update(block)
    return h.hexdigest()

def fetch(url: str, dest: Path, dry_run=False):
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size:
        return {"file": str(dest.relative_to(ROOT)), "url": url, "bytes": dest.stat().st_size,
                "sha256": sha256_file(dest), "status": "kept"}
    if dry_run:
        print(f"PLAN  {url} -> {dest.relative_to(ROOT)}")
        return {"file": str(dest.relative_to(ROOT)), "url": url, "status": "planned"}
    tmp = dest.with_suffix(dest.suffix + ".part")
    print(f"GET   {url}")
    last_error = None
    for attempt in range(1, 4):
        h = hashlib.sha256(); total = 0
        try:
            req = Request(url, headers={"User-Agent": "LUNA-research-data-ingestor/1.0"})
            with urlopen(req, timeout=180) as response, tmp.open("wb") as out:
                while True:
                    block = response.read(1024 * 1024)
                    if not block: break
                    out.write(block); h.update(block); total += len(block)
            if total < 1024: raise RuntimeError(f"Unexpectedly small response ({total} bytes)")
            tmp.replace(dest)
            print(f"SAVED {dest.relative_to(ROOT)} ({total:,} bytes)")
            return {"file": str(dest.relative_to(ROOT)), "url": url, "bytes": total,
                    "sha256": h.hexdigest(), "status": "downloaded"}
        except Exception as exc:
            last_error = exc; tmp.unlink(missing_ok=True)
            if attempt < 3: print(f"Retry {attempt}/3: {exc}"); time.sleep(attempt * 3)
    raise RuntimeError(f"Download failed for {url}: {last_error}")

def main():
    p = argparse.ArgumentParser(description="Download official NASA PGDA LOLA products and NAIF SPICE kernels")
    p.add_argument("--profile", choices=["starter", "global", "south-pole-5m", "all"], default="starter")
    p.add_argument("--lola-only", action="store_true", help="Skip SPICE kernels")
    p.add_argument("--catalogue-only", action="store_true", help="Write the dataset catalogue without downloading")
    p.add_argument("--dry-run", action="store_true", help="List downloads without fetching")
    p.add_argument("--yes", action="store_true", help="Confirm very large --profile all download")
    args = p.parse_args()
    if args.profile == "all" and not (args.yes or args.catalogue_only or args.dry_run):
        p.error("--profile all can require many tens of GB. Review with --dry-run, then repeat with --yes.")
    catalog = build_catalog(args.profile)
    manifest_path = ROOT / "science_api/data/lola_catalog.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps({"generated_utc": datetime.now(timezone.utc).isoformat(),
        "source_pages": ["https://pgda.gsfc.nasa.gov/products/78", "https://pgda.gsfc.nasa.gov/products/81", "https://pgda.gsfc.nasa.gov/products/90"],
        "profile": args.profile, "scope_note": "Curated PGDA derived products; not every raw LOLA/PDS observation.",
        "products": catalog}, indent=2) + "\n")
    print(f"Catalogue: {manifest_path.relative_to(ROOT)} ({len(catalog)} LOLA files)")
    if args.catalogue_only: return
    records = []
    for item in catalog:
        records.append({**item, **fetch(item["url"], ROOT / item["path"], dry_run=args.dry_run)})
    if not args.lola_only and not args.dry_run:
        for name, url in KERNELS.items():
            records.append({"kind": "spice-kernel", "name": name,
                            **fetch(url, ROOT / "science_api/kernels" / name)})
    manifest = {"generated_utc": datetime.now(timezone.utc).isoformat(), "profile": args.profile,
                "source": "NASA GSFC PGDA LOLA + NAIF generic SPICE kernels", "products": records}
    if not args.dry_run:
        out = ROOT / "science_api/data/ingestion_manifest.json"
        out.write_text(json.dumps(manifest, indent=2) + "\n")
        print(f"Wrote {out.relative_to(ROOT)}")
    else:
        print("Dry run complete; no ingestion manifest was written.")

if __name__ == "__main__":
    try: main()
    except Exception as exc:
        print(f"Ingestion failed: {exc}", file=sys.stderr); sys.exit(1)
