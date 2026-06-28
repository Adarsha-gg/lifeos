# Generalizable Learning Games

## 2026-06-26

- Continued the morning learning feature on branch `feature/morning-lessons`.
- Direction: lessons remain the entry point. The user reads a visual lesson first, then plays a real game or puzzle to apply the idea. The game should not be a plain quiz.
- Extended `tools/lifeos_arcade.py` from simple classification drills into a reusable mechanics catalogue:
  - `classify`: fast categorization under time pressure.
  - `runner`: lane/action game driven by category specs.
  - `strategy`: turn-based resource puzzle driven by meters, moves, rules, and win conditions.
- Added spec validation so generated game specs fail fast when required fields are missing or an action references an unknown meter.
- Added two paired lesson reinforcements:
  - `Sleep Stage Sprint` pairs with `why-we-sleep`.
  - `Compounding Engine` pairs with `power-of-compounding`.
- Validation:
  - `python -m py_compile tools\lifeos_arcade.py tools\lifeos_lessons.py`
  - `python tools\lifeos_arcade.py build`
  - `python tools\lifeos_lessons.py build`
  - Generated arcade scripts parsed with Node via `new Function`.
  - Local server `/learn` returned the replay arcade entries for `Sleep Stage Sprint` and `Compounding Engine`.

## Open Decisions

- Future generated games should prefer `runner`, `strategy`, richer simulations, or puzzle mechanics over plain quiz-like recall.
- The next robust step is a small game-spec authoring contract for local models: lesson concept in, validated game spec out.

## 2026-06-26 Reference Pivot

- User pointed to `https://messenger.abeto.co/` as the quality bar: full-screen stylized 3D, tiny-world presentation, character/touch controls, and a real delivery loop.
- Inspected the reference page and assets enough to identify the shape without copying code/assets: Three.js WebGL app, Svelte shell, custom planet/atmosphere/outline/postprocessing, touch controls, and delivery-style gameplay.
- Added a new `arena3d` mechanic to `tools/lifeos_arcade.py`: one Three.js tiny-planet engine powered by subject specs.
- Added three proof specs on the same engine:
  - `arena-civilization`: ordered artifact delivery for history/civilization.
  - `arena-quantum-fields`: particle delivery into matter/force fields.
  - `arena-art-movements`: visual clue delivery into art movement galleries.
- Validation:
  - `python tools\lifeos_arcade.py build`
  - `python tools\lifeos_lessons.py build`
  - Node parsed all generated arena scripts.
  - Edge headless screenshots rendered nonblank desktop/mobile 3D scenes.

## 2026-06-27 Template-Aware Engine

- Pivoted away from a single repeated globe/planet metaphor. The shared engine now means shared runtime pieces: Three.js rendering, camera, movement input, pickup/delivery loop, zones, artifacts, scoring, lives, and spec validation.
- Added subject templates so different topics can render as different worlds while still using the same validated game contract:
  - `civ-board`: settlement/river/forest board for civilization sequence learning.
  - `quantum-lab`: orbital lab/field sorter for matter versus force particles.
  - `gallery-studio`: gallery room for sorting visual clues into art movements.
- Tuned first-frame rendering after screenshot QA:
  - Isometric camera starts at the intended view instead of easing from the origin.
  - Floating labels are smaller so they do not dominate the scene.
  - HUD/toast text contrast works on the light panel style.
  - Mobile HUD and controls no longer push offscreen.
- Validation:
  - `python -m py_compile tools\lifeos_arcade.py tools\lifeos_lessons.py`
  - `python tools\lifeos_arcade.py build`
  - `python tools\lifeos_lessons.py build`
  - Node parsed the generated 3D game scripts.
  - Edge headless screenshots checked desktop civilization/quantum/art worlds and mobile quantum view.

## 2026-06-27 Progression / Skill Tree

- Added `tools/lifeos_skill_tree.py`, a generated skill-tree page at `/output/learn/skill-tree.html`.
- Pattern borrowed from common RPG/learning-map systems, without copying third-party assets/content:
  - tracks, nodes, prerequisites, locked/available/complete states, XP, levels, and next unlocks.
  - localStorage progress key: `lifeos.learning.progress.v1`.
