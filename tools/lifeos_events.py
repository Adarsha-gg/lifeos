#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

from lifeos_audit import log_event
from lifeos_paths import VAULT_ROOT

DATA = VAULT_ROOT / "data" / "lifeos"
EVENTS_JSON = DATA / "events.json"
REPORT = VAULT_ROOT / "output" / "reports" / "web3-events-nyc-nj.md"
TODAY = date(2026, 6, 18)

# Curated from live web search/fetch on 2026-06-18.
# Rule: no events/hackathons with dates or submission deadlines before TODAY.
SEED_EVENTS: list[dict[str, Any]] = [
    {
        "title": "CROO Agent Hackathon",
        "date": "2026-06-09 to 2026-07-12",
        "deadline": "2026-07-12",
        "location": "Virtual",
        "distance_from_wayne": "Remote",
        "kind": "hackathon",
        "status": "open_for_submission",
        "score": 96,
        "why": "Best immediate build target: AI agents + A2A + Web3 + DeFi, GitHub repo and demo video required, $10.2k prize pool. Directly aligned with agent/Web3 startup prototypes.",
        "url": "https://dorahacks.io/hackathon/croo-hackathon",
        "source": "DoraHacks search result, checked 2026-06-18",
    },
    {
        "title": "Casper Agentic Buildathon 2026 — Qualification Round",
        "date": "2026-06-01 to 2026-07-01",
        "deadline": "2026-07-01",
        "location": "Virtual",
        "distance_from_wayne": "Remote",
        "kind": "hackathon",
        "status": "open_for_submission",
        "score": 93,
        "why": "$150k prize pool. Build production-ready apps at the Agentic AI + DeFi + RWA intersection on Casper. Good forcing function for a working prototype and demo video.",
        "url": "https://dorahacks.io/hackathon/casper-agentic-buildathon",
        "source": "DoraHacks search/fetch, checked 2026-06-18",
    },
    {
        "title": "AWS Activate Program for Web3 Startups",
        "date": "2026-02-27 to 2026-07-01",
        "deadline": "2026-07-01",
        "location": "Virtual",
        "distance_from_wayne": "Remote",
        "kind": "startup_grant_hackathon",
        "status": "open_for_submission",
        "score": 82,
        "why": "Not a classic weekend hackathon, but useful if you shape a Web3 startup prototype; offers up to $10k AWS credits per team.",
        "url": "https://dorahacks.io/hackathon/aws-activate/buidl",
        "source": "DoraHacks search result, checked 2026-06-18",
    },
    {
        "title": "Tokenization of Real World Assets using Blockchain | NYC",
        "date": "2026-07-01 13:00 + recurring",
        "deadline": "2026-07-01",
        "location": "New York, NY",
        "distance_from_wayne": "~25-35 miles",
        "kind": "workshop",
        "status": "listed",
        "score": 70,
        "why": "RWA is useful background for agentic finance/onchain validation ideas. Verify it is not a generic paid course before attending.",
        "url": "https://www.eventbrite.com/d/ny--new-york/blockchain/",
        "source": "Eventbrite NYC blockchain listing fetched 2026-06-18",
    },
    {
        "title": "Blockchain and Business Networking | Elevating Your Potential — Hoboken",
        "date": "2026-07-15 18:00",
        "deadline": "2026-07-15",
        "location": "The Shepherd & the Knucklehead, Hoboken, NJ",
        "distance_from_wayne": "~20 miles / easier than Manhattan",
        "kind": "networking",
        "status": "listed",
        "score": 68,
        "why": "Closest practical local blockchain networking option. Lower builder signal than hackathons, but useful for reps and contacts.",
        "url": "https://www.eventbrite.com/d/ny--new-york/blockchain/",
        "source": "Eventbrite NYC blockchain listing fetched 2026-06-18",
    },
    {
        "title": "Bitcoin/Altcoins & Cryptocurrency Enthusiast Night — Crypto Gathering",
        "date": "2026-08-24 18:30",
        "deadline": "2026-08-24",
        "location": "Dawson 39 Restaurant & Bar, New York, NY",
        "distance_from_wayne": "~25-35 miles",
        "kind": "meetup",
        "status": "listed",
        "score": 55,
        "why": "Casual crypto meetup. Use only if you want low-pressure conversations; not a high-signal builder event.",
        "url": "https://www.eventbrite.com/d/ny--new-york/blockchain/",
        "source": "Eventbrite NYC blockchain listing fetched 2026-06-18",
    },
    {
        "title": "THE NEW YORK BLOCKCHAIN FESTIVAL",
        "date": "2026-09-04 09:00",
        "deadline": "2026-09-04",
        "location": "Convene Brookfield Place, 225 Liberty, New York, NY",
        "distance_from_wayne": "~25-35 miles",
        "kind": "conference",
        "status": "listed",
        "score": 72,
        "why": "Broad NYC blockchain event. Worth tracking, but only attend if agenda has developer/founder/operator tracks.",
        "url": "https://www.eventbrite.com/d/ny--new-york/blockchain/",
        "source": "Eventbrite NYC blockchain listing fetched 2026-06-18",
    },
    {
        "title": "Web3 x AI Pitch Night w/ Founders/Investors",
        "date": "2026-09-18 18:00",
        "deadline": "2026-09-18",
        "location": "Civic Hall, 124 E 14th St, New York, NY",
        "distance_from_wayne": "~25-35 miles",
        "kind": "pitch_networking",
        "status": "watchlist_from_past_listing_or_recurring_community",
        "score": 76,
        "why": "High founder/investor relevance if another edition is open. Track NYC Blockchain Community / blockchainnyc.net for current RSVP.",
        "url": "https://luma.com/qhevtrls",
        "source": "Luma fetched 2026-06-18; verify current registration before relying on it",
    },
    {
        "title": "Blockchain Tech Summit (4th Annual)",
        "date": "2026-09-25 11:00",
        "deadline": "2026-09-25",
        "location": "New York, NY — location TBA",
        "distance_from_wayne": "~25-35 miles",
        "kind": "conference",
        "status": "listed",
        "score": 67,
        "why": "Potential technical/business blockchain summit. Needs agenda check before registering.",
        "url": "https://www.eventbrite.com/d/ny--new-york/blockchain/",
        "source": "Eventbrite NYC blockchain listing fetched 2026-06-18",
    },
    {
        "title": "4th Annual Ownership Economy Summit",
        "date": "2026-10-01 08:30",
        "deadline": "2026-10-01",
        "location": "140 Broadway, New York, NY",
        "distance_from_wayne": "~25-35 miles",
        "kind": "summit",
        "status": "listed",
        "score": 64,
        "why": "Adjacent to crypto networks/startups. Track if agenda includes protocols, founder/operators, or product strategy.",
        "url": "https://www.eventbrite.com/d/ny--new-york/blockchain/",
        "source": "Eventbrite NYC blockchain listing fetched 2026-06-18",
    },
]

