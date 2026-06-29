# Product Spec: Adaptive Learning Levels and Recommendations

## Problem

LifeOS has a knowledge graph and lesson deck, but the system does not yet behave like a tutor. It shows nodes and cards, but it does not clearly assess the learner's level, explain readiness, or recommend the next best lesson based on graph prerequisites and progress.

## Goal

Make LifeOS feel like a personal adaptive learning system:

- assess the learner's current level overall and by domain;
- show that assessment visually in the graph/training surfaces;
- recommend next lessons/games from the knowledge graph;
- explain why each recommendation is appropriate;
- keep everything local-first and static-deployable.

## Target user experience

A user opens LifeOS and sees:

1. Their overall level and XP.
2. Domain levels such as History Level 2, Physics Level 1, Startup Level 3.
3. A recommendation queue that says what to do next and why.
4. Recommendations that change after marking nodes learned or reviewed.
5. Cards/graph/training pages that feel coordinated, not separate widgets.

## Behavior requirements

1. **Overall level**
   - The system calculates a total learner level from completed node XP.
   - Existing completed progress in `localStorage['lifeos.learning.progress.v1']` must continue to work.

2. **Domain levels**
   - The system calculates per-domain XP, completed nodes, total nodes, and a domain level.
   - Domain levels are visible in the knowledge graph or training UI.

3. **Readiness assessment**
   - Each candidate recommendation has a readiness state:
     - `review`: already learned but due for spaced review;
     - `ready`: prerequisites satisfied and difficulty matches the learner;
     - `almost`: close to ready but missing light prerequisites or slightly above level;
     - `stretch`: useful but above current level;
     - `explore`: no strong prerequisite signal, suitable for starting/exploration.

4. **Recommendation ranking**
   - Due reviews rank first.
   - New recommendations prefer graph-frontier items whose prerequisites are satisfied.
   - Difficulty should be near the learner's level in that domain, with a mild challenge preferred over content that is too easy or too hard.
   - The system should interleave domains and avoid only recommending one domain forever.
   - The recommendation list should still work for new users with no progress.

5. **Explainability**
   - Recommendations must include visible reasons such as prerequisite ratio, level match, weak domain, review due, or graph connection.
   - The user should not have to trust a black-box recommender.

6. **Local-first privacy**
   - Progress and recommendation state remain client-local in browser localStorage.
   - No backend, account, or analytics dependency is required.

7. **Performance**
   - The graph page must continue rendering under 100ms in the existing graph performance metric on the current graph size.

## Non-goals

- No trained ML model in v1.
- No server user accounts.
- No collaborative filtering across users.
- No automatic claim that reading a page means mastery; explicit actions remain the progress signal.
- No new copyrighted content behavior.

## Acceptance checks

- With empty localStorage, the user sees Level 1 and beginner/explore/ready recommendations.
- After marking nodes learned, overall level and relevant domain level update.
- Recommendations change after progress changes.
- Recommendation cards explain why each item is recommended.
- Reset clears visible levels and recommendations without reload.
- Graph render performance remains below 100ms.

## Expansion: game-like progression

The adaptive layer should feel like a game progression system, not a spreadsheet. Leveling up should produce visible feedback, ranks, and a clear path of what comes first, what comes next, and what unlocks later.

Additional behavior requirements:

- The learner sees a rank/title derived from level.
- The training queue shows a quest/path sequence, ordered from review/current step to ready-next to stretch/future unlocks.
- When the learner crosses a level threshold, the UI shows a level-up moment and stores that it was seen locally.
- The path must remain explainable: every quest item still says why it is recommended.
