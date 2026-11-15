"""Verify installed binaries against recorded installation hashes and TIFF access.
Does NOT establish NASA provenance beyond the user-provided files.
"""
import hashlib, json, sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
kernels=root/'science_api/kernels'
manifest=kernels/'installed_kernel_manifest.json'
print('LUNA data integrity check')
failed=[]
if manifest.exists():
    d=json.loads(manifest.read_text(encoding='utf-8'))
    for name, expected in d.items():
        path=kernels/name
        if not path.exists():failed.append(f'{name}: missing');continue
        sha=hashlib.sha256(path.read_bytes()).hexdigest()
        if sha!=expected['sha256'] or path.stat().st_size!=expected['bytes']:
            failed.append(f'{name}: SHA-256 or size mismatch')
        else:print(name,'SHA-256 OK',sha[:16])
else:print('Kernel manifest not found');failed.append('kernel manifest')
try:
    import rasterio
    for n in ['surf','slp','slperr','ldec','toterr']:
        name=f'Site01_final_adj_5mpp_{n}.tif'
        path=root/'science_api/data/lola/site01'/name
        with rasterio.open(path) as ds:
            print(name, 'pixels', ds.width, 'x',ds.height,'CRS',ds.crs,'bytes',path.stat().st_size)
            if not ds.crs or ds.width!=3200 or ds.height!=3200:failed.append(name)
except Exception as ex:
    failed.append(f'LOLA inspection: {ex}')
checksum_path=root/'DATA_CHECKSUMS_SHA256.txt'
if checksum_path.exists():
    for line in checksum_path.read_text().splitlines():
        sha, rel=line.split(None,1)
        path=root/rel.strip()
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=sha:
            failed.append(f'{rel.strip()}: original uploaded LOLA SHA mismatch')
        else:print('Original LOLA SHA verified',path.name)
print('FAIL' if failed else 'PASS',failed or 'Uploaded files intact relative to recorded checksums; NASA-origin authentication not independently certified')
sys.exit(1 if failed else 0)
