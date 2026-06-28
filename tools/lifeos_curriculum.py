#!/usr/bin/env python3
"""LifeOS mastery curriculum infrastructure.

Normalizes curriculum tracks into LifeOS lesson dicts and knowledge-graph data.
Inspired by Math Academy / Physics Academy *principles* (prerequisite tree,
spaced review hooks, deep sections, thinking questions) — not proprietary content.

Optional bulk content lives in ``lifeos_curriculum_content.py`` as ``CURRICULUM_TRACKS``.
This module must not crash if that file is absent.

Build consumers: ``lifeos_lessons.py``, ``lifeos_skill_tree.py``, ``lifeos_learning_engine.py``
"""
from __future__ import annotations

import argparse
import html
import importlib.util
import json
from pathlib import Path
from typing import Any

try:
    from lifeos_curriculum_content import CURRICULUM_TRACKS as _EXTERNAL_TRACKS
except Exception:
    _EXTERNAL_TRACKS: list[dict[str, Any]] = []

DOMAIN_COLORS: dict[str, str] = {
    "math": "#4d7cff",
    "physics": "#6d6af2",
    "history": "#c4892d",
    "startup": "#1f9d78",
    "thinking": "#d79d3f",
    "invention": "#20c7ff",
    "statecraft": "#d94a2b",
}

