#!/usr/bin/env python3
"""LifeOS learning-game *system*.

The opposite of a bespoke game-per-topic: a small set of reusable game *engines*
(mechanics) driven entirely by a JSON content spec, wrapped in a shared "game
shell" (score, streak combo, lives, timer, ranks, juice) so any subject becomes
a real game. A lesson emits a spec; this turns it into a self-contained, offline
playable packet.

This module ships reusable engines:
- `classify`: discriminate items into categories under time pressure.
- `runner`: steer into the right lane before the prompt crosses the line.
- `strategy`: solve a turn-based resource puzzle with meters and tradeoffs.

Both render from pure data. Adding a subject = adding a spec, not writing a game.

Build:  python tools/lifeos_arcade.py build
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
    """Return inlined Three.js source, downloading it once if missing."""
    if not THREE_JS.exists():
        THREE_JS.parent.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(THREE_CDN, headers={"User-Agent": "LifeOS/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            THREE_JS.write_bytes(resp.read())
    return THREE_JS.read_text(encoding="utf-8")


# --------------------------------------------------------------------------- #
# Content specs. Each is pure data — no game code. A different subject is just a
# different spec; the engine below is identical for all of them.
# --------------------------------------------------------------------------- #
DRILLS: list[dict] = [
    {
        "id": "drill-quantum",
        "emoji": "⚛️",
        "accent": "#b06bf0",
        "mechanic": "classify",
        "title": "Quantum Zoo",
        "subtitle": "Snap-judge each particle: matter or force-carrier?",
        "categories": [
            {"name": "Fermion", "tag": "matter"},
            {"name": "Boson", "tag": "force"},
        ],
        "items": [
            {"label": "Electron", "cat": 0, "why": "Spin-½ building block of matter → fermion."},
            {"label": "Photon", "cat": 1, "why": "Carries the electromagnetic force → boson."},
            {"label": "Up quark", "cat": 0, "why": "Makes up protons & neutrons → matter → fermion."},
            {"label": "Gluon", "cat": 1, "why": "Carries the strong force binding quarks → boson."},
            {"label": "Neutrino", "cat": 0, "why": "Spin-½ lepton of matter → fermion."},
            {"label": "Higgs", "cat": 1, "why": "Spin-0 force-field excitation → boson."},
            {"label": "W boson", "cat": 1, "why": "Carries the weak force → boson (it's in the name)."},
            {"label": "Muon", "cat": 0, "why": "A heavy cousin of the electron → fermion."},
        ],
        "teach": "Fermions are matter (spin-½, and no two can share a state — the Pauli exclusion "
                 "principle is why atoms take up space). Bosons carry forces (integer spin, and they "
                 "love to pile into the same state — that's how lasers work).",
        "source": ("Standard Model — Wikipedia", "https://en.wikipedia.org/wiki/Standard_Model"),
    },
    {
        "id": "drill-primes",
        "emoji": "🔢",
        "accent": "#46d17a",
        "mechanic": "classify",
        "title": "Prime Time",
        "subtitle": "Fast: is the number prime, or composite?",
        "categories": [
            {"name": "Prime", "tag": "1 & itself only"},
            {"name": "Composite", "tag": "has other factors"},
        ],
        "items": [
            {"label": "7", "cat": 0, "why": "Only 1×7 — prime."},
            {"label": "21", "cat": 1, "why": "3 × 7 — composite."},
            {"label": "13", "cat": 0, "why": "No factors but 1 and 13 — prime."},
            {"label": "51", "cat": 1, "why": "3 × 17 (sneaky!) — composite."},
            {"label": "2", "cat": 0, "why": "The only even prime."},
            {"label": "9", "cat": 1, "why": "3 × 3 — composite."},
            {"label": "29", "cat": 0, "why": "Prime."},
            {"label": "91", "cat": 1, "why": "7 × 13 (the classic trap) — composite."},
            {"label": "17", "cat": 0, "why": "Prime."},
            {"label": "27", "cat": 1, "why": "3 × 9 — composite."},
        ],
        "teach": "A prime has exactly two divisors: 1 and itself. Composites have more. Tricks: even "
                 "numbers (>2) and anything ending in 0 or 5 (>5) are composite; for the rest, test "
                 "divisibility by small primes 3, 7, 11, 13.",
        "source": ("Prime number — Wikipedia", "https://en.wikipedia.org/wiki/Prime_number"),
    },
    {
        "id": "drill-sleep-stages",
        "emoji": "😴",
        "accent": "#7c6bf0",
        "mechanic": "runner",
        "title": "Sleep Stage Sprint",
        "subtitle": "Steer each sleep fact into the right lane before it hits you.",
        "pairs": "why-we-sleep",
        "categories": [
            {"name": "Light", "tag": "N1/N2"},
            {"name": "Deep", "tag": "N3"},
            {"name": "REM", "tag": "dream"},
        ],
        "items": [
            {"label": "Sleep spindles", "cat": 0, "why": "Spindles are bursts most associated with N2 light sleep."},
            {"label": "Easy to wake", "cat": 0, "why": "N1/N2 are lighter stages; you can still be woken fairly easily."},
            {"label": "Slow waves", "cat": 1, "why": "Deep N3 sleep is dominated by slow delta waves."},
            {"label": "Physical repair", "cat": 1, "why": "Deep sleep is when growth hormone and tissue repair are strongest."},
            {"label": "Vivid dreams", "cat": 2, "why": "The memorable, cinematic dreams mostly happen in REM sleep."},
            {"label": "Muscle paralysis", "cat": 2, "why": "REM turns most muscles off so you do not act out dreams."},
            {"label": "Memory replay", "cat": 1, "why": "Deep sleep helps replay and stabilize new memories."},
            {"label": "Brain activation", "cat": 2, "why": "REM looks strangely wake-like in the brain while the body stays still."},
        ],
        "teach": "Sleep is not one state. Light sleep eases you down and stabilizes the night, deep "
                 "slow-wave sleep repairs the body and consolidates memory, and REM sleep runs a "
                 "high-activity dream mode while your muscles are mostly offline.",
        "source": ("Sleep — Wikipedia", "https://en.wikipedia.org/wiki/Sleep"),
    },
    {
        "id": "drill-compounding-engine",
        "emoji": "📈",
        "accent": "#46d17a",
        "mechanic": "strategy",
        "title": "Compounding Engine",
        "subtitle": "Build a tiny system that gets stronger without burning out.",
        "pairs": "power-of-compounding",
        "turns": 8,
        "win": "Reach 85 skill while keeping at least 20 energy.",
        "meters": [
            {"id": "skill", "name": "Skill", "value": 12, "min": 0, "max": 100, "target": 85},
            {"id": "energy", "name": "Energy", "value": 68, "min": 0, "max": 100, "target": 20},
            {"id": "momentum", "name": "Momentum", "value": 0, "min": 0, "max": 40, "target": 24, "required": False},
        ],
        "rules": [
            {
                "type": "compound",
                "from": "momentum",
                "to": "skill",
                "scale": 0.18,
                "label": "Momentum compounds into skill",
            },
            {"type": "drift", "meter": "energy", "amount": 5, "label": "Rest restores energy"},
        ],
        "actions": [
            {
                "name": "Tiny daily rep",
                "icon": "•",
                "effects": {"skill": 6, "energy": -7, "momentum": 5},
                "why": "Small repeats look weak early, but they build the meter that compounds later.",
            },
            {
                "name": "Deep practice",
                "icon": "◆",
                "effects": {"skill": 13, "energy": -18, "momentum": 2},
                "why": "High-quality effort moves skill fast, but it needs energy behind it.",
            },
            {
                "name": "Review mistakes",
                "icon": "↻",
                "effects": {"skill": 4, "energy": -9, "momentum": 7},
                "why": "Feedback loops multiply future reps. Boring, but powerful.",
            },
            {
                "name": "Sleep early",
                "icon": "Z",
                "effects": {"energy": 18, "momentum": 1},
                "why": "Recovery is not a pause in the system; it keeps the system alive.",
            },
            {
                "name": "All-nighter",
                "icon": "!",
                "effects": {"skill": 18, "energy": -36, "momentum": -8},
                "why": "Cramming gives a visible jump and damages the machine that would compound.",
            },
            {
                "name": "Scroll break",
                "icon": "~",
                "effects": {"energy": 7, "skill": -2, "momentum": -6},
                "why": "It feels like recovery, but it breaks the streak that makes the curve bend.",
            },
        ],
        "teach": "Compounding is not just growth. It is growth fed back into the next round. The puzzle "
                 "is to protect the inputs that compound: consistency, feedback, and enough recovery "
                 "to keep playing.",
        "source": ("Compound interest — Wikipedia", "https://en.wikipedia.org/wiki/Compound_interest"),
    },
    {
        "id": "arena-civilization",
        "emoji": "🏛️",
        "accent": "#e0a851",
        "mechanic": "arena3d",
        "template": "civ-board",
        "title": "Civilization Builder 3D",
        "subtitle": "Build the chain from foragers to writing on a living strategy board.",
        "pairs": "story-of-civilization",
        "objective": {
            "type": "sequence",
            "zone": "forge",
            "prompt": "Deliver the artifacts to the forge in the order that makes civilization possible.",
            "sequence": ["foraging", "farming", "surplus", "specialists", "city", "writing"],
        },
        "zones": [
            {"id": "forge", "name": "Civilization Forge", "color": "#e0a851", "x": 0, "z": 0, "radius": 34},
        ],
        "artifacts": [
            {"id": "foraging", "label": "Foraging", "info": "Small mobile bands live from wild food.", "x": -110, "z": -70, "color": "#a7d982"},
            {"id": "farming", "label": "Farming", "info": "Planting grains fixes people to a place.", "x": 118, "z": -82, "color": "#d1c45d"},
            {"id": "surplus", "label": "Surplus", "info": "Stored food creates slack beyond survival.", "x": -72, "z": 120, "color": "#f0c884"},
            {"id": "specialists", "label": "Specialists", "info": "Surplus frees potters, priests, soldiers, and scribes.", "x": 152, "z": 74, "color": "#d89b62"},
            {"id": "city", "label": "City", "info": "Dense settlement makes institutions and trade possible.", "x": -165, "z": 38, "color": "#b8a078"},
            {"id": "writing", "label": "Writing", "info": "External memory turns events into history.", "x": 52, "z": 165, "color": "#fff0bf"},
        ],
        "teach": "Civilization is a chain, not a pile of facts: farming enables surplus, surplus enables "
                 "specialists, specialists make cities and writing possible.",
        "source": ("Will Durant — Our Oriental Heritage", "https://archive.org/details/in.ernet.dli.2015.275128"),
    },
    {
        "id": "arena-quantum-fields",
        "emoji": "⚛️",
        "accent": "#b06bf0",
        "mechanic": "arena3d",
        "template": "quantum-lab",
        "title": "Quantum Field Sorter 3D",
        "subtitle": "Carry particles into the right field: matter or force.",
        "objective": {
            "type": "zones",
            "prompt": "Sort every particle into the field it belongs to.",
        },
        "zones": [
            {"id": "matter", "name": "Matter / Fermions", "color": "#7dffb0", "x": -90, "z": 0, "radius": 32},
            {"id": "force", "name": "Force / Bosons", "color": "#b06bf0", "x": 90, "z": 0, "radius": 32},
        ],
        "artifacts": [
            {"id": "electron", "label": "Electron", "zone": "matter", "info": "A lepton: matter with spin 1/2.", "x": -150, "z": -105, "color": "#7dffb0"},
            {"id": "quark", "label": "Quark", "zone": "matter", "info": "Matter constituent inside protons and neutrons.", "x": 0, "z": -145, "color": "#7dffb0"},
            {"id": "neutrino", "label": "Neutrino", "zone": "matter", "info": "Tiny neutral lepton: still matter.", "x": 145, "z": -100, "color": "#7dffb0"},
            {"id": "photon", "label": "Photon", "zone": "force", "info": "Carrier of electromagnetic force.", "x": -150, "z": 110, "color": "#b06bf0"},
            {"id": "gluon", "label": "Gluon", "zone": "force", "info": "Carrier of the strong force.", "x": 0, "z": 150, "color": "#b06bf0"},
            {"id": "higgs", "label": "Higgs", "zone": "force", "info": "Boson excitation of the Higgs field.", "x": 150, "z": 105, "color": "#b06bf0"},
        ],
        "teach": "The Standard Model becomes playable when you treat the world as fields: fermions are "
                 "matter excitations; bosons are force-field messengers.",
        "source": ("Standard Model — Wikipedia", "https://en.wikipedia.org/wiki/Standard_Model"),
    },
    {
        "id": "arena-art-movements",
        "emoji": "🎨",
        "accent": "#ff6b9b",
        "mechanic": "arena3d",
        "template": "gallery-studio",
        "title": "Gallery Curator 3D",
        "subtitle": "Curate clues into the right art movement galleries.",
        "objective": {
            "type": "zones",
            "prompt": "Carry each visual clue into the gallery that explains it.",
        },
        "zones": [
            {"id": "impressionism", "name": "Impressionism", "color": "#ffd36c", "x": -120, "z": -20, "radius": 30},
            {"id": "cubism", "name": "Cubism", "color": "#6cc6ff", "x": 0, "z": 86, "radius": 30},
            {"id": "surrealism", "name": "Surrealism", "color": "#ff6b9b", "x": 120, "z": -20, "radius": 30},
        ],
        "artifacts": [
            {"id": "plein-air", "label": "Open air light", "zone": "impressionism", "info": "Impressionists chased changing light outdoors.", "x": -170, "z": -130, "color": "#ffd36c"},
            {"id": "broken-brush", "label": "Broken brushwork", "zone": "impressionism", "info": "Visible strokes make the eye mix color.", "x": -45, "z": -150, "color": "#ffd36c"},
            {"id": "multiple-views", "label": "Many angles", "zone": "cubism", "info": "Cubism fractures objects into simultaneous viewpoints.", "x": 72, "z": -150, "color": "#6cc6ff"},
            {"id": "geometry", "label": "Geometric planes", "zone": "cubism", "info": "Forms are rebuilt as hard-edged planes.", "x": 170, "z": -120, "color": "#6cc6ff"},
            {"id": "dream-logic", "label": "Dream logic", "zone": "surrealism", "info": "Surrealism makes the unconscious visible.", "x": -100, "z": 160, "color": "#ff6b9b"},
            {"id": "strange-objects", "label": "Impossible objects", "zone": "surrealism", "info": "Ordinary things become uncanny symbols.", "x": 120, "z": 160, "color": "#ff6b9b"},
        ],
        "teach": "Art movements are not names to memorize; they are rule systems for seeing. If you can "
                 "sort visual clues, you understand the movement.",
        "source": ("Art movement — Wikipedia", "https://en.wikipedia.org/wiki/Art_movement"),
    },
]


# --------------------------------------------------------------------------- #
# Engine + shared game shell. One implementation, all specs.
# --------------------------------------------------------------------------- #
SHELL_CSS = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{height:100%;background:#070a12;color:#eaf2ff;font-family:system-ui,-apple-system,sans-serif;overflow:hidden;-webkit-text-size-adjust:100%}
.wrap{max-width:560px;margin:0 auto;height:100%;display:flex;flex-direction:column;padding:14px 16px 22px}
.hud{display:flex;justify-content:space-between;align-items:center;font:700 14px/1 system-ui}
.hud .lives{letter-spacing:2px}
.hud b{color:var(--c)}
.bar{height:8px;border-radius:6px;background:#16203a;margin:12px 0 0;overflow:hidden}
.bar>i{display:block;height:100%;width:100%;background:var(--c);transition:width .08s linear}
.kicker{font:700 12px/1 system-ui;letter-spacing:.14em;text-transform:uppercase;color:var(--c);margin:18px 0 4px}
.q{font-size:17px;color:#9fb6dd;margin-bottom:6px}
.stage{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:10px}
.item{font:800 56px/1.05 Georgia,serif;text-align:center;padding:20px 26px;border-radius:22px;background:#0e1830;border:1px solid #1f2f52;min-width:60%;text-align:center;transition:transform .12s}
.item.good{animation:pop .3s}
.item.bad{animation:shake .3s}
@keyframes pop{0%{transform:scale(1)}40%{transform:scale(1.08)}100%{transform:scale(1)}}
@keyframes shake{0%,100%{transform:translateX(0)}25%{transform:translateX(-9px)}75%{transform:translateX(9px)}}
.why{min-height:22px;font:600 15px/1.35 system-ui;color:#9fb6dd;text-align:center;opacity:0;transition:opacity .2s}
.why.show{opacity:1}
.cats{display:flex;gap:12px;margin-top:6px}
.cat{flex:1;border:2px solid #24345c;background:#0e1830;color:#eaf2ff;border-radius:16px;padding:16px 10px;font:800 18px/1.1 system-ui;cursor:pointer;transition:.1s}
.cat small{display:block;font:600 12px system-ui;color:#7e96c4;margin-top:4px}
.cat:active{transform:scale(.96)}
.cat.right{border-color:#46d17a;background:#0f2a1c}
.cat.wrong{border-color:#ff6b6b;background:#2a1115}
.pop{position:fixed;left:50%;top:38%;transform:translateX(-50%);font:800 30px system-ui;color:var(--c);pointer-events:none;opacity:0}
.pop.go{animation:rise .7s ease-out}
@keyframes rise{0%{opacity:1;transform:translate(-50%,0)}100%{opacity:0;transform:translate(-50%,-60px)}}
.over{position:fixed;inset:0;display:none;align-items:center;justify-content:center;background:rgba(5,7,14,.86);padding:26px;z-index:9}
.over.show{display:flex}
.card{max-width:420px;background:#0e1426;border:1px solid #25345c;border-radius:22px;padding:26px;text-align:center}
.card .rank{font:800 46px/1 system-ui;color:var(--c)}
.card h2{font:800 22px system-ui;margin:6px 0 4px}
.card .sc{font:700 16px system-ui;color:#9fb6dd;margin-bottom:14px}
.card .teach{font:500 15px/1.5 system-ui;color:#cfe0ff;text-align:left;background:#0a1020;border:1px solid #1f2f52;border-radius:14px;padding:14px;margin-bottom:16px}
.card a{color:var(--c)}
.card button{font:800 16px system-ui;color:#04140b;background:var(--c);border:none;border-radius:13px;padding:13px 20px;cursor:pointer;width:100%}
"""

