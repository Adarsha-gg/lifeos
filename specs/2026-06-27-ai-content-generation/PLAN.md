# BUILD SPEC — AI Content Generation Layer for LifeOS Learning

**Status:** Ready to build
**Owner of this doc:** (handoff — implementer has no prior context, read this top to bottom)
**Estimated size:** 1 new module (~250–350 lines) + 2 small edits to existing modules
**Prereqs:** Python 3.11, Ollama running locally with `gemma3:12b` pulled (`ollama list` should show it)

---

## 0. One-line goal

Turn the LifeOS learning system from **~12 hardcoded lessons** into **infinite, AI-generated lessons + games for any topic, at any difficulty**, by adding a generation layer that calls the local `gemma3:12b` model and emits content in the **exact schema the existing renderer/graph already consume**.

Do **not** rebuild the graph, recommender, page renderer, games, morning pipeline, or Telegram ping. They already exist and work. You are adding the missing *content source* in front of them.

---

## 1. Why this exists (context)

LifeOS is a local-first personal assistant. It already has an anti-doomscroll "morning lessons" feature: every morning it builds a set of lessons + an interactive game, puts them on a local web page, and pings the user's phone via Telegram to read them instead of scrolling.

The problem: **all lesson content is hardcoded.** There are ~12 fixed nodes (civilization, quantum mechanics, sleep, compounding, etc.). Nothing calls an LLM. So the system runs out of content and can't personalize to what the user actually wants to learn.

The user maintains topic "missions" in `C:\Users\adars\learn\<topic>\MISSION.md` (currently: `nutrition`, `startups`, `zero-knowledge-proofs`). These are not wired to anything yet.

This task connects: **MISSION topics → LLM generation → existing content schema → existing graph + pages + morning ping.**

---

## 2. Current state of the codebase (verified — trust these references)

Repo root: `C:\Users\adars\Coding\lifeos`
Tools dir: `C:\Users\adars\Coding\lifeos\tools`
Data/vault root: `C:\Users\adars\Coding\knowledgebase` (this is `VAULT_ROOT`; see `tools/lifeos_paths.py`)
Generated output dir: `VAULT_ROOT/output/learn/`

Key existing modules (READ THESE before writing code):

| File | What it does | What you need from it |
|---|---|---|
| `tools/lifeos_paths.py` | Defines `APP_ROOT` and `VAULT_ROOT`. | Import these. Never hardcode paths. |
| `tools/lifeos_skill_tree.py` | The knowledge graph. Hardcoded `GRAPH` dict (domains/nodes/edges) at line ~21. `build()` writes `skill-tree.html` + `knowledge-graph.json`. | **You must make this load the graph from a persisted store instead of only the hardcoded seed** (see §5.1). Study the node/edge shape at lines 21–51. |
| `tools/lifeos_learning_engine.py` | Spaced-repetition + frontier recommender. Contains `INGESTION_CONTRACT` (line ~85) with `node_schema` and `edge_schema` — **this is your output contract.** Imports `GRAPH` from skill_tree. | Use `INGESTION_CONTRACT` as the authoritative schema. |
| `tools/lifeos_lessons.py` | Renders lesson HTML pages (with Wikipedia photos) + embeds a game. Key funcs: `_sections_html` (L866), `_ideas_html` (L882), `_game_html` (L887), `_hero_html` (L941), `render_lesson` (L993), `daily_set` (L1032), `build` (L1223). Writes `today.json` manifest. | **READ L866–L1031 carefully and extract the EXACT dict shape `render_lesson` and `_game_html` consume. Your generated lesson/game objects MUST match it field-for-field. Do not guess these fields — confirm from the code.** |
| `tools/lifeos_morning.py` | Morning pipeline. Runs a `PIPELINE` list of subprocesses in order, incl. `lifeos_lessons.py build`, then `lifeos_morning_ping.py`. Has a Task Scheduler command. | You will add your generator as a new pipeline step (see §5.3). |
| `tools/lifeos_morning_ping.py` | Sends Telegram/ntfy "lessons ready" ping. Reads `output/learn/today.json`. Telegram via env `LIFEOS_TG_BOT_TOKEN` + `LIFEOS_TG_CHAT_ID`. Uses `urllib` (no external deps). | Don't change it. Note its pattern: stdlib `urllib`, never crash the pipeline. |

