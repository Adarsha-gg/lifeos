#!/usr/bin/env python3
"""LifeOS learning-game *system*.

The opposite of a bespoke game-per-topic: a small set of reusable game *engines*
(mechanics) driven entirely by a JSON content spec, wrapped in a shared "game
shell" (score, streak combo, lives, timer, ranks, juice) so any subject becomes
a real game. A lesson emits a spec; this turns it into a self-contained, offline
playable packet.

This module ships engine #1 — `classify` (discriminate items into categories) —
and demonstrates generalization by rendering it for two unrelated subjects from
pure data. Adding a subject = adding a spec, not writing a game.

Build:  python tools/lifeos_arcade.py build
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime

from lifeos_paths import VAULT_ROOT

OUT = VAULT_ROOT / "output" / "learn"


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


def head(spec: dict) -> str:
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


def build() -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    for spec in DRILLS:
        html = (
            head(spec)
            + "<script>const SPEC=" + json.dumps(spec) + ";</script>\n"
            + "<script>" + ENGINE_JS + "</script>\n</body></html>"
        )
        (OUT / f"{spec['id']}.html").write_text(html, encoding="utf-8")
    manifest = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "drills": [
            {"id": d["id"], "title": d["title"], "emoji": d["emoji"],
             "mechanic": d["mechanic"], "url": f"/output/learn/{d['id']}.html"}
            for d in DRILLS
        ],
    }
    (OUT / "drills.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


# Catalogue surfaced on the /learn index (imported by lifeos_lessons).
ARCADE = [
    {"id": d["id"], "emoji": d["emoji"], "accent": d["accent"],
     "title": d["title"], "blurb": d["subtitle"]}
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
