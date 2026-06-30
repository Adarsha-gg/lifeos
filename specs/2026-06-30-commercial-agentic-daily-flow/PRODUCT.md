# PRODUCT — Commercial agentic daily learning flow

## Goal
Make LifeOS feel like a premium daily learning RPG that can become a paid product without cluttering the Hub.

## In scope
1. Hub stays focused: visible page shows today's due/main quest plus the swipe deck.
2. Top-right account chip shows identity/level/progress instead of a bare XP pill.
3. Account menu exposes:
   - Google sign-in entry point
   - level/rank/streak/XP
   - completed quests
   - personal graph preview/link
   - private notes
   - send-to-phone handoff
   - pricing/upgrade plans
4. Daily agent brief shows three recommended learning items for the morning inside the existing quest area.
5. Swipe deck remains the learner-choice surface after the daily brief.
6. Premium art pipeline covers every knowledge-graph lesson with a mythic/Fable-style prompt and static-safe fallback artwork.
7. Google authentication is config-ready and safe on static Vercel; no secrets are hard-coded.
8. Stripe pricing supports three newcomer plans:
   - $10/month
   - $50/6 months
   - $90/year
9. Phone handoff uses browser-native share/copy until a real SMS/push backend is approved.

## Explicitly out of scope
- Automation folder or personal digital-life automation workflows.
- Creating live Google OAuth clients, Stripe products/prices, repos, SMS sends, posts, or payments from the agent.
- Adding new visible hub dashboards.
- Storing private source text in public deploys.

## Behavior invariants
1. `/hub` main content has exactly two top-level sections: `quest` and `deck`.
2. Secondary surfaces remain hidden behind hamburger/account overlays.
3. If Google client ID is missing, sign-in explains what is missing instead of failing silently.
4. If Stripe payment links are missing, plan buttons explain what env/config must be added.
5. No auth token, Stripe secret key, or private text is committed.
6. Daily recommendations are deterministic per day and use real graph/deck data where available.
7. Generated art prompts/fallbacks exist for every node in the public knowledge graph.
8. Notes persist locally and can be exported in the existing memory bundle.
9. Mobile/desktop layouts do not horizontally overflow.

## Non-clutter rule
Only the daily quest, three compact morning picks, and swipe deck may be visible in the main flow. Auth, billing, graph, notes, completed quests, and phone handoff live in the account menu or drawer.
