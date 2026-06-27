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
        "id": "game-orbit",
        "emoji": "🪐",
        "accent": "#6cc6ff",
        "title": "Orbit",
        "blurb": "Fling a probe around a star and feel how gravity really works — "
                 "too slow you fall in, too fast you escape, just right you orbit.",
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


def build() -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    three = ensure_three()
    html = (
        HEAD
        + "<script>" + three + "</script>\n"
        + "<script>" + GAME_JS + "</script>\n"
        + TAIL
    )
    (OUT / "game-orbit.html").write_text(html, encoding="utf-8")
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
