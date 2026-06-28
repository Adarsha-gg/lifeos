#!/usr/bin/env python3
"""Generate LifeOS learning lessons from local missions via Ollama.

Builds one generated article/game pair for a topic + difficulty, stores it in
the generated lesson store, and merges matching nodes into the graph store.

Examples:
  python tools/lifeos_generate.py check
  python tools/lifeos_generate.py topic --name zero-knowledge-proofs --difficulty teen
  python tools/lifeos_generate.py missions --difficulty teen
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

from lifeos_paths import VAULT_ROOT
from lifeos_skill_tree import load_graph_store, save_graph_store

OUT = VAULT_ROOT / "output" / "learn"
LESSON_STORE = OUT / "generated-lessons.json"
GENERATION_STATUS = OUT / "generation-status.json"
LEARN_ROOT = Path.home() / "learn"
OLLAMA = "http://localhost:11434"
MODEL = "gemma3:12b"
PROMPT_VERSION = 2

DIFFICULTIES: dict[str, dict[str, str]] = {
    "child": {
        "audience": "8-year-old",
        "instruction": "Explain with everyday analogies, no jargon, short sentences.",
        "difficulty": "intro",
    },
    "teen": {
        "audience": "curious 15-year-old",
        "instruction": "Plain language, define any term you introduce.",
        "difficulty": "intro",
    },
    "undergrad": {
        "audience": "university student new to the field",
        "instruction": "Standard terminology, assume basic STEM/general literacy.",
        "difficulty": "core",
    },
    "grad": {
        "audience": "someone with field fundamentals",
        "instruction": "Precise, use proper terminology, go into mechanisms.",
        "difficulty": "hard",
    },
    "expert": {
        "audience": "PhD / practitioner",
        "instruction": "Dense, rigorous, assume deep background, focus on nuance and edge cases.",
        "difficulty": "hard",
    },
}

DOMAIN_COLORS = {
    "history": "#c4892d",
    "thinking": "#1f9d78",
    "physics": "#6d6af2",
    "growth": "#3d8fd6",
    "culture": "#d86b8a",
    "systems": "#6b7a86",
    "custom": "#58636f",
}

TOPIC_DOMAIN_HINTS = {
    "nutrition": "growth",
    "diet": "growth",
    "health": "growth",
    "sleep": "growth",
    "startup": "systems",
    "startups": "systems",
    "business": "systems",
    "zero-knowledge": "systems",
    "cryptography": "systems",
    "proof": "systems",
    "physics": "physics",
    "quantum": "physics",
    "history": "history",
    "art": "culture",
}

LESSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "title", "subtitle", "emoji", "accent", "domain", "summary",
        "hero_article", "minutes", "lead", "sections", "ideas", "game",
        "did_you_know", "source_label", "source_url", "next",
    ],
    "properties": {
        "title": {"type": "string"},
        "subtitle": {"type": "string"},
        "emoji": {"type": "string"},
        "accent": {"type": "string"},
        "domain": {"type": "string", "enum": ["history", "physics", "systems", "growth", "culture", "thinking", "custom"]},
        "summary": {"type": "string"},
        "hero_article": {"type": "string"},
        "minutes": {"type": "integer", "minimum": 3, "maximum": 12},
        "lead": {"type": "string"},
        "sections": {
            "type": "array",
            "minItems": 3,
            "maxItems": 4,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["heading", "body_html", "image_article"],
                "properties": {
                    "heading": {"type": "string"},
                    "body_html": {"type": "string"},
                    "image_article": {"type": "string"},
                },
            },
        },
        "ideas": {
            "type": "array",
            "minItems": 4,
            "maxItems": 6,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["term", "definition"],
                "properties": {"term": {"type": "string"}, "definition": {"type": "string"}},
            },
        },
        "game": {
            "type": "object",
            "additionalProperties": False,
            "required": ["type", "prompt", "reveal"],
            "properties": {
                "type": {"type": "string", "enum": ["ponder", "order", "estimate"]},
                "prompt": {"type": "string"},
                "reveal": {"type": "string"},
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["id", "text"],
                        "properties": {"id": {"type": "string"}, "text": {"type": "string"}},
                    },
                },
                "explain": {"type": "string"},
                "answer": {"type": "number"},
                "unit": {"type": "string"},
            },
        },
        "did_you_know": {"type": "string"},
        "source_label": {"type": "string"},
        "source_url": {"type": "string"},
        "next": {"type": "string"},
    },
}


def slug(text: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return value or "topic"


def clean_mission(text: str) -> str:
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    return "\n".join(line.rstrip() for line in text.splitlines() if line.strip())[:5000]


def read_mission(name: str) -> tuple[str, str, Path | None]:
    path = LEARN_ROOT / name / "MISSION.md"
    if path.exists():
        title = name.replace("-", " ").strip()
        return title, clean_mission(path.read_text(encoding="utf-8")), path
    return name, "", None


def mission_hash(mission: str) -> str:
    raw = f"prompt:{PROMPT_VERSION}\n{mission}".encode("utf-8")
    return hashlib.sha1(raw).hexdigest()


def http_json(method: str, url: str, payload: dict[str, Any] | None = None, timeout: int = 30) -> dict[str, Any]:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def ollama_tags() -> dict[str, Any]:
    return http_json("GET", f"{OLLAMA}/api/tags", timeout=8)


def check_ollama() -> dict[str, Any]:
    try:
        tags = ollama_tags()
    except Exception as exc:
        return {"ok": False, "ollama": "down", "model": MODEL, "error": str(exc)}
    models = [m.get("name", "") for m in tags.get("models", [])]
    present = MODEL in models
    return {"ok": present, "ollama": "up", "model": MODEL, "present": present, "models": models}


def prompt(topic: str, mission: str, difficulty: str) -> str:
    spec = DIFFICULTIES[difficulty]
    context = mission or "No mission file was provided. Pick a useful first-principles entry point for this topic."
    return f"""
