# BUILD SPEC — Obsidian-style force-directed knowledge graph view

**Status:** Ready to build
**Goal:** Replace the current static, hand-positioned knowledge-graph view with an **Obsidian-style interactive force-directed graph**: nodes auto-arrange via physics, you can zoom / pan / drag, node size reflects connectivity, color reflects domain, hovering highlights neighbors, and a "local graph" mode shows just one node's neighborhood. This is the reward surface that makes learning feel addictive (watching your brain map grow), so it must feel good on phone and desktop.

Context: `specs/2026-06-27-ai-content-generation/PLAN.md`.

---

## 1. Current state (verified)

`tools/lifeos_skill_tree.py` renders `output/learn/skill-tree.html`:
- Nodes are **absolutely positioned** from hardcoded `x`/`y` percentages on each node.
- Edges are drawn as static `<svg><line>` between those fixed coords.
- Personal/global toggle, XP/level, detail panel, "mark learned"/"reset" all work and read/write `localStorage` (`lifeos.learning.progress.v1`).
- Graph data comes from `load_graph_store()` (`GRAPH` = seed + generated nodes). Nodes have: `id, domain, title, kind (article|game), xp, url, summary, x, y, difficulty_level`. Edges: `from, to, relation, reason, confidence`.

**The problem:** fixed coordinates don't scale. As generation adds dozens of nodes, manual `x`/`y` (`next_coords` grid) overlap and look dead. Obsidian's force layout solves this and is far more engaging.

**Keep everything that works** — the personal/global semantics, progress storage, detail panel, complete/review actions. This task swaps the *renderer*, not the model.

---

## 2. What to port from Obsidian (prioritized)

**Must-have (P1):**
1. **Force-directed layout** — physics simulation replaces fixed coords: center force, charge/repulsion (nodes push apart), link force (edges act as springs with a target distance), collision (no overlap). Use existing `x`/`y` only as optional starting seeds.
2. **Zoom + pan** — mouse wheel / pinch to zoom, drag background to pan.
3. **Drag nodes** — drag to reposition; node "pins" while dragged, then relaxes (or stays pinned — Obsidian relaxes by default).
4. **Node size ∝ degree** — more connections = bigger node (Obsidian's signature look). Compute degree from edges.
5. **Color by domain** — reuse existing domain colors. Learned nodes get the existing "done" treatment (filled/green); unlearned/suggested keep their states.
6. **Hover highlight** — hovering a node highlights it + its direct neighbors and edges; everything else fades. Click still opens the detail panel + navigates.

**Should-have (P2):**
7. **Local graph mode** — given a focused node, show only its N-hop neighborhood (Obsidian's local graph). Wire to the detail panel ("focus this node").
8. **Filters** — by domain (toggle chips, already have the legend), by learned/unlearned, and a **search box** that dims non-matching nodes.
9. **Labels fade with zoom** — labels hidden when zoomed out, appear when zoomed in or on hover (keeps it readable at scale).

**Nice-to-have (P3):**
10. **Physics control panel** — Obsidian-style sliders: center force, repel strength, link force, link distance. Persist to localStorage.
11. **Smooth animated transitions** when toggling personal/global or entering local graph.

---

## 3. Rendering approach (decide up front)

- **Simulation:** vendor **`d3-force`** (small, standalone — not all of d3) into `tools/vendor/`, consistent with the existing vendored `three.min.js`. Alternative: a compact custom force sim (~120 lines: repulsion O(n²) is fine under ~300 nodes, link spring, centering). Recommend `d3-force` for correctness/speed; custom only if avoiding any new vendor file is a hard rule.
- **Drawing:** render on a **`<canvas>`** (not SVG). Canvas pans/zooms/redraws smoothly for hundreds of nodes; SVG degrades. Obsidian itself uses a canvas/WebGL renderer for this reason. For our current scale SVG would work, but canvas future-proofs as generation grows the graph.
- **No build step:** keep it a single self-contained HTML file with inline JS + the vendored sim, matching how `skill_tree.py` already emits everything inline. `skill_tree.py` should inline the vendored lib (read file → embed) or reference it via the local server's static route.

---

## 4. Data wiring

- Feed the existing `GRAPH` (nodes + edges) to the client as JSON, exactly as today (`JS.replace('__GRAPH__', json.dumps(GRAPH))`).
- Client computes: `degree[id]` from edges; node radius = `f(degree)`; node color = domain color; node state (done/suggested/global) from progress (localStorage today; server `progress.json` once Phase 2 lands — read whichever is present).
- Drop dependence on `x`/`y` for layout (the simulation owns positions). Leave the fields in the data harmlessly, or stop emitting them.

---

## 5. Implementation steps

1. **Vendor the sim.** Add `tools/vendor/d3-force.min.js` (or write the custom sim). Confirm `skill_tree.py` can inline/serve it.
2. **Canvas scaffold.** Replace the `.map` SVG block with a `<canvas>` + a render loop. Implement world↔screen transform (scale + translate) for zoom/pan.
3. **Force sim.** Build the simulation from nodes/edges; run ticks → update positions → redraw. Tune forces so domains cluster but the whole graph stays on screen.
4. **Interactions.** Wheel/pinch zoom, drag-pan, node hit-testing, node drag, hover highlight (neighbor set), click → existing `select(id)` detail panel.
5. **Visual encoding.** Degree→size, domain→color, learned/suggested/global states, faded labels by zoom.
6. **Reuse existing UI.** Keep the profile bar (XP/level), legend chips (wire them as domain filters), detail panel, complete/review/reset buttons — they call the same progress functions.
7. **Local graph mode + filters + search (P2).**
8. **Physics panel + transitions (P3).**
9. **Mobile pass.** Touch: one-finger pan, pinch zoom, tap select, long-press drag. The current page has a mobile stacked fallback — replace with the canvas graph but verify it's usable at phone size (and that the detail panel stacks below).

---

## 6. Acceptance criteria
1. Opening `skill-tree.html` shows a force-directed graph that settles into a readable layout with **no manual coordinates** — adding generated nodes never causes overlap.
2. Wheel/pinch zoom and background-drag pan work on desktop and phone.
3. Dragging a node moves it; the graph relaxes naturally.
4. Highly-connected nodes are visibly larger; nodes are colored by domain; learned nodes show the done state.
5. Hovering a node highlights it + neighbors and fades the rest; clicking opens the existing detail panel and the lesson link works.
6. Personal vs global toggle still works and animates between states.
7. (P2) A search box dims non-matches; domain chips filter; "focus node" shows a local graph.
8. Performance stays smooth (60fps pan/zoom) with 200+ nodes (synthetically duplicate the store to test).
9. Progress (learned nodes / XP) is unchanged in behavior — same storage, same numbers.

---

## 7. Risks / notes
- **Performance:** O(n²) repulsion is fine to a few hundred nodes; if the graph grows huge later, switch to a Barnes–Hut quadtree (d3-force's `forceManyBody` already does this). Canvas keeps redraw cheap.
- **Don't regress the model:** the detail panel + complete/review/reset and personal/global semantics are load-bearing — port them as-is, only the layout/drawing changes.
- **Inline-everything constraint:** the repo emits self-contained HTML with no bundler. Keep the vendored sim inlined or served from the existing static route; don't introduce npm/build tooling.
- **Synergy:** this obsoletes the P2/coordinate concerns in `specs/2026-06-27-generation-fixes/PLAN.md` — once layout is automatic, `next_coords` and `x`/`y` quality stop mattering.
- **Phase 2 synergy:** when server-side `progress.json` lands (Mini App), have the graph read it so the phone and desktop show the same lit-up map.