- Wired `/learn` to show current level/XP and link into the skill tree.
- Wired lesson pages with a "Mark complete" control that awards lesson XP locally.
- Wired the `arena3d` engine to save game completion XP on wins.
- Mobile tree layout now switches from absolute-positioned graph to a vertical node list so it remains usable on phones.
- Validation:
  - `python -m py_compile tools\lifeos_skill_tree.py tools\lifeos_lessons.py tools\lifeos_arcade.py`
  - `python tools\lifeos_skill_tree.py build`
  - `python tools\lifeos_lessons.py build`
  - Node parsed generated scripts for skill tree, index, lesson, and arena pages.
  - Edge headless screenshots checked `/learn` and skill tree desktop/mobile.

## 2026-06-27 Blog + Top-Down Graph Pivot

- User clarified the product direction:
  - Generated learning should feel like a blog/publication, not a dashboard.
  - Skill tree should be top-down, like a knowledge graph/prerequisite map.
- Reworked `/learn` into a "LifeOS Field Notes" issue:
  - masthead, date/issue label, lead essay, today's posts, archive, practice lab, and knowledge graph callout.
  - Mobile uses narrower reading measures so article titles and paragraphs wrap cleanly.
- Reworked `skill-tree.html` into a top-down learning graph:
  - root node at the top, prerequisite branches flowing downward.
  - lighter grid canvas and article-to-game pathway language.
  - mobile keeps the vertical list fallback for readability.
- Validation:
  - `python -m py_compile tools\lifeos_skill_tree.py tools\lifeos_lessons.py`
  - `python tools\lifeos_skill_tree.py build`
  - `python tools\lifeos_lessons.py build`
  - Node parsed generated scripts for `/learn` and `skill-tree.html`.
  - Edge headless screenshots checked desktop `/learn`, desktop top-down graph, and mobile `/learn`/graph.

## 2026-06-27 Personal Graph Correction

- User corrected the model: unrelated subjects must not be connected just because the user learned them near each other.
- Replaced the forced universal tree with a two-layer model:
  - global library: domains, nodes, and typed edges between actually related concepts.
  - personal graph: only nodes the user has actually completed, read, or played.
- Current graph behavior:
  - default view is `Personal graph`, which starts empty if no progress is stored.
  - `Global library` mode shows separate topic islands: history, thinking, physics, growth, culture, systems.
  - practice edges exist only inside related pairs, such as civilization article -> civilization game, quantum drill -> quantum field game.
- Added concise task log at `specs/2026-06-26-generalizable-learning-games/WORKLOG.md`.

## 2026-06-27 Math Academy Learning Engine

- Added Math Academy-inspired learning model around the graph:
  - due reviews from spaced repetition,
  - frontier topics from completed prerequisites,
  - mixed practice across domains,
  - source-backed principles and ingestion contract.
- Added `tools/lifeos_learning_engine.py`, generating:
  - `/output/learn/learning-system.html`
  - `/output/learn/learning-engine.json`
  - `/output/learn/ingestion-contract.json`
- Added `tools/lifeos_ingest_doc.py`:
  - `seed-mathacademy` writes the Math Academy learning-model notes packet.
  - `ingest <file>` converts local markdown/text into source, section, concept, and edge candidates.
- Wired `tools/lifeos_lessons.py build` so `/learn`, the knowledge graph, and the training queue regenerate together.
- Validation:
  - `python -m py_compile tools\lifeos_learning_engine.py tools\lifeos_ingest_doc.py tools\lifeos_lessons.py tools\lifeos_skill_tree.py`
  - `python tools\lifeos_ingest_doc.py seed-mathacademy`
  - `python tools\lifeos_learning_engine.py build`
  - `python tools\lifeos_lessons.py build`
  - Node parsed generated scripts for `index.html`, `skill-tree.html`, and `learning-system.html`.