You are a curriculum author for LifeOS, a personal anti-doomscroll learning app.
Produce one tight, accurate, engaging micro-lesson and one quick interactive game.

Topic: {topic}
Mission context:
{context}

Audience: {spec['audience']}
Difficulty instruction: {spec['instruction']}

Requirements:
- Be factual and concrete. Avoid generic motivational prose.
- Do not invent protocol mechanics or fake historical details. If exact mechanics are too advanced, keep the example at the right abstraction level.
- Teach one useful concept deeply enough that the game can test it.
- The lesson should read like a short blog post.
- Use body_html strings with one or two <p>...</p> paragraphs each.
- hero_article and image_article must be Wikipedia article titles, not image URLs.
- Game type must be one of:
  - ponder: prompt + reveal
  - order: prompt + items in correct order + explain
  - estimate: prompt + numeric answer + unit + reveal
- If unsure, use ponder. Do not use a quiz.
- Do not write multiple-choice options like A/B/C/D. The game must require reasoning, ordering, estimating, or explaining.
- Pick source_label/source_url for a credible public reference or write "General reference" with a useful URL.
- Return only JSON matching the supplied schema.
""".strip()


def call_ollama(topic: str, mission: str, difficulty: str, strict: bool = False) -> dict[str, Any]:
    text = prompt(topic, mission, difficulty)
    if strict:
        text += "\n\nYour previous response failed validation. Return valid JSON only. No markdown. No comments."
    payload = {
        "model": MODEL,
        "prompt": text,
        "format": LESSON_SCHEMA,
        "stream": False,
        "options": {"temperature": 0.65},
    }
    data = http_json("POST", f"{OLLAMA}/api/generate", payload, timeout=180)
    raw = data.get("response", "")
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Ollama returned invalid JSON: {exc}") from exc


def ensure_p(body: str) -> str:
    body = body.strip()
    if "<p" in body.lower():
        return body
    return f"<p>{html.escape(body)}</p>"


def plain(text: Any) -> str:
    value = html.unescape(str(text if text is not None else ""))
    value = re.sub(r"<[^>]+>", " ", value)
    value = value.replace("*", "")
    return " ".join(value.split())


def css_color(value: Any, domain: str) -> str:
    text = str(value or "").strip()
    if re.fullmatch(r"#[0-9a-fA-F]{6}", text):
        return text
    return DOMAIN_COLORS.get(domain, "#4d7cff")


def wiki_title(value: Any) -> str:
    text = plain(value)
    if not text or text.lower() in {"body_html", "image_article", "none", "null"}:
        return ""
    if text.startswith("http://") or text.startswith("https://"):
        return ""
    return text[:120]


def display_title(value: Any, fallback: str) -> str:
    title = plain(value or fallback)
    if title.lower().strip("# ").startswith("mission"):
        title = fallback
    if len(title) > 48 and ":" in title:
        title = title.split(":", 1)[0].strip()
    if len(title) > 58:
        title = title[:55].rstrip() + "..."
    return title


def normalize_game(game: dict[str, Any]) -> dict[str, Any]:
    gtype = game.get("type") or "ponder"
    if gtype == "order":
        items = game.get("items") or []
        normalized = []
        for i, item in enumerate(items[:6], start=1):
            if isinstance(item, dict):
                normalized.append((str(item.get("id") or f"i{i}"), plain(item.get("text") or "")))
        if len(normalized) < 3:
            raise ValueError("order game requires at least 3 items")
        return {
            "type": "order",
            "prompt": plain(game.get("prompt") or "Put these in the right order."),
            "items": normalized,
            "explain": str(game.get("explain") or game.get("reveal") or ""),
        }
    if gtype == "estimate":
        return {
            "type": "estimate",
            "prompt": plain(game.get("prompt") or "Make a reasoned estimate."),
            "answer": game.get("answer"),
            "unit": str(game.get("unit") or ""),
            "reveal": str(game.get("reveal") or ""),
        }
    return {
        "type": "ponder",
        "prompt": plain(game.get("prompt") or "Think it through before revealing the answer."),
        "reveal": str(game.get("reveal") or ""),
    }


def normalize_lesson(raw: dict[str, Any], topic_slug: str, difficulty: str, cache_key: str, mission_hash_value: str) -> dict[str, Any]:
    lesson_id = f"gen-{topic_slug}-{difficulty}"
    domain = next((value for key, value in TOPIC_DOMAIN_HINTS.items() if key in topic_slug), str(raw.get("domain") or "custom"))
    if domain not in DOMAIN_COLORS:
        domain = "custom"
    sections = []
    for section in raw.get("sections", []):
        if not isinstance(section, dict):
            continue
        sections.append((
            str(section.get("heading") or "Section"),
            ensure_p(str(section.get("body_html") or "")),
            wiki_title(section.get("image_article")) or None,
        ))
    ideas = []
    for idea in raw.get("ideas", []):
        if isinstance(idea, dict):
            ideas.append((str(idea.get("term") or ""), str(idea.get("definition") or "")))
    lesson = {
        "id": lesson_id,
        "emoji": plain(raw.get("emoji") or "📚")[:4] or "📚",
        "accent": css_color(raw.get("accent"), domain),
        "title": display_title(raw.get("title"), topic_slug.replace("-", " ").title()),
        "subtitle": plain(raw.get("subtitle") or ""),
        "minutes": int(raw.get("minutes") or 6),
        "hero_article": wiki_title(raw.get("hero_article")),
        "lead": plain(raw.get("lead") or ""),
        "sections": sections,
        "ideas": ideas,
        "game": normalize_game(raw.get("game") or {}),
        "did_you_know": str(raw.get("did_you_know") or ""),
        "source": (str(raw.get("source_label") or "General reference"), str(raw.get("source_url") or "https://en.wikipedia.org/")),
        "next": plain(raw.get("next") or ""),
        "generated": True,
        "cache_key": cache_key,
        "mission_hash": mission_hash_value,
        "prompt_version": PROMPT_VERSION,
        "difficulty_level": difficulty,
        "difficulty": DIFFICULTIES[difficulty]["difficulty"],
        "domain": domain,
        "summary": plain(raw.get("summary") or ""),
    }
    validate_lesson(lesson)
    return lesson


def validate_lesson(lesson: dict[str, Any]) -> None:
    required = ["id", "emoji", "accent", "title", "subtitle", "minutes", "lead", "sections", "ideas", "game", "did_you_know", "source"]
    missing = [key for key in required if key not in lesson or lesson[key] in ("", [], None)]
    if missing:
        raise ValueError(f"generated lesson missing fields: {missing}")
    if len(lesson["sections"]) < 3:
        raise ValueError("generated lesson needs at least 3 sections")
    if len(lesson["ideas"]) < 4:
        raise ValueError("generated lesson needs at least 4 ideas")
    gtype = lesson["game"].get("type")
    if gtype not in {"ponder", "order", "estimate"}:
        raise ValueError(f"unsupported game type: {gtype}")
    if gtype == "estimate" and lesson["game"].get("answer") is None:
        raise ValueError("estimate game missing answer")
    prompt = str(lesson["game"].get("prompt", ""))
    if re.search(r"\bA\)|\bB\)|\bC\)|\bD\)|\bmultiple[- ]choice\b", prompt, flags=re.I):
        raise ValueError("game prompt looks like a multiple-choice quiz")


def load_lessons() -> list[dict[str, Any]]:
    try:
        data = json.loads(LESSON_STORE.read_text(encoding="utf-8"))
    except Exception:
        return []
    lessons = data.get("lessons", data) if isinstance(data, dict) else data
    return lessons if isinstance(lessons, list) else []


def save_lessons(lessons: list[dict[str, Any]]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    lessons = sorted(lessons, key=lambda item: str(item.get("id", "")))
    LESSON_STORE.write_text(json.dumps({"generated_at": datetime.now().isoformat(timespec="seconds"), "lessons": lessons}, indent=2), encoding="utf-8")


def cached_lesson(cache_key: str, mission_hash_value: str) -> dict[str, Any] | None:
    for lesson in load_lessons():
        if lesson.get("cache_key") == cache_key and lesson.get("mission_hash") == mission_hash_value:
            return lesson
    return None


def next_coords(graph: dict[str, Any]) -> tuple[int, int]:
    count = len(graph.get("nodes", []))
    col = count % 5
    row = (count // 5) % 4
    return 10 + col * 20, 12 + row * 20


def graph_items(lesson: dict[str, Any], topic: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    graph = load_graph_store()
    x, y = next_coords(graph)
    article_id = lesson["id"]
    game_id = f"{article_id}-game"
    article = {
        "id": article_id,
        "domain": lesson.get("domain") or "custom",
        "title": lesson["title"],
        "kind": "article",
        "xp": 90,
        "url": f"/output/learn/{article_id}.html",
        "summary": lesson.get("summary") or lesson["subtitle"],
        "sources": [{"source_id": f"mission-{slug(topic)}", "locator": "generated"}],
        "difficulty": lesson["difficulty"],
        "difficulty_level": lesson["difficulty_level"],
        "estimated_minutes": lesson["minutes"],
        "cache_key": lesson["cache_key"],
        "mission_hash": lesson.get("mission_hash", ""),
        "x": x,
        "y": y,
    }
    game = {
        "id": game_id,
        "domain": article["domain"],
        "title": f"{lesson['title']} Practice",
        "kind": "game",
        "xp": 120,
        "url": f"/output/learn/{article_id}.html#game",
        "summary": "Practice the generated lesson through an interactive challenge.",
        "difficulty": lesson["difficulty"],
        "difficulty_level": lesson["difficulty_level"],
        "cache_key": f"{lesson['cache_key']}--game",
        "mission_hash": lesson.get("mission_hash", ""),
        "x": min(94, x),
        "y": min(88, y + 18),
    }
    edge = {
        "from": article_id,
        "to": game_id,
        "relation": "practice",
        "reason": "The generated challenge practices the article's core concept.",
        "confidence": 1.0,
    }
    return [article, game], [edge]


def merge_generated(lesson: dict[str, Any], topic: str) -> None:
    lessons = [item for item in load_lessons() if item.get("id") != lesson["id"]]
    lessons.append(lesson)
    save_lessons(lessons)
    graph = load_graph_store()
    nodes, edges = graph_items(lesson, topic)
    graph.setdefault("nodes", []).extend(nodes)
    graph.setdefault("edges", []).extend(edges)
    domain = lesson.get("domain") or "custom"
    graph.setdefault("domains", []).append({"id": domain, "name": domain.title(), "color": DOMAIN_COLORS.get(domain, DOMAIN_COLORS["custom"])})
    save_graph_store(graph)


def generate_topic(name: str, difficulty: str, force: bool = False) -> dict[str, Any]:
    started = time.time()
    topic, mission, mission_path = read_mission(name)
    topic_slug = slug(name)
    cache_key = f"{topic_slug}--{difficulty}"
    mission_hash_value = mission_hash(mission)
    existing = cached_lesson(cache_key, mission_hash_value)
    if existing and not force:
        return {
            "ok": True,
            "status": "reused",
            "topic": name,
            "node_id": existing["id"],
            "url": f"/output/learn/{existing['id']}.html",
            "difficulty": difficulty,
            "mission_hash": mission_hash_value,
            "seconds": round(time.time() - started, 2),
        }
    last_error: str | None = None
    for attempt in range(2):
        try:
            raw = call_ollama(topic, mission, difficulty, strict=attempt > 0)
            lesson = normalize_lesson(raw, topic_slug, difficulty, cache_key, mission_hash_value)
            merge_generated(lesson, topic)
            return {
                "ok": True,
                "status": "generated",
                "topic": name,
                "mission": str(mission_path) if mission_path else "",
                "node_id": lesson["id"],
                "game_node_id": f"{lesson['id']}-game",
                "url": f"/output/learn/{lesson['id']}.html",
                "difficulty": difficulty,
                "mission_hash": mission_hash_value,
                "seconds": round(time.time() - started, 2),
            }
        except Exception as exc:
            last_error = str(exc)
    raise RuntimeError(last_error or "generation failed")


def mission_names() -> list[str]:
    if not LEARN_ROOT.exists():
        return []
    names = []
    for path in sorted(LEARN_ROOT.glob("*/MISSION.md")):
        names.append(path.parent.name)
    return names


def run_missions(difficulty: str, force: bool = False) -> dict[str, Any]:
    results = []
    for name in mission_names():
        try:
            results.append(generate_topic(name, difficulty, force))
        except Exception as exc:
            results.append({"ok": False, "status": "failed", "topic": name, "difficulty": difficulty, "error": str(exc)})
    ok_count = sum(1 for r in results if r.get("ok"))
    failed = [r for r in results if not r.get("ok")]
    summary = f"GENERATION: {ok_count} ok, {len(failed)} failed"
    if failed:
        summary += " (" + "; ".join(f"{r.get('topic')}: {r.get('error', 'unknown')}" for r in failed[:3]) + ")"
    payload = {
        "ok": all(r.get("ok") for r in results),
        "soft_ok": True,
        "summary": summary,
        "failed_count": len(failed),
        "results": results,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    GENERATION_STATUS.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate LifeOS lessons with local Ollama")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check", help="Verify Ollama is up and gemma3:12b is installed")
    topic = sub.add_parser("topic", help="Generate one topic")
    topic.add_argument("--name", required=True)
    topic.add_argument("--difficulty", choices=list(DIFFICULTIES), default="teen")
    topic.add_argument("--force", action="store_true")
    missions = sub.add_parser("missions", help="Generate all ~/learn/*/MISSION.md topics")
    missions.add_argument("--difficulty", choices=list(DIFFICULTIES), default="teen")
    missions.add_argument("--force", action="store_true")
    missions.add_argument("--strict", action="store_true", help="Exit non-zero if any topic fails")
    args = parser.parse_args()
    if args.cmd == "check":
        payload = check_ollama()
        print(json.dumps(payload, indent=2))
        return 0 if payload.get("ok") else 1
    if args.cmd == "topic":
        try:
            payload = generate_topic(args.name, args.difficulty, args.force)
            print(json.dumps(payload, indent=2))
            return 0
        except (urllib.error.URLError, TimeoutError, RuntimeError, ValueError) as exc:
            print(json.dumps({"ok": False, "status": "failed", "topic": args.name, "difficulty": args.difficulty, "error": str(exc)}, indent=2))
            return 1
    if args.cmd == "missions":
        payload = run_missions(args.difficulty, args.force)
        print(payload["summary"])
        print(json.dumps(payload, indent=2))
        return 1 if args.strict and not payload.get("ok") else 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
