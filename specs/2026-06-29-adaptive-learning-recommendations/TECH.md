# Tech Spec: Adaptive Learning Levels and Recommendations

## Current context

Relevant files:

- `tools/lifeos_skill_tree.py`
  - Builds `skill-tree.html` and embeds the graph plus browser-side progress logic.
  - Already has total XP/level, done/review storage, graph rendering, and a simple next-steps list.
- `tools/lifeos_learning_engine.py`
  - Builds `learning-system.html` with due review/frontier/mixed practice queues.
  - Already uses spaced review intervals and prerequisite satisfaction.
- `tools/lifeos_lessons.py`
  - Builds `/learn` deck and a browser-side recommendation catalog based on lesson metadata/categories.
  - Already uses localStorage progress/skips/yes signals.
- `tools/lifeos_vercel_build.py`
  - Runs static build for Vercel.

Progress storage:

```js
localStorage['lifeos.learning.progress.v1'] = {
  done: {
    [nodeId]: { at, xp, title, kind, domain }
  },
  reviews: {
    [nodeId]: { at, stage }
  }
}
```

## Proposed implementation

### 1. Shared browser-side model inside graph/training pages

Add lightweight functions to the generated JS:

- `nodeLevel(node)`
  - Uses `difficulty_level`/`difficulty` when available.
  - Falls back to XP + incoming prerequisites + outgoing complexity.
- `learnerModel()`
  - Returns total XP, overall level, done set, and per-domain stats.
- `prereqInfo(node, done)`
  - Returns prerequisite list, completed count, ratio, and missing titles.
- `reviewInfo(id)`
  - Uses existing review intervals.
- `recommendations(limit)`
  - Scores due reviews and new candidates.
  - Returns `{node, score, kind, readiness, reasons, prereq, nodeLevel, domainLevel}`.

### 2. Graph page UI

Update `tools/lifeos_skill_tree.py`:

- Add an assessment area to the profile card.
- Replace `renderQueue()` with recommendation-driven output.
- In personal mode, show learned nodes plus top recommended nodes, not only outgoing nodes.
- Add recommendation reasons in the right-side queue.
- Add node level/readiness in preview metadata.

### 3. Training queue UI

Update `tools/lifeos_learning_engine.py`:

- Reuse the same conceptual scoring logic.
- Show level/profile metrics.
- Make frontier/mixed practice recommendation-driven and explainable.

### 4. Learn deck ranking

Update `tools/lifeos_lessons.py` lightly:

- Add estimated lesson level to the card catalog.
- Include a level/readiness chip in card metadata.
- Adjust ranking to prefer lessons near the user's overall/domain level and interests.

This can be approximate because the graph/training pages are the authoritative adaptive surfaces.

## Scoring sketch

Due review:

```text
score = 10000 + reviewOverdueDays * 20 + nodeLevel * 2
```

New candidate:

```text
score =
  120 * prereqRatio
+  70 * levelFit
+  35 * graphFrontier
+  25 * weakDomainBoost
+  20 * interestBoost
+  10 * explorationHash
-  60 * missingPrereqPenalty
```

Readiness:

- `ready`: prereq ratio 1 and level gap <= 1
- `almost`: prereq ratio >= .66 and level gap <= 2
- `stretch`: level gap > 2
- `explore`: no prerequisites/root item

## Risks and mitigations

- **Risk: fake precision.** Avoid pretending the model is smarter than the data. Use labels like readiness and reasons, not exact mastery percentages.
- **Risk: empty recommendations.** Always include root/explore fallback.
- **Risk: performance regression.** Keep scoring O(nodes + edges) and cache maps/sets in JS.
- **Risk: UX clutter.** Show only top reasons and compact bars on mobile.

## Validation

Commands:

```bash
py -3 -m py_compile tools/lifeos_skill_tree.py tools/lifeos_learning_engine.py tools/lifeos_lessons.py
py -3 tools/lifeos_vercel_build.py
node inline-script-parse-check
```

Browser checks:

- Empty progress graph/training screenshots.
- Seeded progress graph/training screenshots.
- Reset clears levels without reload.
- Global graph performance loop max render under 100ms.
