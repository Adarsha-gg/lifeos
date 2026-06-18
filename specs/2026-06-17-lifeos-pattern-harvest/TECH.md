# TECH.md — LifeOS Pattern Harvest

## Current Context

LifeOS currently lives inside `C:/Users/adars/adarsha-knowledge-base`.

Relevant files:

- `tools/lifeos_dashboard.py` — generates the local HTML dashboard.
- `tools/lifeos_connectors.py` — collects connector status/data into `output/lifeos-connectors.json`.
- `tools/lifeos_actions.py` — staged action queue for approval before execution.
- `tools/daily_brief.py` — daily markdown brief generator.
- `tools/open_lifeos_dashboard.ps1` — startup script that refreshes and opens dashboard.
- `wiki/personal/daily-command-center.md` — product-level dashboard goals.
- `wiki/personal/tool-connections.md` — current connector setup notes.

## Research Workspace

Reference repos should be cloned outside the product tree to avoid accidental vendoring:

```text
C:/Users/adars/AppData/Local/Temp/lifeos-research/
```

If a reference becomes important, record commit hash and file paths in `SOURCE_MAP.md`; do not copy files into LifeOS unless explicitly approved.

## Output Artifacts

This spec owns the following working artifacts:

- `SOURCE_MAP.md` — compact reference map with repo/file pointers and adoption decisions.
- `IMPLEMENTATION_QUEUE.md` — ordered task queue for stealing patterns safely.

## Evaluation Dimensions

For each repo, inspect:

1. License and copy risk.
2. Runtime shape: daemon, dashboard, MCP server, CLI, static generator, browser extension, etc.
3. Data model: SQLite, JSONL, Markdown vault, Postgres, Upstash/KV, local config.
4. Connector pattern: direct API, IMAP/CalDAV, OAuth, browser automation, gateway bridge.
5. Safety pattern: approval queue, policy engine, scope separation, audit log, read-only defaults.
6. UX pattern: morning brief, dashboard widgets, Telegram commands, setup wizard, inbox triage.
7. What to adopt now vs later.

## Implementation Ordering Rule

Use this order unless Adarsha overrides:

1. Safety substrate: approval queue, audit log, read-only defaults.
2. Local data substrate: append-only JSONL/SQLite archive.
3. Core connectors: Gmail, Calendar, GitHub, Telegram.
4. Dashboard widgets over local data, not live API spam.
5. Agent/MCP exposure for Codex/Cursor/Gemini.
6. Social DM/signals only after filters and approvals exist.
7. Optional long-tail gateway integration.

## Validation

Before implementing any pattern:

- Cite source-map entry.
- State task ID from implementation queue.
- Run narrow verification for changed code.
- Update `MILESTONES.md` through `spec_append_milestone` when focused.

## Risks

- License contamination from AGPL repos.
- Social automation causing account risk or distraction.
- Dashboard becoming a live API client instead of a stable local view.
- Token leakage if connector code logs secrets or passes credentials to model context.
- Overbuilding multi-user SaaS infra when personal local use is enough.
