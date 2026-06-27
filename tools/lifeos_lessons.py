#!/usr/bin/env python3
"""LifeOS morning micro-lessons.

Generates a small set of self-contained, interactive HTML lessons each day so
the user reaches for something to *learn* in the morning instead of doom
scrolling. Output lands in the vault at output/learn/ and is served by
lifeos_server.py at /learn (and the static /output/learn/ path).

Build:  python tools/lifeos_lessons.py build
List:   python tools/lifeos_lessons.py list
"""
from __future__ import annotations

import argparse
import html
import json
from datetime import date, datetime
from typing import Any

from lifeos_paths import VAULT_ROOT

OUT = VAULT_ROOT / "output" / "learn"


# --------------------------------------------------------------------------- #
# Shared look & behaviour (one stylesheet + one script powers every lesson).
# --------------------------------------------------------------------------- #
BASE_CSS = """
:root{--bg:#070b09;--card:#0e1813;--line:#1c3327;--fg:#e7fff1;--muted:#7ea592;--accent:#39ff88}
*{box-sizing:border-box}
body{margin:0;font-family:'Iowan Old Style','Palatino Linotype',Georgia,system-ui,serif;background:var(--bg);color:var(--fg);line-height:1.6;-webkit-text-size-adjust:100%}
.wrap{max-width:680px;margin:0 auto;padding:0 18px 96px}
.topbar{position:sticky;top:0;background:linear-gradient(var(--bg),rgba(7,11,9,.86));backdrop-filter:blur(6px);padding:12px 0;font:600 13px/1 system-ui;display:flex;justify-content:space-between;align-items:center;z-index:9}
.topbar a{color:var(--muted);text-decoration:none}
.hero{margin:8px 0 4px;border-radius:22px;overflow:hidden;border:1px solid var(--line);background:var(--card)}
.hero svg{display:block;width:100%;height:auto}
.kicker{font:700 12px/1 system-ui;letter-spacing:.14em;text-transform:uppercase;color:var(--accent);margin:22px 0 6px}
h1{font-size:34px;line-height:1.15;margin:.1em 0 .2em}
.sub{color:var(--muted);font-size:18px;margin:0 0 6px}
.meta{font:600 13px/1 system-ui;color:var(--muted);display:flex;gap:14px;margin:10px 0 4px}
.lead{font-size:19px}
h2{font-size:13px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);font-family:system-ui;margin:34px 0 10px}
p{margin:0 0 14px}
a.cite{color:var(--accent);text-decoration:none;border-bottom:1px dashed #2c5e44}
/* expandable section */
.acc{border:1px solid var(--line);border-radius:14px;margin:8px 0;overflow:hidden;background:var(--card)}
.acc>summary{cursor:pointer;list-style:none;padding:14px 16px;font-weight:700;display:flex;justify-content:space-between;align-items:center}
.acc>summary::-webkit-details-marker{display:none}
.acc>summary::after{content:'+';color:var(--accent);font-size:22px;font-family:system-ui}
.acc[open]>summary::after{content:'\\2013'}
.acc .body{padding:0 16px 14px;color:#cdeede}
/* timeline */
.tl{position:relative;margin:6px 0 6px 8px;padding-left:22px;border-left:2px solid var(--line)}
.tl .node{position:relative;margin:0 0 6px;padding:10px 12px;border-radius:12px;cursor:pointer;transition:background .15s}
.tl .node:hover{background:var(--card)}
.tl .node::before{content:'';position:absolute;left:-30px;top:16px;width:12px;height:12px;border-radius:50%;background:var(--accent);box-shadow:0 0 0 4px var(--bg)}
.tl .yr{font:700 13px/1 system-ui;color:var(--accent)}
.tl .lbl{font-weight:700}
.tl .det{max-height:0;overflow:hidden;color:var(--muted);transition:max-height .25s ease;font-family:system-ui;font-size:15px}
.tl .node.on .det{max-height:200px;margin-top:6px}
/* flashcards */
.cards{display:grid;grid-template-columns:1fr 1fr;gap:10px}
@media(max-width:480px){.cards{grid-template-columns:1fr}}
.flip{perspective:1000px;height:120px;cursor:pointer}
.flip .in{position:relative;width:100%;height:100%;transition:transform .5s;transform-style:preserve-3d}
.flip.on .in{transform:rotateY(180deg)}
.flip .face{position:absolute;inset:0;backface-visibility:hidden;border:1px solid var(--line);border-radius:14px;padding:14px;display:flex;align-items:center;justify-content:center;text-align:center;background:var(--card)}
.flip .front{font-weight:700;font-size:18px}
.flip .back{transform:rotateY(180deg);font-family:system-ui;font-size:15px;color:#cdeede}
.hint{font:600 12px/1 system-ui;color:var(--muted);margin:6px 0 0}
/* quiz */
.quiz{border:1px solid var(--line);border-radius:16px;padding:16px;background:var(--card);margin:10px 0}
.quiz .q{font-weight:700;font-size:18px;margin-bottom:10px}
.opt{display:block;width:100%;text-align:left;border:1px solid var(--line);background:#0b130f;color:var(--fg);border-radius:12px;padding:12px 14px;margin:8px 0;font:inherit;cursor:pointer;transition:.12s}
.opt:hover{border-color:var(--accent)}
.opt.right{border-color:var(--accent);background:#0f2a1c}
.opt.wrong{border-color:#7a2230;background:#241015;opacity:.85}
.why{font-family:system-ui;font-size:15px;color:var(--muted);margin-top:8px;display:none}
.why.show{display:block}
/* reveal */
.reveal{border:1px dashed #2c5e44;border-radius:14px;padding:14px 16px;background:#0b130f;margin:10px 0}
.reveal button{font:700 14px system-ui;background:none;border:none;color:var(--accent);cursor:pointer;padding:0}
.reveal .txt{display:none;margin-top:10px;color:#cdeede}
.reveal.show .txt{display:block}
.foot{margin-top:30px;padding-top:16px;border-top:1px solid var(--line);font-family:system-ui;color:var(--muted);font-size:15px}
.pill{display:inline-block;font:700 12px system-ui;color:#021008;background:var(--accent);border-radius:999px;padding:5px 11px}
"""

