# Competitor benchmark — commercial agentic daily learning flow

## Scope
Use competitor patterns only where they strengthen LifeOS without cluttering the primary hub. The main page remains: today's due/main quest + swipe deck.

## Source signals
- Microlearning comparisons in 2026 consistently highlight Duolingo for streak/habit loops, Brilliant for interactive STEM problem solving, Headway/Blinkist for short nonfiction lessons, and newer players like BeFreed/NerdSip for personalized any-topic learning/audio.
- AI knowledge products cluster around personal knowledge bases, automatic organization, and resurfacing: ReadGraph, Recall, WisMe.ai, TiSiT, and Prismo emphasize personal graphs, notes, spaced repetition, saving what you consume, and remembering what matters.

## Features worth copying into LifeOS
1. **Daily habit loop** — Duolingo-style streak/XP/account chip, but keep it top-right instead of adding dashboard clutter.
2. **Tiny morning assignment** — three recommended things each morning, like microlearning apps, integrated inside today's quest section.
3. **Swipe choice** — keep Tinder-style deck for learner agency after the three-item daily agent brief.
4. **Knowledge graph ownership** — Recall/TiSiT/ReadGraph pattern: the user profile should expose completed quests and graph progress.
5. **Notes** — Prismo/Readwise pattern: capture notes near the profile/memory layer, not as a noisy article overlay.
6. **Mobile handoff** — share/copy the current hub link to phone; avoid SMS until a real backend/provider exists.
7. **Subscription packaging** — three simple plans for newcomers: $10 monthly, $50 six months, $90 annual. Stripe Payment Links are enough for a static Vercel app until a backend exists.
8. **Authentication** — Google sign-in is useful for identity, but static builds can only do client-side Google Identity Services until a backend verifies tokens.
9. **Premium art** — every lesson needs a stable art asset/prompt path so generated imagery can scale to the full graph without hand-editing cards.

## Features to avoid for this pass
- Multiple visible dashboards on the hub.
- Live billing creation, OAuth client creation, or phone sends without credentials/approval.
- Automation-folder/personal OS workflows; user explicitly moved that to another agent.

## Product implication
Ship a static-safe commercial shell now: top-right account menu, Google/Stripe-ready controls, daily three picks, profile panel with graph/notes/completed quests, and a deterministic mythic-art manifest/fallback for every graph node. Wire real Google client IDs, Stripe payment links, and generated image files later through environment/config, not code changes.
