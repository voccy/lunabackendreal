"""Verify installed LUNA Site01 NAIF kernels using SpiceyPy and a real geometry call.

Runs only when genuine NAIF kernels are installed. Does not claim independent
scientific accuracy validation of the output values.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
KERNELS = ROOT / 'science_api' / 'kernels'
REQUIRED = [
 'naif0012.tls', 'de421.bsp', 'moon_pa_de421_1900-2050.bpc',
 'moon_080317.tf'
]

def main():
    missing = [name for name in REQUIRED if not (KERNELS / name).is_file()]
    if missing:
        print('FAILED: Missing genuine kernel files: ' + ', '.join(missing))
        print('Run: py scripts\\download_spice_kernels.py')
        return 1
    try:
        import spiceypy as spice
    except ImportError:
        print('FAILED: SpiceyPy unavailable. Install: py -m pip install -r science_api\\requirements.txt')
        return 1
    optional = KERNELS / 'pck00011.tpc'
    try:
        spice.kclear()
        for name in REQUIRED:
            spice.furnsh(str(KERNELS / name))
        if optional.is_file(): spice.furnsh(str(optional))
        et = spice.str2et('2026-11-14T00:00:00 UTC')
        moon_to_sun, lt_sun = spice.spkezr('SUN', et, 'MOON_ME', 'LT+S', 'MOON')
        moon_to_earth, lt_earth = spice.spkezr('EARTH', et, 'MOON_ME', 'LT+S', 'MOON')
        print('PASS: All four required kernels loaded into CSPICE.')
        print('PASS: Sun and Earth vectors computed in MOON_ME at 2026-11-14 00:00 UTC.')
        print('Sun vector (km):', [round(float(x), 3) for x in moon_to_sun])
        print('Earth vector (km):', [round(float(x), 3) for x in moon_to_earth])
        # Independently documented numeric reference embedded in NAIF's lunar
        # frame kernel (moon_080317.tf, Example program output). This is
        # a limited regression check, not a full uncertainty validation.
        ref_et = spice.str2et('2008 MAR 17 20:10:00')
        ref_state, _ = spice.spkezr('EARTH', ref_et, 'MOON_ME', 'NONE', 'MOON')
        expected = (379892.825, 33510.118, -12661.5278)
        errors = [abs(float(ref_state[i]) - expected[i]) for i in range(3)]
        if max(errors) > 0.2:
            print('FAILED: DE421/ME reference geometry mismatch (km):', errors)
            return 1
        print('PASS: Earth->Moon geometry matches NAIF lunar frame kernel example within 0.2 km')
        print('NOTE: Limited reference test; not a complete scientific accuracy validation.')
        return 0
    except Exception as exc:
        print('FAILED: SPICE execution error:', exc)
        return 1
    finally:
        spice.kclear()

if __name__ == '__main__':
    sys.exit(main())