BASE_JS = """
// flip cards
document.querySelectorAll('.flip').forEach(function(c){c.addEventListener('click',function(){c.classList.toggle('on');});});
// timeline nodes
document.querySelectorAll('.tl .node').forEach(function(n){n.addEventListener('click',function(){n.classList.toggle('on');});});
// quiz
document.querySelectorAll('.quiz').forEach(function(q){
  var why=q.querySelector('.why');var done=false;
  q.querySelectorAll('.opt').forEach(function(o){
    o.addEventListener('click',function(){
      if(done)return;done=true;
      q.querySelectorAll('.opt').forEach(function(x){
        if(x.dataset.correct==='1')x.classList.add('right');
        else if(x===o)x.classList.add('wrong');
      });
      if(why)why.classList.add('show');
    });
  });
});
// reveal
document.querySelectorAll('.reveal button').forEach(function(b){
  b.addEventListener('click',function(){b.parentElement.classList.toggle('show');});
});
"""


# --------------------------------------------------------------------------- #
# Lesson library. Each lesson is plain data; the renderer turns it into HTML.
# --------------------------------------------------------------------------- #
def _svg(accent: str, glyph: str, motif: str) -> str:
    """A lightweight, always-renders hero illustration (no external images)."""
    return (
        f"<svg viewBox='0 0 680 260' xmlns='http://www.w3.org/2000/svg'>"
        f"<defs><linearGradient id='g' x1='0' y1='0' x2='1' y2='1'>"
        f"<stop offset='0' stop-color='{accent}' stop-opacity='.32'/>"
        f"<stop offset='1' stop-color='#070b09'/></linearGradient></defs>"
        f"<rect width='680' height='260' fill='url(#g)'/>"
        f"{motif}"
        f"<text x='40' y='168' font-size='120'>{glyph}</text></svg>"
    )


