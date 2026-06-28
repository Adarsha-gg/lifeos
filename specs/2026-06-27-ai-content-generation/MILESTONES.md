# Milestones

## 2026-06-27 Implementation

- Added persisted graph store at `output/learn/graph-store.json`.
  - `lifeos_skill_tree.py` now treats the hardcoded graph as a seed and merges it with stored generated nodes/edges.
  - Generated graph nodes are deduped by `id`; edges by `(from, to, relation)`.
- Added `tools/lifeos_generate.py`.
  - `check` verifies Ollama and `gemma3:12b`.
  - `topic` generates one lesson/game/node pair for a topic and difficulty.
  - `missions` loops over `~/learn/*/MISSION.md`, continues on per-topic failures, and reports JSON status.
  - Uses Ollama `/api/generate`, `stream: false`, JSON-schema `format`, retry-on-validation-failure, and local caching by `topic--difficulty`.
- Added generated lesson store at `output/learn/generated-lessons.json`.
  - `lifeos_lessons.py` now merges generated lessons with seed lessons before rendering.
  - Generated lessons render through the existing `render_lesson()` and `_game_html()` path.
- Wired `lifeos_morning.py` to run `lifeos_generate.py missions` before `lifeos_lessons.py build`.
  - The generation step has a longer timeout.
  - `missions` returns success even when individual topics fail, so an unavailable Ollama does not kill the morning pipeline.
- Added content quality guards:
  - difficulty levels: `child`, `teen`, `undergrad`, `grad`, `expert`.
  - generated domains get topic-based hints so unrelated concepts stay in sensible graph islands.
  - generated games are restricted to `ponder`, `order`, and `estimate`.
  - multiple-choice-looking prompts are rejected.
  - generated titles, colors, wiki image titles, and prompt text are normalized for the renderer.
- Improved mobile lesson rendering for generated long titles/headings.

## 2026-06-27 Validation

- `python tools\lifeos_generate.py check` passed; Ollama was up and `gemma3:12b` was present.
- `python tools\lifeos_generate.py topic --name zero-knowledge-proofs --difficulty teen` generated successfully.
- Re-running the same teen command reused cached content instantly.
- `python tools\lifeos_generate.py topic --name zero-knowledge-proofs --difficulty expert` generated a distinct expert lesson.
- `python tools\lifeos_generate.py missions --difficulty teen` generated/reused all mission topics:
  - `nutrition`
  - `startups`
  - `zero-knowledge-proofs`
- Final graph store contains generated article/game nodes and `practice` edges.
- Final build commands passed:
  - `python -m py_compile tools\lifeos_generate.py tools\lifeos_skill_tree.py tools\lifeos_lessons.py tools\lifeos_morning.py tools\lifeos_learning_engine.py`
  - `python tools\lifeos_skill_tree.py build`
  - `python tools\lifeos_lessons.py build`
  - `python tools\lifeos_learning_engine.py build`
- Generated page scripts parsed cleanly with Node.
- Headless Edge screenshots were checked for `/learn` and the generated ZK teen lesson on mobile.
- Full `python tools\lifeos_morning.py run` was attempted with Telegram/ntfy env vars cleared.
  - The new `lifeos_generate.py missions` step returned 0 and reused cached generated lessons.
  - `lifeos_lessons.py build` ran after it and included generated mission content in `today.json`.
  - Overall pipeline returned nonzero because the pre-existing `lifeos_connectors.py` step fails while launching `bash -lc "agent status"` with `WinError 1312`; this is unrelated to the generation layer.

## 2026-06-27 Pipeline Connector Fix

- Fixed `lifeos_connectors.py` subprocess wrapper to catch `OSError` from Windows process launch failures.
- Cursor agent status probe now records the failure in `lifeos-connectors.json` instead of crashing the connector refresh.
- Re-ran `python tools\lifeos_connectors.py`; it exited 0 and wrote `output/lifeos-connectors.json`.
- Re-ran full `python tools\lifeos_morning.py run` with Telegram/ntfy env vars cleared; the full pipeline exited 0.
