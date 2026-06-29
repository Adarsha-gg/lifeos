#!/usr/bin/env python3
"""LifeOS personal learning graph.

The global graph is a content library: separate topic islands with explicit,
typed edges. The personal graph is derived from browser localStorage and only
shows nodes the user has actually completed. Unrelated subjects are not joined.

Build:  python tools/lifeos_skill_tree.py build
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from typing import Any

from lifeos_paths import VAULT_ROOT

OUT = VAULT_ROOT / "output" / "learn"
GRAPH_STORE = OUT / "graph-store.json"

try:
    from lifeos_deep_history import DEEP_GRAPH
except Exception:
    DEEP_GRAPH = {"domains": [], "nodes": [], "edges": []}
try:
    from lifeos_curriculum import CURRICULUM_GRAPH
except Exception:
    CURRICULUM_GRAPH = {"domains": [], "nodes": [], "edges": []}


SEED_GRAPH: dict[str, Any] = {
    "domains": [
        {"id": "history", "name": "History", "color": "#c4892d"},
        {"id": "thinking", "name": "Thinking", "color": "#1f9d78"},
        {"id": "physics", "name": "Physics", "color": "#6d6af2"},
        {"id": "growth", "name": "Growth", "color": "#3d8fd6"},
        {"id": "culture", "name": "Culture", "color": "#d86b8a"},
        {"id": "systems", "name": "Systems", "color": "#6b7a86"},
        {"id": "custom", "name": "Custom", "color": "#58636f"},
    ],
    "nodes": [
        {"id": "story-of-civilization", "domain": "history", "title": "Civilization Chain", "kind": "article", "xp": 80, "url": "/output/learn/story-of-civilization.html", "summary": "Farming, surplus, specialists, cities, and writing.", "x": 12, "y": 12},
        {"id": "arena-civilization", "domain": "history", "title": "Civilization Builder", "kind": "game", "xp": 140, "url": "/output/learn/arena-civilization.html", "summary": "Practice the civilization sequence in a 3D board.", "x": 12, "y": 34},
        {"id": "game-theory", "domain": "systems", "title": "Game Theory", "kind": "article", "xp": 80, "url": "/output/learn/game-theory.html", "summary": "Why selfish choices can destroy shared outcomes.", "x": 25, "y": 56},
        {"id": "fermi-estimation", "domain": "thinking", "title": "Fermi Estimation", "kind": "article", "xp": 80, "url": "/output/learn/fermi-estimation.html", "summary": "Break unknown quantities into rough estimates.", "x": 38, "y": 12},
        {"id": "drill-primes", "domain": "thinking", "title": "Prime Time", "kind": "game", "xp": 100, "url": "/output/learn/drill-primes.html", "summary": "Fast numerical discrimination under pressure.", "x": 38, "y": 34},
        {"id": "quantum-zoo", "domain": "physics", "title": "Quantum Zoo", "kind": "game", "xp": 120, "url": "/output/learn/drill-quantum.html", "summary": "Classify core quantum objects.", "x": 55, "y": 12},
        {"id": "arena-quantum-fields", "domain": "physics", "title": "Quantum Field Sorter", "kind": "game", "xp": 160, "url": "/output/learn/arena-quantum-fields.html", "summary": "Sort matter particles and force carriers.", "x": 55, "y": 34},
        {"id": "power-of-compounding", "domain": "growth", "title": "Compounding", "kind": "article", "xp": 80, "url": "/output/learn/power-of-compounding.html", "summary": "Small loops become large when outputs feed back.", "x": 72, "y": 12},
        {"id": "drill-compounding-engine", "domain": "growth", "title": "Compounding Engine", "kind": "game", "xp": 130, "url": "/output/learn/drill-compounding-engine.html", "summary": "Manage skill, momentum, and energy.", "x": 72, "y": 34},
        {"id": "why-we-sleep", "domain": "growth", "title": "Sleep Architecture", "kind": "article", "xp": 80, "url": "/output/learn/why-we-sleep.html", "summary": "Light, deep, and REM sleep each do different work.", "x": 84, "y": 56},
        {"id": "drill-sleep-stages", "domain": "growth", "title": "Sleep Stage Sprint", "kind": "game", "xp": 120, "url": "/output/learn/drill-sleep-stages.html", "summary": "Steer sleep facts into the right stage.", "x": 84, "y": 78},
        {"id": "arena-art-movements", "domain": "culture", "title": "Gallery Curator", "kind": "game", "xp": 150, "url": "/output/learn/arena-art-movements.html", "summary": "Sort visual clues into art movements.", "x": 88, "y": 12},
    ],
    "edges": [
        {"from": "story-of-civilization", "to": "arena-civilization", "relation": "practice"},
        {"from": "fermi-estimation", "to": "drill-primes", "relation": "practice"},
        {"from": "quantum-zoo", "to": "arena-quantum-fields", "relation": "practice"},
        {"from": "power-of-compounding", "to": "drill-compounding-engine", "relation": "practice"},
        {"from": "why-we-sleep", "to": "drill-sleep-stages", "relation": "practice"},
    ],
}


def _edge_key(edge: dict[str, Any]) -> tuple[str, str, str]:
    return (str(edge.get("from", "")), str(edge.get("to", "")), str(edge.get("relation", "")))


def merge_graphs(*graphs: dict[str, Any]) -> dict[str, Any]:
    domains: dict[str, dict[str, Any]] = {}
    nodes: dict[str, dict[str, Any]] = {}
    edges: dict[tuple[str, str, str], dict[str, Any]] = {}
    for graph in graphs:
        for domain in graph.get("domains", []):
            if domain.get("id"):
                domains[str(domain["id"])] = {**domains.get(str(domain["id"]), {}), **domain}
        for node in graph.get("nodes", []):
            if node.get("id"):
                nodes[str(node["id"])] = {**nodes.get(str(node["id"]), {}), **node}
        for edge in graph.get("edges", []):
            key = _edge_key(edge)
            if all(key):
                edges[key] = {**edges.get(key, {}), **edge}
    return {
        "domains": sorted(domains.values(), key=lambda d: str(d.get("id", ""))),
        "nodes": sorted(nodes.values(), key=lambda n: str(n.get("id", ""))),
        "edges": sorted(edges.values(), key=_edge_key),
    }


def load_graph_store() -> dict[str, Any]:
    if GRAPH_STORE.exists():
        try:
            stored = json.loads(GRAPH_STORE.read_text(encoding="utf-8"))
        except Exception:
            stored = {}
        return merge_graphs(SEED_GRAPH, DEEP_GRAPH, CURRICULUM_GRAPH, stored)
    graph = merge_graphs(SEED_GRAPH, DEEP_GRAPH, CURRICULUM_GRAPH)
    save_graph_store(graph)
    return graph


def save_graph_store(graph: dict[str, Any]) -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    merged = merge_graphs(SEED_GRAPH, DEEP_GRAPH, CURRICULUM_GRAPH, graph)
    GRAPH_STORE.write_text(json.dumps(merged, indent=2), encoding="utf-8")
    return merged


GRAPH = load_graph_store()


CSS = """
*{box-sizing:border-box}html,body{margin:0;min-height:100%;color:#1d160f;font-family:Inter,ui-sans-serif,system-ui,-apple-system,sans-serif}
body{background:radial-gradient(circle at 16% -8%,#fff2bd 0 18%,transparent 43%),radial-gradient(circle at 92% 4%,#d6edff 0 16%,transparent 38%),linear-gradient(180deg,#fffaf0 0%,#f2ece1 45%,#e8edf2 100%);overflow-x:hidden}body:before{content:"";position:fixed;inset:0;pointer-events:none;background-image:linear-gradient(rgba(28,21,14,.035) 1px,transparent 1px),linear-gradient(90deg,rgba(28,21,14,.035) 1px,transparent 1px);background-size:34px 34px;mask-image:linear-gradient(#000,transparent 78%)}a{color:inherit}
.shell{width:min(1180px,calc(100% - 32px));margin:0 auto;padding:22px 0 54px;position:relative;z-index:1}
.top{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:18px;flex-wrap:wrap}.top a{color:#5c5144;text-decoration:none;font:900 13px/1 system-ui;background:rgba(255,255,255,.62);border:1px solid rgba(62,47,30,.12);border-radius:999px;padding:10px 12px;box-shadow:0 10px 28px rgba(62,47,30,.06);backdrop-filter:blur(14px)}
.title{padding:10px 0 8px}.title h1{margin:0 0 8px;font:950 clamp(44px,7vw,92px)/.86 Georgia,serif;letter-spacing:-.06em;color:#17110b;text-wrap:balance}.title p{margin:0;color:#665a4d;font:750 clamp(16px,2vw,20px)/1.45 system-ui;max-width:760px;text-wrap:balance}
.profile{display:grid;grid-template-columns:1fr auto;gap:16px;align-items:center;border:1px solid rgba(255,255,255,.18);background:linear-gradient(135deg,#16110d,#272018 58%,#3a2717);color:#fff4dc;border-radius:28px;padding:18px;margin:18px 0;box-shadow:0 24px 70px rgba(62,38,18,.24),inset 0 1px 0 rgba(255,255,255,.18)}
.lvl{font:950 34px/.94 Georgia,serif;letter-spacing:-.03em}.xp{color:#d8c6a7;font-weight:900;margin-top:5px}.bar{height:12px;background:rgba(255,255,255,.13);border-radius:999px;overflow:hidden;margin-top:12px;box-shadow:inset 0 0 0 1px rgba(255,255,255,.08)}.bar i{display:block;height:100%;width:0;background:linear-gradient(90deg,#ffd36a,#66e7bf,#82b8ff,#ff7aa8);box-shadow:0 0 24px rgba(255,211,106,.46)}
.actions{display:flex;gap:9px;flex-wrap:wrap;justify-content:flex-end}.actions button,.actions a{border:1px solid rgba(255,255,255,.22);background:rgba(255,255,255,.1);color:#fff4dc;border-radius:999px;padding:11px 13px;font-weight:950;text-decoration:none;cursor:pointer;backdrop-filter:blur(10px)}.actions .ghost{background:rgba(255,255,255,.92);color:#1f1710}.actions .active{background:#fff4dc;color:#17110b;border-color:#fff4dc}
.legend{display:flex;gap:9px;flex-wrap:wrap;margin:18px 0 12px}.chip{display:flex;align-items:center;gap:8px;border:1px solid rgba(50,38,25,.12);background:rgba(255,255,255,.7);border-radius:999px;padding:9px 12px;font-weight:950;color:#3b3127;box-shadow:0 10px 24px rgba(63,48,30,.06);backdrop-filter:blur(12px);cursor:pointer}.dot{width:10px;height:10px;border-radius:50%;background:var(--c);box-shadow:0 0 0 4px color-mix(in srgb,var(--c) 18%,transparent)}.chip.off{opacity:.34;filter:grayscale(.4)}
.tools{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin:0 0 14px}.tools input{border:1px solid rgba(50,38,25,.13);background:rgba(255,255,255,.78);border-radius:18px;padding:13px 15px;font:900 14px/1 system-ui;min-width:min(360px,100%);box-shadow:0 14px 34px rgba(63,48,30,.07);outline:none}.tools input:focus{border-color:#17110b;background:#fff}.tools button{border:1px solid rgba(50,38,25,.13);background:#17110b;color:#fff4dc;border-radius:999px;padding:12px 14px;font:950 13px/1 system-ui;cursor:pointer}
.map{position:relative;height:780px;border:1px solid rgba(255,255,255,.2);border-radius:32px;background:radial-gradient(circle at 26% 16%,rgba(99,190,255,.18),transparent 32%),radial-gradient(circle at 80% 14%,rgba(255,211,106,.16),transparent 26%),radial-gradient(circle at 52% 84%,rgba(102,231,191,.12),transparent 34%),linear-gradient(180deg,#111827,#080b12 58%,#040507);overflow:hidden;box-shadow:0 34px 90px rgba(29,21,14,.28),inset 0 1px 0 rgba(255,255,255,.16),inset 0 0 0 1px rgba(255,255,255,.05)}.map:before{content:"";position:absolute;inset:0;pointer-events:none;background-image:radial-gradient(circle,rgba(255,255,255,.34) 0 1px,transparent 1.4px);background-size:47px 47px;opacity:.28}.map:after{content:"";position:absolute;inset:0;pointer-events:none;background:radial-gradient(circle at 50% 46%,transparent 0 44%,rgba(0,0,0,.28) 100%)}
.graphCanvas{display:block;width:100%;height:100%;touch-action:none;cursor:grab;position:relative;z-index:1}.graphCanvas.dragging{cursor:grabbing}.hint{position:absolute;z-index:2;left:14px;bottom:14px;background:rgba(255,250,240,.88);border:1px solid rgba(255,255,255,.5);border-radius:999px;padding:9px 12px;color:#4c4035;font:900 12px/1.25 system-ui;pointer-events:none;box-shadow:0 12px 30px rgba(0,0,0,.18);backdrop-filter:blur(12px)}
.empty{position:absolute;z-index:2;inset:0;display:none;place-items:center;text-align:center;padding:28px;color:#ffecc6}.empty.show{display:grid}.empty strong{display:block;font:950 34px/.95 Georgia,serif;color:#fff8e8;margin-bottom:8px}.empty p{margin:0;max-width:520px;font:750 15px/1.5 system-ui;color:#d8c6a7}
.lines,.node,.kind,.nt,.ns,.reward{display:none}
.panel{display:grid;grid-template-columns:1.1fr .9fr;gap:16px;margin-top:18px}.detail,.queue{border:1px solid rgba(50,38,25,.12);background:rgba(255,255,255,.74);border-radius:24px;padding:18px;box-shadow:0 18px 44px rgba(63,48,30,.09);backdrop-filter:blur(12px)}.detail{border-top:5px solid var(--c,#d19b3e)}.detail h2,.queue h2{margin:0 0 8px;font:950 27px/.98 Georgia,serif;letter-spacing:-.03em;color:#17110b}.detail p,.queue p{color:#63574a;font:720 14px/1.55 system-ui}.detail .go{display:inline-flex;margin-top:10px;background:var(--c,#1f9d78);color:#fff;text-decoration:none;border-radius:999px;padding:12px 15px;font-weight:950}.detail button{margin-left:8px;border:1px solid rgba(50,38,25,.14);background:#fff;color:#1f1710;border-radius:999px;padding:12px 15px;font-weight:950;cursor:pointer}.todo{display:flex;align-items:center;justify-content:space-between;gap:10px;border-top:1px solid rgba(50,38,25,.09);padding:10px 0;color:#211910;font-weight:900}.todo span:last-child{color:#9b6b1f}
.nodePreview{position:absolute;z-index:6;width:min(390px,calc(100% - 24px));max-height:calc(100% - 24px);overflow:auto;background:rgba(255,250,240,.96);backdrop-filter:blur(18px);border:1px solid rgba(255,255,255,.58);border-top:6px solid var(--c,#1f9d78);border-radius:24px;padding:16px;box-shadow:0 26px 80px rgba(0,0,0,.38);opacity:0;visibility:hidden;pointer-events:none;transform:translate3d(0,10px,0);transition:opacity .12s ease,transform .12s ease}.nodePreview.show{opacity:1;visibility:visible;pointer-events:auto;transform:translate3d(0,0,0)}.pvTop{display:flex;align-items:flex-start;justify-content:space-between;gap:10px}.pvKicker{font:950 11px/1 system-ui;letter-spacing:.12em;text-transform:uppercase;color:var(--c,#1f9d78);margin-bottom:7px}.pvTitle{margin:0;font:950 26px/.98 Georgia,serif;letter-spacing:-.03em;color:#17110b}.pvClose{border:1px solid rgba(50,38,25,.14);background:#fff;border-radius:999px;width:32px;height:32px;font:950 17px/1 system-ui;cursor:pointer;color:#51463a}.pvSummary{margin:10px 0 0;color:#554a3f;font:720 14px/1.48 system-ui}.pvMeta{display:flex;flex-wrap:wrap;gap:7px;margin:12px 0}.pvPill{border:1px solid rgba(50,38,25,.11);background:#fff;border-radius:999px;padding:6px 9px;color:#3c3228;font:900 12px/1 system-ui}.pvLists{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:10px 0}.pvLists h4{margin:0 0 5px;font:950 11px/1 system-ui;letter-spacing:.08em;text-transform:uppercase;color:#74675a}.pvLists p{margin:0;color:#61564b;font:700 12px/1.38 system-ui}.pvActions{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}.pvActions a,.pvActions button{border:1px solid rgba(50,38,25,.13);border-radius:999px;padding:10px 12px;font:950 13px/1 system-ui;text-decoration:none;cursor:pointer}.pvActions .primary{background:var(--c,#1f9d78);border-color:var(--c,#1f9d78);color:#fff}.pvActions button{background:#fff;color:#1f1710}.pvActions button:disabled{opacity:.6;cursor:default}
@media(max-width:760px){.shell{width:min(560px,calc(100% - 20px));overflow:hidden;padding-top:12px}.top{align-items:flex-start;justify-content:flex-start;margin-bottom:12px}.top a{padding:9px 11px}.title{padding-top:2px}.title h1{font-size:40px;max-width:100%;overflow-wrap:anywhere}.title p{font-size:14.5px;line-height:1.38;max-width:360px;overflow-wrap:anywhere}.profile{grid-template-columns:1fr;border-radius:22px;padding:14px;margin:12px 0}.lvl{font-size:28px}.xp{font-size:13px}.bar{height:8px;margin-top:9px}.actions{justify-content:flex-start}.actions button{padding:9px 11px;font-size:13px}.legend{flex-wrap:nowrap;overflow-x:auto;padding-bottom:5px;margin:12px 0 10px;scrollbar-width:none}.legend::-webkit-scrollbar{display:none}.chip{flex:0 0 auto;padding:8px 10px;font-size:13px}.tools{margin-bottom:12px}.tools input{min-width:0;width:100%;padding:12px 14px}.tools button{padding:10px 13px}.map{height:590px;border-radius:26px}.panel{grid-template-columns:1fr}.detail button{display:block;margin:10px 0 0}.nodePreview{left:10px!important;right:10px;top:auto!important;bottom:10px;width:auto;max-height:68%;border-radius:22px}.pvLists{grid-template-columns:1fr}.pvTitle{font-size:23px}.hint{display:none}}
"""


JS = r"""
(function(){
const GRAPH=__GRAPH__;
const KEY='lifeos.learning.progress.v1';
const $=s=>document.querySelector(s);
const canvas=$('.graphCanvas'),ctx=canvas.getContext('2d',{alpha:true}),preview=$('.nodePreview');
let mode=new URLSearchParams(location.search).get('mode')==='global'?'global':'personal';
let selected=null,hovered=null,focusId=null,search='';
let filterDomains=new Set(GRAPH.domains.map(d=>d.id));
let nodes=[],edges=[],visibleById=new Map(),view={x:0,y:0,k:1},pointer=null,needsDraw=false;
let progressCache=null,doneCache=null;
let layoutMs=0,drawMs=0,renderMs=0,lastFrame=0,perfSent=false;
const PERF_BEACON=new URLSearchParams(location.search).get('perfBeacon');
const domainsById=new Map(GRAPH.domains.map(d=>[d.id,d]));
const allById=new Map(GRAPH.nodes.map(n=>[n.id,n]));
const outgoing=new Map(),incoming=new Map(),neighbors=new Map(),degree={};
for(const n of GRAPH.nodes){outgoing.set(n.id,[]);incoming.set(n.id,[]);neighbors.set(n.id,new Set([n.id]));degree[n.id]=0;}
for(const e of GRAPH.edges){
 if(!allById.has(e.from)||!allById.has(e.to))continue;
 outgoing.get(e.from).push(e);incoming.get(e.to).push(e);
 neighbors.get(e.from).add(e.to);neighbors.get(e.to).add(e.from);
 degree[e.from]=(degree[e.from]||0)+1;degree[e.to]=(degree[e.to]||0)+1;
}
function load(){try{return JSON.parse(localStorage.getItem(KEY)||'{}')}catch{return {}}}
function save(p){p.done=p.done||{};localStorage.setItem(KEY,JSON.stringify(p));progressCache=p;doneCache=new Set(Object.keys(p.done||{}))}
function progress(){if(progressCache)return progressCache;const p=load();p.done=p.done||{};progressCache=p;return p}
function doneSet(){if(!doneCache)doneCache=new Set(Object.keys(progress().done||{}));return doneCache}
function isDone(id){return doneSet().has(id)}
function level(xp){return Math.floor(Math.sqrt(xp/110))+1}
function nextLevelXp(lvl){return lvl*lvl*110}
function xp(){const p=progress();let total=0;for(const n of GRAPH.nodes){if(p.done[n.id])total+=+n.xp||0}return total}
function domain(id){return domainsById.get(id)||GRAPH.domains[0]||{id:'unknown',name:'Unknown',color:'#58636f'}}
function node(id){return allById.get(id)}
function escHtml(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function screenPoint(n){return {x:n.x*view.k+view.x,y:n.y*view.k+view.y}}
function clamp(v,min,max){return Math.max(min,Math.min(max,v))}
function previewPosition(){
 if(!preview||!preview.classList.contains('show')||!selected)return;
 const n=visibleById.get(selected);if(!n)return;
 const p=screenPoint(n),w=canvas.clientWidth||900,h=canvas.clientHeight||650;
 if(window.matchMedia('(max-width:760px)').matches){preview.style.left='10px';preview.style.top='auto';return;}
 const pw=preview.offsetWidth||370,ph=preview.offsetHeight||240;
 let left=p.x+n.r*view.k+18,top=p.y-ph/2;
 if(left+pw>w-12)left=p.x-pw-n.r*view.k-18;
 preview.style.left=clamp(left,12,Math.max(12,w-pw-12))+'px';
 preview.style.top=clamp(top,12,Math.max(12,h-ph-12))+'px';
}
function hidePreview(){if(preview){preview.classList.remove('show');preview.innerHTML=''}}
function showPreview(n){
 if(!preview||!n)return;const d=domain(n.domain),inc=(incoming.get(n.id)||[]).map(e=>node(e.from)?.title).filter(Boolean),out=(outgoing.get(n.id)||[]).map(e=>node(e.to)?.title).filter(Boolean),learned=isDone(n.id);
 preview.style.setProperty('--c',d.color);
 preview.innerHTML=`<div class="pvTop"><div><div class="pvKicker">${escHtml(d.name)} · ${escHtml(n.kind||'node')}</div><h3 class="pvTitle">${escHtml(n.title)}</h3></div><button class="pvClose" title="Close preview">×</button></div><p class="pvSummary">${escHtml(n.summary||'No summary yet.')}</p><div class="pvMeta"><span class="pvPill">${escHtml(n.xp||0)} XP</span><span class="pvPill">${learned?'Learned':'Not learned'}</span><span class="pvPill">${escHtml(n.difficulty_level||n.difficulty||'standard')}</span><span class="pvPill">${degree[n.id]||0} links</span></div><div class="pvLists"><div><h4>Builds on</h4><p>${inc.length?escHtml(inc.slice(0,3).join(', '))+(inc.length>3?'…':''):'No prerequisite links'}</p></div><div><h4>Can lead to</h4><p>${out.length?escHtml(out.slice(0,3).join(', '))+(out.length>3?'…':''):'No outgoing links yet'}</p></div></div><div class="pvActions"><a class="primary" href="${escHtml(n.url)}">Preview lesson</a><button class="pvLearn" ${learned?'disabled':''}>${learned?'Learned':'Mark learned'}</button><button class="pvFocus">Focus graph</button></div>`;
 preview.classList.add('show');
 preview.querySelector('.pvClose')?.addEventListener('click',hidePreview);
 preview.querySelector('.pvLearn')?.addEventListener('click',()=>complete(n.id));
 preview.querySelector('.pvFocus')?.addEventListener('click',()=>{focusId=n.id;render();showPreview(node(n.id))});
 requestAnimationFrame(previewPosition);
}
function outgoingDoneTargets(){const done=doneSet(),out=new Set();for(const id of done){for(const e of outgoing.get(id)||[])out.add(e.to)}return out}
function complete(id){const n=node(id);if(!n)return;const p=progress();p.done[n.id]={at:new Date().toISOString(),xp:n.xp,title:n.title,kind:n.kind,domain:n.domain};save(p);render();select(n.id,true)}
function reset(){if(confirm('Reset local LifeOS learning progress on this browser?')){localStorage.removeItem(KEY);progressCache={done:{}};doneCache=new Set();focusId=null;selected=null;render()}}
function renderProfile(){const got=xp(),lvl=level(got),next=nextLevelXp(lvl),prev=nextLevelXp(lvl-1),pct=Math.max(0,Math.min(100,((got-prev)/(next-prev))*100));$('.lvl').textContent='Level '+lvl;$('.xp').textContent=got+' XP / '+next+' XP';$('.bar i').style.width=pct+'%'}
function baseNodes(){
 if(mode==='global')return GRAPH.nodes.map(n=>({...n,_state:isDone(n.id)?'done':'global'}));
 const suggested=outgoingDoneTargets(),done=doneSet();
 return GRAPH.nodes.filter(n=>done.has(n.id)||suggested.has(n.id)).map(n=>({...n,_state:isDone(n.id)?'done':'suggested'}));
}
function neighborhoodIds(ids,root,hops=1){
 if(!root)return ids;const allowed=new Set(ids),keep=new Set([root]),front=new Set([root]);
 for(let i=0;i<hops;i++){const next=new Set();for(const id of front){for(const n of neighbors.get(id)||[]){if(allowed.has(n)&&!keep.has(n))next.add(n)}}for(const n of next)keep.add(n);front.clear();for(const n of next)front.add(n)}
 return ids.filter(id=>keep.has(id));
}
function computeVisible(){
 let raw=baseNodes();let ids=raw.map(n=>n.id);ids=neighborhoodIds(ids,focusId,1);
 const keep=new Set(ids);
 raw=raw.filter(n=>keep.has(n.id)&&filterDomains.has(n.domain));
 const set=new Set(raw.map(n=>n.id));
 edges=GRAPH.edges.filter(e=>set.has(e.from)&&set.has(e.to));
 nodes=raw.map(n=>({...n,r:7+Math.min(18,Math.sqrt(degree[n.id]||1)*4),_search:(String(n.title||'')+' '+String(n.summary||'')+' '+String(n.domain||'')).toLowerCase()}));
 visibleById=new Map(nodes.map(n=>[n.id,n]));
 $('.empty').classList.toggle('show',mode==='personal'&&!nodes.length);
}
function sortKey(n){return String(n.curriculum_track||'')+'|'+String(n.y??'')+'|'+String(n.order??'')+'|'+String(n.title||'')}
function computeLayout(){
 const t0=performance.now();
 const groups=new Map();for(const n of nodes){if(!groups.has(n.domain))groups.set(n.domain,[]);groups.get(n.domain).push(n)}
 const orderedDomains=GRAPH.domains.map(d=>d.id).filter(id=>groups.has(id));
 const total=Math.max(1,orderedDomains.length),worldR=Math.max(520,total*120),golden=2.399963229728653;
 if(focusId&&visibleById.has(focusId)&&nodes.length<90){
   const f=visibleById.get(focusId);f.x=0;f.y=0;let ring=0;
   for(const n of nodes.filter(n=>n.id!==focusId).sort((a,b)=>sortKey(a).localeCompare(sortKey(b)))){const a=ring*golden,r=90+Math.sqrt(ring)*58;n.x=Math.cos(a)*r;n.y=Math.sin(a)*r;ring++}
 }else{
   for(let di=0;di<orderedDomains.length;di++){
     const id=orderedDomains[di],arr=groups.get(id).sort((a,b)=>sortKey(a).localeCompare(sortKey(b)));
     const angle=(-Math.PI/2)+(di/total)*Math.PI*2,cx=Math.cos(angle)*worldR,cy=Math.sin(angle)*worldR;
     const clusterShift=(di%2)*0.31;
     for(let i=0;i<arr.length;i++){
       const n=arr[i];
       if(arr.length===1){n.x=cx;n.y=cy;continue}
       const a=i*golden+clusterShift,r=34*Math.sqrt(i)+18;
       n.x=cx+Math.cos(a)*r;n.y=cy+Math.sin(a)*r;
     }
   }
 }
 layoutMs=performance.now()-t0;
}
function resize(){const r=canvas.getBoundingClientRect(),dpr=window.devicePixelRatio||1;const w=Math.max(1,Math.floor(r.width*dpr)),h=Math.max(1,Math.floor(r.height*dpr));if(canvas.width!==w||canvas.height!==h){canvas.width=w;canvas.height=h;ctx.setTransform(dpr,0,0,dpr,0,0);fitView();draw()}}
function fitView(){
 if(!nodes.length){view={x:(canvas.clientWidth||900)/2,y:(canvas.clientHeight||650)/2,k:1};return}
 let minX=Infinity,minY=Infinity,maxX=-Infinity,maxY=-Infinity;
 for(const n of nodes){minX=Math.min(minX,n.x-n.r);minY=Math.min(minY,n.y-n.r);maxX=Math.max(maxX,n.x+n.r);maxY=Math.max(maxY,n.y+n.r)}
 const w=canvas.clientWidth||900,h=canvas.clientHeight||650,pad=120,bw=Math.max(1,maxX-minX),bh=Math.max(1,maxY-minY);
 const k=Math.max(.12,Math.min(1.7,Math.min(w/(bw+pad),h/(bh+pad))));
 view.k=k;view.x=w/2-((minX+maxX)/2)*k;view.y=h/2-((minY+maxY)/2)*k;
}
function worldFromEvent(e){const r=canvas.getBoundingClientRect();return {x:(e.clientX-r.left-view.x)/view.k,y:(e.clientY-r.top-view.y)/view.k}}
function scheduleDraw(){if(needsDraw)return;needsDraw=true;requestAnimationFrame(()=>{needsDraw=false;draw()})}
function visibleEdge(e){return visibleById.has(e.from)&&visibleById.has(e.to)}
function searchMatch(n){if(!search)return true;return n._search.includes(search.toLowerCase())}
function rgba(hex,a){const h=String(hex||'').replace('#','');if(h.length<6)return `rgba(255,255,255,${a})`;const n=parseInt(h.slice(0,6),16);return `rgba(${(n>>16)&255},${(n>>8)&255},${n&255},${a})`}
function updatePerf(){const perf={renderMs:+renderMs.toFixed(2),layoutMs:+layoutMs.toFixed(2),drawMs:+drawMs.toFixed(2),lastFrameMs:+lastFrame.toFixed(2),nodes:nodes.length,edges:edges.length,totalGraphNodes:GRAPH.nodes.length,totalGraphEdges:GRAPH.edges.length,mode};window.LifeOSGraphPerf=perf;let el=document.getElementById('graph-perf');if(!el){el=document.createElement('pre');el.id='graph-perf';el.hidden=true;document.body.appendChild(el)}el.textContent=JSON.stringify(perf);if(PERF_BEACON&&!perfSent&&perf.renderMs>0&&perf.drawMs>0){perfSent=true;const img=new Image();img.src='http://127.0.0.1:'+encodeURIComponent(PERF_BEACON)+'/perf?d='+encodeURIComponent(JSON.stringify(perf))}}
function draw(){
 const t0=performance.now(),w=canvas.clientWidth||900,h=canvas.clientHeight||650;ctx.clearRect(0,0,w,h);ctx.save();ctx.translate(view.x,view.y);ctx.scale(view.k,view.k);
 const hi=hovered?neighbors.get(hovered.id):null,matched=search?new Set(nodes.filter(searchMatch).map(n=>n.id)):null,done=doneSet();
 ctx.lineCap='round';
 for(const e of edges){const a=visibleById.get(e.from),b=visibleById.get(e.to);if(!a||!b)continue;const active=!hi||(hi.has(a.id)&&hi.has(b.id)),searched=!matched||(matched.has(a.id)||matched.has(b.id));ctx.globalAlpha=(active&&searched)?0.34:0.045;ctx.strokeStyle=done.has(a.id)&&done.has(b.id)?'rgba(102,231,191,.72)':'rgba(211,225,242,.48)';ctx.lineWidth=Math.max(1,1.55/view.k);ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);ctx.stroke()}
 for(const n of nodes){const d=domain(n.domain),active=!hi||hi.has(n.id),searched=!matched||matched.has(n.id),learned=done.has(n.id),alpha=(active&&searched)?1:.16;ctx.globalAlpha=alpha*.18;ctx.fillStyle=rgba(d.color,.9);ctx.beginPath();ctx.arc(n.x,n.y,n.r+8,0,Math.PI*2);ctx.fill();ctx.globalAlpha=alpha;ctx.beginPath();ctx.fillStyle=learned?'#dfffea':d.color;ctx.strokeStyle=selected===n.id?'#fff2bd':(n._state==='suggested'?'#ffd36a':'rgba(255,255,255,.78)');ctx.lineWidth=Math.max(1.4,(selected===n.id?4.2:2)/view.k);ctx.arc(n.x,n.y,n.r,0,Math.PI*2);ctx.fill();ctx.stroke();if(selected===n.id){ctx.globalAlpha=.72;ctx.beginPath();ctx.strokeStyle='rgba(255,242,189,.75)';ctx.lineWidth=Math.max(1.4,2.8/view.k);ctx.arc(n.x,n.y,n.r+9,0,Math.PI*2);ctx.stroke();ctx.globalAlpha=alpha}if(n.kind==='game'){ctx.beginPath();ctx.strokeStyle='rgba(5,8,13,.48)';ctx.lineWidth=Math.max(1,2/view.k);ctx.moveTo(n.x-n.r*.42,n.y);ctx.lineTo(n.x+n.r*.42,n.y);ctx.moveTo(n.x,n.y-n.r*.42);ctx.lineTo(n.x,n.y+n.r*.42);ctx.stroke()}}
 const showAllLabels=view.k>1.05&&nodes.length<220,important=hovered?neighbors.get(hovered.id):new Set(selected?[selected]:[]);ctx.textAlign='center';ctx.textBaseline='top';ctx.font=`${Math.max(10,12/view.k)}px Inter, system-ui`;
 for(const n of nodes){if(!(showAllLabels||important.has(n.id)))continue;const active=!hi||hi.has(n.id),searched=!matched||matched.has(n.id);if(!active&&!searched)continue;ctx.globalAlpha=(active&&searched)?0.96:.22;ctx.fillStyle='#fff7e8';wrapLabel(n.title,n.x,n.y+n.r+6,138/view.k,14/view.k)}
 ctx.restore();ctx.globalAlpha=1;drawMs=performance.now()-t0;lastFrame=drawMs;updatePerf();previewPosition();
}
function wrapLabel(text,x,y,max,line){const words=String(text).split(/\s+/),lines=[];let cur='';for(const w of words){const t=cur?cur+' '+w:w;if(ctx.measureText(t).width>max&&cur){lines.push(cur);cur=w}else cur=t;if(lines.length>1)break}if(cur&&lines.length<2)lines.push(cur);for(let i=0;i<lines.length;i++)ctx.fillText(lines[i],x,y+i*line)}
function hit(e){const p=worldFromEvent(e);let best=null,bd=Infinity;for(const n of nodes){const d=Math.hypot(n.x-p.x,n.y-p.y);if(d<n.r+8/view.k&&d<bd){best=n;bd=d}}return best}
function renderQueue(){const done=doneSet(),suggested=[...outgoingDoneTargets()].map(node).filter(Boolean).filter(n=>!done.has(n.id));const roots=GRAPH.nodes.filter(n=>!incoming.get(n.id)?.length&&!done.has(n.id)).slice(0,8);const list=(suggested.length?suggested:roots).slice(0,8);$('.queueList').innerHTML=list.map(n=>`<div class="todo"><span>${n.title}</span><span>${suggested.includes(n)?'next':'+ '+n.xp+' XP'}</span></div>`).join('')}
function select(id,showCard=false){selected=id;const n=id?node(id):null;if(!n){hidePreview();$('.detail').innerHTML='<h2>Personal graph</h2><p>Complete articles or games and this graph becomes your map. Use global mode to browse the full library.</p>';scheduleDraw();return}const d=domain(n.domain),inc=(incoming.get(n.id)||[]).map(e=>node(e.from)?.title).filter(Boolean),out=(outgoing.get(n.id)||[]).map(e=>node(e.to)?.title).filter(Boolean);$('.detail').style.setProperty('--c',d.color);$('.detail').innerHTML=`<h2>${escHtml(n.title)}</h2><p>${escHtml(n.summary||'')}</p><p><b>Domain:</b> ${escHtml(d.name)}. <b>Difficulty:</b> ${escHtml(n.difficulty_level||n.difficulty||'standard')}. <b>Status:</b> ${isDone(n.id)?'learned':'not learned yet'}.</p>`+(inc.length?`<p><b>Builds on:</b> ${escHtml(inc.slice(0,6).join(', '))}${inc.length>6?'…':''}</p>`:'')+(out.length?`<p><b>Can lead to:</b> ${escHtml(out.slice(0,6).join(', '))}${out.length>6?'…':''}</p>`:'')+`<a class="go" href="${escHtml(n.url)}">${n.kind==='game'?'Play':'Read'}</a><button data-complete="${escHtml(n.id)}">${isDone(n.id)?'Completed':'Mark learned'}</button><button data-focus="${escHtml(n.id)}">Focus neighborhood</button>`;const cb=$('.detail [data-complete]');if(cb)cb.addEventListener('click',()=>complete(n.id));const fb=$('.detail [data-focus]');if(fb)fb.addEventListener('click',()=>{focusId=n.id;render();showPreview(n)});if(showCard)showPreview(n);scheduleDraw()}
function render(){const t0=performance.now();document.querySelectorAll('[data-mode]').forEach(b=>b.classList.toggle('active',b.dataset.mode===mode));renderProfile();computeVisible();computeLayout();fitView();renderQueue();if(selected&&!visibleById.has(selected))selected=null;if(!selected&&nodes.length)selected=nodes[0].id;select(selected,false);draw();renderMs=performance.now()-t0;updatePerf()}
canvas.addEventListener('wheel',e=>{e.preventDefault();const before=worldFromEvent(e),factor=Math.exp(-e.deltaY*.001);view.k=Math.max(.08,Math.min(4.5,view.k*factor));const r=canvas.getBoundingClientRect();view.x=e.clientX-r.left-before.x*view.k;view.y=e.clientY-r.top-before.y*view.k;scheduleDraw()},{passive:false});
canvas.addEventListener('pointermove',e=>{const h=hit(e);if(h!==hovered){hovered=h;scheduleDraw()}if(pointer){if(pointer.node){const p=worldFromEvent(e);pointer.node.x=p.x;pointer.node.y=p.y}else{view.x+=e.clientX-pointer.x;view.y+=e.clientY-pointer.y;pointer.x=e.clientX;pointer.y=e.clientY}scheduleDraw()}});
canvas.addEventListener('pointerdown',e=>{canvas.setPointerCapture(e.pointerId);const n=hit(e);pointer={x:e.clientX,y:e.clientY,node:n};canvas.classList.add('dragging');if(n)select(n.id,true)});
canvas.addEventListener('pointerup',e=>{const now=Date.now();if(now-(pointer?.lastTap||0)<330){fitView()}pointer=null;canvas.classList.remove('dragging');scheduleDraw()});
canvas.addEventListener('dblclick',()=>{fitView();scheduleDraw()});
document.querySelectorAll('[data-mode]').forEach(b=>b.addEventListener('click',()=>{mode=b.dataset.mode;focusId=null;selected=null;render()}));
document.querySelectorAll('[data-domain]').forEach(b=>b.addEventListener('click',()=>{const id=b.dataset.domain;if(filterDomains.has(id))filterDomains.delete(id);else filterDomains.add(id);b.classList.toggle('off',!filterDomains.has(id));render()}));
$('.reset').addEventListener('click',reset);$('.clearFocus').addEventListener('click',()=>{focusId=null;search='';$('.search').value='';render()});$('.search').addEventListener('input',e=>{search=e.target.value;scheduleDraw()});
function syncServerProgress(){fetch('/output/learn/progress.json',{cache:'no-store'}).then(r=>r.ok?r.json():null).then(p=>{if(!p||!p.done)return;const cur=progress();let changed=false;for(const [id,item] of Object.entries(p.done)){if(!cur.done[id]){cur.done[id]=item;changed=true}}if(changed){save(cur);render()}}).catch(()=>{})}
window.addEventListener('resize',()=>{resize();fitView();scheduleDraw()});resize();render();syncServerProgress();window.LifeOSGraph={complete,progress,render,preview:id=>select(id,true),perf:()=>window.LifeOSGraphPerf};
})();
"""


def render() -> str:
    chips = "".join(
        f"<button class='chip' data-domain='{d['id']}' style='--c:{d['color']}'><i class='dot'></i>{d['name']}</button>"
        for d in GRAPH["domains"]
    )
    return f"""<!doctype html><html lang='en'><head>
<meta charset='utf-8'>
<meta name='viewport' content='width=device-width,initial-scale=1,viewport-fit=cover'>
<meta name='color-scheme' content='light'>
<title>LifeOS Personal Knowledge Graph</title>
<style>{CSS}</style></head>
<body><main class='shell'>
<div class='top'><a href='/learn'>&larr; Field Notes</a><a href='/output/learn/learning-system.html'>Training Queue</a><a href='/m'>Control &rarr;</a></div>
<section class='title'><h1>Knowledge Graph</h1><p>Your learning atlas: every lesson is a constellation, and only the nodes you actually learn become part of your personal map.</p></section>
<section class='profile'><div><div class='lvl'>Level 1</div><div class='xp'>0 XP</div><div class='bar'><i></i></div></div><div class='actions'><button data-mode='personal' class='active'>Personal graph</button><button data-mode='global'>Global library</button><button class='ghost reset'>Reset</button></div></section>
<div class='legend'>{chips}</div>
<div class='tools'><input class='search' placeholder='Search concepts, domains, games...' autocomplete='off'><button class='clearFocus'>Clear focus</button></div>
<section class='map' aria-label='LifeOS personal knowledge graph'><canvas class='graphCanvas'></canvas><div class='nodePreview' aria-live='polite'></div><div class='empty'><div><strong>No personal graph yet</strong><p>Read an article or complete a game. Once you mark it learned, that node appears here. The global library is available above if you want to browse possible starts.</p></div></div><div class='hint'>Wheel/pinch to zoom, drag background to pan, drag nodes to rearrange.</div></section>
<section class='panel'><div class='detail'></div><div class='queue'><h2>Possible Starts / Next Steps</h2><p>Suggestions come from the global library, but only learned nodes enter your personal graph.</p><div class='queueList'></div></div></section>
</main><script>{JS.replace('__GRAPH__', json.dumps(GRAPH))}</script></body></html>"""


def build() -> dict:
    global GRAPH
    OUT.mkdir(parents=True, exist_ok=True)
    GRAPH = save_graph_store(GRAPH)
    (OUT / "skill-tree.html").write_text(render(), encoding="utf-8")
    (OUT / "knowledge-graph.json").write_text(json.dumps(GRAPH, indent=2), encoding="utf-8")
    (OUT / "skill-tree.json").write_text(json.dumps(GRAPH, indent=2), encoding="utf-8")
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "url": "/output/learn/skill-tree.html",
        "nodes": len(GRAPH["nodes"]),
        "edges": len(GRAPH["edges"]),
        "domains": len(GRAPH["domains"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the LifeOS personal knowledge graph")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("build", help="Build skill-tree.html into output/learn/")
    args = parser.parse_args()
    if args.cmd == "build":
        print(json.dumps(build(), indent=2))
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
