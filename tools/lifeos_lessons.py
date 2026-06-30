#!/usr/bin/env python3
"""LifeOS morning micro-lessons.

Generates a small set of self-contained, magazine-style HTML lessons each day so
the user reaches for something to *learn* in the morning instead of doom
scrolling. Each lesson is readable prose with real photos embedded directly into
the file (base64), so once the page loads on the phone it works fully offline.
Each lesson ends with a *thinking game* (reorder / estimate / ponder) rather than
multiple-choice quizzes.

Output lands in the vault at output/learn/ and is served by lifeos_server.py at
/learn (and the static /output/learn/ path).

Build:  python tools/lifeos_lessons.py build
List:   python tools/lifeos_lessons.py list
"""
from __future__ import annotations

import argparse
import base64
import html
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime
from hashlib import sha1
from typing import Any

from lifeos_paths import APP_ROOT, VAULT_ROOT

try:  # playable WebGL games surfaced alongside the lessons
    from lifeos_games import GAMES as _GAMES
except Exception:
    _GAMES = []
try:  # spec-driven arcade drills (the generalizable learning-game system)
    from lifeos_arcade import ARCADE as _DRILLS
except Exception:
    _DRILLS = []
GAME_CATALOG = list(_GAMES) + list(_DRILLS)
# Reverse map: which game reinforces which lesson (game is played AFTER the lesson).
GAME_FOR_LESSON = {g["pairs"]: g for g in GAME_CATALOG if g.get("pairs")}
try:  # optional progression map for /learn
    from lifeos_skill_tree import build as build_skill_tree
except Exception:
    build_skill_tree = None
try:  # Math Academy-inspired training queue and ingestion contract
    from lifeos_learning_engine import build as build_learning_engine
except Exception:
    build_learning_engine = None
try:  # hand-curated long-form tracks for topics that need real depth
    from lifeos_deep_history import DEEP_LESSONS
except Exception:
    DEEP_LESSONS = []
try:  # mastery curriculum tracks (Math Academy-inspired infrastructure)
    from lifeos_curriculum import CURRICULUM_LESSONS, render_curriculum_page, track_catalog
except Exception:
    CURRICULUM_LESSONS = []
    track_catalog = lambda: []  # noqa: E731
    render_curriculum_page = None

OUT = VAULT_ROOT / "output" / "learn"
GENERATED_LESSONS_PATH = OUT / "generated-lessons.json"
IMG_CACHE = APP_ROOT / ".cache" / "lesson-images"
UA = "LifeOS-personal-learning/1.0 (personal morning lessons app)"


# --------------------------------------------------------------------------- #
# Images: resolve a Wikipedia article -> lead photo, download once, embed as a
# base64 data URI so the lesson is a single offline-capable packet.
# --------------------------------------------------------------------------- #
def _http_get(url: str, timeout: int = 25, retries: int = 3) -> bytes:
    last: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except urllib.error.HTTPError as exc:
            last = exc
            if exc.code == 429:  # rate limited — back off and retry
                time.sleep(2 * (attempt + 1))
                continue
            raise
    if last:
        raise last
    raise RuntimeError("unreachable")


def _meta_path():
    return IMG_CACHE / "_resolved.json"


