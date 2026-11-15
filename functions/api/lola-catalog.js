export async function onRequest({env}){
  if(!env.LUNA_SCIENCE_API_URL){
    return Response.json({error:"Science API is not configured. Set LUNA_SCIENCE_API_URL."},{status:503});
  }
  try{
    const upstream=await fetch(env.LUNA_SCIENCE_API_URL.replace(/\/$/,"")+"/lola/catalog");
    const payload=await upstream.text();
    return new Response(payload,{status:upstream.status,headers:{"Content-Type":"application/json","Cache-Control":"no-store"}});
  }catch(error){
    return Response.json({error:"LOLA catalogue request failed",detail:String(error)},{status:502});
  }
}
