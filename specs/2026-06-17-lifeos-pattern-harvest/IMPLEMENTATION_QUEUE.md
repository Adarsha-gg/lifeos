# IMPLEMENTATION_QUEUE.md — Ordered Pattern Steal Plan

## Phase 0 — Guardrails

### T0.1 — License gate — DONE

- Source: all
- Goal: prevent accidental AGPL contamination.
- Completed: `SOURCE_MAP.md` and `output/lifeos-reference-repos.json` record license/copy policy.
- Rule: MIT/Apache code-level reuse allowed with attribution; AGPL/fair-code/unclear are pattern-only unless accepted.
- Validation: source-map entries and reference repo output include license/status.

### T0.2 — Local clone/update script — DONE

- Source: all
- Goal: one repeatable command to refresh reference repos under temp research directory.
- Added `tools/lifeos_reference_repos.py`.
- Validation: lists repo, commit hash, license, local path; 14/15 repos OK, one Windows path-length failure recorded.

## Phase 1 — Safety Substrate

### T1.1 — Approval queue v2 — DONE

- Source: S2 PersonalDataHub, S6 Clira
- Current state: `tools/lifeos_actions.py` exists.
- Added:
  - `purpose`
  - `risk_level`
  - `preview`
  - `created_by`
  - `approved_at` / `rejected_at`
  - immutable `action_snapshot`
  - `snapshot_hash` integrity check before decision
  - `decided_by`
- Validation: propose/list/approve/reject works; dashboard shows pending count.

### T1.2 — Audit log — DONE

- Source: S2 PersonalDataHub, S3 Kebab logs
- Added append-only `output/lifeos-audit.jsonl` via `tools/lifeos_audit.py`.
- Logs connector refreshes, staged actions, approvals/rejections, and dashboard refreshes.
- Validation: staged action and rejection wrote audit events.

### T1.3 — Tool risk policy — DONE

- Source: Clira, PersonalDataHub, VaultBridge references
- Added simple policy in `tools/lifeos_policy.py`:
  - read: auto
  - draft/create preview: stage
  - send/post/delete/payment: approval required
- Validation: connector JSON includes policy table and dashboard displays Action Policy.

## Phase 2 — Local Data Substrate

### T2.1 — Append-only local archive — DONE

- Source: S5 vadimgest, S7 chief-of-staff
- Added `tools/lifeos_archive.py` and `data/lifeos/archive/<source>.jsonl` runtime archive.
- Initial sources: daily todo, GitHub issues, Gmail metadata when connected, calendar events when connected.
- Validation: sync writes JSONL records without mutating old rows.

### T2.2 — SQLite FTS index — DONE

- Source: S5 vadimgest, S7 chief-of-staff
- Added runtime `data/lifeos/lifeos.sqlite` with records + FTS5.
- Validation: CLI can search records across sources.

### T2.3 — Dashboard reads archive first — DONE

- Source: S5 vadimgest
- Dashboard now includes Local Archive summary from cached records via connector JSON.
- Startup refresh now syncs archive between connector pull and dashboard render.
- Validation: dashboard renders archive card from cached records.

## Phase 3 — Core Connectors

### T3.1 — Gmail connector finalization — AUTH BLOCKED

- Source: S1 mcp-personal-suite, S2 PersonalDataHub, S6 Clira
- Current implementation uses existing `gmcli` path in dashboard/connectors.
- Gmail categories already exist:
  - priority inbox
  - needs reply
  - LinkedIn signals
  - receipts/security
- Blocker: Google OAuth credentials/accounts are not configured locally.
- Validation pending: with auth, dashboard card should show real counts and snippets.

### T3.2 — Calendar connector finalization — AUTH BLOCKED

- Source: S1 mcp-personal-suite, S7 chief-of-staff
- Current implementation uses existing `gccli` path for today/tomorrow events.
- Blocker: Google OAuth credentials/accounts are not configured locally.
- Validation pending: dashboard shows upcoming events; no writes without approval.

### T3.3 — Telegram source — PARTIAL

- Source: Ghost/MPA/Thoth pattern
- Current implementation has Telegram bridge status and a command handler, but no private message export/history ingestion.
- Constraint preserved: no private chat dump in dashboard; only actionable recent items if a safe export source is added.
- Validation pending: action-only Telegram summary source.

### T3.4 — GitHub source — DONE

- Source: existing `gh`, S4 OpenTool
- Added assigned issues, PRs needing review, failed workflows.
- Validation: dashboard shows GitHub signals from `gh`.

## Phase 4 — Agent/MCP Exposure

### T4.1 — Codex connector pack — DONE

