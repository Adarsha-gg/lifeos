# SOURCE_MAP.md — LifeOS Pattern Harvest

## Rules

- MIT/Apache code may be inspected and selectively reused with attribution if needed.
- AGPL/fair-code/unclear projects are pattern references only unless license impact is accepted.
- Each implementation task should cite the relevant source entry ID.

## Source Entries

### S1 — mcp-personal-suite

- Repo: `https://github.com/studiomeyer-io/mcp-personal-suite`
- Local clone: `C:/Users/adars/AppData/Local/Temp/lifeos-research/mcp-personal-suite`
- License: MIT
- Category: local-first personal MCP connector suite
- Useful pattern: single local MCP server for email/calendar/messaging/search/image; encrypted config file; dual stdio/HTTP transport; setup wizard.
- Relevant files:
  - `src/lib/config.ts` — unified config shape and atomic encrypted saves.
  - `src/lib/crypto.ts` — AES-256-GCM field encryption.
  - `src/cli/setup.ts` — browser OAuth setup flow.
  - `src/modules/email/index.ts` — email tool definitions.
  - `src/modules/calendar/index.ts` — calendar tool definitions.
  - `src/modules/messaging/index.ts` — Telegram/Discord/Slack/WhatsApp pattern.
- Adopt now:
  - Use as Codex MCP connector (`personal-suite`) instead of building all connectors immediately.
  - Copy the local config + setup wizard pattern conceptually.
- Later:
  - Replace `gmcli/gccli` dashboard pull with direct local connector if needed.

### S2 — PersonalDataHub

- Repo: `https://github.com/AISmithLab/PersonalDataHub`
- Local clone: `C:/Users/adars/AppData/Local/Temp/lifeos-research/PersonalDataHub`
- License: Apache-2.0
- Category: local data hub between personal services and agents
- Useful pattern: zero-access default; quick filters; source connector interface; action staging; audit log; MCP + REST surface.
- Relevant files:
  - `src/gateway/connectors/types.ts` — `SourceConnector`, `SourceBoundary`, `DataRow`, action result interfaces.
  - `src/ai/mcp/server.ts` — MCP tools require purpose strings and stage write actions.
  - `src/database/encryption.ts` — encrypted fields.
  - `src/gateway/audit/log.ts` — audit pattern.
  - `src/gateway/filters.ts` — quick filter concept.
- Adopt now:
  - Approval queue already started in `tools/lifeos_actions.py`.
  - Add purpose/audit fields before enabling write actions.
- Later:
  - Add quick filters for Gmail/LinkedIn/social surfacing.

### S3 — Kebab MCP / mymcp

- Repo: `https://github.com/Yassinello/mymcp`
- Local clone: `C:/Users/adars/AppData/Local/Temp/lifeos-research/mymcp`
- License: AGPL-3.0
- Category: one MCP endpoint with many connectors and dashboard
- Useful pattern: connector manifest registry; per-connector required env vars; dashboard toggles; credential hydration; connector authoring guide; Apify/Unipile for LinkedIn/WhatsApp.
- Relevant files:
  - `src/connectors/google/manifest.ts` — Google connector manifest and tool registration.
  - `src/core/credential-store.ts` — tenant-safe credential hydration pattern.
  - `docs/CONNECTOR-AUTHORING.md` — connector authoring template.
  - `src/connectors/apify/tools/*` — LinkedIn via Apify pattern.
  - `src/connectors/unipile/*` — LinkedIn/WhatsApp bridge pattern.
- Adopt now:
  - Pattern only: connector manifest schema and dashboard status toggles.
- Do not copy code directly without AGPL decision.

### S4 — OpenTool

- Repo: `https://github.com/Aditya251610/opentool`
- Local clone: `C:/Users/adars/AppData/Local/Temp/lifeos-research/opentool`
- License: MIT
- Category: self-hosted MCP tool platform
- Useful pattern: 26 providers / 133 tools; dashboard + MCP endpoint; broad provider matrix; simple hosted/self-hosted story.
- Relevant files: inspect before implementation.
- Adopt now:
  - Provider matrix as checklist for which tools matter.
- Later:
  - Compare its OAuth broker pattern with PersonalDataHub.

### S5 — vadimgest

- Repo: `https://github.com/VCasecnikovs/vadimgest`
- Local clone: not yet cloned
- License: inspect
- Category: local digital-life archive
- Useful pattern: sync 19 sources into append-only JSONL; SQLite FTS5 search; source grid with status, record counts, last sync; dashboard and daemon.
- Relevant files: clone and inspect.
- Adopt now:
  - Build local archive before adding more live dashboard calls.
- High priority.

### S6 — Clira

- Repo: `https://github.com/Rushik-B/Clira` or `https://github.com/sushenSharma/Clira`
- Local clone: `C:/Users/adars/AppData/Local/Temp/lifeos-research/Clira`
- License: MIT
- Category: open-source AI chief of staff
- Useful pattern: deterministic pre-filtering; draft-first queue; planner/style separation so style cannot add facts; Gmail push/pull ingestion.
- Relevant files:
  - `docs/architecture.md` — inspect next.
  - `src/gmail-pull-worker.ts`
  - `tests/gmail-ingestion/*`
- Adopt later:
  - Email triage pipeline after Gmail connector works.

### S7 — chief-of-staff

- Repo: `https://github.com/ceaksan/chief-of-staff`
- Local clone: not yet cloned
- Category: local-first operational assistant
- Useful pattern: SQLite intermediate layer; morning briefing; Obsidian view; separate “AI Plan” calendar.
- Adopt now:
  - Separate AI Plan calendar idea when calendar writes become available.

### S8 — claude-chief-of-staff / Gary-style systems

- Repos:
  - `https://github.com/mimurchison/claude-chief-of-staff`
  - `https://github.com/matthewod11-stack/gary-ai`
- Category: prompt/ops-system chief-of-staff repos
- Useful pattern: goals file as source of truth; meeting prep; relationship memory.
- Adopt now:
  - Goals-first triage: dashboard priorities and email scoring should reference `wiki/personal/current-priorities.md`.

### S9 — Mission Control / Ghost / Thoth / MPA / Marvis / Meepo

- Category: broader daemon/dashboard personal assistants
- Useful patterns:
  - Telegram bot command surface (`/briefing`, `/emails`, `/meetings`).
  - Setup wizard.
  - Approval routing per channel.
  - Local daemon + dashboard packaging.
- Adopt later after core archive/connectors are stable.
