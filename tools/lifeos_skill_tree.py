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
*{box-sizing:border-box}html,body{margin:0;min-height:100%;background:#f7f8fa;color:#17202a;font-family:Inter,system-ui,-apple-system,sans-serif}
body{background:linear-gradient(180deg,#fbfcfd,#eef3f6 48%,#f8fafb)}a{color:inherit}
.shell{width:min(1180px,calc(100% - 32px));margin:0 auto;padding:22px 0 48px}
.top{display:flex;align-items:center;justify-content:space-between;gap:14px;margin-bottom:18px;flex-wrap:wrap}.top a{color:#5b6875;text-decoration:none;font-weight:850}
.title{border-bottom:1px solid #d8e0e6;padding-bottom:18px}.title h1{margin:2px 0 8px;font:900 clamp(38px,6vw,72px)/.92 Georgia,serif;color:#111820}.title p{margin:0;color:#536170;font:650 17px/1.55 system-ui;max-width:800px}
.profile{display:grid;grid-template-columns:1fr auto;gap:14px;align-items:center;border:1px solid #d6dee5;background:#fff;border-radius:8px;padding:14px 16px;margin:18px 0;box-shadow:0 10px 30px rgba(24,38,55,.06)}
.lvl{font:900 28px/1 system-ui}.xp{color:#657482;font-weight:800}.bar{height:10px;background:#e4eaf0;border-radius:999px;overflow:hidden;margin-top:9px}.bar i{display:block;height:100%;width:0;background:linear-gradient(90deg,#1f9d78,#4d7cff,#d86b8a)}
.actions{display:flex;gap:10px;flex-wrap:wrap}.actions button,.actions a{border:1px solid #ccd6de;background:#111820;color:#fff;border-radius:7px;padding:10px 12px;font-weight:900;text-decoration:none;cursor:pointer}.actions .ghost{background:#fff;color:#17202a}.actions .active{background:#1f9d78;color:#fff;border-color:#1f9d78}
.legend{display:flex;gap:8px;flex-wrap:wrap;margin:18px 0}.chip{display:flex;align-items:center;gap:7px;border:1px solid #d6dee5;background:#fff;border-radius:999px;padding:7px 10px;font-weight:800;color:#344251}.dot{width:10px;height:10px;border-radius:50%;background:var(--c)}
.map{position:relative;height:780px;border:1px solid #d6dee5;border-radius:8px;background:linear-gradient(#f3f6f8 1px,transparent 1px),linear-gradient(90deg,#f3f6f8 1px,transparent 1px),#fff;background-size:44px 44px;overflow:hidden;box-shadow:inset 0 0 0 1px rgba(255,255,255,.7)}
.graphCanvas{display:block;width:100%;height:100%;touch-action:none;cursor:grab}.graphCanvas.dragging{cursor:grabbing}
.tools{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin:14px 0}.tools input{border:1px solid #cdd7df;background:#fff;border-radius:7px;padding:10px 12px;font:800 14px/1 system-ui;min-width:230px}.tools button{border:1px solid #cdd7df;background:#fff;border-radius:7px;padding:10px 12px;font:900 13px/1 system-ui;cursor:pointer}.chip{cursor:pointer}.chip.off{opacity:.35}.hint{position:absolute;left:12px;bottom:10px;background:rgba(255,255,255,.9);border:1px solid #d6dee5;border-radius:7px;padding:7px 9px;color:#64717d;font:800 12px/1.25 system-ui;pointer-events:none}
.empty{position:absolute;inset:0;display:none;place-items:center;text-align:center;padding:28px;color:#596877}.empty.show{display:grid}.empty strong{display:block;font:900 28px/1.05 Georgia,serif;color:#17202a;margin-bottom:8px}.empty p{margin:0;max-width:520px;font:650 15px/1.5 system-ui}
.lines{position:absolute;inset:0;width:100%;height:100%;pointer-events:none}.lines line{stroke:#bbc7d1;stroke-width:3;stroke-linecap:round}.lines line.done{stroke:#1f9d78}.lines line.suggested{stroke:#d79d3f;stroke-dasharray:7 7}
.node{position:absolute;left:calc(var(--x)*1%);top:calc(var(--y)*1%);width:184px;min-height:96px;transform:translate(-50%,-50%);border:1px solid #c8d2db;border-top:4px solid var(--c);background:#fff;color:#17202a;border-radius:8px;padding:11px;text-align:left;box-shadow:0 12px 26px rgba(24,38,55,.13);cursor:pointer;transition:transform .16s,opacity .16s,border-color .16s}
.node:hover{transform:translate(-50%,-54%);border-color:#8fa1b1}.node.global{opacity:.7}.node.done{background:#edf8f3;border-color:#1f9d78}.node.suggested{box-shadow:0 12px 26px rgba(215,157,63,.18),0 0 0 4px rgba(215,157,63,.14)}
.kind{font:900 10px/1 system-ui;text-transform:uppercase;letter-spacing:.08em;color:var(--c)}.nt{font:900 17px/1.08 system-ui;margin:6px 0 4px}.ns{font:700 12px/1.32 system-ui;color:#5c6a77}.reward{margin-top:8px;font:900 12px/1 system-ui;color:#17202a}
.panel{display:grid;grid-template-columns:1.1fr .9fr;gap:14px;margin-top:18px}.detail,.queue{border:1px solid #d6dee5;background:#fff;border-radius:8px;padding:16px;box-shadow:0 10px 30px rgba(24,38,55,.06)}.detail h2,.queue h2{margin:0 0 8px;font:900 24px/1 system-ui}.detail p,.queue p{color:#596877;font:650 14px/1.5 system-ui}.detail .go{display:inline-flex;margin-top:10px;background:var(--c,#1f9d78);color:#fff;text-decoration:none;border-radius:7px;padding:11px 13px;font-weight:900}.detail button{margin-left:8px;border:1px solid #ccd6de;background:#fff;color:#17202a;border-radius:7px;padding:11px 13px;font-weight:900;cursor:pointer}.todo{display:flex;align-items:center;justify-content:space-between;gap:10px;border-top:1px solid #edf1f4;padding:9px 0;color:#17202a;font-weight:850}.todo span:last-child{color:#9b6b1f}
.nodePreview{position:absolute;z-index:6;width:min(370px,calc(100% - 24px));max-height:calc(100% - 24px);overflow:auto;background:rgba(255,255,255,.97);backdrop-filter:blur(12px);border:1px solid #ccd7df;border-top:5px solid var(--c,#1f9d78);border-radius:16px;padding:14px 14px 13px;box-shadow:0 22px 60px rgba(18,32,46,.26);opacity:0;visibility:hidden;pointer-events:none;transform:translate3d(0,8px,0);transition:opacity .12s ease,transform .12s ease}.nodePreview.show{opacity:1;visibility:visible;pointer-events:auto;transform:translate3d(0,0,0)}.pvTop{display:flex;align-items:flex-start;justify-content:space-between;gap:10px}.pvKicker{font:900 11px/1 system-ui;letter-spacing:.11em;text-transform:uppercase;color:var(--c,#1f9d78);margin-bottom:6px}.pvTitle{margin:0;font:950 24px/1.02 system-ui;color:#111820}.pvClose{border:1px solid #d2dce4;background:#fff;border-radius:999px;width:30px;height:30px;font:900 17px/1 system-ui;cursor:pointer;color:#51606e}.pvSummary{margin:9px 0 0;color:#526271;font:650 14px/1.45 system-ui}.pvMeta{display:flex;flex-wrap:wrap;gap:7px;margin:11px 0}.pvPill{border:1px solid #d8e1e8;background:#f7fafc;border-radius:999px;padding:5px 8px;color:#394958;font:850 12px/1 system-ui}.pvLists{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:10px 0}.pvLists h4{margin:0 0 5px;font:900 11px/1 system-ui;letter-spacing:.08em;text-transform:uppercase;color:#6b7885}.pvLists p{margin:0;color:#5f6e7b;font:650 12px/1.35 system-ui}.pvActions{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}.pvActions a,.pvActions button{border:1px solid #ccd6de;border-radius:10px;padding:9px 10px;font:900 13px/1 system-ui;text-decoration:none;cursor:pointer}.pvActions .primary{background:var(--c,#1f9d78);border-color:var(--c,#1f9d78);color:#fff}.pvActions button{background:#fff;color:#17202a}.pvActions button:disabled{opacity:.6;cursor:default}
@media(max-width:760px){.shell{width:min(560px,calc(100% - 20px));overflow:hidden}.top{align-items:flex-start;justify-content:flex-start}.title h1{font-size:36px;max-width:100%;overflow-wrap:anywhere}.title p{max-width:340px;overflow-wrap:anywhere}.profile{grid-template-columns:1fr}.legend{flex-wrap:nowrap;overflow-x:auto;padding-bottom:4px}.chip{flex:0 0 auto}.tools input{min-width:0;width:100%}.map{height:560px}.panel{grid-template-columns:1fr}.detail button{display:block;margin:10px 0 0}.nodePreview{left:10px!important;right:10px;top:auto!important;bottom:10px;width:auto;max-height:68%;border-radius:18px}.pvLists{grid-template-columns:1fr}.pvTitle{font-size:21px}.hint{display:none}}
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
function save(p){localStorage.setItem(KEY,JSON.stringify(p))}
function progress(){const p=load();p.done=p.done||{};return p}
function isDone(id){return !!progress().done[id]}
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
function doneSet(){return new Set(Object.keys(progress().done||{}))}
function outgoingDoneTargets(){const done=doneSet(),out=new Set();for(const id of done){for(const e of outgoing.get(id)||[])out.add(e.to)}return out}
function complete(id){const n=node(id);if(!n)return;const p=progress();p.done[n.id]={at:new Date().toISOString(),xp:n.xp,title:n.title,kind:n.kind,domain:n.domain};save(p);render();select(n.id,true)}
function reset(){if(confirm('Reset local LifeOS learning progress on this browser?')){localStorage.removeItem(KEY);focusId=null;selected=null;render()}}
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
 raw=raw.filter(n=>ids.includes(n.id)&&filterDomains.has(n.domain));
 const set=new Set(raw.map(n=>n.id));
 edges=GRAPH.edges.filter(e=>set.has(e.from)&&set.has(e.to));
 nodes=raw.map(n=>({...n,r:7+Math.min(18,Math.sqrt(degree[n.id]||1)*4)}));
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
function searchMatch(n){if(!search)return true;const q=search.toLowerCase();return (n.title+' '+(n.summary||'')+' '+n.domain).toLowerCase().includes(q)}
function updatePerf(){const perf={renderMs:+renderMs.toFixed(2),layoutMs:+layoutMs.toFixed(2),drawMs:+drawMs.toFixed(2),lastFrameMs:+lastFrame.toFixed(2),nodes:nodes.length,edges:edges.length,totalGraphNodes:GRAPH.nodes.length,totalGraphEdges:GRAPH.edges.length,mode};window.LifeOSGraphPerf=perf;let el=document.getElementById('graph-perf');if(!el){el=document.createElement('pre');el.id='graph-perf';el.hidden=true;document.body.appendChild(el)}el.textContent=JSON.stringify(perf);if(PERF_BEACON&&!perfSent&&perf.renderMs>0&&perf.drawMs>0){perfSent=true;const img=new Image();img.src='http://127.0.0.1:'+encodeURIComponent(PERF_BEACON)+'/perf?d='+encodeURIComponent(JSON.stringify(perf))}}
function draw(){
 const t0=performance.now(),w=canvas.clientWidth||900,h=canvas.clientHeight||650;ctx.clearRect(0,0,w,h);ctx.save();ctx.translate(view.x,view.y);ctx.scale(view.k,view.k);
 const hi=hovered?neighbors.get(hovered.id):null,matched=new Set(nodes.filter(searchMatch).map(n=>n.id));
 ctx.lineCap='round';
 for(const e of edges){const a=visibleById.get(e.from),b=visibleById.get(e.to);if(!a||!b)continue;const active=!hi||(hi.has(a.id)&&hi.has(b.id)),searched=!search||(matched.has(a.id)||matched.has(b.id));ctx.globalAlpha=(active&&searched)?0.48:0.055;ctx.strokeStyle=isDone(a.id)&&isDone(b.id)?'#1f9d78':'#aeb9c3';ctx.lineWidth=Math.max(1.1,1.8/view.k);ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);ctx.stroke()}
 for(const n of nodes){const d=domain(n.domain),active=!hi||hi.has(n.id),searched=!search||matched.has(n.id);ctx.globalAlpha=(active&&searched)?1:.16;ctx.beginPath();ctx.fillStyle=isDone(n.id)?'#dff5eb':d.color;ctx.strokeStyle=selected===n.id?'#111820':(n._state==='suggested'?'#d79d3f':'#ffffff');ctx.lineWidth=Math.max(1.4,(selected===n.id?4:2)/view.k);ctx.arc(n.x,n.y,n.r,0,Math.PI*2);ctx.fill();ctx.stroke();if(n.kind==='game'){ctx.beginPath();ctx.strokeStyle='rgba(0,0,0,.35)';ctx.lineWidth=Math.max(1,2/view.k);ctx.moveTo(n.x-n.r*.42,n.y);ctx.lineTo(n.x+n.r*.42,n.y);ctx.moveTo(n.x,n.y-n.r*.42);ctx.lineTo(n.x,n.y+n.r*.42);ctx.stroke()}}
 const showAllLabels=view.k>.72,important=hovered?neighbors.get(hovered.id):new Set(selected?[selected]:[]);ctx.textAlign='center';ctx.textBaseline='top';ctx.font=`${Math.max(10,12/view.k)}px Inter, system-ui`;
 for(const n of nodes){if(!(showAllLabels||important.has(n.id)))continue;const active=!hi||hi.has(n.id),searched=!search||matched.has(n.id);if(!active&&!searched)continue;ctx.globalAlpha=(active&&searched)?0.92:.2;ctx.fillStyle='#17202a';wrapLabel(n.title,n.x,n.y+n.r+5,130/view.k,14/view.k)}
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
<section class='title'><h1>Knowledge Graph</h1><p>Your personal graph only shows what you have actually learned. The global library underneath stays separated into honest topic islands.</p></section>
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
