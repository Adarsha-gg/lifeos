# BUILD SPEC — Generation layer fixes (post-validation cleanup)

**Status:** Ready to build
**Context:** Phase 1 (`specs/2026-06-27-ai-content-generation/PLAN.md`) is built and validated working. These are the issues found during validation. None block usage; do them in priority order. Small, surgical changes only.

Files in play: `tools/lifeos_generate.py`, `tools/lifeos_morning.py`, `tools/lifeos_lessons.py`, `tools/lifeos_skill_tree.py`.

---

## P1 — Generation failures are silent (visibility)

**Problem:** `lifeos_generate.py missions` always `return 0`, even when individual topics fail (Ollama down, invalid JSON twice). Good for pipeline resilience (the morning run continues and serves cached content), but a real failure is invisible — `morning.py`'s `ok` stays true and nothing flags it.

**Fix:**
- In `run_missions`, the payload already has per-topic `ok`/`error`. Surface a summary line to stdout like `GENERATION: 2 ok, 1 failed (ollama down)` so it shows in the morning status JSON / logs.
- In `lifeos_morning_ping.py`, if any generation failed today, append a one-line note to the ping (e.g. "⚠️ 1 topic didn't generate today"). Keep it non-fatal.
- Optionally: add `--strict` to `missions` that exits non-zero on any failure, for manual debugging runs (the pipeline keeps using the default soft mode).

**Acceptance:** stop Ollama, run `python tools/lifeos_morning.py run` → pipeline completes, status JSON clearly shows generation failed, ping notes it, cached lessons still served.

---

## P2 — Redundant game node points to the article page

**Problem:** In `graph_items` (`lifeos_generate.py`), each generated game node's `url` = `/output/learn/{article_id}.html` — the same page as the article (the game is embedded at the bottom, "lesson first, game last"). So the graph shows a separate game node that just reopens the article.

**Decision:** Keep the game node (the learning engine's retrieval-first ordering distinguishes `kind=='game'` and uses it for the practice/review lanes — it has real value), but make its link land on the game.

**Fix:**
- Give the game section in the rendered lesson page an anchor `id="game"` (in `lifeos_lessons.py` where `_game_html`/the play section is emitted).
- Set the game node `url` to `/output/learn/{article_id}.html#game` in `graph_items`.

**Acceptance:** clicking a generated game node in the skill tree opens the lesson scrolled to the game; the article node opens at the top.

---

## P3 — Cache ignores MISSION.md edits

**Problem:** Cache key is `{topic_slug}--{difficulty}`. If the user rewrites a `MISSION.md`, regeneration won't happen without `--force`, so stale content persists.

**Fix:**
- Compute `mission_hash = sha1(clean_mission_text + PROMPT_VERSION)` and store it on the lesson + node.
- In `generate_topic`, treat a cached lesson as valid only if its `mission_hash` matches the current one; otherwise regenerate.
- Add a module-level `PROMPT_VERSION = 1` constant; bump it whenever the prompt/schema changes so all content regenerates on next run.

**Acceptance:** edit a `MISSION.md`, run `topic` without `--force` → it regenerates. Run again unchanged → `reused`.

---

## P4 — `merge_generated` re-appends all domains every call

**Problem:** `merge_generated` extends `graph["domains"]` with the full `DOMAIN_COLORS` set on every generation. It's deduped on save (`merge_graphs`), so harmless, but sloppy and confusing.

**Fix:** Only ensure the single domain actually used by this lesson exists in `graph["domains"]`; rely on `merge_graphs` for dedup. Remove the blanket extend.

**Acceptance:** generating one topic adds at most its own domain; `graph-store.json` domain list stays clean.

---

## P5 — Coarse `difficulty` field collapses 5 levels into 3

**Problem:** `child`+`teen`→`intro`, `grad`+`expert`→`hard`. The true 5-way axis is `difficulty_level` (correct); the coarse `difficulty: intro|core|hard` exists only because the original `INGESTION_CONTRACT` used it.

**Fix (low priority):**
- Audit consumers: confirm nothing important keys off the coarse `difficulty` instead of `difficulty_level`. (Grep `difficulty` across `tools/`.)
- Prefer `difficulty_level` everywhere it matters (graph display, future adaptive difficulty).
- Optional: scale node `xp` by level (e.g. child 60 → expert 140) so the graph rewards harder material.

**Acceptance:** `difficulty_level` is the field used for any per-level behavior; coarse field is display-only or removed.

---

## P6 — (Optional) multi-difficulty + housekeeping
- `topic --difficulty all` to generate every level for a topic in one run (useful for adaptive difficulty later).
- `list` / `prune` subcommands to inspect and remove generated lessons by id/topic.
- These are conveniences, not required.

---

## Order of work
P1 (visibility) → P2 (game anchor) → P3 (mission hash) → P4 (domain dedup) → P5 (difficulty audit) → P6 (optional). Each is independent; ship them as separate small commits.

> Note: P2's coordinate concern disappears entirely if the Obsidian-style force-directed graph (`specs/2026-06-27-obsidian-graph-view/PLAN.md`) lands, since layout becomes automatic. Coordinate quality in `next_coords` is therefore not worth polishing here.
