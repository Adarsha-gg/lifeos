# design-sync notes — LifeOS Design System

The synced design system is a **purpose-built React library** in `lifeos-ds/` (not extracted
from the Python app). It reproduces the "Warm Parchment / Fable storybook" look for the
Quest Hub flow described in `loop/claude-unified-lifeos-flow-prompt.md`. 15 components.

Project: `LifeOS Design System` — https://claude.ai/design/p/6ecffb18-bd7f-498b-831f-883df07d4bea

## Build / re-sync mechanics

- The DS package lives in `lifeos-ds/`. Build it FROM that dir: `cd lifeos-ds && npm run build`
  (Vite library build → `dist/index.es.js` + `dist/lifeos-ds.css`, then `tsc` emits `.d.ts`).
- Run the converter FROM repo root with explicit paths (the package isn't installed into its
  own node_modules):
  `node .ds-sync/package-build.mjs --config .design-sync/config.json --node-modules ./lifeos-ds/node_modules --entry ./lifeos-ds/dist/index.es.js --out ./ds-bundle`
- Re-sync driver (one command): same `--node-modules` / `--entry`, via `.ds-sync/resync.mjs`,
  with `--remote .design-sync/.cache/remote-sync.json` (fetch the project's `_ds_sync.json` first).
- playwright@latest pins chromium build 1228, which matches the local cache — render check works.

## Decisions / gotchas

- **Fonts**: Fraunces (SIL OFL 1.1), latin subset only, shipped via `cfg.extraFonts`
  (`lifeos-ds/fonts/fraunces-local.css` + 4 woff2). Token stacks name only `Fraunces` +
  web-safe (Georgia/Times) so `[FONT_MISSING]` stays clear. The 400/600/700 woff2 came back
  the same byte size from Google's css2 endpoint — that's the served subset, not a mistake.
- **cardMode column** is set in `cfg.overrides` for the four full-width composite panels
  (MemoryPanel, ProfileRankHeader, MainQuestCard, TeacherPanel) so each story renders one-per-row
  instead of cropping in the product grid. Only MemoryPanel was flagged by `[GRID_OVERFLOW]`;
  the other three are presentation choices.
- Tokens live in `:root` (global); the `.lo-root` wrapper paints the parchment page background
  and editorial defaults. No React provider / theme context — `cfg.provider` is intentionally unset.
- All 15 previews authored in `.design-sync/previews/`, every cell graded `good`. No floor cards.

## User-requested restyle (deliberate — do NOT revert)

- **Block, not rounded**: all radius tokens (`--lo-r-*`) are `0`; circular elements (RankBadge
  crest, TeacherPanel avatar, QuestPath nodes) squared to `border-radius: 0`. GraphPreview SVG
  node/legend dots kept circular (data-viz markers, not UI chrome).
- **Buttons are whiteish/yellowish**, not terracotta/gold fills: `Button` variants + the deck's
  `Read` button use pale cream/butter backgrounds with ink text + a square border. The user
  explicitly disliked the filled colored buttons.
- **No colored side spines** on `CurriculumRail` books — the per-kind colored spine bars (the
  "Paul Graham one") were removed; the glyph column is now a neutral `--lo-card-2` block with a
  thin divider. The user disliked the side highlights.
- The warm parchment palette itself is unchanged — the user likes it.

## Known render warns

None — validate exits 0 with no warnings on the final build.

## Re-sync risks (watch list)

- **Fraunces is fetched from Google Fonts at authoring time only.** The woff2 are committed under
  `lifeos-ds/fonts/`, so a re-sync does NOT refetch — but if those files are ever deleted, the
  download step (a node `fetch` of `fonts.googleapis.com/css2?family=Fraunces...`) must be re-run.
- DeckCard's storybook art is pure CSS (no image assets) — safe across rebuilds.
- The library is hand-authored, not generated from the Python app. If the LifeOS look changes in
  the app, this DS does NOT auto-track it — update `lifeos-ds/src/**` deliberately and re-sync.
- No private/copyrighted text is in the DS (only invented sample lesson titles in previews).
