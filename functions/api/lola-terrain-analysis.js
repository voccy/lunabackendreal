export async function onRequestGet({request,env}) {
  if(!env.LUNA_SCIENCE_API_URL) return Response.json({error:'Science API not configured. Configure LUNA_SCIENCE_API_URL.'},{status:503});
  const url=new URL(request.url), target=new URL(env.LUNA_SCIENCE_API_URL.replace(/\/$/,'')+'/lola/terrain-analysis');
  for(const [k,v] of url.searchParams) if(['latitude','longitude','radius_m','size','sun_azimuth_deg','sun_elevation_deg'].includes(k))target.searchParams.append(k,v);
  try {const response=await fetch(target,{headers:{Accept:'application/json'}});
    return new Response(await response.text(),{status:response.status,headers:{'Content-Type':'application/json','Cache-Control':'no-store'}});
  } catch(e){return Response.json({error:'Terrain science service unreachable',detail:String(e)},{status:502});}
}