def _load_meta() -> dict:
    try:
        return json.loads(_meta_path().read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_meta(meta: dict) -> None:
    IMG_CACHE.mkdir(parents=True, exist_ok=True)
    _meta_path().write_text(json.dumps(meta), encoding="utf-8")


def _ctype(url: str) -> str:
    u = url.lower()
    if u.endswith(".png"):
        return "image/png"
    if u.endswith(".svg"):
        return "image/svg+xml"
    if u.endswith(".gif"):
        return "image/gif"
    if u.endswith(".webp"):
        return "image/webp"
    return "image/jpeg"


def _data_uri(url: str) -> str | None:
    """Download (cached) and return a base64 data URI, or None on failure."""
    try:
        key = sha1(url.encode("utf-8")).hexdigest()
        cached = IMG_CACHE / key
        if cached.exists():
            raw = cached.read_bytes()
        else:
            raw = _http_get(url)
            IMG_CACHE.mkdir(parents=True, exist_ok=True)
            cached.write_bytes(raw)
            time.sleep(0.6)  # be polite to Wikimedia; cache makes later builds instant
        if not raw or len(raw) < 200:
            return None
        return f"data:{_ctype(url)};base64,{base64.b64encode(raw).decode('ascii')}"
    except Exception:
        return None


def wiki_photo(article: str, width: int = 900) -> tuple[str | None, str]:
    """Return (data_uri, credit) for an article's lead image, or (None, '').

    Uses the MediaWiki pageimages API with pithumbsize so the thumbnail server
    returns a valid pre-generated URL at the requested width (hand-editing the
    width into an upload.wikimedia.org URL is now rejected with HTTP 400).
    """
    if os.environ.get("LIFEOS_SKIP_LESSON_IMAGES", "").lower() in {"1", "true", "yes"}:
        return None, ""
    mkey = f"{article}|{width}"
    meta = _load_meta()
    try:
        if mkey in meta:
            src, title = meta[mkey]["src"], meta[mkey]["title"]
        else:
            q = urllib.parse.urlencode({
                "action": "query", "titles": article, "prop": "pageimages",
                "piprop": "thumbnail", "pithumbsize": str(width), "format": "json", "redirects": "1",
            })
            data = json.loads(_http_get(f"https://en.wikipedia.org/w/api.php?{q}").decode("utf-8"))
            pages = (data.get("query") or {}).get("pages") or {}
            page = next(iter(pages.values())) if pages else {}
            src = (page.get("thumbnail") or {}).get("source")
            title = page.get("title", article)
            meta[mkey] = {"src": src, "title": title}  # cache result, incl. negative (src=None)
            _save_meta(meta)
        if not src:
            return None, ""
        uri = _data_uri(src)
        if not uri:
            return None, ""
        return uri, f"{title} · Wikipedia"
    except Exception:
        return None, ""


def _svg_hero(accent: str, glyph: str) -> str:
    return (
        f"<svg viewBox='0 0 900 300' xmlns='http://www.w3.org/2000/svg'>"
        f"<defs><linearGradient id='g' x1='0' y1='0' x2='1' y2='1'>"
        f"<stop offset='0' stop-color='{accent}' stop-opacity='.35'/>"
        f"<stop offset='1' stop-color='#0b0f0d'/></linearGradient></defs>"
        f"<rect width='900' height='300' fill='url(#g)'/>"
        f"<text x='48' y='205' font-size='150'>{glyph}</text></svg>"
    )


# --------------------------------------------------------------------------- #
# Lesson library. Plain data; the renderer turns it into HTML.
#   sections: (heading, body_html, image_article|None)
#   ideas:    (term, definition)
#   game:     dict with type in {order, estimate, ponder}
# --------------------------------------------------------------------------- #
LESSONS: list[dict[str, Any]] = [
    {
        "id": "story-of-civilization",
        "emoji": "🏛️",
        "accent": "#e0a851",
        "title": "How Civilization Began",
        "subtitle": "Foragers to farmers to the first cities — the 10,000-year leap that made everything.",
        "minutes": 6,
        "hero_article": "Göbekli Tepe",
        "lead": "For roughly 300,000 years, humans foraged in small wandering bands. Then, in a "
                "geological blink, we settled down, planted seeds, built cities, and learned to "
                "write. Almost everything you call civilization was invented in the last 5% of "
                "the human story — and it started with a strange, risky bet on a handful of grass seeds.",
        "sections": [
            ("The bet that changed everything",
             "<p>Around <b>9500 BCE</b> in the Fertile Crescent — the arc of land curving from the "
             "Nile up through Mesopotamia — people began planting wild wheat and barley instead of "
             "merely gathering it. Here is the twist: early farming was actually <i>harder</i> than "
             "foraging, and the first farmers were shorter and sicker than the hunters before them. "
             "But farming had one unbeatable advantage — it fed far more people from the same patch "
             "of land.</p><p>More food meant more children, and a planted field had to be guarded "
             "and harvested. The wanderer became the villager. There was no going back.</p>",
             "Neolithic Revolution"),
            ("Why cities were a superpower",
             "<p>Stored grain is stored <b>surplus</b> — and surplus is freedom from finding your "
             "next meal. For the first time, some people didn't have to farm at all. They could be "
             "full-time potters, priests, soldiers, kings. That division of labour is the engine "
             "behind every technology since.</p><p>Uruk, in Sumer, swelled to tens of thousands of "
             "people by <b>3500 BCE</b> — arguably the world's first true city. Around it appeared "
             "the wheel, the plough, and mass-produced pottery.</p>",
             "Uruk"),
            ("Writing: civilization's external memory",
             "<p>To track who owed how much grain, Sumerian accountants pressed wedge-shaped marks "
             "into wet clay — <b>cuneiform</b>, around 3200 BCE. It began not as poetry but as "
             "bookkeeping: receipts for barley and beer.</p><p>Yet the moment thought could be "
             "stored <i>outside</i> a human skull, knowledge stopped dying with each generation. "
             "Ideas could now travel across centuries. That is the precise moment history itself "
             "begins.</p>",
             "Cuneiform"),
        ],
        "ideas": [
            ("Neolithic Revolution", "The shift from foraging to farming (~9500 BCE) — the foundation of all settled life."),
            ("Surplus", "Stored extra food; the thing that first let humans specialize beyond getting fed."),
            ("City-state", "An independent city and its surrounding land — the first form of complex society."),
            ("Cuneiform", "The earliest known writing: wedge marks pressed into clay tablets."),
        ],
        "game": {
            "type": "order",
            "prompt": "Drag these milestones into the order they actually happened — oldest at the top.",
            "items": [
                ("g1", "Göbekli Tepe is carved"),
                ("g2", "Wheat is first farmed"),
                ("g3", "The city of Uruk rises"),
                ("g4", "Cuneiform writing appears"),
                ("g5", "The Great Pyramid is built"),
            ],
            "explain": "Göbekli Tepe (~9600 BCE) → farming (~9500) → Uruk (~3500) → cuneiform (~3200) → "
                       "Great Pyramid (~2560). The shock is that the temple at Göbekli Tepe came "
                       "<i>before</i> farming — worship may have helped pull people into settled life.",
        },
        "did_you_know": "Göbekli Tepe is older than Stonehenge by 6,000 years and older than writing, the "
                        "wheel, and even pottery. Hunter-gatherers with no metal tools quarried and raised "
                        "16-tonne stone pillars — for a temple, before they had a town.",
        "source": ("Will Durant — <i>Our Oriental Heritage</i> (The Story of Civilization, Vol. 1)",
                   "https://archive.org/details/in.ernet.dli.2015.275128"),
        "next": "Next time: how those first city-states grew into the world's first empires.",
    },
    {
        "id": "why-the-sky-is-blue",
        "emoji": "🌤️",
        "accent": "#5b9bf0",
        "title": "Why the Sky Is Blue",
        "subtitle": "The same physics paints the noon sky blue and the evening sky red.",
        "minutes": 5,
        "hero_article": "Diffuse sky radiation",
        "lead": "Sunlight looks white, but it is every colour blended together. The colour of the sky "
                "isn't really about the sky at all — it's a story about how those hidden colours "
                "bounce off the air itself, and why blue wins the fight at noon but loses it at dusk.",
        "sections": [
            ("Light hits air and scatters",
             "<p>Air is mostly nitrogen and oxygen molecules. As sunlight pushes through, it "
             "<b>scatters</b> off these tiny molecules in all directions. The key fact: shorter "
             "wavelengths scatter far more strongly than longer ones. This is <b>Rayleigh "
             "scattering</b>, and the effect is dramatic — blue light scatters roughly nine times "
             "more than red.</p><p>So the whole dome of the sky glows with scattered blue, arriving "
             "at your eye from every direction at once.</p>",
             "Rayleigh scattering"),
            ("So why isn't it violet?",
             "<p>Good catch — violet scatters even more than blue. But two things tip the balance: "
             "the Sun emits less violet to begin with, and your eyes are simply more sensitive to "
             "blue. The mixture your brain finally receives reads as that familiar sky-blue.</p>",
             None),
            ("Sunsets: the long way through",
             "<p>At sunset the Sun sits low, so its light skims sideways through far more atmosphere "
             "before reaching you. Along that long path, the blue is scattered away entirely — "
             "leaving the reds and oranges to travel straight to your eye. Same physics, different "
             "geometry. The fiery sky is just the colours that survived the trip.</p>",
             "Sunset"),
        ],
        "ideas": [
            ("Rayleigh scattering", "Scattering of light by particles far smaller than its wavelength; strongly favours blue."),
            ("Wavelength", "The distance between light waves — blue is short, red is long."),
            ("Why sunsets glow red", "A long, low path through the air scatters away the blue before it reaches you."),
            ("Why clouds are white", "Water droplets are large, so they scatter every colour equally."),
        ],
        "game": {
            "type": "ponder",
            "prompt": "If Earth's atmosphere were suddenly twice as thick, what would midday and sunset "
                      "look like? Picture it before you reveal the answer.",
            "reveal": "Midday blue would deepen and darken (more air = more scattering, so even more blue "
                      "removed from the direct sunbeam and spread across the sky). Sunsets would turn a "
                      "richer, deeper red and last longer, because the already-long path now strips away "
                      "even the greens and yellows — leaving only the longest red wavelengths.",
        },
        "did_you_know": "On Mars the rule flips. Fine dust in the thin air makes the daytime sky a dusty "
                        "butterscotch — and turns sunsets a cool, eerie blue. NASA's rovers have "
                        "photographed it.",
        "source": ("NASA Science — <i>Why Is the Sky Blue?</i>", "https://spaceplace.nasa.gov/blue-sky/en/"),
        "next": "Tonight: look about 90° away from the Sun through polarized sunglasses, and rotate them.",
    },
    {
        "id": "how-memory-works",
        "emoji": "🧠",
        "accent": "#b06bf0",
        "title": "How Memory Works — and How to Hack It",
        "subtitle": "Why you forget so fast, and the two tricks that quietly beat the forgetting curve.",
        "minutes": 5,
        "hero_article": "Memory",
        "lead": "Memory feels like a video recording, but it is nothing of the sort — it is a "
                "reconstruction your brain rebuilds each time, slightly differently. Once you "
                "understand how it actually works, you get a cheat code for learning almost "
                "anything faster and keeping it longer.",
        "sections": [
            ("The forgetting curve",
             "<p>In the 1880s, Hermann Ebbinghaus memorized lists of nonsense syllables and "
             "painstakingly tracked how quickly he lost them. The result was brutal and fast: most "
             "of what you learn today is gone within days — <i>unless</i> you deliberately do "
             "something to interrupt the slide.</p><p>That curve is the enemy. The good news is it "
             "has two well-tested weaknesses.</p>",
             "Hermann Ebbinghaus"),
            ("Hack 1 — Retrieve, don't review",
             "<p>Re-reading your notes feels productive and is almost useless. What actually carves "
             "a memory in is <b>pulling the answer out of your head</b> — the effortful struggle of "
             "recall. Psychologists call it the <b>testing effect</b>, and it beats every passive "
             "method by a wide margin.</p><p>This is why the little game at the bottom of each "
             "lesson matters more than the reading above it.</p>",
             None),
            ("Hack 2 — Space it out",
             "<p>Review something just as you're about to forget it, and each recall resets the "
             "forgetting curve a little flatter. Five reviews spread across two weeks crush five "
             "reviews crammed into one night. This is <b>spaced repetition</b> — and it's the whole "
             "reason a single lesson each morning beats a marathon study session.</p>",
             "Spaced repetition"),
        ],
        "ideas": [
            ("Testing effect", "Recalling information strengthens memory far more than re-reading it."),
            ("Spaced repetition", "Reviewing at growing intervals to fight forgetting efficiently."),
            ("Forgetting curve", "Ebbinghaus's finding that memory decays sharply without reinforcement."),
            ("Desirable difficulty", "A bit of struggle during learning is what makes it stick."),
        ],
        "game": {
            "type": "ponder",
            "prompt": "You have exactly 30 minutes to study, and two tests: one tomorrow, one in two "
                      "weeks. How should you spend the 30 minutes? Decide, then reveal.",
            "reveal": "Don't just re-read for tomorrow. Spend a few minutes reading, then close the notes "
                      "and quiz yourself from memory (testing effect). Stop before you've 'mastered' it, "
                      "and plan two short spaced reviews over the next two weeks. Cramming wins the "
                      "tomorrow test but loses the two-week one; retrieval + spacing wins both.",
        },
        "did_you_know": "That maddening tip-of-the-tongue feeling — when you <i>almost</i> remember — is "
                        "the exact moment learning happens. Easy recall barely strengthens a memory; the "
                        "harder the (successful) struggle, the stronger it sticks.",
        "source": ("Brown, Roediger & McDaniel — <i>Make It Stick</i>", "https://www.retrievalpractice.org/"),
        "next": "Tonight, try to recall today's three lessons from memory before you check. That's the hack.",
    },
    {
        "id": "fermi-estimation",
        "emoji": "📐",
        "accent": "#2bd4c0",
        "title": "Guess Anything: Fermi Estimation",
        "subtitle": "How to land within 10× of almost any number using nothing but reasoning.",
        "minutes": 5,
        "hero_article": "Enrico Fermi",
        "lead": "How many piano tuners work in Chicago? You have no idea — and yet, with sixty seconds "
                "of thinking, you can get surprisingly close. This single mental tool, perfected by "
                "the physicist Enrico Fermi, will make you sharper in every argument, interview, and "
                "decision for the rest of your life.",
        "sections": [
            ("Break the impossible into the easy",
             "<p>Fermi could estimate almost anything by chopping one impossible question into "
             "several smaller questions he <i>could</i> guess — then multiplying them together. "
             "Each guess might be off, but the over- and under-estimates tend to cancel out, so the "
             "final answer lands shockingly close to reality.</p>",
             "Fermi problem"),
            ("The piano tuners of Chicago",
             "<p>Watch it work. Chicago has about 3 million people, so maybe 1 million households. "
             "Say 1 in 20 owns a piano — that's 50,000 pianos. Each is tuned roughly once a year, "
             "and one tuner can service maybe 1,000 pianos a year. So: 50,000 ÷ 1,000 ≈ "
             "<b>50 piano tuners</b>.</p><p>The real number is in that ballpark. You used zero data "
             "— only a chain of reasonable guesses.</p>",
             None),
            ("Why the errors forgive you",
             "<p>Each step might be wrong by 2–3×, some too high, some too low. Multiply several "
             "together and they partially cancel, so you almost never end up more than 10× off the "
             "truth. And 'within 10×' is frequently all a real decision actually needs.</p>",
             None),
        ],
        "ideas": [
            ("Order of magnitude", "Which power of ten a number sits near — the precision a Fermi estimate aims for."),
            ("Decomposition", "Splitting a hard quantity into smaller factors you can each guess."),
            ("Error cancellation", "Independent over- and under-guesses partly offset when multiplied."),
            ("Sanity check", "Asking 'is this magnitude even plausible?' before trusting a number."),
        ],
        "game": {
            "type": "estimate",
            "prompt": "Your turn, Fermi-style: about how many piano tuners work in Chicago? Type your "
                      "best reasoned guess.",
            "answer": "50",
            "unit": "piano tuners",
            "reveal": "Estimates from the chain above land near 50, and surveys put the real figure in the "
                      "dozens — well within Fermi range. If you were within 10×, your <i>reasoning</i> "
                      "was sound, which is the whole point.",
        },
        "did_you_know": "At the first nuclear test in 1945, Fermi dropped scraps of paper as the blast "
                        "wave passed and estimated the bomb's yield from how far they blew — landing close "
                        "to the answer the instruments needed weeks to compute.",
        "source": ("'Fermi problem' — overview & classic examples", "https://en.wikipedia.org/wiki/Fermi_problem"),
        "next": "Practice: estimate how many cups of coffee your city drinks before 9am.",
    },
    {
        "id": "power-of-compounding",
        "emoji": "📈",
        "accent": "#46d17a",
        "title": "The Quiet Power of Compounding",
        "subtitle": "The one idea behind wealth, skills, and habits — and why it always feels like magic.",
        "minutes": 5,
        "hero_article": "Compound interest",
        "lead": "Human intuition runs in straight lines, but the most powerful force in money, skill, "
                "and habit runs in curves. That single mismatch is why steady, boring effort looks "
                "like it's doing nothing — right up until it looks like it's doing everything.",
        "sections": [
            ("Exponential beats linear — eventually",
             "<p>Save $300 a month at 8% a year. After 10 years you'll have around $55,000, of which "
             "only ~$19,000 is growth. Leave it 30 years and it becomes roughly <b>$450,000</b> — "
             "and now <i>most</i> of that is growth piled on earlier growth. The early years feel "
             "pointless; the later years feel unstoppable. Same monthly habit, wildly different "
             "endings.</p>",
             "Exponential growth"),
            ("The Rule of 72",
             "<p>Here's a trick that needs no calculator. To find how long something growing at a "
             "steady rate takes to <i>double</i>, divide 72 by the rate. At 8%, that's 72 ÷ 8 = "
             "<b>9 years</b> to double. It works for money, audiences, skills — anything that "
             "compounds.</p>",
             None),
            ("1% better, every day",
             "<p>Improve by just 1% a day and you don't end the year 365% better — you end up about "
             "<b>37× better</b>, because each day's gain compounds on the last (1.01³⁶⁵ ≈ 37). Slip "
             "1% a day and you shrink to almost nothing. Habits are compound interest, paid in who "
             "you become.</p>",
             None),
        ],
        "ideas": [
            ("Compounding", "Growth that itself produces more growth — a curve, never a straight line."),
            ("Rule of 72", "Doubling time ≈ 72 ÷ the growth rate in percent."),
            ("The 1% rule", "Tiny daily gains multiply (1.01³⁶⁵ ≈ 37×) over a single year."),
            ("Time in market", "The biggest lever in compounding is how long, not how much."),
        ],
        "game": {
            "type": "estimate",
            "prompt": "A single penny doubles every day for 30 days ($0.01 → $0.02 → $0.04 …). Type your "
                      "guess for how many dollars you'd have on day 30.",
            "answer": "5368709",
            "unit": "dollars (≈ $5.4 million)",
            "reveal": "$0.01 × 2²⁹ ≈ <b>$5,368,709</b>. Almost nobody guesses within even 1,000×. That gut "
                      "failure <i>is</i> the lesson: your brain cannot feel exponential growth, which is "
                      "exactly why compounding looks like magic and why starting early matters so much.",
        },
        "did_you_know": "Warren Buffett built ~99% of his fortune after his 50th birthday — not because he "
                        "suddenly got smarter, but because that's where his compounding curve finally went "
                        "near-vertical. His real edge was starting young and never interrupting it.",
        "source": ("James Clear — <i>Atomic Habits</i> (the 1% essay)", "https://jamesclear.com/continuous-improvement"),
        "next": "Pick one 1%-a-day habit and start it today. The curve needs time more than intensity.",
    },
    {
        "id": "game-theory",
        "emoji": "🎲",
        "accent": "#f0922b",
        "title": "Game Theory: Why Selfishness Backfires",
        "subtitle": "Play the most famous game in social science — and discover how trust survives a world of cheaters.",
        "minutes": 6,
        "hero_article": "John von Neumann",
        "lead": "Two suspects, two cells, no way to talk. Betray your partner and you might walk free — "
                "but if you both betray, you both rot. This single puzzle, the Prisoner's Dilemma, "
                "quietly explains arms races, climate deals, office politics, and why your group chat "
                "can't pick a restaurant. Today you don't just read it — you play it.",
        "sections": [
            ("The trap of the one-shot game",
             "<p>The payoffs are brutal. If you both stay silent (cooperate), you each get a light "
             "sentence. If you both talk (defect), you each get a heavy one. But if <i>you</i> talk "
             "while your partner stays silent, you walk and they take the fall.</p><p>Think it "
             "through and the logic is airtight: no matter what your partner does, you're "
             "individually better off defecting. So both of you defect — and both end up worse than "
             "if you'd trusted each other. That grim outcome is the <b>Nash equilibrium</b>: nobody "
             "can improve by changing their move alone.</p>",
             "Nash equilibrium"),
            ("Then you play again. And again.",
             "<p>Everything changes when the game <i>repeats</i> and you'll meet again. Now today's "
             "betrayal can be punished tomorrow. In 1980 Robert Axelrod invited the world's game "
             "theorists to submit strategies for a repeated tournament. The winner stunned everyone "
             "by being the <i>simplest</i> program entered, just a few lines long.</p>",
             "Robert Axelrod (political scientist)"),
            ("Tit-for-Tat: nice, but no pushover",
             "<p>The champion was <b>Tit-for-Tat</b>: cooperate on the first move, then simply copy "
             "whatever your opponent did last. Axelrod found winning strategies shared four traits — "
             "be <b>nice</b> (never defect first), <b>retaliatory</b> (punish defection at once), "
             "<b>forgiving</b> (return to cooperation the moment they do), and <b>clear</b> (so "
             "others can learn to trust you). Now go beat it below — you'll find you can't, and the "
             "reason is the whole lesson.</p>",
             "Tit for tat"),
        ],
        "ideas": [
            ("Nash equilibrium", "An outcome where no player can do better by changing only their own move."),
            ("Dominant strategy", "A move that's best for you no matter what others do — defection, in one shot."),
            ("Non-zero-sum game", "A game where both sides can win together — the precondition for trust."),
            ("Tit-for-Tat", "Cooperate first, then mirror your opponent: nice, retaliatory, forgiving, clear."),
        ],
        "game": {
            "type": "pd",
            "opponent": "Tit-for-Tat",
            "rounds": 8,
            "prompt": "8 rounds against Tit-for-Tat. Each round you both choose. 🤝🤝 = +3 each · "
                      "😈 vs 🤝 = +5 / 0 · 😈😈 = +1 each. Try to out-score it.",
            "reveal": "Notice what happened: cheating wins one round but the copycat punishes you the next, "
                      "and you can never get more than a tie by betraying it. Mutual cooperation (3×8 = 24) "
                      "beats the chaos of mutual defection (1×8 = 8). Trust isn't naïve — against the right "
                      "strategy it's the <i>highest-scoring</i> move. That's Axelrod's discovery.",
        },
        "did_you_know": "Tit-for-Tat won Axelrod's tournament twice despite being the shortest program "
                        "submitted — and it never once beat an opponent head-to-head. It won the war by "
                        "never starting fights, only ending them.",
        "source": ("Nicky Case — <i>The Evolution of Trust</i> (a brilliant interactive)", "https://ncase.me/trust/"),
        "next": "Play the full version at ncase.me/trust — it adds noise, mistakes, and evolving populations.",
    },
    {
        "id": "monty-hall",
        "emoji": "🚪",
        "accent": "#46d17a",
        "title": "The Door Problem That Breaks Brains",
        "subtitle": "A puzzle so counter-intuitive that 1,000 PhDs publicly insisted the right answer was wrong.",
        "minutes": 5,
        "hero_article": "Monty Hall problem",
        "lead": "Three doors. Behind one, a car; behind the others, goats. You pick a door. The host — "
                "who knows where the car is — opens a different door to reveal a goat, then asks: "
                "do you want to switch? Your gut screams it's 50/50. Your gut is wrong, and proving "
                "it to yourself is one of the great little thrills in mathematics.",
        "sections": [
            ("The answer nobody believes",
             "<p>You should <b>always switch</b>. Switching wins the car <b>2 out of 3 times</b>; "
             "staying wins only 1 in 3. When columnist Marilyn vos Savant published this in 1990, "
             "she received around 10,000 letters telling her she was wrong — including roughly 1,000 "
             "from people with PhDs. She was right; they were wrong.</p>",
             None),
            ("Why switching wins",
             "<p>Your first pick had a 1-in-3 chance of being the car — so there's a 2-in-3 chance "
             "the car is behind one of the other two doors. The host then <i>helpfully removes the "
             "goat</i> from that pair. That entire 2/3 probability doesn't vanish — it collapses "
             "onto the single remaining door. The host's knowledge is the secret ingredient: he "
             "never opens the car, so his choice leaks information.</p><p>Still not convinced? "
             "Imagine 100 doors. You pick one (1% chance). The host opens 98 goats. Switch?</p>",
             None),
        ],
        "ideas": [
            ("Conditional probability", "The chance of something given new information — here, the host's reveal."),
            ("The host knows", "Monty never opens the car; that constraint is what makes switching pay."),
            ("Base rate", "Your first guess stays a 1/3 shot; switching inherits the other 2/3."),
            ("Intuition ≠ truth", "Some correct answers feel impossible — proof beats gut feeling."),
        ],
        "game": {
            "type": "monty",
            "prompt": "Play it yourself. Pick a door, the host reveals a goat, then stay or switch. "
                      "Play ~10 rounds and watch the two win-rates below pull apart.",
            "reveal": "Keep going and the numbers converge on the truth: switching wins about 2 in 3, "
                      "staying about 1 in 3. You didn't have to believe the math — you can just watch it "
                      "happen. That's the most honest kind of proof.",
        },
        "did_you_know": "The mathematician Paul Erdős — one of the most prolific ever — flatly refused to "
                        "accept the answer until a colleague showed him a computer simulation. Even genius "
                        "intuition breaks on this one.",
        "source": ("Wikipedia — <i>Monty Hall problem</i>", "https://en.wikipedia.org/wiki/Monty_Hall_problem"),
        "next": "Try the 100-door version in your head — it makes the 2/3 logic feel obvious.",
    },
    {
        "id": "survivorship-bias",
        "emoji": "✈️",
        "accent": "#5b9bf0",
        "title": "The Bullet Holes That Weren't There",
        "subtitle": "A WWII statistician saw what everyone else missed — and it will change how you read every success story.",
        "minutes": 5,
        "hero_article": "Survivorship bias",
        "lead": "In World War II, the military studied bombers returning from raids to decide where to "
                "add armour. The planes came back peppered with bullet holes — concentrated on the "
                "wings and tail. Obvious answer: armour the wings and tail. A quiet mathematician "
                "named Abraham Wald said no — and his reasoning is a lens you'll never un-see.",
        "sections": [
            ("Armour where the holes aren't",
             "<p>Wald pointed out the fatal flaw: they were only looking at the planes that "
             "<i>returned</i>. The bullet holes showed where a bomber could be hit and still survive. "
             "The planes hit in the other places — the engines, the cockpit — never came back to be "
             "studied. So the armour belonged exactly where the survivors showed <b>no</b> damage.</p>"
             "<p>The data wasn't lying. It was just missing everyone who didn't make it.</p>",
             "Abraham Wald"),
            ("The trap is everywhere",
             "<p>Once you see it, you see it constantly. 'Successful founders dropped out of college' "
             "— but we never count the thousands who dropped out and failed. 'Old buildings were "
             "built better' — no, the badly-built old ones already collapsed. Every time you study "
             "only the winners, you learn the wrong lesson. Always ask: <i>who is missing from this "
             "data?</i></p>",
             None),
        ],
        "ideas": [
            ("Survivorship bias", "Drawing conclusions only from the things that 'survived', ignoring the rest."),
            ("Silent evidence", "The failures that never show up in your data — and quietly distort it."),
            ("Selection effect", "When how you gathered the data secretly shapes the answer."),
            ("Wald's question", "'What's invisible here because it didn't survive to be counted?'"),
        ],
        "game": {
            "type": "ponder",
            "prompt": "A magazine finds that 8 of 10 top CEOs wake at 5am, and concludes early rising "
                      "causes success. What did they forget to measure? Think, then reveal.",
            "reveal": "Everyone who woke at 5am and <i>didn't</i> become a CEO — almost certainly millions "
                      "of them. Without the failures, '5am → success' is survivorship bias. The honest "
                      "question is: of all early risers, what fraction succeed, versus late risers? Only "
                      "then can you tell if the alarm clock matters at all.",
        },
        "did_you_know": "Wald's wartime group at Columbia did its work in secret; only decades later was his "
                        "armour analysis declassified. His method now underlies how we estimate aircraft "
                        "vulnerability to this day.",
        "source": ("Wikipedia — <i>Survivorship bias</i> & Abraham Wald", "https://en.wikipedia.org/wiki/Survivorship_bias"),
        "next": "For a week, when you hear a success rule, ask out loud: 'where are the failures?'",
    },
    {
        "id": "why-we-sleep",
        "emoji": "😴",
        "accent": "#7c6bf0",
        "title": "What Your Brain Does While You Sleep",
        "subtitle": "Sleep isn't downtime — it's when your brain files memories and literally washes itself.",
        "minutes": 5,
        "hero_article": "Sleep",
        "lead": "You spend about a third of your life unconscious, and for centuries we assumed it was "
                "wasted time. It's the opposite. While you sleep, your brain runs maintenance no "
                "waking moment can spare — sorting the day's memories and flushing out literal "
                "waste. Skip it, and you pay in ways you can't feel until it's too late.",
        "sections": [
            ("Sleep saves your memories",
             "<p>During deep sleep your brain replays the day and moves fragile new memories into "
             "long-term storage — a process called <b>consolidation</b>. This is why an all-nighter "
             "before an exam backfires: you trade the very hours your brain needs to <i>keep</i> "
             "what you studied. Learn, then sleep, and you remember more than if you'd kept "
             "grinding.</p>",
             "Memory consolidation"),
            ("Your brain takes out the trash",
             "<p>In 2013 scientists found the <b>glymphatic system</b>: during sleep, channels around "
             "your brain cells open up and cerebrospinal fluid rinses through, clearing metabolic "
             "waste — including the proteins linked to Alzheimer's. Your brain has a cleaning cycle, "
             "and it only runs the night shift.</p>",
             "Glymphatic system"),
            ("The cost you can't feel",
             "<p>The cruel part: after a night or two of short sleep, you <i>feel</i> adjusted while "
             "your reaction time, judgement, and mood keep degrading. Subjectively fine, objectively "
             "impaired. The fix isn't heroics — it's protecting a boring, consistent 7–9 hours.</p>",
             None),
        ],
        "ideas": [
            ("Consolidation", "Deep sleep moving fresh memories into durable long-term storage."),
            ("Glymphatic system", "The brain's waste-clearing 'plumbing' that runs mainly during sleep."),
            ("Sleep debt", "Accumulated lost sleep — it adds up and doesn't fully forgive."),
            ("Subjective adaptation", "Feeling fine while staying measurably impaired on too little sleep."),
        ],
        "game": {
            "type": "ponder",
            "prompt": "It's 1am before a big exam. You can study two more hours, or sleep them. Which "
                      "actually scores you more marks tomorrow? Decide, then reveal.",
            "reveal": "Sleep — in most cases. Those two hours of deep sleep are when your brain locks in "
                      "what you already studied, and a rested brain recalls and reasons far better under "
                      "pressure. Cramming adds a little fragile new material at the cost of consolidating "
                      "everything else. Study earlier; protect the sleep.",
        },
        "did_you_know": "Newborns sleep up to 17 hours a day, and spend most of it in REM — the dreaming "
                        "stage thought to wire up the developing brain. We dream most intensely when we "
                        "have the most to learn.",
        "source": ("Matthew Walker — <i>Why We Sleep</i> (read critically; some specifics are debated)", "https://en.wikipedia.org/wiki/Why_We_Sleep"),
        "next": "Pick a fixed wake-up time for the next 7 days — consistency matters more than any trick.",
    },
]


def load_generated_lessons() -> list[dict[str, Any]]:
    try:
        data = json.loads(GENERATED_LESSONS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []
    lessons = data.get("lessons", data) if isinstance(data, dict) else data
    if not isinstance(lessons, list):
        return []
    out: list[dict[str, Any]] = []
    required = {
        "id", "emoji", "accent", "title", "subtitle", "minutes", "lead",
        "sections", "ideas", "game", "did_you_know", "source",
    }
    for lesson in lessons:
        if isinstance(lesson, dict) and required.issubset(lesson):
            out.append(lesson)
    return out


def lesson_library() -> list[dict[str, Any]]:
    by_id = {lesson["id"]: lesson for lesson in LESSONS}
    for lesson in DEEP_LESSONS:
        by_id[lesson["id"]] = lesson
    for lesson in CURRICULUM_LESSONS:
        by_id[lesson["id"]] = lesson
    for lesson in load_generated_lessons():
        by_id[lesson["id"]] = lesson
    return list(by_id.values())


# --------------------------------------------------------------------------- #
# Styling + behaviour (one stylesheet + one script powers every lesson).
# --------------------------------------------------------------------------- #
BASE_CSS = """
:root{--bg:#0b0f0d;--card:#121b16;--line:#22352b;--fg:#eaf6ef;--muted:#8fae9f;--accent:#46d17a}
*{box-sizing:border-box}
html,body{width:100%;max-width:100%;overflow-x:hidden}
body{margin:0;font-family:Georgia,'Iowan Old Style',serif;background:var(--bg);color:var(--fg);line-height:1.72;-webkit-text-size-adjust:100%}
.wrap{max-width:720px;width:100%;margin:0 auto;padding:0 20px 110px;overflow:hidden}
.topbar{position:sticky;top:0;background:rgba(11,15,13,.92);backdrop-filter:blur(8px);display:flex;justify-content:space-between;align-items:center;padding:12px 0;font:600 13px/1 system-ui;z-index:9}
.topbar a{color:var(--muted);text-decoration:none}
.herowrap{display:none}
.herowrap img,.herowrap svg{display:block;width:100%;height:240px;object-fit:cover}
.credit{position:absolute;right:8px;bottom:8px;font:500 11px/1.2 system-ui;color:#eaffef;background:rgba(0,0,0,.45);padding:3px 8px;border-radius:7px;max-width:70%;text-align:right}
.kicker{font:700 12px/1 system-ui;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin:22px 0 6px}
h1{font-size:36px;line-height:1.12;margin:.1em 0 .15em}
.sub{color:var(--muted);font-size:19px;margin:0}
.meta{font:600 13px/1 system-ui;color:var(--muted);display:flex;gap:16px;margin:14px 0 20px;flex-wrap:wrap}
.lead{font-size:20px}
.lead::first-letter{font-size:inherit;float:none;line-height:inherit;padding:0;color:inherit;font-weight:inherit}
.sub,.lead,p,h1,.sec h3,.meta{max-width:100%;overflow-wrap:anywhere;word-break:break-word}
.sec{margin:30px 0}
.sec h3{font-size:24px;margin:0 0 10px}
.fig{margin:14px 0;border-radius:16px;overflow:hidden;border:1px solid var(--line);background:var(--card);position:relative}
.fig img{display:block;width:100%;max-height:360px;object-fit:cover}
p{margin:0 0 16px;font-size:18px}
@media(min-width:640px){
 .sec.withimg{display:grid;grid-template-columns:1fr 280px;gap:24px;align-items:start}
 .sec.withimg.alt{grid-template-columns:280px 1fr}
 .sec.withimg.alt .txt{order:2}
 .sec.withimg .fig{margin:6px 0}
 .sec.withimg .fig img{height:220px}
}
@media(max-width:640px){.wrap{width:100vw;max-width:100vw;padding:0 16px 110px}.topbar{position:static;justify-content:flex-start;gap:12px;flex-wrap:wrap}.topbar span{flex-basis:100%;color:var(--muted)}h1{font-size:24px;line-height:1.12;width:100%;max-width:100%;overflow-wrap:anywhere;word-break:break-word}.sec h3{font-size:22px;width:100%;max-width:100%;overflow-wrap:anywhere;word-break:break-word}.sub,.lead,p{display:block;width:100%;max-width:100%;overflow-wrap:anywhere;word-break:break-word}.lead::first-letter{font-size:inherit;float:none;line-height:inherit;padding:0;color:inherit;font-weight:inherit}.meta{width:100%;max-width:100%;overflow-wrap:anywhere}}
.ideas{border:1px solid var(--line);border-radius:18px;background:var(--card);padding:6px 20px 14px;margin:24px 0}
.ideas h4{font:700 12px/1 system-ui;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);margin:16px 0 4px}
.ideas dl{margin:0}
.ideas dt{font-weight:700;margin-top:12px;font-size:18px}
.ideas dd{margin:2px 0 0;color:#cfe7da;font-size:17px}
.game{border:1px solid var(--line);border-radius:14px;background:var(--card);padding:20px;margin:30px 0}
.game .tag{font:700 12px/1 system-ui;letter-spacing:.12em;text-transform:uppercase;color:var(--muted)}
.gprompt{font-size:19px;font-weight:700;margin:8px 0 14px}
.olist{list-style:none;margin:0;padding:0}
.olist li{display:flex;align-items:center;justify-content:space-between;gap:10px;background:#0b130f;border:1px solid var(--line);border-radius:12px;padding:11px 12px;margin:8px 0;font:600 17px system-ui}
.olist .ctrl{display:flex;flex:none}
.olist .ctrl button{font:700 17px/1 system-ui;background:none;border:1px solid var(--line);color:var(--accent);border-radius:9px;width:38px;height:38px;margin-left:6px;cursor:pointer}
.gin{width:100%;font:inherit;font-size:18px;border:1px solid var(--line);background:#0b130f;color:var(--fg);border-radius:12px;padding:13px;margin:2px 0 4px}
.check{font:700 15px/1 system-ui;background:var(--fg);color:var(--bg);border:none;border-radius:10px;padding:13px 18px;cursor:pointer;margin-top:8px}
.gresult{margin-top:14px;font-family:system-ui;font-size:16px;line-height:1.6;color:#cfe7da;display:none}
.gresult.show{display:block}
.gresult .ok{color:var(--accent);font-weight:700}
.gresult .no{color:#ff9b8a;font-weight:700}
.reveal{border:1px dashed #2c5e44;border-radius:14px;padding:14px 18px;background:#0b130f;margin:20px 0}
.reveal button{font:700 14px/1.3 system-ui;background:none;border:none;color:var(--fg);cursor:pointer;padding:0;text-align:left}
.reveal .txt{display:none;margin-top:10px;color:#cfe7da;font-size:17px}
.reveal.show .txt{display:block}
.foot{margin-top:34px;padding-top:18px;border-top:1px solid var(--line);font-family:system-ui;color:var(--muted);font-size:15px}
.foot a{color:var(--accent)}
.pill{display:inline-block;font:700 12px/1 system-ui;color:var(--fg);background:transparent;border:1px solid var(--line);border-radius:999px;padding:6px 11px}
.playcta{display:flex;align-items:center;gap:14px;text-decoration:none;color:var(--fg);border:1px solid var(--line);border-radius:14px;padding:18px;margin:24px 0 4px;background:var(--card)}
.playcta .pc_k{font:800 12px/1 system-ui;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.playcta .pc_t{font:800 21px/1.1 system-ui;margin:6px 0 3px}
.playcta .pc_s{font:600 14px/1.3 system-ui;color:var(--muted)}
.playcta .pc_go{margin-left:auto;font-size:24px;color:var(--muted)}
/* --- playable games --- */
.pd-scores,.monty-stats{display:flex;gap:18px;font:700 15px/1 system-ui;margin:4px 0 12px;flex-wrap:wrap}
.pd-scores b,.monty-stats b{color:var(--accent)}
.pd-log{font:600 13.5px/1.6 ui-monospace,Menlo,Consolas,monospace;background:#0b130f;border:1px solid var(--line);border-radius:12px;padding:8px 12px;margin:8px 0;max-height:210px;overflow:auto;min-height:26px;color:#bfe6d2}
.pd-log .row{display:flex;justify-content:space-between;gap:12px}
.pd-log .plus{color:var(--accent)}.pd-log .zero{color:#ff9b8a}
.pd-controls,.monty-actions{display:flex;gap:10px;flex-wrap:wrap}
.pd-controls button,.monty-actions button,.pd-reset,.monty-next{flex:1;min-width:130px;font:700 16px/1 system-ui;border:1px solid var(--line);background:#0b130f;color:var(--fg);border-radius:12px;padding:14px;cursor:pointer}
.pd-controls .coop:hover,.monty-actions .switch:hover{border-color:var(--accent)}
.pd-controls .cheat:hover{border-color:#ff9b8a}
.pd-reset,.monty-next{margin-top:10px;width:100%}
button:disabled{opacity:.5}
.doors{display:flex;gap:10px;margin:12px 0}
.door{flex:1;font-size:46px;line-height:1;background:#0b130f;border:2px solid var(--line);border-radius:14px;padding:16px 0;cursor:pointer;transition:.15s}
.door:hover{border-color:var(--accent)}
.door.picked{border-color:var(--fg);box-shadow:none}
.door.open{opacity:.8}
.monty-msg{font:600 16px/1.4 system-ui;margin:10px 0;color:#cfe7da}
"""

BASE_JS = """
// reorder game
document.querySelectorAll('.game.order').forEach(function(g){
  var list=g.querySelector('.olist');
  list.addEventListener('click',function(e){
    var b=e.target.closest('button'); if(!b)return; var li=b.closest('li');
    if(b.classList.contains('up')&&li.previousElementSibling){list.insertBefore(li,li.previousElementSibling);}
    if(b.classList.contains('dn')&&li.nextElementSibling){list.insertBefore(li.nextElementSibling,li);}
  });
  g.querySelector('.check').addEventListener('click',function(){
    var ids=Array.prototype.map.call(list.querySelectorAll('li'),function(li){return li.dataset.id;});
    var ok=ids.join(',')===g.dataset.correct;
    var r=g.querySelector('.gresult');
    r.querySelector('.status').innerHTML=ok?"<span class='ok'>Nailed it. </span>":"<span class='no'>Not quite. </span>";
    r.classList.add('show');
  });
});
// estimate game
document.querySelectorAll('.game.estimate').forEach(function(g){
  g.querySelector('.check').addEventListener('click',function(){
    var ans=parseFloat(g.dataset.answer), v=parseFloat(g.querySelector('.gin').value), s='';
    if(!isNaN(v)&&v>0){var f=v>ans?v/ans:ans/v;
      s=f<2?"<span class='ok'>Spot on — within 2×. </span>":f<10?"<span class='ok'>Solid Fermi range — within 10×. </span>":"<span class='no'>Off by more than 10×. </span>";}
    var r=g.querySelector('.gresult'); r.querySelector('.status').innerHTML=s; r.classList.add('show');
  });
});
// ponder
document.querySelectorAll('.game.ponder .check').forEach(function(b){
  b.addEventListener('click',function(){b.closest('.game').querySelector('.gresult').classList.add('show');});
});
// Iterated Prisoner's Dilemma vs Tit-for-Tat
document.querySelectorAll('.game.pd').forEach(function(g){
  var rounds=parseInt(g.dataset.rounds)||8;
  var you,opp,r,oppNext,over;
  var elYou=g.querySelector('.you'),elOpp=g.querySelector('.opp'),elR=g.querySelector('.rnd');
  var log=g.querySelector('.pd-log'),res=g.querySelector('.gresult'),reset=g.querySelector('.pd-reset');
  var coop=g.querySelector('.coop'),cheat=g.querySelector('.cheat');
  function pay(a,b){if(a==='C'&&b==='C')return[3,3];if(a==='C'&&b==='D')return[0,5];if(a==='D'&&b==='C')return[5,0];return[1,1];}
  function init(){you=0;opp=0;r=1;oppNext='C';over=false;log.innerHTML='';elYou.textContent=0;elOpp.textContent=0;elR.textContent=1;coop.disabled=false;cheat.disabled=false;reset.style.display='none';res.classList.remove('show');}
  function play(me){
    if(over)return; var them=oppNext, p=pay(me,them); you+=p[0]; opp+=p[1]; oppNext=me;
    var row=document.createElement('div'); row.className='row';
    row.innerHTML="<span>R"+r+":  you "+(me==='C'?'🤝':'😈')+"   "+(them==='C'?'🤝':'😈')+" them</span><span class='"+(p[0]>=p[1]?'plus':'zero')+"'>+"+p[0]+" / +"+p[1]+"</span>";
    log.appendChild(row); log.scrollTop=log.scrollHeight;
    r++; elYou.textContent=you; elOpp.textContent=opp; elR.textContent=Math.min(r,rounds);
    if(r>rounds){over=true;coop.disabled=true;cheat.disabled=true;reset.style.display='';
      var v=you>opp?"<span class='ok'>You edged ahead — but look how. </span>":you===opp?"<span class='ok'>Dead even. </span>":"<span class='no'>Tit-for-Tat beat you. </span>";
      res.querySelector('.status').innerHTML=v+"Final score "+you+"–"+opp+". ";res.classList.add('show');
    }
  }
  coop.addEventListener('click',function(){play('C');});
  cheat.addEventListener('click',function(){play('D');});
  reset.addEventListener('click',init);
  init();
});
// Monty Hall
document.querySelectorAll('.game.monty').forEach(function(g){
  var doors=g.querySelectorAll('.door'),msg=g.querySelector('.monty-msg');
  var actions=g.querySelector('.monty-actions'),nextBtn=g.querySelector('.monty-next');
  var stay=g.querySelector('.stay'),sw=g.querySelector('.switch');
  var swEl=g.querySelector('.sw'),stEl=g.querySelector('.st'),res=g.querySelector('.gresult');
  var swWin=0,swTot=0,stWin=0,stTot=0,car,pick,opened,phase;
  function reset(){car=Math.floor(Math.random()*3);pick=null;opened=null;phase='pick';
    doors.forEach(function(d){d.textContent='🚪';d.disabled=false;d.className='door';});
    msg.textContent='Pick a door — one hides a car, two hide goats.';actions.style.display='none';nextBtn.style.display='none';}
  doors.forEach(function(d){d.addEventListener('click',function(){
    if(phase!=='pick')return; pick=parseInt(d.dataset.i); d.classList.add('picked');
    var opts=[0,1,2].filter(function(i){return i!==pick&&i!==car;});
    opened=opts[Math.floor(Math.random()*opts.length)];
    doors[opened].textContent='🐐';doors[opened].classList.add('open');doors[opened].disabled=true;
    phase='decide';msg.textContent='Door '+(opened+1)+' was a goat. Now: stay with door '+(pick+1)+', or switch?';
    actions.style.display='flex';
  });});
  function finish(final,switched){phase='done';actions.style.display='none';
    doors.forEach(function(d,i){d.disabled=true;if(i!==opened)d.textContent=(i===car?'🚗':'🐐');});
    var win=(final===car);
    if(switched){swTot++;if(win)swWin++;}else{stTot++;if(win)stWin++;}
    swEl.textContent=swWin+'/'+swTot;stEl.textContent=stWin+'/'+stTot;
    msg.innerHTML=win?"<b style='color:var(--accent)'>🚗 You won the car!</b>":"<b style='color:#ff9b8a'>🐐 Goat. Bad luck.</b>";
    nextBtn.style.display='';res.classList.add('show');
  }
  stay.addEventListener('click',function(){finish(pick,false);});
  sw.addEventListener('click',function(){finish([0,1,2].filter(function(i){return i!==pick&&i!==opened;})[0],true);});
  nextBtn.addEventListener('click',reset);
  reset();
});
// did-you-know reveal
document.querySelectorAll('.reveal button').forEach(function(b){
  b.addEventListener('click',function(){b.parentElement.classList.toggle('show');});
});
"""


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #
def esc(s: Any) -> str:
    return html.escape(str(s if s is not None else ""))


def _fig(article: str | None) -> str:
    if not article:
        return ""
    uri, credit = wiki_photo(article, width=700)
    if not uri:
        return ""
    return (f"<figure class='fig'><img loading='lazy' src='{uri}' alt='{esc(article)}'>"
            f"<figcaption class='credit'>{esc(credit)}</figcaption></figure>")


def _sections_html(sections: list) -> str:
    out = []
    img_index = 0
    for heading, body, article in sections:
        fig = _fig(article)
        if fig:
            alt = " alt" if img_index % 2 else ""
            img_index += 1
            out.append(
                f"<section class='sec withimg{alt}'><div class='txt'><h3>{esc(heading)}</h3>{body}</div>{fig}</section>"
            )
        else:
            out.append(f"<section class='sec'><h3>{esc(heading)}</h3>{body}</section>")
    return "".join(out)


def _ideas_html(ideas: list) -> str:
    rows = "".join(f"<dt>{esc(t)}</dt><dd>{esc(d)}</dd>" for t, d in ideas)
    return f"<div class='ideas'><h4>Key ideas to keep</h4><dl>{rows}</dl></div>"


def _game_html(game: dict) -> str:
    gtype = game["type"]
    prompt = esc(game["prompt"])
    if gtype == "order":
        items = list(game.get("items", []))
        lis = "".join(f"<li>{esc(i[1])}</li>" for i in items)
        explain = game.get("explain", "Question the chain before you memorize it.")
        reveal = (
            f"<b>Source chain to interrogate:</b><ol>{lis}</ol>"
            f"<p>{explain}</p>"
            "<p><b>Do not just order dates.</b> Ask which link is causal, which is only correlation, "
            "which actor would disagree, and what evidence would change your mind.</p>"
        )
        return (f"<div id='game' class='game ponder'>"
                f"<div class='tag'>🎮 Challenge · question the model</div><div class='gprompt'>{prompt}</div>"
                f"<button class='check'>Show the source chain</button>"
                f"<div class='gresult'><span class='status'></span> <span class='detail'>{reveal}</span></div></div>")
    if gtype == "estimate":
        detail = f"Answer: <b>{esc(game['answer'])} {esc(game['unit'])}</b>. {game['reveal']}"
        return (f"<div id='game' class='game estimate' data-answer='{esc(game['answer'])}'>"
                f"<div class='tag'>🎮 Challenge · estimate</div><div class='gprompt'>{prompt}</div>"
                f"<input class='gin' type='number' inputmode='numeric' placeholder='Your reasoned guess'>"
                f"<button class='check'>Reveal</button>"
                f"<div class='gresult'><span class='status'></span> <span class='detail'>{detail}</span></div></div>")
    if gtype == "pd":
        rounds = int(game.get("rounds", 8))
        opp = esc(game.get("opponent", "Tit-for-Tat"))
        return (f"<div id='game' class='game pd' data-rounds='{rounds}'>"
                f"<div class='tag'>🎮 Play · Prisoner's Dilemma</div><div class='gprompt'>{prompt}</div>"
                f"<div class='pd-scores'><span>You <b class='you'>0</b></span>"
                f"<span>{opp} <b class='opp'>0</b></span><span>Round <b class='rnd'>1</b>/{rounds}</span></div>"
                f"<div class='pd-log'></div>"
                f"<div class='pd-controls'><button class='coop'>🤝 Cooperate</button>"
                f"<button class='cheat'>😈 Cheat</button></div>"
                f"<button class='pd-reset' style='display:none'>Play again</button>"
                f"<div class='gresult'><span class='status'></span> <span class='detail'>{game['reveal']}</span></div></div>")
    if gtype == "monty":
        return ("<div id='game' class='game monty'>"
                f"<div class='tag'>🎮 Play · Monty Hall</div><div class='gprompt'>{prompt}</div>"
                "<div class='monty-stats'>Switched <b class='sw'>0/0</b> · Stayed <b class='st'>0/0</b></div>"
                "<div class='doors'><button class='door' data-i='0'>🚪</button>"
                "<button class='door' data-i='1'>🚪</button><button class='door' data-i='2'>🚪</button></div>"
                "<div class='monty-msg'>Pick a door.</div>"
                "<div class='monty-actions' style='display:none'><button class='stay'>Stay</button>"
                "<button class='switch'>Switch</button></div>"
                "<button class='monty-next' style='display:none'>Next round</button>"
                f"<div class='gresult'><span class='status'></span> <span class='detail'>{game['reveal']}</span></div></div>")
    # ponder
    return (f"<div id='game' class='game ponder'>"
            f"<div class='tag'>🎮 Challenge · think it through</div><div class='gprompt'>{prompt}</div>"
            f"<button class='check'>Reveal the answer</button>"
            f"<div class='gresult'><span class='status'></span> <span class='detail'>{game['reveal']}</span></div></div>")


def _hero_html(lesson: dict) -> str:
    uri, credit = wiki_photo(lesson["hero_article"], width=1000) if lesson.get("hero_article") else (None, "")
    if uri:
        return (f"<div class='herowrap'><img src='{uri}' alt='{esc(lesson['title'])}'>"
                f"<div class='credit'>{esc(credit)}</div></div>")
    return f"<div class='herowrap'>{_svg_hero(lesson['accent'], lesson['emoji'])}</div>"


def _play_cta(lesson_id: str) -> str:
    """End-of-lesson call to action: now that you've learned it, play to lock it in."""
    g = GAME_FOR_LESSON.get(lesson_id)
    if not g:
        return ""
    url = g.get("url") or f"/output/learn/{g['id']}.html"
    return (
        f"<a class='playcta' href='{esc(url)}' style='--c:{g['accent']}'>"
        f"<div class='pc_txt'><div class='pc_k'>🎮 You've learned it — now lock it in</div>"
        f"<div class='pc_t'>Play {esc(g['emoji'])} {esc(g['title'])}</div>"
        f"<div class='pc_s'>Reinforce it through play — beats scrolling the feed.</div></div>"
        f"<div class='pc_go'>▶</div></a>"
    )


PROGRESS_JS = r"""
(function(){
const KEY='lifeos.learning.progress.v1';
const node=window.LIFEOS_NODE;
const tg=window.Telegram&&window.Telegram.WebApp?window.Telegram.WebApp:null;
if(tg){try{tg.ready();tg.expand();tg.MainButton.setText('Lock into graph');tg.MainButton.show();}catch(e){}}
function load(){try{return JSON.parse(localStorage.getItem(KEY)||'{}')}catch{return {}}}
function save(p){localStorage.setItem(KEY,JSON.stringify(p))}
function xp(p){return Object.values(p.done||{}).reduce((s,n)=>s+(+n.xp||0),0)}
function level(x){return x>=1440?4:(x>=720?3:(x>=240?2:1))}
function award(id,title,kind,xpValue){
 const p=load();p.done=p.done||{};
 if(!p.done[id])p.done[id]={at:new Date().toISOString(),title,xp:xpValue,kind};
 save(p);return p;
}
async function syncProgress(){
 if(!tg||!tg.initData||!node)return;
 try{
  const r=await fetch('/api/progress',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({lesson_id:node.id,node_id:node.id,score:100,result:'complete',initData:tg.initData})});
  const data=await r.json();
  if(data&&data.ok){document.querySelectorAll('[data-lifeos-level]').forEach(el=>el.textContent='Level '+data.level+' / '+data.total_xp+' XP');try{tg.HapticFeedback.notificationOccurred('success');tg.MainButton.setText('Saved to graph');}catch(e){}}
  else if(data&&!data.ok){try{tg.HapticFeedback.notificationOccurred('error');}catch(e){}}
 }catch(e){try{tg.HapticFeedback.notificationOccurred('error');}catch(_){}}
}
function update(){
 const p=load(),done=!!(p.done&&node&&p.done[node.id]),total=xp(p);
 document.querySelectorAll('[data-lifeos-level]').forEach(el=>el.textContent='Level '+level(total)+' / '+total+' XP');
 document.querySelectorAll('[data-complete-node]').forEach(btn=>{
  btn.textContent=done?'Completed':'Mark complete + '+node.xp+' XP';
  btn.disabled=done;
 });
}
document.querySelectorAll('[data-complete-node]').forEach(btn=>btn.addEventListener('click',()=>{
 if(!node)return;award(node.id,node.title,node.kind,node.xp);update();syncProgress();
}));
if(tg){try{tg.MainButton.onClick(()=>{if(!node)return;award(node.id,node.title,node.kind,node.xp);update();syncProgress();});}catch(e){}}
update();
})();
"""


HIGHLIGHT_JS = r"""
(function(){
const root=document.querySelector('[data-highlight-root]');
const node=window.LIFEOS_NODE||{};
if(!root)return;
const key='lifeos.highlights.v1.'+(node.id||location.pathname);
const bar=document.createElement('div');
bar.className='hlbar';
bar.innerHTML='<button type="button" data-hl-add>Highlight</button><button type="button" data-hl-clear>Clear</button>';
document.body.appendChild(bar);
let savedRange=null;
function hide(){bar.classList.remove('show')}
function usableSelection(){
 const sel=window.getSelection();
 if(!sel||sel.isCollapsed||sel.rangeCount===0)return null;
 const range=sel.getRangeAt(0);
 if(!root.contains(range.commonAncestorContainer))return null;
 const text=String(sel).trim();
 if(text.length<2)return null;
 return range;
}
function place(){
 const range=usableSelection();
 if(!range){hide();return}
 savedRange=range.cloneRange();
 const rect=range.getBoundingClientRect();
 if(!rect||(!rect.width&&!rect.height)){hide();return}
 bar.style.left=Math.max(10,Math.min(window.innerWidth-170,rect.left+rect.width/2-70))+'px';
 bar.style.top=Math.max(10,rect.top-46)+'px';
 bar.classList.add('show');
}
function skipNode(n){
 const p=n.parentElement;
 return !p||p.closest('mark.user-highlight,button,a,script,style,.hlbar');
}
function textNodes(){
 const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT,{acceptNode(n){return skipNode(n)?NodeFilter.FILTER_REJECT:NodeFilter.FILTER_ACCEPT}});
 const out=[];let n;while((n=walker.nextNode()))out.push(n);return out;
}
function unwrap(mark){
 const parent=mark.parentNode;
 while(mark.firstChild)parent.insertBefore(mark.firstChild,mark);
 parent.removeChild(mark);
 parent.normalize();
}
function save(){
 const items=[...root.querySelectorAll('mark.user-highlight')].map(m=>m.textContent.trim()).filter(Boolean).slice(0,200);
 localStorage.setItem(key,JSON.stringify(items));
}
function highlightRange(range){
 const mark=document.createElement('mark');
 mark.className='user-highlight';
 mark.dataset.userHighlight='1';
 mark.appendChild(range.extractContents());
 range.insertNode(mark);
 mark.normalize();
 save();
}
function restoreOne(text){
 if(!text||text.length<2)return false;
 for(const n of textNodes()){
  const i=n.nodeValue.indexOf(text);
  if(i<0)continue;
  const r=document.createRange();
  r.setStart(n,i);r.setEnd(n,i+text.length);
  highlightRange(r);
  return true;
 }
 return false;
}
function restore(){
 let items=[];try{items=JSON.parse(localStorage.getItem(key)||'[]')}catch{}
 if(Array.isArray(items))items.forEach(restoreOne);
}
bar.querySelector('[data-hl-add]').addEventListener('click',()=>{
 if(!savedRange)return hide();
 try{highlightRange(savedRange)}catch(e){}
 window.getSelection()?.removeAllRanges();
 hide();
});
bar.querySelector('[data-hl-clear]').addEventListener('click',()=>{
 root.querySelectorAll('mark.user-highlight').forEach(unwrap);
 localStorage.removeItem(key);
 window.getSelection()?.removeAllRanges();
 hide();
});
root.addEventListener('mouseup',()=>setTimeout(place,0));
root.addEventListener('touchend',()=>setTimeout(place,80),{passive:true});
document.addEventListener('selectionchange',()=>{if(!usableSelection())hide()});
window.addEventListener('scroll',hide,{passive:true});
restore();
})();
"""



def _source_entries(lesson: dict[str, Any]) -> list[tuple[str, str, str]]:
    """Return unique (label, url, note) entries for the bottom source trail."""
    entries: list[tuple[str, str, str]] = []

    def add(raw: Any) -> None:
        label = url = note = ""
        if isinstance(raw, dict):
            url = str(raw.get("url") or "").strip()
            label = str(raw.get("label") or raw.get("title") or url or "Source").strip()
            note = str(raw.get("note") or "").strip()
        elif isinstance(raw, (list, tuple)) and len(raw) >= 2:
            label = str(raw[0] or "Source").strip()
            url = str(raw[1] or "").strip()
        if url and (url.startswith("http://") or url.startswith("https://")):
            key = url.rstrip("/")
            if key not in {u.rstrip("/") for _, u, _ in entries}:
                entries.append((label or url, url, note))

    for raw in lesson.get("sources") or []:
        add(raw)
    add(lesson.get("source"))
    return entries


def _source_trail_html(lesson: dict[str, Any]) -> str:
    sources = _source_entries(lesson)
    if not sources:
        return ""
    rows = []
    for label, url, note in sources:
        note_html = f"<span>{esc(note)}</span>" if note else ""
        rows.append(
            f"<li><a href='{esc(url)}' target='_blank' rel='noopener noreferrer'>{esc(label)}</a>{note_html}</li>"
        )
    return (
        "<section class='sourceTrail'><h3>Sources and further reading</h3>"
        "<p>These are the links used as the evidence trail for this page. Treat the lesson as a map, then open the sources when a claim matters.</p>"
        f"<ul>{''.join(rows)}</ul></section>"
    )


def _thinking_questions_html(lesson: dict[str, Any]) -> str:
    meta = lesson.get("curriculum") or {}
    specific = list(meta.get("thinking_questions") or lesson.get("thinking_questions") or lesson.get("questions") or [])
    title = str(lesson.get("title") or "this idea")
    generic = [
        f"What is the strongest claim in {title}, and what evidence would actually support it?",
        "Which part is fact, which part is interpretation, and which part is analogy?",
        "What would a smart skeptic say is missing, overstated, or backwards?",
        "What would change your mind after reading the linked sources?",
        "Where would applying this idea to your life or work become dangerous?",
    ]
    questions: list[str] = []
    for q in specific + generic:
        q = str(q).strip()
        if q and q not in questions:
            questions.append(q)
        if len(questions) >= 7:
            break
    items = "".join(f"<li>{esc(q)}</li>" for q in questions)
    return (
        "<section class='questionBlock'><h3>Questions worth arguing with</h3>"
        "<p>Do not memorize this as trivia. Use these to test the claim, the evidence, and your own assumptions.</p>"
        f"<ul>{items}</ul></section>"
    )


def _reading_note_html(lesson: dict[str, Any]) -> str:
    return (
        "<section class='readingNote'><h3>How to read this page</h3>"
        "<p>Read it as a set of claims, not as sacred text. First get the model. Then check the source trail. "
        "Select any sentence to highlight it; use Clear to remove saved highlights for this page. "
        "Finally, write one objection, one application, and one uncertainty you would need to verify before teaching it to someone else.</p>"
        "</section>"
    )

def _domain_companion_lens(domain: str) -> tuple[str, str, str]:
    domain = domain.lower()
    if domain in {"history", "statecraft"}:
        return (
            "timeline, incentives, institutions, and source bias",
            "Ask who benefits, what changed before/after, and which later story is being projected backward.",
            "Draw the chain: pressure → decision → unintended consequence → new institution.",
        )
    if domain in {"math", "physics", "invention"}:
        return (
            "definitions, mechanism, model limits, and worked examples",
            "Do not stop at the formula or name. Track what each variable means and where the model breaks.",
            "Draw the system: inputs → transformation → output → failure mode.",
        )
    if domain == "startup":
        return (
            "customer behavior, incentives, distribution, and founder tradeoffs",
            "Turn the essay into an operating rule, then name when following it would hurt you.",
            "Draw the loop: user pain → wedge → feedback → growth or churn.",
        )
    if domain == "thinking":
        return (
            "claims, assumptions, counterexamples, and transfer",
            "Separate the argument from the metaphor. Then test the argument on a different domain.",
            "Draw the argument: premise → inference → objection → revised belief.",
        )
    return (
        "claims, evidence, mechanism, and application",
        "Read for the structure underneath the facts, not just the facts themselves.",
        "Draw the model: source → claim → test → action.",
    )


def _plain_text(value: Any, limit: int = 260) -> str:
    text = re.sub(r"<[^>]+>", " ", str(value or ""))
    text = " ".join(html.unescape(text).split())
    return text[:limit].rstrip()


def _section_records(sections: list[Any]) -> list[tuple[str, str]]:
    records: list[tuple[str, str]] = []
    for raw in sections:
        heading = body = ""
        if isinstance(raw, dict):
            heading = str(raw.get("heading") or raw.get("title") or "Section")
            body = str(raw.get("body") or raw.get("html") or "")
        elif isinstance(raw, (list, tuple)) and len(raw) >= 2:
            heading = str(raw[0])
            body = str(raw[1])
        body = _plain_text(body, 520)
        if heading or body:
            records.append((heading or "Section", body))
    return records


def _source_cards_html(lesson: dict[str, Any]) -> str:
    cards = []
    for label, url, note in _source_entries(lesson)[:6]:
        cards.append(
            f"<a href='{esc(url)}' target='_blank' rel='noopener noreferrer'><b>{esc(label)}</b>"
            f"<span>{esc(note or 'Open this source while reading the companion notes.')}</span></a>"
        )
    if not cards:
        return "<p>No external source link is attached yet. Treat this as a LifeOS original companion and add sources before relying on the claim.</p>"
    return f"<div class='sourceCards'>{''.join(cards)}</div>"


def _custom_companion_html(lesson: dict[str, Any], companion: dict[str, Any]) -> str:
    title = str(lesson.get("title") or "this reading")
    lede = str(companion.get("lede") or "Use this as a close-reading companion for the linked source.")
    sections = [s for s in companion.get("sections", []) if isinstance(s, dict)]
    anchors = [a for a in companion.get("anchors", []) if isinstance(a, dict)]
    sec_html = "".join(
        "<div class='companion-card companion-section'>"
        f"<h3>{esc(item.get('title', 'Reading note'))}</h3>"
        f"<p>{esc(item.get('body', ''))}</p>"
        + ("<ul>" + "".join(f"<li>{esc(x)}</li>" for x in item.get("items", [])[:5]) + "</ul>" if isinstance(item.get("items"), list) and item.get("items") else "")
        + "</div>"
        for item in sections
    )
    anchor_html = "".join(
        f"<div><b>{esc(item.get('label', 'Anchor'))}</b><span>{esc(item.get('note', 'Track this in the source.'))}</span></div>"
        for item in anchors[:8]
    )
    if anchor_html:
        anchor_html = f"<div class='anchorGrid'>{anchor_html}</div>"
    protocol = str(companion.get("source_protocol") or "Read the linked source in order; mark claims, examples, objections, and applications separately.")
    practice = str(companion.get("practice") or (lesson.get("curriculum") or {}).get("practice_prompt") or lesson.get("next") or "Write one concrete application and one fair objection.")
    return f"""
<section class='companion'>
  <div class='companion-k'>Deep source companion</div>
  <h2>Read {esc(title)} without flattening it</h2>
  <p>{esc(lede)}</p>
  <div class='companion-stack'>{sec_html}</div>
  {anchor_html}
  <div class='companion-card'><h3>Source protocol</h3><p>{esc(protocol)}</p>{_source_cards_html(lesson)}</div>
  <div class='companion-card'><h3>Practice</h3><p>{esc(practice)}</p></div>
</section>
"""


def _fallback_anchor_items(lesson: dict[str, Any], records: list[tuple[str, str]]) -> list[tuple[str, str]]:
    ideas = [(str(a), str(b)) for a, b in (lesson.get("ideas") or []) if a]
    if ideas:
        return ideas[:6]
    terms = []
    signals = lesson.get("source_signals") if isinstance(lesson.get("source_signals"), dict) else {}
    if isinstance(signals.get("top_terms"), list):
        terms.extend(str(t) for t in signals["top_terms"][:8])
    for heading, _ in records[:5]:
        for part in re.findall(r"[A-Za-z][A-Za-z-]{3,}", heading):
            if part.lower() not in {"page", "section", "with", "from", "that", "this"}:
                terms.append(part)
    out: list[tuple[str, str]] = []
    for term in terms:
        term = term.strip()
        if term and term.lower() not in {x[0].lower() for x in out}:
            out.append((term, "Track where this term is evidence, mechanism, warning, or application."))
        if len(out) >= 6:
            break
    return out or [("core claim", "State the argument in your own words before accepting the lesson."), ("counterexample", "Name where this advice fails."), ("application", "Turn the model into a concrete next action.")]


def _deep_companion_html(lesson: dict[str, Any]) -> str:
    """Original companion material; linked source text stays linked, not mirrored."""
    custom = lesson.get("deep_companion")
    if isinstance(custom, dict) and (custom.get("sections") or custom.get("anchors") or custom.get("lede")):
        return _custom_companion_html(lesson, custom)

    title = str(lesson.get("title") or "this reading")
    meta = lesson.get("curriculum") or {}
    domain = str(meta.get("domain") or lesson.get("domain") or lesson.get("track") or "general")
    lens, reading_rule, _drawing_rule = _domain_companion_lens(domain)
    records = _section_records(lesson.get("sections") or [])
    walk_rows = "".join(
        f"<li><b>{esc(heading)}</b><span>{esc(body)}</span></li>"
        for heading, body in records[:6]
    ) or "<li><b>Open the source</b><span>Read the linked material in order, then map claims to evidence.</span></li>"
    anchors = _fallback_anchor_items(lesson, records)
    anchor_html = "".join(
        f"<div><b>{esc(label)}</b><span>{esc(note)}</span></div>"
        for label, note in anchors
    )
    practice = str(meta.get("practice_prompt") or lesson.get("next") or "Write one paragraph applying this to a live decision.")
    return f"""
<section class='companion'>
  <div class='companion-k'>Deep source companion</div>
  <h2>Read {esc(title)} without flattening it</h2>
  <p>This companion is meant to keep the source alive, not replace it. Read for <b>{esc(lens)}</b>. {esc(reading_rule)}</p>
  <div class='companion-card'><h3>Argument walkthrough</h3><ol class='walkList'>{walk_rows}</ol></div>
  <div class='companion-card'><h3>Close-reading anchors</h3><div class='anchorGrid'>{anchor_html}</div></div>
  <div class='companion-card'><h3>Source protocol</h3><p>Open the linked sources. For each major claim, separate what the source states, what this lesson infers, and what evidence would change your mind.</p>{_source_cards_html(lesson)}</div>
  <div class='companion-card'><h3>Practice</h3><p>{esc(_plain_text(practice, 500))}</p></div>
</section>
"""


def _curriculum_extra_html(lesson: dict[str, Any]) -> str:
    meta = lesson.get("curriculum")
    if not meta:
        return ""
    questions = meta.get("thinking_questions") or []
    practice = meta.get("practice_prompt") or ""
    parts = ["<div class='curriculum-extra'>"]
    if questions:
        items = "".join(f"<li>{esc(q)}</li>" for q in questions)
        parts.append(
            f"<div class='thinkbox'><h4>Thinking questions</h4><ul>{items}</ul></div>"
        )
    if practice:
        parts.append(
            f"<div class='practicebox'><h4>Practice</h4><p>{esc(practice)}</p></div>"
        )
    if meta.get("collection"):
        parts.append(
            f"<p class='curmeta'>Track: {esc(meta.get('track_name', ''))} · "
            f"{esc(meta['collection'])}</p>"
        )
    parts.append("</div>")
    return "".join(parts)


def render_lesson(lesson: dict[str, Any], day: str) -> str:
    accent = lesson["accent"]
    src_label, src_url = lesson["source"]
    is_curriculum = bool(lesson.get("curriculum"))
    kicker = (
        f"{esc(lesson['emoji'])} Curriculum · Mastery Track"
        if is_curriculum
        else f"{esc(lesson['emoji'])} Morning Lesson"
    )
    progress_node = {
        "id": lesson["id"],
        "title": lesson["title"],
        "kind": "lesson",
        "xp": 120 if is_curriculum else 80,
    }
    curriculum_css = """
.curriculum-extra{margin:24px 0}.thinkbox,.practicebox{border:1px solid var(--line);border-radius:16px;background:var(--card);padding:16px 18px;margin:12px 0}
.thinkbox h4,.practicebox h4{font:700 12px/1 system-ui;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);margin:0 0 10px}
.thinkbox ul{margin:0;padding-left:20px;font-size:17px;color:#cfe7da}
.practicebox p{margin:0;font-size:17px;color:#cfe7da}
.curmeta{color:var(--muted);font:650 13px/1.4 system-ui;margin-top:8px}
""" if is_curriculum else ""
    curriculum_block = _curriculum_extra_html(lesson)
    return f"""<!doctype html><html lang='en'><head>
<meta charset='utf-8'>
<meta name='viewport' content='width=device-width,initial-scale=1,viewport-fit=cover'>
<meta name='color-scheme' content='dark'>
<script src='https://telegram.org/js/telegram-web-app.js'></script>
<title>{esc(lesson['title'])} — LifeOS Learn</title>
<style>{BASE_CSS}{curriculum_css}
.completebar{{display:flex;align-items:center;justify-content:space-between;gap:12px;border:1px solid var(--line);border-radius:14px;background:var(--card);padding:14px 16px;margin:24px 0}}
.completebar b{{display:block;font:800 17px/1.2 system-ui}}.completebar span{{display:block;color:var(--muted);font:650 13px/1.35 system-ui;margin-top:4px}}
.completebar button{{border:0;border-radius:10px;background:var(--fg);color:var(--bg);font:900 14px/1 system-ui;padding:12px 14px;cursor:pointer;white-space:nowrap}}
.completebar button:disabled{{opacity:.65;cursor:default}}
.user-highlight{{background:#ffe66d;color:#151719;border-radius:3px;padding:0 .08em;box-decoration-break:clone;-webkit-box-decoration-break:clone}}
.hlbar{{position:fixed;z-index:99;display:none;gap:6px;background:#151719;color:#fff;border:1px solid #000;border-radius:999px;padding:6px;box-shadow:0 10px 30px rgba(0,0,0,.22)}}
.hlbar.show{{display:flex}}.hlbar button{{border:0;border-radius:999px;background:#fff;color:#151719;font:850 13px/1 system-ui;padding:9px 12px;cursor:pointer}}.hlbar [data-hl-clear]{{background:#2b2b2b;color:#fff}}
.extrasDrop{{border:1px solid var(--line);border-radius:14px;background:var(--card);margin:28px 0;overflow:hidden}}
.extrasDrop summary{{cursor:pointer;list-style:none;padding:16px 18px;font:850 15px/1.2 system-ui;color:var(--fg);display:flex;justify-content:space-between;gap:12px;align-items:center}}
.extrasDrop summary::-webkit-details-marker{{display:none}}
.extrasDrop summary::after{{content:'+';color:var(--muted);font-size:20px;line-height:1}}
.extrasDrop[open] summary{{border-bottom:1px solid var(--line)}}.extrasDrop[open] summary::after{{content:'–'}}
.extrasInner{{padding:0 18px 18px}}
.readingNote,.questionBlock,.sourceTrail{{border:1px solid var(--line);border-radius:14px;background:var(--card);padding:18px 20px;margin:16px 0}}
.readingNote h3,.questionBlock h3,.sourceTrail h3{{margin:0 0 8px;font:850 22px/1.1 system-ui;color:var(--fg)}}
.readingNote p,.questionBlock p,.sourceTrail p{{margin:0 0 10px;color:#cfe7da;font-size:16px;line-height:1.55}}
.questionBlock ul,.sourceTrail ul{{margin:0;padding-left:20px;color:#dceddf;font-size:16px;line-height:1.55}}
.sourceTrail li+li,.questionBlock li+li{{margin-top:7px}}
.sourceTrail a{{color:inherit;font-weight:850;text-decoration:underline;text-underline-offset:2px}}
.sourceTrail span{{display:block;color:var(--muted);font-size:13px;margin-top:2px}}
.companion{{border-top:1px solid var(--line);border-bottom:1px solid var(--line);padding:26px 0;margin:34px 0;color:var(--fg)}}
.companion-k{{font:850 12px/1 system-ui;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);margin-bottom:8px}}
.companion h2{{font:850 31px/1.08 Georgia,serif;margin:0 0 10px}}.companion h3{{font:850 18px/1.15 system-ui;margin:0 0 8px}}
.companion p{{color:#cfe7da;font-size:17px;line-height:1.65;margin:0 0 12px}}.companion b{{color:var(--fg)}}
.companion-stack{{display:grid;gap:12px;margin:14px 0}}.companion-card{{border:1px solid var(--line);background:var(--card);border-radius:14px;padding:16px;margin:12px 0}}
.companion-card ul,.companion-card ol{{margin:0;padding-left:20px;color:#dceddf;font-size:16px;line-height:1.55}}.companion-card li+li{{margin-top:8px}}.companion-card li span{{display:block;color:#cfe7da;margin-top:2px}}
.walkList b{{display:block;color:var(--fg)}}.walkList span{{display:block;color:#cfe7da;margin-top:3px}}
.anchorGrid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;margin-top:10px}}.anchorGrid div{{border:1px solid var(--line);border-radius:12px;background:#0b130f;padding:12px}}.anchorGrid span{{display:block;color:#cfe7da;font-size:14px;line-height:1.4;margin-top:4px}}
.sourceCards{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;margin-top:10px}}.sourceCards a{{display:block;text-decoration:none;color:var(--fg);border:1px solid var(--line);border-radius:12px;padding:12px;background:#0b130f}}.sourceCards span{{display:block;color:var(--muted);font-size:13px;line-height:1.35;margin-top:4px}}
@media(max-width:640px){{.completebar{{align-items:flex-start;flex-direction:column}}.completebar button{{width:100%}}.anchorGrid,.sourceCards{{grid-template-columns:1fr}}}}
:root{{--accent:{accent}}}</style></head>
<body><div class='wrap'>
<div class='topbar'><a href='/learn'>&larr; Today's lessons</a><a href='/output/learn/skill-tree.html'>Knowledge graph</a><a href='/output/learn/learning-system.html'>Training queue</a><span>{esc(day)}</span></div>
<main class='lessonBody' data-highlight-root>
{_hero_html(lesson)}
<div class='kicker'>{kicker}</div>
<h1>{esc(lesson['title'])}</h1>
<p class='sub'>{esc(lesson['subtitle'])}</p>
<div class='meta'><span>⏱ {esc(max(5, int(lesson.get('minutes') or 5)))} min read</span><span>Worth more than the feed</span></div>
<p class='lead'>{lesson['lead']}</p>
{_sections_html(lesson['sections'])}
{_deep_companion_html(lesson)}
<details class='extrasDrop'><summary>Notes, questions, sources, and practice</summary><div class='extrasInner'>
{_reading_note_html(lesson)}
{_ideas_html(lesson['ideas'])}
{curriculum_block}
{_thinking_questions_html(lesson)}
{_game_html(lesson['game'])}
<div class='reveal'><button>💡 Did you know? Tap to reveal</button><div class='txt'>{lesson['did_you_know']}</div></div>
{_play_cta(lesson['id'])}
<div class='completebar'><div><b>Lock this node into your knowledge graph</b><span data-lifeos-level>Level 1 / 0 XP</span></div><button data-complete-node>Mark complete</button></div>
{_source_trail_html(lesson)}
</div></details>
</main>
<div class='foot'>
<p>{esc(lesson.get('next',''))}</p>
<p>Stuck or curious? Ask your LifeOS agent to go deeper on anything here — it's your teacher.</p>
</div>
</div>
<script>window.LIFEOS_NODE={json.dumps(progress_node)};</script><script>{PROGRESS_JS}</script><script>{HIGHLIGHT_JS}</script><script>{BASE_JS}</script></body></html>"""


def _rotate_pick(pool: list[dict[str, Any]], today: date, salt: int = 0) -> dict[str, Any] | None:
    if not pool:
        return None
    idx = (today.toordinal() + salt) % len(pool)
    return pool[idx]


def daily_set(today: date) -> list[dict[str, Any]]:
    """Balanced morning queue: curriculum domains, deep history, and review hooks."""
    library = lesson_library()
    by_id = {l["id"]: l for l in library}
    curriculum = [l for l in library if str(l.get("track", "")).startswith("curriculum")]
    deep = [l for l in library if l.get("track") == "deep-history"]
    history_core = [by_id["story-of-civilization"]] if "story-of-civilization" in by_id else []

    def curriculum_pool(domain: str) -> list[dict[str, Any]]:
        return [l for l in curriculum if l.get("curriculum", {}).get("domain") == domain]

    invention_pool = curriculum_pool("invention")
    statecraft_pool = curriculum_pool("statecraft")
    target_count = 6 + (1 if invention_pool else 0) + (1 if statecraft_pool else 0)
    picks: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add(lesson: dict[str, Any] | None) -> None:
        if lesson and lesson["id"] not in seen:
            picks.append(lesson)
            seen.add(lesson["id"])

    add(_rotate_pick(curriculum_pool("math"), today, 0))
    add(_rotate_pick(curriculum_pool("physics"), today, 1))
    add(_rotate_pick(invention_pool, today, 2))
    add(_rotate_pick(statecraft_pool, today, 3))
    add(_rotate_pick(curriculum_pool("history"), today, 4) or _rotate_pick(history_core, today, 4))
    add(_rotate_pick(curriculum_pool("startup"), today, 5))
    add(_rotate_pick(curriculum_pool("thinking"), today, 6))
    add(_rotate_pick(deep, today, 7))
    if len(picks) < target_count and len(deep) > 1:
        add(_rotate_pick(deep, today, 8))
    elif len(picks) < target_count and history_core:
        add(history_core[0])

    if not picks:
        rest = [l for l in library if not l.get("generated")]
        n = len(rest)
        start = today.toordinal() % n if n else 0
        return [rest[(start + i) % n] for i in range(min(target_count, n))] if n else []
    return picks[:target_count]




def _lesson_categories(lesson: dict[str, Any]) -> list[str]:
    """Broad reading categories used by the browser recommendation engine."""
    meta = lesson.get("curriculum") or {}
    domain = str(meta.get("domain") or lesson.get("domain") or "").lower()
    track = str(lesson.get("track") or meta.get("track_id") or "").lower()
    title = str(lesson.get("title") or "").lower()
    text = " ".join([domain, track, title, str(lesson.get("subtitle") or "").lower()])
    cats: list[str] = []

    def add(cat: str) -> None:
        if cat not in cats:
            cats.append(cat)

    if domain in {"history", "statecraft"} or "deep-history" in track or any(
        word in text for word in ["civilization", "caesar", "rome", "tesla", "alexandria", "napoleon", "churchill", "gandhi"]
    ):
        add("history")
    if domain == "thinking" or any(
        word in text for word in ["philosophy", "socrates", "plato", "aristotle", "ethics", "stoic", "belief", "logic"]
    ):
        add("philosophy")
    if domain in {"math", "physics", "invention"} or any(
        word in text for word in ["science", "quantum", "calculus", "algebra", "geometry", "energy", "electric", "physics", "proof"]
    ):
        add("science")
    if domain == "startup" or track.startswith("pg-") or "paul graham" in text or "startup" in text:
        add("startup")
    if domain == "statecraft" or any(
        word in text for word in ["strategy", "power", "campaign", "war", "founder", "moat", "distribution"]
    ):
        add("strategy")
    if not cats:
        add("general")
    return cats


def _art_kind_for_lesson(lesson: dict[str, Any], cats: list[str] | None = None) -> str:
    cats = cats or _lesson_categories(lesson)
    title = str(lesson.get("title") or "").lower()
    if "startup" in cats or "paul graham" in title or "programmer" in title:
        return "startup"
    if "science" in cats:
        return "science"
    if "history" in cats:
        return "history"
    if "strategy" in cats:
        return "strategy"
    if "philosophy" in cats:
        return "philosophy"
    return "general"


def _lesson_level(lesson: dict[str, Any]) -> int:
    raw = str((lesson.get("curriculum") or {}).get("difficulty") or lesson.get("difficulty") or lesson.get("difficulty_level") or "").lower()
    if any(word in raw for word in ["intro", "beginner", "foundation", "basic"]):
        return 1
    if any(word in raw for word in ["intermediate", "medium", "core", "formation", "method"]):
        return 2
    if any(word in raw for word in ["advanced", "hard", "expert", "capstone", "synthesis"]):
        return 4
    minutes = int(lesson.get("minutes") or 10)
    sections = len(lesson.get("sections") or [])
    return max(1, min(4, round(1 + max(0, minutes - 12) / 22 + min(1.4, sections / 7))))


def _lesson_card_description(lesson: dict[str, Any]) -> str:
    title = str(lesson.get("title") or "").strip()
    low_title = title.lower()
    if "let the other 95%" in low_title:
        return "Why great programmers are often invisible to normal hiring filters — and how a startup can turn overlooked talent into an unfair advantage."
    if "don't talk to corp dev" in low_title:
        return "How a flattering acquisition conversation can steal focus, weaken morale, and shift leverage away from founders before a deal even exists."
    if "do things that don't scale" in low_title:
        return "Why unscalable work is not inefficiency but instrumentation: a way to discover trust, friction, and user love before automation hides the truth."
    subtitle = str(lesson.get("subtitle") or "").strip()
    lead = str(lesson.get("lead") or "").strip()
    if lead and lead != subtitle:
        return _plain_text(lead, 300)
    for _heading, body in _section_records(lesson.get("sections") or []):
        if body and body != subtitle:
            return _plain_text(body, 300)
    summary = str(lesson.get("summary") or "").strip()
    if summary and summary != subtitle:
        return _plain_text(summary, 300)
    return _plain_text(subtitle, 300)


def _recommendation_catalog(library: list[dict[str, Any]], daily_ids: set[str]) -> list[dict[str, Any]]:
    catalog: list[dict[str, Any]] = []
    for lesson in library:
        lesson_id = str(lesson.get("id") or "")
        if not lesson_id:
            continue
        meta = lesson.get("curriculum") or {}
        cats = _lesson_categories(lesson)
        catalog.append({
            "id": lesson_id,
            "title": str(lesson.get("title") or lesson_id),
            "subtitle": str(lesson.get("subtitle") or ""),
            "description": _lesson_card_description(lesson),
            "minutes": int(lesson.get("minutes") or 10),
            "emoji": str(lesson.get("emoji") or "•"),
            "accent": str(lesson.get("accent") or "#151719"),
            "artKind": _art_kind_for_lesson(lesson, cats),
            "url": f"/output/learn/{lesson_id}.html",
            "categories": cats,
            "domain": str(meta.get("domain") or lesson.get("domain") or lesson.get("track") or "general"),
            "daily": lesson_id in daily_ids,
            "level": _lesson_level(lesson),
        })
    return catalog

def sync_config_js() -> str:
    config = {
        "supabaseUrl": os.getenv("LIFEOS_SUPABASE_URL", ""),
        "supabaseAnonKey": os.getenv("LIFEOS_SUPABASE_ANON_KEY", ""),
    }
    return "window.LIFEOS_SYNC_CONFIG=" + json.dumps(config, separators=(",", ":")) + ";\n"


def render_profile_page() -> str:
    return """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><title>LifeOS Profile</title><style>
*{box-sizing:border-box}html,body{margin:0;min-height:100%;background:#f6f4ee;color:#17130f;font-family:Inter,system-ui,-apple-system,sans-serif}a{color:inherit}.shell{width:min(760px,calc(100% - 28px));margin:0 auto;padding:18px 0 42px}.top{display:flex;gap:10px;flex-wrap:wrap;align-items:center;justify-content:space-between;margin-bottom:18px}.top a{text-decoration:none;border:1px solid #dfd2bd;background:#fff8ec;border-radius:999px;padding:10px 12px;font:900 13px/1 system-ui}.hero{border:1px solid #dfd2bd;background:#fff8ec;border-radius:28px;padding:22px;box-shadow:0 18px 54px rgba(54,38,18,.1)}.k{font:950 12px/1 system-ui;letter-spacing:.14em;text-transform:uppercase;color:#9a6a22}.hero h1{font:950 clamp(42px,8vw,72px)/.88 Georgia,serif;letter-spacing:-.06em;margin:8px 0}.hero p{font:600 16px/1.55 Georgia,serif;color:#53473a;margin:0}.grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:14px}.card{border:1px solid #dfd2bd;background:#fff;border-radius:22px;padding:16px}.card h2{font:950 24px/.98 Georgia,serif;margin:0 0 8px}.card p{color:#5b5148;font:650 13px/1.45 system-ui}.row{display:grid;gap:8px;margin:10px 0}.row label{font:900 11px/1 system-ui;letter-spacing:.12em;text-transform:uppercase;color:#766957}.row input,.row select,.row textarea{width:100%;border:1px solid #d8cbb6;border-radius:12px;padding:11px;background:#fffdf8;font:700 14px/1.3 system-ui;color:#17130f}.row textarea{min-height:130px;font-family:ui-monospace,Consolas,monospace}.buttons{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}.buttons button,.buttons label{border:0;border-radius:999px;background:#17130f;color:#fff8ec;padding:10px 12px;font:950 13px/1 system-ui;cursor:pointer}.buttons .ghost{background:#efe4d2;color:#17130f}.stat{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:12px}.stat div{border:1px solid #eadfce;background:#fff8ec;border-radius:16px;padding:10px}.stat b{display:block;font:950 22px/1 system-ui}.stat span{font:850 11px/1.2 system-ui;color:#756756}.status{margin-top:10px;color:#6b5d4e;font:800 13px/1.35 system-ui}.teacher{border-left:4px solid #8f6bff;padding-left:10px}.ok{color:#227c5b}.bad{color:#9b3328}@media(max-width:720px){.grid{grid-template-columns:1fr}.stat{grid-template-columns:1fr}.hero{border-radius:22px;padding:18px}.hero h1{font-size:42px}}</style></head><body><main class="shell"><div class="top"><a href="/learn">← Field Notes</a><a href="/output/learn/skill-tree.html">Graph</a><a href="/output/learn/learning-system.html">Training</a></div><section class="hero"><div class="k">Profile / Memory</div><h1>Your tree should remember you.</h1><p>LifeOS is local-first: your graph lives in this browser. This page lets you name the profile, export/import the memory, paste a sync code on another device, and optionally connect cloud sync when Supabase keys are configured.</p><div class="stat"><div><b data-known>0</b><span>learned nodes</span></div><div><b data-xp>0</b><span>XP</span></div><div><b data-role>learner</b><span>role</span></div></div></section><section class="grid"><article class="card"><h2>Local profile</h2><p>Good enough for one device; export the bundle before clearing browser data.</p><div class="row"><label>Name</label><input data-name placeholder="Your name"></div><div class="row"><label>Role</label><select data-role-input><option value="learner">Learner</option><option value="teacher">Teacher / mentor</option></select></div><div class="buttons"><button data-save-profile>Save profile</button><button class="ghost" data-refresh>Refresh stats</button></div><p class="status" data-profile-status></p><p class="teacher" data-teacher-note hidden>Teacher mode: import a learner bundle or sync code to inspect their graph on this device. Classroom accounts can use the cloud path once configured.</p></article><article class="card"><h2>Portable memory</h2><p>Use this today to carry progress between phone, laptop, and teacher review.</p><div class="buttons"><button data-export>Download memory</button><label class="ghost">Import file<input data-import type="file" accept="application/json" hidden></label></div><div class="row"><label>Sync code</label><textarea data-code placeholder="Generate a code, or paste one from another device."></textarea></div><div class="buttons"><button data-make-code>Generate code</button><button class="ghost" data-apply-code>Apply pasted code</button></div><p class="status" data-portable-status></p></article><article class="card"><h2>Cloud login</h2><p>Optional. Requires `LIFEOS_SUPABASE_URL` and `LIFEOS_SUPABASE_ANON_KEY` in the Vercel environment plus the table/RLS from the tech spec.</p><div class="row"><label>Email</label><input data-email type="email" placeholder="you@example.com"></div><div class="buttons"><button data-login>Send magic link</button><button class="ghost" data-cloud-save>Save to cloud</button><button class="ghost" data-cloud-load>Load from cloud</button></div><p class="status" data-cloud-status>Checking cloud configuration…</p></article><article class="card"><h2>What gets saved</h2><p>The bundle contains only LifeOS browser memory: profile metadata, learned nodes/review stages, deck skips/yes picks, and last-seen level. It does not include private library files or copied source text.</p><p class="status">If this is a public classroom device, export what you need, then reset browser site data after the session.</p></article></section></main><script src="/output/learn/sync-config.js"></script><script>
(function(){
const KEYS=['lifeos.profile.v1','lifeos.learning.progress.v1','lifeos.deck.skipped.v2','lifeos.deck.yes.v2','lifeos.level.lastSeen.v1'];
const PROFILE_KEY='lifeos.profile.v1',PROGRESS_KEY='lifeos.learning.progress.v1';
const $=s=>document.querySelector(s);let client=null,user=null;
function load(k,f){try{return JSON.parse(localStorage.getItem(k)||JSON.stringify(f))}catch{return f}}
function save(k,v){localStorage.setItem(k,JSON.stringify(v))}
function progress(){const p=load(PROGRESS_KEY,{});p.done=p.done||{};p.reviews=p.reviews||{};return p}
function xp(){return Object.values(progress().done).reduce((s,n)=>s+(+n.xp||0),0)}
function bundle(){const data={version:1,exported_at:new Date().toISOString(),storage:{}};for(const k of KEYS){const v=localStorage.getItem(k);if(v!=null)data.storage[k]=v}return data}
function applyBundle(data){if(!data||!data.storage)throw new Error('Not a LifeOS memory bundle');for(const [k,v] of Object.entries(data.storage)){if(KEYS.includes(k)&&typeof v==='string')localStorage.setItem(k,v)}render();}
function encode(data){return btoa(unescape(encodeURIComponent(JSON.stringify(data))))}
function decode(s){return JSON.parse(decodeURIComponent(escape(atob(String(s).trim()))))}
function render(){const prof=load(PROFILE_KEY,{name:'',role:'learner'}),p=progress();$('[data-name]').value=prof.name||'';$('[data-role-input]').value=prof.role||'learner';$('[data-role]').textContent=prof.role||'learner';$('[data-known]').textContent=Object.keys(p.done||{}).length;$('[data-xp]').textContent=xp();$('[data-teacher-note]').hidden=(prof.role||'learner')!=='teacher'}
function flash(sel,msg,cls=''){$(sel).className='status '+cls;$(sel).textContent=msg}
$('[data-save-profile]').onclick=()=>{save(PROFILE_KEY,{name:$('[data-name]').value.trim(),role:$('[data-role-input]').value,updated_at:new Date().toISOString()});render();flash('[data-profile-status]','Profile saved.','ok')};
$('[data-role-input]').onchange=()=>{$('[data-teacher-note]').hidden=$('[data-role-input]').value!=='teacher'};$('[data-refresh]').onclick=()=>{render();flash('[data-profile-status]','Stats refreshed.','ok')};
$('[data-export]').onclick=()=>{const blob=new Blob([JSON.stringify(bundle(),null,2)],{type:'application/json'}),a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='lifeos-memory-'+new Date().toISOString().slice(0,10)+'.json';a.click();URL.revokeObjectURL(a.href);flash('[data-portable-status]','Memory file downloaded.','ok')};
$('[data-import]').onchange=e=>{const file=e.target.files&&e.target.files[0];if(!file)return;const r=new FileReader();r.onload=()=>{try{applyBundle(JSON.parse(r.result));flash('[data-portable-status]','Imported memory bundle.','ok')}catch(err){flash('[data-portable-status]',err.message,'bad')}};r.readAsText(file)};
$('[data-make-code]').onclick=()=>{try{$('[data-code]').value=encode(bundle());flash('[data-portable-status]','Sync code generated. Paste it on another device.','ok')}catch(err){flash('[data-portable-status]',err.message,'bad')}};
$('[data-apply-code]').onclick=()=>{try{applyBundle(decode($('[data-code]').value));flash('[data-portable-status]','Applied sync code.','ok')}catch(err){flash('[data-portable-status]','Could not read that sync code.','bad')}};
async function loadSupabase(){const cfg=window.LIFEOS_SYNC_CONFIG||{};if(!cfg.supabaseUrl||!cfg.supabaseAnonKey){flash('[data-cloud-status]','Cloud login is not configured on this deployment. Export/import works now.');return null}await new Promise((res,rej)=>{const s=document.createElement('script');s.src='https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2';s.onload=res;s.onerror=rej;document.head.appendChild(s)});client=window.supabase.createClient(cfg.supabaseUrl,cfg.supabaseAnonKey);const sess=await client.auth.getSession();user=sess.data.session&&sess.data.session.user;if(user)flash('[data-cloud-status]','Signed in as '+user.email,'ok');else flash('[data-cloud-status]','Cloud ready. Enter email for a magic link.','ok');return client}
$('[data-login]').onclick=async()=>{try{const c=client||await loadSupabase();if(!c)return;const email=$('[data-email]').value.trim();if(!email)throw new Error('Enter an email first');const {error}=await c.auth.signInWithOtp({email,options:{emailRedirectTo:location.href}});if(error)throw error;flash('[data-cloud-status]','Magic link sent. Open it on this device.','ok')}catch(err){flash('[data-cloud-status]',err.message,'bad')}};
$('[data-cloud-save]').onclick=async()=>{try{const c=client||await loadSupabase();if(!c)return;const sess=await c.auth.getSession();user=sess.data.session&&sess.data.session.user;if(!user)throw new Error('Sign in first');const {error}=await c.from('lifeos_progress').upsert({user_id:user.id,payload:bundle(),updated_at:new Date().toISOString()});if(error)throw error;flash('[data-cloud-status]','Saved memory to cloud.','ok')}catch(err){flash('[data-cloud-status]',err.message,'bad')}};
$('[data-cloud-load]').onclick=async()=>{try{const c=client||await loadSupabase();if(!c)return;const sess=await c.auth.getSession();user=sess.data.session&&sess.data.session.user;if(!user)throw new Error('Sign in first');const {data,error}=await c.from('lifeos_progress').select('payload').eq('user_id',user.id).maybeSingle();if(error)throw error;if(!data)throw new Error('No cloud memory yet');applyBundle(data.payload);flash('[data-cloud-status]','Loaded cloud memory.','ok')}catch(err){flash('[data-cloud-status]',err.message,'bad')}};
render();loadSupabase().catch(()=>flash('[data-cloud-status]','Cloud library failed to load. Export/import still works.','bad'));window.LifeOSProfile={bundle,applyBundle,progress};
})();
</script></body></html>"""


def render_index(daily: list[dict[str, Any]], library: list[dict[str, Any]], today: date) -> str:
    """Render /learn as a Tinder-like photo card deck."""
    day = today.strftime("%A, %B %d").replace(" 0", " ")
    daily_ids = {l["id"] for l in daily}
    rec_catalog = _recommendation_catalog(library, daily_ids)
    rec_data = json.dumps(rec_catalog, separators=(",", ":")).replace("</", "<\\/")
    fallback = []
    for idx, lesson in enumerate(daily[:3]):
        cats = _lesson_categories(lesson)
        art_kind = _art_kind_for_lesson(lesson, cats)
        fallback.append(
            f"<article class='deck-card' style='--i:{idx};--c:{esc(lesson.get('accent', '#151719'))}' data-id='{esc(lesson['id'])}' data-url='/output/learn/{esc(lesson['id'])}.html'>"
            f"<div class='photo art-{esc(art_kind)}'><i></i><b></b><em></em><span></span></div>"
            f"<div class='copy'><div class='meta'>L{_lesson_level(lesson)} · {esc(lesson['minutes'])} min · {esc(', '.join(cats))}</div>"
            f"<h2>{esc(lesson['title'])}</h2><p>{esc(_lesson_card_description(lesson))}</p></div></article>"
        )
    fallback_cards = "".join(fallback)
    game_cards = "".join(
        f"<a class='mini-card' href='{esc(g['url']) if 'url' in g else '/output/learn/'+esc(g['id'])+'.html'}'>"
        f"<span>{esc(g['emoji'])}</span><strong>{esc(g['title'])}</strong></a>"
        for g in GAME_CATALOG[:8]
    )
    recommendation_js = r"""<script>
(function(){
const CATALOG=window.LIFEOS_REC_CATALOG||[];
const PROGRESS_KEY='lifeos.learning.progress.v1';
const SKIP_KEY='lifeos.deck.skipped.v2';
const YES_KEY='lifeos.deck.yes.v2';
const stage=document.querySelector('[data-deck-stage]');
const empty=document.querySelector('[data-empty]');
const globalNo=document.querySelector('[data-global-no]');
const globalYes=document.querySelector('[data-global-yes]');
let queue=[];
function load(key,fallback){try{return JSON.parse(localStorage.getItem(key)||JSON.stringify(fallback))}catch{return fallback}}
function save(key,value){localStorage.setItem(key,JSON.stringify(value))}
function esc(s){const d=document.createElement('div');d.textContent=s==null?'':String(s);return d.innerHTML}
function attr(s){return esc(s).replace(/"/g,'&quot;')}
function hash(s){let h=2166136261;for(let i=0;i<s.length;i++){h^=s.charCodeAt(i);h=Math.imul(h,16777619)}return h>>>0}
function doneIds(){const progress=load(PROGRESS_KEY,{});return new Set(Object.keys(progress.done||{}))}
function prefs(done){const out={};for(const id of done){const item=CATALOG.find(x=>x.id===id);if(!item)continue;(item.categories||[]).forEach(c=>out[c]=(out[c]||0)+1)}return out}
function learnerLevel(done){let xp=0;for(const id of done){const item=CATALOG.find(x=>x.id===id);xp+=item?(item.minutes||10)*6:80}return xp>=1440?4:(xp>=720?3:(xp>=240?2:1))}
function ranked(cat){
 const done=doneIds(),pref=prefs(done),lvl=learnerLevel(done),skipped=load(SKIP_KEY,{}),day=new Date().toISOString().slice(0,10);
 let pool=CATALOG.filter(item=>!done.has(item.id)&&!skipped[item.id]);
 if(cat&&cat!=='all')pool=pool.filter(item=>(item.categories||[]).includes(cat));
 let scored=pool.map(item=>{let s=item.daily?70:0;const gap=Math.abs((item.level||1)-(lvl+1));s+=Math.max(0,70-gap*20);if(done.size){for(const c of item.categories||[])s+=(pref[c]||0)*24}else{s+=item.daily?120:25}s+=(hash(item.id+day)%1000)/1000;return {item,s}}).sort((a,b)=>b.s-a.s).map(x=>x.item);
 if(scored.length<18){const seen=new Set(scored.map(x=>x.id));CATALOG.filter(item=>!seen.has(item.id)&&!done.has(item.id)).slice(0,18-scored.length).forEach(item=>scored.push(item))}
 return scored;
}
function card(item,i){const cats=(item.categories||['general']).join(', '),kind=item.artKind||'general';return `<article class="deck-card" style="--i:${i};--c:${attr(item.accent||'#111')}" data-id="${attr(item.id)}" data-url="${attr(item.url)}">
 <div class="photo art-${attr(kind)}"><i></i><b></b><em></em><span></span></div>
 <div class="copy"><div class="meta">L${esc(item.level||1)} · ${esc(item.minutes)} min · ${esc(cats)}</div><h2>${esc(item.title)}</h2><p>${esc(item.description||item.subtitle||'')}</p></div>
</article>`}
function renderStack(){
 if(!stage)return;
 const visible=queue.slice(0,3);
 stage.innerHTML=visible.map(card).join('');
 empty.hidden=visible.length>0;
 attach(stage);
}
function setCat(cat){queue=ranked(cat);renderStack()}
function topCard(){return stage&&stage.querySelector('.deck-card')}
function advance(card,dir){
 if(!card)return;
 const id=card.dataset.id;
 if(dir<0){const skipped=load(SKIP_KEY,{});skipped[id]={at:new Date().toISOString()};save(SKIP_KEY,skipped);card.classList.add('exit-left')}
 else{const yes=load(YES_KEY,{});yes[id]={at:new Date().toISOString()};save(YES_KEY,yes);card.classList.add('exit-right')}
 setTimeout(()=>{const next=queue.shift(); if(dir>0&&card.dataset.url){location.href=card.dataset.url;return} renderStack();},360);
}
function attach(root){
 root.querySelectorAll('.deck-card').forEach(card=>{
  let sx=0,sy=0,dx=0,dy=0,down=false,drag=false;
  card.addEventListener('pointerdown',e=>{if(e.target.closest('button,a'))return;down=true;drag=false;sx=e.clientX;sy=e.clientY;card.setPointerCapture?.(e.pointerId)});
  card.addEventListener('pointermove',e=>{if(!down)return;dx=e.clientX-sx;dy=e.clientY-sy;if(Math.abs(dx)>8&&Math.abs(dx)>Math.abs(dy)){drag=true;const rot=dx/18;card.style.transition='none';card.style.transform=`translate3d(${dx}px,${Math.abs(dx)*-.04}px,0) rotate(${rot}deg)`;card.style.opacity=String(Math.max(.35,1-Math.abs(dx)/360));e.preventDefault();}});
  function end(e){if(!down)return;down=false;card.style.transition='';if(drag&&dx>88){advance(card,1);return}if(drag&&dx<-88){advance(card,-1);return}card.style.transform='';card.style.opacity='';}
  card.addEventListener('pointerup',end);card.addEventListener('pointercancel',end);
 });
}
globalNo?.addEventListener('click',()=>advance(topCard(),-1));
globalYes?.addEventListener('click',()=>advance(topCard(),1));
document.addEventListener('keydown',e=>{if(e.key==='ArrowLeft')advance(topCard(),-1);if(e.key==='ArrowRight')advance(topCard(),1)});
setCat('all');
})();
</script>"""
    return f"""<!doctype html><html lang='en'><head>
<meta charset='utf-8'>
<meta name='viewport' content='width=device-width,initial-scale=1,viewport-fit=cover'>
<meta name='color-scheme' content='light'>
<title>LifeOS Deck</title>
<style>
*{{box-sizing:border-box}}html,body{{margin:0;min-height:100%;background:#f6f7fb;color:#1b1b1f;font-family:Inter,system-ui,-apple-system,sans-serif;overflow-x:hidden}}body{{display:grid;place-items:start center}}a{{color:inherit}}
.app{{width:min(430px,100vw);min-height:100svh;padding:0 12px 18px;background:#f6f7fb}}
.tinderbar{{height:56px;display:flex;align-items:center;justify-content:space-between;color:#a4a7ae}}.tinderbar button,.tinderbar a{{display:grid;place-items:center;border:0;background:transparent;color:#a4a7ae;font-size:23px;width:44px;height:44px;border-radius:999px;text-decoration:none}}.brand{{font:950 24px/1 system-ui;letter-spacing:-.04em;background:linear-gradient(90deg,#ff4458,#ff7a3d);-webkit-background-clip:text;background-clip:text;color:transparent}}
.stage{{position:relative;width:min(386px,calc(100vw - 24px));height:clamp(500px,68svh,620px);margin:0 auto;perspective:1400px}}
.deck-card{{position:absolute;inset:0;background:#fff8ec;color:#17130f;border-radius:22px;overflow:hidden;box-shadow:0 18px 44px rgba(23,27,33,.18);transform:translate3d(0,calc(var(--i)*9px),0) scale(calc(1 - var(--i)*.035));z-index:calc(20 - var(--i));opacity:calc(1 - var(--i)*.16);transition:transform 560ms cubic-bezier(.16,1,.3,1),opacity 360ms ease;will-change:transform,opacity;touch-action:pan-y;display:flex;flex-direction:column}}
.deck-card.exit-left{{transform:translate3d(-124%,20px,0) rotate(-18deg)!important;opacity:0!important}}.deck-card.exit-right{{transform:translate3d(124%,20px,0) rotate(18deg)!important;opacity:0!important}}
.photo{{height:55%;position:relative;overflow:hidden;background:#8fc9e8;display:block;flex:none;border:10px solid #f5e3bd;border-bottom-width:7px;box-shadow:inset 0 0 0 1px rgba(92,61,28,.18),inset 0 -34px 50px rgba(44,27,12,.18)}}.photo:before{{content:'';position:absolute;inset:-2%;background:radial-gradient(circle at 78% 20%,var(--sun,#ffd166) 0 12%,rgba(255,255,255,.5) 13% 18%,transparent 19%),radial-gradient(circle at 22% 16%,rgba(255,255,255,.42),transparent 18%),linear-gradient(145deg,var(--sky1,#8fc9e8) 0%,var(--sky2,#f7c98b) 58%,var(--ground,#224c3d) 59% 100%);filter:saturate(1.12) contrast(1.04)}}.photo:after{{content:'';position:absolute;left:-18%;right:-18%;bottom:-24%;height:54%;border-radius:52% 52% 0 0;background:linear-gradient(180deg,color-mix(in srgb,var(--ground,#224c3d) 78%,#fff 22%),var(--ground,#224c3d));box-shadow:70px -24px 0 -8px color-mix(in srgb,var(--ground,#224c3d) 68%,#fff 32%),-80px -12px 0 -18px color-mix(in srgb,var(--ground,#224c3d) 58%,#fff 42%),0 -74px 0 -43px rgba(255,246,213,.34),inset 0 22px 35px rgba(255,245,210,.14)}}.photo i,.photo b,.photo em,.photo span{{position:absolute;display:block;z-index:2}}.photo i{{width:116px;height:116px;border-radius:999px;background:radial-gradient(circle at 35% 35%,#fff7c6 0 18%,var(--sun,#ffd166) 19% 62%,rgba(255,209,102,.18) 63%);right:9%;top:10%;box-shadow:0 0 45px color-mix(in srgb,var(--sun,#ffd166) 62%,transparent),0 18px 40px rgba(64,36,9,.18)}}.photo b{{width:116px;height:128px;left:15%;bottom:17%;background:linear-gradient(180deg,var(--shape,#fff8ec),#d9b46f);border-radius:58px 58px 10px 10px;transform:rotate(-4deg);box-shadow:28px 18px 0 -10px rgba(255,244,213,.58),0 14px 0 -7px rgba(60,35,17,.18),inset 0 -18px 0 rgba(83,45,19,.18)}}.photo b:before{{content:'';position:absolute;left:28px;right:28px;top:-32px;height:58px;border-radius:58px 58px 10px 10px;background:var(--accentArt,#ff6b5f);box-shadow:0 42px 0 -21px rgba(67,38,16,.28)}}.photo b:after{{content:'';position:absolute;left:45px;bottom:0;width:28px;height:46px;border-radius:14px 14px 0 0;background:rgba(48,28,15,.46);box-shadow:-38px -32px 0 -13px rgba(48,28,15,.22),38px -42px 0 -13px rgba(48,28,15,.22)}}.photo em{{width:78px;height:112px;right:17%;bottom:15%;background:linear-gradient(180deg,var(--accentArt,#ff6b5f),color-mix(in srgb,var(--accentArt,#ff6b5f) 65%,#3a1d12 35%));border-radius:40px 40px 15px 15px;transform:rotate(8deg);opacity:.96;box-shadow:0 16px 30px rgba(53,28,13,.24),inset 0 -14px 0 rgba(45,26,14,.18)}}.photo em:before{{content:'';position:absolute;left:22px;top:-27px;width:34px;height:34px;border-radius:999px;background:#ffe6b6;box-shadow:0 0 0 8px rgba(255,246,210,.18)}}.photo span{{width:210px;height:2px;left:12%;top:43%;background:rgba(255,248,220,.62);transform:rotate(-13deg);box-shadow:0 28px 0 rgba(255,248,220,.42),0 56px 0 rgba(255,248,220,.24)}}.photo span:before{{content:'';position:absolute;right:-42px;top:-34px;width:84px;height:48px;border-radius:50%;background:radial-gradient(circle at 20% 60%,rgba(255,248,220,.65) 0 14%,transparent 15%),radial-gradient(circle at 60% 35%,rgba(255,248,220,.45) 0 18%,transparent 19%)}}.photo span:after{{content:'';position:absolute;left:-30px;top:72px;width:280px;height:140px;background:repeating-radial-gradient(circle at 50% 50%,rgba(255,255,255,.08) 0 1px,transparent 1px 8px);opacity:.55;transform:rotate(10deg)}}.art-startup{{--sky1:#b9e8d4;--sky2:#6bbf9f;--ground:#174a3a;--sun:#ffe07a;--shape:#fff4d7;--accentArt:#ff6b5f}}.art-startup b{{border-radius:18px 18px 9px 9px;transform:rotate(-6deg)}}.art-startup b:before{{border-radius:8px;transform:rotate(45deg);top:-25px;height:64px}}.art-science{{--sky1:#7fc8ff;--sky2:#17255f;--ground:#151a45;--sun:#d8f3ff;--shape:#f8fbff;--accentArt:#7ee3ff}}.art-science b{{border-radius:999px 999px 20px 20px}}.art-science em{{border-radius:999px;box-shadow:0 0 0 10px rgba(126,227,255,.18),0 16px 30px rgba(0,0,0,.24)}}.art-history{{--sky1:#f1c27d;--sky2:#c66b49;--ground:#5f311d;--sun:#ffe1a6;--shape:#fff2d2;--accentArt:#8b3f2f}}.art-history b{{border-radius:10px 10px 4px 4px;box-shadow:22px 0 0 -6px #f0d29c,44px 0 0 -12px #d9aa6c}}.art-philosophy{{--sky1:#d9c6ff;--sky2:#7862b8;--ground:#37265f;--sun:#fff0a8;--shape:#fff7e8;--accentArt:#9a7cff}}.art-philosophy b{{border-radius:8px;transform:rotate(-11deg) skew(-4deg);height:88px}}.art-strategy{{--sky1:#cfd6df;--sky2:#73808e;--ground:#27313c;--sun:#f5d38a;--shape:#f7efe0;--accentArt:#d65d4a}}.art-strategy b{{border-radius:12px 12px 3px 3px;transform:rotate(0)}}.art-strategy em{{clip-path:polygon(50% 0,100% 100%,0 100%);border-radius:8px}}.art-general{{--sky1:#b8d8ff;--sky2:#f1c6a8;--ground:#304a5f;--sun:#ffe3a1;--shape:#fff8ec;--accentArt:#5aa6ff}}
.copy{{height:45%;padding:17px 20px 20px;display:flex;flex-direction:column;background:#fff8ec;color:#17130f}}.meta{{display:inline-flex;align-self:flex-start;background:#ede4d3;border-radius:999px;padding:6px 9px;font:900 10px/1 system-ui;letter-spacing:.11em;text-transform:uppercase;color:#74695a;margin-bottom:9px}}.copy h2{{font:850 clamp(29px,7.4vw,39px)/.94 Georgia,'Iowan Old Style',serif;letter-spacing:-.025em;margin:0;color:#17130f}}.copy p{{font:500 16px/1.36 Georgia,'Iowan Old Style',serif;color:#3f3a33;margin:10px 0 0;display:-webkit-box;-webkit-line-clamp:4;-webkit-box-orient:vertical;overflow:hidden}}
.action-dock{{height:72px;display:flex;align-items:center;justify-content:center;gap:14px}}.swipe-btn{{display:grid;place-items:center;border-radius:999px;border:0;background:#fff;box-shadow:0 10px 28px rgba(30,38,52,.16);font:950 15px/1 system-ui;cursor:pointer;height:52px;padding:0 28px}}.swipe-btn.no{{color:#ff4458;box-shadow:inset 0 0 0 1px #f0d8dc,0 10px 28px rgba(30,38,52,.13)}}.swipe-btn.yes{{background:#17130f;color:#fff}}
.empty{{width:min(386px,calc(100vw - 24px));height:clamp(500px,68svh,620px);margin:0 auto;border:1px dashed #d7d9df;border-radius:22px;display:grid;place-items:center;text-align:center;padding:30px;color:#6e737d;background:#fff}}.empty[hidden]{{display:none}}.empty h2{{font:900 34px/.95 Georgia,serif;margin:0 0 8px;color:#1b1b1f}}
.hint{{display:none}}.mini{{margin-top:0;background:rgba(255,255,255,.78);border:1px solid #e8e2d8;border-radius:24px;padding:12px;box-shadow:0 18px 42px rgba(30,25,18,.08)}}.mini h2{{font:950 12px/1 system-ui;letter-spacing:.12em;text-transform:uppercase;margin:0 0 10px;color:#8a8072}}.mini-rail{{display:flex;gap:8px;overflow-x:auto;padding-bottom:2px;-webkit-overflow-scrolling:touch;scroll-snap-type:x mandatory;scrollbar-width:none}}.mini-rail::-webkit-scrollbar{{display:none}}.mini-card{{flex:0 0 auto;min-width:104px;min-height:62px;scroll-snap-align:start;text-decoration:none;background:#fff8ec;border:1px solid #eadfce;border-radius:18px;padding:10px 12px;color:#17130f;box-shadow:0 8px 20px rgba(21,28,40,.05)}}.mini-card span{{font-size:18px}}.mini-card strong{{display:block;font:950 13px/1.05 system-ui;margin-top:7px;white-space:nowrap}}
@media(max-height:780px){{.tinderbar{{height:48px}}.stage,.empty{{height:clamp(455px,65svh,535px)}}.action-dock{{height:64px}}.copy h2{{font-size:30px}}.copy p{{font-size:14.5px;-webkit-line-clamp:3}}}}
@media(prefers-reduced-motion:reduce){{.deck-card{{transition:none}}}}
</style></head><body><main class='app'>
<header class='tinderbar'><a href='/output/learn/profile.html' aria-label='Profile'>👤</a><div class='brand'>LifeOS</div><a href='/output/learn/skill-tree.html' aria-label='Knowledge graph'>⚙</a></header>
<section class='stage' data-deck-stage>{fallback_cards}</section><section class='empty' data-empty hidden><div><h2>No cards left.</h2><p>Pick another lane or come back tomorrow.</p></div></section>
<div class='action-dock' aria-label='Swipe actions'><button class='swipe-btn no' type='button' data-global-no aria-label='No'>No</button><button class='swipe-btn yes' type='button' data-global-yes aria-label='Read'>Read</button></div>
<section class='mini'><h2>Explore</h2><div class='mini-rail'><a class='mini-card' href='/hub'><span>🏰</span><strong>Hub</strong></a><a class='mini-card' href='/output/learn/skill-tree.html'><span>🧠</span><strong>Graph</strong></a><a class='mini-card' href='/output/learn/learning-system.html'><span>⚡</span><strong>Training</strong></a><a class='mini-card' href='/output/learn/curriculum.html'><span>🗺️</span><strong>Curriculum</strong></a>{game_cards}</div></section>
</main><script>window.LIFEOS_REC_CATALOG={rec_data};</script>{recommendation_js}</body></html>"""


def build(today: date | None = None) -> dict[str, Any]:
    today = today or date.today()
    OUT.mkdir(parents=True, exist_ok=True)
    day_label = today.strftime("%A, %B %d").replace(" 0", " ")
    library = lesson_library()
    # Render the entire library so every lesson is reachable by URL (cached images
    # keep this cheap); the index features today's rotating set.
    for l in library:
        (OUT / f"{l['id']}.html").write_text(render_lesson(l, day_label), encoding="utf-8")
    if build_skill_tree:
        build_skill_tree()
    if build_learning_engine:
        build_learning_engine()
    featured = daily_set(today)
    (OUT / "index.html").write_text(render_index(featured, library, today), encoding="utf-8")
    (OUT / "profile.html").write_text(render_profile_page(), encoding="utf-8")
    (OUT / "sync-config.js").write_text(sync_config_js(), encoding="utf-8")
    if render_curriculum_page:
        (OUT / "curriculum.html").write_text(render_curriculum_page(), encoding="utf-8")
    manifest = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "date": today.isoformat(),
        "lessons": [
            {"id": l["id"], "title": l["title"], "emoji": l["emoji"],
             "minutes": l["minutes"], "url": f"/output/learn/{l['id']}.html"}
            for l in featured
        ],
        "library_count": len(library),
        "index": "/learn",
    }
    (OUT / "today.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="LifeOS interactive morning lessons")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("build", help="Generate today's lesson set into output/learn/")
    sub.add_parser("list", help="List the lesson library")
    args = parser.parse_args()
    if args.cmd == "build":
        print(json.dumps(build(), indent=2))
        return 0
    if args.cmd == "list":
        print(json.dumps([{"id": l["id"], "title": l["title"]} for l in lesson_library()], indent=2))
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
