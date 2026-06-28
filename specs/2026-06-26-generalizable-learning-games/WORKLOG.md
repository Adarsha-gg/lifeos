# Worklog

## 2026-06-27

- Clarified graph model: global concept library underneath, personal knowledge graph on top.
- Rule: only draw edges for real concept relations; unrelated topics stay as separate islands.
- Replaced forced universal skill tree with `domains`, `nodes`, and typed `edges`.
- Default graph view is personal progress only; global library is a separate browse mode.
- Updated `/learn` copy to point at the personal knowledge graph.
- Validated build/parse and rendered personal/global graph screenshots.
- Ingested Math Academy learning-model notes as source-backed principles, not copied text.
- Added `tools/lifeos_learning_engine.py` for due reviews, frontier topics, mixed practice, and an ingestion contract.
- Added `tools/lifeos_ingest_doc.py` for local markdown/text ingestion into source/concept packets.
- Wired `/learn` to regenerate the graph and training queue together.
