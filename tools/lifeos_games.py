#!/usr/bin/env python3
"""LifeOS playable learning games (real WebGL/Three.js games, not widgets).

Each game is built into a single self-contained HTML packet (Three.js inlined)
so it works offline on the phone, just like the lessons. Served from the vault
at output/learn/ and surfaced on the /learn index.

Build:  python tools/lifeos_games.py build
"""
from __future__ import annotations

import argparse
import json
import urllib.request
from datetime import datetime

from lifeos_paths import APP_ROOT, VAULT_ROOT

OUT = VAULT_ROOT / "output" / "learn"
THREE_JS = APP_ROOT / "tools" / "vendor" / "three.min.js"
THREE_CDN = "https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"


def ensure_three() -> str:
    """Return the inlined Three.js source, downloading it once if missing."""
    if not THREE_JS.exists():
        THREE_JS.parent.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(THREE_CDN, headers={"User-Agent": "LifeOS/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            THREE_JS.write_bytes(resp.read())
    return THREE_JS.read_text(encoding="utf-8")

# Catalogue surfaced on the /learn index (imported by lifeos_lessons).
GAMES = [
    {
        "id": "game-civilization",
        "emoji": "🏛️",
        "accent": "#e0a851",
        "title": "Dawn of Civilization",
        "blurb": "Lead a band of foragers across 10,000 years. Bet on farming, build a "
                 "surplus, free your first specialists, and raise a city that invents writing.",
        "pairs": "story-of-civilization",
    },
    {
        "id": "game-orbit",
        "emoji": "🪐",
        "accent": "#6cc6ff",
        "title": "Orbit",
        "blurb": "Fling a probe around a star and feel how gravity really works — "
                 "too slow you fall in, too fast you escape, just right you orbit.",
        "pairs": "why-the-sky-is-blue",
    },
]


HEAD = """<!doctype html><html lang='en'><head>
<meta charset='utf-8'>
<meta name='viewport' content='width=device-width,initial-scale=1,viewport-fit=cover,user-scalable=no'>
<meta name='color-scheme' content='dark'>
<title>Orbit — a LifeOS learning game</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
html,body{height:100%;overflow:hidden;background:#03040a;color:#eaf2ff;font-family:system-ui,-apple-system,sans-serif;touch-action:none}
#c{display:block;width:100vw;height:100vh}
.panel{position:fixed;background:rgba(8,14,28,.62);backdrop-filter:blur(10px);border:1px solid rgba(120,170,255,.22);border-radius:16px;padding:12px 14px}
#top{top:12px;left:12px;max-width:62vw}
#top h1{font:800 20px/1 system-ui;letter-spacing:.04em}
#top p{font-size:13px;color:#9fb6dd;margin-top:5px;line-height:1.45}
#stats{top:12px;right:12px;text-align:right;font:700 13px/1.5 system-ui}
#stats b{color:#6cc6ff;font-size:18px}
#status{left:50%;transform:translateX(-50%);bottom:88px;font:700 15px/1 system-ui;text-align:center;white-space:nowrap;transition:opacity .3s;opacity:0}
#status.show{opacity:1}
#dock{left:50%;transform:translateX(-50%);bottom:14px;display:flex;gap:10px;align-items:center}
#dock .gauge{font:700 13px/1 system-ui;color:#9fb6dd;min-width:128px;text-align:center}
#dock .gauge b{color:#eaf2ff;font-size:16px}
#dock .tgt{color:#6cc6ff}
button{font:700 14px/1 system-ui;color:#eaf2ff;background:rgba(108,198,255,.16);border:1px solid rgba(120,170,255,.35);border-radius:12px;padding:11px 15px;cursor:pointer}
button:active{transform:scale(.96)}
.hint{font:600 12px/1 system-ui;color:#7e96c4}
#help{left:12px;bottom:14px;max-width:230px;font-size:12.5px;line-height:1.5;color:#9fb6dd}
#help b{color:#cfe0ff}
a.back{position:fixed;top:12px;left:12px;display:none}
@media(max-width:560px){#help{display:none}#top{max-width:54vw}}
</style></head><body>
<canvas id='c'></canvas>
<div id='top' class='panel'><h1>🪐 ORBIT</h1><p>Drag from the glowing pad and release to launch a probe. Find the speed that loops the star — that balance is an <b>orbit</b>.</p></div>
<div id='stats' class='panel'>Orbits <b id='norb'>0</b><br>Probes <span id='nlive'>0</span></div>
<div id='status' class='panel'></div>
<div id='help' class='panel'>Too <b>slow</b> → you fall into the star.<br>Too <b>fast</b> → you escape forever.<br>The <b>Moon</b> is just rock falling sideways fast enough to keep missing Earth.</div>
<div id='dock'>
  <button id='reset'>↺ Clear</button>
  <div class='gauge panel'>speed <b id='spd'>0</b><br><span class='tgt'>orbit ≈ <b id='vc'>0</b></span></div>
  <button id='demo'>＋ Demo orbit</button>
</div>
"""

TAIL = "</body></html>"


GAME_JS = r"""
(function(){
const cv=document.getElementById('c');
const renderer=new THREE.WebGLRenderer({canvas:cv,antialias:true});
renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,2));
const scene=new THREE.Scene();
scene.fog=new THREE.FogExp2(0x03040a,0.0011);
const camera=new THREE.PerspectiveCamera(52,1,0.1,4000);
camera.position.set(0,360,250);camera.lookAt(0,0,0);
function resize(){const w=window.innerWidth,h=window.innerHeight;renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix();}
window.addEventListener('resize',resize);resize();

// --- constants (tuned so a comfortable drag yields an orbit) ---
const GM=520000, STAR_R=16, ESCAPE=820;
const ANCHOR={x:-185,z:0};
const VC_ANCHOR=Math.sqrt(GM/Math.hypot(ANCHOR.x,ANCHOR.z)); // circular speed at the pad
const K=VC_ANCHOR/Math.hypot(ANCHOR.x,ANCHOR.z);             // drag->speed scale
const MAXV=150;

// --- lights ---
scene.add(new THREE.AmbientLight(0x26344f,0.7));
const plight=new THREE.PointLight(0xffe6b0,2.2,0,0);scene.add(plight);

// --- glow texture helper ---
function glowTex(){const s=128,cn=document.createElement('canvas');cn.width=cn.height=s;const x=cn.getContext('2d');
  const g=x.createRadialGradient(s/2,s/2,0,s/2,s/2,s/2);
  g.addColorStop(0,'rgba(255,240,200,1)');g.addColorStop(.25,'rgba(255,210,130,.85)');
  g.addColorStop(.55,'rgba(255,160,70,.35)');g.addColorStop(1,'rgba(255,140,60,0)');
  x.fillStyle=g;x.fillRect(0,0,s,s);return new THREE.CanvasTexture(cn);}

// --- star ---
const star=new THREE.Mesh(new THREE.SphereGeometry(STAR_R,40,40),new THREE.MeshBasicMaterial({color:0xfff0c0}));
scene.add(star);
const glow=new THREE.Sprite(new THREE.SpriteMaterial({map:glowTex(),color:0xffffff,blending:THREE.AdditiveBlending,depthWrite:false,transparent:true}));
glow.scale.set(150,150,1);scene.add(glow);

// --- arena grid + pad ---
const grid=new THREE.PolarGridHelper(ESCAPE,16,12,90,0x1b2c4a,0x14223c);grid.position.y=-0.2;scene.add(grid);
const pad=new THREE.Mesh(new THREE.RingGeometry(9,13,40),new THREE.MeshBasicMaterial({color:0x6cc6ff,side:THREE.DoubleSide,transparent:true,opacity:.9}));
pad.rotation.x=-Math.PI/2;pad.position.set(ANCHOR.x,0,ANCHOR.z);scene.add(pad);

// --- starfield ---
(function(){const n=1400,pos=new Float32Array(n*3);for(let i=0;i<n;i++){const r=1500+Math.random()*1400,th=Math.random()*6.283,ph=Math.acos(2*Math.random()-1);
  pos[i*3]=r*Math.sin(ph)*Math.cos(th);pos[i*3+1]=r*Math.cos(ph);pos[i*3+2]=r*Math.sin(ph)*Math.sin(th);}
  const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.BufferAttribute(pos,3));
  scene.add(new THREE.Points(g,new THREE.PointsMaterial({color:0x9fb6dd,size:2.4,sizeAttenuation:false})));})();

// --- aim line ---
const aimGeo=new THREE.BufferGeometry();aimGeo.setAttribute('position',new THREE.BufferAttribute(new Float32Array(6),3));
const aim=new THREE.Line(aimGeo,new THREE.LineBasicMaterial({color:0x6cc6ff}));aim.visible=false;scene.add(aim);

// --- bodies & trails ---
const COLORS=[0x6cc6ff,0x7dffb0,0xffd36c,0xff8a8a,0xc89bff,0x66e0d0];
const bodies=[];let orbits=0;
const elN=document.getElementById('norb'),elL=document.getElementById('nlive'),elS=document.getElementById('spd'),elVC=document.getElementById('vc'),elStat=document.getElementById('status');
elVC.textContent=VC_ANCHOR.toFixed(0);
function stats(){elN.textContent=orbits;elL.textContent=bodies.filter(b=>b.alive).length;}
let statTimer=null;function status(t){elStat.textContent=t;elStat.classList.add('show');clearTimeout(statTimer);statTimer=setTimeout(()=>elStat.classList.remove('show'),2600);}

function trail(color){const max=520,arr=new Float32Array(max*3),g=new THREE.BufferGeometry();
  g.setAttribute('position',new THREE.BufferAttribute(arr,3));g.setDrawRange(0,0);
  const l=new THREE.Line(g,new THREE.LineBasicMaterial({color:color,transparent:true,opacity:.65}));scene.add(l);
  return {g,arr,n:0,max};}
function push(t,x,y,z){if(t.n<t.max){t.arr.set([x,y,z],t.n*3);t.n++;}else{t.arr.copyWithin(0,3);t.arr.set([x,y,z],(t.max-1)*3);}
  t.g.setDrawRange(0,t.n);t.g.attributes.position.needsUpdate=true;}
function spawn(px,pz,vx,vz){const c=COLORS[bodies.length%COLORS.length];
  const m=new THREE.Mesh(new THREE.SphereGeometry(4.2,18,18),new THREE.MeshStandardMaterial({color:c,emissive:c,emissiveIntensity:.5,roughness:.4}));
  scene.add(m);bodies.push({x:px,z:pz,vx,vz,m,t:trail(c),alive:true,ang:Math.atan2(pz,px),acc:0,orbited:false});stats();}
function kill(b,msg){b.alive=false;b.m.visible=false;status(msg);stats();}

// --- input: drag from pad ---
const ray=new THREE.Raycaster(),ndc=new THREE.Vector2(),plane=new THREE.Plane(new THREE.Vector3(0,1,0),0),hit=new THREE.Vector3();
let drag=false,curV={x:0,z:0};
function world(e){const r=cv.getBoundingClientRect(),cx=(e.touches?e.touches[0].clientX:e.clientX),cy=(e.touches?e.touches[0].clientY:e.clientY);
  ndc.x=((cx-r.left)/r.width)*2-1;ndc.y=-((cy-r.top)/r.height)*2+1;ray.setFromCamera(ndc,camera);ray.ray.intersectPlane(plane,hit);return hit;}
function down(e){drag=true;move(e);}
function move(e){if(!drag)return;const p=world(e);let vx=(p.x-ANCHOR.x)*K,vz=(p.z-ANCHOR.z)*K;const sp=Math.hypot(vx,vz);
  if(sp>MAXV){vx*=MAXV/sp;vz*=MAXV/sp;}curV={x:vx,z:vz};
  const pa=aimGeo.attributes.position;pa.setXYZ(0,ANCHOR.x,0,ANCHOR.z);pa.setXYZ(1,ANCHOR.x+vx*1.4,0,ANCHOR.z+vz*1.4);pa.needsUpdate=true;aim.visible=true;
  elS.textContent=Math.min(sp,MAXV).toFixed(0);}
function up(){if(!drag)return;drag=false;aim.visible=false;if(Math.hypot(curV.x,curV.z)>4){spawn(ANCHOR.x,ANCHOR.z,curV.x,curV.z);}elS.textContent='0';}
cv.addEventListener('mousedown',down);window.addEventListener('mousemove',move);window.addEventListener('mouseup',up);
cv.addEventListener('touchstart',function(e){e.preventDefault();down(e);},{passive:false});
window.addEventListener('touchmove',function(e){e.preventDefault();move(e);},{passive:false});
window.addEventListener('touchend',up);

document.getElementById('reset').addEventListener('click',function(){bodies.forEach(b=>{scene.remove(b.m);scene.remove(b.t.g);b.t.g.dispose&&b.t.g.dispose();});bodies.length=0;orbits=0;stats();status('Cleared — try again.');});
document.getElementById('demo').addEventListener('click',function(){const r=150,v=Math.sqrt(GM/r);spawn(0,-r,v,0);status('A near-perfect circular orbit — copy that speed.');});

// --- main loop ---
let last=performance.now();
function tick(now){const dt=Math.min((now-last)/1000,0.05);last=now;const steps=8,h=dt/steps;
  for(const b of bodies){if(!b.alive)continue;
    for(let s=0;s<steps;s++){const r2=b.x*b.x+b.z*b.z,r=Math.sqrt(r2),inv=GM/(r2*r);
      b.vx-=b.x*inv*h;b.vz-=b.z*inv*h;b.x+=b.vx*h;b.z+=b.vz*h;}
    const a=Math.atan2(b.z,b.x);let d=a-b.ang;if(d>Math.PI)d-=6.283;if(d<-Math.PI)d+=6.283;b.acc+=d;b.ang=a;
    const r=Math.hypot(b.x,b.z);b.m.position.set(b.x,0,b.z);push(b.t,b.x,0,b.z);
    if(r<STAR_R+4)kill(b,'🔥 Too slow — burned up in the star.');
    else if(r>ESCAPE)kill(b,'🚀 Too fast — escaped into deep space.');
    else if(!b.orbited&&Math.abs(b.acc)>=6.283){b.orbited=true;orbits++;status('🛰️ Stable orbit! You found the sweet spot.');stats();}
  }
  const t=now*0.001;glow.scale.setScalar(150+Math.sin(t*2)*6);
  renderer.render(scene,camera);requestAnimationFrame(tick);
}
spawn(0,-150,Math.sqrt(GM/150),0); // a live orbit on load
requestAnimationFrame(tick);
})();
"""


CIV_HEAD = """<!doctype html><html lang='en'><head>
<meta charset='utf-8'>
<meta name='viewport' content='width=device-width,initial-scale=1,viewport-fit=cover,user-scalable=no'>
<meta name='color-scheme' content='dark'>
<title>Dawn of Civilization — a LifeOS learning game</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
html,body{height:100%;overflow:hidden;background:#0a0d14;color:#f3ecd9;font-family:system-ui,-apple-system,sans-serif;touch-action:manipulation}
#c{display:block;width:100vw;height:100vh}
.panel{position:fixed;background:rgba(20,16,10,.66);backdrop-filter:blur(10px);border:1px solid rgba(224,168,81,.28);border-radius:16px;padding:11px 14px}
#top{top:12px;left:12px;max-width:60vw}
#top h1{font:800 18px/1 system-ui;color:#f0c884}
#top .era{font-size:13px;color:#c9b48c;margin-top:4px}
#res{top:12px;right:12px;font:700 13px/1.7 system-ui;text-align:right}
#res b{color:#f0c884}
#hint{left:50%;transform:translateX(-50%);bottom:92px;font:600 13.5px/1.3 system-ui;color:#e9dcc0;max-width:84vw;text-align:center}
#status{left:50%;transform:translateX(-50%);bottom:138px;font:800 15px/1 system-ui;text-align:center;opacity:0;transition:opacity .3s;white-space:nowrap}
#status.show{opacity:1}
#dock{left:50%;transform:translateX(-50%);bottom:14px;display:flex;gap:8px;flex-wrap:wrap;justify-content:center;max-width:96vw}
.act{font:700 14px/1.1 system-ui;color:#f3ecd9;background:rgba(224,168,81,.16);border:1px solid rgba(224,168,81,.4);border-radius:13px;padding:12px 14px;cursor:pointer;text-align:center}
.act:active{transform:scale(.95)}
.act small{display:block;font:600 11px system-ui;color:#c9b48c;margin-top:3px}
#modal{position:fixed;inset:0;display:none;align-items:center;justify-content:center;background:rgba(5,6,10,.72);padding:24px;z-index:20}
#modal.show{display:flex}
#card{max-width:420px;background:#15110a;border:1px solid rgba(224,168,81,.4);border-radius:20px;padding:26px}
#card h2{font:800 24px/1.15 Georgia,serif;color:#f0c884;margin-bottom:10px}
#card p{font-size:17px;line-height:1.55;color:#e9dcc0;margin-bottom:18px}
#card button{font:700 15px system-ui;color:#0a0d14;background:#e0a851;border:none;border-radius:12px;padding:12px 20px;cursor:pointer;width:100%}
</style></head><body>
<canvas id='c'></canvas>
<div id='top' class='panel'><h1>🏛️ Dawn of Civilization</h1><div class='era' id='era'>Foraging band</div></div>
<div id='res' class='panel'>👥 <b id='r_p'>10</b>/<span id='r_cap'>14</span> &nbsp; 📦 <b id='r_s'>0</b><br>🌾 <span id='r_f'>0</span> farms &nbsp; 📜 <b id='r_k'>0</b><br>🗓 season <span id='r_sea'>1</span></div>
<div id='status' class='panel'></div>
<div id='hint' class='panel'></div>
<div id='dock'>
  <button class='act' id='b_forage'>🌿 Forage<small>safe food</small></button>
  <button class='act' id='b_farm'>🌾 Farm<small>+farmland</small></button>
  <button class='act' id='b_build'>🏠 Build<small>5 📦 → homes</small></button>
  <button class='act' id='b_spec'>👤 Specialist<small>6 📦 → 📜</small></button>
</div>
<div id='modal'><div id='card'><h2 id='m_t'></h2><p id='m_b'></p><button id='m_c'>Continue</button></div></div>
"""

CIV_JS = r"""
(function(){
const cv=document.getElementById('c');
const renderer=new THREE.WebGLRenderer({canvas:cv,antialias:true});
renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,2));
const scene=new THREE.Scene();scene.background=new THREE.Color(0x0a0d14);scene.fog=new THREE.FogExp2(0x0a0d14,0.0016);
const camera=new THREE.PerspectiveCamera(50,1,0.1,3000);
function resize(){const w=innerWidth,h=innerHeight;renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix();}
addEventListener('resize',resize);resize();
scene.add(new THREE.HemisphereLight(0xfff0d0,0x202a1a,1.05));
const sun=new THREE.DirectionalLight(0xffe7b0,1.3);sun.position.set(120,200,80);scene.add(sun);

// ground + river
const ground=new THREE.Mesh(new THREE.CircleGeometry(330,64),new THREE.MeshStandardMaterial({color:0x4a5d34,roughness:1}));
ground.rotation.x=-Math.PI/2;scene.add(ground);
const river=new THREE.Mesh(new THREE.PlaneGeometry(680,46),new THREE.MeshStandardMaterial({color:0x2f6f86,roughness:.5,metalness:.2}));
river.rotation.x=-Math.PI/2;river.position.set(0,0.3,150);scene.add(river);
// faint field rows that grow with farms
const fields=new THREE.Group();scene.add(fields);

// huts + ziggurat
const town=new THREE.Group();scene.add(town);
function hutAt(i){
  const a=i*2.399, r=18+i*4.6; const x=Math.cos(a)*r, z=Math.sin(a)*r*0.62 - 8;
  const g=new THREE.Group();
  const base=new THREE.Mesh(new THREE.BoxGeometry(13,10,13),new THREE.MeshStandardMaterial({color:0xa88553,roughness:1}));
  base.position.y=5;const roof=new THREE.Mesh(new THREE.ConeGeometry(11,8,4),new THREE.MeshStandardMaterial({color:0x7a4f28}));
  roof.position.y=13.5;roof.rotation.y=Math.PI/4;g.add(base);g.add(roof);g.position.set(x,0,z);g.scale.setScalar(0);town.add(g);return g;}
const huts=[];
const zig=new THREE.Group();(function(){const cols=[0xcdb487,0xc0a878,0xb39c6c];for(let k=0;k<4;k++){const s=34-k*8,h=8;
  const m=new THREE.Mesh(new THREE.BoxGeometry(s,h,s),new THREE.MeshStandardMaterial({color:cols[k%3],roughness:1}));m.position.y=4+k*h;zig.add(m);} })();
zig.position.set(0,0,-8);zig.scale.setScalar(0);scene.add(zig);

// people dots
const ppl=[];const pplGeo=new THREE.SphereGeometry(1.5,8,8);
function addPerson(){const m=new THREE.Mesh(pplGeo,new THREE.MeshStandardMaterial({color:0xf0d8a8,emissive:0x2a1d0a}));
  const a=Math.random()*6.28,r=Math.random()*46;m.position.set(Math.cos(a)*r,1.5,Math.sin(a)*r*0.7-6);
  m.userData={tx:m.position.x,tz:m.position.z,t:Math.random()*100};scene.add(m);ppl.push(m);}

// ---------- game state (numbers locked from the python balance sim) ----------
const AMB=5.0, FARM=2.4;
const S={season:1,people:10,cap:14,surplus:0,knowledge:0,farms:0,houses:0,spec:0,over:false,era:0};
const ERAS=['Foraging band','Farming village','Town','City of the plain','Civilization'];
const seen={};
const el=id=>document.getElementById(id);
let statT=null;function toast(t){const s=el('status');s.textContent=t;s.classList.add('show');clearTimeout(statT);statT=setTimeout(()=>s.classList.remove('show'),2800);}
function workers(){return Math.max(0,S.people-S.spec);}
function isCity(){return S.people>=24&&S.houses>=4;}

function modal(t,b){el('m_t').textContent=t;el('m_b').innerHTML=b;el('modal').classList.add('show');}
el('m_c').onclick=()=>el('modal').classList.remove('show');

function step(extra,addFarm){
  if(S.over)return;
  if(addFarm&&S.farms<S.people)S.farms++;
  const eff=Math.min(S.farms,workers());
  const produced=AMB+eff*FARM+(extra||0);
  const net=produced-S.people;
  S.surplus+=net; S.knowledge+=S.spec*2.5;
  if(S.surplus<0){const dead=Math.min(S.people-1,Math.ceil(-S.surplus/2));S.people-=dead;S.surplus=0;toast('☠️ Famine — '+dead+' lost. Food ran short.');}
  else if(net>0&&S.people<S.cap){const g=Math.min(Math.floor(S.surplus/4),S.cap-S.people,2);if(g>0){S.people+=g;S.surplus-=g*3;}}
  S.season++; sync(); milestones();
}
function forage(){step(S.people*0.3,false);}
function farm(){step(0,true);}
function build(){if(S.surplus>=5){S.surplus-=5;S.houses++;S.cap+=6;step(0,false);}else toast('Need 5 📦 surplus to build homes.');}
function specialist(){if(S.surplus>=6&&workers()>3){S.surplus-=6;S.spec++;step(0,false);}else toast('Need 6 📦 surplus and spare hands to free a specialist.');}

function milestones(){
  if(!seen.farm&&S.farms>=1){seen.farm=1;modal('🌾 The first farms','Around 9500 BCE, people bet on planting wild grains instead of just gathering them. Farming is <i>harder</i> than foraging — but it feeds far more people from the same land. There is no going back.');}
  if(!seen.surplus&&S.surplus>=4){seen.surplus=1;modal('📦 Surplus!','Stored extra food is stored <i>freedom</i>. For the first time, not everyone has to chase the next meal — and a settlement can start to grow.');}
  if(!seen.village&&S.people>=16){seen.village=1;S.era=Math.max(S.era,1);modal('🏘️ A village forms','People settle permanently to guard the harvest. The wanderer becomes the villager — the basic unit of every society to come.');}
  if(!seen.spec&&S.spec>=1){seen.spec=1;modal('👤 Your first specialist','Surplus frees someone from farming — a potter, a priest, a scribe. This division of labour is the engine behind every technology in history.');}
  if(!seen.city&&isCity()){seen.city=1;S.era=Math.max(S.era,3);modal('🏙️ A city rises','Like Uruk in Sumer (~3500 BCE), thousands now live together. A ziggurat climbs above your people. Around such cities appeared the wheel, the plough, and the king.');}
  if(!S.over&&S.knowledge>=18&&isCity()){S.over=true;S.era=4;win();}
  sync();
}
function win(){modal('📜 Writing is born — you did it','Your scribes press wedge-marks into wet clay: <b>cuneiform</b>. Knowledge can finally be stored outside a human skull and outlive its keepers. This is the moment <i>history itself</i> begins.<br><br>From a wandering band to a writing civilization — in '+S.season+' seasons.');}

function sync(){
  el('r_p').textContent=S.people;el('r_cap').textContent=S.cap;el('r_s').textContent=Math.floor(S.surplus);
  el('r_f').textContent=S.farms;el('r_k').textContent=Math.floor(S.knowledge);el('r_sea').textContent=S.season;
  if(!isCity()&&S.farms>0&&S.era<1)S.era=1; if(S.people>=24&&S.houses>=4&&S.era<3)S.era=3;
  el('era').textContent=ERAS[S.era];
  // grow huts
  const want=S.houses+2;while(huts.length<want)huts.push(hutAt(huts.length));
  zig.visible=isCity();
  // people dots (visual cap)
  const vis=Math.min(S.people,48);while(ppl.length<vis)addPerson();while(ppl.length>vis){scene.remove(ppl.pop());}
  // fields
  while(fields.children.length<Math.min(S.farms,14)){const i=fields.children.length;const f=new THREE.Mesh(new THREE.PlaneGeometry(16,9),new THREE.MeshStandardMaterial({color:0x7a6a2e,roughness:1}));f.rotation.x=-Math.PI/2;f.position.set(-90+(i%5)*20,0.2,60+Math.floor(i/5)*14);fields.add(f);}
  // hint
  let h='';
  if(S.farms===0)h='🌱 Foraging barely feeds you. Tap 🌾 Farm to plant crops and grow.';
  else if(S.surplus<5&&S.houses<4)h='Keep farming to build a 📦 surplus, then 🏠 Build homes to grow your people.';
  else if(!isCity())h='Grow toward a city: more 👥 people and at least 4 🏠 homes.';
  else if(S.knowledge<18)h='You are a city! Free 👤 specialists — only scholars can invent writing (📜 '+Math.floor(S.knowledge)+'/18).';
  el('hint').textContent=h;
  const dis=S.over;['b_forage','b_farm','b_build','b_spec'].forEach(id=>el(id).disabled=dis&&!(id==='b_reset'));
}

el('b_forage').onclick=forage;el('b_farm').onclick=farm;el('b_build').onclick=build;el('b_spec').onclick=specialist;
for(let i=0;i<3;i++)huts.push(hutAt(i)); for(let i=0;i<10;i++)addPerson();
sync();
modal('🏛️ Dawn of Civilization','You lead a small band of foragers by a river, ~10,000 BCE. Your goal: grow them into the first writing civilization.<br><br>🌿 forage to survive · 🌾 farm to grow · 🏠 build to expand · 👤 free specialists to reach 📜 <b>writing</b>.');

// ---------- render ----------
let t0=performance.now();
function loop(now){const dt=Math.min((now-t0)/1000,0.05);t0=now;
  for(const m of huts)if(m.scale.x<1)m.scale.setScalar(Math.min(1,m.scale.x+dt*2));
  if(zig.visible&&zig.scale.x<1)zig.scale.setScalar(Math.min(1,zig.scale.x+dt*1.2));
  for(const p of ppl){p.userData.t+=dt;if(p.userData.t>2.5){p.userData.t=0;const a=Math.random()*6.28,r=Math.random()*48;p.userData.tx=Math.cos(a)*r;p.userData.tz=Math.sin(a)*r*0.7-6;}
    p.position.x+=(p.userData.tx-p.position.x)*dt*0.6;p.position.z+=(p.userData.tz-p.position.z)*dt*0.6;p.position.y=1.5+Math.sin(p.userData.t*4)*0.4;}
  const a=now*0.00008;camera.position.set(Math.sin(a)*205,160,Math.cos(a)*205);camera.lookAt(0,8,0);
  renderer.render(scene,camera);requestAnimationFrame(loop);
}
requestAnimationFrame(loop);
})();
"""

REGISTRY = {
    "game-orbit": (HEAD, GAME_JS),
    "game-civilization": (CIV_HEAD, CIV_JS),
}


def build() -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    three = ensure_three()
    for gid, (head, js) in REGISTRY.items():
        html = head + "<script>" + three + "</script>\n<script>" + js + "</script>\n" + TAIL
        (OUT / f"{gid}.html").write_text(html, encoding="utf-8")
    manifest = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "games": [
            {"id": g["id"], "title": g["title"], "emoji": g["emoji"],
             "blurb": g["blurb"], "accent": g["accent"], "url": f"/output/learn/{g['id']}.html"}
            for g in GAMES
        ],
    }
    (OUT / "games.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="LifeOS playable learning games")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("build", help="Build game packets into output/learn/")
    args = parser.parse_args()
    if args.cmd == "build":
        print(json.dumps(build(), indent=2))
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
