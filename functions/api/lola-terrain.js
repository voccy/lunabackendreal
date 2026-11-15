export async function onRequest({request,env}){
  if(!env.LUNA_SCIENCE_API_URL){
    return Response.json({error:"Science API is not configured. Set LUNA_SCIENCE_API_URL."},{status:503});
  }
  const incoming=new URL(request.url);
  const target=env.LUNA_SCIENCE_API_URL.replace(/\/$/,"")+"/lola/terrain-grid"+incoming.search;
  try{
    const upstream=await fetch(target,{headers:{"Accept":"application/json"}});
    const payload=await upstream.text();
    return new Response(payload,{status:upstream.status,headers:{"Content-Type":"application/json","Cache-Control":"no-store"}});
  }catch(error){
    return Response.json({error:"LOLA terrain request failed",detail:String(error)},{status:502});
  }
}