# --------------------------------------------------------------------------- #
# Fallback seed tracks — prove the pipeline; content worker replaces/extends.
# --------------------------------------------------------------------------- #
SEED_TRACKS: list[dict[str, Any]] = [
    {
        "id": "math-foundations",
        "name": "Math Foundations",
        "domain": "math",
        "author": "LifeOS",
        "collection": "Mastery Curriculum (seed)",
        "units": [
            {
                "id": "curriculum-math-linear-equations",
                "title": "Linear Equations as Balance",
                "subtitle": "Treat an equation like a scale — what you do to one side, you must do to the other.",
                "emoji": "⚖️",
                "accent": "#4d7cff",
                "minutes": 14,
                "hero_article": "Linear equation",
                "prerequisites": [],
                "sections": [
                    {
                        "heading": "Page 1: An equation is a claim of balance",
                        "body": (
                            "<p>A linear equation in one variable, like <b>3x + 5 = 20</b>, is not a "
                            "random symbol puzzle. It is a sentence: <i>some unknown number x, scaled by "
                            "3 and shifted up by 5, equals 20</i>. The equals sign is the fulcrum of a "
                            "balance scale.</p><p>That metaphor matters because every legal move in "
                            "algebra is a move that keeps the scale level. Add 7 to the left? Add 7 to "
                            "the right. Divide the left by 2? Divide the right by 2. Illegal moves — "
                            "like dividing by zero — break the metaphor because they destroy the claim "
                            "being made.</p>"
                        ),
                        "image_article": "Balance scale",
                    },
                    {
                        "heading": "Page 2: Isolate the unknown in reverse order",
                        "body": (
                            "<p>Look at <b>3x + 5 = 20</b>. The operations applied to x are: multiply by "
                            "3, then add 5. To undo them, walk backwards: subtract 5, then divide by 3. "
                            "That gives x = 5. Each step is one balanced transformation.</p><p>Students "
                            "often rush to 'move terms across the equals sign' without knowing why the sign "
                            "flips. The scale picture explains it: moving +5 to the other side is really "
                            "subtracting 5 from both sides.</p>"
                        ),
                        "image_article": "Algebra",
                    },
                    {
                        "heading": "Page 3: Check by substitution",
                        "body": (
                            "<p>A solution is worthless if it does not satisfy the original claim. Plug "
                            "x = 5 back in: 3(5) + 5 = 20. Left side equals right side, so the balance "
                            "holds.</p><p>Checking catches arithmetic slips and conceptual errors — like "
                            "dividing only one term instead of the whole side. Make checking automatic; "
                            "it is cheap insurance.</p>"
                        ),
                        "image_article": None,
                    },
                    {
                        "heading": "Page 4: Word problems are translation",
                        "body": (
                            "<p>\"Twice a number plus 11 equals 35\" translates to <b>2x + 11 = 35</b>. "
                            "The hard part is rarely the algebra; it is naming the unknown and mapping "
                            "English verbs to operations. <i>Twice</i> → multiply, <i>plus</i> → add, "
                            "<i>equals</i> → =.</p><p>Draw a quick sketch or table when the sentence "
                            "feels foggy. Translation errors dwarf manipulation errors in real homework.</p>"
                        ),
                        "image_article": None,
                    },
                    {
                        "heading": "Page 5: Parameters and families of lines",
                        "body": (
                            "<p>Equations like <b>y = mx + b</b> describe entire families of lines. m "
                            "controls steepness; b controls where the line crosses the y-axis. Solving "
                            "for x in ax + b = c is the one-variable special case; graphing y = mx + b "
                            "is the two-variable view of the same idea.</p><p>Mastery here means you can "
                            "move between table, equation, graph, and story without losing the balance "
                            "metaphor.</p>"
                        ),
                        "image_article": "Slope",
                    },
                ],
                "ideas": [
                    ("Balance metaphor", "Equals means both sides stay the same value under legal moves."),
                    ("Inverse operations", "Undo addition with subtraction, multiplication with division — in reverse order."),
                    ("Solution set", "The value(s) of the unknown that make the original claim true."),
                    ("Parameter", "A letter that stands for a fixed but unspecified constant, like m or b."),
                ],
                "thinking_questions": [
                    "Why does dividing both sides by zero break the equation rather than 'solving' it?",
                    "A word problem gives 4x − 7 = 4x + 1. What does 'no solution' mean on a balance scale?",
                ],
                "practice_prompt": (
                    "Write three linear equations: one with a unique solution, one with infinitely many, "
                    "one with none. Solve each and explain using the balance metaphor."
                ),
                "source": {
                    "label": "Khan Academy — Linear equations",
                    "url": "https://www.khanacademy.org/math/algebra-home/alg-basic-eq-ineq",
                },
                "did_you_know": (
                    "Ancient Babylonian clay tablets (~1800 BCE) contain linear problems solved by the "
                    "same balance method — without modern notation."
                ),
                "next": "Next unit: slope as rate of change connects tables, graphs, and equations.",
            },
            {
                "id": "curriculum-math-slope-rate",
                "title": "Slope as Rate of Change",
                "subtitle": "Rise over run is the grammar of how one quantity responds to another.",
                "emoji": "📈",
                "accent": "#315f9d",
                "minutes": 15,
                "hero_article": "Slope",
                "prerequisites": ["curriculum-math-linear-equations"],
                "sections": [
                    {
                        "heading": "Page 1: Slope measures steepness",
                        "body": (
                            "<p>On a line, <b>slope</b> is the ratio of vertical change to horizontal "
                            "change between any two points: m = (y₂ − y₁) / (x₂ − x₁). Steeper uphill "
                            "lines have larger positive slopes; downhill lines have negative slopes; "
                            "flat lines have slope zero.</p><p>Slope is the same everywhere on a straight "
                            "line — that constancy is what makes lines special among curves.</p>"
                        ),
                        "image_article": "Linear function",
                    },
                    {
                        "heading": "Page 2: Slope is a rate",
                        "body": (
                            "<p>If x is time in hours and y is distance in miles, slope is speed in "
                            "mph. If x is items bought and y is total cost, slope is price per item. "
                            "The units of slope are always <i>units of y per unit of x</i>.</p><p>This "
                            "is why slope is more than a geometry trick — it is the language of "
                            "covariation in science, economics, and engineering.</p>"
                        ),
                        "image_article": None,
                    },
                    {
                        "heading": "Page 3: From graph to equation",
                        "body": (
                            "<p>Given two points (1, 2) and (4, 8): slope m = (8−2)/(4−1) = 2. Using "
                            "point-slope form y − 2 = 2(x − 1) expands to y = 2x. The y-intercept b = 0 "
                            "here; in general y = mx + b packages slope and intercept together.</p>"
                        ),
                        "image_article": None,
                    },
                    {
                        "heading": "Page 4: Parallel and perpendicular lines",
                        "body": (
                            "<p>Parallel lines share the same slope. Perpendicular non-vertical lines "
                            "have slopes whose product is −1 (e.g. 2 and −½). These facts fall out of "
                            "geometry but are quick checks when reading graphs.</p>"
                        ),
                        "image_article": None,
                    },
                    {
                        "heading": "Page 5: Piecewise and approximate rates",
                        "body": (
                            "<p>Real data is rarely perfectly linear. Still, a local slope — a secant "
                            "line over a small interval — approximates instantaneous rate. Calculus later "
                            "formalizes that limit; for now, recognize when a straight-line model is "
                            "good enough and when it lies.</p>"
                        ),
                        "image_article": "Derivative",
                    },
                ],
                "ideas": [
                    ("Rise over run", "Vertical change divided by horizontal change between two points."),
                    ("Rate of change", "How much y changes per unit change in x — slope with units attached."),
                    ("y-intercept", "Where the line crosses the y-axis; value of y when x = 0."),
                    ("Linear model", "A straight-line approximation useful over a limited domain."),
                ],
                "thinking_questions": [
                    "A line passes through (0, 5) and (5, 5). What is the slope, and what real-world story fits?",
                    "Can average speed ever differ from the slope of a distance-time graph? When?",
                ],
                "implementation_prompt": (
                    "Plot three points from a real habit (sleep hours vs mood 1–10). Fit a line by eye, "
                    "estimate slope with units, and state where the model breaks down."
                ),
                "source": {
                    "label": "OpenStax — Algebra and Trigonometry (slope section)",
                    "url": "https://openstax.org/details/books/algebra-and-trigonometry",
                },
                "did_you_know": (
                    "René Descartes' pairing of algebra and geometry made slope a bridge between symbols "
                    "and pictures — the start of analytic geometry."
                ),
                "next": "Next: systems of two lines — intersection as simultaneous truth.",
            },
        ],
    },
    {
        "id": "physics-mechanics",
        "name": "Mechanics Core",
        "domain": "physics",
        "author": "LifeOS",
        "collection": "Mastery Curriculum (seed)",
        "units": [
            {
                "id": "curriculum-physics-newton-laws",
                "title": "Newton's Laws — Force and Motion",
                "subtitle": "Three sentences that reorganized the physical world from Aristotle to Apollo.",
                "emoji": "🚀",
                "accent": "#6d6af2",
                "minutes": 16,
                "hero_article": "Newton's laws of motion",
                "prerequisites": [],
                "sections": [
                    {
                        "heading": "Page 1: Inertia — motion continues unless acted on",
                        "body": (
                            "<p><b>First law:</b> An object at rest stays at rest; an object in motion "
                            "stays in motion at constant velocity, unless a net external force acts. "
                            "This overturns the Aristotelian intuition that motion requires continuous "
                            "pushing. Friction hides inertia on Earth — remove it and a puck glides "
                            "indefinitely.</p>"
                        ),
                        "image_article": "Inertia",
                    },
                    {
                        "heading": "Page 2: F = ma links force, mass, acceleration",
                        "body": (
                            "<p><b>Second law:</b> The net force on an object equals mass times "
                            "acceleration: <b>F = ma</b>. Doubling force doubles acceleration; doubling "
                            "mass halves acceleration for the same push. Force is a vector — direction "
                            "matters.</p><p>Weight near Earth's surface is mg, not the same thing as mass. "
                            "Mass is inertia; weight is a force.</p>"
                        ),
                        "image_article": "Force",
                    },
                    {
                        "heading": "Page 3: Action–reaction pairs",
                        "body": (
                            "<p><b>Third law:</b> If object A exerts a force on B, then B exerts an equal "
                            "and opposite force on A. These forces act on <i>different</i> bodies — they "
                            "do not cancel when analyzing one object. Rockets accelerate because they push "
                            "exhaust backward; the exhaust pushes the rocket forward.</p>"
                        ),
                        "image_article": "Rocket",
                    },
                    {
                        "heading": "Page 4: Free-body diagrams",
                        "body": (
                            "<p>To apply F = ma, isolate one object and draw all external forces: gravity, "
                            "normal force, tension, friction. Sum forces along each axis; set net force "
                            "equal to mass times acceleration. This recipe solves inclines, elevators, "
                            "and Atwood machines.</p>"
                        ),
                        "image_article": "Free body diagram",
                    },
                    {
                        "heading": "Page 5: From tabletop to orbit",
                        "body": (
                            "<p>Newton showed the same laws bind a falling apple and the Moon. Gravity "
                            "provides the centripetal force for circular orbit. The leap from classroom "
                            "blocks to celestial mechanics is quantitative, not magical — just larger "
                            "forces, longer times, and careful vectors.</p>"
                        ),
                        "image_article": "Orbit",
                    },
                ],
                "ideas": [
                    ("Inertia", "Resistance to change in velocity — proportional to mass."),
                    ("Net force", "Vector sum of all external forces on one object."),
                    ("Action–reaction", "Force pairs on different bodies; equal magnitude, opposite direction."),
                    ("Free-body diagram", "Sketch isolating one object and its external forces."),
                ],
                "thinking_questions": [
                    "You push on a wall. Why don't you accelerate if the wall pushes back equally?",
                    "An astronaut floats inside a coasting spacecraft. Are forces on them zero?",
                ],
                "practice_prompt": (
                    "Draw free-body diagrams for: (a) a book on a table, (b) a skydiver at terminal velocity, "
                    "(c) a car turning at constant speed. Identify net force direction in each."
                ),
                "source": {
                    "label": "NASA — Newton's Laws of Motion",
                    "url": "https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/newtons-laws-of-motion/",
                },
                "did_you_know": (
                    "Newton published the Principia in 1687, but the story of the falling apple was recorded "
                    "decades later by William Stukeley — part history, part myth."
                ),
                "next": "Next: energy methods often beat force diagrams for complex paths.",
            },
            {
                "id": "curriculum-physics-energy-work",
                "title": "Work, Energy, and Conservation",
                "subtitle": "When forces move things, account for energy instead of tracking every vector.",
                "emoji": "⚡",
                "accent": "#8b5cf6",
                "minutes": 15,
                "hero_article": "Conservation of energy",
                "prerequisites": ["curriculum-physics-newton-laws"],
                "sections": [
                    {
                        "heading": "Page 1: Work transfers energy",
                        "body": (
                            "<p><b>Work</b> (in the physics sense) is W = F·d cos θ — force times "
                            "displacement in the direction of the force. Lifting a book at constant speed "
                            "does positive work against gravity; friction that stops a sled does negative "
                            "work, removing kinetic energy.</p>"
                        ),
                        "image_article": "Work (physics)",
                    },
                    {
                        "heading": "Page 2: Kinetic and potential energy",
                        "body": (
                            "<p><b>Kinetic energy</b> KE = ½mv² grows with speed squared — doubling speed "
                            "quadruples energy. <b>Gravitational potential</b> near Earth: PE = mgh. Energy "
                            "can change form but the bookkeeping helps predict outcomes without solving "
                            "every force component.</p>"
                        ),
                        "image_article": None,
                    },
                    {
                        "heading": "Page 3: Conservation when only conservative forces work",
                        "body": (
                            "<p>If non-conservative forces (like kinetic friction) do negligible work, "
                            "total mechanical energy E = KE + PE stays constant. A roller coaster's "
                            "speed is highest where height is lowest — energy sloshes between forms.</p>"
                        ),
                        "image_article": "Roller coaster",
                    },
                    {
                        "heading": "Page 4: Power is the rate of doing work",
                        "body": (
                            "<p><b>Power</b> P = W/t = F·v. A motor that lifts the same load faster "
                            "delivers more power. Human athletes, engines, and grid electricity are "
                            "compared in watts — joules per second.</p>"
                        ),
                        "image_article": None,
                    },
                    {
                        "heading": "Page 5: Energy bar charts as sanity checks",
                        "body": (
                            "<p>Before crunching numbers, sketch initial and final energy bars. Does the "
                            "story make sense? Did you forget friction heating? Energy methods won't "
                            "replace vectors for every problem, but they collapse whole classes of "
                            "motion into one scalar equation.</p>"
                        ),
                        "image_article": None,
                    },
                ],
                "ideas": [
                    ("Work", "Energy transferred by force through displacement."),
                    ("Conservative force", "Work independent of path; enables potential energy storage."),
                    ("Mechanical energy", "Sum of kinetic and potential energy in a system."),
                    ("Power", "Rate of energy transfer — watts are joules per second."),
                ],
                "thinking_questions": [
                    "You hold a heavy bag stationary at shoulder height. Are your muscles doing physics work?",
                    "Two balls start from rest and roll down identical-height ramps — one steep, one gentle. Same speed at bottom?",
                ],
                "practice_prompt": (
                    "A 2 kg block slides down a 3 m high frictionless ramp. Use energy conservation to "
                    "find speed at the bottom, then check with kinematics if you know the angle."
                ),
                "source": {
                    "label": "HyperPhysics — Conservation of Energy",
                    "url": "http://hyperphysics.phy-astr.gsu.edu/hbase/conser.html",
                },
                "did_you_know": (
                    "Energy conservation as a universal principle took shape in the 19th century as heat was "
                    "recognized as a form of mechanical energy — not a separate fluid called caloric."
                ),
                "next": "Next: momentum conservation handles collisions when forces are brief and unknown.",
            },
        ],
    },
    {
        "id": "startup-paul-graham",
        "name": "Startup Thinking (Paul Graham)",
        "domain": "startup",
        "author": "LifeOS digest",
        "collection": "Essays placeholder — content worker fills corpus",
        "units": [
            {
                "id": "curriculum-startup-do-things-that-dont-scale",
                "title": "Do Things That Don't Scale",
                "subtitle": "Why great products often start with unscalable manual work — a Paul Graham pattern.",
                "emoji": "🛠️",
                "accent": "#1f9d78",
                "minutes": 12,
                "hero_article": "Startup company",
                "prerequisites": [],
                "sections": [
                    {
                        "heading": "Page 1: The scalability trap",
                        "body": (
                            "<p>Founders are told to build systems that scale from day one. Paul Graham "
                            "argues the opposite for early startups: do things that <b>don't scale</b> — "
                            "recruit users manually, write custom onboarding emails, fix bugs in person. "
                            "The goal is learning and love, not efficiency.</p>"
                        ),
                        "image_article": "Startup",
                    },
                    {
                        "heading": "Page 2: Collison installation",
                        "body": (
                            "<p>Stripe's founders literally installed their product on laptops for early "
                            "customers — the 'Collison installation'. That is absurd at billion-user scale "
                            "and perfect at zero users. Manual work reveals friction automated funnels hide.</p>"
                        ),
                        "image_article": None,
                    },
                    {
                        "heading": "Page 3: Narrow wedge, intense delight",
                        "body": (
                            "<p>Pick a small group and overwhelm them with attention. WordPress began "
                            "serving bloggers; Facebook began at one campus. Density beats breadth until "
                            "product–market fit whispers become shouts.</p>"
                        ),
                        "image_article": None,
                    },
                    {
                        "heading": "Page 4: When to stop hand-cranking",
                        "body": (
                            "<p>Manual effort is a phase, not a religion. Signals to automate: the same "
                            "task repeats without new insight, quality stays high as volume doubles, and "
                            "bottleneck shifts from learning to throughput. Premature automation freezes "
                            "the wrong process.</p>"
                        ),
                        "image_article": None,
                    },
                    {
                        "heading": "Page 5: LifeOS application",
                        "body": (
                            "<p>This curriculum unit is a <i>placeholder digest</i> — original summary, "
                            "not the essay text. The content worker will attach source links, locators, "
                            "and richer excerpts per the ingestion contract. Your job now: name one "
                            "unscalable thing you could do this week to learn faster.</p>"
                        ),
                        "image_article": None,
                    },
                ],
                "ideas": [
                    ("Unscalable work", "Manual, high-touch efforts that teach what automation would hide."),
                    ("Product–market fit", "When a small market pulls the product out of your hands."),
                    ("Wedge", "A narrow entry point with intense value before expanding."),
                    ("Premature scaling", "Automating or hiring before the loop is understood."),
                ],
                "thinking_questions": [
                    "What is one manual thing you could do for your next five users that would never work at 50,000?",
                    "How do you know when delight is real versus polite feedback?",
                ],
                "implementation_prompt": (
                    "Pick a side project. List three unscalable actions you could take in 48 hours to "
                    "learn something a survey could not teach."
                ),
                "source": {
                    "label": "Paul Graham — Do Things That Don't Scale (read the original essay)",
                    "url": "http://www.paulgraham.com/ds.html",
                },
                "did_you_know": (
                    "This LifeOS unit summarizes themes from Graham's essay; it does not reproduce the "
                    "essay text. Always read primary sources for nuance."
                ),
                "next": "Content worker: add more PG essay units with prerequisites and cross-links.",
            },
        ],
    },
]