LESSONS: list[dict[str, Any]] = [
    {
        "id": "story-of-civilization",
        "emoji": "🏛️",
        "accent": "#e0a851",
        "title": "How Civilization Began",
        "subtitle": "Foragers to farmers to the first cities — the 10,000-year leap.",
        "minutes": 5,
        "motif": "<g fill='none' stroke='#e0a851' stroke-opacity='.5' stroke-width='3'>"
                 "<path d='M470 200 v-70 l40-26 40 26 v70'/><path d='M470 130 h80'/>"
                 "<path d='M560 200 v-50 l30-20 30 20 v50'/></g>",
        "lead": "For 300,000 years humans foraged in small bands. Then, in a geological blink, "
                "we settled, farmed, built cities, and started writing. Almost everything you "
                "call <em>civilization</em> was invented in the last 5% of our story.",
        "sections": [
            ("The bet that changed everything",
             "Around <b>9500 BCE</b> in the Fertile Crescent, humans began planting wild wheat "
             "and barley instead of just gathering it. Farming was actually <i>harder</i> than "
             "foraging and the early diet was worse — but it let far more people live on the "
             "same land. More food meant more people, and people had to stay put to guard the "
             "harvest. The nomad became the villager."),
            ("Why cities were a superpower",
             "Stored grain is stored <b>surplus</b> — and surplus frees people from food. For "
             "the first time some could be full-time potters, priests, soldiers, kings. "
             "Specialization is the engine of every technology since. Uruk in Sumer "
             "(~<b>3500 BCE</b>) may have been the first true city, with tens of thousands of people."),
            ("Writing: civilization's external memory",
             "To track who owed how much grain, Sumerians pressed marks into clay — "
             "<b>cuneiform</b>, ~3200 BCE. It began as accounting, not poetry. But once thought "
             "could be stored outside a human skull, knowledge stopped dying with each generation. "
             "That is the moment history itself starts."),
        ],
        "timeline": [
            ("9600 BCE", "Göbekli Tepe", "Massive carved stone temple built by people who had not yet invented farming or pottery. Worship may have come <i>before</i> the town."),
            ("9500 BCE", "First farming", "Wild wheat and barley domesticated in the Fertile Crescent — the Neolithic Revolution begins."),
            ("7000 BCE", "Çatalhöyük", "A town of ~8,000 in Anatolia, so dense people walked across the rooftops and entered houses through the roof."),
            ("3500 BCE", "Uruk", "Arguably the world's first city. The wheel, the plough and mass-produced pottery appear around now."),
            ("3200 BCE", "Cuneiform", "Sumerian scribes invent writing — first to count grain and beer rations."),
            ("2560 BCE", "Great Pyramid", "A society organized enough to move 2.3 million blocks for one king's tomb."),
        ],
        "cards": [
            ("Neolithic Revolution", "The shift from foraging to farming, ~9500 BCE — the foundation of settled life."),
            ("Fertile Crescent", "Arc of fertile land from the Nile through Mesopotamia where farming first took hold."),
            ("Cuneiform", "The world's earliest writing: wedge marks pressed into clay tablets."),
            ("Surplus", "Stored extra food — the thing that let humans specialize beyond getting fed."),
        ],
        "quiz": [
            ("What did the very first writing mostly record?",
             [("Religious hymns", 0), ("Accounting — grain and rations", 1), ("Royal love letters", 0), ("Laws", 0)],
             "Cuneiform began as bookkeeping. Literature came centuries later."),
            ("Why was farming such a turning point despite being harder work?",
             [("It tasted better", 0), ("It let many more people live on the same land", 1), ("It required no tools", 0), ("It ended all warfare", 0)],
             "Higher food density per acre drove population and permanent settlement."),
        ],
        "did_you_know": "Göbekli Tepe (~9600 BCE) is older than Stonehenge by 6,000 years and older than "
                        "writing, the wheel, and even pottery. It hints that organized religion may have helped "
                        "<i>cause</i> the move to settled life — not the other way around.",
        "source": ("Will Durant — <i>Our Oriental Heritage</i> (The Story of Civilization, Vol. 1, 1935)",
                   "https://archive.org/details/in.ernet.dli.2015.275128"),
        "next": "Tomorrow: how those first city-states grew into empires.",
    },
    {
        "id": "why-the-sky-is-blue",
        "emoji": "🌤️",
        "accent": "#5b9bf0",
        "title": "Why the Sky Is Blue",
        "subtitle": "And why the same physics turns sunsets red.",
        "minutes": 4,
        "motif": "<g fill='#5b9bf0' fill-opacity='.45'><circle cx='560' cy='70' r='40'/></g>",
        "lead": "Sunlight looks white but is every colour mixed together. The sky's colour is a "
                "story about how those colours bounce off the air itself.",
        "sections": [
            ("Light hits air and scatters",
             "Air is mostly nitrogen and oxygen molecules. When sunlight passes through, it "
             "<b>scatters</b> off these tiny molecules. Crucially, shorter wavelengths (blue, "
             "violet) scatter far more than longer ones (red). This is <b>Rayleigh scattering</b> — "
             "scattering rises with the <i>fourth power</i> of frequency, so blue scatters about "
             "9× more than red."),
            ("So why not violet?",
             "Violet scatters even more than blue — but the Sun emits less violet, and our eyes "
             "are more sensitive to blue. The mix our brain receives reads as sky-blue."),
            ("Sunsets: the long way through",
             "At sunset, light skims through far more atmosphere. The blue is scattered away "
             "long before it reaches you, leaving the reds and oranges to come straight through. "
             "Same physics — different geometry."),
        ],
        "timeline": [
            ("Step 1", "White light arrives", "Sunlight contains all colours at once."),
            ("Step 2", "Blue scatters most", "Short wavelengths bounce off air molecules in every direction."),
            ("Step 3", "Sky fills with blue", "Scattered blue reaches your eye from all over the dome."),
            ("Step 4", "Sunset reddens", "Long path strips the blue, so only red/orange survives the trip."),
        ],
        "cards": [
            ("Rayleigh scattering", "Scattering of light by particles much smaller than its wavelength; strongly favours blue."),
            ("Wavelength", "Distance between light waves — blue is short, red is long."),
            ("Why sunsets are red", "Long atmospheric path scatters away the blue before it reaches you."),
            ("Why clouds are white", "Water droplets are large, so they scatter all colours equally (Mie scattering)."),
        ],
        "quiz": [
            ("Why is the daytime sky blue rather than red?",
             [("Air is naturally blue", 0), ("Blue light scatters much more than red", 1), ("The ocean reflects up", 0), ("The Sun emits only blue", 0)],
             "Rayleigh scattering favours short (blue) wavelengths by roughly 9 to 1 over red."),
            ("Why does the same air make sunsets red?",
             [("The Sun cools down", 0), ("Light travels a longer path, scattering away the blue", 1), ("Dust turns it red", 0), ("Clouds absorb blue", 0)],
             "At a low angle, light crosses much more atmosphere, removing the blue."),
        ],
        "did_you_know": "On Mars the physics flips: fine dust makes the daytime sky butterscotch, and "
                        "<i>sunsets glow blue</i>. NASA's rovers have photographed it.",
        "source": ("NASA Science — <i>Why Is the Sky Blue?</i>", "https://spaceplace.nasa.gov/blue-sky/en/"),
        "next": "Try it: look at the sky 90° from the Sun through polarized sunglasses and rotate them.",
    },
    {
        "id": "how-memory-works",
        "emoji": "🧠",
        "accent": "#b06bf0",
        "title": "How Memory Works (and How to Hack It)",
        "subtitle": "Why you forget — and the two tricks that beat the forgetting curve.",
        "minutes": 4,
        "motif": "<g fill='none' stroke='#b06bf0' stroke-opacity='.5' stroke-width='3'>"
                 "<path d='M470 200 C470 120 600 120 600 200'/><circle cx='535' cy='110' r='28'/></g>",
        "lead": "Memory is not a recording — it is a reconstruction. Knowing how it actually "
                "works hands you a cheat code for learning anything, including everything in this app.",
        "sections": [
            ("The forgetting curve",
             "In the 1880s Hermann Ebbinghaus memorized nonsense syllables and tracked how fast "
             "he forgot them. The loss is brutal and fast: most of what you learn today is gone "
             "within days — <i>unless</i> you do something about it."),
            ("Hack 1 — Retrieval, not review",
             "Re-reading feels productive but barely works. <b>Testing yourself</b> — pulling the "
             "answer out of your head — is what carves it in. This is the <b>testing effect</b>. "
             "Every quiz in these lessons is doing this on purpose."),
            ("Hack 2 — Spacing",
             "Review just as you're about to forget, and each recall resets the curve flatter. "
             "Spreading 5 reviews over 2 weeks beats 5 reviews in one night — by a lot. This is "
             "why a lesson a morning beats a cram session."),
        ],
        "timeline": [
            ("Encode", "Get it in", "Attention + meaning. You can't remember what you never really noticed."),
            ("Store", "Hold it", "Sleep consolidates the day's memories — pulling an all-nighter sabotages this."),
            ("Retrieve", "Pull it out", "Each successful recall strengthens the memory. Struggle is the workout."),
            ("Space", "Repeat later", "Re-test at growing intervals to flatten the forgetting curve."),
        ],
        "cards": [
            ("Testing effect", "Recalling information strengthens memory far more than re-reading it."),
            ("Spaced repetition", "Reviewing at increasing intervals to fight forgetting efficiently."),
            ("Forgetting curve", "Ebbinghaus's finding that memory decays rapidly without reinforcement."),
            ("Desirable difficulty", "A little struggle during learning makes the memory stick harder."),
        ],
        "quiz": [
            ("Which study method builds the strongest long-term memory?",
             [("Re-reading the notes", 0), ("Highlighting", 0), ("Testing yourself from memory", 1), ("Listening passively", 0)],
             "Retrieval practice — the testing effect — beats every passive method."),
            ("Five reviews are most effective when…",
             [("Done all in one night", 0), ("Spread out over two weeks", 1), ("Never repeated", 0), ("Done while tired", 0)],
             "Spacing flattens the forgetting curve far better than massing."),
        ],
        "did_you_know": "The act of <i>almost</i> remembering — that tip-of-the-tongue struggle — is "
                        "exactly when learning happens. Easy recall barely strengthens a memory; effortful "
                        "recall strengthens it a lot.",
        "source": ("Brown, Roediger & McDaniel — <i>Make It Stick</i> (2014)", "https://www.retrievalpractice.org/"),
        "next": "Tonight, try recalling these four lessons from memory before checking. That's the hack.",
    },
    {
        "id": "fermi-estimation",
        "emoji": "📐",
        "accent": "#2bd4c0",
        "title": "Guess Anything: Fermi Estimation",
        "subtitle": "How physicists get within 10× of any number using almost no data.",
        "minutes": 4,
        "motif": "<g fill='none' stroke='#2bd4c0' stroke-opacity='.5' stroke-width='3'>"
                 "<path d='M470 200 h120 M470 200 v-90 M470 180 l40-30 30 20 50-50'/></g>",
        "lead": "How many piano tuners are in Chicago? You have no idea — yet you can get "
                "surprisingly close in 60 seconds. This is one of the most useful thinking tools "
                "you'll ever own.",
        "sections": [
            ("Break the impossible into the easy",
             "Enrico Fermi could estimate anything by chopping a hard question into smaller "
             "questions he <i>could</i> guess, then multiplying. The errors tend to cancel out, "
             "so the final answer lands shockingly close."),
            ("The piano tuners of Chicago",
             "Chicago ≈ 3M people → ~1M households → maybe 1 in 20 owns a piano = 50,000 pianos. "
             "Tuned once a year, one tuner handling ~1,000 pianos/year → about <b>50 tuners</b>. "
             "The real number is in that ballpark. You used zero data."),
            ("Why it works",
             "Each guess might be off by 2–3×, some high, some low. Multiply several together and "
             "the over- and under-estimates partly cancel. You almost never land more than 10× off — "
             "which is often all a decision needs."),
        ],
        "timeline": [
            ("1. Frame", "What am I really after?", "State the quantity and its units clearly."),
            ("2. Decompose", "Break it down", "Split into factors you can each roughly guess."),
            ("3. Estimate", "Order of magnitude", "Pick round numbers; don't agonise — speed over precision."),
            ("4. Multiply", "Recombine", "Chain the factors. Sanity-check the final magnitude."),
        ],
        "cards": [
            ("Order of magnitude", "Which power of ten a number is near — the level Fermi estimates aim for."),
            ("Decomposition", "Splitting a hard quantity into easy-to-guess factors."),
            ("Error cancellation", "Independent over/under guesses partly offset when multiplied."),
            ("Sanity check", "Asking 'is this magnitude even plausible?' before trusting a number."),
        ],
        "quiz": [
            ("What makes Fermi estimates reliable despite rough inputs?",
             [("Lucky guessing", 0), ("Independent errors partly cancel when multiplied", 1), ("Secret data", 0), ("Rounding up always", 0)],
             "Over- and under-estimates offset, keeping you usually within ~10×."),
            ("First step in a Fermi estimate?",
             [("Multiply random numbers", 0), ("Look it up", 0), ("Decompose into guessable factors", 1), ("Give up", 0)],
             "Break the impossible question into smaller answerable ones."),
        ],
        "did_you_know": "At the first nuclear test, Fermi dropped scraps of paper as the blast wave passed "
                        "and estimated the bomb's yield from how far they blew — landing close to the "
                        "answer the instruments took weeks to compute.",
        "source": ("'Fermi problem' — overview & classic examples", "https://en.wikipedia.org/wiki/Fermi_problem"),
        "next": "Your turn: estimate how many cups of coffee your city drinks each morning.",
    },
    {
        "id": "power-of-compounding",
        "emoji": "📈",
        "accent": "#46d17a",
        "title": "The Quiet Power of Compounding",
        "subtitle": "The one idea behind wealth, skills, and habits — and why it feels like magic.",
        "minutes": 4,
        "motif": "<g fill='none' stroke='#46d17a' stroke-opacity='.55' stroke-width='3'>"
                 "<path d='M470 200 C520 200 540 130 600 100'/><path d='M470 200 h130'/></g>",
        "lead": "Humans think in straight lines, but compounding curves. That mismatch is why "
                "small consistent effort looks like nothing — until it looks like everything.",
        "sections": [
            ("Exponential beats linear — eventually",
             "Save $300/month at 8% and after 10 years you have ~$55k, of which $19k is growth. "
             "Leave it 30 years and it's ~$450k — and now <i>most</i> of it is growth on growth. "
             "The early years feel pointless; the late years feel unstoppable."),
            ("The Rule of 72",
             "Want to know how long money (or anything growing at a steady rate) takes to double? "
             "Divide 72 by the rate. At 8% → 72/8 = <b>9 years</b> to double. A fast, no-calculator "
             "trick that works for habits and skills too."),
            ("1% better, every day",
             "Improve 1% a day and you don't end the year 365% better — you end up "
             "<b>~37× better</b> (1.01^365). Decline 1% a day and you shrink to almost nothing. "
             "Habits are compound interest paid in identity."),
        ],
        "timeline": [
            ("Year 1", "Feels useless", "Tiny gains, mostly your own contributions. Easy to quit here."),
            ("Year 5", "Momentum", "Growth starts visibly outpacing effort."),
            ("Year 10", "Inflection", "The curve bends upward; results compound on prior results."),
            ("Year 30", "Runaway", "Most of the total is growth-on-growth. The early discipline pays off."),
        ],
        "cards": [
            ("Compounding", "Growth that itself generates more growth, producing a curve not a line."),
            ("Rule of 72", "Doubling time ≈ 72 ÷ growth-rate percent."),
            ("1% rule", "Tiny daily improvements multiply (1.01^365 ≈ 37×) over a year."),
            ("Time in market", "The biggest lever in compounding is how long, not how much."),
        ],
        "quiz": [
            ("At 6% growth, roughly how long to double (Rule of 72)?",
             [("6 years", 0), ("12 years", 1), ("3 years", 0), ("24 years", 0)],
             "72 ÷ 6 = 12 years."),
            ("Why do compounding's first years feel discouraging?",
             [("Growth is linear at first", 0), ("Most early value is your own input, not growth", 1), ("Interest is negative", 0), ("It only works for the rich", 0)],
             "Growth-on-growth needs a base to build on; that base takes time."),
        ],
        "did_you_know": "Warren Buffett built ~99% of his wealth after age 50 — not because he got smarter, "
                        "but because that's where the compounding curve finally went vertical. His real edge "
                        "was starting early and never interrupting it.",
        "source": ("James Clear — <i>Atomic Habits</i> (the 1% essay)", "https://jamesclear.com/continuous-improvement"),
        "next": "Pick one 1%-a-day habit and start it today. The curve needs time more than intensity.",
    },
]


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #
def esc(s: Any) -> str:
    return html.escape(str(s if s is not None else ""))


