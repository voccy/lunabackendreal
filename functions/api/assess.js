export async function onRequestPost({request,env}){
  if(!env.LUNA_SCIENCE_API_URL){return Response.json({error:"Scientific API is not configured. Set LUNA_SCIENCE_API_URL to the deployed LUNA science_api service."},{status:503});}
  let body;try{body=await request.json();}catch{return Response.json({error:"Invalid JSON body"},{status:400});}
  try{
    const upstream=await fetch(env.LUNA_SCIENCE_API_URL.replace(/\/$/,"")+"/assess",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});
    const payload=await upstream.text();
    return new Response(payload,{status:upstream.status,headers:{"Content-Type":"application/json","Cache-Control":"no-store"}});
  }catch(error){return Response.json({error:"Scientific API request failed",detail:String(error)},{status:502});}
}
