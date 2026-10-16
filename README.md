# DefectRAG v2

**Latest development checkpoint: all 12 VisA categories are fitted and evaluated.** See [all-category metrics](docs/ALL12_EVALUATION.md) and [resume instructions](DEVELOPMENT_PROGRESS.md). API/software/build checks passed; final expanded browser QA, documentation cleanup and release packaging are pending. Earlier release descriptions below refer to the prior three-category handoff.

Local AI-powered industrial anomaly inspection and evidence assistant. React + Vite,
FastAPI, frozen DINOv3, LangChain, LangGraph, SQLite and optional local Qwen generation.

## Start on Windows

Extract the ZIP to a writable folder. Install Python 3.11 (3.12 also supported).
The production dashboard and model assets are already included; Node is needed
only when editing/rebuilding the frontend.

```powershell
.\Start-DefectRAG.cmd -Setup
```

First setup installs dependencies into a new `.venv` and needs internet access.
Subsequent starts need no dependency download:

```powershell
.\Start-DefectRAG.cmd
# Open http://127.0.0.1:8765
```

For NVIDIA acceleration, install the matching CUDA wheels into that venv:

```powershell
.\.venv\Scripts\python.exe -m pip install torch==2.8.0 torchvision==0.23.0 --index-url https://download.pytorch.org/whl/cu126
```

CPU inference also works. Set `DEFECTRAG_DEVICE=cpu` in an optional `.env` copied
from `.env.example` to force CPU. The app uses no paid API and requires no account.
For an existing compatible environment, pass `-PythonPath C:\path\to\python.exe`.
Run `Start-DefectRAG.ps1 -Verify -NoBrowser` for a startup/real-model check.

## Local Evidence Assistant

Run Ollama and make `qwen2.5:3b` available. Existing installations are reused; the
application never automatically downloads an LLM. If needed, explicitly run
`ollama pull qwen2.5:3b` after approving the roughly 1.9 GB download yourself.
`OLLAMA_URL` and `OLLAMA_MODEL` are configurable in `.env`.

Inspect an image, then ask about its score, threshold or heatmap. The assistant
retrieves attributed documents, generates concise claims and checks source IDs
and exact supporting quotes. Follow-ups stay linked to the saved inspection.
Old assistant answers are excluded from context after knowledge changes.
If Ollama is unavailable or citations fail, the UI clearly shows **retrieval only**.
Unsupported process/root-cause questions abstain. Citation checks are not a proof
of semantic correctness; source excerpts remain visible for review.

## What is included

- Image and batch upload for **PCB1, capsules and cashew**, with validation and size limits.
- Good / Anomalous / Uncertain screening, score, calibrated threshold and coarse heatmap.
- Evidence conversation, local inspection history, batch filters and review alerts.
- Printable inspection report (browser Print → Save PDF) and CSV export.
- Performance/About pages, six attributed sample previews and persistent knowledge index.
- Source, fitted normal banks, frozen encoder/embedding weights, training/evaluation
  scripts, measured results, Windows launchers, Docker and static frontend configuration.

Uploads and history live in `runtime/`, created at first start. They are excluded
from the release archive. Local storage is single-user. Do not expose this API
publicly without session isolation, access controls and retention policies.

## Measured detector and scope

The shipped detector is **frozen DINOv3 ViT-S/16 + nearest-normal cosine patch
memory**, not Dinomaly. Normal-bank fitting does not train an encoder or decoder.
Anomalib Dinomaly is an optional, unverified experiment and is not used by the app.

| Product | Final images | AUROC | AP | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|
| PCB1 | 180 | 0.897 | 0.866 | 0.779 | 0.838 | 0.807 |
| Capsules | 140 | 0.825 | 0.889 | 0.838 | 0.713 | 0.770 |
| Cashew | 130 | 0.971 | 0.983 | 1.000 | 0.700 | 0.824 |

