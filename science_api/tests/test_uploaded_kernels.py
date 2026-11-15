"""Verify genuine-format, byte-preserved user supplied kernel files (not ephemeris validation)."""
from pathlib import Path
import hashlib
import json

def test_five_uploaded_kernel_signatures_and_manifest():
    root = Path(__file__).resolve().parents[1] / 'kernels'
    manifest = json.loads((root / 'installed_kernel_manifest.json').read_text())
    expected = {'de421.bsp': b'DAF/SPK', 'moon_pa_de421_1900-2050.bpc': b'DAF/PCK',
                'moon_080317.tf': b'KPL/FK', 'naif0012.tls': b'KPL/LSK', 'pck00011.tpc': b'KPL/PCK'}
    for name, signature in expected.items():
        path = root / name
        assert path.is_file()
        assert path.open('rb').read(len(signature)) == signature
        assert hashlib.sha256(path.read_bytes()).hexdigest() == manifest[name]['sha256']
