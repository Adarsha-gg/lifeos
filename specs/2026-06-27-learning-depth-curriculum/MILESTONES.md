# Learning Depth Curriculum Milestones

## Cursor infrastructure / validation

## 2026-06-27

- Added `tools/lifeos_curriculum.py` — mastery curriculum infrastructure with optional
  `lifeos_curriculum_content.py` import, track/unit schema, lesson + graph converters.
- Schema supports tracks, units, prerequisites, 5+ page sections, `thinking_questions`,
  `implementation_prompt` / `practice_prompt`, source links, author/collection metadata.
- Fallback seed content: 2 math units, 2 physics units, 1 Paul Graham digest placeholder.
- Wired `lifeos_lessons.py`: curriculum in `lesson_library()`, balanced `daily_set`
  (math, physics, history/civilization, startup, deep history), Curriculum section on `/learn`.
- Wired `lifeos_skill_tree.py` to merge `CURRICULUM_GRAPH` prerequisite edges.
- `lifeos_learning_engine.py` inherits curriculum nodes via merged graph (domain enum extended).
- Validation: py_compile, skill-tree build, learning-engine build, lessons build, Node parse of inline scripts.

## 2026-06-27 — curriculum validation follow-up

- Added `validate_tracks()` and `curriculum_report()` in `lifeos_curriculum.py`:
  duplicate track/unit ids, required fields, broken prerequisites (with LifeOS graph allowlist),
  per-track counts (units, substantial ≥5 sections, questions, missing source URLs).
- CLI: `python tools/lifeos_curriculum.py report|list|validate` (`validate` exits 1 on errors).
- Generated `output/learn/curriculum.html` overview page; `/learn` links to it.
- Validation is CLI-only — lesson/skill-tree builds do not fail on warnings.

## Next (content worker)

- Create `tools/lifeos_curriculum_content.py` exporting `CURRICULUM_TRACKS` with full Paul Graham
  essay corpus, civilization/history units, and expanded math/physics sequences.
- Do not paste copyrighted essay text — summaries, locators, and links per ingestion contract.
- Add cross-track prerequisite edges where justified (e.g. Fermi → math modeling).
- Run `python tools/lifeos_curriculum.py validate` after each bulk ingest; fix errors before merge.

## 2026-06-27 — external content-pack validation

- CLI accepts optional `--content-path PATH` on `report`, `list`, and `validate`.
- Loads `CURRICULUM_TRACKS` via `importlib.util.spec_from_file_location` without permanently
  altering `sys.path` or importing local `lifeos_curriculum_content.py`.
- JSON output includes `content_source`: `seed`, `local`, or the resolved external path.
- Fixture: `specs/2026-06-27-learning-depth-curriculum/fixtures/sample_curriculum_content.py`
  (validation-only; one track, two units, one prerequisite edge).
- Validate Codex content before merge:
  `python tools/lifeos_curriculum.py validate --content-path C:/path/to/tools/lifeos_curriculum_content.py`

## Codex content / Paul Graham ingestion

## 2026-06-27

Implemented bulk curriculum content and Paul Graham essay ingestion scaffolding.

### Delivered

- Added `tools/lifeos_curriculum_content.py`.
- Added `tools/lifeos_paul_graham.py`.
- Kept renderer/infrastructure untouched; `lifeos_curriculum_content.py` documents the import contract for any future renderer or scheduler.

### Curriculum Counts

- Math mastery: 63 units, 10 substantial units, 209 sections, 210 thinking questions.
- Physics mastery: 51 units, 9 substantial units, 171 sections, 171 thinking questions.
- Civilization/history: 36 units, 7 substantial units, 122 sections, 124 thinking questions.

### Paul Graham Ingestion

- Official index: `https://www.paulgraham.com/articles.html`.
- Validation run discovered 231 official essay links from the live index.
- Small isolated export wrote 8 fetched essay digest units to `.tmp-lifeos-vault/output/learn/paul-graham-essays.json`.
- Full isolated metadata export then wrote 231 essay digest units to `.tmp-lifeos-vault/output/learn/paul-graham-essays.json`.
- Output stores titles, URLs, original digest text, tags, application prompts, thinking questions, dates when extractable, and small derived text signals.
- Output does not store full essay bodies.
- Resume behavior: existing units are reused by official URL unless `--refresh` is passed.
- Refresh behavior: run `python tools/lifeos_paul_graham.py build --refresh` without `--limit` to create or refresh one unit per essay currently present in the official index.
- Offline behavior: if the official index cannot be fetched, the script can use its static fallback list until a later refresh.

### Validation Commands

