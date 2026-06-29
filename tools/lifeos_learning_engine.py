#!/usr/bin/env python3
"""LifeOS learning engine.

Builds a Math Academy-inspired layer on top of the LifeOS knowledge graph:
source-backed principles, a personal student model, due reviews, frontier
selection, interleaving, and an ingestion contract for long documents.

Build: python tools/lifeos_learning_engine.py build
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from typing import Any

from lifeos_paths import VAULT_ROOT
from lifeos_skill_tree import load_graph_store

OUT = VAULT_ROOT / "output" / "learn"


SOURCE_NOTES: list[dict[str, str]] = [
    {
        "id": "mathacademy-how-ai-works",
        "title": "Math Academy: How Our AI Works",
        "url": "https://www.mathacademy.com/how-our-ai-works",
        "takeaway": (
            "Treat learning as a dynamic student model over a granular knowledge graph. "
            "The system should decide what the learner is ready for next, not just list content."
        ),
    },
    {
        "id": "mathacademy-pedagogy",
        "title": "Math Academy: Pedagogy",
        "url": "https://www.mathacademy.com/pedagogy",
        "takeaway": (
            "Use active recall, spaced review, mixed practice, and mastery thresholds. "
            "Reading is input; durable learning requires retrieval and practice."
        ),
    },
]


PRINCIPLES: list[dict[str, str]] = [
    {
        "id": "atomic-concepts",
        "name": "Atomic concepts",
        "rule": "Break lessons, books, and games into concept nodes small enough to test or practice.",
        "implemented_as": "Every article/game becomes a graph node with domain, kind, XP, and source metadata.",
    },
    {
        "id": "typed-graph",
        "name": "Typed knowledge graph",
        "rule": "Edges must mean something real: prerequisite, practice, analogy, application, or review.",
        "implemented_as": "Unrelated domains remain separate islands until an explicit edge is justified.",
    },
    {
        "id": "student-model",
        "name": "Personal student model",
        "rule": "The user graph is an overlay on top of the global library, not the whole library.",
        "implemented_as": "Browser progress stores learned nodes and review stages in localStorage.",
    },
    {
        "id": "knowledge-frontier",
        "name": "Knowledge frontier",
        "rule": "Recommend nodes whose prerequisites are satisfied, plus a small number of new roots.",
        "implemented_as": "The training queue computes frontier nodes from completed prerequisites.",
    },
    {
        "id": "retrieval-first",
        "name": "Retrieval first",
        "rule": "A lesson should end in recall, manipulation, prediction, or a game, not passive rereading.",
        "implemented_as": "Practice games and review prompts outrank fresh reading when items are due.",
    },
    {
        "id": "spaced-interleaved",
        "name": "Spaced and interleaved",
        "rule": "Due reviews come first; new material is mixed across domains to prevent fake fluency.",
        "implemented_as": "The queue separates due review, frontier, and mixed practice lanes.",
    },
]


INGESTION_CONTRACT: dict[str, Any] = {
    "input_types": ["markdown", "txt", "pdf_text", "web_article"],
    "pipeline": [
        "capture_source_metadata",
        "chunk_into_sections",
        "extract_atomic_concepts",
        "extract_typed_edges",
        "attach_source_pointers",
        "generate_blog_lesson",
        "generate_practice_game_spec",
        "merge_into_global_graph_after_review",
    ],
    "node_schema": {
        "id": "stable-kebab-id",
        "domain": "history|physics|systems|growth|culture|thinking|custom|math|startup",
        "title": "Concept title",
        "kind": "article|game|concept|source",
        "xp": "integer",
        "url": "/output/learn/example.html",
        "summary": "One sentence concept meaning",
        "sources": [{"source_id": "book-or-doc-id", "locator": "chapter/section/page"}],
        "difficulty": "intro|core|hard",
        "estimated_minutes": "integer",
    },
    "edge_schema": {
        "from": "source-node-id",
        "to": "target-node-id",
        "relation": "prerequisite|practice|application|analogy|review",
        "reason": "Short reason this edge is real",
        "confidence": "0.0-1.0",
    },
    "copyright_rule": (
        "Store summaries, source IDs, locators, and short compliant excerpts only when needed. "
        "Do not paste books or long copyrighted docs into generated pages."
    ),
}


CSS = """
*{box-sizing:border-box}html,body{margin:0;min-height:100%;background:#f6f4ee;color:#16191c;font-family:Inter,system-ui,-apple-system,sans-serif}
a{color:inherit}.shell{width:min(1120px,calc(100% - 32px));margin:0 auto;padding:20px 0 48px}.top{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;border-bottom:1px solid #d7d1c4;padding-bottom:14px;margin-bottom:24px}.top a{text-decoration:none;color:#5d625d;font-weight:850}
.hero{display:grid;grid-template-columns:minmax(0,1fr) 320px;gap:28px;align-items:start;border-bottom:3px solid #16191c;padding-bottom:24px}.k{font:900 12px/1 system-ui;letter-spacing:.16em;text-transform:uppercase;color:#926b25}.hero h1{font:850 clamp(44px,7vw,78px)/.9 Georgia,serif;letter-spacing:0;margin:8px 0 12px}.hero p{font:500 19px/1.55 Georgia,serif;color:#434a45;margin:0;max-width:760px}.sourcebox{border:1px solid #d7d1c4;background:#fff;padding:12px}.sourcebox strong{display:block;font:900 14px/1.2 system-ui;margin:0 0 5px}.sourcebox p{margin:0 0 8px;color:#4e5650;font:650 13px/1.38 system-ui}.sourcebox a{display:block;color:#315f9d;font:750 11px/1.25 system-ui;margin:0 0 8px;overflow-wrap:anywhere}
.model{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin:22px 0}.metric{background:#fff;border:1px solid #d7d1c4;padding:14px}.metric.wide{grid-column:1/-1}.metric span{display:block;color:#6a6b66;font:800 11px/1 system-ui;letter-spacing:.12em;text-transform:uppercase}.metric>b{display:block;font:900 30px/1 system-ui;margin-top:7px}.rank{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-top:10px;background:#16191c;color:#fff;border-radius:14px;padding:11px 12px}.rank strong{font:900 16px/1 Georgia,serif}.rank small{font:800 12px/1.3 system-ui;color:#dfd3bd}.domainMini{display:flex;flex-wrap:wrap;gap:8px;margin-top:10px}.domainMini span{display:inline-flex;gap:4px;border:1px solid #e0d9cc;border-radius:999px;padding:7px 9px;color:#3e443f;background:#fbfaf7;font:850 12px/1 system-ui;letter-spacing:0;text-transform:none}.domainMini b{font:900 12px/1 system-ui;color:#16191c}.item.ready{border-left:4px solid #1f9d78;padding-left:10px}.item.almost,.item.stretch{border-left:4px solid #d79d3f;padding-left:10px}.item.review{border-left:4px solid #6d6af2;padding-left:10px}
.quest{background:linear-gradient(135deg,#21170f,#4a3218);color:#fff6df;border-radius:24px;padding:16px;margin:18px 0;box-shadow:0 18px 48px rgba(57,36,16,.22)}.quest h2{font:900 30px/1 Georgia,serif;margin:0 0 6px}.quest p{margin:0 0 12px;color:#e5d6b8;font:700 14px/1.45 system-ui}.questPath{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px}.questStep{position:relative;border:1px solid rgba(255,255,255,.16);background:rgba(255,255,255,.08);border-radius:18px;padding:12px;min-height:118px}.questStep:before{content:attr(data-step);display:grid;place-items:center;width:28px;height:28px;border-radius:999px;background:#fff6df;color:#21170f;font:950 13px/1 system-ui;margin-bottom:9px}.questStep b{display:block;font:950 15px/1.12 system-ui}.questStep small{display:block;margin-top:6px;color:#e8d9bc;font:750 12px/1.35 system-ui}.levelToast{position:fixed;z-index:30;left:50%;top:16px;transform:translate(-50%,-140%);width:min(390px,calc(100% - 24px));background:linear-gradient(135deg,#fff4c2,#ffd36a);color:#25180a;border:1px solid rgba(255,255,255,.7);border-radius:22px;padding:16px 18px;box-shadow:0 24px 80px rgba(56,35,10,.34);transition:transform .35s cubic-bezier(.16,1,.3,1)}.levelToast.show{transform:translate(-50%,0)}.levelToast b{display:block;font:950 30px/.9 Georgia,serif}.levelToast span{font:900 13px/1.4 system-ui;color:#5a3d13}
.queue{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;margin:18px 0 28px}.lane{background:#fff;border:1px solid #d7d1c4;padding:14px;min-height:250px}.lane h2{font:900 22px/1 Georgia,serif;margin:0 0 5px}.lane p{margin:0 0 12px;color:#646a65;font:650 13px/1.4 system-ui}.item{border-top:1px solid #e4dfd4;padding:11px 0}.item:first-of-type{border-top:0}.item strong{display:block;font:850 16px/1.15 system-ui}.item small{display:block;color:#606963;font:650 12px/1.35 system-ui;margin-top:4px}.item .buttons{display:flex;gap:8px;margin-top:9px;flex-wrap:wrap}.item a,.item button{border:1px solid #c9c2b5;background:#fff;color:#16191c;text-decoration:none;border-radius:7px;padding:8px 10px;font:850 12px/1 system-ui;cursor:pointer}.item a{background:#16191c;color:#fff}.empty{color:#74746c;font:650 13px/1.4 system-ui;border-top:1px solid #e4dfd4;padding-top:12px}
.principles{border-top:3px solid #16191c;padding-top:18px;margin-top:26px}.principles h2{font:850 28px/1 Georgia,serif;margin:0 0 12px}.plist{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.principle{background:#fff;border:1px solid #d7d1c4;padding:13px}.principle strong{display:block;font:900 16px/1.15 system-ui;margin-bottom:6px}.principle p{margin:0;color:#4d554f;font:600 13px/1.45 system-ui}.ingest{margin-top:28px;border:1px solid #16191c;background:#fff;padding:16px}.ingest h2{font:850 25px/1 Georgia,serif;margin:0 0 8px}.ingest code{font:800 13px/1.4 ui-monospace,Consolas,monospace;color:#315f9d}.ingest p{color:#4d554f;font:600 14px/1.5 system-ui}.foot{margin-top:26px;color:#6b6d66;font:650 13px/1.5 system-ui}
@media(max-width:860px){.top{justify-content:flex-start;margin-bottom:16px}.top a{overflow-wrap:anywhere}.hero,.queue{grid-template-columns:1fr}.hero{border-bottom:0;padding-bottom:8px}.sourcebox{display:none}.model,.plist{grid-template-columns:1fr}.hero h1{font-size:44px}.hero p{font-size:17px;max-width:32ch;overflow-wrap:break-word}.shell{width:min(620px,calc(100% - 28px))}.model{margin:14px 0}.metric>b{font-size:26px}.quest{margin:12px 0;border-radius:20px}.questPath{grid-template-columns:1fr 1fr}.questStep{min-height:104px}.queue{margin-top:10px}}
"""


JS = r"""
(function(){
const ENGINE=__ENGINE__;
const GRAPH=ENGINE.graph;
const KEY='lifeos.learning.progress.v1';
const LEVEL_SEEN_KEY='lifeos.level.lastSeen.v1';
const INTERVALS=[1,3,7,14,30,60,120];
const PREREQ_RELATIONS=new Set(['prerequisite','practice','application','builds_on','depends_on']);
const $=s=>document.querySelector(s);
const allById=new Map(GRAPH.nodes.map(n=>[n.id,n]));
const domainsById=new Map(GRAPH.domains.map(d=>[d.id,d]));
const incoming=new Map(),outgoing=new Map(),degree={};
for(const n of GRAPH.nodes){incoming.set(n.id,[]);outgoing.set(n.id,[]);degree[n.id]=0}
for(const e of GRAPH.edges){if(!allById.has(e.from)||!allById.has(e.to))continue;incoming.get(e.to).push(e);outgoing.get(e.from).push(e);degree[e.from]=(degree[e.from]||0)+1;degree[e.to]=(degree[e.to]||0)+1}
function load(){try{return JSON.parse(localStorage.getItem(KEY)||'{}')}catch{return {}}}
function save(p){p.done=p.done||{};p.reviews=p.reviews||{};localStorage.setItem(KEY,JSON.stringify(p))}
function progress(){const p=load();p.done=p.done||{};p.reviews=p.reviews||{};return p}
function node(id){return allById.get(id)}
function domain(id){return domainsById.get(id)||{id:'custom',name:'Custom',color:'#58636f'}}
function doneIds(){return new Set(Object.keys(progress().done||{}))}
function esc(s){const d=document.createElement('div');d.textContent=s==null?'':String(s);return d.innerHTML}
function hash(s){let h=2166136261;for(let i=0;i<String(s).length;i++){h^=String(s).charCodeAt(i);h=Math.imul(h,16777619)}return h>>>0}
function daysSince(iso){if(!iso)return 999;return Math.max(0,(Date.now()-new Date(iso).getTime())/86400000)}
function xp(){const p=progress();return Object.values(p.done).reduce((s,n)=>s+(+n.xp||0),0)}
function level(x){return Math.floor(Math.sqrt(x/110))+1}
function nextLevelXp(lvl){return lvl*lvl*110}
function rankTitle(lvl){const ranks=['Novice Pathfinder','Apprentice Scholar','Adept Cartographer','Expert Strategist','Master of Patterns','Grandmaster Polymath','Mythic Founder'];return ranks[Math.min(ranks.length-1,Math.max(0,Math.floor((lvl-1)/2)))]}
function checkLevelUp(lvl){const old=+(localStorage.getItem(LEVEL_SEEN_KEY)||lvl);if(lvl>old){showLevelToast(lvl)}localStorage.setItem(LEVEL_SEEN_KEY,String(lvl))}
function showLevelToast(lvl){let el=document.querySelector('.levelToast');if(!el){el=document.createElement('div');el.className='levelToast';document.body.appendChild(el)}el.innerHTML=`<b>Level ${lvl}</b><span>${esc(rankTitle(lvl))} unlocked · new path options available</span>`;requestAnimationFrame(()=>el.classList.add('show'));setTimeout(()=>el.classList.remove('show'),3600)}
function nodeLevel(n){const raw=String(n.difficulty_level||n.difficulty||'').toLowerCase();if(/intro|beginner|foundation|basic/.test(raw))return 1;if(/intermediate|medium/.test(raw))return 3;if(/advanced|hard|expert/.test(raw))return 5;const xpScore=Math.max(0,(+n.xp||80)-60)/55,graphScore=Math.min(2,((incoming.get(n.id)||[]).length+(outgoing.get(n.id)||[]).length/2)/4);return Math.max(1,Math.min(8,Math.round(1+xpScore+graphScore)))}
function prereqInfo(n,done){const req=(incoming.get(n.id)||[]).filter(e=>PREREQ_RELATIONS.has(e.relation||'prerequisite')),hit=req.filter(e=>done.has(e.from)),missing=req.filter(e=>!done.has(e.from)).map(e=>node(e.from)?.title).filter(Boolean);return {total:req.length,done:hit.length,ratio:req.length?hit.length/req.length:1,missing}}
function domainStats(done){const by=new Map(GRAPH.domains.map(d=>[d.id,{...d,xp:0,done:0,total:0,level:1,pct:0}]));for(const n of GRAPH.nodes){const d=by.get(n.domain)||by.get('custom');if(d)d.total++}for(const n of GRAPH.nodes){if(!done.has(n.id))continue;const d=by.get(n.domain)||by.get('custom');if(d){d.done++;d.xp+=+n.xp||80}}for(const d of by.values()){d.level=level(d.xp);d.pct=d.total?d.done/d.total:0}return [...by.values()].sort((a,b)=>b.xp-a.xp||b.done-a.done||a.name.localeCompare(b.name))}
function reviewInfo(id){const p=progress(),d=p.done[id]||{},r=p.reviews[id]||{},stage=+r.stage||0,last=r.at||d.at,dueIn=(INTERVALS[Math.min(stage,INTERVALS.length-1)]||1)-daysSince(last);return {stage,last,dueIn,due:dueIn<=0}}
function recommendationFor(n,model){const done=model.done,learned=done.has(n.id),nl=nodeLevel(n),dstat=model.domainById.get(n.domain)||{level:1,pct:0,done:0},pre=prereqInfo(n,done);if(learned){const review=reviewInfo(n.id);if(!review.due)return null;return {node:n,score:10000+Math.abs(review.dueIn)*20+nl,kind:'review',readiness:'review',nodeLevel:nl,domainLevel:dstat.level,reasons:[`Review due · stage ${review.stage}`,`Protect ${domain(n.domain).name} memory`]}}const levelGap=nl-(dstat.level+1),fit=Math.max(0,1-Math.abs(levelGap)/4),frontier=pre.total&&pre.ratio>=1?1:0,weak=dstat.pct<.08?1:0,connected=(incoming.get(n.id)||[]).some(e=>done.has(e.from))||(outgoing.get(n.id)||[]).some(e=>done.has(e.to));let score=120*pre.ratio+70*fit+35*frontier+25*weak+(connected?22:0)+(hash(n.id+new Date().toISOString().slice(0,10))%1000)/1000;if(pre.total&&pre.ratio<.5)score-=60;if(levelGap>3)score-=45;const readiness=pre.total===0?'explore':(pre.ratio>=1&&Math.abs(levelGap)<=1?'ready':(pre.ratio>=.66&&Math.abs(levelGap)<=2?'almost':(levelGap>2?'stretch':'explore')));const reasons=[pre.total?`${pre.done}/${pre.total} prereqs`:'Good starting point',`you L${dstat.level} / item L${nl}`];if(weak)reasons.push(`strengthens ${domain(n.domain).name}`);if(connected)reasons.push('connected to learned graph');return {node:n,score,kind:'learn',readiness,nodeLevel:nl,domainLevel:dstat.level,reasons}}
function recommendations(limit=18){const done=doneIds(),domains=domainStats(done),model={done,domains,domainById:new Map(domains.map(d=>[d.id,d]))};return GRAPH.nodes.map(n=>recommendationFor(n,model)).filter(Boolean).sort((a,b)=>b.score-a.score).slice(0,limit)}
function complete(id){const n=node(id);if(!n)return;const p=progress();p.done[id]=p.done[id]||{at:new Date().toISOString(),xp:n.xp||80,title:n.title,kind:n.kind,domain:n.domain};save(p);render()}
function reviewed(id){const n=node(id);if(!n)return;const p=progress();p.done[id]=p.done[id]||{at:new Date().toISOString(),xp:n.xp||80,title:n.title,kind:n.kind,domain:n.domain};const old=p.reviews[id]||{};p.reviews[id]={at:new Date().toISOString(),stage:(+old.stage||0)+1};save(p);render()}
function card(r){const n=r.node,mode=r.kind==='review'?'review':'learn';return `<div class="item ${esc(r.readiness)}"><strong>${esc(n.title)}</strong><small>${esc(domain(n.domain).name)} · Level ${r.nodeLevel} · ${esc(r.readiness)}<br>${r.reasons.map(esc).join(' · ')}</small><div class="buttons"><a href="${esc(n.url)}">${mode==='review'?'Review':(n.kind==='game'?'Play':'Read')}</a>${mode==='review'?`<button data-review="${esc(n.id)}">Mark reviewed</button>`:`<button data-complete="${esc(n.id)}">Mark learned</button>`}</div></div>`}
function renderQuestPath(due,ready,stretch,lvl){const path=[...due.slice(0,1),...ready.slice(0,2),...stretch.slice(0,1)].slice(0,4);$('.questPath').innerHTML=path.length?path.map((r,i)=>`<div class="questStep" data-step="${i+1}"><b>${esc(r.node.title)}</b><small>${esc(r.kind==='review'?'Boss review':(r.readiness==='stretch'?'Future unlock':'Main quest'))}<br>${r.reasons.slice(0,2).map(esc).join(' · ')}</small></div>`).join(''):'<div class="questStep" data-step="1"><b>Start anywhere</b><small>Mark a lesson learned to open your first path.</small></div>';$('.rank strong').textContent=rankTitle(lvl);$('.rank small').textContent=`Next level at ${nextLevelXp(lvl)} XP`}
function render(){
 const done=doneIds(),got=xp(),lvl=level(got),domains=domainStats(done),recs=recommendations(24),due=recs.filter(r=>r.kind==='review'),ready=recs.filter(r=>r.kind==='learn'&&['ready','explore'].includes(r.readiness)),stretch=recs.filter(r=>r.kind==='learn'&&!ready.includes(r));
 $('[data-xp]').textContent=got+' XP';$('[data-level]').textContent='Level '+lvl;$('[data-known]').textContent=done.size+' nodes';$('[data-assessment]').textContent=`${ready.length} ready next · ${due.length} reviews due`;
 $('[data-domains]').innerHTML=domains.slice(0,6).map(d=>`<span><b>${esc(d.name)}</b> L${d.level} · ${d.done}/${d.total}</span>`).join('');
 renderQuestPath(due,ready,stretch,lvl);checkLevelUp(lvl);
 $('.due').innerHTML=due.length?due.slice(0,6).map(card).join(''):'<div class="empty">No reviews due yet. Learn or play something first.</div>';
 $('.frontier').innerHTML=ready.length?ready.slice(0,6).map(card).join(''):'<div class="empty">No ready items yet. Try an explore item or switch to the global graph.</div>';
 $('.mixed').innerHTML=stretch.length?stretch.slice(0,6).map(card).join(''):'<div class="empty">Stretch items appear after the model sees more progress.</div>';
 document.querySelectorAll('[data-complete]').forEach(b=>b.onclick=()=>complete(b.dataset.complete));
 document.querySelectorAll('[data-review]').forEach(b=>b.onclick=()=>reviewed(b.dataset.review));
}
render();
})();
"""


def learning_payload() -> dict[str, Any]:
    graph = load_graph_store()
    return {
        "schema_version": 1,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_notes": SOURCE_NOTES,
        "principles": PRINCIPLES,
        "ingestion_contract": INGESTION_CONTRACT,
        "review_intervals_days": [1, 3, 7, 14, 30, 60, 120],
        "selection_policy": {
            "priority_order": ["due_reviews", "ready_next", "almost_ready", "stretch_or_explore"],
            "frontier_rule": "A node is ready if prerequisites are satisfied and its estimated level is near the learner's domain level.",
            "level_rule": "Learner level is inferred from completed XP overall and per domain; node level comes from difficulty metadata, XP, and graph complexity.",
            "interleaving_rule": "Boost weak domains and connected graph frontier items before repeating the same domain.",
            "explainability_rule": "Every recommendation includes short visible reasons: prereqs, level fit, review due, weak domain, or graph connection.",
        },
        "graph": graph,
    }


def render(payload: dict[str, Any]) -> str:
    sources = "".join(
        f"<strong>{s['title']}</strong><p>{s['takeaway']}</p><a href='{s['url']}' target='_blank' rel='noopener'>{s['url']}</a>"
        for s in payload["source_notes"]
    )
    principles = "".join(
        f"<div class='principle'><strong>{p['name']}</strong><p>{p['rule']}</p><p>{p['implemented_as']}</p></div>"
        for p in payload["principles"]
    )
    engine_json = json.dumps(payload)
    return f"""<!doctype html><html lang='en'><head>
<meta charset='utf-8'>
<meta name='viewport' content='width=device-width,initial-scale=1,viewport-fit=cover'>
<meta name='color-scheme' content='light'>
<title>LifeOS Learning Engine</title>
<style>{CSS}</style></head><body><main class='shell'>
<div class='top'><a href='/learn'>&larr; Field Notes</a><a href='/output/learn/skill-tree.html'>Knowledge Graph</a><a href='/output/learn/profile.html'>Profile</a></div>
<section class='hero'><div><div class='k'>Adaptive learner model</div><h1>Training Queue</h1><p>LifeOS assesses your current level from the graph, then recommends reviews, ready next lessons, and stretch items with reasons instead of dumping a flat library.</p></div><aside class='sourcebox'>{sources}</aside></section>
<section class='model'><div class='metric'><span>Personal XP</span><b data-xp>0 XP</b></div><div class='metric'><span>Level</span><b data-level>Level 1</b></div><div class='metric'><span>Known Graph</span><b data-known>0 nodes</b></div><div class='metric wide'><span>Assessment</span><b data-assessment>0 ready next</b><div class='rank'><strong>Novice Pathfinder</strong><small>Next level at 110 XP</small></div><div class='domainMini' data-domains></div></div></section>
<section class='quest'><h2>Quest Path</h2><p>A game-like route through the graph: clear the review, take the ready quest, then unlock the stretch node.</p><div class='questPath'></div></section>
<section class='queue'><div class='lane'><h2>Due Review</h2><p>Spaced retrieval beats rereading. These come first.</p><div class='due'></div></div><div class='lane'><h2>Ready Next</h2><p>Matched to your current domain level and prerequisite graph.</p><div class='frontier'></div></div><div class='lane'><h2>Stretch / Explore</h2><p>Interleaved options to broaden the graph without overloading you.</p><div class='mixed'></div></div></section>
<section class='principles'><h2>System Rules</h2><div class='plist'>{principles}</div></section>
<section class='ingest'><h2>Book / Doc Ingestion Contract</h2><p>Long sources get chunked into concepts, typed edges, source pointers, blog lessons, and games. The engine stores summaries and locators, not a pasted book.</p><p>Output schema: <code>output/learn/learning-engine.json</code>. Source contract: <code>ingestion_contract</code>.</p></section>
<div class='foot'>Generated {payload['generated_at']}. This is the control layer; the graph remains the source of truth.</div>
</main><script>{JS.replace('__ENGINE__', engine_json)}</script></body></html>"""


def build() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    payload = learning_payload()
    graph = payload["graph"]
    (OUT / "learning-engine.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (OUT / "learning-system.html").write_text(render(payload), encoding="utf-8")
    (OUT / "ingestion-contract.json").write_text(json.dumps(INGESTION_CONTRACT, indent=2), encoding="utf-8")
    return {
        "generated_at": payload["generated_at"],
        "url": "/output/learn/learning-system.html",
        "engine": "/output/learn/learning-engine.json",
        "sources": len(SOURCE_NOTES),
        "principles": len(PRINCIPLES),
        "nodes": len(graph["nodes"]),
        "edges": len(graph["edges"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the LifeOS learning engine")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("build", help="Build the learning engine page and JSON model")
    args = parser.parse_args()
    if args.cmd == "build":
        print(json.dumps(build(), indent=2))
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
