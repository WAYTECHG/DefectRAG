# Apply the DefectRAG v7 source patch

This ZIP contains changed source files only. It does **not** include your MVTec LOCO AD dataset, extracted features, compact memory banks, trained head checkpoints, `.env`, reference gallery, or run outputs. Merge its `DefectRAG/` tree into your existing Windows project, retaining those generated folders. Back up the project first.

The key changes are:

- The shared webpage has a responsive glass-style redesign, method benchmark cards, source-coverage status, and an actual elapsed timer. It has no public document upload control.
- Both local and Render `/api/documents` endpoints reject visitor uploads. Developer-reviewed knowledge is prepared offline. The category-aware retriever excludes another product's documents; an inspection without approved product rules states that it cannot verify product specifications.
- The Space records processing durations and usually avoids a second generation call with the current generic-only knowledge corpus. Its visual observation and report token caps are lower; measure accuracy as well as speed after deployment.
- `scripts/evaluate_compact_localization.py` measures pixel AUROC and single-box overlap for the compact memory, head, and fusion. It is separate from the already completed image-level three-seed runs and is **not** mAP50 or official sPRO.

**Read `docs/CURATED_REBUILD_AND_BENCHMARK.md` for the exact architecture, offline curation steps, metrics, limitations, and deployment order.** Deploy the Space code first, then Render. Rebuild local Docker `api` separately if you use local mode. Check the Space directly before testing the Render website.

Keep your original `retrieval/index/` and `data/knowledge/knowledge_base.jsonl` during the source update unless you are deliberately publishing a reviewed knowledge revision. The 13 bundled index records are generic/category overviews. No product-specific rules have been manufactured by this patch. You can adopt the user interface and safer abstention behavior immediately without redoing DINOv3 features or training.

Run `python -m unittest discover -s tests -v`, `python -m compileall -q app knowledge retrieval rag vision scripts cloud`, and `node --check app/static/app.js` after merging. Real GPU inference and a visual browser review require your running deployment and assets.