SOURCE_LINKS = [
    {"name": "DoraHacks upcoming/ongoing hackathons", "url": "https://dorahacks.io/hackathon?status=upcoming", "note": "Best source for open online Web3 hackathons."},
    {"name": "ETHGlobal events", "url": "https://ethglobal.com/events", "note": "Watch for next NYC/regional ETH hackathon; ETHGlobal NYC 2026 is already past as of 2026-06-18."},
    {"name": "NYC Blockchain Network", "url": "https://blockchainnyc.net", "note": "Monthly NYC builder/founder events and pitch nights."},
    {"name": "Eventbrite NYC blockchain", "url": "https://www.eventbrite.com/d/ny--new-york/blockchain/", "note": "Broad listings; filter hard for builder signal and future dates."},
    {"name": "Luma NYC web3", "url": "https://luma.com", "note": "Good for smaller builder events; many pages are past/waitlist, so verify date/status."},
]


def event_is_future(event: dict[str, Any]) -> bool:
    raw = str(event.get("deadline") or "")[:10]
    try:
        return date.fromisoformat(raw) >= TODAY
    except ValueError:
        return True


def save_events(events: list[dict[str, Any]]) -> dict[str, Any]:
    DATA.mkdir(parents=True, exist_ok=True)
    future_events = [event for event in events if event_is_future(event)]
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "as_of": TODAY.isoformat(),
        "home_base": "Wayne, New Jersey",
        "radius": "NYC / North Jersey / remote Web3 hackathons",
        "items": sorted(future_events, key=lambda e: (-int(e.get("score", 0)), str(e.get("deadline", "9999-99-99")))),
        "source_links": SOURCE_LINKS,
        "rule": "Only include events with event date or submission deadline on/after 2026-06-18.",
    }
    EVENTS_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    write_report(payload)
    log_event("events_refreshed", "lifeos_events", count=len(payload["items"]))
    return payload


def write_report(payload: dict[str, Any]) -> None:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Web3 Events — NYC / NJ / Remote",
        "",
        f"Generated: {payload.get('generated_at')}",
        f"As of: {payload.get('as_of')}",
        "Home base: Wayne, NJ",
        "Rule: no event/deadline before 2026-06-18.",
        "",
        "## Best Bets",
        "",
    ]
    for event in payload.get("items", []):
        lines += [
            f"### {event.get('title')}",
            "",
            f"- Date: {event.get('date')}",
            f"- Deadline/action date: {event.get('deadline')}",
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
            if payload.get("as_of") != TODAY.isoformat():
                payload = save_events(SEED_EVENTS)
        except Exception:
            payload = save_events(SEED_EVENTS)
    items = payload.get("items", []) if isinstance(payload, dict) else []
    return {
        "configured": True,
        "items": items[:limit],
        "status": f"{len(items)} future web3 event(s)/hackathon(s) for Wayne/NYC/remote.",
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
