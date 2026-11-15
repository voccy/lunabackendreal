# NASA SPICE kernel installation status — 14 November 2026

Four genuine-format kernel files supplied by the user have been installed **inside the ZIP** at `science_api/kernels/`, retaining their bytes and normalizing names:

- `de421.bsp` — DE421 planetary/lunar SPK
- `moon_pa_de421_1900-2050.bpc` — DE421 lunar orientation PCK
- `moon_080317.tf` — matching lunar reference frame
- `naif0012.tls` — leap-second kernel

`pck00011.tpc` was **not uploaded** and cannot be downloaded in this environment (NASA hostname resolution fails). It is optional for the app's configured `MOON_ME` + DE421 SPK / binary lunar PCK workflow. Other SPICE routines using IAU planetary constants may require it. `scripts/download_spice_kernels.py` remains available to obtain all five on Windows.

Signature and SHA-256 hashes are recorded in `science_api/kernels/installed_kernel_manifest.json`. These are user-supplied files with NAIF signatures; matching their full contents to NASA's published checksums was not possible offline.

To execute and test the four-kernel geometry:

```bat
py -m pip install -r science_api\requirements.txt
py scripts\verify_spice.py
```

The SPICE calculations cannot be claimed to pass until SpiceyPy loads and executes them. Deployment of the separate Python service and browser/UI verification are likewise outstanding. See `CHECKLIST_AUDITED_2026_11_14.md`.
