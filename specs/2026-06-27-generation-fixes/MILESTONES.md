# Milestones

## 2026-06-27 Fix Pass

- Added `PROMPT_VERSION` and `mission_hash` cache invalidation to `lifeos_generate.py`.
- `missions` now writes `output/learn/generation-status.json` and prints a `GENERATION: ...` summary.
- Added `missions --strict` for manual debugging runs that should fail on any topic failure.
- `lifeos_morning_ping.py` reads generation status and adds a warning line when topics fail.
- Generated game graph nodes now link to `#game`.
- Lesson game containers now render with `id="game"`.
- `merge_generated()` now adds only the generated lesson's actual domain instead of re-appending every domain.
- Audited `difficulty`; generated behavior uses `difficulty_level`, while coarse `difficulty` remains compatibility metadata.
- Hardened generated title normalization against mission-header artifacts like `# Mission`.

## Validation

- `python -m py_compile tools\lifeos_generate.py tools\lifeos_lessons.py tools\lifeos_morning_ping.py`
- `python tools\lifeos_generate.py missions --difficulty teen`
- Immediate rerun reused cached mission-hash-matched lessons.
- Generated game nodes in `graph-store.json` point to `*.html#game`.
- Full `python tools\lifeos_morning.py run` exited 0 and captured the `GENERATION: 3 ok, 0 failed` summary in the step stdout.
