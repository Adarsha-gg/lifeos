#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from lifeos_audit import log_event
from lifeos_paths import VAULT_ROOT

DATA = VAULT_ROOT / "data" / "lifeos"
EVENTS_JSON = DATA / "events.json"
REPORT = VAULT_ROOT / "output" / "reports" / "web3-events-nyc-nj.md"

# Curated from live web search/fetch on 2026-06-18. Keep this small and high-signal.
SEED_EVENTS: list[dict[str, Any]] = [
    {
        "title": "Fork That NYC NEAR Hackathon",
        "date": "2026-08-09 to 2026-08-10",
        "location": "Station3, 26 Broadway, New York, NY",
        "distance_from_wayne": "~25-35 miles / PATH or drive into Manhattan",
        "kind": "hackathon",
        "status": "registration_closed_watchlist",
        "score": 95,
        "why": "24h IRL hackathon for Web3/AI agents, chain abstraction, intents, dev tooling. $17k prize pool. Very aligned with building/startup goals even if registration is closed; subscribe/contact host.",
        "url": "https://luma.com/ForkThatNYCNEAR",
        "source": "Luma fetched 2026-06-18",
    },
    {
        "title": "Blockchain and Business Networking | Elevating Your Potential - Hoboken",
        "date": "2026-07-15 18:00",
        "location": "The Shepherd & the Knucklehead, Hoboken, NJ",
        "distance_from_wayne": "~20 miles / easier than deep Manhattan",
        "kind": "networking",
        "status": "listed",
        "score": 78,
        "why": "Nearby NJ blockchain networking. Lower technical depth, but useful for reps, contacts, and getting out of the house.",
        "url": "https://www.eventbrite.com/d/ny--new-york/blockchain/",
        "source": "Eventbrite NYC blockchain listing fetched 2026-06-18",
    },
    {
        "title": "Bitcoin/Altcoins & Cryptocurrency Enthusiast Night - Crypto Gathering",
        "date": "2026-08-24 18:30",
        "location": "Dawson 39 Restaurant & Bar, New York, NY",
        "distance_from_wayne": "~25-35 miles",
        "kind": "meetup",
        "status": "listed",
        "score": 62,
        "why": "More casual crypto meetup. Good for talking to humans; lower builder signal than a hackathon.",
        "url": "https://www.eventbrite.com/d/ny--new-york/blockchain/",
        "source": "Eventbrite NYC blockchain listing fetched 2026-06-18",
    },
    {
        "title": "THE NEW YORK BLOCKCHAIN FESTIVAL",
        "date": "2026-09-04 09:00",
        "location": "Convene Brookfield Place, 225 Liberty, New York, NY",
        "distance_from_wayne": "~25-35 miles",
        "kind": "conference",
        "status": "listed",
        "score": 74,
        "why": "Broad blockchain festival in NYC. Useful if agenda has founder/dev tracks; verify before committing money/time.",
        "url": "https://www.eventbrite.com/d/ny--new-york/blockchain/",
        "source": "Eventbrite NYC blockchain listing fetched 2026-06-18",
    },
    {
        "title": "Bitcoin Treasuries Conference: September 2026",
        "date": "2026-09",
        "location": "Lavan Midtown, 641 W 42nd St, New York, NY",
        "distance_from_wayne": "~25-35 miles",
        "kind": "conference",
        "status": "tickets_available_student_or_approval",
        "score": 58,
        "why": "More capital/treasury strategy than building. Useful only if you want finance/network exposure; not first priority for coding.",
        "url": "https://luma.com/btunyc",
        "source": "Luma fetched 2026-06-18",
    },
    {
        "title": "Blockchain Tech Summit (4th Annual)",
        "date": "2026-09-25 11:00",
        "location": "New York, NY — location TBA",
        "distance_from_wayne": "~25-35 miles",
        "kind": "conference",
        "status": "listed",
        "score": 70,
        "why": "Potentially useful technical/business blockchain summit. Needs agenda check before registering.",
        "url": "https://www.eventbrite.com/d/ny--new-york/blockchain/",
        "source": "Eventbrite NYC blockchain listing fetched 2026-06-18",
    },
    {
        "title": "4th Annual Ownership Economy Summit",
        "date": "2026-10-01 08:30",
        "location": "140 Broadway, New York, NY",
        "distance_from_wayne": "~25-35 miles",
        "kind": "summit",
        "status": "listed",
        "score": 68,
        "why": "Ownership economy is adjacent to crypto/startups. Good if agenda includes protocols, networks, or founder/operators.",
        "url": "https://www.eventbrite.com/d/ny--new-york/blockchain/",
        "source": "Eventbrite NYC blockchain listing fetched 2026-06-18",
    },
]