- Source: S1 mcp-personal-suite
- Current state: Codex MCP has `personal-suite` configured.
- Added `tools/check_lifeos_agents.py` validation command that checks Codex MCP config, Codex CLI availability/list output, Cursor login status, and Gemini auth status.
- Validation: script confirms Codex config contains `personal-suite` server.

### T4.2 — Cursor worker integration — TOOLING DONE / AUTH BLOCKED

- Source: Cursor Agent CLI docs, existing `cursor-worker` skill
- Added `tools/cursor_worker.py` repeatable delegation wrapper with plan mode, worktree mode, current-checkout force mode, JSONL run records, and post-diff verification.
- Validation: status and verification commands work; actual read-only delegation remains blocked until `agent login`.

### T4.3 — MCP/LifeOS local server — DONE

- Source: S2 PersonalDataHub, S3 Kebab, S4 OpenTool
- Added `tools/lifeos_mcp_server.py` exposing LifeOS tools:
  - `lifeos_daily_brief`
  - `lifeos_search_archive`
  - `lifeos_stage_action`
  - `lifeos_list_pending_actions`
- Added `lifeos` MCP server to `C:/Users/adars/.codex/config.toml`.
- Validation: JSON-RPC initialize/tools/list/tool-call smoke test passed and Codex config contains the server.

## Phase 5 — Social Signals

### T5.1 — LinkedIn via Gmail notification fallback — IMPLEMENTED / AUTH BLOCKED

- Source: current dashboard idea, S3 Apify/Unipile as later option
- Gmail connector includes `LinkedIn Signals` category using LinkedIn notification search.
- Blocker: Gmail auth is not configured, so live validation is pending.
- Validation pending: LinkedIn card shows recruiter/founder/message signals only.

### T5.2 — LinkedIn workspace — DONE

- Source: Marvis, Kebab Apify connector
- Added `wiki/personal/linkedin-workspace.md` with action-only signal rules and staged-action draft command.
- Dashboard Social/Text card links to the LinkedIn workspace.
- No feed.
- Validation: only messages/drafts/action items are allowed by the workspace rules.

### T5.3 — WhatsApp/Discord/Slack optional — DEFERRED

- Source: S1 mcp-personal-suite, MPA/Thoth
- Deferred because Adarsha has not explicitly requested these channels and social surfaces should stay minimal.
- Rule remains: approval required for outbound messages.

## Phase 6 — UX Polish

### T6.1 — Setup wizard — DONE

- Source: S1 mcp-personal-suite, MPA, Thoth, Mission Control
- Added `tools/lifeos_setup.py`, `output/lifeos-setup.md`, and `output/lifeos-setup.html` with auth/status checklist and commands.
- Dashboard Quick Links now includes Setup; startup regenerates setup before dashboard render.
- Validation: setup page renders Gmail/Calendar/Cursor/Gemini/archive next steps.

### T6.2 — Telegram command surface — HANDLER DONE

- Source: Ghost
- Added `tools/lifeos_telegram_commands.py` command handler for:
  - `/briefing`
  - `/emails`
  - `/meetings`
  - `/approve <id>`
- Validation: CLI handler returns help/email/meeting outputs; bridge wiring can be added later if needed.

### T6.3 — Goals-first triage — DONE

- Source: S8 chief-of-staff/Gary
- `tools/daily_brief.py` now uses `wiki/personal/current-priorities.md` keywords to score/reorder todos and adds a `Goal Links` section.
- Validation: generated brief explicitly connects top todos to goals. Email goal scoring waits for Gmail auth.

## Future Work — Phone / Android Telemetry

### F1 — Remote phone access outside LAN — TODO

- Preferred path: Tailscale private network, not public port forwarding.
- Goal: open LifeOS dashboard from Android at work/mobile data without exposing `8787` to the internet.
- Expected URL shape: `http://<tailscale-ip>:8787`.
- Guardrail: no public unauthenticated LifeOS dashboard.

### F2 — Android daily metrics import — TODO

- Goal: pull daily phone/body telemetry into LifeOS summary cards.
- Target fields:
  - steps
  - sleep duration if available
  - screen time
  - pickups/unlocks if available
  - top distracting apps if available
- Likely Android sources:
  - Health Connect / Google Fit for steps and health data
  - Digital Wellbeing for screen time, if accessible
  - Tasker/MacroDroid as fallback automation bridge
- Storage target: `data/lifeos/daily_metrics.jsonl`.
- Dashboard target: “Yesterday: steps, sleep, screen time, pickups, focus score.”
- Constraint: keep it local/private; no random health-data SaaS.
