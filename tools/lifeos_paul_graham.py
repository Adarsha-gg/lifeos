#!/usr/bin/env python3
"""Build LifeOS curriculum units for Paul Graham essays.

The script uses the official Paul Graham essays index as the source of truth
when network access is available. It fetches essays read-only to derive tags and
signals, but output stores only metadata and original study prompts, never full
essay text.

Examples:
    python tools/lifeos_paul_graham.py list --limit 10
    python tools/lifeos_paul_graham.py build --limit 8 --fetch-essays
    python tools/lifeos_paul_graham.py build --metadata-only
"""
from __future__ import annotations

import argparse
import html
import json
import re
import time
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from lifeos_paths import VAULT_ROOT


INDEX_URL = "https://www.paulgraham.com/articles.html"
BASE_URL = "https://www.paulgraham.com/"
UA = "LifeOS-personal-curriculum/1.0 (metadata/digest builder)"
OUT = VAULT_ROOT / "output" / "learn"
PG_JSON = OUT / "paul-graham-essays.json"


FALLBACK_ESSAYS: list[dict[str, str]] = [
    {"title": "How to Do Great Work", "url": "https://www.paulgraham.com/greatwork.html"},
    {"title": "Superlinear Returns", "url": "https://www.paulgraham.com/superlinear.html"},
    {"title": "How to Get New Ideas", "url": "https://www.paulgraham.com/getideas.html"},
    {"title": "The Need to Read", "url": "https://www.paulgraham.com/read.html"},
    {"title": "What You Want to Want", "url": "https://www.paulgraham.com/want.html"},
    {"title": "Alien Truth", "url": "https://www.paulgraham.com/alien.html"},
    {"title": "What I've Learned from Users", "url": "https://www.paulgraham.com/users.html"},
    {"title": "Heresy", "url": "https://www.paulgraham.com/heresy.html"},
    {"title": "Putting Ideas into Words", "url": "https://www.paulgraham.com/words.html"},
    {"title": "Is There Such a Thing as Good Taste?", "url": "https://www.paulgraham.com/goodtaste.html"},
    {"title": "Beyond Smart", "url": "https://www.paulgraham.com/smart.html"},
    {"title": "Weird Languages", "url": "https://www.paulgraham.com/weird.html"},
    {"title": "How to Work Hard", "url": "https://www.paulgraham.com/hwh.html"},
    {"title": "A Project of One's Own", "url": "https://www.paulgraham.com/own.html"},
    {"title": "Fierce Nerds", "url": "https://www.paulgraham.com/fn.html"},
    {"title": "Crazy New Ideas", "url": "https://www.paulgraham.com/newideas.html"},
    {"title": "An NFT That Saves Lives", "url": "https://www.paulgraham.com/nft.html"},
    {"title": "The Real Reason to End the Death Penalty", "url": "https://www.paulgraham.com/deathpenalty.html"},
    {"title": "How People Get Rich Now", "url": "https://www.paulgraham.com/richnow.html"},
    {"title": "Write Simply", "url": "https://www.paulgraham.com/simply.html"},
    {"title": "Donate Unrestricted", "url": "https://www.paulgraham.com/donate.html"},
    {"title": "What I Worked On", "url": "https://www.paulgraham.com/worked.html"},
    {"title": "Earnestness", "url": "https://www.paulgraham.com/earnest.html"},
    {"title": "Billionaires Build", "url": "https://www.paulgraham.com/ace.html"},
    {"title": "The Four Quadrants of Conformism", "url": "https://www.paulgraham.com/conformism.html"},
    {"title": "Orthodox Privilege", "url": "https://www.paulgraham.com/orth.html"},
    {"title": "Coronavirus and Credibility", "url": "https://www.paulgraham.com/cred.html"},
    {"title": "How to Write Usefully", "url": "https://www.paulgraham.com/useful.html"},
    {"title": "Being a Noob", "url": "https://www.paulgraham.com/noob.html"},
    {"title": "Haters", "url": "https://www.paulgraham.com/fh.html"},
    {"title": "The Bus Ticket Theory of Genius", "url": "https://www.paulgraham.com/genius.html"},
    {"title": "General and Surprising", "url": "https://www.paulgraham.com/sun.html"},
    {"title": "Charisma / Power", "url": "https://www.paulgraham.com/power.html"},
    {"title": "The Risk of Discovery", "url": "https://www.paulgraham.com/disc.html"},
    {"title": "How to Make Pittsburgh a Startup Hub", "url": "https://www.paulgraham.com/pgh.html"},
    {"title": "Life is Short", "url": "https://www.paulgraham.com/vb.html"},
    {"title": "Economic Inequality", "url": "https://www.paulgraham.com/ineq.html"},
    {"title": "The Refragmentation", "url": "https://www.paulgraham.com/re.html"},
    {"title": "Jessica Livingston", "url": "https://www.paulgraham.com/jessica.html"},
    {"title": "A Way to Detect Bias", "url": "https://www.paulgraham.com/bias.html"},
    {"title": "Write Like You Talk", "url": "https://www.paulgraham.com/talk.html"},
    {"title": "Default Alive or Default Dead?", "url": "https://www.paulgraham.com/aord.html"},
    {"title": "Why It's Safe for Founders to Be Nice", "url": "https://www.paulgraham.com/safe.html"},
    {"title": "Change Your Name", "url": "https://www.paulgraham.com/name.html"},
    {"title": "What Microsoft Is this the Altair Basic of?", "url": "https://www.paulgraham.com/altair.html"},
    {"title": "The Ronco Principle", "url": "https://www.paulgraham.com/ronco.html"},
    {"title": "What Doesn't Seem Like Work?", "url": "https://www.paulgraham.com/work.html"},
    {"title": "Don't Talk to Corp Dev", "url": "https://www.paulgraham.com/corpdev.html"},
    {"title": "Let the Other 95% of Great Programmers In", "url": "https://www.paulgraham.com/95.html"},
    {"title": "How to Be an Expert in a Changing World", "url": "https://www.paulgraham.com/ecw.html"},
    {"title": "How You Know", "url": "https://www.paulgraham.com/know.html"},
    {"title": "What I've Learned from Hacker News", "url": "https://www.paulgraham.com/hn.html"},
    {"title": "Startup Investing Trends", "url": "https://www.paulgraham.com/swan.html"},
    {"title": "How to Raise Money", "url": "https://www.paulgraham.com/fr.html"},
    {"title": "Investor Herd Dynamics", "url": "https://www.paulgraham.com/herd.html"},
    {"title": "How to Convince Investors", "url": "https://www.paulgraham.com/convince.html"},
    {"title": "Do Things that Don't Scale", "url": "https://www.paulgraham.com/ds.html"},
    {"title": "Startup = Growth", "url": "https://www.paulgraham.com/growth.html"},
    {"title": "Black Swan Farming", "url": "https://www.paulgraham.com/swan.html"},
    {"title": "The Top Idea in Your Mind", "url": "https://www.paulgraham.com/top.html"},
    {"title": "How to Lose Time and Money", "url": "https://www.paulgraham.com/selfindulgence.html"},
    {"title": "Organic Startup Ideas", "url": "https://www.paulgraham.com/organic.html"},
    {"title": "Apple's Mistake", "url": "https://www.paulgraham.com/apple.html"},
    {"title": "Schlep Blindness", "url": "https://www.paulgraham.com/schlep.html"},
    {"title": "Snapshot: Viaweb, June 1998", "url": "https://www.paulgraham.com/vw.html"},
    {"title": "Why Startup Hubs Work", "url": "https://www.paulgraham.com/hubs.html"},
    {"title": "High Resolution Fundraising", "url": "https://www.paulgraham.com/hiresfund.html"},
    {"title": "The Future of Startup Funding", "url": "https://www.paulgraham.com/future.html"},
    {"title": "What Happened to Yahoo", "url": "https://www.paulgraham.com/yahoo.html"},
    {"title": "The Acceleration of Addictiveness", "url": "https://www.paulgraham.com/addiction.html"},
    {"title": "The Anatomy of Determination", "url": "https://www.paulgraham.com/determination.html"},
    {"title": "What Kate Saw in Silicon Valley", "url": "https://www.paulgraham.com/kate.html"},
    {"title": "What Startups Are Really Like", "url": "https://www.paulgraham.com/really.html"},
    {"title": "A Local Revolution?", "url": "https://www.paulgraham.com/revolution.html"},
    {"title": "Why Twitter is a Big Deal", "url": "https://www.paulgraham.com/twitter.html"},
    {"title": "The Founder Visa", "url": "https://www.paulgraham.com/foundervisa.html"},
    {"title": "Five Founders", "url": "https://www.paulgraham.com/5founders.html"},
    {"title": "Relentlessly Resourceful", "url": "https://www.paulgraham.com/relres.html"},
    {"title": "Startups in 13 Sentences", "url": "https://www.paulgraham.com/13sentences.html"},
    {"title": "Keep Your Identity Small", "url": "https://www.paulgraham.com/identity.html"},
    {"title": "After the Credentials", "url": "https://www.paulgraham.com/credentials.html"},
    {"title": "Could VC be a Casualty of the Recession?", "url": "https://www.paulgraham.com/recess.html"},
    {"title": "Why to Start a Startup in a Bad Economy", "url": "https://www.paulgraham.com/badeconomy.html"},
    {"title": "Fundraising Survival Guide", "url": "https://www.paulgraham.com/fundraising.html"},
    {"title": "The Pooled-Risk Company Management Company", "url": "https://www.paulgraham.com/prcmc.html"},
    {"title": "Cities and Ambition", "url": "https://www.paulgraham.com/cities.html"},
    {"title": "Disconnecting Distraction", "url": "https://www.paulgraham.com/distraction.html"},
    {"title": "Lies We Tell Kids", "url": "https://www.paulgraham.com/lies.html"},
    {"title": "Be Good", "url": "https://www.paulgraham.com/good.html"},
    {"title": "Why There Aren't More Googles", "url": "https://www.paulgraham.com/googles.html"},
    {"title": "Some Heroes", "url": "https://www.paulgraham.com/heroes.html"},
    {"title": "How to Disagree", "url": "https://www.paulgraham.com/disagree.html"},
    {"title": "You Weren't Meant to Have a Boss", "url": "https://www.paulgraham.com/boss.html"},
    {"title": "A New Venture Animal", "url": "https://www.paulgraham.com/ycombinator.html"},
    {"title": "Trolls", "url": "https://www.paulgraham.com/trolls.html"},
    {"title": "Six Principles for Making New Things", "url": "https://www.paulgraham.com/newthings.html"},
    {"title": "Why to Move to a Startup Hub", "url": "https://www.paulgraham.com/startuphubs.html"},
    {"title": "The Future of Web Startups", "url": "https://www.paulgraham.com/webstartups.html"},
    {"title": "How Art Can Be Good", "url": "https://www.paulgraham.com/goodart.html"},
    {"title": "The 18 Mistakes That Kill Startups", "url": "https://www.paulgraham.com/startupmistakes.html"},
    {"title": "A Student's Guide to Startups", "url": "https://www.paulgraham.com/mit.html"},
    {"title": "Copy What You Like", "url": "https://www.paulgraham.com/copy.html"},
    {"title": "The Island Test", "url": "https://www.paulgraham.com/island.html"},
    {"title": "The Power of the Marginal", "url": "https://www.paulgraham.com/marginal.html"},
    {"title": "Why Startups Condense in America", "url": "https://www.paulgraham.com/america.html"},
    {"title": "How to Do What You Love", "url": "https://www.paulgraham.com/love.html"},
    {"title": "Good and Bad Procrastination", "url": "https://www.paulgraham.com/procrastination.html"},
    {"title": "Web 2.0", "url": "https://www.paulgraham.com/web20.html"},
    {"title": "Hiring is Obsolete", "url": "https://www.paulgraham.com/hiring.html"},
    {"title": "The Venture Capital Squeeze", "url": "https://www.paulgraham.com/vcsqueeze.html"},
    {"title": "Ideas for Startups", "url": "https://www.paulgraham.com/ideas.html"},
    {"title": "What I Did this Summer", "url": "https://www.paulgraham.com/summer.html"},
    {"title": "Inequality and Risk", "url": "https://www.paulgraham.com/inequality.html"},
    {"title": "After the Ladder", "url": "https://www.paulgraham.com/ladder.html"},
    {"title": "What Business Can Learn from Open Source", "url": "https://www.paulgraham.com/opensource.html"},
    {"title": "How to Start a Startup", "url": "https://www.paulgraham.com/start.html"},
    {"title": "The Python Paradox", "url": "https://www.paulgraham.com/pypar.html"},
    {"title": "Great Hackers", "url": "https://www.paulgraham.com/gh.html"},
    {"title": "Mind the Gap", "url": "https://www.paulgraham.com/gap.html"},
    {"title": "How to Make Wealth", "url": "https://www.paulgraham.com/wealth.html"},
    {"title": "Hackers and Painters", "url": "https://www.paulgraham.com/hp.html"},
    {"title": "If Lisp is So Great", "url": "https://www.paulgraham.com/iflisp.html"},
    {"title": "The Hundred-Year Language", "url": "https://www.paulgraham.com/hundred.html"},
    {"title": "Revenge of the Nerds", "url": "https://www.paulgraham.com/icad.html"},
    {"title": "Succinctness is Power", "url": "https://www.paulgraham.com/power.html"},
    {"title": "What Languages Fix", "url": "https://www.paulgraham.com/fix.html"},
    {"title": "Beating the Averages", "url": "https://www.paulgraham.com/avg.html"},
    {"title": "Java's Cover", "url": "https://www.paulgraham.com/javacover.html"},
    {"title": "Being Popular", "url": "https://www.paulgraham.com/popular.html"},
    {"title": "Why Nerds Are Unpopular", "url": "https://www.paulgraham.com/nerds.html"},
    {"title": "What You'll Wish You'd Known", "url": "https://www.paulgraham.com/hs.html"},
]


