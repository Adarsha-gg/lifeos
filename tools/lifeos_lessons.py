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
.herowrap{margin:6px 0 0;border-radius:22px;overflow:hidden;border:1px solid var(--line);position:relative;background:var(--card)}
.herowrap img,.herowrap svg{display:block;width:100%;height:240px;object-fit:cover}
.credit{position:absolute;right:8px;bottom:8px;font:500 11px/1.2 system-ui;color:#eaffef;background:rgba(0,0,0,.45);padding:3px 8px;border-radius:7px;max-width:70%;text-align:right}
.kicker{font:700 12px/1 system-ui;letter-spacing:.16em;text-transform:uppercase;color:var(--accent);margin:22px 0 6px}
h1{font-size:36px;line-height:1.12;margin:.1em 0 .15em}
.sub{color:var(--muted);font-size:19px;margin:0}
.meta{font:600 13px/1 system-ui;color:var(--muted);display:flex;gap:16px;margin:14px 0 20px;flex-wrap:wrap}
.lead{font-size:20px}
.lead::first-letter{font-size:3.3em;float:left;line-height:.78;padding:6px 10px 0 0;color:var(--accent);font-weight:700}
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
.game{border:1px solid var(--accent);border-radius:20px;background:linear-gradient(180deg,#10271b,#0d1813);padding:20px;margin:30px 0}
.game .tag{font:700 12px/1 system-ui;letter-spacing:.14em;text-transform:uppercase;color:var(--accent)}
.gprompt{font-size:19px;font-weight:700;margin:8px 0 14px}
.olist{list-style:none;margin:0;padding:0}
.olist li{display:flex;align-items:center;justify-content:space-between;gap:10px;background:#0b130f;border:1px solid var(--line);border-radius:12px;padding:11px 12px;margin:8px 0;font:600 17px system-ui}
.olist .ctrl{display:flex;flex:none}
.olist .ctrl button{font:700 17px/1 system-ui;background:none;border:1px solid var(--line);color:var(--accent);border-radius:9px;width:38px;height:38px;margin-left:6px;cursor:pointer}
.gin{width:100%;font:inherit;font-size:18px;border:1px solid var(--line);background:#0b130f;color:var(--fg);border-radius:12px;padding:13px;margin:2px 0 4px}
.check{font:700 15px/1 system-ui;background:var(--accent);color:#04140b;border:none;border-radius:12px;padding:13px 18px;cursor:pointer;margin-top:8px}
.gresult{margin-top:14px;font-family:system-ui;font-size:16px;line-height:1.6;color:#cfe7da;display:none}
.gresult.show{display:block}
.gresult .ok{color:var(--accent);font-weight:700}
.gresult .no{color:#ff9b8a;font-weight:700}
.reveal{border:1px dashed #2c5e44;border-radius:14px;padding:14px 18px;background:#0b130f;margin:20px 0}
.reveal button{font:700 14px/1.3 system-ui;background:none;border:none;color:var(--accent);cursor:pointer;padding:0;text-align:left}
.reveal .txt{display:none;margin-top:10px;color:#cfe7da;font-size:17px}
.reveal.show .txt{display:block}
.foot{margin-top:34px;padding-top:18px;border-top:1px solid var(--line);font-family:system-ui;color:var(--muted);font-size:15px}
.foot a{color:var(--accent)}
.pill{display:inline-block;font:700 12px/1 system-ui;color:#04140b;background:var(--accent);border-radius:999px;padding:6px 11px}
.playcta{display:flex;align-items:center;gap:14px;text-decoration:none;color:var(--fg);border:1px solid var(--c,#46d17a);border-radius:18px;padding:18px;margin:24px 0 4px;background:linear-gradient(110deg,color-mix(in srgb,var(--c,#46d17a) 16%,transparent),var(--card))}
.playcta .pc_k{font:800 12px/1 system-ui;letter-spacing:.1em;text-transform:uppercase;color:var(--c,#46d17a)}
.playcta .pc_t{font:800 21px/1.1 system-ui;margin:6px 0 3px}
.playcta .pc_s{font:600 14px/1.3 system-ui;color:var(--muted)}
.playcta .pc_go{margin-left:auto;font-size:24px;color:var(--c,#46d17a)}
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
.door.picked{border-color:var(--accent);box-shadow:0 0 0 3px rgba(70,209,122,.25)}
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
function level(x){return Math.floor(Math.sqrt(x/110))+1}
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
        "Finally, write one objection, one application, and one uncertainty you would need to verify before teaching it to someone else.</p>"
        "</section>"
    )

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
.completebar{{display:flex;align-items:center;justify-content:space-between;gap:12px;border:1px solid var(--line);border-left:5px solid var(--accent);border-radius:16px;background:var(--card);padding:14px 16px;margin:24px 0}}
.completebar b{{display:block;font:800 17px/1.2 system-ui}}.completebar span{{display:block;color:var(--muted);font:650 13px/1.35 system-ui;margin-top:4px}}
.completebar button{{border:0;border-radius:12px;background:var(--accent);color:#051018;font:900 14px/1 system-ui;padding:12px 14px;cursor:pointer;white-space:nowrap}}
.completebar button:disabled{{opacity:.65;cursor:default}}
.readingNote,.questionBlock,.sourceTrail{{border:1px solid var(--line);border-radius:18px;background:var(--card);padding:18px 20px;margin:24px 0}}
.readingNote h3,.questionBlock h3,.sourceTrail h3{{margin:0 0 8px;font:850 22px/1.1 system-ui;color:var(--fg)}}
.readingNote p,.questionBlock p,.sourceTrail p{{margin:0 0 10px;color:#cfe7da;font-size:16px;line-height:1.55}}
.questionBlock ul,.sourceTrail ul{{margin:0;padding-left:20px;color:#dceddf;font-size:16px;line-height:1.55}}
.sourceTrail li+li,.questionBlock li+li{{margin-top:7px}}
.sourceTrail a{{color:#9fd5ff;font-weight:850}}
.sourceTrail span{{display:block;color:var(--muted);font-size:13px;margin-top:2px}}
@media(max-width:640px){{.completebar{{align-items:flex-start;flex-direction:column}}.completebar button{{width:100%}}}}
:root{{--accent:{accent}}}</style></head>
<body><div class='wrap'>
<div class='topbar'><a href='/learn'>&larr; Today's lessons</a><a href='/output/learn/skill-tree.html'>Knowledge graph</a><a href='/output/learn/learning-system.html'>Training queue</a><span>{esc(day)}</span></div>
{_hero_html(lesson)}
<div class='kicker'>{kicker}</div>
<h1>{esc(lesson['title'])}</h1>
<p class='sub'>{esc(lesson['subtitle'])}</p>
<div class='meta'><span>⏱ {esc(max(5, int(lesson.get('minutes') or 5)))} min read</span><span>Worth more than the feed</span></div>
<p class='lead'>{lesson['lead']}</p>
{_sections_html(lesson['sections'])}
{_reading_note_html(lesson)}
{_ideas_html(lesson['ideas'])}
{curriculum_block}
{_thinking_questions_html(lesson)}
{_game_html(lesson['game'])}
<div class='reveal'><button>💡 Did you know? Tap to reveal</button><div class='txt'>{lesson['did_you_know']}</div></div>
{_play_cta(lesson['id'])}
<div class='completebar'><div><b>Lock this node into your knowledge graph</b><span data-lifeos-level>Level 1 / 0 XP</span></div><button data-complete-node>Mark complete</button></div>
{_source_trail_html(lesson)}
<div class='foot'>
<p>{esc(lesson.get('next',''))}</p>
<p>Stuck or curious? Ask your LifeOS agent to go deeper on anything here — it's your teacher.</p>
</div>
</div>
<script>window.LIFEOS_NODE={json.dumps(progress_node)};</script><script>{PROGRESS_JS}</script><script>{BASE_JS}</script></body></html>"""


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



def render_index(daily: list[dict[str, Any]], library: list[dict[str, Any]], today: date) -> str:
    """Render /learn as a generated blog/publication issue."""
    day = today.strftime("%A, %B %d").replace(" 0", " ")
    featured = daily[0]
    side_posts = "".join(
        f"<a class='post' href='/output/learn/{esc(l['id'])}.html' style='--c:{l['accent']}'>"
        f"<span class='post-k'>{esc(l['emoji'])} {esc(l['minutes'])} min read</span>"
        f"<strong>{esc(l['title'])}</strong><span>{esc(l['subtitle'])}</span></a>"
        for l in daily[1:]
    )
    daily_ids = {l["id"] for l in daily}
    archive_rows = "".join(
        f"<a class='archive-row' href='/output/learn/{esc(l['id'])}.html' style='--c:{l['accent']}'>"
        f"<span>{esc(l['emoji'])}</span><strong>{esc(l['title'])}</strong><em>{esc(l['minutes'])} min</em></a>"
        for l in library
        if l["id"] not in daily_ids
    )
    archive = f"<section class='archive'><h2>Archive</h2><div>{archive_rows}</div></section>" if archive_rows else ""
    games = "".join(
        f"<a class='game' href='{esc(g['url']) if 'url' in g else '/output/learn/'+esc(g['id'])+'.html'}' style='--c:{g['accent']}'>"
        f"<span>{esc(g['emoji'])}</span><strong>{esc(g['title'])}</strong><small>{esc(g['blurb'])}</small></a>"
        for g in GAME_CATALOG
    )
    games_html = (
        "<section class='arcade'><div class='section-head'><h2>Practice Lab</h2>"
        "<p>Games generated from the ideas, not quiz cards.</p></div>"
        f"<div class='games'>{games}</div></section>"
    ) if games else ""
    graph_link = (
        "<a class='graph-link' href='/output/learn/skill-tree.html'>"
        "<span>Personal Knowledge Graph</span><strong>Open your learning map</strong>"
        "<em>Only learned nodes enter your graph; the library stays underneath.</em></a>"
        "<a class='graph-link engine' href='/output/learn/learning-system.html'>"
        "<span>Training Queue</span><strong>Review, frontier, mixed practice</strong>"
        "<em>Math Academy-style scheduling over your personal graph.</em></a>"
    )
    curriculum_tracks = track_catalog()
    curriculum_html = ""
    if curriculum_tracks:
        track_cards = []
        for tr in curriculum_tracks:
            unit_links = "".join(
                f"<a class='cur-unit' href='{esc(u['url'])}'>{esc(u['title'])}"
                f" <em>{esc(u.get('minutes', ''))}m</em></a>"
                for u in tr.get("units", [])
            )
            track_cards.append(
                f"<div class='cur-track' style='--c:{tr['color']}'>"
                f"<div class='cur-track-head'><strong>{esc(tr['name'])}</strong>"
                f"<span>{tr['unit_count']} units · {esc(tr.get('domain', ''))}</span></div>"
                f"<div class='cur-units'>{unit_links}</div></div>"
            )
        curriculum_html = (
            "<section class='curriculum'><div class='section-head'>"
            "<h2>Curriculum / Mastery Tracks</h2>"
            "<p>Prerequisite skill tree, deep sections, thinking questions — original LifeOS infrastructure. "
            "<a href='/output/learn/curriculum.html'>Full curriculum overview →</a></p>"
            "</div>"
            f"<div class='cur-tracks'>{''.join(track_cards)}</div></section>"
        )
    return f"""<!doctype html><html lang='en'><head>
<meta charset='utf-8'>
<meta name='viewport' content='width=device-width,initial-scale=1,viewport-fit=cover'>
<meta name='color-scheme' content='light'>
<title>LifeOS Field Notes</title>
<style>
*{{box-sizing:border-box}}html,body{{margin:0;min-height:100%;overflow-x:hidden;background:#f7f5f0;color:#151719;font-family:Inter,system-ui,-apple-system,sans-serif}}a{{color:inherit}}
.wrap{{width:min(1080px,calc(100% - 32px));margin:0 auto;padding:18px 0 46px}}
.topbar{{display:flex;align-items:center;justify-content:space-between;gap:14px;border-bottom:1px solid #d8d3c8;padding:0 0 14px;margin-bottom:28px;color:#5f665f;font:800 13px/1 system-ui;flex-wrap:wrap}}
.topbar a{{text-decoration:none;color:#5f665f}}.mast{{display:grid;grid-template-columns:1fr auto;gap:20px;align-items:end;border-bottom:3px solid #151719;padding-bottom:22px;margin-bottom:26px}}
.mast h1{{font:800 clamp(44px,8vw,86px)/.9 Georgia,serif;margin:0;color:#151719;letter-spacing:0}}.mast p{{margin:12px 0 0;color:#4e5651;font:500 18px/1.55 Georgia,serif;max-width:720px}}
.issue{{font:800 12px/1 system-ui;letter-spacing:.16em;text-transform:uppercase;color:#6a5b35;text-align:right}}
.bloggrid{{display:grid;grid-template-columns:minmax(0,1.35fr) minmax(280px,.65fr);gap:24px;align-items:start}}
.feature{{display:grid;grid-template-columns:120px 1fr;gap:22px;text-decoration:none;color:#151719;border-bottom:1px solid #d8d3c8;padding-bottom:24px}}.feature .emoji{{font-size:92px;line-height:1;filter:drop-shadow(0 12px 20px rgba(21,23,25,.12))}}
.feature-k{{font:800 12px/1 system-ui;letter-spacing:.14em;text-transform:uppercase;color:#a76d16}}.feature h2{{font:800 clamp(34px,5vw,58px)/.95 Georgia,serif;margin:8px 0 12px;color:#151719;letter-spacing:0}}
.feature p{{font:500 19px/1.58 Georgia,serif;color:#3f4743;margin:0 0 12px}}.readline{{font:800 13px/1 system-ui;color:#a76d16}}
.side{{border-left:1px solid #d8d3c8;padding-left:22px}}.section-head h2,.archive h2{{font:800 22px/1 Georgia,serif;margin:0 0 4px;color:#151719}}.section-head p{{margin:0 0 14px;color:#636b66;font:600 14px/1.45 system-ui}}
.post{{display:block;text-decoration:none;color:#151719;border-top:1px solid #d8d3c8;padding:14px 0}}.post-k{{display:block;font:800 11px/1 system-ui;letter-spacing:.12em;text-transform:uppercase;color:var(--c)}}.post strong{{display:block;font:800 22px/1.08 Georgia,serif;margin:6px 0;color:#151719}}.post span:last-child{{display:block;color:#59605c;font:500 15px/1.45 Georgia,serif}}
.levelbox{{display:flex;align-items:center;justify-content:space-between;gap:12px;border:1px solid #d8d3c8;background:#fffaf0;padding:14px;margin:22px 0}}.levelbox b{{display:block;font:900 19px/1 system-ui}}.levelbox span{{display:block;color:#65665f;font:700 12px/1.35 system-ui;margin-top:5px}}.levelbar{{width:170px;height:10px;background:#e0ddd3;border-radius:999px;overflow:hidden}}.levelbar i{{display:block;width:0;height:100%;background:linear-gradient(90deg,#1f9d78,#4d7cff,#d86b8a)}}
.graph-link{{display:block;text-decoration:none;color:#151719;border:1px solid #151719;background:#fff;padding:14px;margin:16px 0 0}}.graph-link.engine{{border-color:#1f9d78}}.graph-link span{{font:800 11px/1 system-ui;letter-spacing:.12em;text-transform:uppercase;color:#4d7cff}}.graph-link.engine span{{color:#1f9d78}}.graph-link strong{{display:block;font:800 22px/1 Georgia,serif;margin:6px 0}}.graph-link em{{display:block;font:600 13px/1.35 system-ui;color:#5f665f;font-style:normal;overflow-wrap:break-word}}
.arcade,.archive,.curriculum{{margin-top:34px;border-top:3px solid #151719;padding-top:18px}}.games{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}}.game{{display:block;text-decoration:none;color:#151719;background:#fff;border:1px solid #d8d3c8;border-left:4px solid var(--c);padding:13px}}.game span{{font-size:24px}}.game strong{{display:block;font:800 17px/1.1 system-ui;margin:7px 0 4px}}.game small{{display:block;color:#5f665f;font:600 13px/1.35 system-ui}}
.cur-tracks{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}}.cur-track{{background:#fff;border:1px solid #d8d3c8;border-left:4px solid var(--c);padding:14px}}.cur-track-head strong{{display:block;font:800 18px/1.1 system-ui}}.cur-track-head span{{display:block;color:#5f665f;font:650 12px/1.35 system-ui;margin-top:4px}}.cur-units{{margin-top:10px}}.cur-unit{{display:block;text-decoration:none;color:#151719;font:750 15px/1.35 system-ui;padding:7px 0;border-top:1px solid #ece8df}}.cur-unit em{{font:700 11px/1 system-ui;color:#77736a;font-style:normal;margin-left:6px}}
.archive-row{{display:grid;grid-template-columns:32px 1fr auto;gap:12px;align-items:center;text-decoration:none;color:#151719;border-top:1px solid #d8d3c8;padding:12px 0}}.archive-row strong{{font:750 17px/1.2 system-ui}}.archive-row em{{font:700 12px/1 system-ui;color:#77736a;font-style:normal}}.foot{{border-top:1px solid #d8d3c8;color:#676b66;margin-top:32px;padding-top:16px;font:600 13px/1.45 system-ui}}
@media(max-width:760px){{.wrap{{width:min(620px,calc(100% - 32px));overflow:hidden}}.topbar{{justify-content:flex-start}}.mast{{display:block}}.mast h1{{font-size:46px}}.mast p{{display:block;width:31ch;max-width:100%;white-space:normal;overflow-wrap:break-word;font-size:17px}}.issue{{text-align:left;margin-top:20px}}.bloggrid{{display:block}}.feature{{display:block;min-width:0}}.feature article{{display:block;width:100%;min-width:0}}.feature h2{{font-size:36px;max-width:13ch;overflow-wrap:break-word}}.feature p{{display:block;width:31ch;max-width:100%;white-space:normal;font-size:17px;overflow-wrap:break-word}}.feature .emoji{{font-size:72px;margin-bottom:8px}}.side{{border-left:0;padding-left:0;margin-top:22px}}.games,.cur-tracks{{grid-template-columns:1fr}}.levelbox{{align-items:flex-start;flex-direction:column}}.levelbar{{width:100%}}}}
</style></head><body><div class='wrap'>
<div class='topbar'><span>LifeOS Field Notes</span><a href='/output/learn/skill-tree.html'>Knowledge graph</a><a href='/m'>Control</a></div>
<header class='mast'><div><h1>Field Notes</h1><p>Generated essays for the morning: read the idea like a blog post, then use a game to make it stick.</p></div><div class='issue'>{esc(day)}</div></header>
<main class='bloggrid'><section>
<a class='feature' href='/output/learn/{esc(featured['id'])}.html' style='--c:{featured['accent']}'>
<div class='emoji'>{esc(featured['emoji'])}</div><article><div class='feature-k'>Today's lead essay</div><h2>{esc(featured['title'])}</h2><p>{esc(featured['subtitle'])}</p><div class='readline'>{esc(featured['minutes'])} min read -></div></article></a>
<div class='levelbox'><div><b data-level-label>Level 1</b><span data-xp-label>0 XP earned in this browser</span></div><div class='levelbar'><i data-xp-bar></i></div></div>
{graph_link}
</section><aside class='side'><div class='section-head'><h2>Today's Posts</h2><p>The rest of this morning's issue.</p></div>{side_posts}</aside></main>
{archive}
{curriculum_html}
{games_html}
<div class='foot'>A fresh issue is generated every morning by LifeOS. Each article points toward practice, not passive reading.</div>
</div><script>
(function(){{
const KEY='lifeos.learning.progress.v1';
function load(){{try{{return JSON.parse(localStorage.getItem(KEY)||'{{}}')}}catch{{return {{}}}}}}
function xp(p){{return Object.values(p.done||{{}}).reduce((s,n)=>s+(+n.xp||0),0)}}
function level(x){{return Math.floor(Math.sqrt(x/110))+1}}
function next(l){{return l*l*110}}
const total=xp(load()),lvl=level(total),prev=next(lvl-1),goal=next(lvl),pct=Math.max(0,Math.min(100,((total-prev)/(goal-prev))*100));
document.querySelector('[data-level-label]').textContent='Level '+lvl;
document.querySelector('[data-xp-label]').textContent=total+' XP earned in this browser';
document.querySelector('[data-xp-bar]').style.width=pct+'%';
}})();
</script></body></html>"""


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
