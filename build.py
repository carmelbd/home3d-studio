"""Build app/index.html (the web designer) from the Home Assistant card's designer.

The designer lives in the ha-home-3d repo (floor-designer.html). This script copies it and
switches it to web mode: no "Export to HA" or wall-display buttons, its own saved-design key,
and a link back to the site's home page. Run after every designer update:

    python3 build.py                      # expects ../ha-home-3d next to this repo
    python3 build.py path/to/floor-designer.html
"""
import pathlib, sys

root = pathlib.Path(__file__).parent
src = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else root.parent / "ha-home-3d" / "floor-designer.html"
html = src.read_text()


def swap(old, new):
    global html
    if html.count(old) != 1:
        sys.exit(f"build.py: expected exactly one {old!r} in {src} (the designer changed; update build.py)")
    html = html.replace(old, new)


swap("<title>Home Floor Designer</title>", "<title>Home 3D Studio — Designer</title>")
swap("const KEY='ha-floor-designer-v1'", "const KEY='home3d-studio-v1'")
swap('<div class="brand"><b>🏠 Floor Designer</b><small>for Home Assistant</small></div>',
     '<a class="brand" href="../" style="color:inherit;text-decoration:none" title="Back to Home 3D Studio">'
     '<b>🏠 Home 3D Studio</b><small>Design your home</small></a>')
swap("</head>", "<style>#exportBtn,#wallBtn{display:none!important}</style>\n</head>")

# ---------- Studio-only HD realism (the Home Assistant card keeps the lighter renderer) ----------
# HQ: on unless the visitor switched it off (✨ HD button). TQ: photo texture size. FQ: drawn-floor texture scale.
swap("const PH='https://dl.polyhaven.org/file/ph-assets/Textures/jpg/1k/';",
     "const HQ=(()=>{try{return localStorage.getItem('home3d-hq')!=='0'}catch(e){return true}})(),FINE=matchMedia('(pointer:fine)').matches,"
     "TQ=HQ&&FINE?'2k':'1k',FQ=HQ?(FINE?4:2):1;"
     "const PH='https://dl.polyhaven.org/file/ph-assets/Textures/jpg/'+TQ+'/';")
html = html.replace("_1k.jpg`", "_${TQ}.jpg`")  # every photo texture (3 places)
swap("'https://dl.polyhaven.org/file/ph-assets/HDRIs/hdr/1k/kloofendal_48d_partly_cloudy_1k.hdr'",
     "`https://dl.polyhaven.org/file/ph-assets/HDRIs/hdr/${TQ}/kloofendal_48d_partly_cloudy_${TQ}.hdr`")
# drawn floors (tiles, marble, terrazzo…) at 2048px instead of 512px: crisp grout lines instead of a painted look
swap("c.width=c.height=512;const x=c.getContext('2d');let seed=",
     "c.width=c.height=512*FQ;const x=c.getContext('2d');x.scale(FQ,FQ);let seed=")
html = html.replace("t.anisotropy=8;", "t.anisotropy=HQ?16:8;")  # sharp floors at low viewing angles
swap("V.r.setPixelRatio(Math.min(devicePixelRatio,1.5))", "V.r.setPixelRatio(Math.min(devicePixelRatio,HQ?2:1.5))")
swap("dl.shadow.mapSize.set(2048,2048)", "dl.shadow.mapSize.set(HQ?4096:2048,HQ?4096:2048)")
# ambient occlusion (SSAO): soft shading in corners, under furniture and where walls meet the floor
swap("function draw3D(){if(V.r&&V.root)V.r.render(V.scene,V.cam)}",
     "function draw3D(){if(!V.r||!V.root)return;if(HQ&&fxOn())fxDraw();else V.r.render(V.scene,V.cam)}")
swap("V.r.setSize(b.width,b.height);", "V.r.setSize(b.width,b.height);fxSize();")
swap('BufferGeometryUtils.js"></script>', 'BufferGeometryUtils.js"></script>\n' + "\n".join(
    f'<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/{p}.js"></script>' for p in
    ["shaders/CopyShader", "shaders/SSAOShader", "math/SimplexNoise", "postprocessing/EffectComposer", "postprocessing/SSAOPass"]))
swap('<button data-v3="reset">Reset view</button>',
     '<button data-v3="reset">Reset view</button><button data-hq title="High-quality realistic rendering. Turn off if 3D feels slow.">✨ HD</button>')