```powershell
python -m py_compile tools\lifeos_curriculum_content.py tools\lifeos_paul_graham.py
python tools\lifeos_curriculum_content.py
$env:LIFEOS_VAULT=(Join-Path (Get-Location) '.tmp-lifeos-vault'); python tools\lifeos_paul_graham.py list --limit 5
$env:LIFEOS_VAULT=(Join-Path (Get-Location) '.tmp-lifeos-vault'); python tools\lifeos_paul_graham.py build --limit 8 --refresh --sleep 0.02
$env:LIFEOS_VAULT=(Join-Path (Get-Location) '.tmp-lifeos-vault'); python tools\lifeos_paul_graham.py build --metadata-only --refresh
$env:LIFEOS_VAULT=(Join-Path (Get-Location) '.tmp-lifeos-vault'); python tools\lifeos_paul_graham.py count
```

### Next Expansion

Add renderer integration that converts `CURRICULUM_TRACKS` and PG essay units into LifeOS learning-engine graph nodes, then add per-unit problem sets for the substantial math and physics units.

## 2026-06-27 Schema Fix and PG Track Integration

Fixed the curriculum content pack to satisfy the Cursor curriculum contract and expose Paul Graham essays directly through `CURRICULUM_TRACKS`.

### Delivered

- Added `domain` and `name` metadata to math, physics, history, and Paul Graham tracks.
- Added unit-level `summary`, `subtitle`, single `source`, `prerequisites`, and five-section lesson structure across generated compact and substantial units.
- Added `paul-graham-essays` as a startup-domain track.
- PG track reads `.tmp-lifeos-vault/output/learn/paul-graham-essays.json` when present, currently exposing 231 official-index essay digest units.
- PG track falls back to static metadata parsed from `tools/lifeos_paul_graham.py` if the JSON export is absent.
- Import remains side-effect safe: no network fetches and no file writes from `tools/lifeos_curriculum_content.py`.

### Validation

```powershell
$env:LIFEOS_VAULT=(Join-Path (Get-Location) '.tmp-lifeos-vault')
python -m py_compile tools/lifeos_curriculum_content.py tools/lifeos_paul_graham.py
python tools/lifeos_curriculum_content.py
python C:/Users/adars/Coding/lifeos-cursor-curriculum-20260627203149/tools/lifeos_curriculum.py validate --content-path tools/lifeos_curriculum_content.py
python C:/Users/adars/Coding/lifeos-cursor-curriculum-20260627203149/tools/lifeos_curriculum.py report --content-path tools/lifeos_curriculum_content.py
```

Cursor validator result: `ok: true`, 4 tracks, 381 units, 1891 questions, 0 errors, 0 warnings, 0 units missing source.

### Refresh

Refresh the full Paul Graham digest export with:

```powershell
$env:LIFEOS_VAULT=(Join-Path (Get-Location) '.tmp-lifeos-vault')
python tools/lifeos_paul_graham.py build --refresh
```

### Next Expansion

Add renderer integration that imports all four tracks into LifeOS learning-engine graph nodes, then attach problem sets and answer checks to the math and physics units.

## 2026-06-27 Integration

- Merged Cursor curriculum infrastructure and validation CLI into the main LifeOS worktree.
- Merged Codex math/physics/history/Paul Graham content pack and Paul Graham refresh script.
- External validation against Codex content passed with 4 tracks, 381 units, 381 substantial units, 1891 thinking questions, 0 errors, and 0 warnings.

## 2026-06-27 Main Worktree Validation

- Integrated Cursor's curriculum infrastructure/validation and Codex's curriculum content/Paul Graham ingestion into the main LifeOS worktree.
- Copied the generated Paul Graham digest metadata to `C:/Users/adars/Coding/knowledgebase/output/learn/paul-graham-essays.json`.
- Validation passed in the main worktree:
  - `python -m py_compile tools/lifeos_curriculum.py tools/lifeos_curriculum_content.py tools/lifeos_paul_graham.py tools/lifeos_lessons.py tools/lifeos_skill_tree.py tools/lifeos_learning_engine.py`
  - `python tools/lifeos_curriculum.py validate` → `ok: true`, 0 errors, 0 warnings.
  - `python tools/lifeos_paul_graham.py count` → 231 official-index essay units.
  - `python tools/lifeos_skill_tree.py build` → 409 graph nodes / 306 edges / 9 domains.
  - `python tools/lifeos_learning_engine.py build` → 409 nodes / 306 edges.
  - `python tools/lifeos_lessons.py build` → 402 lessons in the library.
  - Node parsed inline scripts for `/learn`, `skill-tree.html`, `curriculum.html`, and representative math/physics/history/Paul Graham lesson pages.
  - Headless Edge screenshots of `/learn` and `curriculum.html` rendered correctly.

## 2026-06-27 Strategic / Analytical Expansion

- Added three additional mastery tracks to `tools/lifeos_curriculum_content.py`:
  - `startup-strategy-builders`: 28 startup strategy units covering customer discovery, wedges, distribution, pricing, retention, moats, AI product strategy, crisis communication, and long-term compounding.
  - `strategic-minds-history`: 31 strategic-mind case studies from Sun Tzu, Pericles, Thucydides, Alexander, Kautilya, Hannibal, Caesar, Augustus, Ashoka, Genghis Khan, Machiavelli, Washington, Napoleon, Clausewitz, Lincoln, Bismarck, Churchill, Gandhi, Deng, Lee Kuan Yew, Mandela, Boyd, Grove, and Bezos.
  - `analytical-minds`: 30 analytical-mind case studies from Aristotle, Euclid, Archimedes, Al-Khwarizmi, Ibn al-Haytham, Galileo, Descartes, Newton, Leibniz, Euler, Gauss, Laplace, Faraday, Maxwell, Darwin, Nightingale, Curie, Einstein, Noether, Keynes, Turing, von Neumann, Shannon, Feynman, Simon, Jacobs, Ostrom, Kahneman, Pearl, and Meadows.