def all_tracks() -> list[dict[str, Any]]:
    """Merge external content tracks with built-in seed tracks (external wins on id clash)."""
    by_id: dict[str, dict[str, Any]] = {t["id"]: t for t in SEED_TRACKS}
    for track in _EXTERNAL_TRACKS:
        if isinstance(track, dict) and track.get("id"):
            by_id[str(track["id"])] = track
    return list(by_id.values())


def load_tracks_from_file(content_path: str) -> list[dict[str, Any]]:
    """Load ``CURRICULUM_TRACKS`` from an external Python module without altering ``sys.path``."""
    path = Path(content_path).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Content module not found: {path}")

    module_name = f"_lifeos_curriculum_external_{path.stem}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load content module from {path}")

    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except SyntaxError as exc:
        raise SyntaxError(f"Syntax error in content module {path}: {exc.msg} (line {exc.lineno})") from exc
    except Exception as exc:
        raise ImportError(f"Failed to execute content module {path}: {exc}") from exc

    if not hasattr(module, "CURRICULUM_TRACKS"):
        raise AttributeError(f"Content module {path} missing CURRICULUM_TRACKS")

    tracks = getattr(module, "CURRICULUM_TRACKS")
    if not isinstance(tracks, list):
        raise TypeError(
            f"Content module {path}: CURRICULUM_TRACKS must be a list, got {type(tracks).__name__}"
        )
    return tracks


