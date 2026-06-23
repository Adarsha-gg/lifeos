#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any, Iterable

from lifeos_audit import log_event
from lifeos_paths import VAULT_ROOT
from lifeos_todos import open_items

ROOT = VAULT_ROOT
WIKI = ROOT / "wiki"
OUT = ROOT / "output"
REPORTS = OUT / "reports"
DIGEST_JSON = OUT / "lifeos-web-digest.json"
TODAY = datetime.now().date().isoformat()
USER_AGENT = "LifeOS morning web digest/1.0 (+local personal assistant)"
TIMEOUT_SECONDS = 9
MAX_PER_SOURCE = 12
MAX_ITEMS = 18

STOPWORDS = {
    "about", "after", "again", "also", "before", "being", "build", "could", "daily", "from",
    "have", "into", "life", "more", "need", "needs", "next", "only", "over", "read", "should",
    "start", "system", "that", "their", "there", "these", "thing", "this", "today", "with",
    "would", "your", "wiki", "source", "summary", "current", "priority", "priorities",
}

DEFAULT_SOURCES: list[dict[str, str]] = [
    {
        "id": "hn-front-page",
        "kind": "hn_algolia",
        "title": "Hacker News front page",
        "url": "https://hn.algolia.com/api/v1/search?tags=front_page",
        "bias": "builder/startup/coding signal",
    },
    {
        "id": "arxiv-ai",
        "kind": "atom",
        "title": "arXiv AI/LLM/ML recent papers",
        "url": "https://export.arxiv.org/api/query?search_query=cat:cs.AI+OR+cat:cs.CL+OR+cat:cs.LG&sortBy=submittedDate&sortOrder=descending&max_results=12",
        "bias": "AI agents and research ideas",
    },
    {
        "id": "ethereum-blog",
        "kind": "rss",
        "title": "Ethereum Foundation blog",
        "url": "https://blog.ethereum.org/feed.xml",
        "bias": "ethereum/protocol learning",
    },
    {
        "id": "yc-blog",
        "kind": "rss",
        "title": "Y Combinator blog",
        "url": "https://www.ycombinator.com/blog/rss",
        "bias": "startup/founder strategy",
    },
    {
        "id": "bitcoin-core",
        "kind": "rss",
        "title": "Bitcoin Core blog",
        "url": "https://bitcoincore.org/en/rss.xml",
        "bias": "bitcoin/protocol engineering",
    },
    {
        "id": "github-engineering",
        "kind": "rss",
        "title": "GitHub engineering",
        "url": "https://github.blog/engineering/feed/",
        "bias": "software engineering practice",
    },
]


@dataclass
class SourceResult:
    source_id: str
    title: str
    url: str
    ok: bool
    count: int = 0
    error: str = ""


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def strip_html(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value)
    return " ".join(html.unescape(value).split())


def words(text: str) -> list[str]:
    return [w.lower() for w in re.findall(r"[A-Za-z0-9][A-Za-z0-9+#.-]{2,}", text)]


def build_life_context() -> dict[str, Any]:
    pages = {
        "current_priorities": read(WIKI / "personal" / "current-priorities.md"),
        "command_center": read(WIKI / "personal" / "daily-command-center.md"),
        "life_os": read(WIKI / "personal" / "life-operating-system.md"),
        "attention": read(WIKI / "personal" / "attention-and-phone.md"),
        "health": read(WIKI / "personal" / "health-and-posture.md"),
    }
    todo_text = "\n".join(str(item.get("text") or "") for item in open_items(20))
    combined = "\n".join(pages.values()) + "\n" + todo_text

    counts: dict[str, int] = {}
    for word in words(combined):
        if word in STOPWORDS or len(word) < 4:
            continue
        counts[word] = counts.get(word, 0) + 1

    manual_boosts = {
        "blockchain": 8,
        "crypto": 7,
        "web3": 7,
        "ethereum": 6,
        "erc": 6,
        "erc-8004": 10,
        "startup": 8,
        "hackathon": 7,
        "agent": 6,
        "agents": 6,
        "ai": 5,
        "coding": 5,
        "founder": 5,
        "fitness": 4,
        "posture": 5,
        "sleep": 3,
        "reading": 4,
    }
    for key, boost in manual_boosts.items():
        counts[key] = counts.get(key, 0) + boost

    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:80]
    return {
        "generated_from": [str(WIKI / "personal" / name) for name in ["current-priorities.md", "daily-command-center.md", "life-operating-system.md"]],
        "keywords": dict(ranked),
        "open_todos": [item for item in open_items(12)],
    }


