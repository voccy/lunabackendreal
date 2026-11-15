import { onRequestPost as assessPost } from "./assess.js";
export async function onRequestPost({request,env}){let body;try{body=await request.json();}catch{return Response.json({error:"Invalid JSON body"},{status:400});}
 const scenarios=body?.scenarios;if(!Array.isArray(scenarios)||scenarios.length<1||scenarios.length>8)return Response.json({error:"Compare 1 to 8 scenarios."},{status:400});
 const results=[];for(const s of scenarios){const req=new Request(new URL("/api/assess",request.url),{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(s)});const res=await assessPost({request:req,env});if(!res.ok)return res;results.push(await res.json());}
 return Response.json({results,note:"Each scenario uses the configured LUNA science API; if it is unavailable, the request returns an error instead of substituting scientific values."});}
