# DefectRAG v2 — resumable development checkpoint

Checkpoint date: **16 October 2026, Asia/Kuala_Lumpur**.
Status: **working source and real calibrated inference saved; application acceptance and final release packaging unfinished**.

## Resume here — do not rebuild or retrain

The user requested a durable checkpoint because internet access may disconnect.
Continue in this same Work conversation after reconnecting. Read this file first,
then inspect the actual files and current process/port state. Reuse all completed
source, normal banks, encoder assets, embeddings, split manifests and results.
Do not restart completed fitting, redownload VisA or replace the original project.

Primary development source at this checkpoint:

`C:\Users\User\.codex\.chatgpt-projects\g-p-6abf9c3f00a4819198b9ff56b5456844\DefectRAG-v2`

Requested Desktop location, populated by checkpoint synchronization:

`C:\Users\User\Desktop\DefectRAG-v2`

The checkpoint archive and its SHA256 receipt are stored beside the development
source and copied to the Desktop. `CHECKPOINT_MANIFEST.json` inventories preserved
files and hashes. The archive is a **development checkpoint**, not the final
accepted `DefectRAG-v2.zip` release. Reconcile any subsequent Desktop edits before
resynchronizing; never overwrite newer edits blindly.

## Preservation boundaries

- Original `C:\Users\User\Desktop\DefectRAG-Verified` was inspected read-only.
  Its source, environments, secrets, histories and experiments were not modified.
- ChatGPT project's `sources/` remains read-only and untouched.
- No cloud resources, public deployment, paid services or external notifications.
- No dataset download or extended gradient-training job was performed.
- Never package the original project's `.env`, history or dataset.

## Completed files and functionality

- `backend/vision.py`: genuine frozen DINOv3 ViT-S/16 patch inference, category
  normal banks, cosine distances, validated score thresholds, review band,
  interpolated heatmap, model checksums and execution-failure handling.
- `scripts/train.py`: bounded 64-shot normal-only fitting for PCB1, capsules,
  cashew; deterministic separate calibration/final identities; cross-split content
  hash checks; image/pixel metrics and saved per-image predictions.
- `models/`: three fitted `.npz` banks and JSON model cards, cached encoder and
  BGE small embedding assets copied into this new project, checksums and upstream
  `DINOV3-LICENSE.md`. Source caches were read-only. Additional third-party notice
  and final licensing inventory remain to be completed.
- `backend/rag.py`: LangChain TextLoader, recursive chunking, local BGE embeddings,
  persistent cosine-search index and bounded query cache; LangGraph routing,
  retrieval, source checks, local Ollama generation, citation ID/exact-quote checks,
  abstention and explicitly labelled retrieval-only fallback.
- `knowledge/`: three attributed source summaries / project policy documents and
  a built five-passage index (`knowledge/index/`).
- `backend/main.py`, `backend/storage.py`: FastAPI API, local SQLite, defensive
  image validation, individual/batch inference, saved images/maps, history filters,
  CSV export, printable HTML report, alerts and saved assistant conversations.
  Repository interface is present for a future cloud implementation.
- `frontend/`: React + Vite dashboard with overview, image inspection, categories,
  six permitted VisA sample previews, results/heatmap, linked assistant, batch
  monitoring, history, alerts, model performance and About/source views.
- `frontend/dist/`: production build completed successfully. `package-lock.json`
  preserves exact frontend dependencies. Installed frontend node_modules remain in
  the development workspace and are deliberately excluded from the checkpoint ZIP.
- `Start-DefectRAG.ps1`, `.cmd`, `.env.example`, `requirements.txt`, Dockerfile,
  compose.yaml, static HF deployment README, opt-in dataset downloader, optional
  Anomalib training script, software tests and live acceptance script are saved.

## Measured model results — retain these, do not invent replacements

Actual NVIDIA RTX 4060 CUDA evaluation on 450 final images in total:

| Category | Final images | Image AUROC | Average precision | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|
| PCB1 | 180 | 0.896625 | 0.866319 | 0.779070 | 0.837500 | 0.807229 |
| Capsules | 140 | 0.825000 | 0.888730 | 0.838235 | 0.712500 | 0.770270 |
| Cashew | 130 | 0.970500 | 0.983017 | 1.000000 | 0.700000 | 0.823529 |