def _sections_html(sections: list[tuple[str, str]]) -> str:
    out = []
    for title, body in sections:
        out.append(
            f"<details class='acc'><summary>{esc(title)}</summary>"
            f"<div class='body'><p>{body}</p></div></details>"
        )
    return "".join(out)


def _timeline_html(items: list[tuple[str, str, str]]) -> str:
    nodes = []
    for yr, lbl, det in items:
        nodes.append(
            f"<div class='node'><div class='yr'>{esc(yr)}</div>"
            f"<div class='lbl'>{esc(lbl)}</div><div class='det'>{det}</div></div>"
        )
    return f"<div class='tl'>{''.join(nodes)}</div>"


def _cards_html(cards: list[tuple[str, str]]) -> str:
    out = []
    for front, back in cards:
        out.append(
            f"<div class='flip'><div class='in'>"
            f"<div class='face front'>{esc(front)}</div>"
            f"<div class='face back'>{esc(back)}</div></div></div>"
        )
    return f"<div class='cards'>{''.join(out)}</div><p class='hint'>Tap a card to flip it.</p>"


def _quiz_html(quiz: list[tuple[str, list[tuple[str, int]], str]]) -> str:
    blocks = []
    for q, opts, why in quiz:
        btns = "".join(
            f"<button class='opt' data-correct='{correct}'>{esc(text)}</button>"
            for text, correct in opts
        )
        blocks.append(
            f"<div class='quiz'><div class='q'>{esc(q)}</div>{btns}"
            f"<div class='why'>{why}</div></div>"
        )
    return "".join(blocks)


