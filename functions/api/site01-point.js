// Cloudflare Pages proxy: raster processing stays in the external Python service.
export async function onRequest({request,env}){
 if(!env.LUNA_SCIENCE_API_URL)return Response.json({error:"Configure LUNA_SCIENCE_API_URL to access Site01 rasters"},{status:503});
 const incoming=new URL(request.url);
 const target=env.LUNA_SCIENCE_API_URL.replace(/\/$/,"")+"/lola/site01-point"+incoming.search;
 try{const response=await fetch(target,{headers:{Accept:"application/json"}});
  return new Response(await response.text(),{status:response.status,headers:{"Content-Type":"application/json","Cache-Control":"no-store"}});
 }catch(error){return Response.json({error:"Site01 service unavailable",detail:String(error)},{status:502});}
}
