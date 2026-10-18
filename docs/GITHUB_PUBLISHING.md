# GitHub publishing guide

Suggested repository name: **DefectRAG**

Suggested About description:

> Visual anomaly inspection across 12 VisA products with DINOv2 heatmaps, evidence-grounded RAG, a React dashboard, and Supabase collaboration on Hugging Face ZeroGPU.

Website: https://huggingface.co/spaces/Wizzas/DefectRAG

Suggested topics: `anomaly-detection`, `computer-vision`, `dinov2`, `rag`, `gradio`,
`langgraph`, `react`, `supabase`, `huggingface-spaces`, `zerogpu`, `visa-dataset`.

## Upload this source structure

| Include | Purpose |
|---|---|
| README.md, LICENSE, .gitignore, .env.example | Project overview, licensing and safe configuration template |
| backend/ | Inference, retrieval/generation workflow, API and local persistence |
| frontend/src/, frontend/public/, frontend/tests/ | Existing React UI, new SVG logo, public attributed showcase assets and tests |
| frontend/package.json, package-lock.json, index.html, vite.config.js | Reproducible frontend build configuration |
| deployment/ | Gradio adapter, pinned Space requirements and reviewed Supabase SQL templates |
| scripts/, tests/ | Asset acquisition, evaluation tooling and meaningful software checks |
| knowledge/ text and sources.json | Attributed RAG documents; exclude generated index |
| docs/ | Architecture, honest metrics, public screenshots, setup and validation evidence |
| Selected results/*.json and highres_comparison.csv | Public aggregate benchmark and deployment summaries; omit private/raw inspection traces |
| Start-DefectRAG.cmd/.ps1, requirements*.txt | Existing local startup and dependency definitions |
| Dockerfile, compose.yaml, render.yaml | Existing optional configuration; Docker execution remains unverified |

**Exclude:** models/, datasets, experiments/, runtime/, development-support/,
.venv/, .python-deps/, node_modules/, .env files, private inspection images,
database dumps, sessions/JWTs, signed links, raw logs/reports and ZIPs. Do not
upload the entire Desktop folder. Publishable Supabase keys are public by design,
but the prepared export replaces the personal project config with a blank template.
Service-role keys, database passwords and HF tokens must never be included.

## Prepared upload folder

The export command copies only allowlisted tracked source/public documentation and
never includes the original .git history. Existing files/models remain untouched:

```powershell
python -m scripts.prepare_github_export
```

Default output: `development-support/github-ready/DefectRAG/`. An existing output
is preserved; choose a different `--output` for another export. This folder is
source-only, not a ready-made model bundle. Fresh-clone asset instructions are in
README.md. The asset downloader is explicit and was not executed during this
documentation update. No new dataset/model download is needed on this computer.

Create a GitHub repository and upload the **contents** of the prepared folder.
Repository creation and public push are manual; no GitHub repository has been
created or published by this task. Review screenshots/attribution before publishing.
Actual model/dataset licenses remain separate from the application MIT license.