def render_lesson(lesson: dict[str, Any], day: str) -> str:
    accent = lesson["accent"]
    hero = _svg(accent, lesson["emoji"], lesson.get("motif", ""))
    src_label, src_url = lesson["source"]
    body = f"""<!doctype html><html lang='en'><head>
<meta charset='utf-8'>
<meta name='viewport' content='width=device-width,initial-scale=1,viewport-fit=cover'>
<meta name='color-scheme' content='dark'>
<title>{esc(lesson['title'])} — LifeOS Learn</title>
<style>{BASE_CSS}
:root{{--accent:{accent}}}</style></head>
<body><div class='wrap'>
<div class='topbar'><a href='/learn'>&larr; Today's lessons</a><span>{esc(day)}</span></div>
<div class='hero'>{hero}</div>
<div class='kicker'>{esc(lesson['emoji'])} Morning Lesson</div>
<h1>{esc(lesson['title'])}</h1>
<p class='sub'>{esc(lesson['subtitle'])}</p>
<div class='meta'><span>⏱ {esc(lesson['minutes'])} min</span><span>Beats 5 min of scrolling</span></div>
<p class='lead'>{lesson['lead']}</p>

<h2>Dig in</h2>
{_sections_html(lesson['sections'])}

<h2>How it unfolded</h2>
{_timeline_html(lesson['timeline'])}

<h2>Lock it in — flip cards</h2>
{_cards_html(lesson['cards'])}

<h2>Quick check</h2>
{_quiz_html(lesson['quiz'])}

<div class='reveal'><button>💡 Did you know? Tap to reveal</button><div class='txt'>{lesson['did_you_know']}</div></div>

<div class='foot'>
<p><span class='pill'>Go deeper</span> &nbsp; Primary source: <a class='cite' href='{esc(src_url)}' target='_blank' rel='noopener'>{src_label}</a></p>
<p>{esc(lesson.get('next',''))}</p>
<p>Questions? You have a teacher — ask your LifeOS agent to go deeper on anything here.</p>
</div>
</div>
<script>{BASE_JS}</script></body></html>"""
    return body