NON_ESSAY_HREFS = {
    "index.html",
    "articles.html",
    "books.html",
    "rss.html",
    "arc.html",
    "bio.html",
    "faq.html",
    "quotes.html",
}

STOPWORDS = {
    "the", "and", "that", "you", "for", "are", "with", "this", "was", "have", "not", "but", "they",
    "from", "his", "her", "one", "all", "can", "would", "there", "their", "what", "when", "about",
    "more", "like", "will", "your", "people", "than", "were", "been", "them", "because", "which",
    "into", "could", "some", "most", "very", "then", "just", "only", "much", "such", "make",
}

TAG_RULES: list[tuple[str, list[str]]] = [
    ("startups", ["startup", "founder", "fundraising", "investor", "venture", "vc", "users", "growth", "company", "y combinator"]),
    ("writing", ["write", "writing", "words", "essay", "talk", "read", "usefully", "simply"]),
    ("thinking", ["ideas", "truth", "bias", "disagree", "know", "expert", "heresy", "taste", "smart"]),
    ("work", ["work", "hard", "determination", "procrastination", "ambition", "boss", "love", "project"]),
    ("programming", ["hackers", "lisp", "language", "python", "java", "programmers", "opensource", "software"]),
    ("society", ["inequality", "cities", "america", "visa", "kids", "conformism", "privilege", "credibility"]),
    ("wealth", ["rich", "wealth", "money", "economic", "risk", "billionaires"]),
    ("learning", ["learned", "noob", "credentials", "students", "school", "nerds"]),
]