**Confirmed facts:**
- No file anywhere calls Ollama / an LLM. (`grep` for `11434`, `api/generate`, `ollama` → zero hits.)
- No difficulty levels exist anywhere (the only "level" in code is XP level).
- The codebase uses **stdlib only** for HTTP (`urllib.request`), `from __future__ import annotations`, `argparse` subcommands, type hints. Match this style. Prefer `urllib` over adding `requests`/`ollama` deps unless you confirm they're already available.

---

## 3. Scope

### In scope (this task = Phase 1)
1. New module `tools/lifeos_generate.py` that generates a lesson + game + graph node/edges for a `(topic, difficulty)` pair using `gemma3:12b`.
2. A persisted **graph store** so generated content accumulates and is reused (not hardcoded).
3. Difficulty levels (ELI5 → expert).
4. Reading topics from `C:\Users\adars\learn\<topic>\MISSION.md`.
5. Wiring into the morning pipeline.
6. Caching so the same `(topic, difficulty)` isn't regenerated every run.

### Out of scope (Phase 2 — do NOT build now, just don't block it)
- Telegram **Mini App** (HTTPS-hosted interactive page with `WebApp.sendData()` feedback). The user wants this eventually; current delivery is a Telegram text ping + LAN browser URL, which keeps working. Leave a clean seam but don't build it here.
- Adaptive difficulty (auto bump/drop based on game score). Phase 3.

---

## 4. Design decisions (already made — implement these, don't relitigate)

### 4.1 Reuse vs personalization → solved by three layers
- **Canonical graph store** (shared, accumulates): every generated concept becomes a node in a persisted JSON file. Content is cached by `(topic, difficulty)` and reused — generating once serves every future morning.
- **Personal overlay** (per-user, already exists): the personal graph lives in browser `localStorage` (`lifeos.learning.progress.v1`). Untouched by this task.
- **Personalization = selection + sequencing**, done by the existing recommender, not by regenerating prose. So caching content does NOT reduce personalization.

### 4.2 Difficulty levels (fixed enum)
Use exactly these five, in this order, lowest→highest:

| key | audience | one-line instruction to the model |
|---|---|---|
| `child` | ~8-year-old | Explain with everyday analogies, no jargon, short sentences. |
| `teen` | curious 15-year-old | Plain language, define any term you introduce. |
| `undergrad` | university student new to the field | Standard terminology, assume basic STEM/general literacy. |
| `grad` | someone with field fundamentals | Precise, use proper terminology, go into mechanisms. |
| `expert` | PhD / practitioner | Dense, rigorous, assume deep background, focus on nuance/edge cases. |

Store the chosen level on the node as `difficulty_level`. (Keep the existing `difficulty: intro|core|hard` field too if the renderer/contract uses it — map child/teen→intro, undergrad→core, grad/expert→hard.)

### 4.3 Caching
Cache key = `f"{topic_slug}--{difficulty_level}"`. Before generating, check the graph store for an existing node with that key; if present and `--force` not passed, skip the LLM call and reuse. This keeps morning runs fast and free.

### 4.4 Schema is the contract
The generator's job is to produce objects that drop straight into the existing pipeline with zero downstream changes (other than the graph-store loader in §5.1). The schema in `INGESTION_CONTRACT` + the actual lesson/game dict shape in `lifeos_lessons.py` are the source of truth. **If your output doesn't render, the bug is in your output, not the renderer.**

---

## 5. Required changes

### 5.1 Persisted graph store (edit `lifeos_skill_tree.py` + new file)

Introduce a canonical store file: `VAULT_ROOT/output/learn/graph-store.json` with the same shape as the existing `GRAPH` dict (`{"domains": [...], "nodes": [...], "edges": [...]}`).

