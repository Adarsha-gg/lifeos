# Research: Adaptive Learning Levels and Recommendations

## Question

What recommendation approach should LifeOS use for a graph-based learning app that runs as a static/mobile-friendly site, stores progress in localStorage, and needs to assess a learner's level before recommending the next lesson/game?

## Sources consulted

- Smart Learning Environments / Springer Nature, "Prerequisites-based course recommendation" (2024): e-learning recommendations should account for learner background knowledge and prerequisites, not only similarity or popularity. The paper frames educational recommendation as matching prerequisites + difficulty, and reports prerequisite-aware recommendations outperforming classical content-only ranking on MRR/MAP/NDCG in their experiment.
- arXiv survey, "A Survey of Knowledge Tracing: Models, Variants, and Applications" (2021/updated): knowledge tracing estimates evolving learner knowledge states from interaction history; model families include Bayesian, logistic, deep, and graph-based approaches. The survey emphasizes interpretability, forgetting, side information, and applications to learning-resource recommendation/adaptive learning.
- Electronics / MDPI, "Personalized Learning Path Recommendation Based on Knowledge Graphs: A Survey" (2026): learning-path systems typically combine learner knowledge-state modeling, knowledge-graph/prerequisite structure, recommendation objectives, and path constraints.
- Additional search results: personal knowledge graphs for learner modeling, GraphRAG/knowledge-graph learning paths, BKT/systematic reviews, and practical adaptive prototypes.

## Practical conclusions for LifeOS

### 1. Use an interpretable hybrid, not heavyweight ML

LifeOS does not yet have a large multi-user interaction dataset. Collaborative filtering, deep knowledge tracing, graph neural networks, and reinforcement learning are overkill right now and would be opaque on-device. The first version should be a deterministic, explainable hybrid:

1. **Prerequisite gating** from graph edges.
2. **Learner model** from local progress/review history.
3. **Difficulty/level matching** from node metadata, XP, and graph complexity.
4. **Spaced review priority** for learned nodes that are due.
5. **Exploration/interleaving** so recommendations do not get stuck in one domain.
6. **Explanation strings** for every recommendation.

This matches the research direction without requiring training data or a backend.

### 2. Educational recommendation is different from Netflix-style recommendation

The Springer paper's key warning applies directly: recommending only what resembles prior preferences can be bad in education because the learner may lack prerequisites. LifeOS must score **readiness**, not just interest. A good recommendation should feel like: "this is the next useful thing you can actually absorb."

### 3. Levels should be per-domain and overall

A single XP level is too shallow. The learner needs:

- overall level: total learned XP;
- per-domain levels: history/thinking/physics/growth/culture/systems/custom;
- readiness state for each target item: review / ready / almost ready / stretch / explore;
- transparent progress bars by domain.

This maps to knowledge tracing's "knowledge state" idea while staying understandable.

### 4. Use lightweight knowledge tracing signals

No binary quiz correctness exists for most LifeOS lessons yet, but local progress still gives useful signals:

- learned/completed node = mastery signal;
- review stage and last review time = forgetting/spaced repetition signal;
- graph prerequisites completed = readiness signal;
- domain XP = local ability signal;
- skipped/read-interest in deck = preference signal;
- game completion later can become stronger evidence.

### 5. Recommendation scoring design

A candidate should get points for:

- due review if learned and spaced interval expired;
- high prerequisite completion ratio;
- difficulty close to learner's domain level plus a small challenge;
- connected to something already learned;
- weak/under-covered domain if the user is too concentrated elsewhere;
- daily/newness/exploration tie-breakers.

Candidates should be penalized when:

- too many prerequisites are missing;
- difficulty gap is too large;
- user explicitly skipped recently;
- already learned and not due for review.

### 6. UI should expose why

Research repeatedly flags interpretability as important in education. Recommendations should not be mysterious. Each recommendation should display reason chips such as:

- "Ready: 3/3 prereqs"
- "Level 2 match"
- "Strengthens weak Physics"
- "Review due: stage 2"
- "Leads to 4 later nodes"

## Recommended v1 algorithm

For each node:

1. Estimate `nodeLevel`:
   - explicit difficulty metadata if present;
   - else from XP + prerequisite count + outgoing complexity.
2. Estimate `learnerModel`:
   - total XP/overall level;
   - domain XP/domain level;
   - done set and review due status.
3. Compute prerequisite info:
   - incoming prerequisite/practice/application parents;
   - completion ratio and missing titles.
4. Score candidates:
   - due reviews first;
   - unlearned nodes with high readiness;
   - ideal challenge around `domainLevel + 1`;
   - weak-domain and graph-frontier boosts;
   - deterministic hash tie-break.
5. Return top recommendations with `{node, score, kind, readiness, reasons}`.

## Non-goals for v1

- No server-side tracking.
- No user accounts.
- No trained model.
- No pretending the learner is mastered because they merely opened a page; explicit "Mark learned" remains the source of truth.
- No copyrighted source-copying changes.

## Validation ideas

- Unit/smoke: generated JS parses and pages render.
- Browser: seed localStorage with learned nodes and verify assessment level/recommendations change.
- Performance: global graph render remains under 100ms.
- UX: screenshot graph/training/learn pages on 390x844 phone viewport.
