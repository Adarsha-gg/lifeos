# LifeOS Quest Hub — how to build with this design system

LifeOS is a personal learning-RPG. The aesthetic is **Warm Parchment / Fable storybook**: cream paper surfaces, warm brown ink, terracotta + gold accents, editorial **Fraunces** serif for display and reading, system-ui for small UI chrome. Build screens that feel like "here is your character, here is your world, here is your next quest" — not a dashboard.

## Wrapping & setup

Wrap each screen/app root in `<div className="lo-root">`. That element paints the parchment background + paper texture and sets the default ink color and font. Design tokens live in `:root` (global), so individual components are styled even without the wrapper — but the **page background and inherited text styling only appear inside `.lo-root`**. There is no React provider and no theme context to configure; importing the bundle's `styles.css` closure is all the setup required.

## Styling idiom — tokens, not new class names

This is a **CSS-custom-property token system plus ready-made components**. Two rules:

1. **Compose the real components** for anything they cover (`window.LifeOS.*`). Don't rebuild a parchment card by hand — use `ParchmentCard`, `MainQuestCard`, etc.
2. **For your own layout glue, style with the `--lo-*` tokens** (inline `style` or your own CSS). Do **not** invent a parallel color/spacing vocabulary and do **not** assume Tailwind-style utility classes exist — the only `lo-` classes are the components' own internals. Use the tokens:

- **Surfaces**: `--lo-paper`, `--lo-paper-2`, `--lo-card`, `--lo-card-2`
- **Ink/text**: `--lo-ink`, `--lo-ink-soft`, `--lo-muted`
- **Lines**: `--lo-line`, `--lo-line-strong`
- **Accents**: `--lo-accent` (terracotta, primary action), `--lo-gold` (XP/ranks/rewards), plus `-soft`/`-wash` variants of each
- **Semantic**: `--lo-green` (mastered), `--lo-blue` (review/info), `--lo-rose` (overdue) + `-wash` tints
- **Type**: `--lo-font-display` (Fraunces, headings), `--lo-font-serif` (Fraunces, reading), `--lo-font-ui` (UI chrome), `--lo-font-mono`
- **Radii**: `--lo-r-sm|md|lg|xl|pill` · **Spacing**: `--lo-sp-1`…`--lo-sp-7` · **Shadows**: `--lo-shadow-sm|md|lg`, `--lo-shadow-inset`

Headings and body reading text should use `font-family: var(--lo-font-display)` / `var(--lo-font-serif)`; reserve `var(--lo-font-ui)` for small labels, chips, and controls.

## Where the truth lives

Read these before styling: the stylesheet closure at `_ds/<folder>/styles.css` → `_ds_bundle.css` (component CSS + the full `:root` token block) and `fonts/fonts.css` (Fraunces `@font-face`). Per-component API + usage is in each `components/general/<Name>/<Name>.prompt.md` and `<Name>.d.ts`.

## Idiomatic build snippet

```jsx
// A Quest Hub home surface, on-brand by construction.
<div className="lo-root" style={{ padding: "var(--lo-sp-5)", display: "grid", gap: "var(--lo-sp-5)", maxWidth: 560, margin: "0 auto" }}>
  <ProfileRankHeader name="Adarsha" role="learner" level={5}
    rankTitle="Apprentice Cartographer" tier="gold" xp={320} xpToNext={500}
    streak={7} persistence="local-only" />

  <MainQuestCard kind="review" domain="Systems Thinking"
    title="3 cards are due for review"
    reason="Reviewing now keeps these concepts in long-term memory — and protects your streak."
    xpReward={80} minutes={6} />

  <h2 style={{ fontFamily: "var(--lo-font-display)", color: "var(--lo-ink)", margin: 0 }}>
    Your quest path
  </h2>
  <QuestPath steps={[
    { lane: "Review", title: "Clear 3 due cards", state: "current", xp: 80 },
    { lane: "Ready next", title: "Al-Khwarizmi & Algorithmic Procedure", state: "ready", xp: 120 },
    { lane: "Stretch", title: "Gödel & the Limits of Proof", state: "locked", xp: 200 },
  ]} />
</div>
```

The learning deck has a non-negotiable contract: its bottom controls are **only** `No` and `Read` (`DeckControls`) — never add more.
