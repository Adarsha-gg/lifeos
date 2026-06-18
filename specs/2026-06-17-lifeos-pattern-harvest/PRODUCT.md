# PRODUCT.md — LifeOS Pattern Harvest

## Summary

Create an ordered, evidence-backed process for borrowing specific architecture/product patterns from open-source LifeOS, AI chief-of-staff, MCP connector, and local-first assistant projects without random copying. The output is a source map and implementation queue that says exactly what to inspect, what to steal conceptually, what not to copy, and in what order to implement.

## User Problem

Adarsha wants LifeOS to move fast by learning from adjacent open-source systems, but does not want chaotic one-off changes. The work needs a disciplined research → architecture map → implementation queue flow so future agent work is targeted and reversible.

## Desired User Experience

1. Adarsha can say “work the pattern harvest” and the agent knows which repos to inspect and what artifact to update.
2. The dashboard/repo contains a clear map of reference projects, their useful patterns, code locations, licenses, and adoption decision.
3. Every borrowed idea becomes a scoped task before code changes happen.
4. Risky patterns, especially social automation and write actions, are explicitly gated behind approval/safety design.
5. The agent avoids over-documenting random notes; artifacts should be short, actionable, and implementation-oriented.

## Invariants

1. Do not copy source code from AGPL or unclear-license repositories into LifeOS unless the license implications are explicitly accepted.
2. Prefer copying patterns/interfaces/architecture over copying implementation.
3. Each reference repo entry must include: repo URL, category, license, useful pattern, relevant files, adoption decision, and next action.
4. Implementation tasks must be ordered by dependency and risk.
5. Write/send/post/delete behavior must go through staged approval before execution.
6. Social media ingestion must be action-oriented only: DMs, mentions, recruiter/founder signals, not feeds.
7. The first implementation priority is local-first, personal-use utility; do not prematurely build multi-user SaaS infrastructure.

## Non-goals

- No full rewrite of LifeOS.
- No cloning paid connector platforms wholesale.
- No connecting every possible app immediately.
- No autonomous posting/sending without approval.
- No large documentation dump unless it directly feeds the task queue.

## Success Criteria

- A compact source map exists in this spec.
- A prioritized implementation queue exists in this spec.
- At least the top 5 reference repos have been locally cloned or inspected with file-level pointers.
- Future LifeOS changes can cite a source-map entry and task ID.
