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

OUT = VAULT_ROOT / "output" / "learn"
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
]


# --------------------------------------------------------------------------- #
# Styling + behaviour (one stylesheet + one script powers every lesson).
# --------------------------------------------------------------------------- #
BASE_CSS = """
:root{--bg:#0b0f0d;--card:#121b16;--line:#22352b;--fg:#eaf6ef;--muted:#8fae9f;--accent:#46d17a}
*{box-sizing:border-box}
body{margin:0;font-family:Georgia,'Iowan Old Style',serif;background:var(--bg);color:var(--fg);line-height:1.72;-webkit-text-size-adjust:100%}
.wrap{max-width:720px;margin:0 auto;padding:0 20px 110px}
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
        items = list(game["items"])
        correct = ",".join(i[0] for i in items)
        shown = items[::-1]  # deterministic non-trivial starting order (reversed)
        lis = "".join(
            f"<li data-id='{esc(i[0])}'><span>{esc(i[1])}</span>"
            f"<span class='ctrl'><button class='up' aria-label='up'>▲</button>"
            f"<button class='dn' aria-label='down'>▼</button></span></li>"
            for i in shown
        )
        return (f"<div class='game order' data-correct='{esc(correct)}'>"
                f"<div class='tag'>🎮 Challenge · reorder</div><div class='gprompt'>{prompt}</div>"
                f"<ul class='olist'>{lis}</ul><button class='check'>Check my order</button>"
                f"<div class='gresult'><span class='status'></span> <span class='detail'>{game['explain']}</span></div></div>")
    if gtype == "estimate":
        detail = f"Answer: <b>{esc(game['answer'])} {esc(game['unit'])}</b>. {game['reveal']}"
        return (f"<div class='game estimate' data-answer='{esc(game['answer'])}'>"
                f"<div class='tag'>🎮 Challenge · estimate</div><div class='gprompt'>{prompt}</div>"
                f"<input class='gin' type='number' inputmode='numeric' placeholder='Your reasoned guess'>"
                f"<button class='check'>Reveal</button>"
                f"<div class='gresult'><span class='status'></span> <span class='detail'>{detail}</span></div></div>")
    # ponder
    return (f"<div class='game ponder'>"
            f"<div class='tag'>🎮 Challenge · think it through</div><div class='gprompt'>{prompt}</div>"
            f"<button class='check'>Reveal the answer</button>"
            f"<div class='gresult'><span class='status'></span> <span class='detail'>{game['reveal']}</span></div></div>")


def _hero_html(lesson: dict) -> str:
    uri, credit = wiki_photo(lesson["hero_article"], width=1000) if lesson.get("hero_article") else (None, "")
    if uri:
        return (f"<div class='herowrap'><img src='{uri}' alt='{esc(lesson['title'])}'>"
                f"<div class='credit'>{esc(credit)}</div></div>")
    return f"<div class='herowrap'>{_svg_hero(lesson['accent'], lesson['emoji'])}</div>"


def render_lesson(lesson: dict[str, Any], day: str) -> str:
    accent = lesson["accent"]
    src_label, src_url = lesson["source"]
    return f"""<!doctype html><html lang='en'><head>