Authoritative records: `results/evaluation.json`, `results/*_predictions.json`,
`results/*_splits.json`, `models/*.json`. Pixel AUROC/AP/F1, confusion matrices,
model size and timing/memory observations are in these files.

Protocol: seed 42, 64 official training normals fitted per category; 32 different
training normals and 20 official test anomalies used for calibration; all remaining
official test normal/anomalous images used for final evaluation. This deliberately
modified protocol is **not the full official VisA benchmark**. Threshold maximizes
validation F1. The ±5% uncertainty band is an operational heuristic, not calibrated
confidence. No final-test labels were used for fitting or threshold selection.

The fallback is **DINOv3 nearest-normal patch memory, not Dinomaly**, and has no
gradient-trained decoder. Anomalib was absent, and current upstream Dinomaly
documents a DINOv2 interface; do not claim a DINOv3 adapter was tested. Optional
`scripts/train_anomalib.py` is unverified and requires explicit extended-training
approval. Do not start it merely to resume this checkpoint.

Capsule localization is weak (pixel AP about 0.045); the UI exposes this. No named
defect classifier, factory acceptance guarantee, process diagnosis or root-cause
claim is supported. Timing observations came from overlapping repeated fitting/
evaluation invocations after slow imports; ranking/classification metrics matched,
but latency needs one clean, bounded serving profile before final publication.
Reported GPU memory is PyTorch allocated peak, not total device/process memory.

## Verification completed

1. Frontend production build passed (`npm.cmd run build`), Vite 6.4.1, React 19.1.1.
2. **16 isolated software tests passed**. `results/software-tests.xml` is the
   authoritative JUnit report. Tests cover persistence, filtering, alerts, reports,
   uploads, failures, SQL parameters, output escaping, batch partial failure,
   graph scope/citation checks and split separation. Synthetic fixtures are used
   only for isolated software tests; they are not model-performance evidence.
3. Live FastAPI at port 8766 accepted six original held-out VisA files, two per
   category, using the real packaged encoder and banks. All six served scores
   matched the frozen evaluation predictions within 1e-5. Image and heatmap
   endpoints and persisted record retrieval returned HTTP 200.
4. Actual BGE retrieval succeeded, returning source-attributed relevant passages.
5. Ollama was contacted and the LangGraph trace reached `generate`, but the first
   Qwen answer produced **no claims passing citation validation**. It correctly
   fell back to `retrieval_only`. Genuine accepted generative RAG is **NOT yet
   verified**, and the live acceptance script stopped on that assertion.
6. An actual in-app browser loaded the dashboard from `http://127.0.0.1:8766/`,
   showing the six persisted real inspections, scores, model cards, samples and
   review counts. Full interaction, screenshots and mobile checks remain pending.

The failed live acceptance report was not written by the current script because
it only writes after all assertions pass. `results/acceptance_checkpoint.json`
preserves partial verified observations and the known blocker. Fix incremental
report saving before re-running acceptance; do not repeatedly create duplicate
six-image batches just to debug generation.

## Runtime and exact resume commands

Development used the already-installed read-only Python **3.12.4** environment:

`C:\Users\User\Desktop\DefectRAG-Verified\.venv-defectrag\Scripts\python.exe`

Its installed torch is `2.8.0+cu126`, torchvision `0.23.0`, transformers `4.57.6`,
FastAPI `0.142.2`, LangChain Core `1.6.10`, LangGraph `1.2.14`.
Python 3.11 is the requested target; clean 3.11 setup has **not yet been tested**.
Do not install or alter packages in the original environment.

Two small missing packages were installed separately into:

`C:\Users\User\.codex\.chatgpt-projects\g-p-6abf9c3f00a4819198b9ff56b5456844\.test-deps`

They are `langchain-community==0.4.1` and
`langchain-text-splitters==1.1.2`. The checkpoint copy preserves this overlay under
`development-support/langchain-overlay/`, so development can resume offline with
the installed original interpreter without changing its environment.

PowerShell from the Desktop copy (after verifying the copy/overlay exists):

