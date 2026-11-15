/* Native WebGL Site01 elevation mesh. No synthetic height data or CDN dependencies.
   Heights originate from installed LOLA raster samples; vertical exaggeration is view-only. */
(() => {
  let canvas, gl, program, buffer, elementBuffer, indexCount = 0, sourceGrid = null, valid = false;
  let aPosition, aShade, uYaw, uPitch, uZoom, uAspect, uVertical;
  let exaggeration = 1;
  function shader(type, source) {
    const s = gl.createShader(type); gl.shaderSource(s, source); gl.compileShader(s);
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s));
    return s;
  }
  function init() {
    if (gl) return true;
    const base = document.getElementById('lunarGlobe');
    if (!base) return false;
    const parent = base.parentElement;
    parent.style.position = 'relative';
    canvas = document.createElement('canvas');
    canvas.id = 'site01Webgl';
    canvas.setAttribute('aria-label', 'WebGL lunar elevation mesh based on the Site01 LOLA elevation raster');
    Object.assign(canvas.style, {position:'absolute',left:base.offsetLeft+'px',top:base.offsetTop+'px',width:base.clientWidth+'px',height:base.clientHeight+'px',pointerEvents:'none',display:'none'});
    parent.appendChild(canvas);
    gl = canvas.getContext('webgl', { alpha:false, antialias:true, preserveDrawingBuffer:false });
    if (!gl) { canvas.remove(); canvas = null; return false; }
    const vs = shader(gl.VERTEX_SHADER, `
      attribute vec3 aPosition; attribute float aShade;
      uniform float uYaw, uPitch, uZoom, uAspect, uVertical;
      varying float vShade;
      void main() {
        float cy=cos(uYaw), sy=sin(uYaw), cp=cos(uPitch), sp=sin(uPitch);
        vec3 p = vec3(aPosition.xy, aPosition.z * uVertical);
        float x = p.x*cy-p.y*sy, y=p.x*sy+p.y*cy;
        vec3 rotated = vec3(x,y*cp-p.z*sp,y*sp+p.z*cp);
        float factor=0.76*uZoom;
        gl_Position=vec4(rotated.x*factor/uAspect,rotated.y*factor,rotated.z*0.20,1.0);
        vShade=aShade;
      }`);
    const fs = shader(gl.FRAGMENT_SHADER, `
      precision mediump float; varying float vShade;
      void main() {
        vec3 low=vec3(0.11,0.21,0.29), high=vec3(0.63,0.76,0.75);
        gl_FragColor=vec4(mix(low, high, clamp(vShade, 0.0,1.0)),1.0);
      }`);
    program=gl.createProgram(); gl.attachShader(program, vs);gl.attachShader(program, fs);gl.linkProgram(program);
    if (!gl.getProgramParameter(program,gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(program));
    aPosition=gl.getAttribLocation(program,'aPosition'); aShade=gl.getAttribLocation(program,'aShade');
    uYaw=gl.getUniformLocation(program,'uYaw');uPitch=gl.getUniformLocation(program,'uPitch');
    uZoom=gl.getUniformLocation(program,'uZoom');uAspect=gl.getUniformLocation(program,'uAspect');
    uVertical=gl.getUniformLocation(program,'uVertical');
    buffer=gl.createBuffer(); elementBuffer=gl.createBuffer();
    gl.enable(gl.DEPTH_TEST);gl.disable(gl.CULL_FACE);
    return true;
  }
  function build(grid) {
    const h=grid.elevations_m, n=h.length, radius=grid.radius_m;
    if (!n || !radius || !h.every(row => row.length===n)) throw Error('Invalid rectangular terrain grid');
    const vals=h.flat().filter(Number.isFinite);
    if (vals.length<3) throw Error('Not enough valid elevation samples');
    const min=Math.min(...vals), max=Math.max(...vals), average=vals.reduce((a,b)=>a+b,0)/vals.length;
    const vertices=new Float32Array(n*n*4), indices=[];
    for(let i=0;i<n;i++) for(let j=0;j<n;j++) {
      const e=h[i][j], k=(i*n+j)*4;
      vertices[k]=2*j/(n-1)-1;
      vertices[k+1]=1-2*i/(n-1);
      vertices[k+2]=Number.isFinite(e)?(e-average)/radius:0;
      vertices[k+3]=Number.isFinite(e)?(max===min?0.5:(e-min)/(max-min)):0;
    }
    for(let i=0;i<n-1;i++)for(let j=0;j<n-1;j++) {
      const a=i*n+j,b=a+1,c=a+n,d=c+1;
      if([h[i][j],h[i][j+1],h[i+1][j+1]].every(Number.isFinite))indices.push(a,b,d);
      if([h[i][j],h[i+1][j+1],h[i+1][j]].every(Number.isFinite))indices.push(a,d,c);
    }
    gl.bindBuffer(gl.ARRAY_BUFFER,buffer);gl.bufferData(gl.ARRAY_BUFFER,vertices,gl.STATIC_DRAW);
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,elementBuffer);gl.bufferData(gl.ELEMENT_ARRAY_BUFFER,new Uint16Array(indices),gl.STATIC_DRAW);
    indexCount=indices.length;
  }
  function controls() {
    const status=document.getElementById('terrain3dStatus');
    if(!status || document.getElementById('terrainVerticalScale'))return;
    const control=document.createElement('button'); control.id='terrainVerticalScale';control.type='button';
    control.textContent='Vertical scale: 1× (true scale)';
    control.style.cssText='margin:6px;padding:6px 12px;border:1px solid #60949d;background:#132b39;color:#dcecf0;border-radius:7px;cursor:pointer';
    control.onclick=()=>{exaggeration=exaggeration===1?2.2:1;control.textContent=`Vertical scale: ${exaggeration}× ${exaggeration===1?'(true scale)':'(exaggerated)'}`; if(sourceGrid)window.renderSite01Webgl(sourceGrid,window.lunaTerrainYaw?.()??-.55,window.lunaTerrainPitch?.()??.72,window.lunaTerrainZoom?.()??1);};
    status.insertAdjacentElement('afterend',control);
  }
  window.renderSite01Webgl=function(grid,yaw,pitch,zoom) {
    try {
      if(!grid){if(canvas)canvas.style.display='none';sourceGrid=null;return false;}
      if(!init())return false;
      controls();
      if(grid!==sourceGrid){build(grid);sourceGrid=grid;}
      const rect=document.getElementById('lunarGlobe').getBoundingClientRect(), dpr=window.devicePixelRatio||1;
      if(!rect.width||!rect.height)return false;
      canvas.style.left=document.getElementById('lunarGlobe').offsetLeft+'px';canvas.style.top=document.getElementById('lunarGlobe').offsetTop+'px';canvas.style.width=rect.width+'px';canvas.style.height=rect.height+'px';canvas.width=Math.round(rect.width*dpr);canvas.height=Math.round(rect.height*dpr);
      canvas.style.display='block';gl.viewport(0,0,canvas.width,canvas.height);
      gl.clearColor(0.035,0.086,0.141,1);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);
      gl.useProgram(program);gl.bindBuffer(gl.ARRAY_BUFFER,buffer);gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,elementBuffer);
      gl.enableVertexAttribArray(aPosition);gl.vertexAttribPointer(aPosition,3,gl.FLOAT,false,16,0);
      gl.enableVertexAttribArray(aShade);gl.vertexAttribPointer(aShade,1,gl.FLOAT,false,16,12);
      gl.uniform1f(uYaw,yaw);gl.uniform1f(uPitch,pitch);gl.uniform1f(uZoom,zoom);
      gl.uniform1f(uAspect,rect.width/rect.height);gl.uniform1f(uVertical,exaggeration);
      gl.drawElements(gl.TRIANGLES,indexCount,gl.UNSIGNED_SHORT,0);
      return true;
    } catch(e){console.warn('WebGL terrain fallback:',e);if(canvas)canvas.style.display='none';return false;}
  };
})();
