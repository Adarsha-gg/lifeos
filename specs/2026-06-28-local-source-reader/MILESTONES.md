# Milestones

## 2026-06-28 Local-only source reader

- Added a source-first, local-only reader path for user-provided full texts.
- Private source files live under `private/library/`, which is git-ignored and not part of Vercel output.
- The reader renders complete local `.txt`, `.md`, and `.html` inputs into `output/private-readings/` with local text highlighting.
- The local server exposes `/private`; public tunnel allowlist still blocks it.
