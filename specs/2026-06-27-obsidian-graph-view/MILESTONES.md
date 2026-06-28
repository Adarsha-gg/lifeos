# Milestones

## 2026-06-27 Canvas Force Graph

- Replaced the static SVG/fixed-coordinate graph renderer in `lifeos_skill_tree.py` with a self-contained canvas renderer.
- Implemented an inline force simulation:
  - link springs,
  - repulsion,
  - collision spacing,
  - center force,
  - pre-settled initial layout,
  - fit-to-bounds first view.
- Added Obsidian-style interactions:
  - wheel zoom,
  - drag pan,
  - node drag,
  - hover neighbor highlighting,
  - click-to-select detail panel.
- Added graph controls:
  - domain chips act as filters,
  - search dims non-matches,
  - focus neighborhood button,
  - clear focus button.
- Preserved existing model behavior:
  - personal/global modes,
  - localStorage progress,
  - XP/level display,
  - mark learned,
  - reset progress,
  - detail panel and queue.
- Added server progress sync from `/output/learn/progress.json` so Telegram Mini App completions can light up the same graph.

## Validation

- `python tools\lifeos_skill_tree.py build`
- Node parsed generated `skill-tree.html` scripts.
- Headless Edge desktop and mobile screenshots rendered a nonblank canvas graph.
- Final graph build still reports 20 nodes, 9 edges, and 7 domains from the persisted graph store.

## 2026-06-28 Graph performance hardening

- Replaced the browser graph renderer's startup force-simulation loop with a deterministic O(nodes + edges) clustered canvas layout. The old path ran repeated O(n^2) collision/repulsion ticks over the full generated graph, which caused hangs as the curriculum grew.
- Kept canvas pan/zoom, node drag, hover-neighborhood highlighting, search dimming, domain filters, personal/global modes, focus-neighborhood mode, detail panel, completion, XP, and progress sync behavior.
- Added lightweight client-side performance instrumentation available as `window.LifeOSGraphPerf` and hidden `#graph-perf`; benchmark mode can beacon results when `perfBeacon=<port>` is present.
- Verified current generated global graph at 603 nodes / 509 edges: 5 headless Edge runs measured global render max 21.3ms, layout max 8.5ms, draw max 8.6ms, all below the 100ms target.
- Rebuilt `skill-tree.html`, parsed inline scripts with Node, rebuilt the learning engine, and captured `C:\tmp\lifeos-skill-tree-bench.png` for visual inspection.

## 2026-06-28 Preview card and Vercel review deployment

- Added a floating graph node preview card in `tools/lifeos_skill_tree.py`. Clicking a node now opens a card with domain/kind, title, summary, XP/status/difficulty/link count, incoming and outgoing links, plus actions for previewing the lesson, marking learned, and focusing the graph.
- Kept the existing detail panel while making the click interaction feel more like Obsidian/mobile card preview. Added mobile styling so the card docks at the bottom of the graph on narrow screens.
- Rebuilt the graph and verified the preview via headless Edge/CDP on both local and deployed pages. Current deployed global graph perf: render 13.0ms, layout 6.1ms, draw 1.1ms on 603 nodes / 509 edges.
- Prepared a public-safe Vercel static staging directory at `C:\tmp\lifeos-review` containing only the learning site (`output/learn`) plus review notes and rewrites for `/output/learn/...`; excluded connector/audit/dashboard/setup files after detecting account/path references that should not be public.
- Deployed production Vercel project `lifeos-review`; verified `/review`, `/learn`, `/output/learn/skill-tree.html?mode=global`, and representative Caesar lesson URLs returned HTTP 200.
