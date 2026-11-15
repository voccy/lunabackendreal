r"""Install user-downloaded genuine NAIF kernels into LUNA without internet access.

Download five files from official NASA links, then run:
    py scripts\install_spice_from_downloads.py
Optionally provide an explicit source directory as the first argument.
"""
from pathlib import Path
import hashlib
import json
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'science_api' / 'kernels'
SOURCES = {
    'de421.bsp': 'https://naif.jpl.nasa.gov/pub/naif/JUNO/kernels/spk/de421.bsp',
    'moon_pa_de421_1900-2050.bpc': 'https://naif.jpl.nasa.gov/pub/naif/generic_kernels/pck/moon_pa_de421_1900-2050.bpc',
    'moon_080317.tf': 'https://naif.jpl.nasa.gov/pub/naif/generic_kernels/fk/satellites/moon_080317.tf',
    'naif0012.tls': 'https://naif.jpl.nasa.gov/pub/naif/generic_kernels/lsk/naif0012.tls',
    'pck00011.tpc': 'https://naif.jpl.nasa.gov/pub/naif/generic_kernels/pck/pck00011.tpc',
}
MAGIC = {
    '.bsp': b'DAF/SPK',
    '.bpc': b'DAF/PCK',
    '.tf': b'KPL/FK',
    '.tls': b'KPL/LSK',
    '.tpc': b'KPL/PCK',
}

def valid_kernel(path):
    if not path.is_file() or path.stat().st_size < 1024:
        return False
    head = path.open('rb').read(96).lstrip(b'\xef\xbb\xbf\r\n ')
    return head.startswith(MAGIC[path.suffix.lower()])

def main():
    source = Path(sys.argv[1]).expanduser() if len(sys.argv)>1 else Path.home()/'Downloads'
    DEST.mkdir(parents=True, exist_ok=True)
    record = {}
    failed = False
    for name, url in SOURCES.items():
        destination = DEST/name
        candidate = source/name
        if not valid_kernel(candidate) and valid_kernel(destination):
            print('ALREADY INSTALLED:', name)
        elif not valid_kernel(candidate):
            print('MISSING OR INVALID:', candidate)
            print('  Obtain from:', url)
            failed = True
            continue
        else:
            shutil.copyfile(candidate, destination)
            print('INSTALLED:', name)
        with destination.open('rb') as f:
            sha256=hashlib.file_digest(f,'sha256').hexdigest()
        record[name]={'official_source':url,'size_bytes':destination.stat().st_size,'sha256':sha256,'file_signature_verified':True}
    (DEST/'installed_kernel_manifest.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    if failed:
        print('Not all five kernels installed. Download missing ones and rerun.')
        return 1
    print('All five kernel file signatures present. Run: py scripts\verify_spice.py')
    print('NOTE: Signature check is not an official NASA checksum or scientific validation.')
    return 0

if __name__ == '__main__':
    sys.exit(main())
