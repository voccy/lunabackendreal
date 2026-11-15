"""Generate a truthful, offline 2D map from installed Site01 DEM values."""
from pathlib import Path
import numpy as np
import rasterio
from rasterio.enums import Resampling
from PIL import Image, ImageDraw
root=Path(__file__).resolve().parents[1]
src=root/'science_api/data/lola/site01/Site01_final_adj_5mpp_surf.tif'
out=root/'data/site01_relief.png'
with rasterio.open(src) as ds:
    a=ds.read(1,out_shape=(512,512),resampling=Resampling.average,masked=True)
    v=np.asarray(a.filled(np.nan),float)
    good=np.isfinite(v)
    if not good.any():raise SystemExit('No valid Site01 DEM pixels')
    lo,hi=np.nanpercentile(v,[2,98])
    q=np.clip((v-lo)/max(hi-lo,1),0,1)
    y,x=np.gradient(v, ds.height / 512 * abs(ds.transform.e), ds.width / 512 * abs(ds.transform.a))
    shade=np.clip(0.68+(x-y)*0.7,0.35,1.0)
    grey=np.clip((55+175*q)*shade,0,255)
    rgba=np.zeros((512,512,4),np.uint8)
    rgba[:,:,:3]=grey[:,:,None].astype('uint8')
    rgba[:,:,3]=np.where(good,255,0).astype('uint8')
    im=Image.fromarray(rgba,'RGBA')
    im.save(out,optimize=True)
    print(out,round(out.stat().st_size/1024),'KiB',f'elevation sample min={np.nanmin(v):.2f} max={np.nanmax(v):.2f} m')
