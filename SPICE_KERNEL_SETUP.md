# SPICE kernels for LUNA Cloudflare / Site01

SPICE kernels are real NASA/JPL NAIF ephemeris, orientation, reference-frame,
planetary-constant and time-conversion files used by SpiceyPy. The scientific API
expects the following five **genuine** files under `science_api/kernels/`:

| File | Purpose | Official source |
|---|---|---|
| `naif0012.tls` | UTC / ephemeris-time conversion | https://naif.jpl.nasa.gov/pub/naif/generic_kernels/lsk/naif0012.tls |
| `de421.bsp` | Sun, Earth, Moon planetary ephemeris | https://naif.jpl.nasa.gov/pub/naif/JUNO/kernels/spk/de421.bsp |
| `moon_pa_de421_1900-2050.bpc` | DE421 Moon principal-axis orientation | https://naif.jpl.nasa.gov/pub/naif/generic_kernels/pck/moon_pa_de421_1900-2050.bpc |
| `moon_080317.tf` | Moon mean-Earth/DE421 reference frame | https://naif.jpl.nasa.gov/pub/naif/generic_kernels/fk/satellites/moon_080317.tf |
| `pck00011.tpc` | Planetary physical constants | https://naif.jpl.nasa.gov/pub/naif/generic_kernels/pck/pck00011.tpc |

## Windows setup

From the extracted `LUNA_Cloudflare` project folder in Command Prompt:

```bat
py -m pip install -r science_api\requirements.txt
scripts\setup_spice_windows.bat
py scripts\verify_spice.py
```

The script stores SHA-256 hashes and downloaded file lengths in
`science_api/kernels/kernel_manifest.json`. A file being present is **not** proof
of scientifically validated ephemeris. The verification script actually loads
all five files with SpiceyPy and evaluates Sun and Earth position vectors in
`MOON_ME` for a reference date; that is an *execution smoke test*, not an
independent numerical accuracy benchmark.

You may also manually download these files from the official NAIF URLs and
place them in `science_api/kernels/`, then run the verifier.

## Packaging status

**No original SPICE kernel binaries or text kernels could be downloaded into
this ZIP in the current execution environment:** `curl` returned `Could not
resolve host: naif.jpl.nasa.gov`, and SpiceyPy was not installed. The included
setup scripts use the official NASA/NAIF servers when run on a Windows system
with Internet access. Do not claim this package includes genuine kernel data
until download and verification succeed.

## Cloudflare

Cloudflare Pages serves the website. The Python + SpiceyPy science API must run
on a separate Python/Docker-capable HTTPS host, with these kernels and the
LOLA GeoTIFF files mounted locally. Pages Functions proxy scientific requests
to that API. Simply uploading SPICE kernels to Pages static assets will not
make Cloudflare execute Python/CSPICE.