In `lifeos_skill_tree.py`:
- Keep the existing hardcoded `GRAPH` as the **seed**.
- Add a loader: if `graph-store.json` exists, load it and **merge** with the seed (dedupe nodes/edges by id / by `(from,to,relation)`); otherwise use the seed and write it to the store on first run.
- `learning_engine.py` imports `GRAPH` from skill_tree, so this one change feeds both the graph page and the recommender. Verify the import still works after the change.

Keep the merge pure and deterministic (sort nodes by id before writing) so diffs are clean.

### 5.2 New module: `tools/lifeos_generate.py`

**CLI (argparse subcommands, matching the repo pattern):**
```
python tools/lifeos_generate.py topic --name zero-knowledge-proofs --difficulty teen [--force]
python tools/lifeos_generate.py missions [--difficulty teen] [--force]   # generate for every ~/learn/*/MISSION.md
python tools/lifeos_generate.py check                                     # verify Ollama is up + model present
```

**Behavior of `topic`:**
1. Resolve topic. If `--name` matches a folder in `C:\Users\adars\learn`, read its `MISSION.md` for intent/constraints/out-of-scope and feed that into the prompt. Otherwise treat `--name` as a freeform topic string.
2. Compute cache key (§4.3). If cached and not `--force`, print a "reused" result and exit 0.
3. Call `gemma3:12b` (see §6) to produce a structured lesson + game + node/edge metadata.
4. Validate the LLM output against the schema (§7). On invalid JSON, retry once with a stricter prompt; on second failure, exit non-zero with a clear error (do NOT write partial garbage into the store).
5. Merge the new node(s)/edge(s) into `graph-store.json`.
6. Write the lesson content where `lifeos_lessons.py` expects to find generated lessons (CONFIRM this location/format from `lessons.py` — it may read from a JSON the generator should write, or you may need a small adapter. Match whatever `daily_set`/`build` consumes).
7. Print a JSON result summary (generated/reused, node id, url, difficulty, timings).

