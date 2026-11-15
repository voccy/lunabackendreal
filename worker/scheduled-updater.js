// Optional separate Cloudflare Worker for scheduled manifest checks.
// Deploy this Worker separately and set LUNA_MANIFEST_URL plus LUNA_CACHE KV binding.
export default {
 async scheduled(controller,env,ctx){
  if(!env.LUNA_MANIFEST_URL)return;
  try{
   const response=await fetch(env.LUNA_MANIFEST_URL,{headers:{"Accept":"application/json"}});
   if(!response.ok)throw new Error(`Manifest HTTP ${response.status}`);
   const manifest=await response.json();
   const record={checked_at:new Date().toISOString(),products:Array.isArray(manifest.products)?manifest.products:[],note:"Metadata check only; product-specific download, checksum, format validation, and safe activation are not implemented."};
   if(env.LUNA_CACHE)await env.LUNA_CACHE.put("manifest:last",JSON.stringify(record),{expirationTtl:60*60*24*30});
  }catch(error){
   const previous=env.LUNA_CACHE?await env.LUNA_CACHE.get("manifest:last","json"):null;
   if(env.LUNA_CACHE)await env.LUNA_CACHE.put("manifest:error",JSON.stringify({at:new Date().toISOString(),message:String(error),previous_preserved:!!previous}),{expirationTtl:60*60*24*7});
  }
 }
};
