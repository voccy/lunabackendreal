"""Download *only* the five official NAIF kernels required by this project.
Avoids downloading unrelated multi-GB LOLA products already included in the ZIP.
Run from Windows: py scripts\\download_spice_kernels.py
"""
from pathlib import Path
import hashlib
import json
import sys
from urllib.request import urlopen, Request

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'science_api' / 'kernels'
SOURCES = {
    'naif0012.tls': 'https://naif.jpl.nasa.gov/pub/naif/generic_kernels/lsk/naif0012.tls',
    'de421.bsp': 'https://naif.jpl.nasa.gov/pub/naif/JUNO/kernels/spk/de421.bsp',
    'moon_pa_de421_1900-2050.bpc': 'https://naif.jpl.nasa.gov/pub/naif/generic_kernels/pck/moon_pa_de421_1900-2050.bpc',
    'moon_080317.tf': 'https://naif.jpl.nasa.gov/pub/naif/generic_kernels/fk/satellites/moon_080317.tf',
    'pck00011.tpc': 'https://naif.jpl.nasa.gov/pub/naif/generic_kernels/pck/pck00011.tpc',
}
def main():
    DEST.mkdir(parents=True, exist_ok=True)
    report = {}
    for name,url in SOURCES.items():
        path=DEST / name
        if path.exists() and path.stat().st_size>=1024:
            print(f'PRESENT {name}')
        else:
            temp=path.with_suffix(path.suffix+'.part')
            try:
                with urlopen(Request(url, headers={'User-Agent':'LUNA-Cloudflare-science/1.0'}),timeout=90) as source, temp.open('wb') as out:
                    while chunk:=source.read(1024*1024):out.write(chunk)
                if temp.stat().st_size<1024:raise ValueError('Download too small')
                temp.replace(path)
                print(f'DOWNLOADED {name} ({path.stat().st_size} bytes)')
            except Exception as exc:
                temp.unlink(missing_ok=True)
                print(f'FAILED {name}: {exc}',file=sys.stderr)
                report[name]={'url':url,'status':'FAILED','detail':str(exc)}
                continue
        with path.open('rb') as handle:
            digest=hashlib.file_digest(handle,'sha256').hexdigest()
        report[name]={'url':url,'bytes':path.stat().st_size,'sha256':digest,'status':'PRESENT'}
    out=DEST / 'kernel_manifest.json'
    out.write_text(json.dumps(report,indent=2)+'\n')
    print(f'Manifest: {out}')
    if len([v for v in report.values() if v['status']=='PRESENT'])!=len(SOURCES):sys.exit(1)
    print('All required files present; run the SPICE calculation tests separately to validate loading and frame geometry.')
if __name__=='__main__':main()