SOURCE_LINKS = [
    {"name": "ETHGlobal events", "url": "https://ethglobal.com/", "note": "Watch for NYC/regional hackathons."},
    {"name": "NYC Blockchain Network", "url": "https://blockchainnyc.net", "note": "Monthly NYC builder/founder events; Telegram linked from Luma/Eventbrite pages."},
    {"name": "Eventbrite NYC blockchain", "url": "https://www.eventbrite.com/d/ny--new-york/blockchain/", "note": "Broad listings; filter aggressively for builder signal."},
    {"name": "Luma NYC web3", "url": "https://luma.com", "note": "Best source for smaller builder events, hackathons, investor nights."},
]


def save_events(events: list[dict[str, Any]]) -> dict[str, Any]:
    DATA.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "home_base": "Wayne, New Jersey",
        "radius": "NYC / North Jersey / nearby regional web3 events",
        "items": sorted(events, key=lambda e: (-int(e.get("score", 0)), str(e.get("date", "")))),
        "source_links": SOURCE_LINKS,
    }
    EVENTS_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    write_report(payload)
    log_event("events_refreshed", "lifeos_events", count=len(payload["items"]))
    return payload


def write_report(payload: dict[str, Any]) -> None:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Web3 Events — NYC / NJ",
        "",
        f"Generated: {payload.get('generated_at')}",
        "Home base: Wayne, NJ",
        "",
        "## Best Bets",
        "",
    ]
    for event in payload.get("items", []):
        lines += [
            f"### {event.get('title')}",
            "",
            f"- Date: {event.get('date')}",
            f"- Location: {event.get('location')}",
            f"- Kind: {event.get('kind')} / status: {event.get('status')}",
            f"- Distance: {event.get('distance_from_wayne')}",
            f"- Score: {event.get('score')}",
            f"- Why: {event.get('why')}",
            f"- Link: {event.get('url')}",
            f"- Source: {event.get('source')}",
            "",
        ]
    lines += ["## Watch Sources", ""]
    for source in payload.get("source_links", []):
        lines.append(f"- [{source.get('name')}]({source.get('url')}) — {source.get('note')}")
    lines.append("")
    REPORT.write_text("\n".join(lines), encoding="utf-8")


def events_summary(limit: int = 5) -> dict[str, Any]:
    if not EVENTS_JSON.exists():
        payload = save_events(SEED_EVENTS)
    else:
        try:
            payload = json.loads(EVENTS_JSON.read_text(encoding="utf-8"))
        except Exception:
            payload = save_events(SEED_EVENTS)
    items = payload.get("items", []) if isinstance(payload, dict) else []
    return {
        "configured": True,
        "items": items[:limit],
        "status": f"{len(items)} curated web3 event(s) near Wayne/NYC.",
        "report": str(REPORT.relative_to(VAULT_ROOT)),
        "source_links": payload.get("source_links", []),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Curate relevant Web3 events near Wayne, NJ / NYC")
    parser.add_argument("cmd", choices=["refresh", "summary"], nargs="?", default="refresh")
    args = parser.parse_args()
    if args.cmd == "refresh":
        print(json.dumps(save_events(SEED_EVENTS), indent=2))
    else:
        print(json.dumps(events_summary(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
