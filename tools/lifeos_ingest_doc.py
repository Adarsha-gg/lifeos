#!/usr/bin/env python3
"""Ingest learning documents into LifeOS source/concept packets.

This does not paste long documents into the app. It stores source metadata,
section summaries, extracted concept candidates, typed edges, and provenance
pointers that the graph/recommendation layer can review and merge later.

Examples:
  python tools/lifeos_ingest_doc.py seed-mathacademy
  python tools/lifeos_ingest_doc.py ingest notes.md --source-id my-book --title "My Book"
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from lifeos_learning_engine import PRINCIPLES, SOURCE_NOTES
from lifeos_paths import VAULT_ROOT

OUT = VAULT_ROOT / "data" / "learn" / "ingested_sources"

STOPWORDS = {
    "about", "after", "again", "against", "because", "before", "between", "could",
    "every", "first", "from", "have", "into", "just", "learning", "more", "should",
    "system", "than", "that", "their", "there", "these", "thing", "this", "through",
    "under", "using", "what", "when", "where", "which", "while", "with", "without",
}


def slug(text: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return base[:80] or "source"


def sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", " ".join(text.split()))
    return [p.strip() for p in parts if len(p.strip()) > 24]


def split_sections(text: str) -> list[dict[str, str]]:
    sections: list[dict[str, str]] = []
    current_title = "Overview"
    current: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        heading = re.match(r"^(#{1,4})\s+(.+)$", line)
        if heading:
            if current:
                sections.append({"title": current_title, "body": "\n".join(current).strip()})
            current_title = heading.group(2).strip()
            current = []
        elif line:
            current.append(line)
    if current:
        sections.append({"title": current_title, "body": "\n".join(current).strip()})
    if not sections:
        chunks = [text[i:i + 1800] for i in range(0, len(text), 1800)]
        sections = [{"title": f"Section {i + 1}", "body": chunk.strip()} for i, chunk in enumerate(chunks) if chunk.strip()]
    return sections[:80]


def summary(text: str) -> str:
    first = sentences(text)
    if not first:
        return " ".join(text.split())[:220]
    return first[0][:260]


def concept_candidates(text: str, limit: int = 8) -> list[str]:
    phrases: dict[str, int] = {}
    for match in re.finditer(r"\b[A-Za-z][A-Za-z\-]*(?:\s+[A-Za-z][A-Za-z\-]*){0,3}\b", text):
        phrase = " ".join(match.group(0).split())
        words = phrase.lower().split()
        if len(words[0]) < 4 or words[0] in STOPWORDS:
            continue
        if len(words) == 1 and not phrase[:1].isupper():
            continue
        key = phrase.lower()
        phrases[key] = phrases.get(key, 0) + len(words)
    ranked = sorted(phrases.items(), key=lambda kv: (-kv[1], kv[0]))
    return [name.title() for name, _ in ranked[:limit]]


def ingest_text(source_id: str, title: str, text: str, url: str = "") -> dict[str, Any]:
    sections = split_sections(text)
    source_node = {
        "id": source_id,
        "title": title,
        "kind": "source",
        "url": url,
        "summary": summary(text),
    }
    nodes = [source_node]
    edges: list[dict[str, Any]] = []
    seen_concepts: set[str] = set()
    for index, section in enumerate(sections, start=1):
        sid = f"{source_id}-s{index:02d}-{slug(section['title'])[:40]}"
        nodes.append({
            "id": sid,
            "title": section["title"],
            "kind": "section",
            "summary": summary(section["body"]),
            "source": {"source_id": source_id, "locator": f"section:{index}"},
        })
        edges.append({"from": source_id, "to": sid, "relation": "contains", "reason": "Section belongs to source", "confidence": 1.0})
        if index > 1:
            edges.append({"from": nodes[-2]["id"], "to": sid, "relation": "sequence", "reason": "Adjacent section order", "confidence": 0.6})
        for term in concept_candidates(section["title"] + "\n" + section["body"]):
            cid = f"concept-{slug(term)}"
            if cid not in seen_concepts:
                seen_concepts.add(cid)
                nodes.append({
                    "id": cid,
                    "title": term,
                    "kind": "concept",
                    "summary": f"Concept candidate extracted from {title}.",
                    "source": {"source_id": source_id, "locator": f"section:{index}"},
                })
            edges.append({"from": sid, "to": cid, "relation": "explains", "reason": "Term appears as a section concept candidate", "confidence": 0.45})
    return {
        "schema_version": 1,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source": source_node,
        "nodes": nodes,
        "edges": edges,
        "merge_status": "candidate_review_required",
    }


def write_packet(packet: dict[str, Any]) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{packet['source']['id']}.json"
    path.write_text(json.dumps(packet, indent=2), encoding="utf-8")
    return path


def seed_mathacademy() -> dict[str, Any]:
    text = "# Math Academy Learning Model Notes\n\n"
    for source in SOURCE_NOTES:
        text += f"## {source['title']}\n{source['takeaway']}\nSource: {source['url']}\n\n"
    text += "## LifeOS Implementation Principles\n"
    for principle in PRINCIPLES:
        text += f"### {principle['name']}\n{principle['rule']} {principle['implemented_as']}\n\n"
    return ingest_text(
        source_id="mathacademy-learning-model",
        title="Math Academy Learning Model Notes",
        url="https://www.mathacademy.com/how-our-ai-works",
        text=text,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest local learning documents into LifeOS concept packets")
    sub = parser.add_subparsers(dest="cmd", required=True)
    ingest = sub.add_parser("ingest", help="Ingest a local .md/.txt document")
    ingest.add_argument("path", type=Path)
    ingest.add_argument("--source-id", required=True)
    ingest.add_argument("--title", required=True)
    ingest.add_argument("--url", default="")
    sub.add_parser("seed-mathacademy", help="Seed the Math Academy learning-model notes packet")
    args = parser.parse_args()
    if args.cmd == "seed-mathacademy":
        path = write_packet(seed_mathacademy())
        print(json.dumps({"ok": True, "path": str(path)}, indent=2))
        return 0
    if args.cmd == "ingest":
        text = args.path.read_text(encoding="utf-8")
        path = write_packet(ingest_text(args.source_id, args.title, text, args.url))
        print(json.dumps({"ok": True, "path": str(path)}, indent=2))
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
