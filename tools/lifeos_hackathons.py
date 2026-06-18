#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from lifeos_audit import log_event
from lifeos_paths import VAULT_ROOT

DATA = VAULT_ROOT / "data" / "lifeos" / "hackathons"
REPORTS = VAULT_ROOT / "output" / "reports"

CROO_BUIDLS: list[dict[str, Any]] = [
    {
        "name": "ShipKit",
        "url": "https://dorahacks.io/buidl/44525",
        "github": "https://github.com/icohangar-ops/shippingkit_CROO",
        "verified_for_croo": True,
        "track": "Developer Tooling Agents",
        "what_they_made": "Developer command center for CROO Agent Protocol: scaffold a callable paid agent, audit CAP integration against @croo-network/sdk, and generate Agent Store listing copy.",
        "evidence": [
            "Uses real @croo-network/sdk surface in generated provider.ts.",
            "Audit harness scores AgentClient init, OrderPaid handler, deliverable type matching, typed errors, idempotent delivery.",
            "Includes E2E lifecycle harness for NegotiationCreated → acceptNegotiation → OrderPaid → deliverOrder → OrderCompleted.",
            "CI reports static + E2E status on push/PR.",
        ],
        "strengths": [
            "Directly hackathon-native: makes other CROO builders ship faster.",
            "Clear wedge: scaffold/audit/list are concrete commands, not vague agent fluff.",
            "Developer tooling is usually easier to judge because outputs are deterministic.",
            "Strong if the demo shows real SDK compliance and catches broken providers.",
        ],
        "risks": [
            "May look like tooling instead of an end-user agent business unless demo ties to paid agent revenue.",
            "Depends on real CROO SDK compatibility; any fake/mock integration would hurt it.",
        ],
        "score": 88,
        "verdict": "Strongest verified CROO-specific BUIDL found so far. Best inspiration: build tools that create/audit/list agents, not just another agent demo.",
    },
    {
        "name": "Cobot",
        "url": "https://dorahacks.io/buidl/39733",
        "github": "",
        "verified_for_croo": False,
        "track": "DeFi / on-chain ops agent style",
        "what_they_made": "One-click autonomous trading agents with MCP tools for perps, memes, prediction markets, yield farming, cross-chain swaps, and live execution logs.",
        "evidence": [
            "Durable Object agents with persistent state and scheduled execution loop.",
            "Strategies include DCA, meme sniper, yield farmer, prediction trader.",
            "Claims 50+ MCP tools and per-user wallet isolation/risk controls.",
        ],
        "strengths": [
            "Good product shape: launch useful agents quickly with visible logs.",
            "If real, breadth of tools is impressive.",
        ],
        "risks": [
            "Not verified as a CROO submission from public data.",
            "Trading-agent category is crowded and risky; judges may punish hand-wavy execution.",
            "Needs proof of live trades/risk controls, otherwise it is a dashboard story.",
        ],
        "score": 72,
        "verdict": "Interesting adjacent competitor/inspiration, but not counted as confirmed CROO until the DoraHacks BUIDL list exposes it.",
    },
]

ADJACENT_STRONG_PROJECTS: list[dict[str, Any]] = [
    {
        "name": "AgentFabric",
        "url": "https://dorahacks.io/buidl/38376",
        "why_track": "Strong x402/agent infrastructure pattern: scoped session keys, paid API calls, MCP execution surface, bounded agent autonomy.",
        "score": 90,
    },
    {
        "name": "Nexus-402",
        "url": "https://dorahacks.io/buidl/38433/",
        "why_track": "Platform thesis: registry + workflow engine + SDK + CLI + MCP, with deployed contracts and registered agents.",
        "score": 88,
    },
    {
        "name": "Croquity",
        "url": "https://dorahacks.io/buidl/38348",
        "why_track": "Strong proof metrics: autonomous treasury payouts, live transactions, policy engine, transparent reasoning.",
        "score": 86,
    },
    {
        "name": "AgentMarket",
        "url": "https://dorahacks.io/buidl/38189",
        "why_track": "Marketplace/service registry + HTTP 402 settlement for machine-to-machine APIs. Good pattern for agent economy UX.",
        "score": 82,
    },
]


def payload() -> dict[str, Any]:
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "hackathon": "CROO Agent Hackathon",
        "source_url": "https://dorahacks.io/hackathon/croo-hackathon/buidl",
        "status_note": "DoraHacks page reports BUIDLs11, but direct scraping is blocked by AWS WAF/JS and Exa returned 'No BUIDLs'. This report tracks verified/search-index-visible projects and separates unverified adjacent hits.",
        "confirmed_buidls": CROO_BUIDLS,
        "adjacent_strong_projects": ADJACENT_STRONG_PROJECTS,
    }


def write_report(data: dict[str, Any]) -> Path:
    REPORTS.mkdir(parents=True, exist_ok=True)
    path = REPORTS / "croo-hackathon-buidl-scout-2026-06-18.md"
    lines = [
        "# CROO Agent Hackathon — BUIDL Scout",
        "",
        f"Generated: {data['generated_at']}",
        f"Source: {data['source_url']}",
        "",
        "## Important caveat",
        "",
        data["status_note"],
        "",
        "I am not treating stale/adjacent DoraHacks search hits as confirmed CROO submissions unless the project text explicitly ties itself to CROO or the BUIDL list exposes it.",
        "",
        "## Strongest confirmed / visible CROO BUIDLs",
        "",
    ]
    for item in data["confirmed_buidls"]:
        lines += [
            f"### {item['name']} — score {item['score']}",
            "",
            f"- URL: {item['url']}",
            f"- GitHub: {item.get('github') or '_not found_'}",
            f"- Verified CROO: {item['verified_for_croo']}",
            f"- Track: {item['track']}",
            f"- What they made: {item['what_they_made']}",
            f"- Verdict: {item['verdict']}",
            "",
            "Strengths:",
        ]
        lines += [f"- {s}" for s in item["strengths"]]
        lines += ["", "Risks:"]
        lines += [f"- {r}" for r in item["risks"]]
        lines.append("")
    lines += [
        "## Adjacent strong projects to steal patterns from — not confirmed CROO",
        "",
    ]
    for item in data["adjacent_strong_projects"]:
        lines += [f"- **{item['name']}** — score {item['score']} — {item['why_track']} ({item['url']})"]
    lines += [
        "",
        "## What this means for us",
        "",
        "- Strong projects show proof: real SDK/API use, live transactions, CI, deployed contracts, demo video, clear runbook.",
        "- Weak projects are generic 'AI agent marketplace' slides with no verifiable path.",
        "- If we enter, do not build a vague agent. Build either:",
        "  1. a concrete research/verifier agent with paid deliverables, or",
        "  2. developer tooling that scaffolds/audits CROO agents like ShipKit but for a narrower killer workflow.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Track hackathon BUIDLs and write scout reports")
    parser.add_argument("target", choices=["croo"], nargs="?", default="croo")
    args = parser.parse_args()
    DATA.mkdir(parents=True, exist_ok=True)
    data = payload()
    json_path = DATA / "croo-buidls.json"
    json_path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    report = write_report(data)
    log_event("hackathon_report_refreshed", "lifeos_hackathons", target=args.target, confirmed=len(CROO_BUIDLS), adjacent=len(ADJACENT_STRONG_PROJECTS))
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