```powershell
Set-Location 'C:\Users\User\Desktop\DefectRAG-v2'
$env:PYTHONPATH = Join-Path $PWD 'development-support\langchain-overlay'
$devPython = 'C:\Users\User\Desktop\DefectRAG-Verified\.venv-defectrag\Scripts\python.exe'
# First check whether 8765/8766 are already serving this app; reuse if healthy.
# If a new server is needed:
& $devPython -m uvicorn backend.main:app --host 127.0.0.1 --port 8766
```

Targeted software regression, only when source changes justify rerunning it:

```powershell
& $devPython -m pytest tests -q --tb=short --basetemp=runtime/test-temp --junitxml=results/software-tests.xml
```

Longer-term standalone setup uses `Start-DefectRAG.ps1 -Setup` and installs an
independent environment. This may require internet and downloads; it is not
necessary simply to resume current development. `frontend/dist` is already built.
Do not rerun npm installation if existing frontend dependencies/build suffice.

Local VisA root already available:

`C:\Users\User\Downloads\VisA_20220922`

Ollama models confirmed: `qwen2.5:3b`, `qwen2.5vl:3b`, `qwen3:8b`.
The app uses `qwen2.5:3b` at `http://127.0.0.1:11434`.

At checkpoint, newly created app servers may still be running from the workspace:
port 8766 was verified, process ID **8548**; another app instance was started on
8765. Treat process IDs as stale after reconnecting. Check identity before stopping
anything, and never stop the original project's services or unrelated experiments.
Ephemeral tool-session identifiers are not a reliable resumption mechanism.

Windows sandbox restrictions blocked local Ollama network access, npm/PyPI DNS,
and pytest's default temporary directory; approved elevated commands were used
where needed. PyTorch imports were slow even though they eventually completed.
Do not infer missing weights from a briefly silent import and launch duplicate jobs.

## Unfinished tasks, in practical order

1. Debug genuine Qwen generation using an EXISTING saved inspection. Capture raw
   model output locally (no secrets) to learn why claim/citation JSON is rejected.
   Use a structured schema / concise prompt or one bounded retry if appropriate;
   retain exact-quote checks, honest fallback and scope abstention.
2. Make live acceptance persist partial results on failure. Finish follow-up
   generation, retrieval, report, batch filtering, alert and invalid-upload checks.
   Add missing meaningful tests only for real bugs or failure modes encountered.
3. Finish browser interactions: sample selection, real inference, heatmap toggle,
   assistant, history filters, alerts and responsive views. The working CUA entry
   was a BACKGROUND IAB tab; a visible-tab creation initially timed out. Use
   `cua.createBrowserTab('iab', URL, {visible:false})` if recreating it, read its
   runtime documentation, and capture final screenshots. Do not assume full UI QA
   is complete merely because the DOM loaded.
4. Profile one clean serving run for timing/memory, without refitting models.
   Verify Windows launcher and clean startup. Record target Python 3.11 and Docker
   limitations honestly if those cannot be tested. Docker configuration is saved,
   but Docker has not been run.
5. Review source for material correctness. In particular, strengthen knowledge
   index compatibility fingerprinting if embedding assets change, verify optional
   Anomalib script API compatibility before calling it runnable, and review
   localhost/privacy/deployment boundaries. No public exposure is authorized.
6. Complete concise README, architecture diagram, portfolio description,
   third-party attribution/license inventory and final test report. Document
   optional Qwen dependency and no-LLM fallback, weak capsule localization,
   modified evaluation protocol and model scope. Avoid excessive documentation.
7. Produce final `DefectRAG-v2.zip` including source, frontend build, banks, lawful
   model assets, knowledge/index, configs, results and launchers. Exclude dataset,
   runtime inspection DB/uploads, test temporary files, node_modules, development
   overlay, secrets and caches. Verify archive entries and SHA256; test extracted
   artifact. Final ZIP has **not** been produced at this checkpoint.

## User intent to retain

Complete Stage 1: a reliable local inspection application and verified ZIP,
prioritizing completion over experiments. Preserve the original project. Future
Supabase/n8n/HF deployment and browser ONNX inference are only prepared, not
deployed. Ask before major downloads, extended GPU training, paid services,
destruction or public deployment. Resume from saved work, not from a proposal or
an empty scaffold.