- Each new unit has 5 sections, thinking questions, source links, review prompts, and a transfer/application prompt.
- Updated the daily queue so a thinking/analytical unit appears alongside math, physics, history/strategy, startup/PG, and deep history.
- Validation passed:
  - `python -m py_compile tools/lifeos_lessons.py tools/lifeos_curriculum_content.py`
  - `python tools/lifeos_curriculum.py validate` → 10 tracks, 475 units, 475 substantial units, 2346 thinking questions, 0 errors, 0 warnings.
  - `python tools/lifeos_skill_tree.py build` → 498 nodes, 392 edges, 9 domains.
  - `python tools/lifeos_learning_engine.py build` → 498 nodes, 392 edges.
  - `python tools/lifeos_lessons.py build` → 491 lessons in the library.
  - Node parsed inline scripts for `/learn`, `curriculum.html`, and representative strategic/analytical/startup lesson pages.
  - Headless Edge screenshots rendered `/learn` and `curriculum.html` after the expansion.

## 2026-06-27 Nikola Tesla Mastery Track

- Added a dedicated `nikola-tesla-mastery` curriculum track with 49 substantial Tesla units and 343 thinking questions.
- The track wires together books, primary sources, patents, archive links, museum links, AC power, induction motors, high-frequency experiments, the Tesla coil, radio/wireless claims, Colorado Springs, Wardenclyffe, business failures, myth filtering, later-life claims, and a capstone Tesla dossier.
- Added a new `invention` curriculum domain/color/layout and scheduled one invention/Tesla item in the daily learning queue, expanding days with invention content to 7 lessons.
- Fixed curriculum practice prompt plumbing so `application_prompt` content appears in lesson practice boxes.
- Validation passed: curriculum validate (11 tracks, 524 units, 2689 thinking questions, 0 errors/warnings), skill tree build (548 nodes, 454 edges, 10 domains), learning engine build, lesson build (540 lesson library, 7 daily lessons), inline script parse for Tesla pages, and headless Edge screenshots for `/learn`, the Tesla source-map lesson, and curriculum overview.

## 2026-06-27 Julius Caesar Mastery Track

- Added a dedicated `julius-caesar-mastery` curriculum track with 55 substantial Caesar units and 385 thinking questions.
- The track wires together primary sources, modern books, Roman institutions, Gallic campaigns, civil war, dictatorship, assassination, aftermath, moral accounting, and modern strategy/power warning labels.
- Added a new `statecraft` curriculum domain/color/layout and scheduled one statecraft/Caesar item in the daily learning queue, expanding days with Tesla and Caesar content to 8 lessons.
- Source spine includes Caesar's Commentaries, Civil War, Plutarch, Suetonius, Appian, Cassius Dio, Cicero, Sallust, MIT OCW readings, Goldsworthy, Gelzer, Meier, Holland, Beard, Syme, Canfora, and Morstein-Marx.
- Validation passed: Caesar source URL check (25/25 reachable or accepted), curriculum validate (12 tracks, 579 units, 3074 thinking questions, 0 errors/warnings), skill tree build (603 nodes, 509 edges, 11 domains), learning engine build, lesson build (595 lesson library, 8 daily lessons), inline script parse for Caesar pages, and headless Edge screenshots for `/learn`, the Caesar source-map lesson, and curriculum overview.

## 2026-06-28 Lesson depth, source trails, and belief questions

- Extended the lesson renderer so every lesson-library page now includes a reading note, a source/further-reading trail at the bottom, and belief-testing questions that ask for evidence, objections, uncertainty, and dangerous applications instead of trivia/date-order memorization.
- Changed chronological/order challenge rendering into a causal/source-chain challenge that asks the learner to question the model rather than just order events.
- Propagated curriculum unit source lists into rendered lessons, added richer source trails for Socrates, Plato, and the Library of Alexandria, and replaced blocked/broken source URLs with reachable alternatives.
- Fixed the only lesson under five minutes (`survivorship-bias`) to a 5 minute minimum and verified the full 595-lesson library has no page below 5 minutes.
- Verified all 595 lesson-library HTML files include `Sources and further reading` and `Questions worth arguing with` blocks; verified 319 unique external source URLs with 319/319 passing.
- Rebuilt lessons, skill tree, and learning engine, validated curriculum (12 tracks, 579 units, 0 errors/warnings), parsed representative inline scripts, and redeployed the public-safe Vercel learning site with the updated review notes.