def daily_set(today: date) -> list[dict[str, Any]]:
    """Featured history lesson first, then 3 rotating picks so each day differs."""
    by_id = {l["id"]: l for l in LESSONS}
    featured = by_id["story-of-civilization"]
    rest = [l for l in LESSONS if l["id"] != featured["id"]]
    n = len(rest)
    start = today.toordinal() % n
    rotated = [rest[(start + i) % n] for i in range(min(3, n))]
    return [featured, *rotated]


def render_index(lessons: list[dict[str, Any]], today: date) -> str:
    day = today.strftime("%A, %B %d").replace(" 0", " ")
    cards = []
    for l in lessons:
        cards.append(f"""<a class='lcard' href='/output/learn/{esc(l['id'])}.html' style='--c:{l['accent']}'>
<div class='lemoji'>{esc(l['emoji'])}</div>
<div class='ltext'><div class='ltitle'>{esc(l['title'])}</div>
<div class='lsub'>{esc(l['subtitle'])}</div>
<div class='lmeta'>⏱ {esc(l['minutes'])} min · tap to start</div></div></a>""")
    return f"""<!doctype html><html lang='en'><head>
<meta charset='utf-8'>
<meta name='viewport' content='width=device-width,initial-scale=1,viewport-fit=cover'>
<meta name='color-scheme' content='dark'>
<title>LifeOS — Learn this morning</title>
<style>{BASE_CSS}
.lcard{{display:flex;gap:14px;align-items:center;text-decoration:none;color:var(--fg);border:1px solid var(--line);border-left:4px solid var(--c);border-radius:16px;padding:16px;margin:12px 0;background:var(--card);transition:.15s}}
.lcard:hover{{transform:translateY(-2px);border-color:var(--c)}}
.lemoji{{font-size:38px;line-height:1}}
.ltitle{{font-size:21px;font-weight:700}}
.lsub{{color:var(--muted);font-size:16px;margin:2px 0 6px}}
.lmeta{{font:600 13px system-ui;color:var(--c)}}
.intro{{color:var(--muted);font-size:18px}}
</style></head><body><div class='wrap'>
<div class='topbar'><span>🌅 LifeOS Learn</span><a href='/m'>Control →</a></div>
<div class='kicker'>{esc(day)}</div>
<h1>Learn something this morning</h1>
<p class='intro'>Four short, interactive lessons — pick one instead of the feed. Each is a few minutes and built to actually stick.</p>
{''.join(cards)}
<div class='foot'><p>A fresh set is generated every morning by LifeOS. Tap any card to begin.</p></div>
</div></body></html>"""


def build(today: date | None = None) -> dict[str, Any]:
    today = today or date.today()
    OUT.mkdir(parents=True, exist_ok=True)
    lessons = daily_set(today)
    day_label = today.strftime("%A, %B %d").replace(" 0", " ")
    written = []
    for l in lessons:
        path = OUT / f"{l['id']}.html"
        path.write_text(render_lesson(l, day_label), encoding="utf-8")
        written.append(str(path))
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