def resolve_cli_tracks(content_path: str | None = None) -> tuple[list[dict[str, Any]], str]:
    """Resolve tracks and ``content_source`` label for CLI report/list/validate."""
    if content_path:
        return load_tracks_from_file(content_path), str(Path(content_path).expanduser().resolve())
    return all_tracks(), "local" if _EXTERNAL_TRACKS else "seed"


def _normalize_section(section: dict[str, Any] | tuple) -> tuple[str, str, str | None]:
    if isinstance(section, tuple):
        heading, body, image = section
        return str(heading), str(body), image
    return (
        str(section.get("heading", section.get("title", "Section"))),
        str(section.get("body", section.get("html", ""))),
        section.get("image_article"),
    )


def _source_tuple(unit: dict[str, Any]) -> tuple[str, str]:
    src = unit.get("source")
    if isinstance(src, dict):
        return str(src.get("label", "Source")), str(src.get("url", ""))
    if isinstance(src, (list, tuple)) and len(src) >= 2:
        return str(src[0]), str(src[1])
    return "LifeOS Curriculum", ""


def _game_from_unit(unit: dict[str, Any]) -> dict[str, Any]:
    if isinstance(unit.get("game"), dict):
        return unit["game"]
    questions = unit.get("thinking_questions") or []
    practice = unit.get("practice_prompt") or unit.get("application_prompt") or unit.get("implementation_prompt") or ""
    prompt = questions[0] if questions else "What is the core claim of this unit, in one sentence?"
    reveal_parts = []
    if len(questions) > 1:
        reveal_parts.append(f"<b>Also consider:</b> {questions[1]}")
    if practice:
        reveal_parts.append(f"<b>Practice:</b> {practice}")
    reveal_parts.append(
        "There is no single correct essay answer — the struggle to articulate the idea is the point."
    )
    return {
        "type": "ponder",
        "prompt": prompt,
        "reveal": " ".join(reveal_parts),
    }