ENGINE_JS = r"""
(function(){
const $=s=>document.querySelector(s);
const cats=SPEC.categories, items=SPEC.items.slice();
const PER=6; // seconds per item
let order=items.map((_,i)=>i);
for(let i=order.length-1;i>0;i--){const j=(Math.random()*(i+1))|0;[order[i],order[j]]=[order[j],order[i]];}
let idx=0,score=0,streak=0,best=0,lives=3,locked=false,t0=0,raf=0;

// build category buttons once
const catWrap=$('.cats');
cats.forEach((c,k)=>{const b=document.createElement('button');b.className='cat';b.dataset.k=k;
  b.innerHTML=c.name+(c.tag?('<small>'+c.tag+'</small>'):'');b.addEventListener('click',()=>answer(k));catWrap.appendChild(b);});

function hud(){
  $('.score').textContent=score;
  $('.streak').textContent=streak>1?('🔥x'+streak):'';
  $('.lives').textContent='❤️'.repeat(lives)+'🤍'.repeat(Math.max(0,3-lives));
  $('.prog').textContent=Math.min(idx+1,items.length)+'/'+items.length;
}
function clearCats(){document.querySelectorAll('.cat').forEach(b=>{b.classList.remove('right','wrong');});}
function show(){
  if(idx>=items.length)return finish(true);
  locked=false;clearCats();const it=items[order[idx]];
  const el=$('.item');el.textContent=it.label;el.className='item';
  $('.why').classList.remove('show');hud();
  t0=performance.now();tick();
}
function tick(){const e=(performance.now()-t0)/1000,left=1-e/PER;
  $('.bar>i').style.width=(Math.max(0,left)*100)+'%';
  if(left<=0){answer(-1);return;}
  raf=requestAnimationFrame(tick);
}
function pop(txt){const p=$('.pop');p.textContent=txt;p.classList.remove('go');void p.offsetWidth;p.classList.add('go');}
function answer(k){
  if(locked)return;locked=true;cancelAnimationFrame(raf);
  const it=items[order[idx]],correct=(k===it.cat);
  document.querySelectorAll('.cat').forEach(b=>{const kk=+b.dataset.k;
    if(kk===it.cat)b.classList.add('right'); else if(kk===k)b.classList.add('wrong');});
  const el=$('.item');
  if(correct){streak++;best=Math.max(best,streak);const pts=Math.round(100*(1+(streak-1)*0.5));score+=pts;el.classList.add('good');pop('+'+pts);}
  else{streak=0;lives--;el.classList.add('bad');pop(k===-1?'⏱':'✗');}
  $('.why').textContent=it.why;$('.why').classList.add('show');hud();
  if(lives<=0){setTimeout(()=>finish(false),1000);return;}
  idx++;setTimeout(show,1050);
}
function finish(won){
  cancelAnimationFrame(raf);
  const done=idx, max=items.length*100*1; // rough cap for ranking
  const pct=score/(items.length*150);
  const rank=!won?'☠️':pct>0.85?'S':pct>0.6?'A':pct>0.35?'B':'C';
  $('.rank').textContent=won?rank:'☠️';
  $('.otitle').textContent=won?'Cleared!':'Out of lives';
  $('.osc').innerHTML='Score <b>'+score+'</b> · best streak 🔥'+best;
  const t=SPEC.teach+(SPEC.source?(" <a href='"+SPEC.source[1]+"' target='_blank' rel='noopener'>"+SPEC.source[0]+"</a>"):"");
  $('.teach').innerHTML=t;
  $('.over').classList.add('show');
}
$('.retry').addEventListener('click',()=>{
  for(let i=order.length-1;i>0;i--){const j=(Math.random()*(i+1))|0;[order[i],order[j]]=[order[j],order[i]];}
  idx=0;score=0;streak=0;lives=3;$('.over').classList.remove('show');show();
});
$('.qtitle').textContent=SPEC.title;$('.qsub').textContent=SPEC.subtitle;
show();
})();
"""


