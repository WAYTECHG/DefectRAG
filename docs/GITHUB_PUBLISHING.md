# GitHub publishing guide

Suggested repository name: **DefectRAG**

Suggested About description:

> Visual anomaly inspection with DINOv2 heatmaps, evidence-grounded RAG, guided practice, private local/cloud sync, native MFA and audited team corrective actions.

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
| frontend/localBuild.mjs | Required source/output receipt plugin imported by the Vite configuration |
| deployment/ | Gradio adapter, pinned Space requirements and reviewed Supabase SQL templates |
| scripts/, tests/ | Asset acquisition, evaluation tooling and meaningful software checks |
| knowledge/ text and sources.json | Attributed RAG documents; exclude generated index |
| Selected docs/ | Setup, security, architecture, user guides, scientific metric definitions and licensing |
| Selected results/*.json and highres_comparison.csv | Public aggregate benchmark and deployment summaries; omit private/raw inspection traces |
| Start-DefectRAG.cmd/.ps1, requirements*.txt | Existing local startup and dependency definitions |
| Dockerfile, compose.yaml, render.yaml | Existing optional configuration; Docker execution remains unverified |

**Exclude:** models/, datasets, experiments/, runtime/, development-support/,
.venv/, .python-deps/, node_modules/, .env files, private inspection images,
database dumps, sessions/JWTs, signed links, raw logs/reports and ZIPs. Do not
upload the entire Desktop folder. Publishable Supabase keys are public by design,
but the prepared export replaces the personal project config with a blank template.
Service-role keys, database passwords and HF tokens must never be included.
Account-specific saved-query catalogs, QA account deletion/backup SQL and email
test queries are also excluded from the public source export.

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

The existing repository is https://github.com/WAYTECHG/DefectRAG. Its separate
Desktop Git copy is `development-support/github-ready/DefectRAG`, branch `main`,
with `origin` pointing to that repository. The main Desktop application folder is
a private development checkout and has no GitHub remote. Do not push its history.

For the prepared update, use this in PowerShell after reviewing its file summary:

```powershell
Set-Location 'C:/Users/User/Desktop/DefectRAG-v2/development-support/github-ready/DefectRAG'
git add --all
git diff --cached --stat
git commit -m "Add guided practice, secure workspaces and corrective actions"
if ($LASTEXITCODE -eq 0) { git push origin main }
```

These commands target only the prepared public copy. No force push is needed.
The update preparation preserves `.git` and never deletes existing repository
files. If the remote changes before pushing, Git's normal rejection protects it;
resolve that update rather than adding `--force`. This task prepares files but
does not run the public commit or push. Review screenshots/attribution before publishing.
Actual model/dataset licenses remain separate from the application MIT license.

## Public documentation policy

Only the named PUBLIC_DOCS allowlist in scripts/prepare_github_export.py is
exported. Progress journals, phase-by-phase rollout reports, internal QA pictures,
raw traces and account troubleshooting notes remain in the private development
archive. Runtime code, reusable tests, schema migrations, n8n templates and the
aggregate metric files remain available. Export receipts are written beside the
private export folder, not into the repository root. Old private workstation
checkpoint/ZIP helpers and one-event result queries are not public application
requirements. Update this allowlist deliberately when adding useful documentation.