def unit_to_lesson(unit: dict[str, Any], track: dict[str, Any]) -> dict[str, Any]:
    """Convert a curriculum unit into the ``lifeos_lessons`` lesson dict shape."""
    domain = str(track.get("domain", "thinking"))
    track_id = str(track["id"])
    sections = [_normalize_section(s) for s in unit.get("sections", [])]
    lesson: dict[str, Any] = {
        "id": str(unit["id"]),
        "emoji": unit.get("emoji", "📚"),
        "accent": unit.get("accent", DOMAIN_COLORS.get(domain, "#58636f")),
        "title": str(unit["title"]),
        "subtitle": str(unit.get("subtitle", "")),
        "minutes": int(unit.get("minutes", max(8, len(sections) * 2))),
        "hero_article": unit.get("hero_article"),
        "lead": str(unit.get("lead", unit.get("subtitle", ""))),
        "sections": sections,
        "ideas": [
            (i["term"], i["definition"]) if isinstance(i, dict) else (i[0], i[1])
            for i in unit.get("ideas", [])
        ],
        "game": _game_from_unit(unit),
        "did_you_know": str(unit.get("did_you_know", "")),
        "source": _source_tuple(unit),
        "sources": unit.get("sources") or [unit.get("source")] or track.get("sources") or [],
        "next": str(unit.get("next", "")),
        "track": f"curriculum-{domain}",
        "tags": list(unit.get("tags") or []),
        "source_signals": unit.get("source_signals") or unit.get("text_signals") or {},
        "deep_companion": unit.get("deep_companion"),
        "curriculum": {
            "track_id": track_id,
            "track_name": str(track.get("name", track_id)),
            "unit_id": str(unit["id"]),
            "domain": domain,
            "prerequisites": list(unit.get("prerequisites") or []),
            "thinking_questions": list(unit.get("thinking_questions") or []),
            "practice_prompt": unit.get("practice_prompt") or unit.get("application_prompt") or unit.get("implementation_prompt") or "",
            "author": track.get("author"),
            "collection": track.get("collection"),
        },
    }
    if unit.get("difficulty_level"):
        lesson["difficulty_level"] = unit["difficulty_level"]
    return lesson


def curriculum_lessons() -> list[dict[str, Any]]:
    lessons: list[dict[str, Any]] = []
    for track in all_tracks():
        for unit in track.get("units", []):
            if isinstance(unit, dict) and unit.get("id"):
                lessons.append(unit_to_lesson(unit, track))
    return lessons


def _layout_for_domain(domain: str, index: int, total: int) -> tuple[float, float]:
    """Spread units within a domain column on the global graph."""
    columns = {"math": 14, "thinking": 26, "physics": 38, "invention": 50, "statecraft": 62, "history": 74, "startup": 88}
    x = columns.get(domain, 50)
    if total <= 1:
        y = 22
    else:
        y = 12 + (index / max(1, total - 1)) * 28
    return x, y