swap("/* ---------- export ---------- */", r"""/* ---------- Studio HD: ambient occlusion layered on the normal render ----------
   The scene is drawn to the screen exactly as before (sun shadows, anti-aliasing, colours); SSAO is then
   computed from a normals/depth pass and multiplied on top. */
function fxOn(){if(V.fx!==undefined)return!!V.fx;V.fx=null;
  try{if(!THREE.SSAOPass||!V.r.capabilities.isWebGL2)return false;
    const sz=V.r.getDrawingBufferSize(new THREE.Vector2()),ssao=new THREE.SSAOPass(V.scene,V.cam,sz.x,sz.y);
    ssao.beautyRenderTarget.dispose();ssao.normalRenderTarget.depthTexture.type=THREE.UnsignedIntType;
    ssao.kernelRadius=.25;ssao.minDistance=.00002;ssao.maxDistance=.008;
    const fs=ssao.ssaoMaterial.fragmentShader,k='gl_FragColor = vec4( vec3( 1.0 - occlusion ), 1.0 );';
    if(fs.includes(k)){ssao.ssaoMaterial.fragmentShader=fs.replace(k,'gl_FragColor = vec4( vec3( pow( 1.0 - occlusion, 1.3 ) ), 1.0 );');ssao.ssaoMaterial.needsUpdate=true}
    /* device icons, labels, glass and fake-shadow decals must not cast ambient occlusion */
    ssao.overrideVisibility=function(){const c=this._visibilityCache;this.scene.traverse(o=>{c.set(o,o.visible);if(fxOverlay(o))o.visible=false})};
    V.fx={ssao}}catch(e){console.warn('HD effects off:',e);V.fx=null}
  return!!V.fx}
function fxOverlay(o){const m=o.material;return o.isPoints||o.isLine||o.isSprite||!!(m&&!Array.isArray(m)&&!m.isShadowMaterial&&(m.transparent||m.isMeshBasicMaterial))}
function fxSize(){if(!V.fx)return;const sz=V.r.getDrawingBufferSize(new THREE.Vector2());V.fx.ssao.setSize(sz.x,sz.y)}
function fxDraw(){const r=V.r,s=V.fx.ssao,u=s.ssaoMaterial.uniforms,sc=V.scene,over=[],solid=[];
  /* tight near/far for the depth-based shading: removes banding on flat floors and walls */
  const far=Math.max(40,V.cam.position.distanceTo(V.ctl.target)*3);if(Math.abs(V.cam.far-far)>1){V.cam.far=far;V.cam.updateProjectionMatrix()}
  sc.traverse(o=>{if(!o.visible)return;if(fxOverlay(o))over.push(o);else if(o.isMesh)solid.push(o)});
  /* 1. the house without icons, labels and glass */
  for(const o of over)o.visible=false;r.render(sc,V.cam);
  s.scene=V.scene;s.camera=V.cam;u.cameraNear.value=V.cam.near;u.cameraFar.value=V.cam.far;
  u.cameraProjectionMatrix.value.copy(V.cam.projectionMatrix);u.cameraInverseProjectionMatrix.value.copy(V.cam.projectionMatrixInverse);
  s.overrideVisibility();s.renderOverride(r,s.normalMaterial,s.normalRenderTarget,0x7777ff,1);s.restoreVisibility();
  u.kernelRadius.value=s.kernelRadius;u.minDistance.value=s.minDistance;u.maxDistance.value=s.maxDistance;
  s.renderPass(r,s.ssaoMaterial,s.ssaoRenderTarget);s.renderPass(r,s.blurMaterial,s.blurRenderTarget);
  s.copyMaterial.uniforms.tDiffuse.value=s.blurRenderTarget.texture;s.copyMaterial.blending=THREE.CustomBlending;s.renderPass(r,s.copyMaterial,null);
  /* 3. icons, labels and glass on top, depth-tested against the house */
  for(const o of over)o.visible=true;for(const o of solid)o.visible=false;const bg=sc.background,ac=r.autoClear;sc.background=null;r.autoClear=false;
  try{r.render(sc,V.cam)}finally{for(const o of solid)o.visible=true;sc.background=bg;r.autoClear=ac}}
document.addEventListener('click',e=>{const b=e.target.closest('[data-hq]');if(!b)return;
  try{localStorage.setItem('home3d-hq',HQ?'0':'1')}catch(err){}location.reload()});
{const b=document.querySelector('[data-hq]');if(b)b.classList.toggle('on',HQ)}

/* ---------- export ---------- */""")

out = root / "app" / "index.html"
out.parent.mkdir(exist_ok=True)
out.write_text(html)
print(f"Built {out.relative_to(root)} from {src} ({len(html):,} bytes)")