<meta charset='utf-8'>
<meta name='viewport' content='width=device-width,initial-scale=1,viewport-fit=cover'>
<meta name='color-scheme' content='dark'>
<title>{esc(lesson['title'])} — LifeOS Learn</title>
<style>{BASE_CSS}
:root{{--accent:{accent}}}</style></head>
<body><div class='wrap'>
<div class='topbar'><a href='/learn'>&larr; Today's lessons</a><span>{esc(day)}</span></div>
{_hero_html(lesson)}
<div class='kicker'>{esc(lesson['emoji'])} Morning Lesson</div>
<h1>{esc(lesson['title'])}</h1>
<p class='sub'>{esc(lesson['subtitle'])}</p>
<div class='meta'><span>⏱ {esc(lesson['minutes'])} min read</span><span>Worth more than the feed</span></div>
<p class='lead'>{lesson['lead']}</p>
{_sections_html(lesson['sections'])}
{_ideas_html(lesson['ideas'])}
{_game_html(lesson['game'])}
<div class='reveal'><button>💡 Did you know? Tap to reveal</button><div class='txt'>{lesson['did_you_know']}</div></div>
<div class='foot'>
<p><span class='pill'>Go deeper</span> &nbsp; Primary source: <a href='{esc(src_url)}' target='_blank' rel='noopener'>{src_label}</a></p>
<p>{esc(lesson.get('next',''))}</p>
<p>Stuck or curious? Ask your LifeOS agent to go deeper on anything here — it's your teacher.</p>
</div>
</div>
<script>{BASE_JS}</script></body></html>"""


def daily_set(today: date) -> list[dict[str, Any]]:
    """Featured history lesson first, then 2 rotating picks so each day differs."""
    by_id = {l["id"]: l for l in LESSONS}
    featured = by_id["story-of-civilization"]
    rest = [l for l in LESSONS if l["id"] != featured["id"]]
    n = len(rest)
    start = today.toordinal() % n
    rotated = [rest[(start + i) % n] for i in range(min(2, n))]
    return [featured, *rotated]


def render_index(lessons: list[dict[str, Any]], today: date) -> str:
    day = today.strftime("%A, %B %d").replace(" 0", " ")
    cards = []
    for l in lessons:
        cards.append(
            f"<a class='lcard' href='/output/learn/{esc(l['id'])}.html' style='--c:{l['accent']}'>"
            f"<div class='lemoji'>{esc(l['emoji'])}</div><div class='ltext'>"
            f"<div class='ltitle'>{esc(l['title'])}</div><div class='lsub'>{esc(l['subtitle'])}</div>"
            f"<div class='lmeta'>⏱ {esc(l['minutes'])} min · tap to read</div></div></a>"
        )
    return f"""<!doctype html><html lang='en'><head>
<meta charset='utf-8'>
<meta name='viewport' content='width=device-width,initial-scale=1,viewport-fit=cover'>
<meta name='color-scheme' content='dark'>
<title>LifeOS — Learn this morning</title>
<style>{BASE_CSS}
.lcard{{display:flex;gap:14px;align-items:center;text-decoration:none;color:var(--fg);border:1px solid var(--line);border-left:5px solid var(--c);border-radius:18px;padding:16px;margin:14px 0;background:var(--card);transition:.15s}}
.lcard:hover{{transform:translateY(-2px);border-color:var(--c)}}
.lemoji{{font-size:40px;line-height:1}}
.ltitle{{font-size:22px;font-weight:700;font-family:Georgia,serif}}
.lsub{{color:var(--muted);font-size:16px;margin:3px 0 7px;font-family:system-ui}}
.lmeta{{font:600 13px/1 system-ui;color:var(--c)}}
.intro{{color:var(--muted);font-size:18px}}
</style></head><body><div class='wrap'>
<div class='topbar'><span>🌅 LifeOS Learn</span><a href='/m'>Control →</a></div>
<div class='kicker'>{esc(day)}</div>
<h1>Learn something this morning</h1>
<p class='intro'>Three short, beautifully readable lessons with real photos — and a thinking game at the end of each. Pick one instead of the feed.</p>
{''.join(cards)}
<div class='foot'><p>A fresh set is generated every morning by LifeOS. Each lesson works offline once it loads.</p></div>
</div></body></html>"""


def build(today: date | None = None) -> dict[str, Any]:
    today = today or date.today()
    OUT.mkdir(parents=True, exist_ok=True)
    lessons = daily_set(today)
    day_label = today.strftime("%A, %B %d").replace(" 0", " ")
    for l in lessons:
        (OUT / f"{l['id']}.html").write_text(render_lesson(l, day_label), encoding="utf-8")
    (OUT / "index.html").write_text(render_index(lessons, today), encoding="utf-8")
    manifest = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "date": today.isoformat(),
        "lessons": [
            {"id": l["id"], "title": l["title"], "emoji": l["emoji"],
             "minutes": l["minutes"], "url": f"/output/learn/{l['id']}.html"}
            for l in lessons
        ],
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
        print(json.dumps([{"id": l["id"], "title": l["title"]} for l in LESSONS], indent=2))
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