def request_text(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/rss+xml, application/atom+xml, application/json, text/xml, */*"})
    with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        return resp.read().decode(charset, errors="replace")


def parse_date(raw: str) -> str:
    raw = raw.strip()
    if not raw:
        return ""
    for parser in (
        lambda s: datetime.fromisoformat(s.replace("Z", "+00:00")),
        parsedate_to_datetime,
    ):
        try:
            dt = parser(raw)
            if dt.tzinfo:
                dt = dt.astimezone(timezone.utc)
            return dt.isoformat(timespec="seconds")
        except Exception:
            continue
    return raw


def text_of(node: ET.Element, *names: str) -> str:
    for child in node.iter():
        tag = child.tag.rsplit("}", 1)[-1].lower()
        if tag in names and child.text:
            return strip_html(child.text)
    return ""


def link_of(node: ET.Element) -> str:
    for child in node.iter():
        tag = child.tag.rsplit("}", 1)[-1].lower()
        if tag == "link":
            href = child.attrib.get("href")
            if href:
                return href.strip()
            if child.text:
                return child.text.strip()
    return ""


def parse_feed_xml(text: str, source: dict[str, str]) -> list[dict[str, Any]]:
    root = ET.fromstring(text)
    entries = [node for node in root.iter() if node.tag.rsplit("}", 1)[-1].lower() in {"item", "entry"}]
    out: list[dict[str, Any]] = []
    for entry in entries[:MAX_PER_SOURCE]:
        title = text_of(entry, "title")
        url = link_of(entry)
        summary = text_of(entry, "summary", "description", "content")
        published = text_of(entry, "published", "updated", "pubdate")
        if title:
            out.append({
                "id": stable_id(source["id"], url or title),
                "source_id": source["id"],
                "source": source["title"],
                "title": title,
                "url": url,
                "summary": summary[:420],
                "published_at": parse_date(published),
            })
    return out


def parse_hn_json(text: str, source: dict[str, str]) -> list[dict[str, Any]]:
    data = json.loads(text)
    hits = data.get("hits", []) if isinstance(data, dict) else []
    out: list[dict[str, Any]] = []
    for hit in hits[:MAX_PER_SOURCE]:
        if not isinstance(hit, dict):
            continue
        title = str(hit.get("title") or hit.get("story_title") or "").strip()
        url = str(hit.get("url") or hit.get("story_url") or "").strip()
        object_id = str(hit.get("objectID") or stable_id(source["id"], url or title))
        if title:
            out.append({
                "id": stable_id(source["id"], object_id),
                "source_id": source["id"],
                "source": source["title"],
                "title": title,
                "url": url or f"https://news.ycombinator.com/item?id={object_id}",
                "summary": f"HN points: {hit.get('points', 0)} · comments: {hit.get('num_comments', 0)}",
                "published_at": parse_date(str(hit.get("created_at") or "")),
                "points": int(hit.get("points") or 0),
                "comments": int(hit.get("num_comments") or 0),
            })
    return out


def stable_id(source: str, value: str) -> str:
    return hashlib.sha256(f"{source}:{value}".encode("utf-8")).hexdigest()[:16]


def matched_keywords(text: str, keywords: dict[str, int]) -> list[str]:
    lower = text.lower()
    matches = []
    for keyword, _weight in sorted(keywords.items(), key=lambda kv: -kv[1]):
        if keyword in lower:
            matches.append(keyword)
        if len(matches) >= 8:
            break
    return matches


def score_item(item: dict[str, Any], keywords: dict[str, int]) -> tuple[int, list[str]]:
    text = f"{item.get('title', '')} {item.get('summary', '')} {item.get('source', '')}".lower()
    matches = matched_keywords(text, keywords)
    score = sum(int(keywords.get(match, 0)) for match in matches)
    source_id = str(item.get("source_id") or "")
    if source_id.startswith("hn"):
        score += min(18, int(item.get("points") or 0) // 25)
    if any(term in text for term in ("agent", "agents", "llm", "ai")):
        score += 8
    if any(term in text for term in ("startup", "founder", "product", "growth")):
        score += 7
    if any(term in text for term in ("ethereum", "blockchain", "crypto", "web3", "erc")):
        score += 9
    if any(term in text for term in ("tiktok", "instagram", "celebrity", "drama")):
        score -= 10
    return score, matches


def fetch_source(source: dict[str, str]) -> tuple[list[dict[str, Any]], SourceResult]:
    try:
        text = request_text(source["url"])
        if source["kind"] == "hn_algolia":
            items = parse_hn_json(text, source)
        else:
            items = parse_feed_xml(text, source)
        return items, SourceResult(source["id"], source["title"], source["url"], True, len(items))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ET.ParseError, OSError) as exc:
        return [], SourceResult(source["id"], source["title"], source["url"], False, 0, str(exc)[:240])


def dedupe(items: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for item in items:
        key = (str(item.get("url") or item.get("title") or item.get("id"))).strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def build_digest() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    context = build_life_context()
    keywords: dict[str, int] = context["keywords"]
    all_items: list[dict[str, Any]] = []
    results: list[SourceResult] = []

    for source in DEFAULT_SOURCES:
        items, result = fetch_source(source)
        results.append(result)
        all_items.extend(items)
        time.sleep(0.2)

    scored = []
    for item in dedupe(all_items):
        score, matches = score_item(item, keywords)
        item = {**item, "score": score, "matched_keywords": matches, "why": why_text(matches, item)}
        scored.append(item)

    scored.sort(key=lambda item: (-int(item.get("score") or 0), str(item.get("published_at") or "")), reverse=False)
    items = scored[:MAX_ITEMS]
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "date": TODAY,
        "configured": True,
        "status": f"{len(items)} ranked web item(s) from {sum(1 for r in results if r.ok)}/{len(results)} source(s).",
        "life_context": context,
        "sources": [r.__dict__ for r in results],
        "items": items,
        "report": str(report_path().relative_to(ROOT)),
        "safety": "Read-only web fetch. No posting, sending, deleting, purchasing, or account actions.",
    }
    DIGEST_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    write_report(payload)
    log_event("web_digest_refreshed", "lifeos_web_digest", items=len(items), sources_ok=sum(1 for r in results if r.ok))
    return payload


def why_text(matches: list[str], item: dict[str, Any]) -> str:
    if matches:
        return "Matches life priorities: " + ", ".join(matches[:5]) + "."
    source = item.get("source") or "source"
    return f"Included as general {source} signal; skim only if headline matters."


def report_path() -> Path:
    return REPORTS / f"lifeos-web-digest-{TODAY}.md"


def write_report(payload: dict[str, Any]) -> None:
    lines = [
        f"# LifeOS Web Digest — {payload.get('date')}",
        "",
        f"Generated: {payload.get('generated_at')}",
        f"Status: {payload.get('status')}",
        "",
        "## Read First",
        "",
    ]
    for idx, item in enumerate(payload.get("items", [])[:8], start=1):
        lines += item_lines(idx, item)
    lines += ["", "## More", ""]
    for idx, item in enumerate(payload.get("items", [])[8:], start=9):
        lines += item_lines(idx, item)
    lines += ["", "## Source Health", ""]
    for source in payload.get("sources", []):
        status = "ok" if source.get("ok") else f"error: {source.get('error')}"
        lines.append(f"- {source.get('title')}: {status} ({source.get('count', 0)} item(s)) — {source.get('url')}")
    lines += ["", "## Safety", "", str(payload.get("safety") or "Read-only web fetch.")]
    report_path().write_text("\n".join(lines) + "\n", encoding="utf-8")


def item_lines(idx: int, item: dict[str, Any]) -> list[str]:
    title = item.get("title") or "Untitled"
    url = item.get("url") or ""
    title_md = f"[{title}]({url})" if url else str(title)
    return [
        f"### {idx}. {title_md}",
        "",
        f"- Source: {item.get('source')}",
        f"- Score: {item.get('score')}",
        f"- Why: {item.get('why')}",
        f"- Published: {item.get('published_at') or 'unknown'}",
        f"- Summary: {item.get('summary') or '_No summary._'}",
        "",
    ]


def load_cached() -> dict[str, Any] | None:
    try:
        data = json.loads(DIGEST_JSON.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def is_fresh(data: dict[str, Any] | None) -> bool:
    return bool(data and data.get("date") == TODAY and data.get("items"))


def web_digest_summary(limit: int = 6, *, refresh_if_stale: bool = True) -> dict[str, Any]:
    data = load_cached()
    if refresh_if_stale and not is_fresh(data):
        try:
            data = build_digest()
        except Exception as exc:
            data = data or {}
            data = {**data, "configured": True, "items": data.get("items", []), "error": str(exc)[:240]}
    items = (data or {}).get("items", []) if isinstance(data, dict) else []
    return {
        "configured": True,
        "items": items[:limit],
        "status": (data or {}).get("status") or f"{len(items)} cached web item(s).",
        "error": (data or {}).get("error", ""),
        "report": (data or {}).get("report") or str(report_path().relative_to(ROOT)),
        "sources": (data or {}).get("sources", []),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a read-only web digest scored against LifeOS priorities")
    parser.add_argument("cmd", choices=["refresh", "summary"], nargs="?", default="refresh")
    args = parser.parse_args()
    if args.cmd == "refresh":
        print(json.dumps(build_digest(), indent=2, sort_keys=True))
    else:
        print(json.dumps(web_digest_summary(refresh_if_stale=False), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