def tracks_to_graph(tracks: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Convert curriculum tracks into graph domains, nodes, and prerequisite edges."""
    tracks = tracks if tracks is not None else all_tracks()
    domains: dict[str, dict[str, Any]] = {}
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    unit_domains: dict[str, str] = {}

    for track in tracks:
        domain = str(track.get("domain", "thinking"))
        if domain not in domains:
            domains[domain] = {
                "id": domain,
                "name": domain.replace("-", " ").title(),
                "color": DOMAIN_COLORS.get(domain, "#58636f"),
            }
        units = [u for u in track.get("units", []) if isinstance(u, dict) and u.get("id")]
        for idx, unit in enumerate(units):
            uid = str(unit["id"])
            unit_domains[uid] = domain
            x, y = _layout_for_domain(domain, idx, len(units))
            nodes.append({
                "id": uid,
                "domain": domain,
                "title": str(unit.get("title", uid)),
                "kind": "article",
                "xp": int(unit.get("xp", 120)),
                "url": f"/output/learn/{uid}.html",
                "summary": str(unit.get("subtitle", ""))[:160],
                "difficulty": unit.get("difficulty_level", unit.get("difficulty", "core")),
                "x": x,
                "y": y,
                "curriculum_track": str(track.get("id", "")),
            })
            for prereq in unit.get("prerequisites") or []:
                edges.append({
                    "from": str(prereq),
                    "to": uid,
                    "relation": "prerequisite",
                    "reason": f"Required before {unit.get('title', uid)}",
                })

    return {
        "domains": sorted(domains.values(), key=lambda d: d["id"]),
        "nodes": nodes,
        "edges": edges,
    }


CURRICULUM_GRAPH: dict[str, Any] = tracks_to_graph()
CURRICULUM_LESSONS: list[dict[str, Any]] = curriculum_lessons()


def track_catalog() -> list[dict[str, Any]]:
    """Summary for /learn curriculum section."""
    catalog: list[dict[str, Any]] = []
    for track in all_tracks():
        units = track.get("units", [])
        catalog.append({
            "id": track["id"],
            "name": track.get("name", track["id"]),
            "domain": track.get("domain", "thinking"),
            "color": DOMAIN_COLORS.get(str(track.get("domain", "thinking")), "#58636f"),
            "author": track.get("author"),
            "collection": track.get("collection"),
            "unit_count": len(units),
            "units": [
                {
                    "id": u["id"],
                    "title": u.get("title", u["id"]),
                    "url": f"/output/learn/{u['id']}.html",
                    "minutes": u.get("minutes"),
                    "prerequisites": u.get("prerequisites") or [],
                }
                for u in units
                if isinstance(u, dict) and u.get("id")
            ],
        })
    return catalog


# LifeOS graph node ids that curriculum units may reference as cross-track prerequisites.
KNOWN_GRAPH_PREREQ_IDS: frozenset[str] = frozenset({
    "story-of-civilization",
    "arena-civilization",
    "game-theory",
    "fermi-estimation",
    "drill-primes",
    "quantum-zoo",
    "arena-quantum-fields",
    "power-of-compounding",
    "drill-compounding-engine",
    "why-we-sleep",
    "drill-sleep-stages",
    "arena-art-movements",
    "deep-socrates-athens",
    "deep-plato-academy",
    "deep-library-alexandria",
})

_TRACK_REQUIRED = ("id", "domain", "units")
_UNIT_REQUIRED = ("id", "title", "sections", "prerequisites", "source")


def _track_title(track: dict[str, Any]) -> str:
    return str(track.get("name") or track.get("title") or "").strip()


def _unit_summary(unit: dict[str, Any]) -> str:
    return str(unit.get("summary") or unit.get("subtitle") or unit.get("lead") or "").strip()


def _unit_questions(unit: dict[str, Any]) -> list[Any]:
    qs = unit.get("thinking_questions")
    if qs is None:
        qs = unit.get("questions")
    return list(qs or [])


def _unit_source_url(unit: dict[str, Any]) -> str:
    src = unit.get("source")
    if isinstance(src, dict):
        return str(src.get("url") or "").strip()
    if isinstance(src, (list, tuple)) and len(src) >= 2:
        return str(src[1] or "").strip()
    return ""


def _all_unit_ids(tracks: list[dict[str, Any]]) -> set[str]:
    ids: set[str] = set()
    for track in tracks:
        for unit in track.get("units") or []:
            if isinstance(unit, dict) and unit.get("id"):
                ids.add(str(unit["id"]))
    return ids


def _valid_prerequisite_ids(tracks: list[dict[str, Any]] | None = None) -> set[str]:
    tracks = tracks if tracks is not None else all_tracks()
    return _all_unit_ids(tracks) | set(KNOWN_GRAPH_PREREQ_IDS)


def validate_tracks(tracks: list[dict[str, Any]] | None = None) -> list[dict[str, str]]:
    """Return validation errors (empty list means structurally valid)."""
    tracks = tracks if tracks is not None else all_tracks()
    errors: list[dict[str, str]] = []
    seen_tracks: set[str] = set()
    seen_units: set[str] = set()
    valid_prereqs = _valid_prerequisite_ids(tracks)

    for t_idx, track in enumerate(tracks):
        if not isinstance(track, dict):
            errors.append({"code": "track_not_dict", "message": f"Track index {t_idx} is not an object"})
            continue
        track_id = str(track.get("id") or f"track[{t_idx}]")
        for field in _TRACK_REQUIRED:
            if field not in track or track[field] in (None, ""):
                if field == "units" and track.get("units") == []:
                    errors.append({
                        "code": "missing_field",
                        "track_id": track_id,
                        "message": f"Track {track_id!r} has no units",
                    })
                elif field != "units":
                    errors.append({
                        "code": "missing_field",
                        "track_id": track_id,
                        "message": f"Track {track_id!r} missing required field {field!r}",
                    })
        if not _track_title(track):
            errors.append({
                "code": "missing_field",
                "track_id": track_id,
                "message": f"Track {track_id!r} missing required title/name",
            })
        tid = track.get("id")
        if tid:
            tid_s = str(tid)
            if tid_s in seen_tracks:
                errors.append({
                    "code": "duplicate_track_id",
                    "track_id": tid_s,
                    "message": f"Duplicate track id {tid_s!r}",
                })
            seen_tracks.add(tid_s)

        units = track.get("units")
        if not isinstance(units, list):
            if "units" in track:
                errors.append({
                    "code": "invalid_units",
                    "track_id": track_id,
                    "message": f"Track {track_id!r} units must be a list",
                })
            continue

        for u_idx, unit in enumerate(units):
            if not isinstance(unit, dict):
                errors.append({
                    "code": "unit_not_dict",
                    "track_id": track_id,
                    "message": f"Track {track_id!r} unit index {u_idx} is not an object",
                })
                continue
            unit_id = str(unit.get("id") or f"{track_id}/unit[{u_idx}]")
            for field in _UNIT_REQUIRED:
                if field not in unit:
                    errors.append({
                        "code": "missing_field",
                        "track_id": track_id,
                        "unit_id": unit_id,
                        "message": f"Unit {unit_id!r} missing required field {field!r}",
                    })
            if not str(unit.get("title") or "").strip():
                errors.append({
                    "code": "missing_field",
                    "track_id": track_id,
                    "unit_id": unit_id,
                    "message": f"Unit {unit_id!r} missing required title",
                })
            if not _unit_summary(unit):
                errors.append({
                    "code": "missing_field",
                    "track_id": track_id,
                    "unit_id": unit_id,
                    "message": f"Unit {unit_id!r} missing summary/subtitle",
                })
            sections = unit.get("sections")
            if sections is None or not isinstance(sections, list) or len(sections) == 0:
                errors.append({
                    "code": "missing_sections",
                    "track_id": track_id,
                    "unit_id": unit_id,
                    "message": f"Unit {unit_id!r} needs at least one section",
                })
            elif isinstance(sections, list):
                for s_idx, section in enumerate(sections):
                    if isinstance(section, dict):
                        if not str(section.get("heading") or section.get("title") or "").strip():
                            errors.append({
                                "code": "missing_section_heading",
                                "track_id": track_id,
                                "unit_id": unit_id,
                                "message": f"Unit {unit_id!r} section {s_idx} missing heading",
                            })
                        if not str(section.get("body") or section.get("html") or "").strip():
                            errors.append({
                                "code": "missing_section_body",
                                "track_id": track_id,
                                "unit_id": unit_id,
                                "message": f"Unit {unit_id!r} section {s_idx} missing body",
                            })
            if "prerequisites" in unit and not isinstance(unit.get("prerequisites"), list):
                errors.append({
                    "code": "invalid_prerequisites",
                    "track_id": track_id,
                    "unit_id": unit_id,
                    "message": f"Unit {unit_id!r} prerequisites must be a list",
                })
            if not _unit_questions(unit):
                errors.append({
                    "code": "missing_questions",
                    "track_id": track_id,
                    "unit_id": unit_id,
                    "message": f"Unit {unit_id!r} missing thinking_questions/questions",
                })
            uid = unit.get("id")
            if uid:
                uid_s = str(uid)
                if uid_s in seen_units:
                    errors.append({
                        "code": "duplicate_unit_id",
                        "track_id": track_id,
                        "unit_id": uid_s,
                        "message": f"Duplicate unit id {uid_s!r}",
                    })
                seen_units.add(uid_s)
                for prereq in unit.get("prerequisites") or []:
                    pid = str(prereq)
                    if pid not in valid_prereqs:
                        errors.append({
                            "code": "broken_prerequisite",
                            "track_id": track_id,
                            "unit_id": uid_s,
                            "message": f"Unit {uid_s!r} prerequisite {pid!r} not in curriculum or allowlist",
                        })

    return errors


def curriculum_report(
    tracks: list[dict[str, Any]] | None = None,
    *,
    content_source: str | None = None,
) -> dict[str, Any]:
    """Structured JSON-friendly validation report with per-track counts."""
    tracks = tracks if tracks is not None else all_tracks()
    if content_source is None:
        content_source = "local" if _EXTERNAL_TRACKS else "seed"
    errors = validate_tracks(tracks)
    warnings: list[dict[str, str]] = []
    by_track: list[dict[str, Any]] = []
    total_units = 0
    total_questions = 0
    total_substantial = 0
    total_missing_source = 0

    for track in tracks:
        if not isinstance(track, dict):
            continue
        track_id = str(track.get("id") or "")
        units = [u for u in (track.get("units") or []) if isinstance(u, dict)]
        substantial = 0
        questions_count = 0
        missing_source = 0
        for unit in units:
            uid = str(unit.get("id") or "")
            section_count = len(unit.get("sections") or [])
            q_count = len(_unit_questions(unit))
            questions_count += q_count
            if section_count >= 5:
                substantial += 1
            elif uid:
                warnings.append({
                    "code": "thin_unit",
                    "track_id": track_id,
                    "unit_id": uid,
                    "message": f"Unit {uid!r} has {section_count} sections (< 5)",
                })
            if not _unit_source_url(unit):
                missing_source += 1
                if uid:
                    warnings.append({
                        "code": "missing_source_url",
                        "track_id": track_id,
                        "unit_id": uid,
                        "message": f"Unit {uid!r} has no source URL",
                    })
        total_units += len(units)
        total_questions += questions_count
        total_substantial += substantial
        total_missing_source += missing_source
        by_track.append({
            "track_id": track_id,
            "track_name": _track_title(track) or track_id,
            "domain": str(track.get("domain") or ""),
            "total_units": len(units),
            "substantial_units": substantial,
            "questions_count": questions_count,
            "units_missing_source": missing_source,
        })

    return {
        "ok": len(errors) == 0,
        "content_source": content_source,
        "errors": errors,
        "warnings": warnings,
        "counts": {
            "tracks": len([t for t in tracks if isinstance(t, dict)]),
            "units": total_units,
            "substantial_units": total_substantial,
            "questions": total_questions,
            "units_missing_source": total_missing_source,
            "by_track": by_track,
        },
    }


def list_tracks_compact(tracks: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """Compact track/unit counts for CLI ``list``."""
    tracks = tracks if tracks is not None else all_tracks()
    rows: list[dict[str, Any]] = []
    for track in tracks:
        if not isinstance(track, dict):
            continue
        units = [u for u in (track.get("units") or []) if isinstance(u, dict) and u.get("id")]
        rows.append({
            "id": str(track.get("id") or ""),
            "name": _track_title(track),
            "domain": str(track.get("domain") or ""),
            "units": len(units),
            "unit_ids": [str(u["id"]) for u in units],
        })
    return rows


def render_curriculum_page() -> str:
    """Standalone curriculum overview for output/learn/curriculum.html."""
    tracks = track_catalog()
    report = curriculum_report()
    esc = html.escape
    track_cards = []
    for tr in tracks:
        unit_rows = "".join(
            f"<tr><td><a href='{esc(u['url'])}'>{esc(u['title'])}</a></td>"
            f"<td>{esc(str(u.get('minutes', '')))}m</td>"
            f"<td>{esc(', '.join(u.get('prerequisites') or []) or '—')}</td></tr>"
            for u in tr.get("units", [])
        )
        track_cards.append(
            f"<section class='track' style='--c:{tr['color']}'>"
            f"<header><h2>{esc(tr['name'])}</h2>"
            f"<p>{tr['unit_count']} units · {esc(tr.get('domain', ''))}"
            f"{(' · ' + esc(tr['collection'])) if tr.get('collection') else ''}</p></header>"
            f"<table><thead><tr><th>Unit</th><th>Min</th><th>Prerequisites</th></tr></thead>"
            f"<tbody>{unit_rows}</tbody></table></section>"
        )
    summary = report["counts"]
    return f"""<!doctype html><html lang='en'><head>
<meta charset='utf-8'>
<meta name='viewport' content='width=device-width,initial-scale=1'>
<title>LifeOS Curriculum</title>
<style>
*{{box-sizing:border-box}}body{{margin:0;background:#f7f5f0;color:#151719;font-family:Inter,system-ui,sans-serif}}
.wrap{{width:min(960px,calc(100% - 32px));margin:0 auto;padding:18px 0 40px}}
.top{{display:flex;gap:14px;flex-wrap:wrap;border-bottom:1px solid #d8d3c8;padding-bottom:12px;margin-bottom:22px;font:800 13px/1 system-ui}}
.top a{{color:#5f665f;text-decoration:none}}h1{{font:800 clamp(32px,6vw,52px)/1 Georgia,serif;margin:0 0 8px}}
.lede{{color:#4e5651;font:500 17px/1.55 Georgia,serif;max-width:62ch;margin:0 0 20px}}
.stats{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin:0 0 28px}}
.stat{{background:#fff;border:1px solid #d8d3c8;padding:12px}}.stat b{{display:block;font:900 22px/1 system-ui}}.stat span{{font:700 11px/1.3 system-ui;color:#65665f;text-transform:uppercase;letter-spacing:.08em}}
.track{{background:#fff;border:1px solid #d8d3c8;border-left:4px solid var(--c);padding:16px;margin:0 0 16px}}
.track h2{{font:800 22px/1.1 system-ui;margin:0}}.track p{{margin:6px 0 0;color:#5f665f;font:650 13px/1.35 system-ui}}
table{{width:100%;border-collapse:collapse;margin-top:12px;font:600 14px/1.4 system-ui}}
th,td{{text-align:left;padding:8px 6px;border-top:1px solid #ece8df}}th{{font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:#77736a}}
a{{color:#151719}}@media(max-width:720px){{.stats{{grid-template-columns:repeat(2,minmax(0,1fr))}}}}
</style></head><body><div class='wrap'>
<div class='top'><a href='/learn'>&larr; Field Notes</a><a href='/output/learn/skill-tree.html'>Knowledge Graph</a></div>
<h1>Curriculum Overview</h1>
<p class='lede'>Mastery tracks with prerequisite edges, deep sections, and thinking questions. Generated from the curriculum schema — safe to grow via content ingestion.</p>
<div class='stats'>
<div class='stat'><b>{summary['tracks']}</b><span>Tracks</span></div>
<div class='stat'><b>{summary['units']}</b><span>Units</span></div>
<div class='stat'><b>{summary['substantial_units']}</b><span>Units ≥5 sections</span></div>
<div class='stat'><b>{summary['questions']}</b><span>Thinking questions</span></div>
</div>
{''.join(track_cards)}
</div><script>
(function(){{
const KEY='lifeos.learning.progress.v1';
function load(){{try{{return JSON.parse(localStorage.getItem(KEY)||'{{}}')}}catch{{return {{}}}}}}
function xp(p){{return Object.values(p.done||{{}}).reduce((s,n)=>s+(+n.xp||0),0)}}
document.title='LifeOS Curriculum · '+xp(load())+' XP';
}})();
</script></body></html>"""


def main() -> int:
    parser = argparse.ArgumentParser(description="LifeOS mastery curriculum")
    content_parent = argparse.ArgumentParser(add_help=False)
    content_parent.add_argument(
        "--content-path",
        metavar="PATH",
        help="External content module exporting CURRICULUM_TRACKS (skips local content import)",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("report", parents=[content_parent], help="Print JSON validation report")
    sub.add_parser("list", parents=[content_parent], help="Print compact track/unit counts")
    sub.add_parser("validate", parents=[content_parent], help="Validate tracks; exit 1 on errors")
    args = parser.parse_args()
    try:
        tracks, content_source = resolve_cli_tracks(getattr(args, "content_path", None))
    except (FileNotFoundError, SyntaxError, AttributeError, TypeError, ImportError) as exc:
        print(json.dumps({"ok": False, "content_source": getattr(args, "content_path", None), "error": str(exc)}, indent=2))
        return 1
    if args.cmd == "report":
        print(json.dumps(curriculum_report(tracks, content_source=content_source), indent=2))
        return 0
    if args.cmd == "list":
        print(json.dumps({"content_source": content_source, "tracks": list_tracks_compact(tracks)}, indent=2))
        return 0
    if args.cmd == "validate":
        report = curriculum_report(tracks, content_source=content_source)
        print(json.dumps(report, indent=2))
        return 0 if report["ok"] else 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