**Behavior of `missions`:** loop over every `C:\Users\adars\learn\*/MISSION.md`, call the topic path for each. Continue on individual failures; report a per-topic status list at the end (mirror the resilient style of `lifeos_morning.py`'s pipeline reporting).

### 5.3 Wire into the morning pipeline (edit `lifeos_morning.py`)

Add a generation step to `PIPELINE` **before** the `lifeos_lessons.py build` step, so freshly generated content is available when lessons are assembled:
```
[sys.executable, "tools/lifeos_generate.py", "missions"],
```
Because of caching (§4.3) this is cheap on days where content already exists. Keep it non-fatal: if Ollama is down, generation should fail soft (log + continue) so the morning pipeline still produces something from existing content — match the existing pipeline's tolerance.

---

## 6. Ollama integration (do this carefully — it's the core)

- Endpoint: `POST http://localhost:11434/api/generate` (or `/api/chat`). Model: `gemma3:12b`.
- Use **structured output**: pass Ollama's `format` parameter set to the JSON schema of the expected object (Ollama supports a JSON-schema `format`). This makes `gemma3` return valid JSON reliably. Set `stream: false`. Set `options.temperature` modestly (e.g. 0.7 for prose variety, but the JSON structure is constrained by `format`).
- Use stdlib `urllib.request` (the repo's convention; see `lifeos_morning_ping.py`). A generation may take 10–60s on a 12B model — set a generous timeout (e.g. 180s) and surface timeouts clearly.
- Add a `check` subcommand that hits `GET http://localhost:11434/api/tags` and confirms `gemma3:12b` is present; print a friendly message if Ollama isn't running.

**Prompt design (build a single well-structured prompt):**
- System/intent: "You are a curriculum author for a personal anti-doomscroll learning app. Produce one tight, accurate, engaging micro-lesson and one quick interactive game to lock it in."
- Inject: the topic, the MISSION.md context (the user's actual goal/constraints/out-of-scope), and the difficulty instruction from the §4.2 table.
- Demand: factual accuracy, no fluff, concrete examples, and a game whose questions actually test the lesson's key idea (recall / spot-the-misconception / ordering — pick what fits).
- Constrain length to fit the difficulty (child = short; expert = denser).
- Output: the exact JSON object from §7.

**Quality bar:** the user's whole competitive edge vs Kinnu/Imprint is generation quality + the difficulty axis. A boring or wrong lesson is a failure even if it renders. Generate, then read one output end-to-end and judge it as a human would.

---

## 7. Data contracts (match exactly)

> ⚠️ The lesson/game field names below are the *intended* shape derived from `INGESTION_CONTRACT`. The **authoritative** lesson + game dict shape is whatever `render_lesson` (L993) and `_game_html` (L887) in `lifeos_lessons.py` actually read. **Open those functions, list every field they access, and make your output match. If there's a conflict, the code wins — update this section to reality.**

**Graph node** (from `INGESTION_CONTRACT.node_schema`, `learning_engine.py` ~L97):
```json
{
  "id": "stable-kebab-id",
  "domain": "history|physics|systems|growth|culture|thinking|custom",
  "title": "Concept title",
  "kind": "article|game|concept|source",
  "xp": 80,
  "url": "/output/learn/<id>.html",
  "summary": "One sentence concept meaning",
  "sources": [{"source_id": "doc-id", "locator": "section"}],
  "difficulty": "intro|core|hard",
  "difficulty_level": "child|teen|undergrad|grad|expert",
  "estimated_minutes": 5,
  "x": 50, "y": 50
}
```
(`x`/`y` are layout coords used by `skill_tree.py`. Pick non-overlapping coords or compute a simple grid placement for new nodes.)

**Graph edge** (from `edge_schema`):
```json
{ "from": "node-id", "to": "node-id", "relation": "prerequisite|practice|application|analogy|review", "reason": "why this edge is real", "confidence": 0.0 }
```
Always create a `practice` edge from the article node → its game node (this mirrors the existing seed graph, e.g. `story-of-civilization → arena-civilization`).

**Lesson + game**: confirmed from `lifeos_lessons.py` on 2026-06-27. `render_lesson()` reads:

```json
{
  "id": "gen-topic-difficulty",
  "emoji": "📚",
  "accent": "#4d7cff",
  "title": "Lesson title",
  "subtitle": "Short dek",
  "minutes": 6,
  "hero_article": "Wikipedia article title or empty string",
  "lead": "Plain text or inline HTML; renderer wraps it in <p class='lead'>",
  "sections": [["Heading", "<p>HTML body</p>", "Wikipedia article title or null"]],
  "ideas": [["Term", "Definition"]],
  "game": {"type": "ponder|order|estimate", "...": "fields below"},
  "did_you_know": "Reveal text",
  "source": ["Source label", "https://source.url"],
  "next": "Optional next action"
}
```

Supported game shapes are:

```json
{"type": "ponder", "prompt": "Think first.", "reveal": "Answer/explanation."}
{"type": "order", "prompt": "Put these in order.", "items": [["i1", "First"], ["i2", "Second"]], "explain": "Why this order is right."}
{"type": "estimate", "prompt": "Estimate X.", "answer": 42, "unit": "items", "reveal": "Reasoning."}
```

The renderer also supports `pd` and `monty`, but Phase 1 generation intentionally emits only `ponder`, `order`, or `estimate` because those map cleanly to arbitrary topics.

---

## 8. Implementation order (do it in this sequence)

1. **Recon.** Read `lifeos_lessons.py` L866–L1031, `lifeos_skill_tree.py` L21–L205, `INGESTION_CONTRACT` in `learning_engine.py`. Write down the exact lesson + game dict fields. Update §7 to match reality.
2. **`check` subcommand + Ollama call.** Get a single raw generation working against `gemma3:12b` with `format` JSON. Print it. Don't integrate yet.
3. **Schema validation + retry.** Validate the LLM JSON; one retry on failure.
4. **Graph store (§5.1).** Add the loader/merge to `skill_tree.py`; create `graph-store.json` from the seed. Verify `skill_tree.py build` and `learning_engine.py build` still run clean.
5. **`topic` subcommand end-to-end.** Generate → validate → merge into store → write lesson in the format `lessons.py` consumes → confirm it renders.
6. **`missions` subcommand.** Loop over `~/learn/*/MISSION.md`.
7. **Caching (§4.3).**
8. **Pipeline wiring (§5.3).**

---

## 9. Verification / acceptance criteria

The build is done when ALL of these pass (the verifier will check these):

1. `python tools/lifeos_generate.py check` reports Ollama up + `gemma3:12b` present.
2. `python tools/lifeos_generate.py topic --name zero-knowledge-proofs --difficulty teen` exits 0 and prints a result JSON.
3. After that run, `graph-store.json` contains a new article node + game node + a `practice` edge, with `difficulty_level: "teen"`.
4. The generated lesson **renders**: running `python tools/lifeos_lessons.py build` (and/or `lifeos_skill_tree.py build`) produces an HTML page for the new node that opens in a browser with the lesson text, image, and a playable game — no missing fields, no template errors.
5. Re-running the same `topic` command **without** `--force` reports "reused" and makes **no** Ollama call (fast).
6. Running the same command with **different** `--difficulty` produces a **distinctly** different lesson (visibly simpler for `child`, denser for `expert`) — confirm by reading both.
7. `python tools/lifeos_generate.py missions` generates for all three `~/learn` topics; per-topic status reported; one topic failing doesn't abort the others.
8. `python tools/lifeos_morning.py run` completes with the new generation step in the pipeline and `today.json` reflects generated content. If Ollama is stopped, the pipeline still completes (generation fails soft).
9. **Human quality check:** open one generated `teen` lesson and one `expert` lesson and read them. They must be accurate, non-generic, and the game must actually test the lesson. (This is a real gate, not a formality.)

---

## 10. Conventions (match the codebase)

- `from __future__ import annotations`, full type hints.
- `argparse` with subcommands; `main() -> int`; `raise SystemExit(main())`.
- Import paths via `from lifeos_paths import APP_ROOT, VAULT_ROOT`. Never hardcode `C:\Users\...`.
- stdlib only for HTTP (`urllib.request`) unless you confirm a dep is already vendored/installed.
- Print machine-readable JSON summaries from commands (the pipeline scrapes stdout).
- Fail soft inside the morning pipeline; fail loud (non-zero, clear message) for direct CLI misuse.
- Keep generated prose free of copyrighted long-form text (the `INGESTION_CONTRACT.copyright_rule` — store summaries/original explanations, not pasted books).

---

## 11. Risks & notes

- **Renderer field mismatch** is the most likely failure. Mitigate by step 1 (recon) — get the exact fields before generating.
- **gemma3 JSON reliability**: rely on Ollama `format` schema, not prompt-only "return JSON". Always validate + retry.
- **Latency**: 12B generation is slow; caching (§4.3) is what makes daily runs viable. Don't skip it.
- **Coordinate collision** in the graph layout: new nodes need sane `x`/`y`. A simple incremental grid is fine; the graph page also has a mobile stacked view so exact layout isn't critical.
- Leave a clean seam for Phase 2 (Mini App): keep generated lessons as self-contained pages addressable by URL so they can later be served over an HTTPS tunnel and wrapped as a Telegram Mini App.

---

## 12. Quick reference — commands the implementer will use

```bash
ollama list                                   # confirm gemma3:12b present
cd /c/Users/adars/Coding/lifeos
python tools/lifeos_generate.py check
python tools/lifeos_generate.py topic --name zero-knowledge-proofs --difficulty teen
python tools/lifeos_generate.py topic --name zero-knowledge-proofs --difficulty expert
python tools/lifeos_generate.py missions
python tools/lifeos_skill_tree.py build
python tools/lifeos_lessons.py build
python tools/lifeos_morning.py run
```