TAG_DIGESTS: dict[str, dict[str, str]] = {
    "startups": {
        "lens": "startup reality",
        "idea": "Graham usually treats startups as experiments under extreme feedback, where users, growth, and founder behavior reveal more than plans do.",
        "prompt": "Apply the essay to one project: what would direct user contact, a smaller launch, or a faster feedback loop change this week?",
    },
    "writing": {
        "lens": "clear writing",
        "idea": "The recurring writing lesson is that useful prose is compressed thinking: clarity comes from noticing the real thought and removing status performance.",
        "prompt": "Rewrite one paragraph of your own work so the strongest claim appears first and every sentence earns its place.",
    },
    "thinking": {
        "lens": "independent judgment",
        "idea": "These essays push against inherited opinions. The useful move is to separate what is prestigious, conventional, or emotionally safe from what is actually true.",
        "prompt": "Name one belief you hold mostly because your group rewards it, then list what evidence would change your mind.",
    },
    "work": {
        "lens": "ambitious work",
        "idea": "Graham often frames great work as a fit between curiosity, stamina, taste, and unusually direct engagement with the problem.",
        "prompt": "Identify one activity that does not feel like work but compounds into ability; protect a two-hour block for it.",
    },
    "programming": {
        "lens": "tools and leverage",
        "idea": "The programming essays emphasize expressive tools, hacker taste, and the compounding advantage of choosing abstractions that let small teams move faster.",
        "prompt": "Audit a tool you use daily: does it make the important path shorter, or merely make the common path familiar?",
    },
    "society": {
        "lens": "institutions and norms",
        "idea": "The social essays ask how norms, institutions, and incentives quietly determine what people can say, build, risk, or become.",
        "prompt": "Pick one norm in your environment and ask who benefits from it, who pays for it, and what truth it makes harder to say.",
    },
    "wealth": {
        "lens": "wealth creation",
        "idea": "Graham distinguishes making wealth from merely redistributing money, usually tying wealth to building something people want at scale.",
        "prompt": "Choose a product or service and trace exactly where new value is created rather than where money changes hands.",
    },
    "learning": {
        "lens": "self-education",
        "idea": "The learning essays favor curiosity, direct experience, and skepticism toward credentials when credentials become substitutes for ability.",
        "prompt": "Pick one credential-shaped goal and convert it into a visible skill demonstration someone could inspect.",
    },
}


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[dict[str, str]] = []
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "a":
            attrs_dict = {k.lower(): v or "" for k, v in attrs}
            self._href = attrs_dict.get("href")
            self._text = []

    def handle_data(self, data: str) -> None:
        if self._href:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self._href:
            text = " ".join(" ".join(self._text).split())
            if text:
                self.links.append({"href": self._href, "title": html.unescape(text)})
            self._href = None
            self._text = []


class TextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self._skip = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"script", "style"}:
            self._skip = True
        if tag.lower() in {"p", "br", "tr", "div", "center", "title"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style"}:
            self._skip = False
        if tag.lower() in {"p", "br", "tr", "div", "center"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._skip:
            self.parts.append(data)

    def text(self) -> str:
        raw = html.unescape(" ".join(self.parts))
        lines = [" ".join(line.split()) for line in raw.splitlines()]
        return "\n".join(line for line in lines if line)


def http_get(url: str, timeout: int = 25) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        return resp.read().decode(charset, errors="replace")


def normalize_url(href: str) -> str:
    return urllib.parse.urljoin(BASE_URL, href)


def canonical_key(url: str) -> str:
    path = urllib.parse.urlparse(url).path.rsplit("/", 1)[-1]
    return path.lower()


def dedupe(items: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[str] = set()
    out: list[dict[str, str]] = []
    for item in items:
        key = canonical_key(item["url"])
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def parse_index(index_html: str) -> list[dict[str, str]]:
    parser = LinkParser()
    parser.feed(index_html)
    essays: list[dict[str, str]] = []
    for link in parser.links:
        href = link["href"].strip()
        key = canonical_key(normalize_url(href))
        if not key.endswith(".html") or key in NON_ESSAY_HREFS:
            continue
        title = clean_title(link["title"])
        if len(title) < 3 or title.lower() in {"essays", "home", "faq"}:
            continue
        essays.append({"title": title, "url": normalize_url(href)})
    return dedupe(essays)


def clean_title(title: str) -> str:
    title = re.sub(r"\s+", " ", html.unescape(title)).strip()
    title = title.strip("-: ")
    return title


def fetch_index(allow_fallback: bool = True) -> tuple[list[dict[str, str]], dict[str, Any]]:
    try:
        raw = http_get(INDEX_URL)
        essays = parse_index(raw)
        if essays:
            return essays, {
                "source": "official-index",
                "index_url": INDEX_URL,
                "fetched_at": datetime.now().isoformat(timespec="seconds"),
                "essay_count": len(essays),
                "fallback_used": False,
            }
        raise RuntimeError("official index parsed but yielded no essay links")
    except Exception as exc:
        if not allow_fallback:
            raise
        essays = dedupe(FALLBACK_ESSAYS)
        return essays, {
            "source": "static-fallback",
            "index_url": INDEX_URL,
            "fetched_at": datetime.now().isoformat(timespec="seconds"),
            "essay_count": len(essays),
            "fallback_used": True,
            "fetch_error": str(exc),
        }


def essay_text_from_html(raw: str) -> str:
    parser = TextParser()
    parser.feed(raw)
    text = parser.text()
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def extract_date(text: str) -> str | None:
    match = re.search(
        r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b",
        text,
    )
    if match:
        return match.group(0)
    year = re.search(r"\b(19|20)\d{2}\b", text[:1200])
    return year.group(0) if year else None


def infer_tags(title: str, url: str, text: str = "") -> list[str]:
    haystack = f"{title} {url} {text[:4000]}".lower()
    tags = [tag for tag, words in TAG_RULES if any(word in haystack for word in words)]
    if not tags:
        tags = ["thinking"]
    return tags[:4]


def top_terms(text: str, limit: int = 8) -> list[str]:
    words = re.findall(r"[a-zA-Z][a-zA-Z']{3,}", text.lower())
    counts = Counter(w.strip("'") for w in words if w not in STOPWORDS)
    return [word for word, _ in counts.most_common(limit)]


def digest_for(title: str, url: str, tags: list[str], terms: list[str]) -> dict[str, Any]:
    profiles = [TAG_DIGESTS[tag] for tag in tags if tag in TAG_DIGESTS]
    if not profiles:
        profiles = [TAG_DIGESTS["thinking"]]
    lenses = ", ".join(profile["lens"] for profile in profiles[:3])
    term_note = f" Key recurring terms to inspect in the original: {', '.join(terms[:5])}." if terms else ""
    key_ideas = [profile["idea"] for profile in profiles[:3]]
    while len(key_ideas) < 3:
        key_ideas.append("Read the essay as a model of how Graham turns a concrete observation into a general rule, then tests the rule against incentives and edge cases.")
    questions = [
        f"What is the strongest claim in '{title}', stated without Graham's wording?",
        "Which assumption would have to be false for the essay's advice to break?",
        "Where does the essay favor direct evidence over prestige, credentials, or consensus?",
        "What would a critic say is missing, overstated, or too dependent on Graham's context?",
        "What concrete behavior would change this week if you believed the essay?",
        "How does this essay connect to another PG theme: startups, writing, wealth, ambition, or independent thought?",
    ]
    return {
        "summary": (
            f"Original LifeOS digest for a Paul Graham essay on {lenses}. "
            f"Use the official essay as the source text; this unit stores a compressed study map rather than the essay body."
            f"{term_note}"
        ),
        "key_ideas": key_ideas[:3],
        "application_prompt": profiles[0]["prompt"],
        "thinking_questions": questions,
        "source_note": "Official essay URL only; no full essay text is reproduced in this JSON.",
        "official_url": url,
    }


def existing_units() -> dict[str, Any]:
    if not PG_JSON.exists():
        return {}
    try:
        data = json.loads(PG_JSON.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return {unit.get("url", ""): unit for unit in data.get("units", []) if unit.get("url")}


def build_units(
    essays: list[dict[str, str]],
    *,
    fetch_essays: bool,
    limit: int | None,
    refresh: bool,
    sleep_s: float,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    prior = existing_units()
    units: list[dict[str, Any]] = []
    fetched = 0
    reused = 0
    failed = 0
    selected = essays[:limit] if limit else essays
    for index, essay in enumerate(selected, start=1):
        url = essay["url"]
        old = prior.get(url)
        if old and not refresh:
            units.append(old)
            reused += 1
            continue
        text = ""
        date = None
        error = None
        if fetch_essays:
            try:
                text = essay_text_from_html(http_get(url))
                date = extract_date(text)
                fetched += 1
                if sleep_s:
                    time.sleep(sleep_s)
            except Exception as exc:
                error = str(exc)
                failed += 1
        tags = infer_tags(essay["title"], url, text)
        terms = top_terms(text) if text else []
        digest = digest_for(essay["title"], url, tags, terms)
        units.append(
            {
                "id": f"pg-{canonical_key(url).replace('.html', '')}",
                "title": essay["title"],
                "author": "Paul Graham",
                "url": url,
                "order": index,
                "date": date,
                "tags": tags,
                "kind": "essay-digest",
                "minutes": 20,
                "digest": digest,
                "text_signals": {
                    "top_terms": terms,
                    "characters_read_for_signals": len(text),
                    "fetch_error": error,
                },
                "prerequisites": [],
                "review_prompts": [
                    "Restate the essay's thesis from memory.",
                    "Name one example from your own work where the idea applies.",
                    "Find the strongest objection and answer it fairly.",
                ],
            }
        )
    return units, {"selected": len(selected), "fetched": fetched, "reused": reused, "failed": failed}


def write_payload(units: list[dict[str, Any]], index_meta: dict[str, Any], build_meta: dict[str, Any]) -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source": {
            "author": "Paul Graham",
            "official_index": INDEX_URL,
            "copyright_policy": "Store URLs, metadata, original digests, questions, and derived signals only; never store full essay bodies.",
        },
        "index": index_meta,
        "build": build_meta,
        "unit_count": len(units),
        "units": units,
        "refresh_policy": {
            "all_essays": "Run without --limit to rebuild one unit per essay discovered from the official index.",
            "resume": "Existing units are reused by official URL unless --refresh is passed.",
            "offline": "If official index fetch fails and fallback is allowed, a large static URL list keeps the curriculum usable until refresh.",
        },
    }
    PG_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def cmd_list(args: argparse.Namespace) -> int:
    essays, meta = fetch_index(allow_fallback=not args.no_fallback)
    selected = essays[: args.limit] if args.limit else essays
    print(json.dumps({"index": meta, "essays": selected, "count": len(essays)}, indent=2))
    return 0


def cmd_build(args: argparse.Namespace) -> int:
    essays, index_meta = fetch_index(allow_fallback=not args.no_fallback)
    units, build_meta = build_units(
        essays,
        fetch_essays=not args.metadata_only,
        limit=args.limit,
        refresh=args.refresh,
        sleep_s=args.sleep,
    )
    payload = write_payload(units, index_meta, build_meta)
    print(json.dumps({
        "path": str(PG_JSON),
        "index_source": index_meta["source"],
        "index_count": index_meta["essay_count"],
        "unit_count": payload["unit_count"],
        "fetched_essay_pages": build_meta["fetched"],
        "reused": build_meta["reused"],
        "failed_fetches": build_meta["failed"],
    }, indent=2))
    return 0


def cmd_count(_: argparse.Namespace) -> int:
    if not PG_JSON.exists():
        print(json.dumps({"exists": False, "path": str(PG_JSON)}, indent=2))
        return 0
    data = json.loads(PG_JSON.read_text(encoding="utf-8"))
    print(json.dumps({
        "exists": True,
        "path": str(PG_JSON),
        "unit_count": data.get("unit_count", len(data.get("units", []))),
        "index_source": data.get("index", {}).get("source"),
        "index_count": data.get("index", {}).get("essay_count"),
        "fallback_used": data.get("index", {}).get("fallback_used"),
    }, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Paul Graham essay digest units for LifeOS")
    sub = parser.add_subparsers(dest="cmd", required=True)

    list_p = sub.add_parser("list", help="Fetch and parse official PG essay index, printing metadata only")
    list_p.add_argument("--limit", type=int, default=0)
    list_p.add_argument("--no-fallback", action="store_true")
    list_p.set_defaults(func=cmd_list)

    build_p = sub.add_parser("build", help="Write output/learn/paul-graham-essays.json")
    build_p.add_argument("--limit", type=int, default=0, help="Optional small export limit for validation")
    build_p.add_argument("--metadata-only", action="store_true", help="Do not fetch individual essay pages")
    build_p.add_argument("--refresh", action="store_true", help="Regenerate even if a unit already exists")
    build_p.add_argument("--sleep", type=float, default=0.15, help="Delay between essay fetches")
    build_p.add_argument("--no-fallback", action="store_true")
    build_p.set_defaults(func=cmd_build)

    count_p = sub.add_parser("count", help="Print current output JSON counts")
    count_p.set_defaults(func=cmd_count)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