def classify_head(spec: dict) -> str:
    return f"""<!doctype html><html lang='en'><head>
<meta charset='utf-8'>
<meta name='viewport' content='width=device-width,initial-scale=1,viewport-fit=cover,user-scalable=no'>
<meta name='color-scheme' content='dark'>
<title>{spec['title']} — LifeOS drill</title>
<style>{SHELL_CSS}
:root{{--c:{spec['accent']}}}</style></head>
<body><div class='wrap'>
<div class='hud'><span>⭐ <b class='score'>0</b> <span class='streak'></span></span>
<span class='prog'>0/0</span><span class='lives'>❤️❤️❤️</span></div>
<div class='bar'><i></i></div>
<div class='kicker'>{spec['emoji']} <span class='qtitle'></span></div>
<div class='q qsub'></div>
<div class='stage'><div class='item'></div><div class='why'></div></div>
<div class='cats'></div>
</div>
<div class='pop'></div>
<div class='over'><div class='card'><div class='rank'></div><h2 class='otitle'></h2>
<div class='osc'></div><div class='teach'></div><button class='retry'>Play again</button></div></div>
"""


# ---- Mechanic: "runner" — a fast lane game (action, not a quiz) ------------- #
RUNNER_CSS = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{height:100%;overflow:hidden;background:#070a12;color:#eaf2ff;font-family:system-ui,-apple-system,sans-serif;touch-action:none;-webkit-text-size-adjust:100%}
#c{display:block}
.over{position:fixed;inset:0;display:none;align-items:center;justify-content:center;background:rgba(5,7,14,.86);padding:26px;z-index:9}
.over.show{display:flex}
.card{max-width:420px;background:#0e1426;border:1px solid #25345c;border-radius:22px;padding:26px;text-align:center}
.card .rank{font:800 46px/1 system-ui;color:var(--c)}
.card h2{font:800 22px system-ui;margin:6px 0 4px}
.card .osc{font:700 16px system-ui;color:#9fb6dd;margin-bottom:14px}
.card .teach{font:500 15px/1.5 system-ui;color:#cfe0ff;text-align:left;background:#0a1020;border:1px solid #1f2f52;border-radius:14px;padding:14px;margin-bottom:16px}
.card a{color:var(--c)}
.card button{font:800 16px system-ui;color:#04140b;background:var(--c);border:none;border-radius:13px;padding:13px 20px;cursor:pointer;width:100%}
"""

RUNNER_JS = r"""
(function(){
const cv=document.getElementById('c'),ctx=cv.getContext('2d');
let W,H,DPR;
function resize(){DPR=Math.min(window.devicePixelRatio||1,2);W=innerWidth;H=innerHeight;cv.width=W*DPR;cv.height=H*DPR;cv.style.width=W+'px';cv.style.height=H+'px';ctx.setTransform(DPR,0,0,DPR,0,0);}
addEventListener('resize',resize);resize();
const ACC=SPEC.accent||'#6cc6ff';
const cats=SPEC.categories.slice(0,3), lanes=cats.length, items=SPEC.items.slice();
function shuffle(a){for(let i=a.length-1;i>0;i--){const j=(Math.random()*(i+1))|0;[a[i],a[j]]=[a[j],a[i]];}return a;}
let order=shuffle(items.map((_,i)=>i)),ci=0,cur=null;
let lane=Math.floor(lanes/2),px=0,playerY=0;
let score=0,combo=0,best=0,lives=3,fallDur=2.4,beatY=0,judging=false,over=false;
let why='',whyT=0,shakeT=0,flashT=0,flashC='#46d17a',parts=[],last=performance.now();
let TOP=70;
function laneC(i){return (i+0.5)*(W/lanes);}
function next(){if(ci>=order.length){order=shuffle(order);ci=0;}cur=items[order[ci++]];beatY=TOP;judging=false;}
function burst(c,n){for(let i=0;i<n;i++){const a=Math.random()*6.28,s=70+Math.random()*180;parts.push({x:px,y:playerY,vx:Math.cos(a)*s,vy:Math.sin(a)*s,l:1,c:c});}}
function judge(){judging=true;const ok=(lane===cur.cat);
 if(ok){combo++;best=Math.max(best,combo);const pts=Math.round(100*(1+(combo-1)*0.5));score+=pts;burst('#46d17a',18);flashC='#46d17a';flashT=.25;fallDur=Math.max(0.95,fallDur-0.08);why='';whyT=0;}
 else{combo=0;lives--;burst('#ff6b6b',18);flashC='#ff6b6b';flashT=.3;shakeT=.4;why=cur.label+' — '+cur.why;whyT=3;}
 if(lives<=0){return gameOver();}
 next();
}
function gameOver(){over=true;const pct=score/Math.max(1,items.length*150);
 document.querySelector('.rank').textContent=pct>0.8?'S':pct>0.5?'A':pct>0.25?'B':'C';
 document.querySelector('.otitle').textContent='Run over';
 document.querySelector('.osc').innerHTML='Score <b>'+score+'</b> · best streak '+best;
 document.querySelector('.teach').innerHTML=SPEC.teach+(SPEC.source?(" <a href='"+SPEC.source[1]+"' target='_blank' rel='noopener'>"+SPEC.source[0]+"</a>"):'');
 document.querySelector('.over').classList.add('show');}
function move(d){if(over)return;lane=Math.max(0,Math.min(lanes-1,lane+d));}
addEventListener('keydown',e=>{if(e.key==='ArrowLeft'||e.key==='a')move(-1);else if(e.key==='ArrowRight'||e.key==='d')move(1);});
cv.addEventListener('pointerdown',e=>move(e.clientX<W/2?-1:1));
document.querySelector('.retry').addEventListener('click',()=>{score=0;combo=0;lives=3;fallDur=2.4;over=false;parts=[];order=shuffle(order);ci=0;document.querySelector('.over').classList.remove('show');next();});
function wrap(t,x,y,mw,lh){const ws=t.split(' ');let ln='',yy=y;for(const w of ws){const tt=ln+w+' ';if(ctx.measureText(tt).width>mw&&ln){ctx.fillText(ln,x,yy);ln=w+' ';yy+=lh;}else ln=tt;}ctx.fillText(ln,x,yy);}
next();
function frame(now){const dt=Math.min((now-last)/1000,.05);last=now;
 TOP=Math.max(64,H*0.16);playerY=H*0.8;
 if(!over){
   px+=(laneC(lane)-px)*Math.min(1,dt*13);
   beatY+=(playerY-TOP)/fallDur*dt;
   if(!judging&&beatY>=playerY)judge();
   if(whyT>0)whyT-=dt;if(shakeT>0)shakeT-=dt;if(flashT>0)flashT-=dt;
   for(const p of parts){p.x+=p.vx*dt;p.y+=p.vy*dt;p.vy+=220*dt;p.l-=dt*1.6;}parts=parts.filter(p=>p.l>0);
 }
 draw();requestAnimationFrame(frame);
}
function draw(){
 ctx.save();const sh=shakeT>0?(Math.random()-.5)*12:0;ctx.translate(sh,0);
 ctx.fillStyle='#070a12';ctx.fillRect(-20,0,W+40,H);
 for(let i=0;i<lanes;i++){
   if(i>0){ctx.strokeStyle='#16203a';ctx.beginPath();ctx.moveTo(i*W/lanes,0);ctx.lineTo(i*W/lanes,H);ctx.stroke();}
   ctx.fillStyle='#0e1830';ctx.fillRect(i*W/lanes+6,TOP-32,W/lanes-12,26);
   ctx.fillStyle='#9fb6dd';ctx.font='700 14px system-ui';ctx.textAlign='center';ctx.fillText(cats[i].name,laneC(i),TOP-13);
 }
 ctx.strokeStyle='#24345c';ctx.beginPath();ctx.moveTo(0,TOP);ctx.lineTo(W,TOP);ctx.stroke();
 if(cur){ctx.fillStyle='#eaf2ff';ctx.font='800 '+Math.min(44,W*0.094)+'px Georgia,serif';ctx.textAlign='center';ctx.fillText(cur.label,W/2,TOP*0.66);}
 ctx.strokeStyle=ACC;ctx.lineWidth=4;ctx.globalAlpha=.9;ctx.beginPath();ctx.moveTo(0,beatY);ctx.lineTo(W,beatY);ctx.stroke();ctx.globalAlpha=1;ctx.lineWidth=1;
 const py=H*0.8;
 if(flashT>0){ctx.globalAlpha=flashT*1.4;ctx.fillStyle=flashC;ctx.fillRect(-20,0,W+40,H);ctx.globalAlpha=1;}
 ctx.fillStyle=ACC;ctx.shadowColor=ACC;ctx.shadowBlur=26;ctx.beginPath();ctx.moveTo(px,py-20);ctx.lineTo(px-15,py+14);ctx.lineTo(px+15,py+14);ctx.closePath();ctx.fill();ctx.shadowBlur=0;
 for(const p of parts){ctx.globalAlpha=Math.max(0,p.l);ctx.fillStyle=p.c;ctx.fillRect(p.x-3,p.y-3,6,6);}ctx.globalAlpha=1;
 ctx.fillStyle='#eaf2ff';ctx.font='800 20px system-ui';ctx.textAlign='left';ctx.fillText('⭐ '+score,16,34);
 if(combo>1){ctx.fillStyle=ACC;ctx.font='800 17px system-ui';ctx.fillText('🔥 x'+combo,16,58);}
 ctx.textAlign='right';ctx.fillStyle='#ff6b6b';ctx.font='800 20px system-ui';ctx.fillText('♥'.repeat(Math.max(0,lives)),W-14,34);
 if(whyT>0){ctx.globalAlpha=Math.min(1,whyT);const tw=Math.min(W-24,560);ctx.fillStyle='rgba(18,14,28,.94)';ctx.fillRect(W/2-tw/2,H-92,tw,56);
   ctx.fillStyle='#cfe0ff';ctx.font='600 15px system-ui';ctx.textAlign='center';wrap(why,W/2,H-66,tw-26,18);ctx.globalAlpha=1;}
 ctx.fillStyle='#5a6b8f';ctx.font='600 13px system-ui';ctx.textAlign='center';ctx.fillText('◀ tap / arrows — pick the lane before the line ▶',W/2,H-18);
 ctx.restore();
}
requestAnimationFrame(frame);
})();
"""


def runner_head(spec: dict) -> str:
    return f"""<!doctype html><html lang='en'><head>
<meta charset='utf-8'>
<meta name='viewport' content='width=device-width,initial-scale=1,viewport-fit=cover,user-scalable=no'>
<meta name='color-scheme' content='dark'>
<title>{spec['title']} — LifeOS run</title>
<style>{RUNNER_CSS}
:root{{--c:{spec['accent']}}}</style></head>
<body><canvas id='c'></canvas>
<div class='over'><div class='card'><div class='rank'></div><h2 class='otitle'></h2>
<div class='osc'></div><div class='teach'></div><button class='retry'>Run again</button></div></div>
"""


# ---- Mechanic: "strategy" — a turn-based systems puzzle -------------------- #
STRATEGY_CSS = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{min-height:100%;background:#070a12;color:#eaf2ff;font-family:system-ui,-apple-system,sans-serif;-webkit-text-size-adjust:100%}
body{display:flex;justify-content:center}
.wrap{width:min(940px,100%);min-height:100vh;padding:18px 16px 24px;display:grid;grid-template-columns:minmax(0,1.1fr) minmax(280px,.9fr);gap:16px}
.panel{background:#0d1424;border:1px solid #223153;border-radius:18px;padding:16px}
.hero{grid-column:1/-1;background:linear-gradient(110deg,rgba(70,209,122,.12),#0d1424);border-color:var(--c)}
.kicker{font:800 12px/1 system-ui;letter-spacing:.14em;text-transform:uppercase;color:var(--c)}
h1{font:900 clamp(32px,6vw,58px)/.95 Georgia,serif;margin:8px 0}
.sub{font:600 17px/1.45 system-ui;color:#aebfe0;max-width:720px}
.goal{margin-top:12px;color:#d9e7ff;font:700 15px/1.45 system-ui}
.hud{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;color:#aebfe0;font:800 13px/1 system-ui}
.turn b,.rank b{color:var(--c)}
.meter{margin:12px 0}
.mrow{display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;font:800 14px/1 system-ui}
.mrow .target{color:#8296bf;font-weight:700}
.bar{height:13px;border-radius:99px;background:#18233c;overflow:hidden;border:1px solid #26375d}
.bar i{display:block;height:100%;width:0;background:linear-gradient(90deg,var(--c),#d7ffe8);border-radius:99px;transition:width .25s ease}
.actions{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.act{border:1px solid #2a3a61;background:#101a30;color:#eaf2ff;border-radius:15px;padding:12px;text-align:left;cursor:pointer;min-height:118px;transition:.12s}
.act:hover{border-color:var(--c);transform:translateY(-1px)}
.act:disabled{opacity:.4;cursor:not-allowed;transform:none}
.act .top{display:flex;align-items:center;gap:9px;font:900 15px/1.1 system-ui}
.act .icon{display:grid;place-items:center;width:28px;height:28px;border-radius:9px;background:var(--c);color:#04140b}
.effects{display:flex;flex-wrap:wrap;gap:5px;margin:10px 0}
.eff{font:800 11px/1 system-ui;border-radius:999px;padding:5px 7px;background:#17223a;color:#cddcff}
.eff.pos{color:#afffcf}.eff.neg{color:#ffb4b4}
.why{font:600 12px/1.35 system-ui;color:#9fb6dd}
.log{height:330px;overflow:auto;display:flex;flex-direction:column;gap:8px;padding-right:4px}
.entry{border-left:3px solid var(--c);background:#0a1020;border-radius:12px;padding:10px 11px;color:#cfe0ff;font:600 13px/1.45 system-ui}
.entry b{color:#fff}
.feedback{min-height:46px;margin-top:12px;color:#d9e7ff;font:700 14px/1.4 system-ui}
.feedback.good{color:#afffcf}.feedback.bad{color:#ffb4b4}
.over{position:fixed;inset:0;display:none;align-items:center;justify-content:center;background:rgba(5,7,14,.86);padding:22px;z-index:5}
.over.show{display:flex}
.card{width:min(440px,100%);background:#0e1426;border:1px solid var(--c);border-radius:20px;padding:24px;text-align:center}
.card .grade{font:900 54px/1 system-ui;color:var(--c)}
.card h2{font:900 24px/1.1 system-ui;margin:8px 0}
.card p{font:600 15px/1.5 system-ui;color:#cfe0ff;text-align:left;margin:10px 0}
.card button{font:900 16px system-ui;color:#04140b;background:var(--c);border:none;border-radius:13px;padding:13px 20px;cursor:pointer;width:100%;margin-top:12px}
.source a{color:var(--c)}
@media(max-width:760px){.wrap{display:block}.panel{margin:12px 0}.actions{grid-template-columns:1fr}.log{height:220px}h1{font-size:40px}}
"""

STRATEGY_JS = r"""
(function(){
const $=s=>document.querySelector(s);
const S=SPEC;
const defs={}; S.meters.forEach(m=>defs[m.id]=m);
let meters={},turn=0,done=false,log=[];
function clamp(id,v){const d=defs[id];return Math.max(d.min??0,Math.min(d.max??100,v));}
function reset(){
  meters={}; S.meters.forEach(m=>meters[m.id]=m.value);
  turn=0; done=false; log=[]; $('.over').classList.remove('show'); render();
}
function pct(m){const d=defs[m.id], min=d.min??0, max=d.max??100; return Math.round(((meters[m.id]-min)/(max-min))*100);}
function fmtDelta(id,v){const name=defs[id]?.name||id; return (v>0?'+':'')+v+' '+name;}
function canUse(a){
  for(const [id,delta] of Object.entries(a.effects||{})){
    const d=defs[id]; if(!d) continue;
    if(meters[id]+delta < (d.min??0)) return false;
  }
  return !done && turn < S.turns;
}
function applyRules(){
  const notes=[];
  (S.rules||[]).forEach(r=>{
    if(r.type==='compound'){
      const raw=(meters[r.from]||0)*(r.scale||0);
      const bonus=Math.floor(raw);
      if(bonus>0){meters[r.to]=clamp(r.to,(meters[r.to]||0)+bonus); notes.push((r.label||'Compound bonus')+': +'+bonus+' '+(defs[r.to]?.name||r.to));}
    } else if(r.type==='drift'){
      meters[r.meter]=clamp(r.meter,(meters[r.meter]||0)+(r.amount||0));
      if(r.amount) notes.push((r.label||'Drift')+': '+fmtDelta(r.meter,r.amount));
    }
  });
  return notes;
}
function requiredMeters(){return S.meters.filter(m=>m.required!==false && typeof m.target==='number');}
function won(){
  return requiredMeters().every(m=>meters[m.id]>=m.target);
}
function grade(){
  const req=requiredMeters();
  const targetAvg=req.length?req.reduce((n,m)=>n+Math.min(1,meters[m.id]/m.target),0)/req.length:0;
  const optional=S.meters.filter(m=>m.required===false && typeof m.target==='number');
  const optAvg=optional.length?optional.reduce((n,m)=>n+Math.min(1,meters[m.id]/m.target),0)/optional.length:0;
  const score=targetAvg*.75+optAvg*.25;
  return won()? score>.95?'S':score>.8?'A':'B' : score>.65?'C':'D';
}
function play(i){
  const a=S.actions[i]; if(!canUse(a)){flash('That move would crash a meter below zero.', false); return;}
  Object.entries(a.effects||{}).forEach(([id,delta])=>{meters[id]=clamp(id,(meters[id]||0)+delta);});
  const ruleNotes=applyRules(); turn++;
  log.unshift({turn, name:a.name, why:a.why, effects:Object.entries(a.effects||{}).map(([id,d])=>fmtDelta(id,d)), rules:ruleNotes});
  if(won() || turn>=S.turns){done=true; render(); finish(); return;}
  flash(a.why, true); render();
}
function flash(txt,good){const f=$('.feedback');f.textContent=txt;f.className='feedback '+(good?'good':'bad');}
function renderMeters(){
  $('.meters').innerHTML=S.meters.map(m=>{
    const target=typeof m.target==='number' ? (m.required===false?'stretch ':'target ')+m.target : '';
    return `<div class="meter"><div class="mrow"><span>${m.name}</span><span><b>${meters[m.id]}</b> <span class="target">${target}</span></span></div><div class="bar"><i style="width:${pct(m)}%"></i></div></div>`;
  }).join('');
}
function renderActions(){
  $('.actions').innerHTML=S.actions.map((a,i)=>{
    const eff=Object.entries(a.effects||{}).map(([id,d])=>`<span class="eff ${d>=0?'pos':'neg'}">${fmtDelta(id,d)}</span>`).join('');
    return `<button class="act" data-i="${i}" ${canUse(a)?'':'disabled'}><div class="top"><span class="icon">${a.icon||'>'}</span><span>${a.name}</span></div><div class="effects">${eff}</div><div class="why">${a.why}</div></button>`;
  }).join('');
  document.querySelectorAll('.act').forEach(b=>b.addEventListener('click',()=>play(+b.dataset.i)));
}
function renderLog(){
  $('.log').innerHTML=log.length?log.map(e=>`<div class="entry"><b>Turn ${e.turn}: ${e.name}</b><br>${e.effects.join(' · ')}${e.rules.length?'<br>'+e.rules.join(' · '):''}<br>${e.why}</div>`).join(''):`<div class="entry"><b>Design the system.</b><br>Pick moves that create feedback loops. Fast gains can be traps if they destroy the engine.</div>`;
}
function render(){
  $('.turn b').textContent=Math.min(turn+1,S.turns)+'/'+S.turns;
  $('.rank b').textContent=grade();
  renderMeters(); renderActions(); renderLog();
}
function finish(){
  const g=grade();
  $('.grade').textContent=g;
  $('.otitle').textContent=won()?'System works':'System stalled';
  $('.summary').innerHTML=(won()?'You hit the required targets. ':'You ran out of turns before the required targets. ')+
    S.teach+(S.source?` <span class="source"><a href="${S.source[1]}" target="_blank" rel="noopener">${S.source[0]}</a></span>`:'');
  $('.over').classList.add('show');
}
$('.retry').addEventListener('click',reset);
$('.qtitle').textContent=S.title; $('.qsub').textContent=S.subtitle; $('.goal').textContent=S.win||'Solve the system.';
reset();
})();
"""


def strategy_head(spec: dict) -> str:
    return f"""<!doctype html><html lang='en'><head>
<meta charset='utf-8'>
<meta name='viewport' content='width=device-width,initial-scale=1,viewport-fit=cover,user-scalable=no'>
<meta name='color-scheme' content='dark'>
<title>{spec['title']} — LifeOS strategy puzzle</title>
<style>{STRATEGY_CSS}
:root{{--c:{spec['accent']}}}</style></head>
<body><div class='wrap'>
<section class='panel hero'><div class='kicker'>{spec['emoji']} <span class='qtitle'></span></div>
<h1>{spec['title']}</h1><p class='sub qsub'></p><p class='goal'></p></section>
<main class='panel'><div class='hud'><span class='turn'>Turn <b>1/1</b></span><span class='rank'>Grade <b>C</b></span></div>
<div class='meters'></div><div class='feedback'></div></main>
<aside class='panel'><div class='actions'></div></aside>
<section class='panel'><div class='kicker'>Move log</div><div class='log'></div></section>
</div>
<div class='over'><div class='card'><div class='grade'></div><h2 class='otitle'></h2>
<p class='summary'></p><button class='retry'>Try another system</button></div></div>
"""


# ---- Mechanic: "arena3d" — one 3D game engine, many subjects ---------------- #
ARENA3D_CSS = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{height:100%;overflow:hidden;background:#050712;color:#eaf2ff;font-family:system-ui,-apple-system,sans-serif;touch-action:none;-webkit-text-size-adjust:100%}
#c{display:block;width:100vw;height:100vh}
.panel{position:fixed;background:rgba(8,13,28,.72);backdrop-filter:blur(12px);border:1px solid rgba(160,190,255,.22);border-radius:16px;padding:12px 14px;box-shadow:0 10px 32px rgba(0,0,0,.28)}
#top{top:12px;left:12px;max-width:min(620px,calc(100vw - 24px))}
#top h1{font:900 22px/1.05 Georgia,serif;color:var(--c);margin-bottom:5px}
#top p{font:600 13px/1.4 system-ui;color:#b9c8e8}
#hud{top:12px;right:12px;text-align:right;font:800 13px/1.5 system-ui;color:#b9c8e8}
#hud b{color:var(--c);font-size:19px}
#carry{left:50%;bottom:86px;transform:translateX(-50%);font:900 15px/1 system-ui;text-align:center;min-width:220px}
#carry span{color:var(--c)}
#toast{left:50%;bottom:142px;transform:translateX(-50%);max-width:min(620px,86vw);font:800 14px/1.35 system-ui;text-align:center;opacity:0;transition:opacity .18s}
#toast.show{opacity:1}
#dock{left:50%;bottom:12px;transform:translateX(-50%);display:grid;grid-template-columns:54px 54px 54px;grid-template-rows:44px 44px;gap:7px;background:rgba(8,13,28,.45)}
#dock button{font:900 18px/1 system-ui;color:#061018;background:var(--c);border:none;border-radius:11px;cursor:pointer}
#dock button:active{transform:scale(.94)}
#dock .up{grid-column:2}.left{grid-column:1}.down{grid-column:2}.right{grid-column:3}
#help{left:12px;bottom:12px;max-width:260px;font:600 12.5px/1.45 system-ui;color:#9fb0d0}
#help b{color:#eaf2ff}
#over{position:fixed;inset:0;display:none;align-items:center;justify-content:center;background:rgba(5,7,14,.82);padding:24px;z-index:10}
#over.show{display:flex}
#card{width:min(460px,100%);background:#0d1424;border:1px solid var(--c);border-radius:20px;padding:24px;text-align:center}
#card .grade{font:900 56px/1 system-ui;color:var(--c)}
#card h2{font:900 25px/1.1 Georgia,serif;margin:8px 0 10px}
#card p{font:600 15px/1.5 system-ui;color:#cfe0ff;text-align:left;margin-bottom:14px}
#card a{color:var(--c)}
#card button{font:900 16px system-ui;color:#061018;background:var(--c);border:none;border-radius:13px;padding:13px 18px;width:100%;cursor:pointer}
@media(max-width:720px){#top{right:12px;max-width:none}#hud{top:auto;right:12px;bottom:12px}#help{display:none}#dock{bottom:78px}#carry{bottom:178px}#toast{bottom:232px}}
"""

ARENA3D_JS = r"""
(function(){
const cv=document.getElementById('c');
const renderer=new THREE.WebGLRenderer({canvas:cv,antialias:true});
renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,2));
const scene=new THREE.Scene();
scene.background=new THREE.Color(0x050712);
scene.fog=new THREE.FogExp2(0x050712,0.0022);
const camera=new THREE.PerspectiveCamera(54,1,0.1,2200);
const ACC=parseInt((SPEC.accent||'#6cc6ff').slice(1),16);
function resize(){const w=innerWidth,h=innerHeight;renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix();}
addEventListener('resize',resize);resize();

scene.add(new THREE.HemisphereLight(0xdfe9ff,0x141822,1.05));
const keyLight=new THREE.DirectionalLight(0xffffff,1.25);keyLight.position.set(80,170,80);scene.add(keyLight);
const rim=new THREE.PointLight(ACC,1.5,420);rim.position.set(0,90,0);scene.add(rim);
const grid=new THREE.GridHelper(420,24,0x274060,0x16243b);scene.add(grid);

const $=s=>document.querySelector(s);
let score=0,lives=3,delivered=0,step=0,carried=null,over=false;
const artifacts=new Map(), zones=new Map(), keys={}, btns={};
const objective=SPEC.objective||{type:'zones'};
const totalNeeded=objective.type==='sequence' ? (objective.sequence||[]).length : (SPEC.artifacts||[]).length;

function esc(s){return String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function labelTexture(text,color){
  const cn=document.createElement('canvas');cn.width=512;cn.height=128;const x=cn.getContext('2d');
  x.fillStyle='rgba(5,8,18,.78)';roundRect(x,10,20,492,86,22);x.fill();
  x.strokeStyle=color;x.lineWidth=5;roundRect(x,10,20,492,86,22);x.stroke();
  x.fillStyle='#eaf2ff';x.font='800 34px system-ui';x.textAlign='center';x.textBaseline='middle';x.fillText(text,256,64,456);
  const tex=new THREE.CanvasTexture(cn);tex.minFilter=THREE.LinearFilter;return tex;
}
function roundRect(x,a,b,w,h,r){x.beginPath();x.moveTo(a+r,b);x.arcTo(a+w,b,a+w,b+h,r);x.arcTo(a+w,b+h,a,b+h,r);x.arcTo(a,b+h,a,b,r);x.arcTo(a,b,a+w,b,r);x.closePath();}
function makeLabel(text,color,scale=48){const sp=new THREE.Sprite(new THREE.SpriteMaterial({map:labelTexture(text,color),transparent:true,depthWrite:false}));sp.scale.set(scale*4,scale,1);sp.position.y=24;return sp;}
function colorNum(hex){return parseInt(String(hex||SPEC.accent||'#6cc6ff').slice(1),16);}
function toast(t,good=true){const el=$('#toast');el.textContent=t;el.style.borderColor=good?'rgba(120,255,180,.45)':'rgba(255,120,120,.5)';el.classList.add('show');clearTimeout(toast.t);toast.t=setTimeout(()=>el.classList.remove('show'),2400);}
function hud(){
  $('#score').textContent=score;$('#done').textContent=delivered+'/'+totalNeeded;$('#lives').textContent='♥'.repeat(Math.max(0,lives));
  $('#carryText').textContent=carried?carried.spec.label:'none';
  let m=objective.prompt||'Move, collect, and deliver.';
  if(objective.type==='sequence'){const want=(objective.sequence||[])[step];const a=SPEC.artifacts.find(x=>x.id===want);m+=' Next: '+(a?a.label:'complete');}
  $('#mission').textContent=m;
}
function buildWorld(){
  (SPEC.zones||[]).forEach((z,i)=>{
    const c=colorNum(z.color), group=new THREE.Group();group.position.set(z.x||0,0,z.z||0);
    const ring=new THREE.Mesh(new THREE.RingGeometry((z.radius||28)-3,z.radius||28,64),new THREE.MeshBasicMaterial({color:c,side:THREE.DoubleSide,transparent:true,opacity:.95}));
    ring.rotation.x=-Math.PI/2;group.add(ring);
    const cyl=new THREE.Mesh(new THREE.CylinderGeometry(z.radius||28,z.radius||28,3,64,true),new THREE.MeshBasicMaterial({color:c,transparent:true,opacity:.11,side:THREE.DoubleSide}));
    cyl.position.y=1.5;group.add(cyl);
    group.add(makeLabel(z.name,z.color||SPEC.accent,36));
    scene.add(group);zones.set(z.id,{spec:z,group});
  });
  (SPEC.artifacts||[]).forEach((a,i)=>{
    const c=colorNum(a.color), group=new THREE.Group();group.position.set(a.x||Math.cos(i)*130,8,a.z||Math.sin(i)*130);
    const core=new THREE.Mesh(new THREE.IcosahedronGeometry(8,1),new THREE.MeshStandardMaterial({color:c,emissive:c,emissiveIntensity:.28,roughness:.38,metalness:.1}));
    group.add(core);group.add(makeLabel(a.label,a.color||SPEC.accent,30));
    group.userData.home=group.position.clone();group.userData.spin=Math.random()*6.28;scene.add(group);
    artifacts.set(a.id,{spec:a,group,core,delivered:false});
  });
}

const player=new THREE.Group();
const body=new THREE.Mesh(new THREE.ConeGeometry(9,22,4),new THREE.MeshStandardMaterial({color:ACC,emissive:ACC,emissiveIntensity:.35,roughness:.45}));
body.rotation.y=Math.PI/4;body.position.y=12;player.add(body);
const aura=new THREE.Mesh(new THREE.RingGeometry(12,16,36),new THREE.MeshBasicMaterial({color:ACC,transparent:true,opacity:.5,side:THREE.DoubleSide}));
aura.rotation.x=-Math.PI/2;player.add(aura);scene.add(player);

function pick(a){
  carried=a;a.group.position.set(0,28,0);player.add(a.group);toast('Picked up '+a.spec.label+': '+a.spec.info,true);hud();
}
function dropHome(a){scene.add(a.group);a.group.position.copy(a.group.userData.home);}
function deliver(zone){
  if(!carried||over)return;
  let ok=false;
  if(objective.type==='sequence'){
    const seq=objective.sequence||[];ok=zone.spec.id===(objective.zone||zone.spec.id)&&carried.spec.id===seq[step];
  } else {
    ok=carried.spec.zone===zone.spec.id;
  }
  const a=carried;carried=null;player.remove(a.group);scene.add(a.group);
  if(ok){
    a.delivered=true;delivered++;score+=100+(objective.type==='sequence'?step*25:0);
    a.group.position.set(zone.spec.x||0,18+(delivered%5)*8,zone.spec.z||0);a.group.scale.setScalar(.72);
    if(objective.type==='sequence')step++;
    toast('Locked in: '+a.spec.label+'. '+a.spec.info,true);
    if(delivered>=totalNeeded)finish(true);
  } else {
    lives--;score=Math.max(0,score-40);dropHome(a);
    const need=objective.type==='sequence' ? SPEC.artifacts.find(x=>x.id===(objective.sequence||[])[step])?.label : zones.get(a.spec.zone)?.spec.name;
    toast('Wrong fit. '+a.spec.label+' belongs with '+(need||'another target')+'.',false);
    if(lives<=0)finish(false);
  }
  hud();
}
function finish(won){
  over=true;$('#grade').textContent=won?(lives>=3?'S':lives>=2?'A':'B'):'C';
  $('#otitle').textContent=won?'Engine solved':'Run failed';
  $('#summary').innerHTML=(won?'You completed the subject map. ':'You ran out of lives. ')+esc(SPEC.teach||'')+
    (SPEC.source?` <a href="${SPEC.source[1]}" target="_blank" rel="noopener">${esc(SPEC.source[0])}</a>`:'');
  $('#over').classList.add('show');
}
function reset(){location.reload();}
$('#retry').addEventListener('click',reset);

function bind(){
  addEventListener('keydown',e=>{keys[e.key.toLowerCase()]=true;});
  addEventListener('keyup',e=>{keys[e.key.toLowerCase()]=false;});
  document.querySelectorAll('#dock button').forEach(b=>{
    const k=b.dataset.k; b.addEventListener('pointerdown',e=>{e.preventDefault();btns[k]=true;});
    b.addEventListener('pointerup',e=>{e.preventDefault();btns[k]=false;});
    b.addEventListener('pointerleave',()=>btns[k]=false);
  });
}
function inputVec(){
  let x=0,z=0;
  if(keys.a||keys.arrowleft||btns.left)x-=1;if(keys.d||keys.arrowright||btns.right)x+=1;
  if(keys.w||keys.arrowup||btns.up)z-=1;if(keys.s||keys.arrowdown||btns.down)z+=1;
  const l=Math.hypot(x,z)||1;return {x:x/l,z:z/l,active:!!(x||z)};
}
function update(dt,now){
  const v=inputVec(), speed=92;
  if(v.active&&!over){player.position.x+=v.x*speed*dt;player.position.z+=v.z*speed*dt;player.rotation.y=Math.atan2(v.x,v.z);}
  player.position.x=Math.max(-205,Math.min(205,player.position.x));player.position.z=Math.max(-205,Math.min(205,player.position.z));
  aura.rotation.z+=dt*1.8;
  if(!carried&&!over){
    artifacts.forEach(a=>{if(!a.delivered&&a.group.parent===scene&&a.group.position.distanceTo(player.position)<19)pick(a);});
  }
  if(carried&&!over){zones.forEach(z=>{const dx=player.position.x-(z.spec.x||0),dz=player.position.z-(z.spec.z||0);if(Math.hypot(dx,dz)<(z.spec.radius||28))deliver(z);});}
  artifacts.forEach(a=>{if(a.group.parent===scene&&!a.delivered){a.group.userData.spin+=dt;a.group.position.y=9+Math.sin(now*.002+a.group.userData.spin)*4;a.group.rotation.y+=dt*.8;}});
  const camTarget=new THREE.Vector3(player.position.x,0,player.position.z);
  camera.position.lerp(new THREE.Vector3(player.position.x,150,player.position.z+185),0.08);
  camera.lookAt(camTarget);
}
let last=performance.now();
function frame(now){const dt=Math.min((now-last)/1000,.05);last=now;update(dt,now);renderer.render(scene,camera);requestAnimationFrame(frame);}

$('#gameTitle').textContent=SPEC.title;$('#gameSub').textContent=SPEC.subtitle;
buildWorld();bind();hud();toast('Move with WASD/arrows or the on-screen controls. Pick up artifacts by touching them.',true);
requestAnimationFrame(frame);
})();
"""


def arena3d_head(spec: dict) -> str:
    return f"""<!doctype html><html lang='en'><head>
<meta charset='utf-8'>
<meta name='viewport' content='width=device-width,initial-scale=1,viewport-fit=cover,user-scalable=no'>
<meta name='color-scheme' content='dark'>
<title>{spec['title']} — LifeOS 3D game</title>
<style>{ARENA3D_CSS}
:root{{--c:{spec['accent']}}}</style></head>
<body><canvas id='c'></canvas>
<div id='top' class='panel'><h1><span>{spec['emoji']}</span> <span id='gameTitle'></span></h1><p id='gameSub'></p><p id='mission'></p></div>
<div id='hud' class='panel'>Score <b id='score'>0</b><br>Done <span id='done'>0/0</span><br><span id='lives'>♥♥♥</span></div>
<div id='toast' class='panel'></div>
<div id='carry' class='panel'>Carrying: <span id='carryText'>none</span></div>
<div id='help' class='panel'><b>Same engine, different subject.</b><br>Specs define artifacts, zones, sequence rules, and feedback. The 3D code stays the same.</div>
<div id='dock' class='panel'><button class='up' data-k='up'>▲</button><button class='left' data-k='left'>◀</button><button class='down' data-k='down'>▼</button><button class='right' data-k='right'>▶</button></div>
<div id='over'><div id='card'><div id='grade' class='grade'></div><h2 id='otitle'></h2><p id='summary'></p><button id='retry'>Play again</button></div></div>
"""


# Template-aware 3D engine override. The generic runtime is shared, but each
# subject chooses a different visible world through `template`.
ARENA3D_CSS = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{height:100%;overflow:hidden;background:#101820;color:#f4f7fb;font-family:system-ui,-apple-system,sans-serif;touch-action:none;-webkit-text-size-adjust:100%}
#c{display:block;width:100vw;height:100vh}
.panel{position:fixed;background:rgba(255,255,255,.80);backdrop-filter:blur(12px);border:3px solid rgba(55,63,66,.28);box-shadow:0 8px 0 rgba(55,63,66,.20),0 18px 42px rgba(0,0,0,.22);border-radius:18px;padding:12px 14px}
#top{top:14px;left:14px;max-width:min(610px,calc(100vw - 28px))}
#top h1{font:950 24px/1.02 system-ui;color:#fff;text-shadow:3px 3px 0 #373f42,-2px -2px 0 #373f42,2px -2px 0 #373f42,-2px 2px 0 #373f42;margin-bottom:6px;letter-spacing:.03em}
#top p{font:800 13px/1.35 system-ui;color:#293942}
#mission{margin-top:7px;color:#435760}
#hud{top:14px;right:14px;text-align:right;font:950 13px/1.55 system-ui;color:#34454d}
#hud b{font-size:21px;color:#fff;text-shadow:2px 2px 0 #373f42,-1px -1px 0 #373f42,1px -1px 0 #373f42,-1px 1px 0 #373f42}
#carry{left:50%;bottom:92px;transform:translateX(-50%);font:950 15px/1 system-ui;text-align:center;min-width:230px;color:#293942}
#carry span{color:#fff;text-shadow:2px 2px 0 #373f42,-1px -1px 0 #373f42,1px -1px 0 #373f42,-1px 1px 0 #373f42}
#toast{left:50%;bottom:154px;transform:translateX(-50%);max-width:min(640px,88vw);font:950 14px/1.35 system-ui;text-align:center;color:#293942;opacity:0;transition:opacity .18s}
#toast.show{opacity:1}
#dock{left:50%;bottom:14px;transform:translateX(-50%);display:grid;grid-template-columns:56px 56px 56px;grid-template-rows:46px 46px;gap:8px;background:rgba(255,255,255,.48)}
#dock button{font:950 20px/1 system-ui;color:#fff;background:var(--c);border:3px solid #373f42;border-radius:14px;cursor:pointer;box-shadow:0 5px 0 #373f42}
#dock button:active{transform:translateY(4px);box-shadow:0 1px 0 #373f42}
#dock .up{grid-column:2}.left{grid-column:1}.down{grid-column:2}.right{grid-column:3}
#help{left:14px;bottom:14px;max-width:272px;font:800 12.5px/1.45 system-ui;color:#34454d}
#help b{color:#111b22}
#over{position:fixed;inset:0;display:none;align-items:center;justify-content:center;background:rgba(92,139,138,.72);padding:24px;z-index:10}
#over.show{display:flex}
#card{width:min(470px,100%);background:#fff;border:4px solid #373f42;border-radius:22px;padding:24px;text-align:center;box-shadow:0 10px 0 #373f42}
#card .grade{font:950 60px/1 system-ui;color:var(--c);text-shadow:3px 3px 0 #373f42,-2px -2px 0 #373f42,2px -2px 0 #373f42,-2px 2px 0 #373f42}
#card h2{font:950 26px/1.1 system-ui;margin:8px 0 10px;color:#17242c}
#card p{font:750 15px/1.5 system-ui;color:#34454d;text-align:left;margin-bottom:14px}
#card a{color:#0d6a78}
#card button{font:950 16px system-ui;color:#fff;background:var(--c);border:3px solid #373f42;border-radius:15px;padding:13px 18px;width:100%;cursor:pointer;box-shadow:0 5px 0 #373f42}
@media(max-width:720px){#top{right:14px;max-width:none}#hud{top:128px;left:14px;right:auto;text-align:left;padding:8px 10px}#help{display:none}#dock{bottom:28px}#carry{bottom:166px;min-width:min(230px,76vw)}#toast{bottom:230px;max-width:76vw}}
"""

ARENA3D_JS = r"""
(function(){
const cv=document.getElementById('c');
const renderer=new THREE.WebGLRenderer({canvas:cv,antialias:true,alpha:false});
renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,2));
if(THREE.sRGBEncoding)renderer.outputEncoding=THREE.sRGBEncoding;
const scene=new THREE.Scene();
const camera=new THREE.PerspectiveCamera(48,1,0.1,1800);
const ACC=parseInt((SPEC.accent||'#6cc6ff').slice(1),16);
const template=SPEC.template||'civ-board';
const bounds={x:210,z:165};
const $=s=>document.querySelector(s);
let score=0,lives=3,delivered=0,step=0,carried=null,over=false;
let px=0,pz=template==='gallery-studio'?118:128,heading=0,last=performance.now();
const artifacts=new Map(),zones=new Map(),keys={},btns={},objective=SPEC.objective||{type:'zones'};
const totalNeeded=objective.type==='sequence'?(objective.sequence||[]).length:(SPEC.artifacts||[]).length;

function resize(){const w=innerWidth,h=innerHeight;renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix();}
addEventListener('resize',resize);resize();

function esc(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function colorNum(hex){return parseInt(String(hex||SPEC.accent||'#6cc6ff').slice(1),16);}
function setWorld(obj,x,z,y=0){obj.position.set(x,y,z);}
function dist2(a,b,c,d){return Math.hypot(a-c,b-d);}
function roundRect(x,a,b,w,h,r){x.beginPath();x.moveTo(a+r,b);x.arcTo(a+w,b,a+w,b+h,r);x.arcTo(a+w,b+h,a,b+h,r);x.arcTo(a,b+h,a,b,r);x.arcTo(a,b,a+w,b,r);x.closePath();}
function labelTexture(text,color){
 const cn=document.createElement('canvas');cn.width=512;cn.height=132;const x=cn.getContext('2d');
 x.fillStyle='rgba(255,255,255,.86)';roundRect(x,8,20,496,88,20);x.fill();
 x.strokeStyle='#373f42';x.lineWidth=6;roundRect(x,8,20,496,88,20);x.stroke();
 x.fillStyle='#17242c';x.font='900 34px system-ui';x.textAlign='center';x.textBaseline='middle';x.fillText(text,256,64,456);
 x.fillStyle=color;x.fillRect(38,100,436,8);
const tex=new THREE.CanvasTexture(cn);tex.minFilter=THREE.LinearFilter;return tex;
}
function makeLabel(text,color,scale=18){const sp=new THREE.Sprite(new THREE.SpriteMaterial({map:labelTexture(text,color),transparent:true,depthWrite:false}));sp.scale.set(scale*4,scale,1);sp.position.y=20;return sp;}
function toast(t,good=true){const el=$('#toast');el.textContent=t;el.style.borderColor=good?'rgba(74,150,94,.55)':'rgba(190,70,70,.58)';el.classList.add('show');clearTimeout(toast.t);toast.t=setTimeout(()=>el.classList.remove('show'),2600);}

function mat(color){return new THREE.MeshToonMaterial({color});}
function addBox(x,z,w,h,d,color){const m=new THREE.Mesh(new THREE.BoxGeometry(w,h,d),mat(color));m.position.set(x,h/2,z);scene.add(m);return m;}
function addCylinder(x,z,r,h,color){const m=new THREE.Mesh(new THREE.CylinderGeometry(r,r,h,32),mat(color));m.position.set(x,h/2,z);scene.add(m);return m;}
function addTree(x,z){addCylinder(x,z,2,9,0x7a5637);const c=new THREE.Mesh(new THREE.DodecahedronGeometry(8,0),mat(0x4e8b5e));c.position.set(x,15,z);scene.add(c);}
function setupLights(bg,fog){
 renderer.setClearColor(bg,1);scene.fog=new THREE.Fog(bg,fog[0],fog[1]);
 scene.add(new THREE.HemisphereLight(0xffffff,0x445566,1.15));
 const sun=new THREE.DirectionalLight(0xfff4d2,1.45);sun.position.set(150,240,120);scene.add(sun);
 const rim=new THREE.DirectionalLight(0xa8d8ff,.65);rim.position.set(-180,90,-180);scene.add(rim);
}
function makeWorld(){
 if(template==='quantum-lab'){
  setupLights(0x060817,[240,760]);
  const floor=new THREE.Mesh(new THREE.CylinderGeometry(185,185,6,96),new THREE.MeshStandardMaterial({color:0x121a32,roughness:.42,metalness:.22}));floor.position.y=-3;scene.add(floor);
  for(let i=0;i<9;i++){const r=48+i*15;const ring=new THREE.Mesh(new THREE.TorusGeometry(r,.5,8,128),new THREE.MeshBasicMaterial({color:i%2?0x5be8ff:0xb06bf0,transparent:true,opacity:.28}));ring.rotation.x=Math.PI/2;scene.add(ring);}
  for(let i=0;i<60;i++){const p=new THREE.Mesh(new THREE.SphereGeometry(1.2,6,6),new THREE.MeshBasicMaterial({color:Math.random()<.5?0x7dffb0:0xb06bf0}));p.position.set((Math.random()-.5)*370,15+Math.random()*90,(Math.random()-.5)*300);scene.add(p);}
 }else if(template==='gallery-studio'){
  setupLights(0xded7c8,[260,760]);
  const floor=new THREE.Mesh(new THREE.PlaneGeometry(430,340),mat(0xc9bfa9));floor.rotation.x=-Math.PI/2;scene.add(floor);
  addBox(0,-173,430,90,8,0xf2efe6);addBox(-218,0,8,90,340,0xe9e1d2);addBox(218,0,8,90,340,0xe9e1d2);
  for(let i=0;i<7;i++){addBox(-165+i*55,-168,34,24,4,[0xffd36c,0x6cc6ff,0xff6b9b][i%3]);}
  for(let i=0;i<12;i++){const p=addCylinder(-190+i*34,112+(i%2)*24,4,18,0xffffff);p.material.color.setHex(i%3===0?0xffd36c:i%3===1?0x6cc6ff:0xff6b9b);}
 }else{
  setupLights(0x9bcfca,[270,820]);
  const ground=new THREE.Mesh(new THREE.PlaneGeometry(430,340),mat(0x8da76f));ground.rotation.x=-Math.PI/2;scene.add(ground);
  const river=new THREE.Mesh(new THREE.PlaneGeometry(430,34),new THREE.MeshStandardMaterial({color:0x62aab2,roughness:.7}));river.rotation.x=-Math.PI/2;river.position.z=64;scene.add(river);
  for(let i=0;i<24;i++)addTree(-200+Math.random()*400,-150+Math.random()*300);
  for(let i=0;i<10;i++){addBox(-85+i*18,-20+Math.sin(i)*10,11,9,11,0xd8d2bf);const roof=new THREE.Mesh(new THREE.ConeGeometry(9,8,4),mat(0xc25f3d));roof.position.set(-85+i*18,13,-20+Math.sin(i)*10);roof.rotation.y=Math.PI/4;scene.add(roof);}
  for(let i=0;i<7;i++){const f=new THREE.Mesh(new THREE.PlaneGeometry(28,16),mat(0xc9b65a));f.rotation.x=-Math.PI/2;f.position.set(-160+i*28,1,118);scene.add(f);}
 }
}

function buildZones(){
 (SPEC.zones||[]).forEach(z=>{
   const c=colorNum(z.color),group=new THREE.Group();
   const ring=new THREE.Mesh(new THREE.TorusGeometry(z.radius||28,2.8,10,80),new THREE.MeshBasicMaterial({color:c}));
   ring.rotation.x=Math.PI/2;group.add(ring);const beam=new THREE.Mesh(new THREE.CylinderGeometry((z.radius||28)*.65,(z.radius||28)*.65,18,36,true),new THREE.MeshBasicMaterial({color:c,transparent:true,opacity:.16,side:THREE.DoubleSide}));beam.position.y=9;group.add(beam);
   group.add(makeLabel(z.name,z.color||SPEC.accent,18));setWorld(group,z.x||0,z.z||0,3);scene.add(group);zones.set(z.id,{spec:z,group});
 });
}
function artifactShape(a,i){
 const c=colorNum(a.color),mat=new THREE.MeshToonMaterial({color:c});
 if((SPEC.id||'').includes('art'))return new THREE.Mesh(new THREE.BoxGeometry(12,16,3),mat);
 if((SPEC.id||'').includes('quantum'))return new THREE.Mesh(new THREE.IcosahedronGeometry(8,1),mat);
 if((SPEC.id||'').includes('civilization'))return new THREE.Mesh(i%2?new THREE.ConeGeometry(8,14,5):new THREE.BoxGeometry(11,11,11),mat);
 return new THREE.Mesh(new THREE.DodecahedronGeometry(8,0),mat);
}
function buildArtifacts(){
 (SPEC.artifacts||[]).forEach((a,i)=>{
   const group=new THREE.Group();const core=artifactShape(a,i);core.position.y=9;group.add(core);group.add(makeLabel(a.label,a.color||SPEC.accent,15));
   group.userData.x=a.x||Math.cos(i)*130;group.userData.z=a.z||Math.sin(i)*130;group.userData.spin=Math.random()*6.28;
   setWorld(group,group.userData.x,group.userData.z,4);scene.add(group);artifacts.set(a.id,{spec:a,group,core,delivered:false});
 });
}

const player=new THREE.Group();
const bodyGeo=THREE.CapsuleGeometry?new THREE.CapsuleGeometry(5,12,4,8):new THREE.CylinderGeometry(5,5,16,8);
const body=new THREE.Mesh(bodyGeo,new THREE.MeshToonMaterial({color:ACC}));
body.position.y=13;player.add(body);
const head=new THREE.Mesh(new THREE.SphereGeometry(5.5,16,12),new THREE.MeshToonMaterial({color:0xffe0bd}));head.position.y=24;player.add(head);
const pack=new THREE.Mesh(new THREE.BoxGeometry(9,9,5),new THREE.MeshToonMaterial({color:0x373f42}));pack.position.set(0,15,-6);player.add(pack);
scene.add(player);

function awardGame(won){
 if(!won)return;
 try{
  const key='lifeos.learning.progress.v1',p=JSON.parse(localStorage.getItem(key)||'{}');
  p.done=p.done||{};const xpMap={'arena-civilization':140,'arena-quantum-fields':160,'arena-art-movements':150};
  const xp=xpMap[SPEC.id]||(SPEC.id&&SPEC.id.includes('arena')?150:100);
  if(!p.done[SPEC.id])p.done[SPEC.id]={at:new Date().toISOString(),title:SPEC.title,xp,kind:'game'};
  localStorage.setItem(key,JSON.stringify(p));
 }catch{}
}
function hud(){ $('#score').textContent=score;$('#done').textContent=delivered+'/'+totalNeeded;$('#lives').textContent='♥'.repeat(Math.max(0,lives));$('#carryText').textContent=carried?carried.spec.label:'none';
 let m=objective.prompt||'Move, collect, deliver.'; if(objective.type==='sequence'){const want=(objective.sequence||[])[step],a=SPEC.artifacts.find(x=>x.id===want);m+=' Next: '+(a?a.label:'complete');} $('#mission').textContent=m; }
function pick(a){carried=a;scene.remove(a.group);a.group.position.set(0,35,0);a.group.scale.setScalar(.72);player.add(a.group);toast('Picked up '+a.spec.label+': '+a.spec.info,true);hud();}
function dropHome(a){player.remove(a.group);scene.add(a.group);a.group.scale.setScalar(1);setWorld(a.group,a.group.userData.x,a.group.userData.z,4);}
function deliver(zone){
 if(!carried||over)return;let ok=false;
 if(objective.type==='sequence'){const seq=objective.sequence||[];ok=zone.spec.id===(objective.zone||zone.spec.id)&&carried.spec.id===seq[step];}
 else ok=carried.spec.zone===zone.spec.id;
 const a=carried;carried=null;player.remove(a.group);scene.add(a.group);a.group.scale.setScalar(.65);
 if(ok){a.delivered=true;delivered++;score+=100+(objective.type==='sequence'?step*25:0);setWorld(a.group,(zone.spec.x||0)+(delivered%4-1.5)*8,(zone.spec.z||0)+Math.floor(delivered/4)*8,18);if(objective.type==='sequence')step++;toast('Locked in: '+a.spec.label+'. '+a.spec.info,true);if(delivered>=totalNeeded)finish(true);}
 else{lives--;score=Math.max(0,score-35);dropHome(a);const need=objective.type==='sequence'?SPEC.artifacts.find(x=>x.id===(objective.sequence||[])[step])?.label:zones.get(a.spec.zone)?.spec.name;toast('Wrong delivery. '+a.spec.label+' belongs with '+(need||'another target')+'.',false);if(lives<=0)finish(false);}
 hud();
}
function finish(won){over=true;awardGame(won);$('#grade').textContent=won?(lives>=3?'S':lives>=2?'A':'B'):'C';$('#otitle').textContent=won?'Subject world solved':'Delivery failed';$('#summary').innerHTML=(won?'You completed the subject map. Progress saved to the skill tree. ':'You ran out of lives. ')+esc(SPEC.teach||'')+(SPEC.source?` <a href="${SPEC.source[1]}" target="_blank" rel="noopener">${esc(SPEC.source[0])}</a>`:'');$('#over').classList.add('show');}
$('#retry').addEventListener('click',()=>location.reload());
function bind(){addEventListener('keydown',e=>keys[e.key.toLowerCase()]=true);addEventListener('keyup',e=>keys[e.key.toLowerCase()]=false);document.querySelectorAll('#dock button').forEach(b=>{const k=b.dataset.k;b.addEventListener('pointerdown',e=>{e.preventDefault();btns[k]=true;});b.addEventListener('pointerup',e=>{e.preventDefault();btns[k]=false;});b.addEventListener('pointerleave',()=>btns[k]=false);});}
function input(){let x=0,z=0;if(keys.a||keys.arrowleft||btns.left)x-=1;if(keys.d||keys.arrowright||btns.right)x+=1;if(keys.w||keys.arrowup||btns.up)z+=1;if(keys.s||keys.arrowdown||btns.down)z-=1;const l=Math.hypot(x,z)||1;return{x:x/l,z:z/l,on:!!(x||z)};}
function cameraTarget(){return new THREE.Vector3(px-180,230,pz+255);}
function update(dt,now){
 const v=input(),speed=54;if(v.on&&!over){px+=v.x*speed*dt;pz+=v.z*speed*dt;heading=Math.atan2(v.x,v.z);px=Math.max(-200,Math.min(200,px));pz=Math.max(-160,Math.min(160,pz));}
 player.position.set(px,8,pz);player.rotation.y=heading;
 if(carried)carried.group.rotation.y+=dt*1.6;
 if(!carried&&!over)artifacts.forEach(a=>{if(!a.delivered&&a.group.parent===scene&&dist2(px,pz,a.group.userData.x,a.group.userData.z)<18)pick(a);});
 if(carried&&!over)zones.forEach(z=>{if(dist2(px,pz,z.spec.x||0,z.spec.z||0)<(z.spec.radius||28))deliver(z);});
 artifacts.forEach(a=>{if(a.group.parent===scene&&!a.delivered){a.group.userData.spin+=dt;const bob=8+Math.sin(now*.003+a.group.userData.spin)*4;setWorld(a.group,a.group.userData.x,a.group.userData.z,bob);a.group.rotation.y+=dt*.9;}});
 camera.position.lerp(cameraTarget(),.08);camera.lookAt(px,8,pz);
}
function loop(now){const dt=Math.min((now-last)/1000,.05);last=now;update(dt,now);renderer.render(scene,camera);requestAnimationFrame(loop);}
$('#gameTitle').textContent=SPEC.title;$('#gameSub').textContent=SPEC.subtitle;makeWorld();buildZones();buildArtifacts();bind();hud();camera.position.copy(cameraTarget());camera.lookAt(px,8,pz);toast('Move through this subject world. Pick up concept objects and deliver them to the right place.',true);requestAnimationFrame(loop);
})();
"""


def validate_spec(spec: dict) -> None:
    """Fail fast when an agent emits an invalid game spec."""
    required = ("id", "title", "subtitle", "emoji", "accent", "mechanic", "teach")
    missing = [k for k in required if not spec.get(k)]
    if missing:
        raise ValueError(f"{spec.get('id', '<unknown>')} missing required fields: {missing}")
    mechanic = spec["mechanic"]
    if mechanic in {"classify", "runner"}:
        if not spec.get("categories") or not spec.get("items"):
            raise ValueError(f"{spec['id']} needs categories and items")
    elif mechanic == "strategy":
        if not spec.get("meters") or not spec.get("actions") or not spec.get("turns"):
            raise ValueError(f"{spec['id']} needs meters, actions, and turns")
        meter_ids = {m["id"] for m in spec["meters"]}
        for action in spec["actions"]:
            unknown = set((action.get("effects") or {}).keys()) - meter_ids
            if unknown:
                raise ValueError(f"{spec['id']} action {action.get('name')} references unknown meters: {sorted(unknown)}")
    elif mechanic == "arena3d":
        if not spec.get("zones") or not spec.get("artifacts") or not spec.get("objective"):
            raise ValueError(f"{spec['id']} needs zones, artifacts, and objective")
        zone_ids = {z["id"] for z in spec["zones"]}
        objective = spec["objective"]
        if objective.get("type") == "sequence":
            artifact_ids = {a["id"] for a in spec["artifacts"]}
            missing = set(objective.get("sequence") or []) - artifact_ids
            if missing:
                raise ValueError(f"{spec['id']} sequence references unknown artifacts: {sorted(missing)}")
            if objective.get("zone") not in zone_ids:
                raise ValueError(f"{spec['id']} sequence objective references unknown zone: {objective.get('zone')}")
        else:
            for artifact in spec["artifacts"]:
                if artifact.get("zone") not in zone_ids:
                    raise ValueError(f"{spec['id']} artifact {artifact.get('id')} references unknown zone: {artifact.get('zone')}")
    else:
        raise ValueError(f"{spec['id']} has unsupported mechanic: {mechanic}")


def packet(spec: dict) -> str:
    """Render a spec into a playable HTML packet using its mechanic's engine."""
    validate_spec(spec)
    if spec.get("mechanic") == "runner":
        head_html, engine = runner_head(spec), RUNNER_JS
    elif spec.get("mechanic") == "strategy":
        head_html, engine = strategy_head(spec), STRATEGY_JS
    elif spec.get("mechanic") == "arena3d":
        head_html, engine = arena3d_head(spec), ARENA3D_JS
        return (head_html
                + "<script>" + ensure_three() + "</script>\n"
                + "<script>const SPEC=" + json.dumps(spec) + ";</script>\n"
                + "<script>" + engine + "</script>\n</body></html>")
    else:
        head_html, engine = classify_head(spec), ENGINE_JS
    return (head_html
            + "<script>const SPEC=" + json.dumps(spec) + ";</script>\n"
            + "<script>" + engine + "</script>\n</body></html>")


def build() -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    for spec in DRILLS:
        (OUT / f"{spec['id']}.html").write_text(packet(spec), encoding="utf-8")
    manifest = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "drills": [
            {"id": d["id"], "title": d["title"], "emoji": d["emoji"],
             "mechanic": d["mechanic"], "pairs": d.get("pairs"),
             "url": f"/output/learn/{d['id']}.html"}
            for d in DRILLS
        ],
    }
    (OUT / "drills.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


# Catalogue surfaced on the /learn index (imported by lifeos_lessons).
ARCADE = [
    {"id": d["id"], "emoji": d["emoji"], "accent": d["accent"],
     "title": d["title"], "blurb": d["subtitle"], "pairs": d.get("pairs"),
     "url": f"/output/learn/{d['id']}.html"}
    for d in DRILLS
]


def main() -> int:
    parser = argparse.ArgumentParser(description="LifeOS learning-game system (spec-driven drills)")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("build", help="Build all drill packets into output/learn/")
    args = parser.parse_args()
    if args.cmd == "build":
        print(json.dumps(build(), indent=2))
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
