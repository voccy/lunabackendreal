const LOCATIONS = [
 {id:"site01",name:"Site01 — Connecting Ridge terrain",kind:"LOLA 5 m survey",lat:-89.463162834,lon:-137.489552922,verified:false},
 {id:"apollo11",name:"Apollo 11",kind:"Historical landing",lat:0.6741,lon:23.4729,verified:false},
 {id:"apollo17",name:"Apollo 17",kind:"Historical landing",lat:20.1908,lon:30.7717,verified:false},
 {id:"luna16",name:"Luna 16",kind:"Historical landing",lat:-0.5137,lon:56.3638,verified:false},
 {id:"change4",name:"Chang'e 4",kind:"Historical landing",lat:-45.4446,lon:177.5991,verified:false},
 {id:"shackleton",name:"Shackleton Crater region",kind:"South-pole candidate region",lat:-89.9,lon:0,verified:false},
 {id:"malapert",name:"Malapert Massif region",kind:"South-pole candidate region",lat:-85.99,lon:0,verified:false}
];
export async function onRequest(){return Response.json(LOCATIONS,{headers:{"Cache-Control":"public, max-age=3600"}});}