Seed 42; 64 official training normals fit each category. Separate validation uses
32 other training normals and 20 anomalies reassigned from the official test pool.
The remaining official test identities form the final evaluation. This is a
**modified VisA protocol**, not the full official benchmark. Content hashes verify
split separation. Thresholds maximize validation F1; final-test labels are not used
to tune them. Binary metrics use that frozen threshold; the UI also defers scores
within a fixed ±5% review band. This band is not calibrated confidence.

The 14×14 heatmap is interpolated patch distance, not a supervised defect mask.
Pixel metrics use 64×64 resized masks and include normal images. Capsule localization
is weak (pixel AP about 0.045). No specific defect names, component counts, root
causes, factory tolerances or product safety/acceptance guarantees are inferred.
The operator-selected category is not automatically verified.

`results/evaluation.json` and category predictions/splits preserve the measurements.
The separate clean `results/serving_profile.json` records roughly 54–66 ms median
model inference on an RTX 4060 Laptop GPU; total file-to-result time is higher.
PyTorch allocated GPU peak is about 66–90 MB for the fitted detector, excluding
driver/other-process memory. CPU inference was also checked. Do not substitute
published Dinomaly performance for these measured results.

## Development and evaluation

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
cd frontend
npm ci
npm run dev
```

Vite proxies `/api` to port 8765. Build with `npm run build`; FastAPI serves the
existing production build. No frontend rebuild is needed for ordinary use.

The VisA dataset is intentionally excluded. Use the existing local dataset where
available. `scripts/download_visa.py` requires explicit `--authorize-download`.
To reproduce fitting, first make a separate experiment copy so current banks and
evaluation records remain preserved, then run:

```powershell
python -m scripts.train --dataset C:\path\to\VisA --encoder models/encoder
```

Do not refit merely to start the app. `scripts/train_anomalib.py` requires a separate
environment, explicit training authorization and subsequent independent evaluation;
its checkpoint is not integrated with the production detector.

## Free static showcase and Docker

The separate static showcase is now implemented and tested. It contains seven
saved real VisA inspections, measured heatmaps, recorded cited Qwen conversations,
history filters, reports, CSV and performance pages. It needs no backend, secrets
or model download. New uploads and live chat remain features of the local app.

Use `DefectRAG-v2-static.zip` for Hugging Face Static Spaces, or deploy the frontend
source with the included Vercel/Render configuration. See
[exact run/deployment commands](deployment/RUN_AND_DEPLOY.md).
The newer full release is `DefectRAG-v2-with-static.zip`; the earlier local ZIP
is preserved. No public deployment has been created on your account.

`docker compose up --build` serves port 8765 on localhost, uses CPU wheels and
persists runtime data in a named volume. Ollama is reached via `host.docker.internal`.
The compose configuration was checked; container execution remains unverified
because the Docker daemon was unavailable during development.
The in-app browser also ignored the requested mobile viewport; narrow-screen
visual QA remains unverified despite the implemented responsive layouts.

See [deployment/README.md](deployment/README.md) for deployment boundaries.
The frontend supports `VITE_API_URL` and hash routes. Public inference needs a
separate service independent of this laptop. Supabase persistence and n8n alerts
are future integrations, not deployed features. Browser ONNX/WebGPU inference has
not been exported or validated. No cloud resources have been created.

## Evidence, architecture and recovery

- [Architecture](docs/ARCHITECTURE.md)
- [Verification report](docs/VERIFICATION_REPORT.md)
- [Third-party notices](docs/THIRD_PARTY_NOTICES.md)
- [Current development progress](DEVELOPMENT_PROGRESS.md)

The generated application code is MIT-licensed. Model and dataset terms remain
separate; see the included licenses and notices before redistributing assets.

**Portfolio description:** DefectRAG v2 combines real industrial anomaly inference
with a traceable evidence assistant. It demonstrates frozen visual feature
extraction, reproducible calibration and held-out evaluation, local retrieval and
generation, graph-based evidence checks, defensive APIs and persistent inspection
workflows. Measured limitations and explicit fallback states make its behavior
reviewable rather than presenting uncertain model outputs as verified diagnoses.
