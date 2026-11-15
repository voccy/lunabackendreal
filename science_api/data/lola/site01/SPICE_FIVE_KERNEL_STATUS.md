# SPICE kernel installation update — 14 November 2026

Five user-supplied NAIF-format kernels are now included in `science_api/kernels/`:

- de421.bsp (planetary ephemeris SPK)
- moon_pa_de421_1900-2050.bpc (lunar orientation binary PCK)
- moon_080317.tf (lunar frame kernel)
- naif0012.tls (leap-seconds kernel)
- pck00011.tpc (planetary constants text PCK; supplied as .tpc.txt, renamed without altering content)

The new pck00011.tpc SHA-256 is `3dff7b1dbeceaa01f25467767d3fa25816051c85d162d1edf04acb310ee28bb1`. The installed kernel manifest records checksums for all five.
The existing science API loader and `scripts/verify_spice.py` already load pck00011.tpc when it exists.

## Scientific status
- Kernel file inclusion and signature/checksum integrity: verified.
- SpiceyPy ephemeris computation: not executed in this environment; SpiceyPy unavailable.
- In-browser WebGL: not tested in this environment.
- Live Cloudflare deployment: not performed.

Windows: `py -m pip install -r science_api\requirements.txt`, then `py scripts\verify_spice.py`.
Run `py scripts\verify_data_integrity.py` and `py -m pytest science_api\tests` from the extracted project root.

This package preserves the pre-existing homepage styling and other functionality. No claim of NASA mission-grade accuracy is made.
